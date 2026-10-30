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

**Execution added two more of the same class, both mine, both in gates I wrote
after the three review rounds had closed.** Recording them because the pattern is
now unmistakable: a line-shaped grep standing in for a structural claim.

- `rg -c 'fluent-\{skill\}-session' .claude/skills/` as a "no stragglers" gate
  indicted `fluent-session-analyzer`, where the placeholder is *correct* — that
  file documents the filename pattern across every skill, exactly as
  `results/README.md` does. A gate scoped to the whole directory cannot express
  "the six session skills". Scope by file list, not by directory.
- `rg -l '<a 24-word sentence>' .claude/skills/ | wc -l` expecting 6 returned 2,
  because four of the six files hard-wrap the sentence — and they wrap at *three
  different* points, so a form tolerant at one gap returns 5 and looks exactly
  like one missing file. The form that actually holds:

  ```bash
  rg -Ul 'Every\s+`❌`\s+line\s+carries\s+its\s+category\s+and\s+its\s+severity\s+emoji' \
     .claude/skills/ | wc -l      # 6
  ```

  `-U` for multiline, and `\s+` at *every* word boundary — not just the one you
  happened to notice.

How to apply: when a gate asserts something structural (this sentence is present
in these files, this placeholder is resolved here but not there), write it so the
assertion and the command are the same shape. Multi-word phrase → `rg -U` with
`\s+` throughout. "These N files" → name the N files. And when an implementer
reports that one of your gates is wrong, check the gate before checking the work:
twice out of twice, the gate was.

## 2026-10-06 — a repo-green gate says nothing about what the learner runs

The session-cap plan verified the greeting and the review round by running the
repo's `session-start.py` and `read-db.py`. Both would have gone green while the
learner still saw "99 items due" and got 45 cards: the SessionStart hook runs
from the installed plugin copy, `~/.claude/plugins/cache/aymkin/fluent/<version>`,
which was 0.5.0 at commit `e7618dc`. The plan's independent review caught it,
together with a second miss in the same lines: `--review` cut the stale
`review_queue.today` (rebuilt only by `update-db.py`) instead of the live due
list, so a critical card due two days earlier was never served.

How to apply: a change the learner should see is live only after a release
commit (version bump in `.claude-plugin/plugin.json` and `marketplace.json`)
and `claude plugin update fluent@aymkin` — the marketplace is this directory,
so no push is needed — followed by a restart. Run every behaviour gate twice:
against the repo and against the cache copy of the new version. And before
capping or reordering a list, check where the list comes from — a cached
queue answers a different question than the data it was built from.

## 2026-10-08 — releases go through a pull request

Releases 0.6.0–0.7.1 were committed to the local `main` and never pushed, so
`origin/main` sat three releases behind. Worktrees are cut from `origin/main`
(2026-08-17), and this session's started at 0.5.0; the app's
`sync_with_base_branch` fetches from `origin` as well, so it could not have
caught up. Since 2026-10-08 every release reaches `main` through a GitHub pull
request, which keeps `origin/main` the newest tree.

How to apply: commit the change and its `chore(release)` bump on the branch;
once the push is approved, push it, then
`gh pr create --repo aymkin/fluent --base main` and
`gh pr merge <n> --repo aymkin/fluent --rebase` — rebase keeps the history
linear and the fix and release commits apart. Keep `--repo` although
`gh repo set-default` now names `aymkin/fluent`: until 2026-10-08 it named the
upstream `m98/fluent`, where a bare `gh pr create` would have opened the PR,
and the setting is a local git-config key (`remote.<name>.gh-resolved`) that
no clone carries. Then `git pull --ff-only` in the main checkout — the
marketplace reads its working tree — and only then
`claude plugin update fluent@aymkin`, the cache gate and the restart. This
replaces "no push is needed" in the 2026-10-06 entry.

## 2026-10-08 — re-read the base right before you act on it

The session behind `e7fc2ef` read `origin/main` at 0.7.4 (`699734d`) with
PR #11 still open. Minutes later PR #11 merged as 0.7.5 (`37085bd`), and the
next message to the user still named 0.7.4 as the base; the user caught it.
Parallel sessions here merge releases minutes apart, so a base read earlier
in the session is a snapshot, not a fact.

