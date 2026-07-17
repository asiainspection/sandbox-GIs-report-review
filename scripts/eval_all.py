#!/usr/bin/env python3
"""Production PolicyGuard eval — all clients, all reports, precision/recall + plot.

Always runs the real production pipeline (run_production_review). No offline mode.

Metrics (checkable specs only — pending/unauthored/advisory excluded):
  - Precision / recall on flawed reports (vs injected labels ∩ checkable)
  - Accuracy on corrected reports (1 − blocking FPs / opportunities)

Usage:
    .venv/bin/python scripts/eval_all.py
    .venv/bin/python scripts/eval_all.py --gis ribkoff dfi
    .venv/bin/python scripts/eval_all.py --no-vision
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import resolve_specs  # noqa: E402
from clients import checkspecs_cache_path, ensure_pipeline_dirs, list_clients, load_client  # noqa: E402
from gi_review import format_cost_summary, load_checkpoints  # noqa: E402
from review import run_production_review  # noqa: E402

DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _checkable_ids(specs: dict[str, dict[str, Any]]) -> set[str]:
    """Only specs the production engine can actually evaluate today."""
    out: set[str] = set()
    for cid, sp in specs.items():
        if str(sp.get("status_class") or "") == "checkable" and sp.get("then"):
            out.add(cid)
    return out


def _load_specs(checkpoints_path: Path) -> dict[str, dict[str, Any]]:
    checkpoints = load_checkpoints(checkpoints_path)
    cache = checkspecs_cache_path(checkpoints_path, ROOT)
    return resolve_specs(
        checkpoints,
        checkpoints_path=checkpoints_path,
        cache_path=cache if cache.exists() else None,
    )


def _flagged_checkable(summary: dict[str, Any], checkable: set[str]) -> set[str]:
    return {
        str(f["checkpoint_id"])
        for f in (summary.get("flags") or [])
        if str(f.get("checkpoint_id") or "") in checkable
    }


def _blocking_checkable(summary: dict[str, Any], checkable: set[str]) -> int:
    return sum(
        1
        for f in (summary.get("flags") or [])
        if str(f.get("checkpoint_id") or "") in checkable
        and str(f.get("severity") or "BLOCKING").upper() == "BLOCKING"
    )


def _run_report(
    report: Path,
    checkpoints: Path,
    *,
    enable_vision: bool,
    model: str,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    run = run_production_review(
        report,
        checkpoints,
        project_root=ROOT,
        enable_vision=enable_vision,
        extract_model=model,
        judge_model=model,
    )
    summary = format_cost_summary(run)
    summary["elapsed_seconds"] = round(time.perf_counter() - t0, 1)
    summary["report"] = report.name
    return summary


def _spec_coverage(specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "checkable": 0,
        "pending": 0,
        "unauthored": 0,
        "unmapped": 0,
        "advisory": 0,
    }
    for sp in specs.values():
        sc = str(sp.get("status_class") or "")
        if sc in counts:
            counts[sc] += 1
        else:
            counts["advisory"] += 1
    total = len(specs)
    return {**counts, "total": total, "coverage_pct": 100.0 * counts["checkable"] / max(total, 1)}


def _plot(results: dict[str, Any], plot_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skip plot (pip install matplotlib)")
        return

    per_client = results.get("per_client") or {}
    clients = sorted(per_client.keys())
    if not clients:
        return

    macro_p = [per_client[c]["macro_precision"] for c in clients]
    macro_r = [per_client[c]["macro_recall"] for c in clients]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        f"Production eval — checkable checks ({results.get('model', DEFAULT_MODEL)}, "
        f"{results.get('report_count', 0)} reports)",
        fontsize=12,
    )

    x = range(len(clients))
    width = 0.35
    ax = axes[0]
    ax.bar([i - width / 2 for i in x], macro_p, width, label="Precision", color="#2563eb")
    ax.bar([i + width / 2 for i in x], macro_r, width, label="Recall", color="#16a34a")
    ax.set_xticks(list(x))
    ax.set_xticklabels([c.upper() for c in clients], rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Per-client macro P / R (flawed reports)")
    ax.legend(loc="lower right")
    ax.axhline(1.0, color="#ccc", linewidth=0.8, linestyle="--")
    for i, (p, r) in enumerate(zip(macro_p, macro_r)):
        ax.text(i - width / 2, p + 0.02, f"{p:.2f}", ha="center", fontsize=8)
        ax.text(i + width / 2, r + 0.02, f"{r:.2f}", ha="center", fontsize=8)

    ax2 = axes[1]
    g = results.get("global") or {}
    labels = ["Precision\n(flawed)", "Recall\n(flawed)", "Accuracy\n(corrected)"]
    vals = [
        g.get("micro_precision_flawed", 0),
        g.get("micro_recall_flawed", 0),
        g.get("accuracy_corrected", 0),
    ]
    colors = ["#2563eb", "#16a34a", "#9333ea"]
    bars = ax2.bar(labels, vals, color=colors)
    ax2.set_ylim(0, 1.05)
    ax2.set_title("Global metrics (checkable checks)")
    for bar, val in zip(bars, vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.3f}", ha="center", fontsize=10)
    ax2.text(
        0.5,
        -0.22,
        f"Coverage: {g.get('checkable_specs', '?')}/{g.get('total_specs', '?')} checkable "
        f"({g.get('coverage_pct', 0):.1f}%) | corrected blocking FPs: {g.get('corrected_fps', 0)}",
        transform=ax2.transAxes,
        ha="center",
        fontsize=9,
    )

    plt.tight_layout()
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wrote plot {plot_path}")


def main() -> None:
    ensure_pipeline_dirs(ROOT)
    available = list_clients(ROOT)
    parser = argparse.ArgumentParser(description="Production PolicyGuard multi-client eval + P/R plot")
    parser.add_argument("--gis", nargs="+", default=available, choices=available or None)
    parser.add_argument("--no-vision", action="store_true")
    parser.add_argument("--model", default=os.environ.get("GI_EXTRACT_MODEL") or DEFAULT_MODEL)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/pipeline/eval/eval_all_results.json",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=ROOT / "data/pipeline/eval/eval_all_pr.png",
    )
    args = parser.parse_args()

    os.environ.setdefault("GI_PIPELINE_LOG", "0")
    os.environ["GI_EXTRACT_MODEL"] = args.model
    os.environ["JUDGE_MODEL"] = args.model
    if args.no_vision:
        os.environ["GI_VISION_ENABLED"] = "0"
    enable_vision = not args.no_vision

    print(f"Mode: production (run_production_review)")
    print(f"Model: {args.model}")
    print(f"Clients: {args.gis}")
    print(f"Vision: {'on' if enable_vision else 'off'}")

    per_client: dict[str, Any] = {}
    all_reports: list[dict[str, Any]] = []
    total_corrected_fps = 0
    total_corrected_reports = 0
    total_caught = 0
    total_expected = 0
    total_flags_flawed = 0
    total_specs = 0
    total_checkable = 0

    for gi in args.gis:
        client = load_client(gi, ROOT)
        cps = client.checkpoints_path
        if not cps.exists():
            print(f"SKIP {gi}: no checkpoints at {cps}")
            continue

        specs = _load_specs(cps)
        checkable = _checkable_ids(specs)
        cov = _spec_coverage(specs)
        total_specs += cov["total"]
        total_checkable += len(checkable)
        print(
            f"\n{'=' * 72}\n{gi.upper()} — checkable={len(checkable)}/{cov['total']} "
            f"({cov['coverage_pct']:.1f}%) pending={cov['pending']} "
            f"unauthored={cov['unauthored']} advisory={cov['advisory']}\n{'=' * 72}",
            flush=True,
        )

        corrected_fps = 0
        macro_p: list[float] = []
        macro_r: list[float] = []

        for report in client.corrected_reports():
            print(f"  [corrected] {report.stem} …", flush=True)
            summary = _run_report(report, cps, enable_vision=enable_vision, model=args.model)
            flags = _flagged_checkable(summary, checkable)
            blocking = _blocking_checkable(summary, checkable)
            corrected_fps += blocking
            all_reports.append(
                {
                    "gi": gi,
                    "kind": "corrected",
                    "report": report.stem,
                    "checkable_flags": sorted(flags),
                    "blocking_fps": blocking,
                    **summary,
                }
            )
            cost = ((summary.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
            print(
                f"    blocking FPs={blocking} total_flags={len(flags)} "
                f"${cost:.4f} {summary.get('elapsed_seconds', 0)}s flags={sorted(flags)}",
                flush=True,
            )

        n_corrected = len(client.corrected_reports())
        total_corrected_fps += corrected_fps
        total_corrected_reports += n_corrected

        for report, label_key in client.flawed_reports():
            expected = client.label_ids(label_key) & checkable
            if not expected:
                print(f"  [flawed] SKIP {report.stem}: no checkable labels for {label_key}", flush=True)
                continue
            print(f"  [flawed] {report.stem} …", flush=True)
            summary = _run_report(report, cps, enable_vision=enable_vision, model=args.model)
            flags = _flagged_checkable(summary, checkable)
            caught = flags & expected
            p = len(caught) / max(len(flags), 1)
            r = len(caught) / max(len(expected), 1)
            macro_p.append(p)
            macro_r.append(r)
            total_caught += len(caught)
            total_expected += len(expected)
            total_flags_flawed += len(flags)
            all_reports.append(
                {
                    "gi": gi,
                    "kind": "flawed",
                    "report": report.stem,
                    "label_key": label_key,
                    "expected_checkable": sorted(expected),
                    "caught": sorted(caught),
                    "missed": sorted(expected - flags),
                    "extra": sorted(flags - expected),
                    "precision": p,
                    "recall": r,
                    "checkable_flags": sorted(flags),
                    **summary,
                }
            )
            cost = ((summary.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
            print(
                f"    P={p:.2f} R={r:.2f} caught={sorted(caught)} missed={sorted(expected - flags)} "
                f"extra={sorted(flags - expected)} ${cost:.4f} {summary.get('elapsed_seconds', 0)}s",
                flush=True,
            )

        per_client[gi] = {
            "checkable_specs": len(checkable),
            "total_specs": cov["total"],
            "coverage_pct": cov["coverage_pct"],
            "corrected_fps": corrected_fps,
            "macro_precision": sum(macro_p) / max(len(macro_p), 1),
            "macro_recall": sum(macro_r) / max(len(macro_r), 1),
            "flawed_reports": len(macro_p),
        }
        if macro_p:
            print(
                f"  -> {gi} macro P={per_client[gi]['macro_precision']:.3f} "
                f"R={per_client[gi]['macro_recall']:.3f} | corrected FPs={corrected_fps}",
                flush=True,
            )

    # Corrected accuracy: fraction of corrected report×checkable opportunities with no blocking FP.
    # Simplified: 1 if zero FPs; else 1 − fps / (checkable × corrected reports).
    accuracy_corrected = (
        1.0
        if total_corrected_fps == 0
        else max(0.0, 1.0 - total_corrected_fps / max(total_checkable * max(total_corrected_reports, 1), 1))
    )
    results = {
        "mode": "production",
        "model": args.model,
        "vision": enable_vision,
        "report_count": len(all_reports),
        "per_client": per_client,
        "global": {
            "micro_precision_flawed": total_caught / max(total_flags_flawed, 1),
            "micro_recall_flawed": total_caught / max(total_expected, 1),
            "accuracy_corrected": accuracy_corrected,
            "corrected_fps": total_corrected_fps,
            "corrected_reports": total_corrected_reports,
            "caught": total_caught,
            "expected_checkable_labels": total_expected,
            "flags_flawed_checkable": total_flags_flawed,
            "checkable_specs": total_checkable,
            "total_specs": total_specs,
            "coverage_pct": 100.0 * total_checkable / max(total_specs, 1),
        },
        "reports": all_reports,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.output}")
    print(
        f"GLOBAL production: P={results['global']['micro_precision_flawed']:.3f} "
        f"R={results['global']['micro_recall_flawed']:.3f} "
        f"corrected accuracy={results['global']['accuracy_corrected']:.3f} "
        f"FPs={total_corrected_fps}"
    )
    _plot(results, args.plot)


if __name__ == "__main__":
    main()
