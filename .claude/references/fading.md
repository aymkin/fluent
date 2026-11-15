# Fading: how much an exercise gives

Load when building an exercise in `/fluent-review`, a `/fluent-grammar` series or a `/fluent-learn` drill.
The code that moves a card's rung: `.claude/hooks/fading.py`.

Every exercise is one decision (`fluent-review` §3). Its **rung** sets how much of that decision the prompt
hands over. A base form, options, the words to assemble, the chunk itself — help like this turns recall into
copying, so it **fades** as answers grow confident, and once no help is left the sentence itself changes.

## Rungs

| Rung | Label | The prompt gives |
| --- | --- | --- |
| `scaffold` | «опора» | the decision's material, as §Scaffold lists it |
| `cue` | «подсказка» | the Russian line, the frame with its gap, and the kind of decision in brackets: «(причастие)», «(вспомогательный глагол)», «(артикль)», «(предлог)», «(глагол к чанку)», «(орфография)»; a word-order item, the Russian sentence, its first Dutch word and «(порядок слов)»; a word to recall, its first letter, with the article for a noun |
| `bare` | «без подсказки» | the Russian line and the frame with its gap; a word-order item, the Russian sentence alone |
| `varied` | «вариация» | `bare` on the card's sentence with one thing changed, as §Varied says |

A vocabulary card still rotates direction — RU → NL, NL → RU, cloze (`fluent-review` §3); the rung sets the
help in whichever direction comes up.

## Scaffold

- **A form of a known word** — participle, verb form, adjective ending, plural: the base form in brackets,
  `Gisteren heb ik mijn moeder ___ (bellen)`.
- **A grammatical choice** — de/het, hebben/zijn: the two options.
- **A word's partner** — the verb or particle of a chunk, the preposition after a verb: its first letter,
  `koffie z…`, `neemt een medewerker a…`, `wachten o…`. Options would pair the word with false partners, and
  learners keep those (`chunks-nl.md` §Chunk).
- **Spelling:** the word with its tricky letters blanked, `va_antie`.
- **Word order:** the words in a neutral order, the first word named; the other order checked wrong.
- **A word to recall:** two or three options — Dutch words for RU → NL, Russian meanings for NL → RU.
- **Find the error, find the subject:** scaffold exercises, since the answer's material is on the page.

## Varied

The card's own sentence (`content`, `answer`) with one change: the person, the time marker, or the
circumstance — the place, the object, the companion. Every other word is one the learner owns. The gap holds
the tested form alone: a new person moves the auxiliary into the frame, so the decision stays the one the card
tests. The change keeps exactly one valid answer: before sending, write down the other candidate and check it
is wrong.

## Moving

- **A card** moves in `update-db.py` after each review: a confident first attempt (8–10/10) takes it one rung
  on, a miss (0–5/10) one rung back, 6–7/10 keeps it. Build from the rung `read-db.py` gives.
- **A series or a drill** starts on its card's `rung` — a rule or pattern with no card starts on `scaffold` —
  and moves the same way after each answer, so a confident series reaches `varied` before it ends.

Before sending, check the prompt against its rung's row: it gives what that row gives, and no more.
