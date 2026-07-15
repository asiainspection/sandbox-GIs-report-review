from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ir_checks import MATCH_UNABLE, build_checkpoint_context, deterministic_verdict, find_nodes

# Minimal IR fixture mirroring the real 3_1_3 node.
IR = {
    "meta": {"report_id": "Q1", "inspection_result": "PASS"},
    "summary": {
        "aql": {"major_allowed": 5, "minor_allowed": 7, "found_major": 4},
        "inspector_instructions": ["Take photos of the boxes on the pallets."],
    },
    "nodes": [
        {
            "path": "Product Packing & Packaging > Outer Packing & Shipping Marks: Front & Side",
            "section": "Product Packing & Packaging",
            "name": "Outer Packing & Shipping Marks: Front & Side",
            "type": "MULTIPLE_CHOICE",
            "result": "NOT_APPLICABLE",
            "applicable": False,
            "requires_photo": True,
            "photos": {"count": 9, "captions": []},
            "values": [],
            "comment": "No spec",
        },
        {
            "path": "General > SAP Group Number",
            "section": "General",
            "name": "SAP Group Number",
            "type": "TEXT",
            "result": "PASS",
            "applicable": True,
            "requires_photo": False,
            "photos": {"count": 0, "captions": []},
            "values": ["12345"],
            "comment": "",
        },
    ],
}


class FindNodesTests(unittest.TestCase):
    def test_binds_by_focus_term(self) -> None:
        nodes = find_nodes(IR, ["outer packing & shipping marks"])
        self.assertEqual(len(nodes), 1)
        self.assertIn("Outer Packing", nodes[0]["path"])

    def test_no_terms_returns_nothing(self) -> None:
        self.assertEqual(find_nodes(IR, []), [])


class DeterministicVerdictTests(unittest.TestCase):
    def test_photo_content_returns_unable_to_check(self) -> None:
        checkpoint = {
            "id": "3_1_3",
            "photo_check": "content",
            "focus_terms": ["Outer Packing & Shipping Marks"],
        }
        verdict = deterministic_verdict(checkpoint, IR)
        self.assertIsNotNone(verdict)
        self.assertEqual(verdict["match"], MATCH_UNABLE)
        # Evidence is grounded in the IR, not invented.
        self.assertIn("applicable=False", verdict["evidence"])
        self.assertIn("photos=9", verdict["evidence"])

    def test_non_photo_checkpoint_defers_to_llm(self) -> None:
        checkpoint = {"id": "1_2_1", "focus_terms": ["SAP Group Number"]}
        self.assertIsNone(deterministic_verdict(checkpoint, IR))

    def test_photo_metadata_checkpoint_defers_to_llm(self) -> None:
        # Only 'content' is auto-resolved today; 'metadata' is left for later primitives.
        checkpoint = {"id": "x", "photo_check": "metadata", "focus_terms": ["Outer Packing"]}
        self.assertIsNone(deterministic_verdict(checkpoint, IR))


class BuildCheckpointContextTests(unittest.TestCase):
    def test_scoped_check_is_node_focused_and_small(self) -> None:
        checkpoint = {
            "id": "3_1_3",
            "scope_type": "QUESTION",
            "focus_terms": ["Outer Packing & Shipping Marks"],
        }
        context = build_checkpoint_context(checkpoint, IR)
        # Bound to its own node; the model sees the typed applicable flag.
        self.assertIn("Outer Packing & Shipping Marks", context)
        self.assertIn("applicable=False", context)
        # Scoped checks drop the cross-report summary (AQL, instructions).
        self.assertNotIn("AQL", context)
        self.assertNotIn("Take photos of the boxes", context)
        self.assertNotIn("SAP Group Number", context)

    def test_full_report_check_carries_cross_report_facts(self) -> None:
        checkpoint = {"id": "7_1_1", "scope_type": "FULL REPORT", "focus_terms": []}
        context = build_checkpoint_context(checkpoint, IR)
        self.assertIn("AQL", context)
        self.assertIn("Take photos of the boxes", context)
        # And still has every node.
        self.assertIn("Outer Packing & Shipping Marks", context)
        self.assertIn("SAP Group Number", context)

    def test_scoped_check_falls_back_to_full_when_unbound(self) -> None:
        checkpoint = {"id": "x", "scope_type": "QUESTION", "focus_terms": ["nonexistent term"]}
        context = build_checkpoint_context(checkpoint, IR)
        self.assertIn("AQL", context)  # fell back to full context


if __name__ == "__main__":
    unittest.main()
