# Reviews of PAPER_V9: summary for the author

Full texts: `reviews_v9/`. Portal closes 20 Nov, 06:00 UTC; aim to submit on 19 Nov.

## 1. Dev-panel scores

| Criterion | R1 | R2 | R3 | V9 | V8 | V7 | V6 | V5 | V4 |
|---|---|---|---|---|---|---|---|---|---|
| C1 Relevance | 5 | 4 | 5 | 4.67 | 5.00 | 4.67 | 4.00 | 4.67 | 4.00 |
| C2 Soundness | 3 | 3 | 3 | 3.00 | 3.00 | 3.33 | 3.00 | 3.33 | 3.00 |
| C3 Significance | 3 | 3 | 3 | 3.00 | 3.00 | 3.33 | 3.00 | 3.00 | 3.00 |
| C4 Originality | 4 | 4 | 3 | 3.67 | 4.00 | 4.00 | 3.33 | 4.00 | 3.33 |
| C5 Clarity / length | 3 | 2 | 3 | 2.67 | 2.33 | 3.00 | 3.00 | 2.00 | 2.00 |
| C6 Reproducibility | 4 | 4 | 4 | 4.00 | 3.67 | 4.00 | 4.00 | 3.67 | 4.00 |
| **Overall** | 6 | 6 | 6 | **6.00** | 5.67 | 6.67 | 5.67 | 6.33 | 5.67 |
| Confidence | 4 | 4 | 4 | 4.00 | 4.00 | 4.00 | 3.67 | 4.00 | 4.00 |

V9 is a third of a point above V8 and below V7, within noise. What changed: V8's main objection (the judge could not abstain) is answered, and the criticism has moved to the new decidable-slot analysis.

## 2. Held-out decisions

| Reviewer | Decision | Conf. |
|---|---|---|
| G1 | accept as poster; a talk if §4.2 holds in the agent-visible unit | 4 |
| G2 | 6/10, marginal accept | 3 |
| G3 | weak accept | 3 |

## 3. Verdict

**Likely decision: accept as a poster.** All six lean to accept; none recommends rejection. They praise the executed grade, the honest status labels and the fit to the call. All six raise one main objection: the script beats the judge with a scale the judge never sees, on slots its own rule selects. One rerun on existing data answers it. Changes made now will not be checked by a fresh panel.

## 4. Issues raised under two or more rubrics

The dev panel counts as one rubric. Fix types: **W** writing, **A** existing data, **N** new runs or calls.

| # | Issue | Raised by | Fix | By 19 Nov? |
|---|---|---|---|---|
| 1 | Judge vs script is unfair: private unit, self-selected slots. In the agent-visible unit the script's κ is 0.16, below the judge's 0.24 | Dev, G1, G2, G3 | A: rerun decidability and Table 2a in that unit; W: grader-unit script as upper bound | Yes |
| 2 | "72 of 77 undecidable" follows from 8 queries against 8 candidates | Dev, G1, G2 | W: state it as a design property; A: blind-64 runs; N: larger-budget arm | W, A yes; N no |
| 3 | The abstaining judge is arguably right; it never says "fail" and abstains on 50 of 64 confirmed passes | Dev, G1, G2 | A: selective accuracy vs coverage, sample reasons; W: reframe | Yes |
| 4 | One judge family, also an agent under test; closed candidate set; general prescriptions | Dev, G1, G2 | W: scope claims; N: second family on ladder, key and leniency probe | W yes; N tight |
| 5 | Six items; run-level McNemar ignores clustering | Dev, G2, G3 | W: item-level tests primary; N: more items | W yes; N no |
| 6 | Terra vs Luna not compute-matched; reason only in §8 and appendix | Dev, G1, G2, G3 | W: one body sentence | Yes |
| 7 | Test-retest κ 0.39, one sample per level, no voting | Dev, G1, G2 | W; N: set-A majority vote | W yes; N tight |
| 8 | "Would hide the agent comparison": interval includes zero, 13/36 exploratory | Dev, G2 | W | Yes |
| 9 | Dense text, coined terms, population zoo, page fit | Dev, G1, G2, G3 | W: glossary, one worked run, body footnotes for 9/17 vs 7/17 and 196 vs 214 | Yes |
| 10 | §5 on agents distracts | Dev, G2 | W: compress | Yes |

Single-rubric factual errors: Figure 1's caption promises a missing main-study hollow star (κ 0.18) (G1); §4.4's p = 0.004 does not name its step (R3).

## 5. Overstated claims (quoted)

- "Where the log does decide (post hoc), the judge with the full transcript reaches balanced accuracy 0.75, against 0.97 for a script reading the log on the grader's scale" and "Where the log decides, the judge stays well below a script" (all six)
- "Absences cannot be checked" and "A `none` can be checked only if every candidate was tested, and here that almost never happened" (R1–R3, G1, G2)
- "Negative verdicts need execution, a key, or evidence that every candidate was tested" (R1–R3)
- "With nothing to check, chance is the best any reader can do" (R1, R3)
- "A consistency check would not reveal these errors" and "The judge is consistent with itself, not with the grade" (R1, R3, G1)
- "ShiftHunt's executed grade resists scripted cheaters, so it can serve as ground truth" (R1, R3)
- "Allowed to abstain, the judge stops crediting failures" (R1, R2)
- "Without it, its errors would hide our agent comparison" (R2, G2)
- "a report-reading judge cannot certify a 'nothing found'" (R2)

## 6. Final submission checklist

1. **Agent-visible rerun (issue 1).** Lead §4.2 and the abstract with it. This is R1's and R3's +1 change and G1's condition for a talk.
2. **Claims pass.** Fix every quote in section 5.
3. **Issues 2, 3, 5, 6, 8.** Apply the W and A fixes.
4. **Factual fixes.** Figure 1 star and caption, the p = 0.004 step, and the footnotes in issue 9.
5. **Scope and readability.** Add the glossary, compress §5, and check the page count in the AAAI template.
6. **Optional, only if done by 18 Nov.** The second judge family and the set-A vote. Otherwise name them as the key open tests.
7. **Before upload.** Regenerate the figures (still named `_v8`) from the final numbers, add the anonymised release link if possible, and submit on 19 Nov.
