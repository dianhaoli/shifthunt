# Portfolio for 12-19 Nov 2026 (deadline 20 Nov 06:00 UTC)

Decider's summary of 27 candidates, 7 designs and 7 critic verdicts. Inputs: `01_ideas.md`, `design_C*.md`, `RANK_V4.md`, `WORKSHOP.md`. Nothing was run or spent to produce this page. Episode/cue rule respected: only [main]/[decoy].

---

## 1. How the judge idea happened, and the reusable pattern

A reviewer wrote "the judge contrast is asserted, not measured; run a judge on the existing reports against the certified grade". We sent the 214 existing reports to a frozen judge for $1.97. That became Claim 2: κ = 0.002, and 41 of the 44 "nothing found" failures were credited.
**The pattern:** take an instrument the community already uses (an LLM judge, Kendall τ, PPI, an audit order, ABC's do-nothing check), score it against our certified grade on runs we already have, for a few dollars. The certified grade is the scarce asset, and every cheap instrument we score against it is a result.
**Two cautions the critics kept raising:**
- Before calling something a finding, check whether it already follows from committed counts. For example, a rule that credits any named cue reaches hard-slot κ ≈ 0.72 using no evidence at all.
- Always include a noise floor (re-send the same calls) and a placebo.

---

## 2. Recommended portfolio (do these, in this order)

**Total:** about $21-23 OpenAI at the core, $28 at most if C14's stage 2 runs. Under $1 of Claude. That leaves about $6-13 of OpenAI and $9 of Claude in reserve.
**One shared gate first (13 Nov, $0):** the box agent confirms that the private per-slot judge verdicts (`results/private_1112/judge/slots.json`), the Luna traces and the replay cache exist. #2-#5 all depend on them.

| # | what | data | $ | hours (agent / author) | result it produces | paper sentence it enables | answers |
|---|---|---|---|---|---|---|---|
| **1** | **C14 (revised): fresh rank-2 traps (F2) plus bank traps with [main] at proxy rank 6 (R6), Terra and Luna, Open-8** | new runs | core ≈ $12.5, including the 3-run shipped anchor (≈ $2.1); stage 2 (+6 Terra on F2 only) up to the $17.5 cap | 6 attended + 6-8 unattended / 3 | Terra's and Luna's NAME and widening rates on 3 held-out rank-2 traps, plus a concurrent shipped anchor. R6 is descriptive; it counts as "one probe, three episodes" if G1 finds a single source. Plus judge credit on the new runs | "On three held-out traps from the same generator, Terra names the [main] in a/6 runs (shipped: 11/12) and Luna in b/9; with the [main] at proxy rank 6, Terra isolates rank ≥ 3 in c runs." | Reviewers' main request: 4 of 5 make it their top ask, and RANK_V4 lists it as new run #5a ("the run that would move them to 8"). CFP: distribution shift, tasks that stay valid after exposure (use "held-out items", never "contamination-proof"). Speakers Rish and Kahou |
| **2** | **C6 (revised): judge evidence ladder.** L0r (same-time re-send of L0) · L1 (+ exact-query log) · L1-redacted (same log with every logit hidden) · Haiku judge on all three rungs. L3 dropped | **existing runs**, new judge calls | ≈ $7-9 OpenAI + < $1 Claude | 6 / 2 | κ on named answers only (J5′), a `none` discrimination index over all slots, false credit split by `none` vs wrong cue, false blame on null slots, test-retest (L0 vs L0r), and a second judge family | "Given the exact-query log, the judge … on named answers (κ X → Y), yet still credits Z/44 `none` failures; hiding the logits removes/keeps the gain; a Claude judge behaves the same." Either outcome gives a measured payoff for "log every exact query". | RANK_V4 new run #5b ("a judge that also sees the exact-query log"), and the objection 4 of 5 reviewers raised to Claim 2 (one judge, same model). CFP: judge reliability, process-level evaluation from traces |
| **3** | **C8 (revised): the frozen judge on Luna's 60 held-out runs.** Run `luna_decoy_flag.py` first, on its own. Re-send Terra's 24 Open-8 judge calls interleaved with Luna's (drift control) | **existing runs** | ≈ $0.8 (Luna's L0 calls are shared with C6) | 3.5 / 1 | Out-of-sample J1/J2 on a population whose errors are commissions. The judge-implied Terra-Luna trap gap (certified 0.86). A mechanical recount of the "[decoy] submitted after its own refuting pair" count | "On Luna's 60 held-out runs the judge again agrees at chance and shrinks the study's largest certified gap from 0.86 to Δ." (Or "a report cannot certify an omission", if it catches the commissions.) | CFP headline: "so that a reported gap between two systems can be attributed to the systems". It also protects an existing number ("7 of 18" in §5.3, Table 4, App. G) |
| **4** | **C19 (revised): what the judge does to established orderings** | **existing data only**, CPU | $0 | 1 / 1.5 | The exact per-agent Block 1 judge rates, replacing App. H's bounds. The reversed established contrasts: the judge makes Terra's budget curve non-monotone (BB-16 judged 21/24 vs BB-64 at most 19/24), puts Haiku-open above Terra-BB64 (certified 13/28 vs 24/24), and flips the Terra-Haiku gap. τ is reported in one line, "for scale", for the L9 and L11 leaderboards together. Report length per system | "Graded by the judge, more exact queries look worse for Terra (16 > 64) and the certified Terra-Haiku gap of +0.32 becomes ≤ 0; between the two leaderboards τ_b ≤ 0.37 in every split consistent with the data (AstaBench, judge vs experts: 0.467)." | CFP: sensitivity of rankings to the judge, cost-normalized reporting, AstaBench's τ. RANK_V4 fix 4 (the per-agent judge reordering table). No body growth |
| **5** | **C21 (slim): audit the negatives first.** Errors caught vs fraction of runs audited, for these orders: random, `none` first, lowest judge confidence first, judge-pass first. Hard slots and all slots. One PPI effective-sample line | **existing data only**, CPU | $0 | 4 / 1 | An audit curve plus "how many certified grades the 214 verdicts are worth" | "Certifying the `none` verdicts first finds X% of the judge's errors after auditing Y% of runs, whereas ordering by the judge's own confidence finds Z%." This turns §5.2's *advice* into a measurement | CFP: sample-efficient evaluation and off-policy reuse of prior judgments, cost-normalized. Backs the contribution sentence "audit negative verdicts first", which currently rests on base rates only |

