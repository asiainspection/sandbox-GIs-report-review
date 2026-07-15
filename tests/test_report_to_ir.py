from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from report_to_ir import build_ir, dumps

REPORT = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"


def _load_ir() -> dict:
    return build_ir(json.loads(REPORT.read_text(encoding="utf-8")))


class ReportToIrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = _load_ir()

    def _node(self, needle: str) -> dict:
        matches = [n for n in self.ir["nodes"] if needle.lower() in n["path"].lower()]
        self.assertTrue(matches, f"node containing {needle!r} not found")
        return matches[0]

    def test_meta_has_cross_reference_fields(self) -> None:
        meta = self.ir["meta"]
        for key in ("report_id", "factory_address", "product", "inspection_result"):
            self.assertIn(key, meta)
        self.assertTrue(meta["factory_address"])

    def test_ir_preserves_facts_markdown_loses(self) -> None:
        # The 3_1_3 failure node: NOT_APPLICABLE but has photos + requires photo.
        node = self._node("Outer Packing & Shipping Marks")
        self.assertFalse(node["applicable"])
        self.assertEqual(node["result"], "NOT_APPLICABLE")
        self.assertTrue(node["requires_photo"])
        self.assertEqual(node["photos"]["count"], 9)
        self.assertEqual(node["photos"]["captions"], [])

    def test_per_photo_captions_are_kept(self) -> None:
        node = self._node("Product Style & Construction")
        self.assertGreater(node["photos"]["count"], 0)
        self.assertTrue(node["photos"]["captions"])

    def test_summary_carries_cross_report_facts(self) -> None:
        # Facts that live outside checklist nodes but cross-report checks need.
        summary = self.ir["summary"]
        self.assertTrue(summary["quantities"])
        self.assertIn("ordered", summary["quantities"][0])
        self.assertTrue(summary["inspector_instructions"])

    def test_aql_level_is_distinct_from_acceptance_point(self) -> None:
        # Regression for the 7_1_1 false flag: the AQL *level* (Major 2.5, Minor 4.0)
        # must not be confused with the acceptance point (Major 5) — the max defects
        # allowed for the sample size.
        aql = self.ir["summary"]["aql"]
        self.assertEqual(aql["aql_level_major"], "2.5")
        self.assertEqual(aql["aql_level_minor"], "4.0")
        self.assertEqual(aql["aql_level_critical"], "not-allowed")
        self.assertEqual(aql["acceptance_major"], 5)  # acceptance point, NOT the AQL
        self.assertEqual(aql["measurement_aql"], "AQL_4_0")

    def test_quantities_use_actual_onsite_not_expected_threshold(self) -> None:
        # Regression: *_actual must be the ACTUAL on-site counts (519), not the
        # expected targets (produced 506 / packed 404 = 80% threshold), which
        # used to trigger a false "packed < 80% of ordered" flag.
        q = self.ir["summary"]["quantities"][0]
        self.assertEqual(q["ordered"], "506")
        self.assertEqual(q["produced_actual"], "519")
        self.assertEqual(q["packed_actual"], "519")
        self.assertEqual(q["produced_expected"], "506")
        self.assertEqual(q["packed_expected"], "404")

    def test_ir_carries_no_precomputed_judgments(self) -> None:
        # Facts, not judgments: the IR summary must not ship checkpoint outcomes
        # (the old attention_items). The check engine derives verdicts from facts.
        self.assertNotIn("attention_items", self.ir["summary"])

    def test_question_node_surfaces_answer_not_no_result(self) -> None:
        from report_to_ir import render_node

        node = self._node("same as booked")
        self.assertEqual(node["result"], "NO_RESULT")
        self.assertEqual(node["values"], ["Yes"])
        rendered = render_node(node)
        self.assertIn("answer=Yes", rendered)
        self.assertNotIn("result=NO_RESULT", rendered)

    def test_ir_is_smaller_than_markdown(self) -> None:
        ir_chars = len(dumps(self.ir))
        md_chars = len((ROOT / "data/pipeline/reports/Q2614146161_llm.md").read_text())
        self.assertLess(ir_chars, md_chars)


if __name__ == "__main__":
    unittest.main()
