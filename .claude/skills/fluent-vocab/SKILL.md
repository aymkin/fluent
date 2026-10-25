---
name: fluent-vocab
description: Vocabulary — today's Anki words as chunks: a true sentence about yourself, then other persons and tenses.
allowed-tools: Read, Write, Bash, mcp__Anki_MCP_Server__findNotes, mcp__Anki_MCP_Server__notesInfo
disable-model-invocation: true
---

# Vocabulary Session: Anki Words as Chunks

## Overview

The words the learner met in Anki today, each practised inside its chunk: first one true sentence about the learner, then — for a verb — the same sentence in other persons and tenses, one cell at a time. After the save, every verb's whole paradigm is shown as a table. Method and Dutch grading rules: `.claude/references/chunks-nl.md`; reading Anki: `.claude/references/anki.md`.

Anki owns these words' schedule: the session reads Anki and leaves it as it is.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-vocab` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py" | jq '.databases as $d
| ($d.spaced_repetition.items | map({(.id): .last_reviewed}) | add) as $seen
| {
    computed,
    learner: ($d.learner_profile.learner | {name, current_level}),
    rounds: [$d.session_log.sessions[] | select((.notes // "") | startswith("Слова из Anki:")) | {session_id, date, notes}],
    open_patterns: [$d.mistakes_db.error_patterns | to_entries[]
      | select(.value.category == "grammar" and .value.mastery_level <= 2)
      | {id: .key, frequency: .value.frequency, last_reviewed: $seen[.key]}]
  }'
```

- `rounds` — earlier rounds of this session type, whichever command saved them. The latest names the previous round's chunks and misses; all of them name the words already drilled; their `Факты:` are the learner's own sentences.
- `open_patterns` — the grammar patterns a cell can aim at, with the day their card was last reviewed.

If a database is missing, direct the learner to `/fluent-setup` and stop.

### 2. Choose the words and plan the round

Search Anki stage by stage, as `.claude/references/anki.md` describes: new today, then reviewed today, then new this week, leaving out the words an earlier round drilled. When both "today" stages are empty and cards still wait in Anki, tell the learner how many wait and ask: Anki first, or this week's words now.

Take verbs first, then other words; skip proper names, numbers and particles; put words alike in meaning into different rounds. Keep taking words while the opener (when there is an earlier round), one personal task per word and two cells per verb still fit in `computed.session_cap`. Answers left over become a verb's third cell. The words that do not fit lead the next round.

Give each word its chunk (`.claude/references/chunks-nl.md` §Chunk) and plan the round privately — the learner sees one task at a time:

- the opener, when there is an earlier round;
- one personal task per word (§Self-reference);
- the cells (§Paradigm by word class, §Cell), each with its frame, its time marker or person, and its one valid answer plus the variants §Acceptance allows; a word's next task comes after a task on another word.

Done when every cell has exactly one valid answer and every personal task has its chunk. Before sending a task, check that no earlier task of the round has shown its answer.

### 3. Opener — the previous round's chunks

```markdown
## Задание 1/{session_cap} · чанки прошлого раунда

Напиши по-нидерландски чанки прошлого раунда:
1. {Russian meaning}
2. {Russian meaning}

**Напиши ответ:**
```

One graded answer: score = chunks right ÷ chunks asked × 10. The feedback shows every missed chunk whole. Skip this step in a first round.

### 4. One task at a time

```markdown
## Задание {N}/{session_cap} · {word} · {о себе | ты | Вы | {person} | вчера | завтра | …}

{the task}

**Напиши ответ:**
```

- **Personal task:** `Чанк: {chunk} — {Russian meaning}.` on one line, then «Напиши правду о себе, одно предложение до 6 слов: {что / где / куда question}?»
- **Cell:** a Russian line with the situation, then the Dutch frame built from the learner's corrected personal sentence (§Cell).

After each answer give feedback with the `fluent-feedback-formatter` skill before the next task. Once in the round, ask the «Почему…?» of §Why — ungraded. Done when `computed.session_cap` answers are graded.

### 5. Save

Save before the final message, with the `fluent-db-updater` skill:

- `command_used: "/fluent-vocab"` (`"/fluent-learn"` when the round was started from its menu), `skills_practiced: ["vocabulary", "grammar"]`
- `skill_scores.vocabulary` — the opener and the personal tasks; `skill_scores.grammar` — the cells; each `{exercises, correct, time_minutes}`
- `errors[]` — form errors (category `grammar`, `articles` or `spelling`), with the `pattern_id` `mistakes-db` already has for the same mistake. A miss on the Anki word itself — its meaning, its partner word — goes to the transcript and the notes only: Anki owns the word.
- `review_results[]` — one entry for each cell aimed at an `error_pattern` card whose `last_reviewed` is not today, right or wrong, with the cell's `quality`
- `new_vocabulary[]` — empty
- `session_notes` — `Слова из Anki: {words}. Чанки: {chunks}. Промахи: {missed chunks and forms}. Факты: {the learner's corrected personal sentences}.`
- `focus_next_session[]` — the forms missed

Save the transcript as `fluent-vocab-session-{NNN}.md` in the `results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. After the Q&A, a `## Paradigms` section holds the tables of step 6, with no ✅, ❌ or `**Score:**` inside it.

Done when `fluent-db-updater` reports the write and the transcript exists.

### 6. Final message

One message, after the save: the paradigm of each verb, then the summary and the offer of the next round. Proofread every sentence of the tables first: verb forms, inversion, de/het.

```markdown
## 🔁 Прокрутка: {word}

| Лицо | {chunk} |
|------|---------|
| ik | {the learner's corrected sentence} |
| jij | {question} / {statement} |
| u | {…} |
| hij/zij | {…} |
| wij | {…} |
| jullie | {…} |
| zij | {…} |

| Время | |
|-------|---|
| perfectum | {…} |
| imperfectum | {…} {👀 outside the A2 set} |
| будущее | {gaan + infinitive} |

## 📖 Слова из Anki — итоги

**Слова:** {words} · **Ответов:** {N} · **Точность:** {X}%
**Получилось:** {what the learner did well}
**В следующий раз:** {the forms to watch}

Ещё раунд? Ждут слова: {count}.
```

A word that is not a verb gets the lines its class shows in `.claude/references/chunks-nl.md` §Paradigm by word class, under its own `## 🔁 Прокрутка` heading.

## Without Anki

When the Anki tools are missing or a call fails, say so and take the `vocabulary` items due today from `.databases.spaced_repetition.items[]` as the round's words, with the same steps. They are Fluent's own cards, so each gets a `review_results[]` entry with its `quality`.
