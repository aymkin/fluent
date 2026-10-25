# Anki words

Load from `/fluent-vocab` and `/fluent-extensive`: where the learner's Anki words live and how to read
them by stage. Each skill keeps its own fallback for a session without Anki.

## Deck and fields

Deck `Frequentie` (subdecks Kern, Werk, Reading), note type `Frequentie NL`, one RU → NL card per note:

| Field | Holds |
| --- | --- |
| `Word` | the Dutch word; a noun with its article |
| `Translation` | one or two Russian meanings; the first is the card's sense |
| `Example` | one short Dutch sentence with the word |
| `TranslationExample` | its Russian version, the front of the card |
| `Rank`, `Audio` | frequency rank; the example's audio |

The learner's own pipeline (`~/Projects/nederlands`) builds these decks through its own gates; the
skills read them.

## Stages

Search with `findNotes`, then read the notes with `notesInfo`, at most 100 ids per call.

| Stage | Search |
| --- | --- |
| new today | `deck:Frequentie introduced:1 -is:learn -is:due -is:suspended` |
| reviewed today | `deck:Frequentie rated:1 -introduced:1 -is:learn -is:due -is:suspended` |
| new this week | `deck:Frequentie introduced:7 -introduced:1 -is:learn -is:due -is:suspended` |
| **onderweg** (in progress) | `deck:Frequentie -is:new prop:ivl<21 -is:due -is:suspended` |
| **vast** (learned) | `deck:Frequentie prop:ivl>=21 -is:due -is:suspended` |

`-is:learn -is:due` keeps out the cards Anki will still show today: a word practised here first would
reach Anki as a recall it did not earn.

`deck:Frequentie is:due -is:suspended` counts the cards still waiting in Anki today. Both "today" stages
empty while this count is above zero means the learner has not done Anki yet today.
