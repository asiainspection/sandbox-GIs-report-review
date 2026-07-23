"""Parse harness-format GI rules.md and compile to check_block / rule dicts.

Harness blocks use lowercase keys:
  **id:** **check:** **where:** **action:** **param:** **when:** **example:**

No ```check fences. Action + Where map to the closed operator / field vocab.
"""

from __future__ import annotations

import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Closed maps (keep in sync with data/library/harness_*.md)
# ---------------------------------------------------------------------------

COVER_WHERE: dict[str, str | list[str]] = {
    "factory address": "report.factory_address",
    "factory name": "report.factory_name",
    "supplier name": "report.supplier_name",
    "production site": "report.production_site",
    "inspector remark": "report.global_remark",
    "overall result": "report.overall_result",
    "inspection type": "report.inspection_type",
    "po reference": "report.po_reference",
    "product name": "report.product_label",
    "sku": "report.sku",
    "ordered quantity": "product._first.ordered_quantity",
    "packed quantity": "product._first.real_packed_quantity",
    "produced quantity": "product._first.real_produced_quantity",
    "unit": "product._first.unit",
    "major aql": "workmanship.aql_level_major",
    "minor aql": "workmanship.aql_level_minor",
    "critical aql": "workmanship.aql_level_critical",
    "workmanship result": "workmanship.result",
    "defects": "report.defects",
    "defect count": "report.defect_count",
    "full report text": "report.inspector_text",
    "all captions": "report.all_captions",
}

EXTERNAL_WHERE: dict[str, str] = {
    "booking": "out_of_report:booking",
    "spec sheet": "out_of_report:spec_sheet",
    "email": "out_of_report:email",
    "sop": "out_of_report:sop",
}

SUFFIX_TO_FIELD: dict[str, str] = {
    "result": "result",
    "comment": "comment",
    "values": "values",
    "photo count": "photo_count",
    "photo caption": "photo_captions",
    "photo content": "photo_content",
    "file name": "attachment_filenames",
    "file content": "attachment_content",
}

_SUFFIXES_SORTED = sorted(SUFFIX_TO_FIELD.keys(), key=len, reverse=True)

_FIELD_KEYS = (
    "id", "row type", "check", "where", "action", "param", "when", "for each", "example"
)
_FIELD_RE = re.compile(
    r"^\*\*(id|row type|check|where|action|param|when|for each|example):\*\*\s*(.*)$",
    re.I,
)


def is_harness_rules_markdown(markdown: str) -> bool:
    """True when rules.md uses harness blocks (not legacy **ID:** / ```check)."""
    lower = markdown.lower()
    if "```check" in lower:
        fence_count = lower.count("```check")
        harness_ids = len(re.findall(r"^\*\*id:\*\*", markdown, re.M | re.I))
        if fence_count >= harness_ids and fence_count > 0:
            return False
    return bool(re.search(r"^\*\*id:\*\*", markdown, re.M | re.I)) and bool(
        re.search(r"^\*\*(check|action):\*\*", markdown, re.M | re.I)
    )


def _slug(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "rule"


def parse_harness_blocks(markdown: str) -> list[dict[str, str]]:
    """Parse harness check blocks into list of field dicts."""
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    section = ""

    for raw in markdown.splitlines():
        line = raw.rstrip()
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            title = heading.group(1).strip()
            if not title.lower().startswith("part "):
                section = title

        m = _FIELD_RE.match(line.strip())
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key == "id":
                if current and current.get("id"):
                    blocks.append(current)
                current = {"id": val, "_section": section}
            elif current is not None:
                current[key] = val
            continue

    if current and current.get("id"):
        blocks.append(current)
    return blocks


def _split_checklist_where(where: str) -> tuple[str, str] | None:
    text = (where or "").strip()
    low = text.lower()
    for suffix in _SUFFIXES_SORTED:
        token = f" {suffix}"
        if low.endswith(token):
            name = text[: -len(token)].strip()
            if name:
                return name, suffix
    return None


def where_to_bindings(where: str, *, action: str = "") -> list[Any]:
    """Map human Where → check_block where list entries."""
    text = (where or "").strip()
    if not text:
        return ["unmapped"]

    key = text.lower()
    if key in EXTERNAL_WHERE:
        return [EXTERNAL_WHERE[key]]
    if key in COVER_WHERE:
        if action == "ratio at least" and key == "packed quantity":
            return [
                "product._first.real_packed_quantity",
                "product._first.ordered_quantity",
            ]
        sel = COVER_WHERE[key]
        return [sel] if isinstance(sel, str) else list(sel)

    split = _split_checklist_where(text)
    if split:
        name, suffix = split
        field = SUFFIX_TO_FIELD[suffix]
        tokens = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if len(t) > 1]
        return [
            {
                "kind": "checklist",
                "match": tokens[:6] or [name.lower()],
                "field": field,
            }
        ]

    tokens = [t for t in re.split(r"[^a-z0-9]+", key) if len(t) > 1]
    return [
        {
            "kind": "checklist",
            "match": tokens[:6] or [key],
            "field": "comment",
        }
    ]


