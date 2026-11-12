# CRITIC r2, d6 (X1: stage-wise localization = d1 environment + d4 process findings + d2 vocabulary)

**Inputs.**
- d6/draft_r2.md.
- 10 claim verdicts: supported C1, C2, C3, C4, C5, C9; overclaimed C6, C7, C8, C10, C11. None contradicted.
- 3 reviews, scored 7 / 7 / 7 (rigor 7 / 7 / 7; CFP fit 8 / 9 / 8).
- LEDGER.md, lit/, and updates/round_9_manual_1112T0830Z.md (the newest update).

**New existing-data checks.** These are in `paperloop/chk_d6r2/`:
- `judgegrade.py` reads the committed judge.json at a20fa7b.
- `misc.py` reads rollouts.csv and rows_r1112.csv.

All of them are read-only and use November-period data only; no [OCT] number is an input.

## 0. Five-line diagnosis

1. r2 is now a clear accept at 7/7/7, with no contradicted claim. The open problems are five overclaims, about ten wrong or mis-scoped numbers, and density, not the direction.
2. All three reviewers make the same structural objection: two of the four stages are ceilinged controls, each hard stage rests on three items, and combinations are not run. Wording cannot remove it. It caps this direction at about 7.5 without new runs.
3. The judge study is presented as κ = 0.002 and nothing more. One reviewer calls it "close to tautological". The committed judge.json already shows something stronger: graded by the judge, the paper's own pre-registered matched-budget study reaches different conclusions. The budget effect shrinks from +0.58 to +0.11, and BB-64 vs Open-8 changes sign (F1). This answers "so what" for the CFP's "sensitivity of rankings to judge".
4. The draft misses a second item-level result. With the proxy, GPT commits all 8 exact texts in one burst in 24/24 runs; at the same budget without the proxy it does so in 0/24 (6/6 items, p = 0.031). This is the mechanism behind "the decision is made before the evidence". It turns that phrase from a definitional observation into a matched-budget proxy effect (F5).
5. The user asked for directions or combos outside the four. The paper's "Beyond four stages" section should name the new design-tempo and report stages as measured, and list the unrun probe combinations as such. §5 below gives four new paper-level directions for the loop.

---

## 1. Prioritized fixes (12)

These are wording fixes plus counts that are already committed; no new runs. Score deltas are expected changes to the mean review score. They overlap, so they do not simply add up.

### F1. Re-grade the pre-registered study with the judge, using committed aggregates. Put the result in §6, one clause in the abstract, and the conclusion. (+0.3; R3 "tautological", R1 and R2 "judge scope", CFP ranking sensitivity)

`judgegrade.py` computes the judge-implied pass rate as certified pass − false blame + false credit, per cell of judge.json. Hard slots use the naming grade, which is the pre-registered certified outcome. The three Block 1 arms each hold 36 slots with the same agent mix (GPT 24 + Haiku 12):

| Hard slots, GPT + Haiku | BB-8 | Open-8 | BB-64 | Open-8 − BB-8 | BB-64 − BB-8 | BB-64 − Open-8 |
|---|---|---|---|---|---|---|
| Certified | 11/36 = 0.31 | 28/36 = 0.78 | 32/36 = 0.89 | +0.47 | +0.58 | +0.11 |
| Judge | 20/36 = 0.56 | 30/36 = 0.83 | 24/36 = 0.67 | +0.28 | +0.11 | **−0.17** |

The judge also changes each agent's rate, computed on that agent's own run set: Haiku 0.45 → 0.76, Opus 0.70 → 0.95, Sonnet 0.68 → 0.79, GPT 0.78 → 0.76. The main-study hard pass rate moves from 0.70 to 0.88.

Insert after the J1-J4 table in §6:
> **The judge would change what the study concludes [PR-d counts; arithmetic done after the fact].** We re-score the pre-registered Block 1 arms with the judge's verdicts. The arms have the same agent mix: GPT and Haiku, 36 hard slots each, naming grade. The proxy effect shrinks from +0.47 to +0.28. The budget effect (BB-64 − BB-8) shrinks from +0.58 to +0.11. The BB-64 vs Open-8 comparison changes sign (+0.11 → −0.17), because the judge credits 16 of 25 failed BB-8 slots and rejects 12 of 32 passing BB-64 slots. Per agent, it raises Haiku's hard-slot rate from 0.45 to 0.76, and GPT's stays put (0.78 → 0.76), which erases the weakest agent's deficit. So the judge's errors are not noise around the certified grade. They are concentrated on the slots where the stage effects in this paper live. These figures come from aggregate counts without intervals, and they cover one judge and one prompt.

