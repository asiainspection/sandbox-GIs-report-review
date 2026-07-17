"""Tests for footer check-block compiler."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from check_block import compile_block, extract_check_blocks, parse_check_block_text, validate_block  # noqa: E402
from compiler import compile_checkpoint  # noqa: E402
from fact_index import build_fact_index  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation import validate_checkspec  # noqa: E402
from obligation_eval import evaluate_obligation  # noqa: E402
from primitives import PRIMITIVE_OPS  # noqa: E402
from checkspec import resolve_specs  # noqa: E402

RULES_MD = ROOT / "data/clients/ribkoff/gi/rules.md"
CPS = ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json"
FLAWED = ROOT / "data/clients/ribkoff/flawed/Q2614146161_flawed.json"
CORRECTED = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"


class CheckBlockCompilerTests(unittest.TestCase):
    def test_extract_blocks_from_rules_md(self) -> None:
        blocks = extract_check_blocks(RULES_MD.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(blocks), 50)
        self.assertIn("3_1_6", blocks)

    def test_carton_drop_compiles_deterministic(self) -> None:
        block = {
            "data_source": "in_report",
            "where": ["checklist.carton_drop_test.photo_count"],
            "when": "checklist.carton_drop_test.result equals PASS",
            "check": "count_at_most(0)",
        }
        cp = {"id": "3_1_6", "severity": "MINOR", "requirement": "No photos on pass"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["tier"], "deterministic")
        self.assertEqual(validate_checkspec(spec), [])

    def test_advisory_never_flags(self) -> None:
        block = {"data_source": "PO_booking", "where": [], "when": None, "check": None}
        cp = {"id": "1_1_2", "severity": "BLOCKING", "requirement": "booking"}
        spec = compile_block(cp, block)
        verdict = evaluate_obligation(spec, {}, atom_answers={})
        self.assertEqual(verdict.status, "advisory")

    def test_flawed_carton_drop_violates(self) -> None:
        report = json.loads(FLAWED.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        checkpoints = {cp["id"]: cp for cp in load_checkpoints(CPS)}
        spec = compile_checkpoint(checkpoints["3_1_6"])
        verdict = evaluate_obligation(spec, facts, atom_answers={})
        self.assertEqual(verdict.status, "violates")

    def test_corrected_carton_drop_clear(self) -> None:
        report = json.loads(CORRECTED.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        checkpoints = {cp["id"]: cp for cp in load_checkpoints(CPS)}
        spec = compile_checkpoint(checkpoints["3_1_6"])
        verdict = evaluate_obligation(spec, facts, atom_answers={})
        self.assertEqual(verdict.status, "clear")

    def test_ribkoff_checkpoints_compile_and_validate(self) -> None:
        checkpoints = load_checkpoints(CPS)
        compiled = resolve_specs(checkpoints, checkpoints_path=CPS)
        self.assertEqual(len(compiled), len(checkpoints))
        for cp_id, spec in compiled.items():
            errors = validate_checkspec(spec)
            self.assertEqual(errors, [], f"{cp_id}: {errors}")

    def test_extract_quote_plus_matches(self) -> None:
        block = {
            "data_source": "in_report",
            "where": ["checklist.adhesive_test.comment"],
            "when": None,
            "check": [
                'extract("Quote the tape model stated in this comment, or null")',
                'matches("3M ?(500|600P|810)")',
            ],
        }
        cp = {"id": "5_4_2", "severity": "BLOCKING", "requirement": "tape model"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["tier"], "atoms")
        then = spec["then"]
        self.assertEqual(then["op"], "all_of")
        quote = then["items"][0]
        consume = then["items"][1]
        self.assertEqual(quote["role"], "quote")
        self.assertEqual(quote["value_type"], "string")
        self.assertEqual(consume["op"], "matches")
        self.assertEqual(consume["selector"], f"atom.{quote['id']}")

    def test_extract_bool_is_required_true(self) -> None:
        block = {
            "data_source": "in_report",
            "where": ["checklist.adhesive_test.comment"],
            "when": None,
            "check": 'extract_bool("Does this comment name a 3M tape model?")',
        }
        cp = {"id": "5_4_2b", "severity": "BLOCKING", "requirement": "tape"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["then"]["role"], "required_true")
        self.assertEqual(spec["then"]["value_type"], "boolean")

        used_ops: set[str] = set()

        def walk(node: dict | None) -> None:
            if not node:
                return
            op = node.get("op")
            if op:
                used_ops.add(str(op))
            if op in ("all_of", "any_of"):
                for item in node.get("items") or []:
                    walk(item)
            elif op == "not":
                walk(node.get("item"))

        checkpoints = load_checkpoints(CPS)
        compiled = resolve_specs(checkpoints, checkpoints_path=CPS)
        for spec in compiled.values():
            for part in ("when", "unless", "then"):
                walk(spec.get(part))
        self.assertTrue(used_ops <= PRIMITIVE_OPS)

    def test_vague_extract_bool_becomes_advisory(self) -> None:
        block = {
            "data_source": "in_report",
            "where": ["checklist.adhesive_test.comment"],
            "when": None,
            "check": 'extract_bool("Is this checklist item correctly filled for the rule requirement?")',
        }
        cp = {"id": "x_1", "severity": "BLOCKING", "requirement": "test"}
        spec = compile_block(cp, block)
        self.assertEqual(spec.get("status_class"), "advisory")
        self.assertEqual(spec.get("advisory_reason"), "vague_llm_question")

    def test_intent_where_parses_and_compiles(self) -> None:
        text = """data_source: in_report
