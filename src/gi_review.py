"""Run DFI GI checkpoints against a cached inspection report (Markdown) via Gemini."""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from report_sections import extract_focus_slice
from glossary import format_glossary_block, load_glossary, matched_glossary_for_checkpoint
from report_to_ir import build_ir, render_context
from ir_checks import build_checkpoint_context, deterministic_verdict


DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_MAX_WORKERS = 10

MATCH_CLEAR = "clear_match"
MATCH_PARTIAL = "partial_unmatch"
MATCH_CLEAR_UNMATCH = "clear_unmatch"
MATCH_UNABLE = "unable_to_check"
VALID_MATCH_LEVELS = (MATCH_CLEAR, MATCH_PARTIAL, MATCH_CLEAR_UNMATCH, MATCH_UNABLE)

# USD per 1M tokens — ai.google.dev, July 2026
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
GEMINI_31_FLASH_LITE_PRICING = MODEL_PRICING["gemini-3.1-flash-lite"]


def pricing_for_model(model: str) -> dict[str, float]:
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    if "lite" in model.lower():
        return MODEL_PRICING["gemini-2.5-flash-lite"]
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
    arm: str = "judge"
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
    """Estimate USD cost from token usage (Gemini 3.1 Flash-Lite rates)."""
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


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_html_comments(report_md: str) -> str:
    """Remove HTML comment blocks (e.g. evaluation changelogs) from report markdown."""
    return _HTML_COMMENT_RE.sub("", report_md).strip()


def strip_inspector_comments(report_md: str) -> str:
    """Remove inspector comment fields from markdown while keeping results, values, and photo counts."""
    lines_out: list[str] = []
    comment_col_idx: int | None = None

    for line in report_md.splitlines():
        stripped = line.strip()

        if stripped.startswith("Comment:"):
            continue
        if stripped.startswith("- **Comment:**") or stripped.startswith("- Comments:"):
            continue
        if stripped.startswith("- ") and " — " in line:
            line = line.split(" — ", 1)[0].rstrip()

        if stripped.startswith("|") and "Comment" in line and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            try:
                comment_col_idx = cells.index("Comment")
            except ValueError:
                comment_col_idx = None
            lines_out.append(line)
            continue

        if comment_col_idx is not None and stripped.startswith("|") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) > comment_col_idx:
                cells[comment_col_idx] = "—"
                line = "| " + " | ".join(cells) + " |"
        elif not stripped.startswith("|"):
            comment_col_idx = None

        lines_out.append(line)

    return "\n".join(lines_out).strip()


def prepare_report_for_llm(report_md: str, *, strip_comments: bool = True) -> str:
    """Sanitize report markdown before sending it to the LLM."""
    text = strip_html_comments(report_md)
    if strip_comments:
        text = strip_inspector_comments(text)
    return text


def load_report_md(path: Path, *, strip_comments: bool = True) -> str:
    return prepare_report_for_llm(path.read_text(encoding="utf-8"), strip_comments=strip_comments)


def load_checkpoints(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"Checkpoints file is empty: {path}. Save data/clients/dfi/gi/rules.json before running.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in checkpoints file {path}: {exc}") from exc
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
        "partially_unmatch": MATCH_PARTIAL,
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
    """Map model match level + ops severity to a flag (Phase 2 policy)."""
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
    return False


