---
name: fluent-speaking
description: Speaking practice in the DUO A2 exam format — two blocks of four questions (a spoken question, then pictures), answered in writing, scored on DUO's rubric. Add b1 for the B1 conversation.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Speaking Session

## Overview

The DUO A2 Spreken exam is 16 spoken answers in four blocks of four, in 35 minutes, into a microphone. A session takes **two blocks, eight answers**, typed in full sentences, one at a time. What a typed answer can show is scored on DUO's rubric: Adequaatheid, Grammatica, Woordgebruik and Coherentie, 8 of the exam's 12 points. **Vloeiendheid and Uitspraak need the voice and stay unscored**; the summary says so. With the argument `b1` (`/fluent-speaking b1`) the session runs the B1 conversation at the end of this file instead.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-speaking` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language), `computed.session_cap`, and the `session_notes` of the latest three `session-log` entries whose `command_used` is `/fluent-speaking`: the blocks they ran and the points each earned.

Read `.claude/references/exam-a2.md` §Spreken and §Rubrics: the four blocks, their wording and the rubric the scoring follows.

```bash
date +%s
```

Keep the number as the session's start mark.

### 2. Choose the two blocks

The blocks are 1 video, 2 one picture, 3 two pictures, 4 three pictures. Take the two the notes show least recently; with no notes, blocks 1 and 2. Each block has four questions, on four different everyday situations the notes leave out (shopping, the doctor, neighbours, work, school, travel, food, clothes, hobbies, the weather).

Write the eight questions by §Questions. Done when every question has its frame, its two-part prompt and, in blocks 2–4, its picture list.

### 3. Opening

Greet the learner by name and give: the two blocks, the eight answers, the exam-pace budget of 2.2 minutes an answer (about 18 minutes), and that a typed answer is two to four full sentences that answer **both** parts of the prompt. Then start with the first question.

### 4. One question at a time

**Block 1, the spoken question.** The exam asks it aloud, in a video, with no text. It takes two turns, because only a turn's final message is sure to stay on screen. The question turn ends on the cue:

```markdown
## Onderdeel 1 — vraag {N}/8

{A man / A woman} stelt je een vraag.

Write **go** to hear it.
```

On "go", speak it with a Dutch voice, the text on stdin so quotes go through as written (Xander, `nl_NL`, for a man; Ellen, `nl_BE`, for a woman):

```bash
say -v Xander -r 160 <<'EOF'
{the question}
EOF
```

`say` returns when the speech ends. The turn's final message asks for the written answer, or "nog een keer" to hear the question again; the written question waits for the feedback. When `say` exits non-zero or the learner hears nothing, end the session and say why.

**Blocks 2–4, the picture questions.** One turn:

```markdown
## Onderdeel {B} — vraag {N}/8

{situation line in Dutch}

**{Vertel … Vertel ook …}**
*{Gebruik het plaatje. / Kies een van de plaatjes. / Gebruik alle plaatjes.}*

