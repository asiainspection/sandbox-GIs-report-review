#!/usr/bin/env python3
"""Create synthetic DFI/Hallmark report fixtures from Ribkoff corrected JSON."""

from __future__ import annotations

import copy
import json
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"

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
    return {**_PHOTO_STUB, "imageId": f"syn-{uuid.uuid4().hex[:12]}-{n}"}


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


def _by_id(report: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for step in (report.get("result") or {}).get("steps", []):
        for action in step.get("actions", []):
            checklist = action.get("testsChecklist") or {}
            for el in _walk((checklist.get("content") or {}).get("elements", [])):
                eid = el.get("id")
                if eid:
                    out[eid] = el
    return out


def make_hallmark_synthetic() -> None:
    out_dir = ROOT / "data/clients/hallmark/synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = copy.deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    by_id = _by_id(report)

    # Carton drop element → Hallmark defect photos section (deterministic rule 9_2_6)
    el = by_id.get("2-9-1-9")
    if el:
        el["translations"] = {"en": {"name": "Defect photos (Workmanship section)"}}
        el["result"] = "PASS"
        el["images"] = [_photo(0)]

    correct_path = out_dir / "hallmark_correct.json"
    flawed = copy.deepcopy(report)
    flawed_el = _by_id(flawed).get("2-9-1-9")
    if flawed_el:
        flawed_el["images"] = [_photo(i) for i in range(3)]

    flawed_path = out_dir / "hallmark_flawed.json"
    correct_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    flawed_path.write_text(json.dumps(flawed, indent=2), encoding="utf-8")

    client_path = ROOT / "data/clients/hallmark/client.json"
    # Do not clobber PDF-backed fixtures / labels written by make_hallmark_pdf_fixtures.py
    if (ROOT / "data/clients/hallmark/corrected").exists() and any(
        (ROOT / "data/clients/hallmark/corrected").glob("*.json")
    ):
        print(f"Wrote {correct_path} and {flawed_path} (kept existing {client_path.name})")
        return

    client = {
        "id": "hallmark",
        "name": "Hallmark synthetic",
        "introduced_checkpoints": {
            "hallmark_flawed": {
                "9_2_6": "Injected extra defect photos (should flag count_at_most)"
            }
        },
    }
    client_path.write_text(json.dumps(client, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {correct_path} and {flawed_path}")


def make_dfi_synthetic() -> None:
    corrected_dir = ROOT / "data/clients/dfi/corrected"
    flawed_dir = ROOT / "data/clients/dfi/flawed"
    corrected_dir.mkdir(parents=True, exist_ok=True)
    flawed_dir.mkdir(parents=True, exist_ok=True)
    report = copy.deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    by_id = _by_id(report)

    el = by_id.get("2-9-1-9")
    if el:
        el["translations"] = {"en": {"name": "Carton Drop Test"}}
        el["result"] = "FAIL"
        el["comment"] = {"message": "Failed", "translations": {"en": {"message": "Failed"}}}

    # Corrected: findings present AND observation remark present
    result_obj = report.setdefault("result", {})
    result_obj["globalRemark"] = {
        "message": "Carton drop: minor crush observed on corner, accepted.",
        "translations": {
            "en": {"message": "Carton drop: minor crush observed on corner, accepted."}
        },
    }

    flawed = copy.deepcopy(report)
    flawed_result = flawed.setdefault("result", {})
    flawed_result["globalRemark"] = {"message": "", "translations": {"en": {"message": ""}}}

    flawed_path = flawed_dir / "dfi_flawed.json"
    correct_path = corrected_dir / "dfi_correct.json"
    correct_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    flawed_path.write_text(json.dumps(flawed, indent=2), encoding="utf-8")

    client_path = ROOT / "data/clients/dfi/client.json"
    if not client_path.exists():
        client = {
            "id": "dfi",
            "name": "DFI",
            "gi_rules": "gi/rules.json",
            "source_gi": "gi/source_gi.txt",
            "corrected_dir": "corrected",
            "flawed_dir": "flawed",
            "introduced_checkpoints": {
                "dfi_flawed": {
                    "remarks.carton_drop_observation": "Carton drop FAIL without required observation remark"
                }
            },
            "holdout_keys": ["dfi_flawed"],
        }
        client_path.write_text(json.dumps(client, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {correct_path} and {flawed_path}")


def main() -> None:
    make_hallmark_synthetic()
    make_dfi_synthetic()


if __name__ == "__main__":
    main()
