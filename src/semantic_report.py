"""Semantic report: QIMAone JSON → PDF-aligned facts (single source of truth).

Field names match what inspectors see on the PDF cover and checklist pages.
Each field documents its JSON source so mis-labeling (e.g. PO target vs on-site
count) cannot recur silently.

    JSON path                              PDF label                    Field name
    -------------------------------------  ---------------------------  -------------------------
    products[].productQuantity             Ordered quantity             ordered_quantity
    productQuantities[].produced           Produced quantity (on-site)  real_produced_quantity
    products[].producedQuantity            Expected under Produced      expected_produced_quantity
    productQuantities[].packed             Packed quantity (on-site)    real_packed_quantity
    products[].packedQuantity              Expected under Packed        expected_packed_quantity
    aqlDefects.major                       AQL level (standard)         aql_level_major
    acceptableQualityLevel.major           Max allowed defects          max_defects_major
    totalDefectsFound.MAJOR                Found (CRI/MAJ/MIN column)   found_major
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from report_extract import (
    clean_text,
    comment_message,
    extract_checklists,
    extract_custom_fields,
    extract_onsite_quantities,
    extract_products,
    extract_supplementary_sections,
    format_address,
    photo_details,
    summarize_workmanship,
    translated_field,
    translated_name,
    walk_checklist_elements,
)

_NAME_KEY_RE = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    return _NAME_KEY_RE.sub("_", name.strip().lower()).strip("_")


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _requires_photo(element: dict[str, Any]) -> bool:
    return any(req.get("type") == "PICTURE" for req in element.get("requirements") or [])


# --- PDF-aligned dataclasses -------------------------------------------------


@dataclass
class ProductQuantity:
    """One product row from the PDF cover 'PO & Product details' table."""

    product_name: str
    sku: str
    po_reference: str
    unit: str
    shipment_date: str
    ordered_quantity: int | None
    real_produced_quantity: int | None
    expected_produced_quantity: int | None
    real_packed_quantity: int | None
    expected_packed_quantity: int | None

    # JSON sources (audit trail)
    source_ordered: str = "products[].productQuantity"
    source_real_produced: str = "result.steps[].actions[].productQuantities[].produced"
    source_expected_produced: str = "products[].producedQuantity"
    source_real_packed: str = "result.steps[].actions[].productQuantities[].packed"
    source_expected_packed: str = "products[].packedQuantity"

    def to_legacy_dict(self) -> dict[str, str]:
        """Keys used by IR / operators before semantic rename."""
        return {
            "name": self.product_name,
            "sku": self.sku,
            "po": self.po_reference,
            "unit": self.unit,
            "shipment_date": self.shipment_date,
            "ordered": "" if self.ordered_quantity is None else str(self.ordered_quantity),
            "produced_actual": "" if self.real_produced_quantity is None else str(self.real_produced_quantity),
            "packed_actual": "" if self.real_packed_quantity is None else str(self.real_packed_quantity),
            "produced_expected": "" if self.expected_produced_quantity is None else str(self.expected_produced_quantity),
            "packed_expected": "" if self.expected_packed_quantity is None else str(self.expected_packed_quantity),
        }


@dataclass
class WorkmanshipFacts:
    """Workmanship block on PDF cover: result, AQL levels, defects found vs max allowed."""

    result: str
    inspection_level: str
    aql_level_critical: str
    aql_level_major: str
    aql_level_minor: str
    max_defects_critical: int | None
    max_defects_major: int | None
    max_defects_minor: int | None
    sample_size_critical: int | None
    sample_size_major: int | None
    sample_size_minor: int | None
    found_critical: float
    found_major: float
    found_minor: float
    measurement_level: str = ""
    measurement_aql: str = ""

    source_aql_levels: str = "aqlDefects / workmanship.aqlDefects"
    source_max_defects: str = "workmanship.acceptableQualityLevel"
    source_found: str = "workmanship.totalDefectsFound"


@dataclass
class ChecklistItem:
    """One answerable checklist row (PDF checklist section)."""

    checklist_name: str
    section: str
    path: str
    item_name: str
    element_type: str
    result: str
    applicable: bool
    not_applicable: bool
    requires_photo: bool
    values: list[str]
    comment: str
    photo_count: int
    photo_captions: list[str]
    attachment_filenames: list[str]
    spotlight_count: int = 0
    instruction: str = ""
    expected_result: str = ""

    @property
    def lookup_key(self) -> str:
        return normalize_name(self.item_name)


@dataclass
class SemanticReport:
    """Full semantic view of one inspection report."""

    report_id: str
    inspection_id: str
    inspection_reference: str
    overall_result: str
    inspection_type: str
    inspection_date: str
    planned_date: str
    days_postponed: int | None
    product_label: str
    sku: str
    po_reference: str
    supplier_name: str
    factory_name: str
    factory_address: str
    production_site: str
    global_remark: str
    tests_result: str
    products: list[ProductQuantity] = field(default_factory=list)
    workmanship: WorkmanshipFacts | None = None
    checklist_items: list[ChecklistItem] = field(default_factory=list)
    checklist_by_name: dict[str, ChecklistItem] = field(default_factory=dict)
    defects: list[dict[str, Any]] = field(default_factory=list)
    custom_fields: dict[str, str] = field(default_factory=dict)
    destinations: list[str] = field(default_factory=list)
    inspector_instructions: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)

    def get_checklist_item(self, name: str) -> ChecklistItem | None:
        return self.checklist_by_name.get(normalize_name(name))

    @property
    def defect_count(self) -> int:
        return len(self.defects)

    @property
    def defects_without_photo(self) -> int:
        return sum(1 for d in self.defects if int(d.get("photo_count") or 0) <= 0)

    @property
    def all_text(self) -> str:
        """Concatenated report text for FULL_REPORT scan ops."""
        parts: list[str] = [
            self.global_remark,
            self.product_label,
            self.supplier_name,
            self.factory_name,
            self.factory_address,
            self.production_site,
            self.po_reference,
            self.sku,
        ]
        for product in self.products:
            parts.extend(
                [
                    product.product_name,
                    product.sku,
                    product.po_reference,
                    product.unit,
                ]
            )
        for item in self.checklist_items:
            # Omit item_name: platform checklist titles often contain words like
            # "Sample" that are not inspector-authored content (scan FPs).
            parts.extend(
                [
                    item.result,
                    item.comment,
                    item.instruction,
                    " ".join(item.values or []),
                    " ".join(item.attachment_filenames or []),
                    " ".join(c for c in (item.photo_captions or []) if str(c).strip()),
                ]
            )
        for defect in self.defects:
            parts.append(str(defect.get("name") or ""))
            parts.append(str(defect.get("classification") or ""))
        for key, value in self.custom_fields.items():
            parts.append(f"{key} {value}")
        parts.extend(self.inspector_instructions)
        parts.extend(self.destinations)
        return "\n".join(p for p in parts if str(p).strip())

    @property
    def all_captions(self) -> str:
        """Concatenated photo captions for FULL_REPORT scan ops."""
        captions: list[str] = []
        for item in self.checklist_items:
            captions.extend(c for c in (item.photo_captions or []) if str(c).strip())
        for defect in self.defects:
            captions.extend(
                c for c in (defect.get("photo_captions") or []) if str(c).strip()
            )
        return "\n".join(captions)

    @property
    def inspector_text(self) -> str:
        """Inspector-authored text only (remarks, comments, captions).

        Excludes checklist item titles and QIMA instruction templates, which
        often contain words like "Sample" and would false-positive scan ops.
        """
        parts: list[str] = [
            self.global_remark,
            self.product_label,
        ]
        for item in self.checklist_items:
            parts.append(item.comment)
            parts.extend(c for c in (item.photo_captions or []) if str(c).strip())
        for defect in self.defects:
            parts.append(str(defect.get("name") or ""))
            parts.append(str(defect.get("classification") or ""))
            parts.extend(
                c for c in (defect.get("photo_captions") or []) if str(c).strip()
            )
        return "\n".join(p for p in parts if str(p).strip())

    @property
    def attachment_filenames(self) -> list[str]:
        names: list[str] = []
        for item in self.checklist_items:
            names.extend(item.attachment_filenames or [])
        return names

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _product_quantities_from_extract(report: dict[str, Any]) -> list[ProductQuantity]:
    rows: list[ProductQuantity] = []
    for raw in extract_products(report):
        rows.append(
            ProductQuantity(
                product_name=raw["name"],
                sku=raw["sku"],
                po_reference=raw["po"],
                unit=raw["unit"],
                shipment_date=raw["shipment_date"],
                ordered_quantity=_to_int(raw.get("ordered")),
                real_produced_quantity=_to_int(raw.get("produced_actual")),
                expected_produced_quantity=_to_int(raw.get("produced_expected")),
                real_packed_quantity=_to_int(raw.get("packed_actual")),
                expected_packed_quantity=_to_int(raw.get("packed_expected")),
            )
        )
    return rows


def _workmanship_from_report(report: dict[str, Any]) -> WorkmanshipFacts:
    result_obj = report.get("result") or {}
    w = summarize_workmanship(result_obj)
    sampling = result_obj.get("samplingSize") or report.get("inspectionSamplingSize") or {}
    measurements = report.get("aqlMeasurements") or {}
    return WorkmanshipFacts(
        result=clean_text(w.get("result")),
        inspection_level=clean_text(sampling.get("inspectionLevel")),
        aql_level_critical=clean_text(w.get("aql_level_critical")),
        aql_level_major=clean_text(w.get("aql_level_major")),
        aql_level_minor=clean_text(w.get("aql_level_minor")),
        max_defects_critical=_to_int(w.get("acceptance_critical")),
        max_defects_major=_to_int(w.get("acceptance_major")),
        max_defects_minor=_to_int(w.get("acceptance_minor")),
        sample_size_critical=_to_int(sampling.get("criticalSampleSize")),
        sample_size_major=_to_int(sampling.get("majorSampleSize")),
        sample_size_minor=_to_int(sampling.get("minorSampleSize")),
        found_critical=float(w.get("found_critical") or 0),
        found_major=float(w.get("found_major") or 0),
        found_minor=float(w.get("found_minor") or 0),
        measurement_level=clean_text(measurements.get("level")),
        measurement_aql=clean_text(measurements.get("aql")),
    )


def _checklist_items_from_report(report: dict[str, Any]) -> list[ChecklistItem]:
    result_obj = report.get("result") or {}
    items: list[ChecklistItem] = []
    for step in result_obj.get("steps", []):
        for action in step.get("actions", []):
            if action.get("type") != "TESTS_CHECKLIST":
                continue
            checklist = action.get("testsChecklist") or {}
            checklist_name = translated_name(checklist) or clean_text(checklist.get("name"))
            elements = (checklist.get("content") or {}).get("elements", [])
            for raw in walk_checklist_elements(elements, section=checklist_name):
                items.append(
                    ChecklistItem(
                        checklist_name=checklist_name,
                        section=raw.section or checklist_name,
                        path=raw.path,
                        item_name=raw.name,
                        element_type="TABLE" if raw.table_md else "CHECKLIST_ITEM",
                        result=raw.result,
                        applicable=not raw.not_applicable,
                        not_applicable=raw.not_applicable,
                        requires_photo=raw.photos > 0 or bool(raw.instruction),
                        values=list(raw.values),
                        comment=raw.comment,
                        photo_count=raw.photos,
                        photo_captions=list(raw.photo_captions),
                        spotlight_count=int(raw.spotlight or 0),
                        attachment_filenames=list(raw.attachments),
                        instruction=raw.instruction,
                        expected_result=raw.expected_result,
                    )
                )
    return items


def _defects_from_checklists(report: dict[str, Any]) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    for checklist in extract_checklists(report.get("result") or {}):
        for defect in checklist.get("defects") or []:
            photos = defect.get("photos")
            if defect.get("photo_count") is not None:
                photo_count = int(defect.get("photo_count") or 0)
            elif isinstance(photos, list):
                photo_count = len(photos)
            else:
                photo_count = int(photos or 0)
            defects.append(
                {
                    "name": defect.get("name", ""),
                    "classification": defect.get("classification", ""),
                    "quantity": defect.get("quantity", 0),
                    "photo_count": photo_count,
                    "photo_captions": defect.get("photo_captions", []),
                }
            )
    return defects


def _entity_name(entity: Any) -> str:
    if not isinstance(entity, dict):
        return ""
    return clean_text(entity.get("name"))


def _days_between(planned: str, inspected: str) -> int | None:
    """Days inspection was postponed (positive) or advanced (negative) vs planned."""
    if not planned or not inspected:
        return None
    try:
        from datetime import date

        p = date.fromisoformat(planned[:10])
        i = date.fromisoformat(inspected[:10])
        return (i - p).days
    except ValueError:
        return None


def parse_semantic_report(report: dict[str, Any]) -> SemanticReport:
    """Parse raw QIMAone JSON into PDF-aligned semantic facts."""
    result_obj = report.get("result") or {}
    products = _product_quantities_from_extract(report)
    primary = products[0] if products else None
    inspection_type = translated_field((report.get("inspectionType") or {}), "description") or clean_text(
        (report.get("inspectionType") or {}).get("description")
    )
    supplementary = extract_supplementary_sections(result_obj)

    checklist_items = _checklist_items_from_report(report)
    by_name: dict[str, ChecklistItem] = {}
    for item in checklist_items:
        key = item.lookup_key
        if key and key not in by_name:
            by_name[key] = item

    destinations = [
        clean_text((dest.get("entity") or {}).get("name") or dest.get("name"))
        for dest in report.get("destinations") or []
    ]
    destinations = [d for d in destinations if d]

    inspection_date = clean_text(report.get("inspectionDate"))
    planned_date = clean_text(report.get("plannedDate"))

    semantic = SemanticReport(
        report_id=str(report.get("reportId", "")),
        inspection_id=str(report.get("inspectionId", "")),
        inspection_reference=str(report.get("inspectionId", "")),
        overall_result=clean_text(report.get("inspectionResult") or result_obj.get("result")),
        inspection_type=inspection_type,
        inspection_date=inspection_date,
        planned_date=planned_date,
        days_postponed=_days_between(planned_date, inspection_date),
        product_label=primary.product_name if primary else "",
        sku=primary.sku if primary else "",
        po_reference=primary.po_reference if primary else "",
        supplier_name=_entity_name(report.get("responsibleEntity")),
        factory_name=_entity_name(report.get("entity") or report.get("productionSiteEntity")),
        factory_address=format_address(report.get("entity")),
        production_site=format_address(report.get("productionSiteEntity")),
        global_remark=comment_message(result_obj.get("globalRemark")),
        tests_result=clean_text(result_obj.get("testsResult")),
        products=products,
        workmanship=_workmanship_from_report(report),
        checklist_items=checklist_items,
        checklist_by_name=by_name,
        defects=_defects_from_checklists(report),
        custom_fields=extract_custom_fields(report),
        destinations=destinations,
        inspector_instructions=[b["text"] for b in supplementary.get("instructions", [])],
    )
    semantic.parse_warnings = semantic_invariants(semantic)
    return semantic


def semantic_invariants(semantic: SemanticReport) -> list[str]:
    """Sanity checks: if these fire, quantity/AQL facts must not drive rules."""
    warnings: list[str] = []

    for product in semantic.products:
        label = product.product_name or "product"
        if (
            product.expected_packed_quantity is not None
            and product.expected_produced_quantity is not None
            and product.expected_packed_quantity > product.expected_produced_quantity
        ):
            warnings.append(
                f"quantity[{label}]: expected_packed_quantity {product.expected_packed_quantity} "
                f"> expected_produced_quantity {product.expected_produced_quantity} (labels likely swapped)"
            )
        if product.ordered_quantity and product.real_packed_quantity is None and product.real_produced_quantity is None:
            warnings.append(f"quantity[{label}]: no on-site counts (real_produced/real_packed missing)")

    w = semantic.workmanship
    if w and (w.result or "").upper() == "PASS":
        for sev in ("critical", "major", "minor"):
            found = getattr(w, f"found_{sev}")
            accept = getattr(w, f"max_defects_{sev}")
            if accept is not None and found > accept:
                warnings.append(
                    f"workmanship: PASS but found_{sev} {found:g} > max_defects_{sev} {accept:g}"
                )
        try:
            lvl_major = float(w.aql_level_major)
            acc_major = float(w.max_defects_major) if w.max_defects_major is not None else None
            if acc_major is not None and lvl_major == acc_major:
                warnings.append("workmanship: aql_level_major == max_defects_major (level/acceptance conflated)")
        except (TypeError, ValueError):
            pass

    return warnings


def semantic_to_ir_summary(semantic: SemanticReport) -> dict[str, Any]:
    """Bridge semantic report → IR summary block (legacy shape + semantic fields)."""
    w = semantic.workmanship
    aql: dict[str, Any] = {}
    if w:
        aql = {
            "inspection_level": w.inspection_level,
            "aql_level_critical": w.aql_level_critical,
            "aql_level_major": w.aql_level_major,
            "aql_level_minor": w.aql_level_minor,
            "acceptance_critical": w.max_defects_critical,
            "acceptance_major": w.max_defects_major,
            "acceptance_minor": w.max_defects_minor,
            "sample_size_critical": w.sample_size_critical,
            "sample_size_major": w.sample_size_major,
            "sample_size_minor": w.sample_size_minor,
            "found_critical": w.found_critical,
            "found_major": w.found_major,
            "found_minor": w.found_minor,
            "measurement_level": w.measurement_level,
            "measurement_aql": w.measurement_aql,
        }

    quantities: list[dict[str, Any]] = []
    for p in semantic.products:
        leg = p.to_legacy_dict()
        leg.update(
            {
                "ordered_quantity": p.ordered_quantity,
                "real_produced_quantity": p.real_produced_quantity,
                "expected_produced_quantity": p.expected_produced_quantity,
                "real_packed_quantity": p.real_packed_quantity,
                "expected_packed_quantity": p.expected_packed_quantity,
            }
        )
        quantities.append(leg)

    return {
        "tests_result": semantic.tests_result,
        "workmanship_result": w.result if w else "",
        "aql": aql,
        "quantities": quantities,
        "inspector_instructions": semantic.inspector_instructions,
        "custom_fields": semantic.custom_fields,
        "defects": semantic.defects,
        "global_remark": semantic.global_remark,
        "parse_warnings": semantic.parse_warnings,
    }


def semantic_to_ir_nodes(semantic: SemanticReport) -> list[dict[str, Any]]:
    """Bridge checklist items → IR nodes (legacy shape)."""
    nodes: list[dict[str, Any]] = []
    for item in semantic.checklist_items:
        nodes.append(
            {
                "path": item.path,
                "section": item.section,
                "name": item.item_name,
                "type": item.element_type,
                "result": item.result,
                "applicable": item.applicable,
                "requires_photo": item.requires_photo,
                "photos": {"count": item.photo_count, "captions": item.photo_captions},
                "values": item.values,
                "comment": item.comment,
                "attachments": item.attachment_filenames,
            }
        )
    return nodes


def build_semantic_ir(report: dict[str, Any]) -> dict[str, Any]:
    """IR built from semantic report (canonical path)."""
    semantic = parse_semantic_report(report)
    return {
        "meta": {
            "report_id": semantic.report_id,
            "inspection_id": semantic.inspection_id,
            "inspection_result": semantic.overall_result,
            "inspection_type": semantic.inspection_type,
            "inspection_date": semantic.inspection_date,
            "product": semantic.product_label,
            "sku": semantic.sku,
            "po": semantic.po_reference,
            "factory_address": semantic.factory_address,
            "production_site": semantic.production_site,
            "destinations": [],
        },
        "summary": semantic_to_ir_summary(semantic),
        "nodes": semantic_to_ir_nodes(semantic),
        "semantic": semantic.to_dict(),
    }


def dumps_semantic(report: dict[str, Any], *, pretty: bool = True) -> str:
    semantic = parse_semantic_report(report)
    if pretty:
        return json.dumps(semantic.to_dict(), ensure_ascii=False, indent=2)
    return json.dumps(semantic.to_dict(), ensure_ascii=False, separators=(",", ":"))


def load_report_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
