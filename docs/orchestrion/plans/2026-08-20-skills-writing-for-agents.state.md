# Session state — `writing-for-agents` sweep

Updated 2026-08-21 after execution finished. Supersedes the pre-execution version of
this file. The spec, the plan and this file are enough to resume.

## Status: executed, reviewed, not integrated

- **Branch:** `chore/writing-for-agents-sweep`, cut from `main`. **Not pushed.**
- **All 18 tasks implemented and individually reviewed.** Every task `Approved`; no
  Critical and no Important finding in any of the eighteen task reviews.
- **Whole-branch review:** `Verdict: With fixes`. Its one Important finding (I1) is
  fixed and re-reviewed `Approved`; the regression that fix introduced is fixed too.
- **Next action:** `orchestrion:finish` — integration. Held for the human, because
  finishing pushes and the standing rule forbids a push without asking in the turn.

Diff against the base: 23 files, +324/-190, on top of `99aae2d`.

## What the sweep delivered, measured on the final tree

| Spec §6 criterion | Measured |
|---|---|
| Test suite passes | 4 files, 24 tests, OK — and still OK with `FLUENT_DATA_DIR` and `CLAUDE_PROJECT_DIR` both exported to junk paths |
| One difficulty band | `60-70` extinct repo-wide; `50-70%` in all three live homes |
| One home for the quality formula | `floor(score` only in `fluent-fsrs-reference` |
| One home for the category canon | one definer (`fluent-feedback-formatter` §"Use these category labels"), three pointers, zero re-lists |
| No stale `file.md:NN` citation | none outside `docs/orchestrion`, which is a historical record |
| F1-F14 | all fourteen closed; F12 delivered exactly per the §2 assumption |

Enforcement is live, not documented-only: an off-canon `errors[].category` exits `1`,
names the offending index and the eleven accepted labels, and writes **no** database.

## The two defects that mattered, and where they came from

1. **I1 — the routed `/fluent-learn` path double-executed the session end.** Menu items
   1-5 read the target skill's `SKILL.md` and follow it, then return to `fluent-learn`
   step 8 — but each target's own "Update all databases" step also calls `update-db.py`,
   with its own `command_used`. Nothing said to skip it. The literal reading writes two
   payloads and two session files for one session, and because
   `update-db.py` calls `backup_all(f"pre-update-{session['session_id']}")`, the second
   invocation overwrites the pre-session snapshot with post-first-update state —
   destroying the rollback point `fluent-db-updater` promises. Fixed router-side in
   `fluent-learn/SKILL.md` §4, naming the superseded step by name (the five targets
   number it §6-§9). **Provenance:** the plan's t13 never asked for the suppression
   clause, and the controller's batch-1b ⚠️ resolution asserted the targets' final steps
   did *not* carry their own update call — which was false and checkable in one command.
   The whole-branch reviewer caught both.
2. **The fix's own regression.** «Include the full text + Q&A for later analysis» existed
   at exactly one place in the tree, inside the step the fix now skips, so a routed
   reading session silently lost the source passage. Closed by one conditional clause in
   `fluent-learn` step 8.

## Follow-ups deliberately not done — all triaged, none blocking

- `.claude/skills/fluent-setup/PROFILE-UPDATES.md` says «restart setup from Step 2», a
  numeric cross-file reference that contradicts this sweep's own cite-by-name rule. It
  resolves today. Name the section instead.
- `LEARNING_SYSTEM.md` §"Spaced Repetition" now sends non-Claude CLIs one hop to a skill
  file for the score→quality scale, and nothing tells them skill files are plain readable
  markdown. `AGENTS.md` already establishes the practice; half a sentence would close it.
- `fluent-session-analyzer` §2 still restates the feedback shape and the severity gloss,
  duplicating `fluent-feedback-formatter`. Collapsing it needs a task owning both files,
  because the pointer would have to carry the parse contract for the whole `❌` line.
- The `_subprocess_env()` helper is duplicated across the two test files. Deliberate:
  `CONTRIBUTING.md` makes each test a standalone script, so a shared module would break
  the house convention for five lines.

## Things a fresh context would otherwise get wrong

- **Never export `FLUENT_DATA_DIR` before running the suite.** The harness scrubs it now,
  but three implementers lost time to it before that landed. `fluent_paths.data_dir()`
  resolves `FLUENT_DATA_DIR` → `$CLAUDE_PROJECT_DIR/data` (when it holds
  `learner-profile.json`) → `./data` → `~/.claude/fluent-data`, so either env var
  outranks the leg the fixtures use.
- `rg` skips dot-directories, so `.claude/` needs `--hidden` when searching from the root.
- **Two gates in this plan were wrong, both mine, both written after the review rounds
  closed.** A directory-scoped grep for `fluent-{skill}-session` indicts
  `fluent-session-analyzer`, where the placeholder is correct; and a line-oriented grep
  for the 24-word §3.3 criterion returns 2 of 6 because four files hard-wrap it at three
  different points. The form that holds is `rg -Ul` with `\s+` at every word boundary.
  Both are recorded in `tasks/lessons.md` with the working commands.
- `results/README.md` and `AGENTS.md` were already correct and stayed untouched (spec §5).
  `fluent-session-analyzer` and `results/README.md` keep the literal `{skill}` pattern on
  purpose — they document the filename shape across all skills.
