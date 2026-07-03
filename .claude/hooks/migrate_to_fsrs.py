#!/usr/bin/env python3
"""One-time SM-2 -> FSRS-6 migration. Idempotent. Backs up before writing.

Usage: python3 .claude/hooks/migrate_to_fsrs.py
Seeds stability/difficulty for reviewed cards; stamps metadata.
"""
import json, os, shutil, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fluent_paths import ensure_data_dir, ensure_backups_dir, force_utf8_io

force_utf8_io()
DATA = ensure_data_dir()
BACKUPS = ensure_backups_dir()
SR_PATH = DATA / "spaced-repetition.json"



def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def seed(card):
    """Return (stability, fsrs_difficulty), or (None, None) for never-reviewed
    cards. Never-reviewed cards stay null so the first FSRS review initializes
    them. NOTE: the returned difficulty is the FSRS numeric difficulty; it is
    stored under the item key "fsrs_difficulty" (the "difficulty" key already
    holds the CEFR level string and must not be touched)."""
    if card.get("repetitions", 0) <= 0:
        return None, None
    interval = card.get("interval_days", 1)
    ef = card.get("easiness_factor", 2.5)
    stability = max(float(interval), 0.5)
    difficulty = _clamp(10.0 - (ef - 1.3) / 1.4 * 9.0, 1.0, 10.0)
    return round(stability, 4), round(difficulty, 4)


def main():
    if not SR_PATH.exists():
        print("[migrate] no spaced-repetition.json; nothing to do")
        return 0
    sr = json.loads(SR_PATH.read_text(encoding="utf-8"))
    items = sr.get("items", {})

    # backup
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    dest = BACKUPS / f"pre-migrate-fsrs-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in DATA.glob("*.json"):
        shutil.copy2(f, dest / f.name)

    seeded = 0
    for card in items.values():
        if card.get("stability") is not None:
            continue  # idempotent
        s, d = seed(card)
        if s is not None:
            card["stability"], card["fsrs_difficulty"] = s, d
            seeded += 1
        else:
            card.setdefault("stability", None)
            card.setdefault("fsrs_difficulty", None)

    meta = sr.setdefault("metadata", {})
    meta.update({
        "scheduler": "fsrs-6",
        "target_retention": 0.9,
        "weights": None,
        "last_optimized": None,
        "reviews_at_last_optimize": 0,
    })

    tmp = SR_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sr, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, SR_PATH)
    print(f"[migrate] seeded {seeded} cards; backup at {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
