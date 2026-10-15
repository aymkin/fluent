---
name: fluent-listening
description: Listening practice in the DUO A2 format — real course recordings from your audio library, one A/B/C question at a time.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Listening Session

## Overview

A round of listening questions in the format of the DUO A2 Luisteren exam: a question with three options A/B/C about an everyday recording, all in the target language. The recordings come from the learner's **library** — their own course audio, each track with a time-stamped transcript. Every question is audio-first: the learner answers from what they heard, and the transcript lines arrive with the feedback.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-listening` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language), `computed.session_cap`, `computed.next_session_id`, and the `session_notes` of the latest three `session-log` entries whose `command_used` is `/fluent-listening`: the tracks they played and the learner's covered themes.

### 2. Find the library

The library lives in `audio/` under the data directory this prints:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/fluent_paths.py"
```

```bash
find -L "<data_dir>/audio" -name '*.mp3'
```

The layout is `audio/<collection>/<NN theme title>/<track>.mp3`. A **track** is an `.mp3` with a `.lrc` transcript beside it, and its theme number is the number that opens its folder name. A track's id is `<collection>/<track file name without .mp3>`, and its length is the last timestamp in its `.lrc`.

When the library has no tracks, or every eligible track (step 3) sits in the last three rounds' notes, read `SYNTHETIC.md` in this skill's folder and follow it in place of steps 3 and 4: the round then runs on the Mac's synthesized voices. Continue at step 5 either way.

Done when the track list is in hand, or the round is on the synthetic path.

### 3. Choose the round

The learner's **covered themes** are the range of the latest round's notes (e.g. "covered: 5–13"). With no range in the notes, ask once: "Which themes of your course have you covered so far?"

- **Pools.** Known: tracks from the covered themes. Ahead: tracks from themes above the range. Themes below the range stay out of the round.
- **Mix.** Half the round's questions come from known tracks, half from ahead tracks.
- **Fresh first.** Take tracks absent from the last three rounds' notes first. Tracks under 20 seconds are too short to carry a question.
- **Questions per track.** One question; a track over 90 seconds may carry a second, so a round of `computed.session_cap` questions plays fewer tracks.

Read each chosen track's `.lrc`. Write its questions by the rules in §Questions below, with two limits that come from the transcript:

- The `.lrc` is an automatic transcript and some lines are misheard. Base a question only on lines that read as correct Dutch, and write the question and options in your own correct Dutch.
- The opening line of a track is the narrator's title and situation ("Op het werk. Twee collega's praten over een vergadering."). The question asks for something the conversation itself settles.

Done when every question has its track, the timestamped `.lrc` lines that settle it, three options and its answer.

### 4. Play, one question at a time

Each question takes two turns. Only a turn's final message is sure to stay on screen — the desktop app folds away text written before a tool call — so the question ends one turn and the recording plays in the next.

**The question turn.** The turn's final message ends on the question and the cue to play. Question 1 follows the round's opening; every later question follows step 5's feedback in the same message.

```markdown
## Vraag {N}/{round size} — {theme title}

**{question}**

A. {option}
B. {option}
C. {option}

Write **go** to play the recording.
```

**The recording turn.** On "go", play the whole track — the narrator's opening sets the scene, as a DUO fragment does:

```bash
afplay "<data_dir>/audio/<collection>/<theme folder>/<track>.mp3"
```

`afplay` returns when the track ends. The turn's final message repeats the question with its options and asks for A, B or C, or "nog een keer" to hear it again. Done when the answer is in — the transcript waits for the feedback (audio-first).

- **Second question.** On a track that carries two, the question turn shows both, and the recording turn repeats both; the learner answers both from the same hearing. Feedback for both follows.
- **Replay.** On "nog een keer" (once more), play the track once more, end the turn on the question again, and note the replay. A second request gets the settling lines, and the question counts as missed.
- **Audio.** Working sound is the session's precondition: when `afplay` exits non-zero or the learner hears nothing, end the round and say why.

### 5. Feedback per question

```markdown
{✅ or ❌} **{right letter}. {right option}**

**From the recording** (automatic transcript):
> [{mm:ss}] {line before}
> [{mm:ss}] **{the line that settles the question}**
> [{mm:ss}] {line after}

{why, in the learner's native language: where the recording settles the question, and what made the distractor tempting}

**Words:** {1-3 useful words or phrases from the recording, with translations}
```

Quote the settling lines with one or two lines around them; the full text stays in the library. Done when the learner has the lines and the explanation. The same message goes on to the next question's question turn (step 4), so it ends on that question and its "go" cue; after the round's last question, the summary (step 6) follows the feedback instead.

### 6. Session summary

```markdown
## 🎧 Listening Session Complete!

**Questions:** {N} · **Correct:** {X} ({percent}%) · **Replays:** {R}
**Known themes:** {x}/{n} · **Ahead:** {x}/{n}

### By question type
- Main point: {x}/{n}
- Detail: {x}/{n}
- Intention / next step: {x}/{n}

### Words from today's recordings
| {target_language} | {native_language} |
|-------|---------|
| {word} | {meaning} |

**Which of these do you want to save for review?** Reply with the words, "all", or "none".
```

Stage each word the learner chose for `new_vocabulary[]`. When the round scored above 80%, close with a pointer to the official DUO practice exams (oefenexamens Luisteren on inburgeren.nl): they are the exam's own format.

### 7. Save

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-listening"`, `skills_practiced: ["listening"]`
- `skill_scores.listening: {exercises: N questions, correct: count_right, time_minutes}`
- `errors[]` — one per question type missed twice or more: category `comprehension` for main point and detail, `inference` for intention and next step (canon: `fluent-feedback-formatter` §"Use these category labels")
- `new_vocabulary[]` — the words the learner chose
- `session_notes` — the track ids played, the covered themes ("covered: 5–13") and the replays, which the next rounds rotate from
- `focus_next_session[]` — the weakest question type

Save the transcript as `fluent-listening-session-{NNN}.md` in the `results/` directory of the data directory (step 2). Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Per question: the track id, the question and options, the answer given, the verdict, and the settling lines as quoted in step 5.

Done when `fluent-db-updater` reports the write and the transcript file exists.

### 8. Offer another round

With everything saved, ask whether the learner wants another round, as CLAUDE.md's session-cap rule asks. On a yes, the learner types `/fluent-listening` again: a new session with its own record.

## Questions

The rules for every question, on a library track or a synthetic fragment:

- **Wording** — in the target language, the way DUO asks, one decision (`fluent-review` §3).
- **Types** — rotate across the round: main point ("Waar gaat het gesprek over?"), detail (a time, a place, a number, a name), intention or next step ("Wat gaat de man doen?").
- **Options** — A, B and C in the target language. Each distractor names something the recording also mentions, so the answer takes listening to the whole recording. The right letter moves across A, B and C over the round.
