# CRITIC r2: d5/draft_r2.md, direction "d6 Silent negatives" (folder d5)

Inputs: BRIEF (RULES, CFP, USER_BRIEF, PRIOR_FIXES, EXISTING_DIRECTIONS), LEDGER (§1 H1-H11, §2.3-2.4, §6 dead claims), lit/L1-L3 (as cited by the verdicts), updates/round_9_manual_1112T0830Z.md (newest), critic_r1, calc_d5.out.md, followup/solvers/README.md, followup/failure_modes/README.md, judge/PREREG_JUDGE.md, 10 claim verdicts (C1-C10), and 3 reviews (6 / 7 / 6).

New numbers below were computed by this critic with ledger/calc/stats_lib from committed counts. They are tagged where used. No new runs and no [OCT] input.
- Hard-slot omission share: 7/8 with the proxy vs 13/25 without, Fisher p = 0.107.
- Hard-slot `none` per run: 7/36 vs 13/36, p = 0.19.
- J3: 41/44 vs 12/24, p = 8.6e-5.
- Haiku commission share of errors, BB-8 vs BB-64: 9/21 vs 0/7, p = 0.062.
- Wilson upper bound for 0/100: 3.70%.

## 1. Diagnosis (5 lines)

1. The core holds. Every number re-verifies, and the matched-budget commission collapse (1/98 vs 24/75; hard slot 1/29 vs 12/23, stratified p = 2.6e-4) is robust. But r2 did not move the scores (still 6/7/6). The three reasons are all fixable: Haiku carries the omission side, the "silent" consequence is argued but not shown, and exploration stays inside the four shipped probe types.
2. The biggest change since r2 is outside the draft. The pre-registered judge study is **complete** (J1 κ = 0.002 on hard slots; J2 false credit 0.78; J3 41/44 `none` failures credited vs 12/24 wrong-cue). That is direct evidence that silent negatives are what report-reading misses. The draft says in five places that no judge results exist (§1 C5, §6, §9, App. D, Abstract by omission). Two of the three reviewers named J3 as their top score-raiser.
3. Four sentences state more than the data show and need correcting: (a) "omissions fall threefold, commissions thirtyfold" mixes denominators and hides the GPT/Haiku split; (b) band solvers V1/Ub1/Ub2 "commit a commission on every shipped trap" is false in the frozen unit (band fired 0/15); (c) "all four exceptions on one borderline item", where two exceptions are untested-extra-cue runs on other items; (d) "information sufficiency in general", which rests on one agent.
4. The compositional shift itself has no cluster-level test. At run level only the commission half is significant; omission share is 7/8 vs 13/25, p = 0.11. Say so. Lead with the design-invariant ratio, under which planted probes end in `none` 23 times vs a wrong name 7 times (3.3:1). Put 18.7% vs 2.5% second, with q stated.
5. User request (relayed): "explore more directions or combos, new ones outside the 4". All three reviewers echo it. §8's list (i-vii) stays inside the shipped types. It should name generator-supported types the bank already contains but no agent ran (two-main, 18 units), plus new proxy, gold and evaluator combos, all labelled unrun. The judge result also opens a new paper-level combo (§5 below).

## 2. Prioritized fixes (12)

No new runs. Fixes are writing plus counts already committed. Score deltas are expected changes to the mean review score; they overlap, so they do not simply add up.

