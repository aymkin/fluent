# Fluent SM-2 → FSRS-6 doc/skill cleanup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the doc/skill layer tell the truth — FSRS-6 (code-owned) schedules
reviews; no skill claims SM-2 or instructs hand-computing intervals.

**Architecture:** Text/markdown edits across skills + top docs, one small dead-code
deletion in `update-db.py`. No scheduler logic changes. The `quality` (0-5) input
contract into `update-db.py` stays — it is mapped to an FSRS rating internally
(`update-db.py:386-387`). Repo: `aymkin/fluent`, working clone at the scratchpad
path used this session.

**Tech Stack:** Markdown (SKILL.md + docs), Python 3 stdlib (`update-db.py`,
`pytest` tests already present: `tests/test_fsrs.py`, `tests/test_update_db.py`).

## Global Constraints

- Do NOT change `.claude/hooks/fsrs.py` or the scheduling math.
- Do NOT change the `{item_id, quality}` payload contract — it is valid.
- Do NOT rewrite CHANGELOG history; the FSRS switch is already logged under
  `[Unreleased]`. Only append a line for this cleanup.
- Do NOT migrate or touch live `~/.claude/fluent-data/spaced-repetition.json`.
- Keep `easiness_factor` field; only mark it vestigial. It is written at item
  init (`update-db.py:442,468`) and read nowhere.
- New reference skill name is exactly `fluent-fsrs-reference`. Every repointed
  cross-reference uses that exact string (was `fluent-sm2-calculator`).
- Commit per task. Push to remote only after explicit user approval (separate
  step, not in this plan).

## File Structure

- `.claude/skills/fluent-fsrs-reference/SKILL.md` — CREATE. Thin scheduling
  contract reference (replaces the SM-2 calculator).
- `.claude/skills/fluent-sm2-calculator/SKILL.md` — DELETE.
- `.claude/references/sm2-worked-examples.md` — DELETE.
- `.claude/skills/fluent-review/SKILL.md` — MODIFY (heaviest).
- `.claude/skills/fluent-db-updater/SKILL.md` — MODIFY.
- `.claude/skills/fluent-feedback-formatter/SKILL.md` — MODIFY.
- `.claude/skills/fluent-learn/SKILL.md` — MODIFY.
- `.claude/skills/fluent-vocab/SKILL.md` — MODIFY.
- `README.md`, `CLAUDE.md`, `AGENTS.md` — MODIFY (current-state SM-2 → FSRS-6).
- `CHANGELOG.md` — MODIFY (append one line under `[Unreleased] → Changed`).
- `.claude/hooks/update-db.py` — MODIFY (delete `calculate_sm2`, comment
  `easiness_factor`).

Phase A (stop-harm): Tasks 1-3. Phase B (full cleanup): Tasks 4-6.

---

## PHASE A — stop the harm (skills)

### Task 1: Replace the reference layer

**Files:**
- Create: `.claude/skills/fluent-fsrs-reference/SKILL.md`
- Delete: `.claude/skills/fluent-sm2-calculator/SKILL.md`
- Delete: `.claude/references/sm2-worked-examples.md`

**Interfaces:**
- Produces: skill name `fluent-fsrs-reference` (referenced by Tasks 2-5).

- [ ] **Step 1: Create the new reference skill** with exactly this content:

```markdown
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
```

- [ ] **Step 2: Delete the two SM-2 files**

```bash
git rm .claude/skills/fluent-sm2-calculator/SKILL.md \
       .claude/references/sm2-worked-examples.md
```

- [ ] **Step 3: Verify no dangling references remain to the deleted files**

