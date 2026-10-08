#!/usr/bin/env python3
"""
Smoke test for .claude/hooks/update-db.py.

Runs the script against a fresh fixture DB in a temp dir, feeds it a sample
session report, and asserts schema invariants on the output files.

Usage:
    python3 tests/test_update_db.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "update-db.py"

# Every date counts from the real calendar day, because a session is saved on
# the day it is dated and a faked clock would test some other program. A suite
# run that straddles midnight can fail spuriously.
TODAY = date.today()


def day(offset: int) -> str:
    """The ISO date ``offset`` days from TODAY."""
    return (TODAY + timedelta(days=offset)).isoformat()


def make_fixtures(data_dir: Path, last_day: int = -1):
    """Six DBs holding one session, recorded ``last_day`` days from TODAY."""
    last, created, due = day(last_day), day(last_day - 3), day(last_day + 1)
    (data_dir / "learner-profile.json").write_text(json.dumps({
        "learner": {"name": "Test", "target_language": "Dutch",
                    "current_level": "A1", "target_level": "A2"},
        "profile_created": created,
        "last_updated": last,
        "current_streak_days": 2,
        "total_sessions": 1,
        "total_study_minutes": 10,
        "skills": {
            "vocabulary": {"current_level": 1, "confidence": 60,
                           "last_practiced": last,
                           "total_practice_time": 10}
        },
        "focus_areas": [],
        "achievements": [],
        "preferences": {}
    }))
    (data_dir / "progress-db.json").write_text(json.dumps({
        "metadata": {"last_updated": last, "language": "Dutch",
                     "tracking_started": created},
        "overall_stats": {"total_sessions": 1, "total_exercises": 4,
                          "total_correct": 3, "total_incorrect": 1,
                          "accuracy_rate": 0.75,
                          "total_study_minutes": 10,
                          "average_session_duration": 10},
        "accuracy_trend": [{"date": last, "accuracy": 0.75,
                            "exercises": 4}],
        "skill_progress": {
            "vocabulary": {"sessions": 1, "accuracy": 0.75,
                           "last_practiced": last,
                           "exercises_completed": 4, "correct_count": 3,
                           "incorrect_count": 1}
        },
        "weekly_summary": []
    }))
    (data_dir / "mistakes-db.json").write_text(json.dumps({
        "metadata": {"last_updated": last,
                     "total_patterns_tracked": 0, "language": "Dutch"},
        "error_patterns": {}
    }))
    (data_dir / "mastery-db.json").write_text(json.dumps({
        "metadata": {"last_updated": last, "language": "Dutch"},
        "skills": {
            "vocabulary": {"mastery_level": 1, "confidence_score": 0.75,
                           "total_practice_time": 10,
                           "last_practiced": last,
                           "practice_count": 4, "avg_accuracy": 0.75}
        },
        "patterns": {}
    }))
    (data_dir / "spaced-repetition.json").write_text(json.dumps({
        "metadata": {"algorithm": "SM-2", "last_updated": last,
                     "total_items_tracked": 1, "language": "Dutch"},
        "review_queue": {"today": [], "tomorrow": ["vocab_dag"],
                         "this_week": [], "later": []},
        "items": {
            "vocab_dag": {
                "id": "vocab_dag", "type": "vocabulary", "content": "dag",
                "answer": "day / hi-bye", "category": "greetings",
                "difficulty": "A1", "created_date": last,
                "due_date": due, "interval_days": 1,
                "repetitions": 1, "easiness_factor": 2.5,
                "consecutive_correct": 1, "consecutive_incorrect": 0,
                "last_reviewed": last, "last_quality": 4,
                "mastery_level": 1, "total_reviews": 1, "priority": "medium"
            }
        }
    }))
    (data_dir / "session-log.json").write_text(json.dumps({
        "metadata": {"language": "Dutch", "learner_name": "Test",
                     "total_sessions": 1},
        "sessions": [{
            "session_id": "session-001", "date": last,
            "duration_minutes": 10,
            "skills_practiced": ["vocabulary"],
            "exercises_completed": 4, "accuracy": 0.75,
            "score_breakdown": {"vocabulary": 0.75},
            "topics_covered": [], "breakthroughs": [],
            "focus_next_session": [], "notes": "",
            "achievements_earned": []
        }],
        "milestones": []
    }))


SESSION_PAYLOAD = {
    "session_id": "session-002",
    "date": day(0),
    "duration_minutes": 15,
    "command_used": "/fluent-learn",
    "skills_practiced": ["vocabulary"],
    "skill_scores": {
        "vocabulary": {"exercises": 5, "correct": 4, "time_minutes": 15}
    },
    "errors": [{
        "pattern_id": "verb_spreek",
        "category": "grammar",
        "subcategory": "verb_conjugation",
        "your_answer": "Hij spreek",
        "correct_answer": "Hij spreekt",
        "context": "3rd person",
        "severity": "critical",
        "difficulty_score": 0.7
    }],
    "new_vocabulary": [{
        "item_id": "het_huis",
        "item_type": "vocabulary",
        "content": "het huis",
        "answer": "the house",
        "category": "nouns",
        "difficulty": "A1",
        "initial_quality": 4
    }],
    "review_results": [{"item_id": "vocab_dag", "quality": 5, "score": 8}],
    "topics_covered": ["house_vocab"],
    "breakthroughs": ["Got 'het huis' on first try"],
    "focus_next_session": ["de/het drill"],
    "session_notes": "Good session.",
    "milestones": []
}

# The eleven labels errors[].category accepts, spelled out here rather than
# imported from the script so the test pins the canon instead of echoing it.
CANON_ERROR_CATEGORIES = (
    "grammar", "formal_informal", "vocabulary", "spelling", "prepositions",
    "articles", "missing", "structure", "comprehension", "inference", "other",
)

# The single review_results entry above targets this item on this session
# date — reused by the FSRS assertions in test_happy_path.
REVIEWED_ID = "vocab_dag"
SESSION_DATE = SESSION_PAYLOAD["date"]


class UpdateDbSmokeTest(unittest.TestCase):
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
        # The script measures the session whose id this names. A suite run under
        # Claude Code inherits a real one, so scrub it and let each test say
        # which session — if any — it is standing in for.
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        return env

    def _run(self, payload: dict, **env_extra):
        env = self._subprocess_env()
        env.update(env_extra)
        proc = subprocess.run(
            ["python3", str(SCRIPT)],
            input=json.dumps(payload).encode(),
            cwd=str(self.tmp),
            env=env,
            capture_output=True,
        )
        return proc

    def _load(self, name):
        with open(self.tmp / "data" / name) as f:
            return json.load(f)

    def _snapshot(self):
        """Path -> bytes for every file under the data dir, backups included."""
        root = self.tmp / "data"
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in sorted(root.rglob("*")) if p.is_file()}

    def test_happy_path(self):
        proc = self._run(SESSION_PAYLOAD)
        self.assertEqual(proc.returncode, 0,
                         msg=f"stdout={proc.stdout!r} stderr={proc.stderr!r}")

        with open(self.tmp / "data" / "session-log.json") as f:
            log = json.load(f)
        latest = log["sessions"][-1]
        self.assertEqual(latest["session_id"], "session-002")
        self.assertIn("skills_practiced", latest)
        self.assertIsInstance(latest["skills_practiced"], list)
        self.assertIn("score_breakdown", latest)
        self.assertIn("topics_covered", latest)
        self.assertIn("breakthroughs", latest)
        self.assertIn("focus_next_session", latest)
        self.assertIn("achievements_earned", latest)
        self.assertEqual(latest["streak_day"], 3)  # was 2, yesterday -> +1

        with open(self.tmp / "data" / "learner-profile.json") as f:
            profile = json.load(f)
        self.assertEqual(profile["current_streak_days"], 3)
        conf = profile["skills"]["vocabulary"]["confidence"]
        self.assertIsInstance(conf, int)
        self.assertGreaterEqual(conf, 0)
        self.assertLessEqual(conf, 100)

        with open(self.tmp / "data" / "spaced-repetition.json") as f:
            sr = json.load(f)
        dag = sr["items"]["vocab_dag"]
        # Schema preserved
        for k in ("consecutive_correct", "consecutive_incorrect",
                  "mastery_level", "total_reviews", "priority",
                  "content", "answer", "category", "difficulty"):
            self.assertIn(k, dag, f"lost field {k} on vocab_dag")
        # Back-compat: the fixture item predates the FSRS migration and still
        # carries the legacy SM-2 easiness_factor. Updating it must not crash,
        # and the untouched legacy key must survive (we stopped writing it, we
        # do not strip it from existing data).
        self.assertEqual(dag["easiness_factor"], 2.5)
        self.assertEqual(dag["total_reviews"], 2)  # was 1, +1 review
        self.assertEqual(dag["last_quality"], 5)

        # FSRS fields present on a reviewed item
        reviewed = sr["items"][REVIEWED_ID]
        self.assertIn("stability", reviewed)
        self.assertIn("fsrs_difficulty", reviewed)
        self.assertIn("last_rating", reviewed)
        self.assertIsInstance(reviewed["stability"], (int, float))
        # due_date is interval_days after the session date
        exp = (date.fromisoformat(SESSION_DATE) + timedelta(days=reviewed["interval_days"])).isoformat()
        self.assertEqual(reviewed["due_date"], exp)

        # Regression: CEFR "difficulty" (a domain field distinct from FSRS's
        # numeric difficulty) must survive the review untouched, while the
        # FSRS difficulty lands in its own "fsrs_difficulty" key.
        self.assertEqual(reviewed["difficulty"], "A1")
        self.assertIsInstance(reviewed["fsrs_difficulty"], float)

        # New vocabulary item fully populated
        huis = sr["items"]["het_huis"]
        for k in ("id", "type", "content", "answer", "category",
                  "difficulty", "due_date", "interval_days", "repetitions",
                  "consecutive_correct", "consecutive_incorrect",
                  "mastery_level", "total_reviews", "priority"):
            self.assertIn(k, huis, f"new item missing {k}")
        # ...and carries no vestigial SM-2 field. Same for the SR item auto-
        # created from the session's error pattern.
        self.assertNotIn("easiness_factor", huis)
        self.assertNotIn("easiness_factor", sr["items"]["verb_spreek"])

        with open(self.tmp / "data" / "mistakes-db.json") as f:
            mistakes = json.load(f)
        self.assertIn("verb_spreek", mistakes["error_patterns"])
        pat = mistakes["error_patterns"]["verb_spreek"]
        self.assertEqual(pat["consecutive_incorrect"], 1)
        # last_seen is the only "when did we last hit this" field; the
        # last_occurred alias is gone.
        self.assertEqual(pat["last_seen"], SESSION_DATE)
        self.assertNotIn("last_occurred", pat)
        self.assertEqual(pat["examples"][-1]["incorrect"], "Hij spreek")
        self.assertEqual(pat["examples"][-1]["correct"], "Hij spreekt")

        # Backup directory exists (nested inside data/ to avoid collisions
        # with other plugins when the global fallback ~/.claude/fluent-data is used).
        backup = self.tmp / "data" / ".backups" / "pre-update-session-002"
        self.assertTrue(backup.exists(), "pre-update backup missing")

    def test_repeat_error_pattern_updates_last_seen_only(self):
        # Second sighting of the same pattern takes the "already tracked"
        # branch, which used to also write a last_occurred alias.
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        payload = dict(SESSION_PAYLOAD)
        payload["session_id"] = "session-003"
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        pat = self._load("mistakes-db.json")["error_patterns"]["verb_spreek"]
        self.assertEqual(pat["frequency"], 2)
        self.assertEqual(pat["last_seen"], SESSION_DATE)
        self.assertNotIn("last_occurred", pat)
        self.assertEqual(pat["next_review"], day(1))

    def test_reviews_carry_pattern_mastery_into_mistakes_db(self):
        """/fluent-learn and /fluent-vocab pick weak patterns by mistakes-db's
        mastery_level. Reviews raised only the spaced-repetition twin, so every
        pattern sat at 0 there and every one was picked."""
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        for n in range(4):
            proc = self._run(dict(SESSION_PAYLOAD, session_id=f"session-01{n}",
                                  errors=[], new_vocabulary=[],
                                  review_results=[{"item_id": "verb_spreek",
                                                   "quality": 5, "score": 10}]))
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        item = self._load("spaced-repetition.json")["items"]["verb_spreek"]
        self.assertEqual(item["mastery_level"], 3)  # past the skills' "<= 2"
        pat = self._load("mistakes-db.json")["error_patterns"]["verb_spreek"]
        self.assertEqual(pat["mastery_level"], item["mastery_level"])

    def test_review_stars_climb_to_five_and_a_miss_costs_one(self):
        """mastery_level is 0-5 stars. From a card's fifth success on, the
        floor branch won every review and held it at 3, while a miss reset
        repetitions and reopened the climb past it — so a card that had been
        forgotten outranked one that never was."""
        errors = [dict(SESSION_PAYLOAD["errors"][0], pattern_id=pid)
                  for pid in ("clean", "lapse")]
        self.assertEqual(self._run(dict(SESSION_PAYLOAD, errors=errors)).returncode, 0)
        stars = {"clean": [], "lapse": []}
        priority, mirror = [], []
        for n, quality in enumerate([5, 5, 5, 5, 5, 5, 1, 1, 5, 5]):
            proc = self._run(dict(SESSION_PAYLOAD, session_id=f"session-02{n}",
                                  errors=[], new_vocabulary=[],
                                  review_results=[{"item_id": "clean", "quality": 5},
                                                  {"item_id": "lapse", "quality": quality}]))
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            items = self._load("spaced-repetition.json")["items"]
            for pid in stars:
                stars[pid].append(items[pid]["mastery_level"])
            priority.append(items["lapse"]["priority"])
            mirror.append(self._load("mistakes-db.json")["error_patterns"]["lapse"]["mastery_level"])

        self.assertEqual(stars, {"clean": [0, 1, 2, 3, 4, 5, 5, 5, 5, 5],
                                 "lapse": [0, 1, 2, 3, 4, 5, 2, 1, 1, 2]})
        # The first miss takes the card out of "low", which sorts it to the
        # back of the 10-card review round.
        self.assertEqual(priority[5:7], ["low", "medium"])
        # /fluent-learn and /fluent-vocab see the drop: back in their "<= 2".
        self.assertEqual(mirror, stars["lapse"])

    def test_a_miss_leaves_a_low_card_below_three_low(self):
        """Only a card that a miss pulls down from 3 or more leaves "low"; one
        the tutor filed as low keeps that priority."""
        vocab = dict(SESSION_PAYLOAD["new_vocabulary"][0], item_id="nice_to_know",
                     priority="low")
        self.assertEqual(self._run(dict(SESSION_PAYLOAD, new_vocabulary=[vocab])).returncode, 0)
        proc = self._run(dict(SESSION_PAYLOAD, session_id="session-003", errors=[],
                              new_vocabulary=[],
                              review_results=[{"item_id": "nice_to_know", "quality": 1}]))
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        item = self._load("spaced-repetition.json")["items"]["nice_to_know"]
        self.assertEqual((item["mastery_level"], item["priority"]), (0, "low"))

    def test_missing_required_field_exits_1(self):
        proc = self._run({"date": SESSION_DATE})  # no session_id
        self.assertEqual(proc.returncode, 1)

    def test_same_day_does_not_bump_streak(self):
        # The first session today extends yesterday's streak; a second one
        # the same day leaves it where it is.
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        self.assertEqual(self._load("learner-profile.json")["current_streak_days"], 3)
        payload = dict(SESSION_PAYLOAD)
        payload["session_id"] = "session-003"
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(self._load("learner-profile.json")["current_streak_days"], 3)

    def test_streak_resets_after_a_gap(self):
        # Last session three days ago: today's session is a broken streak,
        # not a continued one.
        make_fixtures(self.tmp / "data", last_day=-3)
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        self.assertEqual(self._load("learner-profile.json")["current_streak_days"], 1)

    def test_overall_accuracy_is_cumulative(self):
        # Fixture holds 4 exercises / 3 correct; the payload adds 5 / 4.
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        stats = self._load("progress-db.json")["overall_stats"]
        self.assertEqual(stats["total_exercises"], 9)
        self.assertEqual(stats["total_correct"], 7)
        self.assertEqual(stats["total_incorrect"], 2)
        self.assertEqual(stats["accuracy_rate"], round(7 / 9, 3))

    def test_mastery_level_climbs_with_session_count(self):
        # mastery_level is driven by progress-db's per-skill sessions/accuracy.
        # Fixture starts at 1 session / level 1; the 3rd session crosses into 2.
        for n in range(2):
            payload = dict(SESSION_PAYLOAD)
            payload["session_id"] = f"session-00{n + 2}"
            self.assertEqual(self._run(payload).returncode, 0)

        sp = self._load("progress-db.json")["skill_progress"]["vocabulary"]
        self.assertEqual(sp["sessions"], 3)
        self.assertEqual(sp["exercises_completed"], 14)
        self.assertEqual(self._load("mastery-db.json")["skills"]["vocabulary"]["mastery_level"], 2)

    # --- Error categories (spec §3.1) ---

    def _payload_with_error(self, session_id, error, date=SESSION_DATE):
        payload = dict(SESSION_PAYLOAD)
        payload["session_id"] = session_id
        payload["date"] = date
        payload["errors"] = [error]
        return payload

    def test_error_category_from_canon_accepted(self):
        # Every label in the canon is accepted, the three added by D1 included.
        # One pattern_id per label: the "already tracked" branch never rewrites
        # category, so reusing an id would hide what was actually stored.
        for label in CANON_ERROR_CATEGORIES:
            with self.subTest(category=label):
                proc = self._run(self._payload_with_error(
                    f"session-3-{label}",
                    {"pattern_id": f"pat_{label}", "category": label}))
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                pat = self._load("mistakes-db.json")["error_patterns"][f"pat_{label}"]
                self.assertEqual(pat["category"], label)

    def test_error_category_omitted_defaults_to_other(self):
        proc = self._run(self._payload_with_error(
            "session-400", {"pattern_id": "pat_no_category"}))
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        pat = self._load("mistakes-db.json")["error_patterns"]["pat_no_category"]
        self.assertEqual(pat["category"], "other")

    def test_error_category_off_canon_rejected_before_any_write(self):
        # Off-canon labels exit 1 naming the offending index and value, with
        # the data dir byte-identical afterwards — validation runs before any
        # DB file is read or written.
        before = self._snapshot()
        for n, bad in enumerate(("structuur", "Grammar", "", None, 42, ["grammar"])):
            with self.subTest(category=bad):
                proc = self._run(self._payload_with_error(
                    f"session-5{n:02d}",
                    {"pattern_id": "pat_bad", "category": bad}))
                self.assertEqual(proc.returncode, 1,
                                 msg=f"case={bad!r} stdout={proc.stdout!r}")
                err = proc.stderr.decode()
                self.assertIn("index 0", err)
                self.assertIn(repr(bad), err)
                self.assertEqual(self._snapshot(), before)

    # --- Milestones (issue #8) ---

    def _payload_with(self, session_id, milestones, date=SESSION_DATE):
        payload = dict(SESSION_PAYLOAD)
        payload["session_id"] = session_id
        payload["date"] = date
        payload["milestones"] = milestones
        return payload

    def test_milestone_string_form(self):
        text = "Reached A2 vocabulary milestone"
        proc = self._run(self._payload_with("session-100", [text]))
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        log = self._load("session-log.json")
        m = log["milestones"][-1]
        self.assertEqual(m["milestone"], text)
        # The session date and top-level session_id stamp every milestone —
        # the per-milestone "date" override is gone.
        self.assertEqual(m["date"], SESSION_DATE)
        self.assertEqual(m["session_id"], "session-100")

        profile = self._load("learner-profile.json")
        ach = profile["achievements"][-1]
        self.assertEqual(ach["name"], text)
        self.assertEqual(ach["description"], text)
        self.assertEqual(ach["earned_date"], SESSION_DATE)
        self.assertTrue(ach["id"].startswith("session_session-100_"))

    def test_milestone_malformed_rejected_before_any_write(self):
        # Breaking change (post-v0.3.0): only bare non-empty strings. The old
        # object form and every malformed scalar must exit 1 with nothing
        # written — the payload is validated before a single DB is touched.
        bad_cases = [
            {"milestone": "Wrote first paragraph"},   # the old object form
            {"milestone": "Backdated win", "date": "2026-04-20"},
            {"milestone": ""},
            {"date": "2026-04-24"},
            42, None, ["Nested list"], "", "   ",
        ]
        for n, bad in enumerate(bad_cases):
            with self.subTest(case=bad):
                proc = self._run(self._payload_with(f"session-2{n:02d}", [bad]))
                self.assertEqual(proc.returncode, 1,
                                 msg=f"case={bad!r} stdout={proc.stdout!r}")
                err = proc.stderr.decode()
                self.assertIn("index 0", err)
                self.assertIn("string", err)
                log = self._load("session-log.json")
                self.assertEqual(len(log["sessions"]), 1)
                self.assertEqual(log["milestones"], [])
                self.assertEqual(self._load("learner-profile.json")["achievements"], [])

    def test_milestone_achievement_ids_stay_distinct(self):
        # Slugs come from the first 30 chars lowercased: two milestones sharing
        # that prefix, or slugifying to nothing (all-non-Latin), must still get
        # distinct non-empty ids from the index prefix.
        prefix = "Mastered the perfect tense fo"  # 29 chars
        cases = [
            [prefix + "r regular verbs", prefix + "r irregular verbs"],
            ["\u0645\u0631\u062d\u0644\u0629 \u0623\u0648\u0644\u0649", "\u0645\u0631\u062d\u0644\u0629 \u062b\u0627\u0646\u064a\u0629"],
        ]
        for n, ms in enumerate(cases):
            with self.subTest(case=ms):
                proc = self._run(self._payload_with(f"session-10{n}", ms))
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                ids = [a["id"] for a in self._load("learner-profile.json")["achievements"][-2:]]
                self.assertEqual(len(set(ids)), 2, msg=f"colliding ids: {ids}")
                for i in ids:
                    self.assertFalse(i.endswith("_"), f"bare trailing underscore: {i}")

    # --- measured_minutes

    CLOCK_SID = "cccccccc-9999-0000-1111-222222222222"

    def _write_clock(self, *offsets_min):
        """A prompt clock for CLOCK_SID, marks at the given minutes before now,
        the earliest of them carrying the /fluent command flag."""
        now = datetime.now().astimezone()
        lines = []
        for i, off in enumerate(sorted(offsets_min, reverse=True)):
            mark = {"sid": self.CLOCK_SID,
                    "ts": (now - timedelta(minutes=off)).isoformat(timespec="seconds")}
            if i == 0:
                mark["cmd"] = True
            lines.append(json.dumps(mark))
        (self.tmp / "data" / ".prompt-clock.jsonl").write_text("\n".join(lines) + "\n",
                                                               encoding="utf-8")

    def test_measured_minutes_lands_on_the_session_record(self):
        self._write_clock(9, 6, 4, 2)  # gaps of 3, 2 and 2 minutes
        proc = self._run(SESSION_PAYLOAD, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        entry = self._load("session-log.json")["sessions"][-1]
        self.assertEqual(entry["measured_minutes"], 7)
        # The estimate is kept alongside, not replaced: two numbers side by side
        # are what show whether the tutor's guesses were any good.
        self.assertEqual(entry["duration_minutes"], SESSION_PAYLOAD["duration_minutes"])

    def test_no_clock_leaves_the_field_off_the_record(self):
        proc = self._run(SESSION_PAYLOAD, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertNotIn("measured_minutes", self._load("session-log.json")["sessions"][-1])

    def test_a_measurement_in_the_payload_is_ignored(self):
        """The field is a measurement or it is nothing. Accepting it as input
        would hand it straight back to the guessing it exists to replace."""
        self._write_clock(9, 6, 4, 2)
        payload = dict(SESSION_PAYLOAD, measured_minutes=999)
        proc = self._run(payload, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(self._load("session-log.json")["sessions"][-1]["measured_minutes"], 7)

    def test_the_measurement_stays_out_of_the_running_totals(self):
        """total_study_minutes has meant the estimate across 26 sessions.
        Swapping the source mid-history would silently redefine it."""
        self._write_clock(60, 57, 55)
        before = self._load("learner-profile.json")["total_study_minutes"]
        proc = self._run(SESSION_PAYLOAD, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(self._load("learner-profile.json")["total_study_minutes"],
                         before + SESSION_PAYLOAD["duration_minutes"])

    def test_stale_marks_are_pruned_after_a_successful_update(self):
        now = datetime.now().astimezone()
        clock = self.tmp / "data" / ".prompt-clock.jsonl"
        clock.write_text("\n".join([
            json.dumps({"sid": self.CLOCK_SID,
                        "ts": (now - timedelta(hours=30)).isoformat(timespec="seconds"),
                        "cmd": True}),
            json.dumps({"sid": self.CLOCK_SID,
                        "ts": (now - timedelta(minutes=5)).isoformat(timespec="seconds"),
                        "cmd": True}),
            json.dumps({"sid": self.CLOCK_SID,
                        "ts": (now - timedelta(minutes=2)).isoformat(timespec="seconds")}),
        ]) + "\n", encoding="utf-8")
        proc = self._run(SESSION_PAYLOAD, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        kept = [json.loads(l) for l in clock.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(kept), 2)

    # --- Session date

    def _assert_rejected_untouched(self, payload, *in_stderr):
        """Exit 1 naming each of ``in_stderr``, with the data dir byte-identical."""
        before = self._snapshot()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 1, msg=f"stdout={proc.stdout!r}")
        err = proc.stderr.decode()
        for text in in_stderr:
            self.assertIn(text, err)
        self.assertEqual(self._snapshot(), before)
        return err

    def test_a_date_other_than_today_is_rejected_before_any_write(self):
        """A resumed Claude Code session still remembers the day it started:
        the tutor saved one two days late under its first day's date."""
        for date_, extra in ((day(-2), {}), (day(-1), {}), (day(1), {}),
                             (day(1), {"allow_backdate": True})):
            with self.subTest(date=date_, **extra):
                payload = dict(SESSION_PAYLOAD, date=date_, **extra)
                err = self._assert_rejected_untouched(payload, date_, day(0), "date +%F")
                # Naming the opt-in here would invite the tutor to add it just
                # to clear the error, which re-files today's work under a past day.
                self.assertNotIn("allow_backdate", err)

    def test_a_malformed_date_is_rejected_before_any_write(self):
        basic = TODAY.strftime("%Y%m%d")  # date.fromisoformat accepts this form
        for date_, extra in ((basic, {}), (TODAY.strftime("%d-%m-%Y"), {}),
                             (day(0) + " ", {}), ("", {}), (None, {}), (int(basic), {}),
                             ((TODAY - timedelta(days=2)).strftime("%Y%m%d"),
                              {"allow_backdate": True})):
            with self.subTest(date=date_, **extra):
                payload = dict(SESSION_PAYLOAD, date=date_, **extra)
                self._assert_rejected_untouched(payload, repr(date_), "date +%F")

    def test_allow_backdate_must_be_a_boolean(self):
        for flag in ("true", 1, "yes", None):
            with self.subTest(allow_backdate=flag):
                payload = dict(SESSION_PAYLOAD, date=day(-1), allow_backdate=flag)
                self._assert_rejected_untouched(payload, "allow_backdate", repr(flag))

    def test_allow_backdate_records_a_past_session_on_its_own_day(self):
        make_fixtures(self.tmp / "data", last_day=-3)
        self._write_clock(9, 6, 4, 2)
        payload = dict(SESSION_PAYLOAD, date=day(-2), allow_backdate=True)
        proc = self._run(payload, CLAUDE_CODE_SESSION_ID=self.CLOCK_SID)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("Backdated", proc.stdout.decode())

        entry = self._load("session-log.json")["sessions"][-1]
        self.assertEqual(entry["date"], day(-2))
        # The clock holds only this conversation's last 24 hours, so whatever
        # it measured is today's work, not the past day's.
        self.assertNotIn("measured_minutes", entry)

        profile = self._load("learner-profile.json")
        self.assertEqual(profile["last_updated"], day(-2))
        self.assertEqual(profile["current_streak_days"], 3)  # the day after day -3
        dag = self._load("spaced-repetition.json")["items"][REVIEWED_ID]
        self.assertEqual(dag["last_reviewed"], day(-2))
        self.assertEqual(dag["due_date"], day(-2 + dag["interval_days"]))
        self.assertEqual(self._load("mistakes-db.json")["error_patterns"]["verb_spreek"]["last_seen"],
                         day(-2))

    def test_allow_backdate_cannot_reach_before_the_last_recorded_session(self):
        """Filing a day earlier than the last recorded one would rewind the
        profile's last_updated and break the streak, and would pull the review
        dates of cards already studied back into the past."""
        self._assert_rejected_untouched(
            dict(SESSION_PAYLOAD, date=day(-2), allow_backdate=True), day(-2), day(-1))
        # The last recorded day itself is still open: a second session on it.
        proc = self._run(dict(SESSION_PAYLOAD, date=day(-1), allow_backdate=True))
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(self._load("session-log.json")["sessions"][-1]["date"], day(-1))

    # --- Session id

    def test_a_recorded_session_id_is_rejected_before_any_write(self):
        """A rerun would count the session twice and overwrite its backup with
        the state after the first run, the one copy a rollback needs."""
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        # The snapshot covers .backups/, so the first run's backup must survive.
        self._assert_rejected_untouched(SESSION_PAYLOAD, "session-002", "next_session_id")
        # Ids this script never wrote are held to the same rule.
        self._assert_rejected_untouched(dict(SESSION_PAYLOAD, session_id="session-001"),
                                        "session-001")

    def test_a_session_resent_after_restoring_its_backup_counts_once(self):
        self.assertEqual(self._run(SESSION_PAYLOAD).returncode, 0)
        data = self.tmp / "data"
        for f in (data / ".backups" / "pre-update-session-002").glob("*.json"):
            shutil.copy2(f, data / f.name)
        corrected = dict(SESSION_PAYLOAD, duration_minutes=25)
        proc = self._run(corrected)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        ids = [s["session_id"] for s in self._load("session-log.json")["sessions"]]
        self.assertEqual(ids, ["session-001", "session-002"])
        stats = self._load("progress-db.json")["overall_stats"]
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_study_minutes"], 10 + 25)


if __name__ == "__main__":
    unittest.main()
