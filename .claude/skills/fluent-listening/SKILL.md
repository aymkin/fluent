---
name: fluent-listening
description: Listening practice in the DUO A2 exam format — fragments from your audio library, 2–3 A/B/C questions each, at the exam's pace.
allowed-tools: Read, Write, Bash
disable-model-invocation: true
---

# Listening Session

## Overview

A round of the DUO A2 Luisteren exam, built the way the exam is built: short fragments of everyday speech, two or three questions on each, three options A/B/C (now and then four), all in the target language. The recordings come from the learner's **library** — their own course audio, each track with a time-stamped transcript. The learner reads the situation and the questions first, hears the fragment, and answers; the transcript lines arrive with the feedback.

A round is `computed.session_cap` questions on four fragments (3 + 3 + 2 + 2). The exam has 25 questions on 10 fragments in 45 minutes, so a round's time budget is 1.8 minutes a question.

## Instructions

### 0. Load the project's rules

If a skill available in this session says to load it before `/fluent-listening` — a project's own rules for this learner — load it now. Where its rules disagree with this plugin's defaults — these steps, the feedback format, the grading — its rules win.

### 1. Load context

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/read-db.py"
```

Need: `learner-profile` (name, target and native language), `computed.session_cap`, `computed.next_session_id`, and the `session_notes` of the latest three `session-log` entries whose `command_used` is `/fluent-listening`: the tracks they played and the learner's covered themes.

Read `.claude/references/exam-a2.md` §Luisteren: the frame, the question types and the option counts the round copies.

```bash
date +%s
```

Keep the number as the round's start mark.

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
- **Mix.** Two fragments come from known tracks, two from ahead tracks; the two three-question fragments go one to each pool.
- **Fresh first.** Take tracks absent from the last three rounds' notes first.
- **A track is a fragment.** It carries two questions at 30 seconds or more, and three at about 60 seconds or more; each question rests on a different settling line. A track too short or too thin for two separate questions stays out.

Read each chosen track's `.lrc`. Write the fragment's frame and its questions by §Frame and §Questions below, with two limits that come from the transcript:

- The `.lrc` is an automatic transcript and some lines are misheard. Base a question only on lines that read as correct Dutch, and write the question and options in your own correct Dutch.
- The opening line of a track is the narrator's title and situation ("Op het werk. Twee collega's praten over een vergadering."). The questions ask for something the conversation itself settles.

Open the round: greet the learner by name and give the round's size, its four fragments and its time budget (1.8 minutes a question). Done when every fragment has its frame, its questions in the order the recording settles them, each with its settling `.lrc` lines, its options and its answer.

### 4. Play, one fragment at a time

A fragment takes two turns. Only a turn's final message is sure to stay on screen — the desktop app folds away text written before a tool call — so the questions end one turn and the recording plays in the next.

**The question turn.** The turn's final message ends on the fragment's questions and the cue to play. Fragment 1 follows the round's opening, which names the round's size and its time budget; every later fragment follows step 5's feedback in the same message.

```markdown
## Fragment {F}/{fragments}

{frame: two lines in Dutch}

*Lees eerst de vragen. Luister daarna naar de tekst.*

**Vraag {N}/{round size}** — {question}

A. {option}
B. {option}
C. {option}

**Vraag {N+1}/{round size}** — {question}

A. {option}
B. {option}
C. {option}

Write **go** to play the fragment.
```

**The recording turn.** On "go", play the whole track — the narrator's opening sets the scene, as a DUO fragment does:

```bash
afplay "<data_dir>/audio/<collection>/<theme folder>/<track>.mp3"
```

`afplay` returns when the track ends. The turn's final message repeats the questions with their options and asks for one letter per question (A, B or C; "B, A" for two questions), or "nog een keer" to hear the fragment again. Done when the answers are in — the transcript waits for the feedback (audio-first).

- **Replay.** On "nog een keer" (once more), play the track once more, end the turn on the questions again, and note the replay. A second request gets the settling lines, and the fragment's questions count as missed. This is the tutor's practice rule: whether the live exam allows a replay is not published.
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

Give the block once for each question of the fragment, in order. Quote the settling lines with one or two lines around them; the full text stays in the library. Done when the learner has the lines and the explanation for every question of the fragment. The same message goes on to the next fragment's question turn (step 4), so it ends on that fragment's questions and its "go" cue; after the round's last fragment, the summary (step 6) follows the feedback instead.

### 6. Session summary

```bash
date +%s
```

Minutes taken = (this number − the start mark) ÷ 60, rounded up.

```markdown
## 🎧 Listening Session Complete!

**Questions:** {N} · **Correct:** {X} ({percent}%) · **Replays:** {R}
**Time:** {minutes} of {budget} min (exam pace: 1.8 min a question)
**Known themes:** {x}/{n} · **Ahead:** {x}/{n}

### By question type
- Detail (how long, when, where, who, why, how much): {x}/{n}
- What someone must or will do: {x}/{n}

### Words from today's recordings
| {target_language} | {native_language} |
|-------|---------|
| {word} | {meaning} |

**Which of these do you want to save for review?** Reply with the words, "all", or "none".
```

Stage each word the learner chose for `new_vocabulary[]`. Close with the way to the exam's own material: DUO's three practice exams for Luisteren (`inburgeren.nl/examen-doen/oefenen.jsp`) hold 25 questions in 45 minutes; one taken under exam conditions shows what a tutor round cannot — and the learner can report the result here. When the round scored above 80%, say it is time for one of them.

### 7. Save

Use the `fluent-db-updater` skill:

- `command_used: "/fluent-listening"`, `skills_practiced: ["listening"]`
- `skill_scores.listening: {exercises: N questions, correct: count_right, time_minutes}`, with the minutes from step 6
- `errors[]` — one per question type missed twice or more: category `comprehension` for detail, `inference` for what someone must or will do (canon: `fluent-feedback-formatter` §"Use these category labels")
- `new_vocabulary[]` — the words the learner chose
- `session_notes` — the track ids played, the covered themes ("covered: 5–13") and the replays, which the next rounds rotate from
- `focus_next_session[]` — the weakest question type

Save the transcript as `fluent-listening-session-{NNN}.md` in the `results/` directory of the data directory (step 2). Required format: `${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/results/README.md`. Per question: the track id, the fragment's frame, the question and options, the answer given, the verdict, and the settling lines as quoted in step 5. The summary's counts by question type go in the file's Session Summary.

Done when `fluent-db-updater` reports the write and the transcript file exists.

### 8. Offer another round

With everything saved, ask whether the learner wants another round, as CLAUDE.md's session-cap rule asks. On a yes, the learner types `/fluent-listening` again: a new session with its own record.

## Frame

Each fragment opens with a frame of two short lines in Dutch, as the exam shows it: who is where and what they do (`Steven komt Jari tegen op straat. Ze praten met elkaar.`). Write it from the track's opening line and the setting. A frame names the people the questions mention, and none of the answers. Below it goes `Lees eerst de vragen. Luister daarna naar de tekst.`

## Questions

The rules for every question, on a library track or a synthetic fragment:

- **Wording** — in the target language, the way DUO asks, one decision (`fluent-review` §3): a direct question that names the person from the frame (`Wanneer komt Jari eten?`).
- **Types** — a detail (how long, when, where, who, why, how much, which) or what someone must or will do. The exam asks no main-point question, so a round has none. Within a fragment the questions follow the order of the recording.
- **Options** — A, B and C in the target language, short, with the stem's words kept out of them; one or two questions of the round take a fourth, D. Each distractor names something the recording also mentions, so the answer takes listening to the whole recording. The right letter moves across the options over the round.
