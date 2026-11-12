# CRITIC r1: d7/draft_r1.md, direction "W6 Focused empirical short paper: interpretability tools as testing capacity"

Inputs read: BRIEF (RULES, CFP, SOURCES, USER_BRIEF, PRIOR_FIXES, EXISTING_DIRECTIONS), LEDGER, lit/L1-L3 (Pando and Chanin entries re-checked), updates/round_0.md and round_1.md (newest), the draft, 11 claim verdicts (C1-C11), and 3 reviews (6 / 6 / 7). I also re-read these sources: SUMMARY.md §4 predictions table, bb16/PREREG_BB16.md §1-2, bb16_analysis.json, rows_r1112.csv, s3_r1112.csv and failure_modes.json.

New numbers in this critic were computed read-only from committed files. The scripts are `paperloop/d7/calc/exrate.py` and `paperloop/d7/calc/crossing.py`. All inputs are November data. No [OCT] input was used and no runs were made. Each new number is tagged [new, existing data] where it is used.

## 1. Diagnosis (5 lines)

1. The core is the strongest pre-registered result in the paperloop, and every number in it checks out (C1, C2, C3, C5, C6, C8 supported). The pre-registered C1 is +0.71 at 8 queries. C4 is +0.04 at 64. The token direction runs against a token explanation. Commission falls from 15/51 to 0/71. A focused short paper is the right vehicle for it.
2. The headline says more than the design measured, in three ways that all three reviewers flag as major. (a) C4 (BB-64 − Open-8) is read as "the tool is worth +0.04 at 64". That is wrong: Open-64 was never run and BB-64 is at ceiling. (b) "An SAE is worth…" credits SAE-ness. No non-SAE proxy arm exists, and GPT actually used the view as a free surrogate oracle: median 1,921 own texts encoded per run, against 8 exact texts. (c) The exchange rate is a property of six hand-built items with shallow (rank-2) proxy errors and of one agent-harness pair.
3. The bracket is loose and its lower end is soft. Open-8 vs BB-16 is 23/24 vs 16/24 (Fisher p = 0.023; 4 items higher, 2 tied). BB-16 was designed after Block 1 to test the BB-8 result and ran in its own later session, yet Contribution 1 says all four arms share one interleaved order. Existing data give a point estimate: logistic interpolation gives about 36 exact queries.
4. There are precision errors a careful reviewer will catch. Pando is misdescribed as single-budget, when it sweeps k = 3-50 (C11). The 0.40 "best scripted policy" is really the BB-16 reference policy; the best is 0.43, P is 0.095 not 0.096, and "realistic" should go (C7). The tells are scoped too broadly and the grader denominators are unclear (C10). The sign test is labelled pre-registered and the trend test exploratory, when the reverse is true (C1, C3). "7 of 12 held; three failed" leaves two predictions unaccounted for. [OCT-CHECK] marks, "title to be completed" and "recomputed for this note" are still in the text.
5. The relayed user request and every review ask for directions and arm combinations beyond the four cells. New runs are off the table, so answer this with (i) existing-data analyses that already move past the four cells (break-even gold price, interpolated crossing, surrogate-oracle usage, removal gate) and (ii) one concrete "next arms" paragraph that also names the combinations already in flight (Luna L3).

## 2. Prioritized fixes (12; writing and existing-data analysis only; requests for new runs become wording)

The deltas are expected changes to the mean review score. They overlap, so they do not add linearly.

### F1. Fix the C4 reading everywhere  (+0.4; R2 major, "on its own would move me from 6 to 7"; C2 verdict)

Affected places: Abstract, Contribution 2, §4.1 "Plentiful gold", §4.4 last sentence, §5 first sentence, §5 recommendation, Limitations "A bracket".

- Contribution 2 should read:
  > **The budget curve** (§4.1). At a matched 8 exact queries the proxy raises NAME by +0.71. Without it, a black-box agent needs more gold to match: 16 queries give 0.67 and 64 give 1.00, where BB-64 matches Open-8 (C4 = BB-64 − Open-8 = +0.04 [0.00, +0.17]). The proxy's own value at 64 queries (Open-64 − BB-64) was not measured. Its pre-registered trigger was not met, and with BB-64 at 24/24 the outcome could not show a gain there.
