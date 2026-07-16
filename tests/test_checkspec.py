"""Tests for checkpoint → CheckSpec compilation (footer path)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import resolve_specs  # noqa: E402
from compiler import compile_checkpoint  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402


class CheckspecTests(unittest.TestCase):
    def test_carton_drop_from_check_block(self):
        cp = {
            "id": "3_1_6",
            "severity": "BLOCKING",
            "requirement": "No photos on pass",
            "check_block": {
                "data_source": "in_report",
                "where": ["checklist.carton_drop_test.photo_count"],
                "when": "checklist.carton_drop_test.result equals PASS",
                "check": "count_at_most(0)",
            },
        }
        spec = compile_checkpoint(cp)
        self.assertEqual(spec["tier"], "deterministic")
        self.assertIn("then", spec)

    def test_extract_tier(self):
        cp = {
            "id": "1_2_1",
            "severity": "BLOCKING",
            "requirement": "Remark structure",
            "check_block": {
                "data_source": "in_report",
                "where": ["report.global_remark"],
                "when": None,
                "check": 'extract("Does the remark explain defects by PO?")',
            },
        }
        spec = compile_checkpoint(cp)
        self.assertEqual(spec["tier"], "atoms")

    def test_compile_all_ribkoff_checkpoints(self):
        cps_path = ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json"
        checkpoints = load_checkpoints(cps_path)
        compiled = resolve_specs(checkpoints, checkpoints_path=cps_path)
        self.assertEqual(len(compiled), len(checkpoints))
        tiers = {s["tier"] for s in compiled.values()}
        self.assertTrue(tiers <= {"deterministic", "atoms", "vision", "mixed"})


if __name__ == "__main__":
    unittest.main()
