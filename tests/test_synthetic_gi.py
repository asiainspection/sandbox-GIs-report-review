"""Synthetic GI fixture tests (DFI/Hallmark) for obligation engine."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checkspec import resolve_specs  # noqa: E402
from fact_index import build_fact_index  # noqa: E402
from gi_review import load_checkpoints  # noqa: E402
from obligation_eval import evaluate_obligation  # noqa: E402
from semantic_report import parse_semantic_report  # noqa: E402

HALLMARK_CPS = ROOT / "data/pipeline/checkpoints/hallmark_checkpoints.json"
DFI_CPS = ROOT / "data/pipeline/checkpoints/dfi_checkpoints.json"


class SyntheticGiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        script = ROOT / "scripts/make_synthetic_gi_reports.py"
        if script.exists():
            import subprocess

            subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT)

    def test_hallmark_deterministic_flawed_flags(self) -> None:
        flawed = ROOT / "data/clients/hallmark/synthetic/hallmark_flawed.json"
        if not flawed.exists():
            self.skipTest("run scripts/make_synthetic_gi_reports.py")
        report = json.loads(flawed.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        semantic = parse_semantic_report(report)
        checkpoints = load_checkpoints(HALLMARK_CPS)
        specs = resolve_specs(checkpoints, checkpoints_path=HALLMARK_CPS)
        spec = specs["9_2_6"]
        verdict = evaluate_obligation(spec, facts, semantic=semantic, atom_answers={})
        self.assertEqual(verdict.status, "violates")

    def test_dfi_carton_drop_deterministic_flags(self) -> None:
        flawed = ROOT / "data/clients/dfi/flawed/dfi_flawed.json"
        if not flawed.exists():
            self.skipTest("run scripts/make_synthetic_gi_reports.py")
        report = json.loads(flawed.read_text(encoding="utf-8"))
        facts = build_fact_index(report)
        semantic = parse_semantic_report(report)
        checkpoints = load_checkpoints(DFI_CPS)
        specs = resolve_specs(checkpoints, checkpoints_path=DFI_CPS)
        spec = specs["remarks.carton_drop_observation"]
        self.assertEqual(spec.get("tier"), "deterministic", spec)
        verdict = evaluate_obligation(spec, facts, semantic=semantic, atom_answers={})
        self.assertEqual(verdict.status, "violates")

        correct = ROOT / "data/clients/dfi/corrected/dfi_correct.json"
        report_ok = json.loads(correct.read_text(encoding="utf-8"))
        facts_ok = build_fact_index(report_ok)
        semantic_ok = parse_semantic_report(report_ok)
        verdict_ok = evaluate_obligation(spec, facts_ok, semantic=semantic_ok, atom_answers={})
        self.assertEqual(verdict_ok.status, "clear")


if __name__ == "__main__":
    unittest.main()
