---
name: fluent-fsrs-reference
description: FSRS-6 scheduling reference for the Fluent language learning system. Use whenever a skill needs to know how a review is scheduled or how a score becomes a due date. Explains the score→quality→rating→FSRS pipeline, which spaced-repetition fields are live vs vestigial, and that intervals are computed by code — never by hand.
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
  → rating (1-4)       1 if score<=4, 2 if <=6, 3 if <=8, else 4  (update-db.py:386-387)
  → fsrs.schedule(...) → interval_days + due_date            (update-db.py:393)
```

You send `{ "item_id": "...", "quality": <0-5> }` (optionally `"score": <0-10>`)
in `review_results[]`. `update-db.py` maps it to an FSRS rating and reschedules.

## Fields on a spaced-repetition item

| Field | Status | Meaning |
|-------|--------|---------|
| `quality` / `last_quality` | live | 0-5 grade; feeds the mastery heuristic |
| `repetitions` | live | consecutive-success counter; feeds mastery |
| `mastery_level` | live | 0-5 stars, derived from repetitions + quality |
| `stability` | live | FSRS memory stability (days) |
| `fsrs_difficulty` | live | FSRS item difficulty (NOT the CEFR `difficulty` key) |
| `interval_days` / `due_date` | live | computed by FSRS, do not set by hand |
| `easiness_factor` | vestigial | legacy SM-2 field; written at init (2.5), read nowhere |

## When to use

Load when a skill must explain or reason about scheduling. To actually persist a
review, do not compute anything here — hand the payload to the `fluent-db-updater`
skill, which runs `update-db.py`.
