# Minor findings — writing-for-agents sweep

Recorded verbatim per task, never fix-dispatched on their own. Pasted into the final
broad review for triage.

## Batch 1a

- **t1** — `tests/test_read_db.py` and `tests/test_update_db.py` spawn the hook scripts
  via `subprocess` without scrubbing the parent environment, so an **exported**
  `FLUENT_DATA_DIR` overrides the per-test fixture dir and turns both suites spuriously
  red. Pre-existing; not caused by t1. Every Verify command in this plan uses the
  prefix form (`FLUENT_DATA_DIR=$D python3 …`), which does not export, so no gate in
  this sweep is affected. Triage candidate: `env.pop("FLUENT_DATA_DIR", None)` in the
  test harness.
- **t1** — `validate_error_categories` skips a non-dict entry in `errors[]` rather than
  rejecting it. Deliberate: out of scope for category validation, and existing
  behaviour (`update_mistakes_db`'s `error["pattern_id"]`) still exits 2 on such an
  entry. Flagged by the implementer's own self-review.

## Batch 1b

Routed to `t18` rather than left for triage (each is a confirmed gap in an
already-merged file, which is precisely `t18`'s remit):
- `fluent-vocab:12` §Overview restates two deleted F10 bullets and echoes the timing rule.
- `fluent-review` §4 states the queue rebuild twice.
- `fluent-learn:59` «in this same session» vs `fluent-setup:165` «in this session» vs D3's «in the same session».

Left for final triage:
- `fluent-learn/SKILL.md:88` — wording churn: the line already used `stage` before the
  edit, so §3.4's "adopt `stage`" was arguably satisfied without touching it.
## Batch 2 — all for final triage, none routed

- `fluent-feedback-formatter/SKILL.md:18` §"When to Use" still names three canon labels
  as open-ended examples («grammar, vocabulary, prepositions, etc.»). Not a second copy
  of the list — no meanings, explicitly illustrative — and no spec clause forbids it.
- `fluent-setup` Critical Rules keep «Confirm twice before reset» and «Back up before
  reset» while the operative reset step now lives in `PROFILE-UPDATES.md`. The rule and
  its step are now in different files, which is worse co-location — but spec F10's
  survival list explicitly keeps both bullets, and duplicating a data-loss guardrail is
  the right side to err on. Deliberate, not an oversight.
- `PROFILE-UPDATES.md:29` says «Then restart setup from Step 2» — a back-reference into
  `SKILL.md`'s step numbering from the sibling file. It travelled verbatim as F14
  requires and still resolves, but it couples the sibling to the parent's numbering.
- `fluent-progress/SKILL.md:102` — «### 3. Optional interpretation footer» is still a
  numbered Instructions step now holding only a pointer. Keeping the heading preserves
  the spec's §-citation, so this is correct as delivered.
- `LEARNING_SYSTEM.md:88-89` — non-Claude CLIs that `AGENTS.md` routes here now find the
  score→quality scale one hop away in a skill file, and nothing tells them skill files
  are plain readable markdown. `AGENTS.md:31` already prescribes reading `SKILL.md`
  directly (the D3 precedent), so the hop is established practice, but a half-sentence
  in `LEARNING_SYSTEM.md` would remove the doubt.

## Batch 3

Routed to `t18`: the `{skill}` reversal (speaking, vocab), `fluent-reading:78`'s
heading restatement, and the `FLUENT_DATA_DIR` test-harness leak.

Left for final triage:
- `fluent-session-analyzer:41` names `comprehension`, `inference`, `structure` inline as
  behavioural examples. Deliberate: the task requires visible evidence the scan
  recognises them, and a bare pointer shows nothing. Not a second copy of the canon.
- `fluent-session-analyzer` §2 still restates the feedback shape («The wrong form», «The
  correct form») and the severity gloss `(🔴 critical, 🟡 moderate, 🟢 minor)`, both
  duplicating `fluent-feedback-formatter`. Real sediment, but collapsing it means the
  pointer must carry the parse contract for the whole `❌` line — that needs a task owning
  both files, which this sweep does not have.
- The §3.3 criterion is line-wrapped in some skills and single-line in others. Cosmetic,
  but a single-line `rg` for the full sentence will miss the wrapped ones — a
  verification hazard for the broad review, not a defect in the files.

## t17 — left for final triage

- `CHANGELOG.md:184-187` — the off-canon rejection changes what input is *accepted* (any
  string used to save; now exit 1), and the file's own precedent for that class (the
  `milestones[]` object-form removal) leads with bold rather than sitting mid-bullet under
  `Fixed`. Low stakes: the only payload authors are the skills, all updated in this sweep.

