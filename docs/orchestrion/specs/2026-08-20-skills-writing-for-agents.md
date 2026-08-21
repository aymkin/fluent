# Spec — apply `writing-for-agents` to the Fluent skill set

**Status:** approved 2026-08-20
**Source:** review of all 11 skills, `CLAUDE.md`, `AGENTS.md`, `LEARNING_SYSTEM.md`
and `results/README.md` against the `writing-for-agents` reference
(context pointers, the two loads, information hierarchy, completion criteria,
leading words, pruning).

Citations are by **section heading, symbol, or quoted string** — never by line
number, because most of the tasks that consume this spec change line counts.

---

## 1. Why

The skill set works, but it carries three classes of defect that the review
found with evidence:

1. **Mechanically impossible instructions** — a hand-off no agent can perform,
   a format contract no skill points at.
2. **Contradictions between always-loaded and on-demand material** — `CLAUDE.md`
   is in context on every turn and tells the tutor the opposite of what the
   skills say, so it wins on attention.
3. **Sediment** — the same meaning in six places, rules restating the steps they
   follow, and a prohibition that forbids something the frontmatter already makes
   impossible.

None of this is style. Each item below either changes agent behaviour or removes
a maintenance trap that has already caused observable drift.

## 2. Decisions taken (2026-08-20)

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Error-category canon | **Expand to 10 labels and enforce them in code.** `structure`, `comprehension`, `inference` join the canon; `update-db.py` validates `errors[].category` and exits `1` on anything else. |
| D2 | Desirable-difficulty band | **50-70%** — the value already in two of three places. `CLAUDE.md` is the outlier and gets corrected. |
| D3 | Hand-off out of `fluent-learn` / `fluent-setup` | **Read the target skill's `SKILL.md` and follow it in the same session** — the mechanism `AGENTS.md` already prescribes for non-Claude CLIs. The gate on the practice skills stays. |

Assumption taken without asking (F12): the unimplemented mastery preconditions in
the gated skills' *When to Use* sections are **deleted**, not wired in. They never
fire (no step reads them), and a mastery gate that overrides an explicit
`/fluent-writing` from the learner is worse behaviour than no gate. Where a step
already implements the precondition (`fluent-review` §1 empty queue,
`fluent-learn` §1 missing DBs, `fluent-setup` §1 existing profile) the step keeps
it and the *When to Use* copy goes.

## 3. The canon this spec establishes

### 3.1 Error categories — 10 labels + `other`

`fluent-feedback-formatter` §"Use these category labels" is the single home of the
list. `errors[].category` accepts exactly:

```
grammar  formal_informal  vocabulary  spelling  prepositions  articles
missing  structure  comprehension  inference  other
```

- `other` stays accepted because `update-db.py` already writes it as the default
  when a payload omits the key.
- The enum applies to **`errors[].category` only**. `new_vocabulary[].category` is
  a semantic field (`food`, `work`, …) and must stay unvalidated.
- Meanings of the three new labels: `structure` — organisation, flow,
  paragraphing; `comprehension` — misread what the text says; `inference` — failed
  to draw what the text implies.

### 3.2 The score → quality mapping has one home

`fluent-fsrs-reference` owns the pipeline **and** the score→quality meaning table
(moved there from `LEARNING_SYSTEM.md`). Every other document points at it and
states no formula.

### 3.3 Session-file criterion — one sentence, used verbatim

The final step of every session skill (`fluent-learn`, `-writing`, `-speaking`,
`-reading`, `-vocab`, `-review`) ends on:

> Save the session file to `/results/fluent-{skill}-session-{NNN}.md` — structure
> per `results/README.md`. Every `❌` line carries its category and its severity
> emoji; without them `fluent-session-analyzer` cannot parse the session.

### 3.4 `stage` is the leading word for deferred writes

One word for "hold this until the end-of-session payload": **stage**. It retires the
three phrasings that describe *holding* a result — "track the answer for",
"collected during the session", "batch at session end".

The *timing* rule is a separate statement, and it gets the same single-source
treatment as everything else in this spec — three tiers, not one sentence copied
eight times:

1. **The rule with its reason lives in `fluent-db-updater`** §"Critical Rules", which
   already carries it: «Call once per session, at the end. The script rebuilds the
   review queue each run — partial updates risk inconsistency.» That is the only home
   of the *why*.
2. **The two always-loaded documents state the rule and point at that home.**
   `LEARNING_SYSTEM.md` §"Data Files You Must Use" already does exactly this and
   stays as it is. `CLAUDE.md` currently states the opposite and is corrected to the
   same shape: databases are written **once, at session end**, with the reason left
   to `fluent-db-updater`.
3. **The practice skills state no timing at all.** Their final step already points at
   `fluent-db-updater`; that pointer is the whole instruction. Where a skill states
   timing today (`fluent-vocab` §"Feedback after each answer": «Do not call
   `update-db.py` after every word — batch at session end») it becomes the staging
   form — stage the result, and let `fluent-db-updater` write at session end — with
   no reason clause and no second copy of the rule.

