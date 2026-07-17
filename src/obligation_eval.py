"""Evaluate conditional obligations — Python decides, never the LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fact_extractor import AtomAnswer
from obligation import ObligationSpec, collect_all_leaves
from primitives import EvalContext, EvalResult, eval_predicate
from semantic_report import SemanticReport
from symbolic_eval import MATCH_CLEAR, MATCH_CLEAR_UNMATCH, MATCH_UNABLE, SymbolicVerdict
from fact_schema import _is_blank_value, resolve_where_bindings


@dataclass
class ObligationVerdict:
    status: str  # clear | violates | not_applicable | unable | advisory
    match: str
    reason: str
    evidence: str
    source: str = "obligation"


def _to_symbolic(verdict: ObligationVerdict) -> SymbolicVerdict:
    if verdict.status == "violates":
        match = MATCH_CLEAR_UNMATCH
    elif verdict.status == "unable":
        match = MATCH_UNABLE
    else:
        match = MATCH_CLEAR
    return SymbolicVerdict(
        match=match,
        reason=verdict.reason,
        evidence=verdict.evidence,
        source=verdict.source,
    )


def evaluate_obligation(
    spec: dict[str, Any] | ObligationSpec,
    facts: dict[str, Any],
    *,
    semantic: SemanticReport | None = None,
    atom_answers: dict[str, AtomAnswer] | None = None,
    confidence_threshold: float = 0.0,
) -> ObligationVerdict:
    _ = confidence_threshold
    data = spec.to_dict() if isinstance(spec, ObligationSpec) else spec
    status_class = str(data.get("status_class") or "")
    source = str(data.get("source") or "")

    if status_class == "pending" or source == "pending":
        processor = str(data.get("pending_processor") or "processor")
        ds = str(data.get("data_source") or "report_content")
        return ObligationVerdict(
            status="advisory",
            match=MATCH_CLEAR,
            reason=f"In report ({ds}); needs {processor} (not built yet).",
            evidence="",
            source="obligation:pending",
        )
    if status_class == "unauthored" or source == "unauthored":
        ds = str(data.get("data_source") or "report_content")
        return ObligationVerdict(
            status="advisory",
            match=MATCH_CLEAR,
            reason=f"In report ({ds}); check not authored yet.",
            evidence="",
            source="obligation:unauthored",
        )
    if status_class == "unmapped" or source == "unmapped":
        return ObligationVerdict(
            status="advisory",
            match=MATCH_CLEAR,
            reason="Where not grounded to a real report field yet (unmapped).",
            evidence="",
            source="obligation:unmapped",
        )
    if status_class == "advisory" or source == "advisory":
        ds = str(data.get("data_source") or "out_of_report")
        return ObligationVerdict(
            status="advisory",
            match=MATCH_CLEAR,
            reason=f"Evidence requires {ds}; cannot auto-check from report alone.",
            evidence="",
            source="obligation:advisory",
        )
    if source == "missing_block":
        return ObligationVerdict(
            status="advisory",
            match=MATCH_CLEAR,
            reason="No check block authored for this checkpoint yet.",
            evidence="",
            source="obligation:missing_block",
        )
    ctx = EvalContext(
        facts=facts,
        semantic=semantic,
        atom_answers=atom_answers,
    )

    when = data.get("when")
    if when:
        when_result = eval_predicate(when, ctx)
        if when_result.value is None:
            return ObligationVerdict(
                status="unable",
                match=MATCH_UNABLE,
                reason="Cannot determine whether this rule applies.",
                evidence=when_result.evidence,
                source="obligation:when_unknown",
            )
        if not when_result.value:
            return ObligationVerdict(
                status="not_applicable",
                match=MATCH_CLEAR,
                reason="Rule does not apply in this report context.",
                evidence=when_result.evidence,
                source="obligation:not_applicable",
            )

    unless = data.get("unless")
    if unless:
        unless_result = eval_predicate(unless, ctx)
        if unless_result.value is None:
            return ObligationVerdict(
                status="unable",
                match=MATCH_UNABLE,
                reason="Cannot determine whether a never-flag condition applies.",
                evidence=unless_result.evidence,
                source="obligation:unless_unknown",
            )
        if unless_result.value:
            return ObligationVerdict(
                status="clear",
                match=MATCH_CLEAR,
                reason="A never-flag condition applies; requirement not violated.",
                evidence=unless_result.evidence,
                source="obligation:excused",
            )

    then_node = data.get("then")
    if not then_node:
        return ObligationVerdict(
            status="unable",
            match=MATCH_UNABLE,
            reason="CheckSpec missing THEN obligation.",
            evidence="",
            source="obligation:missing_then",
        )

    then_result = eval_predicate(then_node, ctx)
    if then_result.value is None:
        return ObligationVerdict(
            status="unable",
            match=MATCH_UNABLE,
            reason="Insufficient evidence to verify the obligation.",
            evidence=then_result.evidence,
            source=then_result.source,
        )
    if then_result.value:
        return ObligationVerdict(
            status="clear",
            match=MATCH_CLEAR,
            reason="Obligation satisfied.",
            evidence=then_result.evidence,
            source=then_result.source,
        )
    return ObligationVerdict(
        status="violates",
        match=MATCH_CLEAR_UNMATCH,
        reason="Report evidence violates this requirement.",
        evidence=then_result.evidence,
        source=then_result.source,
    )


def evaluate_obligation_symbolic(
    spec: dict[str, Any] | ObligationSpec,
    facts: dict[str, Any],
    *,
    semantic: SemanticReport | None = None,
    atom_answers: dict[str, AtomAnswer] | None = None,
    confidence_threshold: float = 0.0,
) -> SymbolicVerdict:
    return _to_symbolic(
        evaluate_obligation(
            spec,
            facts,
            semantic=semantic,
            atom_answers=atom_answers,
            confidence_threshold=confidence_threshold,
        )
    )


def when_applies_json_only(
    spec: dict[str, Any] | ObligationSpec,
    facts: dict[str, Any],
    *,
    semantic: SemanticReport | None = None,
) -> bool | None:
    """Evaluate WHEN clause using json-grounded nodes only (for gating atom extraction)."""
    data = spec.to_dict() if isinstance(spec, ObligationSpec) else spec
    when = data.get("when")
    if not when:
        return True
    if _has_non_json_ground(when):
        return None
    ctx = EvalContext(facts=facts, semantic=semantic, atom_answers={})
    return eval_predicate(when, ctx).value


def _has_non_json_ground(node: dict[str, Any] | None) -> bool:
    if not node:
        return False
    op = str(node.get("op") or "")
    if op in ("atom", "vision"):
        return True
    if op in ("all_of", "any_of"):
        return any(_has_non_json_ground(item) for item in (node.get("items") or []))
    if op == "not":
        return _has_non_json_ground(node.get("item"))
    return str(node.get("ground") or "json") != "json"


def leaves_for_extraction(
    spec: dict[str, Any] | ObligationSpec,
    facts: dict[str, Any],
    *,
    semantic: SemanticReport | None = None,
) -> list[dict[str, Any]]:
    """Return atom/vision leaves whose WHEN clause is satisfied (or unknown)."""
    applies = when_applies_json_only(spec, facts, semantic=semantic)
    if applies is False:
        return []
    data = spec.to_dict() if isinstance(spec, ObligationSpec) else spec
    where_bindings = list(data.get("where_bindings") or [])
    out: list[dict[str, Any]] = []
    for leaf in collect_all_leaves(spec):
        if leaf.get("op") not in ("atom", "vision"):
            continue
        requires = list(leaf.get("requires_fields") or where_bindings)
        if requires:
            resolved = resolve_where_bindings(requires, facts, semantic)
            if not any(not _is_blank_value(rf.value) for rf in resolved):
                continue
        out.append(leaf)
    return out
