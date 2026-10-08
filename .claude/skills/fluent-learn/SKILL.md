---
name: fluent-learn
description: Main adaptive session across all four skills — warm-up, two weak-pattern drills, one integration task.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Main Adaptive Learning Session

## Overview

The flagship command. Interleaves skills and adapts difficulty per answer: active recall → immediate feedback → spaced repetition → tracking. Holds at most the session cap (`computed.session_cap`) exercises.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-learn` — a project's own rules for this learner — load it now. Where its rules and the steps below disagree, its rules win.

### 1. Load learner context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need all 6 DBs. If any missing, direct the learner to `/fluent-setup` and stop.

### 2. Analyze today's plan

- **Streak:** `learner-profile.current_streak_days`
- **Due reviews:** `computed.due_reviews_count`
- **Weak patterns:** `mistakes-db.error_patterns` where `mastery_level <= 2` (descending by frequency). When `target_level` is B1, add the grammar targets from `.claude/references/level-b1.md` that have no pattern yet; they enter the pool as candidates for the drills in step 5.
- **Recent performance:** `progress-db.weekly_summary`
- **Skills not practiced recently:** check `mastery-db.skills.{skill}.last_practiced`

### 3. Greet

Open with the learner's name, their streak, today's review round (due items up to the session cap), today's focus area (weakest skill or top weak pattern), and level with progress. Then offer the menu:

```markdown
1. 📝 Writing (emails, letters, forms)
2. 🗣️ Speaking (typed conversation)
3. 📖 Vocabulary (flashcard drills)
4. 👀 Reading (comprehension)
5. 🔄 Spaced Review (today's due items)
6. 🎲 Surprise me! (adaptive mix)
```

### 4. Route

Menu items 1-5 target, in order: `fluent-writing`, `fluent-speaking`, `fluent-vocab`, `fluent-reading`, `fluent-review`.

- 1-5 → all five carry `disable-model-invocation: true`, so you cannot invoke them as skills. Read `.claude/skills/<target>/SKILL.md` and follow it in this session. Persist the whole thing once, through step 8 below, with `command_used: "/fluent-learn"` — one session, one record, written at the end.
- 6 (adaptive mix) → use this skill's own exercise sequencer (below).

### 5. Adaptive mix (option 6)

Plan the session cap as four blocks:

1. **Warm-up** — 1 exercise: easy vocabulary recognition on an already-strong word. Builds confidence.
2. **Targeted drill 1** — top weak pattern: isolated exercises, then 1 application.
3. **Targeted drill 2** — second weak pattern. Same structure.
4. **Integration** — 1 exercise: a short writing or speaking task that forces both patterns together.

The two drills share the exercises left between warm-up and integration evenly.

Choose the patterns with `fluent-session-analyzer`. Give each exercise its feedback via `fluent-feedback-formatter` before the next one.

### 6. Adaptive difficulty

Steps 1-3 of the mix are **one decision** each, as defined in `fluent-review` §3. Difficulty moves by widening what surrounds that decision, never by stacking a second one — only step 4, integration, deliberately asks for two.

Set the starting point from the skill's `mastery_level`: **0-1 → easy**, **2-3 → medium**, **4-5 → hard**. Then check rolling accuracy every 3-4 exercises:

- **<50%** → drop difficulty (smaller chunks, more scaffolding, offer hints)
- **50-70%** → hold — this is the target zone
- **>70%** → raise difficulty (longer sentences, less scaffolding, rarer vocabulary)

### 7. Per-answer feedback

Use `fluent-feedback-formatter` template. Score 0-10 + severity tag. Stage the result for the end-of-session payload.

Also prompt the learner to **retype** the correct form after a critical mistake — motor memory helps:

```markdown
Now type the correct version yourself: "{correct_sentence}"
```

### 8. Session end

Close with: duration, exercises done, accuracy and how it moved from the session's start, what broke through, what to focus on next time, and the streak.

Then use the `fluent-db-updater` skill:

- `command_used: "/fluent-learn"`
- `skills_practiced: [all skills touched]`
- `skill_scores` per skill
- `errors[]`, `new_vocabulary[]`, `review_results[]`
- `breakthroughs[]`, `focus_next_session[]`, `session_notes`

Save the transcript as `fluent-learn-session-{NNN}.md` in the `results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. For a routed reading session, include the full text + Q&A.

## Critical Rules

- **One exercise at a time.**
- **Interleave.** Mix 2-3 patterns across the session to force discrimination.
- **Use the learner's name + target-language greetings** throughout.
- **Celebrate progress.** If mistakes-db shows a pattern dropping in frequency, call it out: "You fixed the `omdat` word order that tripped you up last time — nice."
