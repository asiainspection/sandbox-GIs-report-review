"""Symbolic evaluation: atom truth values → match level. Python decides — never the LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from fact_extractor import AtomAnswer

MATCH_CLEAR = "clear_match"
MATCH_CLEAR_UNMATCH = "clear_unmatch"
MATCH_UNABLE = "unable_to_check"

TierName = Literal["operator", "atoms", "vision"]


@dataclass
class SymbolicVerdict:
    match: str
    reason: str
    evidence: str
    source: str = "symbolic"


def _bool_value(answer: AtomAnswer | None) -> bool | None:
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


def evaluate_atoms(
    checkpoint_id: str,
    atoms: list[dict[str, Any]],
    answers: dict[str, AtomAnswer],
    *,
    confidence_threshold: float = 0.0,
) -> SymbolicVerdict:
    """Apply PolicyGuard-style logic: violation atom + optional excuse atoms."""
    _ = confidence_threshold
    violation_id = f"{checkpoint_id}_violation"
    violation = answers.get(violation_id)
    v_val = _bool_value(violation)

    excuse_ids = [a["id"] for a in atoms if str(a["id"]).startswith(f"{checkpoint_id}_excuse_")]
    excuse_hits: list[str] = []
    for eid in excuse_ids:
        ans = answers.get(eid)
        if ans and _bool_value(ans) is True:
            excuse_hits.append(eid)

    if excuse_hits:
        ev = "; ".join(
            f"{eid}: {answers[eid].evidence[:120]}" for eid in excuse_hits if answers.get(eid)
        )
        return SymbolicVerdict(
            match=MATCH_CLEAR,
            reason="A never-flag condition applies; requirement not violated.",
            evidence=ev,
            source="symbolic:excuse",
        )

    if violation is None or v_val is None:
        return SymbolicVerdict(
            match=MATCH_UNABLE,
            reason="Insufficient evidence to determine whether the requirement is violated.",
            evidence=violation.evidence if violation else "",
            source="symbolic:unknown",
        )

    if v_val is True:
        return SymbolicVerdict(
            match=MATCH_CLEAR_UNMATCH,
            reason="Report evidence explicitly supports a violation of this requirement.",
            evidence=violation.evidence,
            source="symbolic:violation",
        )

    return SymbolicVerdict(
        match=MATCH_CLEAR,
        reason="No explicit violation found in report evidence.",
        evidence=violation.evidence,
        source="symbolic:clear",
    )


def vision_verdict(checkpoint_id: str, *, evidence: str = "") -> SymbolicVerdict:
    return SymbolicVerdict(
        match=MATCH_UNABLE,
        reason=(
            "This rule requires judging photo content; text/metadata extraction cannot "
            "verify it (vision tier not run)."
        ),
        evidence=evidence,
        source="symbolic:vision_deferred",
    )
