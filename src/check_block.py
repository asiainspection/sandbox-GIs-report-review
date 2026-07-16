"""Parse, validate, and compile footer ```check blocks into ObligationSpecs."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from fact_schema import FACT_SELECTORS, checklist_selector, custom_selector
from obligation import ObligationSpec, validate_checkspec

ROOT = Path(__file__).resolve().parents[1]

CHECKABLE_SOURCES = frozenset({"in_report", "IP"})
ADVISORY_SOURCES = frozenset({"PO_booking", "spec_sheet", "email", "external", "other"})

OPERATORS = frozenset(
    {
        "present",
        "equals",
        "in_set",
        "matches",
        "no_language",
        "contains",
        "has_number",
        "compare",
        "count_at_least",
        "count_at_most",
        "ratio_at_least",
        "scan_present",
        "scan_absent",
        "filename_matches",
        "extract",
        "vision",
    }
)

CHECKLIST_SUFFIXES = frozenset(
    {
        "result",
        "comment",
        "values",
        "photo_count",
        "photo_captions",
        "applicable",
        "attachment_filenames",
        "spotlight_count",
        "caption_count",
    }
)

_SELECTOR_PREFIXES = ("report.", "product.", "workmanship.", "checklist.", "custom.")
_CMP_OPS = frozenset({">=", "<=", "!=", "==", ">", "<", "="})


def _slug_rule_id(rule_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (rule_id or "").strip().lower()).strip("_") or "rule"


def parse_check_block_text(text: str) -> dict[str, Any]:
    """Parse a ```check fenced block body (simple YAML subset)."""
    data: dict[str, Any] = {}
    current_key: str | None = None
    list_mode = False
    list_items: list[Any] = []

    def flush() -> None:
        nonlocal current_key, list_mode, list_items
        if current_key is None:
            return
        if list_mode:
            data[current_key] = list_items
        list_mode = False
        list_items = []
        current_key = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            if current_key is None:
                raise ValueError(f"list item without key: {stripped}")
            list_mode = True
            list_items.append(_parse_scalar(stripped[2:].strip()))
            continue

        if ":" in line and not line.startswith((" ", "\t")):
            flush()
            key, _, rest = line.partition(":")
            current_key = key.strip()
            value = rest.strip()
            if not value:
                continue
            if value == "null":
                data[current_key] = None
                current_key = None
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if not inner:
                    data[current_key] = []
                else:
                    data[current_key] = [_parse_scalar(p.strip()) for p in _split_list(inner)]
                current_key = None
            else:
                data[current_key] = _parse_scalar(value)
                current_key = None
            continue

        if current_key is not None and not list_mode:
            prev = data.get(current_key, "")
            data[current_key] = f"{prev}\n{stripped}".strip()

    flush()
    return data


def _split_list(inner: str) -> list[str]:
    parts: list[str] = []
    buf = ""
    in_quote = False
    quote = ""
    for ch in inner:
        if in_quote:
            buf += ch
            if ch == quote:
                in_quote = False
            continue
        if ch in "\"'":
            in_quote = True
            quote = ch
            buf += ch
            continue
        if ch == ",":
            parts.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text == "null":
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        return float(text) if "." in text else int(text)
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    return text


def extract_check_blocks(markdown: str) -> dict[str, dict[str, Any]]:
    """Return {slug_rule_id: parsed_block} from rules.md."""
    blocks: dict[str, dict[str, Any]] = {}
    current_id: str | None = None
    pending_block: str | None = None

    for line in markdown.splitlines():
        id_match = re.match(r"^\*\*ID:\*\*\s+(.+)$", line)
        if id_match:
            current_id = _slug_rule_id(id_match.group(1))
            continue
        if line.strip() == "```check":
            pending_block = ""
            continue
        if pending_block is not None:
            if line.strip() == "```":
                if current_id:
                    blocks[current_id] = parse_check_block_text(pending_block)
                pending_block = None
            else:
                pending_block += line + "\n"
    return blocks


