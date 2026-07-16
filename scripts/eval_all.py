#!/usr/bin/env python3
"""Multi-client PolicyGuard benchmark: precision on corrected, recall on labeled flawed.

Discovers clients from data/clients/*/client.json (see src/clients.py).

Usage:
    .venv/bin/python scripts/eval_all.py
    .venv/bin/python scripts/eval_all.py --gis ribkoff cemaco
    .venv/bin/python scripts/eval_all.py --offline --no-vision
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
from clients import ensure_pipeline_dirs, list_clients, load_client  # noqa: E402
from fact_index import build_fact_index  # noqa: E402
from review import run_production_review  # noqa: E402
from gi_review import format_cost_summary, load_checkpoints, match_to_violates, strict_blocking_enabled  # noqa: E402
from obligation_eval import evaluate_obligation  # noqa: E402
from semantic_report import parse_semantic_report  # noqa: E402

DEFAULT_ARMS = ("policy_guard",)


def _flagged_ids(summary: dict) -> set[str]:
    return {f["checkpoint_id"] for f in summary.get("flags") or []}


def _offline_policy(
    report_path: Path,
    checkpoints_path: Path,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    facts = build_fact_index(report)
    semantic = parse_semantic_report(report)
    checkpoints = load_checkpoints(checkpoints_path)
    from clients import checkspecs_cache_path
    cache = checkspecs_cache_path(checkpoints_path, ROOT)
    specs = resolve_specs(
        checkpoints,
        checkpoints_path=checkpoints_path,
        cache_path=cache if cache.exists() else None,
    )
    strict = strict_blocking_enabled()
    flags: list[dict[str, Any]] = []
    unable = 0
    det = 0
    for cp in checkpoints:
        spec = specs.get(cp["id"])
        if not spec:
            continue
        if str(spec.get("tier") or "") == "deterministic":
            det += 1
        verdict = evaluate_obligation(spec, facts, semantic=semantic, atom_answers={})
        severity = str(cp.get("severity") or "BLOCKING").upper()
        violates = match_to_violates(verdict.match, severity, strict_blocking=strict)
        if verdict.match == "unable" or verdict.status == "unable":
            unable += 1
        if violates:
            flags.append(
                {
                    "checkpoint_id": cp["id"],
                    "severity": severity,
                    "match": verdict.match,
                    "reason": verdict.reason,
                }
            )
    blocking = sum(1 for f in flags if f["severity"] == "BLOCKING")
    return {
        "arm": "policy_guard",
        "flags": flags,
        "blocking_flags_count": blocking,
        "total_flags_count": len(flags),
        "unable_to_check_count": unable,
        "obligation_stats": {"deterministic": det, "atom_leaves": 0, "vision_leaves": 0},
        "cost_usd": {"total": {"total_cost_usd": 0.0}},
    }


def _run_arm(
    arm: str,
    *,
    report: Path,
    checkpoints: Path,
    offline: bool,
    enable_vision: bool,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    if arm != "policy_guard":
        raise ValueError(f"Unsupported arm {arm!r}; only policy_guard is available after cleanup.")
    if offline:
        summary = _offline_policy(report, checkpoints)
    else:
        run = run_production_review(
            report,
            checkpoints,
            project_root=ROOT,
            enable_vision=enable_vision,
        )
        summary = format_cost_summary(run)
    summary["elapsed_seconds"] = round(time.perf_counter() - t0, 1)
    summary["arm"] = arm
    summary["report"] = report.name
    return summary


def _eval_corrected(client_id: str) -> list[Path]:
    """Corrected reports for precision; optional holdout via meta.eval_corrected stems."""
    client = load_client(client_id, ROOT)
    reports = client.corrected_reports()
    holdout = client.meta.get("eval_corrected")
    if holdout:
        wanted = {str(x) for x in holdout}
        reports = [p for p in reports if p.stem in wanted]
    return reports


def main() -> None:
    ensure_pipeline_dirs(ROOT)
    available = list_clients(ROOT)
    parser = argparse.ArgumentParser(description="PolicyGuard multi-client eval")
    parser.add_argument("--gis", nargs="+", default=available, choices=available or None)
    parser.add_argument("--arms", nargs="+", default=list(DEFAULT_ARMS))
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--no-vision", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/pipeline/eval/eval_all_results.json",
    )
    args = parser.parse_args()
    os.environ.setdefault("GI_PIPELINE_LOG", "0")
    if args.no_vision:
        os.environ["GI_VISION_ENABLED"] = "0"
    enable_vision = not args.no_vision and not args.offline

    # Optional synthetic refresh (noop if script absent)
    synth = ROOT / "scripts/make_synthetic_gi_reports.py"
    if synth.exists():
        os.system(f"{ROOT / '.venv/bin/python'} {synth} >/dev/null 2>&1")

    print(f"JUDGE_MODEL: {os.environ.get('JUDGE_MODEL', 'gemini-2.5-flash')}")
    print(f"EXTRACT_MODEL: {os.environ.get('GI_EXTRACT_MODEL', 'gemini-2.5-flash-lite')}")
    print(f"GIs: {args.gis}")
    print(f"Arms: {args.arms}")
    print(f"Mode: {'offline' if args.offline else 'online'} | vision={'off' if not enable_vision else 'on'}")

    all_results: list[dict[str, Any]] = []
    for gi in args.gis:
        client = load_client(gi, ROOT)
        cps = client.checkpoints_path
        if not cps.exists():
            print(f"\nSKIP {gi}: missing checkpoints {cps}")
            continue
        print("\n" + "=" * 78)
        print(f"GI: {gi}")
        print("=" * 78)

        for arm in args.arms:
            print(f"\nARM: {arm}")
            print("  PRECISION — corrected")
            fp = 0
            for report in _eval_corrected(gi):
                s = _run_arm(
                    arm,
                    report=report,
                    checkpoints=cps,
                    offline=args.offline,
                    enable_vision=enable_vision,
                )
                all_results.append({**s, "gi": gi})
                ids = sorted(_flagged_ids(s))
                fp += int(s.get("blocking_flags_count") or 0)
                cost = ((s.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
                stats = s.get("obligation_stats") or {}
                print(
                    f"    {report.stem}: blocking={s.get('blocking_flags_count')} "
                    f"total={s.get('total_flags_count')} unable={s.get('unable_to_check_count')} "
                    f"det={stats.get('deterministic', '?')} atom_leaves={stats.get('atom_leaves', '?')} "
                    f"vision_leaves={stats.get('vision_leaves', '?')} "
                    f"${cost:.4f} {s.get('elapsed_seconds', 0)}s flags={ids}"
                )
            print(f"    -> {fp} blocking false positives")

            print("  RECALL — flawed")
            macro_p: list[float] = []
            macro_r: list[float] = []
            for report, label_key in client.flawed_reports():
                expected = client.label_ids(label_key)
                if not expected:
                    print(f"    SKIP {report.stem}: no labels for {label_key}")
                    continue
                s = _run_arm(
                    arm,
                    report=report,
                    checkpoints=cps,
                    offline=args.offline,
                    enable_vision=enable_vision,
                )
                all_results.append({**s, "gi": gi, "label_key": label_key})
                flags = _flagged_ids(s)
                caught = flags & expected
                p = len(caught) / max(len(flags), 1)
                r = len(caught) / max(len(expected), 1)
                macro_p.append(p)
                macro_r.append(r)
                cost = ((s.get("cost_usd") or {}).get("total") or {}).get("total_cost_usd", 0)
                print(
                    f"    {report.stem}: blocking={s.get('blocking_flags_count')} "
                    f"total={s.get('total_flags_count')} unable={s.get('unable_to_check_count')} "
                    f"det={(s.get('obligation_stats') or {}).get('deterministic', '?')} "
                    f"atom_leaves={(s.get('obligation_stats') or {}).get('atom_leaves', '?')} "
                    f"vision_leaves={(s.get('obligation_stats') or {}).get('vision_leaves', '?')} "
                    f"${cost:.4f} {s.get('elapsed_seconds', 0)}s"
                )
                print(
                    f"      expected={sorted(expected)} caught={sorted(caught)} "
                    f"missed={sorted(expected - flags)} extra={sorted(flags - expected)} "
                    f"P={p:.2f} R={r:.2f}"
                )
            if macro_p:
                print(
                    f"    -> MACRO P={sum(macro_p)/len(macro_p):.3f} "
                    f"R={sum(macro_r)/len(macro_r):.3f}"
                )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
