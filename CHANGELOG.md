# Changelog

All notable changes to Fluent will be documented in this file.

## [Unreleased]

### Changed

- Scheduler switched from SM-2 to a stdlib FSRS-6 port
  (`.claude/hooks/fsrs.py`). Reviews are scheduled via `fsrs.schedule` using the
  0-10 tutor score mapped to an FSRS rating (1-4). Cards gain `stability` and
  `fsrs_difficulty` (the pre-existing `difficulty` key keeps the CEFR level);
  `spaced_repetition.metadata` records `scheduler`, `target_retention`, and an
  optional optimized `weights` vector. One-time migration in
  `migrate_to_fsrs.py` seeds `stability`/`fsrs_difficulty` from existing
  intervals.
- Docs and skills updated to describe FSRS-6: replaced the `fluent-sm2-calculator`
  skill and `sm2-worked-examples` reference with a thin `fluent-fsrs-reference`,
  and removed the unused `calculate_sm2()` function from `update-db.py`. The
  legacy `easiness_factor` field is kept (init-only) for back-compat.
- Migrated the remaining doc/data stragglers to FSRS-6: `LEARNING_SYSTEM.md` now
  describes the FSRS-6 pipeline instead of the SM-2 formula/`updateSpacedRepetition`
  block, the `data`/`data-examples` READMEs and the `spaced-repetition` template
  stamp `scheduler: fsrs-6` (template item gains `stability`/`fsrs_difficulty`),
  and the plugin manifest + marketplace metadata replace the `sm2` tag with `fsrs`.
  Historical mentions (CHANGELOG, CONTRIBUTING, migration plan) and the vestigial
  `easiness_factor` field are intentionally kept.

### Added

- `.claude/hooks/optimize_weights.py`: a guarded, offline FSRS-6 weight
  optimizer (uses `fsrs-optimizer` in a separate venv). No-ops until ≥ 400
  reviews and ≥ 50 new reviews since the last run, then writes optimized
  `weights` back to `spaced_repetition.metadata`. Intended to run weekly.

### Performance

- `read-db.py --review` (used by `/fluent-review`'s first step) now dumps
  compact JSON instead of `indent=2`, pre-sorts and caps
  `spaced_repetition.review_queue.today` at `daily_limits.review_items_per_day`
  server-side instead of shipping every due item's full record, and drops
  `mastery_db`/`progress_db`/`session_log` plus unreferenced `mistakes_db`
  patterns — none of which the review flow's opening/exercise steps read.
  Payload for a 369-item queue capped at 30: 444KB → 43KB (-90.3%), cutting
  time-to-first-token on `/fluent-review` accordingly. Default (non-review)
  mode is untouched.
- `read-db.py --review` additionally drops `computed.due_review_items` (the
  full list of due item ids — every skill that calls `read-db.py` only ever
  reads the `due_reviews_count` integer), trims `learner_profile` down to
  `learner.name` + `current_streak_days` (the only two fields the review
  template reads), and strips each capped item's `review_history` (write-only
  from this flow's perspective — `update-db.py` appends to it by rereading the
  files from disk). 35.0KB → 22.9KB (-34.6%) on top of the reduction above.

### Fixed

- `migrate_to_fsrs.py` set `metadata.scheduler = "fsrs-6"` but never updated
  the neighboring `metadata.algorithm`, which stayed `"SM-2"` even after the
  scheduler had fully switched to FSRS-6. Now stamps both.

## [0.3.0] — 2026-06-15

### Added

- Milestones support in the `update-db.py` session payload. The new
  `milestones[]` field accepts either a bare string or an object
  `{ "milestone": <required non-empty string>, "date": <optional YYYY-MM-DD,
  defaults to the session date> }`. Each milestone is recorded in both
  `session-log.milestones[]` and `learner-profile.achievements[]`. Validation
  rejects malformed entries (exit `1`, no files written); an unparseable
  `date` falls back to the session date.

## [0.2.1] — 2026-06-11

### Fixed

- Hooks no longer fail on Windows with `No such file or directory` (#5).
  Plugin hook commands in `hooks.json` used the bash default-value syntax
  `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}`, which Claude Code's own
  variable substitution does not understand on Windows — it replaced the
  variable names but left the `:-` separators literal, producing a single
  garbage path. Hook commands now use plain `${CLAUDE_PLUGIN_ROOT}` (always
  set for plugin hooks) and invoke scripts via an explicit `python3`/`bash`
  interpreter so they don't depend on shebang handling under Git Bash.

## [0.2.0] — 2026-05-14

### Breaking changes

All 12 skills renamed with a `fluent-` prefix to prevent collisions with other
plugins and Claude Code built-ins. Update any muscle memory or external
references.

| Old | New |
|-----|-----|
| `/setup` | `/fluent-setup` |
| `/learn` | `/fluent-learn` |
| `/review` | `/fluent-review` |
| `/vocab` | `/fluent-vocab` |
| `/writing` | `/fluent-writing` |
| `/speaking` | `/fluent-speaking` |
| `/reading` | `/fluent-reading` |
| `/progress` | `/fluent-progress` |
| `sm2-calculator` | `fluent-sm2-calculator` |
| `db-updater` | `fluent-db-updater` |
| `feedback-formatter` | `fluent-feedback-formatter` |
| `session-analyzer` | `fluent-session-analyzer` |

New session result files use `/results/fluent-{skill}-session-{NNN}.md`.
Existing files using the older `{skill}-session-{NNN}.md` naming are still
read by `fluent-session-analyzer` — no migration required.

### Fixed

- Plugin install no longer fails on first DB read. Skills now invoke helper
  scripts via `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/...`
  so the path resolves regardless of CWD.
- Added missing `.claude/hooks/ensure_data_dir.py` referenced by
  `fluent-setup`.

### Migration

```bash
claude plugin update fluent@m98
```

Then use the new slash commands. Your data (`~/.claude/fluent-data/` or
`./data/`) is unchanged.

## [0.1.0] — 2026-03-15

Initial release.
