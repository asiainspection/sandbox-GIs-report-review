"""PolicyGuard review: parse → compile obligations → json eval → atom extract → cascade → symbolic."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cascade import DEFAULT_CONFIDENCE_THRESHOLD, run_cascade
from checkspec import load_hand_specs, resolve_specs
from atom_cache import (
    apply_cache_to_items,
    load_atom_cache,
    merge_answers_into_cache,
    report_cache_key,
    save_atom_cache,
)
from fact_extractor import (
    AtomAnswer,
    ExtractItem,
    apply_extracted_facts,
    build_extract_items,
    run_extract_batches,
)
from fact_index import build_fact_index
from gi_review import (
    CheckpointResult,
    ReviewRun,
    UsageStats,
    estimate_tokens,
    load_checkpoints,
    load_env,
    match_to_violates,
    strict_blocking_enabled,
)
from google import genai
from ir_checks import build_checkpoint_context
from obligation_eval import evaluate_obligation_symbolic, leaves_for_extraction, when_applies_json_only
from photo_store import ensure_report_photos, photos_for_checkpoint
from report_to_ir import build_ir, render_context
from semantic_report import parse_semantic_report
from symbolic_eval import MATCH_UNABLE, SymbolicVerdict
from vision_extract import VisionItem, run_vision_batches


def _answers_from_atoms(atom_answers: dict[str, AtomAnswer]) -> dict[str, Any]:
    return {f"atom.{k}": v.value for k, v in atom_answers.items()}


def _result_from_symbolic(
    checkpoint: dict[str, Any],
    verdict: SymbolicVerdict,
    *,
    strict: bool,
) -> CheckpointResult:
    severity = str(checkpoint.get("severity") or "BLOCKING").upper()
    return CheckpointResult(
        checkpoint_id=checkpoint["id"],
        section=str(checkpoint.get("section", "")),
        match=verdict.match,
        violates=match_to_violates(verdict.match, severity, strict_blocking=strict),
        reason=verdict.reason,
        evidence=verdict.evidence,
        usage=UsageStats(),
        user_prompt="",
        raw_response=verdict.source,
        severity=severity,
    )


def _build_obligation_extract_items(
    specs: dict[str, dict[str, Any]],
    checkpoints_by_id: dict[str, dict[str, Any]],
    ir: dict[str, Any],
    facts: dict[str, Any],
    semantic,
    *,
    ground: str = "atom",
) -> list[ExtractItem]:
    items: list[ExtractItem] = []
    seen: set[str] = set()
    for cp_id, spec in specs.items():
        cp = checkpoints_by_id[cp_id]
        # Ungated fail_if→atom is deferred at eval — skip LLM grounding.
        if str(spec.get("source") or "") == "fail_if_atoms" and not spec.get("when"):
            continue
        applies = when_applies_json_only(spec, facts, semantic=semantic)
        if applies is False:
            continue
        for leaf in leaves_for_extraction(spec, facts, semantic=semantic):
            if leaf.get("op") != ground and leaf.get("ground") != ground:
                continue
            lid = str(leaf["id"])
            if lid in seen:
                continue
            seen.add(lid)
            items.append(
                ExtractItem(
                    item_id=lid,
                    checkpoint_id=cp_id,
                    field=f"{ground}.{lid}",
                    question=str(leaf.get("question") or ""),
                    value_type="boolean",
                    context=build_checkpoint_context(cp, ir)[:6000],
                )
            )
    return items


def _build_vision_items(
    specs: dict[str, dict[str, Any]],
    checkpoints_by_id: dict[str, dict[str, Any]],
    ir: dict[str, Any],
    facts: dict[str, Any],
    semantic,
    photo_index: dict[str, list[Path]],
) -> list[VisionItem]:
    items: list[VisionItem] = []
    seen: set[str] = set()
    for cp_id, spec in specs.items():
        cp = checkpoints_by_id[cp_id]
        if str(spec.get("source") or "") == "fail_if_atoms" and not spec.get("when"):
            continue
        applies = when_applies_json_only(spec, facts, semantic=semantic)
        if applies is False:
            continue
        for leaf in leaves_for_extraction(spec, facts, semantic=semantic):
            if leaf.get("op") != "vision" and leaf.get("ground") != "vision":
                continue
            lid = str(leaf["id"])
            if lid in seen:
                continue
            seen.add(lid)
            paths = photos_for_checkpoint(cp, photo_index, ir=ir)
            items.append(
                VisionItem(
                    item_id=lid,
                    checkpoint_id=cp_id,
                    question=str(leaf.get("question") or ""),
                    image_paths=paths,
                    context=build_checkpoint_context(cp, ir)[:1500],
                )
            )
    return items


def _cache_path_for_checkpoints(checkpoints_path: Path, root: Path) -> Path:
    from clients import checkspecs_cache_path

    return checkspecs_cache_path(checkpoints_path, root)


def _pipeline_log(step: str, message: str, *, verbose: bool | None = None) -> None:
    """Print structured pipeline stage logs (enable with GI_PIPELINE_LOG=1, default on)."""
    if verbose is None:
        verbose = os.environ.get("GI_PIPELINE_LOG", "1").strip() not in {"0", "false", "False"}
    if verbose:
        print(f"[pipeline] {step}: {message}", flush=True)


def run_policy_review(
    report_json_path: Path,
    checkpoints_path: Path,
    *,
    specs_path: Path | None = None,
    checkspec_cache: Path | None = None,
    project_root: Path | None = None,
    extract_model: str | None = None,
    judge_model: str | None = None,
    cascade_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    strict_blocking: bool | None = None,
    enable_vision: bool | None = None,
) -> ReviewRun:
    """Full PolicyGuard path — obligations + atoms (+ optional vision); no per-checkpoint judge."""
    from clients import project_root as _project_root

    root = project_root or _project_root()
    api_key, default_judge = load_env(root)
    judge = judge_model or default_judge
    extractor = extract_model or os.environ.get("GI_EXTRACT_MODEL", "gemini-2.5-flash-lite").strip()
    if not extractor:
        extractor = "gemini-2.5-flash-lite"
    vision_model = os.environ.get("GI_VISION_MODEL", extractor).strip() or extractor
    strict = strict_blocking_enabled() if strict_blocking is None else strict_blocking

    _pipeline_log("1/6 parse", f"report={Path(report_json_path).name}")
    report = json.loads(Path(report_json_path).read_text(encoding="utf-8"))
    ir = build_ir(report)
    facts = build_fact_index(report)
    semantic = parse_semantic_report(report)
    _pipeline_log(
        "1/6 parse",
        f"facts={len(facts)} checklist_items={len(semantic.checklist_items)} ir_nodes={len(ir.get('nodes') or [])}",
    )

    _pipeline_log("2/6 compile", f"checkpoints={Path(checkpoints_path).name}")
    checkpoints = load_checkpoints(checkpoints_path)
    checkpoints_by_id = {cp["id"]: cp for cp in checkpoints}
    hand_specs_path = specs_path
    hand_specs = (
        load_hand_specs(hand_specs_path)
        if hand_specs_path is not None and Path(hand_specs_path).exists()
        else {}
    )
    cache = checkspec_cache or _cache_path_for_checkpoints(checkpoints_path, root)
    specs = resolve_specs(
        checkpoints,
        hand_specs=hand_specs,
        cache_path=cache if cache.exists() else None,
        checkpoints_path=checkpoints_path,
        hand_specs_path=hand_specs_path if hand_specs_path is not None and Path(hand_specs_path).exists() else None,
    )
    tier_counts: dict[str, int] = {}
    for sp in specs.values():
        t = str(sp.get("tier") or "atoms")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    _pipeline_log(
        "2/6 compile",
        f"specs={len(specs)} tiers={tier_counts} cache={'hit' if cache.exists() else 'miss'}",
    )

    client = genai.Client(api_key=api_key)
    working_facts = dict(facts)
    extract_usage = UsageStats()
    atom_answers: dict[str, AtomAnswer] = {}

    # Extract fields needed by hand operator specs (e.g. 1_2_1 remark atoms)
    _pipeline_log("3/6 ground_hand", f"hand_specs={len(hand_specs)}")
    if hand_specs:
        op_checkpoints = [checkpoints_by_id[cid] for cid in hand_specs if cid in checkpoints_by_id]
        op_items = build_extract_items(
            op_checkpoints,
            hand_specs,
            ir,
            working_facts,
            force_extract=False,
            context_facts=facts,
        )
        _pipeline_log("3/6 ground_hand", f"extract_items={len(op_items)}")
        if op_items:
            batch = run_extract_batches(client, extractor, op_items, checkpoints_by_id)
            extract_usage.add_usage(batch.usage)
            working_facts = apply_extracted_facts(working_facts, batch.values)
            for item_id, answer in batch.answers.items():
                atom_answers[item_id] = answer

    # Atom leaves from obligation specs (gated by WHEN) — text only
    atom_items = _build_obligation_extract_items(
        specs, checkpoints_by_id, ir, working_facts, semantic, ground="atom"
    )
    cache_key = report_cache_key(report)
    atom_disk = load_atom_cache(root, cache_key)
    atom_misses, atom_hits = apply_cache_to_items(atom_items, atom_disk)
    atom_answers.update(atom_hits)
    _pipeline_log(
        "4/6 ground_atoms",
        f"atom_leaves={len(atom_items)} cache_hits={len(atom_hits)} misses={len(atom_misses)} model={extractor}",
    )

    # Vision WHEN is json-only — overlap photo download+vision with atom LLM work.
    from concurrent.futures import ThreadPoolExecutor

    def _run_atoms() -> tuple[UsageStats, dict[str, AtomAnswer]]:
        local_usage = UsageStats()
        local_answers = dict(atom_answers)
        if not atom_items:
            return local_usage, local_answers
        if atom_misses:
            batch = run_extract_batches(client, extractor, atom_misses, checkpoints_by_id)
            local_usage.add_usage(batch.usage)
            local_answers.update(batch.answers)
        cascade = run_cascade(
            client,
            judge,
            atom_items,
            local_answers,
            threshold=cascade_threshold,
        )
        local_usage.add_usage(cascade.usage)
        local_answers = cascade.answers
        updated = merge_answers_into_cache(atom_disk, atom_items, local_answers)
        save_atom_cache(root, cache_key, updated)
        return local_usage, local_answers

    def _run_vision() -> tuple[UsageStats, dict[str, AtomAnswer], list[VisionItem], dict[str, list[Path]]]:
        local_usage = UsageStats()
        photo_idx = ensure_report_photos(report, root, enabled=enable_vision)
        v_items: list[VisionItem] = []
        v_answers: dict[str, AtomAnswer] = {}
        if photo_idx:
            v_items = _build_vision_items(
                specs, checkpoints_by_id, ir, working_facts, semantic, photo_idx
            )
            if v_items:
                vision_batch = run_vision_batches(client, vision_model, v_items)
                local_usage.add_usage(vision_batch.usage)
                v_answers = vision_batch.answers
        return local_usage, v_answers, v_items, photo_idx

    vision_items: list[VisionItem] = []
    photo_index: dict[str, list[Path]] = {}
    _pipeline_log("5/6 ground_vision", f"enable_vision={enable_vision} (overlapped with atoms)")

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_atoms = pool.submit(_run_atoms)
        fut_vision = pool.submit(_run_vision)
        a_usage, atom_answers = fut_atoms.result()
        extract_usage.add_usage(a_usage)
        v_usage, v_answers, vision_items, photo_index = fut_vision.result()
        extract_usage.add_usage(v_usage)
        atom_answers.update(v_answers)

    working_facts.update(_answers_from_atoms(atom_answers))
    unable_atoms = sum(1 for a in atom_answers.values() if a.value is None)
    _pipeline_log(
        "4/6 ground_atoms",
        f"answers={len(atom_answers)} unable_or_abstain={unable_atoms} cascade_judge={judge}",
    )
    if photo_index:
        _pipeline_log(
            "5/6 ground_vision",
            f"photos_indexed={sum(len(v) for v in photo_index.values())} vision_leaves={len(vision_items)}",
        )
    else:
        _pipeline_log("5/6 ground_vision", "skipped (no photo index)")

    results: dict[str, CheckpointResult] = {}
    deterministic_count = 0
    atom_count = 0
    vision_count = 0
    vision_evaluated = 0
    status_counts = {"clear": 0, "violates": 0, "unable": 0}

    for cp in checkpoints:
        cid = cp["id"]
        spec = specs[cid]
        tier = spec.get("tier", "atoms")
        if tier == "deterministic":
            deterministic_count += 1
        elif tier == "vision":
            vision_count += 1
        else:
            atom_count += 1

        sym = evaluate_obligation_symbolic(
            spec,
            working_facts,
            semantic=semantic,
            atom_answers=atom_answers,
            confidence_threshold=cascade_threshold,
        )
        if tier == "vision" and sym.match == MATCH_UNABLE and not photo_index:
            sym = SymbolicVerdict(
                match=MATCH_UNABLE,
                reason=(
                    "This rule requires judging photo content; text/metadata extraction cannot "
                    "verify it (vision photos unavailable)."
                ),
                evidence=build_checkpoint_context(cp, ir)[:400],
                source="obligation:vision_deferred",
            )
        elif tier == "vision" and sym.match != MATCH_UNABLE:
            vision_evaluated += 1
        results[cid] = _result_from_symbolic(cp, sym, strict=strict)
        if results[cid].violates:
            status_counts["violates"] += 1
        elif sym.match == MATCH_UNABLE:
            status_counts["unable"] += 1
        else:
            status_counts["clear"] += 1

    _pipeline_log(
        "6/6 evaluate",
        f"counts={status_counts} det={deterministic_count} atoms={atom_count} vision={vision_count}",
    )

    ordered = [results[cp["id"]] for cp in checkpoints]
    run = ReviewRun(
        model=f"policy:{extractor}+{judge}",
        report_path=str(report_json_path),
        report_est_tokens=estimate_tokens(render_context(ir, ir.get("nodes", []))),
        checkpoint_results=ordered,
        arm="policy_guard",
        extract_model=extractor,
        judge_model=judge,
    )
    run.extract_usage = extract_usage
    run.operator_resolved = [
        cp["id"] for cp in checkpoints if specs[cp["id"]].get("tier") == "deterministic"
    ]
    run.precheck_resolved = run.operator_resolved
    run.obligation_stats = {
        "deterministic": deterministic_count,
        "atoms": atom_count,
        "vision": vision_count,
        "atom_leaves_extracted": len(atom_items),
        "vision_leaves_queued": len(vision_items),
        "vision_evaluated": vision_evaluated,
        "photos_indexed": sum(len(v) for v in photo_index.values()),
    }
    return run
