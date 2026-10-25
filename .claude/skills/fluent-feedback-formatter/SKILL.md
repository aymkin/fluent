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

**Исправления:**
- ❌ "{wrong_part}" → **"{correct_part}"** ({category} — {brief_why})
- ✅ "{correct_part}" — {specific_praise}

**Правильный вариант:**
"{full_correct_sentence}"

**Оценка: {X}/10** {emoji} {short_comment}

---
```

Skip the ❌ block if the answer is fully correct. Skip the ✅ block only if truly nothing was right (rare — usually at least word order or intent was right). Otherwise use the shape exactly, labels included: they are literal Russian text. Deviations break session-file parsing downstream.

### 2. Prompt before recast

In a one-decision exercise — a `/fluent-review` item, a `/fluent-learn` drill or a `/fluent-vocab` cell — a miss in the place the exercise tests gets a prompt before the answer. A prompt makes the learner retrieve the form; a recast hands it over, and in classroom studies prompts work better (Lyster & Saito 2010, a meta-analysis of 15 studies).

1. Name where the error is — its category or its place in the sentence — and leave the form for the learner to find: «Посмотри, где стоит глагол.» Ask for one more try.
2. The prompt line carries no ✅, ❌ or severity marker, and the item counter stays put: the retry belongs to the same item.
3. After the retry, give the standard template once. Its ❌ line records the first attempt; a ✅ line may credit the self-correction. The **Оценка** is the first attempt's — the retry is practice, not evidence for the scheduler.

In the session file, write both attempts on the answer line: `**Your answer:** "{first}" → (after prompt) "{retry}"`.

### 3. Tag severity on every error

| Symbol | Severity | Meaning | Example |
|--------|----------|---------|---------|
| 🔴 | Critical | Breaks communication or exam-blocker | Formal/informal mix in formal email; a sentence the reader cannot decode |
| 🟡 | Moderate | Noticeable but understandable | Subordinate-clause word order with the meaning intact, preposition error, missing article |
| 🟢 | Minor | Low priority | Spelling, punctuation, accent marks |

A severity tag is mandatory on every ❌ line; a single answer may contain multiple errors of different severity, so tag each. Severity is stored on the pattern in `mistakes-db` when it is first recorded, and `fluent-session-analyzer` weighs it when planning. It does not set review priority.

### 4. Use these category labels

These are the ten labels `errors[].category` accepts on the way into
`mistakes-db.json`. `update-db.py` enforces the set — an off-canon label exits `1`
before any database is written.

The `({category} — {brief_why})` slot of the chat template shows the Russian name
given in brackets; the session file's ❌ lines and `errors[].category` carry the id.

- `grammar` (грамматика) — word order, conjugation, clause structure
- `formal_informal` (формальность) — u/je, uw/jouw, register mismatch
- `vocabulary` (лексика) — wrong word, English mixing, register-wrong synonym
- `spelling` (орфография) — minor
- `prepositions` (предлоги) — om/op/in/bij/naar/etc.
- `articles` (артикли) — de/het, definite/indefinite
- `missing` (пропуск) — omitted greeting, closing, required word
- `structure` (структура) — organisation, flow, paragraphing
- `comprehension` (понимание) — misread what the text says
- `inference` (вывод) — failed to draw what the text implies

A B1 grammar target from `.claude/references/level-b1.md` is category `grammar`; give its `pattern_id` the target's name (e.g. `bijzin_omdat_word_order`) so the drill pool and `/fluent-progress` find it.

`other` is the eleventh accepted value, not one of the ten: it stays accepted
because `update-db.py` already writes it as the default when a payload omits the
key.

### 5. Tone rules

- **Encourage before correcting.** Open with a ✅ or a warm ❌ (`«Почти! Поправим одно слово.»`), not a bare `«Неверно.»`.
- **Explain why, not just what.** `"Ik schrijf je" → "Ik schrijf u" (формальность — в деловых письмах нужно u)` beats `«Пиши u, а не je.»`. The why is a true reason; for a convention, say «так принято» and set it against the Russian.
- **Correct the whole chunk.** A wrong partner word is corrected as the chunk it belongs to: `"koffie maken" → "koffie zetten"` (лексика — чанк `koffie zetten`, по-русски «варить кофе»).
- **Name the pattern.** Helps the learner generalize: `«Это правило порядка слов с omdat: глагол в конце.»`.
- **Celebrate progress.** `«В прошлый раз здесь ошибок не было — отлично!»` when `mistakes-db` shows improvement.
- **Russian or Dutch.** Every word the learner reads is in their native language (Russian) or the target language (Dutch): greeting, exercise, labels, feedback, menu, summary. The labels in a skill's templates are literal text, copied as written. Language names in headers and tables (`{target_language}`, `{native_language}`) come out as «нидерландский», «русский». English stays in these instructions, in the session file's markers (`results/README.md` §"Key parsing markers"), in the category ids, and in the typed cues (`go`, `rewrite`, `ready`, `yes`, `later`, `all`, `none`).
- **Neutral Russian.** The learner's gender is not on record: «Твой ответ», «Здесь ошибок не было», never a past-tense form that carries gender.
- **Emojis on.** The learner's profile has `use_emojis: true` by default. Keep them.

### 6. Hand score to the scheduler

After scoring, feed the score into the scheduler via the `fluent-db-updater` skill; see `fluent-fsrs-reference` for the pipeline.

## Critical Rules

- **One score per answer.** Total out of 10, with optional breakdown (grammar/vocab/structure) for long answers like writing tasks.
- **Always include the «Правильный вариант»**, even after a perfect answer; echoing the target form reinforces motor memory.