Also make the C9 wording fixes in the same paragraph:
- Replace "a confident 'nothing found' report" with "a 'nothing found' report".
- Write "`none` is how most upstream failures end (13/19 main study; 44/68 failed hard slots in the judge set)".
- Say "certified naming grade" once, where the study is introduced.
- Add "one pre-registered deviation (budget guard raised; no design change)" to C.8.
- Add the per-kind contrast in one clause: "the judge is reasonable where the contract makes the answer checkable (null κ 0.45, AUROC 0.95) and near chance on planted slots (κ 0.06)".

In the abstract, replace "and an LLM judge reading the same runs agrees with the certified grade at chance (κ = 0.002)" with:
> and an LLM judge reading the same runs is at chance on the deciding slot (κ = 0.002); graded by it, the study's budget effect nearly vanishes.

In the conclusion, replace the last sentence with:
> Applied to one judge, it finds that judge at chance on the slot that matters. Grading by that judge would have erased most of the budget effect this paper measures.

### F2. Correct the five statements the verdicts found wrong or mis-scoped. (+0.25; each one is a catchable error)

- **§3.1 (C10).** Replace "all 63 disagreements, read in the raw transcripts, upheld the mechanical value" with:
  > all 63 disagreements upheld the mechanical value under the frozen definitions. On substance, the quantitative flag F1 erred in 6 of 21 items, so we do not use F1; flags F2 and T-D erred in none.
- **§5.1 and C.6 (C4).** Replace "A flat τ of 0.40 (7/45) sits at or above the reference removal on every hard probe" with:
  > A flat τ of 0.40 (7/45) sits at or above the reference removal on 5 of 6 hard probes (within 0.02 on the sixth), so it partly measures the reference ceiling.

  Replace the C.6 caption sentence with: "The flat τ = 0.40 row sits at or near the reference removal on every hard probe." Do not make that statement about the 0.30 row. Add: "The k-cut keeps the first k submitted latents, so the capped rows are a conservative regrade."
- **§5.2 (C6).** Delete "(71/71 rows)". It pools the 11 October Opus 4.8 runs. Replace the sentence with: "On traps, isolating rank 2 *is* testing the true cue, so the content lies in the trap-vs-ordinary contrast." If the count is wanted, recompute it on November rows only, or tag it [OCT-CHECK].
- **C.3 (C2).** Replace "at least one of them is outside the main study" with:
  > Both are Open-8 runs. Haiku's only main-study failure on that item sent its three hard-probe texts in one batch and never tested the [main], so the mechanical measure moves no main-study failure to read.
- **Table 5 text (C2).** Replace "Three acquire failures also err after evidence: …" with:
  > Four acquire failures also err after gold evidence. Two add an untested extra cue (one after testing both the [decoy] and the [main]); one claims the [decoy] against its own test; and one (T5) reads a wrong property out of a bundled contrast that also flipped the [main].
- **LEDGER H5 (outside the paper).** It records "all 4 misreads borderline". Correct it to 2 claim-side + 2 borderline `none`, so later drafts do not reintroduce the error.

### F3. Model differences: concentration, not separation (C8). Apply to §5.0 (iv), the §5.5 heading, table and text, and Contribution 5. (+0.2; it is an overclaim and R2 notes the mixed populations)

- Change §5.0 (iv) to: "(iv) the gap between agents concentrates in a stage-pressured score that the outcome bit dilutes (§5.5)."
- Change the §5.5 heading to: **"Stage-pressured scores locate model differences that the outcome bit dilutes."**
- Replace the trap row of the table with two rows:

  | Trap passes, main study only | 3/8 | 12/16 | 0.10 (item-stratified) | EX |
  |---|---|---|---|---|
  | Trap passes, main + Haiku Open-8 (no Opus/Sonnet Open-8 exists) | 3/14 | 12/16 | 0.010 (item-stratified) | EX |

