"""Compile GI checkpoints from footer check blocks into ObligationSpecs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from check_block import compile_block, compile_checkpoints, validate_block
from fact_schema import resolve_where_bindings
from field_registry import STATUS_ADVISORY, STATUS_UNMAPPED
from obligation import save_checkspecs, validate_checkspec
from semantic_report import parse_semantic_report

COMPILER_VERSION = "2026-07-17.grounded-where"


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


def _load_sample_semantic(sample_report_path: Path | None):
    if sample_report_path is None or not sample_report_path.is_file():
        return None, {}
    report = json.loads(sample_report_path.read_text(encoding="utf-8"))
    semantic = parse_semantic_report(report)
    # Minimal facts dict — resolvability only needs checklist/section structure.
    facts: dict[str, Any] = {}
    return semantic, facts


def apply_resolvability_gate(
    specs: dict[str, dict[str, Any]],
    *,
    sample_report_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Downgrade specs whose where binds to nothing on a real sample report.

    out_of_report / unmapped / advisory are left alone.
    Zero resolved fields → status_class=unmapped (honest backlog, not advisory).
    """
    semantic, facts = _load_sample_semantic(sample_report_path)
    if semantic is None:
        return specs

    for _cp_id, spec in specs.items():
        status = str(spec.get("status_class") or "")
        if status in (STATUS_ADVISORY, STATUS_UNMAPPED):
            continue
        where = spec.get("where_bindings") or []
        if not where:
            continue
        # Skip pure out_of_report / unmapped markers.
        actionable = [
            b
            for b in where
            if isinstance(b, dict) and b.get("type") not in ("out_of_report", "unmapped")
        ]
        if not actionable:
            continue
        resolved = resolve_where_bindings(actionable, facts, semantic)
        if resolved:
            continue
        # Binding authored but resolves to zero fields on a real report.
        spec["status_class"] = STATUS_UNMAPPED
        spec["source"] = "unmapped"
        spec["then"] = None
        spec["when"] = None
        spec["resolvability"] = "unresolved"
        spec["data_source"] = str(spec.get("data_source") or "report_content")
    return specs


def compile_gi(
    checkpoints_path: Path,
    output_path: Path,
    *,
    hand_specs_path: Path | None = None,
    sample_report_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    from gi_review import load_checkpoints

    _ = hand_specs_path
    checkpoints = load_checkpoints(checkpoints_path)
    specs = compile_checkpoints(checkpoints)
    specs = apply_resolvability_gate(specs, sample_report_path=sample_report_path)

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
        "sample_report": str(sample_report_path) if sample_report_path else None,
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
