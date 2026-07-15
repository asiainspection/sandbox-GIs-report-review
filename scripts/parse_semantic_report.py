#!/usr/bin/env python3
"""Parse QIMAone report JSON → PDF-aligned semantic report JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic_report import dumps_semantic, load_report_json, parse_semantic_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse report JSON to semantic (PDF-aligned) facts")
    parser.add_argument("inputs", nargs="+", type=Path, help="Report JSON file(s)")
    parser.add_argument("-o", "--output-dir", type=Path, default=ROOT / "data/pipeline/semantic")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    if args.stdout and len(args.inputs) != 1:
        print("error: --stdout requires exactly one input", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for path in args.inputs:
        if not path.exists():
            print(f"error: not found: {path}", file=sys.stderr)
            return 1
        report = load_report_json(path)
        semantic = parse_semantic_report(report)
        text = dumps_semantic(report)
        if args.stdout:
            print(text)
            continue
        out = args.output_dir / f"{path.stem}_semantic.json"
        out.write_text(text + "\n", encoding="utf-8")
        warnings = semantic.parse_warnings
        print(
            f"Wrote {out} | products={len(semantic.products)} "
            f"checklist_items={len(semantic.checklist_items)} "
            f"warnings={len(warnings)}"
        )
        for w in warnings:
            print(f"  warn: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
