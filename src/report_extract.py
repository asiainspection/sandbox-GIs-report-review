#!/usr/bin/env python3
"""
Semantic extractors: QIMAone report JSON -> typed Python facts.

This is the single parsing layer. It reads the raw platform payload and returns
plain dicts/dataclasses of *facts* (translations resolved, photos counted,
quantities and AQL surfaced with unambiguous names). It renders nothing and
decides nothing:

- ``report_to_ir.py`` turns these facts into the IR the checks read.
- ``report_to_md.py`` turns the same facts into human-readable Markdown.

Keeping extraction here (instead of inside the Markdown renderer) means the IR no
longer depends on a renderer, and both outputs share one source of truth for
"what the PDF means". Facts only — judgments (e.g. "packed < 80%") belong to the
check engine, not here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


GENERIC_COMMENTS = {
    "checked ok",
    "ok",
    "yes",
    "n/a",
    "na",
    "pass",
    "passed",
    "good",
    "low risk",
    "yes confirm the factory location is the same as booked by the client.",
    "tools is callibrated",
    "factory disclaimer, draft report, and coc is signed by inspector and factory representatives",
}

ATTENTION_RESULTS = {"FAIL", "FAILED", "PENDING"}
PASS_RESULTS = {"PASS", "NOT_APPLICABLE"}
SKIP_ACTION_TYPES = {
    "INSPECTOR_ACKNOWLEDGMENT",
    "REPORT",
    "ADDENDUM",
}

SKIP_CUSTOM_FIELD_LABELS = {
    "qspinspectionid",
    "hasbeensyncedautomatically",
}


@dataclass
class CheckItem:
    path: str
    name: str
    result: str
    values: list[str] = field(default_factory=list)
    comment: str = ""
    photos: int = 0
    spotlight: int = 0
    photo_captions: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    table_md: str = ""
    instruction: str = ""
    expected_result: str = ""
    not_applicable: bool = False
    section: str = ""

    @property
    def needs_attention(self) -> bool:
        if self.not_applicable:
            return False
        if self.result in ATTENTION_RESULTS:
            return True
        joined = " ".join(self.values).upper()
        if any(token in joined for token in ("NOT OK", "FAILED", "PENDING")):
            return True
        comment = self.comment.strip().lower()
        if comment and comment not in GENERIC_COMMENTS:
            if self.result != "NO_RESULT" or len(self.comment) > 12:
                return True
        return False


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def translated_field(obj: dict[str, Any] | None, field: str, *, fallback: Any = None) -> str:
    """Prefer translations.en[field]; ignore all other translation locales."""
    if not isinstance(obj, dict):
        return clean_text(fallback)
    translations = obj.get("translations") or {}
    english = translations.get("en") if isinstance(translations, dict) else None
    if isinstance(english, dict):
        english_value = english.get(field)
        if english_value is not None and clean_text(english_value):
            return clean_text(english_value)
    if field in obj:
        return clean_text(obj.get(field))
    return clean_text(fallback)


def translated_name(obj: dict[str, Any] | None, *, fallback: str = "") -> str:
    return translated_field(obj, "name", fallback=fallback) or fallback


def format_address(entity: dict[str, Any] | None) -> str:
    if not entity:
        return ""
    address = entity.get("address") or {}
    country = translated_field((address.get("country") or {}), "label") or clean_text(
        (address.get("country") or {}).get("label")
    )
    parts = [
        translated_name(entity),
        clean_text(address.get("street")),
        clean_text(address.get("city")),
        country,
    ]
    return ", ".join(part for part in parts if part)


def comment_message(comment: Any) -> str:
    if isinstance(comment, dict):
        return translated_field(comment, "message")
    return clean_text(comment)


def photo_details(images: list[dict[str, Any]] | None) -> tuple[int, int, list[str]]:
    if not images:
        return 0, 0, []
    spotlight = sum(1 for image in images if image.get("isSpotlight"))
    captions: list[str] = []
    for image in images:
        caption = translated_field(image, "caption")
        if caption:
            captions.append(caption)
    return len(images), spotlight, captions


def attachment_names(attachments: list[dict[str, Any]] | None) -> list[str]:
    if not attachments:
        return []
    return [clean_text(item.get("filename")) for item in attachments if item.get("filename")]


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    safe_headers = [h.replace("|", "/") for h in headers]
    lines = [
        "| " + " | ".join(safe_headers) + " |",
        "| " + " | ".join("---" for _ in safe_headers) + " |",
    ]
    for row in rows:
        row_cells = list(row)
        padded = row_cells + [""] * (len(headers) - len(row_cells))
        safe_row = [cell.replace("|", "/").replace("\n", " ") for cell in padded[: len(headers)]]
        lines.append("| " + " | ".join(safe_row) + " |")
    return "\n".join(lines)


def table_from_element(element: dict[str, Any]) -> str:
    value = element.get("value")
    if not isinstance(value, dict):
        return ""
    header_cols = value.get("header", {}).get("columns", [])
    headers = [translated_name(col) or clean_text(col.get("name")) for col in header_cols]
    rows: list[list[str]] = []
    for row in value.get("rows", []):
        cols = row.get("columns", [])
        rows.append([clean_text(col.get("value")) for col in cols])
    return render_markdown_table(headers, rows)


def values_to_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(v) for v in value if clean_text(v)]
    if isinstance(value, dict):
        # Hallmark YES_NO / PASS_FAIL often store {"value": true/false, ...}
        if "value" in value and not isinstance(value.get("value"), (dict, list)):
            inner = value.get("value")
            if isinstance(inner, bool):
                return ["Yes" if inner else "No"]
            text = clean_text(inner)
            return [text] if text else []
        return []
    if isinstance(value, bool):
        return ["Yes" if value else "No"]
    return [clean_text(value)] if clean_text(value) else []


def walk_checklist_elements(
    elements: list[dict[str, Any]],
    *,
    section: str,
    path_parts: list[str] | None = None,
) -> list[CheckItem]:
    path_parts = path_parts or []
    items: list[CheckItem] = []

    for element in elements:
        element_type = element.get("type")
        name = translated_name(element) or element_type or "Item"
        current_path = path_parts + ([name] if name else [])

        if element_type == "DIV":
            div_section = name if name not in ("", "Category name") else section
            nested = element.get("elements") or []
            items.extend(
                walk_checklist_elements(
                    nested,
                    section=div_section or section,
                    path_parts=current_path,
                )
            )
            continue

        instruction = translated_field(element, "instruction")
        expected_result = translated_field(element, "expectedResult")

        if element_type == "TABLE":
            photos, spotlight, photo_captions = photo_details(element.get("images"))
            items.append(
                CheckItem(
                    path=" > ".join(current_path),
                    name=name,
                    result=clean_text(element.get("result")) or "TABLE",
                    values=[],
                    comment=comment_message(element.get("comment")),
                    photos=photos,
                    spotlight=spotlight,
                    photo_captions=photo_captions,
                    attachments=attachment_names(element.get("attachments")),
                    table_md=table_from_element(element),
                    instruction=instruction,
                    expected_result=expected_result,
                    not_applicable=bool(element.get("notApplicable")),
                    section=section,
                )
            )
            continue

        # YES_NO / PASS_FAIL are Hallmark's dominant leaf types (not just MULTIPLE_CHOICE).
        if element_type in {
            "MULTIPLE_CHOICE",
            "TEXT",
            "NUMBER",
            "BOOLEAN",
            "DATE",
            "YES_NO",
            "PASS_FAIL",
        }:
            photos, spotlight, photo_captions = photo_details(element.get("images"))
            items.append(
                CheckItem(
                    path=" > ".join(current_path),
                    name=name,
                    result=clean_text(element.get("result")) or "NO_RESULT",
                    values=values_to_strings(element.get("value")),
                    comment=comment_message(element.get("comment")),
                    photos=photos,
                    spotlight=spotlight,
                    photo_captions=photo_captions,
                    attachments=attachment_names(element.get("attachments")),
                    instruction=instruction,
                    expected_result=expected_result,
                    not_applicable=bool(element.get("notApplicable")),
                    section=section,
                )
            )

    return items


def collect_defects(defects_checklist: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for category in defects_checklist.get("categories", []):
        category_name = translated_name(category) or clean_text(category.get("name"))
        for defect in category.get("defects", []):
            instances = defect.get("defectsFound") or []
            if not instances:
                continue
            total_qty = sum(float(inst.get("quantity") or 0) for inst in instances)
            comments = [
                comment_message(inst.get("comment"))
                for inst in instances
                if comment_message(inst.get("comment"))
            ]
            # Instance images only — template defect.images are gallery placeholders
            # and inflate photo_count (often ~60) when merged.
            defect_images: list[Any] = []
            for inst in instances:
                defect_images.extend(inst.get("images") or [])
            photo_count, _, photo_captions = photo_details(defect_images)
            found.append(
                {
                    "category": category_name,
                    "name": translated_name(defect) or clean_text(defect.get("name")),
                    "classification": clean_text(defect.get("classification")),
                    "quantity": total_qty,
                    "comments": comments,
                    "photos": photo_count,
                    "photo_count": photo_count,
                    "photo_captions": photo_captions,
                }
            )
    return found


def extract_custom_fields(report: dict[str, Any]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for entry in report.get("customFieldsWithValues", []):
        label = clean_text((entry.get("customField") or {}).get("label"))
        if not label or label.lower().replace(" ", "") in SKIP_CUSTOM_FIELD_LABELS:
            continue
        value_obj = entry.get("customFieldValue") or {}
        value = value_obj.get("value")
        if isinstance(value, bool):
            rendered = "Yes" if value else "No"
        else:
            rendered = clean_text(value)
        if rendered:
            fields[label] = rendered
    return fields


def extract_onsite_quantities(report: dict[str, Any]) -> dict[tuple[Any, Any], dict[str, Any]]:
    """Actual on-site produced/packed counts, keyed by (productId, purchaseOrderProductId).

    These are the quantities the inspector actually counted (e.g. produced/packed 519)
    and are what the report cover shows. They must NOT be confused with
    ``products[].producedQuantity`` / ``packedQuantity``, which are the EXPECTED targets
    from the PO plan (100% produced / 80% packed acceptance threshold).
    """
    result = report.get("result") or {}
    out: dict[tuple[Any, Any], dict[str, Any]] = {}
    for step in result.get("steps", []):
        for action in step.get("actions", []):
            for qty in action.get("productQuantities") or []:
                out[(qty.get("productId"), qty.get("purchaseOrderProductId"))] = {
                    "produced": qty.get("produced"),
                    "packed": qty.get("packed"),
                }
    return out


def extract_products(report: dict[str, Any]) -> list[dict[str, str]]:
    onsite = extract_onsite_quantities(report)
    products = []
    for item in report.get("products", []):
        product = item.get("product") or {}
        po = item.get("purchaseOrder") or {}
        spec = product.get("specification") or {}

        # Match the on-site counts to this product; fall back to productId only.
        key = (product.get("id"), item.get("purchaseOrderProductId"))
        actual = onsite.get(key)
        if actual is None:
            actual = next(
                (v for (pid, _), v in onsite.items() if pid == product.get("id")),
                {},
            )

        # Two independent sources, no silent fallback: actual = what the inspector
        # counted on-site; expected = the PO plan targets. If on-site is absent we
        # leave actual empty (the invariant suite flags it) rather than quietly
        # substituting the expected value and pretending we measured it.
        actual_produced = actual.get("produced")
        actual_packed = actual.get("packed")

        products.append(
            {
                "name": clean_text(product.get("description") or product.get("identifierValue")),
                "sku": clean_text(spec.get("SKU")),
                "po": clean_text(po.get("reference")),
                "unit": clean_text(item.get("unit")),
                "ordered": str(item.get("productQuantity", "")),
                "produced_actual": str(actual_produced if actual_produced is not None else ""),
                "packed_actual": str(actual_packed if actual_packed is not None else ""),
                "produced_expected": str(item.get("producedQuantity", "")),
                "packed_expected": str(item.get("packedQuantity", "")),
                "shipment_date": clean_text(item.get("shipmentDate")),
            }
        )
    return products


def extract_supplementary_sections(result: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    instructions: list[dict[str, str]] = []
    inspection_details: list[dict[str, str]] = []
    findings_reviews: list[dict[str, str]] = []

    for step in result.get("steps", []):
        step_name = clean_text(step.get("name"))
        for action in step.get("actions", []):
            action_type = action.get("type")
            action_id = clean_text(action.get("id"))
            result_value = clean_text(action.get("result"))
            comment = comment_message(action.get("comment"))

            if action_type == "INSTRUCTIONS":
                text = translated_field(action, "instructions")
                if text:
                    instructions.append(
                        {
                            "step": step_name,
                            "action_id": action_id,
                            "result": result_value,
                            "text": text,
                        }
                    )
                continue

            if action_type == "INSPECTION_DETAILS":
                if comment or result_value not in {"", "NOT_APPLICABLE"}:
                    inspection_details.append(
                        {
                            "step": step_name,
                            "action_id": action_id,
                            "result": result_value,
                            "comment": comment,
                        }
                    )
                continue

            if action_type == "FINDINGS_SUMMARY_REVIEW":
                review = action.get("findingsSummaryReview") or {}
                confirmed = review.get("confirmed")
                if (
                    comment
                    or confirmed is not None
                    or action.get("isInspectionMarkedAsPending") is not None
                    or action.get("isWorkmanshipMarkedAsNA") is not None
                ):
                    findings_reviews.append(
                        {
                            "step": step_name,
                            "action_id": action_id,
                            "result": result_value,
                            "comment": comment,
                            "confirmed": "Yes" if confirmed else "No" if confirmed is not None else "",
                            "confirmation_time": clean_text(review.get("confirmationTime")),
                            "inspection_marked_pending": "Yes"
                            if action.get("isInspectionMarkedAsPending")
                            else "No",
                            "workmanship_marked_na": "Yes"
                            if action.get("isWorkmanshipMarkedAsNA")
                            else "No",
                        }
                    )

    return {
        "instructions": instructions,
        "inspection_details": inspection_details,
        "findings_reviews": findings_reviews,
    }


def extract_checklists(result: dict[str, Any]) -> list[dict[str, Any]]:
    checklists: list[dict[str, Any]] = []
    for step in result.get("steps", []):
        step_name = clean_text(step.get("name"))
        for action in step.get("actions", []):
            action_type = action.get("type")
            if action_type in SKIP_ACTION_TYPES:
                continue

            entry: dict[str, Any] = {
                "step": step_name,
                "action_type": action_type,
                "action_id": clean_text(action.get("id")),
                "result": clean_text(action.get("result")),
                "comment": comment_message(action.get("comment")),
            }

            if action_type == "TESTS_CHECKLIST":
                checklist = action.get("testsChecklist") or {}
                checklist_name = translated_name(checklist) or clean_text(checklist.get("name"))
                entry["name"] = checklist_name
                entry["items"] = walk_checklist_elements(
                    (checklist.get("content") or {}).get("elements", []),
                    section=checklist_name,
                )
                checklists.append(entry)

            elif action_type == "DEFECTS_CHECKLIST":
                checklist = action.get("defectsChecklist") or {}
                entry["name"] = translated_name(checklist) or clean_text(checklist.get("name"))
                entry["defects"] = collect_defects(checklist)
                checklists.append(entry)

            elif action_type == "STARTING_PICTURES":
                photos, _, photo_captions = photo_details(action.get("pictures"))
                entry["name"] = "Starting pictures"
                entry["photos"] = photos
                entry["photo_captions"] = photo_captions
                checklists.append(entry)

            elif action_type == "REFERENCE_SAMPLE":
                sample = action.get("referenceSample") or {}
                entry["name"] = "Reference sample (GSS)"
                entry["details"] = {
                    "mode": clean_text(sample.get("fetchingMode")),
                    "carrier": clean_text(sample.get("carrierName")),
                    "completed": "Yes" if sample.get("isCompleted") else "No",
                }
                checklists.append(entry)

            elif action_type == "INSPECTION_PREPARATION":
                quantities = []
                for qty in action.get("productQuantities", []):
                    quantities.append(
                        f"produced={qty.get('produced', '')}, packed={qty.get('packed', '')}"
                    )
                entry["name"] = "Inspection preparation"
                entry["details"] = {
                    "method": clean_text(action.get("calculationMethod")),
                    "quantities": "; ".join(quantities),
                }
                checklists.append(entry)

            elif action_type == "PRODUCT_PICTURE":
                entry["name"] = "Product cover photo"
                entry["details"] = {"document_id": clean_text(action.get("documentId"))}
                checklists.append(entry)

    return checklists


def summarize_workmanship(result: dict[str, Any]) -> dict[str, Any]:
    workmanship = (result.get("workmanship") or [{}])[0] if result.get("workmanship") else {}
    # Two DIFFERENT things the QIMAone payload keeps separate — do not conflate:
    #  - aqlDefects: the AQL *levels* / quality standard (e.g. Major 2.5, Minor 4.0).
    #    This is what GIs like Ribkoff 7_1_1 verify.
    #  - acceptableQualityLevel: the *acceptance points* (max defects allowed for the
    #    chosen sample size, e.g. Major 5). These are derived from the AQL + sample size,
    #    NOT the AQL itself, so labelling them "AQL" makes the model false-flag.
    aql_levels = result.get("aqlDefects") or workmanship.get("aqlDefects") or {}
    accept = workmanship.get("acceptableQualityLevel") or {}
    totals = workmanship.get("totalDefectsFound") or {}
    return {
        "result": clean_text(workmanship.get("result")),
        "aql_level_critical": clean_text(aql_levels.get("critical")),
        "aql_level_major": clean_text(aql_levels.get("major")),
        "aql_level_minor": clean_text(aql_levels.get("minor")),
        "acceptance_critical": accept.get("critical"),
        "acceptance_major": accept.get("major"),
        "acceptance_minor": accept.get("minor"),
        "found_critical": totals.get("CRITICAL", 0),
        "found_major": totals.get("MAJOR", 0),
        "found_minor": totals.get("MINOR", 0),
        "defects": workmanship.get("defectsFound") or [],
    }
