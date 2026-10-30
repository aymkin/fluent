---
name: fluent-reading
description: Reading practice in the DUO A2 exam format — short everyday texts, 2–3 multiple-choice questions each, at the exam's pace. Add b1 for the B1 round.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Reading Session

## Overview

A round of the DUO A2 Lezen exam, built the way the exam is built: short, structured everyday texts (a letter, a folder, an email, house rules), each followed by two or three multiple-choice questions about one fact in it. The learner reads the question first, then the text. A round is `computed.session_cap` questions on four texts (3 + 3 + 2 + 2). The exam has 25 questions in 65 minutes, so a round's time budget is 2.6 minutes a question.

With the argument `b1` (`/fluent-reading b1`) the round runs the B1 round at the end of this file instead.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-reading` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language, interests), `computed.session_cap`, `mastery-db.skills.reading`, and the `session_notes` of the latest three `session-log` entries whose `command_used` is `/fluent-reading`: the genres they used.

Read `.claude/references/exam-a2.md` §Lezen: the genres, the frame, the stem and the option counts the round copies.

```bash
date +%s
```

Keep the number as the round's start mark.

### 2. Opening

Greet the learner by name and give: the round's size (four texts, `session_cap` questions), its time budget (2.6 minutes a question), and the exam's rule: read the question first, then the text. Then start with the first text.

### 3. Write the round

Four texts, each in a different genre from §Texts, and none of the genres the last round used. A text carries its questions: 3, 3, 2 and 2.

Write each text and its questions by §Texts and §Questions. Done when every text has its frame, its questions in the order the text settles them, each with its options, its answer and the sentence that settles it — and each question clears both bars: its answer is a **paraphrase** of the text (no word-match), and every distractor is a **trap** drawn from the wrong part of the text.

### 4. One question at a time

A question is shown with its text. The first question of a text carries the frame and the text; the next questions of the same text carry the question only and say that the text stands above.

```markdown
## Tekst {T}/{texts}

{frame: one line in Dutch}

*Lees eerst de vraag. Lees daarna de tekst.*

**Vraag {N}/{round size}** — {stem: a short situation and the question}

A. {option}
B. {option}
C. {option}

---

{the text}
```

Wait for the letter. Done when the learner has answered.

### 5. Feedback per question

```markdown
{✅ or ❌} **{right letter}. {right option}**

**В тексте сказано:** "{the settling sentence}"

