---
name: fluent-setup
description: One-time onboarding; also profile updates and reset.
allowed-tools: Read, Write, Bash, AskUserQuestion
disable-model-invocation: true
---

# Language Learning Setup

## Overview

One-time onboarding that seeds the 6 databases every other skill reads. Also handles profile updates and progress resets for returning users.

## Instructions

### 1. Check for existing profile

Resolve the data directory at runtime; `fluent_paths.py` documents the precedence order, so ask it rather than reimplementing it, and write no literal `data/` path. Then probe for `learner-profile.json`:

```bash
DATA_DIR="$(python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/ensure_data_dir.py")"
test -f "$DATA_DIR/learner-profile.json" && echo "exists" || echo "new"
```

If it exists, jump to **Profile updates** below. Otherwise continue.

### 2. Welcome

```markdown
# 🌍 Добро пожаловать в твою личную систему изучения языка!

Эта система на базе ИИ поможет выучить любой язык:
- 📊 Систематический учёт прогресса
- 🧠 Интервальные повторения (научно доказанный метод)
- 🎮 Геймификация (серии, достижения)
- 📈 Адаптивная сложность
- 🎯 Под ТВОИ цели

**Давай всё настроим!** (~5 минут)
```

### 3. Collect info

Use the `AskUserQuestion` tool to gather questions in batches when possible; word each question and its options in Russian. Required fields:

1. **Name** — personalizes greetings.
2. **Target language** — the language being learned (e.g. Spanish, French, German, Japanese, Korean, Arabic, Dutch).
3. **Native language** — for translations and explanations.
4. **Other languages spoken** — optional, used to offer cross-language connections.
5. **Current level** — A1 / A2 / B1 / B2 / C1 / C2 / "not sure".
6. **Target level** — where they want to get to.
7. **Timeline** — 3 months / 6 months / 12 months / 2+ years / custom.
8. **Daily study minutes** — 10 / 15 / 30 / 60 / custom.
9. **Learning goal** — travel / work / exam (specify) / living in country / academic / family / interest.
10. **Learning style** — conversational / academic / immersive / balanced (default).
11. **Gamification on/off** — default on.

If the learner picks "not sure" for current level, run a quick 5-question assessment:

1. Basic vocabulary recognition → A1
2. Simple sentence construction → A2
3. Past tense usage → B1
4. Complex subordinate clauses → B2
5. Idiomatic expression → C1

Map score to level: 0-1 correct = A1, 2 = A2, 3 = B1, 4 = B2, 5 = C1. This is a rough heuristic. When the learner lands at A2 or B1, confirm with three "done when" tests from `.claude/references/level-b1.md`.

### 4. Generate the learning plan

Compute expected months to target level (rough planning figures, not CEFR-measured):

```
A1 → A2: ~100 hours
A2 → B1: ~150 hours
B1 → B2: ~200 hours
B2 → C1: ~300 hours
C1 → C2: ~400 hours

months = hours_needed / (daily_minutes / 60) / 30
```

Adjust:

- `-10%` time if learner's native language is typologically close to the target (e.g. Dutch ↔ English, Spanish ↔ Italian).
- `-10%` per additional language already known (cap at 30% total).

Present:

```markdown
## 🎉 Настройка завершена!

**Твой профиль:**
- 👤 Имя: {name}
- 🌍 Изучаю: {target_language}
- 📚 Родной язык: {native_language}
- 📊 Уровень: {current} → {target}
- 📅 Срок: {timeline}
- ⏱️ Время в день: {minutes} мин
- 💡 Цель: {goal}

## 📋 Персональный план

**Ориентировочное время:** {months} мес.
**Всего часов занятий:** ~{hours} ч

### Расписание на неделю
**Каждый день:**
- 🔄 `/fluent-review` — интервальные повторения ({X} мин)
- 📚 `/fluent-vocab` — новая лексика ({Y} мин)

**По очереди:**
- 📝 `/fluent-writing` (пн/ср/пт)
- 🗣️ `/fluent-speaking` (вт/чт/сб)
- 📖 `/fluent-reading` (вс)

**Раз в неделю:**
- 📊 `/fluent-progress` — проверить статистику (5 мин)

### Вехи
- Месяц 1: {reasonable short-term}
- Месяц 3: {quarter-way}
- Месяц 6: {half-way}
- Целевая дата: {target_level}!

### Что дальше
1. Начни сейчас — напиши `/fluent-learn`
2. Ежедневная привычка — `/fluent-review` каждый день
3. Раз в неделю — `/fluent-progress`, чтобы увидеть статистику
4. Регулярность — даже 10 минут в день лучше, чем 2 часа в неделю

**Твой путь к свободному владению языком ({target_language}) начинается сейчас!** 🚀
```

`{target_language}` and `{native_language}` appear as «нидерландский», «русский»; the goal and the timeline come out in Russian too.

### 5. Write databases

Start from the templates in `data-examples/`. Resolve the target directory via `fluent_paths.ensure_data_dir()` (it creates the directory if missing), then create these 6 files inside it:

- `learner-profile.json` — fill all fields from the interview.
- `progress-db.json` — empty stats.
- `mistakes-db.json` — empty `error_patterns`.
- `mastery-db.json` — `skills` entries with `mastery_level: 0` for each skill.
- `spaced-repetition.json` — empty queues.
- `session-log.json` — empty `sessions` array, `total_sessions: 0`.

Use the Write tool for each; `update-db.py` serves session updates, so bootstrapping writes the files directly. Every file starts empty, and the system builds up from real sessions.

### 6. Optional first lesson

```markdown
## 🎓 Начнём первый урок прямо сейчас?

Короткое вводное занятие на 5–10 минут: выучим первые 10 слов и познакомимся с системой.

Напиши "yes", чтобы начать, или "later", чтобы начать самостоятельно.
```

If yes, read `.claude/skills/fluent-learn/SKILL.md` and follow it in the same session.

## Profile Updates (existing profile)

Reached when §"Check for existing profile" finds an existing `learner-profile.json` — read `.claude/skills/fluent-setup/PROFILE-UPDATES.md` and follow it instead of §"Welcome" through §"Optional first lesson".
