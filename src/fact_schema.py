"""Machine-readable fact selectors aligned with SemanticReport / fact_index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from semantic_report import SemanticReport, normalize_name

# Canonical selectors exposed to the compiler (closed vocabulary).
FACT_SELECTORS: dict[str, str] = {
    "report.overall_result": "Overall inspection result (PASS/FAIL/PENDING)",
    "report.inspection_type": "Inspection type",
    "report.inspection_date": "Inspection date",
    "report.planned_date": "Originally planned inspection date",
    "report.days_postponed": "Days postponed (+) or advanced (-) vs planned",
    "report.global_remark": "Inspector global remark",
    "report.supplier_name": "Supplier / responsible entity name",
    "report.factory_name": "Factory / production entity name",
    "report.factory_address": "Factory address on cover",
    "report.production_site": "Production site address",
    "report.po_reference": "PO reference",
    "report.product_label": "Product name on cover",
    "report.sku": "SKU / product reference",
    "report.tests_result": "Tests result summary",
    "report.destinations": "Shipment destination names",
    "report.all_text": "All report text (FULL_REPORT scan)",
    "report.inspector_text": "Inspector remarks/comments/captions (scan without template titles)",
    "report.all_captions": "All photo captions (FULL_REPORT scan)",
    "report.attachment_filenames": "All attachment filenames",
    "report.defect_count": "Number of workmanship defects recorded",
    "report.defects_without_photo": "Defects with photo_count == 0",
    "report.defects": "Workmanship defect rows (name, classification, quantity, photos)",
    "workmanship.result": "Workmanship result",
    "workmanship.aql_level_major": "Major AQL level",
    "workmanship.aql_level_minor": "Minor AQL level",
    "workmanship.aql_level_critical": "Critical AQL level",
    "workmanship.found_major": "Major defects found",
    "workmanship.max_defects_major": "Max allowed major defects",
    "product._first.ordered_quantity": "First product ordered quantity",
    "product._first.real_packed_quantity": "First product on-site packed quantity",
    "product._first.real_produced_quantity": "First product on-site produced quantity",
    "product._first.expected_packed_quantity": "First product expected packed quantity",
    "product._first.unit": "First product unit",
}

_LEGACY_FIELD_MAP = {
    "packed_actual": "real_packed_quantity",
    "produced_actual": "real_produced_quantity",
    "packed_expected": "expected_packed_quantity",
    "produced_expected": "expected_produced_quantity",
    "ordered": "ordered_quantity",
}


def checklist_selector(name: str, field: str) -> str:
    return f"checklist.{normalize_name(name)}.{field}"


def custom_selector(name: str) -> str:
    return f"custom.{normalize_name(name)}"


def legacy_path_to_selector(path: str) -> str:
    """Map legacy fact_index paths to canonical selectors."""
    if path.startswith("node."):
        parts = path.split(".")
        if len(parts) < 3:
            return path
        name = parts[1]
        if len(parts) >= 4 and parts[2] == "photos" and parts[3] == "count":
            return checklist_selector(name, "photo_count")
        if len(parts) >= 4 and parts[2] == "attachments" and parts[3] == "filenames":
            return checklist_selector(name, "attachment_filenames")
        return checklist_selector(name, parts[2])
    if path == "summary.inspection_result":
        return "report.overall_result"
    if path == "summary.global_remark":
        return "report.global_remark"
    if path.startswith("summary.aql."):
        return "workmanship." + path.split("summary.aql.", 1)[1]
    if path.startswith("summary.quantities._first_product."):
        field = path.rsplit(".", 1)[-1]
        mapped = _LEGACY_FIELD_MAP.get(field, field)
        return f"product._first.{mapped}"
    if path.startswith("extract."):
        return path
    return path


def selector_to_fact_path(selector: str) -> str:
    """Resolve selector to fact_index lookup path."""
    if selector.startswith("checklist."):
        _, name, field = selector.split(".", 2)
        if field == "photo_count":
            return f"node.{name}.photos.count"
        if field == "attachment_filenames":
            return f"node.{name}.attachments.filenames"
        return f"node.{name}.{field}"
    if selector == "report.overall_result":
        return "summary.inspection_result"
    if selector == "report.global_remark":
        return "summary.global_remark"
    if selector == "report.factory_address":
        return "summary.factory_address"
    if selector == "report.inspection_type":
        return "summary.inspection_type"
    if selector.startswith("workmanship."):
        field = selector.split(".", 1)[1]
        return f"summary.aql.{field}"
    if selector.startswith("product._first."):
        field = selector.split(".", 2)[2]
        reverse = {v: k for k, v in _LEGACY_FIELD_MAP.items()}
        legacy = reverse.get(field, field)
        return f"summary.quantities._first_product.{legacy}"
    if selector.startswith("custom."):
        return f"custom.{selector.split('.', 1)[1]}"
    return selector


def _first_product_prefix(facts: dict[str, Any]) -> str:
    for key in sorted(facts):
        if key.startswith("summary.quantities.") and key.endswith(".ordered"):
            parts = key.split(".")
            if len(parts) >= 4:
                return ".".join(parts[:3])
    return "summary.quantities._unknown"


def resolve_selector(selector: str, facts: dict[str, Any], semantic: SemanticReport | None = None) -> Any:
    """Read a value for a canonical selector from facts or semantic report."""
    path = selector_to_fact_path(selector)
    token = "summary.quantities._first_product."
    if token in path:
        prefix = _first_product_prefix(facts)
        path = path.replace(token, f"{prefix}.")

    if path in facts:
        return facts[path]
    if path.startswith("extract.") or path.startswith("atom."):
        return facts.get(path)

    if semantic is None:
        return None

    if selector == "report.overall_result":
        return semantic.overall_result
    if selector == "report.inspection_type":
        return semantic.inspection_type
    if selector == "report.inspection_date":
        return semantic.inspection_date
    if selector == "report.planned_date":
        return semantic.planned_date
    if selector == "report.days_postponed":
        return semantic.days_postponed
    if selector == "report.global_remark":
        return semantic.global_remark
    if selector == "report.supplier_name":
        return semantic.supplier_name
    if selector == "report.factory_name":
        return semantic.factory_name
    if selector == "report.factory_address":
        return semantic.factory_address
    if selector == "report.production_site":
        return semantic.production_site
    if selector == "report.po_reference":
        return semantic.po_reference
    if selector == "report.product_label":
        return semantic.product_label
    if selector == "report.sku":
        return semantic.sku
    if selector == "report.tests_result":
        return semantic.tests_result
    if selector == "report.destinations":
        return semantic.destinations
    if selector == "report.all_text":
        return semantic.all_text
    if selector == "report.inspector_text":
        return semantic.inspector_text
    if selector == "report.all_captions":
        return semantic.all_captions
    if selector == "report.attachment_filenames":
        return semantic.attachment_filenames
    if selector == "report.defect_count":
        return semantic.defect_count
    if selector == "report.defects_without_photo":
        return semantic.defects_without_photo
    if selector == "report.defects":
        return semantic.defects

    if selector.startswith("workmanship.") and semantic.workmanship:
        field = selector.split(".", 1)[1]
        return getattr(semantic.workmanship, field, None)

    if selector.startswith("product._first.") and semantic.products:
        field = selector.split(".", 2)[2]
        product = semantic.products[0]
        return getattr(product, field, None)

    if selector.startswith("checklist."):
        parts = selector.split(".", 2)
        if len(parts) < 3:
            return None
        _, name, field = parts
        item = bind_checklist_item(semantic, name)
        if item is None:
            return None
        if field == "photo_count":
            return item.photo_count
        if field == "caption_count":
            return sum(1 for c in (item.photo_captions or []) if str(c).strip())
        if field == "spotlight_count":
            return int(getattr(item, "spotlight_count", 0) or 0)
        if field == "attachment_filenames":
            return item.attachment_filenames
        # Future processors — return sentinel so pending fields resolve to unable, not crash.
        if field == "attachment_content":
            return "UNPARSED"
        if field == "photo_content":
            # Vision loads image bytes separately; resolve to a non-blank locus marker
            # when photos exist so requires_fields does not treat the binding as missing.
            if int(getattr(item, "photo_count", 0) or 0) <= 0:
                return None
            return {
                "photo_count": item.photo_count,
                "captions": list(item.photo_captions or []),
            }
        return getattr(item, field, None)

    if selector.startswith("custom."):
        key = selector.split(".", 1)[1]
        return semantic.custom_fields.get(key)

    return facts.get(path)


def _token_set(name: str) -> set[str]:
    return {t for t in normalize_name(name).split("_") if t and len(t) > 1}


def bind_checklist_name(
    query: str,
    available_names: list[str],
    *,
    min_score: float = 0.45,
) -> str | None:
    """Map a compiler/human checklist name to the best matching report name."""
    scored = [
        (cand, _score_checklist_name(query, cand))
        for cand in available_names
    ]
    scored = [(name, score) for name, score in scored if score >= min_score]
    if not scored:
        return None
    scored.sort(key=lambda row: (-row[1], row[0]))
    return scored[0][0]


def bind_checklist_item(semantic: SemanticReport, query: str) -> Any:
    """Resolve a checklist selector name against a SemanticReport with fuzzy bind."""
    exact = semantic.get_checklist_item(query.replace("_", " "))
    if exact is not None:
        return exact
    exact = semantic.checklist_by_name.get(normalize_name(query))
    if exact is not None:
        return exact
    available = [item.item_name for item in semantic.checklist_items if item.item_name]
    matched = bind_checklist_name(query, available)
    if matched is None:
        return None
    return semantic.get_checklist_item(matched) or semantic.checklist_by_name.get(normalize_name(matched))


def checklist_names_from_semantic(semantic: SemanticReport) -> list[str]:
    return sorted({item.item_name for item in semantic.checklist_items if item.item_name})


_REPORT_LABELS: dict[str, str] = {
    "report.global_remark": "Global remark",
    "report.overall_result": "Overall result",
    "report.factory_address": "Factory address",
    "report.supplier_name": "Supplier name",
    "report.factory_name": "Factory name",
    "report.inspector_text": "Inspector text",
    "report.all_text": "All report text",
    "report.all_captions": "All photo captions",
    "report.product_label": "Product label",
}


@dataclass
class ResolvedField:
    """One bound report field with a human-readable label for LLM payloads."""

    kind: str  # checklist | report | custom | product | workmanship
    name: str  # display name, e.g. "Carton Drop Test"
    field: str  # comment | result | photo_count | …
    value: Any
    selector: str = ""  # canonical selector when available


def _is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    return str(value).strip() == ""


def _checklist_field_value(item: Any, field: str) -> Any:
    if item is None:
        return None
    if field == "photo_count":
        return item.photo_count
    if field == "caption_count":
        return sum(1 for c in (item.photo_captions or []) if str(c).strip())
    if field == "spotlight_count":
        return int(getattr(item, "spotlight_count", 0) or 0)
    if field == "attachment_filenames":
        return item.attachment_filenames
    if field == "photo_captions":
        return item.photo_captions
    if field == "attachment_content":
        return "UNPARSED"
    if field == "photo_content":
        if int(getattr(item, "photo_count", 0) or 0) <= 0:
            return None
        return {
            "photo_count": item.photo_count,
            "captions": list(item.photo_captions or []),
        }
    return getattr(item, field, None)


def _score_checklist_name(query: str, cand: str) -> float:
    q_tokens = _token_set(query)
    if not q_tokens:
        return 0.0
    q_norm = normalize_name(query)
    c_norm = normalize_name(cand)
    if q_norm == c_norm:
        return 1.0
    c_tokens = _token_set(cand)
    if not c_tokens:
        return 0.0
    inter = len(q_tokens & c_tokens)
    union = len(q_tokens | c_tokens)
    jaccard = inter / union if union else 0.0
    if q_norm in c_norm or c_norm in q_norm:
        coverage = inter / max(len(q_tokens), 1)
        length_ratio = min(len(q_norm), len(c_norm)) / max(len(q_norm), len(c_norm), 1)
        return 0.85 * coverage * max(length_ratio, 0.35)
    return jaccard


def bind_checklist_names_all(
    query: str,
    available_names: list[str],
    *,
    min_score: float = 0.45,
) -> list[str]:
    """Return all checklist names scoring at or above ``min_score``, best first."""
    scored: list[tuple[str, float]] = []
    for cand in available_names:
        score = _score_checklist_name(query, cand)
        if score >= min_score:
            scored.append((cand, score))
    scored.sort(key=lambda row: (-row[1], row[0]))
    return [name for name, _ in scored]


def parse_where_entry(entry: Any) -> dict[str, Any]:
    """Normalize a ``where`` list entry to selector, intent, or out_of_report binding."""
    if isinstance(entry, dict):
        # Already-normalized bindings (from compile_block) must pass through.
        if entry.get("type") == "unmapped" or entry.get("kind") == "unmapped":
            return {"type": "unmapped"}
        if entry.get("type") == "selector" and entry.get("selector"):
            return {"type": "selector", "selector": str(entry["selector"])}
        if entry.get("type") == "out_of_report" or (
            entry.get("kind") == "out_of_report"
            or str(entry.get("on") or "").strip() == "out_of_report"
        ):
            kind = str(entry.get("kind") or entry.get("out_of_report_kind") or "other").strip()
            if kind == "out_of_report":
                kind = "other"
            return {"type": "out_of_report", "kind": kind}
        if entry.get("type") == "intent" or entry.get("kind"):
            kind = str(entry.get("kind") or "").strip()
            if kind == "out_of_report":
                return {
                    "type": "out_of_report",
                    "kind": str(entry.get("out_of_report_kind") or "other").strip(),
                }
            if kind == "unmapped":
                return {"type": "unmapped"}
            match = entry.get("match") or []
            if isinstance(match, str):
                match = [m.strip() for m in match.split(",") if m.strip()]
            field = str(entry.get("field") or "comment").strip()
            return {"type": "intent", "kind": kind, "match": list(match), "field": field}
        if entry.get("selector"):
            return {"type": "selector", "selector": str(entry["selector"])}
    text = str(entry).strip()
    if text == "unmapped":
        return {"type": "unmapped"}
    if text.startswith("out_of_report"):
        # out_of_report or out_of_report:booking
        parts = text.split(":", 1)
        kind = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "other"
        return {"type": "out_of_report", "kind": kind}
    if text.startswith("intent:"):
        parts = text.split(":")
        if len(parts) >= 4:
            kind = parts[1]
            match = [m.strip() for m in parts[2].split(",") if m.strip()]
            field = parts[3]
            return {"type": "intent", "kind": kind, "match": match, "field": field}
    return {"type": "selector", "selector": text}


def normalize_where_bindings(where: list[Any] | None) -> list[dict[str, Any]]:
    return [parse_where_entry(entry) for entry in (where or [])]


def _resolve_intent_binding(
    binding: dict[str, Any],
    facts: dict[str, Any],
    semantic: SemanticReport | None,
) -> list[ResolvedField]:
    if semantic is None:
        return []
    kind = str(binding.get("kind") or "").strip().lower()
    field = str(binding.get("field") or "comment").strip()
    match_terms = [str(m).strip() for m in (binding.get("match") or []) if str(m).strip()]
    query = " ".join(match_terms)

    if kind == "section":
        # Resolve every checklist item whose section fuzzy-matches the query,
        # then expose the requested field on each (per-item obligation).
        sections = sorted(
            {item.section for item in semantic.checklist_items if str(item.section or "").strip()}
        )
        matched_sections = bind_checklist_names_all(query, sections) if query else []
        wanted = set(matched_sections)
        resolved: list[ResolvedField] = []
        for item in semantic.checklist_items:
            if str(item.section or "") not in wanted:
                continue
            value = _checklist_field_value(item, field)
            resolved.append(
                ResolvedField(
                    kind="checklist",
                    name=item.item_name or item.section,
                    field=field,
                    value=value,
                    selector=checklist_selector(item.item_name or item.section, field),
                )
            )
        return resolved

    if kind == "checklist":
        available = [item.item_name for item in semantic.checklist_items if item.item_name]
        names = bind_checklist_names_all(query, available) if query else []
        resolved: list[ResolvedField] = []
        for name in names:
            item = semantic.get_checklist_item(name)
            if item is None:
                continue
            value = _checklist_field_value(item, field)
            resolved.append(
                ResolvedField(
                    kind="checklist",
                    name=item.item_name or name,
                    field=field,
                    value=value,
                    selector=checklist_selector(name, field),
                )
            )
        return resolved

    if kind in ("remark", "report"):
        selector = "report.global_remark" if field in ("remark", "global_remark") else f"report.{field}"
        value = resolve_selector(selector, facts, semantic)
        label = _REPORT_LABELS.get(selector, field.replace("_", " ").title())
        return [
            ResolvedField(
                kind="report",
                name=label,
                field=field,
                value=value,
                selector=selector,
            )
        ]

    if kind == "caption":
        if match_terms and semantic.checklist_items:
            available = [item.item_name for item in semantic.checklist_items if item.item_name]
            names = bind_checklist_names_all(query, available)
            resolved = []
            for name in names:
                item = semantic.get_checklist_item(name)
                if item is None:
                    continue
                captions = [c for c in (item.photo_captions or []) if str(c).strip()]
                resolved.append(
                    ResolvedField(
                        kind="checklist",
                        name=item.item_name or name,
                        field="photo_caption",
                        value="\n".join(captions) if captions else None,
                        selector=checklist_selector(name, "photo_captions"),
                    )
                )
            return resolved
        value = semantic.all_captions
        return [
            ResolvedField(
                kind="report",
                name="Photo captions",
                field="caption",
                value=value,
                selector="report.all_captions",
            )
        ]

    return []


def _resolve_selector_binding(
    selector: str,
    facts: dict[str, Any],
    semantic: SemanticReport | None,
) -> list[ResolvedField]:
    value = resolve_selector(selector, facts, semantic)
    if selector.startswith("checklist."):
        parts = selector.split(".", 2)
        if len(parts) < 3:
            return []
        _, slug, field = parts
        display = slug.replace("_", " ").title()
        if semantic is not None:
            item = bind_checklist_item(semantic, slug)
            if item is not None and item.item_name:
                display = item.item_name
        return [
            ResolvedField(
                kind="checklist",
                name=display,
                field=field,
                value=value,
                selector=selector,
            )
        ]
    if selector.startswith("report."):
        field = selector.split(".", 1)[1]
        return [
            ResolvedField(
                kind="report",
                name=_REPORT_LABELS.get(selector, field.replace("_", " ").title()),
                field=field,
                value=value,
                selector=selector,
            )
        ]
    if selector.startswith("custom."):
        key = selector.split(".", 1)[1]
        return [
            ResolvedField(
                kind="custom",
                name=key.replace("_", " ").title(),
                field="value",
                value=value,
                selector=selector,
            )
        ]
    if selector.startswith("product._first."):
        field = selector.split(".", 2)[2]
        return [
            ResolvedField(
                kind="product",
                name="First product",
                field=field,
                value=value,
                selector=selector,
            )
        ]
    if selector.startswith("workmanship."):
        field = selector.split(".", 1)[1]
        return [
            ResolvedField(
                kind="workmanship",
                name="Workmanship",
                field=field,
                value=value,
                selector=selector,
            )
        ]
    return [
        ResolvedField(
            kind="field",
            name=selector,
            field="value",
            value=value,
            selector=selector,
        )
    ]


def resolve_where_bindings(
    where: list[Any] | None,
    facts: dict[str, Any],
    semantic: SemanticReport | None = None,
) -> list[ResolvedField]:
    """Resolve ``where`` entries (selectors or intents) against one report."""
    resolved: list[ResolvedField] = []
    for binding in normalize_where_bindings(where):
        if binding.get("type") in ("out_of_report", "unmapped"):
            continue
        if binding["type"] == "intent":
            resolved.extend(_resolve_intent_binding(binding, facts, semantic))
        else:
            resolved.extend(_resolve_selector_binding(str(binding["selector"]), facts, semantic))
    return resolved


def _format_field_value(value: Any, *, max_len: int = 400) -> str:
    if value is None:
        return "(missing)"
    if isinstance(value, list):
        text = "\n".join(str(v) for v in value if str(v).strip())
    else:
        text = str(value)
    text = text.strip()
    if not text:
        return "(blank)"
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text.replace('"', "'")


def build_evidence_payload(
    requirement: str,
    resolved: list[ResolvedField],
) -> str:
    """Structured labeled evidence for LLM atom/vision prompts.

    Do not put the GI Requirement line in the evidence block — models echo it as
    ``evidence`` quotes, which then pollutes findings Original Content.
    ``requirement`` is kept in the signature for call-site compat only.
    """
    _ = requirement
    lines: list[str] = [
        "Answer ONLY from the bound field content below.",
        "evidence must be a short quote copied from content: (never invent a Requirement line).",
    ]
    if not resolved:
        lines.append("(no bound fields resolved)")
        return "\n".join(lines)[:6000]
    for rf in resolved:
        content = _format_field_value(rf.value)
        lines.append("")
        lines.append(f"[{rf.kind}] {rf.name}")
        lines.append(f"  field: {rf.field}")
        lines.append(f'  content: "{content}"')
    return "\n".join(lines).strip()[:6000]


def all_selectors() -> list[str]:
    """Return base selectors plus dynamic checklist field patterns."""
    patterns = list(FACT_SELECTORS.keys())
    patterns.extend(
        [
            "checklist.<name>.result",
            "checklist.<name>.photo_count",
            "checklist.<name>.comment",
            "checklist.<name>.values",
            "checklist.<name>.applicable",
            "checklist.<name>.attachment_filenames",
            "custom.<name>",
        ]
    )
    return patterns