Run: `grep -rn 'sm2-worked-examples\|fluent-sm2-calculator' .claude README.md CLAUDE.md AGENTS.md`
Expected: only hits are in files Tasks 2-5 will fix (fluent-review, fluent-db-updater,
fluent-feedback-formatter, fluent-learn, fluent-vocab, README.md, CLAUDE.md, AGENTS.md).
Note them; they are handled downstream. No hit should be inside the (now deleted) files.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/fluent-fsrs-reference/SKILL.md
git commit -m "feat(skills): replace fluent-sm2-calculator with fluent-fsrs-reference"
```

### Task 2: Fix fluent-review skill

**Files:**
- Modify: `.claude/skills/fluent-review/SKILL.md`

**Interfaces:**
- Consumes: `fluent-fsrs-reference` (Task 1).

- [ ] **Step 1: Fix the frontmatter `description` (line 3).** Replace:

`description: Run today's spaced-repetition review queue — items scheduled by SM-2 that need reinforcement before the learner forgets them. Triggered only when the learner types /fluent-review. Pulls due items from spaced-repetition.review_queue.today, generates a targeted exercise for each, evaluates the response, updates SM-2 parameters, and reshelves items into the correct future queue.`

with:

`description: Run today's spaced-repetition review queue — items scheduled by FSRS-6 that need reinforcement before the learner forgets them. Triggered only when the learner types /fluent-review. Pulls due items from spaced-repetition.review_queue.today, generates a targeted exercise for each, evaluates the response, submits the score so update-db.py reschedules via FSRS, and reshelves items into the correct future queue.`

- [ ] **Step 2: Fix line 16.** Replace `mutating SM-2 state from a misread prompt`
  with `mutating spaced-repetition state from a misread prompt`.

- [ ] **Step 3: Fix the step heading (line 97).** Replace `### 4. Evaluate + update SM-2`
  with `### 4. Evaluate + submit the score`.

- [ ] **Step 4: Fix line 107.** Replace:

`The \`update-db.py\` script runs the SM-2 math (see \`fluent-sm2-calculator\` skill) and rebuilds the queue. Mapping: \`quality = floor(score / 2)\`.`

with:

`The \`update-db.py\` script maps the score to an FSRS rating, reschedules via FSRS-6, and rebuilds the queue (see \`fluent-fsrs-reference\` skill). Mapping: \`quality = floor(score / 2)\`.`

- [ ] **Step 5: Fix the worked-example on line 206.** Replace:

`> (Logged: quality=5 → \`interval_days = round(14 * EF)\`, queue: \`later\`. \`consecutive_correct\` = 5, mastery → 5 ⭐⭐⭐⭐⭐.)`

with:

`> (Logged: quality=5 → FSRS reschedules to a longer interval, queue: \`later\`. \`consecutive_correct\` = 5, mastery → 5 ⭐⭐⭐⭐⭐.)`

- [ ] **Step 6: Fix line 211.** Replace `Long interactive + SM-2 mutation.`
  with `Long interactive + spaced-repetition mutation.`

  (Line 186's `interval_days=1, repetitions=0` and lines 64-66/104/154-156/213's
  `quality` references are FSRS-valid — `quality`/`repetitions`/`interval_days`
  are live fields — leave them.)

- [ ] **Step 7: Verify**

Run: `grep -n 'SM-2\|sm2-calculator\|round(14 \* EF)' .claude/skills/fluent-review/SKILL.md`
Expected: no output.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/fluent-review/SKILL.md
git commit -m "docs(review): describe FSRS-6 scheduling, not SM-2"
```

### Task 3: Fix the other four skills

**Files:**
- Modify: `.claude/skills/fluent-db-updater/SKILL.md`
- Modify: `.claude/skills/fluent-feedback-formatter/SKILL.md`
- Modify: `.claude/skills/fluent-learn/SKILL.md`
- Modify: `.claude/skills/fluent-vocab/SKILL.md`

**Interfaces:**
- Consumes: `fluent-fsrs-reference` (Task 1).

- [ ] **Step 1: fluent-db-updater line 56.** Replace:

`- \`review_results[]\` — items already in the queue that were reviewed. The script runs SM-2 on each. See the \`fluent-sm2-calculator\` skill. Mapping: \`quality = floor(score / 2)\`.`

