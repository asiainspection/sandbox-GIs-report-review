#!/usr/bin/env python3
"""Build Hallmark PDF-backed fixtures when QIMAone JSON is unavailable.

Caches:
  - MD text extract from PDF (old-path dump material)
  - JSON skeleton = synthetic Hallmark + PDF cover facts (+ injectable checklist fields)

Honest limitation: checklist structure is synthetic; cover stats / remarks come from the real PDF.
"""

from __future__ import annotations

import copy
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_facts import extract_cover_facts, pdf_full_text  # noqa: E402

PDF_DIR = ROOT / "data/clients/hallmark/pdfs"
SYN_CORRECT = ROOT / "data/clients/hallmark/synthetic/hallmark_correct.json"
OUT_JSON = ROOT / "data/clients/hallmark/corrected"
OUT_MD = ROOT / "data/pipeline/reports"
OUT_FLAWED = ROOT / "data/clients/hallmark/flawed"
CLIENT = ROOT / "data/clients/hallmark/client.json"

_PHOTO = {
    "type": "PHOTO",
    "date": "2026-07-01T12:00:00.000Z",
    "timezone": "GMT",
    "pictureTags": [],
    "translations": {},
    "pictureSource": "UPLOAD",
    "uploadedFromDeviceType": "PHONE",
    "video": False,
}


def _photo(n: int) -> dict[str, Any]:
    return {**_PHOTO, "imageId": f"hmk-{uuid.uuid4().hex[:10]}-{n}"}


def _walk(elements: list[dict]) -> list[dict]:
    found: list[dict] = []
    for el in elements:
        found.append(el)
        nested = el.get("elements") or (el.get("content") or {}).get("elements")
        if nested:
            found.extend(_walk(nested))
        value = el.get("value")
        if isinstance(value, dict):
            for row in value.get("rows") or []:
                for col in row.get("columns") or []:
                    found.append(col)
    return found


def _checklist_elements(report: dict[str, Any]) -> list[dict]:
    out: list[dict] = []
    for step in (report.get("result") or {}).get("steps", []):
        for action in step.get("actions", []):
            checklist = action.get("testsChecklist") or {}
            out.extend(_walk((checklist.get("content") or {}).get("elements", [])))
    return out


def _el_name(el: dict) -> str:
    name = el.get("name") or ""
    if isinstance(name, dict):
        name = name.get("message") or ""
    tr = ((el.get("translations") or {}).get("en") or {}).get("name")
    return str(tr or name or "")


def _ensure_extra_checklist_items(report: dict[str, Any]) -> None:
    """Append Hallmark-shaped checklist items used by structural injectors / WHEN gates."""
    # Must attach under TESTS_CHECKLIST — semantic parse ignores INSPECTION_DETAILS checklists.
    target_elements = None
    for step in (report.get("result") or {}).get("steps") or []:
        for action in step.get("actions") or []:
            if action.get("type") != "TESTS_CHECKLIST":
                continue
            checklist = action.get("testsChecklist") or {}
            content = checklist.setdefault("content", {})
            elements = content.setdefault("elements", [])
            names = {_el_name(el).lower() for el in _walk(elements)}
            if any("defect photo" in n for n in names) or any("checkpoint" in n for n in names):
                target_elements = elements
                break
            if target_elements is None:
                target_elements = elements
        if target_elements is not None and any(
            "defect photo" in _el_name(el).lower() for el in _walk(target_elements)
        ):
            break
    if target_elements is None:
        return

    existing = {_el_name(el).lower() for el in _walk(target_elements)}

    def add(name: str, result: str = "PASS", *, values: list | None = None, images: list | None = None) -> None:
        key = name.lower()
        if any(key in e or e in key for e in existing):
            return
        eid = f"hmk-{uuid.uuid4().hex[:8]}"
        target_elements.append(
            {
                "id": eid,
                "type": "MULTIPLE_CHOICE",
                "name": name,
                "translations": {"en": {"name": name}},
                "result": result,
                "applicable": True,
                "notApplicable": result == "NOT_APPLICABLE",
                "value": values or (["PASSED"] if result == "PASS" else []),
                "images": images or [],
                "comment": {"message": "", "translations": {"en": {"message": ""}}},
            }
        )
        existing.add(name.lower())

    add("High Attention Product (HA)", result="NO_RESULT", values=["No"])
    add("HCLP", result="NO_RESULT", values=["No"])
    add("SR Test Report Check (Document Availability checklist)", result="PASS", values=["Passed"])
    add("FR Test Report Check (Document Availability checklist)", result="PASS", values=["Passed"])
    if not any("defect photo" in e for e in existing):
        add("Defect photos (Workmanship section)", result="PASS", images=[_photo(0)])


