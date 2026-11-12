# Critic r3, direction D2 (proxy-and-gold recipe)

Reviews: 6 / 7 / 7. Rigor 7, CFP fit 9 from all three; confidence 0.75–0.8. All three rate the headline "partly" supported. The verdicts confirm every load-bearing number. C1, C2, C3, C7 and C8 are supported. C4, C5, C6, C9 and C10 are overclaimed in wording only.

## 1. Diagnosis (5 lines)

1. What earns the 7s: the pre-registered matched-budget C1 with its item-level sign test, the grader validation, the trace-derived allocation curve and the pre-registered judge study (κ = 0.002; 41/44 false credit on confident "none"). The reviewers praise these and the numbers hold.
2. What caps the score is the same major point from all three reviewers: three rank-2 trap items, an item-level floor of 0.125, and a scripted Π₂ that ties GPT. Reviewers 2 and 3 add a second major point: nothing positive is said about what makes GPT widen on the trap probe (and on 11/20 two-part probes), so "recognises which probe needs widening" is under-supported.
3. The headline in its current form (targeted widening: the proxy concentrates exact tests on its top two, and success depends on reaching the runner-up on the probe where the head is wrong) is supported as an item-conditional, exploratory finding. Two phrases are not: "detects where the head is wrong" (the data say "widens on the hard probe; trigger unknown") and "decided before any gold result returns" (the operational definition is a 10-second window, and for GPT, which sends all its gold in one burst, the claim is trivially true).
4. Writing and existing data can fix most of the rest: one population per table, consistent wording, three OCT-contaminated sentences, and a body about 1,800 words too long for 8 AAAI pages (6,860 words plus 5 tables and 4 figures).
5. The remaining gap to 8 needs new items (deeper or fresh traps), which are not allowed now. The realistic ceiling with writing fixes alone is about 7, with one reviewer possibly at 7.5–8.

## 2. Prioritised fix list

### Fix 1. Recast the widening mechanism honestly: "targeted to the hard probe, trigger not identified". Name the untested alternative and use the gold budget as the knob that separates targeted from blanket widening. [writing + existing data; +0.3, answers the shared major point of R2 and R3 and part of R1's]

Replace the §6.3 subsection "Is the widening a magnitude rule?" (whole paragraph) and the sentence "This is not a fixed top-two rule … needs a wider batch." with:

