"""Offline tests for photo ZIP indexing helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from photo_store import index_photos, normalize_photo_stem, photos_for_checkpoint  # noqa: E402


class PhotoStoreTests(unittest.TestCase):
    def test_normalize_strips_trailing_index(self) -> None:
        self.assertEqual(
            normalize_photo_stem("Test - Cartons before selection-1.jpeg"),
            normalize_photo_stem("Test - Cartons before selection"),
        )

    def test_index_and_match_focus_terms(self) -> None:
        tmp = ROOT / "data" / "cache" / "photos" / "_test_index"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "Carton Drop Test-1.jpg").write_bytes(b"fake")
        (tmp / "Other-2.png").write_bytes(b"fake")
        index = index_photos(tmp)
        self.assertIn(normalize_photo_stem("Carton Drop Test"), index)
        cp = {"id": "x", "focus_terms": ["Carton Drop Test"], "requirement": "Carton Drop Test — photos"}
        paths = photos_for_checkpoint(cp, index)
        self.assertTrue(paths)
        self.assertTrue(any("Carton" in p.name for p in paths))


if __name__ == "__main__":
    unittest.main()
