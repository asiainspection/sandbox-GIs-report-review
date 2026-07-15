"""CI invariants: vocab bound, validation, json-WHEN floor across GIs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import load_hand_specs, resolve_specs  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation import collect_all_leaves, validate_checkspec  # noqa: E402
from primitives import PRIMITIVE_OPS  # noqa: E402

GIs = [
    ("ribkoff", ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json", ROOT / "data/clients/ribkoff/gi/hand_specs.json"),
    ("dfi", ROOT / "data/pipeline/checkpoints/dfi_checkpoints.json", None),
    ("hallmark", ROOT / "data/pipeline/checkpoints/hallmark_checkpoints.json", None),
]

# Soft floor: fraction of specs whose WHEN (if any) has no atom/vision leaves.
JSON_WHEN_FLOOR = {
    "ribkoff": 0.85,
    "dfi": 0.70,
    "hallmark": 0.80,
}


def _is_json_only_when(spec: dict) -> bool:
    when = spec.get("when")
    if not when:
        return True
    for leaf in collect_all_leaves({"when": when, "then": {"op": "true"}, "unless": None}):
        if leaf.get("op") in ("atom", "vision") or leaf.get("ground") in ("atom", "vision"):
            return False
    return True


class CiInvariantTests(unittest.TestCase):
    def test_vocab_bounded(self) -> None:
        used: set[str] = set()

        def walk(node: dict | None) -> None:
            if not node:
                return
            op = node.get("op")
            if op:
                used.add(str(op))
            if op in ("all_of", "any_of"):
                for item in node.get("items") or []:
                    walk(item)
            elif op == "not":
                walk(node.get("item"))

        for name, cps_path, specs_path in GIs:
            checkpoints = load_checkpoints(cps_path)
            hand = load_hand_specs(specs_path) if specs_path else {}
            compiled = resolve_specs(
                checkpoints, hand_specs=hand, checkpoints_path=cps_path, hand_specs_path=specs_path
            )
            for spec in compiled.values():
                for part in ("when", "unless", "then"):
                    walk(spec.get(part))
        self.assertTrue(used <= PRIMITIVE_OPS, used - PRIMITIVE_OPS)
        self.assertLessEqual(len(used), 25, f"too many primitives: {used}")

    def test_all_specs_validate_vocabulary(self) -> None:
        for name, cps_path, specs_path in GIs:
            checkpoints = load_checkpoints(cps_path)
            hand = load_hand_specs(specs_path) if specs_path else {}
            compiled = resolve_specs(
                checkpoints, hand_specs=hand, checkpoints_path=cps_path, hand_specs_path=specs_path
            )
            for cp_id, spec in compiled.items():
                errors = validate_checkspec(spec)
                self.assertEqual(errors, [], f"{name}/{cp_id}: {errors}")

    def test_json_when_floor(self) -> None:
        for name, cps_path, specs_path in GIs:
            checkpoints = load_checkpoints(cps_path)
            hand = load_hand_specs(specs_path) if specs_path else {}
            compiled = resolve_specs(
                checkpoints, hand_specs=hand, checkpoints_path=cps_path, hand_specs_path=specs_path
            )
            ok = sum(1 for s in compiled.values() if _is_json_only_when(s))
            share = ok / max(len(compiled), 1)
            floor = JSON_WHEN_FLOOR[name]
            self.assertGreaterEqual(
                share,
                floor,
                f"{name}: json-WHEN share {share:.2f} < floor {floor}",
            )


if __name__ == "__main__":
    unittest.main()
