"""Parse, validate, and compile footer ```check blocks into ObligationSpecs."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from fact_schema import FACT_SELECTORS, checklist_selector, custom_selector, normalize_where_bindings, parse_where_entry
from field_registry import (
    STATUS_ADVISORY,
    STATUS_CHECKABLE,
    STATUS_PENDING,
    STATUS_UNAUTHORED,
    STATUS_UNMAPPED,
    derive_feasibility,
)
from obligation import ObligationSpec, validate_checkspec

ROOT = Path(__file__).resolve().parents[1]

# Legacy authored values still accepted as hints; derived data_source wins at compile.
LEGACY_CHECKABLE_SOURCES = frozenset({"in_report", "IP"})
LEGACY_ADVISORY_SOURCES = frozenset({"PO_booking", "spec_sheet", "email", "external", "other"})
DERIVED_SOURCES = frozenset(
    {"report_content", "report_images", "report_attachments", "out_of_report"}
)
KNOWN_SOURCES = LEGACY_CHECKABLE_SOURCES | LEGACY_ADVISORY_SOURCES | DERIVED_SOURCES

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
        "extract_bool",
        "vision",
    }
)

# Ops that may consume a preceding extract quote when `where` is empty in a list.
_CONSUMING_OPS = frozenset(
    {"equals", "in_set", "matches", "contains", "has_number", "no_language", "present"}
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
        "attachment_content",
        "photo_content",
    }
)

_SELECTOR_PREFIXES = ("report.", "product.", "workmanship.", "checklist.", "custom.")
_CMP_OPS = frozenset({">=", "<=", "!=", "==", ">", "<", "="})

BANNED_QUESTION_SUBSTRINGS = (
    # Keep in sync with data/library/operators.yaml banned_question_substrings
    # and check_format.yaml HARD BANS — vague judge prompts destroy precision.
    "correctly filled",
    "the evidence this rule requires",
    "what this rule requires",
    "required information for this rule",
    "clearly show what this rule",
    "clearly state the required information",
    "satisfy the gi",
    "satisfy the gi requirement",
    "satisfy the requirement",
    "does this field evidence satisfy",
    "does the bound remark/comment satisfy",
    "does this pass",
    "according to the rule",
    "per the requirement",
    "as required by the gi",
)

INTENT_KINDS = frozenset({"checklist", "section", "caption", "remark", "report", "out_of_report"})


def _slug_rule_id(rule_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (rule_id or "").strip().lower()).strip("_") or "rule"


def parse_check_block_text(text: str) -> dict[str, Any]:
    """Parse a ```check fenced block body (simple YAML subset)."""
    data: dict[str, Any] = {}
    current_key: str | None = None
    list_mode = False
    list_items: list[Any] = []
    list_dict_mode = False

    def flush() -> None:
        nonlocal current_key, list_mode, list_items, list_dict_mode
        if current_key is None:
            return
        if list_mode:
            data[current_key] = list_items
        list_mode = False
        list_items = []
        list_dict_mode = False
        current_key = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if list_dict_mode and line.startswith((" ", "\t")) and ":" in stripped:
            key, _, rest = stripped.partition(":")
            key = key.strip()
            val = rest.strip()
            if list_items and isinstance(list_items[-1], dict):
                if val.startswith("[") and val.endswith("]"):
                    inner = val[1:-1].strip()
                    list_items[-1][key] = (
                        []
                        if not inner
                        else [_parse_scalar(p.strip()) for p in _split_list(inner)]
                    )
                else:
                    list_items[-1][key] = _parse_scalar(val)
            continue

        if stripped.startswith("- "):
            if current_key is None:
                raise ValueError(f"list item without key: {stripped}")
            list_mode = True
            item_text = stripped[2:].strip()
            if ":" in item_text:
                key, _, val = item_text.partition(":")
                key = key.strip()
                if key in ("kind", "type"):
                    list_items.append({key: _parse_scalar(val.strip())})
                    list_dict_mode = True
                    continue
            list_dict_mode = False
            list_items.append(_parse_scalar(item_text))
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
    if selector == "unmapped":
        return True
    if selector.startswith("out_of_report"):
        return True
    if selector.startswith("intent:"):
        binding = parse_where_entry(selector)
        return binding.get("type") == "intent" and str(binding.get("kind") or "") in INTENT_KINDS
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


def is_valid_where_entry(entry: Any) -> bool:
    binding = parse_where_entry(entry)
    if binding["type"] in ("out_of_report", "unmapped"):
        return True
    if binding["type"] == "intent":
        kind = str(binding.get("kind") or "")
        field = str(binding.get("field") or "")
        match = binding.get("match") or []
        return kind in INTENT_KINDS and bool(field) and (
            kind not in ("checklist", "section") or bool(match)
        )
    return is_valid_selector(str(binding.get("selector") or ""))


def is_vague_question(question: str) -> bool:
    low = str(question or "").strip().lower()
    return any(fragment in low for fragment in BANNED_QUESTION_SUBSTRINGS)


def _question_from_then(then_node: dict[str, Any] | None) -> str | None:
    if not then_node:
        return None
    op = str(then_node.get("op") or "")
    if op in ("atom", "vision"):
        return str(then_node.get("question") or "")
    if op in ("all_of", "any_of"):
        for item in then_node.get("items") or []:
            q = _question_from_then(item)
            if q:
                return q
    if op == "not":
        return _question_from_then(then_node.get("item"))
    return None


def _then_is_vague_llm_judge(then_node: dict[str, Any] | None) -> bool:
    if not then_node:
        return False
    op = str(then_node.get("op") or "")
    if op in ("atom", "vision"):
        return is_vague_question(str(then_node.get("question") or ""))
    if op in ("all_of", "any_of"):
        leaves = [item for item in (then_node.get("items") or []) if str(item.get("op") or "") in ("atom", "vision")]
        return bool(leaves) and all(
            is_vague_question(str(item.get("question") or "")) for item in leaves
        )
    return False


def _attach_requires_fields(node: dict[str, Any] | None, where_bindings: list[dict[str, Any]]) -> None:
    if not node:
        return
    op = str(node.get("op") or "")
    if op in ("atom", "vision"):
        node["requires_fields"] = where_bindings
        return
    if op in ("all_of", "any_of"):
        for item in node.get("items") or []:
            _attach_requires_fields(item, where_bindings)
    elif op == "not":
        _attach_requires_fields(node.get("item"), where_bindings)


def _uses_extract_bool(check: Any) -> bool:
    if isinstance(check, list):
        return any(_uses_extract_bool(item) for item in check)
    text = str(check or "").strip()
    return text.startswith("extract_bool(") or " extract_bool(" in text


def validate_block(block: dict[str, Any], *, checkpoint_id: str = "") -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    prefix = checkpoint_id or "block"

    legacy_ds = str(block.get("data_source") or "").strip()
    # data_source is optional (derived from where). If present, must be known.
    if legacy_ds and legacy_ds not in KNOWN_SOURCES:
        errors.append(
            {"id": prefix, "field": "data_source", "message": f"unknown data_source {legacy_ds!r}"}
        )

    where = block.get("where")
    if where is None:
        errors.append({"id": prefix, "field": "where", "message": "where is required (use [] for advisory)"})
    elif not isinstance(where, list):
        errors.append({"id": prefix, "field": "where", "message": "where must be a list"})
    else:
        for sel in where:
            if not is_valid_where_entry(sel):
                errors.append(
                    {"id": prefix, "field": "where", "message": f"unknown where entry {sel!r}"}
                )

    where_bindings = normalize_where_bindings(where if isinstance(where, list) else [])
    has_check = block.get("check") not in (None, "null")
    derived = derive_feasibility(
        where_bindings,
        has_check=has_check,
        legacy_data_source=legacy_ds or None,
    )
    data_source = str(derived["data_source"])

    # Advisory / pending / unauthored / unmapped: no further check validation required.
    if derived["status_class"] in (
        STATUS_ADVISORY,
        STATUS_PENDING,
        STATUS_UNAUTHORED,
        STATUS_UNMAPPED,
    ):
        if data_source == "out_of_report" and where not in ([], None) and where:
            # Allow out_of_report markers in where; reject mixed in-report selectors with advisory legacy.
            non_oor = [
                b
                for b in where_bindings
                if b.get("type") != "out_of_report"
                and not str(b.get("selector") or "").startswith("out_of_report")
            ]
            if non_oor and legacy_ds in LEGACY_ADVISORY_SOURCES and not has_check:
                # Legacy advisory with accidental where — keep soft: no hard error.
                pass
        return errors

    # checkable: require a check and validate it
    check = block.get("check")
    if check is None:
        errors.append({"id": prefix, "field": "check", "message": "check is required for checkable rules"})
    else:
        if _uses_extract_bool(check) and not (where or []):
            errors.append(
                {
                    "id": prefix,
                    "field": "where",
                    "message": "extract_bool requires at least one where field",
                }
            )
        try:
            then_preview = _compile_calls(check, where or [], f"{prefix}.check")
            vague_q = _question_from_then(then_preview)
            if vague_q and is_vague_question(vague_q):
                errors.append(
                    {
                        "id": prefix,
                        "field": "check",
                        "message": f"vague LLM question not allowed: {vague_q[:80]}",
                    }
                )
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

    # Function-call form first (extract("… equals …") must not hit infix).
    match = re.match(r"^([a-z_]+)\((.*)\)$", text, re.DOTALL)
    if match:
        op = match.group(1)
        args = _parse_args(match.group(2))
        if op not in OPERATORS:
            raise ValueError(f"{path}: unknown op {op!r}")
        return _compile_op_on_where(op, args, where, path)

    if text in OPERATORS:
        return _compile_op_on_where(text, [], where, path)

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

    raise ValueError(f"{path}: cannot parse {text!r}")


def _quote_atom(path: str, question: str) -> dict[str, Any]:
    atom_id = re.sub(r"[^a-z0-9]+", "_", question.lower())[:48] or "extract"
    leaf_id = f"{path}_{atom_id}"
    return {
        "op": "atom",
        "id": leaf_id,
        "question": question,
        "role": "quote",
        "value_type": "string",
        "ground": "atom",
    }


def _compile_calls(
    check: Any,
    where: list[str],
    path: str,
) -> dict[str, Any]:
    if isinstance(check, list):
        items: list[dict[str, Any]] = []
        last_quote_id: str | None = None
        calls = [str(c).strip() for c in check]
        for i, call in enumerate(calls):
            match = re.match(r"^([a-z_]+)\((.*)\)$", call, re.DOTALL)
            op_name = match.group(1) if match else (call if call in OPERATORS else "")
            next_op = ""
            if i + 1 < len(calls):
                nm = re.match(r"^([a-z_]+)\(", calls[i + 1])
                next_op = nm.group(1) if nm else ""
            if last_quote_id and op_name in _CONSUMING_OPS:
                args = _parse_args(match.group(2)) if match else []
                node = _compile_single_op(
                    op_name,
                    args,
                    f"atom.{last_quote_id}",
                    f"{path}[{i}]",
                )
            elif op_name == "extract":
                question = str(_parse_args(match.group(2))[0]) if match else ""
                atom = _quote_atom(f"{path}[{i}]", question)
                last_quote_id = str(atom["id"])
                # Pair with a following consumer when present; else require non-blank quote.
                if next_op in _CONSUMING_OPS:
                    node = atom
                else:
                    node = {
                        "op": "all_of",
                        "items": [
                            atom,
                            {
                                "op": "not",
                                "item": {
                                    "op": "is_blank",
                                    "selector": f"atom.{atom['id']}",
                                    "ground": "json",
                                },
                            },
                        ],
                    }
                    last_quote_id = None  # consumed by implicit present
            else:
                node = _compile_call(call, where, f"{path}[{i}]")
                if str(node.get("op") or "") == "atom" and str(node.get("role") or "") == "quote":
                    last_quote_id = str(node.get("id") or "")
            items.append(node)
        if len(items) == 1:
            return items[0]
        return {"op": "all_of", "items": items}

    # Solo check: extract => quote + non-blank; extract_bool / others as usual.
    call = str(check).strip()
    match = re.match(r"^extract\((.*)\)$", call, re.DOTALL)
    if match:
        question = str(_parse_args(match.group(1))[0])
        atom = _quote_atom(path, question)
        return {
            "op": "all_of",
            "items": [
                atom,
                {
                    "op": "not",
                    "item": {
                        "op": "is_blank",
                        "selector": f"atom.{atom['id']}",
                        "ground": "json",
                    },
                },
            ],
        }
    return _compile_call(call, where, path)


def _compile_op_on_where(
    op: str,
    args: list[Any],
    where: list[str],
    path: str,
) -> dict[str, Any]:
    if op == "extract":
        if not args:
            raise ValueError(f"{path}: extract requires a question string")
        return _quote_atom(path, str(args[0]))
    if op == "extract_bool":
        if not args:
            raise ValueError(f"{path}: extract_bool requires a question string")
        question = str(args[0])
        atom_id = re.sub(r"[^a-z0-9]+", "_", question.lower())[:48] or op
        return {
            "op": "atom",
            "id": f"{path}_{atom_id}",
            "question": question,
            "role": "required_true",
            "value_type": "boolean",
            "ground": "atom",
        }
    if op == "vision":
        if not args:
            raise ValueError(f"{path}: vision requires a question string")
        question = str(args[0])
        atom_id = re.sub(r"[^a-z0-9]+", "_", question.lower())[:48] or op
        return {
            "op": "vision",
            "id": f"{path}_{atom_id}",
            "question": question,
            "value_type": "boolean",
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
        bindings = normalize_where_bindings(where) if where else []
        if bindings and bindings[0]["type"] == "selector" and bindings[0].get("selector"):
            selector = str(bindings[0]["selector"])
        else:
            selector = "report.inspector_text"
        return {"op": "contains", "selector": selector, "text": term, "ground": "json"}

    if op == "scan_absent":
        term = str(args[0]) if args else ""
        bindings = normalize_where_bindings(where) if where else []
        if bindings and bindings[0]["type"] == "selector" and bindings[0].get("selector"):
            selector = str(bindings[0]["selector"])
        else:
            selector = "report.inspector_text"
        return {
            "op": "not",
            "item": {"op": "contains", "selector": selector, "text": term, "ground": "json"},
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

    targets = normalize_where_bindings(where) if where else []
    nodes: list[dict[str, Any]] = []
    for binding in targets or [{"type": "selector", "selector": ""}]:
        if binding["type"] == "intent":
            nodes.append(_compile_single_op(op, args, "", path, binding=binding))
        else:
            nodes.append(_compile_single_op(op, args, str(binding["selector"]), path))
    if len(nodes) == 1:
        return nodes[0]
    return {"op": "all_of", "items": nodes}


def _compile_single_op(
    op: str,
    args: list[Any],
    selector: str,
    path: str,
    *,
    binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if op == "present":
        node: dict[str, Any] = {"op": "not", "item": {"op": "is_blank", "ground": "json"}}
        if binding:
            node["item"]["binding"] = binding
        else:
            node["item"]["selector"] = selector
        return node
    base: dict[str, Any] = {"op": op, "ground": "json"}
    if binding:
        base["binding"] = binding
    else:
        base["selector"] = selector
    if op == "equals":
        base["expected"] = args[0] if args else None
        return base
    if op == "in_set":
        base["values"] = list(args)
        return base
    if op == "matches":
        base["pattern"] = str(args[0]) if args else ""
        return base
    if op == "no_language":
        base["language"] = str(args[0]) if args else "chinese"
        return base
    if op == "contains":
        base["text"] = str(args[0]) if args else ""
        return base
    if op == "has_number":
        base["op"] = "contains_number"
        return base
    if op == "count_at_least":
        base["min"] = int(args[0]) if args else 1
        return base
    if op == "count_at_most":
        base["max"] = int(args[0]) if args else 0
        return base
    raise ValueError(f"{path}: unsupported op {op!r}")


def compile_block(
    checkpoint: dict[str, Any],
    block: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compile a checkpoint + optional check block to an ObligationSpec dict.

    data_source and status_class are DERIVED from the field registry
    (where bindings), not trusted from authored data_source alone.
    """
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
        ).to_dict() | {
            "status_class": STATUS_UNMAPPED,
            "data_source": "report_content",
            "schema_version": 1,
        }

    legacy_ds = str(block.get("data_source") or "").strip() or None
    where = list(block.get("where") or [])
    where_bindings = normalize_where_bindings(where)
    has_check = block.get("check") not in (None, "null", "")
    derived = derive_feasibility(
        where_bindings,
        has_check=has_check,
        legacy_data_source=legacy_ds,
    )
    data_source = str(derived["data_source"])
    status_class = str(derived["status_class"])

    # Non-checkable paths: advisory / pending / unauthored / unmapped
    if status_class in (
        STATUS_ADVISORY,
        STATUS_PENDING,
        STATUS_UNAUTHORED,
        STATUS_UNMAPPED,
    ) or not has_check:
        source = {
            STATUS_ADVISORY: "advisory",
            STATUS_PENDING: "pending",
            STATUS_UNAUTHORED: "unauthored",
            STATUS_UNMAPPED: "unmapped",
        }.get(status_class, "unmapped")
        out = ObligationSpec(
            checkpoint_id=cp_id,
            severity=severity,
            when=None,
            then=None,
            requirement=requirement,
            source=source,
            extract=[],
        ).to_dict()
        out.update(
            {
                "status_class": status_class,
                "data_source": data_source,
                "where_bindings": where_bindings,
                "schema_version": 1,
                "modality": derived.get("modality"),
                "processor": derived.get("processor"),
            }
        )
        if derived.get("pending_processor"):
            out["pending_processor"] = derived["pending_processor"]
        return out

    when_node = None
    when_raw = block.get("when")
    if when_raw not in (None, "null", ""):
        when_node = _compile_call(str(when_raw), where, f"{cp_id}.when", allow_field_refs=True)

    then_node = _compile_calls(block.get("check"), where, f"{cp_id}.check")

    if _then_is_vague_llm_judge(then_node):
        return ObligationSpec(
            checkpoint_id=cp_id,
            severity=severity,
            when=None,
            then=None,
            requirement=requirement,
            source="advisory",
            extract=[],
        ).to_dict() | {
            "status_class": STATUS_ADVISORY,
            "data_source": data_source,
            "where_bindings": where_bindings,
            "advisory_reason": "vague_llm_question",
            "schema_version": 1,
        }

    _attach_requires_fields(then_node, where_bindings)
    _attach_requires_fields(when_node, where_bindings)

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
    spec["status_class"] = STATUS_CHECKABLE
    spec["where_bindings"] = where_bindings
    spec["schema_version"] = 1
    spec["modality"] = derived.get("modality")
    spec["processor"] = derived.get("processor")
    return spec


def compile_checkpoints(
    checkpoints: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cp in checkpoints:
        block = cp.get("check_block")
        out[cp["id"]] = compile_block(cp, block)
    return out
