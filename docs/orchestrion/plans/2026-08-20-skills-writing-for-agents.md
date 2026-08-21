# Skills `writing-for-agents` Sweep Implementation Plan
**Spec:** docs/orchestrion/specs/2026-08-20-skills-writing-for-agents.md
**Profile note:** Almost every task is prose surgery on agent-facing documents, but
none of it is a known mechanical diff — deciding which Critical Rules bullet dies and
where its rule lands needs judgement, so implementation tier throughout. `t1` is the
only code+test task. `t18` is a cross-file verification sweep — review-debug tier.
Tasks `t8`-`t15` each own exactly one `SKILL.md` and are fully parallel.

## Global constraints

Forward all of these into every implementer and reviewer dispatch.

1. **Cite by name, never by line.** These tasks rewrite the files other documents
   cite. Reference sections, symbols, and quoted strings. `t17` owns the two live
   line citations in `tasks/lessons.md`; no other task adds one.
2. **Copy comes from the spec verbatim.** Descriptions (spec §3.5, §3.6), the
   session-file criterion (§3.3), the category list (§3.1), the word `stage` and the
   string `once, at session end` (§3.4) are literal — do not paraphrase, do not
   "improve" them. §3.4's three tiers also say where the timing rule may **not**
   appear: no `SKILL.md` except `fluent-db-updater`'s states it.
3. **Frontmatter is load-bearing.** `disable-model-invocation: true` stays on all
   seven gated skills; `allowed-tools` lists stay as they are; every `SKILL.md`
   opens with a `---` on line 1, closes the block with a second `---`, and carries a
   `name:` matching its directory. Frontmatter checks are scoped to the head of the
   file — `---` also appears inside the output templates, where constraint 5 forbids
   touching it, so a whole-file delimiter count is not a frontmatter check.
4. **Markers are parsed downstream.** `❌`, `✅`, `🔴`, `🟡`, `🟢` and the
   `**Score: {X}/10**` shape stay byte-identical — `fluent-session-analyzer` and
   `results/README.md` depend on them.
5. **No pedagogy changes.** Output templates, exercise content, topic lists and
   session flow stay as they are except where the spec names them (spec §5).
6. **Python 3.8+, stdlib only.** No pip, no new dependency (`CONTRIBUTING.md`).
7. **Never hardcode `data/`.** Paths resolve through `fluent_paths.data_dir()` /
   `ensure_data_dir.py`, or the `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}`
   prefix for scripts.
8. **Verification never touches the learner's real data.** Any `update-db.py`
   invocation in a Verify step runs with `FLUENT_DATA_DIR` pointed at a temp dir.
9. **Conventional commits**, one per task: `<type>(<scope>): <subject>`.
10. **No CHANGELOG entry per task.** Refactor-only notes are excluded by house
    rule; `t17` writes the single user-facing entry for the whole sweep.

## Tasks

### Task 1: Validate `errors[].category` against the canon in `update-db.py`   [id: t1]
**Depends-on:** none
**TDD:** required
**Files:** `.claude/hooks/update-db.py`, `tests/test_update_db.py`
Add a `validate_error_categories(session)` alongside the existing
`validate_milestones`, called from `main` at the same gate — **before any DB file is
read or written**, so a bad payload exits `1` with no side effects even when the data
dir is empty. Accept exactly the eleven labels in spec §3.1; on anything else print
the offending index and value to stderr and `sys.exit(1)`, matching the wording style
`validate_milestones` already uses. A payload that omits `category` keeps defaulting
to `other` (the existing `error.get("category", "other")` behaviour). Leave
`new_vocabulary[].category` unvalidated — spec §3.1 says why. Tests: one accepted
label, one omitted key, one rejected label asserting exit `1` and an untouched data
dir.
**Verify:**
```bash
for t in tests/test_*.py; do echo "=== $t"; python3 "$t" -q; done   # every file: OK
D=$(mktemp -d); FLUENT_DATA_DIR=$D python3 .claude/hooks/update-db.py <<'EOF'
{"session_id":"session-999","date":"2026-08-20","errors":[{"pattern_id":"x","category":"structuur"}]}
EOF
echo "exit=$?"; find "$D" -type f | wc -l
# exit=1, stderr names index 0 and "structuur", 0 files written.
# `$D/.backups/` is created at import time by ensure_backups_dir() and is expected —
# assert on files, not on an empty dir.
```

