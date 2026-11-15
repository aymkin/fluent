# TODO

## Improvements

- [x] **Feedback header: the mark contradicts the text after a prompted retry.**
  The `fluent-feedback-formatter` template opens with `{✅ or ❌} {one-line encouragement or gentle correction}`.
  When the first attempt missed and the retry after a prompt was right, the tutor wrote
  «❌ Хорошо, что со второй попытки ты сам нашёл правильный порядок!»: a red cross in front of praise,
  which confuses the learner (seen 2026-11-10, `/fluent-review` session-106, Q6).
  Fix in `.claude/skills/fluent-feedback-formatter/SKILL.md` §1–2: the header line must agree with its mark —
  either a correction line after ❌ (praise for the self-correction goes on a ✅ line below), or a dedicated
  header for a "missed, then self-corrected" answer. Check that `fluent-session-analyzer` and
  `results/README.md` markers still parse.

- [x] **Drop «Правильный вариант» when the answer is already fully correct.**
  After a 10/10 answer the block repeats the learner's own sentence word for word, which the learner finds
  redundant (2026-11-10, session-106, Q8 `Ik heb twee katten.`). This reverses a stated rule:
  `fluent-feedback-formatter` Critical Rules — "Always include the «Правильный вариант», even after a perfect
  answer; echoing the target form reinforces motor memory." Decide whether to drop it only when the answer
  matches the target exactly (keep it when it differs in any way, e.g. a typo or a missing period), update
  §1 and the Critical Rules, and check `fluent-vocab` (release 0.12.0 "переписать правильный вариант")
  and the session-file format, which keeps `**Correct answer:**` per question.

- [ ] **The last answer of a round gets its feedback before the summary.**
  `/fluent-review` session-107, Q10: the learner answered `Gisteren ochtend heb ik koffie gekookt.` and the tutor
  started the save first: the learner watched «Running a command» with no feedback on the screen, and the
  feedback was left for the closing message after the save. In the earlier rounds of the day the last answer's
  feedback also came only at the very end, after the tool calls.
  Fix in `.claude/skills/fluent-review/SKILL.md` §6–7 (and the round-end rule in `fluent-feedback-formatter`
  Critical Rules): the turn that receives the final answer opens with that answer's standard feedback as text,
  before any tool call; the save and the summary follow. Check the other round-based skills (`fluent-vocab`, `fluent-grammar`, `fluent-reading`,
  `fluent-listening`, `fluent-learn`) for the same gap.
