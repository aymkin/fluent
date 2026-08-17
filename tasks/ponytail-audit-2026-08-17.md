# Ponytail audit cleanup — 2026-08-17

Removing ~2000 lines of over-engineering found by `/ponytail-audit`. Four tasks,
split by **file ownership** so parallel worktrees merge without conflicts.

`CHANGELOG.md` is owned by nobody — the orchestrator writes one entry after all
merges. Any task touching it would conflict with the other three.

Baseline before the work: all 6 test files pass.

---

## Task A — docs consolidation

**Owns:** `docs/superpowers/`, `AGENTS.md`, `PRACTICE.md`, `README.md`,
`CLAUDE.md`, `LEARNING_SYSTEM.md`, `.claude/references/`, `data/README.md`,
`results/README.md`, `data-examples/README.md`, `CONTRIBUTING.md`

| # | Tag | Cut |
|---|-----|-----|
| 1 | delete | `docs/superpowers/` — finished SM-2→FSRS plan + spec, zero inbound refs, history is in git |
| 2 | delete | `AGENTS.md` 470 → pointer stub at `LEARNING_SYSTEM.md` |
| 3 | delete | `PRACTICE.md` — Dutch-writing methodology in a language-agnostic kit |
| 8 | delete | `.claude/references/session-file-template.md` — 4th copy of the session-file format |
| 9 | delete | `.claude/references/feedback-template.md` — verbatim copy of `fluent-feedback-formatter/SKILL.md` §1-2 |
| 10 | delete | README marketing: Star This Project, Success Stories, Project Stats, Support & Community |

Also removes doc mentions of what Tasks B/C delete (`migrate_to_fsrs.py`,
`optimize_weights.py`, `ensure_data_dir.py`, `precompact-backup.sh`) from the
files it owns.

**Target:** −1534 lines

---

## Task B — dead code

**Owns:** `.claude/hooks/migrate_to_fsrs.py`, `.claude/hooks/optimize_weights.py`,
`.claude/hooks/ensure_data_dir.py`, `tests/test_migrate_to_fsrs.py`,
`tests/test_optimize_weights.py`

| # | Tag | Cut |
|---|-----|-----|
| 4 | delete | `migrate_to_fsrs.py` + test — one-time migration, already run, no callers |
| 11 | yagni | `optimize_weights.py` + test — no hook/cron/skill invokes it; needs 400 reviews; drags in torch |
| 12 | delete | `ensure_data_dir.py` — CLI wrapper around one function, zero callers |

**Target:** −278 lines, −1 optional dep (torch)

---

## Task C — hooks & backups

**Owns:** `.claude/settings.json`, `.claude/hooks/hooks.json`,
`.claude/hooks/session-end.py`, `.claude/hooks/precompact-backup.sh`,
`.claude/hooks/README.md`

| # | Tag | Cut |
|---|-----|-----|
| 5 | delete | Duplicate `hooks` block in `settings.json` — same 4 hooks as `hooks.json`; both fired in one session (banner printed twice) |
| 6 | delete | `hooks_documentation` + `description` + `version` in `settings.json` — 50 lines the settings schema ignores |
| 7 | shrink | 4 backup mechanisms → 2. Drop `precompact-backup.sh` (nothing writes during compaction) and the daily-snapshot half of `session-end.py` (duplicates the per-write `.backup-*`). Keep per-write validation backup + `update-db.py` pre-update backup |

**Target:** −174 lines

---

## Task D — python shrink

**Owns:** `.claude/hooks/update-db.py`, `.claude/hooks/read-db.py`,
`.claude/hooks/fluent_paths.py`, `tests/test_update_db.py`,
`tests/test_read_db.py`, `docs/DB_SCRIPTS.md`, `data-examples/*.json`,
`.claude/skills/**/SKILL.md`

| # | Tag | Cut |
|---|-----|-----|
| 13 | shrink | 6 date helpers in `update-db.py` → `date_plus_days` covers `tomorrow`/`yesterday` |
| 14 | delete | Vestigial fields written but never read: `easiness_factor`, `last_occurred`, `computed.days_since_last_session`, `computed.review_queue_trimmed_to` |
| 15 | shrink | `@lru_cache(maxsize=1)` on 3 pure `os.environ` readers in a one-shot process |

Also removes `optimize_weights` / `migrate_to_fsrs` mentions from
`.claude/skills/**/SKILL.md`.

**Target:** −21 lines + schema noise

---

## Not cut

- `fsrs.py` — dense but earned; cross-checked against py-fsrs, comments explain upstream divergences.
- `read-db.py --review` — looked dead on first grep, is actually called by `fluent-review/SKILL.md:25`.
