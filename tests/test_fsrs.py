#!/usr/bin/env python3
"""Invariant tests for the stdlib FSRS-6 port. Run: python3 tests/test_fsrs.py"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))
import fsrs


class TestFsrsInvariants(unittest.TestCase):
    def test_retrievability_at_stability_is_target(self):
        # R(t=S) must equal the target retention (~0.90).
        self.assertAlmostEqual(fsrs.retrievability(10.0, 10.0), 0.90, places=2)

    def test_interval_equals_stability_at_target(self):
        self.assertAlmostEqual(fsrs.interval_from_stability(10.0), 10.0, delta=0.5)

    def test_good_review_grows_stability(self):
        item = {"stability": 10.0, "difficulty": 5.0, "last_reviewed": "2026-07-01"}
        out = fsrs.schedule(item, rating=3, today="2026-07-11")
        self.assertGreater(out["stability"], 10.0)
        self.assertGreaterEqual(out["interval_days"], 1)

    def test_again_shrinks_stability_and_short_interval(self):
        item = {"stability": 10.0, "difficulty": 5.0, "last_reviewed": "2026-07-01"}
        out = fsrs.schedule(item, rating=1, today="2026-07-11")
        self.assertLess(out["stability"], 10.0)
        self.assertEqual(out["interval_days"], 1)

    def test_difficulty_clamped(self):
        for g in (1, 2, 3, 4):
            item = {"stability": None, "difficulty": None, "last_reviewed": "2026-07-01"}
            out = fsrs.schedule(item, rating=g, today="2026-07-01")
            self.assertGreaterEqual(out["difficulty"], 1.0)
            self.assertLessEqual(out["difficulty"], 10.0)

    def test_new_card_initializes(self):
        item = {"stability": None, "difficulty": None, "last_reviewed": "2026-07-01"}
        out = fsrs.schedule(item, rating=3, today="2026-07-01")
        self.assertIsNotNone(out["stability"])
        # Note (brief Step 2): a new card's first-review interval is
        # max(1, round(interval(S0))), which for rating=3 rounds above 0, so
        # due_date is today+interval, not today itself.
        self.assertGreaterEqual(out["interval_days"], 1)

    def test_weights_are_used(self):
        item = {"stability": 10.0, "difficulty": 5.0, "last_reviewed": "2026-07-01"}
        base = fsrs.schedule(item, 3, "2026-07-11")
        bumped = list(fsrs.DEFAULT_W)
        bumped[8] += 0.5  # perturb a stability-growth weight
        alt = fsrs.schedule(item, 3, "2026-07-11", weights=bumped)
        self.assertNotAlmostEqual(base["stability"], alt["stability"], places=3)


if __name__ == "__main__":
    unittest.main()