The greppable invariant is the literal string `once, at session end`: present in
`CLAUDE.md` and `LEARNING_SYSTEM.md`, absent from every `SKILL.md` except
`fluent-db-updater`'s.

### 3.5 Human-facing descriptions for the seven gated skills

`disable-model-invocation: true` puts the description out of the agent's reach, so
it is a slash-menu label — one line, no trigger list, no step summary:

| Skill | Description |
|-------|-------------|
| `fluent-learn` | Adaptive mixed-skill practice session. |
| `fluent-writing` | Writing practice with systematic error analysis. |
| `fluent-speaking` | Typed conversation practice — communication over grammar. |
| `fluent-reading` | Reading comprehension with a graded question sequence. |
| `fluent-vocab` | Flashcard-style vocabulary drill. |
| `fluent-review` | Today's FSRS review queue. |
| `fluent-setup` | One-time onboarding; also profile updates and reset. |

### 3.6 Descriptions for the model-invoked skills

Always-loaded, so one trigger per branch and no identity the body already carries:

- `fluent-progress` — `Progress dashboard — stats, mastery levels, streak, achievements. Use when the learner asks how they are doing.`
- `fluent-db-updater` — `Persist a practice session's results — errors, review results, new vocabulary, session metadata — by piping one JSON payload to update-db.py. Use at the end of every practice session.`
- `fluent-feedback-formatter` — `Canonical feedback shape for every graded learner answer: corrections with category and severity, the full correct version, a score out of 10. Use after the learner submits an answer in any practice session.`
- `fluent-fsrs-reference` — `FSRS-6 scheduling reference: how a score becomes a due date, and which fields live on a spaced-repetition item. Use when a skill must reason about review scheduling.`
- `fluent-session-analyzer` — unchanged.

## 4. Findings to close

### F1 — `CLAUDE.md` contradicts the skills from always-loaded context

- «ALWAYS update tracking databases after every exercise» and «NEVER skip
  updating the databases» contradict `fluent-vocab` §4 («Do not call
  `update-db.py` after every word — batch at session end»),
  `fluent-db-updater` §"Critical Rules" («Call once per session, at the end»)
  and `LEARNING_SYSTEM.md` §"Session End Protocol" («Write all six databases in
  one shot»). **Batch-at-end wins**; `CLAUDE.md` states the rule in §3.4's tier-2
  shape — the literal `once, at session end` plus the pointer to
  `fluent-db-updater`, which is the one home of the *why*. (Before §3.4 was
  rewritten this bullet asked `CLAUDE.md` to carry the reason itself; §3.4
  governs.)
- «YOU MUST READ `/data/learner-profile.json`» plus the seven `/data/*.json` rows
  of the *Key Files You Work With* table contradict `fluent-progress` §1 («do NOT
  hardcode `data/`»). Replace the literal paths with the resolved data directory.
- The paragraph enumerating which skills carry `disable-model-invocation` is a
  cache of the frontmatter, one `rg` away and already at risk of going stale.
  Collapse it to the rule plus where to look.

### F2 — hand-off into gated skills is impossible

`fluent-learn` §"Route" and `fluent-setup` §"Optional first lesson" hand off to
skills that carry `disable-model-invocation: true`; nothing but the human can fire
those. Replace per D3.

### F3 — no session skill points at `results/README.md`

`results/README.md` declares itself the canonical session-file format and
`fluent-session-analyzer` parses it, yet no `SKILL.md` references it (only
`CLAUDE.md`, `AGENTS.md`, `README.md`, `LEARNING_SYSTEM.md` do). The existing
criterion («Save exchange to /results/…») is unfalsifiable. Fix with §3.3.

### F4 — error-category taxonomy split three ways

Canon in `fluent-feedback-formatter` (7 labels) vs `fluent-writing`
§"Systematic error analysis" (adds `Structure`, folds `prepositions`/`articles`
into `Grammar`) vs `fluent-reading` §"Update all databases" (`comprehension`,
`inference`). `fluent-session-analyzer` scans only the canonical 7, and
`update-db.py` validates nothing. Fix with §3.1 — and `fluent-writing` /
`fluent-reading` point at the canon instead of restating it.

`fluent-db-updater` §"Field notes" gains one clause under `errors[]`: the category
comes from the canon and `update-db.py` now rejects anything else. That is where a
payload author looks, and D1 makes the constraint machine-enforced — a caller that
learns about it only from the exit code learns it too late.

### F5 — two values for one band

`CLAUDE.md` «60-70% success rate» vs `fluent-learn` and
`fluent-session-analyzer` «50-70% → target zone». Fix per D2.

### F6 — gated skills carry model-facing descriptions

Seven descriptions are 3-4 sentence step summaries no agent can read; they have
already drifted (`fluent-vocab` says «calls fluent-db-updater at the end», its
siblings say «updates all databases»). Fix with §3.5.

### F7 — `fluent-progress` states one branch three times

Six trigger synonyms in the always-loaded description, repeated again in the body
*When to Use*. «Read-only — safe to auto-invoke» is maintainer commentary inside a
pointer. Fix with §3.6; the body keeps one *When to Use* line for the genuine
second branch (skip mid-practice).

### F8 — sibling enumerations inside always-loaded descriptions

