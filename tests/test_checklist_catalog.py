"""Tests for checklist catalog grounding (Field/Location → real item names)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checklist_catalog import (  # noqa: E402
    ground_where,
    match_checklist_item,
    match_section,
    load_checklist_names,
    load_checklist_names_from_reports,
    intent_from_prose,
    resolve_locus,
)


class ChecklistCatalogTests(unittest.TestCase):
    def test_ribkoff_barcode_grounds(self) -> None:
        names = load_checklist_names_from_reports(ROOT, "ribkoff")
        self.assertIn("Barcode scanning test", names)
        hit = match_checklist_item(
            "Barcode scanning test — Tests checklist / report photos",
            names,
        )
        self.assertEqual(hit, "Barcode scanning test")

    def test_intent_from_prose_no_catalog(self) -> None:
        intent = intent_from_prose(
            "Barcode scanning test — Tests checklist / report photos",
            "Upload 1 photo per barcode type present on the product.",
            "photo_count",
        )
        self.assertEqual(intent["kind"], "checklist")
        self.assertEqual(intent["field"], "photo_count")
        self.assertIn("barcode", intent["match"])
        self.assertIn("scanning", intent["match"])

    def test_tests_checklist_maps_to_checkpoints(self) -> None:
        section = match_section(
            "Barcode scanning test — Tests checklist / report photos",
            ["Checkpoints", "Product Specifications"],
        )
        self.assertEqual(section, "Checkpoints")

    def test_ground_where_barcode_photo(self) -> None:
        where = ground_where(
            client="ribkoff",
            root=ROOT,
            field="Barcode scanning test — Tests checklist / report photos",
            what="Upload 1 photo per barcode type present on the product.",
            section_names=["Checkpoints"],
        )
        self.assertIsNotNone(where)
        assert where is not None
        self.assertEqual(where[0]["kind"], "checklist")
        self.assertEqual(where[0]["field"], "photo_count")
        self.assertIn("barcode", " ".join(where[0]["match"]))

    def test_ground_where_without_sample_reports(self) -> None:
        where = ground_where(
            client="_nonexistent_client_",
            root=ROOT,
            field="Barcode scanning test — Tests checklist / report photos",
            what="Upload 1 photo per barcode type.",
            section_names=[],
        )
        self.assertIsNotNone(where)
        assert where is not None
        self.assertEqual(where[0]["kind"], "checklist")
        self.assertIn("barcode", where[0]["match"])

    def test_symmetry_grounds(self) -> None:
        where = ground_where(
            client="ribkoff",
            root=ROOT,
            field="Symmetry check — Tests checklist / report photos",
            what="The result and a supporting photo must be present.",
            section_names=["Checkpoints"],
        )
        self.assertIsNotNone(where)
        assert where is not None
        self.assertEqual(where[0]["kind"], "checklist")
        self.assertIn("symmetry", " ".join(where[0]["match"]))


    def test_resolve_locus_never_empty(self) -> None:
        where = resolve_locus(
            client="ribkoff",
            root=ROOT,
            field="Care content label — language sequence",
            what="Misprinting or variation in the sequence of languages is not acceptable.",
            section_names=["Checkpoints"],
        )
        self.assertTrue(where)
        where2 = resolve_locus(
            client="dfi",
            root=ROOT,
            field="Location — Cover page, Inspection Details",
            what="The location field must be written entirely in English.",
            section_names=[],
        )
        self.assertEqual(where2, ["report.production_site"])

    def test_defect_locus(self) -> None:
        where = resolve_locus(
            client="ribkoff",
            root=ROOT,
            field="Defects checklist — Workmanship section",
            what="All dirt and stain defects must be classified as MAJOR.",
            section_names=["Checkpoints"],
        )
        self.assertEqual(where, ["report.defects"])


if __name__ == "__main__":
    unittest.main()
