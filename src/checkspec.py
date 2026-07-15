"""Compile GI checkpoints into PolicyGuard obligation CheckSpecs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from compiler import compile_checkpoint, compile_checkpoints, load_cached_or_compile
from ir_checks import build_checkpoint_context
from obligation import collect_all_leaves


def load_hand_specs(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("specs") or {}


def load_checkspec_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("specs") or {}


def resolve_specs(
    checkpoints: list[dict[str, Any]],
    *,
    hand_specs: dict[str, dict[str, Any]] | None = None,
    cache_path: Path | None = None,
    checkpoints_path: Path | None = None,
    hand_specs_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    return load_cached_or_compile(
        checkpoints,
        cache_path=cache_path,
        hand_specs=hand_specs,
        checkpoints_path=checkpoints_path,
        hand_specs_path=hand_specs_path,
    )


def leaf_to_extract_item(
    leaf: dict[str, Any],
    checkpoint: dict[str, Any],
    ir: dict[str, Any],
) -> dict[str, Any]:
    """Shape atom/vision leaf → ExtractItem-compatible dict."""
    return {
        "item_id": leaf["id"],
        "checkpoint_id": checkpoint["id"],
        "field": f"atom.{leaf['id']}",
        "question": str(leaf.get("question") or ""),
        "value_type": "boolean",
        "context": build_checkpoint_context(checkpoint, ir)[:6000],
    }


def extract_items_from_spec(
    spec: dict[str, Any],
    checkpoint: dict[str, Any],
    ir: dict[str, Any],
) -> list[dict[str, Any]]:
    return [leaf_to_extract_item(leaf, checkpoint, ir) for leaf in collect_all_leaves(spec) if leaf.get("op") == "atom"]
