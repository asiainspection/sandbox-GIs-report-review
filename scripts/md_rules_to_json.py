"""Convert a Markdown GI rules reference into deterministic JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FIELD_MAP = {
    "ID": "id",
    "Field / Location": "field_location",
    "What to check": "what_to_check",
    "Scope": "scope",
    "Never flag if": "never_flag_if",
    "Error example": "error_example",
    "Correct example": "correct_example",
    "Severity": "severity",
}


def normalize_severity(value: str) -> str:
    cleaned = value.strip().strip("`").replace("⚠️", "").strip().upper()
    if "TO CONFIRM" in cleaned or cleaned == "TO_CONFIRM":
        return "TO_CONFIRM"
    if cleaned == "MINOR":
        return "MINOR"
    if cleaned == "BLOCKING":
        return "BLOCKING"
    return "BLOCKING"


def clean_cell(value: str) -> str:
    return value.strip().replace("<br>", "\n")


def parse_table(lines: list[str]) -> dict[str, Any] | None:
    rows = [[clean_cell(cell) for cell in line.strip().strip("|").split("|")] for line in lines]
    if len(rows) < 2:
        return None
    headers = rows[0]
    data_rows = rows[2:] if set(rows[1][0].replace("-", "").replace(":", "").strip()) == set() else rows[1:]
    return {
        "headers": headers,
        "rows": [dict(zip(headers, row)) for row in data_rows if len(row) == len(headers)],
    }


def extract_tables(extra_lines: list[str]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    index = 0
    while index < len(extra_lines):
        if not extra_lines[index].lstrip().startswith("|"):
            index += 1
            continue

        start = index
        while index < len(extra_lines) and extra_lines[index].lstrip().startswith("|"):
            index += 1

        table = parse_table(extra_lines[start:index])
        if table:
            title = ""
            for previous in reversed(extra_lines[:start]):
                previous = previous.strip()
                if previous:
                    title = re.sub(r"^\*\*(.*?)\*\*:?\s*$", r"\1", previous)
                    break
            table["title"] = title
            tables.append(table)

    return tables


def split_scope(value: str) -> dict[str, str]:
    match = re.match(r"`?([A-Z ]+)`?\s*(?:[—-]\s*)?(.*)", value)
    if not match:
        return {"level": value.strip(), "detail": ""}
    return {"level": match.group(1).strip(), "detail": match.group(2).strip()}


def compact_never_flag_lines(value: str) -> list[str]:
    lines = [line.strip(" -") for line in re.split(r"\n+", value.strip()) if line.strip()]
    return lines


def parse_rule(block: list[tuple[int, str]], section: str, subsection: str) -> dict[str, Any]:
    rule: dict[str, Any] = {
        "section": section,
        "subsection": subsection,
        "source_lines": {"start": block[0][0], "end": block[-1][0]},
    }
    extra_lines: list[str] = []

    for _, line in block:
        field_match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
        if not field_match:
            if line.strip() and line.strip() != "---":
                extra_lines.append(line)
            continue

        label, value = field_match.groups()
        key = FIELD_MAP.get(label)
        if not key:
            extra_lines.append(line)
            continue

        if key == "scope":
            rule[key] = split_scope(value)
        elif key == "never_flag_if":
            rule[key] = compact_never_flag_lines(value)
        elif key == "severity":
            rule[key] = normalize_severity(value)
        else:
            rule[key] = value.strip()

    extra_markdown = "\n".join(line for line in extra_lines).strip()
    rule["additional_markdown"] = extra_markdown
    rule["tables"] = extract_tables(extra_lines)
    return rule


def parse_rules(markdown: str) -> dict[str, Any]:
    lines = markdown.splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("# ") else ""
    sources = ""
    last_compiled = ""
    rules: list[dict[str, Any]] = []
    section = ""
    subsection = ""
    current: list[tuple[int, str]] = []
    current_section = ""
    current_subsection = ""

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("> Sources:"):
            sources = line.removeprefix("> Sources:").strip()
        elif line.startswith("> Last compiled:"):
            last_compiled = line.removeprefix("> Last compiled:").strip()

        section_match = re.match(r"^##\s+Section\s+\d+\s+[–-]\s+(.+)$", line)
        subsection_match = re.match(r"^###\s+(.+)$", line)
        id_match = re.match(r"^\*\*ID:\*\*\s+(.+)$", line)

        if section_match:
            if current:
                rules.append(parse_rule(current, current_section, current_subsection))
                current = []
            section = section_match.group(1).strip()
            subsection = ""
            continue
        elif subsection_match:
            if current:
                rules.append(parse_rule(current, current_section, current_subsection))
                current = []
            subsection = subsection_match.group(1).strip()
            continue

        if id_match:
            if current:
                rules.append(parse_rule(current, current_section, current_subsection))
            current = [(line_number, line)]
            current_section = section
            current_subsection = subsection or section
            continue

        if current:
            current.append((line_number, line))

    if current:
        rules.append(parse_rule(current, current_section, current_subsection))

    return {
        "title": title,
        "sources": sources,
        "last_compiled": last_compiled,
        "rule_count": len(rules),
        "rules": rules,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert GI Markdown rules to JSON.")
    parser.add_argument("input_md", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    parsed = parse_rules(args.input_md.read_text(encoding="utf-8"))
    parsed["source_file"] = str(args.input_md)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {parsed['rule_count']} rules to {args.output_json}")


if __name__ == "__main__":
    main()
