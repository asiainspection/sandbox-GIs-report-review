#!/usr/bin/env python3
"""Dump per-client checklist item names from corrected report fixtures.

Output: data/library/checklist_names/<client>.txt
Give the client file to Claude as HINTS when authoring that client's GI
(not a closed allowlist — runtime still fuzzy-matches).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic_report import parse_semantic_report  # noqa: E402


def dump_client(client_dir: Path, out_dir: Path) -> int:
    corrected = client_dir / "corrected"
    if not corrected.is_dir():
        return 0
    names: Counter[str] = Counter()
    for path in sorted(corrected.glob("*.json")):
        if "injection" in path.name:
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        semantic = parse_semantic_report(report)
        for item in semantic.checklist_items:
            nm = (item.item_name or "").strip()
            if nm:
                names[nm] += 1
    if not names:
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{client_dir.name}.txt"
    lines = [
        f"# Checklist names for client={client_dir.name}",
        f"# Generated from {sum(names.values())} item occurrences across corrected reports.",
        "# Hints for Claude authoring — pick a real name, then use checklist.<name>.<suffix>.",
        "# Runtime fuzzy-matches casing/whitespace; unmatched → unable (not a flag).",
        "",
    ]
    for name, count in sorted(names.items(), key=lambda x: x[0].lower()):
        lines.append(f"{name}  # seen={count}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(names)} names)")
    return len(names)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clients-root",
        type=Path,
        default=ROOT / "data" / "clients",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "library" / "checklist_names",
    )
    parser.add_argument("--client", type=str, default=None, help="Single client id")
    args = parser.parse_args()

    clients = (
        [args.clients_root / args.client]
        if args.client
        else sorted(p for p in args.clients_root.iterdir() if p.is_dir())
    )
    total = 0
    for client_dir in clients:
        if not client_dir.is_dir():
            continue
        total += dump_client(client_dir, args.out)
    print(f"Done. {total} distinct name entries across clients.")


if __name__ == "__main__":
    main()
