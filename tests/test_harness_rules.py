"""Tests for harness-format rules.md → checkpoints / check_blocks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from check_block import _compile_call, compile_block, extract_check_blocks, validate_block  # noqa: E402
from harness_rules import (  # noqa: E402
    action_to_check,
    block_to_check_block,
    is_harness_rules_markdown,
    parse_harness_rules,
    when_to_predicate,
    where_to_bindings,
)
from md_rules_to_json import parse_rules  # noqa: E402
from primitives import EvalContext, eval_predicate  # noqa: E402
from rules_to_checkpoints import rules_to_checkpoints  # noqa: E402

HARNESS_MD = ROOT / "data/clients/ribkoff/gi/rules.md"
LEGACY_MD = ROOT / "data/clients/ribkoff/gi/_archive/rules_pre_harness_20260721.md"


class HarnessRulesTests(unittest.TestCase):
    def test_detect_harness_vs_legacy(self) -> None:
        self.assertTrue(is_harness_rules_markdown(HARNESS_MD.read_text(encoding="utf-8")))
        self.assertFalse(is_harness_rules_markdown(LEGACY_MD.read_text(encoding="utf-8")))

    def test_parse_ribkoff_harness_count(self) -> None:
        parsed = parse_harness_rules(HARNESS_MD.read_text(encoding="utf-8"))
        self.assertGreaterEqual(parsed["rule_count"], 25)
        self.assertEqual(parsed["format"], "harness")
        self.assertIn("a_5_1", parsed["check_blocks"])

    def test_carton_drop_maps_deterministic(self) -> None:
        blocks = parse_harness_rules(HARNESS_MD.read_text(encoding="utf-8"))["check_blocks"]
        block = blocks["a_5_1"]
        self.assertEqual(block["check"], "count_at_most(0)")
        where = block["where"][0]
        self.assertEqual(where["kind"], "checklist")
        self.assertEqual(where["field"], "photo_count")
        self.assertIsNotNone(block["when"])

    def test_english_address(self) -> None:
        blocks = parse_harness_rules(HARNESS_MD.read_text(encoding="utf-8"))["check_blocks"]
        block = blocks["a_1_2"]
        self.assertEqual(block["where"], ["report.factory_address"])
        self.assertEqual(block["check"], "no_language(chinese)")

    def test_ratio_binds_two_fields(self) -> None:
        where = where_to_bindings("Packed quantity", action="ratio at least")
        self.assertEqual(
            where,
            [
                "product._first.real_packed_quantity",
                "product._first.ordered_quantity",
            ],
        )
        self.assertEqual(action_to_check("ratio at least", "0.8"), "ratio_at_least(0.8)")

    def test_photo_content_suffix(self) -> None:
        where = where_to_bindings("Stitch density check photo content")
        self.assertEqual(where[0]["field"], "photo_content")

    def test_build_checkpoints_end_to_end(self) -> None:
        markdown = HARNESS_MD.read_text(encoding="utf-8")
        parsed = parse_rules(markdown)
        blocks = extract_check_blocks(markdown)
        checkpoints = rules_to_checkpoints(parsed["rules"], check_blocks=blocks)
        self.assertEqual(len(checkpoints), parsed["rule_count"])
        with_blocks = sum(1 for cp in checkpoints if cp.get("check_block"))
        self.assertEqual(with_blocks, len(checkpoints))

        # Compiles without validate errors for deterministic carton-drop
        cp = next(c for c in checkpoints if c["id"] == "a_5_1")
        errs = validate_block(cp["check_block"], checkpoint_id=cp["id"])
        self.assertEqual(errs, [])
        spec = compile_block(cp, cp["check_block"])
        self.assertEqual(spec["status_class"], "checkable")


class WhenCompilationTests(unittest.TestCase):
    """When mirrors Where: <place> <comparator> <value>, no client keywords."""

    def test_empty_when_always_applies(self) -> None:
        self.assertIsNone(when_to_predicate("", ""))

    def test_structured_comparators(self) -> None:
        cases = {
            ("Overall result is FAIL", ""): 'report.overall_result equals "FAIL"',
            ("Workmanship result is not Passed", ""): "workmanship.result != Passed",
            ("Overall result is one of FAIL, N/A", ""): "report.overall_result in_set FAIL, N/A",
            ("Defects includes dirt", ""): 'defects_name_any("dirt")',
            ("Carton drop test photo count greater than 0", ""): "checklist.carton_drop_test.photo_count > 0",
            ("Inspection type is Pre-Shipment Inspection", ""): 'report.inspection_type equals "Pre-Shipment Inspection"',
        }
        for (when, where), expected in cases.items():
            self.assertEqual(when_to_predicate(when, where), expected, msg=when)

    def test_legacy_freetext_backcompat(self) -> None:
        # Frozen Ribkoff phrasings still compile (no hardcoded defect names in code).
        self.assertEqual(
            when_to_predicate("when untrimmed thread defects exist", ""),
            'defects_name_any("untrimmed", "thread")',
        )
        self.assertEqual(
            when_to_predicate("when dirt or stain defects exist", ""),
            'defects_name_any("dirt", "stain")',
        )
        self.assertEqual(when_to_predicate("when defects are found", ""), "report.defect_count > 0")
        self.assertEqual(
            when_to_predicate("when the drop test passed", "Carton drop test photo count"),
            "checklist.carton_drop_test.result equals PASS",
        )

    def test_unknown_when_skips_not_always(self) -> None:
        # Unrecognized WHEN must skip (false), never silently always-apply.
        self.assertEqual(when_to_predicate("some nonsense condition", ""), "false")
        self.assertEqual(
            when_to_predicate("when multiple colors or references have the same defect", ""),
            "false",
        )

    def test_all_outputs_parse_to_valid_nodes(self) -> None:
        samples = [
            ("Overall result is FAIL", ""),
            ("Overall result is one of FAIL, N/A", ""),
            ("Defects includes dirt", ""),
            ("Carton drop test photo count greater than 0", ""),
            ("when untrimmed thread defects exist", ""),
            ("when the test failed", "Carton drop test result"),
            ("some nonsense condition", ""),
        ]
        for when, where in samples:
            pred = when_to_predicate(when, where)
            if pred in (None, "null"):
                continue
            node = _compile_call(str(pred), [], "t.when", allow_field_refs=True)
            self.assertIn("op", node, msg=f"{when!r} -> {pred!r}")


class ForEachIteratorTests(unittest.TestCase):
    """`For each` compiles to an `each` node and evaluates per element."""

    def test_each_defect_compiles_to_each_node(self) -> None:
        block = {
            "id": "T.1",
            "check": "Every defect type should have at least 2 photos",
            "where": "Defect photo count",
            "action": "at least N photos",
            "param": "2",
            "for each": "each defect",
        }
        cb = block_to_check_block(block)
        self.assertEqual(cb["for_each"], "each defect")
        spec = compile_block({"id": "T.1", "requirement": "r"}, cb)
        self.assertEqual(spec["status_class"], "checkable")
        then = spec["then"]
        self.assertEqual(then["op"], "each")
        self.assertEqual(then["source"], "report.defects")
        self.assertEqual(then["item"]["op"], "count_at_least")
        self.assertEqual(then["item"]["selector"], "item.photo_count")

    def test_unsupported_iterator_is_advisory(self) -> None:
        block = {
            "id": "T.2",
            "check": "Every PO should have a label photo",
            "where": "Label photo count",
            "action": "at least N photos",
            "param": "1",
            "for each": "each PO",
        }
        spec = compile_block({"id": "T.2", "requirement": "r"}, block_to_check_block(block))
        self.assertEqual(spec["status_class"], "advisory")
        self.assertTrue(str(spec.get("advisory_reason", "")).startswith("iterator_not_supported"))

    def test_each_node_evaluates_per_element(self) -> None:
        node = {
            "op": "each",
            "source": "report.defects",
            "item": {"op": "count_at_least", "selector": "item.photo_count", "min": 2},
        }
        ok = eval_predicate(node, EvalContext(facts={"report.defects": [{"photo_count": 2}, {"photo_count": 5}]}))
        self.assertIs(ok.value, True)
        bad = eval_predicate(node, EvalContext(facts={"report.defects": [{"photo_count": 3}, {"photo_count": 1}]}))
        self.assertIs(bad.value, False)
        empty = eval_predicate(node, EvalContext(facts={"report.defects": []}))
        self.assertIs(empty.value, True)


class LinkedConditionWhenTests(unittest.TestCase):
    """Production Applies when: Condition rows + @C1 AND @C2."""

    def test_compound_condition_refs_compile(self) -> None:
        from excel_to_checkpoints import compile_excel_blocks

        blocks = [
            {
                "id": "C1",
                "row type": "Condition (hidden)",
                "section": "",
                "check": "PSI",
                "where": "Inspection type",
                "action": "equals",
                "param": "Pre-Shipment Inspection",
                "when": "",
                "for each": "",
                "example": "",
            },
            {
                "id": "C2",
                "row type": "Condition (hidden)",
                "section": "",
                "check": "FAIL",
                "where": "Overall result",
                "action": "equals",
                "param": "FAIL",
                "when": "",
                "for each": "",
                "example": "",
            },
            {
                "id": "X.1",
                "row type": "Rule",
                "section": "",
                "check": "remark filled",
                "where": "Inspector remark",
                "action": "is present",
                "param": "",
                "when": "@C1 AND @C2",
                "for each": "",
                "example": "",
            },
        ]
        rules, cbs = compile_excel_blocks(blocks)
        cps = rules_to_checkpoints(rules, check_blocks=cbs)
        spec = compile_block(cps[0], cps[0]["check_block"])
        self.assertEqual(spec["when"]["op"], "all_of")
        self.assertEqual(len(spec["when"]["items"]), 2)

    def test_free_prose_applies_when_rejected(self) -> None:
        from excel_to_checkpoints import _validate_applies_when

        with self.assertRaises(SystemExit):
            _validate_applies_when("A.2.1", "when defects are found")


class LegacyArchiveStillParses(unittest.TestCase):
    def test_legacy_archive_has_check_fences(self) -> None:
        markdown = LEGACY_MD.read_text(encoding="utf-8")
        parsed = parse_rules(markdown)
        blocks = extract_check_blocks(markdown)
        self.assertGreaterEqual(len(parsed["rules"]), 50)
        self.assertGreaterEqual(len(blocks), 50)


if __name__ == "__main__":
    unittest.main()
