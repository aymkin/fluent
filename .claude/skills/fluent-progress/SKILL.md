---
name: fluent-progress
description: Progress dashboard — stats, mastery levels, streak, achievements. Use when the learner asks how they are doing.
allowed-tools: Read, Bash
---

# Progress Dashboard

## Overview

Show the learner a comprehensive, personalized progress report with visual statistics, skill mastery levels, trends, and next goals. This is read-only: do not modify any database files.

## When to Use

Skip this skill when the learner is mid-practice — the ongoing session skill already shows per-turn feedback, and opening the full dashboard interrupts the flow.

## Instructions

### 1. Load all 6 databases

Prefer the helper script over manual Read calls:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

This returns a single JSON with all 6 databases + computed fields (`due_reviews_count`, `next_session_id`, `streak_active`).

If the helper is unavailable, fall back to reading each file directly. Resolve the data directory via `fluent_paths.data_dir()` first — do NOT hardcode `data/` (plugin installs store data under `~/.claude/fluent-data/`):

- `<data_dir>/learner-profile.json`
- `<data_dir>/progress-db.json`
- `<data_dir>/mastery-db.json`
- `<data_dir>/mistakes-db.json`
- `<data_dir>/spaced-repetition.json`
- `<data_dir>/session-log.json`

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

Append this only if the learner seems new or asks what the numbers mean:

```markdown
## 📖 How to Read Your Stats

**Mastery Levels:**
- ⭐☆☆☆☆ (1/5): Just started
- ⭐⭐☆☆☆ (2/5): Learning
- ⭐⭐⭐☆☆ (3/5): Good
- ⭐⭐⭐⭐☆ (4/5): Strong
- ⭐⭐⭐⭐⭐ (5/5): Mastered

**Accuracy bands:** 0-40% intensive, 40-60% learning, 60-75% good, 75-85% strong, 85%+ excellent.
```

## Critical Rules

- **Read-only.** Never call `update-db.py` or edit any JSON in `data/`.
- **Use the current streak value** from `learner-profile.json`. Never guess or increment.
- **Use `day` vs `days`** correctly (1 = day, else days).
- **Skip sections with no data.** If speaking hasn't been practiced, show "Not yet practiced" — don't fabricate numbers.
- **Cite the learner by name** from `learner-profile.json`.
- **Use target-language greetings** where natural (e.g. "Goed gedaan!" for Dutch).