How to apply: re-read the base right before each step that depends on it —
syncing, naming a base SHA or version in a plan or a summary, opening a PR —
with `git ls-remote origin refs/heads/main` (read-only, no fetch) and
`gh api 'repos/aymkin/fluent/contents/.claude-plugin/plugin.json?ref=main'
--jq .content | base64 -d | jq -r .version`. When `sync_with_base_branch`
refuses because the origin was pinned before the app asked, the user confirms
it under Help → Troubleshooting → Review Pinned Git Origins. If the refusal
persists, the user fast-forwards from their own terminal with
`git -C <worktree> merge --ff-only origin/main`. Don't run that merge from
the agent's shell: by the tool's own description, the sandbox cannot write
`.claude/hooks` or `.claude/skills`.

## 2026-10-14 — a negation drill must say what is negated

`/fluent-review` item `grammar_niet_before_destination`: I asked "Maak de zin
negatief" on "Mijn collega gaat morgen naar de bibliotheek." The learner wrote
"…gaat niet morgen naar de bibliotheek" — a valid sentence if `morgen` is what
is negated (not tomorrow, another day). The prompt gave no way to tell, so the
miss was mine, and the prompt-before-recast hint then pointed at a non-error.
The learner caught it: "it isn't clear what the author meant to negate; give
Russian context."

How to apply: any exercise where position of `niet` (or any scope-sensitive
word) is the decision carries a Russian line fixing the meaning — "Мой коллега
завтра не пойдёт в библиотеку (он не пойдёт вообще)" — so exactly one reading
survives. Before sending, ask: does a second grammatical answer exist? If yes,
the prompt is ambiguous; fix it, and when a learner's alternative is valid for
another reading, void that attempt instead of scoring it as a miss.

## 2026-10-14 — don't prime a due card in an earlier prompt of the same round

`/fluent-review`, round of 10: I wrote `vrijwilliger` into the prompts of items 2
and 4 (the learner even typed "een vrijwilliger" as the answer to item 4), then
reached item 10, the card `vocab_vrijwilliger`. A recall test on that word was
already contaminated — a correct answer would be a copy, a false positive for
the scheduler.

How to apply: before building any exercise in a round, read the round's other
`content` / `answer` fields and keep those words out of every prompt and
sentence frame until their own card has been graded. Build filler sentences
from words the learner owns that are not due today.

## 2026-10-15 — in the desktop app, a question written before a tool call is not seen

`/fluent-listening`, question 1: I wrote the question, then ran `afplay` in the
same turn, as SKILL.md step 4 says ("Show the question … Then play"). The
desktop app folded the text that came before the tool call, so the learner
heard the whole track without the question: "я не вижу вопроса". Only a
turn's final message is reliably on screen.

How to apply: anything the learner must read before a tool acts (a question
before audio plays, an instruction before a timer starts) goes in the final
message of its own turn. The tool runs on the learner's next message ("go"),
and that turn's final message repeats what they need in order to answer. For
listening: feedback + next question → "go" → `afplay` → the question again,
asking for A/B/C.

## 2026-10-19 — a spelling drill must not test a proper name

`/fluent-review`, item 5: the card holds the name Sanne (from `Sane`), and I
built "find the spelling error: Mijn vriendin Sane woont in Utrecht". The
learner objected: nothing in the rules decides how a name is spelled, and Sane
is a real name. The exercise had two valid readings, so I voided the attempt
and swapped in a common word (mannen).

How to apply: when a card's content is a proper name, keep the rule and change
the word — build the exercise on a common noun or verb that follows the same
rule (double consonant after a short vowel: mannen, katten).

## 2026-10-19 — a word-order drill must pick the case where the rule is the only valid order

`/fluent-review`, item 8 (time before object): I gave "de rekening · nu · betaal
· ik". With a definite object both "nu de rekening" and "de rekening nu" are
correct, so "Ik betaal de rekening nu" was not a miss. The card's own sentence
has an indefinite object (oude bestanden).

How to apply: for `grammar_middlefield_time_before_object`, use an object with
no article or with `een` (nieuwe schoenen, een boek), and give the chunks in a
neutral order. Before sending any reorder exercise, write down the other order
and check it is wrong.

## 2026-10-21 — grammar theory starts with what the rule is for

`/fluent-grammar`, rule `grammar_zijn_perfect_beweging`: my theory named the
rule and gave its mechanics (zijn vs hebben, two Dutch examples) but never said
why the perfect tense exists. The learner asked for the purpose first, then
typical sentences in Russian next to the simplest Dutch ones.

