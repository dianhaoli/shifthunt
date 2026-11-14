# V6 compliance critic

Checked: `PAPER_V6.md` (body in full, plus Appendices E, G, K, L and M), `fig1_ladder.png` and `fig2_budget.png`, against four sources:
- `00_FINAL_FEEDBACK.md` (consensus list, §4 decisions and §5);
- `REVIEW_V5.md` §7, with W1-W9 and §5 for detail;
- `V4_VS_V5.md` §4-5;
- `V6_PLAN.md`, which records the author decisions.

Every number was re-checked against `RESULTS_FOR_PAPER_2e30670.md` and `gpuplan_c6c_ladder.json`. The body is 4,704 words from §1 to the references, and the abstract is 180 words. The band and topic-unit JSON files are committed (`git ls-files`).

**Bottom line.** V6 follows the consensus closely: it leads with the ladder, presents L3 as a positive control, and says the transcript level is not confirmed after Holm. The changes most likely to decide acceptance are these:
1. **The headline mechanism is not robust across sets.** "Commissions are caught, omissions are not" holds cleanly only on set A. On Luna's runs, credited omissions fall from 24 to 10 of 38. On the main study, wrong-cue credit rises from 3 to 5 of 6. Appendix E prints all of this, so a statistics reviewer will find it.
2. **The abstract's agent sentence lacks its "descriptive, same-builder" label**, which the reviewers asked for explicitly.
3. **The "harder variant" (0.77) is still in Figure 1**, against the moderator's instruction to hold it back. It also visually contradicts the figure's title.
4. **Some keyless differences are within noise.** The placebo log beats the real log (0.20 vs 0.06), yet the body reads the keyless levels as a trend.
5. **The page count is unverified.** Compile in the AAAI kit. If the paper is over 8 pages, move Table 3 to the appendix (wording in §5, A5).

All fixes below are text-only and use only numbers already in the sources.

---

## 1. Problems not covered by any feedback list (fix first)

**N1. The commission/omission asymmetry holds only on set A** (body §4 heading, Table 1 title, §1(ii), abstract).

Source: `ladder.json` and Appendix E1.

| set | `none` failures credited, L0 → L1 → L2 | wrong cues credited, L0 → L1 → L2 |
|---|---|---|
| set A | 23 → 21 → 17 of 26 | 9 → 7 → 3 of 17 |
| Luna | 24 → 21 → 10 of 38 | 11 → 6 → 4 of 15 |
| main study | 13 → 8 of 13 (L0 → L2) | 3 → 5 of 6 (L0 → L2) |

What does hold on every set and at every keyless level is that omissions make up most of the false credit. At L2 they are 17 of 20 credited failures on set A, 10 of 14 on Luna and 8 of 13 on the main study. Part of this follows from the base rates (Luna has 38 omissions against 15 wrong cues), so say "most of".
- §4 heading. Old: "**Commissions are caught, omissions are not** (Table 1)." New: "**Commissions are caught more often than omissions** (Table 1)."
- §4, after "Credited `none` failures barely move (23, 21, then 17 of 26) until the key removes them all." Add: "The contrast is clearest on set A. On Luna's runs credited omissions also fall (24 → 10 of 38), and on the main study the transcript raises wrong-cue credit (3 → 5 of 6; Appendix E). On every set and at every keyless level, though, omissions are most of what the judge wrongly credits."
- §4. Old: "an omission leaves nothing to contradict." New: "an omission leaves no contradicting result, only an untested candidate."
- Table 1 title. Old: "More evidence fixes commissions, not omissions." New: "On set A, more evidence fixes commissions more than omissions."
- §1(ii). Old: "More evidence teaches the judge to reject wrong named cues but not wrong `none` answers (Figure 1, Table 1)." New: "More evidence cuts credited wrong cues more than credited wrong `none` answers (set A: 9 → 3 of 17 vs 23 → 17 of 26), and omissions remain most of the judge's false credit on every set until the key removes them (Figure 1, Table 1)."
- Abstract. Old: "and it keeps crediting omissions." New (see A1): "and most of what it wrongly credits are omissions."

**N2. The placebo log is undersold.** §4. Old: "A placebo log with the logits hidden (0.20 on set A) does no worse than the real log." New: "A placebo log with the logits hidden scores higher than the real log (0.20 vs 0.06 on set A), so differences of this size between keyless levels are within the judge's own variability; only the step to the key is large."

