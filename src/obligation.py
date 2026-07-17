"""Conditional obligation model: WHEN / THEN / UNLESS over primitive predicates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from primitives import PRIMITIVE_OPS


@dataclass
class ObligationSpec:
    checkpoint_id: str
    severity: str = "BLOCKING"
    when: dict[str, Any] | None = None
    then: dict[str, Any] | None = None
    unless: dict[str, Any] | None = None
    requirement: str = ""
    extract: list[dict[str, Any]] = field(default_factory=list)
    source: str = "compiled"

    def to_dict(self) -> dict[str, Any]:
        base = {
            "checkpoint_id": self.checkpoint_id,
            "severity": self.severity,
            "when": self.when,
            "then": self.then,
            "unless": self.unless,
            "requirement": self.requirement,
            "extract": self.extract,
            "source": self.source,
        }
        base["tier"] = derive_tier(base)
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObligationSpec:
        return cls(
            checkpoint_id=str(data["checkpoint_id"]),
            severity=str(data.get("severity") or "BLOCKING"),
            when=data.get("when"),
            then=data.get("then"),
            unless=data.get("unless"),
            requirement=str(data.get("requirement") or ""),
            extract=list(data.get("extract") or []),
            source=str(data.get("source") or "compiled"),
        )


def derive_tier(spec: ObligationSpec | dict[str, Any]) -> str:
    """Classify spec for metrics: deterministic | atoms | vision | mixed."""
    if isinstance(spec, ObligationSpec):
        data = {
            "when": spec.when,
            "then": spec.then,
            "unless": spec.unless,
        }
    else:
        data = spec
    leaves = collect_leaves(data.get("then"))
    collect_leaves(data.get("when"), leaves)
    collect_leaves(data.get("unless"), leaves)
    kinds = {leaf.get("ground") or leaf.get("op") for leaf in leaves}
    kinds.discard(None)
    if "vision" in kinds:
        return "vision"
    if "atom" in kinds:
        return "atoms"
    return "deterministic"


def collect_leaves(node: dict[str, Any] | None, out: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Collect atom and vision leaves from a predicate tree."""
    if out is None:
        out = []
    if not node:
        return out
    op = str(node.get("op") or "")
    if op == "atom":
        out.append({**node, "ground": "atom"})
        return out
    if op == "vision":
        out.append({**node, "ground": "vision"})
        return out
    if op in ("all_of", "any_of"):
        for item in node.get("items") or []:
            collect_leaves(item, out)
    elif op == "not":
        collect_leaves(node.get("item"), out)
    return out


def collect_all_leaves(spec: dict[str, Any] | ObligationSpec) -> list[dict[str, Any]]:
    if isinstance(spec, ObligationSpec):
        data = {"when": spec.when, "then": spec.then, "unless": spec.unless}
    else:
        data = spec
    leaves: list[dict[str, Any]] = []
    for part in ("when", "unless", "then"):
        collect_leaves(data.get(part), leaves)
    return leaves


def validate_predicate(node: dict[str, Any] | None, errors: list[str], path: str = "root") -> None:
    if not node:
        return
    op = str(node.get("op") or "")
    if op not in PRIMITIVE_OPS:
        errors.append(f"{path}: unknown op '{op}'")
        return
    if op in ("all_of", "any_of"):
        for i, item in enumerate(node.get("items") or []):
            validate_predicate(item, errors, f"{path}.{op}[{i}]")
    elif op == "not":
        validate_predicate(node.get("item"), errors, f"{path}.not")
    elif op in ("atom", "vision"):
        if not node.get("id"):
            errors.append(f"{path}: {op} missing id")
    elif op not in ("true", "false"):
        if op in ("ratio_at_least",):
            for key in ("numerator", "denominator"):
                if not node.get(key):
                    errors.append(f"{path}: {op} missing {key}")
        elif op == "compare":
            has_two = bool(node.get("left") and node.get("right"))
            has_const = bool(node.get("selector") and (node.get("value") is not None or node.get("right")))
            has_left_const = bool(node.get("left") and node.get("value") is not None)
            has_binding = bool(node.get("binding"))
            if not (has_two or has_const or has_left_const or node.get("selector") or has_binding):
                errors.append(f"{path}: compare needs selector+value or left+right")
        elif op == "filename_matches":
            if not node.get("selector") and not node.get("binding"):
                errors.append(f"{path}: filename_matches missing selector")
        elif op not in ("all_of", "any_of", "not", "atom", "vision", "true", "false"):
            # Intent bindings are a valid alternative to frozen selectors.
            if not node.get("selector") and not node.get("binding"):
                if op in (
                    "equals",
                    "in_set",
                    "contains",
                    "contains_number",
                    "count_at_most",
                    "count_at_least",
                    "exists",
                    "is_blank",
                    "matches",
                ):
                    errors.append(f"{path}: {op} missing selector")


def validate_checkspec(spec: dict[str, Any] | ObligationSpec) -> list[str]:
    if isinstance(spec, ObligationSpec):
        data = {
            "checkpoint_id": spec.checkpoint_id,
            "when": spec.when,
            "unless": spec.unless,
            "then": spec.then,
            "source": spec.source,
            "status_class": None,
        }
    else:
        data = spec
    errors: list[str] = []
    if not data.get("checkpoint_id"):
        errors.append("missing checkpoint_id")
    status = str(data.get("status_class") or "")
    source = str(data.get("source") or "")
    # Non-checkable specs have no then — that's intentional.
    if status in ("advisory", "pending", "unauthored", "unmapped") or source in (
        "advisory",
        "pending",
        "unauthored",
        "unmapped",
        "missing_block",
    ):
        return errors
    if not data.get("then"):
        errors.append("missing then obligation")
    for part in ("when", "unless", "then"):
        validate_predicate(data.get(part), errors, part)
    return errors


def save_checkspecs(path: str | Any, specs: dict[str, dict[str, Any]], meta: dict[str, Any] | None = None) -> None:
    from pathlib import Path

    payload = {
        "meta": meta or {},
        "specs": specs,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_checkspecs(path: str | Any) -> dict[str, dict[str, Any]]:
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("specs") or {}