- Replace "Only the acquire-pressured score separates Haiku…" with:
  > The gap is largest in the acquire-pressured score: trap passes 3/8 vs 12/16 in the main study, and 3/14 vs 12/16 when Haiku's Open-8 runs are added, with Haiku lower on 3/3 trap items (item floor 0.25). It is absent from the hypothesize-pressured score (failures 2/16 vs 5/32, p = 1.0) and diluted in the run outcome (8/16 vs 23/32, p = 0.20).

### F4. Adaptive width: like-for-like populations, no clustered p-values (C6 plus R2 major). (+0.25)

- Replace the §5.2 "Adaptive width" paragraph with:
  > **Adaptive width.** Every agent widens to the runner-up selectively. Rank 2 is isolated far more often when it is the true cue than when rank 1 is: GPT 17/18 vs 16/96, Opus 4/7 vs 1/38, Sonnet 5/8 vs 2/37, Haiku 5/14 vs 7/70 [EX; run-level, 3 trap items, item floor 0.25]. Restricted to ordinary probes, GPT widens on 23/24 trap probes vs 5/88 ordinary ones. On traps, isolating rank 2 *is* testing the true cue, so the content lies in this trap-vs-ordinary contrast. It is not mechanical use of the contract band: scripted band solvers (frozen unit) fail all 3 shipped traps, and 2 of 36 read trap passes measured the [main] by band reasoning [SC/RC]. Use of the midpoint tell was checked only in Block 1 (0 runs).
- **Table 6.** Drop the Fisher p row. The 2.6e-14 treats 360 slots as independent. Add to the caption: "Counts are probe slots clustered within 24 runs and 6 items; descriptive."
- **§5.2 rank-prefix sentence.** Name the null: "against 23 expected if, for the same number of tests per probe, the tested candidates had been drawn without regard to proxy rank".
- Drop the "p = 4.8e-18" in Contribution 4 and §5.2. Drop "p = 6.2e-5" in §5.5, or label it "run-level, cross-harness".
- Rename "Deference is not the failure" to **"Overriding gold is not the failure."** First sentence: "Agents never kept the proxy's reading against a clean gold pair (0/11 [EX]; [decoy] rejected 30/31 [RC])." Keep the reliance clause.

### F5. Add the proxy-induced one-burst contrast. It is the second result that clears its item floor. (+0.25; it turns "decided before evidence" from definitional into a matched-budget proxy effect)

The source is committed `failure_modes.json` G_one_burst (CALC/03 §D), all counted runs. Every Block 1 item has 4 runs per arm, so 24/24 vs 0/24 means every item is 4/4 vs 0/4. Insert as the first paragraph of "On the trap, the outcome is largely decided by the first exact batch":

> **The proxy moves the design of the gold experiment ahead of the evidence.** With the proxy, GPT commits all eight exact texts within 60 s in 24/24 Open-8 runs. At the same budget without it, it does so in 0/24 BB-8 runs: 4/4 vs 0/4 on every item, two-sided sign test p = 0.031 [EX]. (BB-64: 3/24. Claude main-study runs: 30/47. Haiku Open-8 4/11 vs BB-8 1/12.) Without the proxy, gold results guide the next test. With it, the agent decides which hypotheses earn a gold test before any gold result exists, as a fixed, non-adaptive design like Pando's k = 10 protocol, chosen by the agent itself. One-burst querying does not by itself predict failure (main-study traps: 8/10 failures vs 15/22 passes); what matters is how wide the burst is on the trap probe.

Then add "the proxy turns sequential gold testing into one pre-planned batch (24/24 vs 0/24 runs, 6/6 items)" to Contribution 4 and to the §1 "What the instrument shows" paragraph. Do not write "one-burst causes failure" (dead claim 22).

### F6. Abstract, Contribution 3 and Table 5: label the exploratory results and add the batch-1 robustness check. (+0.2; R2 major on the abstract, R2 minor on forking paths)

