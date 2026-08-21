# Language Learning System - AI Guide

How to run a Fluent practice session: what state to load, how to schedule
reviews, what to write at the end. The teaching principles and the tutor's
personality live in `CLAUDE.md`; each command's flow lives in its own
`.claude/skills/<name>/SKILL.md`, which is what Claude Code actually loads.
This document does not restate either.

---

## 📁 Data Files You Must Use

### Core Databases (JSON files in the resolved data directory)

| File | Purpose | When to Read |
|------|---------|--------------|
| `learner-profile.json` | Learner info, preferences, current level, streak | **Every session start** |
| `progress-db.json` | Overall statistics, skill progress, trends | **Every session start** |
| `mistakes-db.json` | Error patterns with frequency, mastery, examples | **Before generating exercises** |
| `mastery-db.json` | Skill mastery levels (0-5 scale) | **Before exercise selection** |
| `spaced-repetition.json` | Review queue, scheduling, FSRS-6 parameters | **Every session start** |
| `session-log.json` | Session history, notes, recommendations | Session start (for context) |

Read all six in one call with `.claude/hooks/read-db.py`. **All six are written by
`.claude/hooks/update-db.py`, once, at session end** — never by hand. That script
owns the counters, the accuracy averages, the error-pattern examples and every
`mastery_level`; a hand-written value will diverge from what it recomputes. Stage
each answer during the session, then submit one payload via the
`fluent-db-updater` skill.

### Session Result Files (`/results` directory)

`fluent-{skill}-session-{NNN}.md`, e.g. `fluent-writing-session-042.md`. `NNN` is
the global session counter, matching `session_id` in `session-log.json`.
**`results/README.md` is the canonical spec** for the file name, the required
section structure, and the exact markers the `fluent-session-analyzer` skill
parses. Follow it verbatim — deviations break next-session planning.

---

## 🎯 How to Start Every Session

### Step 1: Load learner context

```bash
python3 .claude/hooks/read-db.py
```

### Step 2: Greet personally

```
"{Greeting in target language}, {learner_name}! 👋

Welcome back! You're on a {streak_days}-day streak! 🔥

Today's focus:
📝 {skill_name} practice ({mastery_level}/5 ⭐)
🔄 {review_count} items due for review

Ready? Let's make today count!"
```

### Step 3: Check the review queue

From `spaced-repetition.json`:
- Load `review_queue.today` items
- Prioritize by `priority` field (critical > high > medium > low)
- Limit to `daily_limits.review_items_per_day` (default: 20)

### Step 4: Generate a session plan

Based on review items due today, `learner-profile.focus_areas`, skill balance
(practice all 4 skills weekly), and `learner-profile.daily_goal_minutes`.

Grade every answer with the `fluent-feedback-formatter` skill — it owns the
per-answer template, the category labels and the 🔴/🟡/🟢 severity scale.

---

## 🔄 Spaced Repetition (FSRS-6)

Scheduling is owned by `.claude/hooks/fsrs.py` (a stdlib FSRS-6 port) and invoked
by `.claude/hooks/update-db.py`. **Never compute intervals by hand** — unlike the
old SM-2 formula, FSRS-6 uses 21 fitted weights plus per-item `stability` and
`fsrs_difficulty`, so any manual calculation will diverge from the code. You submit
a score; `update-db.py` maps it to an FSRS rating (1-4), calls `fsrs.schedule(...)`,
updates `stability` / `fsrs_difficulty` / `interval_days` / `due_date`, advances
`consecutive_correct` / `mastery_level`, and rebuilds the review queue. See the
`fluent-fsrs-reference` skill for the full pipeline, the score→quality scale and the
field list.

---

## 🎮 Gamification

- **Streaks are real.** `learner-profile.current_streak_days` is maintained by
  `update-db.py`; always read the stored value rather than assuming an increment.
- **Achievements are hand-authored.** `learner-profile.achievements[]` is written
  only from the `milestones[]` you put in the session payload — nothing awards
  them automatically. Only claim a milestone the learner actually earned.
- **Visualization** (progress bars, 0-5 ⭐ mastery) is rendered by the
  `fluent-progress` skill; that skill is the reference for the format.

---

## 🎯 Session End Protocol

1. **Calculate session statistics** — duration, exercises completed, accuracy
   rate, topics covered, breakthroughs, areas needing work.

2. **Write all six databases in one shot** via the `fluent-db-updater` skill.
   `update-db.py` appends the `session-log` entry and derives the profile's
   `total_sessions`, `total_study_minutes`, `current_streak_days` and
   `skills.{skill_name}.last_practiced` itself — pass the session payload, don't
   compute or edit those fields.

3. **Save the session result file** — `/results/fluent-{skill}-session-{NNN}.md`,
   with all exercises, errors and feedback, plus the error-pattern and strengths
   tables. See `results/README.md` for the exact structure.

4. **Show the session summary**:

```markdown
## 🎉 Session Complete!

**Today's Stats:**
- Duration: {X} minutes
- Exercises: {Y} completed
- Accuracy: {Z}%
- Improvement: +{N}% from start!

**Breakthroughs:** ✨
- {What they mastered or improved}

**Focus for Next Time:**
- {What to practice next}

**Streak:** 🔥 {current_streak} days! Keep it going!  _(use "day" when `current_streak == 1`, else "days")_

See you tomorrow for review! Goed gedaan! 👏
```

**NOTE:** Use the CURRENT streak value from `learner-profile.json` — do not guess
or assume an increment.
