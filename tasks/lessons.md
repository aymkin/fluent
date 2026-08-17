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
`.claude/skills/fluent-setup/SKILL.md:24` invokes it as the prescribed bootstrap
recipe, and `CHANGELOG.md:118` records that its *absence* was already shipped
once as a bug ("Added missing `ensure_data_dir.py` referenced by
`fluent-setup`"). Deleting it would have regressed that fix and broken
onboarding. The subagent executing the deletion caught it and refused.

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
