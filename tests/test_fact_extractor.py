"""Tests for section-grouped atom extraction (no API calls)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fact_extractor import (  # noqa: E402
    ExtractItem,
    _parse_batch_response,
    group_extract_items,
    section_key_for_checkpoint,
)


class ExtractGroupingTests(unittest.TestCase):
    def test_section_key_from_md_sections(self) -> None:
        cp = {"id": "x", "md_sections": ["Workmanship"], "section": "Other"}
        self.assertEqual(section_key_for_checkpoint(cp), "Workmanship")

    def test_groups_by_section_and_caps_batch_size(self) -> None:
        cps = {
            "a": {"id": "a", "md_sections": ["Qty"], "section": "Qty"},
            "b": {"id": "b", "md_sections": ["Qty"], "section": "Qty"},
            "c": {"id": "c", "md_sections": ["AQL"], "section": "AQL"},
        }
        items = [
            ExtractItem("a:f1", "a", "f1", "q", "string", "ctx"),
            ExtractItem("a:f2", "a", "f2", "q", "string", "ctx"),
            ExtractItem("b:f3", "b", "f3", "q", "string", "ctx"),
            ExtractItem("c:f4", "c", "f4", "q", "string", "ctx"),
        ]
        batches = group_extract_items(items, cps, max_per_batch=2)
        self.assertEqual(len(batches), 3)
        sizes = sorted(len(b) for b in batches)
        self.assertEqual(sizes, [1, 1, 2])


class ParseBatchResponseTests(unittest.TestCase):
    def test_parses_clean_answers_array(self) -> None:
        raw = '{"answers": [{"id": "a", "value": true}]}'
        rows = _parse_batch_response(raw)
        self.assertEqual(rows[0]["id"], "a")
        self.assertTrue(rows[0]["value"])

    def test_tolerates_trailing_extra_json(self) -> None:
        raw = '{"answers": [{"id": "a", "value": false}]}\n{"extra": true}'
        rows = _parse_batch_response(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "a")

    def test_parses_fenced_json(self) -> None:
        raw = '```json\n{"answers": [{"id": "b", "value": true}]}\n```'
        rows = _parse_batch_response(raw)
        self.assertEqual(rows[0]["id"], "b")


if __name__ == "__main__":
    unittest.main()
