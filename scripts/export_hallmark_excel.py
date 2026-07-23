#!/usr/bin/env python3
"""Export Ribkoff rules.md → ops Excel with Condition rows for Applies when.

Legacy free-text `when:` lines are converted into Condition (hidden) rows + @C refs
so the spreadsheet matches the production authoring contract.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from build_gi_authoring_excel import CHECK_PARTS, build_workbook  # noqa: E402
from harness_rules import _FIELD_RE, is_structured_when  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/clients/hallmark/gi_authoring_hallmark.xlsx"

ACTION_MAP = {
    "manual review": "Manual review",
    "is present": "Must be filled in",
    "is in English": "Must be in English",
    "equals": "Must equal",
    "is one of": "Must be one of",
    "contains phrase": "Must contain text",
    "matches pattern": "Matches pattern",
    "at least N photos": "At least N",
    "at most N photos": "At most N",
    "ratio at least": "Ratio at least",
    "filename matches": "File name matches",
    "term must not appear": "Must not contain text",
    "LLM quote then match": "AI document check",
    "LLM yes/no": "AI yes/no (flag if false)",
    "needs vision": "AI photo check (flag if false)",
    "number greater than": "Number greater than",
    "number less than": "Number less than",
    "defect type includes": "Defect type includes",
}


def parse_with_section(markdown_text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current = None
    section = ""
    for line in markdown_text.splitlines():
        line = line.rstrip()
        m_heading = re.match(r"^##\s+(.+)$", line)
        if m_heading:
            title = m_heading.group(1).strip()
            if not title.lower().startswith("part "):
                section = title
        
        # Also capture field/location and what to check for hallmark rules
        if line.startswith("**ID:**"):
            if current:
                blocks.append(current)
            val = line.split("**ID:**")[1].strip()
            current = {"id": val, "section": section}
        elif current is not None:
            if line.startswith("**Field / Location:**"):
                current["where"] = line.split("**Field / Location:**")[1].strip()
            elif line.startswith("**What to check:**"):
                # Fake an action for now, we'll try to guess it later or just put manual review
                current["action"] = "manual review"
                current["example"] = line.split("**What to check:**")[1].strip()
            elif line.startswith("**Scope:**"):
                current["scope"] = line.split("**Scope:**")[1].strip()
            elif line.startswith("**Error example:**"):
                current["error_example"] = line.split("**Error example:**")[1].strip()
            elif line.startswith("**Correct example:**"):
                current["correct_example"] = line.split("**Correct example:**")[1].strip()
                current["example"] = current.get("example", "") + f" | Wrong: {current['error_example']} | Right: {current['correct_example']}"
        else:
            m = _FIELD_RE.match(line.strip())
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if key == "id":
                    if current:
                        blocks.append(current)
                    current = {"id": val, "section": section}
                elif current is not None:
                    current[key] = val
    if current:
        blocks.append(current)
    return blocks


def split_where(where_raw: str) -> tuple[str, str]:
    look_at = where_raw
    check_part = ""
    for cp in CHECK_PARTS:
        if where_raw.endswith(" " + cp):
            look_at = where_raw[: -(len(cp) + 1)]
            check_part = cp
            break
    return look_at, check_part


def when_to_condition(when: str, where_raw: str, cond_id: str) -> dict[str, str] | None:
    """Map a legacy when phrase → one Condition row, or None if unmappable."""
    text = (when or "").strip()
    if not text:
        return None
    if text.startswith("@"):
        return None  # already linked
    if is_structured_when(text):
        # Split structured when into Condition columns.
        body = re.sub(r"^when\s+", "", text, flags=re.I).strip()
        for phrase in ("is one of", "is not", "greater than", "less than", "includes", "equals", "is"):
            token = f" {phrase} "
            low = body.lower()
            idx = low.find(token)
            if idx == -1:
                continue
            place = body[:idx].strip()
            value = body[idx + len(token) :].strip()
            look_at, check_part = split_where(place)
            if phrase == "is one of":
                rule_type, val = "Must be one of", value
            elif phrase == "is not":
                # No dedicated op — keep structured on rule (advanced). Return None.
                return None
            elif phrase == "greater than":
                rule_type, val = "Number greater than", value
            elif phrase == "less than":
                rule_type, val = "Number less than", value
            elif phrase == "includes":
                if look_at.lower() == "defects":
                    rule_type, val = "Defect type includes", value
                else:
                    rule_type, val = "Must contain text", value
            else:  # is / equals
                rule_type, val = "Must equal", value
            return {
                "id": cond_id,
                "row_type": "Condition (hidden)",
                "section": "Conditions",
                "rule": text,
                "applies_when": "",
                "for_each": "",
                "look_at": look_at,
                "check_part": check_part,
                "rule_type": rule_type,
                "value": val,
                "example": "",
            }

    low = re.sub(r"^when\s+", "", text, flags=re.I).strip().lower()
    look_at_where, _ = split_where(where_raw)

    # Defect existence / type
    if "defect" in low:
        if "same" in low or "color" in low or "colour" in low or "reference" in low:
            return None  # no JSON mapping — leave rule always-on
        m = re.search(r"([a-z0-9 ]+?)\s+defects?\b", low)
        if m and m.group(1).strip() not in ("", "when"):
            words = [
                w
                for w in re.split(r"[^a-z0-9]+", m.group(1))
                if w and w not in {"the", "a", "an", "any", "when", "or", "and"}
            ]
            if words:
                return {
                    "id": cond_id,
                    "row_type": "Condition (hidden)",
                    "section": "Conditions",
                    "rule": text,
                    "applies_when": "",
                    "for_each": "",
                    "look_at": "Defects",
                    "check_part": "",
                    "rule_type": "Defect type includes",
                    "value": " ".join(words),
                    "example": "",
                }
        return {
            "id": cond_id,
            "row_type": "Condition (hidden)",
            "section": "Conditions",
            "rule": "Any defects found",
            "applies_when": "",
            "for_each": "",
            "look_at": "Defect count",
            "check_part": "",
            "rule_type": "Number greater than",
            "value": "0",
            "example": "",
        }

    # Pass/Fail on the rule's checklist item
    if "pass" in low or "fail" in low:
        look_at = look_at_where
        # Strip trailing photo-ish words if where was photo count
        for noise in ("photo count", "photo caption", "photo content", "comment", "result", "values"):
            if look_at.lower().endswith(noise):
                look_at = look_at[: -(len(noise))].strip()
        verdict = "FAIL" if "fail" in low else "PASS"
        return {
            "id": cond_id,
            "row_type": "Condition (hidden)",
            "section": "Conditions",
            "rule": text,
            "applies_when": "",
            "for_each": "",
            "look_at": look_at,
            "check_part": "result",
            "rule_type": "Must equal",
            "value": verdict,
            "example": "",
        }

    return None


def main() -> int:
    markdown_path = ROOT / "data/clients/hallmark/gi/_archive/rules_previous.md"
    blocks = parse_with_section(markdown_path.read_text(encoding="utf-8"))

    excel_rows: list[dict[str, str]] = []
    cond_n = 0

    for b in blocks:
        where_raw = b.get("where", "")
        look_at, check_part = split_where(where_raw)
        action = b.get("action", "")
        # Vision on Defects needs photo content (structured list alone is not AI-groundable).
        if action == "needs vision" and look_at.lower() == "defects" and not check_part:
            check_part = "photo content"
        rule_type = ACTION_MAP.get(action, action)
        when_raw = (b.get("when") or "").strip()
        applies = ""

        if when_raw:
            cond_n += 1
            cond_id = f"C{cond_n}"
            cond = when_to_condition(when_raw, where_raw, cond_id)
            if cond:
                excel_rows.append(cond)
                applies = f"@{cond_id}"
            elif is_structured_when(when_raw):
                applies = when_raw  # advanced; compiler accepts with note
            else:
                # Unmappable — leave blank (always) and note in example
                print(f"[export] WARN: could not map when for {b.get('id')}: {when_raw!r} → always")

        row = {
            "id": b.get("id", ""),
            "row_type": b.get("row type") or "Rule",
            "section": b.get("section", ""),
            "rule": b.get("check", ""),
            "applies_when": applies,
            "for_each": b.get("for each", ""),
            "look_at": look_at,
            "check_part": check_part,
            "rule_type": rule_type,
            "value": b.get("param", ""),
            "example": b.get("example", ""),
        }
        # Do not dump unmapped when into Optional Example (confuses ops).
        excel_rows.append(row)

    wb = build_workbook(excel_rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    # Also refresh library template (examples only)
    from build_gi_authoring_excel import OUT_XLSX, OUT_SCHEMA, build_schema
    import json

    build_workbook().save(OUT_XLSX)
    OUT_SCHEMA.write_text(json.dumps(build_schema(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(excel_rows)} rows, {cond_n} conditions from when)")
    print(f"Wrote {OUT_XLSX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
