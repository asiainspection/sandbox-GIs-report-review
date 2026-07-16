"""Tests for obligation model and evaluation."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compiler import compile_checkpoint  # noqa: E402
from fact_index import build_fact_index  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation import validate_checkspec  # noqa: E402
from obligation_eval import evaluate_obligation  # noqa: E402

CORRECTED = ROOT / "data/clients/ribkoff/corrected/Q2614146161.json"
FLAWED = ROOT / "data/clients/ribkoff/flawed/Q2614146161_flawed.json"
CPS = ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json"


class ObligationEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checkpoints = {cp["id"]: cp for cp in load_checkpoints(CPS)}

    def test_no_photos_when_pass_compiled(self) -> None:
        spec = compile_checkpoint(self.checkpoints["3_1_6"])
        self.assertEqual(validate_checkspec(spec), [])
        self.assertEqual(spec["tier"], "deterministic")

    def test_flawed_carton_drop_violates(self) -> None:
        report = json.loads(FLAWED.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        spec = compile_checkpoint(self.checkpoints["3_1_6"])
        verdict = evaluate_obligation(spec, facts, atom_answers={})
        self.assertEqual(verdict.status, "violates")

    def test_corrected_carton_drop_clear(self) -> None:
        report = json.loads(CORRECTED.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        spec = compile_checkpoint(self.checkpoints["3_1_6"])
        verdict = evaluate_obligation(spec, facts, atom_answers={})
        self.assertEqual(verdict.status, "clear")

    def test_flawed_injected_deterministic_errors(self) -> None:
        report = json.loads(FLAWED.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        should_flag = {"3_1_6", "3_1_7", "3_2_3", "5_2_1", "5_2_2", "5_1_1"}
        for cp_id in should_flag:
            spec = compile_checkpoint(self.checkpoints[cp_id])
            verdict = evaluate_obligation(spec, facts, atom_answers={})
            self.assertEqual(verdict.status, "violates", cp_id)


if __name__ == "__main__":
    unittest.main()