**Why C14 is first although it screened fifth on utility.** The utility screen penalises cost and risk. C14 is the only candidate that touches the one weakness all five reviewers named: only three rank-2 traps, all of them public. Every critic ranked it ahead of C6. Expected gain, as the critics estimated it: C14 +0.3 (range −0.2 to +0.6); C6 +0.2 to +0.4; C8 ≈ +0.15; C19 +0.1 to +0.2; C21 ≈ +0.1.

**Required critic changes, in short.**
- C14:
  - G1 reports the number of distinct R6 sources first.
  - Add the shipped anchor, paid for by cutting Luna on R6.
  - Spend stage 2 on F2 Terra only.
  - Publish the true effects of candidates at ranks 1-5 as numbers.
  - If F2 reverses, use the pre-written Claim 3 rewrite.
- C6:
  - J5 becomes J5′ (named answers only), with the answer-type baseline (κ 0.72) shown next to it.
  - "Reversal" needs null-slot false blame to stay flat.
  - Never cut per-probe headers when truncating.
  - If the main-study replay join is not validated by the end of 13 Nov, set A becomes Block 1 + BB-16.
- C8:
  - A `partial` answer counts as an omission.
  - "Fluency-driven" becomes "credulous across error types".
  - Add a length gate.
  - Report an interval plus the MDE instead of "Fisher p ≥ 0.05".
- C19:
  - Not tagged [pre-reg].
  - No $0-gold cross-harness frontier: use a Terra-only cost-per-pass curve instead.
  - Keep the abstract's "+0.38" unless the paired interval excludes 0.

**Calendar (UTC).**
- **13 Nov:** shared gate; C14 Step 0 (G1-G6) and the fresh build; the C8 flag script, then the C8 calls; C19 on CPU; C6 freeze and its 5-call dry run.
- **14 Nov:** C6 calls (about 4-5 h, interleaved); C14 go/no-go at 15:00, then its runs start; C21 on CPU.
- **15 Nov:** C14 runs finish; C6 and C8 analysis.
- **16 Nov:** C14 judge and analysis; insert the pre-written paragraphs.
- **17 Nov 23:59:** hard stop for new data.
- **18-19 Nov:** writing only.