- **Abstract.** Replace "On traps, runs whose first exact batch reached the runner-up passed 25/26, against 5/21 otherwise (agent-stratified p = 2e-4; three items)." with:
  > On traps, runs that tested both the proxy's top candidate and its runner-up in their first exact batch passed 25/26, against 5/21 otherwise (exploratory; agent-stratified p = 2e-4; three items). With the proxy, GPT plans its whole gold batch before any gold result returns (24/24 runs vs 0/24 without it).
- **Table 5 caption.** Add (`misc.py`, rollouts.csv): "In the pre-registered batch 1 alone, all 12 failures fall at hypothesize (4) or acquire (8)." This answers the concern that batch 2 was chosen after six GPT results.
- **§5.2 (C5).** Replace "Claude agents alone 9/9 vs 5/20, Fisher p = 2.0e-4" with "Claude agents alone 9/9 vs 5/20, agent-stratified p = 0.002; same direction in all four agents". Define the first batch once, in the Table 7 caption: "hard-probe exact calls within 10 s of the first, sent before any true logit is returned".
- Optional, one clause: "not only the number of texts: among runs giving the hard probe ≥ 3 texts, the [main] went untested in 6/10 failures vs 2/28 passes".
- **Hypothesize scope in the abstract.** Replace "Nested cues are usually pruned untested" with "Nested cues are usually never formed as candidates (reader-coded)".

### F7. SHIFT section: GPT counterweight, correct tags, absolute removal (C11 plus R3 major). (+0.2)

Replace the §5.6 body after the SHIFT sentence with:
> Our agents encode their own edited texts through the SAE (100/100 SAE runs [EX]). In most rollouts they pick latents by gᵢ·Δfᵢ from paired edits [RC]. In 36/50 timed trap runs, the counterfactual for the true cue went through the SAE before the first exact query (a lower bound) [EX]. The route is property → counterfactual edit → latents. Latent meanings are optional, not absent. GPT reads a few latents in most runs (15/16; median 3 calls), while Opus never called `latent_examples` in the main study (0/16) and passed 10/14 runs that used no meaning tool. No association between meaning-tool use and passing was detected among Claude runs (10/16 vs 21/32, p = 1.0) [EX]. Asked text-only and unprompted, 0/12 responses gave a SHIFT-style recipe; with a leading prompt, the step most often missing was judging features (7/12 vs 12/12 for the others) [Exp E]. Agents thus reach the *shape* of SHIFT's goal unprompted: they name the cue and remove at least the shipped fraction of its effect, 176/176 whenever the cue is named. They do not reach its magnitude. Passing trap ablations remove 0.24-0.37 of the [main]'s effect (median 0.26), and two-part ablations 0.36-0.43 [EX]. Most of a trap cue's effect lies in the SAE error term by construction, so the same proxy limit that hides the cue also bounds what any latent ablation can remove. The route is close to SHIFT's feature skyline and to Karvonen et al. (2024), so it is not new; the logs show which tools each step used.

Also drop "(call order is not in the released tables)". The P1 lower bound replaces it.

### F8. Hypothesize wording (C7). (+0.1)

- Replace "once the child cue was exact-tested it always passed (26/26; 24/26 without the proxy)" with "once exact-tested, the child passed 26/26 with the proxy (24/26 without)".
- Replace "This is the route in 7/9 failures (… N1); a second reader codes 4/10" with:
  > Failures mostly never formed it (8/9 by one reading); the usual route was pruning the parent under the alignment rule (7/9 by one reader, 4/10 by a second). In 6 of 10 failures the proxy flagged the parent or child and the agent did not follow it up.
- Replace the "thinkable" sentence with:
  > Text-only, the nested cue is listed at the plain rate (42/60 vs 162/240) but later in the list (21/60 vs 140/240 within the first 8 candidates; exploratory, added after an interim look). That fits GX-Chen et al. (2025): the conjunction is thinkable but ranked too low to win a scarce test, and the contract's alignment rule then prunes it.

### F9. Read and act controls, and Haiku's trap result (C3, C4, R2). (+0.1)

