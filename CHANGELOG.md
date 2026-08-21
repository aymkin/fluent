# Changelog

All notable changes to Fluent will be documented in this file.

## [Unreleased]

### Changed

- Scheduler switched from SM-2 to a stdlib FSRS-6 port
  (`.claude/hooks/fsrs.py`). Reviews are scheduled via `fsrs.schedule` using the
  0-10 tutor score mapped to an FSRS rating (1-4). Cards gain `stability` and
  `fsrs_difficulty` (the pre-existing `difficulty` key keeps the CEFR level);
  `spaced_repetition.metadata` records `scheduler`, `target_retention`, and an
  optional optimized `weights` vector. Existing cards were seeded with
  `stability`/`fsrs_difficulty` from their old intervals by a one-time migration
  script, since removed.
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

### Removed

- **Clone installs now need one extra command.** Hooks are registered in exactly
  one place (`.claude/hooks/hooks.json`, wired in through the plugin manifest);
  the duplicate registration in `.claude/settings.json` is gone. With both files
  present every hook fired twice — the SessionStart briefing printed itself
  twice on startup. If you use Fluent from a git clone rather than a plugin
  install, run `claude plugin marketplace add ./ && claude plugin install
  fluent@aymkin` once from the repo root, or you get the slash commands with no
  SessionStart briefing, no JSON validation, and no automatic backups.
- Two of the four backup layers. Every save is still backed up (10 rotating
  generations per file at `<data_dir>/<name>.json.backup-<timestamp>`), and
  `update-db.py` still snapshots all six databases before a session write. The
  end-of-session daily snapshot and the pre-compaction copy are gone: both wrote
  the same six files to the same `.backups/` directory that already held them,
  and nothing writes to your data during conversation compaction.
- The weekly FSRS-6 weight optimizer, along with its `fsrs-optimizer`/torch
  dependency. Nothing scheduled it — no hook, no command — and it needed 400
  accumulated reviews before it would act, so no weights were ever fitted. The
  scheduler already ran on the pinned py-fsrs defaults and continues to.
- The one-time SM-2 → FSRS-6 migration script. It ran, it was idempotent, and it
  had no callers left.
- **`milestones[]` no longer accepts the object form.** Each entry must be a
  plain string, and every milestone is dated with the session date. The
  `{ "milestone": ..., "date": ... }` form added in 0.3.0 is rejected with exit
  `1`, naming the offending index, before any database is written. This is an
  input-format change only — nothing in your stored data moves or is rewritten.
- A second pass of duplicated documentation, ~1150 lines: `docs/DB_SCRIPTS.md`
  (the payload schema also lives in the `fluent-db-updater` skill and the
  example JSON that skill points at), the per-command flow summaries and the
  hand-edit instructions in `LEARNING_SYSTEM.md` (576 → 310 lines), the generic
  hook-authoring tutorial in `.claude/hooks/README.md` (340 → 200 — the backup
  strategy and the restore recipe stay), the contributor boilerplate in
  `CONTRIBUTING.md` (404 → 52), the marketing sections and the third copy of the
  install commands in `README.md` (501 → 408), and an `evals.json` written in a
  schema `claude plugin eval` does not read.
- `PRACTICE.md` (Dutch-writing methodology in a language-agnostic kit; its
  content lives in the `fluent-writing` and `fluent-session-analyzer` skills),
  the finished FSRS migration plan/spec under `docs/superpowers/`, and two
  `.claude/references/` files that duplicated the session-file format and the
  feedback template verbatim. `AGENTS.md` is now a 44-line pointer for
  non-Claude CLIs instead of a 470-line restatement of `LEARNING_SYSTEM.md`.
- **The end-of-session banner is gone.** The SessionEnd hook printed your streak
  and total session count when you closed Claude Code — both are a subset of
  what the SessionStart banner shows on the way in, and `update-db.py` already
  prints them when it saves your session. Nothing about your data changes.
- A third pass of duplicated documentation, ~1160 lines. The six-database table
  had copies in five files, the eight-command list in three, and the six
  learning principles in three; each now has one home. `LEARNING_SYSTEM.md`
  576 → 310 → 150 (the sections that had become one-line pointers are gone;
  `CLAUDE.md` keeps the principles, each `SKILL.md` keeps its own flow),
  `README.md` 501 → 408 → 264 (Key Features, Learning Principles, Technical
  Details, FAQ), `data/README.md` 133 → 30, `.claude/hooks/README.md` 200 → 105,
  and the Dutch-specific appendices in `fluent-reading` / `fluent-speaking` /
  `fluent-writing` — the same thing `PRACTICE.md` was deleted for.
- A fourth pass, ~700 lines, mostly the last Dutch content in a
  language-agnostic kit. Every skill carried an `## Examples` section that
  re-rendered, in Dutch A2, the output template printed a few lines above it in
  the same file — 317 lines across 11 skills. `fluent-reading`'s five hardcoded
  `Vraag N` question blocks and `fluent-vocab`'s three `## Word {N}` blocks are
  now one parameterized block each. In the docs: the README's Learning Loop and
  Recommended Daily Routine sections, its three command tables collapsed to one
  (501 → 408 → 264 → 190 lines), the six-database table's third and fourth
  copies (`README.md`, `data-examples/README.md`), and the clone-install
  instructions' second copy in `.claude/hooks/README.md`.