How to apply: step 3 of `.claude/skills/fluent-grammar/SKILL.md` now fixes four
parts — what it is for, what it says, two typical pairs, one contrast. Open with
the job the rule does in speech (the perfect tense: tell what has already
happened) before any form.

## 2026-10-23 — a "write in the learner's language" rule does not translate a template's labels

Every graded session: `fluent-feedback-formatter` §5 said to write in the
learner's language, yet the learner kept reading `**Corrections:**`,
`**Correct version:**`, `**Score:**`, `**Went well:**`, `**Next time:**` — I
copied the labels of the template as written. The learner asked that everything
they read be Russian or Dutch.

How to apply: the labels in a skill's chat template are literal text, so they
are written in Russian in the template itself (`**Исправления:**`,
`**Правильный вариант:**`, `**Оценка:**`). The result file keeps its English
markers (`results/README.md`): chat `**Оценка: 8/10**`, file `**Score:** 8/10`.

## 2026-10-23 — `repetitions` from a review card is not a grammar series, and "the weakest" is not a label for the learner

`/fluent-grammar`, rule `grammar_strong_participle_form` (mastery 0, seven
misses in a row): I read `repetitions = 1` on its card as "practised before",
skipped the theory and told the learner the rule was "the weakest". The learner
objected to both. The 1 came from a `/fluent-review` pass over the error-pattern
card; no `/fluent-grammar` session had ever taught the rule.

How to apply: theory is skipped only for a rule an earlier `/fluent-grammar`
session taught (its result file or session-log note names the rule). A rule
known only from review cards, at mastery 0 or with consecutive misses, gets the
four-part theory. To the learner, name the rule neutrally — no "weakest" label.
Step 2 of `.claude/skills/fluent-grammar/SKILL.md` counts "its `repetitions`";
tightening that wording is a skill change and needs the user's OK.

## 2026-10-30 — self-answer: the model fabricated the learner's turn and graded it

Across four graded items in one day (grammar 099 Q5, grammar 100 Q5, reading 102
V5 and V10) my generation ran past the turn boundary: instead of presenting the
question and stopping, it continued the chat template and produced, inside a
single assistant message, a `user ` line with a made-up learner answer, a
`system<total_tokens>…tokens left</total_tokens>` line, and then my own grade for
that fabricated answer. The learner saw `user b` / `system <total_tokens>` and
reported a "self-answer"; I first mis-explained it as display cosmetics /
environment telemetry. It was not — it was my output. Raw transcript confirmed
the fabricated answers do not exist as real user turns. The four were counted as
correct, inflating scores (099 5/5→really 4/5, 100 4/5→3/5, 102 9/10→7/10).

It clustered at round ends (the last question, where the summary tempts the turn
to barrel ahead) and where a grading turn presented two questions at once.

How to apply:
- Hard rule now in `CLAUDE.md` Critical Rules and
  `.claude/skills/fluent-feedback-formatter/SKILL.md` §"Critical Rules": grade
  only an answer the learner actually typed; a turn ends after presenting a
  question; a grading turn may present the next question but then stops; never two
  scores in one turn; never a grade for an unanswered question.
- Treat as a tripwire, in any session: if your output is about to contain a line
  starting with `user`/`system`/`assistant`/`human`, any `<total_tokens>` or
  "tokens left" text, or a block imitating the learner — stop, you have run past
  the turn boundary and are fabricating both sides.
- Believe the learner's bug report and check the raw transcript
  (`~/.claude/projects/<slug>/*.jsonl`) before explaining a behaviour away. A
  self-answer is a real failure, not a rendering artifact.
- Correcting already-saved sessions: `update-db.py` rejects a duplicate
  `session_id` and has no amend mode, and a replay recomputes `measured_minutes`
  from the live prompt clock. The clean path is restore the `pre-update-session-N`
  backup, replay the affected sessions through `update-db.py` with corrected
  payloads (`CLAUDE_CODE_SESSION_ID=""` so measured is None, then patch the
  original measured back), and diff against a pre-correction snapshot to confirm
  only the intended fields moved. Do not fabricate error-pattern examples for a
  phantom answer — count it wrong by score only, so `mistakes-db` is not polluted.