def _param_list(param: str) -> list[str]:
    raw = (param or "").strip()
    if not raw:
        return []
    if "," in raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [raw]


def action_to_check(action: str, param: str) -> Any:
    """Map Action (+ Param) → check_block check value (string, list, or null)."""
    act = (action or "").strip()
    p = (param or "").strip()

    if act == "manual review":
        return None
    if act == "is present":
        return "present"
    if act == "is in English":
        return "no_language(chinese)"
    if act == "equals":
        return f"equals({p})" if p else "equals(PASS)"
    if act == "is one of":
        parts = _param_list(p) or ["PASS", "FAIL"]
        return "in_set(" + ", ".join(parts) + ")"
    if act == "contains phrase":
        return f'contains("{p}")' if p else None
    if act == "matches pattern":
        return f'matches("{p}")' if p else None
    if act == "at least N photos":
        return f"count_at_least({p or '1'})"
    if act == "at most N photos":
        return f"count_at_most({p or '0'})"
    if act == "ratio at least":
        return f"ratio_at_least({p or '0.8'})"
    if act == "filename matches":
        return f'filename_matches("{p}")' if p else 'filename_matches("*.xlsx")'
    if act == "term must not appear":
        return f'scan_absent("{p}")' if p else None
    if act == "number greater than":
        return f"compare(>, {p or '0'})"
    if act == "number less than":
        return f"compare(<, {p or '0'})"
    if act == "defect type includes":
        # Author supplies type words (comma or space); no client defect list in code.
        names = [n for n in re.split(r"[,]+", p) if n.strip()] if "," in p else [
            n for n in re.split(r"\s+", p) if n.strip()
        ]
        if not names:
            return None
        quoted = ", ".join(f'"{n.strip()}"' for n in names)
        return f"defects_name_any({quoted})"
    if act == "LLM quote then match":
        if not p:
            return None
        return [
            'extract("Quote the relevant phrase from this field, or null")',
            f'contains("{p}")',
        ]
    if act == "LLM yes/no":
        q = (p or "Is the required information present in this field?").replace('"', "'")
        return f'extract_bool("{q}")'
    if act == "needs vision":
        q = (p or "Does the photo show the required evidence?").replace('"', "'")
        return f'vision("{q}")'
    return None


# ---------------------------------------------------------------------------
# When = <place> <comparator> <value>  (mirrors Where; closed vocabulary)
# Kept in sync with the "When" section of data/library/harness_where.md.
# ---------------------------------------------------------------------------

# Ordered most-specific first so "is one of"/"is not" win over "is".
_WHEN_COMPARATORS: list[tuple[str, str]] = [
    ("is one of", "in_set"),
    ("is not", "!="),
    ("greater than", ">"),
    ("less than", "<"),
    ("includes", "includes"),
    ("equals", "=="),
    ("is", "=="),
]

# Words dropped when reading defect-type descriptors from author text.
_DEFECT_TYPE_STOPWORDS = frozenset(
    {
        "when", "the", "a", "an", "are", "is", "if", "found", "exist", "exists",
        "present", "any", "have", "has", "with", "and", "or", "same", "of", "no", "not",
    }
)


def _where_to_selector(place: str) -> str | None:
    """Resolve a Where phrase (cover, or checklist place+suffix) to one selector."""
    text = (place or "").strip()
    if not text:
        return None
    key = text.lower()
    if key in COVER_WHERE:
        sel = COVER_WHERE[key]
        return sel if isinstance(sel, str) else (sel[0] if sel else None)
    split = _split_checklist_where(text)
    if split:
        name, suffix = split
        field = SUFFIX_TO_FIELD[suffix]
        tokens = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if len(t) > 1]
        slug = "_".join(tokens[:5]) or name.lower()
        return f"checklist.{slug}.{field}"
    return None


