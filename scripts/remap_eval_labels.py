#!/usr/bin/env python3
"""Remap client.json introduced_checkpoints from legacy IDs → current checkpoint slugs.

Uses injection_manifest.json when present. Only keeps checkpoint IDs that exist
in the compiled checkspecs. Unevaluable injections are dropped (empty label set
→ eval_all skips that report for recall).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (client, checkpoint_name, field) → list of current checkpoint IDs
INJECTION_TO_CPS: dict[tuple[str, str, str], list[str]] = {
    # DFI
    ("dfi", "Green Seal Sample(GSS)", "comment"): ["2_2_2"],
    ("dfi", "Carton Check: Dimensions and Weight", "photo_count"): [],  # no authored ops check
    ("dfi", "Adhesive test", "comment"): ["5_4_2"],
    # Cemaco — injected flaws currently have no matching deterministic/ops checks
    ("cemaco", "Available Quantity Check: Finished&Packed&Unpacked", "comment"): [],
    ("cemaco", "Carton drop test", "photo_count"): [],
    ("cemaco", "Product Details - Barcode", "photo_count"): [],
    ("cemaco", "Product Weights Result", "result"): [],
    ("cemaco", "Product Dimensions Result", "photo_count"): [],
    # New Era
    ("new_era", "Available Quantity Check", "comment"): [],
    ("new_era", "Fabric Weight Test", "result"): ["6_1_2"],
    ("new_era", "Fabric weight test", "result"): ["6_1_2"],
    ("new_era", "Selected cartons", "photo_count"): [],
    # TPW
    ("tpw", "Step 3: Shock Rotational Edge Drop Test", "result"): [],
    # Injection 6→2 photos still satisfies any count_at_least(1); no authored min=17 check.
    ("tpw", "Step 5a: Shock Concentrated Impact Test", "photo_count"): [],
    ("tpw", "Match packing info", "result"): [],
    ("tpw", "Outer Packing & Shipping Marks: Front & Side", "result"): [],
}

HALLMARK_LEGACY: dict[str, list[str]] = {
    "9_2_6": ["rpt_10_10"],
    "4_3_2": ["wm_9_6"],
    "2_1_1": [],  # SR fail + overall PASS — not authored
    "2_2_1": [],  # FR fail + overall PASS — not authored
}

# Cemaco holdout uses synthetic caption findings with legacy IDs — keep if still in specs
CEMACO_HOLDOUT_KEEP = {
    "report_q2519476686_flawed": {
        "9_3_1": "outer packing captions only on 1 photo",
        "9_3_2": "measurement photos missing captions",
        "9_3_3": "measurement screenshot not spotlighted",
    }
}


def _spec_ids(cid: str) -> set[str]:
    data = json.loads((ROOT / f"data/pipeline/checkspecs/{cid}_checkspecs.json").read_text())
    return set((data.get("specs") or data).keys()) - {"meta"}


def _label_key(stem: str) -> str:
    return f"report_{stem.lower()}"


def remap_from_manifest(cid: str) -> dict[str, dict[str, str]]:
    man_path = ROOT / f"data/clients/{cid}/flawed/injection_manifest.json"
    manifest = json.loads(man_path.read_text())
    valid = _spec_ids(cid)
    out: dict[str, dict[str, str]] = {}
    for stem, data in manifest.items():
        mapped: dict[str, str] = {}
        for inj in data.get("injected") or []:
            key = (cid, str(inj.get("checkpoint") or ""), str(inj.get("field") or ""))
            targets = INJECTION_TO_CPS.get(key)
            if targets is None:
                print(f"  WARN unmapped injection {key}")
                targets = []
            note = str(inj.get("gi_rationale") or inj.get("report_team_claim") or key[1])
            for tid in targets:
                if tid in valid:
                    mapped[tid] = note
                else:
                    print(f"  WARN {cid}: {tid} not in checkspecs")
        out[_label_key(stem)] = mapped
        print(f"  {stem} -> {list(mapped) or '(no evaluable labels)'}")
    return out


def main() -> None:
    # DFI / cemaco / new_era / tpw from manifests
    for cid in ["dfi", "cemaco", "new_era", "tpw"]:
        print(f"\n==== {cid} ====")
        client_path = ROOT / f"data/clients/{cid}/client.json"
        client = json.loads(client_path.read_text())
        old = dict(client.get("introduced_checkpoints") or {})
        new = remap_from_manifest(cid)

        if cid == "dfi" and "dfi_flawed" in old:
            # Holdout synthetic — remap known carton_drop key if present
            hold = old["dfi_flawed"]
            remapped_hold = {}
            for k, v in hold.items():
                if k == "remarks.carton_drop_observation":
                    # no current check id authored for this; keep empty
                    print(f"  drop holdout label {k}")
                elif k in _spec_ids(cid):
                    remapped_hold[k] = v
                else:
                    print(f"  drop unknown holdout {k}")
            new["dfi_flawed"] = remapped_hold

        if cid == "cemaco":
            for k, v in CEMACO_HOLDOUT_KEEP.items():
                valid = _spec_ids(cid)
                kept = {cid_: note for cid_, note in v.items() if cid_ in valid}
                if kept:
                    new[k] = kept
                    print(f"  holdout {k} -> {list(kept)}")
                else:
                    new[k] = {}
                    print(f"  holdout {k} -> (none of {list(v)} in specs)")

        client["introduced_checkpoints"] = new
        client_path.write_text(json.dumps(client, indent=2) + "\n")
        print(f"  wrote {client_path}")

    # Hallmark
    print("\n==== hallmark ====")
    client_path = ROOT / "data/clients/hallmark/client.json"
    client = json.loads(client_path.read_text())
    valid = _spec_ids("hallmark")
    new = {}
    for key, labels in (client.get("introduced_checkpoints") or {}).items():
        mapped = {}
        for lid, note in labels.items():
            for tid in HALLMARK_LEGACY.get(lid, [lid]):
                if tid in valid:
                    mapped[tid] = note
                elif tid:
                    print(f"  WARN hallmark {tid} missing")
        new[key] = mapped
        print(f"  {key}: {list(labels)} -> {list(mapped)}")
    client["introduced_checkpoints"] = new
    client_path.write_text(json.dumps(client, indent=2) + "\n")
    print(f"  wrote {client_path}")

    # Ribkoff already uses current IDs — verify
    print("\n==== ribkoff ====")
    client = json.loads((ROOT / "data/clients/ribkoff/client.json").read_text())
    valid = _spec_ids("ribkoff")
    for key, labels in (client.get("introduced_checkpoints") or {}).items():
        missing = [x for x in labels if x not in valid]
        print(f"  {key}: {len(labels)} labels, missing={missing}")


if __name__ == "__main__":
    main()
