"""Extract focused slices from inspection report markdown for scoped checkpoints."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_HEADER_RE = re.compile(r"^(#{2,4})\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ReportBlock:
    level: int
    title: str
    text: str


def split_report_blocks(report_md: str) -> list[ReportBlock]:
    """Split markdown into ## / ### / #### blocks with their body text."""
    matches = list(_HEADER_RE.finditer(report_md))
    if not matches:
        return []

    blocks: list[ReportBlock] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report_md)
        title = match.group(2).split(" — ", 1)[0].strip()
        blocks.append(
            ReportBlock(
                level=len(match.group(1)),
                title=title,
                text=report_md[match.start() : end].strip(),
            )
        )
    return blocks


_GENERIC_FOCUS_TERMS = {
    "report photos",
    "report photo",
    "inspector's remark",
    "checklist",
    "report",
    "photos",
}


def _normalize_terms(terms: list[str]) -> list[str]:
    out: list[str] = []
    for term in terms:
        cleaned = re.sub(r"\s+", " ", term.strip().lower())
        if len(cleaned) >= 4 and cleaned not in _GENERIC_FOCUS_TERMS:
            out.append(cleaned)
    return list(dict.fromkeys(out))


def _block_contains_term(block: ReportBlock, term: str) -> bool:
    return term in block.title.lower() or term in block.text.lower()


def _ranked_terms(terms: list[str]) -> list[str]:
    return sorted(terms, key=len, reverse=True)


def _matching_blocks(blocks: list[ReportBlock], terms: list[str], section_hints: list[str]) -> list[ReportBlock]:
    ranked = _ranked_terms(terms)

    # Prefer checklist subsections (### / ####) that contain the focus phrase.
    deep_blocks = [block for block in blocks if block.level >= 3]
    for term in ranked:
        if len(term) < 6:
            continue
        matched = [block for block in deep_blocks if _block_contains_term(block, term)]
        if matched:
            return matched

    # Exact ## section title from md_sections hints.
    for block in blocks:
        if block.level != 2:
            continue
        if any(hint.lower() == block.title.lower() for hint in section_hints):
            return [block]

    # Broader title match on longer focus terms only.
    for term in ranked:
        if len(term) < 8:
            continue
        matched = [block for block in blocks if term in block.title.lower()]
        if matched:
            return matched

    return []


def _narrow_to_matching_lines(section_text: str, terms: list[str], *, window: int = 3) -> str:
    if not terms:
        return section_text

    lines = section_text.splitlines()
    picked: list[str] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        line_lower = line.lower()
        if not any(term in line_lower for term in terms):
            continue
        start = max(0, index - window)
        end = min(len(lines), index + window + 1)
        for snippet_line in lines[start:end]:
            if snippet_line not in seen:
                seen.add(snippet_line)
                picked.append(snippet_line)

    return "\n".join(picked)


def extract_focus_slice(report_md: str, checkpoint: dict[str, Any]) -> str:
    """Return a focused markdown slice for QUESTION / SECTION scoped checkpoints."""
    scope_type = str(checkpoint.get("scope_type") or "FULL REPORT").upper()
    if scope_type == "FULL REPORT":
        return ""

    terms = _normalize_terms(list(checkpoint.get("focus_terms") or []))
    section_hints = list(checkpoint.get("md_sections") or [])
    blocks = split_report_blocks(report_md)
    if not blocks:
        return ""

    matched_blocks = _matching_blocks(blocks, terms, section_hints)
    if not matched_blocks and terms:
        # Last resort: scan line-by-line across the full report for the focus term.
        narrowed = _narrow_to_matching_lines(report_md, terms, window=4)
        if narrowed:
            return f"## Report focus\n{narrowed}"

    if scope_type == "SECTION":
        if not matched_blocks:
            return ""
        return "\n\n".join(block.text for block in matched_blocks)

    # QUESTION — section body narrowed to matching checklist rows / guidance.
    slices: list[str] = []
    for block in matched_blocks:
        narrowed = _narrow_to_matching_lines(block.text, terms, window=3)
        slices.append(narrowed or block.text)
    return "\n\n".join(slices)
