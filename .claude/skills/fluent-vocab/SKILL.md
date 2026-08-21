---
name: fluent-vocab
description: Flashcard-style vocabulary drill.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Vocabulary Drill Session

## Overview

Flashcard-style vocabulary practice using spaced repetition. Interleaves three modes (recognition, production, cloze) to force active recall rather than passive re-reading.

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

Stage the answer for the `fluent-db-updater` skill to write:

- Stage it for `review_results[]` with the `quality` for this score — see the `fluent-fsrs-reference` skill.
- If the learner met a new word, stage it for `new_vocabulary[]`.
- If the learner made an error, stage it for `errors[]`.

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
- `errors[]`, `new_vocabulary[]`, `review_results[]` — the entries staged per answer
- `focus_next_session[]` — top 2-3 weak words

Save the session file to `/results/fluent-vocab-session-{NNN}.md` — structure
per `results/README.md`. Every `❌` line carries its category and its severity
emoji; without them `fluent-session-analyzer` cannot parse the session.

## Critical Rules

- **Mix modes.** Don't drill 20 recognition prompts in a row — interleave for discrimination.
- **Use target language** for greetings + transitions when the learner is B1+; for A1-A2 mix target + native.
