"""Production review entrypoint: PolicyGuard via policy_review."""

from __future__ import annotations

from pathlib import Path

from cascade import DEFAULT_CONFIDENCE_THRESHOLD
from gi_review import ReviewRun


def review(
    report_json_path: Path,
    checkpoints_path: Path,
    *,
    specs_path: Path | None = None,
    project_root: Path | None = None,
    max_workers: int = 8,
    strict_blocking: bool | None = None,
    extract_model: str | None = None,
    judge_model: str | None = None,
    cascade_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    enable_vision: bool | None = None,
) -> ReviewRun:
    """Run PolicyGuard on one report (atoms + symbolic eval; no per-checkpoint LLM judge)."""
    from policy_review import run_policy_review

    root = project_root or Path(__file__).resolve().parents[1]
    _ = max_workers  # CLI compat; policy path is batched
    return run_policy_review(
        report_json_path,
        checkpoints_path,
        specs_path=specs_path,
        project_root=root,
        extract_model=extract_model,
        judge_model=judge_model,
        cascade_threshold=cascade_threshold,
        strict_blocking=strict_blocking,
        enable_vision=enable_vision,
    )


# Alias kept for older scripts / notebooks
run_production_review = review
