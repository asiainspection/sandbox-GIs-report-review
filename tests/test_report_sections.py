from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gi_review import build_checkpoint_prompt
from md_rules_to_json import parse_rules
from report_sections import extract_focus_slice, split_report_blocks
from rules_to_checkpoints import rule_to_checkpoint

RULES_MD = ROOT / "data/clients/ribkoff/gi/rules.md"
FLAWED_MD = ROOT / "data/pipeline/reports/report_q2614146161_flawed.md"


class ReportSectionsTests(unittest.TestCase):
    def test_split_report_blocks_finds_checklist_sections(self) -> None:
        report_md = FLAWED_MD.read_text(encoding="utf-8")
        titles = [block.title for block in split_report_blocks(report_md)]
        self.assertIn("Checklist Sections", titles)
        self.assertIn("Joseph Ribkoff - Product Specifications - SL", titles)

    def test_question_scope_narrows_to_carton_drop_test(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        checkpoint = rule_to_checkpoint(rule)
        report_md = FLAWED_MD.read_text(encoding="utf-8")

        self.assertEqual(checkpoint["scope_type"], "QUESTION")
        focus = extract_focus_slice(report_md, checkpoint)
        self.assertIn("Carton drop test", focus)
        self.assertNotIn("Stitch density check", focus)

    def test_full_report_scope_returns_empty_focus(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "1.2.1")
        checkpoint = rule_to_checkpoint(rule)
        report_md = FLAWED_MD.read_text(encoding="utf-8")

        self.assertEqual(checkpoint["scope_type"], "FULL REPORT")
        self.assertEqual(extract_focus_slice(report_md, checkpoint), "")

    def test_build_checkpoint_prompt_includes_report_context(self) -> None:
        parsed = parse_rules(RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        checkpoint = rule_to_checkpoint(rule)
        context = "| Carton drop test | PASS | PASSED | — | 4 | — |"
        prompt = build_checkpoint_prompt(checkpoint, report_context=context)

        self.assertIn("REPORT EVIDENCE", prompt)
        self.assertIn("Carton drop test", prompt)


if __name__ == "__main__":
    unittest.main()
