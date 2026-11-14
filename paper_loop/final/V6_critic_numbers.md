# V6 number audit and overclaim check

Scope: every number, n, p-value, interval and status in `final/PAPER_V6.md` (body, tables, captions, Appendices A-P) and `final/fig/FIGURES_V6.md`. I checked them against `gpu_results/RESULTS_FOR_PAPER_2e30670.md`, `gpu_results/data/*` (c6, c6b README, c6bh, c6c, c6c ladder.json, c14/c14b/c14l READMEs, xr_curves, xr_alloc, xr_noise, followup_solvers band.json, topicunit.json and README), `exchange_rate/SUMMARY_PLAIN.md`, `exchange_rate/00_ANSWER.md` and `referee.md`, and, for numbers that predate the GPU plan, `final/PAPER_V5.md`. I recomputed the Wilson intervals and Fisher p-values.

**Bottom line.** The numbers are in very good shape. Every κ cell in Table 1, Table E1 and Figure 1 matches `ladder.json` / `c6.json` / `c6c.json` exactly. Every Fisher p and Wilson interval I recomputed matches. Every held-out per-item count matches c14/c14b/c14l, every scripted-policy value matches `xr_curves.json`, and every firing rate and checker rate matches `band.json` / `topicunit.json`. I found **two small factual mismatches** and about a dozen claims that are **stronger than the evidence or inconsistent in status**. For acceptance, the claims matter much more than the mismatches. Items are listed by priority.

---

## A. Priority 1: claims stronger than the evidence (fix before submission)

1. **"Commissions are caught, omissions are not" holds on set A only, but the paper states it as general.**
   - §1 contribution (ii) says "More evidence teaches the judge to reject wrong named cues but not wrong `none` answers". §4's heading and Table 1 say the same.
   - In `ladder.json`, set A fits: `none` credit 23 → 21 → 17 of 26, wrong-cue credit 9 → 7 → 3 of 17.
   - Luna's runs do not. `none` credit falls 24 → 21 → **10 of 38** (63% → 26%), about as much as wrong-cue credit (11 → 6 → 4 of 15, 73% → 27%).
   - The main study goes the other way: wrong-cue credit **rises** 3/6 → 5/6, while `none` credit falls 13/13 → 8/13. E1's note admits the rise; the body does not.
   - Fix: scope the sentence to set A, or rephrase it as "the key, not the transcript, is what removes omission credit on every set (0 of 26 / 38 / 13)". The key result holds on all three sets. Add one clause on Luna and the main study.
   - Also, "Credited `none` failures barely move" is true only of set A's 23/21/17.

2. **The item-level standard is applied inconsistently. This is reviewer W1 and is still not fixed.**
   - §3 and §6 say "item-level statements are primary". But §6 then argues survival with run-level p-values (2e-7, 3e-6), and Table 3 marks the shipped-trap Terra-Luna test "confirmed, after Terra's results".
   - The shipped-trap contrast has the same item-level evidence as the held-out contrast: 3 of 3 items, one-sided sign p = 0.125. §5.3 calls the held-out contrast "descriptive" for exactly that reason.
   - BB-16 is called "inconclusive" because its item-level p is 0.125 (D1, M1).
   - By one standard, these items survive at item level: C1, C2 and X3-H1, each higher on 6 of 6 items (one-sided sign p = 1/64 ≈ 0.016; V5 gave 0.031 two-sided for C1). The L1/L2 shipped-trap contrast does not.
   - Fix:
     - add the item-level result beside each run-level p (6/6 for C1, C2 and X3-H1; 3/3, p = 0.125 for L1/L2 and for the held-out contrast);
     - label L1/L2 "confirmed at run level (3 items); item level 3/3, p = 0.125";
     - keep "descriptive" for the held-out contrast.
   - State the sidedness. The held-out 0.125 is one-sided on 3/3; BB-16's 0.125 is **two-sided** on 4/4 non-tied (one-sided would be 0.0625).
   - Also still missing from the review's to-do list: item-clustered κ intervals for the headline κ values. I cannot supply them; they need an analysis run.

3. **The C1 test is described two ways.**
   - Table M1 calls the test "item-clustered, permutation, Holm" with p = 0.0002. §6 calls the same p "run-level".
   - With 6 items, an item-level permutation cannot give p below 1/64. So the CI is item-clustered and the p comes from a run-level (within-item) permutation.
   - Fix M1's "test" cell to read "item-clustered CI; run-level permutation p, Holm".

