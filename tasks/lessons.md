# Lessons

## 2026-08-17 — jq queries against the read-db.py dump

`read-db.py` prints ~300KB, so the result is persisted to a file and has to be
queried with `jq`. Two avoidable errors:

- **exit 5** (jq runtime error) — queried `.databases.progress` / `.mistakes` /
  `.mastery`; the real keys are `progress_db`, `mistakes_db`, `mastery_db`.
  `null | keys` raises. Read key names first, don't guess.
- **exit 3** (jq compile error) — `{lvl: .a // .b}` is invalid; the `//`
  operator needs parens inside an object constructor: `{lvl: (.a // .b)}`.

Also: chaining probes with `&&` means one failure cancels the rest of the batch.
Use `;`. And `read-db.py --review` already returns a trimmed payload for
`/fluent-review` — no need to filter the full dump.

## 2026-08-17 — skills are calling code; grep them before declaring anything dead

The ponytail audit reported `.claude/hooks/ensure_data_dir.py` as having zero
callers and queued it for deletion. It has one:
`.claude/skills/fluent-setup/SKILL.md` invokes it as the prescribed bootstrap
recipe in §"Overview" and again in §"1. Check for existing profile", and
`CHANGELOG.md`'s 0.2.0 §"Fixed" entry "Added missing
`.claude/hooks/ensure_data_dir.py` referenced by `fluent-setup`" records that its
*absence* was already shipped once as a bug. Deleting it would have regressed
that fix and broken onboarding. The subagent executing the deletion caught it
and refused.

Why it happened: in this repo the `.md` files under `.claude/skills/` *are* the
program — they hold the bash Claude actually runs. I grepped for invocations the
way you would in a normal codebase and mentally filtered markdown hits as "just
docs".

How to apply: before calling any script or helper dead in a Claude Code plugin,
grep the whole tree with no path exclusions, for both the
filename-with-extension and the bare symbol, and read every `.md` hit as a
potential call site. A hit in `.claude/skills/**/SKILL.md` is a caller. A
CHANGELOG entry saying a file was added *because something referenced it* is
direct evidence of a live dependency.

## 2026-08-17 — check the worktree's base commit before trusting any agent report

Round 2 dispatched four agents with `isolation: "worktree"`. Every worktree was
created from `126cb4b` — `origin/main` — not from local `main` at `21fe65f`.
Round 1's entire cleanup (nine merges, −1801 lines) was missing from all four.
The agents did competent work on a tree that no longer exists.

The tell was in the reports, not in git: three agents independently said
"there are **six** test files, not four". Two more contradicted the audit on
specifics — `.claude/settings.json` still wiring clone-mode hooks, the
Star-This-Project block still in README, `marketplace add ./` appearing
nowhere. Those read as *the audit was wrong*; they were actually *the base is
wrong*. Symmetrically, the agents' own line numbers were off by 10-35 in every
file round 1 had touched, which one of them noticed and worked around without
drawing the conclusion.

The dangerous part is what a merge does with this. Task D refactored two
duplicated dict literals in `update-db.py` into a helper. Round 1 had deleted
`easiness_factor: 2.5` and the `tomorrow()` helper from *those same literals*.
A three-way merge kept `easiness_factor` — git saw it as content the agent
newly wrote, not a line `main` had removed — and kept a call to `tomorrow()`,
which no longer exists, so the merged file would have raised `NameError` on the
first new vocabulary item. Both were invisible in the diffstat and in the
agent's own byte-identity proof, which was correct against the base it ran on.

How to apply: before dispatching, run `git rev-parse HEAD` and tell the agent
the SHA it must be on; after it returns, run
`git merge-base --is-ancestor HEAD <branch>` before reading a single line of
the report. If the base is stale, do not merge the branch — `git merge-file`
each owned file against the real base, resolve every conflict by hand, and then
grep the result for the specific things the intervening commits deleted. A
clean merge is not evidence of a correct merge. And re-verify any behavioural
proof the agent supplied; equivalence against the wrong base proves nothing.

## 2026-08-17 — give parallel agents file ownership, not topics

Four agents worked simultaneously in git worktrees and all four merged with zero
conflicts, because each brief listed the exact paths it owned and the exact paths
it must not touch, and `CHANGELOG.md` was assigned to nobody (written after the
merges). Splitting by theme would have put three agents in `README.md` at once.

The cost: work that crosses a boundary can't be finished by the agent that finds
it. Task A deleted `.claude/references/feedback-template.md` while the dangling
pointer to it sat in Task D's file; Task C's decision to delete
`.claude/settings.json` invalidated clone-install instructions in Task A's
`README.md` after A had already finished. Both were reported instead of silently
crossed — the right behavior, but it means the orchestrator must budget for a
post-merge pass and must ask each agent to flag out-of-boundary consequences.

## 2026-08-18 — a green local test run says nothing about skipped tests

The round-4 audit reported `fsrs.schedule()`'s `weights=` parameter as dead
flexibility: the optimizer that produced the vector had been deleted and grep
showed `spaced_repetition.metadata.weights` was read but never written. Both
facts were true. The parameter still had a live caller —
`tests/test_fsrs_crosscheck.py`, which passes py-fsrs's own parameters into it.
The local suite reported OK because that file is `@unittest.skipUnless(HAVE_FSRS)`
and py-fsrs only exists in `.devvenv`. A skipped test is a test that did not
run; "all tests pass" is not evidence about it.

How to apply: when a symbol is a candidate for deletion, grep `tests/` for it
explicitly rather than trusting a green run, and run the gated suites with the
interpreter that can actually execute them (`.devvenv/bin/python
tests/test_fsrs_crosscheck.py`) before and after the change. When the only
caller turns out to be a test, ask what the test was buying: here it was
silently absorbing any drift between the hardcoded `DEFAULT_W` and the pinned
package, so removing the parameter was still right, but only alongside an
explicit `DEFAULT_W == Scheduler().parameters` assertion to keep the gate.

## 2026-08-21 — a verify command has to be run against the pre-change tree

Three review rounds on the `writing-for-agents` sweep plan found 18 defects. The
largest single class — 6 of the 18 — was verify commands that gated nothing,
and every one of them was invisible on self-review and obvious the moment the
command was actually run against the untouched repo:

- `awk '/^---$/{n++} END{print n}' SKILL.md` = 2 as a frontmatter check. `---`
  also delimits the output templates, so the real counts are 3-5 and the gate
  could never go green. Worse, the sweep task was told "fix whatever the sweep
  catches", so the gate actively pushed an implementer to strip template rules.
- `ls -A "$tmpdir"` expecting empty, when `update-db.py` creates `.backups/` at
  import time, before `main` runs.
- `rg -c 'Track each answer' LEARNING_SYSTEM.md # no match` — the phrase is
  broken across two lines in the source, so a line-oriented grep answers "no
  match" before the edit too.
- `rg -c 'stage|Stage'` >= 2, already satisfied by the untouched file.
- A case-sensitive `after every answer` that missed the file's `After every
  answer`.

How to apply: run every `**Verify:**` command while writing the plan, and record
what it prints *now* next to what it must print after. A gate whose two states
are identical is not a gate. Corollary for greps as gates: check whether the
phrase you are matching is line-wrapped, whether case varies, and whether some
legitimate line also matches — for the last one, name the lines that must NOT
match in a comment beside the command, so the next reader can tell a false
positive from a regression.