def _defect_names_from_text(text: str) -> list[str]:
    """Descriptor words before 'defect(s)' — the author names the type, not code."""
    m = re.search(r"([a-z0-9 ]+?)\s+defects?\b", text.lower())
    if not m:
        return []
    return [
        w
        for w in re.split(r"[^a-z0-9]+", m.group(1))
        if w and w not in _DEFECT_TYPE_STOPWORDS
    ]


def _emit_when(selector: str, cmp: str, value: str) -> str:
    value = value.strip()
    if cmp == "includes":
        if selector == "report.defects":
            names = [v.strip() for v in re.split(r",|\bor\b", value) if v.strip()]
            quoted = ", ".join(f'"{n}"' for n in names) or f'"{value}"'
            return f"defects_name_any({quoted})"
        return f'{selector} contains "{value}"'
    if cmp == "in_set":
        return f"{selector} in_set {value}"
    if cmp == "==":
        scalar = value if re.fullmatch(r"-?\d+(\.\d+)?", value) else f'"{value}"'
        return f"{selector} equals {scalar}"
    return f"{selector} {cmp} {value}"  # numeric inequality (>, <)


def _structured_when(text: str) -> str | None:
    """Compile `<place> <comparator> <value>`; None if no comparator matched."""
    low = text.lower()
    for phrase, cmp in _WHEN_COMPARATORS:
        token = f" {phrase} "
        idx = low.find(token)
        if idx == -1:
            continue
        place = text[:idx].strip()
        value = text[idx + len(token):].strip()
        selector = _where_to_selector(place)
        if not selector:
            return None
        return _emit_when(selector, cmp, value)
    return None


def _warn_unmapped_when(when: str) -> None:
    print(
        f"[harness] WARNING: unrecognized When {when!r} -> rule skipped. "
        "Use '<place> <comparator> <value>' (see harness_where.md, When section).",
        file=sys.stderr,
    )


def is_linked_when(when: str) -> bool:
    """True when Applies when is a Condition reference expression (@C1 AND @C2)."""
    return "@" in (when or "")


def is_structured_when(when: str) -> bool:
    """True when Applies when matches ``<place> <comparator> <value>``."""
    text = (when or "").strip()
    if not text:
        return False
    body = re.sub(r"^when\s+", "", text, flags=re.I).strip()
    return _structured_when(body) is not None


def when_to_predicate(when: str, where: str) -> str | None:
    """Compile When into a check_block predicate string.

    Production authoring (Excel) should use Condition rows + ``@C1 AND @C2``.
    This function still accepts the structured grammar
    ``<place> <comparator> <value>`` for markdown / advanced edits.

    Empty When -> None (always applies). Unrecognized When -> ``false``
    (skip; never silent-always) with a stderr warning.
    """
    text = (when or "").strip()
    if not text:
        return None
    if is_linked_when(text):
        # Linked @IDs are resolved in parse_harness_rules / excel_to_checkpoints.
        return text
    body = re.sub(r"^when\s+", "", text, flags=re.I).strip()

    # Structured grammar only (closed place + comparator + value).
    structured = _structured_when(body)
    if structured is not None:
        return structured

    # Legacy free-text back-compat for frozen rules.md phrasings.
    # New Excel authoring must NOT rely on this — use Condition rows.
    low = body.lower()
    if "psi" in low or "pre-shipment" in low or "pre shipment" in low:
        return 'report.inspection_type equals "Pre-Shipment Inspection"'
    if "dupro" in low or "during production" in low:
        return 'report.inspection_type equals "During Production Inspection"'
    if "pass" in low or "fail" in low:
        split = _split_checklist_where(where)
        if split:
            tokens = [t for t in re.split(r"[^a-z0-9]+", split[0].lower()) if len(t) > 1]
            slug = "_".join(tokens[:5])
            if slug:
                verdict = "FAIL" if "fail" in low else "PASS"
                return f"checklist.{slug}.result equals {verdict}"
    if "defect" in low:
        if "same" in low or "color" in low or "colour" in low or "reference" in low:
            _warn_unmapped_when(text)
            return "false"
        names = _defect_names_from_text(low)
        if names:
            quoted = ", ".join(f'"{n}"' for n in names)
            return f"defects_name_any({quoted})"
        return "report.defect_count > 0"

    _warn_unmapped_when(text)
    return "false"


