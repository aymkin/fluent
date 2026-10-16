#!/usr/bin/env python3
"""Run: python3 tests/test_backfill_skill_scores.py"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "backfill_skill_scores.py"


def dump(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def databases(totals):
    """The three files holding these running totals: {tag: (sessions, exercises, correct, minutes)}."""
    return {
        "learner-profile.json": {"skills": {
            t: {"total_practice_time": m} for t, (n, e, c, m) in totals.items()}},
        "progress-db.json": {"skill_progress": {
            t: {"sessions": n, "exercises_completed": e, "correct_count": c}
            for t, (n, e, c, m) in totals.items()}},
        "mastery-db.json": {"skills": {
            t: {"total_practice_time": m, "practice_count": e} for t, (n, e, c, m) in totals.items()}},
    }


# Three sessions: 001 grammar 3/4 in 10 min; 002 reading 5/5 in 8 and grammar
# 1/2 in 4; 003 listening 9/10 in 20 — the last, so it ends at the live files.
BEFORE = {
    "session-001": {},
    "session-002": {"grammar": (1, 4, 3, 10)},
    "session-003": {"grammar": (2, 6, 4, 14), "reading": (1, 5, 5, 8)},
}
LIVE = {"grammar": (2, 6, 4, 14), "reading": (1, 5, 5, 8), "listening": (1, 10, 9, 20)}
BREAKDOWN = {
    "session-001": {"grammar": 0.75},
    "session-002": {"reading": 1.0, "grammar": 0.5},
    "session-003": {"listening": 0.9},
}
FILLED = {
    "session-001": {"grammar": {"exercises": 4, "correct": 3, "time_minutes": 10}},
    "session-002": {"reading": {"exercises": 5, "correct": 5, "time_minutes": 8},
                    "grammar": {"exercises": 2, "correct": 1, "time_minutes": 4}},
    "session-003": {"listening": {"exercises": 10, "correct": 9, "time_minutes": 20}},
}


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-backfill-"))
        self.data = self.tmp / "data"
        for sid, totals in BEFORE.items():
            self._write(self.data / ".backups" / f"pre-update-{sid}", databases(totals))
        self._write(self.data, databases(LIVE))
        self.log = {"sessions": [{"session_id": sid, "date": "2026-10-01", "score_breakdown": dict(b)}
                                 for sid, b in BREAKDOWN.items()],
                    "metadata": {"total_sessions": 3}}
        self._write(self.data, {"session-log.json": self.log})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, d: Path, files: dict):
        d.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (d / name).write_text(dump(data), encoding="utf-8")

    def _run(self, *args):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        env["FLUENT_DATA_DIR"] = str(self.data)
        proc = subprocess.run(["python3", str(SCRIPT), *args], env=env, cwd=str(self.tmp),
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        return proc.stdout

    def _records(self):
        log = json.loads((self.data / "session-log.json").read_text(encoding="utf-8"))
        return {s["session_id"]: s for s in log["sessions"]}

    def _snapshot(self):
        return {p.relative_to(self.data).as_posix(): p.read_bytes()
                for p in sorted(self.data.rglob("*")) if p.is_file()}

    def test_a_session_gets_what_its_update_added(self):
        self.assertIn("3 to fill: 3 match, 0 refused.", self._run("--write"))
        records = self._records()
        for sid, scores in FILLED.items():
            self.assertEqual(records[sid]["skill_scores"], scores)
        # In the order the session sent its skills, as update-db.py would have written them.
        self.assertEqual(list(records["session-002"]["skill_scores"]), ["reading", "grammar"])

    def test_shares_that_are_not_score_breakdown_are_refused(self):
        self.log["sessions"][1]["score_breakdown"]["grammar"] = 0.6
        self._write(self.data, {"session-log.json": self.log})
        out = self._run("--write")
        self.assertIn("REFUSED session-002", out)
        self.assertIn("3 to fill: 2 match, 1 refused.", out)
        records = self._records()
        self.assertNotIn("skill_scores", records["session-002"])
        self.assertEqual(records["session-003"]["skill_scores"], FILLED["session-003"])

    def test_minutes_mastery_db_does_not_agree_with_are_refused(self):
        mastery = databases(LIVE)["mastery-db.json"]
        mastery["skills"]["listening"]["total_practice_time"] = 21
        self._write(self.data, {"mastery-db.json": mastery})
        out = self._run()
        self.assertIn("REFUSED session-003: listening: 20 min and 10 exercises, mastery-db 21 min", out)
        self.assertIn("3 to fill: 2 match, 1 refused.", out)

    def test_a_missing_backup_refuses_both_sessions_it_bounds(self):
        shutil.rmtree(self.data / ".backups" / "pre-update-session-002")
        out = self._run()
        self.assertIn("REFUSED session-001", out)
        self.assertIn("REFUSED session-002", out)
        self.assertIn("3 to fill: 1 match, 2 refused.", out)

    def test_a_dry_run_writes_nothing(self):
        before = self._snapshot()
        self.assertIn("3 to fill: 3 match, 0 refused.", self._run())
        self.assertEqual(self._snapshot(), before)

    def test_writing_adds_the_key_and_nothing_else(self):
        before = self._snapshot()
        self._run("--write")
        after = self._snapshot()
        new = sorted({k.split("/")[1] for k in after if k.startswith(".backups/pre-backfill-")})
        self.assertEqual(len(new), 1)
        self.assertEqual(after[f".backups/{new[0]}/session-log.json"], before["session-log.json"])
        log = json.loads(after["session-log.json"])
        for s in log["sessions"]:
            s.pop("skill_scores")
        self.assertEqual(dump(log).encode(), before["session-log.json"])
        for name, data in before.items():
            if name != "session-log.json":
                self.assertEqual(after[name], data, msg=name)

    def test_a_second_run_changes_nothing(self):
        self._run("--write")
        before = self._snapshot()
        self.assertIn("0 to fill: 0 match, 0 refused.", self._run("--write"))
        self.assertEqual(self._snapshot(), before)

    def test_a_filled_record_stays_a_boundary(self):
        self.log["sessions"][1]["skill_scores"] = FILLED["session-002"]
        self._write(self.data, {"session-log.json": self.log})
        self.assertIn("2 to fill: 2 match, 0 refused.", self._run("--write"))
        records = self._records()
        self.assertEqual(records["session-001"]["skill_scores"], FILLED["session-001"])
        self.assertEqual(records["session-003"]["skill_scores"], FILLED["session-003"])


if __name__ == "__main__":
    unittest.main()
