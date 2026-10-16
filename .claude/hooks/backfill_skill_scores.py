#!/usr/bin/env python3
"""One-time backfill of skill_scores on the session records written before
update-db.py kept them. Dry run by default; --write applies.

Usage: python3 .claude/hooks/backfill_skill_scores.py [--write]

A session's counts are what its update added to the databases: the difference
between .backups/pre-update-<its id> and the backup taken before the next
session — the live files for the last one. A record is filled only when that
difference reproduces its score_breakdown and mastery-db's own difference
agrees on the minutes and the exercises; any other record is REFUSED and kept
as it is.
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fluent_paths import data_dir, force_utf8_io  # noqa: E402

# Per database, the object holding a skill tag's running totals.
FILES = {"profile": ("learner-profile.json", "skills"),
         "progress": ("progress-db.json", "skill_progress"),
         "mastery": ("mastery-db.json", "skills")}


def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# update-db.py's save_json, byte for byte: a filled log then differs from its
# backup by the new keys alone.
def save_json(path: Path, data: dict):
    tmp_path = path.with_suffix('.json.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp_path), str(path))


def counters(d: Path):
    if not all((d / name).exists() for name, _ in FILES.values()):
        return None
    return {part: load(d / name).get(key, {}) for part, (name, key) in FILES.items()}


def reconstruct(record: dict, before: dict, after: dict):
    """(skill_scores, None) when the difference is this record's, else (None, why)."""
    def diff(part, tag, key):
        return after[part].get(tag, {}).get(key, 0) - before[part].get(tag, {}).get(key, 0)

    # update-db.py counts one session for every skill in skill_scores, a skill
    # with no exercises included, so that is which skills the session had.
    tags = [t for t in after["progress"] if diff("progress", t, "sessions") == 1]
    scores = {t: {"exercises": diff("progress", t, "exercises_completed"),
                  "correct": diff("progress", t, "correct_count"),
                  "time_minutes": diff("profile", t, "total_practice_time")} for t in tags}
    shares = {t: round(s["correct"] / s["exercises"], 3) if s["exercises"] > 0 else 0.0
              for t, s in scores.items()}
    if shares != record["score_breakdown"]:
        return None, f"shares {shares}, score_breakdown {record['score_breakdown']}"
    for t, s in scores.items():
        theirs = (diff("mastery", t, "total_practice_time"), diff("mastery", t, "practice_count"))
        if theirs != (s["time_minutes"], s["exercises"]):
            return None, (f"{t}: {s['time_minutes']} min and {s['exercises']} exercises, "
                          f"mastery-db {theirs[0]} min and {theirs[1]}")
    # In score_breakdown's order, which is the order update-db.py was sent them in.
    return {t: scores[t] for t in record["score_breakdown"]}, None


def main() -> int:
    force_utf8_io()
    if sys.argv[1:] not in ([], ["--write"]):
        print("usage: backfill_skill_scores.py [--write]", file=sys.stderr)
        return 1
    d = data_dir()
    log_path = d / "session-log.json"
    if not log_path.exists():
        print(f"[backfill] no session-log.json in {d}")
        return 0
    read_at = log_path.stat().st_mtime_ns
    log = load(log_path)
    order = sorted(log.get("sessions", []), key=lambda s: int(s["session_id"].rsplit("-", 1)[-1]))

    fills, refused = [], []
    for k, record in enumerate(order):
        if "skill_scores" in record or not record.get("score_breakdown"):
            continue
        before = counters(d / ".backups" / f"pre-update-{record['session_id']}")
        after = counters(d / ".backups" / f"pre-update-{order[k + 1]['session_id']}"
                         if k + 1 < len(order) else d)
        if before is None or after is None:
            refused.append((record["session_id"], "a backup it needs is missing"))
            continue
        scores, why = reconstruct(record, before, after)
        if why:
            refused.append((record["session_id"], why))
        else:
            fills.append((record, scores))

    for sid, why in refused:
        print(f"REFUSED {sid}: {why}")
    print(f"{len(fills) + len(refused)} to fill: {len(fills)} match, {len(refused)} refused.")
    if sys.argv[1:] != ["--write"] or not fills:
        return 0

    dest = d / ".backups" / f"pre-backfill-skill-scores-{datetime.now():%Y-%m-%d-%H%M%S}"
    dest.mkdir(parents=True)
    for f in d.glob("*.json"):
        shutil.copy2(f, dest / f.name)
    # A session saved since the read would be lost under the copy read before it.
    if log_path.stat().st_mtime_ns != read_at:
        print("[backfill] session-log.json changed while this ran; nothing written",
              file=sys.stderr)
        return 2
    for record, scores in fills:
        record["skill_scores"] = scores
    save_json(log_path, log)
    print(f"[backfill] wrote {len(fills)} records; backup in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
