# B1 targets

Load when the learner's `target_level` is B1, or when an exercise is being tuned
to B1. Sources are listed at the end; a number without a source there is not
established.

## What B1 asks for

B1 measures **task success**: the learner explains a problem, follows an
instruction, writes a complaint, and the meaning lands. Grammar is the skeleton
that carries longer, more abstract thoughts past A2's fixed phrases; it is not
the goal. CEFR does not list B1 grammar. `redelijk correcte` grammar is a B2
descriptor (Taalprofielen, Raamwerk NT2), and B1 test-takers still miss about
one passive in two (Hulstijn et al. 2012).

Grade to match:

- Lead the feedback with whether the task worked, then correct the form.
- Tag a slip that leaves the meaning clear 🟡 or 🟢. Reserve 🔴 for errors that
  break the message.
- Pick each session's drill from the targets below, one target per drill, so a
  miss names a single pattern.

## Grammar targets (Dutch)

Every target is a **course goal**, not an official requirement. **Done** means
the learner's first attempt is right — before any prompt from the tutor, with
no table in view and no options to choose from — on a task in their own
language that names what they want to say by its function (the situation and
the intent), never by its form. A sentence to translate is the form: it hands
over the skeleton of their own language, and the test turns into translation.
Tag errors `grammar` and name the target in `pattern_id`.

| Target                                | Example                                     | Done when                              | Note                            |
| ------------------------------------- | ------------------------------------------- | -------------------------------------- | ------------------------------- |
| Bijzin with omdat, als, dat           | Ik blijf thuis, omdat ik ziek ben.          | 5 of 5 with the verb last              | word order: B1 ≈ 81 % (H. 2012) |
| Bijzin with hoewel, nadat             | Hoewel het regent, ga ik fietsen.           | both, with inversion in the main part  |                                 |
| Perfectum, hebben or zijn             | Ik ben naar huis gegaan.                    | 10 common verbs, right auxiliary       | B1 ≈ 66 % (H. 2012): drill      |
| Imperfectum of modals                 | Ik wilde bellen, maar ik mocht niet.        | wilde, mocht, kon, moest in a sentence |                                 |
| Plusquamperfectum                     | Nadat ik gegeten had, belde ik hem.         | 3 sentences with had or was + participle |                               |
| Passief, present and past             | Het brood wordt gebakken. Het huis werd gebouwd. | 5 of 5                            | B1 ≈ 59 %: recognise first, produce later |
| `om … te` + infinitive                | Ik ga naar de winkel om brood te kopen.     | 3 sentences, infinitive last           |                                 |
| Zich-verbs                            | Ik verveel me. Hij haast zich.              | me, je, zich, ons, jullie for 6 verbs  |                                 |
| Relative clause, die or dat           | Het boek dat ik las, was mooi.              | 10 nouns, right pronoun                | B1 ≈ 56 % (H. 2012): drill      |

Order of introduction, when the learner's `mistakes-db` gives no steer: bijzin →
imperfectum of modals → perfectum → `om … te` → zich → passief → relative clause
→ plusquamperfectum. A target the learner reaches in three consecutive drills
leaves the rotation for spaced review.

## Vocabulary anchors

No official lemma count exists for B1. Use ranges with their source, never a
single threshold:

- Measured active vocabulary of B1 speakers ≈ 4000 words (SD ≈ 1600), B2 ≈ 7000
  (Hulstijn et al. 2012, _Internationale Neerlandistiek_).
- Text coverage by written vocabulary: 4731 base words cover 85.4 % of tokens
  (Hazenberg & Hulstijn 1996, books 1970-1988; a "base word" excludes transparent
  compounds and derivations, so it is not a lemma in a frequency list's sense).
  No published curve ties coverage to a CEFR level, and the 90/95/98 % thresholds
  are measured for English only. Treat a coverage figure from any other corpus as
  a comparison inside that corpus.
- Spoken-language proxy (SUBTLEX-NL, film subtitles, lemmas, computed 2026-09-29):
  2000 lemmas cover ≈ 90 % of tokens, 4000 ≈ 93 %, 10 000 ≈ 95-97 %
  (Keuleers, Brysbaert & New 2010). Applying the level estimates above to this
  curve is a calculation, not a measurement, and it does not transfer to written
  text.
- Selection pool for exam-relevant words: the Core and General lists of _A
  Frequency Dictionary of Dutch_ (5000 words) plus the CvTE addendum of
  Staatsexamen NT2. It is a pool to draw from, not a closed B1 list.
- New words at B1 come mostly from abstract, work and civic domains: work,
  health, housing, municipality, news. Function words are already known from A2;
  add only connectors (hoewel, nadat, terwijl, zodat) and the prepositions they
  bring.

## Genres

- Writing: opinion, complaint, inquiry, a short formal email (`u`).
- Speaking: narrate a past event, compare two options, one hypothetical
  ("Wat zou je doen als …?"), an unplanned phone call.

## Sources

- Keuleers, Brysbaert & New 2010, SUBTLEX-NL: <https://osf.io/3d8cx/>
- Hazenberg & Hulstijn 1996, _Applied Linguistics_:
  <https://www.scienceguide.nl/wp-content/uploads/2017/11/165030_Hazenberg_Hulstijn_Applied_Linguistics_1996.pdf>
- Hulstijn et al. 2012, _Internationale Neerlandistiek_ (grammar test and
  vocabulary size by level):
  <https://www.dbnl.org/tekst/_nee005201201_01/_nee005201201_01_0064.php>
- Taalprofielen, Raamwerk NT2:
  <https://www.nt2.nl/documenten/disk/taalprofielen_nt2_raamwerk.pdf>
- Staatsexamen NT2, CvTE addendum:
  <https://www.staatsexamensnt2.nl/documenten/2023/01/16/aanvullende-woordenlijst-cvte>
- Tiberius & Schoonheim 2013, _A Frequency Dictionary of Dutch_:
  <https://www.routledge.com/A-Frequency-Dictionary-of-Dutch-Core-Vocabulary-for-Learners/Tiberius-Schoonheim/p/book/9780415523806>
