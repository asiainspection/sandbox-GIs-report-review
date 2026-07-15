#!/usr/bin/env python3
"""
Convert a QIMAone inspection report JSON into a compact, typed Intermediate
Representation (IR).

Why this exists
---------------
The Markdown export (`report_to_md.py`) is optimized for a human to *read*, so it
flattens structured facts into prose and tables. That flattening is lossy:
`applicable=false`, `requires_photo=true`, per-photo captions and photo counts
all become sentences the model has to re-parse and re-interpret. That is the
root cause of failures like checkpoint 3_1_3, where a `NOT_APPLICABLE` row with
9 attached photos was misread as a violation.

Both this IR and the Markdown renderer read facts from `report_extract.py` (the
single parsing layer); neither parses the raw payload itself.

The IR keeps those facts as *typed fields* instead of prose. It is:
- lossless for the fields checks actually care about,
- small (a few KB per report vs the full API payload), and
- stable in shape, so deterministic checks can read fields directly instead of
  asking an LLM to guess them.

The IR is a flat list of `nodes` (one per checklist element) plus a `meta`
header for cross-reference checks (address vs booking, product vs PO, etc.).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterator

# The IR reads facts from the single extraction layer — not from the Markdown
# renderer — so nothing structural depends on how we happen to format for humans.
from report_extract import (
    clean_text,
    comment_message,
    extract_checklists,
    extract_custom_fields,
    extract_products,
    extract_supplementary_sections,
    format_address,
    photo_details,
    summarize_workmanship,
    translated_field,
    translated_name,
)

# Element types that represent a single answerable checklist item.
LEAF_TYPES = {"MULTIPLE_CHOICE", "TEXT", "NUMBER", "BOOLEAN", "DATE", "PASS_FAIL", "TABLE"}


def _requires_photo(element: dict[str, Any]) -> bool:
    return any(req.get("type") == "PICTURE" for req in element.get("requirements") or [])


def _values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean_text(v) for v in value if clean_text(v)]
    if isinstance(value, (str, int, float)) and clean_text(value):
        return [clean_text(value)]
    return []


def walk_nodes(
    elements: list[dict[str, Any]],
    *,
    section: str,
    path: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield one IR node per leaf checklist element, recursing through DIVs."""
    path = path or []
    for element in elements:
        etype = element.get("type")
        name = translated_name(element) or etype or "Item"
        current_path = path + ([name] if name else [])

        if etype == "DIV":
            div_section = name if name not in ("", "Category name") else section
            yield from walk_nodes(
                element.get("elements") or [],
                section=div_section or section,
                path=current_path,
            )
            continue

        if etype not in LEAF_TYPES:
            continue

        count, _, captions = photo_details(element.get("images"))
        applicable = bool(element.get("applicable", True)) and not bool(element.get("notApplicable"))

        yield {
            "path": " > ".join(current_path),
            "section": section,
            "name": name,
            "type": etype,
            "result": clean_text(element.get("result")) or "NO_RESULT",
            "applicable": applicable,
            "requires_photo": _requires_photo(element),
            "photos": {"count": count, "captions": captions},
            "values": _values(element.get("value")),
            "comment": comment_message(element.get("comment")),
        }


def build_meta(report: dict[str, Any]) -> dict[str, Any]:
    """Report identity + parties used by cross-reference checks (address, product)."""
    result_obj = report.get("result") or {}
    products = extract_products(report)
    destinations = [
        clean_text((dest.get("entity") or {}).get("name") or dest.get("name"))
        for dest in report.get("destinations") or []
    ]
    inspection_type = translated_field((report.get("inspectionType") or {}), "description") or clean_text(
        (report.get("inspectionType") or {}).get("description")
    )
    return {
        "report_id": str(report.get("reportId", "")),
        "inspection_id": str(report.get("inspectionId", "")),
        "inspection_result": clean_text(report.get("inspectionResult") or result_obj.get("result")),
        "inspection_type": inspection_type,
        "inspection_date": clean_text(report.get("inspectionDate")),
        "product": products[0]["name"] if products else "",
        "sku": products[0]["sku"] if products else "",
        "po": products[0]["po"] if products else "",
        "factory_address": format_address(report.get("entity")),
        "production_site": format_address(report.get("productionSiteEntity")),
        "destinations": [d for d in destinations if d],
    }


