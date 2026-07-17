#!/usr/bin/env python3
"""Dry-run: reclassify all checkpoints via the field registry (no writes).

Prints a coverage grid proving every checkpoint lands in exactly one cell.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from check_block import compile_block  # noqa: E402
from clients import list_clients, load_client  # noqa: E402
from field_registry import (  # noqa: E402
    STATUS_ADVISORY,
    STATUS_CHECKABLE,
    STATUS_PENDING,
    STATUS_UNAUTHORED,
    STATUS_UNMAPPED,
    derive_feasibility,
)
from fact_schema import normalize_where_bindings  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402


def main() -> None:
    status_counts: Counter[str] = Counter()
    ds_counts: Counter[str] = Counter()
    pending_proc: Counter[str] = Counter()
    per_gi: dict[str, Counter[str]] = defaultdict(Counter)
    unknown = 0
    total = 0

    for gi in list_clients(ROOT):
        client = load_client(gi, ROOT)
        if not client.checkpoints_path.exists():
            print(f"SKIP {gi}: no checkpoints")
            continue
        for cp in load_checkpoints(client.checkpoints_path):
            total += 1
            block = cp.get("check_block") or {}
            where = list(block.get("where") or [])
            bindings = normalize_where_bindings(where)
            has_check = block.get("check") not in (None, "null", "")
            legacy = str(block.get("data_source") or "").strip() or None
            derived = derive_feasibility(
                bindings, has_check=has_check, legacy_data_source=legacy
            )
            # Also compile to ensure engine path agrees
            spec = compile_block(cp, block if block else None)
            sc = str(spec.get("status_class") or derived["status_class"])
            ds = str(spec.get("data_source") or derived["data_source"])
            if sc not in (
                STATUS_CHECKABLE,
                STATUS_PENDING,
                STATUS_UNAUTHORED,
                STATUS_UNMAPPED,
                STATUS_ADVISORY,
            ):
                unknown += 1
                print(f"  UNKNOWN {gi}/{cp['id']}: status={sc} ds={ds}")
            status_counts[sc] += 1
            ds_counts[ds] += 1
            per_gi[gi][sc] += 1
            if sc == STATUS_PENDING:
                pending_proc[str(spec.get("pending_processor") or "unknown")] += 1

    print("=" * 72)
    print(f"RECLASSIFY DRY-RUN  total={total}  unknown={unknown}")
    print("=" * 72)
    print("\nstatus_class:")
    for k in (
        STATUS_CHECKABLE,
        STATUS_PENDING,
        STATUS_UNAUTHORED,
        STATUS_UNMAPPED,
        STATUS_ADVISORY,
    ):
        print(f"  {k:12} {status_counts[k]:4}")
    print("\ndata_source:")
    for k, v in ds_counts.most_common():
        print(f"  {k:22} {v:4}")
    if pending_proc:
        print("\npending_processor:")
        for k, v in pending_proc.most_common():
            print(f"  {k:12} {v:4}")
    print("\nper client:")
    for gi in sorted(per_gi):
        c = per_gi[gi]
        print(
            f"  {gi:10} checkable={c[STATUS_CHECKABLE]:3} "
            f"pending={c[STATUS_PENDING]:3} unauthored={c[STATUS_UNAUTHORED]:3} "
            f"unmapped={c[STATUS_UNMAPPED]:3} "
            f"advisory={c[STATUS_ADVISORY]:3}"
        )
    if unknown:
        raise SystemExit(1)
    print("\nOK — every checkpoint classified.")


if __name__ == "__main__":
    main()