Plaatje {1}: {description in the learner's language}
Plaatje {2}: {description}

**Type your answer in Dutch:**
```

Pictures are listed in the learner's language, one line each, without the Dutch words the learner has to find. Done when the answer is in.

### 5. Evaluate

Work in the order the rubric ranks the aspects:

1. **Adequaatheid (0–3)** — both parts of the prompt answered, and understandable. A missing part is `missing`, 🔴 when the whole part is absent; it costs more than any grammar slip. A 0 zeroes the other rows.
2. **Grammatica (0–2)** — by the number of errors: many, quite a few, hardly any.
3. **Woordgebruik (0–2)** — words that fit; an answer that only repeats the prompt's words earns less.
4. **Coherentie (0–1)** — *en, maar, want, omdat* that join the sentences.

Tag each finding with severity (🔴 critical, 🟡 moderate, 🟢 minor) and a category from `fluent-feedback-formatter` §"Use these category labels", and correct the two or three that cost the most points; a page of red marks ends a speaking session. Stage each finding for the end-of-session update.

Feedback, a variant of `fluent-feedback-formatter`:

```markdown
{✅ or 🟡} {one-line encouragement}

**What you said:** "{their answer}"
{block 1 only: **The question was:** "{the question}"}

**Both parts answered:** {part 1 ✅/❌} · {part 2 ✅/❌}

**Corrections:**
- ❌ {🔴/🟡/🟢} "{wrong}" → **"{correct}"** ({category} — {why})
- ✅ "{right}" — {specific praise}

**Natural version:** "{a version the learner could say}"

| Adequaatheid | Grammatica | Woordgebruik | Coherentie | Total |
|---|---|---|---|---|
| {a}/3 | {g}/2 | {w}/2 | {c}/1 | **{P}/8** |

**Score: {X}/10** — {P} ÷ 8 × 10, rounded
```

The assessors apply DUO's own rubric; this is the tutor's estimate of its typed part. The same message goes on to the next question (step 4); after the eighth answer, the summary (step 6) follows the feedback.

### 6. Session summary

```bash
date +%s
```

Minutes taken = (this number − the start mark) ÷ 60, rounded up.

```markdown
## 🎉 Speaking Session Complete!

| Block | Question | Points | Score |
|---|---|---|---|
| {B} | {N} | {P}/8 | {X}/10 |

**Time:** {minutes} of {budget} min (exam pace: 2.2 min an answer)
**Weakest aspect:** {aspect}
**Not scored:** Vloeiendheid and Uitspraak (4 of the exam's 12 points): they need your voice.

### For next time
- Say today's three best natural versions aloud once.
- Practice: {weak area}
```

Close with the way to the exam's own material: DUO's three practice exams for Spreken (`inburgeren.nl/examen-doen/oefenen.jsp`) run in the exam's own player with the microphone and the video questions, which a typed round cannot give; one taken before the exam shows what the voice adds.

### 7. Update all databases

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-speaking"`, `skills_practiced: ["speaking"]`
- `skill_scores.speaking: {exercises: 8, correct: count of answers with Adequaatheid of 2 or 3, time_minutes}`, with the minutes from step 6
- `errors[]` — one per pattern that cost a point on two or more answers, and one for each whole part left unanswered (`missing`)
- `session_notes` — the blocks run and the points each earned ("blok 1: 6/8, 5/8, 7/8, 6/8; blok 3: …"), which the next sessions rotate from
- `focus_next_session[]` — one block + one pattern

Save the transcript as `fluent-speaking-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Each answer is one question: the block, the prompt (the spoken question's text included), the picture list, the answer, the rubric row and the `**Score:**`; `**Accuracy:**` is the share of answers counted correct.

Done when `fluent-db-updater` reports the write and the transcript file exists.

### 8. Offer another session

With everything saved, ask whether the learner wants another session of two blocks, as CLAUDE.md's session-cap rule asks. On a yes, the learner types `/fluent-speaking` again: a new session with its own record.

## Questions

The form of each block is the exam's (`.claude/references/exam-a2.md` §Spreken). Questions are in Dutch at A2 and address the learner as *u*; each has two parts, and the answer owes both.

- **Block 1** — one or two sentences a person asks about the learner's own life (the day, the family, the street, work, food); no text is shown. The two parts sit inside the question (`… en waarom?`).
- **Block 2, one picture** — a situation line about a named person, then `Vertel wat … Vertel ook …` (what the person does or can eat, and an opinion, a reason, how often, or what happens next). One question in a session asks `Noem drie dingen.`
- **Block 3, two pictures** — a situation about the learner, then `… liever …? Vertel ook waarom.` or `… wanneer …`, and `Kies een van de plaatjes.`
- **Block 4, three pictures** — a situation, `Vertel wat voor spullen dat zijn. Vertel ook wat …` or `Vertel wat {name} doet. Vertel iets over alle plaatjes.`, and `Gebruik alle plaatjes.`
- **One decision** — each part asks for one thing; the pictures say what is to be said about, not the words (`fluent-review` §3).

## B1 conversation

With the argument `b1`: a typed conversation of `computed.session_cap` questions, one at a time, on topics from `.claude/references/level-b1.md` §"Genres" (narrate a past event, compare two options, a hypothetical, an unplanned phone call), each worded so that answering it calls for one grammar target the learner has not yet mastered. After three or four questions on one topic, change topic. Score each answer: Communication 0–5 (clear, answers the question), Grammar 0–3, Vocabulary 0–2, total out of 10; a slip that leaves the message clear is noted lightly, and the Communication score leads. Feedback is the template of step 5 with the four rubric columns replaced by those three scores. Update: `skill_scores.speaking: {exercises: N, correct: count of clear answers, time_minutes}`; `errors[]` hold the communication-blocking ones and misses on a B1 target from `.claude/references/level-b1.md`.
