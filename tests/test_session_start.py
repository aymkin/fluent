#!/usr/bin/env python3
"""
Tests for the SessionStart greeting (.claude/hooks/session-start.py): its review
line names today's round — at most the session cap — not the whole backlog.

Usage:
    python3 tests/test_session_start.py
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / ".claude" / "hooks" / "session-start.py"


class SessionStartReviewLineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-test-"))
        (self.tmp / "learner-profile.json").write_text(json.dumps({
            "learner": {"name": "Test", "target_language": "Dutch",
                        "current_level": "A2", "target_level": "A2"},
            "current_streak_days": 1,
        }))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _review_lines(self, due: int, later: int = 0) -> list:
        items = {f"due_{n}": {"due_date": "2026-07-01"} for n in range(due)}
        items.update({f"later_{n}": {"due_date": "2099-01-01"} for n in range(later)})
        (self.tmp / "spaced-repetition.json").write_text(json.dumps({"items": items}))
        env = os.environ.copy()
        env.pop("CLAUDE_PROJECT_DIR", None)
        env["FLUENT_DATA_DIR"] = str(self.tmp)
        proc = subprocess.run(["python3", str(HOOK)], input=b"", env=env,
                              capture_output=True)
        self.assertEqual(proc.returncode, 0, msg=f"stderr={proc.stderr!r}")
        return [l for l in proc.stdout.decode("utf-8").splitlines() if "📅" in l]

    def test_backlog_over_the_cap_shows_one_round(self):
        self.assertEqual(self._review_lines(due=12),
                         ["[Fluent] 📅 Today: 10 reviews (~10 min) — run /fluent-review"])

    def test_backlog_under_the_cap_shows_all_of_it(self):
        self.assertEqual(self._review_lines(due=3, later=2),
                         ["[Fluent] 📅 Today: 3 reviews (~3 min) — run /fluent-review"])

    def test_one_due_is_singular(self):
        self.assertEqual(self._review_lines(due=1),
                         ["[Fluent] 📅 Today: 1 review (~1 min) — run /fluent-review"])

    def test_nothing_due_prints_no_review_line(self):
        self.assertEqual(self._review_lines(due=0, later=2), [])


if __name__ == "__main__":
    unittest.main()
