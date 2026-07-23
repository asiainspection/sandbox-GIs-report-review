"""Unit tests for report-team findings Excel wording."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from findings_export import (  # noqa: E402
    MANUAL_ATTACHMENT_ACTION,
    MANUAL_PHOTO_ACTION,
    WHAT_WAS_CHECKED,
    WHAT_WAS_CHECKED_UNABLE,
    checkpoint_column,
    checkpoint_meta_by_id,
    flag_rows_for_order,
    non_conformity,
    original_content,
    pending_media_kind,
    suggested_actions,
)


class FindingsExportWordingTests(unittest.TestCase):
    def test_carton_drop_photo_flag_is_short_and_clear(self) -> None:
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "3_1_6",
                    "requirement": (
                        "Carton drop test — Product Specifications checklist / report photos — "
                        "Photos of the carton drop test must NOT be included unless the test fails."
                    ),
                    "check_block": {"where": ["checklist.carton_drop_test.photo_count"]},
                    "fail_if": ["photo_count > 0 when PASS"],
                }
            ]
        )["3_1_6"]
        flag = {
            "checkpoint_id": "3_1_6",
            "evidence": "checklist.carton_drop_test.photo_count=2, max=0",
            "reason": "Report evidence violates this requirement.",
        }

        self.assertEqual(checkpoint_column(flag, meta), "Carton drop test")
        self.assertIn("2 photo", original_content(flag))
        nc = non_conformity(flag, meta)
        self.assertTrue(nc.startswith("Rules:"))
        self.assertIn("Inconsistency:", nc)
        self.assertIn("0 photos", nc)
        action = suggested_actions(flag, meta)
        self.assertTrue(action[0].isupper())
        self.assertIn("Remove", action)

        rows = flag_rows_for_order(
            order_id="Q1",
            flags=[flag],
            requirements={"3_1_6": meta["requirement"]},
            meta_by_id={"3_1_6": meta},
        )
        self.assertEqual(rows[0][3], WHAT_WAS_CHECKED)
        self.assertEqual(rows[0][4], "Carton drop test")
        self.assertLessEqual(len(rows[0][5]), 160)
        self.assertLessEqual(len(rows[0][7]), 120)

    def test_global_remark_action_is_verb_first(self) -> None:
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "1_2_1",
                    "requirement": (
                        "Inspector's Remark — report header summary — "
                        "Verify that a complete list of all defects found is provided by PO."
                    ),
                    "check_block": {"where": ["report.global_remark"]},
                }
            ]
        )["1_2_1"]
        flag = {
            "checkpoint_id": "1_2_1",
            "evidence": "report.global_remark blank=True",
        }
        self.assertEqual(checkpoint_column(flag, meta), "Inspector's Remark")
        self.assertIn("(blank)", original_content(flag))
        self.assertTrue(suggested_actions(flag, meta).startswith("Add "))

    def test_pending_attachment_content_row(self) -> None:
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "5_1_2",
                    "requirement": (
                        "Product Dimensions Result — measurement chart (Excel attachment) — "
                        "Verify measurement sequence matches the POM template."
                    ),
                    "check_block": {
                        "where": ["checklist.product_dimensions_result.attachment_content"]
                    },
                }
            ]
        )["5_1_2"]
        spec = {
            "checkpoint_id": "5_1_2",
            "status_class": "pending",
            "data_source": "report_attachments",
            "pending_processor": "xlsx",
            "requirement": meta["requirement"],
            "where_bindings": [
                {
                    "type": "selector",
                    "selector": "checklist.product_dimensions_result.attachment_content",
                }
            ],
        }
        self.assertEqual(pending_media_kind(spec), "attachment")
        report = {
            "result": {
                "steps": [
                    {
                        "actions": [
                            {
                                "testsChecklist": {
                                    "content": {
                                        "elements": [
                                            {
                                                "name": "Product Dimensions Result",
                                                "attachments": [
                                                    {"name": "Measurement Chart-271904.xlsx"}
                                                ],
                                                "images": [],
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        rows = flag_rows_for_order(
            order_id="Q9",
            flags=[],
            requirements={},
            meta_by_id={"5_1_2": meta},
            report=report,
            specs_by_id={"5_1_2": spec},
            include_unable_media=True,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], WHAT_WAS_CHECKED_UNABLE)
        self.assertTrue(str(rows[0][4]).startswith("Attachment:"))
        self.assertIn("Measurement Chart-271904.xlsx", str(rows[0][5]))
        self.assertIn("Verify measurement sequence", str(rows[0][6]))
        self.assertEqual(rows[0][7], MANUAL_ATTACHMENT_ACTION)

    def test_out_of_report_not_emitted(self) -> None:
        spec = {
            "checkpoint_id": "1_1_2",
            "status_class": "advisory",
            "data_source": "out_of_report",
            "where_bindings": [{"type": "out_of_report", "kind": "booking"}],
            "requirement": "Match booking address",
        }
        self.assertIsNone(pending_media_kind(spec))
        rows = flag_rows_for_order(
            order_id="Q9",
            flags=[],
            requirements={},
            meta_by_id={},
            report={},
            specs_by_id={"1_1_2": spec},
        )
        self.assertEqual(rows, [])

    def test_pending_photo_content_row(self) -> None:
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "5_2_3",
                    "requirement": (
                        "Ironing, washing, treatment check — Tests checklist / report photos — "
                        "Include clear photos of ironing and washing treatment."
                    ),
                    "check_block": {
                        "where": [
                            {
                                "kind": "checklist",
                                "match": ["ironing", "washing"],
                                "field": "photo_content",
                            }
                        ]
                    },
                }
            ]
        )["5_2_3"]
        spec = {
            "status_class": "pending",
            "data_source": "report_images",
            "pending_processor": "vision",
            "requirement": meta["requirement"],
            "where_bindings": [
                {
                    "type": "intent",
                    "kind": "checklist",
                    "match": ["ironing", "washing"],
                    "field": "photo_content",
                }
            ],
        }
        self.assertEqual(pending_media_kind(spec), "photo")
        report = {
            "result": {
                "steps": [
                    {
                        "actions": [
                            {
                                "testsChecklist": {
                                    "content": {
                                        "elements": [
                                            {
                                                "name": "Ironing washing treatment check",
                                                "images": [{"caption": "Front ironing view"}],
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        rows = flag_rows_for_order(
            order_id="Q2",
            flags=[],
            requirements={},
            meta_by_id={"5_2_3": meta},
            report=report,
            specs_by_id={"5_2_3": spec},
            include_unable_media=True,
        )
        self.assertEqual(rows[0][3], WHAT_WAS_CHECKED_UNABLE)
        self.assertTrue(str(rows[0][4]).startswith("Photo:"))
        self.assertIn("Front ironing view", str(rows[0][5]))
        self.assertEqual(rows[0][7], MANUAL_PHOTO_ACTION)


    def test_requirement_echo_suppressed_in_original_content(self) -> None:
        flag = {
            "checkpoint_id": "a_3_2",
            "evidence": "Requirement: Defects — All dirt/stain defects should be classified MAJOR",
        }
        text = original_content(flag)
        self.assertNotIn("Requirement:", text)
        self.assertNotIn("All dirt/stain", text)

    def test_unable_media_off_by_default(self) -> None:
        spec = {
            "checkpoint_id": "x",
            "status_class": "pending",
            "data_source": "report_attachments",
            "pending_processor": "xlsx",
            "requirement": "Check xlsx",
            "where_bindings": [
                {
                    "type": "intent",
                    "kind": "checklist",
                    "match": ["product", "dimensions"],
                    "field": "attachment_content",
                }
            ],
        }
        rows = flag_rows_for_order(
            order_id="Q1",
            flags=[],
            requirements={},
            meta_by_id={},
            report={"result": {"steps": []}},
            specs_by_id={"x": spec},
        )
        self.assertEqual(rows, [])

    def test_non_conformity_uses_enriched_snippet(self) -> None:
        flag = {
            "checkpoint_id": "3_1_6",
            "evidence": "checklist.carton_drop_test.photo_count=2, max=0",
        }
        meta = {"rule_short": "No photos when PASS", "fail_if": ["photo_count > 0 when PASS"]}
        snippet = 'Carton Drop Test: photos=2, captions=0, result=PASS'
        nc = non_conformity(flag, meta, snippet)
        self.assertIn(snippet, nc)
        self.assertNotIn("Carton Drop Test: 2 photo(s)", nc)

    def test_pending_skipped_when_locus_missing(self) -> None:
        spec = {
            "status_class": "pending",
            "data_source": "report_images",
            "pending_processor": "vision",
            "requirement": "Ironing check — photos must show treatment",
            "where_bindings": [
                {
                    "type": "intent",
                    "kind": "checklist",
                    "match": ["ironing", "washing"],
                    "field": "photo_content",
                }
            ],
        }
        report = {
            "result": {
                "steps": [
                    {
                        "actions": [
                            {
                                "testsChecklist": {
                                    "content": {
                                        "elements": [
                                            {
                                                "name": "Barcode scanning test",
                                                "images": [{"caption": "UPC scan"}],
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        rows = flag_rows_for_order(
            order_id="Q3",
            flags=[],
            requirements={},
            meta_by_id={},
            report=report,
            specs_by_id={"5_2_3": spec},
        )
        self.assertEqual(rows, [])

    def test_empty_where_does_not_scan_all_photos(self) -> None:
        from findings_export import media_asset_names

        report = {
            "result": {
                "steps": [
                    {
                        "actions": [
                            {
                                "testsChecklist": {
                                    "content": {
                                        "elements": [
                                            {
                                                "name": "Other test",
                                                "images": [{"caption": "Should not appear"}],
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        # report.* selector with no checklist targets must not harvest all photos
        names = media_asset_names(
            report,
            kind="photo",
            where=["report.inspector_text"],
        )
        self.assertEqual(names, [])

    def test_pending_when_false_skipped(self) -> None:
        from findings_export import _pending_when_applies

        spec = {
            "status_class": "pending",
            "data_source": "report_images",
            "pending_processor": "vision",
            "requirement": "Ironing — photos",
            "when": {
                "op": "equals",
                "ground": "json",
                "selector": "report.overall_result",
                "value": "PASS",
            },
            "where_bindings": [
                {
                    "type": "intent",
                    "kind": "checklist",
                    "match": ["ironing"],
                    "field": "photo_content",
                }
            ],
        }
        report = {
            "inspectionResult": "FAIL",
            "result": {
                "result": "FAIL",
                "steps": [
                    {
                        "actions": [
                            {
                                "testsChecklist": {
                                    "content": {
                                        "elements": [
                                            {
                                                "name": "Ironing check",
                                                "images": [{"caption": "iron view"}],
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
        }
        self.assertFalse(_pending_when_applies(spec, report))
        rows = flag_rows_for_order(
            order_id="Q4",
            flags=[],
            requirements={},
            meta_by_id={},
            report=report,
            specs_by_id={"x": spec},
        )
        self.assertEqual(rows, [])



    def test_atom_evidence_shows_quote_not_unavailable(self) -> None:
        """AI yes/no flags carry raw quotes — must surface as Original Content."""
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "a_1_1",
                    "requirement": "Factory address — must include postal code",
                    "check_block": {"where": ["report.factory_address"]},
                }
            ]
        )["a_1_1"]
        flag = {
            "checkpoint_id": "a_1_1",
            "evidence": "No. 89, South of Chunfeng Road, Yudu, China",
            "reason": "Report evidence violates this requirement.",
        }
        oc = original_content(flag)
        self.assertNotIn("unavailable", oc.lower())
        self.assertNotIn("bound field", oc.lower())
        self.assertIn("Chunfeng", oc)

    def test_blank_status_is_human_readable(self) -> None:
        oc = original_content(
            {"checkpoint_id": "a_9_2", "evidence": "required field blank"}
        )
        self.assertIn("not in the report", oc.lower())
        self.assertNotIn("bound field", oc.lower())
        self.assertNotIn("unavailable", oc.lower())

    def test_enrich_from_where_when_atom_evidence(self) -> None:
        meta = checkpoint_meta_by_id(
            [
                {
                    "id": "a_2_1",
                    "requirement": "Inspector remark — defects by PO",
                    "check_block": {"where": ["report.global_remark"]},
                }
            ]
        )["a_2_1"]
        report = {
            "result": {
                "globalRemark": {
                    "message": "1. packed. 2. PO 1: 2 defects. Total: 5%.",
                    "translations": {"en": {"message": "1. packed. 2. PO 1: 2 defects. Total: 5%."}},
                }
            }
        }
        rows = flag_rows_for_order(
            order_id="Qatom",
            flags=[
                {
                    "checkpoint_id": "a_2_1",
                    "evidence": "1. packed. 2. PO 1: 2 defects.",
                }
            ],
            requirements={"a_2_1": meta["requirement"]},
            meta_by_id={"a_2_1": meta},
            report=report,
        )
        self.assertNotIn("unavailable", str(rows[0][5]).lower())
        self.assertTrue("remark" in str(rows[0][5]).lower() or "PO" in str(rows[0][5]))


if __name__ == "__main__":
    unittest.main()
