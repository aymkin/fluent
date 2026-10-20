---
name: fluent-grammar
description: Grammar practice — the theory of one rule, then five exercises on it, scored.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Grammar Session

## Overview

A session is one rule and one series of five exercises on it. A rule the learner meets for the first time opens with its theory; a rule they have practised before opens with the exercises, because the series tests what they remember, and its theory comes only after a weak series. The time spent on theory counts as grammar time.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-grammar` — a project's own rules for this learner, such as which rule comes next — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, native and target language, level), the `grammar` patterns of `mistakes-db` with `mastery_level <= 2`, and the `grammar_rule` items of `spaced-repetition`. When `target_level` is B1, also the grammar targets of `.claude/references/level-b1.md`.

If a database is missing, direct the learner to `/fluent-setup` and stop.

### 2. Choose the rule

Take the rule the project's rules name. Without one, take the weakest grammar pattern, then the first B1 target that has no pattern yet.

Open the session: greet the learner by name and name the rule. Done when one rule is named and you know how many times the learner has practised it (its `repetitions`; none on record is zero).

### 3. Theory — a rule practised zero times

```bash
date +%s
```

Teach the rule in the learner's native language: what it says, two examples in the target language, and one contrast with the form it is confused with. End the message on "go?" and wait.

```bash
date +%s
```

Theory minutes = (this number − the first) ÷ 60, rounded up. Done when the learner has answered "go".

A practised rule skips this step and goes to step 4.

### 4. Five exercises

Present them one at a time. The rule is each exercise's only difficulty; keep the rest of the sentence at the learner's level, and vary the form: complete the sentence, find the error, transform, translate a short line, build from words.

```bash
date +%s
```

Mark the time when each exercise is sent and when its answer arrives. Exercise minutes = the sum of those gaps in seconds ÷ 60, rounded up once for the whole stretch.

Give feedback after each answer with the `fluent-feedback-formatter` skill's template, before the next exercise. Done when five answers are graded.

### 5. Score the series

Series score = correct answers out of five × 2. `quality` follows from it — see the `fluent-fsrs-reference` skill.

A practised rule that scores below 7 gets its theory now, as in step 3, and its minutes join the theory minutes. Done when the score and the quality are set.

The five answers count toward `computed.session_cap`; theory is not a graded answer and does not.

### 6. Session summary

```markdown
## 📐 Grammar Session Complete!

**Rule:** {rule}
**Series:** {correct}/5 → {score}/10
**Time:** {theory minutes} min theory + {exercise minutes} min exercises

**Went well:** {what the learner applied correctly}
**Next time:** {the one error to watch, or the next rule when the series passed}

{target-language "well done"}! 🌟
```

### 7. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-grammar"`, `skills_practiced: ["grammar"]`
- `skill_scores.grammar: {exercises: 5, correct, time_minutes}`, with `time_minutes` = theory minutes + exercise minutes
- `review_results[]` — one entry for the series: the rule's `item_id`, its `quality` and `score`; five answers are one review
- `errors[]` — one per distinct pattern found, category `grammar`
- `focus_next_session[]` — the rule when the series scored below 7, else the next rule

Save the transcript as `fluent-grammar-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. A question is one exercise.

Done when `fluent-db-updater` reports the write and the transcript file exists.
