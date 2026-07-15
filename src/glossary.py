"""Match shared glossary terms into checkpoint prompts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _default_glossary_path() -> Path:
    from clients import project_root

    return project_root() / "data" / "glossary.json"


def load_glossary(path: Path | None = None) -> dict[str, str]:
    glossary_path = path or _default_glossary_path()
    raw: dict[str, Any] = json.loads(glossary_path.read_text(encoding="utf-8"))
    return {str(term): str(defn).strip() for term, defn in raw.items() if str(defn).strip()}


def _checkpoint_text(checkpoint: dict[str, Any]) -> str:
    parts = [
        checkpoint.get("requirement", ""),
        checkpoint.get("context", ""),
        checkpoint.get("lookup_table", ""),
        " ".join(checkpoint.get("fail_if") or []),
        " ".join(checkpoint.get("never_flag_if") or []),
    ]
    examples = checkpoint.get("examples") or {}
    for key in ("pass", "fail"):
        parts.append(" ".join(examples.get(key) or []))
    return " ".join(str(part) for part in parts if part)


def match_terms(text: str, glossary: dict[str, str]) -> dict[str, str]:
    """Return glossary entries whose term appears in text (longest terms first)."""
    lowered = text.lower()
    matched: dict[str, str] = {}
    for term in sorted(glossary, key=len, reverse=True):
        pattern = re.escape(term)
        if re.search(pattern, text, flags=re.IGNORECASE) or term.lower() in lowered:
            matched[term] = glossary[term]
    return matched


def matched_glossary_for_checkpoint(
    checkpoint: dict[str, Any],
    glossary: dict[str, str],
) -> dict[str, str]:
    return match_terms(_checkpoint_text(checkpoint), glossary)


def format_glossary_block(matched: dict[str, str]) -> str:
    if not matched:
        return ""
    lines = ["Glossary (matched terms):"]
    for term, definition in matched.items():
        lines.append(f"- {term}: {definition}")
    return "\n".join(lines)
