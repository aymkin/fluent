# Session Results Directory

This directory holds a markdown transcript of every practice session. It is empty by
design until you finish your first session.

It is also the **canonical definition of the session-file format** — the
`fluent-session-analyzer` skill parses these files to plan your next session, so the
structure below has to stay consistent.

## 📛 File naming

```
<data dir>/results/fluent-{skill}-session-{NNN}.md
```

For example: `fluent-writing-session-012.md`.

`<data dir>` is resolved at runtime — `FLUENT_DATA_DIR`, a project `data/`, or the
`~/.claude/fluent-data` fallback — so it is not a fixed path. Ask for it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

`NNN` is the **global** session counter (not per-skill) — it matches `session_id` in
`session-log.json`.

> Files created before v0.2.0 may use the older `{skill}-session-{NNN}.md` naming (no
> `fluent-` prefix). The analyzer reads both — do not rename existing files.

## 📝 Required structure

```markdown
# {Skill} Practice Session {NNN}

**Date:** YYYY-MM-DD
**Duration:** {X} minutes
**Skill:** {writing/speaking/vocab/reading/review/learn}
**Command:** {/fluent-writing, /fluent-speaking, etc.}

---

## Session Summary
- Questions: {Y}
- Correct: {Z}
- Accuracy: {percent}%

---

## Questions & Answers

### Question 1: {Type}

**Prompt:** {what the learner was asked}
**Your answer:** "{what they wrote}"
**Correct answer:** "{correct version}"

**Analysis:**
- ❌ 🟡 ontbreeken → ontbreekt (grammar)
- ✅ dat-clause built correctly

**Score:** {X}/10

---

### Question 2: {Type}

[repeat]

---

## Error Pattern Summary

| Pattern | Category | Severity | Count This Session |
|---------|----------|----------|--------------------|
| {pattern} | {category} | 🔴/🟡/🟢 | {N} |

## Strengths

| Skill | Evidence |
|-------|----------|
| {skill} | {what the learner did well} |

## Progress Tracking

**Improvements:**
- {what improved compared to last session}

**Focus Areas:**
- {what needs work}

**Next Session:**
- {recommended focus}
```

## 🔍 Key parsing markers

The `fluent-session-analyzer` skill relies on these exact markers being present:

- `❌` — error line. Carries **both** a severity emoji and a category, every
  time: the analyzer counts by category and ranks by severity, so a line
  missing either is a mistake the next session never plans around.
- `✅` — strength line
- `**Score:** {X}/10` — per-question score
- `**Accuracy:** {percent}%` — session accuracy
- `| 🔴` / `| 🟡` / `| 🟢` — severity in tables
- `**Focus Areas:**` — cue for next-session planning

Do not rename these headings or reorder sections. Changes break the analyzer.

## 🔗 Interaction with the databases

Session files are **markdown narrative**. The JSON databases (`mistakes-db.json`,
`mastery-db.json`, …) hold aggregated counts and FSRS scheduling state. Both must be
updated — the markdown records the story, the JSON records the numbers.

Call `.claude/hooks/update-db.py` once at session end with a full payload (see
`.claude/references/db-updater-payload.example.json`). The script handles the JSON side;
the practice skill handles the markdown side. The `fluent-db-updater` skill documents
the payload schema.

## ✅ Before you save

Re-read the file you are about to write and confirm, literally:

1. Every `❌` line has a severity emoji (🔴/🟡/🟢) **and** a category label.
2. Every category label is one from `fluent-feedback-formatter`
   §"Use these category labels" — the analyzer recognises no others.
3. `**Score:** {X}/10` is present per question, and `**Accuracy:** {percent}%`
   once for the session.

A transcript that fails any of these is written but unreadable: the next
session plans around the errors it can parse, and silently around nothing else.
