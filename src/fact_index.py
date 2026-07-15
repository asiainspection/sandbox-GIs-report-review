"""Build a flat fact lookup from a QIMAone report (parse once, query per checkpoint)."""

from __future__ import annotations

import re
from typing import Any

from report_extract import comment_message
from semantic_report import normalize_name, parse_semantic_report, semantic_to_ir_nodes, semantic_to_ir_summary

_NODE_KEY_RE = re.compile(r"[^a-z0-9]+")


def _node_key(name: str) -> str:
    return _NODE_KEY_RE.sub("_", name.strip().lower()).strip("_")


def _walk_raw_elements(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for el in elements:
        found.append(el)
        if el.get("elements"):
            found.extend(_walk_raw_elements(el["elements"]))
        content = (el.get("content") or {}).get("elements")
        if content:
            found.extend(_walk_raw_elements(content))
        value = el.get("value")
        if isinstance(value, dict):
            for row in value.get("rows") or []:
                for col in row.get("columns") or []:
                    found.append(col)
            header = value.get("header") or {}
            for col in header.get("columns") or []:
                found.append(col)
    return found


def _raw_nodes_by_name(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    result = report.get("result") or {}
    for step in result.get("steps", []):
        for action in step.get("actions", []):
            if action.get("type") != "TESTS_CHECKLIST":
                continue
            checklist = action.get("testsChecklist") or {}
            elements = (checklist.get("content") or {}).get("elements", [])
            for el in _walk_raw_elements(elements):
                name = el.get("name")
                if name:
                    out[_node_key(str(name))] = el
    return out


def build_fact_index(report: dict[str, Any]) -> dict[str, Any]:
    """Typed facts keyed by PDF-aligned semantic names (+ legacy aliases for operators)."""
    semantic = parse_semantic_report(report)
    ir = {
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
    }
    raw_by_name = _raw_nodes_by_name(report)
    facts: dict[str, Any] = {
        "_ir": ir,
        "_semantic": semantic,
        "_nodes": {},
        "_checklist_by_name": semantic.checklist_by_name,
    }

    facts["summary.workmanship_result"] = (semantic.workmanship.result if semantic.workmanship else "")
    facts["summary.global_remark"] = semantic.global_remark
    facts["summary.inspection_result"] = semantic.overall_result
    facts["summary.parse_warnings"] = semantic.parse_warnings

    w = semantic.workmanship
    if w:
        for key, value in {
            "inspection_level": w.inspection_level,
            "aql_level_critical": w.aql_level_critical,
            "aql_level_major": w.aql_level_major,
            "aql_level_minor": w.aql_level_minor,
            "max_defects_critical": w.max_defects_critical,
            "max_defects_major": w.max_defects_major,
            "max_defects_minor": w.max_defects_minor,
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
        }.items():
            facts[f"summary.aql.{key}"] = value

    for product in semantic.products:
        base = f"summary.quantities.{normalize_name(product.product_name)}"
        pairs = {
            "ordered_quantity": product.ordered_quantity,
            "real_produced_quantity": product.real_produced_quantity,
            "expected_produced_quantity": product.expected_produced_quantity,
            "real_packed_quantity": product.real_packed_quantity,
            "expected_packed_quantity": product.expected_packed_quantity,
            # Legacy aliases (operators / existing specs)
            "ordered": product.ordered_quantity,
            "produced_actual": product.real_produced_quantity,
            "packed_actual": product.real_packed_quantity,
            "produced_expected": product.expected_produced_quantity,
            "packed_expected": product.expected_packed_quantity,
        }
        for key, value in pairs.items():
            facts[f"{base}.{key}"] = value

    for item in semantic.checklist_items:
        key = item.lookup_key
        if not key:
            continue
        prefix = f"checklist.{key}"
        facts[f"{prefix}.name"] = item.item_name
        facts[f"{prefix}.result"] = item.result
        facts[f"{prefix}.applicable"] = item.applicable
        facts[f"{prefix}.comment"] = item.comment
        facts[f"{prefix}.photo_count"] = item.photo_count
        facts[f"{prefix}.values"] = item.values
        facts[f"{prefix}.attachment_filenames"] = item.attachment_filenames
        # Legacy node.* paths for existing operator specs
        node_prefix = f"node.{key}"
        facts[f"{node_prefix}.result"] = item.result
        facts[f"{node_prefix}.applicable"] = item.applicable
        facts[f"{node_prefix}.comment"] = item.comment
        facts[f"{node_prefix}.photos.count"] = item.photo_count
        facts[f"{node_prefix}.photos.captions"] = item.photo_captions
        facts[f"{node_prefix}.values"] = item.values
        facts[f"{node_prefix}.attachments.filenames"] = item.attachment_filenames
        facts["_nodes"][key] = {
            "name": item.item_name,
            "result": item.result,
            "applicable": item.applicable,
            "comment": item.comment,
            "photos": {"count": item.photo_count, "captions": item.photo_captions},
            "values": item.values,
        }

        raw = raw_by_name.get(key) or {}
        if raw.get("comment"):
            facts[f"{node_prefix}.comment"] = comment_message(raw.get("comment"))

    return facts


def get_fact(facts: dict[str, Any], path: str) -> Any:
    return facts.get(path)
