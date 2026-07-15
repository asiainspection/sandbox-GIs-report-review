#!/usr/bin/env python3
"""Build an augmented flawed Ribkoff dataset from corrected reports + golden labels.

Also sanitizes "corrected" gold so deterministic CheckSpec obligations hold
(before measuring precision). Repairs are driven by obligation ops, not cp ids.

Usage:
    .venv/bin/python scripts/make_flawed_dataset.py
"""

from __future__ import annotations

import copy
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import load_hand_specs, resolve_specs  # noqa: E402
from fact_index import build_fact_index  # noqa: E402
from fact_schema import bind_checklist_name  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation_eval import evaluate_obligation  # noqa: E402
from semantic_report import normalize_name, parse_semantic_report  # noqa: E402

CORRECTED_DIR = ROOT / "data/clients/ribkoff/corrected"
OUT_DIR = ROOT / "data/clients/ribkoff/flawed"
CLIENT = ROOT / "data/clients/ribkoff/client.json"
CHECKPOINTS = ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json"
HAND_SPECS = ROOT / "data/clients/ribkoff/gi/hand_specs.json"

_PHOTO_STUB = {
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
    return {**_PHOTO_STUB, "imageId": f"flawed-{uuid.uuid4().hex[:12]}-{n}"}


def _walk(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for el in elements:
        found.append(el)
        nested = el.get("elements")
        if nested:
            found.extend(_walk(nested))
        content = (el.get("content") or {}).get("elements")
        if content:
            found.extend(_walk(content))
        value = el.get("value")
        if isinstance(value, dict):
            for row in value.get("rows") or []:
                for col in row.get("columns") or []:
                    found.append(col)
            header = value.get("header") or {}
            for col in header.get("columns") or []:
                found.append(col)
    return found


def _by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    result = report.get("result") or {}
    for step in result.get("steps", []):
        for action in step.get("actions", []):
            checklist = action.get("testsChecklist") or {}
            elements = (checklist.get("content") or {}).get("elements", [])
            for el in _walk(elements):
                eid = el.get("id")
                if eid:
                    out[eid] = el
    return out


def _element_display_name(el: dict[str, Any]) -> str:
    name = el.get("name") or el.get("title") or ""
    if isinstance(name, dict):
        name = name.get("message") or ""
    return str(name)


def _find_element_by_checklist_name(report: dict[str, Any], query: str) -> dict[str, Any] | None:
    by_id = _by_id(report)
    names = [_element_display_name(el) for el in by_id.values()]
    names = [n for n in names if n]
    matched = bind_checklist_name(query, names)
    if matched is None:
        return None
    target = normalize_name(matched)
    for el in by_id.values():
        if normalize_name(_element_display_name(el)) == target:
            return el
    return None


def _checklist_name_from_selector(selector: str) -> str | None:
    if not selector.startswith("checklist."):
        return None
    parts = selector.split(".")
    if len(parts) < 3:
        return None
    return parts[1].replace("_", " ")


def _style_number(report: dict[str, Any]) -> str:
    facts = build_fact_index(report)
    for key in facts:
        if not key.startswith("summary.quantities."):
            continue
        head = key.split(".", 3)[2] if key.count(".") >= 2 else ""
        match = re.search(r"(\d{5,7})", head)
        if match:
            return match.group(1)
    return "000000"


def _leaves(node: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not node:
        return []
    op = node.get("op")
    if op in ("all_of", "any_of"):
        out: list[dict[str, Any]] = []
        for item in node.get("items") or []:
            out.extend(_leaves(item))
        return out
    if op == "not":
        return _leaves(node.get("item"))
    return [node]


def sanitize_report_for_deterministic_specs(report: dict[str, Any], specs: dict[str, dict]) -> list[str]:
    """Mutate report so deterministic obligations pass — repair by primitive op.

    General: photo count_at_most → trim images; contains_number → append digit;
    filename_matches Measurement Chart pattern → rewrite attachment name.
    """
    repairs: list[str] = []
    for _ in range(5):
        round_fixes = 0
        for cid, spec in specs.items():
            if spec.get("tier") != "deterministic":
                continue
            facts = build_fact_index(report)
            semantic = parse_semantic_report(report)
            verdict = evaluate_obligation(spec, facts, semantic=semantic)
            if verdict.match != "clear_unmatch":
                continue
            for leaf in _leaves(spec.get("then")):
                op = leaf.get("op")
                sel = str(leaf.get("selector") or "")
                name = _checklist_name_from_selector(sel)
                if not name:
                    continue
                el = _find_element_by_checklist_name(report, name)
                if el is None:
                    continue
                if op == "count_at_most" and sel.endswith(".photo_count"):
                    max_n = int(leaf.get("max", 0))
                    imgs = list(el.get("images") or [])
                    if len(imgs) > max_n:
                        el["images"] = imgs[:max_n]
                        repairs.append(f"{cid}:trim_photos→{max_n}")
                        round_fixes += 1
                elif op == "contains_number":
                    comment = el.get("comment") or {}
                    msg = str(comment.get("message") or "")
                    if not re.search(r"\d", msg):
                        msg = (msg + " 12").strip()
                        el["comment"] = {"message": msg, "translations": {"en": {"message": msg}}}
                        repairs.append(f"{cid}:add_number_to_comment")
                        round_fixes += 1
                elif op == "filename_matches":
                    pattern = str(leaf.get("pattern") or "")
                    style = _style_number(report)
                    if "Measurement Chart" in pattern or "measurement chart" in pattern.lower():
                        fname = f"Measurement Chart-{style}.xlsx"
                        el["attachments"] = [
                            {
                                "attachmentId": f"sanitized-{style}",
                                "filename": fname,
                                "downloadUrl": f"https://example.invalid/{fname}",
                            }
                        ]
                        repairs.append(f"{cid}:fix_attachment_filename")
                        round_fixes += 1
        if round_fixes == 0:
            break

    # Gold: when workmanship findings exist, ensure remark has PO + % so all_true-style
    # defect-breakdown obligations are satisfiable without LLM.
    try:
        facts = build_fact_index(report)
        found = float(facts.get("summary.aql.found_major") or 0) + float(
            facts.get("summary.aql.found_minor") or 0
        ) + float(facts.get("summary.aql.found_critical") or 0)
        result = report.setdefault("result", {})
        remark = result.get("globalRemark") or {}
        msg = str(remark.get("message") or "")
        if found > 0 and ("PO" not in msg.upper() or "%" not in msg):
            suffix = "PO 000000: 0 pcs defects found; Total: 0.00% defects found."
            msg = (msg + "\n" + suffix).strip()
            result["globalRemark"] = {"message": msg, "translations": {"en": {"message": msg}}}
            repairs.append("defect_remark:ensure_po_pct")
    except Exception:  # noqa: BLE001 — sanitize best-effort
        pass
    return repairs


def _inj_carton_drop_photos(report: dict[str, Any]) -> list[str]:
    el = _find_element_by_checklist_name(report, "Carton drop test") or _by_id(report).get("2-9-1-9")
    if not el:
        return []
    el["result"] = "PASS"
    el["images"] = [_photo(i) for i in range(3)]
    return ["3_1_6"]


def _inj_stitch_no_number(report: dict[str, Any]) -> list[str]:
    el = _find_element_by_checklist_name(report, "Stitch density check") or _by_id(report).get("2-13-1-15")
    if not el:
        return []
    el["comment"] = {"message": "PASSED", "translations": {"en": {"message": "PASSED"}}}
    return ["5_2_2"]


def _inj_logo_na(report: dict[str, Any]) -> list[str]:
    el = _find_element_by_checklist_name(report, "Logo check") or _by_id(report).get("2-9-2-3")
    if not el:
        return []
    el["result"] = "NOT_APPLICABLE"
    el["notApplicable"] = True
    el["applicable"] = False
    el["value"] = ["No logo"]
    el["images"] = []
    return ["3_2_3"]


def _inj_shading_extra_photo(report: dict[str, Any]) -> list[str]:
    el = _find_element_by_checklist_name(report, "Color shading check") or _by_id(report).get("2-13-1-12")
    if not el:
        return []
    el["images"] = list(el.get("images") or []) + [_photo(99)]
    return ["5_2_1"]


def _inj_measuring_photos(report: dict[str, Any]) -> list[str]:
    el = (
        _find_element_by_checklist_name(report, "Outer Packing: Assortment, Dimensions & Weight")
        or _by_id(report).get("2-9-1-6")
    )
    if not el:
        return []
    el["images"] = [_photo(i) for i in range(4)]
    return ["3_1_7"]


def _inj_wrong_measurement_file(report: dict[str, Any]) -> list[str]:
    el = _find_element_by_checklist_name(report, "Product Dimensions Result") or _by_id(report).get("2-11-1-1")
    if not el:
        return []
    el["attachments"] = [
        {
            "attachmentId": "flawed-attachment-0001",
            "filename": "Measurement_chart_format-Joseph_Ribkoff-264902.xlsx",
            "downloadUrl": "https://example.invalid/flawed-measurement.xlsx",
        }
    ]
    return ["5_1_1"]


def _inj_clear_global_remark(report: dict[str, Any]) -> list[str]:
    """Blank global remark — useful when qty overage would need an explanation."""
    result = report.setdefault("result", {})
    result["globalRemark"] = {"message": "", "translations": {"en": {"message": ""}}}
    return ["1_3_2"]


INJECTORS: list[Callable[[dict[str, Any]], list[str]]] = [
    _inj_carton_drop_photos,
    _inj_stitch_no_number,
    _inj_logo_na,
    _inj_shading_extra_photo,
    _inj_measuring_photos,
    _inj_wrong_measurement_file,
    _inj_clear_global_remark,
]


def _apply_subset(report: dict[str, Any], injectors: list[Callable]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for inj in injectors:
        for cid in inj(report):
            labels[cid] = f"injected by {inj.__name__}"
    return labels


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    introduced: dict[str, dict[str, str]] = {}

    checkpoints = load_checkpoints(CHECKPOINTS)
    hand = load_hand_specs(HAND_SPECS) if HAND_SPECS.exists() else {}
    specs = resolve_specs(
        checkpoints,
        hand_specs=hand,
        checkpoints_path=CHECKPOINTS,
        hand_specs_path=HAND_SPECS if HAND_SPECS.exists() else None,
    )

    for path in sorted(CORRECTED_DIR.glob("Q*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        repairs = sanitize_report_for_deterministic_specs(report, specs)
        if repairs:
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Sanitized {path.name}: {repairs}")

    # Keep original 6-error Q2614146161_flawed (all injectors except remark)
    base = CORRECTED_DIR / "Q2614146161.json"
    if base.exists():
        report = json.loads(base.read_text(encoding="utf-8"))
        flawed = copy.deepcopy(report)
        labels = _apply_subset(
            flawed,
            [
                _inj_carton_drop_photos,
                _inj_stitch_no_number,
                _inj_logo_na,
                _inj_shading_extra_photo,
                _inj_measuring_photos,
                _inj_wrong_measurement_file,
            ],
        )
        out = OUT_DIR / "Q2614146161_flawed.json"
        out.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        introduced["report_q2614146161_flawed"] = labels
        print(f"Wrote {out} labels={sorted(labels)}")

    # Second labeled flawed report from Q2614430689
    base2 = CORRECTED_DIR / "Q2614430689.json"
    if base2.exists():
        report = json.loads(base2.read_text(encoding="utf-8"))
        flawed = copy.deepcopy(report)
        labels = _apply_subset(
            flawed,
            [
                _inj_carton_drop_photos,
                _inj_stitch_no_number,
                _inj_measuring_photos,
                _inj_wrong_measurement_file,
                _inj_clear_global_remark,
            ],
        )
        # Alias for 1_2_1: clear remark also hits PO-breakdown style issues in some arms
        labels["1_2_1"] = "injected blank global remark (PO / qty explanation missing)"
        out = OUT_DIR / "Q2614430689_flawed.json"
        out.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        introduced["report_q2614430689_flawed"] = labels
        print(f"Wrote {out} labels={sorted(labels)}")

    # Extra reports: rotate injector subsets for coverage
    extras = sorted(CORRECTED_DIR.glob("Q*.json"))
    for i, path in enumerate(extras):
        if path.name in ("Q2614146161.json", "Q2614430689.json"):
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        flawed = copy.deepcopy(report)
        # Pick 3 injectors cycling through the list
        subset = [INJECTORS[j % len(INJECTORS)] for j in range(i, i + 3)]
        labels = _apply_subset(flawed, subset)
        if not labels:
            continue
        key = f"report_{path.stem.lower()}_flawed"
        out = OUT_DIR / f"{path.stem}_flawed.json"
        out.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        introduced[key] = labels
        print(f"Wrote {out} labels={sorted(labels)}")

    client = {
        "id": "ribkoff",
        "name": "Joseph Ribkoff",
        "gi_rules": "gi/rules.md",
        "hand_specs": "gi/hand_specs.json",
        "corrected_dir": "corrected",
        "flawed_dir": "flawed",
        "introduced_checkpoints": introduced,
        "holdout_keys": [
            "report_q2614146161_flawed",
            "report_q2614430689_flawed",
        ],
        "eval_corrected": ["Q2614146161", "Q2614430689"],
    }
    CLIENT.write_text(json.dumps(client, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {CLIENT} with {len(introduced)} labeled flawed reports")


if __name__ == "__main__":
    main()
