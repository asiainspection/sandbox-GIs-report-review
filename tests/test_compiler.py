"""Tests for footer check-block compiler."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from check_block import compile_block, extract_check_blocks, validate_block  # noqa: E402
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

    def test_vocab_bounded(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