4. **The abstract and §1 call the key level "(pre-registered)" with no outcome stated.** It was pre-registered as a prediction of 0.60-0.90, and it missed the band on the high side on 5 of 6 bases. Read cold, "(pre-registered)" signals "confirmed". Fix: "a pre-registered positive control, which landed above its predicted band". §4 already says this; carry it into the abstract and §1.

5. **The abstract's agent result has no qualifier.** "GPT 6.1 Terra passes every held-out item (20/21 runs) and GPT-6 Luna rarely does (2/17)" gives no "three items, same builder, descriptive". The review's to-do list (W3) asked for the fresh-trap contrast to be labelled descriptive in the abstract. Fix: "on three held-out traps from the same builder … (descriptive)".

6. **§4 heading "Reliable but not valid".**
   - Hard-slot test-retest is Fleiss κ 0.39 (C17), with all three replicates agreeing on only 60% of hard slots. Re-sending Terra's 24 Open-8 calls gives κ 0.32 with 7/24 flips. That is "fair", not "reliable".
   - RESULTS' own wording is "partly stable, invalid".
   - Fix: "Partly stable, not valid".

7. **§5.1 "the proxy did not lift Luna (5/36 vs 1/24; not confirmed)" and "The gain is Terra's".**
   - "Not confirmed" (p = 0.22) is not "did not lift". Luna's point estimate is higher with the proxy, and exploratory ordinary-slot passes are 62/72 vs 8/48.
   - The sentence cites Haiku's trap result (0/6 vs 2/6) but leaves out Haiku's two-part result (5/6 vs 1/6 with the proxy, D2). That reads as selective.
   - Fix: "the registered lift for Luna was not confirmed (5/36 vs 1/24); Haiku gained on two-part probes (5/6 vs 1/6) but not on traps (0/6 vs 2/6)".

8. **Figure 2 title: "The proxy shifts Terra's whole budget curve".** Terra has proxy points only at B = 4 and 8, so there is no proxy curve at 16 or 64 to shift. Fix: "With the proxy, Terra reaches at 4-8 queries what it needs 16-64 for blind; at 8 a top-two script does as well".

9. **The Figure 2b citation does not match the plotted lines.**
   - §5.3 cites "a policy told the trap rank stays at 0.90-0.95 … (Figure 2b)". But `FIGURES_V6.md` lists the plotted (b) lines as top-two, Bayes with the bank prior, hedge and best blind. The told-rank policy is not drawn.
   - The caption lists only panel (a)'s lines, and never names hedge.
   - Fix: either plot `bayes_law` (0.9533/0.9033/0.9167/0.9200/0.9167 in `xr_curves.json` depth; RESULTS rounds these to 0.95/0.90/0.92/0.92/0.92), or cite Appendix H instead of Figure 2b. Also list (b)'s lines in the caption.
   - The depth wording elsewhere is correct: "agents show one-step widening, not depth"; "only scripts show depth"; "references, not bounds" in H. No "bounds" misuse anywhere.

10. **§6 claims "Table 3 lists every pre-registered test, including those not confirmed".** Table 3 is a subset. Missing: the harder-variant prediction ("not supported as registered"), BB-16 (inconclusive), C4, C3 (not run), C12, C17, C7 P3, J13, C14 H1b/H6, C14b H1c/H2c/H5c and C14L. The harder-variant row is a failed registered prediction, so leaving it out of the body table invites a selective-reporting complaint. Fix: "Table 3 lists the main pre-registered tests; Appendix M lists all of them, including the unsupported harder-variant prediction".

11. **The Table 3 key row understates its range.** "answer key: κ in 0.60-0.90 | 272; 6 | 0.92-1.00 | above band (5 of 6 bases)". The n of 272 includes the 18 harder-variant runs, whose κ is 0.77, inside the band. Fix: "0.92-1.00; harder variant 0.77 (in band)".

12. **The harder variant should not be in Figure 1.**
   - The moderator's consensus #3 says "Hold 0.77 until W9 is reconciled", and Appendix L says it is still not reconciled.
   - On that set L3 = 0.77 sits **below** the trivial rule's 0.87. That contradicts the caption title "with it, the judge is nearly perfect".
   - Fix: drop the harder variant from Figure 1 (it adds no claim) or drop "nearly perfect".

