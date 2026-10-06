---
name: fluent-progress
description: Progress dashboard — stats, mastery levels, streak, achievements. Use when the learner asks how they are doing.
allowed-tools: Read, Bash
---

# Progress Dashboard

## Overview

A progress report: skill mastery, trends, weak patterns, reviews due, next goals.

## When to Use

Skip this skill when the learner is mid-practice — the ongoing session skill already shows per-turn feedback, and opening the full dashboard interrupts the flow.

## Instructions

### 1. Load all 6 databases

Prefer the helper script over manual Read calls:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

This returns a single JSON with all 6 databases + computed fields (`due_reviews_count`, `next_session_id`, `streak_active`, `session_cap`).

If the helper is unavailable, read the six JSON files directly from `fluent_paths.data_dir()`; plugin installs keep them under `~/.claude/fluent-data/`, not `data/`.

If any are missing, point the learner at `/fluent-setup` and stop.

### 2. Generate the report

Use this exact structure. Fill in values from the databases; compute percentages and progress bars yourself.

```markdown
# 📊 {learner_name}'s {target_language} Learning Dashboard

**Last Updated:** {today}

## 🎯 Overview

**Level:** {current_level} → {target_level} · {progress_bar} {percentage}%
**Streak:** 🔥 {streak_days} {day_or_days} {streak_message}
**Total:** {total_sessions} sessions · {total_minutes} min ({hours} h) over {total_days} days

## 💪 Skills Mastery

One block per skill practised (writing ✍️ / speaking 🗣️ / vocabulary 📚 / reading 👀):

### {Skill} {emoji}
**Level:** {n}/5 {stars} · **{Accuracy|Comprehension}:** {percent}% · **Last practiced:** {date}
{progress_bar}

Vocabulary also gets **Words known** / **Words mastered**.

## 📈 Progress Trends

ASCII accuracy chart from `progress-db.weekly_summary`, then this week:
{sessions} sessions · {minutes} min · {exercises} exercises · {percent}% · skills: {list}

## 🎯 Focus Areas

Group `mistakes-db.error_patterns` by mastery: 🔴 Critical (0-1, high frequency),
🟡 Working on (2-3), 🟢 Strong (4-5).

When `target_level` is B1, add one line per grammar target in `.claude/references/level-b1.md`: ✅ done (its pattern in `mistakes-db` at mastery 4-5), 🔄 drilling (mastery 1-3), ⬜ not yet met (no pattern). These are course goals, not official CEFR requirements.

## 🔄 Spaced Repetition

**Due today:** {count} · **Due this week:** {count} · **Mastered:** {count}

## 🏆 Achievements

{list from learner-profile → achievements; if empty, say so — achievements are
earned from the milestones recorded at session end, there is no fixed catalogue}

## 📅 Session History

| Date | Duration | Skill | Accuracy |
|------|----------|-------|----------|
{most recent 5-10 sessions from session-log}

## 🎯 Next Goals & Recommendations

**This week:** {weak patterns + due reviews} · **This month:** {skill mastery gaps}
· **Long-term:** {target level gap}

1. {top weak area from mistakes-db}
2. {skill not practiced recently}
3. {due review count if > 0}

"{personalized motivational message}"
```

### 3. Optional interpretation footer

Only when the learner seems new or asks what the numbers mean — append the footer in `.claude/skills/fluent-progress/STATS-GLOSSARY.md`.

## Critical Rules

- **Read-only.** Leave `update-db.py` and every JSON in the data directory untouched.
- **Streak** is `learner-profile.current_streak_days` as stored.
- **Every number comes from a database.** A skill with no data reads "Not yet practiced".
