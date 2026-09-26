#!/usr/bin/env python3
"""
Tests for .claude/hooks/prompt_clock.py and the prompt-clock.py hook.

The library is exercised by direct import (it is a pure helper, like fsrs.py);
the hook is exercised by subprocess, because what is under test there is its
behaviour as a hook — that it stays silent and always exits 0.

Usage:
    python3 tests/test_prompt_clock.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS = REPO_ROOT / ".claude" / "hooks"
HOOK = HOOKS / "prompt-clock.py"

sys.path.insert(0, str(HOOKS))
import prompt_clock  # noqa: E402

SID = "aaaaaaaa-1111-2222-3333-444444444444"
OTHER_SID = "bbbbbbbb-5555-6666-7777-888888888888"


class PromptClockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-test-"))
        # The library resolves its path through fluent_paths on every call, so
        # pointing FLUENT_DATA_DIR at the temp dir is enough to keep the real
        # learner data out of reach. CLAUDE_PROJECT_DIR outranks nothing here —
        # FLUENT_DATA_DIR is the first leg — but it is scrubbed anyway, so a
        # failure to set the env var cannot silently fall through to it.
        self._saved = {k: os.environ.get(k) for k in ("FLUENT_DATA_DIR", "CLAUDE_PROJECT_DIR")}
        os.environ["FLUENT_DATA_DIR"] = str(self.tmp)
        os.environ.pop("CLAUDE_PROJECT_DIR", None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- helpers

    def _write(self, marks):
        """marks: list of (sid, datetime, is_command)."""
        path = self.tmp / prompt_clock.CLOCK_FILE
        with open(path, "w", encoding="utf-8") as f:
            for sid, ts, cmd in marks:
                line = {"sid": sid, "ts": ts.isoformat(timespec="seconds")}
                if cmd:
                    line["cmd"] = True
                f.write(json.dumps(line) + "\n")
        return path

    def _lines(self):
        path = self.tmp / prompt_clock.CLOCK_FILE
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    @staticmethod
    def _at(base, *offsets_min):
        return [base + timedelta(minutes=m) for m in offsets_min]

    # --- measured_minutes

    def test_no_file_is_none_not_zero(self):
        """An absent file means the hook is not installed. That has to be
        distinguishable from a session that was measured at zero, or a record
        written without the hook would claim a measurement it never had."""
        self.assertIsNone(prompt_clock.measured_minutes(SID))

    def test_single_mark_is_zero_not_none(self):
        now = datetime.now().astimezone()
        self._write([(SID, now, True)])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 0)

    def test_sums_only_gaps_within_the_cutoff(self):
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=60)
        # 0 →+3 →+3 (6 counted), then a 30-minute break, then +4 →+2 (6 counted).
        stamps = self._at(base, 0, 3, 6, 36, 40, 42)
        self._write([(SID, t, i == 0) for i, t in enumerate(stamps)])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 12)

    def test_gap_exactly_at_the_cutoff_counts(self):
        """The cutoff is the longest pause still treated as one sitting, so the
        boundary itself belongs to the session. Exclusive would make the
        threshold mean 4:59, which is not what the measurement was tuned on."""
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=30)
        stamps = self._at(base, 0, prompt_clock.PAUSE_CUTOFF_MIN)
        self._write([(SID, t, i == 0) for i, t in enumerate(stamps)])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), prompt_clock.PAUSE_CUTOFF_MIN)

    def test_a_gap_one_second_over_the_cutoff_is_dropped(self):
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=30)
        stamps = [base, base + timedelta(minutes=prompt_clock.PAUSE_CUTOFF_MIN, seconds=1)]
        self._write([(SID, t, i == 0) for i, t in enumerate(stamps)])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 0)

    def test_window_starts_at_the_last_command_mark(self):
        """A single Claude Code session can hold ordinary work before the study
        command. Everything before the last /fluent prompt is somebody else's."""
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=90)
        marks = [
            (SID, base, False),                              # ordinary work
            (SID, base + timedelta(minutes=2), False),       # still ordinary
            (SID, base + timedelta(minutes=60), True),       # /fluent-learn
            (SID, base + timedelta(minutes=63), False),
            (SID, base + timedelta(minutes=65), False),
        ]
        self._write(marks)
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 5)

    def test_without_a_command_mark_the_whole_session_counts(self):
        """A resumed session carries no /fluent prompt — the command was typed
        before the transcript this file knows about. It still called update-db,
        so it is a study session; measuring all of its marks is the best
        available answer, and better than reporting nothing."""
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=20)
        stamps = self._at(base, 0, 2, 4)
        self._write([(SID, t, False) for t in stamps])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 4)

    def test_another_session_is_not_counted(self):
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=30)
        self._write([
            (SID, base, True),
            (OTHER_SID, base + timedelta(minutes=1), False),
            (OTHER_SID, base + timedelta(minutes=2), False),
            (SID, base + timedelta(minutes=3), False),
        ])
        # The other session's two marks sit inside our window in wall-clock
        # terms; only our own two may contribute, and their gap is 3 minutes.
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 3)

    def test_marks_older_than_the_retention_window_are_ignored(self):
        now = datetime.now().astimezone()
        stale = now - timedelta(hours=prompt_clock.RETAIN_HOURS + 1)
        self._write([
            (SID, stale, True),
            (SID, stale + timedelta(minutes=3), False),
            (SID, now - timedelta(minutes=4), True),
            (SID, now - timedelta(minutes=1), False),
        ])
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 3)

    def test_a_corrupt_line_does_not_break_the_read(self):
        """An append interrupted mid-line leaves a partial record. Losing the
        measurement over it would be worse than losing the one mark."""
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=30)
        path = self._write([(SID, base, True), (SID, base + timedelta(minutes=3), False)])
        with open(path, "a", encoding="utf-8") as f:
            f.write('{"sid": "' + SID + '", "ts": "2026-0\n')
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sid": SID, "ts": (base + timedelta(minutes=5)).isoformat()}) + "\n")
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 5)

    def test_a_mark_without_a_usable_timestamp_is_skipped(self):
        now = datetime.now().astimezone()
        base = now - timedelta(minutes=30)
        path = self.tmp / prompt_clock.CLOCK_FILE
        path.write_text("\n".join([
            json.dumps({"sid": SID, "ts": base.isoformat(timespec="seconds"), "cmd": True}),
            json.dumps({"sid": SID}),
            json.dumps({"sid": SID, "ts": "not a date"}),
            json.dumps({"ts": base.isoformat(timespec="seconds")}),
            json.dumps({"sid": SID, "ts": (base + timedelta(minutes=2)).isoformat(timespec="seconds")}),
        ]) + "\n", encoding="utf-8")
        self.assertEqual(prompt_clock.measured_minutes(SID, now=now), 2)

    # --- record

    def test_record_appends_and_creates_the_data_dir(self):
        nested = self.tmp / "made-on-demand"
        os.environ["FLUENT_DATA_DIR"] = str(nested)
        prompt_clock.record(SID, is_command=True)
        prompt_clock.record(SID, is_command=False)
        lines = [json.loads(l) for l in
                 (nested / prompt_clock.CLOCK_FILE).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([l["sid"] for l in lines], [SID, SID])
        self.assertEqual([l.get("cmd") for l in lines], [True, None])
        for line in lines:
            datetime.fromisoformat(line["ts"])  # parses, and carries an offset
            self.assertIsNotNone(datetime.fromisoformat(line["ts"]).tzinfo)

    def test_record_without_a_sid_writes_nothing(self):
        prompt_clock.record("", is_command=False)
        prompt_clock.record(None, is_command=False)
        self.assertFalse((self.tmp / prompt_clock.CLOCK_FILE).exists())

    # --- prune

    def test_prune_drops_stale_lines_and_keeps_fresh_ones(self):
        now = datetime.now().astimezone()
        stale = now - timedelta(hours=prompt_clock.RETAIN_HOURS + 2)
        self._write([
            (SID, stale, True),
            (OTHER_SID, stale + timedelta(minutes=1), False),
            (SID, now - timedelta(minutes=2), True),
        ])
        prompt_clock.prune(now=now)
        kept = self._lines()
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["sid"], SID)

    def test_prune_on_a_missing_file_is_a_no_op(self):
        prompt_clock.prune()
        self.assertFalse((self.tmp / prompt_clock.CLOCK_FILE).exists())

    def test_prune_leaves_no_temp_file_behind(self):
        now = datetime.now().astimezone()
        self._write([(SID, now - timedelta(minutes=1), True)])
        prompt_clock.prune(now=now)
        leftovers = [p.name for p in self.tmp.iterdir() if p.name != prompt_clock.CLOCK_FILE]
        self.assertEqual(leftovers, [])


