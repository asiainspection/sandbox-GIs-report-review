from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gi_review import build_checkpoint_prompt
from md_rules_to_json import parse_rules
from rules_to_checkpoints import (
    infer_never_flag_if,
    lookup_table_from_rule,
    rule_to_checkpoint,
    rules_to_checkpoints,
)

RULES_MD = ROOT / "data/clients/ribkoff/gi/rules.md"


class RulesToCheckpointsTests(unittest.TestCase):
    def test_rule_3_1_6_uses_rule_text_not_hardcoded_enrichment(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        checkpoint = rule_to_checkpoint(rule)

        self.assertEqual(checkpoint["scope_type"], "QUESTION")
        self.assertTrue(checkpoint["focus_terms"])
        self.assertIn("4 photos of cartons being dropped", checkpoint["fail_if"][0])
        self.assertTrue(
            any("unless the test fails" in item.lower() for item in checkpoint.get("never_flag_if", []))
        )

    def test_rule_5_2_6_infers_conditional_never_flag(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "5.2.6")
        never_flag = infer_never_flag_if(rule)

        self.assertTrue(
            any("leg twisting is identified" in item.lower() for item in never_flag)
        )

    def test_rule_7_1_2_includes_lookup_table_from_rules_md(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "7.1.2")
        checkpoint = rule_to_checkpoint(rule)

        self.assertIn("lookup_table", checkpoint)
        self.assertIn("Non-denim", checkpoint["lookup_table"])
        self.assertIn("Denim", checkpoint["lookup_table"])
        self.assertEqual(
            checkpoint["context"],
            "FULL REPORT — cross-check measurement sampling level and unit count against the above requirements",
        )
        self.assertIn("Denim pant inspection reports 13 units", checkpoint["fail_if"][0])

    def test_never_flag_if_parsed_from_rules_md_field(self) -> None:
        rule = {
            "id": "9.9.9",
            "field_location": "Test field",
            "what_to_check": "Check something",
            "never_flag_if": ["PASS with no contradicting evidence", "Rule not applicable to this product type"],
        }
        checkpoint = rule_to_checkpoint(rule)
        self.assertEqual(len(checkpoint["never_flag_if"]), 2)

    def test_all_table_rules_get_lookup_table(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        table_rule_ids = [rule["id"] for rule in parsed["rules"] if rule.get("tables")]
        checkpoints = {cp["source_rule_id"]: cp for cp in rules_to_checkpoints(parsed["rules"])}

        self.assertTrue(table_rule_ids)
        for rule_id in table_rule_ids:
            self.assertIn("lookup_table", checkpoints[rule_id], rule_id)
            self.assertTrue(checkpoints[rule_id]["lookup_table"].startswith("|"))

    def test_rule_1_2_1_defaults_blocking_without_severity(self) -> None:
        checkpoint = rule_to_checkpoint(
            {
                "id": "1.2.1",
                "field_location": "Remarks",
                "what_to_check": "Check remarks",
            }
        )
        self.assertEqual(checkpoint["severity"], "BLOCKING")

    def test_rule_3_1_6_photo_metadata(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        checkpoint = rule_to_checkpoint(rule)
        self.assertEqual(checkpoint.get("photo_check"), "metadata")

    def test_build_checkpoint_prompt_includes_reference_table(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "7.1.2")
        prompt = build_checkpoint_prompt(rule_to_checkpoint(rule))

        self.assertIn("Reference table:", prompt)
        self.assertIn("Match levels:", prompt)

    def test_lookup_table_from_rule_prefers_structured_tables(self) -> None:
        rule = {
            "additional_markdown": "| A | B |\n|---|---|\n| 1 | 2 |",
            "tables": [
                {
                    "headers": ["Product type", "Sampling level"],
                    "rows": [{"Product type": "Denim", "Sampling level": "S4"}],
                }
            ],
        }
        lookup = lookup_table_from_rule(rule)
        self.assertIn("Product type", lookup)
        self.assertIn("Denim", lookup)


if __name__ == "__main__":
    unittest.main()