### F1. Turn §6 into a results section on the judge (J1-J3). Remove every "no judge results" sentence.  (+0.45; R2, R3 top ask; R1 weakness 4; C1, C2, C3, C4, C6 extra_support)
Replace §6 with:
> ## 6 A Report-Reading Judge Credits Silent Negatives [PR]
> We pre-registered a test of one LLM judge against the certified grade (frozen 2026-11-12T06:00Z, before any judge call). The judge is gpt-6.1-terra, one call per run. It reads the task contract, the agent's own messages and its final answer per probe. It does not see the model, data, tools or answer key. The 214 runs come from every study above (main study and its harder variant, Open-8, BB-8, BB-16, BB-64) and give 856 probe slots. All 214 calls parsed; the cost was $1.97.
>
> **Table 7. Judge vs certified grade.**
> | | pre-registered prediction | result | |
> |---|---|---|---|
> | J1 hard-slot agreement | κ < 0.40 | κ = 0.002 (raw agreement 0.60; certified pass 146/214) | confirmed |
> | J2 false credit on certified-failed hard slots | ≥ 0.50 | 53/68 = 0.78 | confirmed |
> | J3 false credit, `none` failures vs wrong-cue failures | (descriptive) `none` higher | **41/44 = 93% vs 12/24 = 50%** (Fisher p = 9e-5, computed after the fact) | as predicted |
> | J4 all slots | (descriptive) | κ 0.12 (null probes 0.45, planted 0.06); confidence AUROC 0.71 | |
>
> On the slot that decides the score, the judge agrees with the certified grade no better than chance. Its errors are not random. It credits 41 of the 44 failures in which the agent reported finding nothing, but only half of those that named a wrong cue. A wrong cue is a claim a reader can doubt; a fluent "no cue found" gives the reader nothing to check. These are the errors that remain once agents have the proxy (§5.1-5.2). The judge also rejects 32 of 146 certified-correct hard slots, so a judge-graded score would be wrong in both directions. Scope: this is one judge model and one prompt. The agents' messages were not written as reports (GPT's median is about 1,400 characters). The runs pool arms with and without the proxy. A judge with tools or the answer key would be a different instrument.

Also make these edits:
- Contribution 5: change it to "**A pre-registered judge test** (§6): a report-reading LLM judge is at chance on the deciding probe (κ = 0.002) and credits 41/44 false 'nothing found' verdicts."
- §1, after "trust the positives, audit the negatives": add "A report-reading judge does the opposite (§6)."
- Rec. 3: add "and do not delegate that audit to a report-reading judge, which credited 41 of 44 silent negatives".
- §9 "Pending": write "The Luna arm is in progress (about 24 of 60 counted runs, no outcomes computed by rule). The judge test is one model and one prompt."
- App. D: replace "no results exist" with "J1-J4 complete (2026-11-12); Luna pending".
- §5.3: add one motivating clause (C6 fix b).
- Tag: [PR] for J1/J2, [PR-d] for J3/J4.

Do not claim an arm-specific judge rate. Judge.json is not in the local checkout, so J4's by-access table cannot be verified here. Add an SAE-only false-credit figure only if the author confirms it from judge.json.

