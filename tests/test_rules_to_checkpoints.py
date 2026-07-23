from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from check_block import extract_check_blocks  # noqa: E402
from md_rules_to_json import parse_rules  # noqa: E402
from rules_to_checkpoints import rule_to_checkpoint, rules_to_checkpoints, severity_from_rule  # noqa: E402

# Legacy format (```check fences) lives in the pre-harness archive.
LEGACY_MD = ROOT / "data/clients/ribkoff/gi/_archive/rules_pre_harness_20260721.md"


class RulesToCheckpointsTests(unittest.TestCase):
    def test_rule_to_checkpoint_carries_check_block(self) -> None:
        parsed = parse_rules(LEGACY_MD.read_text(encoding="utf-8"))
        blocks = extract_check_blocks(LEGACY_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        checkpoint = rule_to_checkpoint(rule, check_blocks=blocks)
        self.assertIn("check_block", checkpoint)
        self.assertIsNotNone(checkpoint["check_block"].get("where"))

    def test_rules_to_checkpoints_count(self) -> None:
        parsed = parse_rules(LEGACY_MD.read_text(encoding="utf-8"))
        markdown = LEGACY_MD.read_text(encoding="utf-8")
        checkpoints = rules_to_checkpoints(parsed["rules"], markdown=markdown)
        self.assertEqual(len(checkpoints), len(parsed["rules"]))
        with_blocks = sum(1 for cp in checkpoints if cp.get("check_block"))
        self.assertGreaterEqual(with_blocks, 50)

    def test_rule_1_2_1_defaults_blocking_without_severity(self) -> None:
        checkpoint = rule_to_checkpoint(
            {
                "id": "1.2.1",
                "field_location": "Remarks",
                "what_to_check": "Check remarks",
            }
        )
        self.assertEqual(checkpoint["severity"], "BLOCKING")

    def test_severity_minor_preserved(self) -> None:
        self.assertEqual(severity_from_rule({"severity": "MINOR"}), "MINOR")


if __name__ == "__main__":
    unittest.main()
