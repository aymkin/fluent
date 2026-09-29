---
name: fluent-writing
description: Writing practice — one scenario, full-text correction by severity and category.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Writing Practice Session

## Overview

One scenario per session, corrected as a full text. Mastery picks the scenario, so the task stays challenging and within reach.

## Instructions

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (level, target language, focus areas), `mistakes-db` (weak writing patterns), `mastery-db` (writing sub-skills).

### 2. Pick scenario type

From `mastery-db.skills`:

- Formal email (if `writing_formal_email` mastery < 4)
- Informal email (if `writing_informal_email` < 4)
- Form filling (if `writing_forms` < 4)
- Newsletter / personal text (if overall writing < 3)
- Mixed scenarios (if all ≥ 4)

Scenarios match the learner's CEFR level: A2 uses everyday situations. When `target_level` is B1, take the genre from `.claude/references/level-b1.md` §"Genres" (opinion, complaint, inquiry) and put one grammar target the learner has not yet mastered into **Include**, named by its function ("give a reason for your complaint"), never by its form.

### 3. Present the task

```markdown
## ✍️ Writing Exercise

**Scenario:** {clear description in native language}

**Task:** Write a {type} in {target_language}.

**Requirements:**
- Length: {X-Y} words
- Include: {must-include elements}
- Register: {formal / informal}
- Level: {CEFR}

{Optional: example structure for harder tasks}

**Write your {text_type} below:**
```

### 4. Wait for the full text

Hold all feedback until the learner sends the finished text.

### 5. Systematic error analysis

Check every sentence against the category canon in `fluent-feedback-formatter`
§"Use these category labels" — the single home of the list, `structure` included.

The Title-Case headings the learner reads in the feedback (**Grammar**,
**Formal/informal**, **Missing elements**, **Structure**, …) are display copy, not
payload values. `errors[].category` takes the lowercase canon label
(`formal_informal`, `missing`, `structure`, …); `update-db.py` rejects anything
else and writes no database at all, so a display heading copied into the payload
fails the whole update.

Tag each finding with a severity: 🔴 critical, 🟡 moderate, 🟢 minor. Severity is
mandatory: `mistakes-db` stores it on the pattern, and `fluent-session-analyzer`
weighs it when planning. Weigh spelling light at A2, heavier at B2+. At B1, grade
as `.claude/references/level-b1.md` §"What B1 asks for" sets out: a slip that
leaves the meaning clear is 🟡 or 🟢, and the Communication score leads. Stage
each finding for the end-of-session payload.

### 6. Detailed feedback

Diverges slightly from the standard `fluent-feedback-formatter` template because writing answers are multi-sentence. Use this variant:

```markdown
## Feedback

### ✅ What You Did Well
- {strength 1}
- {strength 2}

### ❌ Areas to Improve

**Critical:** 🔴
- {issue}: "{wrong}" → **"{correct}"** — {why}

**Moderate:** 🟡
- {issue}: {explanation}

**Minor:** 🟢
- {spelling / punctuation}

### 📝 Corrected Version

```
{fully corrected text}
```

**Score: {X}/10**

**Breakdown:**
- Grammar: {Y}/10
- Vocabulary: {Z}/10
- Structure: {W}/10
- Communication: {V}/10

---
```

### 7. Optional rewrite

If score < 7, offer:

```markdown
**Want to try again?** Rewriting with the corrections locks in the patterns.

Type "rewrite" to try again, or "next" to continue.
```

### 8. Session summary

```markdown
## 📊 Writing Session Summary

**Text Type:** {type}
**Score:** {X}/10
**Key Takeaways:**
- {learning 1}
- {learning 2}
- {learning 3}

**Next Time:**
- Focus on: {weak pattern}
- Review: {relevant flashcards}

{target-language "well done"}! ✍️
```

### 9. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-writing"`, `skills_practiced: ["writing"]`
- `skill_scores.writing: {exercises: 1, correct: 1_if_score_≥_7_else_0, time_minutes}`
- `errors[]` — one per distinct pattern found (dedupe; the script bumps frequency)
- `focus_next_session[]` — top 2 patterns to drill

Save the transcript as `fluent-writing-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`.

## Critical Rules

- **One scenario per session**; depth over breadth.
