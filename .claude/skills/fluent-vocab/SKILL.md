---
name: fluent-vocab
description: Run an interactive vocabulary drill session with flashcard-style prompts, spaced repetition, and per-answer feedback. Triggered only when the learner types /fluent-vocab. Reads spaced-repetition / mistakes / mastery DBs to pick words, presents one word at a time, scores each answer, and calls fluent-db-updater at the end.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Vocabulary Drill Session

## Overview

Flashcard-style vocabulary practice using spaced repetition. One word at a time, immediate feedback, DB update at the end. Interleaves three modes (recognition, production, cloze) to force active recall rather than passive re-reading.

## When to Use

Skip this skill if no vocabulary items are due and no new words are queued — offer `/fluent-review` or `/fluent-learn` instead.

## Instructions

### 1. Load vocabulary data

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

If the helper is unavailable, resolve `<data_dir>` via `fluent_paths.data_dir()` then read:

- `<data_dir>/spaced-repetition.json`
- `<data_dir>/mistakes-db.json`
- `<data_dir>/mastery-db.json`
- `<data_dir>/learner-profile.json` (for target_language, name, level)

If any are missing, direct the learner to `/fluent-setup` and stop.

### 2. Select words

Priority order:

1. Items in `spaced-repetition.review_queue.today` with `item_type == "vocabulary"`.
2. Words from `mistakes-db.json` where `category == "vocabulary"` and `mastery_level <= 2`.
3. New high-frequency words matching `learner-profile.focus_areas`.

Limit: `spaced-repetition.daily_limits.review_items_per_day` (default 20).

### 3. Present one word at a time

```markdown
## Word {N}/{total}

{the prompt — see the three modes below}

**Type your answer:**
```

Rotate the three modes so the session is not monotonous:

- **Recognition** (target → native) — show the word plus a `**Context:**` example sentence, ask what it means.
- **Production** (native → target) — show the native word, ask how to say it, invite an optional sentence.
- **Cloze** — show a target-language sentence with `_____` where the word goes, ask for the missing word.

### 4. Feedback after each answer

Use the `fluent-feedback-formatter` skill's template. Score out of 10, tag severity.

Track the answer for the end-of-session DB update:

- Add to `review_results[]` with `quality = floor(score / 2)` (see `fluent-fsrs-reference` skill).
- If the learner met a new word, stage it for `new_vocabulary[]`.
- If the learner made an error, stage it for `errors[]`.

Do **not** call `update-db.py` after every word — batch at session end.

### 5. Session summary

```markdown
## 📚 Vocabulary Session Complete!

**Words Reviewed:** {N}
**Accuracy:** {X}%
**New Words Learned:** {Y}
**Words Mastered (→ level 5):** {Z}

**Strong:** {list words with mastery 4-5}
**Need more practice:** {list words with mastery 0-2}

**Next review:**
- Tomorrow: {count} words
- This week: {count} words

{target-language "well done"}! 🌟
```

### 6. Update all databases

Call the `fluent-db-updater` skill's workflow — one `update-db.py` invocation with:

- `session_id`, `date`, `duration_minutes`
- `command_used: "/fluent-vocab"`
- `skills_practiced: ["vocabulary"]`
- `skill_scores.vocabulary`: `{exercises, correct, time_minutes}`
- `errors[]`, `new_vocabulary[]`, `review_results[]` collected during the session
- `focus_next_session[]` — top 2-3 weak words

## Critical Rules

- **One word at a time.** Wait for the learner's answer before showing the next.
- **Immediate feedback** after each — use `fluent-feedback-formatter`.
- **Mix modes.** Don't drill 20 recognition prompts in a row — interleave for discrimination.
- **Use target language** for greetings + transitions when the learner is B1+; for A1-A2 mix target + native.
- **Never** update the DBs mid-session — batch at end.
- **Never auto-invoke.** This skill is gated; must fire only on explicit `/fluent-vocab`.