### Task 2: Make `fluent-feedback-formatter` the single home of the category canon   [id: t2]
**Depends-on:** [t1]
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-feedback-formatter/SKILL.md`
Extend §"Use these category labels" to the ten labels of spec §3.1 with the three new
meanings, **plus `other`** carrying §3.1's note on why it stays accepted (it is the
+1, not one of the ten), and state that `update-db.py` enforces the set. Replace the description with
spec §3.6. Drop the formula from §"Hand score to the scheduler", keeping the pointer
to `fluent-fsrs-reference` (spec §3.2). Drop the two Critical Rules bullets named in
spec F10's table, moving each one's reason onto its step — «Deviations break
session-file parsing downstream» onto §"Standard template", «Drives spaced-repetition
priority» onto §"Tag severity on every error". Keep «One score per answer» and «Never
skip the "Correct version"».
**Verify:**
```bash
for c in grammar formal_informal vocabulary spelling prepositions articles missing \
         structure comprehension inference other; do
  rg -q "\b$c\b" .claude/hooks/update-db.py \
    && rg -q "\b$c\b" .claude/skills/fluent-feedback-formatter/SKILL.md || echo "MISSING $c"
done                                                              # no output
rg -c 'floor\(score' .claude/skills/fluent-feedback-formatter/SKILL.md   # no match
rg -c 'Deviations break session-file parsing|Drives spaced-repetition priority' \
   .claude/skills/fluent-feedback-formatter/SKILL.md                     # 2 (reasons survived)
sed -n '1,12p' .claude/skills/fluent-feedback-formatter/SKILL.md | grep -c '^---$'  # 2
```

### Task 3: Give `fluent-fsrs-reference` the quality-scale table   [id: t3]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-fsrs-reference/SKILL.md`
Adopt the score→quality meaning table currently in `LEARNING_SYSTEM.md`
§"Spaced Repetition (FSRS-6)" — six rows, `10 → 5 → Perfect` through
`0-1 → 0 → Complete blackout` — co-located under §"The pipeline" so the formula and
what each grade *means* sit together. Replace the description with spec §3.6.
**Verify:**
```bash
rg -c '^\| 0-1 \| 0 \|' .claude/skills/fluent-fsrs-reference/SKILL.md   # 1
rg -c 'floor\(score' .claude/skills/fluent-fsrs-reference/SKILL.md      # 1 (the only home)
```

### Task 4: Point `LEARNING_SYSTEM.md` at the reference instead of restating it   [id: t4]
**Depends-on:** [t3]
**TDD:** waived (doc prose)
**Files:** `LEARNING_SYSTEM.md`
Delete §"Quality scale" — the formula line and the six-row table — from
§"Spaced Repetition (FSRS-6)". The section already ends on «See the
`fluent-fsrs-reference` skill for the full pipeline and field list»; extend that
sentence to cover the score→quality scale so nothing is lost for the non-Claude CLIs
`AGENTS.md` routes here.
Second, one clause of §"Data Files You Must Use" — «Track each answer in your own
working notes during the session» — is the holding idea spec §3.4 renames, so it
adopts `stage`. That section's timing statement is already the shape §3.4 prescribes
(the rule plus a pointer to `fluent-db-updater`) and stays untouched. Everything else
in the file stays.
**Verify:**
```bash
rg -c 'floor\(score|Complete blackout' LEARNING_SYSTEM.md     # no match
rg -c 'fluent-fsrs-reference' LEARNING_SYSTEM.md              # >= 1
rg -c 'once, at session end' LEARNING_SYSTEM.md               # 1 (still there)
rg -c 'working notes' LEARNING_SYSTEM.md                      # no match
                        # NOT `Track each answer` — that phrase is broken across two
                        # lines in the source, so a line-oriented grep for it reports
                        # "no match" before the edit too and gates nothing.
```

