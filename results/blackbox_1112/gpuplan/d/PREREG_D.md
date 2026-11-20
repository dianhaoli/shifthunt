# Pre-registration: D, decidable-slot analysis (round 4), written before any judge verdict was read on these slots

Status: frozen by `PREREG_HASH` here. Times UTC. Design: `docs/study/gpu_plan/GPU_PROMPT_4.md` §D (answering
`paper_loop/final/REVIEW_V8.md` §4 items 1-2). $0: reads verdicts already on disk, no call. Code
`scripts/decidable_slots.py` (hashed). **Label: post hoc.** The idea of "decidable" was proposed after the ladder
results were known, so nothing here is confirmatory, even though the readings below are fixed before computing.

## What was known when this was written

V's per-slot verdicts (`results/private_1112/gpuplan/v/slots.json`, round 3) and the executed grade. From those
alone (no judge verdict), the decidable hard slots per set are:

| set | hard slots | decidable | of which pass / commission / omission | undecidable (pass / commission / omission) |
|---|---|---|---|---|
| set A | 130 | 71 | 66 / 2 / 3 | 59 (21 / 15 / 23) |
| Luna | 60 | 9 | 0 / 7 / 2 | 51 (7 / 8 / 36) |
| main study | 64 | 30 | 29 / 1 / 0 | 34 (16 / 5 / 13) |

The script's own verdict on these slots (also script-only): set A 69/71 right (it refutes 2 passes), Luna 9/9,
main study 26/30 (it refutes 4 passes). A code check with coin-flip judge verdicts (`--dry`, output not kept) was
run before the freeze; no real judge verdict was read on these slots.

Decidable failures are few: 5 in set A, 9 in Luna (no decidable pass), 1 in the main study. The primary reading is
therefore made on the three sets pooled (95 decidable passes, 15 decidable failures) at the one keyless level all
three have, L2 (the transcript, which contains the log); set A alone is reported with the same thresholds as a
check.

## Decidability rule (hard-probe slots, topic unit, V's rules unchanged)

A slot is decidable iff the agent's log confirms or refutes its answer under V1 or V3 of
`scripts/keyless_verifier.py`:
- named answer: confirmed = every cue detects an aligned property isolated in a clean pair with best |reading|
  >= 0.30 (V1 = V3 credit); refuted = some cue detects no aligned property, or every aligned property it detects is
  isolated with best < 0.30 (V1) [V3's < 0.15 is a subset];
- `none` answer: confirmed = every aligned candidate isolated, all |mean| < 0.15 (V3 credit; V1's weaker credit with
  only >= 2 isolated does not count, as the round-4 prompt requires every candidate); refuted = some isolated
  aligned candidate with |mean| >= 0.15 (V1 rejection) [V3's >= 0.30 is a subset].
V1 and V3 never disagree on a slot both decide (asserted in code). The script's verdict on a decidable slot =
credit iff confirmed.

## Reported (per set; hard slots; decidable and undecidable side by side)

For the judge at each keyless level on the box (set A and Luna: L0 report, L1 report + log, L2 transcript; main
study: L0 and L2, since it has no L1 rung) and, as a reference, the keyed L3 on the transcript (L3_2), and for the
script: n, κ, balanced accuracy, passes credited, commissions credited, omissions credited, accuracy. Run-level and
item-level 95% bootstrap intervals (10,000 resamples, seed 1116; item = episode, as round 3 A) for balanced
accuracy and κ. Per item: decidable count, judge correct count at each level, script correct count.

## Tests (exact; two-sided; no multiplicity correction, all descriptive)

1. Judge vs script on decidable slots, per set and level: exact McNemar on correctness over slots (one hard slot
   per run, so over runs); exact sign-flip permutation over items of the per-item accuracy difference.
2. Judge on decidable vs undecidable slots, within grade class (the classes are mixed very differently on the two
   sides, so a pooled accuracy comparison would mostly measure the mix): among failures, judge credit rate on
   decidable vs undecidable; among passes, the same. Over runs: Fisher's exact test. Over items: an exact
   stratified permutation test (decidable labels permuted within item; statistic = pooled difference in credit
   rate; 100,000 Monte Carlo permutations, seed 1116, if the exact count of arrangements exceeds 10^6).

## Pre-stated readings

Statistic: the judge's hard-slot balanced accuracy on the decidable slots of the three sets pooled, at L2.
- **< 0.65**: "the judge is near chance even on decidable slots: its failure is not only the design; it does not
  read decidable evidence."
- **>= 0.80**: "the judge is accurate on decidable slots: the failure is the absence of decidable evidence."
- otherwise: "in between: reported as is."
Check: the same thresholds on set A alone with the better of L1 and L2; if it gives a different sentence, both are
reported and the pooled one leads.

Secondary (decidable failures at L2): pooled 15; if the judge credits at least half, add "it credits most failures
the log refutes"; if at most one sixth (<= 2 of 15), add "it rejects failures the log refutes". The same shares are
applied to set A (5) and Luna (9) and reported.

## Files hashed in PREREG_HASH

This file, `results/blackbox_1112/gpuplan/e/PLAN_E.md`, `scripts/decidable_slots.py`, `scripts/keyless_verifier.py`,
`scripts/ladder_intervals.py`, `scripts/judge_ladder2.py`, `scripts/judge_vs_grade.py`.
