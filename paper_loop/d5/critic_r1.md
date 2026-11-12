# CRITIC r1: d5/draft_r1.md, direction "d6 Silent negatives" (with the proxy, errors become false "nothing found" verdicts)

Inputs read: BRIEF (RULES, CFP, USER_BRIEF, PRIOR_FIXES, EXISTING_DIRECTIONS), LEDGER, lit/L1-L3, updates/round_1.md (newest), d5/calc_d5.out.md, ledger/calc/10 and 11, followup/solvers and proxy_verify READMEs, the Block 1 prereg NAME definition, 10 claim verdicts, and 3 reviews (6 / 7 / 6). Housekeeping: the folder is d5, the task calls the direction d6, and the draft header says "d5 (I6)". Use one label.

New numbers below were computed by this critic with ledger/calc/stats_lib.fisher2 and wilson from committed counts (C.2, CALC/10, calc_d5 §1). No new runs, no [OCT] input. Each is tagged where it is used.

## 1. Diagnosis (5 lines)

1. The core is sound and every number checks out. The grader certifies negatives, so verdict precision (named-claim PPV, "none" NPV) and error composition can be measured. The matched-budget commission collapse (1/98 vs 24/75; run-level hard slot 1/29 vs 12/23, stratified p = 2.6e-4) is the strongest result in the whole paperloop.
2. All three reviewers raise the same main threat: the omission side looks engineered (trap contract), rests on Haiku (9/10 Open-8 omissions), and is never stress-tested where the proxy could push agents toward a false claim. The draft concedes this but never rebuts it with data it already has: two-part-only items, scripted policies that show composition depends on the policy, and leave-Haiku-out.
3. The framing overreaches in four places. The title ("moves", "an AI scientist") implies errors transfer from one type to the other, but omissions also fell about 3x. "A named answer is a tested answer" is contradicted by 39/42 untested ordinary probes that passed. The §6 judge consequent generalizes from one pending prompt. Recheck "cost" is equated with the share of verdicts.
4. Precision gaps are fixable with wording: grader cells ("untested" is reader-coded, not a bucket), the tells (only the midpoint tell was checked), the 17/22 vs 17/47 trap-failure denominators, NAME 6/24 vs 8 correct named, 4.4% vs 4.8%, and the 0/100 null-false bound behind "invariant to q".
5. Brief fit: the environment, grader, prompt and generator are present. The SHIFT comparison and the removal half are missing, though USER_BRIEF requires them and Reviewer 3 flags them. The relayed user request ("explore more directions or combos outside the 4") should go in as a short, concrete open-directions paragraph, since new runs are off the table now.

## 2. Prioritized fixes (12; writing and existing-data analysis only; new-run asks become wording)

Each fix gives an expected average review-score delta. The deltas overlap, so they do not simply add up.

### F1. Rebut "omission dominance is built in" with data already in hand  (+0.4; R1, R2, R3 major)
Add a robustness paragraph at the end of §5.2 and one sentence in §5.4. Use (a) two-part items only, where the trap contract plays no role, (b) the scripted-policy bracket, which shows the same trap produces commissions under a credulous policy, and (c) trap-only for symmetry.

Replacement text (§5.2, new last paragraph):
> **Not only a trap artefact [EX/SC].** On traps, `none` is the contract-literal answer once the [decoy] is refuted, so we check the ordering where that does not apply. On the three two-part items the proxy ranks the [main] first and no decoy exists. There a named claim is wrong 1/141 times and a `none` 9/59 times (verdict-level Fisher p = 8e-5, descriptive). On traps the figures are 6/136 and 14/64 (p = 2.7e-4). The trap also does not force an omission. Scripted policies run on the same three traps show that the type of error depends on the policy. A policy that trusts the proxy's head names the [decoy] and makes a commission on every shipped trap (the "[decoy] only" cheater in Table 1; band solvers V1, Ub1, Ub2) [SC]. A policy that tests the head, refutes it and stops answers `none` (V2) [SC]. A policy that tests the proxy's top two on every probe passes 0.96 [SC, privileged, written after the rank-2 placement was known]. When agents with the proxy fail, they fail like the second policy, not the first.

