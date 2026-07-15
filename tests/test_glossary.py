from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gi_review import build_checkpoint_prompt
from glossary import format_glossary_block, load_glossary, match_terms, matched_glossary_for_checkpoint
from md_rules_to_json import normalize_severity, parse_rules
from rules_to_checkpoints import rule_to_checkpoint

V2_RULES_MD = ROOT / "data/clients/ribkoff/gi/rules.md"


class GlossaryTests(unittest.TestCase):
    def test_load_glossary(self) -> None:
        glossary = load_glossary()
        self.assertIn("AQL", glossary)
        self.assertLess(len(glossary["AQL"].split()), 8)

    def test_match_terms_longest_first(self) -> None:
        glossary = {
            "PO": "purchase order number",
            "Purchase Order": "purchase order number",
        }
        matched = match_terms("Verify PO number on label", glossary)
        self.assertIn("PO", matched)

    def test_matched_glossary_for_checkpoint(self) -> None:
        checkpoint = {
            "requirement": "Verify AQL and PO on carton",
            "fail_if": ["Wrong PO number"],
        }
        matched = matched_glossary_for_checkpoint(checkpoint, load_glossary())
        self.assertIn("AQL", matched)
        self.assertIn("PO", matched)
        block = format_glossary_block(matched)
        self.assertIn("Glossary (matched terms):", block)

    def test_build_checkpoint_prompt_includes_glossary_and_severity(self) -> None:
        parsed = parse_rules(V2_RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "1.2.1")
        checkpoint = rule_to_checkpoint(rule)
        glossary_block = format_glossary_block(matched_glossary_for_checkpoint(checkpoint, load_glossary()))
        prompt = build_checkpoint_prompt(checkpoint, glossary_block=glossary_block)

        self.assertEqual(checkpoint["severity"], "MINOR")
        self.assertIn("Match levels:", prompt)
        self.assertIn('"match":', prompt)

    def test_normalize_severity(self) -> None:
        self.assertEqual(normalize_severity("`BLOCKING`"), "BLOCKING")
        self.assertEqual(normalize_severity("`MINOR`"), "MINOR")
        self.assertEqual(normalize_severity("`⚠️ TO CONFIRM`"), "TO_CONFIRM")


if __name__ == "__main__":
    unittest.main()
