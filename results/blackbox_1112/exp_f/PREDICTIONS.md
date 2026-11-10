# Exp F: predictions (editable)

Written before any Exp F call. The round trip and the 20-call pilot (one shipped free-text episode) were seen after this file was written; the file was not changed after them. The "Claude's draft" columns are **Claude's draft, edit freely**: each range is a
predicted listing rate (primary rule, pooled over the cues of the row and its 5 repeats) with one line of
reasoning from Exp D and the generator only (no Exp F data). The "user" columns are empty for you to fill in.
Exp D facts used: with ONE aligned property, listing rates were GPT 100/100, Opus 100/100, Sonnet 99/100, Haiku
68/100; GPT gave about 2 candidates per answer, Opus 17, Sonnet 18, Haiku 15; Haiku missed child cues most
(ps_tentative 0/5, signoff_excl 0/5, signoff_initial 2/5).

| level | model | Claude's draft (edit freely) | Claude's reasoning (one line) | user: range | user: note |
|---|---|---|---|---|---|
| L2 typography | gpt-6.1-terra | 0.40-0.90 | Exp D 15/15, but with ~2 candidates per answer subtle marks may be crowded out by 7 louder aligned properties | | |
| L2 typography | claude-opus-5-5 | 0.80-1.00 | Exp D 15/15 and ~17 candidates per answer cover all 8 aligned properties | | |
| L2 typography | claude-sonnet-5-5 | 0.80-1.00 | Exp D 15/15 and ~18 candidates per answer | | |
| L2 typography | claude-haiku-5-5 | 0.40-0.90 | Exp D 13/15; less careful with invisible-looking marks among many | | |
| L3 positional | gpt-6.1-terra | 0.20-0.70 | the greeting "?" now replaces a "." in the same words (easy to miss) and "Oh!" is visible; a position-free regex fails (0.70) and few candidates are given | | |
| L3 positional | claude-opus-5-5 | 0.50-0.90 | scoped first-line / last-line regexes were its habit for P.S. children in Exp D; the one-character greeting change is the harder half | | |
| L3 positional | claude-sonnet-5-5 | 0.40-0.90 | as Opus, with more position-free "? anywhere" regexes | | |
| L3 positional | claude-haiku-5-5 | 0.05-0.40 | Exp D Haiku 0-3/5 on line-specific children; position-free regexes likely | | |
| L4 property of a property | gpt-6.1-terra | 0.40-0.90 | Exp D 10/10, but candidate count limits coverage of 8 | | |
| L4 property of a property | claude-opus-5-5 | 0.70-1.00 | Exp D 10/10 | | |
| L4 property of a property | claude-sonnet-5-5 | 0.70-1.00 | Exp D 10/10 | | |
| L4 property of a property | claude-haiku-5-5 | 0.00-0.40 | Exp D 2/10 with one aligned property | | |
| L5 two together | gpt-6.1-terra | 0.00-0.30 | it will name "informal greeting" and "lower case" apart, and each alone fails (0.75) | | |
| L5 two together | claude-opus-5-5 | 0.10-0.60 | may notice that neither component is exact in the sample (BA 0.78 each) and combine them | | |
| L5 two together | claude-sonnet-5-5 | 0.10-0.50 | as Opus, less often | | |
| L5 two together | claude-haiku-5-5 | 0.00-0.20 | components only; a case-sensitive "hey" literal no longer counts (counterfactual gate) | | |
| L6 doubly conditional | gpt-6.1-terra | 0.00-0.30 | "P.S. question" and "P.S. names someone" apart, each 0.75 | | |
| L6 doubly conditional | claude-opus-5-5 | 0.10-0.60 | same chance of combining as L5; the P.S. line is where it already looks | | |
| L6 doubly conditional | claude-sonnet-5-5 | 0.10-0.50 | as Opus, less often | | |
| L6 doubly conditional | claude-haiku-5-5 | 0.00-0.20 | components only | | |
| stress L1 controls | gpt-6.1-terra | 0.50-1.00 | loud plain marks ( and " survive crowding | | |
| stress L1 controls | claude-opus-5-5 | 0.80-1.00 | Exp D 10/10 | | |
| stress L1 controls | claude-sonnet-5-5 | 0.80-1.00 | Exp D 10/10 | | |
| stress L1 controls | claude-haiku-5-5 | 0.30-0.90 | Exp D parenthetical 5/5, quote 1/5 | | |
| stress bridge (P.S. question, sign-off "!") | gpt-6.1-terra | 0.40-0.90 | Exp D 10/10, crowding as above | | |
| stress bridge | claude-opus-5-5 | 0.70-1.00 | Exp D 10/10 | | |
| stress bridge | claude-sonnet-5-5 | 0.70-1.00 | Exp D 10/10 | | |
| stress bridge | claude-haiku-5-5 | 0.10-0.50 | Exp D 3/10 | | |
| stress multi (P.S. question AND "Oh!", ordering) | gpt-6.1-terra | 0.10-0.60 | the question-and-"Oh!" cue is a two-condition cue like L6 (each part alone 0.75); ordering needs a multi-line regex | | |
| stress multi | claude-opus-5-5 | 0.30-0.80 | ordering is a visible layout fact once noticed; the two-condition P.S. cue is as hard as L6 | | |
| stress multi | claude-sonnet-5-5 | 0.20-0.80 | as Opus | | |
| stress multi | claude-haiku-5-5 | 0.00-0.30 | weak on line-specific regexes and on combining conditions | | |
| calibration plain | gpt-6.1-terra | 0.50-0.95 | shipped plain cues are loud properties, but share the list with 7 others | | |
| calibration plain | claude-opus-5-5 | 0.85-1.00 | main study named 128/128 with tools; listing 17-20 covers the aligned set | | |
| calibration plain | claude-sonnet-5-5 | 0.85-1.00 | as Opus | | |
| calibration plain | claude-haiku-5-5 | 0.50-0.90 | Exp D 13 plain cues: Haiku about 0.8 with one aligned | | |
| calibration nested P.S. question | gpt-6.1-terra | 0.40-0.90 | Exp D 5/5 alone; main study 23/32 with tools | | |
| calibration nested P.S. question | claude-opus-5-5 | 0.60-1.00 | Exp D 5/5 | | |
| calibration nested P.S. question | claude-sonnet-5-5 | 0.60-1.00 | Exp D 5/5 | | |
| calibration nested P.S. question | claude-haiku-5-5 | 0.10-0.60 | Exp D 3/5 | | |
| calibration trap (reported apart) | gpt-6.1-terra | 0.50-1.00 | trap main cues are plain templated properties; the trap lies in testing, not listing | | |
| calibration trap | claude-opus-5-5 | 0.80-1.00 | as plain | | |
| calibration trap | claude-sonnet-5-5 | 0.80-1.00 | as plain | | |
| calibration trap | claude-haiku-5-5 | 0.40-0.90 | as plain | | |
| negative control | every model | 0.00-0.05 | a coin property shows |corr| < 0.2 in 128 notes; listing it at BA >= 0.8 needs a regex for it by chance | | |

## Trend over levels (L1 = 1 ... L6 = 6, Spearman, exploratory)

| model | Claude's draft (edit freely) | Claude's reasoning (one line) | user: direction | user: note |
|---|---|---|---|---|
| gpt-6.1-terra | decreasing (rho < 0) | flat across L1-L4 at a level set by candidate count, then a drop at L5-L6 | | |
| claude-opus-5-5 | decreasing (rho < 0) | near 1 to L4, drop at L5-L6 where a conjunction must be formed | | |
| claude-sonnet-5-5 | decreasing (rho < 0) | as Opus | | |
| claude-haiku-5-5 | decreasing (rho < 0) | already lower from L3 (position) and L4 (children) | | |
| pooled | decreasing; the main drop between L4 and L5 | conjunctions are the one level where naming a visible property is not enough | | |

## Distractor effect (Exp D 1 aligned vs here 8 aligned, same cue)

| model | Claude's draft (edit freely) | Claude's reasoning (one line) | user | user: note |
|---|---|---|---|---|
| gpt-6.1-terra | drop of 0.1-0.5 | few candidates per answer: crowding hits it most | | |
| claude-opus-5-5 | drop of 0.0-0.2 | lists enough candidates to cover all 8 | | |
| claude-sonnet-5-5 | drop of 0.0-0.2 | as Opus | | |
| claude-haiku-5-5 | drop of 0.1-0.4 | more invalid or off-target candidates in Exp D | | |