This also helps with N1 and with the "not confirmed after Holm" line.

**N3. Set A's run count does not add up.** §3 lists 108 + 24 = 132 runs, but set A has 130. In §3 Runs, after "Terra blind at 16 a day later." add: "Set A is these 132 runs less two whose judge calls failed (130)."

**N4. The held-out judge count includes the shipped anchor.** §4 Consequences. Old: "On the held-out traps the judge credited 6 of 10 and 5 of 7 failed trap answers". New: "On the held-out-trap runs (with three anchor runs on a shipped trap), the judge credited 6 of 10 and 5 of 7 failed trap answers".

In Table 3, the row "judge fails on held-out traps | 27; 3" should read "27; 2 held-out + 1 shipped".

**N5. Luna's "3/10" reads as a contradiction of 2/17.** The 3/10 is the isolation rate; 2/17 is the naming rate. §5.3. Old: "The registered Terra-Luna gap on the first two held-out items (0.63) fell outside every pre-registered band: it cleared the gap bar, but Luna's 3/10 missed the companion condition by one run." New: "A registered Terra-Luna test on the first two held-out items fell outside every pre-registered band: Luna isolated the [main] in 3 of 10 runs, one more than the prediction allowed (Appendix F)."

**N6. The text and Figure 2b disagree.** The text cites "a policy told the trap rank stays at 0.90-0.95". The figure does not draw that policy; it draws "hedge", which the text never mentions.
- Cheapest fix (text). Old: "a policy told the trap rank stays at 0.90-0.95; best blind scores 0.40." New: "a policy told the trap rank stays at 0.90-0.95 (Appendix H); a hedging script stays near 0.5 at every rank, and best blind scores 0.40."
- Also fix the figure labels:
  - the legend says "fresh traps" and the caption says "held-out traps"; use "held-out" in both;
  - change the y-axis "P(NAME)" to "pass rate" (W9, two metrics).

**N7. The test-retest figures come from two populations.** The body gives "Fleiss κ 0.39 on the hard probe" (214 runs, three replicates); Figure 1's line is 0.44 (set A, L0 vs L0r, all probes). §4. Old: "agrees with itself at Fleiss κ 0.39 on the hard probe". New: "agrees with itself at Fleiss κ 0.39 on the hard probe (0.44 over all probes of set A, the dotted line in Figure 1)".

**N8. "Terra's widening is targeted at the trap" (§5.3) reads as a skill claim**, which §5.4 then undercuts. New: "Terra widens mostly on the trap probe (11 of 12 trap probes vs 4 of 48 ordinary probes)."

---

## 2. (a) Moderator consensus list and §5