with:

`- \`review_results[]\` — items already in the queue that were reviewed. The script reschedules each via FSRS-6. See the \`fluent-fsrs-reference\` skill. Mapping: \`quality = floor(score / 2)\`.`

- [ ] **Step 2: fluent-db-updater line 145.** Replace `updated SM-2 params,`
  with `updated spaced-repetition params (FSRS),`.

- [ ] **Step 3: fluent-feedback-formatter line 73.** Replace
  `### 5. Hand score to SM-2` with `### 5. Hand score to the scheduler`.

- [ ] **Step 4: fluent-feedback-formatter line 75.** Replace:

`After scoring, feed the score into the SM-2 update via the \`fluent-sm2-calculator\` skill: \`quality = floor(score / 2)\`.`

with:

`After scoring, feed the score into the scheduler via the \`fluent-db-updater\` skill; see \`fluent-fsrs-reference\` for the pipeline: \`quality = floor(score / 2)\`.`

- [ ] **Step 5: fluent-learn line 193.** Replace `\`fluent-sm2-calculator\`,`
  with `\`fluent-fsrs-reference\`,`.

- [ ] **Step 6: fluent-vocab line 97.** Replace `(see \`fluent-sm2-calculator\` skill)`
  with `(see \`fluent-fsrs-reference\` skill)`.

- [ ] **Step 7: Verify**

