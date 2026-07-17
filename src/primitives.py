"""Closed predicate/obligation vocabulary — reusable kernels, not checkpoint-specific."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from fact_extractor import AtomAnswer
from fact_schema import (
    ResolvedField,
    _is_blank_value,
    resolve_where_bindings,
    resolve_selector,
)
from semantic_report import SemanticReport

MATCH_CLEAR = "clear_match"
MATCH_CLEAR_UNMATCH = "clear_unmatch"
MATCH_UNABLE = "unable_to_check"

PRIMITIVE_OPS = frozenset(
    {
        "equals",
        "in_set",
        "matches",
        "contains",
        "contains_number",
        "no_language",
        "compare",
        "exists",
        "is_blank",
        "count_at_most",
        "count_at_least",
        "ratio_at_least",
        "filename_matches",
        "all_of",
        "any_of",
        "not",
        "atom",
        "vision",
        "true",
        "false",
    }
)

_SINGLE_VALUE_OPS = frozenset(
    {
        "equals",
        "in_set",
        "matches",
        "contains",
        "contains_number",
        "no_language",
        "count_at_most",
        "count_at_least",
        "filename_matches",
    }
)


def _resolved_from_node(node: dict[str, Any], ctx: EvalContext) -> list[ResolvedField]:
    binding = node.get("binding")
    if binding:
        return resolve_where_bindings([binding], ctx.facts, ctx.semantic)
    selector = str(node.get("selector") or "")
    if not selector:
        return []
    return resolve_where_bindings([selector], ctx.facts, ctx.semantic)


def _requires_fields_resolved(node: dict[str, Any], ctx: EvalContext) -> bool:
    requires = node.get("requires_fields") or []
    if not requires:
        return True
    resolved = resolve_where_bindings(requires, ctx.facts, ctx.semantic)
    return any(not _is_blank_value(rf.value) for rf in resolved)


_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


@dataclass
class EvalResult:
    value: bool | None
    evidence: str = ""
    source: str = "json"


@dataclass
class EvalContext:
    facts: dict[str, Any]
    semantic: SemanticReport | None = None
    atom_answers: dict[str, AtomAnswer] | None = None


def _norm_text(value: Any) -> str:
    return str(value or "").strip().upper()


def _bool_atom(answer: AtomAnswer | None) -> bool | None:
    if answer is None or answer.value is None:
        return None
    if isinstance(answer.value, bool):
        return answer.value
    text = str(answer.value).strip().lower()
    if text in ("true", "yes", "1"):
        return True
    if text in ("false", "no", "0"):
        return False
    return None


def _infer_style_number(ctx: EvalContext) -> str:
    for key in ctx.facts:
        if not key.startswith("summary.quantities."):
            continue
        head = key.split(".", 3)[2] if key.count(".") >= 2 else ""
        match = re.search(r"(\d{5,7})", head)
        if match:
            return match.group(1)
    return ""


def eval_predicate(node: dict[str, Any], ctx: EvalContext) -> EvalResult:
    """Evaluate one predicate node. None value means unknown / unable."""
    op = str(node.get("op") or "")
    if op not in PRIMITIVE_OPS:
        return EvalResult(None, f"unknown op {op}", "primitive:unknown")

    if op == "true":
        return EvalResult(True, "true", "primitive:true")
    if op == "false":
        return EvalResult(False, "false", "primitive:false")

    if op == "atom":
        atom_id = str(node.get("id") or "")
        if not _requires_fields_resolved(node, ctx):
            return EvalResult(None, "bound field missing", f"atom:{atom_id}:unresolved")
        answers = ctx.atom_answers or {}
        answer = answers.get(atom_id)
        role = str(node.get("role") or "boolean")
        # Quote atoms: extraction only — a following deterministic op decides.
        # Gate: missing/null quote => unable; otherwise pass (True) so all_of continues.
        if role == "quote":
            raw = None if answer is None else answer.value
            text = "" if raw is None else str(raw).strip()
            if not text or text.lower() in {"null", "none", "n/a", "na"}:
                return EvalResult(
                    None,
                    answer.evidence if answer else "quote missing",
                    f"atom:{atom_id}:quote",
                )
            return EvalResult(True, str(answer.evidence or text)[:300], f"atom:{atom_id}:quote")
        val = _bool_atom(answer)
        if val is None:
            return EvalResult(None, answer.evidence if answer else "", f"atom:{atom_id}")
        if role == "violation":
            # violation atom true => obligation fails (predicate false for THEN)
            return EvalResult(not val, answer.evidence if answer else "", f"atom:{atom_id}:violation")
        if role == "excuse":
            return EvalResult(val, answer.evidence if answer else "", f"atom:{atom_id}:excuse")
        if role == "required_true":
            return EvalResult(val, answer.evidence if answer else "", f"atom:{atom_id}:required")
        return EvalResult(val, answer.evidence if answer else "", f"atom:{atom_id}")

    if op == "vision":
        vision_id = str(node.get("id") or "")
        if not _requires_fields_resolved(node, ctx):
            return EvalResult(None, "bound field missing", f"vision:{vision_id}:unresolved")
        answer = (ctx.atom_answers or {}).get(vision_id)
        if answer is None:
            return EvalResult(
                None,
                "Vision leaf not evaluated (no photo answers).",
                f"vision:{vision_id}",
            )
        val = _bool_atom(answer)
        if val is None:
            return EvalResult(None, answer.evidence, f"vision:{vision_id}")
        # Vision question is phrased as "does content satisfy?" — true means obligation ok.
        return EvalResult(val, answer.evidence, f"vision:{vision_id}")

    if op in ("all_of", "any_of"):
        items = node.get("items") or []
        if not items:
            return EvalResult(True if op == "all_of" else False, "empty", f"primitive:{op}")
        results = [eval_predicate(item, ctx) for item in items]
        values = [r.value for r in results]
        evidence = "; ".join(r.evidence for r in results if r.evidence)[:300]
        if op == "any_of":
            if any(v is True for v in values):
                return EvalResult(True, evidence, "primitive:any_of")
            if any(v is None for v in values):
                return EvalResult(None, evidence, "primitive:any_of:unknown")
            return EvalResult(False, evidence, "primitive:any_of")
        # all_of
        if any(v is False for v in values):
            return EvalResult(False, evidence, "primitive:all_of")
        if any(v is None for v in values):
            return EvalResult(None, evidence, "primitive:all_of:unknown")
        return EvalResult(True, evidence, "primitive:all_of")

    if op == "not":
        inner = eval_predicate(node.get("item") or {}, ctx)
        if inner.value is None:
            return EvalResult(None, inner.evidence, "primitive:not")
        return EvalResult(not inner.value, inner.evidence, "primitive:not")

    selector = str(node.get("selector") or "")
    binding = node.get("binding")
    if binding:
        resolved = _resolved_from_node(node, ctx)
        if not resolved:
            return EvalResult(None, "binding unresolved", f"primitive:{op}:unresolved")
        if len(resolved) > 1 and op in _SINGLE_VALUE_OPS:
            results = []
            for rf in resolved:
                child = {**node, "binding": None, "selector": rf.selector}
                results.append(eval_predicate(child, ctx))
            values = [r.value for r in results]
            evidence = "; ".join(r.evidence for r in results if r.evidence)[:300]
            if any(v is False for v in values):
                return EvalResult(False, evidence, f"primitive:{op}:all")
            if any(v is None for v in values):
                return EvalResult(None, evidence, f"primitive:{op}:unknown")
            return EvalResult(True, evidence, f"primitive:{op}:all")
        actual = resolved[0].value
        selector = resolved[0].selector or f"{resolved[0].kind}.{resolved[0].name}.{resolved[0].field}"
    else:
        actual = resolve_selector(selector, ctx.facts, ctx.semantic) if selector else None
    ground = str(node.get("ground") or "json")

    if ground == "atom":
        atom_id = str(node.get("id") or selector)
        return eval_predicate({"op": "atom", "id": atom_id, "role": node.get("role", "boolean")}, ctx)

    # Multi-selector ops resolve their own fields — don't early-exit on empty `selector`.
    if op in ("compare", "ratio_at_least"):
        pass
    elif actual is None and op not in ("is_blank", "exists"):
        return EvalResult(None, f"{selector}=missing", f"primitive:{op}:missing")

    if op == "equals":
        expected = node.get("expected")
        try:
            same = float(actual) == float(expected)
        except (TypeError, ValueError):
            same = _norm_text(actual) == _norm_text(expected)
        evidence = f"{selector}={actual}, expected={expected}"
        return EvalResult(same, evidence, "primitive:equals")

    if op == "in_set":
        options = {_norm_text(v) for v in (node.get("values") or [])}
        ok = _norm_text(actual) in options
        return EvalResult(ok, f"{selector}={actual}, in={sorted(options)}", "primitive:in_set")

    if op == "matches":
        pattern = str(node.get("pattern") or "")
        text = str(actual or "")
        ok = bool(re.search(pattern, text, re.I))
        return EvalResult(ok, f"{selector}={text[:120]}", "primitive:matches")

    if op == "contains":
        needle = str(node.get("text") or "").lower()
        hay = str(actual or "").lower()
        if isinstance(actual, list):
            hay = " ".join(str(v) for v in actual).lower()
        ok = needle in hay if needle else False
        return EvalResult(ok, f"{selector} contains '{needle}'", "primitive:contains")

    if op == "contains_number":
        text = str(actual or "")
        ok = bool(re.search(r"\d", text))
        return EvalResult(ok, f"{selector}={text[:120]}", "primitive:contains_number")

    if op == "no_language":
        language = str(node.get("language") or "chinese").lower()
        text = str(actual or "")
        if language == "chinese":
            ok = _CJK_RE.search(text) is None
        else:
            ok = language.lower() not in text.lower()
        return EvalResult(ok, f"{selector} has no {language} chars", "primitive:no_language")

    if op == "exists":
        if isinstance(actual, list):
            ok = len(actual) > 0
        else:
            ok = actual not in (None, "", [])
        return EvalResult(ok, f"{selector}={actual}", "primitive:exists")

    if op == "is_blank":
        if isinstance(actual, list):
            ok = len(actual) == 0
        else:
            ok = str(actual or "").strip() == ""
        return EvalResult(ok, f"{selector} blank={ok}", "primitive:is_blank")

    if op == "count_at_most":
        if isinstance(actual, list):
            count = len(actual)
        else:
            try:
                count = int(actual or 0)
            except (TypeError, ValueError):
                return EvalResult(None, f"{selector}={actual!r} not countable", "primitive:count_at_most")
        maximum = int(node.get("max", 0))
        ok = count <= maximum
        return EvalResult(ok, f"{selector}={count}, max={maximum}", "primitive:count_at_most")

    if op == "count_at_least":
        if isinstance(actual, list):
            count = len(actual)
        else:
            try:
                count = int(actual or 0)
            except (TypeError, ValueError):
                return EvalResult(None, f"{selector}={actual!r} not countable", "primitive:count_at_least")
        minimum = int(node.get("min", 1))
        ok = count >= minimum
        return EvalResult(ok, f"{selector}={count}, min={minimum}", "primitive:count_at_least")

    if op == "ratio_at_least":
        num_sel = str(node.get("numerator") or "")
        den_sel = str(node.get("denominator") or "")
        num = resolve_selector(num_sel, ctx.facts, ctx.semantic)
        den = resolve_selector(den_sel, ctx.facts, ctx.semantic)
        if num is None or den is None:
            return EvalResult(None, f"{num_sel}/{den_sel} missing", "primitive:ratio_at_least")
        try:
            ratio = float(num) / float(den)
        except (TypeError, ValueError, ZeroDivisionError):
            return EvalResult(None, f"{num}/{den} invalid", "primitive:ratio_at_least")
        minimum = float(node.get("min", 0))
        ok = ratio >= minimum
        return EvalResult(ok, f"{num}/{den}={ratio:.4f}, min={minimum}", "primitive:ratio_at_least")

    if op == "compare":
        # Two-selector mode: {left, right, cmp} OR constant mode: {selector, value, cmp}
        left_sel = str(node.get("left") or selector or "")
        right_sel = str(node.get("right") or "")
        cmp = str(node.get("cmp") or node.get("relation") or ">=")
        if right_sel:
            left_raw = resolve_selector(left_sel, ctx.facts, ctx.semantic)
            right_raw = resolve_selector(right_sel, ctx.facts, ctx.semantic)
        else:
            left_raw = actual
            right_raw = node.get("value")
        if left_raw is None or right_raw is None:
            return EvalResult(
                None,
                f"{left_sel}={left_raw}, right={right_sel or right_raw}",
                "primitive:compare:missing",
            )
        try:
            left_f = float(left_raw)
            right_f = float(right_raw)
            numeric = True
        except (TypeError, ValueError):
            left_f = left_raw
            right_f = right_raw
            numeric = False
        if numeric:
            ops = {
                ">=": left_f >= right_f,
                "<=": left_f <= right_f,
                ">": left_f > right_f,
                "<": left_f < right_f,
                "==": left_f == right_f,
                "!=": left_f != right_f,
                "=": left_f == right_f,
            }
            ok = bool(ops.get(cmp, left_f == right_f))
        else:
            ln = _norm_text(left_f)
            rn = _norm_text(right_f)
            if cmp in ("!=", "<>"):
                ok = ln != rn
            else:
                ok = ln == rn
        evidence = f"{left_sel}={left_raw} {cmp} {right_sel or right_raw}"
        return EvalResult(ok, evidence, "primitive:compare")

    if op == "filename_matches":
        raw = actual
        if isinstance(raw, list):
            filenames = raw
        elif isinstance(raw, str) and raw.strip():
            filenames = [raw.strip()]
        else:
            filenames = []
        if not filenames:
            return EvalResult(None, "no filenames", "primitive:filename_matches")
        style = str(node.get("style_number") or _infer_style_number(ctx) or "")
        pattern = str(node.get("pattern") or "Measurement Chart-{style}.xlsx")
        expected = pattern.replace("{style}", style)
        actual_name = str(filenames[0])
        norm_a = actual_name.lower().replace(" ", "").replace("_", "-")
        norm_e = expected.lower().replace(" ", "").replace("_", "-")
        if norm_a == norm_e:
            return EvalResult(True, f"filename={actual_name}", "primitive:filename_matches")
        wrong_template = "chart-format" in actual_name.lower() or "chart_format" in actual_name.lower()
        if style and style in actual_name and wrong_template:
            return EvalResult(
                False,
                f"filename={actual_name}, expected={expected}",
                "primitive:filename_matches",
            )
        if style and style not in actual_name:
            return EvalResult(False, f"missing style {style}", "primitive:filename_matches")
        if wrong_template:
            return EvalResult(
                False,
                f"wrong template: {actual_name}",
                "primitive:filename_matches",
            )
        return EvalResult(True, f"filename={actual_name}", "primitive:filename_matches")

    return EvalResult(None, f"unhandled {op}", "primitive:unhandled")
