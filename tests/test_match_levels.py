from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gi_review import (
    MATCH_CLEAR,
    MATCH_CLEAR_UNMATCH,
    MATCH_PARTIAL,
    MATCH_UNABLE,
    build_checkpoint_prompt,
    match_to_violates,
    normalize_match,
    parse_checkpoint_response,
)
from md_rules_to_json import parse_rules
from rules_to_checkpoints import photo_check_from_rule, rule_to_checkpoint

V2_RULES_MD = ROOT / "data/clients/ribkoff/gi/rules.md"


class MatchLevelTests(unittest.TestCase):
    def test_normalize_match_aliases(self) -> None:
        self.assertEqual(normalize_match("clear_unmatch"), MATCH_CLEAR_UNMATCH)
        self.assertEqual(normalize_match("partial unmatch"), MATCH_PARTIAL)
        self.assertEqual(normalize_match("unable_to_check"), MATCH_UNABLE)

    def test_minor_flags_only_clear_unmatch(self) -> None:
        self.assertTrue(match_to_violates(MATCH_CLEAR_UNMATCH, "MINOR"))
        self.assertFalse(match_to_violates(MATCH_PARTIAL, "MINOR"))
        self.assertFalse(match_to_violates(MATCH_UNABLE, "MINOR"))

    def test_blocking_flags_clear_unmatch(self) -> None:
        self.assertTrue(match_to_violates(MATCH_CLEAR_UNMATCH, "BLOCKING"))
        self.assertFalse(match_to_violates(MATCH_PARTIAL, "BLOCKING"))
        self.assertFalse(match_to_violates(MATCH_UNABLE, "BLOCKING"))

    def test_strict_blocking_includes_partial(self) -> None:
        self.assertTrue(match_to_violates(MATCH_PARTIAL, "BLOCKING", strict_blocking=True))

    def test_parse_legacy_violates_response(self) -> None:
        parsed = parse_checkpoint_response('{"violates": true, "reason": "x", "evidence": "y"}')
        self.assertEqual(parsed["match"], MATCH_CLEAR_UNMATCH)

    def test_parse_match_response(self) -> None:
        parsed = parse_checkpoint_response(
            '{"match": "unable_to_check", "reason": "no images", "evidence": ""}'
        )
        self.assertEqual(parsed["match"], MATCH_UNABLE)

    def test_photo_metadata_rule_3_1_6(self) -> None:
        parsed = parse_rules(V2_RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.6")
        self.assertEqual(photo_check_from_rule(rule), "metadata")
        prompt = build_checkpoint_prompt(rule_to_checkpoint(rule))
        self.assertIn("PHOTO METADATA", prompt)
        self.assertIn("unable_to_check", prompt)

    def test_photo_content_rule_3_1_7(self) -> None:
        parsed = parse_rules(V2_RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "3.1.7")
        self.assertEqual(photo_check_from_rule(rule), "content")
        prompt = build_checkpoint_prompt(rule_to_checkpoint(rule))
        self.assertIn("PHOTO CONTENT", prompt)
        self.assertIn("Do NOT infer photo content from count alone", prompt)

    def test_prompt_has_not_applicable_guardrail(self) -> None:
        parsed = parse_rules(V2_RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "1.2.1")
        prompt = build_checkpoint_prompt(rule_to_checkpoint(rule))
        self.assertIn("NOT_APPLICABLE", prompt)
        self.assertIn("Do NOT treat NOT_APPLICABLE as a", prompt)

    def test_prompt_uses_match_json_not_violates(self) -> None:
        parsed = parse_rules(V2_RULES_MD.read_text(encoding="utf-8"))
        rule = next(item for item in parsed["rules"] if item["id"] == "1.2.1")
        prompt = build_checkpoint_prompt(rule_to_checkpoint(rule))
        self.assertIn('"match":', prompt)
        self.assertNotIn("SEVERITY:", prompt)
        self.assertNotIn('"violates":', prompt)


if __name__ == "__main__":
    unittest.main()
