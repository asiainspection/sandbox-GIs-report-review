"""Null-only retry: re-ask the same extractor when a leaf returned no value.

No LLM self-scored confidence. No second-model judge. Keep it simple:
value present -> use it; value null -> one retry; still null -> unable.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from google import genai

from fact_extractor import AtomAnswer, ExtractItem, run_extract_atom, run_extract_batch
from gi_review import UsageStats

DEFAULT_CASCADE_WORKERS = 4
# Kept for import compatibility with older call sites.
DEFAULT_CONFIDENCE_THRESHOLD = 0.0


@dataclass
class CascadeResult:
    answers: dict[str, AtomAnswer] = field(default_factory=dict)
    escalated_ids: list[str] = field(default_factory=list)
    disagreed_ids: list[str] = field(default_factory=list)
    usage: UsageStats = field(default_factory=UsageStats)


def needs_escalation(answer: AtomAnswer, *, threshold: float = 0.0) -> bool:
    """Retry only when the leaf has no usable value."""
    _ = threshold
    return answer.value is None or (
        isinstance(answer.value, str) and not str(answer.value).strip()
    )


def run_cascade(
    client: genai.Client,
    judge_model: str,
    items: list[ExtractItem],
    initial: dict[str, AtomAnswer],
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    double_sample: bool = False,
    max_workers: int = DEFAULT_CASCADE_WORKERS,
) -> CascadeResult:
    """Re-extract null leaves with the same extractor model (no confidence, no judge)."""
    _ = double_sample
    by_id = {item.item_id: item for item in items}
    out = dict(initial)
    usage = UsageStats()

    candidates = [
        item_id
        for item_id, answer in initial.items()
        if needs_escalation(answer, threshold=threshold) and item_id in by_id
    ]
    if not candidates:
        return CascadeResult(answers=out)

    cand_items = [by_id[i] for i in candidates]
    extractor = judge_model  # same model; call site may still pass judge_model for compat

    if len(cand_items) >= 2:
        batch = run_extract_batch(client, extractor, cand_items)
        usage.add_usage(batch.usage)
        for item_id in candidates:
            retry = batch.answers.get(item_id)
            if retry is not None and retry.value is not None:
                out[item_id] = retry
            elif item_id not in batch.answers:
                single = run_extract_atom(client, extractor, by_id[item_id])
                usage.add_usage(single.usage)
                if single.answer is not None and single.answer.value is not None:
                    out[item_id] = single.answer
    else:
        workers = max(1, min(max_workers, len(cand_items)))
        if workers == 1:
            for item_id in candidates:
                retry = run_extract_atom(client, extractor, by_id[item_id])
                usage.add_usage(retry.usage)
                if retry.answer is not None and retry.answer.value is not None:
                    out[item_id] = retry.answer
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(run_extract_atom, client, extractor, by_id[item_id]): item_id
                    for item_id in candidates
                }
                for fut in as_completed(futures):
                    item_id = futures[fut]
                    retry = fut.result()
                    usage.add_usage(retry.usage)
                    if retry.answer is not None and retry.answer.value is not None:
                        out[item_id] = retry.answer

    return CascadeResult(
        answers=out,
        escalated_ids=candidates,
        disagreed_ids=[],
        usage=usage,
    )


def answers_to_fact_values(answers: dict[str, AtomAnswer]) -> dict[str, Any]:
    return {answer.field: answer.value for answer in answers.values() if answer.value is not None}
