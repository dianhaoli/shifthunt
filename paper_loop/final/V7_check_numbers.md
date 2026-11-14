# V7 number audit and overclaim check

Scope: every number, n, interval, p and status in `final/PAPER_V7.md` (body, captions, Tables 1-3, Appendices A-P) and `final/fig/FIGURES_V7.md` (and the rendered `fig1_v7.png`). Checked against `gpu_results/RESULTS_FOR_PAPER_84b3a82.md` and `gpu_results/data/`: `gpuplan_v_*`, `gpuplan_a_*`, `gpuplan_b_*` (`reconcile.json`, `body_numbers`), `gpuplan_t_*` (`tell.json`, `tell_posthoc.json`), `gpuplan_k_*` (`k.json`), `gpuplan_RECONCILE.md`, `gpuplan_c6_c6.json`, `gpuplan_c6c_ladder.json`, `gpuplan_c6b_README.md`, `gpuplan_c6bh_c6bh.json`, and the c14/c14b/c14l READMEs. Numbers that predate the GPU plan were checked against `PAPER_V5.md` / `PAPER_V6.md`, and against `V6_critic_numbers.md` §C where that audit already confirmed them.

**Bottom line.** The Round 3 numbers (V, A, B, T, K) are carried over correctly: every cell of Table 1, Table E1, Table E2, Table F2, Table G0 and Table 3, and every value in FIGURES_V7, matches its source. I found **no wrong digit in a table**. The problems are a few **headline sentences that say more than the tables**. Most important: "given the key the judge credits no failure" is false on the main study, and "the judge still credits most [wrong `none`]" is false at the transcript level pooled over the 77. A few smaller scope and wording slips follow.

---

## 1. Mismatches: text vs source (fix)