**Writing that must happen regardless ($0, about 1.5 days of the author's time).**
- Get to 8 pages, with a one-paragraph abstract of about 200 words.
- Replace "worse than no auditor at all" and "keep pace" with measured statements.
- Bring in PAPER_BEST's conditional route test, the token-cap sensitivity and the per-agent reordering table (the reordering table is delivered by #4).
- Each design above trades body text, so net body growth must be ≤ 0 words.

**Fallbacks.**
- If C14 fails its gates by 14 Nov 15:00, run plan B (re-used probes, with the wording changed) or drop it. Move about $5 to C7-slim and C12 (§3).
- If the private verdict files are missing, re-derive them from `raw/`. If that fails, C19 and C21 drop to the Part A bound sentence, which holds whatever the data say.

---

## 3. Also worth doing if time (next 5)

1. **C12 lean: the judge on scripted controls** (≈ $0.6-1.5, existing scripted policies). Make P7 vs P0 the primary contrast: an unsupported `none` vs an unsupported true cue on the same slot. If the judge credits the `none` more often, the 41/44 comes from its prior, not from agents' prose. P1 (all-`none`) is reported as an ABC-style number. Keep it out of the abstract unless it holds on both shipped and bank items.
2. **C7 slim: second-family and skeptical-prompt judges.** Cells L-F, H-F, T-K, L-K, H-K, plus S-F only if Claude money remains (≈ $2-4 OpenAI, $0.4-4 Claude). The primary metric is a within-run paired `none` AUROC. Label K as a "failure-mode-informed upper-bound rubric". Incremental over C6's Haiku arm: about +0.1.
3. **C17 judge half only: one more re-send, R2** ($1.97). Together with C6's L0r it gives three replicates. Report raw agreement and PABAK next to Fleiss κ ("reliable but invalid"). Optionally add a CPU-only, naming-only grader redraw with 20 salts. Do not touch §9's "near-noiseless" sentence: it refers to the exact readings, not to the grader.
4. **C18: what the judge tracks** ($0, existing data). Logistic models with item fixed effects for judge credit: answer type, length, hedge lexicon, and whether the true cue was isolated. Add an Oaxaca-style split of each system's judge-vs-certified gap. This gives the quantitative "why" behind κ = 0.002, and it pairs with #4.
5. **C3 + C4: effort metrics and verification claims vs certified pass** ($0-1, existing data). "How much an agent verified does not predict whether it is right; what it verified does." It also mechanically replaces the reader count "about 19 of 40". It speaks to the CFP's Goodharting topic.

---

## 4. Good ideas for after the deadline

**Camera-ready (by 15 Jan), if the paper is accepted:**
- **C26, a menu / forced-allocation arm.** This was reviewer request #5c. It needs an image rebuild, so it is impossible by 17 Nov. It is a causal test of whether Luna's 0/18 is an enumeration failure.
- **C23, a scripted bank map** (budget × trap rank, with a 2PL item map). It turns "single-budget ablations mislead" into a figure and pre-registers predictions for more depth items.
- **C22, a G-study / D-study** ("buy items, not reruns"; dollars needed for G = 0.8). Watch for false precision with six items.
- **C24, pass@k with a fallible verifier**, and **C20, rubric-variant vs judge-threshold fragility**: both $0 appendix material.
- **C14 extended:** more rank-6 sources and a rank-3/4 pool, if R6 turns out to be one probe.

**Follow-up paper ("auditing the auditors with certified ground truth"):**
- **C11, rubric-authorship bias with a certified control.** This is AstaBench's open question asked directly.
- **C10, identical work narrated by different models.**
- **C9, answer-swap and rhetoric perturbations** (the "polished null" attack surface).
- **C13, agent self-grading.**
- **C5, certifying LLM trace coders.**
- **C1, a truth-free provenance auditor from the query log.**
- **C2, concept-erasure metrics (SHIFT/SCR-style) vs certified removal.**
- **C25, a calibrated VOI policy and agent regret.**
- **C27, thinking compute vs exact queries.**
- **C16, the agent as item designer.**

---

## 5. What this audience wants

This is a measurement-science room more than an agents room. The subtitle is "how good is the instrument". The senior advisor edits JASA (Zhu). The primary organizers work on statistical metrology of evaluation (Zhou) and on auditable, budget-aware agent evaluation (Shi). The speakers bring uncertainty quantification (Dai), statistically rigorous evaluation of research agents (Wang), budget-constrained test-time compute (Hu), causal reasoning (Jin) and robustness under distribution shift (Rish, Kahou). The supporting team works on LLM-judge reliability. They want an instrument checked against ground truth stronger than opinion, with reliability and validity separated. They want honest power and minimum-detectable-effect statements, rather than six-item p-values passed off as generality. They want cost-normalized, matched-compute comparisons, and AstaBench's open question (do judge and rubric gaps reflect the systems?) actually asked. Our certified grade is exactly what they lack, so judge results scored against it (#2-#5) hit the centre of the call. The held-out traps (#1) answer the distribution-shift and contamination interest and the reviewers' main doubt. They care less about interpretability for its own sake: the CFP says papers "must directly address the evaluation of autonomous scientific discovery". Lead with the AI-scientist framing, present oversight as the reason for the testbed, and show item-level floors next to every run-level result.

---

## 6. Full ranked candidate table

The order is the decider's final rank. The utility column is the screening score; the screen order differs (for example, C14 screened 5th). Cost is new API dollars from the screen; critic-revised costs are in §2. Tier: P = portfolio, T = if time, A = after the deadline.

| rank | id | title | impact | gain | feas | risk | cost $ | util | tier |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C14 | Rank-6 bank traps and fresh rank-2 traps, Terra and Luna | 8.33 | 7.67 | 5.33 | 6.33 | 14 | 5.93 | P |
| 2 | C6 | Judge evidence ladder (report → + query log; Haiku arm; redacted placebo) | 9 | 7.67 | 8 | 4.33 | 7 | 7.37 | P |
| 3 | C8 | Out-of-sample judge on Luna's 60 runs | 7 | 5.33 | 10 | 3 | 0.6 | 6.72 | P |
| 4 | C19 | Leaderboard reversal in AstaBench's units, plus cost view | 8.67 | 6 | 9 | 4 | 0.6 | 7.03 | P |
| 5 | C21 | Price the judge in certified labels: PPI and audit-the-negatives-first | 7 | 4 | 7.67 | 4.67 | 0 | 5.22 | P |
| 6 | C12 | ABC do-nothing test on the judge: scripted cheaters and controls | 7 | 4.67 | 9 | 4.67 | 0.9 | 5.85 | T |
| 7 | C7 | Judge panel: model family × skeptical prompt, self-preference | 8 | 5.67 | 7 | 4.33 | 6 | 6.02 | T |
| 8 | C17 | Reliability vs validity: judge test-retest, grader regrade, agent ICC | 8 | 5.33 | 6.67 | 4.67 | 4 | 5.73 | T |
| 9 | C18 | What the judge tracks: MTMM and per-system bias decomposition | 6.67 | 4.67 | 7.67 | 4.33 | 0 | 5.40 | T |
| 10 | C3 | Effort and activity metrics as rigor proxies | 5.33 | 3 | 9 | 3.67 | 0 | 4.88 | T |
| 11 | C4 | Agents' verification claims vs logged tests and certified grade | 6 | 4 | 7 | 5 | 1 | 4.60 | T |
| 12 | C26 | Menu intervention (forced allocation; enumeration vs depth) | 6.67 | 5.33 | 4.33 | 5.67 | 6 | 4.37 | A (camera-ready) |
| 13 | C23 | Scripted bank map and IRT diagnostic panel | 5.67 | 3.67 | 6.67 | 4.33 | 0 | 4.40 | A (camera-ready) |
| 14 | C24 | pass@k with a fallible verifier | 6.67 | 3.67 | 8 | 4 | 0 | 5.22 | A (camera-ready) |
| 15 | C15 | Stage-wise certified scorecard and its power | 6 | 3.67 | 8 | 3.67 | 0 | 5.05 | A (camera-ready) |
| 16 | C20 | Leaderboard fragility: rubric variants vs judge thresholds | 6.67 | 3.67 | 7.33 | 4.67 | 0 | 4.88 | A (camera-ready) |
| 17 | C22 | G-study / D-study, slot IRT, anytime-valid replay | 7 | 3.67 | 6.33 | 6.33 | 0 | 4.37 | A (camera-ready) |
| 18 | C11 | Rubric-authorship bias with a certified control | 7.67 | 3 | 4.33 | 6.33 | 9 | 3.77 | A (follow-up) |
| 19 | C10 | Identical work, different narrators | 7.67 | 4 | 5 | 5.67 | 5 | 4.45 | A (follow-up) |
| 20 | C9 | Counterfactual perturbations: answer swap and rhetoric | 7 | 4 | 5.33 | 6 | 5 | 4.25 | A (follow-up) |
| 21 | C1 | Truth-free evidence-provenance auditor from the query log | 6.67 | 4.67 | 7 | 6 | 0 | 4.87 | A (follow-up) |
| 22 | C5 | Certify the trace reader: LLM coder vs mechanical flags | 6.67 | 4 | 6.33 | 5 | 7 | 4.63 | A (follow-up) |
| 23 | C13 | Agent self-grading with full trace | 6 | 3.67 | 6.33 | 5 | 6 | 4.28 | A (follow-up) |
| 24 | C27 | Thinking compute vs exact queries | 6 | 3.33 | 6 | 5.67 | 11 | 3.93 | A (follow-up) |
| 25 | C25 | Calibrated VOI reference policy and regret decomposition | 6 | 4.67 | 4 | 6 | 0 | 3.73 | A (follow-up) |
| 26 | C2 | Concept-erasure metrics (SHIFT/SCR-style) vs certified removal | 5 | 3.33 | 5.33 | 7 | 0 | 3.12 | A (follow-up) |
| 27 | C16 | Agent as item designer | 6.33 | 2.33 | 2 | 6.33 | 3 | 2.37 | A (follow-up) |