def is_valid_selector(selector: str) -> bool:
    if selector in FACT_SELECTORS:
        return True
    if selector.startswith("custom."):
        name = selector.split(".", 1)[1]
        return bool(name)
    if selector.startswith("checklist."):
        parts = selector.split(".", 2)
        if len(parts) != 3:
            return False
        _, name, suffix = parts
        return bool(name) and suffix in CHECKLIST_SUFFIXES
    if selector.startswith("product._first."):
        return True
    if selector.startswith("workmanship."):
        return True
    return False


def validate_block(block: dict[str, Any], *, checkpoint_id: str = "") -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    prefix = checkpoint_id or "block"

    data_source = str(block.get("data_source") or "").strip()
    if not data_source:
        errors.append({"id": prefix, "field": "data_source", "message": "data_source is required"})
    elif data_source not in CHECKABLE_SOURCES | ADVISORY_SOURCES:
        errors.append(
            {"id": prefix, "field": "data_source", "message": f"unknown data_source {data_source!r}"}
        )

    where = block.get("where")
    if where is None:
        errors.append({"id": prefix, "field": "where", "message": "where is required (use [] for advisory)"})
    elif not isinstance(where, list):
        errors.append({"id": prefix, "field": "where", "message": "where must be a list"})
    else:
        for sel in where:
            if not is_valid_selector(str(sel)):
                errors.append(
                    {"id": prefix, "field": "where", "message": f"unknown selector {sel!r}"}
                )

    if data_source in ADVISORY_SOURCES:
        if where not in ([], None) and where:
            errors.append({"id": prefix, "field": "where", "message": "advisory blocks must use where: []"})
        if block.get("check") not in (None, "null"):
            errors.append({"id": prefix, "field": "check", "message": "advisory blocks must use check: null"})
        return errors

    if data_source in CHECKABLE_SOURCES:
        check = block.get("check")
        if check is None:
            errors.append({"id": prefix, "field": "check", "message": "check is required for in_report rules"})
        else:
            try:
                _compile_calls(check, where or [], f"{prefix}.check")
            except ValueError as exc:
                errors.append({"id": prefix, "field": "check", "message": str(exc)})

        when = block.get("when")
        if when not in (None, "null"):
            try:
                _compile_call(str(when), where or [], f"{prefix}.when", allow_field_refs=True)
            except ValueError as exc:
                errors.append({"id": prefix, "field": "when", "message": str(exc)})

    return errors