> **What the widening tracks.** GPT widens on the *hard* probe, not on "head wrong" as such. It reaches the runner-up on 23/24 trap probes, on at least 11 of 20 two-part probes (where the head is right and the runner-up is the cue's parent) and on 5/88 ordinary probes. Its passing trap runs put 3.95 gold texts on the trap probe, against 1.16 on each other probe (20 of 21 runs put more there). We could not identify the trigger. None of three zero-gold tells we scored on the bank reproduces this selectivity (exploratory; Appendix E):
> - The band rule in the prompt's unit fires on the [decoy], and as often on ordinary as on trap probes (0.36 vs 0.36).
> - The band rule in the proxy's own unit (post hoc) fires on every shipped-trap cell, so as a widening trigger it would match GPT on traps. But it also fires on 21% of single-cue ordinary and 26% of null bank probes, against GPT's 6% on the shipped ordinary probes.
> - The calibration tell separates traps from ordinary probes only partly (AUROC 0.84 on the bank). Catching every shipped trap flags 62% of ordinary probes and 77% of null probes.
>
> These rates are bank rates; we have not computed them on the shipped ordinary probes alone. Band reasoning was no more common in passes than in failures (4/31 vs 8/55, reader-coded). One natural rule we did not score: on a trap the runner-up's proxy reading is about 0.56 of the head's by construction, and the prompt allows "one or two" main cues, so testing both strong candidates is a reasonable response to an ambiguous proxy. If that is the trigger, the finding reads "agents widen where the proxy's top two are close". That is still gold spent where the proxy is least decisive, and step M4 of the recipe measures it whatever drives it.
>
> **The score can be made to reward targeted rather than blanket widening.** At B = 8, Π₂ ties GPT (0.96) because it can afford the top two on every probe. At B = 4, testing the top two on every probe would need 8 texts. In the exploratory harder variant (traps at 4 texts), GPT passed 3 of 4 trap runs. The gold budget is therefore the knob that turns the trace contrast into a score contrast; we leave its powered use to fresh items.

Also edit:
- Abstract: "Exploratory analyses tie trap success to widening the tested set to the proxy's runner-up on that probe, usually in the first gold batch" → "Exploratory analyses tie trap success to widening the tested set to the proxy's runner-up on that probe, usually in the agent's opening burst of gold queries".
- §1: "whether the tested set widens to the runner-up *on the one probe where the head is wrong*, which is usually decided in the first gold batch, before any result returns" → "whether the tested set widens to the runner-up *on the hard probe*, which includes the one probe where the head is wrong; this is usually decided in the opening burst of gold queries". Delete "Every model widens more there than elsewhere; GPT 6.1 Terra almost always does, Haiku seldom." and use Fix 2's wording instead.
- Optional existing-data analysis, available only from the git-ignored `results/private_1112/followup/solvers/` per-unit outputs, which are not in this checkout: score the rank-2/rank-1 proxy-ratio rule with the band machinery. If the author can run it, report its trap / ordinary / two-part firing rates in one line. If not, keep the "did not score" sentence above.

### Fix 2. One population per table and per contrast (Table 4, §6.6). [existing data; +0.2; R1, R2 and R3 each list shifting denominators]

Make Table 4 entirely main study + Open-8, so that the printed p-values belong to the printed counts (C3 verdict):

| model (harness) | trap hard slots passed | runner-up isolated, trap probe | runner-up isolated, rank 1 true | within-model Fisher p (probe-level, descriptive) |
|---|---|---|---|---|
| GPT 6.1 Terra (Codex) | 18/20 | 17/18 | 16/96 | 2.4e-10 |
| Opus 5.5 (Claude Code) | 6/8 | 4/7 | 1/38 | 0.0011 |
| Sonnet 5.5 (Claude Code) | 6/8 | 5/8 | 2/37 | 0.00084 |
| Haiku 5.5 (Claude Code) | 3/14 | 5/14 | 7/70 | 0.025 |

- Caption: "Main study + Open-8 (8 gold texts). Every model widens more on the trap probe than where rank 1 is true; models differ in how often. Item-level floor with three trap items: 0.125 one-sided. With held-out runs GPT's trap figure is 23/24."
- Delete the italic line under Table 4 ("Columns 2–3: all November SAE runs…").
- §6.6 replacement: "On the same runs the width difference is 5/14 vs 9/15 (p = 0.27): within one harness the pass gap is significant at run level and the width gap is not." Drop "5/16 vs 12/20 with held-out runs included (p = 0.11)", because those held-out runs include 4-text budgets. Add after the item-stratified p: "dropping any one item, 0.024–0.086; Haiku's Open-8 runs come from a different block".
- In the 23/24 vs 5/88 sentence, keep the stated scope ("all GPT SAE runs, held-out included; 44 runs"). That headline contrast stays on its own population.

### Fix 3. Make "chosen early" carry content: report it for Claude, where it is not definitional; define the batch operationally. [existing data, computed here; +0.2; R2 calls the timing result near-definitional, R3 echoes it]

Replace the first paragraph of §6.4 with:

> On traps, testing the [main] nearly guarantees a pass (§6.5), so the informative question is *when* the width is chosen. GPT sends all its gold in one burst (40/40 runs with the proxy), so for GPT the first batch is the whole allocation. The timing result has content for Claude. Among the 29 timed Claude trap runs (main + Open-8), 9 of 14 passes and 0 of 15 failures exact-tested both the [decoy] and the [main] in the opening burst (gold calls within 10 s of the first; run-level Fisher p = 2e-4, conditional on three items). For Opus and Sonnet alone the split is 7 of 11 vs 0 of 4 (p = 0.08); they also passed by other routes. Pooled over agents, 25 of 30 passes and 1 of 17 failures had a wide opening burst (agent-stratified, not item-stratified, p = 2e-4; Appendix F).

The counts come from Appendix F's route table. Claude: S1 passes 3+4+2 = 9 of 14 passes, 0 of 15 failures; p computed with `stats_lib.fisher2(9,5,0,15)` = 2.0e-4 and `(7,4,0,4)` = 0.077.

Also:
- Failure-modes bullet: "Failure to follow up is a minor part" → "Failure to follow up explains few failures". Then "Only 4 failures, all Haiku, had gold left and never exact-tested the [main]" → "Only 4 of 17 failures, all Haiku, had gold left after the [decoy] result and never isolated the [main] (one tested it only in a bundle)".
- Appendix B "Wide first batch" definition: add "(sent before any result was read, operationalised as within 10 s)".

### Fix 4. Provenance hygiene: three untagged sentences pool October runs; resolve the [OCT-CHECK] placeholders. [writing + existing data; +0.15; R1, R2 and R3 all flag the placeholders]

- **§6.4 "Passing Claude runs put more gold on the trap probe than failing ones (mean 4.4 vs 3.1 texts)".** This is MIXED: rebuttal T6 pools the 11 Opus 4.8 October runs (CALC/11 says so) and it is untagged. Replace it with the November-only GPT figure already used in Fix 1, "GPT's passing runs put 3.95 texts on the trap probe vs 1.16 on each other probe (20 of 21 runs)", or delete it. Do not keep 4.4/3.1 untagged.
- **§6.5 "stating … that the proxy can be wrong was not protective (reader-coded)".** It rests on the MIXED 25/28 figure. Use November P3 (`failure_modes_mech.json`): "Most Claude trap runs stated before their first gold query that the proxy can be wrong (24/30; Haiku 12/14, the agent that failed most): stating it was not protective."
- **§6.2 held-out.** Make the 15 current-model runs primary: "On the 15 current-model held-out runs, all three R1 criteria hold (28/39 = 72%, 9/39, 3/39, 1/195; split post hoc). The pre-registered verdict, which pools 11 earlier-model runs, is in Appendix I [OCT-CHECK]. Pre-registered R2 (prefix) and R3 (R1 on ordinary probes alone) were also confirmed on that pool [OCT-CHECK]. The 12 previously read runs had been read only for their trap probe. One pre-registered test, R4 (spare gold to non-hard probes), failed (Appendix I)." Print no OCT number in the body. The 44.4% vs 45% figure stays in Appendix I with [OCT-CHECK].
- Table 2, held-out row: keep "15 current-model + 11 earlier-model [OCT-CHECK]". Add "primary: the 15 current-model runs".
- §6.2, scope the prefix sentence (C2 verdict): "Pooled over all four agents with the proxy (main + Open-8), tested sets are proxy prefixes in 208/231 planted audits (GPT 95/104), against 44/162 without the proxy (BB arms, budgets pooled) and 23.4 under uniform choice." Add to the rank sentence: "rank 3 does not change (9/72 vs 5/72, p = 0.40)".

### Fix 5. Cut the body from 6,860 to about 5,000 words. [writing; +0.2; R1 says the paper "likely runs past 8 pages", and all three call it very dense]

Targets (current → target words):
- **§2: 1,082 → 700.** Move the trap-construction mechanics (w ← w − γ(w·d)d, αz, projections) and the generator description into Appendix B. Keep one sentence per probe type plus the model-organism sentence (Fix 8).
- **§6: 2,034 → 1,500.**
  - Fix 1 replaces a longer paragraph.
  - Compress the success/failure bullets to the trap and two-part lines.
  - Move "black-box" success modes and the text-only listing experiment to the appendix.
  - Drop the Table 3 Fisher row. Keep rank 2 (p = 0.0055) and rank 3 (p = 0.40) in the text, labelled candidate-level and descriptive. This also removes the 2.6e-14 that R1 objects to.
- **§9 related work: 489 → 330.** Keep Circuit Oracle, Pando, ACED, Klayman & Ha, PPI/active testing and Table 5.
- **§5: 437 → 300.** The token-matching paragraph moves to Appendix J, leaving one sentence in the body (Fix 7).
- **§8: 157 → 120** (Fix 6).
- **Abstract: 201 → about 170.** Write "six scripted cheating policies score 0", not "No scripted cheater scored". Cut the abstract to its four central numbers: 6/24 → 23/24; 23/24 vs 5/88; rank 2 on all traps; κ = 0.002.
- **Add one line under Table 2:** "Every in-text fraction names its population; the GPT headline contrast uses all GPT SAE runs, and every per-model table uses main + Open-8." This answers the reviewers' "single table mapping each claim to its population" without adding a table.

### Fix 6. §8 SHIFT: same goal, different and data-richer route; drop "without being told the method". [writing; +0.1; R3 minor, R1 and R2 nitpicks; the brief requires the section]

Replace §8 with:

> SHIFT (Marks et al. 2025) removes spurious reliance with a human reading latent meanings and **without disambiguating data**: latent → meaning → judgement → ablation. Our agents reach SHIFT's goal, targeted erasure at a reference-calibrated bar, without being told how to find the cue or choose latents, and by a different route: **property → counterfactual edit → latents**. They use exactly the resource SHIFT assumes is absent, namely disambiguating texts they write themselves.
>
> - **Logs.** All 100 SAE runs encoded their own edited texts and called `probe_gradient`. Every correctly named hard cue cleared removal (73/73 slots), against 1 of 6 hard slots for the 16 largest-attribution latents, so latent choice is targeted, not trivial.
> - **Transcripts (reader-coded).** Latents were chosen by g_i·Δf_i with a topic filter. This is close to Karvonen et al.'s (2024) spurious-feature-informed selection, which they found to be a good proxy for SHIFT.
> - **Latent meanings were optional.** In the main study `latent_examples` was called by GPT 15/16, Sonnet 6/16, Haiku 3/16 and Opus 0/16. Among Claude runs it showed no detectable association with passing (5/9 vs 26/39, p = 0.70). Opus passed 11/16 without it.
>
> Where the hypotheses are eight enumerable properties, a latent-reading process rubric would be invalid. We make no claim about SHIFT's open-concept setting.

Contribution 5 → "**A comparison with human practice** (§8): agents reach SHIFT-style targeted erasure (Marks et al. 2025) at a reference-calibrated bar without being told how to choose latents, by a counterfactual-attribution route rather than by reading latent meanings."

### Fix 7. Claim-precision batch from the verdicts. [writing; about +0.2 combined; these remove the "overclaimed" verdicts]

- **C1 (§6.1).** Change "(item-level sign test p = 0.031, the minimum with six items)" to "(item-level sign test, post hoc, p = 0.031 two-sided, the minimum with six items)". The "[pre-registered]" tag covers C1, C2 and C4 only.
- **Token cap (§5).** Replace the sentence (R2 calls the current version trivially true) with: "C1 stays ≥ +0.71 at every output-token cap of 68k or more (+0.83 at the Open-8 maximum, 86k), and falls to +0.46 at the Open-8 median (62k, a cap that fails half the Open-8 runs by construction); C4 ≥ 0 at every cap."
- **Π₂ (§6.3 / Appendix E).** Change "Π₂ scores 0.96, matching GPT's 23/24" to "Π₂ scores 0.96 on traps and two-part alike, the same as GPT's Open-8 NAME (23/24; traps 11/12), but widens on every probe".
- **C6 (§6.5).** Replace "This rules out credulity:" through "frozen unit)" with: "Credulity is rare. The [decoy] was rejected in 30 of the 31 main-study trap runs that tested it (reader-coded). The one exception, a Haiku run, claimed it although its own gold test disagreed. All 11 slots with a mechanically measurable proxy-vs-gold contradiction (topic unit, exploratory; none in the frozen unit) followed gold." Add to the commission sentence: "The omission drop is mostly GPT (21 → 1; Haiku 12 → 9)."
- **C7 (§7).** Replace "and its κ on GPT's own runs is 0.08, so self-preference does not explain it" with: "Self-preference does not explain it: the judge gives GPT's own failed runs less false credit (18/26) than Claude's (35/42), and its κ is near zero on both (0.08 and −0.05)." Tag the bootstrap interval, the always-pass baseline and the by-population split as post hoc. The by-agent and by-access tables are pre-registered J4 descriptives.
- **C8 (Table 1, §3, abstract, contribution 1).** Rollout row: "86 main-study-period runs (64 counted, 18 harder-variant, 4 smoke; one unblinded LLM reader): clean; 0 web or subagent calls in 2,649 Claude tool calls. Block 1 and held-out runs rely on the regrade and the tool server's isolation (separate daemon user, unreadable weights, per-rollout latent re-salt, leak scan)." Difficulty-knob sentences in §2.3, §3 and Appendix C:
  - write "0 of 73 (45 main + 28 Open-8) at τ ≥ 0.5", not "0/45";
  - anchor the knob on the feasible rows: "at τ = 1.0 × reference, 62 of 100 hard slots pass (38 + 24); capping at 8 latents with τ = 0.9 × reference leaves 16; a flat τ ≥ 0.5 removes every pass and may exceed what latents can remove on traps";
  - in Table 1 write "1 of 6 hard slots", not "episodes", so the units match 73/73.
- **C2 (§6.2).** Covered in Fix 4.

### Fix 8. State up front that the trap is a model organism. [writing; +0.1; R3's third major point]

- **§1**, after "on *trap* probes": add "The trap is a deliberate weight edit, a model organism: it tests whether an agent notices that a lossy readout disagrees with exact queries, not how often natural SAEs mislead on probes trained on real data."
- **§2.2 item 4**: end with the same clause.
- **§10**: keep the existing sentence.

No new trap build. The hardercue attempt (0 of 532 fits passed for a plain planted cue) shows that natural-cue construction is non-trivial; leave this out of the paper.

### Fix 9. Intro evidence: replace the non-significant Haiku 0/6 vs 2/6. [writing; +0.05; R1 nitpick]

Replace "and agents that skip it fail: with the proxy, Haiku named no trap cue … (Block 1, descriptive)" with: "and agents that skip it fail: with the proxy, a trap slot whose [main] was never exact-tested passed 3 of 16 times, against 27 of 31 when it was." This is H5, November data. It is near-definitional, and the sentence is only meant to say that skipping costs a pass. Keep the Haiku 0/6 figure out of the body.

### Fix 10. Luna arm text. [writing; +0.05]

§6.6: "A pre-registered GPT-6 Luna arm in Terra's Codex harness (60 counted runs; 23 collected as of commit 1b7468b; no outcome computed before the last) has fixed readings. If L1 (Luna widens on traps less often than Terra) holds, width depends on the model within one harness. If it does not, a weaker same-family model does not reproduce the cross-harness gap. L1 can detect only a drop to at most 10 of 18 trap runs against Terra's 11/12 (one-sided Fisher)." Update the count at submission. If Luna completes before 20 Nov, its L1 result becomes the within-harness model evidence that R1 asks for. Insert it under the pre-written reading whichever way it falls.

### Fix 11. New runs. Not allowed now; use this wording instead. [writing; 0 now, the ceiling lever later]

- **Fresh or deeper traps (all three reviewers).** Do not promise results. §10 already says what is needed. Keep it and add the scripted evidence that the knob discriminates: "Moving the [main] to proxy rank 3 drops Π₂ from 0.97 to 0.00 while the hedge holds at 0.59 (bank, B = 8), so a rank-3 item would separate one-step widening from search."
- **Evidence-access judge (R1, R3).** One sentence in §7 scope, already present: "a judge with the gold-query log is a different instrument and the natural next comparison".

### Fix 12. Small consistency items. [writing; +0.05]

- §3 "agents can preview removal exactly (71/86 did)": the denominator is the 86 coded runs. Write "(71 of 86 coded runs)".
- §11 spend: "about $87 OpenAI (rising with the Luna arm) and $78 Anthropic at the time of writing" (round_3: 86.80 at 1b7468b; round_1: Anthropic $78.403).
- Contribution 3: change "chosen early" to "usually chosen in the opening burst of gold".
- Conclusion: change "decided in the first batch" to "usually decided in the opening burst of gold queries", and add "on these three rank-2 items".

## 3. Ignore (nitpicks or confounds no paper can control)

- **Mean-ablation reference means (R3 nitpick).** The prompt defines the mean, and the grader applies it identically to every agent. The choice is part of the task, not a validity threat. Spending space on a sensitivity analysis buys nothing.
- **Contamination and refresh plan (R1 nitpick).** §10 already says comparisons across model generations need fresh generated items, and the generator *is* the refresh plan. Add nothing more.
- **Probe-level Fisher p-values in general (R1).** They are labelled descriptive, and item floors are given. Fix 5 drops the most extreme one; do not strip the rest.
- **Batch-2 item choice, the substrate/hint confound and the harness confound.** These are disclosed, unavoidable in the existing data, and not load-bearing for any confirmatory claim.
- **Natural (training-data) trap (R3 major).** This needs new builds; answer it with disclosure (Fix 8), not experiments.
- **Removal "does little work at shipped τ" (R3).** This is already stated candidly. Fix 7 anchors the knob on the feasible rows; no more is needed.
- **Information tells as "design flaws" (R3).** They are disclosed, tested and unused (no Block 1 run used the midpoint). That is the right treatment.
- **Generalisation "by analogy" (R1 minor).** The paper generalises the recipe, not the behaviour, and §4's transfer paragraph already gives concrete instances: docking vs assay, and a learned reviewer vs replication. Do not add speculative transfer claims.
- **Contribution 5 "tangential" (R1, R2).** The brief requires it. Shrink it (Fix 6); do not cut it.

## 4. New in the updates file (round_3 and the manual pull at 08:30Z)

- The judge study (J1–J4) is already in the draft. Two things from the update and verdicts should enter it: the per-agent false-credit contrast (GPT 18/26 vs Claude 35/42; Claude-only hard κ −0.05) as the self-preference answer (Fix 7), and the post hoc labels on the bootstrap, the always-pass baseline and the by-population split.
- Luna: still in progress (23 of 60 counted runs at 1b7468b). Per the pre-registration no outcome may be drafted. Add the L1 power line (Fix 10).
- Terra driver validation (11/12 trap runner-up, 11/12 trap NAME, 23/24 NAME) is already in §11. Nothing else is new: the other branches have no commits after the snapshot, and there are no paper/ changes.

## 5. Is this direction worth continuing?

Yes, for one more round, then freeze. Fixes 1–5 address the reviewers' recurring complaints that writing and existing data can answer: the trigger of widening, mixed populations, near-definitional timing, OCT placeholders and length. They should move 6/7/7 to about 7/7/7, with an outside chance of one 8 from the reader who values clarity. The ceiling without new runs is about 7. All three reviewers' remaining major point, three rank-2 items with Π₂ tied, can only be answered with fresh or rank-3 trap items, plus the Luna L1 result for within-harness model dependence. If runs are allowed later, the highest-value experiment is about 3 fresh rank-3 trap items × GPT and Haiku × 4–6 runs. At Luna-like or Terra Open-8 costs ($0.7/run for GPT) that is under $30, and it is the one change that could make the headline item-level and lift the ceiling to about 8.