- §5.1: replace "Genuine misreads are therefore 2 in 207" with "Genuine misreads are therefore at most 2 in 207; given its own reading, `none` was consistent with the contract."
- After 176/176, add: "and no named hard slot in the fresh Open-8 runs failed the removal half (28/28)".
- §5.2, replace "Haiku is descriptive and shows no such gain on traps (Open-8 0/6 vs BB-8 2/6)" with:
  > For Haiku (descriptive), the proxy shows no gain on traps (Open-8 0/6 vs BB-8 2/6, p = 0.45). That fits the stage account. The proxy pays only if the agent widens past its head, and Haiku widens least (rank 2 on traps 5/14). The pre-registered Luna arm tests this within GPT's harness (L3).

  Do not write "the SAE hurts Haiku" (dead claim 5).

### F10. Matched-budget and cost reporting (C1, R2, R3 cost frontier). (+0.15)

- **§4.** Replace "the Open-8 − BB-8 contrast stays ≥ +0.71 at any cap of at least 86k" with "C1 ≥ +0.71 at any output-token cap ≥ 68k; +0.46 at the Open-8 median cap". The +0.46 is the honest matched-token figure, so keep it in the body.
- **§5.2.** Replace "acts as acquisition capacity [PR]" with "acts as testing capacity [PR; our acquisition reading]". "Testing capacity" is the pre-registered label.
- **Define NAME once.** Use: "the hard cue named with no extra cue and every null answered `none`". Hard-slot identification alone is 8/24 vs 23/24.
- **Explain C3** in one clause: "C3 (Open-64 − BB-64) was not run, as pre-registered, because BB-64 reached 24/24 (trigger ≤ 0.76)".
- **Intervals.** Add "(6-cluster percentile bootstrap; may under-cover; the sign test is the item-level check)". State the C4 lower bound "0 by construction, since BB-64 has no failure".
- **Cost frontier**, after "the cheapest arm at $0.372 per run" in §2:
  > Exact queries are free here apart from the cap. Pricing each exact query at c, GPT's Open-8 arm is cheaper per NAME pass than BB-64 whenever c > $0.006 [EX; assumed list prices]. In real science, where a gold experiment costs far more than a cent, the proxy arm dominates.

### F11. "Beyond four isolated stages": answer the user's and reviewers' request with what is measured and what is not run. (+0.2; all three reviews list it under to-raise, and the user asked for it)

Restructure §6 into three labelled parts.

> **Two further stages are already measured.**
> (a) *Design tempo:* with the proxy, gold testing becomes one pre-planned batch (F5).
> (b) *Cross-probe triage:* 58% of exact texts go to probes that pass without them (87/88). We state this descriptively, because a pre-registered held-out prediction failed narrowly.
> (c) *Report:* the judge study (J1-J4 plus the Block 1 re-grade, F1).
>
> **Combinations the generator supports but no agent has run.** Each is labelled with the stage pair it crosses.
> - hypothesize × acquire: nested child in the error term;
> - acquire × read: trap [main] at near-threshold reliance;
> - acquire × act: trap × null, where the proxy shows a confident cue on a clean probe;
> - acquire generality: a trap [main] at proxy rank 3 to 5, or a continuous γ;
> - natural proxy failures (feature absorption; an SAE layer mismatched to the probe);
> - two-main probes (18 bank units).
>
> These test the composition prediction: end-to-end pass ≈ the product of conditional stage rates. If stages interact, the four-stage factorization is wrong.
>
> **Arms that would separate explanations.**
> - forced-sequential (batch size 1): harness habit vs proxy-induced design;
> - a process-aware judge given the exact-query log: does the trace recover the certified grade?;
> - a matched-lossiness non-SAE proxy: what is SAE-specific;
> - Luna in Terra's harness: pre-registered, 23 of 60 counted runs collected at 08:23Z, no outcome computed by rule.

Drop the OCT-CHECK sentences ("passing runs put more texts…" and the R4 [OCT-CHECK] clause). Replace them with "a pre-registered held-out prediction about this spending failed narrowly (44.4% vs 45%)" only if that figure is November-only. Otherwise omit it; nothing rests on it.

### F12. Density and length. (+0.15; all three reviewers)

