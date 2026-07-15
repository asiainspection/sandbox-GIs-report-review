"""
Deterministic checks that run on the report IR *before* any LLM call.

The idea (and why it scales)
----------------------------
We do NOT write code per checkpoint. We write a small set of *primitives* that
read typed IR fields. A checkpoint declares which primitive applies via fields
it already carries (e.g. `photo_check: "content"`), so thousands of checkpoints
across different GIs reuse the same handful of functions.

Each primitive returns a `Verdict` (a match level + grounded evidence pulled
from the IR) or `None` to mean "no deterministic answer — defer to the LLM".

Match levels mirror `gi_review`:
    clear_match | partial_unmatch | clear_unmatch | unable_to_check

Currently implemented primitive:
- photo_content: a rule that needs to judge what a photo *shows* cannot be
  answered from metadata. Return `unable_to_check` (grounded with the photo
  count / applicability of the bound nodes) instead of letting the model invent
  a text-based violation. This fixes the 3_1_3 class of errors for every client.

To add a primitive later (e.g. photo_count, enum_equals, cross_field_equals),
write one function with the same signature and append it to `PRIMITIVES`.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from report_to_ir import render_context

# Match levels — kept as literals so this module has no heavy dependencies.
MATCH_CLEAR = "clear_match"
MATCH_PARTIAL = "partial_unmatch"
MATCH_CLEAR_UNMATCH = "clear_unmatch"
MATCH_UNABLE = "unable_to_check"

Verdict = dict[str, Any]
Primitive = Callable[[dict[str, Any], dict[str, Any]], Optional[Verdict]]

_MIN_TERM_LEN = 4


def _clean_terms(raw: list[str]) -> list[str]:
    terms = [str(t).strip().lower() for t in raw]
    terms = [t for t in terms if len(t) >= _MIN_TERM_LEN]
    return list(dict.fromkeys(terms))


def _binding_terms(checkpoint: dict[str, Any]) -> list[str]:
    """Tight terms (focus_terms only) — used by primitives to cite precise evidence."""
    return _clean_terms(list(checkpoint.get("focus_terms") or []))


def _context_terms(checkpoint: dict[str, Any]) -> list[str]:
    """Broader terms for locating LLM context: focus_terms + section + md_sections.

    Generic hints (e.g. "Executive Summary") simply won't match a node and are
    ignored, so no per-checkpoint code is needed.
    """
    raw: list[str] = list(checkpoint.get("focus_terms") or [])
    if checkpoint.get("section"):
        raw.append(str(checkpoint["section"]))
    raw.extend(checkpoint.get("md_sections") or [])
    return _clean_terms(raw)


def find_nodes(ir: dict[str, Any], terms: list[str]) -> list[dict[str, Any]]:
    """Best-effort deterministic binding: nodes whose path/section contains a term.

    Uses substring match first, then Jaccard token overlap for longer terms.
    """
    if not terms:
        return []
    matched: list[dict[str, Any]] = []
    seen: set[int] = set()
    for node in ir.get("nodes", []):
        haystack = f"{node.get('path', '')} {node.get('section', '')} {node.get('name', '')}".lower()
        hit = False
        for term in terms:
            t = term.lower().strip()
            if len(t) < 3:
                continue
            if t in haystack:
                hit = True
                break
            # token overlap for multi-word terms
            t_tokens = {x for x in re.sub(r"[^a-z0-9]+", " ", t).split() if len(x) > 1}
            h_tokens = {x for x in re.sub(r"[^a-z0-9]+", " ", haystack).split() if len(x) > 1}
            if t_tokens and h_tokens:
                score = len(t_tokens & h_tokens) / len(t_tokens | h_tokens)
                if score >= 0.5:
                    hit = True
                    break
        if hit:
            nid = id(node)
            if nid not in seen:
                seen.add(nid)
                matched.append(node)
    return matched


def _photo_evidence(nodes: list[dict[str, Any]]) -> str:
    if not nodes:
        return "No matching photo node located in the report IR."
    parts: list[str] = []
    for node in nodes[:4]:
        photos = node.get("photos") or {}
        captions = photos.get("captions") or []
        parts.append(
            f"'{node.get('name')}': applicable={node.get('applicable')}, "
            f"result={node.get('result')}, photos={photos.get('count', 0)}, "
            f"captions={captions if captions else '[]'}"
        )
    return " | ".join(parts)


def photo_content_primitive(checkpoint: dict[str, Any], ir: dict[str, Any]) -> Optional[Verdict]:
    """Photo rules needing visual judgment can't be answered from metadata."""
    if checkpoint.get("photo_check") != "content":
        return None
    nodes = find_nodes(ir, _binding_terms(checkpoint))
    return {
        "match": MATCH_UNABLE,
        "reason": (
            "This rule requires judging the content of a photo, which cannot be "
            "verified from report metadata (only a vision model can). Not flagged."
        ),
        "evidence": _photo_evidence(nodes),
        "source": "deterministic:photo_content",
    }


PRIMITIVES: list[Primitive] = [
    photo_content_primitive,
]


def build_checkpoint_context(checkpoint: dict[str, Any], ir: dict[str, Any]) -> str:
    """Compact per-checkpoint evidence from the IR (replaces the full cached report).

    Scoped checks (QUESTION/SECTION) get only the bound nodes; FULL REPORT checks
    get every node. Report facts + summary are always included so cross-report
    checks (AQL, quantities, instructions) keep their evidence. If binding finds
    nothing, we fall back to all nodes rather than risk dropping evidence.
    """
    scope = str(checkpoint.get("scope_type") or "FULL REPORT").upper()
    all_nodes = ir.get("nodes", [])
    scoped = scope in ("QUESTION", "SECTION")
    if scoped:
        bound = find_nodes(ir, _context_terms(checkpoint))
        # Fall back to full context if binding found nothing (don't drop evidence).
        if bound:
            return render_context(ir, bound, include_summary=False)
    return render_context(ir, all_nodes, include_summary=True)


def deterministic_verdict(checkpoint: dict[str, Any], ir: dict[str, Any]) -> Optional[Verdict]:
    """Return the first deterministic verdict for this checkpoint, or None.

    `None` means no primitive applied and the checkpoint should go to the LLM.
    """
    for primitive in PRIMITIVES:
        verdict = primitive(checkpoint, ir)
        if verdict is not None:
            return verdict
    return None
