#!/usr/bin/env python3
"""Create flawed report JSON by mutating a corrected report (evaluation fixtures).

Usage:
    .venv/bin/python scripts/make_flawed_json.py
"""

from __future__ import annotations

import copy
import json
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CORRECTED = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"
OUT_DIR = ROOT / "data/clients/ribkoff/flawed"

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


def _mutate_q2614146161(report: dict[str, Any]) -> dict[str, Any]:
    """Inject the six mistakes from report_q2614146161_flawed.md changelog."""
    by_id = _by_id(report)

    # CHANGE 1: Carton drop test photos when PASS
    drop = by_id["2-9-1-9"]
    drop["images"] = [_photo(i) for i in range(4)]

    # CHANGE 2: Stitch density — no numeric count in comment
    stitch = by_id["2-13-1-15"]
    stitch["comment"] = {
        "date": "2026-07-01T07:22:44.880487Z",
        "timezone": "GMT",
        "message": "PASSED",
        "translations": {},
    }

    # CHANGE 3: Product Logo wrongly marked N/A
    logo = by_id["2-9-2-3"]
    logo["result"] = "NOT_APPLICABLE"
    logo["notApplicable"] = True
    logo["applicable"] = False
    logo["images"] = []
    logo["value"] = ["No logo"]
    logo["comment"] = {
        "date": "2026-07-01T11:53:14.568Z",
        "timezone": "GMT",
        "message": "No logo",
        "translations": {},
    }

    # CHANGE 4: Color shading — multiple photos per test
    shading = by_id["2-13-1-12"]
    shading["images"] = list(shading.get("images") or []) + [_photo(99)]

    # CHANGE 5: Measuring box photos on Outer Packing
    outer = by_id["2-9-1-6"]
    outer["images"] = [_photo(i) for i in range(5)]

    # CHANGE 6: Wrong measurement attachment filename
    dims = by_id["2-11-1-1"]
    dims["attachments"] = [
        {
            "attachmentId": "flawed-attachment-0001",
            "filename": "Measurement_chart_format-Joseph_Ribkoff-264902.xlsx",
            "downloadUrl": "https://example.invalid/flawed-measurement.xlsx",
        }
    ]

    return report


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = json.loads(CORRECTED.read_text(encoding="utf-8"))
    flawed = _mutate_q2614146161(copy.deepcopy(report))
    out_path = OUT_DIR / "Q2614146161_flawed.json"
    out_path.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
