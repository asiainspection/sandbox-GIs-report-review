"""Tests for GI compiler and CheckSpec validation across all three GIs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import load_hand_specs, resolve_specs  # noqa: E402
from compiler import compile_checkpoint  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation import validate_checkspec  # noqa: E402
from primitives import PRIMITIVE_OPS  # noqa: E402

GIs = [
    ("ribkoff", ROOT / "data/pipeline/checkpoints/ribkoff_checkpoints.json", ROOT / "data/clients/ribkoff/gi/hand_specs.json"),
    ("dfi", ROOT / "data/pipeline/checkpoints/dfi_checkpoints.json", None),
    ("hallmark", ROOT / "data/pipeline/checkpoints/hallmark_checkpoints.json", None),
]


class CompilerTests(unittest.TestCase):
    def test_operator_tier_becomes_deterministic_obligation(self) -> None:
        cp = {"id": "3_1_6", "severity": "BLOCKING", "requirement": "No photos on pass"}
        hand = load_hand_specs(ROOT / "data/clients/ribkoff/gi/hand_specs.json")["3_1_6"]
        spec = compile_checkpoint(cp, hand)
        self.assertEqual(spec["tier"], "deterministic")
        self.assertIn("then", spec)
        self.assertEqual(validate_checkspec(spec), [])

    def test_vision_tier_for_photo_content(self) -> None:
        cp = {
            "id": "3_1_3",
            "severity": "BLOCKING",
            "photo_check": "content",
            "requirement": "Photo must show defect",
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["tier"], "vision")

    def test_structured_fail_implies_overall(self) -> None:
        cp = {
            "id": "2_1_1",
            "severity": "BLOCKING",
            "focus_terms": ["SR Test Report Check"],
            "requirement": "SR checkpoint must be Passed. If not passed, overall result must be FAIL.",
            "fail_if": ["SR checkpoint = Failed; overall result = Pass"],
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["tier"], "deterministic")
        self.assertEqual(spec["source"], "checkpoint_fail_implies_overall")
        self.assertEqual(validate_checkspec(spec), [])

    def test_hclp_no_photos_gated(self) -> None:
        cp = {
            "id": "1_4_2",
            "severity": "BLOCKING",
            "focus_terms": ["All photo fields throughout the report"],
            "requirement": (
                "For HCLP products, the report must contain no product photos. "
                'Every image field must show a blank image with the remark "HCLP, no photo".'
            ),
            "fail_if": ["HCLP = Yes; report contains a photo of the retail product"],
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["source"], "hclp_no_product_photos")
        self.assertIsNotNone(spec.get("when"))
        self.assertEqual(spec["then"]["op"], "vision")
        self.assertEqual(validate_checkspec(spec), [])

    def test_destination_gated_yes_no(self) -> None:
        cp = {
            "id": "1_4_1",
            "severity": "BLOCKING",
            "focus_terms": [
                "High Attention Product (HA) field",
                "HCLP field (Document Availability checklist)",
            ],
            "requirement": (
                "If the order ships to USA Kansas City (KC), both HA and HCLP fields "
                "must be answered Yes or No. If the order does NOT ship to KC, both fields must be N/A."
            ),
            "fail_if": ["Destination = KC HKBO; HA field = N/A"],
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["source"], "destination_gated_yes_no")
        self.assertEqual(spec["when"]["selector"], "report.destinations")
        self.assertEqual(validate_checkspec(spec), [])

    def test_attachment_when_not_pass_not_ungated_photos(self) -> None:
        cp = {
            "id": "2_1_4",
            "severity": "BLOCKING",
            "focus_terms": ["SR Test Report Check (Document Availability checklist)"],
            "requirement": (
                "If SR report result shows a failure but the factory provides a Hallmark "
                "override email, the checkpoint is acceptable. The override email must be "
                "uploaded in the report."
            ),
            "fail_if": [
                "SR fails; factory mentions an override email but it is not uploaded in the report"
            ],
            "never_flag_if": [
                "SR report result shows a failure but the factory provides a Hallmark override "
                "email is not identified or mentioned in the report"
            ],
        }
        spec = compile_checkpoint(cp, None)
        self.assertEqual(spec["source"], "attachment_when_not_pass")
        self.assertEqual(spec["when"]["op"], "all_of")
        self.assertEqual(spec["then"]["op"], "count_at_least")
        self.assertEqual(validate_checkspec(spec), [])

    def test_fail_if_atoms_not_generic_violation_id(self) -> None:
        cp = {
            "id": "cover.po_number",
            "requirement": "If no PO on site, field must be N/A with no additional comment.",
            "fail_if": ["PO field blank", "PO field contains comment instead of N/A when PO not found"],
        }
        spec = compile_checkpoint(cp, None)
        then = spec["then"]
        # Prefer targeted fail_if atoms over a single *_violation id.
        self.assertNotEqual(then.get("id"), "cover.po_number_violation")
        self.assertEqual(validate_checkspec(spec), [])

    def test_all_three_gis_compile_and_validate(self) -> None:
        for name, cps_path, specs_path in GIs:
            checkpoints = load_checkpoints(cps_path)
            hand = load_hand_specs(specs_path) if specs_path else {}
            compiled = resolve_specs(checkpoints, hand_specs=hand, checkpoints_path=cps_path, hand_specs_path=specs_path)
            self.assertEqual(len(compiled), len(checkpoints), name)
            for cp_id, spec in compiled.items():
                errors = validate_checkspec(spec)
                self.assertEqual(errors, [], f"{name}/{cp_id}: {errors}")

    def test_vocab_bounded_across_all_gis(self) -> None:
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

        for name, cps_path, specs_path in GIs:
            checkpoints = load_checkpoints(cps_path)
            hand = load_hand_specs(specs_path) if specs_path else {}
            compiled = resolve_specs(checkpoints, hand_specs=hand, checkpoints_path=cps_path, hand_specs_path=specs_path)
            for spec in compiled.values():
                for part in ("when", "unless", "then"):
                    walk(spec.get(part))

        self.assertTrue(used_ops <= PRIMITIVE_OPS)
        self.assertLessEqual(len(used_ops), 20, f"too many primitives: {used_ops}")


if __name__ == "__main__":
    unittest.main()