| # | Where in V7 | V7 says | Correct value | Source |
|---|---|---|---|---|
| 1 | Abstract ("Given the answer key, the judge credits no failure, even from the report alone"); §1 What we find ("Given the answer key, the judge stops crediting failures"); §10 ("the same judge given the key credits no failure") | No failure credited with the key | True on **set A and Luna only** (every key level: 0/17 + 0/26; 0/15 + 0/38). On the **main study**, transcript + key credits **1 of 6 wrong cues** (1 of 19 failures). Fix: "on set A and Luna's set, the judge given the key credits no failure; on the main study it credits 1 of 19" (or scope the sentence to set A) | `gpuplan_c6c_ladder.json` `main_study."L3 = L2 + key".false_credit_wrong_cue` = 1/6; `gpuplan_b_reconcile.json` `credit_baselines.main_study.L3_2.commissions` = 1/6; V7's own Table E2 and F row |
| 2 | Abstract ("a ceiling version of the script decides none of 77, and the judge still credits most"); §10 ("the judge credits most such answers") | The judge credits most of the 77 wrong `none` | With the transcript, the judge credits **35 of 77** (17/26 set A, 10/38 Luna, 8/13 main), which is not most. "Most" holds at the **report level** (60/77: 23 + 24 + 13) or **on set A** (17/26 with the transcript). Fix: "and the judge, even with the full transcript, still credits most on our largest set (17 of 26)", or "credits most at the report level (60 of 77)" | `gpuplan_b_reconcile.json` `credit_baselines.*.L0/L2.omissions`; `gpuplan_v_README.md` |
| 3 | Abstract ("because the agent never tested every candidate"); §10 ("the agent never tested every candidate, so the log cannot decide it") | Never | **76 of 77**. In the 77th, all 8 candidates were isolated, but one read in the contract gap. §1 and §4 already say "76 of 77"; the abstract and conclusion should match. Fix: "because the agent almost never tested every candidate (76 of 77)" | `gpuplan_v_diagnostics.json`; RESULTS Round 3 V |
| 4 | §8 Limitations ("On three further held-out traps the judge ran only at the report level (it credited 6 of 10 and 5 of 7 failed trap answers)") | 6 of 10 on the held-out traps | The 10 failed trap slots come from **27 runs: 24 held-out plus the 3-run shipped anchor**, and the anchor's one failure is among the 10. Fix: "6 of 10 on the first two held-out items and the shipped anchor, and 5 of 7 on the third". (Same issue as V6 audit B5. Table 3's "27; 3" is right.) | RESULTS C14 H5 ("27 counted C14 runs (24 fresh-trap + 3 shipped anchor; the anchor's one failure is among the 10)"); `gpuplan_c14_README.md` H5 |
| 5 | Figure 2 caption title ("Terra reaches at 4-8 exact queries what it needs 16-64 for blind") | blind needs 16-64 | Blind at 16 is **16/24 = 0.67**, below the proxy arm's 23/24 and 12/12. The identified bracket is **(16, 64]** at run level and **(8, 64]** at item level (Appendix I). Fix: "what it needs more than 16, and up to 64, for blind" or "what blind needs 64 for" | Appendix I; Table D2; `FIGURES_V6.md` Fig 2(a) |
| 6 | Appendix E, end of "Hypotheses" ("The L1 gain over L0r was less false blame (33 → 25 of 87) with false credit unchanged") | false credit unchanged | False credit went from **27 to 28 of 43** (`none` 20 → 21 of 26; wrong cue 7 → 7 of 17). Fix: "false credit about unchanged (27 → 28 of 43)" | `gpuplan_c6_c6.json` `set_A.L0r` (20/26, 7/17, 33/87) and `set_A.L1` via `ladder.json` (21/26, 7/17, 25/87) |
| 7 | Appendix E1 "Reading" ("on all slots it is 0.17-0.28, below the transcript-level judge (0.28-0.58)") | rule 0.17-0.28 below the transcript level | The **0.28** is the harder variant's, and the harder variant has **no transcript level**. There the rule's all-slot 0.28 is *above* the report-level judge's 0.18. On the three main sets the rule is **0.17-0.26**, against transcript-level 0.28-0.58. Fix: "on all slots of the three main sets it is 0.17-0.26, below the transcript-level judge (0.28-0.58)". The source sentence in `gpuplan_a_README.md` has the same slip | `gpuplan_a_README.md` table (rule all-slot 0.22 / 0.26 / 0.17 / 0.28; L2 all-slot 0.32 / 0.58 / 0.28; harder L0 0.18) |
| 8 | §4 ("no keyless judge level exceeds 0.26 on any set"); Figure 1 caption and FIGURES_V7 suggested caption ("no level of access lifts the judge above κ 0.26") | max 0.26 | Main-study L2 is **0.263** (Luna 0.258), so "exceeds 0.26" is false at three decimals. This is cosmetic. Fix: "reaches at most 0.26" | `gpuplan_a_intervals.json` / `ladder.json` `main_study.L2.hard_kappa` 0.2629 |
| 9 | Appendix L.1 Consequences ("Judged Terra BB-16 − BB-64 on set A has the wrong sign at every Terra-judge level (executed −0.25; L0 +0.18, L0r +0.27, L1 +0.14, L1r +0.05)") | every Terra-judge level | The values cover **L0, L0r, L1 and L1r only**. RESULTS' "every rung" was written for C6, before L2, L3 and K0 existed; V7 now has those levels and gives no value for them. Fix: "at every report- and log-level judge" | RESULTS C6 bullet; `gpuplan_c6_c6.json` `J11_terra_contrasts` |

No numeric mismatch was found in Tables 1, 2, 3, A1, B1, C1-C3, D1-D3, E1, E2, E4, E5, F1, F2, G0-G2, I1, K1-K5, L1, L2, M1 or N1, or in FIGURES_V7.

---

## 2. Claims stronger than the evidence

### 2a. Causal language beyond the two measured parts