def build_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Report-level FACTS only (results, AQL, quantities, instructions, defects).

    These live outside the checklist elements but are needed by cross-report
    checks (AQL vs inspection type, packed vs ordered, photos-per-defect, …).

    Facts, not judgments: this returns only what the platform recorded (numbers,
    answers, logged defects). Verdicts like "packed < 80%" or "section not pass"
    are checkpoint *outcomes* — the check engine derives them from these facts.
    Pre-computing them here (the old ``attention_items``) let a wrong opinion
    contradict a true number and poisoned the model, so it is gone.
    """
    result_obj = report.get("result") or {}
    products = extract_products(report)
    workmanship = summarize_workmanship(result_obj)
    supplementary = extract_supplementary_sections(result_obj)
    checklists = extract_checklists(result_obj)
    global_remark = comment_message(result_obj.get("globalRemark"))
    sampling = result_obj.get("samplingSize") or report.get("inspectionSamplingSize") or {}
    measurements = report.get("aqlMeasurements") or {}

    defects: list[dict[str, Any]] = []
    for checklist in checklists:
        for defect in checklist.get("defects", []):
            defects.append(
                {
                    "name": defect.get("name", ""),
                    "classification": defect.get("classification", ""),
                    "quantity": defect.get("quantity", 0),
                    "photos": defect.get("photos", 0),
                    "captions": defect.get("photo_captions", []),
                }
            )

    return {
        "tests_result": clean_text(result_obj.get("testsResult")),
        "workmanship_result": workmanship.get("result", ""),
        "aql": {
            "inspection_level": clean_text(sampling.get("inspectionLevel")),
            # AQL levels (the quality standard, e.g. Major 2.5 / Minor 4.0) — what GIs verify.
            "aql_level_critical": workmanship.get("aql_level_critical"),
            "aql_level_major": workmanship.get("aql_level_major"),
            "aql_level_minor": workmanship.get("aql_level_minor"),
            "measurement_level": clean_text(measurements.get("level")),
            "measurement_aql": clean_text(measurements.get("aql")),
            # Acceptance points (max defects allowed at this sample size) — NOT the AQL level.
            "acceptance_critical": workmanship.get("acceptance_critical"),
            "acceptance_major": workmanship.get("acceptance_major"),
            "acceptance_minor": workmanship.get("acceptance_minor"),
            "sample_size_critical": sampling.get("criticalSampleSize"),
            "sample_size_major": sampling.get("majorSampleSize"),
            "sample_size_minor": sampling.get("minorSampleSize"),
            "found_critical": workmanship.get("found_critical"),
            "found_major": workmanship.get("found_major"),
            "found_minor": workmanship.get("found_minor"),
        },
        "quantities": [
            {
                k: p[k]
                for k in (
                    "name", "unit", "ordered", "produced_actual", "packed_actual",
                    "produced_expected", "packed_expected", "shipment_date",
                )
            }
            for p in products
        ],
        "inspector_instructions": [block["text"] for block in supplementary.get("instructions", [])],
        "custom_fields": extract_custom_fields(report),
        "defects": defects,
        "global_remark": global_remark,
    }


def build_ir(report: dict[str, Any]) -> dict[str, Any]:
    """Convert a full QIMAone report payload into the IR (via semantic layer)."""
    from semantic_report import parse_semantic_report, semantic_to_ir_nodes, semantic_to_ir_summary

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
    }


def build_ir_legacy(report: dict[str, Any]) -> dict[str, Any]:
    """Previous IR builder (kept for reference tests)."""
    result_obj = report.get("result") or {}
    nodes: list[dict[str, Any]] = []
    for step in result_obj.get("steps", []):
        for action in step.get("actions", []):
            if action.get("type") != "TESTS_CHECKLIST":
                continue
            checklist = action.get("testsChecklist") or {}
            checklist_name = translated_name(checklist) or clean_text(checklist.get("name"))
            elements = (checklist.get("content") or {}).get("elements", [])
            nodes.extend(walk_nodes(elements, section=checklist_name))
    return {"meta": build_meta(report), "summary": build_summary(report), "nodes": nodes}


# --- Invariant suite: QA the parse without re-reading the PDF ------------------

def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ir_invariants(ir: dict[str, Any]) -> list[str]:
    """Cheap contract checks the IR must satisfy for ANY report."""
    violations: list[str] = []
    summary = ir.get("summary") or {}

    for q in summary.get("quantities") or []:
        name = q.get("name")
        packed_exp = _to_float(q.get("expected_packed_quantity", q.get("packed_expected")))
        produced_exp = _to_float(q.get("expected_produced_quantity", q.get("produced_expected")))
        packed_act = q.get("real_packed_quantity", q.get("packed_actual"))
        produced_act = q.get("real_produced_quantity", q.get("produced_actual"))
        ordered = q.get("ordered_quantity", q.get("ordered"))
        if packed_exp is not None and produced_exp is not None and packed_exp > produced_exp:
            violations.append(
                f"quantity[{name}]: expected_packed_quantity {packed_exp:g} > expected_produced_quantity "
                f"{produced_exp:g} (labels likely swapped)"
            )
        if ordered and not packed_act and not produced_act:
            violations.append(f"quantity[{name}]: no on-site actual counts (quantity checks untrusted)")

    aql = summary.get("aql") or {}
    # A PASS workmanship result implies defects found <= acceptance point.
    if (summary.get("workmanship_result") or "").upper() == "PASS":
        for sev in ("critical", "major", "minor"):
            found = _to_float(aql.get(f"found_{sev}"))
            accept = _to_float(aql.get(f"acceptance_{sev}"))
            if found is not None and accept is not None and found > accept:
                violations.append(
                    f"aql[{sev}]: workmanship PASS but found {found:g} > acceptance {accept:g}"
                )
    # AQL level (a standard like 2.5/4.0) must not equal the acceptance point (a
    # defect count) — equality means extraction collapsed the two distinct facts.
    lvl_major = _to_float(aql.get("aql_level_major"))
    acc_major = _to_float(aql.get("acceptance_major"))
    if lvl_major is not None and acc_major is not None and lvl_major == acc_major:
        violations.append("aql[major]: level == acceptance point (level/acceptance likely conflated)")

    return violations


# --- Rendering the IR to compact text for the LLM ------------------------------

def render_meta(meta: dict[str, Any]) -> str:
    lines = ["## Report facts"]
    for label, key in (
        ("Overall result", "inspection_result"),
        ("Inspection type", "inspection_type"),
        ("Product", "product"),
        ("SKU", "sku"),
        ("PO", "po"),
        ("Factory address", "factory_address"),
        ("Production site", "production_site"),
    ):
        value = str(meta.get(key) or "")
        if value:
            lines.append(f"- {label}: {value}")
    if meta.get("destinations"):
        lines.append(f"- Destinations: {', '.join(meta['destinations'])}")
    return "\n".join(lines) if len(lines) > 1 else ""


def render_summary(summary: dict[str, Any]) -> str:
    lines = ["## Summary"]
    if summary.get("tests_result"):
        lines.append(f"- Tests result: {summary['tests_result']}")
    if summary.get("workmanship_result"):
        lines.append(f"- Workmanship result: {summary['workmanship_result']}")
    aql = summary.get("aql") or {}
    if any(v not in (None, "") for v in aql.values()):
        lines.append(
            f"- Inspection level: {aql.get('inspection_level', '')}"
        )
        lines.append(
            f"- AQL levels (quality standard) critical/major/minor = "
            f"{aql.get('aql_level_critical')}/{aql.get('aql_level_major')}/{aql.get('aql_level_minor')}"
        )
        if aql.get("measurement_aql") or aql.get("measurement_level"):
            lines.append(
                f"- Measurement sampling: level={aql.get('measurement_level')} "
                f"AQL={aql.get('measurement_aql')}"
            )
        # Defects table exactly as the cover shows it: found / sample size / max allowed.
        lines.append(
            "- Defects (found / sample size / max allowed = acceptance point): "
            f"critical {aql.get('found_critical')}/{aql.get('sample_size_critical')}/{aql.get('acceptance_critical')} | "
            f"major {aql.get('found_major')}/{aql.get('sample_size_major')}/{aql.get('acceptance_major')} | "
            f"minor {aql.get('found_minor')}/{aql.get('sample_size_minor')}/{aql.get('acceptance_minor')}"
        )
    for q in summary.get("quantities") or []:
        real_p = q.get("real_packed_quantity", q.get("packed_actual"))
        real_prod = q.get("real_produced_quantity", q.get("produced_actual"))
        exp_p = q.get("expected_packed_quantity", q.get("packed_expected"))
        exp_prod = q.get("expected_produced_quantity", q.get("produced_expected"))
        lines.append(
            f"- Quantity [{q.get('name')}]: ordered={q.get('ordered')} "
            f"real_produced={real_prod} real_packed={real_p} "
            f"expected_produced={exp_prod} expected_packed={exp_p} "
            f"unit={q.get('unit')} shipment={q.get('shipment_date')}"
        )
    for d in summary.get("defects") or []:
        lines.append(
            f"- Defect [{d.get('classification')}] {d.get('name')}: qty={d.get('quantity')} "
            f"photos={d.get('photos')}"
        )
    if summary.get("inspector_instructions"):
        lines.append("- Inspector instructions:")
        lines.extend(f"  {i}. {text}" for i, text in enumerate(summary["inspector_instructions"], start=1))
    for label, value in (summary.get("custom_fields") or {}).items():
        lines.append(f"- {label}: {value}")
    if summary.get("global_remark"):
        lines.append(f"- Global remark: {summary['global_remark']}")
    return "\n".join(lines) if len(lines) > 1 else ""


def render_node(node: dict[str, Any]) -> str:
    photos = node.get("photos") or {}
    captions = photos.get("captions") or []
    result = node.get("result")
    values = node.get("values") or []
    parts = [f"[{node.get('section')}] {node.get('name')}"]
    # A question with no pass/fail (NO_RESULT) but an answer in `value` is not
    # "unchecked" — surface the answer, or the model treats it as missing evidence.
    if result in ("NO_RESULT", "", None) and values:
        parts.append("answer=" + ", ".join(values))
    else:
        parts.append(f"result={result}")
        if values:
            parts.append("value=" + ", ".join(values))
    parts.append(f"applicable={node.get('applicable')}")
    if photos.get("count"):
        parts.append(f"photos={photos['count']}")
    if captions:
        parts.append("captions=" + "; ".join(captions))
    if node.get("comment"):
        parts.append("comment=" + node["comment"])
    if node.get("requires_photo"):
        parts.append("requires_photo=yes")
    return " | ".join(parts)


def render_nodes(nodes: list[dict[str, Any]]) -> str:
    if not nodes:
        return ""
    return "## Checklist items\n" + "\n".join("- " + render_node(node) for node in nodes)


def render_context(
    ir: dict[str, Any],
    nodes: list[dict[str, Any]],
    *,
    include_summary: bool = True,
) -> str:
    """Compact text evidence for the LLM: report facts + (summary) + selected nodes.

    ``include_summary`` carries the cross-report facts (AQL, quantities, inspector
    instructions, defects). Scoped checks that only look at their own node don't
    need it, so we drop it to keep their context tiny.
    """
    blocks = [render_meta(ir.get("meta", {}))]
    if include_summary:
        blocks.append(render_summary(ir.get("summary", {})))
    blocks.append(render_nodes(nodes))
    return "\n\n".join(block for block in blocks if block)


def dumps(ir: dict[str, Any], *, compact: bool = True) -> str:
    if compact:
        return json.dumps(ir, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(ir, ensure_ascii=False, indent=2)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert QIMAone report JSON to the checkpoint IR.")
    parser.add_argument("inputs", nargs="+", type=Path, help="One or more report JSON files.")
    parser.add_argument("-o", "--output-dir", type=Path, default=None)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print instead of compact JSON.")
    parser.add_argument("--stdout", action="store_true", help="Write to stdout (single input only).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.stdout and len(args.inputs) != 1:
        print("error: --stdout requires exactly one input file", file=sys.stderr)
        return 2
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in args.inputs:
        if not input_path.exists():
            print(f"error: file not found: {input_path}", file=sys.stderr)
            return 1
        report = json.loads(input_path.read_text(encoding="utf-8"))
        ir = build_ir(report)
        text = dumps(ir, compact=not args.pretty)
        if args.stdout:
            sys.stdout.write(text + "\n")
            continue
        target_dir = args.output_dir or input_path.parent
        output_path = target_dir / f"{input_path.stem}_ir.json"
        output_path.write_text(text, encoding="utf-8")
        print(f"Wrote {output_path} ({len(ir['nodes'])} nodes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
