---
name: fluent-db-updater
description: Persist a practice session's results — errors, review results, new vocabulary, session metadata — by piping one JSON payload to update-db.py. Use at the end of every practice session.
---

# DB Updater

## Overview

Every practice skill ends by piping one JSON report to `update-db.py`, which backs up, validates the payload, applies all six databases atomically (`.tmp + fsync + rename`) and rebuilds the spaced-repetition queue.

## When to Use

Load this skill when a practice session ends and its results (errors, review results, new vocabulary, totals) need persisting.

Skip this skill for read-only operations (use the `fluent-progress` skill or `read-db.py` directly) and during session setup (use `fluent-setup` skill instead — `update-db.py` is for session deltas, not bootstrap).

## Instructions

### 1. Read state

Call `read-db.py` at session start for current state and `next_session_id`; one call replaces reading each JSON file:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

It returns all 6 databases plus computed fields (`due_reviews_count`, `next_session_id`, `streak_active`).

### 2. Fill the payload

**Required fields**

- `session_id` — string, convention `session-NNN`. Use `computed.next_session_id` from `read-db.py`.
- `date` — today, as the output of `date +%F` run while you build the payload. A resumed session still remembers the day it started; the shell knows the day it is saved. `update-db.py` rejects any other day with exit `1`.

**Optional fields** — omit to skip. Full canonical example (copy-paste this and fill in):

```
${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/references/db-updater-payload.example.json
```

Key blocks the example covers: `skill_scores`, `errors[]`, `new_vocabulary[]`, `review_results[]`, `topics_covered`, `breakthroughs`, `focus_next_session`, `session_notes`, `achievements_earned`, `milestones`.

### 3. Field notes

- `errors[]` — one entry per distinct mistake staged this session. Collapse duplicates (same `pattern_id`) before sending; `frequency` is bumped by the script. `category` comes from the canon in `fluent-feedback-formatter` §"Use these category labels" — `update-db.py` rejects any other value.
- `new_vocabulary[]` — items the learner met for the first time. Fill every field; incomplete entries yield incomplete spaced-repetition records.
- `review_results[]` — items already in the queue that were reviewed; stage each result as the session runs. The script reschedules each via FSRS-6 — see the `fluent-fsrs-reference` skill for how a score becomes a due date.
- `skill_scores[].correct` counts correct exercises, not a percentage. Accuracy is derived.
- `confidence` in `learner-profile.skills` is 0–100 integer; `accuracy` in `progress-db` is 0.0–1.0 float. The script handles the conversion.
- `milestones[]` — each entry is a bare non-empty **string**. The object form (`{ "milestone": ..., "date": ... }`) was removed after v0.3.0 and now exits `1`, naming the offending index, with no files written. Every milestone is dated with the top-level `date` and stamped with the top-level `session_id`. Each becomes both a `session-log.milestones[]` record and a `learner-profile.achievements[]` entry.
- `allow_backdate` — `true` when the learner asks you to record a session from an earlier day, such as one whose save failed. `date` may then name any day from the last recorded session up to yesterday, and the record carries no `measured_minutes`, because the prompt clock holds only today. A date error means `date` is wrong: rerun `date +%F`.

### 4. Call the script

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/update-db.py" <<'EOF'
{ ...payload... }
EOF
```

Exit codes: `0` success, `1` validation error, `2` I/O error. On `1` or `2` no files are touched — fix the payload, or clear the disk-space/permission problem, and retry.

## Critical Rules

- **Call once, at session end.** The script rebuilds the review queue each run — partial updates risk inconsistency.
- **`review_queue` is regenerated on every run**; feed `review_results[]` and leave the queue itself alone.
- **One `session_id`, one run.** Every run adds to running totals, so `update-db.py` exits `1`, writing nothing, on a `session_id` already in the session log. On a retry, that exit means the first run landed.
- **Backups are automatic.** Before any change the script copies the six databases to `<data_dir>/.backups/pre-update-<session_id>/` (`fluent_paths.py` prints `<data_dir>`). When the learner asks to correct the last saved session, copy that folder's `*.json` files back into `<data_dir>`, then send the corrected payload under the same `session_id`. The copy rolls back every session saved after it too, so this corrects the most recent session only.
