# V8 number and wording audit

Scope: `final/PAPER_V8.md` (body, captions, Tables 1-3, Appendices A-O) and `final/fig/FIGURES_V8.md`, plus the rendered `fig1_v8.png` and `fig2_v8.png`. Checked against `synthesis/MASTER_FACTS.md` (MF rN = §2 row N, cN = §5 row N), `gpu_results/RESULTS_FOR_PAPER_f44495b.md` [R] and `gpu_results/data/` (`gpuplan_a_intervals.json`, `gpuplan_b_reconcile.json`, `gpuplan_b_body_numbers.json`, `gpuplan_v_verifier.json`, `gpuplan_v_commissions.json`, `gpuplan_v_diagnostics.json`, `gpuplan_k_k.json`, `gpuplan_c6c_ladder.json`, `gpuplan_c8_c8.json`, `gpuplan_c19_reorder.json`, and the c14 / c14b / c14l READMEs). Appendix text carried over unchanged from V7 was checked by `V7_check_numbers.md`; I re-checked only lines that changed and every body sentence.

**Bottom line.** I found no wrong digit in any body number, table cell or plotted value. The problems are:
- one wrong caption in FIGURES_V8;
- a false self-description in Appendix M;
- several "not computed" marks on values that were computed;
- 214-run values that lead where the 196-run value should;
- harder-variant numbers outside footnote b;
- four body sentences that say more than their master-table wording.

There is no October material, no date after 14 Nov, no name, URL, branch, item id or cue property name, and no placeholder.

---

## 1. Mismatches: text vs source (fix)

| # | Where | Says | Correct | Source |
|---|---|---|---|---|
| 1 | FIGURES_V8 l.125, Fig 2 suggested caption | "On the **held-out** comparison of Terra and Luna on trap probes" | The comparison uses the **shipped** trap probes (Open-8, 11/12 vs 1/18, 30 runs), as the paper's caption at l.109 says. Change "held-out" to "shipped". | `gpuplan_c8_c8.json` `gap_open8.trap`; MF r19 |
| 2 | App M l.831 | "the registered 214-run values appear **once**, in a footnote to Table 3" | They also appear in E5 (l.552-561), App E Robustness C17 (l.563), App J (l.697), N1 (l.852-854, l.881), M1/M text (l.815, l.827) and L.1 PPI (l.761). Either rewrite the sentence ("appear in footnote b of Table 3 and, as secondary values, in Appendices E, J and N") or cut those appearances. | the paper itself |
| 3 | App M l.831 | "We therefore report no result on the variant" | The same paragraph gives two outcome forms: "Terra 7/8 vs 6/8" and "11/15 vs 11/15". The sentence contradicts itself. Delete the counts and keep "our records give its outcomes in two unreconciled forms". See also §3. | MF §6.4 #1 |
| 4 | App E5 l.557, all-slot agreement, 196 runs | "—" with "—: not computed" (l.561) | Computed: **0.758** (196 runs). The cell should read "0.76 [0.765]". | `gpuplan_b_reconcile.json` `runs_196_reconciled.J4_all_slots.agreement` |
| 5 | App E1 footnote l.507, "Blank cells: not computed" | Several blank run-bootstrap cells | Computed: set A L3 transcript + key run **[1.00, 1.00]**; Luna L3 run **[1.00, 1.00]** (7 undefined draws); Luna V1 / V2 / V3 run **[−0.24, −0.06] / [−0.42, −0.07] / [0.00, 0.00]**; main-study V3 run **[0.27, 0.61]**. Only K0 (report + key) has no run interval (`k.json` stores the item bootstrap only). Fill the cells or reword: "blank: not shown". | `gpuplan_a_intervals.json` `*.hard_kappa_run_boot95` |
| 6 | Table 1 l.83, transcript + key, run 95% | "—" ("not computed", l.85) | Computed: **[1.00, 1.00]**. The "—" is right only for report + key (l.81). | `gpuplan_a_intervals.json` `set_A.L3_2.hard_kappa_run_boot95` |
| 7 | Table 3 l.136 | "every keyless level κ < 0.40 … ≤ 0.26" | Main-study L2 is **0.263**, so "≤ 0.26" is false at three decimals. This is cosmetic, the same as V7 fix 8. Write "at most 0.26" (rounded) or "≤ 0.263". | `gpuplan_a_intervals.json` `main_study.L2.hard_kappa` 0.2629; MF r16, c30 |
| 8 | Table 3 l.145, n column "30; 21; 24; 3" | The "3" reads as the item count for the held-out isolation gap | The gap 0.63 is C14 H2: **two** items, 14 + 10 = 24 runs. Write "24 (2 items)". (App H l.663 and N1 l.884 already say "two items".) | `gpuplan_c14_README.md`; MF r42 |
| 9 | App M1 l.817-818 | four-query arm "Nov 13-14"; held-out traps "Nov 13-14" | Every X3/X3b, C14, C14b and C14L run is stamped **13 Nov**: c14 13 Nov 08:40Z-14:28Z; c14b 13 Nov 19:18-21:35Z; c14l 13 Nov 21:35-22:10Z. This is not a date after 14 Nov, only a precision slip. Write "13 Nov". | MF §3 rows X3, X3b, C14, C14b, C14L; item READMEs |
| 10 | App E2 l.524 and l.530, K0 rows, "κ among named" | blank | Computed: **0.67** (set A) and **0.89** (Luna). E2 makes no "not computed" claim, so filling these is optional. | `gpuplan_k_k.json` `K0.kappa_within_named_hard` |

