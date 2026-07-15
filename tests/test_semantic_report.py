"""Tests for PDF-aligned semantic report parsing."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic_report import parse_semantic_report, semantic_invariants

REPORT = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"
CONTRACTS = ROOT / "data/pipeline/eval/_archive_gi/pdf_contracts.json"


class SemanticReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.semantic = parse_semantic_report(self.report)
        self.contract = json.loads(CONTRACTS.read_text())["reports"]["Q2614146161"]

    def test_quantity_names_match_pdf(self) -> None:
        p = self.semantic.products[0]
        self.assertEqual(p.ordered_quantity, self.contract["ordered_quantity"])
        self.assertEqual(p.real_produced_quantity, self.contract["real_produced_quantity"])
        self.assertEqual(p.expected_produced_quantity, self.contract["expected_produced_quantity"])
        self.assertEqual(p.real_packed_quantity, self.contract["real_packed_quantity"])
        self.assertEqual(p.expected_packed_quantity, self.contract["expected_packed_quantity"])

    def test_real_packed_not_confused_with_expected(self) -> None:
        p = self.semantic.products[0]
        self.assertGreater(p.real_packed_quantity or 0, p.expected_packed_quantity or 0)

    def test_workmanship_aql_separated(self) -> None:
        w = self.semantic.workmanship
        self.assertIsNotNone(w)
        assert w is not None
        self.assertEqual(w.result, "PASS")
        self.assertEqual(w.aql_level_major, "2.5")
        self.assertEqual(w.max_defects_major, 5)
        self.assertEqual(w.found_major, 4.0)
        self.assertNotEqual(w.aql_level_major, str(w.max_defects_major))

    def test_checklist_by_name_lookup(self) -> None:
        item = self.semantic.get_checklist_item("Carton drop test")
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.result, "PASS")

    def test_no_parse_warnings_on_clean_report(self) -> None:
        self.assertEqual(semantic_invariants(self.semantic), [])

    def test_legacy_dict_aliases(self) -> None:
        leg = self.semantic.products[0].to_legacy_dict()
        self.assertEqual(leg["packed_actual"], "519")
        self.assertEqual(leg["packed_expected"], "404")


class Q2612918144SemanticTests(unittest.TestCase):
    def test_contract_quantities(self) -> None:
        path = ROOT / "data/pipeline/eval/_archive_gi/Q2612918144.json"
        if not path.exists():
            self.skipTest("Q2612918144.json not fetched")
        contract = json.loads(CONTRACTS.read_text(encoding="utf-8"))["reports"]["Q2612918144"]
        p = parse_semantic_report(json.loads(path.read_text(encoding="utf-8"))).products[0]
        self.assertEqual(p.ordered_quantity, contract["ordered_quantity"])
        self.assertEqual(p.real_packed_quantity, contract["real_packed_quantity"])
        self.assertEqual(p.expected_packed_quantity, contract["expected_packed_quantity"])


class AllRibkoffReportsTests(unittest.TestCase):
    def test_all_corrected_reports_pass_invariants(self) -> None:
        for path in sorted((ROOT / "data/clients/ribkoff/corrected").glob("Q*.json")):
            report = json.loads(path.read_text(encoding="utf-8"))
            semantic = parse_semantic_report(report)
            self.assertEqual(
                semantic.parse_warnings,
                [],
                f"{path.name}: {semantic.parse_warnings}",
            )


if __name__ == "__main__":
    unittest.main()