class PromptClockHookTest(unittest.TestCase):
    """The hook's contract as a hook: silent on stdout, always exit 0."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _env(self, **extra):
        env = os.environ.copy()
        env.pop("CLAUDE_PROJECT_DIR", None)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        env["FLUENT_DATA_DIR"] = str(self.tmp)
        env.update(extra)
        return env

    def _run(self, stdin: bytes, **env):
        return subprocess.run(
            ["python3", str(HOOK)],
            input=stdin, env=self._env(**env), capture_output=True,
        )

    def _lines(self):
        path = self.tmp / prompt_clock.CLOCK_FILE
        if not path.exists():
            return []
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_records_a_prompt_and_stays_silent(self):
        proc = self._run(json.dumps({"session_id": SID, "prompt": "Ik woon in Hilversum."}).encode())
        self.assertEqual(proc.returncode, 0)
        # A UserPromptSubmit hook's stdout is fed to the model, so anything
        # printed here would land in the learner's conversation.
        self.assertEqual(proc.stdout, b"")
        lines = self._lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["sid"], SID)
        self.assertNotIn("cmd", lines[0])

    def test_marks_a_fluent_command(self):
        self._run(json.dumps({"session_id": SID, "prompt": "  /fluent-learn"}).encode())
        self.assertIs(self._lines()[0]["cmd"], True)

    def test_another_slash_command_is_not_a_fluent_mark(self):
        self._run(json.dumps({"session_id": SID, "prompt": "/commit"}).encode())
        self.assertNotIn("cmd", self._lines()[0])

    def test_falls_back_to_the_session_id_from_the_environment(self):
        self._run(json.dumps({"prompt": "hallo"}).encode(), CLAUDE_CODE_SESSION_ID=OTHER_SID)
        self.assertEqual(self._lines()[0]["sid"], OTHER_SID)

    def test_malformed_stdin_exits_zero_and_writes_nothing(self):
        proc = self._run(b"not json at all")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(self._lines(), [])

    def test_empty_stdin_exits_zero(self):
        proc = self._run(b"")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self._lines(), [])

    def test_no_session_id_anywhere_exits_zero_and_writes_nothing(self):
        proc = self._run(json.dumps({"prompt": "hallo"}).encode())
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self._lines(), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
