# Synthetic round

The fallback for `SKILL.md` steps 3 and 4, reached when step 2 finds no library track to play: you write each fragment and the Mac's speech synthesizer speaks it. Steps 5-8 of `SKILL.md` follow as written, with the differences noted at the end.

## 1. Cast the voices

```bash
say -v '?'
```

Cast the voices whose locale is the target language's. For Dutch, roles go to `nl_NL` voices first, since the exam is spoken in the Netherlands; with one `nl_NL` voice installed, a dialogue's second role goes to `nl_BE`.

With no voice for the target language, end the session with the way to add one: System Settings → Accessibility → Spoken Content → System voice → Manage Voices… → the language → a voice (Claire, for Dutch).

Done when every role in the round has a voice.

## 2. Write the round

The round is four fragments carrying the session cap (`computed.session_cap`) questions between them: 3, 3, 2 and 2. Each fragment has:

- **Situation** — rotated through a conversation in the street, at the buurthuis, at work, on the phone, at the doctor's or in a shop, a voicemail, a message from the children's school, a news item, a short clip from the internet. Start with the situations the previous round's notes leave out.
- **Frame** — two lines in Dutch, by `SKILL.md` §Frame.
- **Script** — 50-70 words for a two-question fragment and 80-120 for a three-question one, natural speech at `current_level`, one or two roles (a voicemail has one), with times, days, prices, numbers and names said the way people say them; each question rests on a different detail. Proofread it: finite verb last in every bijzin, inversion after a fronted element, de/het, participle forms.
- **Questions and options** — by `SKILL.md` §Questions.

Done when every fragment has a frame, a proofread script with a voice per line, its questions with their options and answers.

## 3. Play, one fragment at a time

Run each fragment in the two turns of `SKILL.md` step 4. The frame is the context; the question turn adds nothing to it. On "go", the recording turn plays the fragment line by line, each line in its role's voice — one `say` per line, with the text on stdin so quotes and apostrophes go through as written:

```bash
say -v Xander -r 170 <<'EOF'
{line}
EOF
```

- **Speech rate** — 170 words per minute. When the running accuracy is below 50% after four fragments, play the rest of the round at 150 and tell the learner.
- **Replay and audio** — as in `SKILL.md` step 4, with `say` in place of `afplay`.

Done when the answer is in.

## Back in SKILL.md

- **Step 5** — each question's block quotes the whole script, role by role, with that question's settling sentence in bold; the script is yours, so nothing stays back.
- **Step 7** — `session_notes` record the situations, voices and speech rate in place of track ids; the transcript file carries every script with its question.
