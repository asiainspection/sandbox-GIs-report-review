#!/usr/bin/env python3
"""Head-to-head: PolicyGuard vs dump-to-LLM judge (honest P/R + latency).

Runs corrected (precision) + labeled flawed (recall) for selected GIs.
Hallmark note: PDFs are real; JSON is cover-overlay fixtures (QIMAone fetch needs
qsp rows / GUID per qimaone_report_fetch.py — not PDF CDN URLs).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from review import run_production_review  # noqa: E402
from gi_review import format_cost_summary, run_all_checkpoints  # noqa: E402

os.environ.setdefault("GI_VISION_ENABLED", "0")
os.environ.setdefault("GI_PIPELINE_LOG", "0")


def _labels(client: Path) -> dict[str, set[str]]:
    data = json.loads(client.read_text(encoding="utf-8"))
    return {k: set(v) for k, v in (data.get("introduced_checkpoints") or {}).items()}


def _flags(summary: dict[str, Any]) -> set[str]:
    return {f["checkpoint_id"] for f in summary.get("flags") or []}


def _run(arm: str, report: Path, checkpoints: Path, specs: Path | None) -> dict[str, Any]:
    t0 = time.perf_counter()
    if arm == "policy_guard":
        run = run_production_review(
            report,
            checkpoints,
            specs_path=specs,
            project_root=ROOT,
            enable_vision=False,
        )
    else:
        # Minimal dump-to-LLM baseline (no hybrid arms).
        run = run_all_checkpoints(
            None,
            checkpoints,
            report_json_path=report,
            max_workers=8,
            ir_precheck=True,
        )
    summary = format_cost_summary(run)
    summary["elapsed_seconds"] = round(time.perf_counter() - t0, 1)
    summary["arm"] = arm
    summary["report"] = report.name
    return summary


def _eval_gi(name: str, cfg: dict[str, Any], arms: list[str]) -> list[dict[str, Any]]:
    labels = _labels(cfg["client"])
    results: list[dict[str, Any]] = []
    print("=" * 72)
    print(f"GI: {name}")
    if cfg.get("note"):
        print(f"NOTE: {cfg['note']}")
    print("=" * 72)

    for arm in arms:
        print(f"\nARM: {arm}")
        print("  PRECISION — corrected")
        fp = 0
        for report in cfg["corrected"]:
            if not report.exists():
                print(f"    SKIP {report}")
                continue
            s = _run(arm, report, cfg["checkpoints"], cfg.get("specs"))
            results.append(s)
            ids = sorted(_flags(s))
            fp += int(s.get("blocking_flags_count") or 0)
            cost = ((s.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
            print(
                f"    {report.stem}: blocking={s.get('blocking_flags_count')} "
                f"total={s.get('total_flags_count')} unable={s.get('unable_to_check_count')} "
                f"${cost:.4f} {s['elapsed_seconds']}s flags={ids}"
            )
        print(f"    -> {fp} blocking FPs on corrected")

        print("  RECALL — labeled flawed")
        macro_p: list[float] = []
        macro_r: list[float] = []
        for report in cfg["flawed"]:
            if not report.exists():
                continue
            key = f"report_{report.stem.lower()}"
            expected = labels.get(key, set())
            if not expected:
                print(f"    SKIP {report.stem}: no labels for {key}")
                continue
            s = _run(arm, report, cfg["checkpoints"], cfg.get("specs"))
            results.append(s)
            flags = _flags(s)
            caught = flags & expected
            p = len(caught) / max(len(flags), 1)
            r = len(caught) / max(len(expected), 1)
            macro_p.append(p)
            macro_r.append(r)
            cost = ((s.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
            print(
                f"    {report.stem}: P={p:.2f} R={r:.2f} "
                f"caught={sorted(caught)} missed={sorted(expected - flags)} "
                f"extra={sorted(flags - expected)} ${cost:.4f} {s['elapsed_seconds']}s"
            )
        if macro_p:
            print(
                f"    -> MACRO P={sum(macro_p)/len(macro_p):.3f} "
                f"R={sum(macro_r)/len(macro_r):.3f}"
            )
    return results


def main() -> None:
    configs = {
        "ribkoff": {
            "checkpoints": ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json",
            "specs": ROOT / "data/clients/ribkoff/gi/hand_specs.json",
            "client": ROOT / "data/clients/ribkoff/client.json",
            "corrected": [
                ROOT / "data/clients/ribkoff/corrected/Q2614146161.json",
                ROOT / "data/clients/ribkoff/corrected/Q2614430689.json",
            ],
            "flawed": [
                ROOT / "data/clients/ribkoff/flawed/Q2614146161_flawed.json",
                ROOT / "data/clients/ribkoff/flawed/Q2614430689_flawed.json",
            ],
            "note": "Fair JSON head-to-head (holdout).",
        },
        "hallmark": {
            "checkpoints": ROOT / "data/pipeline/checkpoints/hallmark_checkpoints.json",
            "specs": None,
            "client": ROOT / "data/clients/hallmark/client.json",
            "corrected": sorted((ROOT / "data/clients/hallmark/corrected").glob("*.json")),
            "flawed": sorted((ROOT / "data/clients/hallmark/flawed").glob("*_flawed.json")),
            "note": (
                "PDF covers from real Hallmark reports; checklist JSON is synthetic overlay. "
                "QIMAone JSON not fetched: qimaone_report_fetch requires QSP id/rows, not PDF CDN URLs."
            ),
        },
    }

    arms = ["policy_guard", "judge"]
    all_results: list[dict[str, Any]] = []
    for gi, cfg in configs.items():
        gi_arms = list(arms)
        # Hallmark fixtures: PolicyGuard only (judge × 96 CPs is multi-hour noise).
        if gi == "hallmark":
            gi_arms = ["policy_guard"]
        all_results.extend(_eval_gi(gi, cfg, gi_arms))

    out = ROOT / "data/pipeline/eval/head_to_head_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