`fluent-db-updater` and `fluent-feedback-formatter` list all six practice skills —
one branch written six times — and the formatter's list already omits
`fluent-learn` while its body includes it. Fix with §3.6.

### F9 — «Never auto-invoke» is a no-op, eight times

Present in all seven gated skills (twice in `fluent-setup`). The frontmatter
enforces it; the rule spends its slot forbidding the impossible. Delete every
occurrence, including the description sentences «Triggered only when the learner
types /X» and «Must never auto-invoke because …». The reason behind the setup one
survives in its existing «Confirm twice before reset» rule.

### F10 — Critical Rules restating their own steps

Delete the bullet where a numbered step already carries the rule; keep the rule on
the step (co-location). Confirmed pairs:

| Skill | Bullet to drop | Step that owns it |
|---|---|---|
| `fluent-writing` | «Wait for the full answer» | §"Wait for the full text" |
| `fluent-writing` | «Severity tagging is mandatory» | §"Systematic error analysis" |
| `fluent-writing` | «Always save the session file» | §"Update all databases" |
| `fluent-vocab` | «One word at a time» | §"Present one word at a time" |
| `fluent-vocab` | «Immediate feedback» | §"Feedback after each answer" |
| `fluent-vocab` | «Never update the DBs mid-session» | §"Feedback after each answer" |
| `fluent-reading` | «Wait for "ready"» | §"Present the text" |
| `fluent-reading` | «One question at a time» | §"Question sequence" |
| `fluent-review` | «Never hand-edit `spaced-repetition.json`» | §"Evaluate + submit the score" |
| `fluent-review` | «One item at a time» | §"Generate exercise per item" |
| `fluent-speaking` | «One question at a time» | §"One question at a time" |
| `fluent-db-updater` | exit-code bullets | §"Call the script" |
| `fluent-feedback-formatter` | «Always use the template exactly» | §"Standard template" |
| `fluent-feedback-formatter` | «Severity tag is mandatory» | §"Tag severity on every error" |

The two formatter bullets carry reasons the steps do not («Deviations break
session-file parsing downstream», «Drives spaced-repetition priority»). Those reasons
are load-bearing: they move onto the step, they do not disappear with the bullet.
Its «One score per answer» and «Never skip the "Correct version"» bullets survive —
the template alone does not enforce either.

What must **survive** in Critical Rules: the constraints with no step —
`fluent-review` «Daily» and «Let the learner struggle», `fluent-speaking`
«Communication first», «Stay in the target language», «Praise natural expression»
and «Don't over-correct», `fluent-setup` «Confirm twice before reset» / «Back up
before reset» / «Don't invent data», `fluent-learn` «Interleave» and «Use the
helper skills», `fluent-reading` «Don't reuse a text», «Quote the text»,
«Vocabulary opt-in» and «Ask questions in the target language».

`fluent-progress` is **not** in scope for F10: none of its six bullets restates a
step — «Read-only», «Use the current streak value», «Use `day` vs `days`», «Skip
sections with no data», «Cite the learner by name» and «Use target-language
greetings» are all report rules the numbered steps do not carry. They all stay.

### F11 — `quality = floor(score / 2)` in six places

`fluent-fsrs-reference`, `fluent-feedback-formatter`, `fluent-db-updater`,
`fluent-vocab`, `fluent-review`, `LEARNING_SYSTEM.md` — and four of them already
carry the pointer to the reference in the same sentence. Fix with §3.2.

### F12 — preconditions no step checks

*When to Use* gates in `fluent-writing` («mastery 2 in basic vocabulary»),
`fluent-speaking` («below A1 mastery 2»), `fluent-reading` («below A1 mastery 3»),
`fluent-vocab` («no vocabulary items are due») are read by no step. Handled by the
assumption in §2.

### F13 — four phrasings for one idea

Fix with §3.4.

### F14 — branch-only material sitting in the main file

Reached by only one branch, so it belongs behind a pointer:

| Move | From | To (sibling of `SKILL.md`) |
|---|---|---|
| §"Profile Updates (existing profile)" | `fluent-setup` | `PROFILE-UPDATES.md` |
| §"Optional interpretation footer" | `fluent-progress` | `STATS-GLOSSARY.md` |
| §"What the Schedule Means" | `fluent-review` | `SCHEDULE-MEANING.md` |

Lowest-value item in this spec — gated skills load once per session, so the win is
legibility, not context load. Included for completeness; the first candidate to
drop if the sweep has to be cut short.

## 5. Out of scope

- No change to any session's pedagogy, exercise content, or output templates
  beyond the copy named above.
- No change to `fsrs.py`, `read-db.py`, or the review-queue rebuild.
- `AGENTS.md` and `results/README.md` are already correct and stay as they are.
- No renaming of existing `/results/*.md` files.

## 6. Done means

- Every finding F1-F14 closed, or explicitly waived in writing.
- `for t in tests/test_*.py; do python3 "$t" -q; done` passes.
- One value for the difficulty band, one home for the quality formula, one home
  for the category list, across the whole repo.
- No `file.md:NN` citation left pointing at a line that moved.
