"""Convert parsed Markdown rules into gi_review checkpoint payloads."""

from __future__ import annotations

import re
from typing import Any


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


def focus_terms_from_rule(rule: dict[str, Any], scope_detail: str) -> list[str]:
    terms: list[str] = []
    for chunk in re.split(r"[/—]", str(rule.get("field_location") or "")):
        chunk = chunk.strip()
        if len(chunk) >= 4:
            terms.append(chunk)

    for source in (scope_detail, str(rule.get("what_to_check") or "")):
        lowered = source.lower()
        for pattern in (
            r"check(?: the)?\s+(.+?)\s+(?:field|section|checkpoint|result)",
            r"within the\s+(.+?)\s+section",
            r"in the\s+(.+?)\s+section",
        ):
            match = re.search(pattern, lowered)
            if match:
                terms.append(match.group(1).strip())

    return list(dict.fromkeys(terms))[:6]


def checklist_hints_from_rule(rule: dict[str, Any]) -> list[str]:
    """Extract checklist/section names from field_location (client-agnostic)."""
    hints: list[str] = []
    field = str(rule.get("field_location") or "")
    for part in re.split(r"[/—]", field):
        part = part.strip()
        if not part or part.lower().startswith("report "):
            continue
        if "checklist" in part.lower():
            name = re.sub(r"\s*checklist.*$", "", part, flags=re.I).strip()
            if name:
                hints.append(name)
        elif len(part) >= 8:
            hints.append(part)
    return list(dict.fromkeys(hints))[:4]


def infer_md_sections(rule: dict[str, Any], scope_detail: str = "") -> list[str]:
    text = " ".join(
        str(rule.get(key, ""))
        for key in ("section", "subsection", "field_location", "what_to_check", "additional_markdown")
    ).lower()
    detail = scope_detail.lower()
    sections: list[str] = list(checklist_hints_from_rule(rule))

    if any(term in text for term in ("supplier", "factory", "address", "location", "inspector")):
        sections.append("Parties & Location")
    if any(term in text for term in ("product", "sku", "po", "quantity", "carton", "batch", "date code")):
        sections.extend(["Executive Summary", "Products & Quantities", "Additional Fields"])
    if "available quantity" in detail or ("quantity" in detail and "available" in text):
        sections.append("Checklist Sections")
    if any(term in text for term in ("aql", "sampling", "defect", "critical", "major", "minor")):
        sections.extend(["AQL & Sampling", "Checklist Sections", "Attention Items (read first)"])
    if any(term in text for term in ("photo", "picture", "image", "barcode", "label")):
        sections.extend(["Checklist Sections", "Attention Items (read first)"])
    if "workmanship" in detail or "defect" in detail:
        sections.append("Checklist Sections")
    if "product dimensions" in detail or "measurement" in text:
        sections.append("Checklist Sections")
    if "starting picture" in detail:
        sections.append("Starting pictures")

    if not sections:
        sections = [
            "Executive Summary",
            "Additional Fields",
            "Checklist Sections",
            "Attention Items (read first)",
        ]
    return list(dict.fromkeys(sections))


def table_to_markdown(table: dict[str, Any]) -> str:
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    if not headers:
        return ""

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def lookup_table_from_rule(rule: dict[str, Any]) -> str:
    tables = rule.get("tables") or []
    rendered = [table_to_markdown(table) for table in tables]
    rendered = [table for table in rendered if table]
    if rendered:
        return "\n\n".join(rendered)

    extra = str(rule.get("additional_markdown") or "").strip()
    if extra.startswith("|"):
        return extra
    return ""


def never_flag_if_from_rule(rule: dict[str, Any]) -> list[str]:
    raw = rule.get("never_flag_if")
    if isinstance(raw, list):
        return compact_lines(*raw)
    if isinstance(raw, str):
        return compact_lines(raw)
    return []


def infer_never_flag_if(rule: dict[str, Any]) -> list[str]:
    """Derive guardrails from rule wording — same logic for any GI rules document."""
    inferred: list[str] = []
    what = str(rule.get("what_to_check") or "")
    field = str(rule.get("field_location") or "")

    if_match = re.match(r"If\s+(.+?),\s", what, flags=re.IGNORECASE)
    if if_match:
        condition = if_match.group(1).strip()
        inferred.append(f"{condition} is not identified or mentioned in the report")

    only_match = re.search(r"([\w][\w\s]*?)\s+only\b", field, flags=re.IGNORECASE)
    if only_match:
        scope = only_match.group(1).strip()
        inferred.append(f"Report context does not match '{scope}' — rule is not applicable")

    unless_match = re.search(r"\bunless\s+(.+?)(?:\.|$)", what, flags=re.IGNORECASE)
    if unless_match:
        exception = unless_match.group(1).strip()
        inferred.append(f"Exception condition is met: unless {exception}")

    return inferred


