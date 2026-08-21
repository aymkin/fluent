---
name: fluent-fsrs-reference
description: "FSRS-6 scheduling reference: how a score becomes a due date, and which fields live on a spaced-repetition item. Use when a skill must reason about review scheduling."
---

# FSRS Scheduling Reference

Fluent schedules reviews with **FSRS-6**, implemented in `.claude/hooks/fsrs.py`
and driven by `.claude/hooks/update-db.py`. **Do not compute intervals by hand.**
Unlike the old SM-2 formula, FSRS-6 uses 21 fitted weights, `stability`, and
`fsrs_difficulty`; any hand calculation will diverge from the code. Skills submit
a score/quality and let `update-db.py` do the scheduling.

## The pipeline

```
tutor score (0-10)
  → quality (0-5)      quality = floor(score / 2)
  → rating (1-4)       1 if score<=4, 2 if <=6, 3 if <=8, else 4
  → fsrs.schedule(...) → interval_days + due_date
```

What each grade means:

| Score | Quality | Meaning |
|-------|---------|---------|
| 10 | 5 | Perfect — instant recall, no hesitation |
| 8-9 | 4 | Correct after hesitation |
| 6-7 | 3 | Correct with difficulty |
| 4-5 | 2 | Incorrect but remembered when shown |
| 2-3 | 1 | Incorrect, familiar |
| 0-1 | 0 | Complete blackout |

You send `{ "item_id": "...", "quality": <0-5> }` (optionally `"score": <0-10>`)
in `review_results[]`. `update-db.py` maps it to an FSRS rating and reschedules.

## Fields on a spaced-repetition item

| Field | Meaning |
|-------|---------|
| `quality` / `last_quality` | 0-5 grade; feeds the mastery heuristic |
| `repetitions` | consecutive-success counter; feeds mastery |
| `mastery_level` | 0-5 stars, derived from repetitions + quality |
| `stability` | FSRS memory stability (days) |
| `fsrs_difficulty` | FSRS item difficulty (NOT the CEFR `difficulty` key) |
| `interval_days` / `due_date` | computed by FSRS, do not set by hand |

Items created before the FSRS migration may still carry a legacy SM-2
`easiness_factor`. Nothing reads it and new items no longer get one — ignore it.

## When to use

Load when a skill must explain or reason about scheduling. To actually persist a
review, do not compute anything here — hand the payload to the `fluent-db-updater`
skill, which runs `update-db.py`.