| # | Item | Status | Fix (old → new) |
|---|---|---|---|
| 1 | Lead with the ladder; one figure; the rule per set (0.37, 0.67, 0.75, 0.87); test-retest at L0 only | **partly** | Title, abstract and §4 lead with the ladder. Problems: Figure 1's rule ticks are unlabelled colours; add the numbers 0.67 / 0.37 / 0.75 beside the ticks. The test-retest line mixes populations (N7). Drop the harder variant (row 3 of this table). |
| 2 | Delete every "a judge given the key is untested" | **done** | Both remaining uses of "untested" refer to other things: a keyless judge with an exact-query budget, and the closeness script. |
| 3 | L3 as a positive control, above band; the finding is the L2-L3 gap; **hold 0.77 until W9 is reconciled** | **partly** | The control framing is done (§4 "A positive control"). 0.77 is still plotted in Figure 1, and it sits below its own rule tick (0.87) under a title that says "with it, the judge is nearly perfect". Remove the harder-variant series and the caption's last sentence. In §4, old: "it landed above that band on 5 of 6 bases" → new: "it landed above that band on all three main sets". In Table 3, old: "272; 6 \| 0.92-1.00 \| above band (5 of 6 bases)" → new: "254; 6 \| 0.92-1.00 \| above band on every main set (harder variant: Appendix L)". |
| 4 | L2 "not confirmed after Holm" | **done** | §4 "Statistical status" and Table 3. |
| 5 | Commissions vs omissions is the mechanism; Haiku shows the direction of failure, not a second validation | **partly** | The Haiku framing is right ("a stricter judge model is no fix"). The mechanism is overstated outside set A (N1). |
| 6 | Fix the auditing-game citation (they grade at L3; verify) | **done** | §4 and §7: "grade reports against a known implanted behaviour, which is our key level." This is consistent with the cited designs. |
| 7 | Check the tell before rewriting Claims 1 and 3 | **partly** | The firing rates are reported. The frozen closeness script at B = 4 and B = 8 was not run, and §5.4 says so ("untested"). See §5 row of this table. |
| 8a | An item count next to every p | **partly** | Done in Table 3 (the n column) and in §6 "on two items". Missing for: §4 "p = 0.030" (add "130 runs, 6 items"); §6 "2×10⁻⁴ ... 1.5×10⁻⁵" (add "6 items each"); §4 Consequences "−0.19 [−0.42, +0.03]" (add "84 runs, 6 items"). |
| 8b | One Luna denominator per table (2/17 primary, 2/21 secondary) | **done** | Body uses 2/17; Appendices D and L explain 2/21. |
| 8c | Primary held-out result is "a pass on every fresh item"; 6/6 sign test descriptive | **done** | §5.3 and Table 2. The sign-test floor of 0.125 is stated. |
| 9 | About 7 pages; V4 motivation; SHIFT in one sentence; routes/cost/PPI/C21 to the appendix; no hypothesis IDs; drop "remove"; "certified" only as a name | **partly** | Content done: motivation in §1, SHIFT one sentence in §7, no IDs, PPI/C21/routes out of the body, "certified" absent. Length not verified: 4,704 words plus Box 1, three tables and two figures is close to 8 pages. Compile; if over, apply A5 in §5. |
| 10 | Freeze the judge work | **done** | No new judge runs. |
| §5 | Commit `band.json` and `topicunit.json` | **done** | Tracked in git. |
| §5 | Firing rate in all three units, unfavourable unit in the body | **done** | §5.4: 15/15, 0.925, about 0.2, 0.26; topic unit 12/15 with the [decoy] in the gap; class-gap 0/15. Change "about 0.2" to "0.205" so it is not read as rounding for comfort. |
| §5 | Pre-write both outcome sentences, then score the closeness script | **missing** | V6 has only one hedged sentence. If the script is run, use the two sentences below verbatim. If it is not run, keep §5.4's "untested" and the limitation; do not add a third framing. |
| §5 | Disclose band checkers 0/3, C3 3/14 vs 5/12, the C14 margin, signature-not-phenomenon | **done** | In §5.4 the "at most 3 of 15 cells" clause is fine. Add "and none passes any shipped trap on a majority of seeds" so the 0/3 item-level figure is in the body. |

**The two pre-written outcome sentences** (moderator §5):
- *If the closeness script matches Terra* (about 12/12 at B = 4 and selectivity like 11/12 vs 4/48): "A frozen script that widens when the top two candidates are close and one reads in the contract's gap matches Terra, so Terra's advantage is consistent with checking the proxy against the stated prior; contracts can leak, and items should be audited for such signals."
- *If it falls short*: "A frozen script that widens on the gap plus the closeness of the top two candidates does not reach Terra's pass rate or selectivity, so the gap alone does not explain Terra's widening."

---

## 3. (b) REVIEW_V5 §7 to-do list

