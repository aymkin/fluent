---
name: fluent-setup
description: One-time onboarding; also profile updates and reset.
allowed-tools: Read, Write, Bash, AskUserQuestion
disable-model-invocation: true
---

# Language Learning Setup

## Overview

One-time onboarding that seeds all 6 databases in the Fluent data directory. After setup, every other skill reads from those files — this is the bootstrap. Also handles profile updates and progress resets for returning users.

The data directory is resolved at runtime — never write a literal `data/` path.
`fluent_paths.py`'s module docstring documents the precedence order; always ask
it rather than reimplementing it:

```bash
FLUENT_DATA="$(python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/ensure_data_dir.py")"
```

## Instructions

### 1. Check for existing profile

Resolve the data directory first, then probe for `learner-profile.json`:

```bash
DATA_DIR="$(python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/ensure_data_dir.py")"
test -f "$DATA_DIR/learner-profile.json" && echo "exists" || echo "new"
```

If it exists, jump to **Profile updates** below. Otherwise continue.

### 2. Welcome

```markdown
# 🌍 Welcome to Your Personal Language Learning System!

This AI-powered system will help you learn any language through:
- 📊 Systematic progress tracking
- 🧠 Spaced repetition (scientifically proven)
- 🎮 Gamification (streaks, achievements)
- 📈 Adaptive difficulty
- 🎯 Personalized to YOUR goals

**Let's get you set up!** (~5 minutes)
```

### 3. Collect info

Use the `AskUserQuestion` tool to gather questions in batches when possible. Required fields:

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

Map score to level: 0-1 correct = A1, 2 = A2, 3 = B1, 4 = B2, 5 = C1.

### 4. Generate the learning plan

Compute expected months to target level:

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
## 🎉 Setup Complete!

**Your Learning Profile:**
- 👤 Name: {name}
- 🌍 Learning: {target_language}
- 📚 Native: {native_language}
- 📊 Level: {current} → {target}
- 📅 Timeline: {timeline}
- ⏱️ Daily time: {minutes} min
- 💡 Goal: {goal}

## 📋 Personalized Plan

**Estimated time:** {months} months
**Total study hours:** ~{hours} hours

### Weekly Schedule
**Daily:**
- 🔄 `/fluent-review` — spaced repetition ({X} min)
- 📚 `/fluent-vocab` — new vocabulary ({Y} min)

**Alternating:**
- 📝 `/fluent-writing` (Mon/Wed/Fri)
- 🗣️ `/fluent-speaking` (Tue/Thu/Sat)
- 📖 `/fluent-reading` (Sun)

**Weekly:**
- 📊 `/fluent-progress` — check stats (5 min)

### Milestones
- Month 1: {reasonable short-term}
- Month 3: {quarter-way}
- Month 6: {half-way}
- Target date: {target_level}!

### Next Steps
1. Start now — type `/fluent-learn`
2. Daily habit — `/fluent-review` every day
3. Weekly — `/fluent-progress` to see stats
4. Stay consistent — even 10 min daily beats 2 hours weekly

**Your journey to {target_language} fluency starts now!** 🚀
```

### 5. Write databases

Start from the templates in `data-examples/`. Resolve the target directory via `fluent_paths.ensure_data_dir()` (it creates the directory if missing), then create these 6 files inside it:

- `learner-profile.json` — fill all fields from the interview.
- `progress-db.json` — empty stats.
- `mistakes-db.json` — empty `error_patterns`.
- `mastery-db.json` — `skills` entries with `mastery_level: 0` for each skill.
- `spaced-repetition.json` — empty queues, `daily_limits.review_items_per_day: 20`.
- `session-log.json` — empty `sessions` array, `total_sessions: 0`.

Use the Write tool for each. Do not call `update-db.py` — that script is for session updates, not bootstrapping.

### 6. Optional first lesson

```markdown
## 🎓 Want to start your first lesson now?

A quick 5-10 min intro session to learn your first 10 words and get familiar with the system.

Type "yes" to start, "later" to begin on your own.
```

If yes, read `.claude/skills/fluent-learn/SKILL.md` and follow it in this session.

## Profile Updates (existing profile)

Reached when Step 1 finds an existing `learner-profile.json` — read `.claude/skills/fluent-setup/PROFILE-UPDATES.md` and follow it instead of Steps 2-6.

## Critical Rules

- **Confirm twice before reset.** "This will erase X days of progress, Y sessions, and Z mastered words. Proceed? (yes/no)".
- **Always seed all 6 files** — every other skill assumes they exist.
- **Back up before reset.** Hooks may not fire here; back up manually to `.backups/pre-reset-<timestamp>/`.
- **Don't invent data.** Start every file empty — progress, mistakes, mastery all start at zero. The system builds up from real sessions.
