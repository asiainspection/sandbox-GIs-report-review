#!/usr/bin/env python3
"""Build Cemaco correct/flawed fixtures from fetched QIMAone JSON + review labels.

Corrected baseline: live JSON (GUID AA836CB2…) with the one missing measurement
caption filled so gold is caption-complete. Flawed injectors replay the three
Q2519476686 review findings (outer packing captions, measurement captions, spotlight).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SRC = ROOT / "data/clients/cemaco/corrected/Q2519476686.json"
OUT_CORRECTED = ROOT / "data/clients/cemaco/corrected/Q2519476686.json"
OUT_FLAWED = ROOT / "data/clients/cemaco/flawed/Q2519476686_flawed.json"
CLIENT = ROOT / "data/clients/cemaco/client.json"

LABELS = ["9_3_1", "9_3_2", "9_3_3"]


def _el_name(el: dict[str, Any]) -> str:
    name = el.get("name") or ""
    if isinstance(name, dict):
        name = name.get("message") or ""
    tr = ((el.get("translations") or {}).get("en") or {}).get("name")
    return str(tr or name or "")


def _walk(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
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


def _checklist_elements(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for step in (report.get("result") or {}).get("steps", []):
        for action in step.get("actions", []):
            checklist = action.get("testsChecklist") or {}
            out.extend(_walk((checklist.get("content") or {}).get("elements", [])))
    return out


def _cap_text(image: dict[str, Any]) -> str:
    cap = image.get("caption")
    if isinstance(cap, dict):
        return str(cap.get("message") or cap.get("text") or "").strip()
    return str(cap or "").strip()


def _set_caption(image: dict[str, Any], text: str) -> None:
    image["caption"] = text
    tr = image.setdefault("translations", {}).setdefault("en", {})
    tr["caption"] = text


def _find(report: dict[str, Any], needle: str) -> dict[str, Any] | None:
    for el in _checklist_elements(report):
        if needle.lower() in _el_name(el).lower():
            return el
    return None


def sanitize_corrected(report: dict[str, Any]) -> dict[str, Any]:
    """Fill any blank measurement captions so corrected is a true gold for caption rules."""
    out = copy.deepcopy(report)
    dims = _find(out, "Product Dimensions Result")
    if dims and dims.get("images"):
        for im in dims["images"]:
            if not _cap_text(im):
                _set_caption(im, "1180753 &1180763 size check")
    return out


def inject_flaws(report: dict[str, Any]) -> dict[str, Any]:
    """Replay Q2519476686 NEED_MORE_INFORMATION findings."""
    out = copy.deepcopy(report)

    outer = _find(out, "Outer Packing & Shipping Marks: Front & Side")
    if outer and outer.get("images"):
        for i, im in enumerate(outer["images"]):
            if i == 0:
                if not _cap_text(im):
                    _set_caption(im, "1182656")
            else:
                _set_caption(im, "")

    dims = _find(out, "Product Dimensions Result")
    if dims and dims.get("images"):
        for im in dims["images"]:
            _set_caption(im, "")
            im["isSpotlight"] = False

    return out


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing source JSON: {SRC} (fetch GUID first)")

    raw = json.loads(SRC.read_text(encoding="utf-8"))
    corrected = sanitize_corrected(raw)
    flawed = inject_flaws(corrected)

    OUT_CORRECTED.parent.mkdir(parents=True, exist_ok=True)
    OUT_FLAWED.parent.mkdir(parents=True, exist_ok=True)
    OUT_CORRECTED.write_text(json.dumps(corrected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_FLAWED.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    client = {
        "id": "cemaco",
        "name": "Cemaco Nuevos Almacenes",
        "gi_rules": "gi/rules.md",
        "source_gi": "gi/source_gi.md",
        "corrected_dir": "corrected",
        "flawed_dir": "flawed",
        "qimaone_guid": "AA836CB221564BC29096240979771339",
        "inspection_id": raw.get("inspectionId"),
        "fixture_note": (
            "Corrected = live QIMAone JSON with measurement caption sanitized. "
            "Flawed injects the three Q2519476686 review findings (outer packing captions, "
            "measurement captions, measurement spotlight)."
        ),
        "introduced_checkpoints": {
            "report_q2519476686_flawed": {
                "9_3_1": "outer packing captions only on 1 photo",
                "9_3_2": "measurement photos missing captions",
                "9_3_3": "measurement screenshot not spotlighted",
            }
        },
        "holdout_keys": ["report_q2519476686_flawed"],
    }
    CLIENT.write_text(json.dumps(client, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_CORRECTED}")
    print(f"Wrote {OUT_FLAWED}")
    print(f"Wrote {CLIENT} labels={LABELS}")


if __name__ == "__main__":
    main()
