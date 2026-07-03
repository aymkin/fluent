#!/usr/bin/env python3
"""Numeric parity vs py-fsrs. Correctness gate. Run in the dev venv:
   ~/Projects/fluent/.devvenv/bin/python tests/test_fsrs_crosscheck.py

PINNED fsrs==6.3.1. py-fsrs's default `Scheduler` keeps new cards in a
"Learning" state with sub-day learning_steps (1min, 10min) and reviews a
lapsed card through "Relearning" sub-day steps too — neither of which this
stdlib port models, because `fsrs.schedule()`'s `item` only carries a
last-reviewed *date* (see fsrs.py's scope note). To compare like with like,
this test configures py-fsrs's Scheduler with empty learning_steps /
relearning_steps (every review then goes straight through the same
long-term stability/interval formulas fsrs.py ports) and disables interval
fuzzing (so both sides advance the clock by the same integer day count).
"""
import unittest
import importlib.util
from pathlib import Path

# Load our stdlib module under a private spec name (NOT registered as
# sys.modules["fsrs"]) so it can't collide with the pip-installed "fsrs"
# package imported below — both are named "fsrs", and a plain
# `sys.path.insert(...); import fsrs` would cache whichever loads first
# under the same sys.modules key, silently shadowing the other.
_HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
_spec = importlib.util.spec_from_file_location("_fsrs_hook", _HOOKS_DIR / "fsrs.py")
fsrs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fsrs)

try:
    from fsrs import Scheduler, Card, Rating  # pip-installed py-fsrs (dev venv only)
    from datetime import datetime, timezone

    HAVE_FSRS = True
except Exception:
    HAVE_FSRS = False


@unittest.skipUnless(HAVE_FSRS, "py-fsrs not installed (dev-only gate)")
class TestCrossCheck(unittest.TestCase):
    def test_sequences_match_pyfsrs(self):
        sched = Scheduler(
            desired_retention=fsrs.TARGET_RETENTION,
            learning_steps=(),
            relearning_steps=(),
            enable_fuzzing=False,
        )
        for seq in ([3, 3, 3], [3, 1, 3], [2, 3, 4], [4, 4, 1, 3]):
            card = Card()
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            item = {
                "stability": None,
                "difficulty": None,
                "last_reviewed": "2026-01-01",
            }
            t = "2026-01-01"
            for g in seq:
                card, _ = sched.review_card(card, Rating(g), now)
                out = fsrs.schedule(item, g, t, weights=list(sched.parameters))
                self.assertAlmostEqual(
                    out["stability"],
                    card.stability,
                    delta=max(card.stability * 0.02, 1e-6),
                )
                self.assertGreaterEqual(out["difficulty"], 1.0)
                self.assertLessEqual(out["difficulty"], 10.0)
                item = {
                    "stability": card.stability,
                    "difficulty": card.difficulty,
                    "last_reviewed": t,
                }
                now = card.due
                t = card.due.date().isoformat()


if __name__ == "__main__":
    unittest.main()