The body is about 7,300 words, plus 7 tables, Box 1 and Figure 1. Eight AAAI pages with that many tables hold about 5,000. Cut about 30%:
- Fold §5.0 into a 2-sentence lead of §5.
- Merge Table 4 into Table 1 by adding a "main-study pass" column, and delete Table 4.
- Move Table 6 and the "Acquisition, not follow-up" paragraph to Appendix C.
- Shorten §5.4 to three bullets of one line each.
- Cut §7 to two paragraphs and move the GX-Chen and Klayman & Ha sentences inline.
- Cut the §8 bullets to one line each.
- Use one label system ([PR], [EX], [RC], [SC]) and drop [PR-d], [HO] and [DS] from the body. Write "descriptive" in prose instead.
- Rename "development runs" to "timed trap runs (main study + Open-8)".
- Lead each §5 subsection with the transferable evaluation lesson in italics, for example: *Ration gold so acquisition is observable*; *Grade each stage from logged gold queries*; *Check judges against certified slots*.
- Figure 1 must actually be drawn. It is described but absent.

---

## 2. Nitpicks to ignore (at most one clause each, or none)

- GLMMs, cluster-robust models and IRT analysis. F4 drops the clustered p-values instead. With 6 agent-run items there is nothing to fit an IRT model on, and the bank has only scripted data.
- A second blinded human coder for the hypothesize codes. Not possible now. F8 reports both readers, and the batch-1 split (F6) covers forking paths.
- A real SHIFT baseline with auto-interp labels, a non-SAE proxy arm, a process-aware judge, forced-sequential, rank-3 or absorption traps, a binding-act agent run, and fresh generator items. All need runs. List them as unrun in F11 and nothing more.
- Checking the main study for use of the midpoint tell. It is disclosed, Block 1 is clean, and the band check is 2/36. One clause is enough (F4).
- "κ = 0.002 is a low bar / J1 threshold weak". F1 replaces the threshold argument with consequences.
- "Judge = same model as one agent". One clause in the scope sentence at most.
- The missing γ range and the error-term share on ordinary probes. F7's absolute-removal sentence covers the substance; the γ range can go in Appendix D if it is in the build logs.
- The 784 vs 771 audit counts, Haiku cost rows, "knowing is not doing", "12/24 mixed cells". Leave these out (dead claims).

## 3. New in updates/ (round_9_manual_1112T0830Z.md, newest; serene-fermi 1b7468b)

- **Judge J1-J4 is complete.** It is already in draft r2 and the numbers match judge.json.
  - New since r2: judge.json's committed `hard_by_access` / `hard_by_population` / `hard_by_agent` cells give the Block 1 re-grade (F1). By access arm, hard-slot κ is BB-8 −0.225, BB-64 −0.20 (AUROC 0.07), Open-8 −0.06 and main study 0.056, so the near-zero κ is not driven by one arm.
  - LEDGER H11 and dead claim 10 ("no judge.json") are stale. Update them.
- **Luna arm.** 23 counted runs plus the pilot are logged by 08:23Z (Open-8 and BB-8 mixed), at $0.04-0.16 per run. Cumulative spend is $86.8. **No outcome may be computed until the last counted run.** In the draft, keep Luna as pre-registered and pending, with the run count.
  - If L1 lands before 20 Nov: supported means "the widening gap is model-dependent within one harness"; not supported means "the cross-harness gap is not reproduced by a weaker same-family model".
  - If L3 lands: it answers the Haiku question in F9.
- No [OCT] material. No number in the draft changes, apart from the F1 additions.

## 4. Existing-data results computed this round (`paperloop/chk_d6r2/`)

- **Judge re-grade of Block 1.** The table is in F1. Arms have the same agent mix (GPT 24 + Haiku 12 hard slots each). Judge-implied pass = certified − false blame + false credit; exact arithmetic on committed counts.
- **One-burst by arm.** GPT Open-8 24/24 vs BB-8 0/24, giving every item 4/4 vs 0/4 and sign p = 0.031. BB-64 3/24; Haiku 4/11 vs 1/12; main-study Claude 30/47. Source: CALC/03 §D.
- **Table 5 by batch.** b1 (pre-registered queue) has 12 failures: hypothesize 4 (N1 3, N2 1) and acquire 8 (T1 4, T3 2, T4 1, N3 1). b2 has 7: hypothesize 4 and acquire 3. There are 0 read or act failures in either batch.
- **Absolute removal, passing main-study hard slots.** Trap 0.24 / 0.26 / 0.37 (min / median / max, n = 22). Two-part 0.36 / 0.38 / 0.43 (n = 23).
- **Break-even exact-query price.** GPT Open-8 vs BB-64, per NAME pass: $0.006 per query. Both arms used their full budget (median 8 and 64 texts).

