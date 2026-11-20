# C7 slim: a second and third judge family and a sceptical-negatives rubric (pre-registered; `PREREG_C7.md`)

Driver `scripts/judge_panel.py` (`run --part small|terra`, `analyse` → `c7.json`). Run set R: the 214 L0 runs plus
Luna's 60 counted runs (274). Cells: judge model (Terra T, Luna L, Haiku H) x prompt (frozen F, sceptical-negatives
K). TF is the existing L0 + C8 verdicts; HF reuses C6's H0 on set A (byte-identical prompts) plus 142 new calls.

## Calls and spend

13 Nov 08:22-19:18Z. Terra TK 274 ($2.27), Luna LF + LK 548 ($0.69), Haiku HF 142 + HK 274 ($0.39 Anthropic).
2 Haiku calls returned http_503 and were not re-sent (HF 273 runs, HK 272). The Terra part shared its guard with
C17's R2 batch (interleaved). No other deviation.

## Results

| cell | within-run `none` AUROC [95%] | pairs | hard κ | κ among named | hard false credit | `none` credited when wrong (FPR) | `none` credited when right (TPR) |
|---|---|---|---|---|---|---|---|
| TF (Terra, frozen) | 0.58 [0.52, 0.64] | 146 | 0.05 | 0.17 | 88/121 | 106/148 | 247/263 |
| TK (Terra, sceptical) | 0.48 [0.46, 0.50] | 146 | 0.55 | 0.19 | 22/121 | 3/148 | 6/263 |
| LF (Luna, frozen) | 0.51 [0.45, 0.57] | 146 | −0.33 | 0.02 | 59/121 | 84/148 | 222/263 |
| LK (Luna, sceptical) | 0.51 [0.47, 0.55] | 146 | 0.25 | 0.08 | 9/121 | 1/148 | 6/263 |
| HF (Haiku, frozen) | 0.58 [0.53, 0.63] | 146 | −0.09 | 0.01 | 18/121 | 24/148 | 100/262 |
| HK (Haiku, sceptical) | 0.54 [0.49, 0.59] | 144 | 0.02 | 0.01 | 1/120 | 2/146 | 4/261 |

| hypothesis | result | label |
|---|---|---|
| **P1** within-run `none` AUROC < 0.65 in every cell | 0.48-0.58 in all six (upper bounds ≤ 0.64) | holds |
| **P2** K vs F per judge model | Terra ΔAUROC −0.10 [lower −0.16], ΔFPR −0.70; Luna −0.00, ΔFPR −0.56; Haiku −0.03, ΔFPR −0.15 | Terra and Luna **threshold-only**; Haiku inert |
| **P3** Claim 2 replicates across judge models (frozen cells: AUROC < 0.65 and named κ < 0.40) | TF, LF, HF all | holds |

## Reading

No judge model, with either prompt, tells a correct `none` from a wrong `none` in the same report (AUROC 0.48-0.58).
The sceptical rubric, written after the `none` leniency was known, does not add discrimination: it moves the
threshold, so Terra and Luna now reject almost every `none`, right or wrong (`none` credited when right: 247/263 →
6/263 for Terra). The sceptical Terra cell's hard κ of 0.55 is that threshold at work: on the hard slot most failures
are `none`, so rejecting every `none` approaches the answer-type rule ("credit iff a cue is named", κ 0.67-0.72), and
it costs every correct `none` on the null probes. K is a failure-informed rubric: an upper bound on what a generic
rubric would do.
