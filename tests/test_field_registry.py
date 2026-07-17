"""Tests for typed field registry derivation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from field_registry import (  # noqa: E402
    STATUS_ADVISORY,
    STATUS_CHECKABLE,
    STATUS_PENDING,
    STATUS_UNAUTHORED,
    STATUS_UNMAPPED,
    classify_selector,
    derive_data_source,
    derive_feasibility,
)
from fact_schema import normalize_where_bindings, parse_where_entry  # noqa: E402


class FieldRegistryTests(unittest.TestCase):
    def test_photo_count_is_report_content_now(self) -> None:
        fc = classify_selector("checklist.carton_drop_test.photo_count")
        self.assertEqual(fc.data_source, "report_content")
        self.assertEqual(fc.feasible, "now")

    def test_attachment_filenames_is_attachments(self) -> None:
        fc = classify_selector("checklist.product_dimensions_result.attachment_filenames")
        self.assertEqual(fc.data_source, "report_attachments")
        self.assertEqual(fc.feasible, "now")

    def test_photo_content_pending_vision(self) -> None:
        fc = classify_selector("checklist.carton_drop_test.photo_content")
        self.assertEqual(fc.data_source, "report_images")
        self.assertEqual(fc.feasible, "pending")
        self.assertEqual(fc.pending_processor, "vision")

    def test_attachment_content_pending_xlsx(self) -> None:
        fc = classify_selector("checklist.product_dimensions_result.attachment_content")
        self.assertEqual(fc.data_source, "report_attachments")
        self.assertEqual(fc.pending_processor, "xlsx")

    def test_out_of_report_parse(self) -> None:
        b = parse_where_entry("out_of_report:booking")
        self.assertEqual(b["type"], "out_of_report")
        self.assertEqual(b["kind"], "booking")
        ds = derive_data_source(normalize_where_bindings(["out_of_report:booking"]))
        self.assertEqual(ds, "out_of_report")

    def test_derive_checkable(self) -> None:
        d = derive_feasibility(
            normalize_where_bindings(["checklist.x.photo_count"]),
            has_check=True,
        )
        self.assertEqual(d["status_class"], STATUS_CHECKABLE)

    def test_derive_unauthored(self) -> None:
        d = derive_feasibility(
            normalize_where_bindings(["report.attachment_filenames"]),
            has_check=False,
        )
        self.assertEqual(d["status_class"], STATUS_UNAUTHORED)
        self.assertEqual(d["data_source"], "report_attachments")

    def test_derive_pending(self) -> None:
        d = derive_feasibility(
            normalize_where_bindings(["checklist.x.photo_content"]),
            has_check=False,
        )
        self.assertEqual(d["status_class"], STATUS_PENDING)
        self.assertEqual(d["pending_processor"], "vision")

    def test_derive_advisory_empty_where(self) -> None:
        d = derive_feasibility([], has_check=False, legacy_data_source="external")
        self.assertEqual(d["status_class"], STATUS_ADVISORY)
        self.assertEqual(d["data_source"], "out_of_report")

    def test_empty_where_is_unmapped_not_advisory(self) -> None:
        d = derive_feasibility([], has_check=False)
        self.assertEqual(d["status_class"], STATUS_UNMAPPED)
        self.assertEqual(d["data_source"], "report_content")

    def test_unmapped_marker(self) -> None:
        d = derive_feasibility(
            normalize_where_bindings(["unmapped"]),
            has_check=False,
        )
        self.assertEqual(d["status_class"], STATUS_UNMAPPED)


if __name__ == "__main__":
    unittest.main()
