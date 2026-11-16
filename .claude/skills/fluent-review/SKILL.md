---
name: fluent-review
description: Daily FSRS review — one round of today's due items, one decision per exercise.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Spaced-Repetition Review Session

## Overview

Replay items the learner learned before, timed to hit just before the forgetting curve drops them. Right answers push an item further out; a miss resets it and brings it back within a few days.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-review` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load review queue

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py" --review
```

The queue comes back as one round: today's due items, the least likely to be recalled first — cards never reviewed, then the lowest FSRS retrievability — cut to the review round (`computed.review_round`) and expanded to just the items you will use.

The output is about 20 KB: read it straight from the command's result.

`computed.due_reviews_count` counts everything due today. Whatever this round leaves out stays due and leads the next round.

If the queue is empty:

```markdown
🎉 На сегодня повторений нет! Интервальные повторения в порядке.

Хочешь позаниматься чем-то новым? Попробуй:
- `/fluent-learn` — смешанная адаптивная практика
- `/fluent-vocab` — слова из Anki: чанки, лица, времена
- `/fluent-progress` — твоя статистика
```

### 2. Opening

The opening turn is the greeting and item 1. Greet the learner by name, give the round's size, its minutes (about one per item) and how many items wait for later rounds, then present item 1.

### 3. Generate one exercise per item

**Build each exercise in the turn that presents it.** The only work done ahead of item 1: settle the round's order and note every card's `answer` words, so that until a card is graded its words stay out of every other prompt.

Each item has:

```json
{
  "item_id": "...",
  "item_type": "error_pattern | vocabulary | grammar_rule",
  "interval_days": 6,
  "repetitions": 2,
  "due_date": "YYYY-MM-DD",
  "priority": "critical | high | medium | low",
  "fsrs_difficulty": 7.24,
  "stability": 1.95,
  "content": "...",
  "answer": "..."
}
```

**Every exercise is one decision.** The learner's answer differs from your prompt in exactly the place this item tests, and nowhere else; build the rest out of forms they already own. Count the decisions your prompt demands before you send it — at two or more, cut it down.

**Its rung sets the help.** Each item comes with its `rung`; build the prompt from that rung's row in `.claude/references/fading.md`.

Match the exercise to `item_type`:

- **error_pattern**: load the pattern from `mistakes-db` and build a scenario that forces the correct form. Keep that form out of the prompt — naming it is the whole test.
- **vocabulary**: recognition (target → native), production (native → target), or cloze — rotate the direction; the rung sets the help.
- **grammar_rule**: cloze, or find the one error (a `scaffold` exercise).

Once an `error_pattern` or `grammar_rule` item that names a target in `.claude/references/level-b1.md` reaches `mastery_level` 3, switch to that target's "done when" test, as that file defines "done".

Present one item, wait for the answer, then the next; a rushed item scores as a false positive. Cards that test one rule — two zijn-perfectum cards, say — stand apart in the round, with other cards between them, so the first does not answer the second. Each prompt carries its place in the round (`Задание {N}/{round size}`), the item type as «ошибка», «слово» or «правило», days since last review, current mastery, `fsrs_difficulty`, and the rung's label from `fading.md`.

### 4. Evaluate + submit the score

Use the `fluent-feedback-formatter` skill for per-answer feedback.

Then stage the item for the end-of-session update through `review_results[]` in the `fluent-db-updater` payload. `update-db.py` rebuilds the queue on every call, so a hand edit to `spaced-repetition.json` is overwritten:

```json
{ "item_id": "vocab_huis", "quality": 4 }
```

The `update-db.py` script maps the quality to an FSRS rating and reschedules via FSRS-6 (see `fluent-fsrs-reference` skill). A low score is not a failure to hide: `quality <= 2` resets `repetitions`, takes `mastery_level` down to 2 or less, and brings the item back within a few days — 1 day for a young item, longer for a well-established one — which is exactly the signal the scheduler needs.

### 5. Progress pulse every 5 items

One line: `Готово {done}/{round size} · точность {X}% · осталось ≈{K} мин`.

### 6. Session summary

The round's last graded item gets its feedback first, then the returns of its misses (`fluent-feedback-formatter` §2, step 4); the summary follows the last return's answer.

Give: how many were reviewed, accuracy, minutes spent. Then the breakdown — «чисто» (gone for a while), «мелкие промахи» (back in X days), «пропущено» (back within a few days) — followed by how many fall due tomorrow, this week, and next week, the streak, and one line of advice pitched at today's accuracy.

### 7. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-review"`, `skills_practiced: [derived from reviewed items]`
- `skill_scores` — aggregate per skill touched
- `review_results[]` — every item reviewed, with `quality`
- `errors[]` — only patterns where the learner got it wrong (bumps frequency; a pattern this round did not review takes a missed review on its card)
- `focus_next_session[]` — the 2-3 items with lowest quality this session
- `session_notes` — `Повторено: {Y}/{N}, точность {X}%.`

Save the transcript as `fluent-review-session-{NNN}.md` in the `results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`.

### 8. Offer another round

With the update and the transcript saved, and items still due, offer the next round of `{review_round}` as the command to type: «Ещё раунд — набери `/fluent-review`». The command opens a new session with its own record and its own start mark for the prompt clock; a round started without it runs on the previous round's clock.

## Critical Rules

- **Let the learner struggle.** If they don't remember, that is useful data (quality 0-2) — the algorithm needs honest signals. A guess scored as knowledge pushes the item weeks out and takes the schedule with it, so when the learner says they guessed, score the guess.
- **Daily.** The spacing assumes a session every day. After a gap the backlog comes back round by round, the most forgotten first; one round is a full session.

## What the Schedule Means

If the learner asks what their next-review intervals mean — read `.claude/skills/fluent-review/SCHEDULE-MEANING.md` and answer from there.