Check before using: confirm in proxy_verify that the "SAE only, no exact query" policy submits the [decoy] (it scores 0.00 on traps). If you cannot confirm it, cite only the Table 1 cheater and V1/Ub1/Ub2, which solvers/README §5 documents ("name the decoy and fail; V2 … names `none`").

### F2. Show the ordering is not Haiku's alone  (+0.3; R1, R2, R3)
Add this after the per-agent rows of Table 3 (C3, C4):
> The ordering holds in direction for each agent. It is individually significant only for Haiku (verdict-level p: GPT 0.17, Opus 0.15, Sonnet 0.075, Haiku 3e-5), and GPT's rests on 3 errors. With Haiku removed, a named claim is wrong 4/208 times (1.9%) and a `none` 8/80 times (10.0%; p = 0.005, descriptive). Rechecking `none` (28% of verdicts) then catches 8 of 12 errors. Averaged with equal agent weights, the rates are 2.9% and 17.8%.

In §5.1, replace "This is a statement about composition…" with (C3):
> The shift is compositional. Pooled over the two agents, omissions also fall (10/108 vs 33/108 per planted probe, p = 1.3e-4). That fall is GPT's (1/72 vs 21/72); Haiku's omissions barely change (9/36 vs 12/36). Either way, omissions fall much less than commissions, so the errors that remain are nearly all false "nothing found" verdicts (10/11 vs 33/57; Open-8 share run-clustered 95% CI [73, 100]%).

In Table 2, mark the 0.045 p-value "verdict-level, descriptive" or replace it with the clustered CI.

### F3. Retitle and rescope; treat BB-64 as support, not a threat  (+0.3; R1, R2, R3)
Title: **"Nothing Found: Grading Negatives Shows That a Cheap Proxy Leaves an Auditing Agent's Errors Silent"**. Alternative: "…Removes an Auditing Agent's Wrong Claims Far Faster Than Its Misses". Drop "moves" and "an AI Scientist's".

Replace the first sentence of §5.5 with this, which rests on Haiku per C9 and gives the information-sufficiency reading:
> **Abundant gold removes commissions first, too [PR-d arm / EX composition].** With 64 exact queries and no proxy, GPT makes no errors, so it cannot show which error type goes first. Haiku can. Its commissions fall from 9/24 at BB-8 to 0/29 at BB-64 (p = 3e-4), while its omissions fall only from 12/36 to 7/36 (p = 0.28), and all 7 remaining errors are `none`. The proxy has the same signature for Haiku (commissions 9/24 → 1/27; omissions 12/36 → 9/36). The pattern therefore reflects information sufficiency in general: once an agent has enough evidence, wrong claims disappear before missed findings do. The proxy supplies that evidence at 8 exact queries, where a black-box agent needs somewhere between 16 and 64.

Add one sentence to the Conclusion that scopes the claim to "agents auditing with a cheap proxy and a scarce exact budget".

### F4. Fix the audit-rule wording, lead with matched arms, and state the bound behind "zero"  (+0.25; C5, C6, R2, R3)
In the Abstract and §1, replace "at about a third of the recheck cost" with "by rechecking about a third of all verdicts (31% at our 1-in-4 null share)". Lead §5.3 with:
> With the proxy (all SAE runs, four agents), rechecking only the `none` verdicts, 31% of verdicts, catches 77% of errors (2.5× random; bootstrap 58-93%). At matched budget with the same two agents, the lift is 2.9× with the proxy (Open-8, 11 errors) and 1.2× without it (BB-8, 46% → 55%), where the rule is barely better than random. The share of errors caught does not depend on the null share. The share of verdicts rechecked does.

After the q-table add (C6):
> This invariance assumes the observed rate of zero false claims on null probes (0/100; 95% upper bound 3.7%). At that bound, rechecking negatives still catches 68% of errors at q = 0.25 but only 56% at q = 0.50, where named and `none` verdicts become about equally reliable (6.3% vs 7.4%). Ordering: at the observed per-probe rates, P(wrong | `none`) exceeds P(wrong | named) for any null share below about 3/4.

Name the statistics once in §3.1: "verdict precision is the positive predictive value of named claims and the negative predictive value of `none`; what is new is not the statistic but a benchmark whose certified nulls make NPV computable." This answers the R1 and R3 nitpick and helps statisticians on the committee.

