---
name: fluent-writing
description: Writing practice in the DUO A2 exam format — four tasks (email, neighbourhood paper, form, note) in 40 minutes, scored on DUO's rubric. Add b1 for the B1 task.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Writing Session

## Overview

A session is the DUO A2 Schrijven exam: four tasks, one at a time, 40 minutes of writing in all. The real exam is written with a pen on paper; here the learner types each task in full sentences, and each answer is scored on DUO's rubric before the next task starts. With the argument `b1` (`/fluent-writing b1`) the session runs the B1 task at the end of this file instead.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-writing` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language), `mistakes-db` (weak writing patterns), and the `session_notes` of the latest three `session-log` entries whose `command_used` is `/fluent-writing`: the points each task type earned.

Read `.claude/references/exam-a2.md` §Schrijven and §Rubrics: the four task types, their wording and the rubric the scoring follows.

### 2. Choose the four tasks

Every session has an **email**, a **neighbourhood-paper text**, a **form** and a fourth task: a second email or a **note** to a colleague from pictures, whichever of the two earned fewer points in the notes (a second email when there are no notes). The two emails of a session go to different readers (a teacher or boss with *u*, a colleague or fellow student with *je*), and the order of the four is shuffled each session, as it varies in the exam.

Write each task new, in the form of §Tasks, on an everyday situation the last sessions' notes leave out. A weak writing pattern from `mistakes-db` goes in as a bullet or a field that asks for it, named by its function, never by its form.

Open the session: greet the learner by name, name the four tasks and the 40 minutes of writing in all, and say the tasks begin on **go** after the first. Done when the four tasks are written and their order is set.

### 3. Present one task

```bash
date +%s
```

Keep the number as the task's start mark; the tasks after the first begin when the learner types **go** (step 7), so the mark measures writing, not reading feedback. The first task follows the opening in the same message.

Send the task as §Tasks lays it out, ending with the instruction to write in full sentences. The turn's final message ends on the task.

### 4. Wait for the full text

Hold all feedback until the learner sends the finished text.

```bash
date +%s
```