- **The FSRS weights override is gone.** `fsrs.schedule()` no longer takes a
  `weights=` vector and `update-db.py` no longer reads
  `spaced_repetition.metadata.weights`. The optimizer that produced that vector
  was removed earlier in this release, so nothing had written the key since and
  the scheduler always ran on the pinned py-fsrs defaults — it still does.
  Re-adding the optimizer means re-adding the parameter. If you hand-wrote a
  `weights` key it is now ignored; nothing in your data moves or is rewritten.

### Changed

- New spaced-repetition items no longer carry `easiness_factor`, and new mistake
  patterns no longer carry the `last_occurred` alias of `last_seen`. Both were
  written on every insert and read by nothing. Existing items keep their copies
  and reschedule normally — nothing migrates or strips your data.
- `read-db.py` no longer emits `computed.days_since_last_session`, which no
  skill consumed. `due_reviews_count`, `next_session_id`, `streak_active`, and
  `today` are unchanged.
- The plugin's marketplace keywords no longer list seven individual languages
  (Dutch, Spanish, French, …) in a kit that works with any of them. Search by
  `language-learning`, `spaced-repetition`, `fsrs`, `tutor` or `flashcards`.
- Internal cleanup with no user-visible effect: `fluent_paths.plugin_root()`
  (no callers) is deleted, `backups_dir()` folded into `ensure_backups_dir()`,
  and the SessionStart hook no longer tolerates a list-form `items` map or a
  `next_review_date` alias — neither has ever been written.
- `update-db.py`'s test suite traded eight milestone slug edge-case tests for
  three, and spent the difference on the counters that actually drive
  scheduling: streak reset after a missed day, cumulative `accuracy_rate`, and
  `mastery_level` climbing with session count. The FSRS cross-check now pins
  `DEFAULT_W` to the pinned py-fsrs package explicitly instead of injecting the
  package's own vector, so a drift in its defaults fails the gate.

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

- `/fluent-setup` built `mastery-db.json` around a top-level `skills_mastery`
  key, and `/fluent-writing`, `/fluent-speaking` and `/fluent-reading` read
  their mastery level from it. `update-db.py` reads and writes `skills`, so the
  database created at onboarding and the one the updater maintains disagreed
  from the first session onward. All four now say `skills`.
- `fluent-session-analyzer` searched `/results/{skill}-session-{ID}.md`. Every
  practice skill has written `/results/fluent-{skill}-session-{NNN}.md` since
  v0.2.0, so the pattern matched nothing and next-session planning had no input
  to work from. It now matches the current name and the pre-0.2.0 one.
- `fluent-progress` was told to render "locked" achievements with 🔒. There is no
  catalogue of achievements to lock — they exist only as the milestones you
  record at session end, so the dashboard now says as much when the list is empty.
- `LEARNING_SYSTEM.md` told the tutor to hand-edit `progress-db`, `mistakes-db`
  and `mastery-db`, using a mastery formula, a top-level key and field names
  that none of them matched `update-db.py` — while `CLAUDE.md` requires the
  scripts be used instead. Those instructions are gone.
- The README's learning-loop table said a session updates 4 databases. It is six.
- The README's install commands used the ref `fluent@m98`, which does not exist.
  The `@` suffix is the marketplace name from `.claude-plugin/marketplace.json`
  (`"name": "aymkin"`), so the working ref is `fluent@aymkin` — corrected in the
  Quick Start, the verify/update/uninstall block, and the troubleshooting steps.
- The SM-2 → FSRS-6 migration set `metadata.scheduler = "fsrs-6"` but never
  updated the neighboring `metadata.algorithm`, which stayed `"SM-2"` even after
  the scheduler had fully switched. Both are stamped in existing data.
- `data/README.md` documented a `session-log.json` entry keyed by `id`; the key
  `update-db.py` actually writes is `session_id`. It also called the directory
  "empty by design", which is only true for a git clone — a plugin install keeps
  your six databases in `~/.claude/fluent-data/`. Both corrected, and the
  hand-copied schema now points at `data-examples/`, the one place the templates
  are maintained.
- The README described `.claude/references/db-updater-payload.example.json` as a
  "shared payload schema used by `update-db.py`". The script never opens that
  file — it is a copy-paste template the `fluent-db-updater` skill points at.
- Six defects a learner could see, found by reviewing `CLAUDE.md` and the whole
  skill set against the `writing-for-agents` reference.
  - Menu items 1-5 in `/fluent-learn` now start the practice you picked — they
    handed off to skills gated behind their own slash command, which nothing but
    you can type, so the hand-off could not fire; the router now reads the target
    skill and follows it in the same session, recorded as a single session.
  - Session files are written in the shape `fluent-session-analyzer` can parse:
    every session skill now names `results/README.md` as the structure and
    requires the category and the severity emoji on every corrected-error line,
    so "what should I practice next" has something to read.
  - Text-structure, reading-comprehension and reading-inference mistakes are
    tracked and drilled — `/fluent-writing` and `/fluent-reading` already tagged
    them, but the category canon and the analyzer knew only seven labels, so
    those weaknesses were recorded once and never came back.
  - An off-canon error category now fails the save with exit `1`, naming the
    offending index and the accepted labels, instead of settling into
    `mistakes-db.json` as a pattern nothing will ever schedule.
  - The six databases are written in one shot at the end of a session instead of
    after every exercise.
  - The desirable-difficulty target is one band everywhere, 50-70% success —
    only `CLAUDE.md` stated a different band, and it was the outlier.

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
