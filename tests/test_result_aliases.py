"""Result dropdown aliases + blank required-field semantics for AI yes/no."""

from __future__ import annotations

import unittest

from primitives import EvalContext, _norm_comparable, eval_predicate


class ResultAliasTests(unittest.TestCase):
    def test_norm_aliases(self) -> None:
        self.assertEqual(_norm_comparable("PASS"), "PASS")
        self.assertEqual(_norm_comparable("Passed"), "PASS")
        self.assertEqual(_norm_comparable("FAIL"), "FAIL")
        self.assertEqual(_norm_comparable("failed"), "FAIL")
        self.assertEqual(_norm_comparable("N/A"), "N/A")
        self.assertEqual(_norm_comparable("NOT_APPLICABLE"), "N/A")
        self.assertEqual(_norm_comparable("Not Applicable"), "N/A")
        self.assertEqual(_norm_comparable("Pending"), "PENDING")

    def test_in_set_accepts_not_applicable_as_na(self) -> None:
        node = {
            "op": "in_set",
            "selector": "x",
            "values": ["PASS", "FAIL", "N/A", "Pending"],
            "ground": "json",
        }
        ctx = EvalContext(facts={"x": "NOT_APPLICABLE"})
        self.assertTrue(eval_predicate(node, ctx).value)

    def test_in_set_rejects_na_when_not_allowed(self) -> None:
        node = {
            "op": "in_set",
            "selector": "x",
            "values": ["PASS", "FAIL", "Pending"],
            "ground": "json",
        }
        ctx = EvalContext(facts={"x": "NOT_APPLICABLE"})
        self.assertFalse(eval_predicate(node, ctx).value)

    def test_equals_passed_is_pass(self) -> None:
        node = {
            "op": "equals",
            "selector": "x",
            "expected": "PASS",
            "ground": "json",
        }
        ctx = EvalContext(facts={"x": "PASSED"})
        self.assertTrue(eval_predicate(node, ctx).value)


class BlankRequiredAtomTests(unittest.TestCase):
    def test_required_true_blank_field_fails(self) -> None:
        node = {
            "op": "atom",
            "id": "a_2_1",
            "role": "required_true",
            "requires_fields": [{"type": "selector", "selector": "report.global_remark"}],
            "ground": "atom",
        }
        ctx = EvalContext(facts={"report.global_remark": ""}, atom_answers={})
        result = eval_predicate(node, ctx)
        self.assertIs(result.value, False)
        self.assertIn("blank", result.evidence)


if __name__ == "__main__":
    unittest.main()
