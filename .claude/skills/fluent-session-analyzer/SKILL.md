---
name: fluent-session-analyzer
description: Parse Fluent `/results/*.md` session files to extract error patterns, strengths, accuracy trends, and focus areas for the next session. Use when the tutor needs to analyze the learner's recent performance — planning the next lesson, recommending focus areas, or answering "what should I practice next?".
---

# Session Analyzer

## Overview

Every practice session writes a markdown report to `/results/fluent-{skill}-session-{NNN}.md`. Read those files to plan follow-up practice when the textual context matters: the exact sentence the learner wrote, the scenario, the feedback they received.

## When to Use

Load this skill when the tutor plans today's focus, generates the next session plan, or answers "what's my weakest area" or "what should I work on".

Skip it when aggregated numbers are enough; `read-db.py` gives counts, trends and mastery levels.

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
- A category — one of the labels in `fluent-feedback-formatter` §"Use these category labels"
- A severity (🔴 critical, 🟡 moderate, 🟢 minor)

Recognise every label in that canon, not only the ones a writing session tends to produce: a reading session tags `comprehension` and `inference`, a long answer tags `structure`, and a label this scan skips is a weakness the next session plan never sees.

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

### 5. Plan the next session

Based on the analysis:

1. **Top 3 critical weaknesses** (highest frequency + severity) → 50% of session time.
2. **Top 2 moderate patterns** → 30% of session time.
3. **One full integration scenario** → 20% of session time.

When `target_level` is B1, unmet targets from `.claude/references/level-b1.md` fill the drill slots the weaknesses leave open.

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

Tune today's difficulty from recent session accuracy against the 50-70% target zone, using the bands in `fluent-learn` §"Adaptive difficulty".

## Critical Rules

- **`/results/` markdown supplies context**; `read-db.py` supplies the counts, so they are never re-derived from markdown.
- **Cap the look-back window.** 3-5 recent sessions for the relevant skill. Older data is already baked into `mistakes-db.json` mastery levels.
- **`/results/` files are immutable records**; this skill plans and edits nothing.