{why, in the learner's native language: where the text settles it, and what made the distractor tempting}

**Оценка: {X}/10**
```

Score 10 for the right letter and 0 for a wrong one, as the exam marks. Stage each wrong answer for the end-of-session update. Done when the learner has the sentence and the explanation. The same message goes on to the next question (step 4), so it ends on that question; after the round's last question, the summary (step 7) follows the feedback instead, with the words (step 6) between.

### 6. Words

After the last question, pick 3–5 words from the texts the learner is likely not to know:

```markdown
## 📚 Слова из текстов

| {target_language} | {native_language} | В тексте |
|-------|---------|-------------|
| {word} | {meaning} | "{sentence}" |

**Какие из них сохранить для повторения?** Напиши слова, **all** или **none**.
```

Stage each word the learner chose for `new_vocabulary[]`.

### 7. Session summary

```bash
date +%s
```

Minutes taken = (this number − the start mark) ÷ 60, rounded up.

```markdown
## 📊 Сессия по чтению завершена!

**Текстов:** {T} · **Вопросов:** {N} · **Верно:** {X} ({percent}%)
**Время:** {minutes} из {budget} мин (темп экзамена: 2,6 мин на вопрос)

### По видам вопросов
- Факт (когда, где, кто, сколько, что взять с собой): {x}/{n}
- Какое предложение подходит человеку: {x}/{n}
- Зачем написан текст: {x}/{n}

### По текстам
- {genre}: {x}/{n}

### Добавлено новых слов: {count}
{list}

### На следующий раз
- {suggestion based on the weakest kind}
```

`{genre}` is named in Russian («письмо жильцам», «буклет магазина», «правила дома»).

Close with the way to the exam's own material: DUO's practice exams for Lezen (`inburgeren.nl/examen-doen/oefenen.jsp`) hold 25 questions in 65 minutes; one taken under exam conditions shows what a tutor round cannot — and the learner can report the result here. When the round scored above 80%, say it is time for one of them.

### 8. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-reading"`, `skills_practiced: ["reading"]`
- `skill_scores.reading: {exercises: N questions, correct: count_right, time_minutes}`, with the minutes from step 7
- `errors[]` — one per question kind missed twice or more: category `comprehension`, or `vocabulary` when the miss came from a word the learner did not know (canon: `fluent-feedback-formatter` §"Use these category labels")
- `new_vocabulary[]` — words the learner chose to save
- `session_notes` — the genres used, which the next rounds rotate from
- `focus_next_session[]` — the weakest question kind

Save the transcript as `fluent-reading-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Include each full text with its questions and answers.

Done when `fluent-db-updater` reports the write and the transcript file exists.

### 9. Offer another round

With everything saved, ask whether the learner wants another round, as CLAUDE.md's session-cap rule asks. On a yes, the learner types `/fluent-reading` again: a new session with its own record.

## Texts

- **Genres** — from `.claude/references/exam-a2.md` §Lezen: a letter to residents, a shop or course folder, a letter or email from work, an email from a colleague, a letter from the neighbourhood association, a newspaper item, house rules, tips in a course guide. A round takes four different ones.
- **Frame** — one line in Dutch about a named person and the text they get or see (`Sabrina krijgt een brief van haar werk.`).
- **Text** — 60–140 words of A2 Dutch, laid out the way the genre is: a letter with greeting and closing, a folder with a list or a small table of days, prices or courses, house rules as numbered lines. Times, dates, prices and names appear in the text, each decidable from it (never inference) — but the fact a question asks for sits inside a sentence, often a subordinate clause, stated once and in words the question will not reuse. Topic from `learner-profile` interests when the genre allows it.
- **Level** — A2 words and sentences; one or two words above the level are guessable from the sentence.

## Questions

- **Stem** — a short situation about a named person, then one question about one fact: what to bring, when, whom to ask, how much, which offer fits, what to do. One decision (`fluent-review` §3).
- **Kinds** — mostly a fact in the text; one question in a round may ask which offer in a folder fits a person's wish, and at most one asks why the text was written.
- **Paraphrase** — the correct answer is never a phrase the learner can lift by matching words to the text. Reword it (`op de hoogte brengen` in the text → `informeren` in the option), make it a small computation (`€ 60` and "de helft" → `€ 30`; `07.00 uur` and "een half uur later" → `07.30`), or leave the fact in a subordinate clause the stem rephrases. Word-matching must fail; reading for meaning must land it.
- **Trap** — options are A, B and C, short, in the target language; about every second question takes a fourth, D. Every distractor is a trap: a value the text really contains, taken from the wrong part of it — the bus time `07.15` for a question about the shift start `07.30`, `bellen` where the text says to `mailen`. No filler option no one would pick. The right letter moves across the options over the round.
- **Order** — the questions of a text follow the order of the text.

## B1 round

With the argument `b1`: one text of 200–350 words (opinion pieces, longer narratives, structured guides) with subordinate clauses and at least one passive, so the grammar targets in `.claude/references/level-b1.md` appear in context; topic from `learner-profile.focus_areas` when possible. Stop after the text and ask the first question once the learner types "ready". Then five questions, one at a time, in this order, written in the target language: main idea (multiple choice), a detail (open answer), vocabulary in context (multiple choice), an inference the text implies and never states (answered in the target language), and one true/false statement. Feedback per question as in step 5, with the open answers checked against the text. Then the words (step 6), the summary with the five questions' breakdown, and the update (step 8) with `inference` also an allowed error category.
