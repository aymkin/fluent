# Session state — `writing-for-agents` sweep

Written 2026-08-21, before context compaction and before `execute` starts. This file
plus the spec and the plan are enough to resume; nothing needed is only in the
conversation.

## Where the work is

- **Branch:** `chore/writing-for-agents-sweep`, cut from `main`. Not pushed.
- **Commits so far:** `66269f6 docs(skills): spec and plan for the writing-for-agents sweep`
  plus this state file and a `tasks/lessons.md` entry. **No task has been executed.**
- **Spec:** `docs/orchestrion/specs/2026-08-20-skills-writing-for-agents.md` — owns the
  14 findings, the three human decisions, and the canon (§3).
- **Plan:** `docs/orchestrion/plans/2026-08-20-skills-writing-for-agents.md` — 18 tasks,
  five dependency batches.
- **Next action:** invoke `orchestrion:execute` on the plan. Nothing else is pending.

## Decisions already taken — do not reopen

The human chose all three (spec §2 carries them with the provenance marks):

1. Error-category canon expands to ten labels and is **enforced in code**
   (`update-db.py` exits 1 on anything outside the set).
2. The desirable-difficulty band is **50-70%**. `CLAUDE.md` is the outlier.
3. `fluent-learn` / `fluent-setup` hand off by **reading the target skill's
   `SKILL.md`** and following it in the same session. The gate on the practice
   skills stays.

One assumption was taken without asking (spec §2, F12): the unimplemented mastery
preconditions in the gated skills' *When to Use* sections are deleted rather than
wired in. Flagged to the human; not contested.

## Review record

Three rounds, one fresh read-only reviewer each, review-debug tier. 18 defects found
and addressed. The round-3 reviewer's closing judgement: with its four fixes applied,
the plan is executable as written.

Round-by-round, what actually mattered:

- **R1 (9 findings).** Three gates were unachievable by construction — a whole-file
  `---` count as a frontmatter check (templates also use `---`), an empty-temp-dir
  assertion against a script that creates `.backups/` at import, and a repo-wide
  `auto-invoke` grep that would indict `CLAUDE.md`'s legitimate use. `fluent-progress`
  was wrongly placed in F10 scope: none of its six Critical Rules restates a step, so
  the instruction to prune them would have destroyed meaning. F13 (`stage`) was
  instructed in seven tasks and verified in none.
- **R2 (5 findings).** The timing rule was tasked into only one of its homes. Fixed by
  **rewriting spec §3.4 into three tiers**, deliberately *not* by the reviewer's
  suggested fix (repeat one sentence in eight files), which would have re-created the
  duplication the sweep exists to remove. Also: t7's gate missed half the
  contradictions its own body named; t14 could be satisfied by deleting the section it
  was supposed to fix; t17's dependencies omitted two tasks whose behaviour its
  CHANGELOG entry describes; t2's pruning had no spec provenance.
- **R3 (4 findings).** t7's body contradicted the tier design it implements, and the
  natural repair passed every gate while violating it. t4's gate was a no-op because
  the phrase it matched is line-wrapped. t7's gate was still case-sensitive against a
  capitalised occurrence. t11's positive `stage` gate was already satisfied on the
  untouched file.

## Open item — one, and it is a process gap, not a known defect

**The final state of the plan has not been seen by a fresh reviewer.** The loop's
three-iteration cap was reached, so round 3's four fixes were verified by hand
(commands below) rather than by a fourth reviewer. Round 3 said the plan is executable
with exactly those fixes, and they are applied as specified. If you want the belt-and-braces
pass, dispatch one more read-only reviewer before `execute`; otherwise proceed.

## Gate baselines — measured 2026-08-21 on the untouched tree

Every gate below is currently **red** and turns green only on a real change. This is
the "before" column; a resumed session can re-run these to prove progress, and their
existence is why the lesson in `tasks/lessons.md` was written.

| Gate | Now | After a correct sweep |
|---|---|---|
| `rg -ci '60-70\|/data\|after (every )?(exercise\|answer\|mistake)' CLAUDE.md` | 11 | no match |
| `rg -c 'working notes' LEARNING_SYSTEM.md` | 1 | no match |
| `rg -l 'once, at session end'` (repo, minus `.git` and `docs/orchestrion`) | 1 file | 3 files |
| `rg -l 'auto-invoke' .claude/skills/` | 8 files | none |
| `rg -l 'floor\(score'` (same scope) | 6 files | only `fluent-fsrs-reference` |
| `rg -n 'prepositions.*articles' .claude/skills/` | `fluent-session-analyzer` | no match |
| `rg -n 'batch at session end\|collected during the session\|Track the answer' .claude/skills/` | 3 hits, all `fluent-vocab` | no match |
| `rg -c 'results/README.md'` × the six session skills | 0 each | 1 each |
| citation sweep `[a-z.-]+\.(md\|json\|py\|sh\|js\|mjs):[0-9]+` | 2 hits in `tasks/lessons.md` | no match |
| `for t in tests/test_*.py; do python3 "$t" -q; done` | all OK | all OK |

`sed -n '1,12p' SKILL.md \| grep -c '^---$'` is 2 for all twelve skills today and must
stay 2 — it is the one invariant that is already green, and the reason it is scoped to
the head of the file is R1's finding.

## Things a fresh context would otherwise get wrong

- `rg` skips dot-directories by default, so `.claude/` needs `--hidden` when searching
  from the repo root without naming the path. Two counts in the original review were
  briefly wrong for this reason.
- The data directory is resolved, never literal: `FLUENT_DATA_DIR` wins, then
  `$CLAUDE_PROJECT_DIR/data`, then `./data`, then `~/.claude/fluent-data`. Point
  `FLUENT_DATA_DIR` at a temp dir for any verify that runs `update-db.py` — the real
  databases hold live learner progress.
- Tests run the hooks as subprocesses (`SCRIPT = REPO_ROOT / ".claude" / "hooks" / …`),
  not by import, so there is no module to import an enum from; doc-vs-code agreement
  is checked by grepping both sides.
- `results/README.md` is the canonical session-file format and is already correct.
  `AGENTS.md` is already correct. Neither is in scope.
