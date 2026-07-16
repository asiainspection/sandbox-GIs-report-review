"""Compile GI checkpoints from footer check blocks into ObligationSpecs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from check_block import compile_block, compile_checkpoints, validate_block
from obligation import save_checkspecs, validate_checkspec

COMPILER_VERSION = "2026-07-16.footer"


def compile_checkpoint(
    checkpoint: dict[str, Any],
    hand_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile one checkpoint using its embedded check_block."""
    _ = hand_spec  # legacy arg — ignored
    block = checkpoint.get("check_block")
    return compile_block(checkpoint, block)


def source_hash(checkpoints_path: Path, hand_specs_path: Path | None = None) -> str:
    _ = hand_specs_path
    h = hashlib.sha256()
    h.update(COMPILER_VERSION.encode("utf-8"))
    h.update(checkpoints_path.read_bytes())
    return h.hexdigest()[:16]


def compile_gi(
    checkpoints_path: Path,
    output_path: Path,
    *,
    hand_specs_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    from gi_review import load_checkpoints

    _ = hand_specs_path
    checkpoints = load_checkpoints(checkpoints_path)
    specs = compile_checkpoints(checkpoints)
    errors: list[str] = []
    for cp in checkpoints:
        block = cp.get("check_block")
        if block:
            for err in validate_block(block, checkpoint_id=cp["id"]):
                errors.append(f"{cp['id']}.{err['field']}: {err['message']}")
    for cp_id, spec in specs.items():
        spec_errors = validate_checkspec(spec)
        if spec_errors:
            errors.extend(f"{cp_id}: {e}" for e in spec_errors)
    if errors:
        raise ValueError("CheckSpec validation failed:\n" + "\n".join(errors[:20]))

    meta = {
        "source": str(checkpoints_path),
        "checkpoint_count": len(specs),
        "source_hash": source_hash(checkpoints_path),
        "compiler": COMPILER_VERSION,
    }
    save_checkspecs(output_path, specs, meta)
    return specs


def load_cached_or_compile(
    checkpoints: list[dict[str, Any]],
    *,
    cache_path: Path | None = None,
    hand_specs: dict[str, dict[str, Any]] | None = None,
    checkpoints_path: Path | None = None,
    hand_specs_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    _ = hand_specs
    _ = hand_specs_path
    if cache_path and cache_path.exists() and checkpoints_path:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        meta = cached.get("meta") or {}
        expected = source_hash(checkpoints_path)
        if meta.get("source_hash") == expected:
            return cached.get("specs") or {}
    return compile_checkpoints(checkpoints)
