"""Convert parsed Markdown rules into gi_review checkpoint payloads."""

from __future__ import annotations

import re
from typing import Any

from check_block import extract_check_blocks


def slug(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "general"


def compact_lines(*values: object) -> list[str]:
    lines: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        for line in re.split(r"\n+", text):
            line = line.strip(" -")
            if line:
                lines.append(line)
    return lines


def scope_from_rule(rule: dict[str, Any]) -> tuple[str, str]:
    scope = rule.get("scope")
    if isinstance(scope, dict):
        level = str(scope.get("level") or "FULL REPORT").strip().upper()
        detail = str(scope.get("detail") or "").strip()
        return level, detail
    raw = str(scope or "").strip()
    if not raw:
        return "FULL REPORT", ""
    match = re.match(r"`?([A-Z ]+)`?\s*(?:[—-]\s*)?(.*)", raw, re.DOTALL)
    if match:
        return match.group(1).strip().upper(), match.group(2).strip()
    return raw.upper(), ""


def severity_from_rule(rule: dict[str, Any]) -> str:
    raw = str(rule.get("severity") or "BLOCKING").strip().upper()
    if raw in ("MINOR", "TO_CONFIRM"):
        return raw
    return "BLOCKING"


def rule_to_checkpoint(
    rule: dict[str, Any],
    *,
    check_blocks: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rule_id = str(rule.get("id") or "").strip() or f"rule.{rule.get('source_lines', {}).get('start', 'unknown')}"
    cp_id = slug(rule_id)
    requirement_bits = compact_lines(rule.get("field_location"), rule.get("what_to_check"))
    requirement = " — ".join(requirement_bits) or str(rule.get("additional_markdown", "")).strip()
    scope_type, scope_detail = scope_from_rule(rule)
    context = f"{scope_type} — {scope_detail}".strip(" —") if scope_detail else scope_type

    checkpoint: dict[str, Any] = {
        "id": cp_id,
        "section": slug(rule.get("section") or rule.get("subsection") or "rules"),
        "requirement": requirement,
        "severity": severity_from_rule(rule),
        "scope_type": scope_type,
        "scope_detail": scope_detail,
        "source_rule_id": rule_id,
        "source_lines": rule.get("source_lines", {}),
        "context": context,
    }
    if check_blocks and cp_id in check_blocks:
        checkpoint["check_block"] = check_blocks[cp_id]
    return checkpoint


def rules_to_checkpoints(
    rules: list[dict[str, Any]],
    *,
    markdown: str | None = None,
    check_blocks: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    blocks = check_blocks
    if blocks is None and markdown:
        blocks = extract_check_blocks(markdown)
    return [rule_to_checkpoint(rule, check_blocks=blocks) for rule in rules]