Run: `grep -rn 'SM-2\|sm2-calculator' .claude/skills/fluent-db-updater .claude/skills/fluent-feedback-formatter .claude/skills/fluent-learn .claude/skills/fluent-vocab`
Expected: no output.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/fluent-db-updater/SKILL.md .claude/skills/fluent-feedback-formatter/SKILL.md .claude/skills/fluent-learn/SKILL.md .claude/skills/fluent-vocab/SKILL.md
git commit -m "docs(skills): repoint SM-2 references to fluent-fsrs-reference"
```

---

## PHASE B — full cleanup (docs + code)

### Task 4: README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Current-state prose swaps.** Apply each replacement (left → right):
  - L127 `**Spaced Repetition (SM-2 algorithm)**` → `**Spaced Repetition (FSRS-6 algorithm)**`
  - L136 `SM-2 algorithm schedules reviews` → `FSRS-6 algorithm schedules reviews`
  - L164 `based on SM-2 algorithm` → `based on FSRS-6 algorithm`
  - L174 `**2. Spaced Repetition (SM-2 Algorithm)**` → `**2. Spaced Repetition (FSRS-6 Algorithm)**`
  - L196 `(SM-2 math, feedback formatter, DB updater, session analyzer)` → `(FSRS reference, feedback formatter, DB updater, session analyzer)`
  - L210 `due for review today based on the SM-2 algorithm` → `due for review today based on the FSRS-6 algorithm`
  - L274 `Review queue (SM-2 algorithm)` → `Review queue (FSRS-6 algorithm)`
  - L288 `Shared templates (SM-2 worked examples, feedback template, ...` → `Shared templates (feedback template, ...` (drop the deleted worked-examples item)
  - L301 `### Spaced Repetition (SM-2 Algorithm)` → `### Spaced Repetition (FSRS-6 Algorithm)`
  - L349 `- **Algorithm:** SM-2 (SuperMemo 2)` → `- **Algorithm:** FSRS-6 (Free Spaced Repetition Scheduler)`

- [ ] **Step 2: Skill-table / catalog rows (L233, L292).**
  - L233 replace the whole `/fluent-sm2-calculator` row with:
    `| **\`/fluent-fsrs-reference\`** | FSRS-6 scheduling reference: score→quality→rating→FSRS pipeline, live vs vestigial fields, intervals computed by code. | Auto-loaded whenever scheduling must be reasoned about. |`
  - L292 replace `\`/fluent-sm2-calculator\`` with `\`/fluent-fsrs-reference\`` (in the helper-skills sentence).

- [ ] **Step 3: Attribution / history lines — reword, keep credit.**
  - L15 already reads "FSRS-6 scheduling (replacing SM-2)…" — leave as-is.
  - L427 `- **SuperMemo** - For the SM-2 algorithm` → `- **SuperMemo** - For SM-2, Fluent's original scheduler` .
  - L498 `- [SM-2 Algorithm Explained](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)` → add a sibling line above it and keep the historical one:
    `- [FSRS Algorithm](https://github.com/open-spaced-repetition/fsrs4anki/wiki) — current scheduler`
    `- [SM-2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2) — Fluent's original scheduler`

- [ ] **Step 4: Verify** — no current-state SM-2 claims left, history/credit lines OK.

Run: `grep -n 'SM-2\|sm2-calculator\|SuperMemo' README.md`
Expected: only L15 (replacing SM-2), L427 (original scheduler credit), and the
L498 SM-2 line marked "original scheduler". No standalone "uses SM-2" claims.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs(readme): FSRS-6 is the current scheduler, SM-2 is history"
```

### Task 5: CLAUDE.md, AGENTS.md, CHANGELOG.md

**Files:**
- Modify: `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md`

- [ ] **Step 1: CLAUDE.md swaps.**
  - L21 `You implement SM-2 algorithm to optimize review timing` → `The FSRS-6 scheduler (fsrs.py) optimizes review timing; you submit scores, it reschedules`
  - L47 `Review queue, SM-2 parameters` → `Review queue, FSRS-6 parameters`
  - L66 `Helper skills (\`fluent-sm2-calculator\`, ...` → `Helper skills (\`fluent-fsrs-reference\`, ...` (same list, first name only)
  - L73 `2. **Spaced Repetition (SM-2)**` → `2. **Spaced Repetition (FSRS-6)**`

- [ ] **Step 2: AGENTS.md line-level swaps.**
  - L49 `Review queue, SM-2 algorithm data` → `Review queue, FSRS-6 algorithm data`
  - L71 `Review items due today (SM-2)` → `Review items due today (FSRS-6)`
  - L82 replace the `fluent-sm2-calculator` row: `| \`fluent-fsrs-reference\` | FSRS-6 scheduling reference |`
  - L147 `### 2. Spaced Repetition (SM-2 Algorithm)` → `### 2. Spaced Repetition (FSRS-6 Algorithm)`
  - L149 `- Update \`easiness_factor\` based on performance` → `- Submit the score; FSRS updates \`stability\`/\`fsrs_difficulty\``
  - L196 leave `"easiness_factor": 2.5,` in the sample item (it is still written at init — vestigial but present).

- [ ] **Step 3: AGENTS.md — replace the SM-2 implementation section (heading + fenced
  code block only).** Replace from the `## 🔄 SM-2 Algorithm Implementation` heading
  through the CLOSING ```` ``` ```` fence of its python code block (the block that ends a
  few lines after `easiness_factor = max(1.3, easiness_factor)`, past `repetitions += 1` /
  `else:` / `interval = 1`) with the exact FSRS-6 block below. Do NOT delete what follows
  the code fence: the `**Quality scale:**` subsection (0-5 grades) and its `---` separator
  are KEPT — the 0-5 `quality` grade is still the tutor's input (score→quality→rating), so
  it remains valid under FSRS. Replacement block:

```markdown
## 🔄 FSRS-6 Scheduling

Scheduling is owned by `.claude/hooks/fsrs.py` (a stdlib FSRS-6 port) and invoked
by `.claude/hooks/update-db.py`. Agents never compute intervals by hand. Submit a
score (0-10); `update-db.py` maps it to an FSRS rating (1-4) and calls
`fsrs.schedule(...)`, which returns the next `interval_days` and `due_date` and
updates `stability` / `fsrs_difficulty`. See the `fluent-fsrs-reference` skill for
the full pipeline and field list.
```

- [ ] **Step 4: CHANGELOG.md — append one bullet under `[Unreleased] → Changed`**
  (after the existing FSRS switch bullet, do NOT edit existing bullets):

```markdown
- Docs and skills updated to describe FSRS-6: replaced the `fluent-sm2-calculator`
  skill and `sm2-worked-examples` reference with a thin `fluent-fsrs-reference`,
  and removed the unused `calculate_sm2()` function from `update-db.py`. The
  legacy `easiness_factor` field is kept (init-only) for back-compat.
```

- [ ] **Step 5: Verify**

Run: `grep -n 'SM-2\|easiness_factor\|sm2-calculator' CLAUDE.md AGENTS.md`
Expected: CLAUDE.md → no output; AGENTS.md → only L196 sample `easiness_factor: 2.5`.
CHANGELOG history retains its SM-2 mentions (expected).

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md AGENTS.md CHANGELOG.md
git commit -m "docs(agents,claude,changelog): FSRS-6 replaces SM-2 in current-state docs"
```

### Task 6: Remove dead SM-2 code from update-db.py

**Files:**
- Modify: `.claude/hooks/update-db.py`
- Test: `tests/test_update_db.py`, `tests/test_fsrs.py`

- [ ] **Step 1: Confirm the function is uncalled**

Run: `grep -rn 'calculate_sm2' .claude tests`
Expected: only the `def calculate_sm2` line at `update-db.py:149`. If any call
site appears, STOP — the deletion is not safe; re-plan.

- [ ] **Step 2: Delete the dead function.** Remove the block from the
  `# --- SM-2 Algorithm ---` comment through the end of `calculate_sm2`'s
  `return {...}` (the function returning `easiness_factor`/`interval_days`/
  `repetitions`, roughly lines 147-172). Delete the comment header too.

- [ ] **Step 3: Mark the surviving `easiness_factor` writes as vestigial.**
  At both new-item init sites (currently `update-db.py:442` and `:468`,
  `"easiness_factor": 2.5,`), add on the line above each:
  `# ponytail: vestigial SM-2 field, kept for back-compat with existing data`

- [ ] **Step 4: Run the scheduler tests**

Run: `python3 -m pytest tests/test_fsrs.py tests/test_update_db.py -v`
Expected: all PASS (deleting an uncalled function changes no behavior).

- [ ] **Step 5: Verify no stray SM-2 compute remains in the file**

Run: `grep -n 'calculate_sm2\|SM-2 Algorithm' .claude/hooks/update-db.py`
Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/update-db.py
git commit -m "refactor(hooks): drop unused calculate_sm2, mark easiness_factor vestigial"
```

---

## Post-plan (NOT part of task execution — needs explicit user approval)

- Run full grep gate: `grep -rniE 'SM-?2|sm2-calculator' .claude README.md CLAUDE.md AGENTS.md`
  → residual allowed: CHANGELOG history, the `fluent-fsrs-reference` skill naming
  `easiness_factor`/SM-2 as dead, the AGENTS L196 sample field, README history/credit lines.
- `git push origin main` — ONLY after the user approves the push.
- `/plugin update` (or `/plugin marketplace update aymkin`) to pull into the
  installed plugin.

## Self-Review

- **Spec coverage:** Unit 1 → Task 1; Unit 2 → Tasks 2-3; Unit 3 → Tasks 4-5;
  Unit 4 → Task 6; Verification → per-task grep + Task 6 pytest. All covered.
- **Placeholder scan:** every edit is a concrete old→new string or full block; no
  TBD/TODO/"handle appropriately".
- **Type/name consistency:** new skill is `fluent-fsrs-reference` everywhere;
  `quality`/`repetitions`/`interval_days`/`stability`/`fsrs_difficulty` used
  consistently as live fields; `easiness_factor` consistently vestigial.
