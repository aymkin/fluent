#!/usr/bin/env python3
"""
Fluent DB Update Script
Updates all 6 learning databases from a single JSON session report via stdin.

Usage:
    python3 .claude/hooks/update-db.py <<'EOF'
    { "session_id": "session-005", "date": "2026-04-24", ... }
    EOF

See .claude/skills/fluent-db-updater/SKILL.md for the full input schema.

Exit codes: 0=success, 1=validation error, 2=blocking/data error
"""
import copy
import json
import os
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fluent_paths import ensure_data_dir, ensure_backups_dir, force_utf8_io  # noqa: E402
import fsrs  # noqa: E402

force_utf8_io()
DATA_DIR = ensure_data_dir()
BACKUP_DIR = ensure_backups_dir()

# --- Utility functions ---

def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    tmp_path = path.with_suffix('.json.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp_path), str(path))  # atomic + overwrites (os.rename fails on Windows if dest exists)


def date_plus_days(today_str: str, days: int) -> str:
    return (date.fromisoformat(today_str) + timedelta(days=days)).isoformat()


def get_week_start(today_str: str) -> str:
    d = date.fromisoformat(today_str)
    return (d - timedelta(days=d.weekday())).isoformat()


def session_totals(session: dict) -> tuple:
    """(exercises, correct) summed across every skill in skill_scores."""
    scores = session.get("skill_scores", {}).values()
    return (sum(s.get("exercises", 0) for s in scores),
            sum(s.get("correct", 0) for s in scores))


def validate_milestones(session: dict) -> None:
    """Normalize session['milestones'] to a list of clean non-empty strings.

    Malformed entries exit 1 (validation error) before any DB is touched. The
    session date and top-level session_id stamp every milestone downstream.
    """
    raw = session.get("milestones", [])
    if not isinstance(raw, list):
        print(f"[Fluent] Error: 'milestones' must be a list, got {type(raw).__name__}", file=sys.stderr)
        sys.exit(1)
    for i, ms in enumerate(raw):
        if not isinstance(ms, str) or not ms.strip():
            print(f"[Fluent] Error: milestone at index {i} must be a non-empty string "
                  f"(got {type(ms).__name__}) — pass a plain string; the "
                  f"'milestone'/'date' object form is no longer accepted", file=sys.stderr)
            sys.exit(1)
    session["milestones"] = [ms.strip() for ms in raw]


def backup_all(tag: str):
    backup_path = BACKUP_DIR / tag
    backup_path.mkdir(parents=True, exist_ok=True)
    for f in DATA_DIR.glob("*.json"):
        shutil.copy2(f, backup_path / f.name)


# --- Updater functions ---
# Each mutates in place. Confidence in learner-profile is 0-100 int.
# Session-log preserves the existing rich schema (skills_practiced array,
# score_breakdown, topics_covered, breakthroughs, focus_next_session,
# achievements_earned). Spaced-repetition preserves consecutive_*,
# mastery_level, total_reviews, priority, content, answer, category,
# difficulty fields on existing items.

def update_learner_profile(profile: dict, session: dict):
    today = session["date"]
    last = profile.get("last_updated", "")

    if last == today:
        pass
    elif last == date_plus_days(today, -1):
        profile["current_streak_days"] = profile.get("current_streak_days", 0) + 1
    else:
        profile["current_streak_days"] = 1

    profile["last_updated"] = today
    profile["total_sessions"] = profile.get("total_sessions", 0) + 1
    profile["total_study_minutes"] = profile.get("total_study_minutes", 0) + session.get("duration_minutes", 0)

    for skill, scores in session.get("skill_scores", {}).items():
        skills = profile.setdefault("skills", {})
        s = skills.setdefault(skill, {
            "current_level": 0, "confidence": 0,
            "last_practiced": None, "total_practice_time": 0,
        })
        s["last_practiced"] = today
        s["total_practice_time"] = s.get("total_practice_time", 0) + scores.get("time_minutes", 0)
        if scores.get("exercises", 0) > 0:
            # confidence is 0-100 int; EWMA against session accuracy (0-100)
            new_acc_pct = (scores["correct"] / scores["exercises"]) * 100
            old_conf = s.get("confidence", 0)
            s["confidence"] = round(old_conf * 0.7 + new_acc_pct * 0.3)
        s["current_level"] = max(s.get("current_level", 0), 1)

    if session.get("focus_areas"):
        profile["focus_areas"] = session["focus_areas"]

    for i, text in enumerate(session.get("milestones", [])):
        # Index prefix keeps ids distinct when two milestones share their first
        # 30 chars or slugify to nothing (all-non-Latin text).
        slug = re.sub(r'[^a-z0-9]+', '_', text[:30].lower()).strip('_') or "milestone"
        profile.setdefault("achievements", []).append({
            "id": f"session_{session['session_id']}_{i}_{slug}",
            "name": text,
            "earned_date": today,
            "description": text,
        })


def update_progress_db(progress: dict, session: dict):
    today = session["date"]
    skill_scores = session.get("skill_scores", {})
    total_ex, total_cor = session_totals(session)
    accuracy = round(total_cor / total_ex, 3) if total_ex > 0 else 0.0

    stats = progress.setdefault("overall_stats", {
        "total_sessions": 0, "total_exercises": 0, "total_correct": 0,
        "total_incorrect": 0, "accuracy_rate": 0.0,
        "total_study_minutes": 0, "average_session_duration": 0,
    })
    stats["total_sessions"] = stats.get("total_sessions", 0) + 1
    stats["total_exercises"] = stats.get("total_exercises", 0) + total_ex
    stats["total_correct"] = stats.get("total_correct", 0) + total_cor
    stats["total_incorrect"] = stats.get("total_incorrect", 0) + (total_ex - total_cor)
    stats["accuracy_rate"] = round(stats["total_correct"] / stats["total_exercises"], 3) if stats["total_exercises"] > 0 else 0.0
    stats["total_study_minutes"] = stats.get("total_study_minutes", 0) + session.get("duration_minutes", 0)
    stats["average_session_duration"] = round(stats["total_study_minutes"] / stats["total_sessions"])

    trend = progress.setdefault("accuracy_trend", [])
    # Dedup same-day entries: replace if present, else append
    existing = next((t for t in trend if t.get("date") == today), None)
    if existing is not None:
        existing["accuracy"] = accuracy
        existing["exercises"] = existing.get("exercises", 0) + total_ex
    else:
        trend.append({"date": today, "accuracy": accuracy, "exercises": total_ex})

    for skill, scores in skill_scores.items():
        sp = progress.setdefault("skill_progress", {}).setdefault(skill, {
            "sessions": 0, "accuracy": 0.0, "last_practiced": None,
            "exercises_completed": 0, "correct_count": 0, "incorrect_count": 0,
        })
        old_sessions = sp.get("sessions", 0)
        sp["sessions"] = old_sessions + 1
        new_acc = scores["correct"] / scores["exercises"] if scores.get("exercises", 0) > 0 else 0.0
        sp["accuracy"] = round(
            (sp.get("accuracy", 0.0) * old_sessions + new_acc) / sp["sessions"], 3
        )
        sp["last_practiced"] = today
        sp["exercises_completed"] = sp.get("exercises_completed", 0) + scores.get("exercises", 0)
        sp["correct_count"] = sp.get("correct_count", 0) + scores.get("correct", 0)
        sp["incorrect_count"] = sp.get("incorrect_count", 0) + (scores.get("exercises", 0) - scores.get("correct", 0))

    week_start = get_week_start(today)
    weekly = progress.setdefault("weekly_summary", [])
    week_entry = next((w for w in weekly if w.get("week_start") == week_start), None)
    if week_entry is None:
        week_entry = {"week_start": week_start, "sessions": 0, "total_minutes": 0, "accuracy": 0.0}
        weekly.append(week_entry)

    old_s = week_entry.get("sessions", 0)
    week_entry["sessions"] = old_s + 1
    week_entry["total_minutes"] = week_entry.get("total_minutes", 0) + session.get("duration_minutes", 0)
    week_entry["accuracy"] = round(
        (week_entry.get("accuracy", 0.0) * old_s + accuracy) / week_entry["sessions"], 3
    )

    progress.setdefault("metadata", {})["last_updated"] = today


def update_mistakes_db(mistakes: dict, session: dict):
    today = session["date"]
    patterns = mistakes.setdefault("error_patterns", {})

    for error in session.get("errors", []):
        pid = error["pattern_id"]

        if pid in patterns:
            pat = patterns[pid]
            pat["frequency"] = pat.get("frequency", 0) + 1
            pat["last_seen"] = today
            pat["next_review"] = date_plus_days(today, 1)
            pat["consecutive_incorrect"] = pat.get("consecutive_incorrect", 0) + 1
            pat["consecutive_correct"] = 0
            pat.setdefault("examples", []).append({
                "incorrect": error.get("your_answer", ""),
                "correct": error.get("correct_answer", ""),
                "context": error.get("context", ""),
                "date": today,
            })
            pat["examples"] = pat["examples"][-5:]
            if error.get("notes"):
                pat["notes"] = error["notes"]
        else:
            patterns[pid] = {
                "category": error.get("category", "other"),
                "subcategory": error.get("subcategory", ""),
                "description": error.get("description", ""),
                "severity": error.get("severity", "minor"),
                "frequency": 1,
                "mastery_level": 0,
                "difficulty_score": error.get("difficulty_score", 0.5),
                "last_seen": today,
                "next_review": date_plus_days(today, 1),
                "consecutive_correct": 0,
                "consecutive_incorrect": 1,
                "examples": [{
                    "incorrect": error.get("your_answer", ""),
                    "correct": error.get("correct_answer", ""),
                    "context": error.get("context", ""),
                    "date": today,
                }],
                "notes": error.get("notes", ""),
            }

    mistakes.setdefault("metadata", {})["last_updated"] = today
    mistakes["metadata"]["total_patterns_tracked"] = len(patterns)


def update_mastery_db(mastery: dict, session: dict, progress: dict):
    today = session["date"]

    for skill, scores in session.get("skill_scores", {}).items():
        s = mastery.setdefault("skills", {}).setdefault(skill, {
            "mastery_level": 0, "confidence_score": 0.0,
            "total_practice_time": 0, "last_practiced": None,
            "practice_count": 0, "avg_accuracy": 0.0,
        })
        s["last_practiced"] = today
        s["total_practice_time"] = s.get("total_practice_time", 0) + scores.get("time_minutes", 0)
        s["practice_count"] = s.get("practice_count", 0) + scores.get("exercises", 0)

        sp = progress.get("skill_progress", {}).get(skill, {})
        acc = sp.get("accuracy", 0)
        sessions = sp.get("sessions", 0)
        s["confidence_score"] = round(acc, 3)
        s["avg_accuracy"] = round(acc, 3)

        if sessions == 0:
            s["mastery_level"] = 0
        elif sessions < 3 or acc < 0.5:
            s["mastery_level"] = max(s.get("mastery_level", 0), 1)
        elif sessions < 5 or acc < 0.65:
            s["mastery_level"] = max(s.get("mastery_level", 0), 2)
        elif sessions < 10 or acc < 0.8:
            s["mastery_level"] = max(s.get("mastery_level", 0), 3)
        elif sessions < 20 or acc < 0.9:
            s["mastery_level"] = max(s.get("mastery_level", 0), 4)
        else:
            s["mastery_level"] = 5

    mastery.setdefault("metadata", {})["last_updated"] = today


def new_sr_item(item_id, today, item_type, content, answer, category, difficulty,
                *, consecutive_incorrect, last_quality, priority):
    """A fresh spaced-repetition item. Key set and order are the on-disk
    contract for the learner's scheduling state — don't add/drop/reorder."""
    return {
        "id": item_id,
        "type": item_type,
        "content": content,
        "answer": answer,
        "category": category,
        "difficulty": difficulty,
        "created_date": today,
        "due_date": date_plus_days(today, 1),
        "interval_days": 1,
        "repetitions": 0,
        "stability": None,
        "fsrs_difficulty": None,
        "consecutive_correct": 0,
        "consecutive_incorrect": consecutive_incorrect,
        "last_reviewed": today,
        "last_quality": last_quality,
        "mastery_level": 0,
        "total_reviews": 0,
        "priority": priority,
    }


def update_spaced_repetition(sr: dict, session: dict):
    today = session["date"]
    items = sr.setdefault("items", {})

    for review in session.get("review_results", []):
        item_id = review["item_id"]
        quality = review["quality"]
        if item_id in items:
            item = items[item_id]
            weights = sr.get("metadata", {}).get("weights")
            score = review.get("score", quality * 2)
            rating = 1 if score <= 4 else 2 if score <= 6 else 3 if score <= 8 else 4
            fsrs_state = {
                "stability": item.get("stability"),
                "difficulty": item.get("fsrs_difficulty"),
                "last_reviewed": item.get("last_reviewed"),
            }
            r = fsrs.schedule(fsrs_state, rating, today, weights)
            item["stability"] = r["stability"]
            item["fsrs_difficulty"] = r["difficulty"]
            item["interval_days"] = r["interval_days"]
            item["due_date"] = r["due_date"]
            item["last_rating"] = rating
            item["repetitions"] = item.get("repetitions", 0) + 1 if quality >= 3 else 0
            item["last_reviewed"] = today
            item["last_quality"] = quality
            item["total_reviews"] = item.get("total_reviews", 0) + 1
            if quality >= 3:
                item["consecutive_correct"] = item.get("consecutive_correct", 0) + 1
                item["consecutive_incorrect"] = 0
            else:
                item["consecutive_incorrect"] = item.get("consecutive_incorrect", 0) + 1
                item["consecutive_correct"] = 0
            # Mastery: rough map from repetitions and quality (clamped 0..5)
            current = item.get("mastery_level", 0)
            if item["repetitions"] >= 5 and item["consecutive_correct"] >= 3:
                item["mastery_level"] = min(5, max(current, 3))
            elif item["repetitions"] >= 2 and item["consecutive_correct"] >= 1 and quality >= 4:
                item["mastery_level"] = min(5, current + 1)
            # priority heuristic
            if item.get("consecutive_incorrect", 0) >= 2:
                item["priority"] = "high"
            elif item.get("mastery_level", 0) >= 3:
                item["priority"] = "low"
            else:
                item["priority"] = item.get("priority", "medium")
            item.setdefault("review_history", []).append({
                "date": today,
                "quality": quality,
                "score": review.get("score", 0),
            })

    for vocab in session.get("new_vocabulary", []):
        item_id = vocab["item_id"]
        if item_id not in items:
            items[item_id] = new_sr_item(
                item_id, today, vocab.get("item_type", "vocabulary"),
                vocab.get("content", ""), vocab.get("answer", ""),
                vocab.get("category", ""), vocab.get("difficulty", ""),
                consecutive_incorrect=0,
                last_quality=vocab.get("initial_quality", 3),
                priority=vocab.get("priority", "medium"))

    for error in session.get("errors", []):
        item_id = error["pattern_id"]
        if item_id not in items:
            items[item_id] = new_sr_item(
                item_id, today, "error_pattern", error.get("your_answer", ""),
                error.get("correct_answer", ""), error.get("category", ""), "",
                consecutive_incorrect=1, last_quality=2, priority="high")

    # Rebuild review queue
    sr["review_queue"] = {"today": [], "tomorrow": [], "this_week": [], "later": []}
    tom = date_plus_days(today, 1)
    week_end = date_plus_days(today, 7)
    for item_id, item in items.items():
        due = item.get("due_date", today)
        if due <= today:
            sr["review_queue"]["today"].append(item_id)
        elif due == tom:
            sr["review_queue"]["tomorrow"].append(item_id)
        elif due <= week_end:
            sr["review_queue"]["this_week"].append(item_id)
        else:
            sr["review_queue"]["later"].append(item_id)

    sr.setdefault("metadata", {})["last_updated"] = today
    sr["metadata"]["total_items_tracked"] = len(items)


def update_session_log(log: dict, session: dict, streak: int):
    """Matches existing schema: skills_practiced (array), score_breakdown,
    topics_covered, breakthroughs, focus_next_session, achievements_earned."""
    today = session["date"]
    skill_scores = session.get("skill_scores", {})
    total_ex, total_cor = session_totals(session)

    score_breakdown = {
        skill: round(s["correct"] / s["exercises"], 3) if s.get("exercises", 0) > 0 else 0.0
        for skill, s in skill_scores.items()
    }

    entry = {
        "session_id": session["session_id"],
        "date": today,
        "duration_minutes": session.get("duration_minutes", 0),
        "skills_practiced": session.get("skills_practiced", list(skill_scores.keys())),
        "command_used": session.get("command_used", "/fluent-learn"),
        "exercises_completed": total_ex,
        "accuracy": round(total_cor / total_ex, 3) if total_ex > 0 else 0.0,
        "score_breakdown": score_breakdown,
        "topics_covered": session.get("topics_covered", []),
        "breakthroughs": session.get("breakthroughs", []),
        "focus_next_session": session.get("focus_next_session", session.get("focus_areas", [])),
        "notes": session.get("session_notes", ""),
        "achievements_earned": session.get("achievements_earned", []),
        "streak_day": streak,
    }
    if session.get("exam_focus"):
        entry["exam_focus"] = session["exam_focus"]
    if session.get("critical_errors_identified"):
        entry["critical_errors_identified"] = session["critical_errors_identified"]

    log.setdefault("sessions", []).append(entry)

    for text in session.get("milestones", []):
        log.setdefault("milestones", []).append({
            "date": today,
            "milestone": text,
            "session_id": session["session_id"],
        })

    log.setdefault("metadata", {})["total_sessions"] = len(log["sessions"])


# --- Main ---

def main():
    try:
        session = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[Fluent] Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    for field in ("session_id", "date"):
        if field not in session:
            print(f"[Fluent] Error: Missing required field '{field}'", file=sys.stderr)
            sys.exit(1)

    # Validate milestones before touching any DB (exits 1 on malformed input,
    # so disk stays untouched on a validation failure).
    validate_milestones(session)

    session.setdefault("duration_minutes", 0)

    files = {
        "profile": DATA_DIR / "learner-profile.json",
        "progress": DATA_DIR / "progress-db.json",
        "mistakes": DATA_DIR / "mistakes-db.json",
        "mastery": DATA_DIR / "mastery-db.json",
        "sr": DATA_DIR / "spaced-repetition.json",
        "log": DATA_DIR / "session-log.json",
    }

    try:
        originals = {k: load_json(p) for k, p in files.items()}
    except Exception as e:
        print(f"[Fluent] Error loading databases: {e}", file=sys.stderr)
        sys.exit(2)

    # Work on deep copies so a mid-run exception leaves disk untouched.
    data = {k: copy.deepcopy(v) for k, v in originals.items()}

    try:
        update_learner_profile(data["profile"], session)
        update_progress_db(data["progress"], session)
        update_mistakes_db(data["mistakes"], session)
        update_mastery_db(data["mastery"], session, data["progress"])
        update_spaced_repetition(data["sr"], session)
        streak = data["profile"].get("current_streak_days", 0)
        update_session_log(data["log"], session, streak)
    except Exception as e:
        import traceback
        print(f"[Fluent] Error updating databases: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)

    # Backup originals BEFORE writing new state.
    backup_all(f"pre-update-{session['session_id']}")

    try:
        for k, p in files.items():
            save_json(p, data[k])
    except Exception as e:
        print(f"[Fluent] Error saving databases: {e}", file=sys.stderr)
        sys.exit(2)

    # Summary
    stats = data["progress"]["overall_stats"]
    total_ex, total_cor = session_totals(session)
    hit = f"{total_cor}/{total_ex} correct ({round(total_cor / total_ex * 100)}%)" if total_ex else "no exercises"

    print(f"[Fluent] ✅ Updated 6 databases for session {session['session_id']}")
    print(f"[Fluent] 🔥 Streak: {streak} days | Sessions: {stats['total_sessions']} | Minutes: {stats['total_study_minutes']}")
    print(f"[Fluent] 📊 This session: {hit} | Overall: {stats['accuracy_rate']*100:.0f}% of {stats['total_exercises']}")
    print(f"[Fluent] 🧠 SR: {data['sr']['metadata']['total_items_tracked']} items, "
          f"{len(data['sr']['review_queue'].get('tomorrow', []))} due tomorrow | "
          f"📝 {data['mistakes']['metadata']['total_patterns_tracked']} error patterns")

    sys.exit(0)


if __name__ == "__main__":
    main()
