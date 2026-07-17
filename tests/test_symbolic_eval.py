"""Tests for PolicyGuard symbolic evaluation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fact_extractor import AtomAnswer
from symbolic_eval import (
    MATCH_CLEAR,
    MATCH_CLEAR_UNMATCH,
    MATCH_UNABLE,
    evaluate_atoms,
    vision_verdict,
)


def _answer(item_id: str, value, evidence: str = "ev") -> AtomAnswer:
    return AtomAnswer(item_id=item_id, field=f"atom.{item_id}", value=value, evidence=evidence)


class SymbolicEvalTests(unittest.TestCase):
    def test_clear_when_no_violation(self):
        atoms = [{"id": "1_1_1_violation"}]
        answers = {"1_1_1_violation": _answer("1_1_1_violation", False)}
        verdict = evaluate_atoms("1_1_1", atoms, answers)
        self.assertEqual(verdict.match, MATCH_CLEAR)

    def test_flag_when_violation_true(self):
        atoms = [{"id": "2_1_1_violation"}]
        answers = {"2_1_1_violation": _answer("2_1_1_violation", True)}
        verdict = evaluate_atoms("2_1_1", atoms, answers)
        self.assertEqual(verdict.match, MATCH_CLEAR_UNMATCH)

    def test_excuse_overrides_violation(self):
        atoms = [{"id": "3_1_1_violation"}, {"id": "3_1_1_excuse_0"}]
        answers = {
            "3_1_1_violation": _answer("3_1_1_violation", True),
            "3_1_1_excuse_0": _answer("3_1_1_excuse_0", True),
        }
        verdict = evaluate_atoms("3_1_1", atoms, answers)
        self.assertEqual(verdict.match, MATCH_CLEAR)

    def test_unable_when_violation_unknown(self):
        atoms = [{"id": "4_1_1_violation"}]
        answers = {"4_1_1_violation": _answer("4_1_1_violation", None)}
        verdict = evaluate_atoms("4_1_1", atoms, answers)
        self.assertEqual(verdict.match, MATCH_UNABLE)

    def test_flag_when_violation_true_no_confidence(self):
        atoms = [{"id": "5_1_1_violation"}]
        answers = {"5_1_1_violation": _answer("5_1_1_violation", True)}
        verdict = evaluate_atoms("5_1_1", atoms, answers)
        self.assertEqual(verdict.match, MATCH_CLEAR_UNMATCH)

    def test_vision_deferred(self):
        verdict = vision_verdict("6_1_1")
        self.assertEqual(verdict.match, MATCH_UNABLE)
        self.assertIn("vision", verdict.reason.lower())


if __name__ == "__main__":
    unittest.main()
