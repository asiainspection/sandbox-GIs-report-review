"""Tests for checkpoint → CheckSpec compilation (obligation format)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import load_hand_specs, resolve_specs  # noqa: E402
from compiler import compile_checkpoint  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402


class CheckspecTests(unittest.TestCase):
    def test_operator_tier_from_hand_spec(self):
        cp = {"id": "3_1_6", "severity": "BLOCKING", "requirement": "No photos on pass"}
        hand = load_hand_specs(ROOT / "data/clients/ribkoff/gi/hand_specs.json")["3_1_6"]
        spec = compile_checkpoint(cp, hand)
        self.assertEqual(spec["tier"], "deterministic")
        self.assertIn("then", spec)

    def test_vision_tier_for_photo_content(self):
        cp = {
            "id": "3_1_3",
            "severity": "BLOCKING",
            "photo_check": "content",
            "requirement": "Photo must show defect",
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["tier"], "vision")

    def test_atoms_tier_with_excuses(self):
        cp = {
            "id": "1_2_1",
            "severity": "BLOCKING",
            "requirement": "Qty must match PO",
            "fail_if": ["Report does not satisfy: rule", "Packed below 80%"],
            "never_flag_if": ["N/A selected"],
        }
        spec = compile_checkpoint(cp, None)
        self.assertIn(spec["tier"], ("atoms", "deterministic"))

    def test_compile_all_ribkoff_checkpoints(self):
        cps_path = ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json"
        specs_path = ROOT / "data/clients/ribkoff/gi/hand_specs.json"
        checkpoints = load_checkpoints(cps_path)
        hand = load_hand_specs(specs_path)
        compiled = resolve_specs(
            checkpoints,
            hand_specs=hand,
            checkpoints_path=cps_path,
            hand_specs_path=specs_path,
        )
        self.assertEqual(len(compiled), len(checkpoints))
        tiers = {s["tier"] for s in compiled.values()}
        self.assertTrue(tiers <= {"deterministic", "atoms", "vision"})
        det_count = sum(1 for s in compiled.values() if s["tier"] == "deterministic")
        self.assertGreaterEqual(det_count, len(hand))


if __name__ == "__main__":
    unittest.main()
