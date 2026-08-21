# ⚠️ cannot-verify-from-diff items and their controller resolutions

## Batch 1a — resolved by the controller

| Task | ⚠️ item | Resolution |
|---|---|---|
| t1 | TDD test-first ordering not confirmable from a single squashed commit | **Not a gap.** The implementer's report carries the RED block: 6 failures across `category='structuur'`, `'Grammar'`, `''`, `None`, `42`, `['grammar']` before the change, GREEN after. The contract makes the implementer's report the test evidence; reviewers do not re-run it. |
| t3 | «Mapping has ONE home» — the table still stands in `LEARNING_SYSTEM.md` | **Not a gap.** `t4` owns that deletion (`Depends-on: [t3]`, batch 2) and its Verify gates `rg -c 'floor\(score\|Complete blackout' LEARNING_SYSTEM.md # no match`. |
| t6 | The new doc claim «`update-db.py` now rejects anything else» is false in this worktree | **Resolved by merge order.** `t1` implements the rejection and was merged first (`521ffd9` before `422b256`); re-verified on the merged tree — an off-canon category exits 1 with 0 files written. |
| t6 | `once, at session end` cross-file invariant spans unmerged branches | **Deferred to `t18`,** which owns the repo-wide grep (exactly three files). Measured on the merged tree so far: `CLAUDE.md` 2, `fluent-db-updater` 1, `LEARNING_SYSTEM.md` 1 — `t4` keeps its one, so the invariant is on track. |
| t7 | Full test suite not run for a prose-only change | **Not a gap.** Run by the controller on the merged tree: all four suites OK. |

## Plan/spec defects the reviewers surfaced — controller rulings

1. **Spec F1's first bullet contradicts spec §3.4** (flagged independently by t7's
   reviewer). F1 says `CLAUDE.md` «states the rule that way and explains why (the script
   rebuilds the review queue on every run)»; §3.4's three tiers say the *why* lives only
   in `fluent-db-updater`, and t7's Verify forbids it in `CLAUDE.md`. F1 is residual text
   from before §3.4 was rewritten in review round 2. **§3.4 governs** — the
   implementation is correct. Spec F1 corrected to match, so the final broad review does
   not re-raise it as a live contradiction.
2. **`LEARNING_SYSTEM.md`'s «Track each answer in your own working notes»** — t7's
   reviewer asked who rules on it. **`t4` owns it**; its brief already says that clause
   «is the holding idea spec §3.4 renames, so it adopts `stage`», and its Verify gates
   `rg -c 'working notes'` to no match.
3. **`fluent-writing`'s Title-Case display strings vs the lowercase canon** (t1's
   implementer, confirmed by its test pinning `"Grammar"` as rejected). Real integration
   risk now that enforcement is live. **`t8` owns it**; a controller note was appended to
   its brief distinguishing the display heading from the DB category value.