Minutes for this task = (this number − the task's start mark) ÷ 60, rounded up.

### 5. Systematic error analysis

Work in the order the rubric ranks the aspects:

1. **Adequaatheid** — is every bullet, question or field answered, and is the text understandable? A missing bullet costs more than any grammar slip. Tag a missing bullet or field `missing`, 🔴 when the whole bullet is absent.
2. **Woordgebruik** — a word that fits the task. An answer made almost only of the task's own words earns 0 here.
3. **Grammatica** — by the number of errors across the whole text: many, quite a few, hardly any. Not scored on a form.
4. **Spelling** — scored on every task type, up to 2 points; a typo that does not repeat is 🟢, a pattern the learner meets again is 🟡.
5. **Coherentie** — *en, maar, want, omdat* and pronouns that join the sentences. Not scored on a form.

Check every sentence against the category canon in `fluent-feedback-formatter` §"Use these category labels" — the single home of the list, `structure` included.

The Title-Case headings the learner reads in the feedback are display copy, not payload values. `errors[].category` takes the lowercase canon label (`formal_informal`, `missing`, `structure`, …); `update-db.py` rejects anything else and writes no database at all, so a display heading copied into the payload fails the whole update.

Tag each finding with a severity: 🔴 critical, 🟡 moderate, 🟢 minor. Severity is mandatory: `mistakes-db` stores it on the pattern, and `fluent-session-analyzer` weighs it when planning. Stage each finding for the end-of-session payload.

### 6. Feedback

Diverges slightly from the standard `fluent-feedback-formatter` template because a writing answer is a whole text. Use this variant:

```markdown
## Feedback — taak {T}/4: {task type}

### ✅ What worked
- {strength}

### ❌ To fix

**Critical:** 🔴
- {issue}: "{wrong}" → **"{correct}"** — {why}

**Moderate:** 🟡
- {issue}: {explanation}

**Minor:** 🟢
- {spelling / punctuation}

### 📝 Corrected version

{fully corrected text}

### Rubric (DUO, my estimate)

| Aspect | Points |
|---|---|
| Adequaatheid | {a}/3 |
| Grammatica | {g}/2 |
| Spelling | {s}/2 |
| Woordgebruik | {w}/2 |
| Coherentie | {c}/1 |
| **Total** | **{P}/{max}** |

**Score: {X}/10** — {P} ÷ {max} × 10, rounded
**Time:** {minutes} min
```

The maximum is 10 on an email, a neighbourhood-paper text and a note, with every row; 7 on a form, with Adequaatheid, Spelling and Woordgebruik only. An Adequaatheid of 0 zeroes every other row. The assessors apply DUO's own rubric; this is the tutor's estimate of it.

### 7. Next task

If the Score is below 7, offer a second try at this task: "Type **rewrite** to write it again with the corrections, or **go** for the next task." The rewrite is practice and the Score stays the first text's. Every feedback message ends on that cue ("Type **go** for task {T+1}."); after **go**, return to step 3 with the next task. After the fourth task, the summary (step 8) follows the feedback instead.

### 8. Session summary

```markdown
## 📊 Writing Session Complete!

| Task | Type | Points | Score |
|---|---|---|---|
| 1 | {type} | {P}/{max} | {X}/10 |

**Time:** {total minutes} of 40 min for the four tasks
**Weakest aspect:** {aspect}
**Next time:**
- Focus on: {weak pattern}
- Review: {relevant flashcards}
```

Close with the way to the exam's own material: DUO's three practice exams for Schrijven (`inburgeren.nl/examen-doen/oefenen.jsp`, PDF) are written by hand in 40 minutes; the learner can type what they wrote and send it here to be scored on the same rubric.

### 9. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-writing"`, `skills_practiced: ["writing"]`
- `skill_scores.writing: {exercises: 4, correct: count of tasks with Adequaatheid of 2 or 3 and at least 70% of the maximum, time_minutes}`, with the summed task minutes
- `errors[]` — one per distinct pattern found (dedupe; the script bumps frequency, and a pattern that already has a card takes a missed review on it)
- `session_notes` — each task's type, subject and points ("email 7/10, wijkkrant 8/10, formulier 5/7, note 6/10"), which the next sessions rotate from
- `focus_next_session[]` — top 2 patterns to drill

Save the transcript as `fluent-writing-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. A task is one question: its prompt, the learner's text, the corrected version, the rubric table and the `**Score:**`; `**Accuracy:**` is the share of tasks counted correct.

Done when `fluent-db-updater` reports the write and the transcript file exists.

## Tasks

The form of each task is the exam's (`.claude/references/exam-a2.md` §Schrijven). The task text is in Dutch at A2, addressing the learner as *u*; the learner invents what the task leaves open (`Bedenk zelf waarom.`).

**Email** — a situation of two or three lines, three or four bullets that say what to write, and `Schrijf in hele zinnen.`

```markdown
**{title}**

{situation}

- Schrijf {bullet}.
- Schrijf {bullet}. Bedenk het zelf.
- Schrijf {bullet}.

Schrijf de e-mail. Schrijf in hele zinnen.

Van: kandidaat@mail.nl
Aan: {recipient}@mail.nl
Onderwerp: {subject}

{Beste mevrouw/meneer … , or Hallo …,}

[write here]

{closing}
```

**Neighbourhood paper** — a situation line that says everyone may write for the weekly paper, a topic, `Schrijf minimaal drie zinnen op. Denk aan:` with three guiding questions, and `Schrijf in hele zinnen.`

**Form** — a form named in Dutch (`Aanmeldformulier`, `Aangifteformulier`, `Meldingsformulier`), with personal fields (name, address, postcode, town, phone, email), one choice and one or two free-text fields, and `Sommige gegevens moet u zelf bedenken.` The learner answers field by field as `Field: answer`. A form that takes its content from pictures lists them in the learner's language, one line each (`Plaatje 1: …`), without the Dutch words the learner has to find.

**Note** — a situation (a colleague comes in later), pictures listed as for the form, and `Schrijf drie dingen op.` in the exam's form: a short note with salutation and thanks.

## B1 task

With the argument `b1`: one scenario for the session. Take the genre from `.claude/references/level-b1.md` §"Genres" (opinion, complaint, inquiry, a short formal email) and put one grammar target the learner has not yet mastered into **Include**, named by its function ("give a reason for your complaint"), never by its form. Present it as **Scenario** (in the learner's language), **Task**, **Requirements** (length in words, **Include**, register, level) and wait for the full text. Analyse as step 5, but with B1's grading stance from `.claude/references/level-b1.md` §"What B1 asks for": a slip that leaves the meaning clear is 🟡 or 🟢, and Communication leads. Give the feedback of step 6 with **Score: {X}/10** and a breakdown of Grammar, Vocabulary, Structure and Communication, each out of 10. Update: `skill_scores.writing: {exercises: 1, correct: 1 if the Score is 7 or more else 0, time_minutes}`.
