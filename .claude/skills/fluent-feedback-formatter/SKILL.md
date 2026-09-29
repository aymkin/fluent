---
name: fluent-feedback-formatter
description: 'Canonical feedback shape for every graded learner answer: corrections with category and severity, the full correct version, a score out of 10. Use after the learner submits an answer in any practice session.'
---

# Feedback Formatter

## Overview

One feedback shape for every graded answer. The learner builds mental models from its structure, and `fluent-session-analyzer` mines session files for its markers (❌, ✅, severity emoji), so the shape stays fixed.

## When to Use

Load this skill whenever the tutor grades a learner answer in any practice skill, and whenever it classifies an error by severity or category.

Skip this skill for non-feedback output (greetings, summaries, progress reports).

## Instructions

### 1. Standard template

```markdown
{✅ or ❌} {one-line encouragement or gentle correction}

**Corrections:**
- ❌ "{wrong_part}" → **"{correct_part}"** ({category} — {brief_why})
- ✅ "{correct_part}" — {specific_praise}

**Correct version:**
"{full_correct_sentence}"

**Score: {X}/10** {emoji} {short_comment}

---
```

Skip the ❌ block if the answer is fully correct. Skip the ✅ block only if truly nothing was right (rare — usually at least word order or intent was right). Otherwise use the shape exactly. Deviations break session-file parsing downstream.

### 2. Tag severity on every error

| Symbol | Severity | Meaning | Example |
|--------|----------|---------|---------|
| 🔴 | Critical | Breaks communication or exam-blocker | Formal/informal mix in formal email; a sentence the reader cannot decode |
| 🟡 | Moderate | Noticeable but understandable | Subordinate-clause word order with the meaning intact, preposition error, missing article |
| 🟢 | Minor | Low priority | Spelling, punctuation, accent marks |

A severity tag is mandatory on every ❌ line; a single answer may contain multiple errors of different severity, so tag each. Severity is stored on the pattern in `mistakes-db` when it is first recorded, and `fluent-session-analyzer` weighs it when planning. It does not set review priority.

### 3. Use these category labels

These are the ten labels `errors[].category` accepts on the way into
`mistakes-db.json`. `update-db.py` enforces the set — an off-canon label exits `1`
before any database is written.

- `grammar` — word order, conjugation, clause structure
- `formal_informal` — u/je, uw/jouw, register mismatch
- `vocabulary` — wrong word, English mixing, register-wrong synonym
- `spelling` — minor
- `prepositions` — om/op/in/bij/naar/etc.
- `articles` — de/het, definite/indefinite
- `missing` — omitted greeting, closing, required word
- `structure` — organisation, flow, paragraphing
- `comprehension` — misread what the text says
- `inference` — failed to draw what the text implies

A B1 grammar target from `.claude/references/level-b1.md` is category `grammar`; give its `pattern_id` the target's name (e.g. `bijzin_omdat_word_order`) so the drill pool and `/fluent-progress` find it.

`other` is the eleventh accepted value, not one of the ten: it stays accepted
because `update-db.py` already writes it as the default when a payload omits the
key.

### 4. Tone rules

- **Encourage before correcting.** Open with a ✅ or a warm ❌ (`"Close! Let's tune one word."`), not a bare `Wrong.`.
- **Explain why, not just what.** `"Ik schrijf je" → "Ik schrijf u" (formal_informal — business emails require u)` beats `"Use u not je."`.
- **Name the pattern.** Helps the learner generalize: `"This is the omdat word-order rule: verb goes last."`.
- **Celebrate progress.** `"You didn't miss this last time — well done."` when `mistakes-db` shows improvement.
- **Write in the learner's language.** Every message — greeting, exercise, feedback, summary — goes in the language they write to you in. The templates in these skills say what a message carries, not which words to use.
- **Emojis on.** The learner's profile has `use_emojis: true` by default. Keep them.

### 5. Hand score to the scheduler

After scoring, feed the score into the scheduler via the `fluent-db-updater` skill; see `fluent-fsrs-reference` for the pipeline.

## Critical Rules

- **One score per answer.** Total out of 10, with optional breakdown (grammar/vocab/structure) for long answers like writing tasks.
- **Always include the "Correct version"**, even after a perfect answer; echoing the target form reinforces motor memory.
