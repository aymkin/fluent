---
name: fluent-learn
description: Adaptive mixed-skill practice session.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Main Adaptive Learning Session

## Overview

The flagship command. Interleaves skills, adapts difficulty per answer, and covers the whole evidence-based loop: active recall → immediate feedback → spaced repetition → tracking. Typically runs 15-20 min, mixing 2-3 patterns to force discrimination.

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

```markdown
# {greeting in target language}, {name}! 👋

**Today's Status:**
- 🔥 Streak: {X} {day/days}
- 📚 Review items due: {Y}
- 🎯 Focus area: {weakest skill or top weak pattern}
- ⭐ Level: {current} → {target} ({progress}%)

**What would you like to practice today?**

1. 📝 Writing (emails, letters, forms)
2. 🗣️ Speaking (typed conversation)
3. 📖 Vocabulary (flashcard drills)
4. 👀 Reading (comprehension)
5. 🔄 Spaced Review (today's due items)
6. 🎲 Surprise me! (adaptive mix)

**Type a number or skill name:**
```

### 4. Route

Menu items 1-5 target, in order: `fluent-writing`, `fluent-speaking`, `fluent-vocab`, `fluent-reading`, `fluent-review`.

- 1-5 → all five carry `disable-model-invocation: true`, so you cannot invoke them as skills. Read `.claude/skills/<target>/SKILL.md` and follow it in the same session — skipping its **Update all databases** step, which step 8 below supersedes — then finish with step 8. Keep `command_used: "/fluent-learn"` so the session stays one record.
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

After every 3-4 exercises, check rolling accuracy:

- **<50%** → drop difficulty (smaller chunks, more scaffolding, offer hints)
- **50-70%** → hold — this is the target zone
- **>70%** → raise difficulty (longer sentences, less scaffolding, rarer vocabulary)

Set the starting point from the skill's `mastery_level`: **0-1 → easy**, **2-3 → medium**,
**4-5 → hard**. Then let the rolling accuracy above move it up or down.

### 7. Per-answer feedback

Use `fluent-feedback-formatter` template. Score 0-10 + severity tag. Stage the result for the end-of-session payload.

Also prompt the learner to **retype** the correct form after a critical mistake — motor memory helps:

```markdown
Now type the correct version yourself: "{correct_sentence}"
```

### 8. Session end

```markdown
## 🎉 Session Complete!

**Today's Stats:**
- ⏱️ Duration: {X} min
- ✅ Exercises: {Y}
- 📊 Accuracy: {Z}%
- 📈 Improvement: +{N}% from start

**Breakthroughs:** ✨
- {what mastered or improved}

**Next Time Focus:**
- {what to practice next}

**Streak:** 🔥 {X} {day/days}! {motivational line}

{goodbye in target language}! 👏
```

Then use the `fluent-db-updater` skill:

- `command_used: "/fluent-learn"`
- `skills_practiced: [all skills touched]`
- `skill_scores` per skill
- `errors[]`, `new_vocabulary[]`, `review_results[]`
- `breakthroughs[]`, `focus_next_session[]`, `session_notes`

Save the session file to `/results/fluent-learn-session-{NNN}.md` — structure per `results/README.md`. Every `❌` line carries its category and its severity emoji; without them `fluent-session-analyzer` cannot parse the session.

## Critical Rules

- **Always load all 6 DBs at start.** Missing context → generic, demotivating content.
- **One exercise at a time.**
- **Interleave.** Don't drill one pattern for 20 min — mix 2-3 patterns to force discrimination.
- **Use the helper skills** (`fluent-fsrs-reference`, `fluent-feedback-formatter`, `fluent-db-updater`, `fluent-session-analyzer`) — don't reimplement.
- **Use the learner's name + target-language greetings** throughout.
- **Celebrate progress.** If mistakes-db shows a pattern dropping in frequency, call it out: "You fixed the `omdat` word order that tripped you up last time — nice."