The two measured parts are: (i) on commissions, the log holds evidence that the judge does not fully use (V1 0/17, 0/15, 0/6 vs the judge's 7/17 and 3/17 on set A, and 5/6 on the main study); (ii) omissions cannot be decided from the log (V3 0/77; 76 of 77 left a candidate unisolated). These are causal readings that go further:

1. **§4, "The strict script credits fewer wrong `none` answers than the judge (7 of 26 on set A) only because it rejects most right ones as well."** The "only because" is not measured. The data show V1 credits 7/26 wrong and blames 86/125 right `none` answers, and nothing more. Fix: "It credits fewer wrong `none` answers than the judge (7 of 26 on set A), but it also blames 86 of 125 right ones."
2. **§4, the script "blames 23 of 87 passes on set A, because agents often leave no clean single-property test of what they claim".** The post hoc diagnostic supports this for **11 of the 23**, which had no clean isolating pair on the hard probe. In the other **12**, the agent isolated something but not the named cue above 0.30. Fix: "in 11 of these the agent left no clean isolating test on the hard probe" (`gpuplan_v_README.md` post hoc diagnostics).
3. **§5, "An omission is a test that was not run."** The evidence (26 of 30 failed planted probes never had the true cue tested; 53/57 tested true cues passed) covers all failures, not omissions specifically, and it is exploratory. The omission-specific fact is V3's 76 of 77. Fix: "Most failures are tests that were not run", or cite 76 of 77.
4. **§4, "Its leniency toward `none` is a prior."** This rests on C12 (descriptive: unsupported `none` credited 31/39 vs a true cue 1/39). That shows the leniency appears without any report. It does not show where it comes from. Acceptable, but "behaves like a prior: given scripted answers with no report…" is safer.
5. **§10, "a fixed script uses it more fully than an LLM judge reading the same log or the whole transcript."** This holds for commissions on every set. As a κ statement it holds only on set A, where the item intervals separate (V1 [0.39, 0.65] vs L2 [0.12, 0.36]). On the main study they overlap (V1 [0.34, 0.55] vs L2 [−0.04, 0.54]). Keep the sentence about wrong named cues.

The title, abstract and §1 keep the causal account within (i) and (ii). V6's "the judge fails for lack of ground truth" is gone. Good.

### 2b. Run-level p used as item-level

None found. §3 and §6 say run-level p-values describe these items only. Table 3 marks the shipped Terra-Luna test "confirmed (run level)", and the held-out contrast "descriptive (a one-sided sign test cannot go below p = 0.125)". N1's C1 cell reads "within-item (run-level) permutation p". Keep as is.

### 2c. "Clears" where intervals overlap

None found. Every "clears", "above" or "non-overlapping" statement checks out against `gpuplan_a_intervals.json`:
- the step to the key, at every level, on set A, Luna and the main study;
- not on the harder variant ([−0.25, 0.58] vs [0.43, 1.00]);
- set A report vs placebo log and vs transcript;
- every set-A keyless level vs V1 and vs the rule;
- main-study L0 vs V1;
- main-study L2 vs the rule (0.539 < 0.546, narrowly);
- Luna V1 below L2.

The body never calls the main-study script-vs-judge difference "above".

### 2d. Depth claims

- **§5 Limits, "our agents show one-step widening, not depth; only scripts show depth (Figure 2b)."** The first half is right. The second half points to the wrong figure:
  - The Figure 2b lines are top-two, bank-prior Bayes, hedge and best blind. The first two fall to 0 at r ≥ 3 **by construction**, and hedge (about 0.5) and best blind (0.40) are flat.
  - The only policy that holds up at depth, Bayes *told the trap rank* (0.90-0.92), uses privileged knowledge and is **not drawn** in 2b (Appendix I only).
  - Fix: "only scripted references are run at depth, and the one that holds up is told the trap rank (Appendix I)".

### 2e. Reference policies called bounds

None found. Appendix I says "references, not bounds". §5 limits its claim to "no script that uses only the ranking exceeds 0.50" at B = 4. That stays correct beside T's 0.66, because the band policy uses proxy readings, not only ranks.

### 2f. Other scope slips (minor)

- **§4, "the key level landed above its pre-registered band of 0.60-0.90"** comes right after K0's 0.81, which lies *inside* that band. Say "the log and transcript key levels (0.92-1.00) landed above…". (C6c's band applies to L3; K had its own reading.)
- **§4, first sentence.** It sets test-retest κ 0.39 (set A, 132 runs) against κ −0.006 (196 runs). The two populations differ. The like-for-like set-A value is −0.02 (130 runs). Not wrong, but give both or say "on the larger report-level set".
- **§5, "The trigger is selective."** This is true on the **shipped** cells (0/60 ordinary, 0/30 null). On the bank it fires on 45/385 = 0.12 of null cells (and 0.45 of trap cells). That is in G.1 but not in the body. Add "on the shipped items".
- **§1 contribution (iv), "passes all three held-out traps"** can read as every run. Terra is 20/21 (7/7, 6/7, 7/7). Say "passes each of three held-out traps (20 of 21 runs)".
- **§9, "$1.14 for the report-and-key calls"** leaves out the $0.045 dry run that L.2 includes. Fine for the body.
- **Appendix L.1, C21 "(random order: 50%)"** is ambiguous. V5 says a random order needs, in expectation, 50% of runs to catch 50% of errors. Write it that way.