Add a process-level comparator from existing routes (R1, R3: "only compared with random") [EX, CALC/10, trap hard slot only]:
> A trace-based flag does as well on the trap probe. An evaluator who holds the same proxy can flag runs whose exact queries never isolated the proxy's runner-up. The flag marks 16 of 47 timed trap runs and catches 13 of the 17 failures (failure rate 13/16 flagged vs 4/31 unflagged; run-level p = 7e-6). The verdict-type rule needs no trace. The process flag needs logged queries and the proxy ranking, both of which ShiftHunt releases. Both rules are post hoc.

### F5. Make the acquisition evidence mechanical, and remove one overclaim  (+0.2; C7, R1, R2, R3)
- §5.1: delete "A named answer with the proxy is a tested answer." Untested ordinary probes pass 39/42, so it is false. Replace with: "With the proxy, named answers are either tested or sit on probes where the proxy's head is right."
- §5.4, Abstract and Contribution 4: replace "so failures happen at acquisition" with:
> Decisive tests are read correctly once run (203/207; trap probes 27/31, all four exceptions on one borderline item), so failures are mostly acquisition failures. 26 of the 30 wrong planted answers with the proxy came on probes whose true cue was never exact-tested.

  Add "this conditions on testing, so it shows that reading is not the bottleneck; the 26/30 figure shows where the errors sit."
- Add one clause from updates (tender-dijkstra): "failing main-study runs ended with 91-124 of 150 tool calls unused (median 115)". Omissions are therefore not caused by running out of overall budget; exact-query allocation is.
- Table 5: rename the column to "[main] + an extra cue matching no main (reader-coded untested)". Mark "Half of the six trap commissions are untested claims" [RC]. Cite the grader buckets (planted_none 11 / extra_cue 3 / cue_not_identified 3) next to failure_modes.json D. Do not cite the README §D prose (2/4).
- §5.4: replace "17 of 22 NOV trap failures never isolated rank 2 (11 of them Haiku's)" with "13 of the 17 trap failures in Table 5 never isolated the [main] (9 of them Haiku's)". The 22 comes from a different, derived 63-slot set (CALC/11). Add to the Table 5 caption: "47 timed trap runs; the 3 untimed trap runs of the 50 all passed".

### F6. Correct the grader-cell definition and the tells  (+0.1 rigor; C1)
In the §3.1 table cell, write: "commission (a wrong cue, an extra cue matching no main cue, or a false claim on a null probe; buckets `cue_not_identified`, `extra_cue`, `null_false_claim`)". Add:
> The grader's removal and format buckets (`removal_short`, `keep_violated`, `format`) are empty in these runs: every named cue passed removal and keep at the shipped τ and every submission was accepted. The four cells are therefore cells of naming verdicts. In black-box arms they come from the naming half of the grade.

In Contribution 1, change "two information tells that no agent used" to: "two information tells: the midpoint tell was used by no Block 1 run (main-study runs unchecked); the band tell yields a zero-query policy that fails as a whole-episode policy (false claims on 0.27 of ordinary bank probes)". Mirror this in §3.2. Cite ABC's do-nothing agent scoring 38% on τ-bench airline (Zhu et al. 2025, R.13) as the contrast to the all-`none` cheater scoring 0.

### F7. Commission claim: name the agents and use the per-probe denominator  (+0.1; C2)
In the Abstract and Contribution 2, write:
> At a matched 8-query budget, the proxy almost removes wrong named claims on planted probes for GPT 6.1 Terra and Haiku 5.5 (1/98 vs 24/75; per planted probe 1/108 vs 24/108, so the drop is not a denominator effect). It appears for each agent at the verdict level, for GPT also at run level (hard slot 0/23 vs 8/16), and in a run-level item-stratified test (p = 2.6e-4; lower with the proxy on 5/5 untied items, sign-test p = 0.031).

Keep "Haiku's run-level contrast alone is not significant (p = 0.27)".

Footnote in §5.1: "8 of GPT's 16 named BB-8 hard answers were correct; the pre-registered NAME counts 6/24 because NAME also requires `none` on every null probe, and two of these runs made a null false claim."

