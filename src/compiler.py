"""Compile GI checkpoints into conditional-obligation CheckSpecs (WHEN/THEN/UNLESS)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from fact_schema import checklist_selector, custom_selector, legacy_path_to_selector
from obligation import ObligationSpec, derive_tier, save_checkspecs, validate_checkspec

# Bump when compile heuristics change so cached CheckSpecs invalidate.
COMPILER_VERSION = "2026-07-14.11"

_BOILERPLATE_FAIL = re.compile(r"^Report does not satisfy:", re.I)
_PHOTO_METADATA_SIGNALS = (
    "must not be included",
    "no photo",
    "only 1 photo",
    "1 photo per",
    "at most 1",
    "more than 1 photo",
    "more than one photo",
    "exactly 1 photo",
    "photos uploaded",
    "do not upload",
)
_PASS_PHOTO_SIGNALS = (
    "unless the test fails",
    "only a failure requires photos",
    "must not be included in the report unless",
    "photos must not",
    "no photos when pass",
)


def _substantive_fail_lines(fail_if: list[str]) -> list[str]:
    out: list[str] = []
    for line in fail_if or []:
        text = str(line).strip()
        if not text or _BOILERPLATE_FAIL.match(text):
            continue
        out.append(text)
    return out[:3]


def _checklist_name_from_checkpoint(checkpoint: dict[str, Any]) -> str | None:
    for term in checkpoint.get("focus_terms") or []:
        text = str(term).strip()
        if len(text) >= 4 and "checklist" not in text.lower():
            return text.split("/")[0].strip()
    req = str(checkpoint.get("requirement") or "")
    match = re.match(r"^([^—]+)", req)
    if match:
        head = match.group(1).strip()
        if len(head) >= 4:
            return head
    return None


def _json_equals(selector: str, expected: Any) -> dict[str, Any]:
    return {"op": "equals", "selector": selector, "expected": expected, "ground": "json"}


def _json_count_at_most(selector: str, maximum: int) -> dict[str, Any]:
    return {"op": "count_at_most", "selector": selector, "max": maximum, "ground": "json"}


def _json_count_at_least(selector: str, minimum: int) -> dict[str, Any]:
    return {"op": "count_at_least", "selector": selector, "min": minimum, "ground": "json"}


def _json_not_blank(selector: str) -> dict[str, Any]:
    return {"op": "not", "item": {"op": "is_blank", "selector": selector, "ground": "json"}}


def _atom(id_: str, question: str, *, role: str = "boolean") -> dict[str, Any]:
    return {"op": "atom", "id": id_, "question": question, "role": role, "ground": "atom"}


def _vision(id_: str, question: str) -> dict[str, Any]:
    return {"op": "vision", "id": id_, "question": question, "ground": "vision"}


def _violation_atom(cp_id: str, checkpoint: dict[str, Any]) -> dict[str, Any]:
    fail_lines = _substantive_fail_lines(checkpoint.get("fail_if") or [])
    question = (
        "Does the report evidence explicitly show a violation of this requirement? "
        "Answer true only if there is clear contradicting evidence — not mere absence of detail."
    )
    if fail_lines:
        question += " Pay particular attention to: " + "; ".join(fail_lines[:2])
    return _atom(f"{cp_id}_violation", question, role="violation")


def _fail_if_obligation(cp_id: str, checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Targeted THEN: each substantive fail_if line is a violation atom (all must be clear)."""
    fail_lines = _substantive_fail_lines(checkpoint.get("fail_if") or [])
    if not fail_lines:
        return _violation_atom(cp_id, checkpoint)
    items = [
        _atom(
            f"{cp_id}_fail_{i}",
            (
                "Does the report evidence clearly show this failing condition? "
                f"Condition: {line}. Answer true only with clear contradicting evidence."
            ),
            role="violation",
        )
        for i, line in enumerate(fail_lines)
    ]
    if len(items) == 1:
        return items[0]
    return {"op": "all_of", "items": items}


