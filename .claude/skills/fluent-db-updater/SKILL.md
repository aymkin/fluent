---
name: fluent-db-updater
description: Atomically update all 6 Fluent learner databases (learner-profile, progress, mistakes, mastery, spaced-repetition, session-log) at session end by calling .claude/hooks/update-db.py with a single JSON payload. Use at the end of every practice session — fluent-writing, fluent-vocab, fluent-speaking, fluent-reading, fluent-review, fluent-learn — to persist the session's errors, review results, new vocabulary, and session metadata.
---

# DB Updater

## Overview

Every practice skill ends with a DB update. Instead of hand-editing 6 JSON files (error-prone, racy, easy to desync), pipe one JSON report to `update-db.py`. The script runs pre-write backups, validates the payload, applies all changes atomically via `.tmp + fsync + rename`, and rebuilds the spaced-repetition queue.

## When to Use

Load this skill whenever the tutor:

- Finishes a practice session and needs to persist results.
- Needs to add new vocabulary to the spaced-repetition queue.
- Needs to record new errors, review results, or mastery changes.
- Needs to bump `total_sessions`, `current_streak_days`, or `total_study_minutes`.

Skip this skill for read-only operations (use the `fluent-progress` skill or `read-db.py` directly) and during session setup (use `fluent-setup` skill instead — `update-db.py` is for session deltas, not bootstrap).

## Instructions

### 1. Call the script

Run from the repo root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/update-db.py" <<'EOF'
{ ...payload... }
EOF
```

Exit codes: `0` success, `1` validation error, `2` I/O error.

### 2. Fill the payload

**Required fields**

- `session_id` — string, convention `session-NNN`. Use `computed.next_session_id` from `read-db.py`.
- `date` — YYYY-MM-DD.

**Optional fields** — omit to skip. Full canonical example (copy-paste this and fill in):

```
${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/references/db-updater-payload.example.json
```

Key blocks the example covers: `skill_scores`, `errors[]`, `new_vocabulary[]`, `review_results[]`, `topics_covered`, `breakthroughs`, `focus_next_session`, `session_notes`, `achievements_earned`, `milestones`.

### 3. Field notes

- `errors[]` — one entry per distinct mistake this session. Collapse duplicates (same `pattern_id`) before sending; `frequency` is bumped by the script.
- `new_vocabulary[]` — items the learner met for the first time. Fill every field; incomplete entries yield incomplete spaced-repetition records.
- `review_results[]` — items already in the queue that were reviewed. The script reschedules each via FSRS-6. See the `fluent-fsrs-reference` skill. Mapping: `quality = floor(score / 2)`.
- `skill_scores[].correct` counts correct exercises, not a percentage. Accuracy is derived.
- `confidence` in `learner-profile.skills` is 0–100 integer; `accuracy` in `progress-db` is 0.0–1.0 float. The script handles the conversion.
- `milestones[]` — each entry is a bare non-empty **string**. The object form (`{ "milestone": ..., "date": ... }`) was removed after v0.3.0 and now exits `1`, naming the offending index, with no files written. Every milestone is dated with the top-level `date` and stamped with the top-level `session_id`. Each becomes both a `session-log.milestones[]` record and a `learner-profile.achievements[]` entry.

### 4. Read before writing

Always call `read-db.py` at session start to get current state + `next_session_id`. Don't read each JSON file separately:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Returns all 6 databases plus computed fields (`due_reviews_count`, `next_session_id`, `streak_active`).

## Critical Rules

- **Call once per session, at the end.** The script rebuilds the review queue each run — partial updates risk inconsistency.
- **Never hand-edit `spaced-repetition.review_queue`.** It's regenerated from scratch on every run.
- **Same `session_id` replaces.** Sending the same ID twice overwrites the first call. Useful for corrections, dangerous if unintentional.
- **Backups are automatic.** Written to `.backups/pre-update-<session_id>/` before any change. Check there to roll back.
- **Exit code 1 means validation failed, no files touched.** Fix the payload and retry.
- **Exit code 2 means I/O failure, no files touched.** Check disk space, permissions, then retry.
