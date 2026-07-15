"""Confidence / disagreement cascade: escalate missing or disagreeing atom answers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from google import genai

from fact_extractor import AtomAnswer, ExtractItem, run_extract_atom, run_extract_batch
from gi_review import UsageStats

DEFAULT_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_CASCADE_WORKERS = 4


@dataclass
class CascadeResult:
    answers: dict[str, AtomAnswer] = field(default_factory=dict)
    escalated_ids: list[str] = field(default_factory=list)
    disagreed_ids: list[str] = field(default_factory=list)
    usage: UsageStats = field(default_factory=UsageStats)


def _boolish(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "yes", "1"):
        return True
    if text in ("false", "no", "0"):
        return False
    return None


def needs_escalation(answer: AtomAnswer, *, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> bool:
    """Escalate on abstention, or low confidence (kept as coarse gate only)."""
    if answer.value is None:
        return True
    if _boolish(answer.value) is None:
        return True
    return answer.confidence < threshold


def _merge_judge_answer(
    item_id: str,
    initial: dict[str, AtomAnswer],
    retry: AtomAnswer | None,
    *,
    double_sample: bool,
) -> tuple[AtomAnswer | None, bool]:
    """Return (updated answer or None to keep original, disagreed?)."""
    if retry is None:
        return None, False
    first = initial.get(item_id)
    first_b = _boolish(first.value) if first else None
    second_b = _boolish(retry.value)
    if double_sample and first_b is not None and second_b is not None and first_b != second_b:
        return (
            AtomAnswer(
                item_id=item_id,
                field=retry.field,
                value=None,
                confidence=0.0,
                evidence=(
                    f"disagreement: extract={first_b} vs judge={second_b}; {retry.evidence}"
                )[:500],
            ),
            True,
        )
    return retry, False


def run_cascade(
    client: genai.Client,
    judge_model: str,
    items: list[ExtractItem],
    initial: dict[str, AtomAnswer],
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    double_sample: bool = True,
    max_workers: int = DEFAULT_CASCADE_WORKERS,
) -> CascadeResult:
    """Escalate missing/low-confidence atoms via batched/parallel judge calls.

    Disagreement policy: if extract and judge disagree on the boolean, set value=None
    (unable) rather than trusting either — confidence self-grades are biased.
    """
    by_id = {item.item_id: item for item in items}
    out = dict(initial)
    escalated: list[str] = []
    disagreed: list[str] = []
    usage = UsageStats()

    candidates = [
        item_id
        for item_id, answer in initial.items()
        if needs_escalation(answer, threshold=threshold) and item_id in by_id
    ]
    if not candidates:
        return CascadeResult(answers=out)

    cand_items = [by_id[i] for i in candidates]
    escalated.extend(candidates)

    # Prefer one batched judge call when many candidates; parallel singles as fallback chunks.
    if len(cand_items) >= 2:
        batch = run_extract_batch(client, judge_model, cand_items)
        usage.add_usage(batch.usage)
        for item_id in candidates:
            updated, was_dis = _merge_judge_answer(
                item_id, initial, batch.answers.get(item_id), double_sample=double_sample
            )
            if was_dis:
                disagreed.append(item_id)
            if updated is not None:
                out[item_id] = updated
            elif item_id not in batch.answers:
                # Missing from batch — single retry
                item = by_id[item_id]
                retry = run_extract_atom(client, judge_model, item)
                usage.add_usage(retry.usage)
                updated, was_dis = _merge_judge_answer(
                    item_id, initial, retry.answer, double_sample=double_sample
                )
                if was_dis:
                    disagreed.append(item_id)
                if updated is not None:
                    out[item_id] = updated
    else:
        workers = max(1, min(max_workers, len(cand_items)))
        if workers == 1:
            for item_id in candidates:
                retry = run_extract_atom(client, judge_model, by_id[item_id])
                usage.add_usage(retry.usage)
                updated, was_dis = _merge_judge_answer(
                    item_id, initial, retry.answer, double_sample=double_sample
                )
                if was_dis:
                    disagreed.append(item_id)
                if updated is not None:
                    out[item_id] = updated
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(run_extract_atom, client, judge_model, by_id[item_id]): item_id
                    for item_id in candidates
                }
                for fut in as_completed(futures):
                    item_id = futures[fut]
                    retry = fut.result()
                    usage.add_usage(retry.usage)
                    updated, was_dis = _merge_judge_answer(
                        item_id, initial, retry.answer, double_sample=double_sample
                    )
                    if was_dis:
                        disagreed.append(item_id)
                    if updated is not None:
                        out[item_id] = updated

    return CascadeResult(
        answers=out,
        escalated_ids=escalated,
        disagreed_ids=disagreed,
        usage=usage,
    )


def answers_to_fact_values(answers: dict[str, AtomAnswer]) -> dict[str, Any]:
    return {answer.field: answer.value for answer in answers.values() if answer.value is not None}