def _unless_from_never_flag(cp_id: str, never_flag_if: list[str]) -> dict[str, Any] | None:
    excuses = [str(x).strip() for x in (never_flag_if or []) if str(x).strip()]
    if not excuses:
        return None
    items = [
        _atom(
            f"{cp_id}_excuse_{i}",
            f"Does this never-flag condition apply (if yes, do not flag)? Condition: {text}",
            role="excuse",
        )
        for i, text in enumerate(excuses)
    ]
    if len(items) == 1:
        return items[0]
    return {"op": "any_of", "items": items}


_APPLIES_JSON: dict[str, dict[str, Any]] = {
    # DFI: carton-drop observation required when drop test has findings
    "carton_drop_has_findings": {
        "when": {"op": "equals", "selector": checklist_selector("Carton Drop Test", "result"), "expected": "FAIL", "ground": "json"},
        "name_hints": ("carton drop", "drop test"),
    },
}


def _when_from_applies_when(applies_when: dict[str, Any], cp_id: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for key, value in applies_when.items():
        mapped = _APPLIES_JSON.get(str(key))
        if mapped and value in (True, "true", "yes", 1):
            items.append(dict(mapped["when"]))
            continue
        question = f"Does this report match the condition '{key}' = {value!r} for this rule to apply?"
        items.append(_atom(f"{cp_id}_applies_{key}", question, role="required_true"))
    if len(items) == 1:
        return items[0]
    return {"op": "all_of", "items": items}


def _combined_text(checkpoint: dict[str, Any]) -> str:
    parts = [
        str(checkpoint.get("requirement") or ""),
        str(checkpoint.get("scope_detail") or ""),
        " ".join(str(x) for x in (checkpoint.get("fail_if") or [])),
    ]
    return " ".join(parts).lower()


def _looks_like_photo_content(checkpoint: dict[str, Any]) -> bool:
    if checkpoint.get("photo_check") == "content":
        return True
    text = _combined_text(checkpoint)
    content_signals = (
        "photo must show",
        "photos must show",
        "must show consumer pack",
        "blank image",
        "hclp, no photo",
        "cover photo must",
        "frontal angle",
        "product name readable",
        "must not appear in photos",
        "tape measure",
        "photo content",
    )
    return any(sig in text for sig in content_signals)


def _compile_remark_when_fail(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN result=FAIL THEN comment not blank — only with an explicit checklist focus term."""
    text = _combined_text(checkpoint)
    # Prefer real checklist names from focus_terms (avoid parsing requirement prose as a name).
    name = None
    for term in checkpoint.get("focus_terms") or []:
        text_term = str(term).strip()
        if len(text_term) >= 4 and "checklist" not in text_term.lower():
            name = text_term.split("/")[0].strip()
            break
    if not name:
        return None
    remark_signals = (
        "remark must",
        "must describe",
        "observation remark",
        "comment must",
        "must state",
        "remark does not describe",
        "no separate remark",
        "not remarked",
        "remark missing",
        "comment is required",
        "add a remark",
    )
    fail_gate = (
        "has findings",
        "when fail",
        "if fail",
        "result is fail",
        "result = fail",
        "drop test has findings",
        "finding",
        "failed",
        "unless the test fails",
    )
    if not any(sig in text for sig in remark_signals):
        return None
    # Conditional obligation: never require a remark without a FAIL (or findings) gate.
    # Ungated "comment not blank" floods false positives on PASS / unanswered items.
    if not any(sig in text for sig in fail_gate):
        return None
    when = _json_equals(checklist_selector(name, "result"), "FAIL")
    then = _json_not_blank(checklist_selector(name, "comment"))
    return {"when": when, "then": then, "source": "remark_when_fail"}


def _compile_applies_when_obligation(
    checkpoint: dict[str, Any],
    cp_id: str,
) -> dict[str, Any]:
    """Compile applies_when → WHEN, with structured THEN when possible."""
    applies = checkpoint.get("applies_when") or {}
    when = _when_from_applies_when(applies, cp_id)
    requirement = str(checkpoint.get("requirement") or "").lower()
    # Remarks gated by findings: require a non-blank global remark (common DFI shape).
    if (
        cp_id.startswith("remarks.")
        or "remark" in requirement
        or "describe" in requirement
    ):
        then = _json_not_blank("report.global_remark")
        source = "remark_global"
    else:
        then = _fail_if_obligation(cp_id, checkpoint)
        source = "applies_when"
    return {"when": when, "then": then, "source": source}

def _answered_yes_no(selector_name: str) -> dict[str, Any]:
    """True when a Yes/No checklist field is answered (values or result)."""
    return {
        "op": "any_of",
        "items": [
            {
                "op": "contains",
                "selector": checklist_selector(selector_name, "values"),
                "text": "yes",
                "ground": "json",
            },
            {
                "op": "contains",
                "selector": checklist_selector(selector_name, "values"),
                "text": "no",
                "ground": "json",
            },
            {
                "op": "in_set",
                "selector": checklist_selector(selector_name, "result"),
                "values": ["YES", "NO"],
                "ground": "json",
            },
        ],
    }


def _compile_destination_gated_yes_no(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN destination is KC THEN HA/HCLP-style fields must be Yes or No.

    Non-KC N/A side stays deferred (needs reliable destination coverage).
    """
    text = _combined_text(checkpoint)
    if not any(sig in text for sig in ("kansas city", "kc hkbo", "ships to usa")):
        return None
    if not any(sig in text for sig in ("yes or no", "answered yes or no", "ha and hclp")):
        return None
    fields: list[str] = []
    for term in checkpoint.get("focus_terms") or []:
        t = str(term).strip()
        low = t.lower()
        if "destination" in low:
            continue
        if "ha" in low or "hclp" in low or "high attention" in low:
            fields.append(t.split("/")[0].strip())
    if len(fields) < 1:
        return None
    when = {
        "op": "contains",
        "selector": "report.destinations",
        "text": "kc",
        "ground": "json",
    }
    then_items = [_answered_yes_no(name) for name in fields[:2]]
    then = then_items[0] if len(then_items) == 1 else {"op": "all_of", "items": then_items}
    return {"when": when, "then": then, "source": "destination_gated_yes_no"}


def _compile_hclp_no_product_photos(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN HCLP=Yes THEN no retail product photos (vision obligation)."""
    text = _combined_text(checkpoint)
    if "hclp" not in text:
        return None
    if not any(
        sig in text
        for sig in (
            "no product photos",
            "blank image",
            "hclp, no photo",
            "contain no product photos",
        )
    ):
        return None
    cp_id = str(checkpoint.get("id") or "cp")
    when = {
        "op": "any_of",
        "items": [
            {
                "op": "contains",
                "selector": checklist_selector("HCLP", "values"),
                "text": "yes",
                "ground": "json",
            },
            {
                "op": "equals",
                "selector": checklist_selector("HCLP", "result"),
                "expected": "YES",
                "ground": "json",
            },
        ],
    }
    then = _vision(
        f"{cp_id}_hclp_blank",
        (
            "For HCLP products, every product image must be blank / placeholder with caption "
            "like 'HCLP, no photo'. Are all product photos blank (no retail product visible)?"
        ),
    )
    return {"when": when, "then": then, "source": "hclp_no_product_photos"}


def _compile_must_not_be_na(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    text = _combined_text(checkpoint)
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    if not any(
        sig in text
        for sig in (
            "must not be n/a",
            "must not be na",
            "cannot be n/a",
            "should not be n/a",
            "n/a is not allowed",
            "must be answered yes or no",
            "must not select n/a",
        )
    ):
        return None
    # Destination-/channel-gated yes-no fields are conditional obligations — not ungated.
    if any(
        sig in text
        for sig in (
            "if the order ships",
            "if the order does not",
            "ships to",
            "does not ship",
            "destination",
            "kansas city",
            " if ",
            " when ",
        )
    ):
        return None
    # Obligation: result must not equal NOT_APPLICABLE
    then = {
        "op": "not",
        "item": _json_equals(checklist_selector(name, "result"), "NOT_APPLICABLE"),
    }
    return {"when": None, "then": then, "source": "must_not_be_na"}


def _compile_checkpoint_fail_implies_overall_fail(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN checklist ≠ PASS THEN overall result = FAIL (Hallmark SR/FR pattern)."""
    text = _combined_text(checkpoint)
    if not any(
        sig in text
        for sig in (
            "overall result must be fail",
            "overall report result must be fail",
            "overall result is fail",
            "if not passed, the overall",
            "if not passed, overall",
        )
    ):
        return None
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    when = {
        "op": "not",
        "item": _json_equals(checklist_selector(name, "result"), "PASS"),
    }
    then = _json_equals("report.overall_result", "FAIL")
    return {"when": when, "then": then, "source": "checkpoint_fail_implies_overall"}


_PHOTO_REQUIRED_SIGNALS = (
    "photos must be included",
    "photo must be included",
    "photos are required",
    "must upload",
    "must be uploaded",
    "photos of all",
    "must include photo",
    "must include photos",
    "override email must be uploaded",
    "must be uploaded in the report",
)

# Conditional attachment: only obligates evidence when a checklist is not PASS.
_ATTACHMENT_WHEN_NOT_PASS_SIGNALS = (
    "if sr report result shows a failure",
    "override email",
    "but the factory provides",
    "only a failure requires",
    "must not be included in the report unless",
    "unless the test fails",
)


def _compile_attachment_when_not_pass(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN checklist ≠ PASS AND a claim/override is present THEN attachment evidence.

    Cross-GI shape: failure alone is not enough — the report must assert the
    claim that obligates the upload (e.g. override email mentioned).
    """
    text = _combined_text(checkpoint)
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    if not any(sig in text for sig in _PHOTO_REQUIRED_SIGNALS):
        return None
    if not any(sig in text for sig in _ATTACHMENT_WHEN_NOT_PASS_SIGNALS):
        return None
    cp_id = str(checkpoint.get("id") or "cp")
    not_pass = {
        "op": "not",
        "item": _json_equals(checklist_selector(name, "result"), "PASS"),
    }
    # Soft atom: only the claim that triggers the attachment obligation.
    claim = _atom(
        f"{cp_id}_attachment_claim",
        (
            "Does the report clearly state that a factory/Hallmark override email "
            "(or equivalent waiver/approval document) was provided for this checklist "
            "failure? Answer true only if that claim is explicitly present."
        ),
        role="required_true",
    )
    when = {"op": "all_of", "items": [not_pass, claim]}
    then = _json_count_at_least(checklist_selector(name, "photo_count"), 1)
    return {"when": when, "then": then, "source": "attachment_when_not_pass"}


def _compile_photos_required(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """Unconditional photo presence — never apply to if/when/override clauses."""
    text = _combined_text(checkpoint)
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    if not any(sig in text for sig in _PHOTO_REQUIRED_SIGNALS):
        return None
    # Conditional obligations belong in attachment_when_not_pass, not here.
    if any(sig in text for sig in _ATTACHMENT_WHEN_NOT_PASS_SIGNALS):
        return None
    if any(
        sig in text
        for sig in (
            " if ",
            " when ",
            " unless ",
            "only if",
            "only when",
            "override",
        )
    ):
        return None
    then = _json_count_at_least(checklist_selector(name, "photo_count"), 1)
    return {"when": None, "then": then, "source": "photos_required"}


def _compile_photos_require_captions(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN photo_count >= 1 THEN every photo has a non-blank caption."""
    text = _combined_text(checkpoint)
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    if not any(
        sig in text
        for sig in (
            "caption",
            "captions",
            "picturetags",
            "picture tags",
            "tagged by sku",
            "named/tagged",
            "tag feature",
        )
    ):
        return None
    if not any(
        sig in text
        for sig in (
            "all photo",
            "every photo",
            "each photo",
            "must have caption",
            "must include caption",
            "add captions",
            "captions to all",
            "captions as per",
            "with captions",
            "caption accordingly",
        )
    ):
        return None
    when = {
        "op": "compare",
        "selector": checklist_selector(name, "photo_count"),
        "value": 0,
        "cmp": ">",
        "ground": "json",
    }
    then = {
        "op": "compare",
        "left": checklist_selector(name, "caption_count"),
        "right": checklist_selector(name, "photo_count"),
        "cmp": ">=",
        "ground": "json",
    }
    return {"when": when, "then": then, "source": "photos_require_captions"}


def _compile_spotlight_required(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN photos exist THEN at least one spotlight image."""
    text = _combined_text(checkpoint)
    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    if "spotlight" not in text:
        return None
    when = {
        "op": "compare",
        "selector": checklist_selector(name, "photo_count"),
        "value": 0,
        "cmp": ">",
        "ground": "json",
    }
    then = _json_count_at_least(checklist_selector(name, "spotlight_count"), 1)
    return {"when": when, "then": then, "source": "spotlight_required"}


def _compile_qty_discrepancy_remark(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """WHEN packed/ordered differ THEN remark must explain (quantity-discrepancy pattern)."""
    text = _combined_text(checkpoint)
    cp_id = str(checkpoint.get("id") or "")
    signals = (
        "discrepancy between the booking quantity",
        "shortage or overage",
        "overage",
        "shortage",
        "qty discrepancy",
        "quantity discrepancy",
        "on-site quantity",
    )
    if not any(sig in text for sig in signals):
        return None
    when = {
        "op": "compare",
        "left": "product._first.real_packed_quantity",
        "right": "product._first.ordered_quantity",
        "cmp": "!=",
        "ground": "json",
    }
    # Ribkoff-style qty explanations almost always state a packed %; blank injects lack it.
    then = {
        "op": "any_of",
        "items": [
            {"op": "contains", "selector": "report.global_remark", "text": "%", "ground": "json"},
            _atom(
                f"{cp_id}_qty_remark",
                (
                    "Does a remark in the report clearly explain the quantity discrepancy "
                    "(shortage or overage vs booking)? Answer true only if an explicit explanation is present."
                ),
                role="required_true",
            ),
        ],
    }
    return {"when": when, "then": then, "source": "qty_discrepancy_remark"}


def _compile_structured_obligation(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """Try reusable structured patterns before generic atoms."""
    for builder in (
        _compile_qty_discrepancy_remark,
        _compile_checkpoint_fail_implies_overall_fail,
        _compile_attachment_when_not_pass,
        _compile_destination_gated_yes_no,
        _compile_hclp_no_product_photos,
        _compile_photos_require_captions,
        _compile_spotlight_required,
        _compile_must_not_be_na,
        _compile_photos_required,
        _compile_remark_when_fail,
        _compile_photo_metadata,
    ):
        result = builder(checkpoint)
        if result:
            if builder is _compile_photo_metadata:
                return {
                    "when": result.get("when"),
                    "then": result["then"],
                    "source": "photo_metadata",
                }
            return result
    return None


def _compile_photo_metadata(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    text = " ".join(
        str(checkpoint.get(k) or "")
        for k in ("requirement", "scope_detail")
    ).lower()
    fail_text = " ".join(str(x) for x in (checkpoint.get("fail_if") or [])).lower()
    combined = text + " " + fail_text

    # Rules that require photos to be present → atom tier, not metadata restriction.
    if any(
        sig in combined
        for sig in (
            "must be included",
            "must include",
            "photos must be included",
            "photos are required",
            "must upload",
            "must be uploaded",
            "photos of all",
        )
    ):
        return None

    if not any(sig in combined for sig in _PHOTO_METADATA_SIGNALS + _PASS_PHOTO_SIGNALS):
        return None

    name = _checklist_name_from_checkpoint(checkpoint)
    if not name:
        return None
    result_sel = checklist_selector(name, "result")
    photo_sel = checklist_selector(name, "photo_count")

    when: dict[str, Any] | None = None
    if any(sig in combined for sig in _PASS_PHOTO_SIGNALS):
        when = _json_equals(result_sel, "PASS")

    then: dict[str, Any]
    if "at most 1" in combined or "only 1 photo" in combined or "1 photo per" in combined:
        then = _json_count_at_most(photo_sel, 1)
    else:
        then = _json_count_at_most(photo_sel, 0)

    return {"when": when, "then": then}


def _operator_to_obligation(
    hand_spec: dict[str, Any],
    checkpoint: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, Any] | None, list[dict[str, Any]]]:
    """Convert legacy hand operator spec to WHEN/THEN/UNLESS + extract defs."""
    op = str(hand_spec.get("operator") or "")
    params = hand_spec.get("params") or {}
    extract = list(hand_spec.get("extract") or [])
    when: dict[str, Any] | None = None
    unless: dict[str, Any] | None = None
    then: dict[str, Any]

    if op == "no_photos_when_pass":
        when = _json_equals(legacy_path_to_selector(params["result_field"]), "PASS")
        then = _json_count_at_most(legacy_path_to_selector(params["photos_field"]), 0)
    elif op == "no_photos_allowed":
        then = _json_count_at_most(legacy_path_to_selector(params["photos_field"]), 0)
    elif op == "photo_count_at_most":
        then = _json_count_at_most(
            legacy_path_to_selector(params["photos_field"]),
            int(params.get("max", 1)),
        )
    elif op == "comment_has_number":
        comment_sel = legacy_path_to_selector(params["comment_field"])
        then = {
            "op": "all_of",
            "items": [
                {"op": "not", "item": {"op": "is_blank", "selector": comment_sel, "ground": "json"}},
                {"op": "contains_number", "selector": comment_sel, "ground": "json"},
            ],
        }
    elif op == "equals":
        then = _json_equals(legacy_path_to_selector(params["field"]), params.get("expected"))
    elif op == "ratio_at_least":
        then = {
            "op": "ratio_at_least",
            "numerator": legacy_path_to_selector(params["numerator"]),
            "denominator": legacy_path_to_selector(params["denominator"]),
            "min": params.get("min", 0),
            "ground": "json",
        }
    elif op == "overall_pass_requires_ratio":
        when = _json_equals(legacy_path_to_selector(params.get("result_field", "summary.inspection_result")), "PASS")
        ratio = params.get("ratio") or {}
        then = {
            "op": "ratio_at_least",
            "numerator": legacy_path_to_selector(ratio["numerator"]),
            "denominator": legacy_path_to_selector(ratio["denominator"]),
            "min": ratio.get("min", 0),
            "ground": "json",
        }
    elif op == "must_not_be_na":
        result_sel = legacy_path_to_selector(params["result_field"])
        values_sel = legacy_path_to_selector(params.get("values_field", ""))
        when = _json_equals(result_sel, "NOT_APPLICABLE")
        if params.get("flag_all_na"):
            then = {"op": "false", "ground": "json"}
        else:
            then = {
                "op": "not",
                "item": {"op": "contains", "selector": values_sel, "text": "no logo", "ground": "json"},
            }
    elif op == "filename_matches":
        then = {
            "op": "filename_matches",
            "selector": legacy_path_to_selector(params["filenames_field"]),
            "pattern": params.get("pattern", "Measurement Chart-{style}.xlsx"),
            "ground": "json",
        }
    elif op == "all_true":
        # Defect/remark checklists of this shape only apply when findings exist.
        when = {
            "op": "any_of",
            "items": [
                {
                    "op": "compare",
                    "selector": "workmanship.found_critical",
                    "value": 0,
                    "cmp": ">",
                    "ground": "json",
                },
                {
                    "op": "compare",
                    "selector": "workmanship.found_major",
                    "value": 0,
                    "cmp": ">",
                    "ground": "json",
                },
                {
                    "op": "compare",
                    "selector": "workmanship.found_minor",
                    "value": 0,
                    "cmp": ">",
                    "ground": "json",
                },
            ],
        }
        atom_items = []
        for field_path in params.get("fields") or []:
            field_path = str(field_path)
            for definition in extract:
                if definition.get("field") == field_path:
                    atom_items.append(
                        _atom(
                            f"{checkpoint['id']}:{field_path}",
                            str(definition.get("question") or f"What is {field_path}?"),
                            role="required_true",
                        )
                    )
                    break
        # Blank remarks cannot satisfy defect-breakdown atoms (avoid LLM hallucinating structure).
        # A remark that already states PO + % satisfies the obligation shape deterministically.
        atom_block: dict[str, Any] = (
            {"op": "all_of", "items": atom_items} if atom_items else {"op": "true"}
        )
        then = {
            "op": "all_of",
            "items": [
                {
                    "op": "not",
                    "item": {"op": "is_blank", "selector": "report.global_remark", "ground": "json"},
                },
                {
                    "op": "any_of",
                    "items": [
                        {
                            "op": "matches",
                            "selector": "report.global_remark",
                            "pattern": r"\bPO\b.*%",
                            "ground": "json",
                        },
                        atom_block,
                    ],
                },
            ],
        }
    else:
        then = _violation_atom(checkpoint["id"], checkpoint)

    return when, then, unless, extract


def compile_checkpoint(
    checkpoint: dict[str, Any],
    hand_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile one checkpoint to an obligation CheckSpec."""
    cp_id = checkpoint["id"]
    requirement = str(checkpoint.get("requirement") or "").strip()
    when: dict[str, Any] | None = None
    unless = _unless_from_never_flag(cp_id, checkpoint.get("never_flag_if") or [])
    then: dict[str, Any]
    extract: list[dict[str, Any]] = []
    source = "compiled"

    if hand_spec and hand_spec.get("operator"):
        when, then, hand_unless, extract = _operator_to_obligation(hand_spec, checkpoint)
        unless = hand_unless
        source = "hand_operator"
    elif checkpoint.get("applies_when"):
        compiled = _compile_applies_when_obligation(checkpoint, cp_id)
        when = compiled.get("when")
        then = compiled["then"]
        source = str(compiled.get("source") or "applies_when")
    else:
        structured = _compile_structured_obligation(checkpoint)
        if structured:
            when = structured.get("when")
            then = structured["then"]
            source = str(structured.get("source") or "structured")
        elif _looks_like_photo_content(checkpoint):
            then = _vision(
                f"{cp_id}_vision",
                f"Does photo content satisfy this requirement? {requirement[:300]}",
            )
            source = "photo_content"
        else:
            then = _fail_if_obligation(cp_id, checkpoint)
            source = "fail_if_atoms"

    spec = ObligationSpec(
        checkpoint_id=cp_id,
        severity=str(checkpoint.get("severity") or "BLOCKING"),
        when=when,
        then=then,
        unless=unless,
        requirement=requirement,
        extract=extract,
        source=source,
    )
    return spec.to_dict()


def compile_checkpoints(
    checkpoints: list[dict[str, Any]],
    hand_specs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    hand_specs = hand_specs or {}
    return {
        cp["id"]: compile_checkpoint(cp, hand_specs.get(cp["id"]))
        for cp in checkpoints
    }


def source_hash(checkpoints_path: Path, hand_specs_path: Path | None = None) -> str:
    h = hashlib.sha256()
    h.update(COMPILER_VERSION.encode("utf-8"))
    h.update(checkpoints_path.read_bytes())
    if hand_specs_path and hand_specs_path.exists():
        h.update(hand_specs_path.read_bytes())
    return h.hexdigest()[:16]


def compile_gi(
    checkpoints_path: Path,
    output_path: Path,
    *,
    hand_specs_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    from gi_review import load_checkpoints
    from checkspec import load_hand_specs

    checkpoints = load_checkpoints(checkpoints_path)
    hand = load_hand_specs(hand_specs_path) if hand_specs_path else {}
    specs = compile_checkpoints(checkpoints, hand)
    errors: list[str] = []
    for cp_id, spec in specs.items():
        spec_errors = validate_checkspec(spec)
        if spec_errors:
            errors.extend(f"{cp_id}: {e}" for e in spec_errors)
    if errors:
        raise ValueError("CheckSpec validation failed:\n" + "\n".join(errors[:20]))

    meta = {
        "source": str(checkpoints_path),
        "hand_specs": str(hand_specs_path) if hand_specs_path else None,
        "checkpoint_count": len(specs),
        "source_hash": source_hash(checkpoints_path, hand_specs_path),
    }
    save_checkspecs(output_path, specs, meta)
    return specs


def load_cached_or_compile(
    checkpoints: list[dict[str, Any]],
    *,
    cache_path: Path | None = None,
    hand_specs: dict[str, dict[str, Any]] | None = None,
    checkpoints_path: Path | None = None,
    hand_specs_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Load cached CheckSpecs when hash matches; otherwise compile in memory."""
    if cache_path and cache_path.exists() and checkpoints_path:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        meta = cached.get("meta") or {}
        expected = source_hash(checkpoints_path, hand_specs_path)
        if meta.get("source_hash") == expected:
            return cached.get("specs") or {}
    return compile_checkpoints(checkpoints, hand_specs)