- §4.1, second paragraph, replace the last two sentences with:
  > The pre-registered rule therefore returns "R3 eliminated": *with plentiful exact tests the SAE is not needed* for GPT. Together with a significant C1, this is the outcome the pre-registration called "the SAE acts as testing capacity". (C4's lower bound of 0 holds by construction. An unclustered Newcombe interval on the pooled rates, which was not pre-registered, is [−0.10, +0.20] and gives the same verdict.)
- §5, first sentence:
  > With plentiful gold our agent no longer needs the proxy (BB-64 = 24/24 matches Open-8). With scarce gold the proxy is worth +0.71. The null results and ours are therefore compatible: they measure what a tool *knows* beyond ground truth, and we measure what it *saves*.
- §4.4, last sentence: replace "in it the proxy has nothing left to add" with "in it our agent does not need the proxy".

### F2. Retitle and rescope the headline: what was valued is the SAE view as an agent used it, on shallow proxy errors, for one agent  (+0.4; R1, R2, R3 major; C4, C9 verdicts)

**New existing-data fact** (from s3_r1112.csv, column n_own_text_sae_texts; exploratory): GPT encoded a median of 1,921 of its own texts through the SAE in each Open-8 run (range 1,620-2,450), against 8 exact texts. Haiku encoded 843 (range 392-1,800). Black-box arms encoded 0, because they have no SAE tools. Their matched 3,000 forward units can only score sample notes. This is reviewer 3's "free approximate oracle", measured. It makes "testing capacity" concrete instead of contestable.

- Title, option A (recommended):
  > **What an SAE View Saves an Auditing Agent: Valuing an Interpretability Tool Against a Scarce Ground-Truth Budget**
- Title, option B (keeps the number):
  > **An SAE View Stood In for 16 to 64 Exact Queries — for One Agent, on Shallow Proxy Errors**
- Drop "An SAE Is Worth…" as the opening, because it reads as a property of SAEs.
- Abstract, replace sentences 4-6 ("Without the proxy, … budget curves.") with:
  > Without the proxy, 16 queries give 16/24 and 64 give 24/24. For this agent and these items, the proxy therefore stood in for somewhere between 16 and 64 exact queries (about 36 by interpolation). With the proxy, the agent scored about 1,900 of its own texts approximately per run and spent its 8 exact texts on the proxy's top candidates without adding exact tests; wrong named cues fell from 15/51 to 0/71. The proxy's errors here are shallow (the truth is its second choice), and a second agent shows no reliable gain. We recommend reporting tool ablations as budget curves against reference policies.
- New paragraph at the end of §4.2:
  > **What the agent used the proxy for [exploratory].** In every Open-8 run GPT encoded its own edited texts through the SAE: a median of 1,921 texts per run (range 1,620-2,450), against 8 exact texts. It also read latent meanings (`latent_examples`) in 21 of 24 runs. The proxy therefore worked mainly as free, approximate experiments on arbitrary text: a reconstruction-only logit that is wrong only by the SAE error term. We cannot separate that surrogate channel from the latent semantics. We therefore claim value for the SAE view as deployed, not for sparsity or interpretability as such. A dense reconstruction with matched error, or a difference-of-means direction, would be the comparison that tests the latter (§7).
- §4.1 "The value survives…" paragraph, replace with the C4 verdict's scoped text:
  > **For GPT, the value survives where the proxy's top pick is wrong.** On all three trap items the proxy ranks the [decoy] first and the [main] second, yet trap C1 = +0.75 (11/12 vs 2/12; unadjusted p = 0.0012). The pre-registration expected this contrast to be biased toward 0. It also predicted BB-8 trap NAME ≥ Open-8 trap NAME, and that prediction failed (0.17 vs 0.92). The capacity comes from a short list that contains the truth: GPT isolated the proxy's rank 2 on 11/12 trap probes, and a privileged rank-1-only policy scores 0.00 on traps against 0.96 for ranks 1-2 (Appendix D). This is a rank-2 error. With the [main] at rank 3 or lower the top-two policy falls to 0.00, so the exchange rate is a function of how deep the proxy's error is. Haiku shows no trap gain (0/6 vs 2/6).
- Move the error-depth sentence ("with the cue at rank 3 or lower a top-two policy drops to 0.00 …") from Limitations into this paragraph. Keep a one-line pointer in Limitations.

### F3. Replace the loose bracket with a point estimate plus the bracket, and state BB-16's provenance  (+0.3; R1, R2, R3; C3 verdict)

**New existing-data result** (`d7/calc/crossing.py`; exploratory, model-based): a two-parameter logistic fit of NAME on log2(budget) over BB-8/16/64 (24 runs each) predicts 0.23 / 0.69 / 0.88 / 0.94 / 0.99 at 8 / 16 / 24 / 32 / 64. It reaches Open-8's 0.958 at **about 36 exact queries**. A bootstrap that resamples the six items gives a 95% interval of 21 to beyond 64 (the upper tail extrapolates). Open-8 vs BB-16, run-level Fisher: p = 0.023.

- §4.1 "Where the curves cross", replace with:
  > **Where the curves cross.** BB-16 reached 16/24 = 0.67. Open-8 (0.96) lies above BB-16 (run-level Fisher p = 0.02; higher on 4 items and tied on 2) and does not differ from BB-64, which is at ceiling. The crossing therefore lies between 16 and 64 exact queries. A logistic interpolation over the three black-box budgets puts it at about 36 (item-bootstrap 95% interval 21 to beyond 64) [exploratory]. No budget between 16 and 64 was run. A pre-registered descriptive trend test over 8/16/64 (BB-16 pre-registration §5) gives Cochran–Armitage p = 1.1e-6.
- §3 Execution, add:
  > BB-16 was designed after Block 1, to test whether the BB-8 result was budget arithmetic. Its own pre-registration was hashed before its first counted run, and it ran a day after Block 1 with the same image, CLI version and effort, in its own seeded order (seed bb16-1111).
- Contribution 1: replace "share image, items, non-query budgets and a seeded, interleaved order" with "share image, items and non-query budgets. Block 1 (Open-8, BB-8, BB-64) ran in one seeded, interleaved order, and BB-16 followed under its own pre-registration".
- Appendix C: replace "Open-8 is at or above BB-16 on 6/6 items" with "Open-8 is at or above BB-16 on 6/6 items (4 higher, 2 tied)".
- Recommendation sentence: "is the SAE view cheaper than about 8 to 56 more experiments?" stays as written.

### F4. Make cost-normalization real with existing data: the break-even price of gold  (+0.25; R1 and R2 minor, CFP "cost-normalized reporting"; reviewers explicitly asked for the break-even price)

**New existing-data result** (`d7/calc/exrate.py`; rows_r1112.csv; GPT cost = tokens × assumed list prices). Every GPT run used its whole exact budget (8, 8 and 64 texts). Per NAME pass, Open-8 spends $0.707 plus 8.35 exact texts, BB-64 spends $0.372 plus 64.0, and BB-8 spends $3.864 plus 32.0. Open-8 is cheaper than BB-64 per correct answer whenever one exact query costs more than **$0.006**. Open-8 dominates BB-8 at every price. It also dominates BB-16 at every price: BB-16 costs $14.64 for 16 passes, which is $0.92 plus 24 texts per pass.

- §4.4, replace the last paragraph with:
  > **Cost per correct answer, with gold priced.** Exact queries cost nothing in dollars here, so we price them as a parameter p. Per NAME pass the proxy arm spends $0.71 in tokens plus 8.4 exact queries, BB-16 spends $0.92 plus 24, and BB-64 spends $0.37 plus 64. The proxy arm is the cheapest per correct answer whenever an exact query costs more than about $0.006. That price is below the cost of any real experiment, a fine-tuning run, or a single expert label. It dominates the 8- and 16-query black-box arms at every price.
- Add a fifth column, "exact queries per pass", to Table 2 or Appendix F.
- Recommendation 5 becomes: "cost per correct answer as a function of the price of a gold query, with the break-even price".

### F5. Correct the reference-policy section (§4.3, Appendix D, Figure 1)  (+0.2; C7 overclaimed; R2 minor "not ceilings for agents")

- Rename "ceilings" to "**privileged reference policies**" throughout. GPT BB-64 = 1.00 > 0.93 shows they do not bound agents.
- §4.3, replace the bullets and the bold sentence with the C7 fix text:
  > [Offline, privileged] Scripted no-proxy policies that are given the 8 candidates, their exact edits and signs, and the null count reach at most 0.43 (exact back-end) or 0.44 (additive) at 8 queries. The reference policy pre-registered for BB-16 (bisect-and-confirm) reaches 0.40 / 0.80 / 0.93 at 8 / 16 / 64. A noiseless-optimal group-testing policy played on the stored readings reaches 0.497, and the exact noiseless optimum is 0.703. Both come from simulations that are not part of the release; the tracked noiseless reference reaches at most 0.58 at 8. Open-8's 0.96 exceeds all of them. At least 65% of C1 lies beyond every scripted no-proxy policy we wrote (73-79% beyond the best scripted and reference policies), and 36% lies beyond even the noiseless optimum. GPT BB-8 is 0.15 below the 0.40 reference (P = 0.095, not significant).
- Add one clause on two-part items:
  > On two-part items this reading assumes the method hint is procedural. If the hint is read as a prior pointing to the nested property, a privileged policy reaches 0.92 with 4 texts, and the shortfall there is search, consistent with BB-16 (7/12 vs 0.84).
- Replace "at most about a third of C1 reflects weaker black-box play" with "these policies do not bound agent skill (GPT BB-64 exceeds its reference), so the decomposition says how much of C1 budget arithmetic alone can explain, not how much is skill".
- Appendix D table: relabel the 8-query row "0.43 best / 0.40 reference". Change P = 0.096 to 0.095 everywhere. In Figure 1, mark the noiseless-optimum line "0.70, untracked simulation".

### F6. Correct Pando and the "single budget" framing  (+0.2; C11 overclaimed; prevents a damaging error for any reviewer who knows Pando)

- §1, sentence 5: replace "Each study values the tool at one fixed amount of ground truth, an amount AI scientists rarely have." with:
  > These studies value the tool with no gold budget, with a budget that does not bind on ground truth, or with gold spent on random, non-adaptive queries. None measures what the tool saves when an agent chooses where to spend scarce gold, which is the situation AI scientists face.
- Abstract, sentence 1: "…is usually measured where the agent does not choose where to spend ground truth; we measure it as a function of a scarce, adaptively spent budget."
- §5, second paragraph, replace the Pando sentence with:
  > Pando sweeps the gold budget (k = 3-50) with a budget-matched sample-only arm, but spends it on random, non-adaptive queries. Its attribution method's lead over sample-only is largest at k = 3 (10.1-10.3 points). Its SAE readouts stay near sample-only at every k, with per-field AUC at chance. What Pando lacks and we add is adaptivity (the agent chooses which inputs get gold) and a proxy whose short list contains the truth.
- Recommendation 1: credit Pando ("as Pando does, a no-tool arm at two or more budgets…"). The new items are then 2-5: items where the tool is certifiably wrong, logged adaptive gold queries, reference policies, and priced cost per correct answer.
- Related Work: "Pando … uses fixed, non-adaptive queries at several budgets, and we supply the adaptive setting it calls for".

### F7. Mechanism section: scope, label and the S3 sentence  (+0.2; C5, C6 verdicts; R2 minor on interval and group tests; R3 on tool use)

- Heading §4.2: "Mechanism: triage, not more exact tests [exploratory; GPT, matched 8 queries]".
- Item 1: replace "The proxy relocates testing; it does not add any." with:
  > The proxy relocates exact testing without increasing it (1.32 vs 1.29 isolations per planted probe; no interval, because the committed data are aggregates). Isolation counts single-difference pairs only, so it undercounts multi-property designs. Those are rare at 8 queries but common at BB-16 (median 4 multi-property edits per run).
- Add one sentence of process evidence:
  > With the proxy, GPT sent all its exact texts within 60 s in 24/24 Open-8 runs, against 0/24 BB-8 runs. Without it, the hard probe got a median of 2 of 8 texts, the same as an even split.
- Item 3: add GPT's own p and the labels.
  > For GPT, wrong named cues fall from 15/51 to 0/71 (Fisher p = 5.2e-7), and for Haiku from 9/24 to 1/27 (p = 0.0036). These are answer-level Fisher tests, not clustered by run. With the proxy, wrong answers are almost all `none` (10/11 vs 33/57 at BB-8).

  Delete the unchecked gloss "an agent that has not verified a candidate answers `none` rather than guess".
- Line 136, replace from "In every arm…" to the end with:
  > Wherever GPT varied the true cue cleanly it named it, in every arm (Open-8 15/15, BB-8 1/1, BB-64 23/23). In BB-8, 23 of 24 runs never did so. The black-box shortfall is consistent with not testing the true cue cleanly: 12 of 18 BB-8 failures never varied it, and 6 varied it only together with other properties. S3 is descriptive and post-treatment, and it does not count free sample notes.
- Abstract: add "[exploratory]" in spirit by writing "traces suggest" before "relocates".

### F8. Grader section: denominators, tells, and the removal gate  (+0.15; C10 overclaimed; R2 and R3 minor; R3's "SHIFT half is decoration")

- Table 1, row 1:
  > Regrade of every run that submitted latents (64 main-study + 36 Block 1 Open-8) with its own latent permutation: 100/100 runs, 400/400 probe records; an independent re-implementation also gives 100/100. Black-box runs submit no latents; their NAME is recomputed from grade files by the pre-registered scorer.
- Table 1, coded-rollouts row: "86/86 cross-model study rollouts clean (one unblinded LLM reader, quotes verified; 0 web or subagent calls in 2,221 Claude tool calls)".
- §2.2, replace the two-caveats paragraph with:
  > At the shipped τ, naming decides every pass: all 176 correctly named main-study cues passed removal and keep, and no named slot is lost to removal in the 100 regraded runs. Removal is nonetheless a real gate. A naive answer with the true regex and the 16 largest public-attribution latents names 6/6 but reaches open reward on only 1/6 items. Hard-slot τ ranges from 0.15 to 0.25, and raising τ to 0.40 leaves 6 of 36 Open-8 hard passes, so removal is a difficulty knob. NAME is our outcome because black-box arms cannot submit latents. The items carry two information tells. The first is a free sample-logit midpoint on 2 of 3 trap hard probes; no Block 1 run used it (main-study runs unchecked). The second is a band inference from the 0.3/0.15 contract, which fails as a whole-episode policy (it false-claims 0.272 of ordinary probes).
- If this needs room, one sentence placing removal relative to SHIFT and Chanin already exists in Related Work. Keep it.

### F9. Statistics labels and the predictions count  (+0.1; C1, C3 verdicts; R2 minor)

- §4.1: "Open-8 beats BB-8 on all six items, so an exploratory item-level sign test (not pre-registered) gives two-sided p = 0.031, the lowest p six items allow." After the Holm p, add "(within-item permutation, 10^4 resamples; 6 clusters, so intervals are approximate)".
- Appendix G, Block 1 row:
  > 7 of 12 predictions held. Three range predictions failed because observed rates were higher than predicted. One order prediction was reversed (BB-8 traps vs two-part). The prediction that BB-8 traps ≥ Open-8 traps failed (0.17 vs 0.92), and it failed in the direction of C1.

  Also use this in §4.1 as the "failed in the direction of the claim" point (F2).
- §7: add one sentence on power. "The design simulation gave power 0.89 for a 0.45 gap at 24 runs per arm". This is LEDGER §2.5 (`analysis_dryrun/power.md`), NOV.

### F10. Second agent: inconclusive, not absent  (+0.1; C9 overclaimed; R2 minor; R3 harness confound)

Replace §4.5 with:
> Haiku 5.5 (descriptive, 12 runs per arm) shows no reliable gain: Open-8 5/12 vs BB-8 3/12, +0.17 (Fisher p = 0.67; clustered CI [−0.33, +0.67]). The proxy helps on two-part items (5/6 vs 1/6) but not on traps (0/6 vs 2/6; p = 0.45, no claim). Haiku isolated the trap runner-up in 2 of 6 Open-8 trap audits, and in 5 of 16 across all its proxy runs, against 12/20 for Opus and Sonnet in the same harness (p = 0.11) [exploratory]. Capacity never spent on the runner-up is no capacity on a trap. Haiku also failed in the Open-8 runs where it did isolate the runner-up, so allocation explains most of its trap failures, not all of them. This is AuditBench's "tool-to-agent gap" in allocational form. Model and harness are confounded here (Haiku runs in Claude Code, GPT in Codex). The curve is therefore claimed for one agent-harness pair. A tool's value is a property of the agent as well as the tool, and can be zero.

Add the last sentence to the reporting rule in §5 as a sixth item: "report it per agent".

### F11. Add "Beyond the four arms": what the environment already supports, and what is in flight  (+0.3; relayed user request; R1 major, R2 and R3 to-raise)

Put this as the last paragraph of §5, or as §7a, and shorten "A bracket, not an estimate" in Limitations to a pointer. Wording only; no runs are claimed.

> **Beyond these four arms.** Every arm below is a parameter setting of the released environment. Together they would turn one exchange rate into a function of tool, agent and price.
> (i) *Completing the curves*: Open-0/2/4/16 and BB-32, for a measured crossing instead of an interpolated one. The privileged proxy-only policy already scores 0.50 at 0 queries, and the additive reference is 0.89 at 32.
> (ii) *Proxy error depth*: the [main] at proxy rank 3-8, or the decoy inflation swept from 1× to 3×. Reference policies predict a collapse of the top-two policy (0.00) and a floor for screening policies (0.46-0.56).
> (iii) *What part of the proxy carries the value*: a shuffled-rank placebo; surrogate scoring only (gradient and own-text encodings, no latent semantics) against semantics only; and a dense reconstruction with matched error or a difference-of-means direction in place of the SAE.
> (iv) *Sample-only access*, the intermediate access mode the code already implements.
> (v) *Priced or noisy gold*, which makes F4's break-even price a manipulated variable.
> (vi) *Agent × harness*: a second model in GPT's harness. This is pre-registered and under way: GPT-6 Luna, L3 = proxy vs no proxy at 8 queries, 36 vs 24 runs.
> (vii) *A second proxy-gold domain*: a pre-registered judge-versus-certified-grade study is running, in which an LLM judge is the proxy and the closed-form grade is the gold.
> Each needs only certified-truth items and a matched no-tool arm, which is the recipe of §5.

### F12. Remove draft residue and cut jargon  (+0.15; all three reviewers' nitpicks, which cost credibility; RULE 3)

- Appendix B: remove both [OCT-CHECK] items. Use NOV-only R1 ("rank 1 28/39 = 72%, rank 2 9/39, rank 3 3/39, rank 4+ 1/195; same six items; some runs read before the freeze") and write "its companion prediction R4 failed", with no pooled number. The pooled 40/71 and the 44.4% are MIXED, and neither is needed here. The Appendix G R4 cell becomes "R4 failed".
- References: Chanin 2026 is "Are SAE Benchmarks Reliable?" (arXiv 2605.18229). Delete the "[Full author lists … paperloop/lit/]" line after completing the list. Delete "Recomputed for this note from the per-run rows (read-only)" in Appendix E.
- Appendix E/§4.4: write "at a cap equal to the Open-8 median, which cuts half the Open-8 runs, C1 = +0.46". Also add: "a cap here re-scores completed runs; it is not a token-limited rerun".
- Render Figure 1 as an actual plot: BB curve with Wilson bars, the Open-8 band, the logistic fit from F3 drawn dashed and labelled "interpolation", and the reference-policy points.
- Define C1/C2/C4 once in §3 and use "proxy effect at 8", "BB-64 − Open-8" in prose afterwards. Drop S3/R3/R4/L3 codes from the body, or gloss each at first use.
- Keep the header "Short paper (body about 4 pages)" only if the body really fits. With F3/F4/F11 added, move Appendix D's second table and Table 3's p-values out of the body to stay within it.

## 3. Nitpicks to ignore (or answer in one clause at most)

- A mixed-effects model or an item-clustered test for Table 3. The per-slot data are not committed, and six items do not support a GLMM. Say "descriptive" and give the share contrast (2% vs 56%). That is enough.
- An equivalence margin for 1.32 vs 1.29. The F7 wording ("without increasing it", no interval) is the honest answer.
- "The Cochran-Armitage test only shows more queries help". This is true and harmless. It is one clause, now correctly labelled (F3).
- Contamination of public items. It is already in Limitations; do not expand it.
- "Construction limits external validity (regex-detectable properties, enumerable hypothesis space)". One clause in Limitations: "the hypothesis space is small and enumerable, which favours group testing and rank-following alike". Nothing more.
- A full SHIFT comparison of agents' latent sets with the attribution reference. Out of scope for this direction. F8's removal-gate sentence is the proportionate answer.
- A power or sample-size rationale for Haiku's 12 runs. Haiku was pre-registered as descriptive, so say so (F10). One clause.
- A per-run breakdown of every tool call. F2's own-text count plus `latent_examples` 21/24 covers what matters.

## 4. New in updates/ (round_1.md, newest)

- **GPT-6 Luna arm**: pre-registered (L1-L4; Open-8 ×6 and BB-8 ×4 per item, i.e. 36 vs 24 runs; seed luna-1112; same Codex harness as GPT 6.1 Terra). The pilot ran fine ($0.136). **There are no counted results.** L3 (does the proxy raise Luna's NAME at 8 queries) is exactly the second confirmatory agent this paper lacks, with no harness confound. The draft describes it correctly. Keep "pending; no claim depends on it". If L3 lands before 20 Nov, it goes into §4.5 as a pre-registered second agent. That is the single largest possible score gain (see §6), whichever way it comes out: a positive result broadens the claim, and a null makes "a tool's value is agent-specific" a confirmatory finding. The driver validation on Terra reproduces 23/24, trap NAME 11/12 and trap rank-2 isolation 11/12. Nothing changes for the draft.
- **Judge J1-J4**: still no results. Keep it pending (F11 vii).
- **Token-cap (brave-curie)**: C1 is +0.83 at the BB-8-median cap of 87k, C4 is 0.00, and C1 ≥ +0.71 at any cap ≥ 86k. This matches Appendix E exactly. No change.
- **tender-dijkstra**: GLMM ranges and the calls-left fact concern the main study. They are not needed in this direction.
- No [OCT] material in the new files.

## 5. Directions and combinations beyond d1-d4 (relayed user request)

This direction (d7) is already outside d1-d4. Combinations that strengthen it without new runs:

- **d7 + d5 (silent negatives)**: commission 0/71 vs 15/51 is d7's second outcome. Use d5's leave-Haiku-out and two-part-only robustness numbers in one sentence of §4.2, which answers "the omission side is built into the trap".
- **d7 + d2 (proxy-and-gold recipe)**: the reporting rule of §5 is d2's recipe applied to tool valuation. Borrow d2's "judge as second proxy-gold instance" paragraph as F11 (vii), in one sentence.
- **d7 + d3 (budgeted search)**: the interpolated crossing (about 36) and the break-even price ($0.006) are "exchange rates" in the PROBE sense (Ma et al. 2026, a (1 − ρ²) factor). One sentence in Related Work connects them. Do not import BAI formalism.

New directions not yet drafted, if the loop wants more:

- **(N1) "Free experiments": interpretability tools as surrogate oracles.** Built on the new own-text fact: GPT ran about 1,900 approximate experiments per run through the SAE, against 8 exact ones. The paper measures how agents convert free surrogate readings into a few gold tests, and where that breaks (traps: the surrogate is wrong by the error term). It fits the CFP "process-level evaluation" area. It needs Appendix-level tool-log statistics that already exist (s3_r1112.csv, LEDGER H9).
- **(N2) "Price the gold": cost-normalized evaluation of AI-scientist tools.** A methods note: tool value as a break-even price per gold query, for proxy and no-proxy arms at several budgets. ShiftHunt is the worked example and the judge study is the second. It fits the CFP "cost-normalized reporting" area directly. Short, and mostly built from F3/F4.
- **(N3) "A pre-registration that was wrong in the right places".** An instrument-quality paper. It covers the predictions that failed (Open-8 above its range, BB-8 traps ≥ Open-8 traps failed, BB-64 two-part above its range) and what they reveal about how well authors forecast agent difficulty. It fits the CFP "how good is the instrument" area. It is thin on its own, so treat it as a section of d6 or d1 rather than a paper.

## 6. Ceiling

- Current reviews: 6 / 6 / 7 (mean 6.3). Rigor 7 across all three.
- With F1-F12 (wording and existing data only): **about 7.0 (accept), range 6.7-7.3.** The largest gains are F1 (reviewer 2 states it is worth +1 on its own), F2 (the surrogate-oracle fact defuses reviewer 3's "SAE trap" honestly) and F3/F4 (a point estimate and a priced exchange rate turn the bracket into a measurement). F11 answers the user's request and reviewer 1's main generality complaint as well as words can.
- **7.5** if Luna L3 reports before 20 Nov, in either direction, because it removes "one agent-harness pair".
- **8** needs new arms: at least one of Open-2/4, a deep-error trap (rank 3+), or a non-SAE proxy with matched error. Out of scope for this round.
- Structural cap: six items with shallow proxy errors. However the paper is worded, it remains a careful case study with a transferable reporting rule, not a law about SAEs. Present it as exactly that.