4. **§3.6 descriptions containing `: ` need YAML quoting** (t3's reviewer). Checked by the
   controller across all twelve skills on the merged tree: every frontmatter parses
   (`yq`). A parse gate was appended to `t18`'s brief so the remaining description
   rewrites (`t2`, and the seven §3.5 ones) cannot land broken.

## Batch 1b — resolved by the controller

| Task | ⚠️ item | Resolution |
|---|---|---|
| t11, t10 | Do all six session skills carry the §3.3 sentence with the literal `{skill}`, or their own name? Raised independently by two implementers and three reviewers. | **Verbatim `{skill}` stays.** Not a preference call — it is the repo's own convention: `results/README.md:13` (self-declared canonical format, spec §5 keeps it unchanged) writes the pattern as `/results/fluent-{skill}-session-{NNN}.md` and supplies the concrete example on the next line, and `fluent-session-analyzer:27` writes the identical string. Substituting per skill would be the drift. Six byte-identical copies also keep the greppable invariant meaningful. |
| t13 | Does the routed branch cohere with the five target skills' own session-end steps (no double record)? | **Coheres.** `fluent-learn:59` keeps `command_used: "/fluent-learn"` and sends the agent back to «finish with step 8 below», so the routed session produces one record. The five targets' final steps end on the §3.3 criterion (a save instruction), not on their own `update-db.py` call — verified on the merged tree for all five. |
| t14 | `tasks/lessons.md:22` cites `fluent-setup/SKILL.md:24`, now moved | **`t17` owns it** — global constraint 1 assigns it, and its Verify runs the repo-wide citation sweep. |

## Batch 2 — resolved by the controller

| Task | ⚠️ item | Resolution |
|---|---|---|
| t16 | Were `t12`, `t14`, `t15` complete before this task? Not visible in a single-commit diff. | **Yes.** All three merged in batch 1b; `t16`'s worktree was cut from `941db0c`, the branch tip *after* those merges, so it moved the post-sweep text — which is what its controller note instructed. |

## Batch 3 — resolved by the controller

| Task | ⚠️ item | Resolution |
|---|---|---|
| t9 | Does spec §6's test suite still pass? Doc-only diff, not re-run per the test budget. | **Passes.** Run by the controller on the merged tree after every batch; all four files OK. |
| t8, t9 | The `{skill}` placeholder is inconsistent across the tree | **Confirmed and reversed.** Measured on the merged tree: `fluent-writing:154`, `fluent-reading:170`, `fluent-review:151`, `fluent-learn:126` concretised; `fluent-speaking:164`, `fluent-vocab:98` literal. My batch-1b ruling was the weaker reading — see `t18` note 4 for the reversal and its reasoning. Routed to `t18`. |

### A plan defect that turned out not to be one

`t9`'s reviewer flagged spec F10 as internally tense for `fluent-reading`: it lists
§"Present the text" as owning the «Wait for "ready"» rule, but that step's only statement
of it was learner-facing template copy, so deleting the bullet would drop the
agent-facing instruction. Checked on the merged tree — `fluent-reading/SKILL.md:74` now
reads «Wait for `"ready"` before asking the first question — rushing the reading step
defeats the purpose.» The implementer moved the rule *and* gave it a reason. F10 honoured,
nothing lost.

## t17 / t18 — resolved by the controller

| Task | ⚠️ item | Resolution |
|---|---|---|
| t17 | Does `docs/orchestrion` hold a stale `file.md:NN` the sweep's exclusion hides? | **No.** One match in there, `plans/…:395`, and it is t17's own task text quoting the two strings it had to fix. The plan is a historical record; the orchestrion plan skill states its citations are as-of references and must not be re-pointed. |
| t18 | The whitespace-tolerant replacement gate was not in the reviewer's inputs, and a form tolerant at only one gap returns 5, not 6 — silently indistinguishable from a missing file. | **The form I ran is the correct one** and returns 6: `rg -Ul 'Every\s+`❌`\s+line\s+carries\s+its\s+category\s+and\s+its\s+severity\s+emoji' .claude/skills/ \| wc -l`. `-U` plus `\s+` at every word boundary. Now recorded in `tasks/lessons.md` so the next run does not re-derive it. |
| t18 | `fluent-reading/SKILL.md:171` interpolates «Include the full text + Q&A for later analysis.» between spec §3.3's two sentences — was that blessed by the owning task? | **Yes, explicitly planned.** t9's brief says the criterion is adopted «(this skill's «include the full text + Q&A» detail survives inside it)». Authorised interpolation, not drift; t18 was right to leave it. |

## Judgement calls the controller accepted, with the evidence

1. **t18 declared gate (b) wrong and left it unenforced.** Upheld — by its own reviewer independently, and by me. All six session skills carry the criterion unmangled; spec §3.3's own blockquote is hard-wrapped at the same points, so the wrapped files are the *faithful* ones. Making the literal gate pass would have meant re-flowing four files whose tasks are already correct — the exact re-wording t18 is forbidden to do.
2. **t18 scrubbed `CLAUDE_PROJECT_DIR` as well as `FLUENT_DATA_DIR` from the test subprocess env.** Upheld. `fluent_paths.py:35-51`: `FLUENT_DATA_DIR` wins unconditionally, then `$CLAUDE_PROJECT_DIR/data` wins whenever it holds `learner-profile.json` — i.e. precisely when a learner's real data dir exists — and only then does the `./data` leg the fixtures use get a look. Pre-fix, a suite run under Claude Code in a live clone read and wrote the real data dir (`update-db.py` creates `.backups/` there). Two test-only lines to close a path into learner data; constraint 8 exists for exactly this.
