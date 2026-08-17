# Ponytail audit cleanup, round 2 — 2026-08-17

Second-pass audit of the post-cleanup tree (53 files, 7391 lines). Removing
~1320 more lines. Four tasks, split by **file ownership** so parallel worktrees
merge without conflicts — same protocol as round 1, which merged 4/4 clean.

`CHANGELOG.md` is owned by nobody; the orchestrator writes it after all merges.

Baseline before the work: 4 test files pass
(`for t in tests/test_*.py; do python3 "$t" -q; done`).

The structural finding behind most of this: three layers describe one system —
`LEARNING_SYSTEM.md` (576), twelve `SKILL.md` (~1850), `README`/`docs` (~730).
Only the skills are loaded by Claude Code on command. The other two trail behind
and have drifted into contradiction.

---

## Task A — LEARNING_SYSTEM.md

**Owns:** `LEARNING_SYSTEM.md`, `.claude/skills/fluent-learn/SKILL.md`

| # | Tag | Cut |
|---|-----|-----|
| 4 | delete | §🚀 Slash Command Behaviors (406-492) — lossy pretend-copy of seven `SKILL.md` |
| 5 | delete | §📊 Progress Tracking After Each Exercise (236-320) — contradicts `update-db.py`: wrong key `skills_mastery`, wrong mastery formula, dead fields |
| 8 | delete | §🎲 Exercise Generation Strategy (127-192) — dupe of `fluent-learn/SKILL.md` §6-7; also kill the dead `mastery_level == 3` branch in the surviving copy |
| 12 | shrink | §🎮 Gamification (358-404) → ~8 lines; nothing awards the seven achievement types |
| 11 | shrink | §💬 Feedback Format (323-356) → 4 lines; section itself names `fluent-feedback-formatter` as canonical |
| 17a | shrink | Stale `Last Updated` / `Version` header (5-6) |

**Target:** −307 lines

---

## Task B — README.md + CONTRIBUTING.md

**Owns:** `README.md`, `CONTRIBUTING.md`

| # | Tag | Cut |
|---|-----|-----|
| 1 | delete | `CONTRIBUTING.md` 404 → ~40. Boilerplate + fiction (`languages/{code}/`, `CONTRIBUTORS.md`, `m98/fluent` clone URL) |
| 6 | delete | README §Why This Actually Works / §What Is This? / §Evidence-Based Methods (99-195) |
| 13 | delete | README §Contributing / §Priority Areas (395-421) — verbatim dupe of `CONTRIBUTING.md:376-382` |
| 16 | delete | README trailing clone block (491-501) — third install copy, and it contradicts `README.md:71-74` by omitting `marketplace add ./` |
| 17b | shrink | Stale `Last updated:` footer in CONTRIBUTING |

Also fix `README.md:164` — "Updates 4 databases" is six.

**Target:** −499 lines

---

## Task C — docs / data-examples / results

**Owns:** `docs/DB_SCRIPTS.md`, `data-examples/README.md`, `results/README.md`,
`CLAUDE.md`, `AGENTS.md`, `tests/test_read_db.py`,
`.claude/skills/fluent-progress/evals/`

| # | Tag | Cut |
|---|-----|-----|
| 3 | delete | `docs/DB_SCRIPTS.md` — third copy of the payload schema (skill + example JSON already hold it). Repoint every referrer |
| 7 | shrink | `data-examples/README.md` 94 → ~20; explains `{YOUR_NAME}` three times |
| 9 | yagni | `.claude/skills/fluent-progress/evals/evals.json` — see below |
| 10 | shrink | `results/README.md` tail (120-155) — user advice inside a parser spec |

**Target:** −313 lines

---

## Task D — python + hooks docs

**Owns:** `.claude/hooks/update-db.py`, `.claude/hooks/README.md`,
`tests/test_update_db.py`, `.claude/skills/fluent-db-updater/SKILL.md`,
`.claude/references/db-updater-payload.example.json`

| # | Tag | Cut |
|---|-----|-----|
| 2 | delete | `.claude/hooks/README.md` §Customization/§Debugging/§Hook Events/§Troubleshooting (184-330) — generic hook tutorial |
| 14 | shrink | Two near-identical 21-line SR item-init literals → one helper |
| 15 | yagni | `normalize_milestones` dual-form (string OR object) → strings only. **Breaking**: drops the per-milestone `date` override shipped in 0.3.0 |

**Target:** −188 lines

---

## #9 — verified before dispatch

Round 1 taught us not to call a file dead on a grep (`ensure_data_dir.py`), so
this one was checked against the CLI before being queued. `claude plugin eval`
discovers `evals/<case>/case.yaml`, or `evals/<case>/prompt.md` +
`evals/<case>/graders/*.md`. A single `evals.json` holding
`{skill_name, evals: [{id, prompt, expected_output, files, expectations}]}`
matches neither pattern — the schema does not exist in the eval runner. Nothing
in the repo reads it either (no `.github/`, no other reference). It is dead
weight, not a working suite. Real coverage for `fluent-progress` would mean
`evals/<case>/prompt.md` + graders, which nobody has written.

## Not cut

- `fsrs.py`, `fluent_paths.py`, `validate-data.py`, `read-db.py --review`,
  `ensure_data_dir.py`, the four test files.
