"""Batched fact extraction: cheap model answers closed questions, Python decides."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from gi_review import UsageStats, _usage_from_meta
from ir_checks import build_checkpoint_context


@dataclass
class ExtractItem:
    item_id: str
    checkpoint_id: str
    field: str
    question: str
    value_type: str
    context: str


@dataclass
class AtomAnswer:
    item_id: str
    field: str
    value: Any
    evidence: str


@dataclass
class ExtractBatchResult:
    values: dict[str, Any] = field(default_factory=dict)
    answers: dict[str, AtomAnswer] = field(default_factory=dict)
    usage: UsageStats = field(default_factory=UsageStats)
    raw_response: str = ""


@dataclass
class SingleExtractResult:
    answer: AtomAnswer | None
    usage: UsageStats = field(default_factory=UsageStats)
    raw_response: str = ""


DEFAULT_MAX_ITEMS_PER_BATCH = 8


def _operator_fields(spec: dict[str, Any]) -> list[str]:
    params = spec.get("params") or {}
    paths: list[str] = []
    for key, value in params.items():
        if key == "fields" and isinstance(value, list):
            paths.extend(str(v) for v in value)
        elif isinstance(value, str) and "." in value:
            paths.append(value)
    return paths


def build_extract_items(
    checkpoints: list[dict[str, Any]],
    specs: dict[str, dict[str, Any]],
    ir: dict[str, Any],
    facts: dict[str, Any],
    *,
    force_extract: bool = False,
    context_facts: dict[str, Any] | None = None,
) -> list[ExtractItem]:
    """Build extraction questions for spec checkpoints with missing or forced fields."""
    items: list[ExtractItem] = []
    seen: set[str] = set()
    context_lookup = context_facts or facts

    for checkpoint in checkpoints:
        cp_id = checkpoint["id"]
        spec = specs.get(cp_id)
        if not spec:
            continue

        extract_defs = list(spec.get("extract") or [])
        if not extract_defs and force_extract:
            for path in _operator_fields(spec):
                extract_defs.append(
                    {
                        "field": path,
                        "question": f"What is the value of {path}?",
                        "type": "string",
                    }
                )

        for definition in extract_defs:
            field_path = str(definition["field"])
            item_id = f"{cp_id}:{field_path}"
            if item_id in seen:
                continue
            current = facts.get(field_path)
            missing = current in (None, "", [])
            if not force_extract and not missing:
                continue
            seen.add(item_id)

            context = str(definition.get("context") or "")
            if not context:
                context_field = definition.get("context_field")
                if context_field:
                    raw = context_lookup.get(context_field)
                    if isinstance(raw, list):
                        context = ", ".join(str(v) for v in raw)
                    else:
                        context = str(raw or "")
                if not context:
                    context = build_checkpoint_context(checkpoint, ir)

            items.append(
                ExtractItem(
                    item_id=item_id,
                    checkpoint_id=cp_id,
                    field=field_path,
                    question=str(definition["question"]),
                    value_type=str(definition.get("type", "string")),
                    context=context[:4000],
                )
            )
    return items


def section_key_for_checkpoint(checkpoint: dict[str, Any]) -> str:
    """Group atoms by evidence slice to reduce cross-question interference (REST-style)."""
    sections = checkpoint.get("md_sections") or []
    if sections:
        return str(sections[0])
    if checkpoint.get("section"):
        return str(checkpoint["section"])
    scope = str(checkpoint.get("scope_type") or "FULL REPORT").upper()
    return scope


def group_extract_items(
    items: list[ExtractItem],
    checkpoints_by_id: dict[str, dict[str, Any]],
    *,
    max_per_batch: int = DEFAULT_MAX_ITEMS_PER_BATCH,
) -> list[list[ExtractItem]]:
    """Split items into section-scoped batches capped at ``max_per_batch``."""
    buckets: dict[str, list[ExtractItem]] = {}
    for item in items:
        cp = checkpoints_by_id.get(item.checkpoint_id, {})
        key = section_key_for_checkpoint(cp)
        buckets.setdefault(key, []).append(item)

    batches: list[list[ExtractItem]] = []
    for key in sorted(buckets):
        chunk = buckets[key]
        for i in range(0, len(chunk), max_per_batch):
            batches.append(chunk[i : i + max_per_batch])
    return batches


def _answers_from_parsed(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    answers = data.get("answers", data)
    if isinstance(answers, dict):
        return [{"id": key, "value": value} for key, value in answers.items()]
    if isinstance(answers, list):
        return [row for row in answers if isinstance(row, dict)]
    return []


def _parse_batch_response(text: str) -> list[dict[str, Any]]:
    """Parse model JSON; tolerate fences, trailing junk, and concatenated objects."""
    text = (text or "").strip()
    if not text:
        return []

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()

    decoder = json.JSONDecoder()
    candidates: list[Any] = []

    # Prefer first complete JSON value (object or array).
    for start in (m.start() for m in re.finditer(r"[\{\[]", text)):
        try:
            obj, _ = decoder.raw_decode(text, start)
            candidates.append(obj)
            break
        except json.JSONDecodeError:
            continue

    if not candidates:
        # Last resort: strip after first closing brace/bracket mismatch via greedy object match
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                candidates.append(json.loads(match.group(0)))
            except json.JSONDecodeError:
                return []

    for obj in candidates:
        rows = _answers_from_parsed(obj)
        if rows:
            return rows
    return _answers_from_parsed(candidates[0]) if candidates else []


def _coerce_value(raw: Any, value_type: str) -> Any:
    if raw is None:
        return None
    if value_type == "number":
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    if value_type == "boolean":
        if isinstance(raw, bool):
            return raw
        text = str(raw).strip().lower()
        if text in ("true", "yes", "1"):
            return True
        if text in ("false", "no", "0"):
            return False
        return None
    if value_type == "integer":
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None
    text = str(raw).strip()
    if text.lower() in {"null", "none", "n/a", "na", ""}:
        return None
    return text


def _build_extract_prompt(items: list[ExtractItem]) -> str:
    lines = [
        "You ground atomic facts for a compliance engine. Answer ONLY from the evidence shown.",
        "Do NOT decide pass/fail or violations — only extract factual values.",
        'Return JSON: {"answers": [{"id": "...", "value": ..., "evidence": "short quote"}]}',
        "Use null for value when not found.",
        "For boolean questions return true or false.",
        "For string questions return the quoted text (or null).",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"--- {item.item_id} ---",
                f"Question: {item.question}",
                f"Type: {item.value_type}",
                "Evidence:",
                item.context,
                "",
            ]
        )
    return "\n".join(lines)


def _rows_to_answers(
    rows: list[dict[str, Any]],
    by_id: dict[str, ExtractItem],
) -> tuple[dict[str, Any], dict[str, AtomAnswer]]:
    values: dict[str, Any] = {}
    answers: dict[str, AtomAnswer] = {}
    for row in rows:
        item_id = str(row.get("id", ""))
        item = by_id.get(item_id)
        if not item:
            continue
        coerced = _coerce_value(row.get("value"), item.value_type)
        evidence = str(row.get("evidence", ""))[:500]
        atom = AtomAnswer(
            item_id=item_id,
            field=item.field,
            value=coerced,
            evidence=evidence,
        )
        answers[item_id] = atom
        if coerced is not None:
            values[item.field] = coerced
    return values, answers


def run_extract_batch(
    client: genai.Client,
    model: str,
    items: list[ExtractItem],
) -> ExtractBatchResult:
    """One batched call: extract facts as atoms with confidence + evidence."""
    if not items:
        return ExtractBatchResult()

    import time

    prompt = _build_extract_prompt(items)
    last_err: Exception | None = None
    response = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            last_err = None
            break
        except Exception as exc:  # noqa: BLE001 — retry transient API failures
            last_err = exc
            msg = str(exc)
            if attempt >= 3 or not any(code in msg for code in ("503", "UNAVAILABLE", "429")):
                raise
            time.sleep(2 ** attempt)
    if response is None:
        raise last_err or RuntimeError("extract batch failed")
    raw = response.text or ""
    usage = _usage_from_meta(response.usage_metadata)

    by_id = {item.item_id: item for item in items}
    values, answers = _rows_to_answers(_parse_batch_response(raw), by_id)
    return ExtractBatchResult(values=values, answers=answers, usage=usage, raw_response=raw)


def run_extract_atom(
    client: genai.Client,
    model: str,
    item: ExtractItem,
) -> SingleExtractResult:
    """Single-atom extraction for cascade escalation."""
    batch = run_extract_batch(client, model, [item])
    answer = batch.answers.get(item.item_id)
    return SingleExtractResult(answer=answer, usage=batch.usage, raw_response=batch.raw_response)


def run_extract_batches(
    client: genai.Client,
    model: str,
    items: list[ExtractItem],
    checkpoints_by_id: dict[str, dict[str, Any]],
    *,
    max_per_batch: int = DEFAULT_MAX_ITEMS_PER_BATCH,
    max_workers: int | None = None,
) -> ExtractBatchResult:
    """Section-grouped batched extraction; independent batches run in parallel."""
    if not items:
        return ExtractBatchResult()

    from concurrent.futures import ThreadPoolExecutor, as_completed

    batches = list(group_extract_items(items, checkpoints_by_id, max_per_batch=max_per_batch))
    workers = max_workers
    if workers is None:
        workers = int(os.environ.get("GI_EXTRACT_WORKERS", "4") or 4)
    workers = max(1, min(workers, len(batches)))

    merged_values: dict[str, Any] = {}
    merged_answers: dict[str, AtomAnswer] = {}
    total_usage = UsageStats()
    raw_parts: list[str] = []

    if workers == 1 or len(batches) == 1:
        results = [run_extract_batch(client, model, batch_items) for batch_items in batches]
    else:
        results = [ExtractBatchResult()] * len(batches)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(run_extract_batch, client, model, batch_items): idx
                for idx, batch_items in enumerate(batches)
            }
            for fut in as_completed(futures):
                results[futures[fut]] = fut.result()

    for result in results:
        total_usage.add_usage(result.usage)
        merged_values.update(result.values)
        merged_answers.update(result.answers)
        if result.raw_response:
            raw_parts.append(result.raw_response)

    return ExtractBatchResult(
        values=merged_values,
        answers=merged_answers,
        usage=total_usage,
        raw_response="\n---\n".join(raw_parts),
    )


def apply_extracted_facts(facts: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    merged = dict(facts)
    for key, value in extracted.items():
        merged[key] = value
    return merged


def strip_fields(facts: dict[str, Any], field_paths: list[str]) -> dict[str, Any]:
    """Remove parser values so extraction must fill gaps."""
    stripped = dict(facts)
    for path in field_paths:
        stripped[path] = None
    return stripped
