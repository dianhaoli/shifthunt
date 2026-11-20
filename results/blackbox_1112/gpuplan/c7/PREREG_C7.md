# Pre-registration: C7 slim, a second judge family and a skeptical-negatives rubric (before any C7 call)

Status: frozen by `PREREG_HASH` here. Design `paper_loop/brainstorm/design_C7.md` (slim form, plan "if time",
approved 13 Nov) with the critic's required changes. Code `scripts/judge_panel.py`; inputs in `inputs.json`.
Labels: [pre-reg C7].

## Cells (run set R: the 214 L0 runs + Luna's 60 counted runs = 274)

| | frozen prompt F | skeptical-negatives prompt K |
|---|---|---|
| Terra | exists (L0 + C8) | TK, 274 calls |
| Luna (`gpt-6-luna`) | LF, 274 | LK, 274 |
| Haiku (`claude-haiku-5-5`) | HF: C6's H0 on set A (132, byte-identical prompts) + 142 new | HK, 274 |

K = F with one paragraph after the confidence sentence (text and sha256 in `scripts/judge_panel.py` /
`inputs.json`). **K is a failure-mode-informed rubric, written after J3 was known; it is an upper bound on what a
generic rubric can do** (critic 4). Sonnet (S-F) is not run (the plan's Claude total is $5; the cell needs about
$4). Orders: seeded shuffles "c7-1113-terra" and "c7-1113-small". Guards: OpenAI $6 (Terra part, shared with C17
R2), $1.2 (Luna part); Anthropic $0.8.

## Metrics and hypotheses (written before any call)

- **Primary metric: within-run `none` AUROC** (critic 1): in runs whose report has both a correct `none` (null probe)
  and a wrong `none` (planted probe), the share of such pairs where the judge gives the correct `none` the higher
  p_correct (ties 0.5). Holds agent, harness, item and report fixed. Run-cluster bootstrap 95% (5,000, seed 1115).
- **P1:** within-run `none` AUROC < 0.65 in every primary cell (TF, TK, LF, LK, HF, HK), on the point estimate; the
  equivalence reading is an upper bound < 0.75. A point estimate alone does not "confirm" a null.
- **P2 (per judge model, K vs F):** discrimination gain if paired ΔAUROC (K − F) ≥ 0.10 with a bootstrap lower
  bound > 0; threshold-only if |ΔFPR on wrong `none`| ≥ 0.20 without a gain; inert otherwise.
- **P3 (Claim 2 replicates across judge models):** in each frozen cell (TF, LF, HF), within-run `none` AUROC < 0.65
  and named-answer hard-slot κ < 0.40. Hard-slot κ and false credit are reported beside the answer-type rule
  (κ ≈ 0.72) and are never read alone.
- P4 (self-preference), P5, P6 are cut (critic 6): per-slot verdicts go to C17/C19 instead.