---

## B. Priority 2: factual mismatches (cheap to fix)

| # | Where | V6 says | Correct | Source |
|---|---|---|---|---|
| B1 | §6 and Appendix M "Multiplicity" | Bonferroni "over all 45 registered entries" / "45 rows of this table" (α ≈ 0.0011) | Table M1 has **46** rows (45 if the [oct-check] R1/R4 row is excluded; say so). α/46 = 0.00109. Every claimed survivor still survives, and C14 H2's 0.002 still fails | count of rows in `PAPER_V6.md` Table M1 |
| B2 | §4 Robustness / §1 | "Hiding the SAE outputs from the transcript lowers κ (main study 0.26 to 0.18)" | Correct, but give both figures: set A open arm 0.35 → 0.29 and main study 0.26 → 0.18 | `gpuplan_c6b_README.md` |
| B3 | §5.2 | "The proxy concentrates Terra's tests on its top two candidates (84 of 95 isolations at 8 queries, against 36 of 93 blind)", in a paragraph headed "(100 runs with the proxy …)" | The 84/95 and 36/93 come from **Terra's Block 1 Open-8 vs BB-8** (24 + 24 runs), not the 100-run development set. Say "Terra, controlled block" | Table J1; V5 |
| B4 | §5.3 and Table 3 | "registered Terra-Luna gap on the first two held-out items (0.63)" | The gap is the **iso(main)** (isolation) gap: 13/14 vs 3/10. The naming gap on the same runs is 13/14 − 2/10 = 0.73. Say "isolation gap" | `gpuplan_c14_README.md` H2 |
| B5 | §4 Consequences | "On the held-out traps the judge credited 6 of 10 … failed trap answers" | The 10 failures include one from the 3-run **shipped anchor** (27 runs = 24 held-out + 3 anchor). Say "on the held-out runs and the shipped anchor", or give 5/9 held-out only if that split is in the data (it is not in the sources; do not invent it) | `gpuplan_c14_README.md` H5 |
| B6 | Figure 1 caption vs §4 | Dotted line = test-retest κ 0.44 (set A, L0 vs L0r Cohen κ, **all 520 slots**). §4's text cites Fleiss κ **0.39 on hard slots** (C17, 214 runs) | Not wrong, but two different statistics on two populations, and an all-slot κ drawn on a hard-slot axis. Use the hard-slot 0.39 (C17) for the line, or say in the caption that it is all slots and not comparable to the hard-slot lines | `gpuplan_c6_c6.json` `test_retest_L0_L0r.kappa` 0.4429 (520 slots); RESULTS C17 |
| B7 | Appendix G Table G1 | Only the topic-unit column is labelled [expl] | The **proxy unit is exploratory too**: "Exploratory, in band.json 'proxy_unit' (… not in DEFINITIONS)". Only the class-gap unit is frozen. §5.4 leans on the proxy unit, so label it | `followup_solvers_README.md` |
| B8 | §5.4 | "the gap says *that* something is off, not *where*" | True on the **shipped** traps (≤ 3/15 cells). But proxy-unit V1 passes 0.433 of all bank traps (0.467 of the 21 other bank traps), so on bank traps the gap sometimes does point to the cue. Add "on the shipped traps" | `followup_solvers_band.json` `tables.proxy_unit.V1` |
| B9 | §5.1 / Appendix H | Exchange rate "ranges from 11 to about 50 queries" | The Terra-fit value is ≈ 36 with equally defensible fits spanning **22-58**, so the upper end is 58, not 50. Say "11 to about 50 (fits to Terra up to 58)" | `exchange_rate/SUMMARY_PLAIN.md`; Appendix H |
| B10 | Table 2, "targeting" row | Status "exploratory" for widening on ordinary probes (4/48 vs 2/72) | Part of pre-registered L4 (descriptive) per Table J3. Use "descriptive" | Appendix J3 / M1 L4 |
| B11 | §1 "Why it matters" | "18.7% of 'nothing found' verdicts were wrong, against 2.5% of named claims (400 verdicts; exploratory)" | Numbers correct (23/123, 7/277; Wilson [12.8, 26.5], [1.2, 5.1]). V5 had the caveat **"at our null share of 1/4"**, and V6 dropped it. The predictive value is design-dependent (40.8% at q = 0.10, 7.1% at 0.50; Appendix E). Restore the caveat in the body | `PAPER_V5.md`; Appendix E |