## 5. New directions and combos outside the four (user request)

The loop already covers d1-d4, d5 (silent negatives), d6/X1 (this draft) and d7 (SAE as testing capacity). It also has the proposals X2-X4 (d6 critic r1), N1-N3 (d5 critic r2) and N1-N3 (d7 critic r1). The four below are new combinations. Each is buildable from existing data and is ranked by expected score.

- **Y1. "Same experiment, two graders: certified gold vs an LLM judge"** (d2 recipe + judge study + d7's pre-registered contrast). Headline: grading the identical pre-registered matched-budget study by a report-reading judge erases most of the budget effect (+0.58 → +0.11), shrinks the proxy effect (+0.47 → +0.28), flips BB-64 vs Open-8, and erases the weakest agent's deficit (Haiku 0.45 → 0.76). Mechanism: the judge credits `none` (41/44), and `none` is how proxy-induced acquisition failures end. CFP fit is highest of all directions: judge reliability, ranking sensitivity, ground truth beyond opinion. Risk: one judge, one prompt, aggregate arithmetic without intervals. Ceiling about 7.5-7.8 without runs. A process-aware judge arm (about $2) would make it 8.
- **Y2. "Cheap proxies turn agents from adaptive experimenters into batch designers"** (an upgrade of X4 with F5's contrast + d3 vocabulary). Headline: same model, same budget, the proxy changes the *tempo* of science. GPT plans its whole gold batch up front with the proxy (24/24) and goes sequential without it (0/24). Under the proxy, first-batch width then decides traps (25/26 vs 5/21). Ties to Pando's non-adaptive protocol and to batched Bayesian top-k selection (lit/L2). This is the cleanest "general scientific skill" framing the author asked about, with two item-level results (C1 and tempo). Ceiling about 7.5. A forced-sequential arm would make it 8.
- **Y3. "Bounded by the proxy at both ends"** (d7 + act stage). Headline: the same SAE error term that hides the trap cue from acquisition also caps the remedy. Passing trap ablations remove only 0.24-0.37 of the cue's effect, against 0.36-0.43 on nested cues. So SAE-based auditing has an acquisition limit and a remedy limit, both certified. It is thin alone (6 items, regrade-only). Best used as a section of d7 or X1, not a paper.
- **Y4. "Reading the contract as evidence"** (d4 + prompt facts). Headline: agents treat the task specification's guarantees as hypothesis filters. They prune nested cues under the exact-alignment rule (N1 7/9 by one reader), answer the contract-literal `none` when gold runs out (10/11 omissions with the proxy), and reason from the 0.15-0.3 band (2/36). For AI-scientist evaluation, the specification is part of the instrument and shapes the failures measured. It is reader-coded and hint-confounded, so treat it as a 1-paragraph discussion point inside X1 rather than a paper.

**Recommended combo for the tournament: X1 + Y1 + Y2.** Keep the stage-graded environment as the frame. Make the judge re-grade and the proxy-tempo contrast the two "beyond four stages" findings: report and design. This raises the number of results that clear their item-level floor or are pre-registered from two to four (C1, tempo, J1, J2), and it directly answers R1's and R3's "only two stages discriminate" with two more measured stages.

## 6. Ceiling

- **Current:** 7 / 7 / 7, mean 7.0, up from 6.8 at r1.
- **With F1-F12:** about 7.5 (range 7.3-7.7). The largest gains come from F1 (judge consequences), F5 (the tempo contrast, the second item-level result), F4 and F3 (removing the overclaims a statistician would catch), and F12 (readability).
- **Ceiling for this direction without new runs: 7.5, or 7.7 if Luna L1/L3 report before 20 Nov and are added to F11.**
- **8 needs new runs**, for example: one combination probe run with two agents (the composition test); 6+ fresh generator items per hard stage; an agent run at a binding act bar (0.9× reference, k = 8); or a process-aware judge arm. Wording cannot fix the remaining caps: one domain, three items per hard stage, and two stages at ceiling as shipped.
