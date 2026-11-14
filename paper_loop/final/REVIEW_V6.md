# Reviews of PAPER_V6: summary for the author

Three blind reviews used the V4/V5 rubric and reviewer setups, plus three order-balanced V5-vs-V6 head-to-heads. Full texts: `reviews_v6/`, `compare_v5_v6/`.

## 1. Scores

| Criterion | R1 | R2 | R3 | V6 mean | V5 mean | V4 mean |
|---|---|---|---|---|---|---|
| C1 Relevance | 4 | 4 | 4 | 4.00 | 4.67 | 4.00 |
| C2 Soundness | 3 | 3 | 3 | 3.00 | 3.33 | 3.00 |
| C3 Significance | 3 | 3 | 3 | 3.00 | 3.00 | 3.00 |
| C4 Originality | 4 | 3 | 3 | 3.33 | 4.00 | 3.33 |
| C5 Clarity / length | 3 | 3 | 3 | **3.00** | 2.00 | 2.00 |
| C6 Reproducibility | 4 | 4 | 4 | 4.00 | 3.67 | 4.00 |
| **Overall** | 6 | 5 | 6 | **5.67** | 6.33 | 5.67 |
| Confidence | 4 | 3 | 4 | 3.67 | 4.00 | 4.00 |

Clarity left 2/5 for the first time. Overall fell back to V4's level.

## 2. Head-to-heads (V5 vs V6)

| Reader | Winner | Margin | V5 | V6 |
|---|---|---|---|---|
| H1 | V6 | clear | 5.5 | 6.5 |
| H2 | V6 | clear | 5.5 | 6.5 |
| H3 (Sonnet) | V6 | clear | 6.0 | 6.8 |

All three prefer V6 by about one point, for the answer-key ladder, the omission/commission mechanism, a single thesis that fits the call, and readability. All three say V5 did better with the Box 2 recipe, the in-body consequences of judge error (13/36 leaderboard pairs flip, PPI worth 0) and cost per pass.

## 3. Verdict

**Likely decision: borderline accept, not safe** (6, 5, 6; R2 says "borderline reject, leaning to borderline accept for a workshop").

**What changed.** Side by side, V6 wins. Alone, it is held to its own headline: the title and "the judge fails for lack of ground truth, which the agent's materials do not supply" make a causal claim that all three reviewers say is untested. The sharper thesis bought clarity but cost soundness and originality; V5's smaller claims were harder to fault.

**What limits it.** All three name the same one-point change: **a keyless verifier.** The exact-query log holds the true logit for every tested candidate (a tested true cue passes 53/57). If a scripted reader of it does well, the finding is "LLM judges ignore evidence that is present", not "the evidence is absent". The title depends on which holds.

## 4. Remaining weaknesses, ranked

| # | Weakness | Raised by | Fix type | Before 17-20 Nov? |
|---|---|---|---|---|
| 1 | No keyless verifier. "Materials do not supply ground truth" is untested. | R1, R2, R3 | Analysis (scripted verifier on L1/L2 logs). New runs for R2's version, a judge with its own query budget. | Scripted: yes. Tool judge: risky. |
| 2 | "Below a trivial rule" comes from the design: every hard probe has a cue. κ also depends on prevalence (87/130, 7/60, 45/64). | R1, R2, R3 | Writing (demote the rule). Analysis: balanced accuracy, κ within named and within `none` answers, all-slot ladder. | Yes |
| 3 | No interval on any κ. Only 6 items, shared across the three "replicating" sets. Judge noise is as big as the effects (7/24 hard-slot flips, placebo log 0.20 vs real 0.06). | R1, R2, R3 | Analysis: item-bootstrap κ; Table 1 steps labelled descriptive. Cheap new judge runs: majority of samples. | Yes |
| 4 | The answer-key control is close to string matching and missed its registered band (0.92-1.00 vs 0.60-0.90). | R1, R2, R3 | Writing. Cheap new judge runs: key-on-report. | Yes |
| 5 | Generality is overreached: one ladder prompt, a same-family judge, 6 items from one builder, a closed set of 8 candidates. | R1, R2, R3 | Writing (scope). New runs: non-GPT judge at L2. | Writing yes; judge probably. |
| 6 | J1/J2 (214 runs) includes 18 unreconciled harder-variant runs; set A is 130 vs 132; Table 1/3 commission baselines differ (9→7 vs 7→7 of 17); Figure 1 dotted line uses all-probe κ 0.44, not hard-slot 0.39. | R1, R2, R3 | Analysis + writing | Yes |
| 7 | Section 5 is a second paper; agent claims rest on 3-6 items; contract-signal account untested. | R2, R3 | Writing (move 5.4 out). New runs for the ablation. | Writing yes; ablation no. |
| 8 | Process notes pile up (L1/L2 registered after Terra's results, fall-through "partial", a Luna count from a README, a relaxed margin). | R1 | Writing, scripts | Yes |
| 9 | Still dense (about 5,000 body words). | R1, R2, R3 | Writing | Yes |

## 5. Overstated claims (quoted)

- Title: "Without the Answer Key, an LLM Judge Fails to Grade Research Agents" (R3).
- "The judge fails for lack of ground truth, which the agent's materials do not supply." (R1, R3)
- "Without ground truth, the judge never beats a trivial rule, however much of the agent's material it reads." (R1, R2, R3)
- "Neither the prompt nor the judge model fixes this." (R1, R3)
- "A positive control, not string matching." (R1, R3)
- Table 1 caption: "more evidence removes credited commissions faster than credited omissions" (R1: J12 p = 0.11; reverses on the main study).
- "GPT 6.1 Terra passes every item (20/21 runs) and GPT-6 Luna rarely does (2/17)" (R2: 3 items)

## 6. To-do list

1. **Build a pre-specified scripted keyless verifier on L1 and L2.** Credit a named cue only if its isolating edit beat 0.30; credit `none` only if the top-2 proxy candidates were isolated below 0.15. Fix the rule first, report κ and false-credit split beside the LLM judge and keep or reframe the title.
2. Item-bootstrap intervals on every κ, plus balanced accuracy; take the trivial rule out of the abstract and Figure 1 title.
3. Rerun J1/J2, C17 and 41/44 on the 196 reconciled runs; fix 130/132, the Table 1/3 baseline and Figure 1's line.
4. Reword L3 as "the judge can apply a key"; if budget allows, add key-on-report and a non-GPT L2 judge.
5. Scope every headline claim to this task, judge and item set; make model names consistent.
6. Move 5.4 and bookkeeping to the appendix; bring back one sentence each on leaderboard flips, PPI and cost per pass.
7. Commit a script for every body number; flag claims resting on items with deviations.