---

## 2. Claims stronger than the master-table safe wording

| # | Where | Says | Safe wording | Source |
|---|---|---|---|---|
| 1 | §1 l.21 | "With the key, the judge credits no failure from the report alone" | The claim is unscoped. K ran only on set A and Luna's set. The main-study keyed judge (transcript + key) still credits 1 of 6 wrong cues. Add "on set A and Luna's set" (the abstract already says "on either set tested"). | MF r36, r35, c23 |
| 2 | §1 l.21 "it lacks information, not reading skill"; §10 l.172 "One line of answer key fixes the grading" | Absolute | §4.4 l.99 hedges correctly: "on these items it lacks information more than reading skill". Use that wording in §1. For §10, write "grades almost perfectly" (MF r35), because main-study keyed κ is 0.96 with 1 of 6 commissions credited. | MF r35, r36 |
| 3 | §1 l.21 "no judge model or prompt separates them"; §4.2 heading l.65 "No judge model or prompt separates…"; Table 3 l.141 "no judge model or prompt separates right from wrong `none`" | General | Three judge models under two prompts, at report level only. Write "none of three judge models, under either of two prompts, separates…" (MF r12: "AUROC 0.48-0.58 in every cell"; "the sceptical rubric was run at report level only"). | MF r12 |
| 4 | §4.2 l.65 | the sceptical rubric "leaves the ranking unchanged" | For Terra as judge, ΔAUROC is **−0.10**, so the ranking did change, slightly for the worse. Write "does not improve the ranking (ΔAUROC −0.10 for Terra, −0.00 for Luna)" or "moves only the threshold". | MF r12; App E l.563 |
| 5 | §8 l.161 | "the placebo log **beats** the real one" | κ 0.20 vs 0.06, and both the item intervals ([0.06, 0.33] vs [−0.03, 0.17]) and the run intervals overlap. Write "scores above the real one (intervals overlap)", as §4.1 l.57 does. | MF r13, §6.1 #8; `gpuplan_a_intervals.json` |
| 6 | §4.3 l.91 | "The script rejects these cues because nothing supports them, not because the log refutes them" | This holds on set A (0/17 refuted). On Luna's set the log refutes 6 of 15, and on the main study 1 of 6, as the next sentence says. Open with "On set A, …". | MF r31; `gpuplan_v_commissions.json` |
| 7 | §4.4 l.99; Table 3 l.139 | keyed judge "landed above" / "above the band" | Registered on six bases. The sixth, the harder variant (κ 0.77), lay **inside** the band (MF r35: "above the band on 5 of 6 bases"). Appendix E l.550 and N1 l.870 say only "not reported". To avoid selective reporting while keeping the variant's single home, add to footnote b: "one further keyed base, on the same runs, fell inside the band (0.77)", or at minimum say "on all five main-set bases" in Table 3. | MF r35, r37; [R] l.84-86 |
| 8 | Table 3 l.140 | "κ 0.52 (set A, grader-side unit; agent-visible 0.16)" | MF r28: "always pair 0.52 with its strictness (23/87 passes blamed)". Add "blames 23 of 87 passes". Table 1 carries the 23, so this is minor. | MF r28, r29 |
| 9 | §4.0 l.51 | "With eight exact queries and eight candidates per probe" | The eight queries are per episode and shared by four probes, not per probe. Write "eight exact queries per episode (four probes) and eight candidates per probe". This is clarity, not a number. | App A budget l.342 |
| 10 | Abstract l.9 | self-agreement κ 0.39 against grade κ −0.006 (196 runs) | Two populations: 132 set-A runs vs 196 runs. §4.1 gives both n. The abstract gives only 196. Optional: "(κ 0.39 on set A)", or quote set A's own grade κ −0.02 (130 runs). | MF r7, r10; V7 check §2f |
| 11 | §4.0 l.51, §4.2 l.65, Table 3 l.141 (C7, 274 runs; 247 → 6 of 263) | No population note | 274 = 214 + Luna 60, so the C7 result includes the 18 unreconciled harder-variant runs (App M l.827). C17's 214 does too. The body never says so, which sits badly with "we report no result on the variant". Optional: add to footnote b "C7 (274 runs) and C17 also include these 18 runs". | MF r12, §7 glossary; App M l.827 |

