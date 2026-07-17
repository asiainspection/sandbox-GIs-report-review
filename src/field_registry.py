"""Typed field registry — single source of truth for evidence modality.

The authored check block is three keys only: where / when / check.
Everything else (data_source, modality, processor, feasibility) is DERIVED
from this registry by looking at the field being pointed at.

Stability contract (schema_version 1):
  - Block schema never gains keys.
  - Growth = appending rows here (or new operators). Additive only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = 1

# Derived data_source buckets (matches user design).
DATA_SOURCES = frozenset(
    {
        "report_content",  # text, enums, counts, structured scalars
        "report_images",  # photo content (vision) or captions routed as text
        "report_attachments",  # filenames now; content later
        "out_of_report",  # booking / spec / email / sop / ip
    }
)

# Feasibility: can the engine check this field today?
FEASIBLE_NOW = "now"
FEASIBLE_PENDING = "pending"
FEASIBLE_NEVER = "never"

# status_class on compiled specs
STATUS_CHECKABLE = "checkable"
STATUS_PENDING = "pending"
STATUS_UNAUTHORED = "unauthored"
STATUS_UNMAPPED = "unmapped"  # in-report likely, but where not grounded yet
STATUS_ADVISORY = "advisory"

# Legacy authored data_source values mapped to derived buckets.
LEGACY_TO_DERIVED: dict[str, str] = {
    "in_report": "report_content",
    "IP": "out_of_report",
    "PO_booking": "out_of_report",
    "spec_sheet": "out_of_report",
    "email": "out_of_report",
    "external": "out_of_report",
    "other": "out_of_report",
    "report_content": "report_content",
    "report_images": "report_images",
    "report_attachments": "report_attachments",
    "out_of_report": "out_of_report",
}

OUT_OF_REPORT_KINDS = frozenset({"booking", "po_booking", "spec_sheet", "email", "sop", "ip", "other"})


@dataclass(frozen=True)
class FieldClass:
    """Classification of one evidence field."""

    modality: str  # enum | text | number | filename | file_content | image | none
    processor: str  # structured | text | file | vision | none
    feasible: str  # now | pending | never
    data_source: str  # report_content | report_images | report_attachments | out_of_report
    pending_processor: str | None = None  # e.g. "xlsx" | "vision"


# ---------------------------------------------------------------------------
# Checklist suffixes
# ---------------------------------------------------------------------------
SUFFIX_REGISTRY: dict[str, FieldClass] = {
    "result": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "values": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "applicable": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "comment": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "photo_captions": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "caption_count": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "photo_count": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "spotlight_count": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "attachment_filenames": FieldClass("filename", "file", FEASIBLE_NOW, "report_attachments"),
    # Hooks — not built yet; rules pointing here become status_class=pending.
    "attachment_content": FieldClass(
        "file_content", "file", FEASIBLE_PENDING, "report_attachments", pending_processor="xlsx"
    ),
    "photo_content": FieldClass(
        "image", "vision", FEASIBLE_PENDING, "report_images", pending_processor="vision"
    ),
}

# ---------------------------------------------------------------------------
# Report / workmanship / product selectors
# ---------------------------------------------------------------------------
REPORT_FIELD_REGISTRY: dict[str, FieldClass] = {
    "report.overall_result": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "report.inspection_type": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.inspection_date": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.planned_date": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.days_postponed": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "report.global_remark": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.supplier_name": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.factory_name": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.factory_address": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.production_site": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.po_reference": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.product_label": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.sku": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.tests_result": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "report.destinations": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "report.all_text": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.inspector_text": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.all_captions": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "report.attachment_filenames": FieldClass("filename", "file", FEASIBLE_NOW, "report_attachments"),
    "report.defect_count": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "report.defects_without_photo": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "report.defects": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.result": FieldClass("enum", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.aql_level_major": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.aql_level_minor": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.aql_level_critical": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.found_major": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.found_minor": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.found_critical": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.max_defects_major": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.max_defects_minor": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.max_defects_critical": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.inspection_level": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.sample_size_critical": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.sample_size_major": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.sample_size_minor": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.measurement_level": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "workmanship.measurement_aql": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.ordered_quantity": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.real_packed_quantity": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.real_produced_quantity": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.expected_packed_quantity": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.expected_produced_quantity": FieldClass("number", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.unit": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.product_name": FieldClass("text", "text", FEASIBLE_NOW, "report_content"),
    "product._first.sku": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.po_reference": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
    "product._first.shipment_date": FieldClass("text", "structured", FEASIBLE_NOW, "report_content"),
}

OUT_OF_REPORT_CLASS = FieldClass("none", "none", FEASIBLE_NEVER, "out_of_report")

# Priority when combining multiple where fields into one data_source.
_DS_PRIORITY = ("out_of_report", "report_attachments", "report_images", "report_content")


def classify_selector(selector: str) -> FieldClass:
    """Classify a canonical selector string."""
    text = str(selector or "").strip()
    if not text:
        return OUT_OF_REPORT_CLASS

    if text == "unmapped":
        # Honest backlog: in-report assumed until grounded — not out_of_report.
        return FieldClass("none", "none", FEASIBLE_NOW, "report_content")

    if text.startswith("out_of_report"):
        return OUT_OF_REPORT_CLASS

    if text in REPORT_FIELD_REGISTRY:
        return REPORT_FIELD_REGISTRY[text]

    if text.startswith("checklist."):
        parts = text.split(".", 2)
        if len(parts) == 3:
            suffix = parts[2]
            if suffix in SUFFIX_REGISTRY:
                return SUFFIX_REGISTRY[suffix]
        # Unknown checklist suffix → treat as in-report text (safe default).
        return FieldClass("text", "text", FEASIBLE_NOW, "report_content")

    if text.startswith("custom."):
        return FieldClass("text", "text", FEASIBLE_NOW, "report_content")

    if text.startswith("product._first.") or text.startswith("workmanship."):
        # Unknown but structured-looking → report_content now.
        return FieldClass("text", "structured", FEASIBLE_NOW, "report_content")

    if text.startswith("report."):
        return FieldClass("text", "text", FEASIBLE_NOW, "report_content")

    return FieldClass("text", "text", FEASIBLE_NOW, "report_content")


def classify_binding(binding: dict[str, Any]) -> FieldClass:
    """Classify a normalized where binding (selector | intent | out_of_report)."""
    btype = str(binding.get("type") or "").strip()
    if btype == "unmapped":
        return FieldClass("none", "none", FEASIBLE_NOW, "report_content")
    if btype == "out_of_report":
        return OUT_OF_REPORT_CLASS

    if btype == "intent":
        kind = str(binding.get("kind") or "").strip().lower()
        field = str(binding.get("field") or "comment").strip()
        if kind == "out_of_report":
            return OUT_OF_REPORT_CLASS
        if kind == "caption":
            # Captions are text (checkable now), not image content.
            return FieldClass("text", "text", FEASIBLE_NOW, "report_content")
        if field in SUFFIX_REGISTRY:
            return SUFFIX_REGISTRY[field]
        if field in ("remark", "global_remark"):
            return REPORT_FIELD_REGISTRY["report.global_remark"]
        if field.startswith("report."):
            return classify_selector(field)
        # Intent field name like photo_count / comment / attachment_filenames
        return SUFFIX_REGISTRY.get(
            field, FieldClass("text", "text", FEASIBLE_NOW, "report_content")
        )

    selector = str(binding.get("selector") or "")
    return classify_selector(selector)


def _merge_classes(classes: list[FieldClass]) -> FieldClass:
    if not classes:
        return OUT_OF_REPORT_CLASS
    # Worst feasibility wins (never > pending > now).
    feas_rank = {FEASIBLE_NEVER: 2, FEASIBLE_PENDING: 1, FEASIBLE_NOW: 0}
    worst = max(classes, key=lambda c: feas_rank.get(c.feasible, 0))
    # Highest-priority data_source among the set.
    ds_set = {c.data_source for c in classes}
    data_source = next((d for d in _DS_PRIORITY if d in ds_set), classes[0].data_source)
    pending = worst.pending_processor
    if worst.feasible == FEASIBLE_PENDING and not pending:
        for c in classes:
            if c.pending_processor:
                pending = c.pending_processor
                break
    return FieldClass(
        modality=worst.modality,
        processor=worst.processor,
        feasible=worst.feasible,
        data_source=data_source,
        pending_processor=pending,
    )


def _is_unmapped_binding(binding: dict[str, Any]) -> bool:
    if str(binding.get("type") or "") == "unmapped":
        return True
    return str(binding.get("selector") or "").strip() == "unmapped"


def derive_data_source(
    where_bindings: list[dict[str, Any]] | None,
    *,
    legacy_data_source: str | None = None,
) -> str:
    """Derive data_source from where bindings.

    Empty where + legacy out-of-report hint → out_of_report.
    Empty where with no hint → report_content (unmapped backlog, not advisory).
    """
    bindings = list(where_bindings or [])
    if not bindings:
        if legacy_data_source:
            return LEGACY_TO_DERIVED.get(str(legacy_data_source).strip(), "out_of_report")
        return "report_content"
    if all(_is_unmapped_binding(b) for b in bindings):
        return "report_content"
    merged = _merge_classes([classify_binding(b) for b in bindings])
    return merged.data_source


def derive_feasibility(
    where_bindings: list[dict[str, Any]] | None,
    *,
    has_check: bool,
    legacy_data_source: str | None = None,
) -> dict[str, Any]:
    """Return status_class + optional pending_processor + derived data_source.

    Status rules:
      - unmapped marker / empty where (no out_of_report legacy) → unmapped
      - out_of_report (or feasible never) → advisory
      - in-report, field pending → pending
      - in-report, field now, no check → unauthored
      - in-report, field now, has check → checkable
    """
    bindings = list(where_bindings or [])
    data_source = derive_data_source(bindings, legacy_data_source=legacy_data_source)
    legacy_ds = (
        LEGACY_TO_DERIVED.get(str(legacy_data_source).strip(), None) if legacy_data_source else None
    )

    if not bindings:
        # Empty where used to dump into advisory — that was the junk drawer.
        # Only treat as advisory when legacy explicitly says out_of_report.
        if legacy_ds == "out_of_report":
            return {
                "status_class": STATUS_ADVISORY,
                "data_source": "out_of_report",
                "pending_processor": None,
                "feasible": FEASIBLE_NEVER,
                "modality": "none",
                "processor": "none",
            }
        return {
            "status_class": STATUS_UNMAPPED,
            "data_source": "report_content",
            "pending_processor": None,
            "feasible": FEASIBLE_NOW,
            "modality": "none",
            "processor": "none",
        }

    if all(_is_unmapped_binding(b) for b in bindings):
        return {
            "status_class": STATUS_UNMAPPED,
            "data_source": "report_content",
            "pending_processor": None,
            "feasible": FEASIBLE_NOW,
            "modality": "none",
            "processor": "none",
        }

    merged = _merge_classes([classify_binding(b) for b in bindings])

    if merged.data_source == "out_of_report" or merged.feasible == FEASIBLE_NEVER:
        return {
            "status_class": STATUS_ADVISORY,
            "data_source": "out_of_report",
            "pending_processor": None,
            "feasible": FEASIBLE_NEVER,
            "modality": merged.modality,
            "processor": merged.processor,
        }

    if merged.feasible == FEASIBLE_PENDING:
        return {
            "status_class": STATUS_PENDING,
            "data_source": merged.data_source,
            "pending_processor": merged.pending_processor,
            "feasible": FEASIBLE_PENDING,
            "modality": merged.modality,
            "processor": merged.processor,
        }

    # feasible now
    if not has_check:
        return {
            "status_class": STATUS_UNAUTHORED,
            "data_source": merged.data_source,
            "pending_processor": None,
            "feasible": FEASIBLE_NOW,
            "modality": merged.modality,
            "processor": merged.processor,
        }

    return {
        "status_class": STATUS_CHECKABLE,
        "data_source": merged.data_source,
        "pending_processor": None,
        "feasible": FEASIBLE_NOW,
        "modality": merged.modality,
        "processor": merged.processor,
    }


def normalize_legacy_data_source(value: str | None) -> str | None:
    if not value:
        return None
    return LEGACY_TO_DERIVED.get(str(value).strip())
