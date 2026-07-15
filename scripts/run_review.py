#!/usr/bin/env python3
"""Production GI review: PolicyGuard (parse → operators → atoms → cascade → symbolic eval)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from review import run_production_review  # noqa: E402
from gi_review import format_cost_summary  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PolicyGuard GI review (no per-checkpoint LLM judge)")
    parser.add_argument(
        "--report-json",
        type=Path,
        default=ROOT / "data/clients/ribkoff/corrected/Q2614146161.json",
    )
    parser.add_argument(
        "--checkpoints",
        type=Path,
        default=ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json",
    )
    parser.add_argument(
        "--specs",
        type=Path,
        default=ROOT / "data/clients/ribkoff/gi/hand_specs.json",
    )
    parser.add_argument("--judge-model", type=str, default=None)
    parser.add_argument("--extract-model", type=str, default=None)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "data/pipeline/eval/production_review.json")
    args = parser.parse_args()

    started = time.perf_counter()
    run = run_production_review(
        args.report_json,
        args.checkpoints,
        specs_path=args.specs,
        project_root=ROOT,
        max_workers=args.max_workers,
        judge_model=args.judge_model,
        extract_model=args.extract_model,
    )
    summary = format_cost_summary(run)
    summary["elapsed_seconds"] = round(time.perf_counter() - started, 1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Arm: {summary['arm']}")
    print(f"Extract: {summary.get('extract_model') or '—'} | Judge: {summary['judge_model']}")
    print(
        f"Checkpoints: {summary['checkpoints_run']} | "
        f"Operators: {summary.get('operator_resolved_count', 0)} | "
        f"Precheck: {summary['precheck_resolved_count']} | "
        f"LLM: {summary['llm_checkpoints_count']}"
    )
    print(
        f"Blocking flags: {summary['blocking_flags_count']} | "
        f"Total flags: {summary['total_flags_count']} | "
        f"Unable: {summary['unable_to_check_count']}"
    )
    cost = summary["cost_usd"]["total"]["total_cost_usd"]
    print(f"Cost: ${cost:.4f} | Elapsed: {summary['elapsed_seconds']}s")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
