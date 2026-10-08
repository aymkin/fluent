---
name: fluent-fsrs-reference
description: "FSRS-6 scheduling reference: how a score becomes a due date, and which fields live on a spaced-repetition item. Use when a skill must reason about review scheduling."
---

# FSRS Scheduling Reference

Fluent schedules reviews with **FSRS-6**, implemented in `.claude/hooks/fsrs.py`
and driven by `.claude/hooks/update-db.py`. Skills submit a quality and
`update-db.py` schedules: FSRS-6 uses 21 fitted weights, `stability` and
`fsrs_difficulty`, so a hand-computed interval diverges from the code.

## The pipeline

```
tutor score (0-10)
  → quality (0-5)      quality = floor(score / 2)
  → rating (1-4)       1 if quality<=2, else quality - 1
  → fsrs.schedule(...) → interval_days + due_date
```

What each grade means:

| Score | Quality | Rating | Meaning |
|-------|---------|--------|---------|
| 10 | 5 | 4 Easy | Perfect — instant recall, no hesitation |
| 8-9 | 4 | 3 Good | Correct after hesitation |
| 6-7 | 3 | 2 Hard | Correct with difficulty |
| 4-5 | 2 | 1 Again | Incorrect but remembered when shown |
| 2-3 | 1 | 1 Again | Incorrect, familiar |
| 0-1 | 0 | 1 Again | Complete blackout |

You send `{ "item_id": "...", "quality": <0-5> }` in `review_results[]`.
`update-db.py` maps the quality to an FSRS rating and reschedules. Quality 0-2
is a miss for the rating, `repetitions` and `mastery_level` alike; a `"score"`
beside it is only recorded in the item's `review_history`.

## Fields on a spaced-repetition item

| Field | Meaning |
|-------|---------|
| `quality` / `last_quality` | 0-5 grade; feeds the mastery heuristic |
| `repetitions` | consecutive-success counter; feeds mastery |
| `mastery_level` | 0-5 stars: +1 per quality 4-5 review from the second success in a row, at least 3 after five in a row; a miss (quality 0-2) takes one off and caps it at 2 |
| `stability` | FSRS memory stability (days) |
| `fsrs_difficulty` | FSRS item difficulty (NOT the CEFR `difficulty` key) |
| `interval_days` / `due_date` | computed by FSRS, do not set by hand |

A legacy SM-2 `easiness_factor` on older items is read by nothing.

## When to use

Load when a skill must explain or reason about scheduling. To actually persist a
review, do not compute anything here — hand the payload to the `fluent-db-updater`
skill, which runs `update-db.py`.
