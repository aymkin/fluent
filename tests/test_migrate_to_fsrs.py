#!/usr/bin/env python3
"""Run: python3 tests/test_migrate_to_fsrs.py"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))
import migrate_to_fsrs as m


class TestSeed(unittest.TestCase):
    def test_reviewed_card_seeded_from_interval(self):
        card = {"interval_days": 48, "easiness_factor": 2.5, "repetitions": 3}
        s, d = m.seed(card)
        self.assertAlmostEqual(s, 48.0, delta=0.5)
        self.assertGreaterEqual(d, 1.0)
        self.assertLessEqual(d, 10.0)

    def test_never_reviewed_card_stays_null(self):
        card = {"interval_days": 1, "easiness_factor": 2.5, "repetitions": 0}
        s, d = m.seed(card)
        self.assertIsNone(s)
        self.assertIsNone(d)


if __name__ == "__main__":
    unittest.main()