def match_instructions(photo_check: str | None = None) -> list[str]:
    lines = [
        "Classify how well the report matches this requirement.",
        "Do NOT decide pass/fail — only return a match level.",
        "",
        "Match levels:",
        f"- {MATCH_CLEAR}: requirement met with explicit text evidence",
        f"- {MATCH_PARTIAL}: minor gap or incompleteness, not a clear contradiction",
        f"- {MATCH_CLEAR_UNMATCH}: explicit contradiction in report text",
        f"- {MATCH_UNABLE}: evidence missing or rule needs photo/image content not in markdown",
        "",
        "NOT_APPLICABLE handling: a NOT_APPLICABLE / N/A result means the inspector marked "
        "the check as not applicable for this order. Do NOT treat NOT_APPLICABLE as a "
        f"contradiction. Only return {MATCH_CLEAR_UNMATCH} for an N/A item if the requirement "
        f"explicitly says the check must be performed or must not be N/A; otherwise use {MATCH_UNABLE}.",
    ]
    if photo_check == "content":
        lines.extend(
            [
                "",
                "PHOTO CONTENT: You only have photo counts and captions, not images.",
                f"If judging requires seeing what is IN a photo, return {MATCH_UNABLE}.",
                "Do NOT infer photo content from count alone.",
            ]
        )
    elif photo_check == "metadata":
        lines.extend(
            [
                "",
                "PHOTO METADATA: You may use PASS/FAIL, photo counts, and explicit captions.",
            ]
        )
    return lines


def build_checkpoint_prompt(
    checkpoint: dict[str, Any],
    *,
    report_context: str = "",
    glossary_block: str = "",
) -> str:
    fail_if = checkpoint.get("fail_if") or []
    examples = checkpoint.get("examples") or {}
    lookup_table = checkpoint.get("lookup_table", "")
    never_flag_if = checkpoint.get("never_flag_if") or []
    context = checkpoint.get("context", "")
    photo_check = checkpoint.get("photo_check")

    lines = [
        f"Checkpoint ID: {checkpoint['id']}",
        f"Section: {checkpoint.get('section', '')}",
        f"Requirement: {checkpoint.get('requirement', '')}",
    ]

    lines.extend(match_instructions(photo_check))

    if glossary_block:
        lines.extend(["", glossary_block])

    if context:
        lines.append(f"Context: {context}")

    if lookup_table:
        lines.append(f"Reference table:\n{lookup_table}")

    if report_context:
        lines.extend(["", "REPORT EVIDENCE (use only this):", report_context])

    lines.append("")
    lines.append("Flag if any of:")
    lines.extend(f"- {item}" for item in fail_if)

    if never_flag_if:
        lines.append("NEVER flag if:")
        lines.extend(f"- {item}" for item in never_flag_if)

    if examples:
        if examples.get("pass"):
            lines.append("Pass examples:")
            lines.extend(f"  - {x}" for x in examples["pass"])
        if examples.get("fail"):
            lines.append("Fail examples:")
            lines.extend(f"  - {x}" for x in examples["fail"])

    lines.extend(
        [
            "",
            "Use only the report evidence above. When uncertain between partial and unable, prefer unable_to_check.",
            'Return ONLY valid JSON: {"match": "clear_match|partial_unmatch|clear_unmatch|unable_to_check", "reason": "...", "evidence": "..."}',
        ]
    )
    return "\n".join(lines)


def parse_checkpoint_response(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
    data = json.loads(text)

    if "match" in data:
        match = normalize_match(str(data.get("match", "")))
    elif "violates" in data:
        match = MATCH_CLEAR_UNMATCH if bool(data.get("violates")) else MATCH_CLEAR
    else:
        match = MATCH_CLEAR

    return {
        "match": match,
        "reason": str(data.get("reason", "")),
        "evidence": str(data.get("evidence", "")),
    }


def run_checkpoint(
    client: genai.Client,
    model: str,
    checkpoint: dict[str, Any],
    report_context: str,
    *,
    glossary: dict[str, str] | None = None,
    strict_blocking: bool = False,
    sleep_seconds: float = 0.0,
) -> CheckpointResult:
    glossary = glossary or {}
    user_prompt = build_checkpoint_prompt(
        checkpoint,
        report_context=report_context,
        glossary_block=format_glossary_block(
            matched_glossary_for_checkpoint(checkpoint, glossary)
        ),
    )
    severity = str(checkpoint.get("severity") or "BLOCKING").upper()
    if sleep_seconds:
        time.sleep(sleep_seconds)

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )
        raw = response.text or ""
        parsed = parse_checkpoint_response(raw)
        match = parsed["match"]
        violates = match_to_violates(match, severity, strict_blocking=strict_blocking)
        usage = _usage_from_meta(response.usage_metadata)
        return CheckpointResult(
            checkpoint_id=checkpoint["id"],
            section=str(checkpoint.get("section", "")),
            match=match,
            violates=violates,
            reason=parsed["reason"],
            evidence=parsed["evidence"],
            usage=usage,
            user_prompt=user_prompt,
            raw_response=raw,
            severity=severity,
        )
    except Exception as exc:
        return CheckpointResult(
            checkpoint_id=checkpoint["id"],
            section=str(checkpoint.get("section", "")),
            match=MATCH_UNABLE,
            violates=False,
            reason=f"LLM call failed: {type(exc).__name__}",
            evidence="",
            usage=UsageStats(),
            user_prompt=user_prompt,
            raw_response="",
            severity=severity,
            error=f"{type(exc).__name__}: {exc}",
        )