---

## 3. FIGURES_V7.md and the rendered Figure 1

- Every plotted value and interval in Fig 1(a) matches `gpuplan_a_intervals.json` / `gpuplan_k_k.json` (for example set A K0 0.805 [0.561, 1.000]; Luna K0 0.914 [0.487, 1.000], 8 undefined draws; V1 0.524 [0.395, 0.655] and 0.426 [0.339, 0.550]). The test-retest line is 0.388 (hard-slot Fleiss, 132 runs): the V6 all-slot error is fixed.
- Every Fig 1(b) bar matches: 7/17, 21/26; 3/17, 17/26; 0/17, 7/26; 0/17, 0/26. The rendered PNG shows these values.
- Answer-type rule values in the caption (0.67, 0.37, 0.75; all-slot 0.22) match.
- **Inconsistency, not a number:**
  - The body embeds `fig1_ladder_v7.png`, which is panel (a) alone, with a caption for (a) only.
  - FIGURES_V7's suggested caption covers (a) and (b), and `fig1_v7.png` holds both.
  - Choose one. If (b) stays out of the body, Table 1 carries its numbers, which is fine.
- Same cosmetic point as mismatch 8: "above 0.26" against 0.263.
- Figure 2 is unchanged from V6, and its plotted values match `FIGURES_V6.md` / `xr_curves.json`. Only the caption title needs the fix in mismatch 5.

---

## 4. Verified correct (no action)

- **Body judge numbers.**
  - 36/39 (196 runs); κ −0.006, 48/62 (registered 214: 0.002, 53/68).
  - Test-retest 0.39 (132 runs).
  - C12 31/39 vs 1/39; AUROC 0.48-0.58 (274 runs).
  - Ladder −0.02 / 0.06 / 0.24 and 0.81 / 0.92 / 1.00 (set A); 0.91 / 1.00 / 1.00 (Luna); 0.96 (main study); harder variant 0.10 → 0.77.
  - Holm 0.030 > 0.025; J12 7 → 3, p = 0.11.
  - Luna's refuted [decoy] answers 0 / 4 / 6 of 7.
  - Main-study wrong-cue credit 3 → 5 of 6; Haiku 82/87, κ −0.21; C8 −0.19 [−0.42, +0.03] vs 0.86 (84 runs); 13 of 36 pairs; PPI 0.
- **Table 1.** Every cell matches `gpuplan_k_README.md` / `gpuplan_v_README.md` / `reconcile.json` `credit_baselines`; footnote 86/125.
- **V numbers.** 0/17, 0/15, 0/6; 7/26; 23/87; κ 0.52 [0.39, 0.65], 0.43 [0.34, 0.55], −0.16; gap unit 0.16; V3 0/26, 0/38, 0/13 = 0/77; 76 of 77; 34 of 256 slots; unit factor 1.4-2.1; Table F2 in full.
- **K numbers.** 0.81 [0.56, 1.00], 0.91 [0.49, 1.00]; 12 / 5 / 0 of 87; 190 calls; $1.14 (+ $0.045).
- **T numbers.**
  - 0.66 (per item 0, 1, 0, 1, 0.99, 0.95); 1.00 vs 11/12 (Wilson 0.65-0.99); 1.00 vs 4/48 (0.03-0.20).
  - Trigger 5/15, 0/60, 0/30; bank 47/105, 2/520, 45/385.
  - Shipped B = 8 0.84 / 0.73; bank 0.88 / 0.93, 0.27 / 0.78.
  - 2,000 seeds (deviation stated).
