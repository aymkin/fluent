#!/usr/bin/env python3
"""
Smoke test for .claude/hooks/read-db.py --review payload trimming.

Usage:
    python3 tests/test_read_db.py
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "read-db.py"


def make_fixtures(data_dir: Path):
    (data_dir / "learner-profile.json").write_text(json.dumps({
        "learner": {"name": "Test"},
        "last_updated": "2026-07-08",
        "current_streak_days": 3,
        "achievements": [{"id": "x", "name": "x", "earned_date": "2026-01-01"}],
        "skills": {"vocabulary": {"current_level": 1, "confidence": 60}},
    }))
    (data_dir / "progress-db.json").write_text(json.dumps({"overall_stats": {"x": 1}}))
    (data_dir / "mistakes-db.json").write_text(json.dumps({
        "metadata": {"total_patterns_tracked": 2},
        "error_patterns": {
            "grammar_referenced": {"category": "grammar", "frequency": 2},
            "grammar_unreferenced": {"category": "grammar", "frequency": 1},
        },
    }))
    (data_dir / "mastery-db.json").write_text(json.dumps({"skills": {"x": 1}}))
    (data_dir / "spaced-repetition.json").write_text(json.dumps({
        "metadata": {"algorithm": "FSRS-6", "total_items_tracked": 2},
        "review_queue": {"today": ["grammar_referenced", "vocab_due"], "tomorrow": [],
                         "this_week": [], "later": []},
        "items": {
            "grammar_referenced": {
                "id": "grammar_referenced", "type": "error_pattern",
                "content": "x", "answer": "y", "due_date": "2026-07-01",
                "priority": "high",
                "review_history": [{"date": "2026-06-01", "quality": 3, "score": 6}],
            },
            "vocab_due": {
                "id": "vocab_due", "type": "vocabulary",
                "content": "dag", "answer": "day", "due_date": "2026-07-01",
                "priority": "medium",
                "review_history": [{"date": "2026-06-01", "quality": 4, "score": 8}],
            },
        },
    }))
    (data_dir / "session-log.json").write_text(json.dumps({"sessions": []}))


class ReadDbReviewTrimTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-test-"))
        (self.tmp / "data").mkdir()
        make_fixtures(self.tmp / "data")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _subprocess_env(self):
        """Env for the script under test, with the data-dir overrides scrubbed.

        The fixtures live in ``<tmp>/data`` and the script finds them through the
        ``./data`` leg of ``fluent_paths.data_dir()``. An inherited
        ``FLUENT_DATA_DIR`` — or a ``CLAUDE_PROJECT_DIR`` whose ``data/`` holds a
        real ``learner-profile.json`` — outranks that leg, so the script would
        read (and write) a directory other than the one under test.
        """
        env = os.environ.copy()
        env.pop("FLUENT_DATA_DIR", None)
        env.pop("CLAUDE_PROJECT_DIR", None)
        return env

    def _run(self, *args):
        proc = subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=str(self.tmp),
            env=self._subprocess_env(),
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, msg=f"stderr={proc.stderr!r}")
        return json.loads(proc.stdout)

    def test_review_mode_drops_unused_fields(self):
        out = self._run("--review")

        self.assertNotIn("due_review_items", out["computed"])
        self.assertNotIn("review_queue_trimmed_to", out["computed"])

        profile = out["databases"]["learner_profile"]
        self.assertEqual(set(profile.keys()), {"learner", "current_streak_days"})
        self.assertEqual(profile["learner"]["name"], "Test")
        self.assertEqual(profile["current_streak_days"], 3)

        items = out["databases"]["spaced_repetition"]["items"]
        self.assertEqual(set(items.keys()), {"grammar_referenced", "vocab_due"})
        self.assertTrue(all("review_history" not in it for it in items.values()))

        patterns = out["databases"]["mistakes_db"]["error_patterns"]
        self.assertEqual(set(patterns.keys()), {"grammar_referenced"})

        self.assertEqual(out["databases"]["mastery_db"], {})
        self.assertEqual(out["databases"]["progress_db"], {})
        self.assertEqual(out["databases"]["session_log"], {})

    def test_plain_mode_still_has_due_reviews_count_only(self):
        out = self._run()
        self.assertNotIn("due_review_items", out["computed"])
        self.assertEqual(out["computed"]["due_reviews_count"], 2)
        # plain mode does not trim learner_profile
        self.assertIn("achievements", out["databases"]["learner_profile"])

    def test_review_round_serves_the_least_likely_recall_first(self):
        # review_queue.today is rebuilt only by update-db.py, so between sessions
        # it goes stale: here it misses a card that fell due since (fresh) and
        # still lists one reviewed after it was built (reviewed_since).
        # All reviewed cards were last seen on one day, so a lower stability
        # means a lower recall probability today, whatever today is.
        seen = "2026-06-01"
        items = {
            f"card_{n}": {"type": "error_pattern", "priority": "high",
                          "due_date": "2026-07-01", "last_reviewed": seen,
                          "stability": 10.0 + n}
            for n in range(1, 15)
        }
        items["vocab_faded"] = {"type": "vocabulary", "priority": "medium",
                                "due_date": "2026-07-15", "last_reviewed": seen,
                                "stability": 2.0}
        items["reviewed_since"] = {"type": "error_pattern", "priority": "critical",
                                   "due_date": "2099-01-01", "last_reviewed": seen,
                                   "stability": 1.0}
        items["fresh"] = {"type": "error_pattern", "priority": "high",
                          "due_date": "2026-07-20", "last_reviewed": "2026-07-19",
                          "stability": None}
        (self.tmp / "data" / "spaced-repetition.json").write_text(json.dumps({
            "daily_limits": {"review_items_per_day": 45},
            "review_queue": {"today": [iid for iid in items if iid != "fresh"],
                             "tomorrow": [], "this_week": [], "later": []},
            "items": items,
        }))

        out = self._run("--review")
        sr = out["databases"]["spaced_repetition"]
        served = sr["review_queue"]["today"]

        self.assertEqual(len(served), 15)           # the review round, not the session cap
        # never reviewed first, then the lowest recall — priority no longer leads
        self.assertEqual(served[:3], ["fresh", "vocab_faded", "card_1"])
        self.assertNotIn("card_14", served)         # the best-remembered due card waits
        self.assertNotIn("reviewed_since", served)  # no longer due
        self.assertEqual(set(sr["items"]), set(served))
        self.assertEqual((out["computed"]["session_cap"], out["computed"]["review_round"]),
                         (10, 15))

    def test_computed_fields_are_exactly_the_documented_six(self):
        # The skills advertise these and only these.
        self.assertEqual(
            set(self._run()["computed"]),
            {"today", "due_reviews_count", "next_session_id", "streak_active",
             "session_cap", "review_round"},
        )


if __name__ == "__main__":
    unittest.main()