def _apply_cover(report: dict[str, Any], cover) -> None:
    result = report.setdefault("result", {})
    result["inspectionResult"] = cover.overall_result or result.get("inspectionResult") or "PASS"
    if cover.global_remark_lines:
        msg = "\n".join(cover.global_remark_lines)
        result["globalRemark"] = {"message": msg, "translations": {"en": {"message": msg}}}
    # Patch first product quantities if present
    for step in result.get("steps", []):
        for action in step.get("actions", []):
            products = action.get("products") or []
            for product in products[:1]:
                if cover.ordered_quantity is not None:
                    product["orderedQuantity"] = cover.ordered_quantity
                if cover.real_packed_quantity is not None:
                    product["realPackedQuantity"] = cover.real_packed_quantity
                if cover.real_produced_quantity is not None:
                    product["realProducedQuantity"] = cover.real_produced_quantity


def _inj_defect_extra_photos(report: dict[str, Any]) -> list[str]:
    touched = False
    for el in _checklist_elements(report):
        if "defect photo" in _el_name(el).lower():
            el["images"] = [_photo(i) for i in range(3)]
            el["result"] = "PASS"
            touched = True
    return ["9_2_6"] if touched else []


def _inj_sr_failed_overall_pass(report: dict[str, Any]) -> list[str]:
    """SR not Passed while overall PASS — Hallmark structural pattern (2_1_1)."""
    result = report.setdefault("result", {})
    result["inspectionResult"] = "PASS"
    for el in _checklist_elements(report):
        if "sr test report" in _el_name(el).lower():
            el["result"] = "FAIL"
            el["value"] = ["Failed"]
            return ["2_1_1"]
    return []


def _inj_fr_failed_overall_pass(report: dict[str, Any]) -> list[str]:
    result = report.setdefault("result", {})
    result["inspectionResult"] = "PASS"
    for el in _checklist_elements(report):
        if "fr test report" in _el_name(el).lower():
            el["result"] = "FAIL"
            el["value"] = ["Failed"]
            return ["2_2_1"]
    return []


def build_one(stem: str, pdf_path: Path) -> dict[str, Any]:
    text = pdf_full_text(pdf_path)
    cover = extract_cover_facts(text[:50000])
    OUT_MD.mkdir(parents=True, exist_ok=True)
    (OUT_MD / f"{stem}.md").write_text(
        f"# Hallmark report {stem}\n\n"
        f"_Source PDF: {pdf_path.name}_\n"
        f"_Inspection reference (PDF): {cover.inspection_reference}_\n\n"
        + text[:120000],
        encoding="utf-8",
    )

    base = json.loads(SYN_CORRECT.read_text(encoding="utf-8")) if SYN_CORRECT.exists() else {}
    report = copy.deepcopy(base)
    _ensure_extra_checklist_items(report)
    _apply_cover(report, cover)
    report["_fixture_meta"] = {
        "source": "pdf_cover_overlay",
        "pdf": pdf_path.name,
        "sku": cover.sku,
        "inspection_reference": cover.inspection_reference,
        "note": "QIMAone JSON unavailable for Hallmark tenant; checklist scaffold is synthetic.",
    }
    OUT_JSON.mkdir(parents=True, exist_ok=True)
    (OUT_JSON / f"{stem}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    if not SYN_CORRECT.exists():
        from make_synthetic_gi_reports import make_hallmark_synthetic

        make_hallmark_synthetic()

    introduced: dict[str, dict[str, str]] = {}
    stems = sorted(p.stem for p in PDF_DIR.glob("*.pdf"))
    OUT_FLAWED.mkdir(parents=True, exist_ok=True)

    injectors = [
        _inj_defect_extra_photos,
        _inj_sr_failed_overall_pass,
        _inj_fr_failed_overall_pass,
    ]

    for i, stem in enumerate(stems):
        pdf = PDF_DIR / f"{stem}.pdf"
        report = build_one(stem, pdf)
        print(f"Wrote corrected {stem}")

        flawed = copy.deepcopy(report)
        labels: dict[str, str] = {}
        # Each report gets defect-photo inject + one of SR/FR rotates
        for cid in _inj_defect_extra_photos(flawed):
            labels[cid] = "injected by _inj_defect_extra_photos"
            # Same underlying photo_count fact also trips the Photos-section twin rule.
            labels["4_3_2"] = "same inject as 9_2_6 (defect photo_count>1)"
        extra = injectors[1 + (i % 2)]
        for cid in extra(flawed):
            labels[cid] = f"injected by {extra.__name__}"
        out = OUT_FLAWED / f"{stem}_flawed.json"
        out.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        key = f"report_{stem.lower()}_flawed"
        introduced[key] = labels
        print(f"Wrote {out.name} labels={sorted(labels)}")

    client = {
        "id": "hallmark",
        "name": "Hallmark Cards (PDF-backed fixtures; JSON API blocked)",
        "gi_rules": "gi/rules.md",
        "corrected_dir": "corrected",
        "flawed_dir": "flawed",
        "introduced_checkpoints": introduced,
        "holdout_keys": sorted(introduced.keys()),
        "fixture_note": (
            "QIMAone report GET returned 404/500 for inspection refs from PDFs "
            "(tenant/token mismatch). Fixtures overlay real PDF cover facts onto a "
            "Hallmark-shaped synthetic checklist scaffold."
        ),
    }
    CLIENT.write_text(json.dumps(client, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {CLIENT}")


if __name__ == "__main__":
    main()
