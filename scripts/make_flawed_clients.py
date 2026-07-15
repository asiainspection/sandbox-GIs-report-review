#!/usr/bin/env python3
"""Inject GI-detectable mistakes into corrected reports -> flawed/ (test dataset).

Each mutation is a *deviation from the correct report* that a GI rule flags:
  - result_flip:  PASS a checkpoint whose comment/GI says it should FAIL / be N/A
  - packed_pct:   quantity result stays PASS while packed % drops below GI threshold
  - forbidden:    insert a term the GI bans (e.g. "sample" instead of "GSS")
  - drop_detail:  remove info the GI requires in a remark (e.g. adhesive tape type)
  - set_images:   reduce photo count below what the GI requires (0 = missing)

Mutations are located by stable element id within each specific fixture and are
recorded (id + name + field + old -> new + GI rationale + report-team claim) in
flawed/injection_manifest.json so the flawed set stays a clean, labelled dataset.

Usage:  .venv/bin/python scripts/make_flawed_clients.py
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

CLIENTS_DIR = ROOT / "data/clients"

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
        if el.get("elements"):
            found.extend(_walk(el["elements"]))
        content = (el.get("content") or {}).get("elements")
        if content:
            found.extend(_walk(content))
        value = el.get("value")
        if isinstance(value, dict):
            for row in value.get("rows") or []:
                for col in row.get("columns") or []:
                    found.append(col)
    return found


def _by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for step in (report.get("result") or {}).get("steps", []):
        for action in step.get("actions", []):
            for key in ("testsChecklist", "defectsChecklist"):
                cl = action.get(key) or {}
                for el in _walk((cl.get("content") or {}).get("elements", [])):
                    if el.get("id"):
                        out[el["id"]] = el
    return out


def _name(el: dict[str, Any]) -> str:
    n = el.get("name") or el.get("title") or ""
    if isinstance(n, dict):
        n = n.get("message") or ""
    return str(n)


def _comment_text(el: dict[str, Any]) -> str:
    c = el.get("comment") or {}
    return str(c.get("message") or "") if isinstance(c, dict) else ""


def _set_comment(el: dict[str, Any], msg: str) -> None:
    el["comment"] = {
        "date": "2026-07-01T12:00:00.000Z",
        "timezone": "GMT",
        "message": msg,
        "translations": {"en": {"message": msg}},
    }


# --- mutators: each returns (field, old, new) for the manifest ----------------

def m_result(el: dict[str, Any], new: str) -> tuple[str, Any, Any]:
    old = el.get("result")
    el["result"] = new
    if new == "PASS":
        el["notApplicable"] = False
        el["applicable"] = True
    elif new == "NOT_APPLICABLE":
        el["notApplicable"] = True
        el["applicable"] = False
    return ("result", old, new)


def m_comment(el: dict[str, Any], new: str) -> tuple[str, Any, Any]:
    old = _comment_text(el)
    _set_comment(el, new)
    return ("comment", old, new)


def m_images(el: dict[str, Any], keep: int) -> tuple[str, Any, Any]:
    imgs = list(el.get("images") or [])
    old = len(imgs)
    el["images"] = imgs[:keep] if keep <= len(imgs) else imgs + [_photo(i) for i in range(keep - len(imgs))]
    return ("photo_count", old, keep)


MUTATORS = {"result": m_result, "comment": m_comment, "images": m_images}


# --- per-report injection plans (grounded in fetched fixtures) ----------------
# Each item: (element_id, mutator_key, arg, gi_rationale, report_team_claim)

PLANS: dict[str, dict[str, list[tuple]]] = {
    "cemaco": {
        "Q2601959645": [
            ("2-6-1-1", "comment", "Actual found 145 pcs (72.50%) were finished and packed",
             "Quantity result must FAIL when packed % is below the client threshold; PASS with low packed % is inconsistent.",
             "quantity section is passed but not aligned with the requirements (packed % too low)."),
            ("2-7-1-9", "images", 0,
             "Carton drop test result requires drop photos as evidence.",
             "inspector needs to attach defect/evidence photos."),
        ],
        "Q2605650175": [
            ("2-6-1-1", "comment", "Actual found 6135 pcs (72.00%) were finished and packed",
             "Quantity result must FAIL when packed % is below the client threshold.",
             "order and packed quantity inconsistent; packed % too low but passed."),
            ("2-7-3-5", "images", 0,
             "Barcode check requires photo evidence of the scanned barcode.",
             "name/attach pictures by SKU for barcode as required in GI."),
        ],
        "Q2610766318": [
            ("2-9-1-2", "result", "PASS",
             "Result must reflect findings: comment states dimensions/weight do not match spec, so result cannot be PASS.",
             "findings for dimension and weight do not match client specs."),
            ("2-9-1-1", "images", 0,
             "Product dimension result requires measurement photos for the measured pieces.",
             "for dimensions there should be photos per measured pc."),
        ],
    },
    "new_era": {
        "Q2616262288": [
            ("2-6-1-1", "comment", "The available qty 15530 pcs (67.32%) against booking were finished and packed",
             "New Era GI: quantity section must FAIL when packed is 60-80%; PASS at 67.32% is a violation.",
             "as per GI packed quantity should be >=80%, 67.32% packed but report passed."),
            ("2-12-1-2", "result", "PASS",
             "New Era GI: Fabric Weight Test must be N/A for this scope; marking PASS is wrong.",
             "why is the Fabric weight test Pass instead of N/A as per GI."),
        ],
        "Q2616171227": [
            ("2-13-1-2", "result", "PASS",
             "New Era GI: Fabric Weight Test must be N/A for this scope; marking PASS is wrong.",
             "Fabric weight test should be N/A as per GI."),
            ("2-8-1-4", "images", 0,
             "New Era GI: selected carton photos are mandatory.",
             "please provide selected carton as per GI."),
        ],
        "Q2616292623": [
            ("2-6-1-1", "comment", "As per booking quantity 21334 pcs, factory packed 14352 pcs (67.28%)",
             "New Era GI: quantity section must FAIL when packed is 60-80%.",
             "packed between 60-80% must fail per GI."),
            ("2-11-2-9", "result", "PASS",
             "New Era GI: Fabric weight test must be N/A for this scope; marking PASS is wrong.",
             "Fabric weight test Pass instead of N/A."),
        ],
    },
    "dfi": {
        "Q2614313993": [
            ("2-9-1-2", "comment", "Sample checked OK, sample matched the approval",
             "DFI GI: use only the term 'GSS' in report and pictures; 'sample' is banned.",
             "GI: use only the term GSS in the report, but 'sample' found."),
            ("2-12-1-3", "images", 0,
             "DFI GI: outer carton dimension and weight images are required.",
             "missing carton weight and dimension images."),
        ],
        "Q2615301660": [
            ("2-9-1-2", "comment", "Sample re-sealed and checked OK",
             "DFI GI: use only the term 'GSS'; 'sample' is banned.",
             "GI: use only the term GSS in the report and pictures."),
            ("2-8-1-6", "comment", "Checked OK",
             "DFI GI: adhesive test remark must state the type of tape used.",
             "add type of tape used during adhesive tape test."),
        ],
        "Q2616195180": [
            ("2-9-1-2", "comment", "Sample checked OK",
             "DFI GI: use only the term 'GSS'; 'sample' is banned.",
             "GI: use only the term GSS in the report and pictures."),
            ("2-12-1-3", "images", 0,
             "DFI GI: outer carton dimension and weight images are required.",
             "missing carton weight and dimension images / barcode info."),
        ],
    },
    "tpw": {
        "Q2611142925": [
            ("2-7-1-2", "result", "PASS",
             "Carton drop (ISTA) result must reflect the finding: comment describes damage, so PASS is inconsistent.",
             "carton drop test result must match the ISTA finding."),
            ("2-7-1-4", "images", 2,
             "TPW ISTA 3A requires a full drop set; too few drop photos fails the layout requirement.",
             "ISTA 3A mandates at least 17 drops; only a few photos attached."),
        ],
        "Q2614472847_2": [
            ("2-6-1-8", "result", "PASS",
             "Result must reflect findings: comment says PO number missing, so Match packing info cannot be PASS.",
             "PO number missing on carton but packing marked pass."),
            ("2-6-1-6", "result", "PASS",
             "Result must reflect findings: comment reports missing barcode sticker, so PASS is inconsistent.",
             "missing barcode sticker on cartons but marked pass."),
        ],
        "Q2614472847_4": [
            ("2-6-1-8", "result", "PASS",
             "Result must reflect findings: comment says wrong PO number, so Match packing info cannot be PASS.",
             "wrong PO number on carton but packing marked pass."),
            ("2-6-1-6", "result", "PASS",
             "Result must reflect findings: comment reports packing not conform to spec.",
             "packing way not conform to spec but marked pass."),
        ],
    },
}


def main() -> None:
    grand_total = 0
    for client, reports in PLANS.items():
        corrected_dir = CLIENTS_DIR / client / "corrected"
        flawed_dir = CLIENTS_DIR / client / "flawed"
        flawed_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {}
        introduced: dict[str, dict[str, str]] = {}

        for stem, items in reports.items():
            src = corrected_dir / f"{stem}.json"
            if not src.exists():
                print(f"SKIP  {client}/{stem}: corrected report not found")
                continue
            report = json.loads(src.read_text(encoding="utf-8"))
            flawed = copy.deepcopy(report)
            by_id = _by_id(flawed)
            entries: list[dict[str, Any]] = []
            label_key = f"report_{stem.lower()}_flawed"
            labels: dict[str, str] = {}

            for eid, mkey, arg, gi, claim in items:
                el = by_id.get(eid)
                if el is None:
                    print(f"WARN  {client}/{stem}: element id {eid} not found; skipped")
                    continue
                field, old, new = MUTATORS[mkey](el, arg)
                entries.append({
                    "element_id": eid,
                    "checkpoint": _name(el),
                    "field": field,
                    "old": old,
                    "new": new,
                    "gi_rationale": gi,
                    "report_team_claim": claim,
                })
                labels[eid] = f"{field}: {gi}"

            out = flawed_dir / f"{stem}_flawed.json"
            out.write_text(json.dumps(flawed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            manifest[f"{stem}_flawed"] = {"source": f"corrected/{stem}.json", "injected": entries}
            introduced[label_key] = labels
            grand_total += len(entries)
            print(f"OK    {client}/{stem}_flawed.json  injected={len(entries)}")

        (flawed_dir / "injection_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        # Merge into client.json (keep any prior synthetic labels).
        cj_path = CLIENTS_DIR / client / "client.json"
        cj = json.loads(cj_path.read_text(encoding="utf-8"))
        cj.setdefault("introduced_checkpoints", {}).update(introduced)
        cj["flawed_manifest"] = "flawed/injection_manifest.json"
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nDONE: injected {grand_total} mistakes across clients.")


if __name__ == "__main__":
    main()