def result_from_verdict(
    checkpoint: dict[str, Any],
    verdict: dict[str, Any],
    *,
    strict_blocking: bool,
) -> CheckpointResult:
    """Turn a deterministic IR verdict into a CheckpointResult (no LLM usage)."""
    severity = str(checkpoint.get("severity") or "BLOCKING").upper()
    match = verdict["match"]
    return CheckpointResult(
        checkpoint_id=checkpoint["id"],
        section=str(checkpoint.get("section", "")),
        match=match,
        violates=match_to_violates(match, severity, strict_blocking=strict_blocking),
        reason=verdict.get("reason", ""),
        evidence=verdict.get("evidence", ""),
        usage=UsageStats(),
        user_prompt="",
        raw_response=verdict.get("source", "deterministic"),
        severity=severity,
    )


def build_report_context(
    checkpoint: dict[str, Any],
    *,
    ir: dict[str, Any] | None,
    report_md: str,
) -> str:
    """Per-checkpoint evidence. IR-slice when we have the typed report, else markdown.

    IR mode sends only the bound nodes + report facts (~50-800 tokens) instead of
    the whole report, which is smaller, faster, and keeps typed facts like
    ``applicable`` the model would otherwise re-derive from prose.
    """
    if ir is not None:
        return build_checkpoint_context(checkpoint, ir)
    focus = extract_focus_slice(report_md, checkpoint)
    return focus or report_md