Checked and within safe wording: abstract (scoped key claim, "post hoc" on 76/77 and on commissions, 0.26 "best keyless", 31/39); §4.1 ("consistent, not valid", 48/62, 36/39 vs 12/23, Holm 0.030 > 0.025); §4.2 (76 of 77, 17/26 scoped to set A, 60/77 and 35/77); §4.3 (0 vs 3 of 17 = three discordant runs, p = 0.125; J12 p = 0.11; the post hoc rule stated); Luna's 7 (0/4/6 of 7 and the script's 6/7, "support no inference"); §4.5 (6 of 10 includes the anchor; 13 of 36; exploratory labels); §5 ("rarely", "more than 16 and at most 64", Luna weaker in general); §8 (the candidate-aware sceptical judge is untested; rubric is report-level only).

---

## 3. Harder-variant numbers outside footnote b

The blueprint (§8, §9) makes footnote b the single home of the variant's numbers and App M its only description. Under the hard rule, these still carry variant-derived numbers outside footnote b:

| # | Where | Number(s) | Kind | Recommendation |
|---|---|---|---|---|
| 1 | App M l.831 | "Terra 7/8 vs 6/8"; "15 + 15 runs with 11/15 vs 11/15"; "18-run variant" | **outcome counts** | Delete the outcome counts (see §1 #3). Keep the run count if App M must describe the variant. |
| 2 | App E5 l.552-559 | bracketed 214-run values [0.002], [0.60], [53/68], [32/146], [0.12], [0.765], [84/118], [117/738]; the "214 only" null and planted slices (0.45, 0.97, 2/5, 5/209; 0.06, 0.70, 82/113, 112/529); confidence AUROC (214) 0.61 / 0.71 / 0.95 / 0.68; "adds 18 unreconciled harder-variant runs" | population including the variant | The blueprint keeps 214 secondary in E5. If the rule is strict, drop the bracketed 214 values. The slices and AUROC have no 196-run version in the sources, so either keep them, labelled as they are, or drop them. |
| 3 | App E l.561 | "(214 runs: 41 of 44 against 12 of 24)" | population including the variant | Same as #2. |
| 4 | N1 l.852-854 | J1 0.002, J2 53/68 = 0.78, J3 41/44 vs 12/24 | population including the variant | See §4: lead with 196. |
| 5 | App M l.819, l.827 | "harder variant 18"; "214 = … + harder variant 18"; "(272 with the harder variant)"; "196 = 214 less the 18" | population counts only | Acceptable as denominators. No outcome number. |

No harder-variant κ (0.10, 0.77, 0.28, 0.87), prevalence (12/18, 5/18) or interval ([−0.25, 0.58], [0.43, 1.00]) appears anywhere. Table E1, the E1 "Reading", Table E2, Figure 1 and FIGURES_V8 (l.16: "No harder-variant series is plotted") are clean.

---

## 4. 214-run values placed where the 196-run value should be primary

| # | Where | Now | Fix (196 values from `gpuplan_b_reconcile.json`) |
|---|---|---|---|
| 1 | App E Robustness l.563 (C17) | "Two replicates … over 214 runs: Cohen κ 0.47 on all slots, 0.51 on hard slots (196 runs: 0.46, 0.51)" | "over the 196 reconciled runs: hard slots 0.51, all slots 0.46 (registered 214 runs: 0.51, 0.47)" |
| 2 | App J l.697 | "Two sends on 214 runs: Cohen κ 0.51 …, 0.47 … (196 runs: 0.51, 0.46)" | Same reorder. |
| 3 | N1 l.852 J1 | "214 (196 reconciled) \| 0.002 (−0.006)" | "196 (registered 214) \| −0.006 (0.002)" |
| 4 | N1 l.853 J2 | "68 slots (62) \| 53/68 = 0.78 (48/62 = 0.77)" | "62 slots (68) \| 48/62 = 0.77 (53/68 = 0.78)" |
| 5 | N1 l.854 J3 | "214 (196) \| 41/44 vs 12/24 (36/39 vs 12/23)" | "196 (214) \| 36/39 vs 12/23 (41/44 vs 12/24)" |
| 6 | N1 l.881 C17 R2 | "132; 214 \| 0.44 (hard slots 0.39); 0.47 (hard slots 0.51)" | Lead with hard slots and 196: "132; 196 \| hard 0.39 (all 0.44); hard 0.51 (all 0.46; 214: 0.47)". MF r10: self-agreement is quoted as hard-slot 0.39. |
| 7 | L.1 l.761 (PPI, C21) | "the 214 L0 verdicts … r = 0.002"; the C21 audit curve also rests on 214 | No 196-run value exists in the sources (MF r21, r23 are 214 only). Acceptable as appendix-only, unused in the body. Optionally note "(registered 214-run population)". |

Already correct: the body (§4.1, Table 3 with 214 only in footnote b), Table E5's header row (196 primary, 214 in brackets) and App M l.827.

---

## 5. Hard rules

- **October:** none. Appendix P is gone, the N1 October row is gone, and no "[oct-check]" remains (grep for "oct" and "[oct": no hits).
- **Dates:** none after 14 Nov 2026. Dated items: "13-14 November" (L2), "14 November" (Round 3), "Nov 12", "2026-11-12T06:17Z", "Nov 3-4", "Nov 10-11". See §1 #9 for the 13 vs 13-14 precision point. The cited venues "NeurIPS 2026" and "AAAI-27" are publication venues, not run dates.
- **Anonymization:** no author names, emails, URLs, branch names or image tags. The only "@" characters are in the tool help's matrix notation.
- **Ids and cues:** no probe or episode id, no internal tag (ep…, F2-a/b/c, knob_…), no cue property name. Trap roles appear only as [main] / [decoy]. Held-out items are "held-out 1-3".
- **Placeholders:** none.

---

## 6. FIGURES_V8 and the rendered figures

- Fig 1(a): every plotted value and interval matches `gpuplan_a_intervals.json` and `gpuplan_k_k.json`. Values: set A −0.021 / 0.063 / 0.241 / 0.805 / 0.916 / 1.000; Luna 0.018 / −0.033 / 0.258 / 0.914 / 1.000 / 1.000; main 0.056 / 0.263 / 0.962; script 0.524 [0.395, 0.655] and 0.426 [0.339, 0.550]; hollow star 0.164; test-retest 0.388.
- The rendered `fig1_v8.png` shows the hollow star, the dotted link to the filled star, the "positive control" band and the 0.39 line.
- Fig 1(b): 7/17, 21/26; 3/17, 17/26; 0/17, 7/26; 0/17, 0/26. All match.
- Fig 2(a): matches `c8.json` and `c19_reorder.json`.
  - +0.861 (11/12 − 1/18) → −0.194 (9/12 − 17/18), with interval [−0.417, +0.028].
  - +0.667 (24/24 − 8/24) → +0.083.
  - +0.375 → −0.0625.
- Fig 2(b): all nine systems' counts match `L9.systems`. I recomputed all 13 reversed-pair gaps from those counts, and they match. Pairs = 36, discordant = 13, τ_b = 0.229. The robust pairs (Terra BB-64 vs Haiku open; Terra BB-64 vs Terra BB-16) match `hypotheses.H2`.
- **Error:** the Fig 2 suggested caption (l.125) says "held-out"; the correct word is "shipped" (§1 #1). The rendered panel's label "Terra − Luna trap probes, 30 runs" is consistent with "shipped".
- Naming: FIGURES calls the rule "credit any named cue" and the paper calls it "credit any named answer". This is cosmetic; pick one.

---

## 7. Verified correct (no action)

- **Body numbers against MF and data:**
  - κ −0.006, 48/62, 36/39 vs 12/23 (196); footnote b 0.002, 53/68 (214).
  - Self κ 0.39 (132); re-send κ 0.34 and 9 vs 7 of 17.
  - 31/39 vs 1/39; AUROC 0.48-0.58 (274); 247 → 6 of 263.
  - Best keyless 0.26 (main L2); placebo 0.20 vs 0.06; J11 +0.18, p 0.030 > 0.025; J12 7 → 3, p 0.11.
  - 76/77 and the isolation counts 0 (10), 1 (5), 2 (7), 5 (1), 7 (2), 8 (1); 17/26, 7/125, 60/77, 35/77.
  - Script 0/17, 0/15, 0/6 vs judge 3, 4, 5.
  - Refutation 0/17 (15 never isolated; the other two read 0.15-0.30 / ≥ 0.30 and 0.15-0.30 / never isolated), 6/15, 1/6; Luna 0/4/6 of 7 and script 6/7.
  - Unit 0.52 → 0.16, 51/87, 0/17; key 0.81 [0.56, 1.00], 0.91 [0.49, 1.00], 12/5/0 of 87, main 0.96 with 1/6.
  - Gap 0.86 → −0.19 [−0.42, +0.03]; +0.67 → +0.08; +0.375 → −0.06; 13/36; Haiku 82/87, κ −0.21; held-out 6/10 (with anchor) and 5/7.
  - Agents: 23/24 vs 6/24 (6/6 items); 5/36 vs 1/24; 11/12 vs 0/18; 20/21 (7/7, 6/7, 7/7) vs 2/17 (1/5, 1/5, 0/7); 4/48 vs 2/72; 4/18 vs 12/12; T 0.66 vs 12/12.
  - Also: 61/64; 116/116 and 12/12; 1.7×; 100/100; 87/130, 7/60; 34/256; +0.46; 87k vs 62k; 0.54; $0.08.
- **Table 1:** every cell matches `a/intervals.json`, `k.json` and `v/verifier.json`, including the new ceiling row (0, 0, 23, 0.65 [0.53, 0.75], run [0.52, 0.77], BA 0.87) and footnotes a and b (106/125, 86/125).
- **Table 2 and Table 3:** all values match, apart from the n-column point in §1 #8 and the "≤ 0.26" in §1 #7. The 6/6 items for BB-64 vs BB-8 and for Open-4 vs BB-8 were checked against Table D1.
- **Appendix lines that changed:**
  - E1 values (L0r −0.01 [−0.22, 0.17]; L1r 0.20 [0.06, 0.33]; all within-type κ).
  - E2 (`none` index and null false blame from `c6c_ladder.json`).
  - E5 196-run row (0.597, 31/134, 0.11, 79/111, 111/673).
  - F commission paragraph against `commissions.json`; diagnostics against `diagnostics.json`.
  - E "five bases above the band"; M populations 254 / 272 / 274 / 190 / 84 / 27 / 14; L2 13-14 Nov table and $1.14 + $0.045.
