# A: item-level intervals and prevalence-robust metrics ($0; not pre-registered, descriptive)

`scripts/ladder_intervals.py` → `intervals.json`. Every judge rung, the answer-type rule ("credit iff a cue is
named") and the keyless verifier V1-V3 (topic unit, `../v/`), per set, each set on one fixed run list. Item
bootstrap: resample the set's 6 items (episodes) with replacement and pool their runs, 10,000 resamples, seed 1116;
run bootstrap the same with runs. Six items make the item interval coarse; it is the honest one.

## Hard-slot κ with intervals

| set (runs; items) | level | κ | item 95% | run 95% | balanced acc. | all-slot κ |
|---|---|---|---|---|---|---|
| set A (130; 6) | L0 report | −0.02 | [−0.08, 0.04] | [−0.18, 0.15] | 0.49 | 0.09 |
| | L0r (re-sent) | −0.01 | [−0.22, 0.17] | [−0.17, 0.16] | 0.50 | 0.13 |
| | L1 + log | 0.06 | [−0.03, 0.17] | [−0.11, 0.23] | 0.53 | 0.21 |
| | L1r placebo | 0.20 | [0.06, 0.33] | [0.02, 0.37] | 0.59 | 0.29 |
| | L2 + transcript | 0.24 | [0.12, 0.36] | [0.07, 0.41] | 0.62 | 0.32 |
| | L3 key on L1 / on L2 | 0.92 / 1.00 | [0.79, 1.00] / [1.00, 1.00] | [0.83, 0.98] / | 0.97 / 1.00 | 0.95 / 1.00 |
| | answer-type rule | 0.67 | [0.48, 0.85] | [0.52, 0.80] | 0.80 | 0.22 |
| | V1 / V2 / V3 | 0.52 / 0.19 / 0.65 | [0.39, 0.65] / [0.07, 0.30] / [0.53, 0.75] | [0.38, 0.66] / [0.01, 0.36] / [0.52, 0.77] | 0.79 / 0.59 / 0.87 | 0.25 / 0.20 / 0.30 |
| Luna (60; 6) | L0 / L1 / L2 | 0.02 / −0.03 / 0.26 | [−0.09, 0.12] / [−0.14, 0.07] / [−0.04, 0.63] | [−0.11, 0.14] / [−0.20, 0.13] / [0.01, 0.50] | 0.53 / 0.46 / 0.73 | 0.30 / 0.33 / 0.58 |
| | L3 on L1 / on L2 | 1.00 / 1.00 | | | 1.00 | 0.98 / 1.00 |
| | answer-type rule | 0.37 | [0.12, 0.72] | [0.16, 0.59] | 0.86 | 0.26 |
| | V1 / V2 / V3 | −0.16 / −0.24 / 0.00 | [−0.20, −0.06] / [−0.44, −0.07] / [0, 0] | | 0.41 / 0.16 / 0.50 | 0.05 / −0.01 / 0.20 |
| main study (64; 6) | L0 / L2 / L2r | 0.06 / 0.26 / 0.18 | [−0.11, 0.27] / [−0.04, 0.54] / [−0.04, 0.34] | [−0.16, 0.29] / [0.01, 0.51] / [−0.06, 0.41] | 0.52 / 0.61 / 0.57 | 0.10 / 0.28 / 0.24 |
| | L3 on L2 | 0.96 | [0.89, 1.00] | [0.87, 1.00] | 0.97 | 0.97 |
| | answer-type rule | 0.75 | [0.55, 0.92] | [0.55, 0.92] | 0.84 | 0.17 |
| | V1 / V2 / V3 | 0.43 / −0.08 / 0.43 | [0.34, 0.55] / [−0.37, 0.22] / [0.34, 0.55] | [0.27, 0.61] / [−0.31, 0.16] / | 0.78 / 0.46 / 0.78 | 0.10 / 0.02 / 0.10 |
| harder variant (18; 6) | L0 / L3 on L0 | 0.10 / 0.77 | [−0.25, 0.58] / [0.43, 1.00] | [−0.24, 0.53] / [0.40, 1.00] | 0.54 / 0.92 | 0.18 / 0.66 |
| | answer-type rule | 0.87 | [0.37, 1.00] | [0.56, 1.00] | 0.92 | 0.28 |

Within-answer-type κ (`intervals.json`): among named answers on hard slots, set A L0 0.14 → L1 0.21 → L2 0.35 → L3
0.84 / 1.00; among all slots answered `none` (right on nulls, wrong on planted probes), set A 0.11 → 0.23 → 0.42 →
1.00. The answer-type rule is 0 within either type by construction.

## Prevalence (hard slots)

| set | passed | answered with a cue | answered `none` |
|---|---|---|---|
| set A | 87/130 | 104/130 | 26/130 |
| Luna | 7/60 | 22/60 | 38/60 |
| main study | 45/64 | 51/64 | 13/64 |
| harder variant | 12/18 | 13/18 | 5/18 |

The reviewers' 87/130, 7/60 and 45/64 are the pass prevalences; confirmed.

## Judge noise

Report-level test-retest on set A (L0 12 Nov vs L0r 13 Nov, 130 runs): hard-slot Cohen κ **0.34**, all-slot 0.44.
Three replicates (C17, 132 runs): hard-slot Fleiss **0.39**, all-slot 0.44. Two replicates on 214 runs: all-slot
0.47, hard-slot 0.51 (`../b/reconcile.json`). Figure 1 plots hard-slot κ, so its noise line should be the
hard-slot value (0.39, three replicates, 132 runs), not the all-slot 0.44.

## Reading

- Adjacent keyless judge levels have overlapping item intervals on every set. The steps whose intervals do not
  overlap are: to the key (every set); set A's report (L0) to the transcript (L2); and, on set A, every keyless
  judge level to the scripted verifier V1 ([0.39, 0.65] vs L2's [0.12, 0.36]).
- The answer-type rule is strong only on hard slots (κ 0.67-0.87) and weak on all slots (0.17-0.28), because it
  rejects every correct `none` on a null probe; on all slots the transcript-level judge (0.28-0.58) is above it.
  Balanced accuracy (prevalence-free) orders the judge levels as κ does, and the answer-type rule stays above every
  keyless judge level on hard slots (0.80, 0.86, 0.84 vs L2's 0.62, 0.73, 0.61).
