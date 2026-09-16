---
name: fluent-learn
description: Adaptive mixed-skill practice session.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Main Adaptive Learning Session

## Overview

The flagship command. Interleaves skills, adapts difficulty per answer, and covers the whole evidence-based loop: active recall → immediate feedback → spaced repetition → tracking. Typically runs 15-20 min, mixing 2-3 patterns to force discrimination.

Write every message in the language the learner writes to you in. The blocks below say what each message must carry, not which words to use.

## Instructions

### 1. Load learner context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need all 6 DBs. If any missing, direct the learner to `/fluent-setup` and stop.

### 2. Analyze today's plan

- **Streak:** `learner-profile.current_streak_days`
- **Due reviews:** `computed.due_reviews_count`
- **Weak patterns:** `mistakes-db.error_patterns` where `mastery_level <= 2` (descending by frequency)
- **Recent performance:** `progress-db.weekly_summary`
- **Skills not practiced recently:** check `mastery-db.skills.{skill}.last_practiced`

### 3. Greet

Open with the learner's name, their streak, reviews due, today's focus area (weakest skill or top weak pattern), and level with progress. Then offer the menu:

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

Plan a 20-min session:

1. **Warm-up (3 min)** — easy vocabulary recognition on already-strong words. Builds confidence.
2. **Targeted drill 1 (7 min)** — top weak pattern. 3-4 isolated exercises + 1 application.
3. **Targeted drill 2 (5 min)** — second weak pattern. Same structure.
4. **Integration (5 min)** — short writing or speaking task that forces both patterns together.

Run one exercise at a time with immediate feedback via `fluent-feedback-formatter`.

Use `fluent-session-analyzer` to choose which patterns to target.

### 6. Adaptive difficulty

Steps 1-3 of the mix are **one decision** each: the learner's answer differs from your prompt in exactly the place the exercise tests, and nowhere else. Difficulty moves by widening what surrounds that decision, never by stacking a second one — only step 4, integration, deliberately asks for two.

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

Then save the transcript beside the databases, in their `results/` directory:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

That prints the data directory; write to `<it>/results/fluent-learn-session-{NNN}.md`. The directory is resolved at runtime (`FLUENT_DATA_DIR`, a project `data/`, or the `~/.claude` fallback), so ask rather than assume. Format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md` — it is the canonical definition, and `fluent-session-analyzer` parses exactly the markers it lists. For a routed reading session, include the full text + Q&A.

## Critical Rules

- **Always load all 6 DBs at start.** Missing context → generic, demotivating content.
- **One exercise at a time.**
- **Interleave.** Don't drill one pattern for 20 min — mix 2-3 patterns to force discrimination.
- **Use the helper skills** (`fluent-fsrs-reference`, `fluent-feedback-formatter`, `fluent-db-updater`, `fluent-session-analyzer`) — don't reimplement.
- **Use the learner's name + target-language greetings** throughout.
- **Celebrate progress.** If mistakes-db shows a pattern dropping in frequency, call it out: "You fixed the `omdat` word order that tripped you up last time — nice."
