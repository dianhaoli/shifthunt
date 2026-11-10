# S3 detector validation against hand labels (plan §5)

## What was done

- Sample: 50 logged texts, 42 templated and 8 free text, drawn by `scripts/s3_coder.py --validate-sample 50 --seed 20261112`
  from the "ok" probe_query texts of the four pilot runs (pool: 80 distinct templated texts from three runs, 8 distinct
  free-text texts from one run, so the free-text sample is the whole pool). 21 of the 50 are scored texts of S3 (written
  to the run's hard probe); the other 29 were written to other probes.
- Detector flags: `flags_for` of `scripts/s3_coder.py` (`shifthunt.detectors.detect_all` for templated texts,
  `shifthunt.freetext.detect` for free text), 15 properties per text, 750 cells.
- Hand labels: two independent labellers, A and B. Each wrote property definitions from the render code of the
  generator (`shifthunt/textgen.py`, `shifthunt/freetext.py`) before reading the texts, then labelled all 15
  properties of every text by reading it. The labels were made without the detectors. A's report states that no
  detector was run and that neither the detector flags nor the other labeller's file was opened, and that the
  free-text detector table at the bottom of `shifthunt/freetext.py` was seen while reading the render code; B's
  report gives no process note.
- Comparison and adjudication: agreement counts and Cohen's kappa per substrate and property; every cell where the
  detector differs from a labeller was adjudicated against the text, the render code and the detector, as L (labeller
  slip), D (detector wrong under the generator's own definition) or A (agent-written form the generator never
  produces, neither value clearly right). The texts, labels, comparison script and adjudication detail are private.

## Agreement

Cells are (text, property) pairs. Kappa is given where both classes occur for both raters, else "-".
"on" is the number of cells labelled 1 by A / by B / by the detector.

**templated** (42 texts x 15 properties)

| property | cells | A = B | kappa | A = detector | kappa | B = detector | kappa | on: A / B / detector |
|---|---|---|---|---|---|---|---|---|
| all properties pooled | 630 | 630 | 1.00 | 630 | 1.00 | 630 | 1.00 | 255 / 255 / 255 |
| exclamation | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 12 / 12 / 12 |
| lowercase | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 18 / 18 / 18 |
| signoff | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 19 / 19 / 19 |
| british_spelling | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 20 / 20 / 20 |
| bullet_list | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 20 / 20 / 20 |
| past_tense | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 19 / 19 / 19 |
| she_pronoun | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 28 / 28 / 28 |
| question_ending | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 18 / 18 / 18 |
| quote | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 4 / 4 / 4 |
| greeting | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 16 / 16 / 16 |
| hashtag | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 21 / 21 / 21 |
| postscript | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 15 / 15 / 15 |
| weekday | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 14 / 14 / 14 |
| parenthetical | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 18 / 18 / 18 |
| negative_sentiment | 42 | 42 | 1.00 | 42 | 1.00 | 42 | 1.00 | 13 / 13 / 13 |

**freetext** (8 texts x 15 properties)

| property | cells | A = B | kappa | A = detector | kappa | B = detector | kappa | on: A / B / detector |
|---|---|---|---|---|---|---|---|---|
| all properties pooled | 120 | 118 | 0.97 | 120 | 1.00 | 118 | 0.97 | 56 / 58 / 56 |
| exclamation | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 7 / 7 / 7 |
| lowercase | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 6 / 6 / 6 |
| signoff | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 4 / 4 / 4 |
| signoff_excl | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 2 / 2 / 2 |
| ellipsis | 8 | 8 | - | 8 | - | 8 | - | 0 / 0 / 0 |
| emoticon | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 3 / 3 / 3 |
| she_pronoun | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 4 / 4 / 4 |
| question | 8 | 6 | 0.50 | 8 | 1.00 | 6 | 0.50 | 4 / 6 / 4 |
| quote | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 3 / 3 / 3 |
| greeting | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 1 / 1 / 1 |
| hashtag | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 5 / 5 / 5 |
| postscript | 8 | 8 | - | 8 | - | 8 | - | 8 / 8 / 8 |
| ps_question | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 3 / 3 / 3 |
| weekday | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 3 / 3 / 3 |
| parenthetical | 8 | 8 | 1.00 | 8 | 1.00 | 8 | 1.00 | 3 / 3 / 3 |

Totals over both substrates: A = B in 748 of 750 cells, A = detector in 750 of 750, B = detector in 748 of 750.
On the 21 sampled texts that are scored texts of S3, all 315 cells agree between A, B and the detector.

## Detector-versus-labeller disagreements

2 cells of 750: L 0, D 0, A 2. Both are the free-text property `question`, both in the one free-text pilot run, and
in both the detector agrees with A and differs from B.

- A, v008, `question` (A 0, B 1, detector 0): the body keeps one of the generator's question sentences but ends it
  with a full stop ("is that so strange."). The generator writes that sentence only with "?" and otherwise leaves it
  out; the detector tests for "?" in the body.
- A, v019, `question` (A 0, B 1, detector 0): same form with another of the generator's question sentences
  ("can you picture it.").

The two labellers split exactly along their definitions written beforehand: A required the question mark, B went by
the wording. Neither text was written to its run's hard probe, so neither is a scored text of S3, and recoding either
cell leaves that run's S3 unchanged (checked: the run's four scored texts are all in the sample and S3 computed from
A's labels, from B's labels and from the detector flags is the same).

One further cell was marked ambiguous by both labellers although all three values agree (0): v021, `weekday`, where
the generator's weekday sentence is there with "tomorrow" in place of the day name ("tomorrow is her only free
evening"). It is the same kind of half-present form, and it is also not a scored text.

## Conclusion

The detectors are fit for coding the agent-written texts: no detector error was found in 750 cells, and they agree
with both labellers on every cell of every sampled scored text. Caveats:

1. Half-present forms. An agent can switch a free-text property "off" by removing only its mark (the "?" of a
   question sentence, the day name of a weekday sentence) and keeping the rest of the generator's sentence. The
   detectors code the mark, so such a text is coded as the property being off, and a pair of texts that differ only
   in the mark counts as varying that property. Three of the 8 free-text texts hold such a form (two disputed by the
   labellers, one not). S3 is to be read with this rule: a property is what its detector tests, not the wording
   around it. No scored text in the sample holds such a form.
2. Coverage. All 42 templated texts are in the generator's exact sentence forms (checked against a pattern built from
   the templates and word banks), so the templated detectors were confirmed on generator-form texts only, not on
   freely worded ones. The free-text evidence is 8 texts from one run by one agent; `ellipsis` was never on and
   `postscript` never off, so those two free-text detectors were checked in one class only, and several others
   rest on one to three "on" texts.
