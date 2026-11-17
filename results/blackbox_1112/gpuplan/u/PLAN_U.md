# U: decidable slots in the agent-visible unit, and a judge-visible rule (round 6; post hoc; $0)

Plan: `paper_loop/gpu_plan/GPU_PROMPT_6.md` (branch `claude/nifty-wozniak-vunb6z`), answering `REVIEW_V9.md` issues 1
and 5. Written on 17 Nov before any gap-unit decidable-slot number was computed. Everything here is **post hoc**: the
idea of decidability came after the ladder results (round 4 D), and the units and rules below come after D's
results were read.

## Units
- **Topic unit (D, reference):** the pair reading divided by the probe's topic coefficient T, which only the grader
  has. Reproduces D.
- **Agent-visible unit (primary here):** divided by the probe's class-mean gap on the public sample (mean sample
  logit of label 1 minus label 0), which the agent can compute from the free sample scores. The verifier already
  stores every slot in this unit (`keyless_verifier.py`, `gap|<run>` in its private slots file).

## Decidable (as D's rule, in the gap unit)
A named cue is decidable when V1 or V3 confirms it or refutes it. A `none` is decidable when V3 confirms it (every
aligned candidate isolated, below 0.15) or V1 refutes it (an isolated candidate at or above 0.15). The script's
verdict is its credit.

## Judge-visible decidable (new; stricter)
A gap-unit decidable slot counts as judge-visible when both of these hold:
1. **Pairs visible.** Rerun the rule using only the clean pairs whose two logits are both printed in the L2 prompt
   the judge saw, after any length cut, matched at 3 or 4 decimals. A sample-note logit counts only when it is
   printed. The slot must still be decided, with the same verdict.
2. **Unit visible.** The probe's class-mean gap is printed in that prompt (3 or 4 decimals), or at least 90% of the
   probe's sample-note logits are.

**Pairs-visible only** (condition 1 alone) is reported as a looser variant.

## Measures (hard slots; per set: set A, Luna, main study; pooled)
- **Coverage:** how many slots are decidable, and their make-up (passes, wrong cues, wrong `none`; confirmed vs
  refuted).
- **The judge vs the script at each level the box has:** report (L0), log (L1), transcript (L2), with transcript +
  key (L3_2) as a reference. For each: κ, balanced accuracy, false credit (wrong cues, wrong `none`) and false blame,
  with item- and run-bootstrap 95% intervals (10,000 draws, seed 1116).
- **Tests.** Primary: item level. An exact sign-flip over items of the per-item accuracy difference (judge minus
  script), plus a sign test, run two ways:
  - with the item as the cluster;
  - pooled with (set, item) as the cluster.

  Secondary: exact McNemar over runs.

## Paper sentence (rule fixed now; pooled, L2 vs script, gap-unit decidable slots)
- **"Still trails"** if the script's balanced accuracy exceeds the judge's by at least 0.10 and the primary item-level
  test (pooled, (set, item) clusters) gives p < 0.05.
- **"Similar"** if the gap is under 0.10. The sentence is then: "the script's advantage depends on a scale the judge
  never sees; in the agent's own unit they are similar".
- **"Reported as is"** otherwise: a gap of 0.10 or more that the item-level test does not support. The sentence then
  gives both numbers and the p value.

The judge-visible slots get the same three sentences, computed on those slots.