where:
  - kind: checklist
    match: [adhesive, rubbing]
    field: comment
when: null
check: extract("Quote the tape model, or null")
"""
        block = parse_check_block_text(text)
        self.assertIsInstance(block["where"][0], dict)
        cp = {"id": "5_4_2", "severity": "BLOCKING", "requirement": "tape model"}
        spec = compile_block(cp, block)
        self.assertEqual(spec.get("tier"), "atoms")
        self.assertIn("where_bindings", spec)
        then = spec["then"]
        quote = then["items"][0] if then.get("op") == "all_of" else then
        self.assertEqual(quote["role"], "quote")
        self.assertIn("requires_fields", quote)

    def test_validate_rejects_vague_question(self) -> None:
        block = {
            "data_source": "in_report",
            "where": ["report.global_remark"],
            "when": None,
            "check": 'extract_bool("Does the remark contain the evidence this rule requires?")',
        }
        errors = validate_block(block, checkpoint_id="1_1")
        self.assertTrue(any("vague" in e["message"].lower() for e in errors))

    def test_build_evidence_payload_uses_real_names(self) -> None:
        from fact_schema import ResolvedField, build_evidence_payload

        payload = build_evidence_payload(
            "Tape model required",
            [
                ResolvedField(
                    kind="checklist",
                    name="Adhesive Rubbing Test",
                    field="comment",
                    value="3M 810 applied",
                    selector="checklist.adhesive_rubbing_test.comment",
                )
            ],
        )
        self.assertIn("[checklist] Adhesive Rubbing Test", payload)
        self.assertIn('field: comment', payload)
        self.assertIn("3M 810 applied", payload)
        self.assertNotIn("checklist.adhesive_rubbing_test", payload)

    def test_data_source_derived_from_attachment_field(self) -> None:
        block = {
            "where": ["checklist.product_dimensions_result.attachment_filenames"],
            "when": None,
            "check": 'filename_matches("Measurement Chart-*.xlsx")',
        }
        cp = {"id": "5_1_1", "severity": "BLOCKING", "requirement": "chart name"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["status_class"], "checkable")
        self.assertEqual(spec["data_source"], "report_attachments")

    def test_unauthored_in_report_is_not_advisory(self) -> None:
        block = {
            "where": ["report.attachment_filenames"],
            "when": None,
            "check": None,
        }
        cp = {"id": "x_att", "severity": "MINOR", "requirement": "file must be attached"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["status_class"], "unauthored")
        self.assertEqual(spec["data_source"], "report_attachments")
        verdict = evaluate_obligation(spec, {}, atom_answers={})
        self.assertEqual(verdict.status, "advisory")
        self.assertEqual(verdict.source, "obligation:unauthored")

    def test_pending_photo_content(self) -> None:
        block = {
            "where": ["checklist.carton_drop_test.photo_content"],
            "when": None,
            "check": None,
        }
        cp = {"id": "x_vis", "severity": "MINOR", "requirement": "photo must show"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["status_class"], "pending")
        self.assertEqual(spec["data_source"], "report_images")
        self.assertEqual(spec["pending_processor"], "vision")
        verdict = evaluate_obligation(spec, {}, atom_answers={})
        self.assertEqual(verdict.status, "advisory")
        self.assertEqual(verdict.source, "obligation:pending")

    def test_out_of_report_marker(self) -> None:
        block = {
            "where": ["out_of_report:booking"],
            "when": None,
            "check": None,
        }
        cp = {"id": "1_1_2", "severity": "BLOCKING", "requirement": "booking"}
        spec = compile_block(cp, block)
        self.assertEqual(spec["status_class"], "advisory")
        self.assertEqual(spec["data_source"], "out_of_report")

    def test_validate_allows_missing_data_source(self) -> None:
        block = {
            "where": ["report.factory_address"],
            "when": None,
            "check": "no_language(chinese)",
        }
        errors = validate_block(block, checkpoint_id="1_1")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
