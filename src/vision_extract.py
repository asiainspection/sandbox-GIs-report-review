"""Batched boolean vision extraction for photo-content obligations."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from fact_extractor import AtomAnswer, ExtractBatchResult, _coerce_value, _parse_batch_response
from gi_review import UsageStats, _usage_from_meta

DEFAULT_MAX_VISION_PER_BATCH = 4
DEFAULT_MAX_IMAGES_PER_ITEM = 4


@dataclass
class VisionItem:
    item_id: str
    checkpoint_id: str
    question: str
    image_paths: list[Path]
    context: str = ""


@dataclass
class VisionBatchResult:
    answers: dict[str, AtomAnswer] = field(default_factory=dict)
    usage: UsageStats = field(default_factory=UsageStats)
    raw_response: str = ""


def _mime(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "image/jpeg"


def _build_vision_prompt(items: list[VisionItem]) -> str:
    lines = [
        "You ground photo-content facts for a compliance engine.",
        "Answer ONLY from the attached images (and brief context if provided).",
        "Do NOT invent details not visible in the photos.",
        'Return JSON: {"answers": [{"id": "...", "value": true|false|null, "confidence": 0.0-1.0, "evidence": "short description"}]}',
        "value=true only when photos clearly satisfy the question; false when they clearly contradict it; null when images are missing/unreadable.",
        "",
    ]
    for item in items:
        n = len(item.image_paths)
        lines.extend(
            [
                f"--- {item.item_id} ---",
                f"Question: {item.question}",
                f"Attached images for this question: {n}",
                f"Context: {item.context[:800]}" if item.context else "Context: (none)",
                "",
            ]
        )
    return "\n".join(lines)


def run_vision_batch(
    client: genai.Client,
    model: str,
    items: list[VisionItem],
) -> VisionBatchResult:
    """One multimodal batch: boolean answers for photo-content questions."""
    if not items:
        return VisionBatchResult()

    parts: list[Any] = [types.Part.from_text(text=_build_vision_prompt(items))]
    for item in items:
        for path in item.image_paths[:DEFAULT_MAX_IMAGES_PER_ITEM]:
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if not data:
                continue
            parts.append(types.Part.from_bytes(data=data, mime_type=_mime(path)))

    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    raw = response.text or ""
    usage = _usage_from_meta(response.usage_metadata)
    answers: dict[str, AtomAnswer] = {}
    by_id = {item.item_id: item for item in items}
    for row in _parse_batch_response(raw):
        item_id = str(row.get("id", ""))
        item = by_id.get(item_id)
        if not item:
            continue
        coerced = _coerce_value(row.get("value"), "boolean")
        try:
            confidence = float(row.get("confidence", 0.0 if coerced is None else 0.85))
        except (TypeError, ValueError):
            confidence = 0.85 if coerced is not None else 0.0
        confidence = max(0.0, min(1.0, confidence))
        answers[item_id] = AtomAnswer(
            item_id=item_id,
            field=f"vision.{item_id}",
            value=coerced,
            confidence=confidence,
            evidence=str(row.get("evidence", ""))[:500],
        )
    # Missing answers → unable (null) with low confidence
    for item in items:
        if item.item_id in answers:
            continue
        if not item.image_paths:
            answers[item.item_id] = AtomAnswer(
                item_id=item.item_id,
                field=f"vision.{item.item_id}",
                value=None,
                confidence=0.0,
                evidence="No matching photos found for this checkpoint.",
            )
        else:
            answers[item.item_id] = AtomAnswer(
                item_id=item.item_id,
                field=f"vision.{item.item_id}",
                value=None,
                confidence=0.0,
                evidence="Vision model did not return an answer for this id.",
            )
    return VisionBatchResult(answers=answers, usage=usage, raw_response=raw)


def run_vision_batches(
    client: genai.Client,
    model: str,
    items: list[VisionItem],
    *,
    max_per_batch: int = DEFAULT_MAX_VISION_PER_BATCH,
    max_workers: int = 4,
) -> VisionBatchResult:
    if not items:
        return VisionBatchResult()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os

    chunks = [items[i : i + max_per_batch] for i in range(0, len(items), max_per_batch)]
    workers = int(os.environ.get("GI_VISION_WORKERS", str(max_workers)) or max_workers)
    workers = max(1, min(workers, len(chunks)))

    merged: dict[str, AtomAnswer] = {}
    usage = UsageStats()
    raw_parts: list[str] = []

    if workers == 1 or len(chunks) == 1:
        results = [run_vision_batch(client, model, chunk) for chunk in chunks]
    else:
        results = [VisionBatchResult()] * len(chunks)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_vision_batch, client, model, chunk): idx for idx, chunk in enumerate(chunks)}
            for fut in as_completed(futures):
                results[futures[fut]] = fut.result()

    for result in results:
        merged.update(result.answers)
        usage.add_usage(result.usage)
        if result.raw_response:
            raw_parts.append(result.raw_response)
    return VisionBatchResult(
        answers=merged,
        usage=usage,
        raw_response="\n---\n".join(raw_parts),
    )


def as_extract_batch(vision: VisionBatchResult) -> ExtractBatchResult:
    values = {a.field: a.value for a in vision.answers.values() if a.value is not None}
    return ExtractBatchResult(
        values=values,
        answers=vision.answers,
        usage=vision.usage,
        raw_response=vision.raw_response,
    )
