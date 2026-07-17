"""Compile GI checkpoints to cached obligation CheckSpecs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compiler import compile_gi  # noqa: E402
from clients import ensure_pipeline_dirs, load_client, list_clients  # noqa: E402


def _sample_report_for_stem(stem: str) -> Path | None:
    """Pick first corrected report for the client matching checkpoints stem."""
    try:
        client = load_client(stem, ROOT)
    except Exception:
        return None
    reports = client.corrected_reports()
    return reports[0] if reports else None


def main() -> None:
    ensure_pipeline_dirs(ROOT)
    parser = argparse.ArgumentParser(description="Compile GI checkpoints to obligation CheckSpecs.")
    parser.add_argument("checkpoints", type=Path, nargs="?", help="Path to checkpoints JSON")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (default: data/pipeline/checkspecs/<stem>_checkspecs.json)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Compile every client under data/clients/",
    )
    parser.add_argument(
        "--sample-report",
        type=Path,
        default=None,
        help="Corrected report JSON for resolvability gate (default: first corrected)",
    )
    args = parser.parse_args()

    if args.all:
        for gid in list_clients(ROOT):
            client = load_client(gid, ROOT)
            if not client.checkpoints_path.exists():
                print(f"SKIP {gid}: no checkpoints")
                continue
            sample = client.corrected_reports()
            sample_path = sample[0] if sample else None
            specs = compile_gi(
                client.checkpoints_path,
                client.checkspecs_path,
                sample_report_path=sample_path,
            )
            print(f"{gid}: Wrote {len(specs)} specs -> {client.checkspecs_path}")
        return

    if not args.checkpoints:
        parser.error("checkpoints path required (or use --all)")

    stem = args.checkpoints.stem.replace("_checkpoints", "")
    if stem.endswith("_v2"):
        stem = stem[:-3]
    output = args.output or ROOT / "data" / "pipeline" / "checkspecs" / f"{stem}_checkspecs.json"
    sample = args.sample_report or _sample_report_for_stem(stem)
    specs = compile_gi(args.checkpoints, output, sample_report_path=sample)
    print(f"Wrote {len(specs)} specs -> {output}")


if __name__ == "__main__":
    main()