- **A numbers.** Every E1 cell, run interval and BA; prevalence 87/130, 7/60, 45/64, 12/18; `none` 26/130, 38/60, 13/64, 5/18; within-type κ.
- **B numbers.** E5's 196-run row (agreement 0.597 → 0.60, 31/134, all-slot 0.11, 79/111, 111/673); C17 0.47 / 0.51 (196: 0.46, 0.51); 0.34 / 0.44 on 130 runs; set A 132 → 130 (two http_503); [decoy]/[main] about 1.7 (0.362 vs 0.212).
- **Agents.**
  - Budget curve: 12/12 (Wilson 0.76-1.00), 23/24, 6/24, 16/24, 24/24; 6/6 items each (checked from Table D1); 0.96 top-two at 8; ≤ 0.50 at 4; 2.67 vs 0.44.
  - Luna: 5/36 vs 1/24.
  - Table 2 in full; 9/17 primary "head" answers support "most often the proxy's favourite".
  - Held-out: D3 matches c14/c14b/c14l (including the 7-run answers and 2.81 / 0.71, 3.67 / 1.44, 2.86 / 1.71, 18/21, 21/21); C14 H2 0.63, p = 0.002, naming gap 0.73; H2c p = 0.0003; C14L 0.81, p = 6e-8; shipped vs held-out p = 0.80; 13/15.
  - Margin 0.12 → 0.15 and one re-queued launch match `gpuplan_c14_README.md`.
- **Appendix sums.**
  - D1 rows sum to D2.
  - Main study traps 22/32 and two-part 23/32 (total 45/64).
  - K1 84/95 and 36/93; 1.32 / 1.29.
  - Route counts: 25 + 5 = 30 passes, 1 + 16 = 17 failures, 26 + 5 = 31.
  - Capability adjustment 0.42 → 7.0 of 18.
  - Bank 116 + 83 + 24 + 18 + 9 = 250.
  - Judge populations 254 / 272 / 274 / 190 / 84 / 27.
- **Spend.** L2 rows and totals $101.45 / $5.27 (rounded rows 101.48); cumulative $192.21 / $83.67; $29.25 / 354 ≈ $0.08.
- **Pre-GPU-plan numbers.** 61/64, 176, 116/116, 18.7% / 2.5% with the null-share caveat restored, 53/57, 26/30, 13/36, AstaBench τ 0.467 "on one of ten subsets", prompt sizes, B1, C1-C3, G2 tells, I and K tables, L1 costs, power 0.54 / 0.39. All match V5/V6, and V6_critic_numbers §C had already confirmed them.

---

## 5. Hard rules

- No probe, episode or image id and no internal tag (ep8xx, F2-a/b/c, `knob_*`, image names) appears in V7 or FIGURES_V7. Held-out items are "held-out 1-3"; shipped items are "trap 1-3", "two-part 1-3".
- No cue property name appears anywhere. The one detector-like word, "bullet" in Appendix A, refers to a bullet of the prompt. Trap cues are only [main] / [decoy].
- [oct-check] material is confined to Appendix P and the R1/R4 row of N1, marked never load-bearing. The new P item (contract-gap reasoning, 3/14 vs 5/12) is not used in the body.
- No names, emails, URLs or branch names; "anonymized repository" is used throughout ("http_503" is an error code). No placeholders.
- The body cites exchange-rate values from a file with no generating script nowhere. Appendix I flags them, as RECONCILE requires. The "fits 22-58" span and the "45 registered entries" are gone.
