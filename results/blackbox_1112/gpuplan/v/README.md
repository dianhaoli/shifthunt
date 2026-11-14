# V: a keyless scripted verifier (pre-registered; `PREREG_V.md`, hash in `PREREG_HASH`)

A fixed script grades each answer slot from the agent's own exact-query log: no answer key, no hard-probe identity,
no LLM. It reads clean isolating pairs (an agent text and the sample note it was edited from, or two agent edits,
same topic, differing in exactly one property), in the contract's unit (the probe's topic coefficient). V1 strict,
V2 lenient, V3 identifiability ceiling (rules in the prereg). `scripts/keyless_verifier.py run` (14 Nov
20:38-21:01Z) and `report` → `verifier.json`; intervals from item A (`../a/intervals.json`, item bootstrap: 6 items,
10,000 resamples, seed 1116). $0.

## Runs and deviations

Set A 130, Luna 60, main study 64; every run had a readable log. Main study: replay-recovered texts; 34 of 256 slots
lost at least one text whose logit was not recovered (kept, marked). No deviation from the prereg in the run; the
prereg lists its deviations from the plan (V3's named side; the main study has no L1; the unit).

## Results (hard slot; κ vs the executed grade, item-bootstrap 95%)

| set | rule | κ [item 95%] | balanced acc. | commissions credited | omissions credited | passes blamed | null-slot `none` blamed | hard slots decided (`none` slots) |
|---|---|---|---|---|---|---|---|---|
| **set A (130)** | **V1** | **0.52** [0.39, 0.65] | 0.79 | 0/17 | 7/26 | 23/87 | 86/125 | 78/130 (10/26) |
| | V2 | 0.19 [0.07, 0.30] | 0.59 | 1/17 | 23/26 | 22/87 | 2/125 | 84/130 (16/26) |
| | V3 | 0.65 [0.53, 0.75] | 0.87 | 0/17 | 0/26 | 23/87 | 106/125 | 64/130 (**0/26**) |
| | judge L1 (log) | 0.06 [−0.03, 0.17] | 0.53 | 7/17 | 21/26 | 25/87 | 8/125 | |
| | judge L2 (transcript) | 0.24 [0.12, 0.36] | 0.62 | 3/17 | 17/26 | 25/87 | 7/125 | |
| | judge L3 (key) | 0.92 / 1.00 | 0.97 / 1.00 | 0/17 | 0/26 | 5/87 / 0/87 | 0/125 | |
| | answer-type rule | 0.67 [0.48, 0.85] | 0.80 | 17/17 | 0/26 | 0/87 | | |
| **Luna (60)** | V1 | −0.16 [−0.20, −0.06] | 0.41 | 0/15 | 10/38 | 7/7 | 45/54 | 19/60 (12/38) |
| | V2 | −0.24 [−0.44, −0.07] | 0.16 | 0/15 | 36/38 | 7/7 | 0/54 | 28/60 (21/38) |
| | V3 | 0.00 | 0.50 | 0/15 | 0/38 | 7/7 | 54/54 | 6/60 (0/38) |
| | judge L1 / L2 | −0.03 / 0.26 [−0.04, 0.63] | 0.46 / 0.73 | 6/15, 4/15 | 21/38, 10/38 | 4/7, 2/7 | 18/54, 16/54 | |
| | judge L3 | 1.00 | 1.00 | 0/15 | 0/38 | 0/7 | 0/54 | |
| | answer-type rule | 0.37 [0.12, 0.72] | 0.86 | 15/15 | 0/38 | 0/7 | | |
| **main study (64)** | **V1** | **0.43** [0.34, 0.55] | 0.78 | 0/6 | 0/13 | 20/45 | 64/64 | 30/64 (0/13) |
| | V2 | −0.08 [−0.37, 0.22] | 0.46 | 0/6 | 13/13 | 18/45 | 0/64 | 35/64 (5/13) |
| | V3 | 0.43 [0.34, 0.55] | 0.78 | 0/6 | 0/13 | 20/45 | 64/64 | 28/64 (0/13) |
| | judge L0 / L2 | 0.06 / 0.26 [−0.04, 0.54] | 0.52 / 0.61 | 3/6, 5/6 | 13/13, 8/13 | 5/45, 4/45 | 0/64, 1/64 | |
| | judge L3 | 0.96 | 0.97 | 1/6 | 0/13 | 0/45 | 0/64 | |
| | answer-type rule | 0.75 [0.55, 0.92] | 0.84 | 6/6 | 0/13 | 0/45 | | |

**Sensitivity, agent-visible unit** (the public sample's class gap, 1.4-2.1 times the topic unit, so readings are
smaller): V1 κ 0.16 (set A), −0.17 (Luna), 0.18 (main study); V2 0.08, −0.25, −0.13; V3 0.30, 0.00, 0.18. False
blame rises (set A V1: 51/87); false credit stays near zero for commissions.

**Post hoc diagnostics** (`scripts/keyless_verifier_diag.py` → `diagnostics.json`). Where V1 blames passes (set A,
23): in 11 the agent isolated no aligned candidate on the hard probe in a clean pair (10 sent texts that formed no
clean pair, 1 sent none); in 12 it isolated something, but not the named cue above 0.30. Luna: 5 of its 7 passes
have no clean isolating pair. Wrong `none` answers on hard probes by how many of the 8 aligned candidates were
isolated: set A 0 (10 slots), 1 (5), 2 (7), 5 (1), 7 (2), 8 (1); Luna 0-2 in all 38; main study 0-2 in all 13.

## Pre-stated reading

Set A V1 κ = 0.52: neither ≥ 0.60 nor < 0.40, so **"in between: reported as is"** (`verifier.json` `reading`).

What the numbers say, within that:
- **A fixed script reading the exact-query log agrees with the executed grade better than the LLM judge given the
  same log or the whole transcript** (set A 0.52 vs 0.06 and 0.24; main study 0.43 vs 0.26; on set A the item
  intervals of V1 and of the judge's L1 and L2 do not overlap). It does so mainly by never crediting a wrong named cue (0 on every set, against
  7/17 and 3/17 for the judge) and by crediting far fewer wrong `none` answers on set A (7/26 vs 21/26 and 17/26).
- **Commissions are identifiable from the log; omissions are not.** V3 decides none of the wrong `none` answers on a
  hard probe in any set (0/26, 0/38, 0/13): in 76 of these 77 the agent had not isolated every aligned candidate,
  and in the remaining one a candidate read in the contract gap, so a `none` can be neither confirmed nor refuted
  from the log.
- **The log confirms few correct answers.** The strict verifier blames a quarter of set A's passes and most correct
  `none` answers on null probes, because agents often do not leave a clean single-property test of what they
  claim; on Luna's runs it has almost nothing to read (κ −0.16).
- So the paper's sentence "the judge fails for lack of ground truth, which the agent's materials do not supply" is
  half right: the materials supply enough to reject wrong named cues, which the LLM judge does not fully use, and
  not enough to judge a `none`, which no reader of the log can.