def _tokenize_call(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text[i] in "\"'":
            quote = text[i]
            j = i + 1
            while j < len(text) and text[j] != quote:
                j += 1
            tokens.append(text[i : j + 1])
            i = j + 1
            continue
        if text[i] in "(),":
            tokens.append(text[i])
            i += 1
            continue
        j = i
        while j < len(text) and text[j] not in "(), \t":
            j += 1
        tokens.append(text[i:j])
        i = j
    return tokens


def _parse_args(arg_text: str) -> list[Any]:
    arg_text = arg_text.strip()
    if not arg_text:
        return []
    parts: list[str] = []
    buf = ""
    depth = 0
    in_quote = False
    quote = ""
    for ch in arg_text:
        if in_quote:
            buf += ch
            if ch == quote:
                in_quote = False
            continue
        if ch in "\"'":
            in_quote = True
            quote = ch
            buf += ch
            continue
        if ch == "(":
            depth += 1
            buf += ch
            continue
        if ch == ")":
            depth -= 1
            buf += ch
            continue
        if ch == "," and depth == 0:
            parts.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return [_parse_scalar(p) for p in parts]


def _is_selector(token: str) -> bool:
    return any(token.startswith(p) for p in _SELECTOR_PREFIXES)


def _compile_call(
    call: str,
    where: list[str],
    path: str,
    *,
    allow_field_refs: bool = True,
) -> dict[str, Any]:
    text = call.strip()
    if not text:
        raise ValueError(f"{path}: empty call")

    for cmp in sorted(_CMP_OPS, key=len, reverse=True):
        if cmp in text:
            left, _, right = text.partition(cmp)
            left = left.strip()
            right = right.strip()
            if _is_selector(left) and _is_selector(right):
                return {
                    "op": "compare",
                    "left": left,
                    "right": right,
                    "cmp": cmp if cmp != "=" else "==",
                    "ground": "json",
                }
            if _is_selector(left):
                return {
                    "op": "compare",
                    "selector": left,
                    "value": _parse_scalar(right),
                    "cmp": cmp if cmp != "=" else "==",
                    "ground": "json",
                }

    infix_ops = (" equals ", " contains ", " matches ")
    for sep in infix_ops:
        if sep in text:
            left, op_name, right = text.partition(sep)
            left = left.strip()
            right = right.strip()
            op_name = op_name.strip()
            if not _is_selector(left):
                raise ValueError(f"{path}: infix left must be a selector, got {left!r}")
            if op_name == "equals":
                return {"op": "equals", "selector": left, "expected": _parse_scalar(right), "ground": "json"}
            if op_name == "contains":
                return {
                    "op": "contains",
                    "selector": left,
                    "text": str(_parse_scalar(right)),
                    "ground": "json",
                }
            if op_name == "matches":
                return {
                    "op": "matches",
                    "selector": left,
                    "pattern": str(_parse_scalar(right)),
                    "ground": "json",
                }

    match = re.match(r"^([a-z_]+)\((.*)\)$", text, re.DOTALL)
    if match:
        op = match.group(1)
        args = _parse_args(match.group(2))
        if op not in OPERATORS:
            raise ValueError(f"{path}: unknown op {op!r}")
        return _compile_op_on_where(op, args, where, path)

    if text in OPERATORS:
        return _compile_op_on_where(text, [], where, path)

    raise ValueError(f"{path}: cannot parse {text!r}")


def _compile_calls(
    check: Any,
    where: list[str],
    path: str,
) -> dict[str, Any]:
    if isinstance(check, list):
        items = [_compile_call(str(c), where, f"{path}[{i}]") for i, c in enumerate(check)]
        if len(items) == 1:
            return items[0]
        return {"op": "all_of", "items": items}
    return _compile_call(str(check), where, path)


def _compile_op_on_where(
    op: str,
    args: list[Any],
    where: list[str],
    path: str,
) -> dict[str, Any]:
    if op in ("extract", "vision"):
        if not args:
            raise ValueError(f"{path}: {op} requires a question string")
        question = str(args[0])
        atom_id = re.sub(r"[^a-z0-9]+", "_", question.lower())[:48] or op
        if op == "extract":
            return {
                "op": "atom",
                "id": f"{path}_{atom_id}",
                "question": question,
                "role": "required_true",
                "ground": "atom",
            }
        return {
            "op": "vision",
            "id": f"{path}_{atom_id}",
            "question": question,
            "ground": "vision",
        }

    if op == "ratio_at_least":
        if len(where) < 2:
            raise ValueError(f"{path}: ratio_at_least needs two fields in where")
        minimum = float(args[0]) if args else 0.0
        return {
            "op": "ratio_at_least",
            "numerator": where[0],
            "denominator": where[1],
            "min": minimum,
            "ground": "json",
        }

    if op == "scan_present":
        term = str(args[0]) if args else ""
        return {"op": "contains", "selector": "report.all_text", "text": term, "ground": "json"}

    if op == "scan_absent":
        term = str(args[0]) if args else ""
        return {
            "op": "not",
            "item": {"op": "contains", "selector": "report.all_text", "text": term, "ground": "json"},
        }

    if op == "filename_matches":
        pattern = str(args[0]) if args else ""
        selector = where[0] if where else ""
        return {"op": "filename_matches", "selector": selector, "pattern": pattern, "ground": "json"}

    if op == "compare" and len(args) >= 2:
        first = str(args[0])
        second = str(args[1])
        if first in _CMP_OPS:
            cmp, val = first, args[1]
            selector = where[0] if where else ""
            if _is_selector(str(val)):
                return {"op": "compare", "left": selector, "right": str(val), "cmp": cmp, "ground": "json"}
            return {"op": "compare", "selector": selector, "value": val, "cmp": cmp, "ground": "json"}
        if second in _CMP_OPS:
            selector = where[0] if where else ""
            return {
                "op": "compare",
                "selector": selector,
                "value": args[0],
                "cmp": second if second != "=" else "==",
                "ground": "json",
            }

    targets = where if where else [""]
    nodes: list[dict[str, Any]] = []
    for selector in targets:
        nodes.append(_compile_single_op(op, args, selector, path))
    if len(nodes) == 1:
        return nodes[0]
    return {"op": "all_of", "items": nodes}


def _compile_single_op(op: str, args: list[Any], selector: str, path: str) -> dict[str, Any]:
    if op == "present":
        return {"op": "not", "item": {"op": "is_blank", "selector": selector, "ground": "json"}}
    if op == "equals":
        return {"op": "equals", "selector": selector, "expected": args[0] if args else None, "ground": "json"}
    if op == "in_set":
        return {"op": "in_set", "selector": selector, "values": list(args), "ground": "json"}
    if op == "matches":
        return {
            "op": "matches",
            "selector": selector,
            "pattern": str(args[0]) if args else "",
            "ground": "json",
        }
    if op == "no_language":
        return {"op": "no_language", "selector": selector, "language": str(args[0]) if args else "chinese", "ground": "json"}
    if op == "contains":
        return {
            "op": "contains",
            "selector": selector,
            "text": str(args[0]) if args else "",
            "ground": "json",
        }
    if op == "has_number":
        return {"op": "contains_number", "selector": selector, "ground": "json"}
    if op == "count_at_least":
        return {"op": "count_at_least", "selector": selector, "min": int(args[0]) if args else 1, "ground": "json"}
    if op == "count_at_most":
        return {"op": "count_at_most", "selector": selector, "max": int(args[0]) if args else 0, "ground": "json"}
    raise ValueError(f"{path}: unsupported op {op!r}")


def compile_block(
    checkpoint: dict[str, Any],
    block: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compile a checkpoint + optional check block to an ObligationSpec dict."""
    cp_id = str(checkpoint["id"])
    requirement = str(checkpoint.get("requirement") or "").strip()
    severity = str(checkpoint.get("severity") or "BLOCKING")

    if not block:
        return ObligationSpec(
            checkpoint_id=cp_id,
            severity=severity,
            when=None,
            then=None,
            requirement=requirement,
            source="missing_block",
            extract=[],
        ).to_dict() | {"status_class": "advisory", "data_source": "other"}

    data_source = str(block.get("data_source") or "other").strip()
    where = list(block.get("where") or [])

    if data_source in ADVISORY_SOURCES or block.get("check") is None:
        return ObligationSpec(
            checkpoint_id=cp_id,
            severity=severity,
            when=None,
            then=None,
            requirement=requirement,
            source="advisory",
            extract=[],
        ).to_dict() | {"status_class": "advisory", "data_source": data_source}

    when_node = None
    when_raw = block.get("when")
    if when_raw not in (None, "null", ""):
        when_node = _compile_call(str(when_raw), where, f"{cp_id}.when", allow_field_refs=True)

    then_node = _compile_calls(block.get("check"), where, f"{cp_id}.check")

    spec = ObligationSpec(
        checkpoint_id=cp_id,
        severity=severity,
        when=when_node,
        then=then_node,
        unless=None,
        requirement=requirement,
        extract=[],
        source="check_block",
    ).to_dict()
    spec["data_source"] = data_source
    return spec


def compile_checkpoints(
    checkpoints: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cp in checkpoints:
        block = cp.get("check_block")
        out[cp["id"]] = compile_block(cp, block)
    return out
