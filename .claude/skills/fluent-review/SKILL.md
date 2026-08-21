---
name: fluent-review
description: Today's FSRS review queue.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Spaced-Repetition Review Session

## Overview

Replay items the learner learned before, timed so they hit just before the forgetting curve drops them. This is the single most effective session type — the system depends on it running daily. Items the learner gets right get pushed further into the future; items they miss come back tomorrow.

## Instructions

### 1. Load review queue

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py" --review
```

`--review` sorts `spaced-repetition.review_queue.today` by `priority` (critical → high → medium → low) and caps it at `daily_limits.review_items_per_day` server-side, so only the items you'll actually use come back expanded. Use `computed.due_reviews_count` for the true total due when writing the opening message — it can be larger than the trimmed queue. It also empties `mastery_db`/`progress_db`/`session_log` (unused by this flow — `computed.next_session_id` already covers what session_log would've been needed for) and narrows `mistakes_db.error_patterns` to just the patterns referenced by today's capped queue.

If the queue is empty:

```markdown
🎉 No reviews due today! Your spaced repetition is up to date.

Want to practice something new? Try:
- `/fluent-learn` — adaptive mixed practice
- `/fluent-vocab` — learn new words
- `/fluent-progress` — see your stats
```

### 2. Opening

```markdown
# 🔄 Today's Spaced Repetition Review

Hallo {name}! Time to review items your brain is about to forget. This keeps everything fresh. 🧠

**Items Due Today:** {count}
**Estimated Time:** ~{minutes} min

Why review? Spaced repetition prevents forgetting, moves items into long-term memory, and builds automaticity.

**Ready? Let's start!** 💪
```

### 3. Generate exercise per item

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

Generate an exercise matched to `item_type`:

- **error_pattern**: load the pattern from `mistakes-db`, create a scenario that forces the correct form. E.g. `formal_informal_confusion` → ask the learner to complete a formal email opening.
- **vocabulary**: recognition (target → native), production (native → target), or cloze — rotate modes.
- **grammar_rule**: a fill-in or error-correction exercise that tests the rule.

Present one at a time — rushing = false positives:

```markdown
## Review {N}/{total} — {priority emoji}

**Type:** {item_type}
**Last reviewed:** {X} days ago
**Current mastery:** {stars}
**FSRS difficulty:** {fsrs_difficulty}/10

{exercise}

**Type your answer:**
```

### 4. Evaluate + submit the score

Use the `fluent-feedback-formatter` skill for per-answer feedback.

Then stage the item for the end-of-session update. Do NOT hand-edit `spaced-repetition.json` — the queue is rebuilt on every `update-db.py` call; use `review_results[]` in the `fluent-db-updater` payload:

```json
{ "item_id": "vocab_huis", "quality": 4 }
```

The `update-db.py` script maps the score to an FSRS rating, reschedules via FSRS-6, and rebuilds the queue (see `fluent-fsrs-reference` skill). A low score is not a failure to hide: `quality <= 2` resets `repetitions` and keeps the item in today's queue, which is exactly the signal the scheduler needs.

### 5. Progress pulse every 5 items

```markdown
## Progress Update

**Reviewed:** {N}/{total}
**Accuracy:** {percent}%
**Time Remaining:** ~{min} min

Keep going! 💪
```

### 6. Session summary

```markdown
## 🎉 Review Session Complete!

**Reviewed:** {count}
**Accuracy:** {percent}%
**Time:** {min} min

### Breakdown

**Mastered (no mistakes):** {count} — won't appear again for a while 🎉
**Good (minor slips):** {count} — next in {X} days
**Need more practice:** {count} — tomorrow again

### Next Review Schedule
- Tomorrow: {count}
- This week: {count}
- Next week: {count}

**Streak:** 🔥 {X} {day/days} 🔥

**Tip:** {one line of advice based on accuracy}

{target-language well done}! 🌟
```

### 7. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-review"`, `skills_practiced: [derived from reviewed items]`
- `skill_scores` — aggregate per skill touched
- `review_results[]` — every item reviewed, with `quality`
- `errors[]` — only patterns where the learner got it wrong (bumps frequency)
- `focus_next_session[]` — the 2-3 items with lowest quality this session

Save the session file to `/results/fluent-review-session-{NNN}.md` — structure per `results/README.md`. Every `❌` line carries its category and its severity emoji; without them `fluent-session-analyzer` cannot parse the session.

## Critical Rules

- **Daily.** The whole system assumes the learner runs `/fluent-review` every day. Missing a day breaks the intended spacing.
- **Let the learner struggle.** If they don't remember, that's useful data (quality 0-2). The algorithm needs honest signals.

## What the Schedule Means

Tell the learner if they ask:

- 1 day — new or struggling items
- 2-3 days — learning, building strength
- 1 week — getting comfortable
- 2+ weeks — strong, maintenance only
- 1+ month — mastered, long-term memory
