#!/usr/bin/env python3
"""Run: python3 tests/test_optimize_weights.py  (no torch needed)"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))
import optimize_weights as o


def _sr(n_reviews):
    hist = [{"date": "2026-01-01", "quality": 5, "score": 0} for _ in range(n_reviews)]
    return {"items": {"c1": {"id": "c1", "review_history": hist}},
            "metadata": {"reviews_at_last_optimize": 0}}


class TestGuard(unittest.TestCase):
    def test_extract_maps_quality_not_score(self):
        sr = {"items": {"c1": {"id": "c1", "review_history": [
            {"date": "2026-01-01", "quality": 5, "score": 0},   # score 0 must be ignored
            {"date": "2026-01-02", "quality": 1, "score": 0},
        ]}}, "metadata": {}}
        logs, total = o.extract_logs(sr)
        self.assertEqual(total, 2)
        self.assertEqual([r[2] for r in logs], [4, 1])  # q5->Easy(4), q1->Again(1)

    def test_guard_blocks_below_400(self):
        self.assertFalse(o.should_optimize(165, {"reviews_at_last_optimize": 0}))

    def test_guard_blocks_when_too_few_new(self):
        self.assertFalse(o.should_optimize(420, {"reviews_at_last_optimize": 400}))

    def test_guard_allows_when_ready(self):
        self.assertTrue(o.should_optimize(460, {"reviews_at_last_optimize": 400}))

    def test_main_noops_below_threshold(self):
        # main() with today's real data must not raise and must return 0
        self.assertEqual(o.main(dry_data=_sr(165)), 0)


if __name__ == "__main__":
    unittest.main()
