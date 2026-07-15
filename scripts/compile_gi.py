#!/usr/bin/env python3
"""Compile GI checkpoints to cached obligation CheckSpecs.

Usage:
    .venv/bin/python scripts/compile_gi.py data/pipeline/checkpoints/ribkoff_checkpoints.json \
        --hand-specs data/clients/ribkoff/gi/hand_specs.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compiler import compile_gi  # noqa: E402
from clients import ensure_pipeline_dirs  # noqa: E402


def main() -> None:
    ensure_pipeline_dirs(ROOT)
    parser = argparse.ArgumentParser(description="Compile GI checkpoints to obligation CheckSpecs.")
    parser.add_argument("checkpoints", type=Path, help="Path to checkpoints JSON")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (default: data/pipeline/checkspecs/<stem>_checkspecs.json)",
    )
    parser.add_argument(
        "--hand-specs",
        type=Path,
        default=None,
        help="Optional hand operator specs JSON",
    )
    args = parser.parse_args()

    stem = args.checkpoints.stem.replace("_checkpoints", "")
    if stem.endswith("_v2"):
        stem = stem[:-3]
    output = args.output or ROOT / "data" / "pipeline" / "checkspecs" / f"{stem}_checkspecs.json"
    specs = compile_gi(args.checkpoints, output, hand_specs_path=args.hand_specs)
    print(f"Wrote {len(specs)} specs -> {output}")


if __name__ == "__main__":
    main()