### F8. Two-part omissions: spread across agents, with the contract caveat  (+0.15; C8, R1 underplayed finding)
Replace the §5.4 two-part paragraph's middle with:
> These omissions are spread across all four agents (9 = GPT 1, Opus 3, Sonnet 2, Haiku 3), unlike trap omissions (9 of 11 Haiku's). Eight of the 10 two-part failures never wrote the nested cue down [RC]. Exact-tested children pass 26/26, and the proxy flagged the parent or child in 6 of 10 failures, so what is missing is the hypothesis, not proxy guidance. In 4 of the 10 failures the agent pruned the parent by applying the prompt's exact-alignment statement, so these omissions also partly reflect item and contract design. Two-part items also carry a hint and a different substrate. Without the proxy, the nested hypothesis was written down in 15/16 black-box failures [RC]. The proxy arm fails earlier in the pipeline, consistent with the proxy anchoring hypothesis generation. Language agents under-hypothesize conjunctive causes unless hypotheses are enumerated explicitly (GX-Chen et al. 2025).

### F9. Shrink §6 to a scoped pre-registration note  (+0.15; C10, R2, R3)
Cut §6 to about 6 lines and keep only the design, J3 and this sentence:
> If J3 holds for this judge and prompt, a report-reading judge of this kind would give more false credit to the error type that remains once agents have a good proxy, so benchmarks graded this way could under-count it. The pre-registration measures one judge model and one prompt, not judges in general.

Motivation that does not depend on the result: the WebArena judge in ABC accepts empty replies on N/A tasks; about 19 of 40 pre-registered runs call something "checked/confirmed" on proxy-only evidence (CROSS_MODEL §4.7). Luna: "pre-registered, 60 runs (Open-8 ×6, BB-8 ×4 per item), no counted results". Remove "would systematically under-count" from §1 and §8. Use the freed space for F1 and F10.

### F10. Add the SHIFT relation and the removal half  (+0.2; USER_BRIEF requirement; R3 major)
Add one paragraph at the end of §3.2 or in §7 (H9 numbers, all NOV):
> **Relation to SHIFT.** SHIFT (Marks et al. 2025) has a human read SAE features and ablate the task-irrelevant ones. Without being told how to find the cue or choose latents, agents reach the same goal by another route: property → counterfactual edit → latents ranked by g·Δf. Every SAE run encoded its own edited texts through the SAE (100/100). Reading latent meanings was optional: 47/100 runs did it, and Opus passed 11/16 without ever doing so. The removal half is a knob (τ). At the shipped τ it never binds (176/176 named cues pass removal and keep), so this paper's verdicts are naming verdicts. A stricter τ, or traps whose cue no small latent set removes, would make removal decide grades.

Add SHIFT and Karvonen et al. to Table 6 or its prose.

### F11. Add an open-directions paragraph that answers the user's request  (+0.2; user request; all three reviewers' "go beyond the four")
Add to §8 or as §9a; wording only, no runs claimed:
> **Directions the environment already supports.** The knobs that produced these items can produce the combinations this paper could not test. (i) *Null + decoy*: a null probe on which the proxy shows a strong spurious latent, which tests whether named claims stay trustworthy when the proxy invites commission. (ii) *Trap × two-part*: a [decoy] on top of a nested [main]. (iii) *Deep trap*: the [main] absent from the proxy's top-k rather than ranked second (the top-two policy then scores 0.00 [SC]). (iv) *Null share varied per episode* (0-3 nulls, disclosed or not), measuring whether agents' `none` propensity shifts, which our q-table only extrapolates. (v) *Contract variants*: an explicit "inconclusive" answer or asymmetric penalties, which would measure how much omission dominance comes from scoring incentives (recommendation 5). (vi) *Second agents at matched budget* (Luna, Claude BB-8). (vii) *A second domain with certified nulls*, e.g. ML experiments where some interventions have a planted effect and others none. Each needs only certified-null items next to planted ones.

Soften recommendation 5 to "we expect" and point to (v).

### F12. Consistency, length and labels  (+0.1; R2, R3 nitpicks that cost credibility)
- Use one per-agent maximum for the named-claim error: the all-SAE "at most 4.4%" in §1, Contribution 2 and §5.1. Label the main-study 4.8% row "main study only" or drop it.
- Table 3 BB-8 row: mark that 27/78 includes 3 null false claims.
- Drop R5 [OCT-CHECK] from §5.5. The NOV supplementary runs (8/9; named 1/58; `none` 8/30; null 0/22) cover the point. Describe them as "show the same composition (budgets of 4 or 8 exact texts; same six items)", not "replicate".
- Length: the body probably exceeds 8 AAAI pages. Cut §6 (F9), merge recommendations 3 and 4, move C.3-C.7 tables out of the body, and keep Box 1 in the body and the full prompt in the appendix.

## 3. Nitpicks to ignore (or answer in one clause at most)
- A hierarchical GLMM with agent/item/run random effects. Agent-weighted rates and leave-Haiku-out (F2) plus the existing run/item bootstraps are enough for a workshop. Do not add a model fitted on 6 items.
- The bootstrap with 6 item clusters is unreliable. Keep the sign-test floors (0.016; 0.031) beside it, which the draft already does.
- Per-arm dollar or token cost per error caught. The cumulative ledger and the token-direction argument suffice.
- The SAE feature-absorption link for nested cues (R3). It is not in the lit notes; skip it unless a verified citation is at hand.
- [RC] single unblinded reader. This is already disclosed. The mechanical 26/30 and route tables (F5) now carry the load.
- R2's "47 vs 50" and "8 vs 6 NAME". These are resolved by one caption clause and one footnote (F5, F7), not by reanalysis.
- Recomputing anything from BB-8 non-hard slots per run. This is impossible by construction and already disclosed in C.1.

## 4. New in updates/ (round_1.md, newest)
- **Luna arm:** pre-registered (L1-L4; 60 runs: Open-8 ×6 and BB-8 ×4 per item; seed luna-1112). The pilot ran fine ($0.136; model confirmed). **No counted results.** Its confirmatory tests concern rank-2 isolation and NAME, not verdict composition. If it lands before 20 Nov, its per-probe buckets allow a third matched-budget agent in the composition tables, but only as [EX]. Do not promise this; say "pending".
- **Judge J1-J4:** still no results (only PREREG_JUDGE.md and inputs.json). Write it as pending (F9).
- **Token-cap sensitivity** (brave-curie): the draft's "≥ +0.71 at any cap ≥ 86k" matches. Nothing to change.
- **tender-dijkstra:** "91-124 of 150 tool calls left in the 19 failing main-study runs (median 115)". This is directly useful for F5, since omissions are not caused by running out of overall budget. The GLMM ranges are not needed for this direction.
- No [OCT] material in the new files.

## 5. Combos with other directions (relayed user request: directions outside d1-d4)
This direction is itself outside d1-d4. To strengthen it without new runs, borrow from:
- **d2 (proxy-and-gold):** the "mirror" paragraph already makes the evaluator's allocation problem the second proxy-gold instance. Add the PPAT citation (gold labels where the proxy is likely to err), which links the agent-side and evaluator-side halves.
- **d4 (process failures):** F5/F8 make "acquisition failure → silent negative" the bridge from process to output. That is the paper's process-level contribution to the CFP.
- **New candidate directions, if the loop wants more:** (a) *Instrument quality*: certified negatives as a property of a good grader (NPV computable; all-`none` cheater = 0; power floors), aimed at the CFP's "how good is the instrument" area. (b) *Information sufficiency*: proxy and abundant gold both remove commissions first (Haiku BB-64; F3); the proxy is worth 16-64 exact queries. (c) *Evaluator audit allocation*: verdict-type rule vs process flag (F4) as a PPAT-style evaluator design paper.

## 6. Ceiling
- Current reviews: 6 / 7 / 6 (mean 6.3).
- With F1-F12 (wording and existing data only): **about 7 (accept), likely 6.5-7.** The two biggest lifts are F1 (built-in rebuttal) and F2/F3 (Haiku dependence; scope and information sufficiency).
- 7.5 if J3 reports before the deadline in either direction.
- 8 needs new runs: a null+decoy item, an empirically varied null share, or a held-out generator-item replication. That is out of scope for this round.
