---
name: fluent-session-analyzer
description: Parse Fluent `/results/*.md` session files to extract error patterns, strengths, accuracy trends, and focus areas for the next session. Use when the tutor needs to analyze the learner's recent performance — planning the next lesson, recommending focus areas, or answering "what should I practice next?".
---

# Session Analyzer

## Overview

Every practice session writes a markdown report to `/results/fluent-{skill}-session-{NNN}.md` (e.g. `fluent-writing-session-012.md`). This skill describes how to read those files to plan adaptive follow-up practice. Use it when the tutor needs narrative context the JSON databases don't capture — the exact sentence the learner wrote, the scenario, the feedback they received.

## When to Use

Load this skill whenever the tutor:

- Plans today's focus before `/fluent-learn`, `/fluent-writing`, etc.
- Answers the learner's question "what's my weakest area" or "what should I work on".
- Generates the next session plan.

Skip this skill when aggregated JSON numbers are enough — prefer `read-db.py` for counts, trends, and mastery levels. Use this skill only when the textual context matters.

## Instructions

### 1. Find recent session files

```
/results/fluent-{skill}-session-{NNN}.md
```

`NNN` is the global session counter, so files group by skill and sort chronologically. Files written before v0.2.0 lack the `fluent-` prefix (`{skill}-session-{NNN}.md`) — glob for both, and don't rename the old ones. Read the most recent 3-5 files of the relevant skill; don't re-read the entire history.

### 2. Extract error patterns

Scan for `❌` markers. Each correction has:

- The wrong form ("Your answer")
- The correct form
- A category (grammar, formal_informal, vocabulary, prepositions, articles, spelling, missing)
- A severity (🔴 critical, 🟡 moderate, 🟢 minor)

Count frequency per pattern across recent files:

- **1 occurrence** — possibly a typo, ignore
- **2-3** — emerging pattern, worth drilling
- **4+** — critical weakness, highest priority

### 3. Extract strengths

Scan for `✅` markers and scores ≥ 7/10. Note consistent correct usage — these are reinforcement targets, not drill targets.

### 4. Track trajectory

Across sessions, track:

- Overall accuracy per session
- Critical vs moderate vs minor error counts
- Writing speed (words per minute, if tracked)

### 5. Plan the next session

Based on the analysis:

1. **Top 3 critical weaknesses** (highest frequency + severity) → 50% of session time.
2. **Top 2 moderate patterns** → 30% of session time.
3. **One full integration scenario** → 20% of session time.

Plan template:

```markdown
## Session {N} Plan ({X} min)

**Top 3 Weaknesses:**
1. {pattern} — {count} occurrences, severity {emoji}
2. ...

**Strengths to Reinforce:**
- {skill}

**Drill Sequence:**
1. Warm-up ({x} min) — quick wins on known patterns
2. Targeted drill 1 ({y} min) — focus on weakness #1
3. Targeted drill 2 ({y} min) — focus on weakness #2
4. Mixed integration ({z} min) — combine all patterns
5. Full scenario ({w} min) — exam-style task
```

### 6. Tune difficulty

Use recent session accuracy to tune today's difficulty:

- **<50%** → simplify, add scaffolding, smaller chunks
- **50-70%** → correct zone, keep going
- **>70%** → raise difficulty, introduce new patterns

## Critical Rules

- **Read `/results/` markdown for context.** Use `read-db.py` for numerical summaries — don't reimplement counts by re-parsing markdown when the DB already has them.
- **Cap the look-back window.** 3-5 recent sessions for the relevant skill. Older data is already baked into `mistakes-db.json` mastery levels.
- **Never alter `/results/` files.** They are immutable records. Planning only.
