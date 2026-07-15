"""Machine-readable fact selectors aligned with SemanticReport / fact_index."""

from __future__ import annotations

from typing import Any

from semantic_report import SemanticReport, normalize_name

# Canonical selectors exposed to the compiler (closed vocabulary).
FACT_SELECTORS: dict[str, str] = {
    "report.overall_result": "Overall inspection result (PASS/FAIL)",
    "report.inspection_type": "Inspection type",
    "report.global_remark": "Inspector global remark",
    "report.factory_address": "Factory address on cover",
    "report.po_reference": "PO reference",
    "report.product_label": "Product name on cover",
    "report.tests_result": "Tests result summary",
    "report.destinations": "Shipment destination names",
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
    if selector == "report.global_remark":
        return semantic.global_remark
    if selector == "report.factory_address":
        return semantic.factory_address
    if selector == "report.po_reference":
        return semantic.po_reference
    if selector == "report.product_label":
        return semantic.product_label
    if selector == "report.tests_result":
        return semantic.tests_result
    if selector == "report.destinations":
        return semantic.destinations

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
    """Map a compiler/human checklist name to the best matching report name.

    Returns the *available* name (raw), or None if below threshold.
    Score = |intersection| / |union| of normalized tokens (Jaccard).
    """
    q_tokens = _token_set(query)
    if not q_tokens:
        return None
    q_norm = normalize_name(query)
    best_name: str | None = None
    best_score = 0.0
    for cand in available_names:
        c_norm = normalize_name(cand)
        if q_norm == c_norm:
            return cand
        c_tokens = _token_set(cand)
        if not c_tokens:
            continue
        inter = len(q_tokens & c_tokens)
        union = len(q_tokens | c_tokens)
        jaccard = inter / union if union else 0.0
        # Containment: require the query to cover most of its own tokens AND
        # not be a tiny prefix of a much longer checklist name (truncation FPs).
        if q_norm in c_norm or c_norm in q_norm:
            coverage = inter / max(len(q_tokens), 1)
            length_ratio = min(len(q_norm), len(c_norm)) / max(len(q_norm), len(c_norm), 1)
            score = 0.85 * coverage * max(length_ratio, 0.35)
        else:
            score = jaccard
        if score > best_score:
            best_score = score
            best_name = cand
    if best_score < min_score:
        return None
    return best_name


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
