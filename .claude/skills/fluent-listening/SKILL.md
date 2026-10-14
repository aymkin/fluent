---
name: fluent-listening
description: Listening practice in the DUO A2 format — short spoken fragments, one A/B/C question each.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Listening Session

## Overview

A round of short spoken fragments in the format of the DUO A2 Luisteren exam: an everyday situation, then one question with three options A/B/C, all in the target language. The macOS speech synthesizer plays each fragment through the learner's speakers. Every fragment is audio-first: the learner answers from what they heard, and the transcript arrives with the feedback.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-listening` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language, `current_level`), `computed.session_cap`, `computed.next_session_id`, and the `session_notes` of the latest `session-log` entry whose `command_used` is `/fluent-listening`: the situations, voices and speech rate of the previous round.

### 2. Cast the voices

```bash
say -v '?'
```

Cast the voices whose locale is the target language's. For Dutch, roles go to `nl_NL` voices first, since the exam is spoken in the Netherlands; with one `nl_NL` voice installed, a dialogue's second role goes to `nl_BE`.

With no voice for the target language, end the session with the way to add one: System Settings → Accessibility → Spoken Content → System voice → Manage Voices… → the language → a voice (Claire, for Dutch).

Done when every role in the round has a voice.

### 3. Write the round

The round is the session cap (`computed.session_cap`) fragments. Each fragment has:

- **Situation** — rotated through a conversation in the street, at the buurthuis, at work, at the doctor's or in a shop, a voicemail, a message from the children's school, an announcement, a short radio or video clip. Start with the situations the previous round's notes leave out.
- **Script** — 40-120 words of natural speech at `current_level`, one or two roles, with times, days, prices, numbers and names said the way people say them. Proofread it: finite verb last in every bijzin, inversion after a fronted element, de/het, participle forms.
- **Question** — in the target language, worded the way DUO asks, one decision (`fluent-review` §3). Rotate three types: main point ("Waar gaat het gesprek over?"), detail (a time, a place, a number, a name), intention or next step ("Wat gaat de man doen?").
- **Options** — A, B and C in the target language. Each distractor names something the fragment also mentions, so the answer takes listening to the whole fragment. The right letter moves across A, B and C over the round.

Done when every fragment has a situation, a proofread script with a voice per line, a question, three options and its answer.

### 4. Play, one fragment at a time

Show the fragment:

```markdown
## Fragment {N}/{round size}: {situation, in the target language}

{one line of context in the target language, e.g. "Je hoort een voicemail van de tandarts."}

**{question}**

A. {option}
B. {option}
C. {option}
```

Then play it line by line, each line in its role's voice. One `say` per line, with the text on stdin, so quotes and apostrophes go through as written:

```bash
say -v Xander -r 170 <<'EOF'
{line}
EOF
```

Ask for the answer: A, B or C. Done when the answer is in — the transcript waits for the feedback (audio-first).

- **Speech rate** — 170 words per minute. When the running accuracy is below 50% after four fragments, play the rest of the round at 150 and tell the learner.
- **Replay** — on "nog een keer" (once more), play the fragment once more and note the replay. A second request gets the transcript, and the fragment counts as missed.
- **Audio** — working sound is the session's precondition: when `say` exits non-zero or the learner hears nothing, end the round and say why.

### 5. Feedback per fragment

```markdown
{✅ or ❌} **{right letter}. {right option}**

**Transcript:**
> {the script, role by role; the sentence that settles the question in **bold**}

{why, in the learner's native language: where the fragment settles the question, and what made the distractor tempting}

**Words:** {1-3 useful words or phrases from the fragment, with translations}
```

Done when the learner has the transcript and the explanation; then the next fragment.

### 6. Session summary

```markdown
## 🎧 Listening Session Complete!

**Fragments:** {N} · **Correct:** {X} ({percent}%) · **Replays:** {R} · **Speech rate:** {rate}

### By question type
- Main point: {x}/{n}
- Detail: {x}/{n}
- Intention / next step: {x}/{n}

### Words from today's fragments
| {target_language} | {native_language} |
|-------|---------|
| {word} | {meaning} |

**Which of these do you want to save for review?** Reply with the words, "all", or "none".
```

Stage each word the learner chose for `new_vocabulary[]`. When the round scored above 80%, close with a pointer to the official DUO practice exams (oefenexamens Luisteren on inburgeren.nl): they play recorded human voices, as the exam does.

### 7. Save

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-listening"`, `skills_practiced: ["listening"]`
- `skill_scores.listening: {exercises: N, correct: count_right, time_minutes}`
- `errors[]` — one per question type missed twice or more: category `comprehension` for main point and detail, `inference` for intention and next step (canon: `fluent-feedback-formatter` §"Use these category labels")
- `new_vocabulary[]` — the words the learner chose
- `session_notes` — the situations, voices, speech rate and replays, which the next round rotates from
- `focus_next_session[]` — the weakest question type

Save the transcript as `fluent-listening-session-{NNN}.md` in the
`results/` directory of the path this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Include every script with its question, the answer given and the verdict.

Done when `fluent-db-updater` reports the write and the transcript file exists.

### 8. Offer another round

With everything saved, ask whether the learner wants another round, as CLAUDE.md's session-cap rule asks. On a yes, the learner types `/fluent-listening` again: a new session with its own record.
