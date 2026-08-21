---
name: fluent-writing
description: Writing practice with systematic error analysis.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Writing Practice Session

## Overview

Full-text writing practice with systematic correction. One scenario per session, detailed feedback broken down by severity and category, DB update at end. Mastery-driven scenario selection keeps the task at the right level — challenging, not frustrating.

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

Scenarios must match the learner's CEFR level — A2 uses everyday situations, B1+ adds opinion / complaint / inquiry.

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

Don't correct mid-composition. Let the learner finish.

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
mandatory — it feeds `mistakes-db` and drives spaced-repetition priority. Weigh
spelling light at A2, heavier at B2+. Stage each finding for the end-of-session
payload.

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

Save the session file to `/results/fluent-writing-session-{NNN}.md` — structure
per `results/README.md`. Every `❌` line carries its category and its severity
emoji; without them `fluent-session-analyzer` cannot parse the session.

## Critical Rules

- **One scenario per session.** Don't chain multiple writing tasks — depth over breadth.