---

## C. Verified correct (no action)

- **Ladder, all sets and levels** (Table 1, Table E1, Figure 1, §4, abstract): match `gpuplan_c6c_ladder.json` and `gpuplan_c6_c6.json`.
  - Set A: −0.021 / 0.0626 / 0.2405 / 0.9156 / 1.0, rule 0.6718.
  - Luna: 0.0177 / −0.0333 / 0.2581 / 1.0 / 1.0, rule 0.3715.
  - Main study: 0.0562 / 0.2629 / L2r 0.176 / 0.962, rule 0.7529.
  - Harder variant: 0.10 / 0.7692, rule 0.8696.
  - Every FC, FB, `none`-index and null-FB cell matches, as do the κ-among-named values. L0r −0.007 and L1r 0.1978 match too.
- **Holm**: J11 Δ +0.18, LB +0.02, p = 0.030 > 0.025, "not confirmed after Holm". J12 7 → 3 of 17, McNemar p = 0.11. J5′ +0.08 (LB −0.02). J6 7 → 7 (L0r → L1). J7′ 0.19. All match the c6.json / c6b README. **L2 is never called an improvement without the Holm caveat** (§4 "Statistical status", Table 3, M1).
- **Haiku judge**: H0 −0.11, H1 −0.23, H1r −0.10, H2 −0.21, false blame 82/87, Δ +0.02 (LB −0.05), open arm −0.22 / −0.18 / −0.02 (n = 35). These match `gpuplan_c6bh_c6bh.json`.
- **C8**: κ 0.018, 35/53 [0.53, 0.77]; judged gap −0.19 [−0.42, +0.03] vs executed 0.86 (11/12 − 1/18 = 0.861). V6 does **not** call this "reversed" (good). The interval includes 0.
- **C12, C7, C17, C14 H5, C14b H5c**: all match RESULTS.
- **Agents**: 12/12 (Wilson 0.758-1.000), 23/24 (0.798-0.993), 6/24, 16/24, 24/24; Table D1 rows sum to D2. Luna 5/36 vs 1/24 (trap 1/18 vs 1/12, two-part 4/18 vs 0/12). Haiku 5/3/8 of 12. Main study 14/12/11/8 of 16 (traps 22/32, two-part 23/32). Open-4 trap/other 2.67 vs 0.44.
- **Held-out** (D3, Table 2, §5.3, L): Terra 7/7, 6/7, 7/7 = 20/21 (Wilson 0.773-0.992); iso 6/7, 7/7, 7/7. Luna primary 1/5, 1/5, 0/7 = 2/17 (iso 3/17); 7-run 2/21 (iso 3/21); answers head 11, `none` 5, other wrong 3, main 2. Breadth 2.81 vs 0.71; texts 3.67/1.44 vs 2.86/1.71; one-burst 18/21 vs 21/21. C14 13/14 (Wilson 0.685-0.987). These match the c14/c14b/c14l READMEs. Luna's 9/17 primary head answers support "most often answered with the proxy's favourite".
- **Recomputed one-sided Fisher p** (all match): C1-equivalent 23/24 vs 6/24 = 2.8e-7 (the paper's 0.0002 is the Holm permutation p, fine); X3-H1 1.48e-5; L1 2.20e-7; L2 2.51e-6; L3 0.22; C14 H2 0.0023; H2c 0.00029; C14L 6.3e-8; shipped vs held-out 0.797; J2 table 2.4e-10 / 0.0011 / 0.00084 / 0.025. C12 two-sided sign p = 1.9e-9.
- **Scripted policies** (H1, Figure 2, §5.1, §5.3): all match `gpuplan_xr_curves.json`: Bayes bank 0.17/0.49/0.80/0.95/0.98/0.98; told rank 0.17/0.49/0.93/0.96/0.98/0.99; top-two 0.00/0.49/0.66/0.96/0.99/1.00; hedge 0.50/0.50/0.50/0.68/0.79/0.90; top-one 0/0/0/0.50/0.50/0.50; best blind 0.10/0.21/0.27/0.44/0.79/0.97; flat 0.00/0.16/0.16/0.16/0.84/0.96. The depth values match too, and "at 4 no rank-only script exceeds 0.50" holds (hedge and proxy-only are 0.50 exactly).
- **X4 allocation and burst** (J5, Table 2): match `gpuplan_xr_alloc.json` (Terra 4.0/1.33 and 3.92/1.36; Luna 1.94/2.02; Haiku 3.67/1.44; Opus 4.57/1.14; Sonnet 3.5/1.5; burst counts; Haiku follow-up 4/5).
- **X2 noise** (I): matches `gpuplan_xr_noise.json` (0.051/0.074, 0.110/0.135, 1.3%, 1.4%, trap 3.1%, n 113/1311).
- **Contract gap** (§5.4, G1, G2): match `band.json` and `topicunit.json`.
  - Proxy unit: 15/15, 0.925, 0.205, 0.290, 0.422, 0.258.
  - Topic unit: 12/15, 0.358, 0.260, 0.358, 0.667, 0.022.
  - Class-gap unit: 0/15, 0.108, 0.566, 0.597, 0.822, 0.072.
  - V1 proxy unit: 3/15, 0.433, 1.000, 0.017, 0.282. Ub2: 0/15, 0.217, 0.978, 0.017, 0.282. Topic V1: 0.017, 1.000, 0.024, 0.022.
  - Class-gap V1: 0.000, 0.889, 0.159, 0.072.
  - Unit factor 1.43-2.14 → "1.4-2.1". Gap share 0.41/0.47/0.58, median 0.56 (0.36-0.76), AUROC 0.84, false positives 0.62/0.77.
  - "About 2.5×" = 0.205 / (4/48) = 2.46.
- **Exchange-rate decomposition**: information 0.30-0.64, blind shortfall 0.10-0.45, misuse 0.00-0.04, bracket (16, 64] / (8, 64], abstract-model values, 0.36 → 0.76. These match `exchange_rate/00_ANSWER.md`, `referee.md` and `SUMMARY_PLAIN.md`.
- **Spend** (§9, K2): every row and both totals ($101.45 / $5.27; the rounded rows add to 101.48) match RESULTS. K1 per-pass costs check by arithmetic (e.g. 0.678 × 24/23 = 0.707; break-even 0.335/55.65 = $0.0060; 2,083/55.65 ≈ 37c).
- **Pre-GPU-plan numbers**, checked against V5: 61/64 runs; ≤ 77 tool calls; 53/57 and 26/30; 116/116; 41/44; 13 of 36 pairs; 62/72 vs 8/48; prompt sizes 9,459/6,592/7,254/10,121; 293/293, 183/183 and 706 tests; 0.858; 2,713; 748/750; 36-61%; [decoy] and [main] readings; null-share 40.8%/7.1%; 1/98 vs 24/75; the cap test p = 0.031; 47/100; 10/16 vs 21/32; 69/73; power 0.54 / 84 runs; 23/24 vs 5/88; route counts (sum checks: 25 + 5 = 30 passes, 1 + 16 = 17 failures, 26 + 5 = 31). All match.
- **Hard rules**: no episode or probe id or internal tag (ep4xx/ep80x, F2-a/b/c, image tags, pool names) appears in V6. Cues appear only as [main]/[decoy]. October material appears only in Appendix P and the R1/R4 row, marked never load-bearing. No URLs, names or branches. "http_503" is an error code, not a URL. No placeholders found.

---

## D. Lower-priority wording (optional)

- Title: "Only When It Holds the Answer Key" is scoped by "In ShiftHunt", but it generalizes past what was tested. One judge family plus a Haiku check, two prompts; the keyless judge with its own query budget is untested (§8). Acceptable given the scope. "Without the answer key, an LLM judge fails to grade…" would be safer.
- §4's opening sentence, "the judge does not track the executed grade, whatever of the agent's material it reads". L2 reaches κ 0.24-0.26, which is weak tracking, not none. Consider "never beats a trivial rule".
- §5.4, "off traps it fires about 2.5 times as often as Terra widens". This compares probe-level firing over the bank (single-main ordinary) with Terra's widening on the shipped ordinary probes. Against nulls (0.258) or ordinary including two-main (0.290) it is about 3.1-3.5×. Say "2.5-3.5 times".
- §9 reports only the final round's spend. RESULTS gives the cumulative RUNLOG totals (OpenAI $192.21, Anthropic $83.67 at the end of the plan). The CFP stresses efficient evaluation, so consider giving the cumulative total once.
- Body length: about 4,900 words before the references, plus 3 tables and 2 figures. Compile in the AAAI kit to confirm it fits 7 pages.
