from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gi_review import prepare_report_for_llm, strip_html_comments, strip_inspector_comments


class GiReviewSanitizeTests(unittest.TestCase):
    def test_strip_html_comments(self) -> None:
        text = "<!-- secret changelog -->\n# Report\nBody"
        self.assertEqual(strip_html_comments(text), "# Report\nBody")

    def test_strip_inspector_comments(self) -> None:
        text = "\n".join(
            [
                "| Item | Result | Value | Comment | Photos |",
                "| --- | --- | --- | --- | --- |",
                "| Stitch density | PASS | PASSED | 9 stitches | 1 |",
                "- Attention item: PASS (value: OK) — inspector wrote this",
                "Comment: should disappear",
            ]
        )
        cleaned = strip_inspector_comments(text)
        self.assertIn("| Stitch density | PASS | PASSED | — | 1 |", cleaned)
        self.assertNotIn("inspector wrote this", cleaned)
        self.assertNotIn("Comment:", cleaned)

    def test_prepare_report_for_llm(self) -> None:
        text = "<!-- eval -->\n| Item | Comment |\n| --- | --- |\n| A | note |\n"
        cleaned = prepare_report_for_llm(text)
        self.assertNotIn("eval", cleaned)
        self.assertIn("| A | — |", cleaned)


if __name__ == "__main__":
    unittest.main()
