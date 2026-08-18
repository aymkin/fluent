---
name: fluent-reading
description: Run an interactive reading comprehension session with a short target-language text followed by main-idea, detail, vocabulary-in-context, inference, and true/false questions. Triggered only when the learner types /fluent-reading. Presents the text, waits for the learner to read, then asks questions one at a time with immediate feedback, and optionally adds new vocabulary to the spaced-repetition queue.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Reading Comprehension Session

## Overview

Present one text (100-500 words depending on level), ask 4-6 comprehension questions, extract vocabulary. Builds passive-to-active bridge: learners decode target-language writing, then answer questions that force recall.

## When to Use

Skip this skill below A1 mastery 3 — shorter flashcard drills (`/fluent-vocab`) are more appropriate for very early learners.

## Instructions

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (level, target language, interests), `mastery-db.skills.reading`.

### 2. Opening

```markdown
# 👀 {target_language} Reading Practice

Hallo {name}!

Today we're practicing **reading comprehension**. I'll show you a short {target_language} text, then ask you questions about it.

**Focus:** main ideas, details, vocabulary in context
**Level:** {CEFR}
**Duration:** 15-20 min

**Tips:**
- Read the whole text first
- Don't translate every word — get the gist
- Use context clues for unknown words
- Read the questions before rereading the text

**Ready? Let's read!** 📖
```

### 3. Pick text type + length

A2 types (100-200 words): personal email, short news, advertisement, instructions, simple story, blog post, social media post, info leaflet.

B1 (200-350 words): opinion pieces, longer narratives, structured guides.

B2+ (350-500): editorials, technical explanations, interviews.

Match the topic to `learner-profile.focus_areas` when possible.

### 4. Present the text

```markdown
## 📄 Reading Text {N}

**Topic:** {topic}
**Type:** {text_type}
**Length:** ~{word_count} words

---

{target-language text — clean formatting, no inline translation}

---

Take your time. When you're done, type **"ready"**.
```

### 5. Question sequence (one at a time)

One block per question, headings in the target language:

```markdown
## {"Question" in target_language} {N}: {type label in target_language}

{the question}

{a) b) c) options — multiple-choice types only}

**Type your answer:**
```

Rotate across these types, in this order:

1. **Main idea** — multiple choice.
2. **Details** — a specific fact from the text, open answer.
3. **Vocabulary in context** — `In the text it says "{word}". What does this mean?`, multiple choice.
4. **Inference** — something the text implies but never states; answer in the target language.
5. **True / false** — one statement to judge.

### 6. Feedback per question

```markdown
{✅ or ❌}

**Answer:** {correct_answer}

**Explanation:** {why — reference the text}

{If incorrect: **The text says:** "{relevant_quote}"}

**Score: {X}/10**

---
```

### 7. Vocabulary review

After the questions:

```markdown
## 📚 New Vocabulary from the Text

| {target_language} | {native_language} | Example from text |
|-------|---------|-------------------|
| {word 1} | {meaning} | "{sentence}" |
| {word 2} | {meaning} | "{sentence}" |

**Save these for future review?** (They'll enter spaced repetition.)

Type "yes" to add, "no" to skip.
```

If yes, stage each word for `new_vocabulary[]` in the end-of-session DB update.

### 8. Session summary

```markdown
## 📊 Reading Session Complete!

**Text:** {title/topic}
**Length:** {words} words
**Questions:** {N}
**Accuracy:** {percent}%

### Comprehension Breakdown
- Main idea: {✅ or ❌}
- Details: {score}
- Vocabulary: {score}
- Inference: {score}

### New Words Added: {count}
{list}

### For Next Time
- {suggestion based on which question type was weakest}

**{target-language well done}!** 📖✨
```

### 9. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-reading"`, `skills_practiced: ["reading"]`
- `skill_scores.reading: {exercises: N, correct: count_right, time_minutes}`
- `errors[]` — per question-type weakness (category `comprehension`, `vocabulary`, `inference`)
- `new_vocabulary[]` — words the learner chose to save
- `focus_next_session[]`

Save to `/results/fluent-reading-session-{NNN}.md` — include the full text + Q&A for later analysis.

## Critical Rules

- **Wait for "ready"** before asking the first question. Rushing the reading step defeats the purpose.
- **One question at a time.** Multiple at once invites skimming.
- **Ask questions in the target language** (at least from A2 up). Reading-comprehension checks should happen in the same language as the text.
- **Quote the text** in explanations so the learner can trace the answer back to the source.
- **Vocabulary opt-in.** Don't force-add every unknown word — ask the learner which they want to keep.
- **Don't reuse a text** in consecutive sessions; vary topic and text type.
- **Never auto-invoke.** Gated; must fire only on explicit `/fluent-reading`.