def block_to_check_block(block: dict[str, str]) -> dict[str, Any]:
    """Compile one harness block → {where, when, check}."""
    row_type = (block.get("row type") or "Rule").strip()
    action = (block.get("action") or "").strip()
    where_raw = (block.get("where") or "").strip()
    param = (block.get("param") or "").strip()
    for_each = (block.get("for each") or block.get("for_each") or "").strip()
    when_raw = (block.get("when") or "").strip()

    where = where_to_bindings(where_raw, action=action)
    check = action_to_check(action, param)

    # Note: parsing linked `@ID AND @ID` from `when_raw` happens in `when_to_predicate`
    # or inside `parse_harness_rules` where we have the full macro dictionary.
    when = when_raw  # Keep raw text; we will resolve it across the dataset later

    out: dict[str, Any] = {"where": where, "when": when, "check": check, "row_type": row_type}
    if for_each:
        out["for_each"] = for_each
    return out


def block_to_rule(block: dict[str, str]) -> dict[str, Any]:
    """Harness block → md_rules_to_json-compatible rule dict."""
    where = (block.get("where") or "").strip()
    check = (block.get("check") or "").strip()
    example = (block.get("example") or "").strip()
    return {
        "id": (block.get("id") or "").strip(),
        "section": (block.get("_section") or "rules").strip(),
        "subsection": (block.get("_section") or "rules").strip(),
        "field_location": where,
        "what_to_check": check,
        "scope": {"level": "QUESTION", "detail": ""},
        "error_example": "",
        "correct_example": example,
        "severity": "BLOCKING",
        "additional_markdown": "",
        "tables": [],
        "harness": {
            "action": (block.get("action") or "").strip(),
            "param": (block.get("param") or "").strip(),
            "when": (block.get("when") or "").strip(),
            "for_each": (block.get("for each") or block.get("for_each") or "").strip(),
        },
    }


def _parse_linked_when(text: str, macros: dict[str, dict[str, Any]]) -> dict[str, Any] | str | None:
    """Parse `@ID1 AND @ID2` into an AST, resolving from the macros dict."""
    if not text:
        return None
    if "@" not in text:
        return text  # Handled by fallback string parser
    
    # Very basic AND / OR / NOT parser for ID macros
    def _resolve(token: str) -> dict[str, Any]:
        token = token.strip()
        is_not = False
        if token.upper().startswith("NOT "):
            is_not = True
            token = token[4:].strip()
        if token.startswith("@"):
            token = token[1:]
        
        cb = macros.get(_slug(token))
        if not cb:
            # Fallback to failing node if macro is missing
            ast = {"op": "false", "ground": "json"}
        else:
            ast = {"op": "_macro_ref", "check": cb.get("check"), "where": cb.get("where")}
            
        if is_not:
            return {"op": "not", "item": ast, "ground": "json"}
        return ast

    if " OR " in text.upper():
        parts = re.split(r"(?i)\s+OR\s+", text)
        return {"op": "any_of", "items": [_resolve(p) for p in parts], "ground": "json"}
    
    if " AND " in text.upper():
        parts = re.split(r"(?i)\s+AND\s+", text)
        return {"op": "all_of", "items": [_resolve(p) for p in parts], "ground": "json"}

    return _resolve(text)


def parse_harness_rules(markdown: str) -> dict[str, Any]:
    """Full parse: rules + check_blocks keyed by slug id."""
    blocks = parse_harness_blocks(markdown)
    
    # 1. First pass: extract Condition macros
    macros: dict[str, dict[str, Any]] = {}
    check_blocks: dict[str, dict[str, Any]] = {}
    for b in blocks:
        cb = block_to_check_block(b)
        rid = _slug(b.get("id") or "")
        check_blocks[rid] = cb
        if cb.get("row_type", "").lower().startswith("condition"):
            # Store the whole CheckBlock so _macro_ref can access `where` and `check` strings
            macros[rid] = cb

    # 2. Second pass: resolve Applies when using macros
    rules = []
    for b in blocks:
        cb = check_blocks[_slug(b.get("id") or "")]
        if cb.get("row_type", "").lower().startswith("condition"):
            continue  # Don't output hidden conditions as rules
        
        when_raw = cb.get("when")
        if isinstance(when_raw, str):
            if "@" in when_raw:
                cb["when"] = _parse_linked_when(when_raw, macros)
            else:
                where_raw = (b.get("where") or "").strip()
                cb["when"] = when_to_predicate(when_raw, where_raw)
        
        rules.append(block_to_rule(b))
        
    title = ""
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return {
        "title": title,
        "sources": "harness",
        "last_compiled": "",
        "rule_count": len(rules),
        "rules": rules,
        "check_blocks": check_blocks,
        "format": "harness",
    }
