---
name: fluent-review
description: Today's FSRS review queue.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Spaced-Repetition Review Session

## Overview

Replay items the learner learned before, timed so they hit just before the forgetting curve drops them. This is the single most effective session type — the system depends on it running daily. Items the learner gets right get pushed further into the future; items they miss come back tomorrow.

Write every message in the language the learner writes to you in. The blocks below say what each message must carry, not which words to use.

## Instructions

### 1. Load review queue

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py" --review
```

The queue comes back sorted by `priority` and cut to `daily_limits.review_items_per_day`, expanded to just the items you will actually use.

**`computed.due_reviews_count` is the real number due, and it can exceed the queue you received.** Everything past the cut is not postponed — it is simply never served today, lowest priority first. When the two numbers differ, open with both and name what got cut. A backlog the learner cannot see is a backlog nobody triages; if the overflow repeats for several days, offer to raise `review_items_per_day`.

If the queue is empty:

```markdown
🎉 No reviews due today! Your spaced repetition is up to date.

Want to practice something new? Try:
- `/fluent-learn` — adaptive mixed practice
- `/fluent-vocab` — learn new words
- `/fluent-progress` — see your stats
```

### 2. Opening

Greet the learner by name and give: items due today (plus the overflow, if any), the estimated minutes, and one line on why review works — it interrupts forgetting just before it happens. Then start.

### 3. Generate one exercise per item

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

**Every exercise is one decision.** The learner's answer differs from your prompt in exactly the place this item tests, and nowhere else; build the rest out of forms they already own. Count the decisions your prompt demands before you send it — at two or more, cut it down. An item that tests one thing inside a sentence that demands ten tells you nothing about that one thing.

Match the exercise to `item_type`:

- **error_pattern**: load the pattern from `mistakes-db` and build a scenario that forces the correct form. Keep that form out of the prompt — naming it is the whole test.
- **vocabulary**: recognition (target → native), production (native → target), or cloze — rotate modes.
- **grammar_rule**: cloze, or find the one error.

Present one at a time — rushing = false positives. Each prompt carries its number in the session, the item type, days since last review, current mastery, and `fsrs_difficulty`.

### 4. Evaluate + submit the score

Use the `fluent-feedback-formatter` skill for per-answer feedback.

Then stage the item for the end-of-session update. Do NOT hand-edit `spaced-repetition.json` — the queue is rebuilt on every `update-db.py` call; use `review_results[]` in the `fluent-db-updater` payload:

```json
{ "item_id": "vocab_huis", "quality": 4 }
```

The `update-db.py` script maps the score to an FSRS rating and reschedules via FSRS-6 (see `fluent-fsrs-reference` skill). A low score is not a failure to hide: `quality <= 2` resets `repetitions` and keeps the item in today's queue, which is exactly the signal the scheduler needs.

### 5. Progress pulse every 5 items

Items done out of the total, running accuracy, minutes left.

### 6. Session summary

Give: how many were reviewed, accuracy, minutes spent. Then the breakdown — clean (gone for a while), minor slips (back in X days), missed (back tomorrow) — followed by how many fall due tomorrow, this week, and next week, the streak, and one line of advice pitched at today's accuracy.

### 7. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-review"`, `skills_practiced: [derived from reviewed items]`
- `skill_scores` — aggregate per skill touched
- `review_results[]` — every item reviewed, with `quality`
- `errors[]` — only patterns where the learner got it wrong (bumps frequency)
- `focus_next_session[]` — the 2-3 items with lowest quality this session

Then save the transcript beside the databases, in their `results/` directory:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

That prints the data directory; write to `<it>/results/fluent-review-session-{NNN}.md`. The directory is resolved at runtime (`FLUENT_DATA_DIR`, a project `data/`, or the `~/.claude` fallback), so ask rather than assume. Format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md` — it is the canonical definition, and `fluent-session-analyzer` parses exactly the markers it lists.

## Critical Rules

- **Let the learner struggle.** If they don't remember, that is useful data (quality 0-2) — the algorithm needs honest signals. A guess scored as knowledge pushes the item weeks out and takes the schedule with it, so when the learner says they guessed, score the guess.
- **Daily.** The spacing assumes a session every day. After a gap, say what the gap cost — the size of today's backlog — and triage it together; skip the scolding.

## What the Schedule Means

If the learner asks what their next-review intervals mean — read `.claude/skills/fluent-review/SCHEDULE-MEANING.md` and answer from there.