def run_all_checkpoints(
    report_md_path: Path | None,
    checkpoints_path: Path,
    *,
    project_root: Path | None = None,
    limit: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    sleep_seconds: float = 0.0,
    strip_comments: bool = True,
    strict_blocking: bool | None = None,
    report_json_path: Path | None = None,
    ir_precheck: bool = True,
) -> ReviewRun:
    """Review checkpoints against a report. Parallel when max_workers > 1.

    Context is built per checkpoint (no shared cache):
      - IR mode (``report_json_path`` given): send only the bound IR nodes + report
        facts. Deterministic IR checks run first and skip the LLM entirely.
      - Legacy markdown mode (``report_md_path`` only, e.g. hand-edited flawed
        reports): send the focus slice, or the whole report if there is no slice.
    """
    api_key, model = load_env(project_root)
    client = genai.Client(api_key=api_key)
    strict = strict_blocking_enabled() if strict_blocking is None else strict_blocking

    ir = None
    if report_json_path is not None:
        ir = build_ir(json.loads(Path(report_json_path).read_text(encoding="utf-8")))
        report_md = ""
        report_path = str(report_json_path)
        report_est_tokens = estimate_tokens(render_context(ir, ir.get("nodes", [])))
    else:
        report_md = load_report_md(report_md_path, strip_comments=strip_comments)
        report_path = str(report_md_path)
        report_est_tokens = estimate_tokens(report_md)

    checkpoints = load_checkpoints(checkpoints_path)
    if limit is not None:
        checkpoints = checkpoints[:limit]

    # Deterministic pre-check: resolve what we can from the typed IR, no LLM.
    precheck_by_id: dict[str, CheckpointResult] = {}
    llm_checkpoints: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        verdict = deterministic_verdict(checkpoint, ir) if (ir is not None and ir_precheck) else None
        if verdict is not None:
            precheck_by_id[checkpoint["id"]] = result_from_verdict(
                checkpoint, verdict, strict_blocking=strict
            )
        else:
            llm_checkpoints.append(checkpoint)

    context_by_id = {
        cp["id"]: build_report_context(cp, ir=ir, report_md=report_md)
        for cp in llm_checkpoints
    }
    glossary = load_glossary()

    run = ReviewRun(
        model=model,
        report_path=report_path,
        report_est_tokens=report_est_tokens,
    )
    run.precheck_resolved = list(precheck_by_id.keys())

    llm_by_id: dict[str, CheckpointResult] = {}
    if max_workers <= 1:
        for checkpoint in llm_checkpoints:
            llm_by_id[checkpoint["id"]] = run_checkpoint(
                client,
                model,
                checkpoint,
                context_by_id[checkpoint["id"]],
                glossary=glossary,
                strict_blocking=strict,
                sleep_seconds=sleep_seconds,
            )
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    run_checkpoint,
                    client,
                    model,
                    checkpoint,
                    context_by_id[checkpoint["id"]],
                    glossary=glossary,
                    strict_blocking=strict,
                    sleep_seconds=0.0,
                ): checkpoint["id"]
                for checkpoint in llm_checkpoints
            }
            for future in as_completed(futures):
                result = future.result()
                llm_by_id[result.checkpoint_id] = result

    # Merge deterministic + LLM results back into original checkpoint order.
    merged: dict[str, CheckpointResult] = {**precheck_by_id, **llm_by_id}
    run.checkpoint_results = [merged[cp["id"]] for cp in checkpoints if cp["id"] in merged]
    return run


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

    per_call = []
    for result in run.checkpoint_results:
        per_call.append(
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
        )

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

    payload = {
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
    return payload



def main() -> None:
    import argparse

    from clients import project_root

    root = project_root()
    parser = argparse.ArgumentParser(description="Run GI checkpoint review via Gemini")
    parser.add_argument(
        "--report-json",
        type=Path,
        default=root / "data/clients/ribkoff/corrected/Q2614146161.json",
    )
    parser.add_argument(
        "--checkpoints",
        type=Path,
        default=root / "data/pipeline/checkpoints/ribkoff_checkpoints.json",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "data/pipeline/results/gi_review_results.json",
    )
    args = parser.parse_args()

    started = time.time()
    run = run_all_checkpoints(
        None,
        args.checkpoints,
        project_root=root,
        limit=args.limit,
        max_workers=args.max_workers,
        report_json_path=args.report_json,
    )
    elapsed = time.time() - started

    summary = format_cost_summary(run)
    summary["elapsed_seconds"] = round(elapsed, 1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Model: {run.model}")
    print(f"Checkpoints: {summary['checkpoints_run']} | Blocking flags: {summary['flags_count']} | Total flags: {summary['total_flags_count']} | Errors: {len(summary['errors'])}")
    print(f"Pre-checked (no LLM): {summary['precheck_resolved_count']} | LLM calls: {summary['llm_checkpoints_count']}")
    print(f"Tokens — prompt: {summary['totals']['prompt_tokens']:,} | output: {summary['totals']['output_tokens']:,}")
    cost = summary["cost_usd"]["total"]
    print(
        f"Cost ({run.model}) — "
        f"input ${cost['input_cost_usd']:.4f} + "
        f"output ${cost['output_cost_usd']:.4f} = "
        f"${cost['total_cost_usd']:.4f}"
    )
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Results written to {args.output}")

    if summary["blocking_flags"]:
        print("\n--- BLOCKING FLAGS ---")
        for flag in summary["blocking_flags"]:
            print(f"\n[{flag['checkpoint_id']}] ({flag['section']})")
            print(f"  Reason: {flag['reason']}")
            print(f"  Evidence: {flag['evidence']}")


if __name__ == "__main__":
    main()
