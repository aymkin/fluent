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
# 📊 {learner_name}: дашборд изучения языка — {target_language}

**Обновлено:** {today}

## 🎯 Обзор

**Уровень:** {current_level} → {target_level} · {progress_bar} {percentage}%
**Серия:** 🔥 {streak_days} {day_or_days} {streak_message}
**Всего:** {total_sessions} сессий · {total_minutes} мин ({hours} ч) за {total_days} дней

## 💪 Освоение навыков

Один блок на каждый практиковавшийся навык (письмо ✍️ / говорение 🗣️ / лексика 📚 / чтение 👀):

### {Skill} {emoji}
**Уровень:** {n}/5 {stars} · **{Точность|Понимание}:** {percent}% · **Последняя практика:** {date}
{progress_bar}

У лексики есть ещё **Слов известно** / **Слов освоено**.

## 📈 Динамика

ASCII-график точности из `progress-db.weekly_summary`, затем эта неделя:
{sessions} сессий · {minutes} мин · {exercises} упражнений · {percent}% · навыки: {list}

## 🎯 Над чем работать

Сгруппируй `mistakes-db.error_patterns` по освоению: 🔴 Критично (0-1, высокая частота),
🟡 В работе (2-3), 🟢 Сильное (4-5).

When `target_level` is B1, add one line per grammar target in `.claude/references/level-b1.md`: ✅ готово (its pattern in `mistakes-db` at mastery 4-5), 🔄 в работе (mastery 1-3), ⬜ ещё не встречалось (no pattern). Это цели курса, а не официальные требования CEFR.

## 🔄 Интервальные повторения

**На сегодня:** {count} · **На этой неделе:** {count} · **Освоено:** {count}

## 🏆 Достижения

{list from learner-profile → achievements; if empty, say so — achievements are
earned from the milestones recorded at session end, there is no fixed catalogue}

## 📅 История сессий

| Дата | Длительность | Навык | Точность |
|------|----------|-------|----------|
{most recent 5-10 sessions from session-log}

## 🎯 Цели и рекомендации

**На этой неделе:** {weak patterns + due reviews} · **В этом месяце:** {skill mastery gaps}
· **Надолго:** {target level gap}

1. {top weak area from mistakes-db}
2. {skill not practiced recently}
3. {due review count if > 0}

"{personalized motivational message}"
```

Fill the placeholders in Russian: `{Skill}` as «Письмо», «Говорение», «Лексика», «Чтение», «Аудирование», «Грамматика»; `{target_language}` and `{native_language}` as «нидерландский», «русский»; `{day_or_days}` as «день», «дня» or «дней» by the Russian rule (1 день, 2–4 дня, 5–20 дней, 21 день).

### 3. Optional interpretation footer

Only when the learner seems new or asks what the numbers mean — append the footer in `.claude/skills/fluent-progress/STATS-GLOSSARY.md`.

## Critical Rules

- **Read-only.** Leave `update-db.py` and every JSON in the data directory untouched.
- **Streak** is `learner-profile.current_streak_days` as stored.
- **Every number comes from a database.** A skill with no data reads «Ещё не практиковалось».
