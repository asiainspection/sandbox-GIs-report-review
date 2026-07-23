"""Shared types and utilities for PolicyGuard GI review."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

MATCH_CLEAR = "clear_match"
MATCH_PARTIAL = "partial_unmatch"
MATCH_CLEAR_UNMATCH = "clear_unmatch"
MATCH_UNABLE = "unable_to_check"
VALID_MATCH_LEVELS = (MATCH_CLEAR, MATCH_PARTIAL, MATCH_CLEAR_UNMATCH, MATCH_UNABLE)

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {
        "input_per_m": 0.30,
        "cached_input_per_m": 0.03,
        "output_per_m": 2.50,
    },
    "gemini-2.5-flash-lite": {
        "input_per_m": 0.10,
        "cached_input_per_m": 0.01,
        "output_per_m": 0.40,
    },
    "gemini-3.1-flash-lite": {
        "input_per_m": 0.25,
        "cached_input_per_m": 0.025,
        "output_per_m": 1.50,
    },
}

GEMINI_25_FLASH_PRICING = MODEL_PRICING["gemini-2.5-flash"]


def pricing_for_model(model: str) -> dict[str, float]:
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    if "lite" in model.lower():
        return MODEL_PRICING["gemini-3.1-flash-lite"]
    return MODEL_PRICING["gemini-2.5-flash"]


@dataclass
class UsageStats:
    prompt_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, meta: Any) -> None:
        if meta is None:
            return
        self.prompt_tokens += int(getattr(meta, "prompt_token_count", 0) or 0)
        self.cached_tokens += int(getattr(meta, "cached_content_token_count", 0) or 0)
        self.output_tokens += int(getattr(meta, "candidates_token_count", 0) or 0)
        self.total_tokens += int(getattr(meta, "total_token_count", 0) or 0)

    def add_usage(self, other: UsageStats) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.cached_tokens += other.cached_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens


@dataclass
class CheckpointResult:
    checkpoint_id: str
    section: str
    match: str
    violates: bool
    reason: str
    evidence: str
    usage: UsageStats
    user_prompt: str
    raw_response: str
    severity: str = "BLOCKING"
    error: str = ""

    @property
    def is_blocking_flag(self) -> bool:
        return self.violates and self.severity == "BLOCKING"


@dataclass
class ReviewRun:
    model: str
    report_path: str
    report_est_tokens: int
    checkpoint_results: list[CheckpointResult] = field(default_factory=list)
    skipped_checkpoints: list[str] = field(default_factory=list)
    precheck_resolved: list[str] = field(default_factory=list)
    arm: str = "policy_guard"
    extract_model: str = ""
    judge_model: str = ""
    extract_usage: UsageStats = field(default_factory=UsageStats)
    operator_resolved: list[str] = field(default_factory=list)
    obligation_stats: dict[str, int] = field(default_factory=dict)

    @property
    def total_usage(self) -> UsageStats:
        total = UsageStats()
        for result in self.checkpoint_results:
            total.add_usage(result.usage)
        total.add_usage(self.extract_usage)
        return total

    def flagged(self) -> list[CheckpointResult]:
        return [r for r in self.checkpoint_results if r.violates]

    def flagged_blocking(self) -> list[CheckpointResult]:
        return [r for r in self.checkpoint_results if r.is_blocking_flag]


def _usage_from_meta(meta: Any) -> UsageStats:
    usage = UsageStats()
    usage.add(meta)
    return usage


def estimate_cost_usd(
    usage: UsageStats,
    *,
    cache_create_tokens: int = 0,
    pricing: dict[str, float] | None = None,
) -> dict[str, float]:
    rates = pricing or GEMINI_25_FLASH_PRICING
    new_input = max(0, usage.prompt_tokens - usage.cached_tokens)
    input_cost = new_input / 1_000_000 * rates["input_per_m"]
    cached_cost = usage.cached_tokens / 1_000_000 * rates["cached_input_per_m"]
    output_cost = usage.output_tokens / 1_000_000 * rates["output_per_m"]
    cache_create_cost = cache_create_tokens / 1_000_000 * rates["input_per_m"]
    total = input_cost + cached_cost + output_cost + cache_create_cost
    return {
        "new_input_tokens": float(new_input),
        "cached_input_tokens": float(usage.cached_tokens),
        "output_tokens": float(usage.output_tokens),
        "input_cost_usd": input_cost,
        "cached_input_cost_usd": cached_cost,
        "output_cost_usd": output_cost,
        "cache_create_cost_usd": cache_create_cost,
        "total_cost_usd": total,
    }


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def load_env(project_root: Path | None = None) -> tuple[str, str]:
    from clients import project_root as _project_root

    root = project_root or _project_root()
    load_dotenv(root / ".env")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    return api_key, model


def load_checkpoints(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"Checkpoints file is empty: {path}")
    data = json.loads(raw)
    return data["checkpoints"]


def strict_blocking_enabled() -> bool:
    return os.environ.get("GI_STRICT_BLOCKING", "").strip().lower() in ("1", "true", "yes")


def normalize_match(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "match": MATCH_CLEAR,
        "clear_match": MATCH_CLEAR,
        "partial_unmatch": MATCH_PARTIAL,
        "partial": MATCH_PARTIAL,
        "clear_unmatch": MATCH_CLEAR_UNMATCH,
        "unmatch": MATCH_CLEAR_UNMATCH,
        "unable_to_check": MATCH_UNABLE,
        "unable": MATCH_UNABLE,
    }
    return aliases.get(cleaned, MATCH_CLEAR)


def match_to_violates(
    match: str,
    severity: str,
    *,
    strict_blocking: bool = False,
) -> bool:
    level = normalize_match(match)
    sev = (severity or "BLOCKING").upper()
    if level in (MATCH_CLEAR, MATCH_UNABLE):
        return False
    if level == MATCH_CLEAR_UNMATCH:
        return True
    if level == MATCH_PARTIAL:
        if sev == "MINOR":
            return False
        if sev == "BLOCKING":
            return strict_blocking
    return False


def format_cost_summary(run: ReviewRun) -> dict[str, Any]:
    total = run.total_usage
    rates = pricing_for_model(run.judge_model or run.model)
    total_cost = estimate_cost_usd(total, pricing=rates)
    extract_cost = estimate_cost_usd(run.extract_usage, pricing=pricing_for_model(run.extract_model or run.model))
    judge_usage = UsageStats()
    judge_usage.prompt_tokens = max(0, total.prompt_tokens - run.extract_usage.prompt_tokens)
    judge_usage.cached_tokens = max(0, total.cached_tokens - run.extract_usage.cached_tokens)
    judge_usage.output_tokens = max(0, total.output_tokens - run.extract_usage.output_tokens)
    judge_usage.total_tokens = max(0, total.total_tokens - run.extract_usage.total_tokens)
    judge_cost = estimate_cost_usd(judge_usage, pricing=rates)

    per_call = [
        {
            "checkpoint_id": result.checkpoint_id,
            "section": result.section,
            "severity": result.severity,
            "match": result.match,
            "violates": result.violates,
            "reason": result.reason,
            "evidence": result.evidence,
            "prompt_tokens": result.usage.prompt_tokens,
            "cached_tokens": result.usage.cached_tokens,
            "output_tokens": result.usage.output_tokens,
            "total_tokens": result.usage.total_tokens,
            "error": result.error,
        }
        for result in run.checkpoint_results
    ]

    def _flag_dict(result: CheckpointResult) -> dict[str, str]:
        return {
            "checkpoint_id": result.checkpoint_id,
            "section": result.section,
            "severity": result.severity,
            "match": result.match,
            "reason": result.reason,
            "evidence": result.evidence,
        }

    all_flags = [_flag_dict(r) for r in run.flagged()]
    blocking_flags = [_flag_dict(r) for r in run.flagged_blocking()]
    minor_flags = [_flag_dict(r) for r in run.flagged() if r.severity == "MINOR"]
    unable_count = sum(1 for r in run.checkpoint_results if r.match == MATCH_UNABLE)

    return {
        "model": run.model,
        "arm": run.arm,
        "extract_model": run.extract_model,
        "judge_model": run.judge_model or run.model,
        "report_path": run.report_path,
        "report_est_tokens": run.report_est_tokens,
        "checkpoints_run": len(run.checkpoint_results),
        "precheck_resolved_count": len(run.precheck_resolved),
        "operator_resolved_count": len(run.operator_resolved),
        "precheck_resolved": run.precheck_resolved,
        "operator_resolved": run.operator_resolved,
        "llm_checkpoints_count": len(run.checkpoint_results) - len(run.precheck_resolved),
        "flags_count": len(blocking_flags),
        "total_flags_count": len(all_flags),
        "blocking_flags_count": len(blocking_flags),
        "minor_flags_count": len(minor_flags),
        "unable_to_check_count": unable_count,
        "flags": all_flags,
        "blocking_flags": blocking_flags,
        "minor_flags": minor_flags,
        "errors": [r.checkpoint_id for r in run.checkpoint_results if r.error],
        "obligation_stats": dict(run.obligation_stats or {}),
        "totals": {
            "prompt_tokens": total.prompt_tokens,
            "cached_tokens": total.cached_tokens,
            "output_tokens": total.output_tokens,
            "total_tokens": total.total_tokens,
            "extract_prompt_tokens": run.extract_usage.prompt_tokens,
            "extract_output_tokens": run.extract_usage.output_tokens,
            "judge_prompt_tokens": judge_usage.prompt_tokens,
            "judge_output_tokens": judge_usage.output_tokens,
        },
        "pricing": rates,
        "cost_usd": {
            "extract": extract_cost,
            "judge": judge_cost,
            "total": total_cost,
        },
        "per_checkpoint": per_call,
    }