### Task 5: Teach `fluent-session-analyzer` the full canon   [id: t5]
**Depends-on:** [t2]
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-session-analyzer/SKILL.md`
§"Extract error patterns" lists the seven old labels inline. Replace the inline list
with a pointer to `fluent-feedback-formatter`'s canon so it cannot drift again, and
make sure the scan recognises `structure`, `comprehension` and `inference`.
**Verify:**
```bash
rg -c 'fluent-feedback-formatter' .claude/skills/fluent-session-analyzer/SKILL.md  # >= 1
rg -c 'prepositions, articles' .claude/skills/fluent-session-analyzer/SKILL.md     # no match
```

### Task 6: Prune `fluent-db-updater`   [id: t6]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-db-updater/SKILL.md`
Description per spec §3.6. Drop the exit-code bullets from Critical Rules — §"Call the
script" already states them (spec F10) — and drop the formula from §"Field notes",
keeping the pointer (spec §3.2). Adopt `stage` (spec §3.4) wherever the file talks
about holding results for the end-of-session payload. Also note under
`errors[]` that the category must come from the canon and that `update-db.py` now
rejects anything else (spec F4).
This file is tier 1 of spec §3.4 — the one home of the timing rule *with its reason*.
Its «Call once per session, at the end» bullet stays, reworded only enough to carry
the literal `once, at session end`; no other skill may state the rule.
**Verify:**
```bash
rg -c 'floor\(score' .claude/skills/fluent-db-updater/SKILL.md   # no match
rg -c 'Exit code 1 means|Exit code 2 means' .claude/skills/fluent-db-updater/SKILL.md  # no match
rg -c 'Exit codes' .claude/skills/fluent-db-updater/SKILL.md     # 1
rg -c 'once, at session end' .claude/skills/fluent-db-updater/SKILL.md  # 1
rg -c 'rebuilds the review queue' .claude/skills/fluent-db-updater/SKILL.md  # >= 1 (reason stays)
```

### Task 7: Stop `CLAUDE.md` contradicting the skills   [id: t7]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `CLAUDE.md`
Close spec F1 and F5 in the one file that is loaded on every turn:
- §"Every Session You Must" step 6 («After every answer, update …») and the two
  Critical Rules about updating after every exercise state the rule in spec §3.4's
  **tier-2** shape: the literal `once, at session end` plus the pointer to
  `fluent-db-updater` for the why. The reason clause itself must not appear here —
  tier 1 declares `fluent-db-updater` the only home of the *why*, and a copy of it in
  always-loaded context is the duplication this sweep removes.
- The word «auto-invoke» is allowed to survive here, and only here: this file's
  statement that `/fluent-progress` auto-invokes on stats questions is an accurate
  description of the mechanism, not the no-op rule F9 removes from the skills.
- Every literal `/data` in the file goes, in favour of the resolved data directory
  (constraint 7) — not just §"Core Identity" and the *Key Files You Work With* paths
  but also §"Every Session You Must" step 2 («Load learner data from `/data`
  directory»).
- The table's *When* column carries the same contradiction in miniature — «Read &
  update every session», «Read daily, update after every answer», «Read before
  exercises, update after mistakes». Bring the whole column into line with the
  once-at-session-end rule; a row that says «update after every answer» outranks the
  skills' staging instruction because this file is always loaded.
- §"Learning Principles" item 6 reads `50-70%` (spec D2).
- The paragraph enumerating which skills carry `disable-model-invocation` collapses
  to the rule plus where to look, instead of caching the frontmatter.
**Verify:**
```bash
rg -ci '60-70|/data|after (every )?(exercise|answer|mistake)' CLAUDE.md  # no match
                        # `-i` is required: step 6 reads "After every answer" and the
                        # gate missed it while case-sensitive. `/data` catches the
                        # table rows, step 2 and §"Core Identity" alike; the
                        # `/results/...` row does not contain it. Verified against the
                        # current file: this pattern hits lines 9, 32, 36, 43-48, 76,
                        # 105 and does NOT hit the pedagogy lines 35 and 104
                        # («immediate feedback after each answer»), which must stay.
rg -c 'once, at session end' CLAUDE.md                                  # >= 1
rg -c 'fluent-db-updater' CLAUDE.md                                     # >= 1 (the why lives there)
rg -c 'rebuilds the review queue|partial updates' CLAUDE.md             # no match
                        # tier 2 states the rule and points; it does not restate the why
```