def severity_from_rule(rule: dict[str, Any]) -> str:
    raw = str(rule.get("severity") or "BLOCKING").strip().upper()
    if raw in ("MINOR", "TO_CONFIRM"):
        return raw
    return "BLOCKING"


def photo_check_from_rule(rule: dict[str, Any]) -> str | None:
    """Classify photo rules: metadata (counts/result) vs content (needs vision)."""
    text = " ".join(
        str(rule.get(key) or "")
        for key in ("field_location", "what_to_check", "error_example", "correct_example")
    ).lower()
    if not any(term in text for term in ("photo", "picture", "image", "caption")):
        return None

    metadata_signals = (
        "must not be included",
        "only include if",
        "only 1 photo",
        "1 photo per",
        "photos uploaded",
        "do not upload multiple",
        "number of photos",
        "photos are uploaded",
        "more than 1 photo",
        "more than one photo",
        "exactly 1 photo",
    )
    content_signals = (
        "tape measure",
        "scale reading",
        "measuring the boxes",
        "measuring boxes",
        "photo content",
        "what the photo shows",
        "side by side",
        "identifying which is which",
        "cartons stacked on pallets",
        "carton seals",
        "labelling on the side",
        "captions describing",
    )
    if any(signal in text for signal in content_signals):
        return "content"
    if any(signal in text for signal in metadata_signals):
        return "metadata"
    return "content"


def fail_if_from_rule(rule: dict[str, Any], *, has_lookup_table: bool) -> list[str]:
    fail_if = compact_lines(rule.get("error_example"))
    if rule.get("what_to_check") and not has_lookup_table:
        fail_if.append(f"Report does not satisfy: {rule['what_to_check']}")
    if not fail_if:
        fail_if.append("Report evidence conflicts with this rule")
    return fail_if


def rule_to_checkpoint(rule: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(rule.get("id") or "").strip() or f"rule.{rule.get('source_lines', {}).get('start', 'unknown')}"
    requirement_bits = compact_lines(rule.get("field_location"), rule.get("what_to_check"))
    requirement = " — ".join(requirement_bits) or str(rule.get("additional_markdown", "")).strip()

    scope_type, scope_detail = scope_from_rule(rule)
    lookup_table = lookup_table_from_rule(rule)
    never_flag_if = list(
        dict.fromkeys([*never_flag_if_from_rule(rule), *infer_never_flag_if(rule)])
    )
    fail_if = fail_if_from_rule(rule, has_lookup_table=bool(lookup_table))
    focus_terms = focus_terms_from_rule(rule, scope_detail)

    examples: dict[str, list[str]] = {}
    pass_examples = compact_lines(rule.get("correct_example"))
    fail_examples = compact_lines(rule.get("error_example"))
    if pass_examples:
        examples["pass"] = pass_examples
    if fail_examples:
        examples["fail"] = fail_examples

    context = f"{scope_type} — {scope_detail}".strip(" —") if scope_detail else scope_type

    checkpoint: dict[str, Any] = {
        "id": slug(rule_id),
        "section": slug(rule.get("section") or rule.get("subsection") or "rules"),
        "requirement": requirement,
        "severity": severity_from_rule(rule),
        "scope_type": scope_type,
        "scope_detail": scope_detail,
        "focus_terms": focus_terms,
        "md_sections": infer_md_sections(rule, scope_detail),
        "fail_if": fail_if,
        "source_rule_id": rule_id,
        "source_lines": rule.get("source_lines", {}),
        "context": context,
    }
    if lookup_table:
        checkpoint["lookup_table"] = lookup_table
    if never_flag_if:
        checkpoint["never_flag_if"] = never_flag_if
    if examples:
        checkpoint["examples"] = examples
    photo_check = photo_check_from_rule(rule)
    if photo_check:
        checkpoint["photo_check"] = photo_check
    return checkpoint


def rules_to_checkpoints(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [rule_to_checkpoint(rule) for rule in rules]
