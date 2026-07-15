"""Disk cache for grounded atom answers — keyed by report + leaf, not checkpoint anecdotes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fact_extractor import AtomAnswer, ExtractItem


def _cache_root(project_root: Path) -> Path:
    return project_root / "data" / "cache" / "atoms"


def report_cache_key(report: dict[str, Any] | Path | str) -> str:
    if isinstance(report, (str, Path)):
        raw = Path(report).read_bytes()
    else:
        raw = json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _leaf_key(item: ExtractItem) -> str:
    blob = f"{item.item_id}|{item.field}|{item.question}|{item.context[:800]}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


def load_atom_cache(project_root: Path, report_key: str) -> dict[str, dict[str, Any]]:
    if os.environ.get("GI_ATOM_CACHE", "1").strip().lower() in {"0", "false", "no", "off"}:
        return {}
    path = _cache_root(project_root) / f"{report_key}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_atom_cache(project_root: Path, report_key: str, cache: dict[str, dict[str, Any]]) -> None:
    if os.environ.get("GI_ATOM_CACHE", "1").strip().lower() in {"0", "false", "no", "off"}:
        return
    root = _cache_root(project_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{report_key}.json"
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_cache_to_items(
    items: list[ExtractItem],
    cache: dict[str, dict[str, Any]],
) -> tuple[list[ExtractItem], dict[str, AtomAnswer]]:
    """Split items into cache hits (answers) and misses (still need LLM)."""
    hits: dict[str, AtomAnswer] = {}
    misses: list[ExtractItem] = []
    for item in items:
        key = _leaf_key(item)
        row = cache.get(key)
        if not row:
            misses.append(item)
            continue
        hits[item.item_id] = AtomAnswer(
            item_id=item.item_id,
            field=item.field,
            value=row.get("value"),
            confidence=float(row.get("confidence") or 0.0),
            evidence=str(row.get("evidence") or "atom_cache"),
        )
    return misses, hits


def merge_answers_into_cache(
    cache: dict[str, dict[str, Any]],
    items: list[ExtractItem],
    answers: dict[str, AtomAnswer],
) -> dict[str, dict[str, Any]]:
    by_id = {item.item_id: item for item in items}
    out = dict(cache)
    for item_id, answer in answers.items():
        item = by_id.get(item_id)
        if item is None:
            continue
        out[_leaf_key(item)] = {
            "item_id": item_id,
            "value": answer.value,
            "confidence": answer.confidence,
            "evidence": answer.evidence,
        }
    return out
