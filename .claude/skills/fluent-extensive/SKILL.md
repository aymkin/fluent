---
name: fluent-extensive
description: Extensive reading — a three-episode story built from the learner's Anki words in progress, then a five-word recognition check.
allowed-tools: Read, Write, Bash, mcp__Anki_MCP_Server__findNotes, mcp__Anki_MCP_Server__notesInfo
disable-model-invocation: true
---

# Extensive Reading Session

## Overview

Extensive reading: a lot of easy text, read for flow. The story is built from words the learner is learning in Anki right now, so each one comes back several times, in different forms and combinations. The goal is recognition in new contexts. `/fluent-reading` owns comprehension and the exam format; this session owns volume.

Anki owns these words' schedule. The session reads Anki and leaves both Anki and the Fluent review queue as they are.

## Instructions

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, level, native language), `computed.session_cap`, `computed.next_session_id`, and the `session_notes` of the latest `session-log` entry whose `command_used` is `/fluent-extensive` — it names the previous target words.

### 2. Collect the words

Read the onderweg and vast stages as `.claude/references/anki.md` describes them.

Choose **10 target words** from onderweg: words that fit one story topic, leaving out the previous session's targets. The rest of the story uses vast words and basic vocabulary at the learner's level.

When the Anki tools are missing or a call fails, say so, and take the targets from `spaced-repetition.json` items with `type == "vocabulary"` instead. With fewer than 5 of those, tell the learner the session needs Anki and stop.

Done when 10 targets (or the fallback set) each have a translation.

### 3. Write the story

One story in three episodes, 150-200 words each, at `current_level`.

- Each target appears 2-3 times across the story, in at least 2 different forms and in at least 2 episodes: present and past, perfectum, a split separable verb, singular and plural, an inflected adjective, a new collocation.
- Each target sits in a fresh context: write sentences of your own, unlike the note's `Example`.
- Targets look like every other word in the text, so the learner meets them the way a reader does.

Before showing an episode, proofread it: finite verb last in every bijzin, inversion after a fronted element, de/het, participle forms.

Done when all three episodes are written and each target has its 2-3 uses.

### 4. Read, one episode at a time

```markdown
# 📚 Экстенсивное чтение

Hallo {name}! История из трёх частей, собранная из слов, которые ты сейчас учишь. Читай ради потока: значение подскажет контекст.

## Deel {N}/3: {episode title}

{episode text — clean formatting, no translation, no highlighting}

---

Напиши **"verder"** для следующей части или перечисли незнакомые слова.
```

Send one episode, then wait. Record the words the learner names as unrecognised. The learner may stop after any episode; then go to step 5 with the episodes read.

Done when three episodes are read or the learner stopped.

### 5. Forms table

```markdown
## 🔁 Твои слова в этой истории

| Слово | {native_language} | Формы в истории |
|------|-------------------|--------------------|
| {target} | {Translation} | {each form as it appeared} |
```

Mark each unrecognised word with 👀.

### 6. Recognition check

Five targets, one at a time. Each sits in a new sentence, one that appears nowhere in the story:

```markdown
## Woord {N}/5

"{new sentence with the target}"

Что значит **{form of the target}** здесь?

a) {meaning}
b) {meaning}
c) {meaning}

**Напиши ответ:**
```

Options are in the learner's native language. Grade each answer with `fluent-feedback-formatter` before sending the next one.

Done when five answers are graded.

### 7. Session summary

```markdown
## 📊 Экстенсивное чтение завершено!

**История:** {title} — прочитано {episodes read}/3 частей, ~{words} слов
**Целевые слова:** {count}
**Проверка узнавания:** {correct}/5
**Точность:** {percent}%

### Пока не узнаются 👀
{list, or "нет"}

**{target-language well done}!** 📖✨
```

### 8. Save

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-extensive"`, `skills_practiced: ["reading", "vocabulary"]`
- `skill_scores.vocabulary: {exercises: 5, correct: count_right, time_minutes}` — the check measures word recognition; `reading` stays the comprehension score of `/fluent-reading`
- `session_notes` — the 10 targets, the unrecognised words, the missed check words
- `focus_next_session[]` — the unrecognised words
- `errors[]`, `new_vocabulary[]` and `review_results[]` stay empty, so the Fluent review queue is unchanged

Save the transcript as `fluent-extensive-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Include the story, the forms table, and the five check questions as the Q&A.
