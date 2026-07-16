# Design: SM-2 → FSRS-6 doc/skill cleanup

Date: 2026-07-15
Repo: `aymkin/fluent` (standalone marketplace + plugin)
Status: approved (design), pending implementation plan

## Problem

The scheduler migrated from SM-2 to FSRS-6 (live 2026-07-04): `update-db.py`
calls `fsrs.schedule(...)` and `fsrs.py` owns the math. But the doc/skill layer
was never updated. It still claims SM-2 is the algorithm and, worse, instructs
the model to hand-compute intervals with the dead SM-2 formula.

Evidence (on `main`):

- `update-db.py:393` — `r = fsrs.schedule(fsrs_state, rating, today, weights)`
  drives scheduling. `fsrs.py:1` — "FSRS-6 spaced-repetition scheduler".
- `fluent-sm2-calculator/SKILL.md` description: "Fluent uses SM-2 … single
  source of truth … update-db.py runs SM-2 internally." All false.
- `fluent-review/SKILL.md` states `interval_days = round(14 * EF)` — FSRS
  computes intervals; EF does not.
- `calculate_sm2()` (`update-db.py:149`) is defined but never called.
- `easiness_factor` is written only at item init (2.5) and read nowhere.
- Still live: `quality` (0-5) input contract, `repetitions`, `quality` →
  feed the `mastery_level` heuristic. These stay.

## Goal / non-goals

Goal: doc/skill layer tells the truth — FSRS-6 schedules (code-owned), nobody
hand-computes intervals.

Non-goals: change `fsrs.py`; change the `quality` input contract (it works —
`update-db.py:386-387` maps score→rating internally); rewrite CHANGELOG history;
migrate live `spaced-repetition.json` data.

## Units

### Unit 1 — reference layer (core stop-harm)

- Delete `.claude/skills/fluent-sm2-calculator/SKILL.md`
- Delete `.claude/references/sm2-worked-examples.md`
- Create `.claude/skills/fluent-fsrs-reference/SKILL.md` — thin: documents the
  contract `score → quality → rating(1-4) → fsrs.schedule`; live fields
  (`quality`, `repetitions`, `mastery_level`, `stability`, `fsrs_difficulty`)
  vs vestigial (`easiness_factor`); explicit "intervals are computed by code,
  do NOT hand-compute." No FSRS formulas.

### Unit 2 — 5 live skills (stop-harm)

- `fluent-review/SKILL.md` (heaviest): fix the `description` loader text
  ("scheduled by SM-2", "updates SM-2 parameters" → FSRS); fix step "Evaluate +
  update SM-2"; remove the false `interval_days = round(14 * EF)` worked-example
  lines; repoint `fluent-sm2-calculator` → `fluent-fsrs-reference`. Keep the
  `{item_id, quality}` payload — still valid.
- `fluent-db-updater`, `fluent-feedback-formatter`, `fluent-learn`,
  `fluent-vocab`: replace SM-2/EF wording with FSRS; repoint references.

### Unit 3 — top docs

- `README.md`, `CLAUDE.md`, `AGENTS.md`: update current-state SM-2 descriptions
  to FSRS-6.
- `CHANGELOG.md`: do NOT rewrite past SM-2 entries (legitimate history); add one
  new entry for this cleanup.

### Unit 4 — code (minimal, no behavior change)

- Delete `calculate_sm2()` (`update-db.py` ~147-172) — uncalled.
- Keep `easiness_factor`; mark
  `# ponytail: vestigial SM-2 field, kept for back-compat with existing data`.

## Verification

- `grep -riE 'SM-?2|sm2-calculator'` over skills/docs → 0 (except CHANGELOG
  history). Allowed residual mentions of `easiness_factor`/SM-2: the
  `update-db.py` back-compat comment and the `fluent-fsrs-reference` skill,
  which names them precisely to mark them dead. No skill still *instructs*
  SM-2 computation.
- No skill/doc references the two deleted files.
- `python3 -m pytest tests/test_fsrs.py tests/test_update_db.py` green
  (guards the function deletion).

## Sequencing

- Phase A: Units 1 + 2 (stop-harm — fixes the instructions the model loads).
- Phase B: Units 3 + 4 (full cleanup).
- Commit per phase. Push to `aymkin/fluent` only with explicit user approval;
  then `/plugin update` pulls it into the installed plugin.