### Task 8: Sweep `fluent-writing`   [id: t8]
**Depends-on:** [t2]
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-writing/SKILL.md`
Description per spec §3.5. Delete the *When to Use* precondition (spec §2) and the
«Never auto-invoke» rule (F9). §"Systematic error analysis" points at the canon
instead of listing its own six categories — including for `structure`, which is now
a canon label (F4). §"Update all databases" ends on the spec §3.3 criterion; drop the
three Critical Rules bullets that restate steps per the F10 table. Adopt `stage`.
**Verify:**
```bash
rg -c 'auto-invoke|floor\(score' .claude/skills/fluent-writing/SKILL.md   # no match
rg -c 'results/README.md' .claude/skills/fluent-writing/SKILL.md          # 1
sed -n '1,12p' .claude/skills/fluent-writing/SKILL.md | grep -c '^---$'   # 2
```

### Task 9: Sweep `fluent-reading`   [id: t9]
**Depends-on:** [t2]
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-reading/SKILL.md`
Description per spec §3.5. Delete the *When to Use* precondition and «Never
auto-invoke». §"Update all databases" uses the canon labels `comprehension` /
`inference` with a pointer to the canon, and ends on the spec §3.3 criterion (this
skill's «include the full text + Q&A» detail survives inside it). Drop the two
Critical Rules bullets named in spec F10's table; keep the other four — «Don't reuse
a text», «Quote the text», «Vocabulary opt-in» and «Ask questions in the target
language». Adopt `stage`.
**Verify:**
```bash
rg -c 'auto-invoke' .claude/skills/fluent-reading/SKILL.md            # no match
rg -c 'results/README.md' .claude/skills/fluent-reading/SKILL.md      # 1
rg -c 'fluent-feedback-formatter' .claude/skills/fluent-reading/SKILL.md  # >= 1
```

### Task 10: Sweep `fluent-speaking`   [id: t10]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-speaking/SKILL.md`
Description per spec §3.5. Delete the *When to Use* precondition and «Never
auto-invoke». §"Update all databases" ends on the spec §3.3 criterion. Keep
«Communication first», «Stay in the target language», «Praise natural expression»,
«Don't over-correct» — no step carries them. Drop «One question at a time», which
§"One question at a time" already owns. Adopt `stage`.
**Verify:**
```bash
rg -c 'auto-invoke' .claude/skills/fluent-speaking/SKILL.md         # no match
rg -c 'results/README.md' .claude/skills/fluent-speaking/SKILL.md   # 1
```

### Task 11: Sweep `fluent-vocab`   [id: t11]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-vocab/SKILL.md`
Description per spec §3.5. Delete the *When to Use* precondition and «Never
auto-invoke». Drop the formula from §"Feedback after each answer", keeping the
pointer. Add the spec §3.3 criterion to §"Update all databases" — this skill has no
session-file step at all today. Drop the three Critical Rules bullets that restate
steps per the F10 table. Adopt `stage`.
This file holds all three of spec §3.4's retired phrasings — «Track the answer for»
and «batch at session end» in §"Feedback after each answer", «collected during the
session» in §"Update all databases". They become the staging form (tier 3): stage the
result, let `fluent-db-updater` write. Do **not** restate the timing rule here.
**Verify:**
```bash
rg -c 'auto-invoke|floor\(score' .claude/skills/fluent-vocab/SKILL.md   # no match
rg -c 'results/README.md' .claude/skills/fluent-vocab/SKILL.md          # 1
rg -c 'batch at session end|collected during the session|Track the answer|once, at session end' \
   .claude/skills/fluent-vocab/SKILL.md                                 # no match
                        # the negative gate is the real one — a `stage` count gate
                        # would pass on the untouched file, which already says
                        # "stage it for `new_vocabulary[]`" twice.
```

### Task 12: Sweep `fluent-review`   [id: t12]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-review/SKILL.md`
Description per spec §3.5. Delete the *When to Use* line — §"Load review queue"
already implements the empty-queue branch (spec §2) — and «Never auto-invoke». Drop
the formula from §"Evaluate + submit the score", keeping the pointer and the
`quality <= 2` explanation. §"Update all databases" ends on the spec §3.3 criterion.
Drop the two Critical Rules bullets that restate steps; keep «Daily» and «Let the
learner struggle». Adopt `stage`. Leave §"What the Schedule Means" in place — `t16`
moves it.
**Verify:**
```bash
rg -c 'auto-invoke|floor\(score' .claude/skills/fluent-review/SKILL.md   # no match
rg -c 'results/README.md' .claude/skills/fluent-review/SKILL.md          # 1
```

### Task 13: Sweep `fluent-learn` and fix its routing   [id: t13]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-learn/SKILL.md`
Description per spec §3.5. §"Route" implements spec D3: for menu items 1-5, read
`.claude/skills/<target>/SKILL.md` and follow it in the same session, keeping
`command_used: "/fluent-learn"` so the session stays one record — say plainly that
those skills are gated and cannot be invoked as skills. §"Adaptive difficulty" reads
`50-70%` (already correct — confirm it survives). Delete the *When to Use*
precondition (§1 already routes missing DBs to `/fluent-setup`) and «Never
auto-invoke». §"Session end" ends on the spec §3.3 criterion. Adopt `stage`.
**Verify:**
```bash
rg -c 'auto-invoke' .claude/skills/fluent-learn/SKILL.md                    # no match
rg -c 'hand off to the matching skill' .claude/skills/fluent-learn/SKILL.md # no match
rg -c 'SKILL.md' .claude/skills/fluent-learn/SKILL.md                       # >= 1
rg -c 'results/README.md' .claude/skills/fluent-learn/SKILL.md              # 1
```

### Task 14: Sweep `fluent-setup` and fix its hand-off   [id: t14]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-setup/SKILL.md`
Description per spec §3.5 — the «Must never auto-invoke because re-running can reset
progress» clause goes; its reason already lives in the «Confirm twice before reset»
rule. §"Optional first lesson" implements spec D3 (read
`.claude/skills/fluent-learn/SKILL.md` and follow it). Delete the *When to Use*
precondition — §"Check for existing profile" already branches on it — and both
«Never auto-invoke» occurrences. Keep every reset guardrail. Leave
§"Profile Updates (existing profile)" in place — `t16` moves it.
**Verify:**
```bash
rg -c 'auto-invoke' .claude/skills/fluent-setup/SKILL.md                # no match
rg -c 'Confirm twice before reset' .claude/skills/fluent-setup/SKILL.md  # 1
rg -c 'hand off to the `fluent-learn` skill' .claude/skills/fluent-setup/SKILL.md  # no match
rg -c 'fluent-learn/SKILL.md' .claude/skills/fluent-setup/SKILL.md      # >= 1
                        # positive gate: the D3 replacement must exist. Without it,
                        # deleting §"Optional first lesson" outright passes.
```

### Task 15: Collapse `fluent-progress`'s triple-stated trigger   [id: t15]
**Depends-on:** none
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-progress/SKILL.md`
Description per spec §3.6 — six synonyms and «safe to auto-invoke» go. §"When to
Use" keeps only the genuine second branch (skip mid-practice) and stops repeating the
trigger synonyms. **Critical Rules stay exactly as they are** — spec F10 explicitly
puts this skill out of scope, all six bullets are report rules no step carries. Leave
§"Optional interpretation footer" in place — `t16` moves it.
**Verify:**
```bash
rg -c 'how am I doing|safe to auto-invoke|auto-invoke' .claude/skills/fluent-progress/SKILL.md  # no match
rg -c 'Read-only|current streak value|Skip sections with no data' .claude/skills/fluent-progress/SKILL.md  # 3
```

### Task 16: Disclose the three branch-only sections   [id: t16]
**Depends-on:** [t12, t14, t15]
**TDD:** waived (doc prose)
**Files:** `.claude/skills/fluent-setup/SKILL.md`,
`.claude/skills/fluent-setup/PROFILE-UPDATES.md`,
`.claude/skills/fluent-progress/SKILL.md`,
`.claude/skills/fluent-progress/STATS-GLOSSARY.md`,
`.claude/skills/fluent-review/SKILL.md`,
`.claude/skills/fluent-review/SCHEDULE-MEANING.md`
Move each section named in spec F14 into its sibling file and leave a context pointer
where it was — one line naming the file and the branch that reaches it. The moved text
travels unchanged; the pointer must state the condition, not just the filename.
**Verify:**
```bash
for f in fluent-setup/PROFILE-UPDATES fluent-progress/STATS-GLOSSARY \
         fluent-review/SCHEDULE-MEANING; do
  test -s ".claude/skills/$f.md" || echo "MISSING $f"
done                                                                    # no output
rg -c 'PROFILE-UPDATES.md' .claude/skills/fluent-setup/SKILL.md         # 1
rg -c 'STATS-GLOSSARY.md' .claude/skills/fluent-progress/SKILL.md       # 1
rg -c 'SCHEDULE-MEANING.md' .claude/skills/fluent-review/SKILL.md       # 1
rg -c 'Reset progress' .claude/skills/fluent-setup/SKILL.md             # no match (moved)
```

### Task 17: One user-facing CHANGELOG entry, and re-point the stale citations   [id: t17]
**Depends-on:** [t1, t2, t5, t7, t8, t9, t10, t11, t13, t16]
**TDD:** waived (content)
**Files:** `CHANGELOG.md`, `tasks/lessons.md`
Add one `[Unreleased]` entry covering only what a learner would notice: menu items
1-5 in `/fluent-learn` now actually start the chosen practice; session files are
written in the format the analyzer can parse; text-structure and reading-inference
mistakes are now tracked and drilled instead of silently dropped; an unknown error
category fails loudly instead of landing in the DB; databases are written once at
session end instead of after every exercise; one difficulty band. No entry for the
doc-pruning tasks (house rule: no refactor-only notes).
This task shifts `CHANGELOG.md`'s line count, and `t16`/`t14` shifted
`fluent-setup/SKILL.md`'s, so it also owns the two live line citations in
`tasks/lessons.md` §"2026-08-17 — skills are calling code": re-point
`.claude/skills/fluent-setup/SKILL.md:24` and `CHANGELOG.md:118` to name the section
and the entry instead of a line.
**Verify:**
```bash
rg -n '[a-zA-Z0-9_.-]+\.(md|json|py|sh|js|mjs):[0-9]+' --hidden \
   --glob '!.git' --glob '!docs/orchestrion' .          # no matches
rg -c 'ensure_data_dir' tasks/lessons.md                # >= 1 (the lesson still lands)
```

### Task 18: Cross-file consistency sweep   [id: t18]
**Depends-on:** [t4, t6, t10, t11, t12, t15, t17]
**TDD:** waived (verification only)
**Files:** none expected; fix-ups land in whichever file the sweep indicts
Run the repo-wide invariants from spec §6 and fix whatever they catch. Close gaps the
per-file tasks left; do not restate or re-word what they produced. If an invariant
indicts a file whose owning task is already correct, the invariant is wrong — say so
rather than editing the file.
**Verify:**
```bash
for t in tests/test_*.py; do echo "=== $t"; python3 "$t" -q; done   # every file: OK
rg -n 'auto-invoke' .claude/skills/                                # no match
                        # scoped to the skills on purpose: CLAUDE.md keeps the word
                        # for the /fluent-progress mechanism (see t7)
rg -l --hidden --glob '!.git' --glob '!docs/orchestrion' 'floor\(score' .
                        # exactly .claude/skills/fluent-fsrs-reference/SKILL.md
rg -n --hidden --glob '!.git' --glob '!docs/orchestrion' '60-70' .      # no match
rg -n 'prepositions.*articles' .claude/skills/                     # no match
                        # spec §6: one home for the category list. The canon lists
                        # one label per line, so a same-line pair means someone
                        # re-inlined the taxonomy instead of pointing at it.
rg -n 'batch at session end|collected during the session|Track the answer' .claude/skills/
                        # no match — spec §3.4's retired phrasings
rg -l 'once, at session end' --hidden --glob '!.git' --glob '!docs/orchestrion' .
                        # exactly three files: CLAUDE.md, LEARNING_SYSTEM.md,
                        # .claude/skills/fluent-db-updater/SKILL.md — spec §3.4's
                        # three tiers. A fourth means someone copied the rule again;
                        # a missing one means a tier is unstated.
rg -c 'results/README.md' .claude/skills/fluent-{learn,writing,speaking,reading,vocab,review}/SKILL.md
                        # 1 for each of the six
for f in .claude/skills/*/SKILL.md; do
  printf '%s %s\n' "$(sed -n '1,12p' "$f" | grep -c '^---$')" "$f"; done  # 2 for every file
```