| # | To-do | Status | Fix |
|---|---|---|---|
| 1 | Tell check: firing rate by probe type, and a magnitude-aware script at B = 4 and 8 | **partly** | Firing rates done (§5.4, Table G1). The magnitude-aware script was not run. See the pre-written sentences in §2. |
| 2 | Item-level inference primary; items next to p; item-clustered κ intervals; L1/L2 flagged as registered after Terra's results; Luna's per-item split | **partly** | Done: Luna per item (Table 2); "registered after Terra's results" (Tables 2-3); the n column. **Missing: κ intervals.** Cheapest honest fix, in §3 Statistics after "describe these items only": "κ values carry no item-clustered interval; with six items such intervals would be wide, so we interpret only the gap between keyless levels and the key, not differences among keyless levels." Also reorder §6 (A5). |
| 3 | Length: compile in the AAAI kit, drop IDs, shorter abstract, redraw Figure 2 | **partly** | IDs dropped, abstract at 180 words, Figure 2 redrawn. Not compiled. Figure 2b's legend still disagrees with the text (N6). |
| 4 | Rewrite the twelve overstated sentences (§5 of the review) | **mostly done** | Title "Certified" retired; "remove it" dropped; "few", not "none"; the answer-type sentence rephrased; "in our setup" scoping implied. **One left:** the abstract's held-out contrast is still not labelled descriptive or same-builder (A1). |
| 5 | Claim 1: B = 8 matches the rank-only script; ablation-preview scripts at B = 4; prompt confound; Luna and Haiku sentence; scope to Terra | **partly** | Done: "matching Terra", "The gain is Terra's", the Luna/Haiku sentence, the prompt confound (Limitations, Appendix A). The B = 4 script with the ablation preview was not run; the Limitations bullet "which we do not separate" covers it honestly. |
| 6 | Claim 3: the shipped-trap Terra-vs-Luna test, fresh contrast descriptive, rank-2 and same-builder limits next to the claim | **done in the body, missing in the abstract** | §5.3 opens with the shipped-trap test, and the rank-2/one-builder caveat is the next paragraph. Fix the abstract (A1). |
| 7 | Judge analyses on existing data: κ on named answers at L0/L1; a scripted evidence-ceiling judge on L1 logs; rephrase "answer type"; the judge with evidence as the open test | **partly** | Named-answer κ is in Appendix E1 (0.14 / 0.21 / 0.35) but not in the body. Rephrase done. Open test stated in Limitations. The evidence-ceiling judge was not run. Optional body clause in §4 "The ladder": "(among named answers only: 0.14, 0.21, 0.35 on set A)". |
| 8 | W9 inconsistencies: harder variant, Figure 1 caption, √κ bound, two success metrics | **partly** | √κ gone. The harder variant is still in Figure 1 (§2 row 3). "P(NAME)" is still on the Figure 2 axes (N6). The body uses "pass" consistently. |
| 9 | Small new runs (design-prior judge, non-GPT judge, BB-4, forced allocation) | **not done (consistent with the freeze)** | Correctly listed as limitations. No action. |
| 10 | Reproducibility: pin model and harness versions; claim numbers in the appendix; natural rank; "remove"/"certified" | **partly** | Natural rank done (116/116 bank, 12/12 shipped). Appendix numbers done. **Missing: model snapshot IDs and Codex CLI / Claude Code versions** (no version strings anywhere). Take them from the run manifests into Appendix L. Do not write placeholders. |

---

## 4. (c) V4_VS_V5 take-back and keep lists

**Take back from V4**

| Item | Status | Fix |
|---|---|---|
| Motivation: a confident "nothing found" is the dangerous error | **done** | §1 "Why it matters" and abstract sentence 2. |
| Plain claim wording and the running example | **done** | §1 running example. |
| Stage-by-stage failure/success table | **done** | Table 2. |
| Grader controls in the body (positive, naive, removal sweep) | **partly** | Positive control and cheaters are in §2. Add to §2 Grader after "with a removal gate": "; a naive attribution answer earns full reward on only 1 of 3 trap episodes, and a stricter removal setting (f = 0.9, k = 8) does bind (Appendices B, C)." |
| Power sentence | **partly** | The sentence is present but the cold reader could not tell which drop it means. Old: "detects only a drop of 0.54 at 80% power" → new: "can detect only a pass-rate difference of 0.54 at 80% power". Confirm the contrast against V4 §3 before printing. |
| Rank-by-rank allocation in one sentence | **done** | §5.2 "84 of 95 isolations ... against 36 of 93 blind". |
| Per-run cost next to the matched-budget rule | **missing** | In §3 Matched budget, after "3,600 s of charged time." add: "(a Terra run at 8 queries costs about $0.68 at list prices; Appendix K)". |
| Reference-policy and agent comparison | **partly** | Carried by Figure 2a and the §5.1 text. Acceptable. |

**Keep from V5**

