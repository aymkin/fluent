"""
Prompt clock — measure how long a study session actually took.

The `UserPromptSubmit` hook (`prompt-clock.py`) appends one timestamp per
prompt; `update-db.py` sums the gaps between them at session end and writes the
total as `measured_minutes`, beside the tutor's `duration_minutes` estimate.

The file is a scratch pad, not a database: one JSONL line per prompt, appended
and never rewritten by the hook, pruned by the one consumer that already writes
atomically.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fluent_paths import data_dir, ensure_data_dir

CLOCK_FILE = ".prompt-clock.jsonl"

# The longest pause still counted as one sitting. Measured, not guessed: over
# the two sessions of 2026-09-21 this cutoff reproduces the tutor's own
# estimates — 26.3 minutes against a written 27, and 21.7 against a written 20.
# Every wider cutoff diverges hard (10 minutes gives 40.6 and 42.9; 30 minutes
# gives 40.6 and 155.1), because the gaps in a real session fall off a cliff
# right here: ... 4, 4, 4, 5, then 9, 30, 32, 92, 96.
#
# It earns a second keep: the pauses around prompts that are not study at all —
# the three about a browser extension that closed one of those sessions — are
# all wider than this, so they drop out without anyone marking where the
# studying stopped.
PAUSE_CUTOFF_MIN = 5

# A mark is only ever read by the session that wrote it, and a session does not
# outlive a day. Anything older is another day's leftovers.
RETAIN_HOURS = 24


def _path(create: bool = False) -> Path:
    return (ensure_data_dir() if create else data_dir()) / CLOCK_FILE


def _read(path: Path, now: datetime) -> list:
    """Parsed, fresh, chronological marks. Unreadable lines are dropped.

    An append cut short by a killed process leaves a partial line, and a
    truncated tail must not cost the whole measurement.
    """
    cutoff = now - timedelta(hours=RETAIN_HOURS)
    marks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                mark = json.loads(line)
                ts = datetime.fromisoformat(mark["ts"])
            except (ValueError, TypeError, KeyError):
                continue
            if not isinstance(mark.get("sid"), str) or ts < cutoff:
                continue
            marks.append((ts, mark))
    marks.sort(key=lambda m: m[0])
    return marks


def record(sid: Optional[str], is_command: bool, now: Optional[datetime] = None) -> None:
    """Append one mark. Append-only on purpose: the hook runs on the learner's
    every prompt, so it may not read, rewrite, or block."""
    if not sid:
        return
    mark = {"sid": sid, "ts": (now or datetime.now().astimezone()).isoformat(timespec="seconds")}
    if is_command:
        mark["cmd"] = True
    with open(_path(create=True), "a", encoding="utf-8") as f:
        f.write(json.dumps(mark, ensure_ascii=False) + "\n")


def measured_minutes(sid: Optional[str], now: Optional[datetime] = None) -> Optional[int]:
    """Minutes this session spent studying, or None if it was never clocked.

    None and 0 are different answers: None means no marks exist for this
    session — the hook is not installed, or the file was pruned — and a record
    written then must carry no measurement at all rather than claim zero.
    """
    if not sid:
        return None
    now = now or datetime.now().astimezone()
    path = _path()
    if not path.exists():
        return None
    marks = [(ts, m) for ts, m in _read(path, now) if m["sid"] == sid]
    if not marks:
        return None

    # From the last /fluent prompt onward: one Claude Code session can hold
    # ordinary work before the command, and that time is not studying. With no
    # command mark the session was resumed — the command predates this file —
    # and since only a study session reaches update-db.py, measuring all of its
    # marks is the best answer available.
    start = 0
    for i, (_, mark) in enumerate(marks):
        if mark.get("cmd"):
            start = i
    window = [ts for ts, _ in marks[start:]]

    cutoff = PAUSE_CUTOFF_MIN * 60
    total = sum(
        gap for gap in ((window[i + 1] - window[i]).total_seconds() for i in range(len(window) - 1))
        if gap <= cutoff
    )
    return round(total / 60)


def prune(now: Optional[datetime] = None) -> None:
    """Drop marks past the retention window, atomically.

    Called from update-db.py rather than from the hook: rewriting the file is a
    read-modify-write, and the hook has no business doing one on a prompt.
    """
    path = _path()
    if not path.exists():
        return
    now = now or datetime.now().astimezone()
    kept = _read(path, now)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for _, mark in kept:
            f.write(json.dumps(mark, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp), str(path))
