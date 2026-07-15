"""Contract tests for the IR: synthetic fixtures + the invariant suite.

Fixtures, not live vibes: instead of eyeballing real reports, we build minimal
QIMAone-shaped payloads for the scenarios that historically broke the parser
(over-pack, under-pack, missing on-site counts, level/acceptance conflation) and
assert the IR states the facts a reviewer would read from the PDF.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from report_to_ir import build_ir, ir_invariants


def make_report(
    *,
    ordered: int = 500,
    produced_expected: int = 500,
    packed_expected: int = 400,
    onsite_produced: int | None = 519,
    onsite_packed: int | None = 519,
    aql_levels: dict | None = None,
    acceptance: dict | None = None,
    found: dict | None = None,
    workmanship_result: str = "PASS",
) -> dict:
    """A minimal report payload exercising quantity + AQL extraction."""
    actions: list[dict] = []
    if onsite_produced is not None or onsite_packed is not None:
        actions.append(
            {
                "type": "INSPECTION_PREPARATION",
                "productQuantities": [
                    {
                        "productId": "P1",
                        "purchaseOrderProductId": "PO1",
                        "produced": onsite_produced,
                        "packed": onsite_packed,
                    }
                ],
            }
        )
    return {
        "reportId": "R1",
        "products": [
            {
                "product": {"id": "P1", "description": "Widget", "specification": {"SKU": "SKU1"}},
                "purchaseOrder": {"reference": "PO-REF"},
                "purchaseOrderProductId": "PO1",
                "unit": "Pcs",
                "productQuantity": ordered,
                "producedQuantity": produced_expected,
                "packedQuantity": packed_expected,
            }
        ],
        "result": {
            "result": "PASS",
            "testsResult": "PASS",
            "aqlDefects": aql_levels or {"critical": "not-allowed", "major": "2.5", "minor": "4.0"},
            "samplingSize": {
                "inspectionLevel": "II",
                "majorSampleSize": 80,
                "minorSampleSize": 80,
            },
            "workmanship": [
                {
                    "result": workmanship_result,
                    "acceptableQualityLevel": acceptance or {"critical": 0, "major": 5, "minor": 7},
                    "totalDefectsFound": found or {"CRITICAL": 0, "MAJOR": 4, "MINOR": 0},
                }
            ],
            "steps": [{"actions": actions}],
        },
    }


class QuantityFactsTests(unittest.TestCase):
    def _qty(self, report: dict) -> dict:
        return build_ir(report)["summary"]["quantities"][0]

    def test_over_pack_actual_exceeds_expected(self) -> None:
        q = self._qty(make_report(packed_expected=400, onsite_packed=519))
        self.assertEqual(q["packed_actual"], "519")
        self.assertEqual(q["packed_expected"], "400")

    def test_under_pack_keeps_both_sources_no_silent_pick(self) -> None:
        q = self._qty(make_report(packed_expected=400, onsite_packed=250))
        self.assertEqual(q["packed_actual"], "250")
        self.assertEqual(q["packed_expected"], "400")

    def test_missing_onsite_leaves_actual_empty(self) -> None:
        # No silent fallback to the expected target.
        q = self._qty(make_report(onsite_produced=None, onsite_packed=None))
        self.assertEqual(q["packed_actual"], "")
        self.assertEqual(q["produced_actual"], "")
        self.assertEqual(q["packed_expected"], "400")


class InvariantSuiteTests(unittest.TestCase):
    def test_clean_report_has_no_violations(self) -> None:
        self.assertEqual(ir_invariants(build_ir(make_report())), [])

    def test_missing_onsite_is_flagged_untrusted(self) -> None:
        v = ir_invariants(build_ir(make_report(onsite_produced=None, onsite_packed=None)))
        self.assertTrue(any("no on-site actual counts" in x for x in v))

    def test_pass_with_found_over_acceptance_is_flagged(self) -> None:
        # Workmanship says PASS but 6 major defects > acceptance point 5 — impossible.
        v = ir_invariants(
            build_ir(make_report(found={"MAJOR": 6}, acceptance={"critical": 0, "major": 5, "minor": 7}))
        )
        self.assertTrue(any("found 6 > acceptance 5" in x for x in v))

    def test_level_equals_acceptance_is_flagged(self) -> None:
        # The exact 7_1_1 regression: AQL level extracted as the acceptance point.
        v = ir_invariants(
            build_ir(make_report(aql_levels={"critical": 0, "major": 5, "minor": 7}))
        )
        self.assertTrue(any("level == acceptance" in x for x in v))

    def test_labels_swapped_is_flagged(self) -> None:
        v = ir_invariants(build_ir(make_report(produced_expected=400, packed_expected=500)))
        self.assertTrue(any("labels likely swapped" in x for x in v))


class RealReportsSatisfyContractTests(unittest.TestCase):
    """The invariant suite is CI: every shipped report must pass it clean."""

    def test_corrected_reports_have_no_violations(self) -> None:
        import json

        reports = sorted((ROOT / "data/clients/ribkoff/corrected").glob("Q*.json"))
        reports = [p for p in reports if not p.stem.endswith("_ir")]
        self.assertTrue(reports, "no corrected reports found")
        for path in reports:
            ir = build_ir(json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(ir_invariants(ir), [], f"{path.name} violates the IR contract")


if __name__ == "__main__":
    unittest.main()