| Item | Status |
|---|---|
| Reliability vs validity, the ladder, placebo, report-free control, trivial rule, 3 judges × 2 prompts | **done** |
| Leaderboard reordering | in Appendix E only; acceptable given length (the −0.19 gap carries the point) |
| PPI | in the appendix, per the moderator |
| Curves, not one exchange rate (11 to about 50) | **done** (§5.1) |
| Depth panel | **done** (Figure 2b; fix N6) |
| Open-4 arm; held-out replication with the out-of-band result | **done** |
| Ledger with Bonferroni, unconfirmed tests listed | **done** (Table 3; Appendix M) |
| First-batch width on the trap probe (corrected Claim 3) | **done** (Table 2, queries on the trap vs other probes) |
| Token-cap check | **done** (§3, including +0.46) |
| Cost per pass | in Appendix K only. Acceptable, but see the efficiency sentence in A4. |

---

## 5. (d) Author decisions (moderator §4, as recorded in V6_PLAN)

| Decision | V6 | Status |
|---|---|---|
| 1. Lead: the ladder, with agents as testbed | Title, abstract, §4 first | **done** |
| 2. Title: "No Substitute for Ground Truth..." | "No Substitute for Ground Truth: In ShiftHunt, an LLM Judge Grades Research Agents Only When It Holds the Answer Key" | **done**. Optional: drop the awkward "In ShiftHunt" → "No Substitute for Ground Truth: An LLM Judge Grades Research Agents Only When It Holds the Answer Key". |
| 3. Claim 3 descriptive | Body yes; abstract no label | **partly**. Fix A1. |
| 4. Last run slot: freeze | No gap-removed Terra run; it is a limitation | **done** |
| 5. State what is measured (SAE-ranked causal verification over 8 closed candidates; rationed queries stand in for experiments) | Running example (eight properties); "budget is artificial, but it mirrors empirical research"; Limitations | **partly**. Add to the end of §2 Probe types: "What ShiftHunt measures is causal verification of SAE-ranked candidates from a closed set of eight, with rationed exact queries standing in for costly experiments." |

---

## 6. Highest-value text changes (A1-A5)

**A1. Abstract, last four sentences.**
- Old: "Without the key, the judge's agreement with the executed grade stays at or below κ = 0.26 on every run set, never above a rule that credits any named answer, and it keeps crediting omissions. With the key, agreement reaches 0.92-1.00 (pre-registered). On traps where the tools rank a decoy first, GPT 6.1 Terra passes every held-out item (20/21 runs) and GPT-6 Luna rarely does (2/17). Evaluating research agents needs executed ground truth."
- New: "Without the key, the judge's agreement with the executed grade stays at or below κ = 0.26 on every run set, below a rule that credits every named answer, and most of what it wrongly credits are omissions. With the key, agreement reaches 0.92-1.00 (a pre-registered positive control). Descriptively, on three held-out traps from the same builder, where the tools rank a decoy first, GPT 6.1 Terra passes every item (20/21 runs) and GPT-6 Luna rarely does (2/17). Evaluating research agents needs executed ground truth."
- This splits the three-claim sentence the cold reader flagged. Word count is about +10.

