"""Compile GI checkpoints into PolicyGuard obligation CheckSpecs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from compiler import compile_checkpoint, compile_checkpoints, load_cached_or_compile


def resolve_specs(
    checkpoints: list[dict[str, Any]],
    *,
    cache_path: Path | None = None,
    checkpoints_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    return load_cached_or_compile(
        checkpoints,
        cache_path=cache_path,
        checkpoints_path=checkpoints_path,
    )
