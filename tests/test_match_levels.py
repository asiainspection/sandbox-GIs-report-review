from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gi_review import (  # noqa: E402
    MATCH_CLEAR,
    MATCH_CLEAR_UNMATCH,
    MATCH_PARTIAL,
    MATCH_UNABLE,
    match_to_violates,
    normalize_match,
)


class MatchLevelTests(unittest.TestCase):
    def test_normalize_aliases(self) -> None:
        self.assertEqual(normalize_match("clear_match"), MATCH_CLEAR)
        self.assertEqual(normalize_match("unable"), MATCH_UNABLE)

    def test_blocking_strict_partial(self) -> None:
        self.assertFalse(match_to_violates(MATCH_PARTIAL, "BLOCKING", strict_blocking=False))
        self.assertTrue(match_to_violates(MATCH_PARTIAL, "BLOCKING", strict_blocking=True))

    def test_minor_partial_not_flagged(self) -> None:
        self.assertFalse(match_to_violates(MATCH_PARTIAL, "MINOR"))

    def test_clear_unmatch_flags(self) -> None:
        self.assertTrue(match_to_violates(MATCH_CLEAR_UNMATCH, "BLOCKING"))


if __name__ == "__main__":
    unittest.main()