### F2. State the composition result accurately: heterogeneity, denominators and the cluster-level test  (+0.3; R2 major 1, R1 major 3, R3 major 4; C3 overclaimed)
In §5.1, replace "**[EX]** The shift is compositional. … not an artefact of fewer named answers." with:
> **[EX]** The shift is compositional, and the two agents reach it differently. Pooled, omissions fall about threefold per planted probe (33/108 → 10/108) and commissions about 24-fold (24/108 → 1/108; per named answer 32% → 1.0%). For GPT the proxy removes both error types (omissions 21/72 → 1/72; commissions 15/51 → 0/71), leaving a single error. For Haiku it removes commissions (9/24 → 1/27) but barely changes omissions (12/36 → 9/36). The errors that remain at matched budget are therefore nearly all `none` (10/11, 9 of them Haiku's). The commission drop is significant at run level (below). The rise in omission share follows from it and is not an independently significant shift: on the hard slot, one verdict per run, omissions are 7/8 errors with the proxy and 13/25 without (p = 0.11) [EX].

In Table 2, add the row "Hard slot: omission share of errors | 7/8 | 13/25 | 0.11 (run-level)". In the claim line and Abstract, replace "thirtyfold" with "24-fold per planted probe".

### F3. Rewrite the Abstract and title around the design-invariant ratio, the "in direction" scope and J3  (+0.25; R2 minor 3 and title ask; R1 major 1; C4)
Title (pick one):
- "Nothing Found: Certified Negatives Show That a Cheap Proxy Leaves an Auditing Agent's Remaining Errors Silent, and a Judge Credits Them"
- "Nothing Found: What a Proxy-Guided Auditing Agent Misses, and Why a Judge Cannot Tell"

Abstract (replacement):
> Evaluations of AI scientists usually score what an agent claims. A "nothing found" verdict is harder to grade, because certifying it needs planted ground truth. ShiftHunt is an environment in which agents audit linear probes on Gemma-2-2B for spurious cues. They have free but lossy sparse-autoencoder tools (the proxy) and 8 exact queries. A closed-form grader certifies both verdict types: every episode has one probe with nothing to find and three with a planted cue, so `none` is graded right or wrong like a named claim. At matched budget (GPT 6.1 Terra, Claude Haiku 5.5), the proxy almost removes wrong named claims (1/98 vs 24/75; run-level item-stratified p = 2.6e-4). Omissions fall less (10/108 vs 33/108 planted probes), so the errors that remain are nearly all false "nothing found" verdicts (10/11, mostly Haiku's). Across four frontier agents with the proxy, planted probes end in a false `none` 3.3 times as often as in a wrong name (23 vs 7 of 300). At our 1-in-4 null share, a `none` is wrong 18.7% of the time and a named claim 2.5%, in the same direction for every agent and item and on items with no decoy. Traces locate the cause: decisive tests, once run, are read correctly (203/207), and 26 of the 30 errors sit on probes whose true cue was never exact-tested. In a pre-registered test, an LLM judge reading the same runs is at chance on the deciding probe (κ = 0.002) and credits 41 of 44 false "nothing found" verdicts. Evaluators should report precision per verdict type with the null share, and audit negatives first.

In §5.2, replace the first sentence ("about seven times as likely") with:
> Planted probes end in a false `none` 23 times and in a wrong name 7 times (3.3:1; the run-clustered 95% CI for the `none` share of errors, [60, 91]%, corresponds to a ratio of 1.5-10). This ratio does not depend on the item mix. At our 1-in-4 null share it makes a `none` about seven times as likely to be wrong as a named claim.

Wherever the draft says "for every agent", write "in direction for every agent".

### F4. Correct the scripted-policy paragraph in §5.2  (+0.15 rigor; C5 overclaimed; a reviewer who opens solvers/README would catch it)
Replace "Nor does the trap force an omission … fail like the second policy and not the first." with:
> Nor does the trap force an omission. On the shipped traps, a policy that names the proxy's head without testing it (the "[decoy] only" cheater, Table 1) commits a commission by construction. In an exploratory rerun in the prompt's unit, the band solvers V1, Ub1 and Ub2 name the [decoy] in the 12 of 15 trap-seed cells where their band fires, while V2 tests it, refutes it and answers `none` [SC, exploratory]. A privileged top-two policy names the trap cue 0.96 [SC]. Agents with the proxy mostly fail like V2. 11 of 17 trap hard errors are `none` (9 of them Haiku's), and the [decoy] was claimed in only 2 of 32 main-study trap runs. The larger agents' few trap failures were mostly untested extra claims, not trust in the proxy's head.

Add the two-part spread here as well: "two-part omissions GPT 1, Opus 3, Sonnet 2, Haiku 3".

### F5. Repair §5.4's acquisition paragraph: the exceptions, F4, a base rate and causal wording  (+0.2; C8 overclaimed; R2 minor 4 and 6; R3 major 2)
Replace the paragraph's first five sentences with:
> **Decisive tests are read correctly [EX].** With the proxy, a probe passes in 203/207 cases once the true cue has been exact-tested: ordinary 150/150, trap 27/31, two-part 26/26. Of the four trap exceptions, two named the true cue but added an untested claim. The other two read the true cue at a small value on the one borderline item and answered `none`. When the true cue was not tested, probes pass 39/42 (ordinary), 3/16 (trap) and 13/23 (two-part). The oracle is noise-free and the contract leaves a 0.15-vs-0.30 gap, so easy reading is partly by design. The finding is where the errors sit. **Untested probes are 81 of the 288 planted probes with logged queries (28%), but they hold 26 of the 30 errors** (32% wrong vs 4/207 = 1.9% when tested).

Replace "no run that saw the proxy contradicted … kept the proxy's answer (0/11) [EX]" with:
> Under a mechanical contradiction rule (exploratory, prompt unit; 11 applicable slots), 0/11 kept the proxy's answer. One Haiku run, coded by a reader, claimed the [decoy] after its own exact test disagreed (1 of 31 tested) [EX-expl/RC].

Replace "Allocation of the exact budget decides the outcome." with "Where the exact budget went, not how much budget was left, tracks the outcome; this is observational, and a forced-allocation arm would test it causally (§8)."

Add a caption to explain the 12 planted probes outside the 288 (runs without recovered query logs; take the reason from failure_modes.json).

### F6. §5.4 routes and two-part: scope the GPT figure and state the output fact  (+0.1; C9 overclaimed)
- After Table 5, write: "Failure to widen to the runner-up mostly surfaces as `none`. Of the 13 trap failures that never isolated the [main] (9 of them Haiku's), 9 answered `none` and 4 named a wrong or untested cue."
- In "Search narrows to the proxy's head", move the 23/24 figure out of the matched-budget sentence: "Across all GPT runs with the proxy (main study and Open-8), rank 2 is isolated on 23/24 trap probes vs 5/88 ordinary ones." Keep the Open-8 vs BB-8 curve as the matched-budget statement.
- Two-part: add "9 of the 10 two-part failures answered `none`". Cite the 4/10 parent pruning to the failure_modes reader. Optionally add: "in 7 of the 13 trap failures that never exact-tested the [main], the agent had built a counterfactual for it and read it on the proxy only. The hypothesis was in hand and was never checked against gold" [EX]. This is the cleanest "verification without search" datum and fits the author's framing.

### F7. Rescope §5.5 "information sufficiency"  (+0.15; C10 overclaimed; R1 minor 7)
Replace from "Its commissions fall …" to the end of the paragraph with:
> For Haiku, abundant gold leaves the same signature as the proxy. Commissions fall from 9/24 at BB-8 to 0/29 at BB-64 (p = 3e-4), while omissions fall from 12/36 to 7/36 (p = 0.28), so all 7 remaining errors are `none` (commission share of errors 9/21 → 0/7, p = 0.06). GPT makes no errors at BB-64, so it cannot show the order. This is consistent with an information-sufficiency reading, which a BB-16 composition or a third agent could test. For GPT, the proxy at 8 queries matches NAME somewhere between BB-16 and BB-64 [PR] (0.25 / 0.67 / 1.00 vs 0.96). For Haiku it matches BB-64 on commissions (1/27 vs 0/29) but not on NAME (5/12 vs 8/12).

Delete "The pattern therefore reflects information sufficiency in general". In §8's "three further framings", keep "suggests measuring a proxy's value as the gold budget at which the error composition matches".

### F8. Grader scope, and give the removal half real content  (+0.2; C1 fixes; R3 major 3 "the SAE contributes little / SHIFT rhetorical")
- §3.1: replace "(176/176)" with: "in all 100 SAE runs no named slot fails removal or keep (0 `removal_short` / `keep_violated` in 400 records; in the main study, 176/176 correctly named cues pass)".
- §2.2: add "every shipped episode has 1 certified-null and 3 planted probes; the generator draws 1 to n−1 nulls per episode".
- Table 1: write "86/86 coded main-study and harder-variant rollouts clean". Add "resists every scripted and observed exploit in the November validation".
- §3.3, replacing "The removal half is a knob (τ). At the shipped τ it never binds …":
> The removal half is a knob, and tightening it bites. Regrading the stored submissions (agents not told) at τ = 0.30 cuts hard passes from 45 to 33 of 64 main-study runs and from 28 to 21 of 36 Open-8 runs; at τ ≥ 0.50 none pass [EX, regrade]. At the shipped τ = clip(0.6 × reference, 0.15, 0.6), removal decided no grade. On traps, the 16-latent reference removes little of an error-term cue, so τ_m sits at or near its 0.15 floor; that is how a ≤16-latent ablation still passes. This paper's verdicts are therefore naming verdicts, and the SAE acts mainly as a ranked candidate list. That role is the proxy this paper studies.

Report per-trap τ_m from grade.json in Appendix C. The main-study trap near-misses show graded removal 0.19-0.22 against τ 0.15-0.16 (CROSS_MODEL_STUDY.md:271); verify before quoting. This answers R3's "error-term trap vs removal pass" tension without new runs.

### F9. Audit rule: "comparable", not "matches"; why it is not a restatement; cost  (+0.1; C6; R1 minor 8; R3 minor 10)
- Replace "**A trace-based flag does as well on the trap probe.**" with "**A trace-based flag is comparable on the trap probe.**" Then write: "11 rechecks catch 11 of 17 failures, against 16 rechecks catching 13; together 18 rechecks catch 15. Unlike the flag, the verdict rule needs neither the logged queries nor knowledge of which probe is the trap. Applied to every planted probe, 'rank 2 never isolated' would flag most ordinary verdicts too."
- Add one sentence answering R1: "The rule is not a restatement of the composition result. Its value lies in the regime contrast (2.9× with the proxy vs 1.2× without at matched budget) and in being free: an evaluator needs only the verdicts."
- Keep the "rechecks differ in cost" paragraph. Add "and the judge in §6 is not a cheap substitute for that recheck (41/44 credited)".

### F10. q-table: one assumption clause, a precise reversal, and a corrected direction (iv)  (+0.05; C7; R1 minor 6)
- After "Holding the observed per-probe rates fixed", add: "(assuming per-probe rates do not shift with q; the prompt does not disclose how many probes are cued, so agents cannot condition on it)".
- Replace "Without the proxy the ordering can even reverse at high q (Appendix C.6)" with: "Without the proxy the ordering reverses by q = 0.5 (25.0% vs 39.3%; BB-8 rates, C.6)."
- Change direction (iv) to "1-3 nulls per episode (the generator's existing range; zero nulls needs a code change), disclosed or not". Measuring agents' `none` propensity directly would replace the extrapolation.

### F11. Expand §8 beyond the four shipped probe types, per the user request  (+0.2; user request; R1 major 2, R2 weakness 11, R3 to_raise 6)
Replace the "Directions the environment already supports" paragraph with the text below. It is wording only: no runs are claimed, and each item is labelled by what already exists.
> **Directions the environment already supports.** Every agent run here uses four shipped probe types (easy/near-threshold, null, trap, two-part). The generator and bank support more, and each direction below needs only certified-null items next to planted ones.
> *Combinations of shipped types:* (i) **null + decoy**, a null probe on which the proxy shows a strong spurious latent. Agents made 0/100 null false claims, but a proxy-led scripted policy already false-claims on 7% of bank null probes (band V1, frozen unit [SC]). This tests whether named claims stay trustworthy when the proxy invites a commission. (ii) **Trap × two-part**: a [decoy] over a nested [main]. (iii) **Deep trap**: the [main] outside the proxy's top-k, where the top-two policy scores 0.00 [SC].
> *Types in the bank that no agent has run:* (iv) **two-main probes** (18 bank units). One verdict can then be partly right, which adds a third error type, the *incomplete positive*. Scripted band policies name a set other than the planted pair on these units [SC]. A two-main probe with one trapped cue would show whether the proxy turns omissions into incomplete positives.
> *New knobs on the proxy and the gold:* (v) **proxy-fidelity dose-response**: vary the [decoy]'s proxy strength (1.8× by construction here) or the [main]'s proxy rank (1, 2, 5, 20, absent), or SAE width and layer, and trace error composition against proxy error. (vi) **an exact-budget sweep with the proxy** (Open-4/8/16). The harder variant at 4 texts already shows 8 of 9 errors as `none`. (vii) **noisy gold**: exact queries with calibrated noise, which tests whether "read correctly once run" survives realistic measurement. (viii) **a forced-allocation arm** ("exact-test the proxy's top two before concluding"), the causal test of §5.4. (ix) **null share varied per episode** (1-3 nulls, disclosed or not).
> *New evaluator-side arms:* (x) **a costed second opinion**: a second agent with k exact queries rechecks only `none` verdicts, which measures the audit rule's real cost and catch rate. (xi) **judge variants**: a judge with tool access, or one told the null share, to test whether J3's blind spot closes. (xii) **contract variants**: an explicit "inconclusive" answer or asymmetric penalties.
> *Beyond this task:* (xiii) more agents at matched budget (the Luna arm; BB-8 for the Claude agents; one model in both harnesses), and (xiv) a second domain with certified nulls, e.g. ML experiments where some interventions have a planted effect and others none.

Before quoting the "7% of null probes" and "two-main" scripted figures, verify them against followup/solvers/README §5: V1 null 0.072 and two-main 1.000 in the frozen unit; in the prompt unit, null 0.022 and two-main 0.011-1.000 by variant. Quote them as "[SC], frozen unit", or drop the numbers and keep the directions.

### F12. Length, figure and labels  (+0.1; R1, R3 nitpicks; all three call it dense)
- The body is over 8 AAAI pages. Cut §5.5's supplementary paragraph to one clause. Move the q-table, Table 6 and the two-part paragraph's second half to the appendix. Merge recommendations 3 and 4.
- Render Figure 1 as an actual figure; two stacked bars plus an inset can be drawn from Table 2/4 counts.
- Use at most four evidence tags in the body ([PR], [EX], [RC], [SC]). Fold [PR-d] and [DS] into prose.
- Housekeeping: use one direction label throughout (folder d5, direction d6). Update the header comment's provenance line to cite updates/round_9.

## 3. Nitpicks to ignore (or answer in one clause at most)
- A GLMM with agent, item and run random effects (R2). The hard-slot run-level test (F2), item-stratified CMH, leave-Haiku-out and clustered bootstraps are enough for a workshop. A model fitted on six items adds nothing.
- Percentile bootstrap at the 100% boundary (R2). Label the Open-8 interval descriptive; the four-agent interval carries the claim.
- Per-agent lift "2.0-2.5×" vs GPT 2.54, and the Wilson/Bowyer attribution. Ignore these.
- Cost per verdict and per error caught (R2). At most add one sentence from per-run rows; do not add a table.
- MDE/power for Haiku's 12-run arms. One clause in Limitations: "12 runs per arm detect only large run-level effects".
- "The audit rule restates the composition" (R1). Answered in one sentence (F9).
- The 47 vs 50 and 49 vs 50 denominators. A caption clause (F5) covers them; do not reanalyse.
- R3's call for a LEACE or linear-erasure baseline, and the SHIFT human skyline. Out of scope; F8 narrows the claim instead.
- Recomputing anything from BB-8 non-hard slots per run. This is impossible by construction and is already in C.1.

## 4. New in updates/ (round_9_manual_1112T0830Z.md, newest; supersedes earlier files)
- **Judge J1-J4: COMPLETE and pre-registered** (gpt-6.1-terra; 214 runs, 856 slots; $1.97).
  - J1: κ = 0.002 on hard slots (confirmed). J2: false credit 53/68 = 0.78 (confirmed). J3: 41/44 vs 12/24, p = 9e-5 post hoc (as predicted). J4: all-slot κ 0.12, null 0.45, planted 0.06, AUROC 0.71.
  - Per agent: hard-slot κ GPT 0.08, Haiku −0.08, Opus −0.09, Sonnet −0.07. False credit 18/26, 24/30, 6/6, 5/6. It also rejects 32/146 certified-correct hard slots.
  - The run set pools SAE and black-box arms and includes BB-16 and the harder variant. Scope: one judge, one prompt; messages were not written as reports. → F1.
  - judge.json is not in the local checkout at 2ec5800, so per-arm splits are unverifiable here.
- **Luna arm: in progress**, about 24 of 60 counted runs, no outcomes computed by rule. The Terra validation reproduced (trap rank-2 isolation 11/12, trap NAME 11/12, NAME 23/24). Write it as pending, and the paper must not depend on it. Its tests concern widening and NAME, not composition.
- No [OCT] material in the update.
- LEDGER dead claim 10 ("any judge result") is now superseded for J1-J4 only. Luna stays dead until results land.

## 5. Combos and new directions (user request: "explore more directions or combos, new ones outside the 4")
Inside this paper, F11 adds 14 concrete item, proxy, gold and evaluator directions, five of them outside the shipped types. For the loop, the other drafted directions are d1 environment-first, d2 proxy-and-gold, d3 best-arm identification, d4 process failures, d6 stage-graded and d7 SAE as testing capacity. New combos outside them:
- **N1. "Certified grade vs judge: what report-reading cannot see"** (d5 + J1-J4). This has the highest CFP fit: LLM-as-judge reliability, ground truth stronger than reviewer opinion, and instrument validity. Headline: the judge is at chance on the deciding slot, and its blind spot is the silent negative, which is the error type the proxy leaves. The error-composition result becomes the "why it matters" half. Risk: one judge and one prompt. Ceiling about 7.5 without runs.
- **N2. d5 as the error-type section of d1 or d2.** Tables 2-4 and §6 drop into the environment paper as "what a certified-negative grader measures that a score hides". This is the best merge if the tournament picks d1/d2.
- **N3. "Null share as an evaluation design parameter"** (prevalence, NPV, q-table, the audit rule's dependence on q, generator range 1-3 nulls). It is too thin alone without the varied-q run. Keep it as a section, not a paper.

## 6. Ceiling
- Current reviews: 6 / 7 / 6 (mean 6.3), unchanged from r1.
- With F1-F12 (wording plus committed counts, J3 included): **about 7, range 6.7-7.3.** The biggest lifts are F1 (J3 is what R2 and R3 asked for), then F2/F3 (honest composition test, invariant ratio, abstract) and F11 (the user's and reviewers' "beyond the four").
- Retitled toward N1 (judge + certified negatives), with the same data: up to about 7.5.
- 8 needs new runs: null+decoy or two-main items, a Claude BB-8 arm (or Luna composition) so the omission side is not Haiku's alone, a held-out generator-item replication, or an empirically varied null share. That is out of scope for this round.
