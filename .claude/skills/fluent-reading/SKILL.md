---
name: fluent-reading
description: Reading comprehension with a graded question sequence.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Reading Comprehension Session

## Overview

One text, 4-6 comprehension questions asked one at a time, then vocabulary. The learner decodes target-language writing, then answers questions that force recall.

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

Stop after the text. Ask the first question only once the learner types `"ready"`; the reading step needs its full time.

### 5. Question sequence

Send one question, then wait for the answer and give its feedback (step 6) before the next; a batch invites skimming. Write the question and its headings in the target language:

```markdown
## {"Question" in target_language} {N}: {type label in target_language}

{the question}

{a) b) c) options — multiple-choice types only}

**Type your answer:**
```

Question types, in this order:

1. **Main idea** — multiple choice.
2. **Details** — a specific fact from the text, open answer.
3. **Vocabulary in context** — `In the text it says "{word}". What does this mean?`, multiple choice.
4. **Inference** — something the text implies but never states; answer in the target language.
5. **True / false** — one statement to judge.

### 6. Feedback per question

```markdown
{✅ or ❌}

**Answer:** {correct_answer}

**Explanation:** {why}

**The text says:** "{relevant_quote}"

**Score: {X}/10**

---
```

### 7. Vocabulary review

After the last question:

```markdown
## 📚 New Vocabulary from the Text

| {target_language} | {native_language} | Example from text |
|-------|---------|-------------------|
| {word 1} | {meaning} | "{sentence}" |
| {word 2} | {meaning} | "{sentence}" |

**Which of these do you want to save for review?** (They'll enter spaced repetition.)

Reply with the words, "all", or "none".
```

Stage each word the learner chose for `new_vocabulary[]` in the end-of-session payload.

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
- True / false: {score}
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
- `errors[]` — per question-type weakness, category `comprehension`, `vocabulary` or `inference` from the canon in `fluent-feedback-formatter` §"Use these category labels"
- `new_vocabulary[]` — words the learner chose to save
- `focus_next_session[]`

Save the transcript as `fluent-reading-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Include the full text + Q&A.

## Critical Rules

- **Target-language questions** (from A2 up): the check runs in the language of the text.
- **Quote the text** in every explanation, so the learner can trace the answer to its source.
- **Vocabulary opt-in.** Only words the learner picks get saved.
- **Fresh text** each session: change topic and text type from the previous one.