**A2. §4, the rule caveat where the rule is introduced** (the cold reader's issue 2; reviewer W6).
- Old: "A rule that credits every named answer and rejects every `none` scores 0.67, 0.37 and 0.75 on the three sets; without the key, no level beats it on any set."
- New: "A rule that credits every named answer and rejects every `none` scores 0.67, 0.37 and 0.75 on the three sets. It is strong only because every hard probe here has a cue, so it is a reference for this design, not a usable judge. Without the key, no level beats it on any set."

**A3. §1, pre-empt "trivially true".** After "Few studies test such a judge against a grade that is executed rather than opined." add:

"One might expect a judge to fail on an omission, but the transcript does show which candidates the agent tested and what the proxy ranked next, so a cautious judge could withhold credit from an untested `none`; ours credits most of them. The practical cost is concrete: graded by the report-level judge, a 0.86 executed gap between two agents reads −0.19."

All numbers are in §4; this promotes the −0.19 result that the cold reader called the most persuasive.

**A4. §9, efficiency for the CFP.** After the spend sentence add: "For scale, a Terra run at 8 exact queries costs about $0.68 and a transcript-level judge call about $0.08 ($29.25 for 354), while the executed grade needs no LLM call, only forward passes of the 2B model on 256-384 hidden notes per probe."

The $0.08 is derived from the two figures given, $29.25 / 354.

**A5. §6, item-level first and length.**
- Old: "The run-level p-values that carry agent claims (...) survive Bonferroni correction ...; the held-out gap's p = 0.002, on two items, does not. Item-level statements are primary."
- New: "Item-level statements are primary: with the proxy at 8 queries Terra is higher on 6 of 6 items, on the shipped traps on 3 of 3, and on the held-out traps it passes every item. The run-level p-values (...) describe these items only; they survive Bonferroni correction over all 45 registered entries (α ≈ 0.0011), and the held-out gap's p = 0.002, on two items, does not."
- **If the compiled paper is over 8 pages**, move Table 3 to Appendix M (it is already a superset) and keep: "Of the 14 tests behind the body's claims, 9 were confirmed (one registered after Terra's results), 3 were not, the answer-key control landed above its predicted band, and one Terra-Luna test fell outside every band (Appendix M)." This saves about 330 words.

---

## 7. Five attacks a sceptical reviewer is still most likely to make

**1. "Trivially true: a judge cannot see what was never tested, and of course the key fixes it."** This is the most likely objection. It is already raised by the cold reader and in the moderator's live disagreement D.
- *Cheapest honest fix:*
  - Add A3 to §1 (the transcript does expose *which* candidates went untested, and the judge still credits most untested `none`s; and the 0.86 → −0.19 consequence).
  - Move "A positive control, not string matching" up to sit directly after "The ladder".
  - Keep the open test explicit: a keyless judge with its own exact-query budget.

**2. "Your trivial baseline is a design artifact; hard-slot κ just measures leniency to `none`."**
- *Fix:* A2, which moves the caveat from Limitations into the sentence that introduces the rule. Also say "below a rule that credits every named answer" in the abstract, not "never above", and avoid calling it a baseline any judge should beat in general.

**3. "Omissions-vs-commissions is cherry-picked from set A; Appendix E shows the main study going the other way."**
- *Fix:* N1. Retitle the heading and Table 1, add the two-sentence cross-set disclosure, and restate the robust claim: omissions remain most of the false credit at every keyless level on every set (17/20, 10/14, 8/13 at L2).

**4. "The agent result is the contract tell plus one builder: rank 2 only, same builder, capability-confounded, and Terra judges its own family."**
- *Fix:*
  - Use A1 ("Descriptively, on three held-out traps from the same builder").
  - Use N8 ("widens mostly on the trap probe", not "targeted").
  - Lead §5.4 with its takeaway: "The contract's gap can tell an agent *that* the proxy is off on a trap, not *where*: gap-only scripts pass at most 3 of 15 shipped-trap cells, and whether Terra uses the gap is untested."
  - Insert whichever pre-written closeness sentence applies, if that script is run before the deadline.

**5. "The κ differences are noise: no intervals, six items, a placebo that beats the real log, 7 of 24 hard-slot flips on re-send."**
- *Fix:*
  - Use N2 (the placebo sentence that makes the noise point yourself).
  - Add the to-do 2 Statistics sentence (no item-clustered κ intervals, so only the keyless-versus-key gap is interpreted).
  - Use A5 (§6 leads with item-level results).

  The lead result survives all of this because the L2-to-L3 jump (0.24-0.26 to 0.92-1.00) is several times larger than any keyless difference.

---

## 8. Hard-rule check

- **Cue confidentiality:** no probe or episode id appears next to a cue property. Held-out items are numbered 1-3; cues are only [main] and [decoy]. Appendix D's answer-type column ("head", "main", "`none`") reveals no cue. **OK.**
- **October material:** only in Appendix P, marked [oct-check] and not load-bearing. **OK.** Minor: Appendix P and Table K2 say "13-17 November". If every run finished earlier, give the actual end date.
- **Anonymization:** no names, emails, URLs or branch names; "anonymized repository" in §9. The image tags (`rl-task-...`) appear only in the results file, not the paper. **OK.**
- **Numbers:**
  - Every body number checked traces to the results file or `ladder.json`. That includes Table 1, the ladder values, the rule per set, 20/21 and 2/17, Luna 1/5, 1/5, 0/7, the Haiku −0.21 and 82/87, the spend, AUROC, 31/39, the band rates and 3/14 vs 5/12.
  - **Exceptions:** the four items N3, N4, N5 and N7.
  - No placeholders in the body.
