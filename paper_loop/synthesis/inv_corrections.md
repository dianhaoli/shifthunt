# Corrections and open questions log (ShiftHunt paper loop, through PAPER_V7)

Read-only synthesis, 14 Nov 2026. Every fact carries a source tag (§0). Trap cues appear only as [main] and [decoy];
no probe or episode id, cue property name, person's name or email appears here. October-period material is listed
only as "excluded" (§6). "Latest results" = `gpu_results/RESULTS_FOR_PAPER_f44495b.md` plus `gpu_results/data/`.
Line numbers ("l.") refer to the cited file as it stands on disk.

---

## 0. Sources and tags

All paths are relative to `/home/user/shifthunt/paper_loop/`.

| tag | file |
|---|---|
| [V7] | `final/PAPER_V7.md` (second-pass V7; saved 22:50:43) |
| [V7d] | `final/PAPER_V7_draft1.md` (first draft; 22:39) |
| [R] | `gpu_results/RESULTS_FOR_PAPER_f44495b.md` (latest results; 22:59:24) |
| [R−] | `gpu_results/RESULTS_FOR_PAPER_84b3a82.md` (snapshot before R; 22:03) |
| [V] / [VC] / [VD] | `gpu_results/data/gpuplan_v_README.md` (22:59:24) / `gpuplan_v_commissions.json` (22:59:31) / `gpuplan_v_diagnostics.json` |
| [A] | `gpu_results/data/gpuplan_a_README.md` |
| [B] | `gpu_results/data/gpuplan_RECONCILE.md` |
| [C6b] [C6c] [C6bh] [C14] [C14b] [C14L] [K] [T] | `gpu_results/data/gpuplan_<item>_README.md` |
| [CL7] | `final/V7_CHANGELOG.md` (22:51) |
| [CHK7] | `final/V7_check_numbers.md` (checked against [R−], l.3) |
| [RV6] / [RV7] | `final/REVIEW_V6.md` / `final/REVIEW_V7.md` |
| [OA7] | `final/OUTSIDE_ADVICE_V7.md` (23:00:56; written on [V7d], header l.3) |
| [O5] | `final/V5_OUTLINE.md` (list of V4 sentences to correct, l.535 ff.) |
| [V2] [V3] [V3r1] [V3r2] [V4] [V5] [V6] [BEST] | `final/PAPER_V2.md`, `PAPER_V3.md`, `PAPER_V3_r1.md`, `PAPER_V3_r2.md`, `PAPER_V4_user.md`, `PAPER_V5.md`, `PAPER_V6.md`, `PAPER_BEST.md` |
| [REC2] | `final/RECOMMENDATION_V2.md` |
| [XR] / [XRS] / [XRref] | `exchange_rate/00_ANSWER.md` / `exchange_rate/SUMMARY_PLAIN.md` / `exchange_rate/referee.md` |
| [RM] / [LED] | `README.md` / `LEDGER.md` |
| [d5] [d5c1] [d7] | `d5/final.md`, `d5/critic_r1.md`, `d7/final.md` |
| [GREV] | `gpu_results/review/00_WHAT_REVIEWERS_SAY_NOW.md`; [GREVa] `review_agents.md`; [GREVs] `review_skeptic.md` |
| [ADD] | `gpu_plan/C6B_ADDON.md` |
| [IC] | `synthesis/inv_claims.md` (sibling synthesis; cited only where it needs correcting) |

File times are from `ls --time-style=full-iso`, all on 14 Nov.

---

## 1. The ten named corrections

### 1.1 "The proxy is worth about 36 queries"

| | |
|---|---|
| **Claimed** | "about 36 by interpolation [exploratory]" ([d7] l.20); "reaches 0.958 at about 36 queries; … 95% interval of 21 to beyond 64" ([d7] l.399); "a logistic crossing near 36 queries" ([RM] l.64); Terra "≈ 36" in the exchange-rate table ([XRS] l.28); V4: "A three-point logistic fit puts the match near 36" (quoted for deletion in [O5] item 6, l.541). V2-era body: "near 36, with an extrapolating interval" ([REC2] item 7). A sibling claim, "The SAE is worth about 50 queries", is on the dead list ([RM] l.122). |
| **Corrected by** | (a) Fragility: "11 equally defensible fits span 22-58; 28 or ≈ 133 if one Open-8 run flipped" ([XR] l.88). (b) "'Worth X queries' is not a property of the SAE": X is 11, 24, ≈ 36 or ≈ 50 depending on the blind reference ([XRS] l.10-29). (c) The four values come from a copied input with no generating script, and "the 'fits 22-58' span is not in this repo" ([B], "exchange rate range" row). (d) [O5] item 6: replace with the measured curve and move the fit to an appendix as history. |
| **Current statement** | "The blind budget matching the proxy arm lies above 16 and at most 64; we report curves, not one exchange rate" ([V7] l.101, Figure 2 caption). Identified bracket (16, 64] at run level, (8, 64] at item level; the four values are flagged and "use[d] none in the body" ([V7] App I l.687). Blind Terra: 6/24, 16/24, 24/24 at 8, 16, 64 ([B] "Terra budget curve" row). |
| **Status in V7** | Fixed. |

### 1.2 "Every agent commits all its queries in one batch"

| | |
|---|---|
| **Claimed** | "What we saw: every agent we ran committed all its queries in one batch" ([XRS] l.55). V4 Claim 3: "they commit their exact queries to the proxy's top candidates in a single batch, before any result returns" (quoted in [O5] item 10, l.545). |
| **Corrected by** | X4 log analysis: "Correction to the exchange-rate summary: not every agent commits in one batch; with the SAE, Terra and Luna both do (blind arms mostly do not), and the batch's width on the anomalous probe separates them" ([R] l.22-27). One-burst rates: Terra with SAE 40/40, BB-8 0/24, BB-16 1/24, BB-64 3/24; Luna Open-8 36/36, BB-8 14/24; Haiku main 9/15, Open-8 4/11, BB-8 1/12, BB-64 0/12; Opus 10/16; Sonnet 11/16 ([R] l.22-24). |
| **Current statement** | One-burst rates vary by agent and arm; with the proxy both GPT agents commit in one burst, and what separates them is how many texts go to the trap probe (Terra 3.9-4.0 vs 1.3-1.4 per other probe; Luna 1.9 vs 2.0) ([R] l.24-25). Held-out runs: one-burst Terra 18/21, Luna 21/21 ([V7] App H l.667). |
| **Status in V7** | Fixed (the claim is absent from the body; X4 values are in App K/M, e.g. [V7] l.827). |

### 1.3 "Audit negatives first"

| | |
|---|---|
| **Claimed** | d5 §5.3 "An audit rule for evaluators: recheck the negatives first" ([d5] l.188), with "rechecking 31% … catches 77%" ([d5] l.202); V2 contributions "grade by execution and audit negatives first" ([REC2] l.521); V4: "Evaluators should therefore audit negative verdicts first; this judge does the opposite" ([V4] l.162); it came back in V6's conclusion: "audit 'nothing found' verdicts first" ([V6] l.174). |
| **Corrected by** | C21: `none`-first catches 50% of the judge's hard-slot errors after 24% of runs (random 50%) and 80% after 67% (random 80%); the rule was suggested by J3 on the same runs, so the gain is in-sample ([V5] l.725; [V7] App L.1 l.759). Reviewers: "in-sample and weak … wins only early. Fix: exploratory; drop from contributions" ([GREV] l.51; [GREVs] l.30). [O5] items 5 and 8 delete both sentences. |
| **Current statement** | Exploratory, in-sample, appendix only ([V7] l.759). The body's practice is "grade negative verdicts against executed ground truth or a key" ([V7] l.166), not an audit order. |
| **Status in V7** | Fixed (absent from body and conclusion). |

### 1.4 "No deeper trap exists" → "deep traps already exist" → rank-6 bank traps cancelled

| | |
|---|---|
| **Claimed (1st)** | A rank-3+ item "needs a newly trained two-decoy trap" ([BEST] l.88; [V2] l.431; [V3] l.451). |
| **Claimed (2nd, replacing it)** | "Deep traps already exist": of the bank's "24 distinct trap probes, the [main] sits at proxy rank 1 on 11, rank 2 on 10 and rank 6 on 3", making a deep-trap agent run "a run-only job" ([REC2] item 9, l.527-531); "the bank holds three with the [main] at proxy rank 6, never run with agents" ([V3r1] l.213; [V3r2] l.213; [V4] l.238, l.482); "Deep traps: the bank holds 3 trap probes with the true cue at SAE rank 6" ([RM] §G row 1). |
| **Corrected by** | Step 0 of the GPU plan: "R6 cancelled at Step 0: one probe in three episodes; its held-out checker finds a non-main property at 0.186 (> the 0.15 promise); the budget-faithful correct method solves it in 0-2.5% of draws" ([C14] l.8-9; [R] l.116). [O5] item 16 corrects the V4 sentences. |
| **Current statement** | "The bank's only rank-6 trap is one probe in three episodes, and its checker is not clean … so the pre-registered rank-6 agent arm (R6) was cancelled before any run. All clean bank traps sit at rank ≤ 2" ([V7] l.439). Agents ran only at rank 2; "Only scripts ran at deeper ranks, and the one that holds up there is told the trap rank" ([V7] l.116). The first claim (no usable deeper trap) was thus closer to right than the second. |
| **Status in V7** | Fixed. |

### 1.5 "Wrong cues leave evidence [in the log]"

| | |
|---|---|
| **Claimed** | Title of [V7d] l.1: "Wrong Cues Leave Evidence, Missed Cues Do Not". [R−] l.170-171: "The log is enough to reject commissions"; its sentence for the paper: "A scripted reader of the agent's exact-query log rejects every wrong named cue the judge credits, so the judge leaves evidence unused" ([R−] l.178-180). Still in [V7]: abstract "Wrong named cues leave evidence in the agent's query log" (l.9); §1 "Commissions leave evidence in the log" (l.23); §4 heading "Commissions: the evidence is in the log" (l.67); §10 "A fixed script reading that log rejects every such cue … so it underuses evidence that is present" (l.166); App F "the log is enough to reject every wrong named cue" (l.611); [CL7] l.51. |
| **Corrected by** | Post hoc commission count (`keyless_verifier_commissions.py`; wording rule fixed before computing: "most" = at least 9 of 17): the ceiling rule V3 decides **0 of set A's 17** wrong named cues wrong; 15 of the 17 claimed cues were never isolated in a clean test; the other 2 read 0.20-0.56; Luna 6 of 15; main study 1 of 6; two independent read-only rechecks also find 0 of 17 and reproduce Luna's 6 ([V] l.59-65; [VC] `set_A.decided_wrong_V3` "0/17", `by_reason` "claimed property never isolated": 15; [R] l.170-175). |
| **Current statement** | "Wrong named cues lack evidence; they are rarely refuted by it … V1's 0 credited commissions is therefore absence of support, not refutation" ([V] l.59-63). Luna is the exception: 6 of its 7 [decoy] answers submitted after its own refuting test are decided wrong from its log; the 7th reads in the 0.15-0.30 gap ([R] l.176-177; [VC] `c8_refuted_then_submitted_decided_wrong` "6/7"). The pre-agreed rule calls for the retitle "wrong cues lack evidence; missed cues look like right ones" ([R] l.188-189; [VC] `wording`). |
| **Status in V7** | **Not fixed.** The count postdates V7 ([V] and [VC] saved 22:59, [V7] 22:50). V7's title no longer says "leave evidence" ([V7] l.1), but [CL7] l.41-45 gives other reasons for the new title; the abstract, §1, §4 heading, §10 and App F still carry the refuted framing. |

### 1.6 Reference policies called "bounds"

| | |
|---|---|
| **Claimed** | "Following the proxy two deep is the best reference policy here" ([V4] l.105); "Present them as reference bounds, not as measurements of skill" ([XRS] l.95); "the references bound skill" ([XR] l.193). [O5] item 12 (l.547): "'[priv] … reference policies' written as bounds, and XR's 'reference bounds'". |
| **Corrected by** | X1 measured policies in the environment plus Open-4: at B = 4 Terra passes 12/12 while no rank-only script exceeds 0.50, so they cannot be upper bounds ([R] l.9-16). [O5] item 12: rename them "rank-only reference policies"; say Terra beats them at B = 4. |
| **Current statement** | "These policies use only the ranking, so they are references, not bounds: at B = 4 Terra (12/12) exceeds all of them (at most 0.50)" ([V7] App I l.683; also [V5] l.73, l.650). The band-plus-closeness script's 0.66 at B = 4 does not break §5's "no script using only the ranking exceeds 0.50", because it uses proxy readings ([CHK7] §2e). Separate, legitimate bounds (V4's "per-agent Block 1 bounds", −0.21 to +0.38) were superseded by the exact C19 contrasts (+0.67 → +0.08) and kept only as history ([V5] l.600). |
| **Status in V7** | Fixed ("None found", [CHK7] §2e). |

### 1.7 "A trivial rule beats the judge" and its design caveat

| | |
|---|---|
| **Claimed** | V6 contributions: κ "at most 0.26 on every run set, below a rule that credits every named answer" ([V6] l.23); V6 conclusion: the judge "never beats a trivial rule" ([V6] l.174); V6's Figure 1 title made the comparison ([CL7] l.67). [OA7] ("A trivial rule beats the judge … κ 0.67 on hard probes. Present it with its design caveat"). |
| **Corrected by** | Reviewers: "'Below a trivial rule' comes from the design: every hard probe has a cue" ([RV6] l.43). Item A: the rule's all-slot κ is 0.22 on set A (0.26 Luna, 0.17 main study, 0.28 harder variant), "below the transcript level on every set, because it rejects every correct `none` on a null probe. It is a hard-slot reference only" ([R] l.199-201; [A] table). Within either answer type the rule's κ is 0 by construction ([A] "Within-answer-type κ"). |
| **Current statement** | Hard-probe κ 0.67, 0.37, 0.75 on set A, Luna, main study; 0.22 on all of set A's probes; "a reference, not a grader" ([V7] l.65 caption; Table 1 footnote a, l.83). On all slots of the three main sets the rule is 0.17-0.26, below the transcript-level judge (0.28-0.58) ([V7] l.513; [CHK7] #7). Remaining objection: hard-probe κ still favours any reader that rejects `none`; over all probes the script (0.25) trails the transcript judge (0.32) ([RV7] issue 3; [A] all-slot column). |
| **Status in V7** | Fixed as a demotion (caption and footnote); no body paragraph uses the rule as a finding. |

### 1.8 L2 (full transcript) "improves" the judge

| | |
|---|---|
| **Claimed** | The analysis driver `judge_ladder2.py analyse` labels J11 "confirmed" from the uncorrected one-sided bound ([C6b] l.16-19; [R] l.121-123); the C6b README's reading: "The full transcript helps the judge more than the exact-query log did" ([C6b] "Reading"). |
| **Corrected by** | Registered Holm step (`c6b_holm.py`, same seed and draws): J11 Δκ +0.18, one-sided lower bound +0.02, bootstrap p 0.030 > Holm threshold 0.025, **not confirmed**; J12 wrong-cue credit 7/17 → 3/17, McNemar p = 0.11, **not confirmed** ([C6b] hypothesis table; [R] l.79-81). Adjacent keyless levels overlap on every set ([A] "Reading"). Main study: wrong-cue credit rises 3/6 → 5/6 with the transcript ([C6b]; [B]). |
| **Current statement** | Descriptively κ 0.06 → 0.24 on set A; the gain is "not confirmed" ([V7] l.61, Table 3 l.128). "More access does not reliably help" ([V7] l.67). |
| **Status in V7** | Fixed in §4 and Table 3. Residue: §10's "so it underuses evidence that is present" ([V7] l.166) leans on the unconfirmed 7 → 3 of 17 drop (see §4 #5). |

### 1.9 The harder variant is unreconciled

| | |
|---|---|
| **Claimed** | V6's registered J1/J2 population of 214 runs used as headline, including 18 harder-variant runs ([RV6] l.47: "includes 18 unreconciled harder-variant runs"). |
| **Corrected by** | Item B: on the 196 reconciled runs κ −0.006 (214: 0.002), failures credited 48/62 (53/68), wrong `none` 36/39 (41/44), wrong cue 12/23 (12/24); "No label changes; the 196-run values can be primary" ([R] l.207-209). The variant's outcomes exist in two forms, Terra 7/8 vs 6/8 and "15 + 15 runs with 11/15 vs 11/15", which "describe different subsets that we have not reconciled" ([V7] App M l.829; [LED] l.362). Its registered prediction "≥ 10 points lower" is "not supported as registered" ([V7] l.849). [OA7]: "Drop the harder variant entirely". |
| **Current statement** | Body uses 196-run values, 214 in a footnote ([V7] l.59, Table 3 footnote b l.142). The variant remains as a judge set (report κ 0.10 → report + key 0.77; the key step does not clear its item intervals, [−0.25, 0.58] vs [0.43, 1.00]) ([A]). |
| **Status in V7** | Partly fixed: 196 primary, but the variant was deliberately kept ([CL7] l.157, "Not adopted"). It appears in §3 l.47, §4 l.61, Table 3 l.130 and footnote b, App C l.425, App E l.508/540/567, M l.829, N l.849 ([V7]). [RV7] issue 13: "called excluded but enters Tables 3 and E1". |

### 1.10 Dates

| | |
|---|---|
| **Claimed** | "13-17 Nov 2026" ([R] l.1, title); "Table L2. Spend of the final round (13-17 November)" ([V7] l.780); "four-query arm (Nov 13-17)" and "held-out traps (Nov 13-17)" ([V7] l.815-816); "the final round on Nov 13-17" ([V7] App P l.921). |
| **Corrected by** | [OA7] l.13: "Some dates are later than today … Replace them with the actual run dates." Item timestamps: C6b 13 Nov 18:20-20:25Z ([C6b] l.10); C6c 13 Nov 19:25-20:18Z ([C6c] l.11); C6b-H 13 Nov 19:24-19:50Z ([C6bh] l.9); held-out 3 Terra 13 Nov 19:18-20:44Z, Luna 20:44-21:35Z ([C14b]); C14L 13 Nov 21:35-22:10Z ([C14L] l.10); C14 ledger repair 13 Nov 08:40Z and stage 2 queued 13 Nov 14:28Z ([C14]); V 14 Nov 20:38-21:01Z ([V] l.6-7); T 14 Nov 20:46-20:47Z ([T] l.6); K 14 Nov 21:06-21:34Z ([K] l.4). |
| **Current statement** | Every dated final-round item ran on 13-14 Nov; the files were written on 14 Nov. |
| **Status in V7** | **Not fixed** (all four V7 locations unchanged). A related source-side slip: [ADD] l.55 heads the guard raise "author, 14 Nov", while the C6b calls it governed are stamped 13 Nov ([C6b] l.10, l.123 of [R]). |

---

## 2. Further corrections, weakenings and retractions

| # | claim (where) | corrected by | current statement |
|---|---|---|---|
| 1 | Test-retest "κ 0.44" and drawn as Figure 1's noise line ([R] l.74; V6 Figure 1, per [RV6] l.47) | It is all-slot; hard-slot is 0.39 (three sends, 132 runs) or 0.34 (two sends, 130); 0.39 is on 132 runs, not 214 ([A] "Judge noise"; [B] test-retest row) | Hard-slot Fleiss κ 0.39 on 132 runs ([V7] l.59, l.569) |
| 2 | Report-judge κ 0.002, 53/68 as the headline ([V6]) | 196 reconciled runs: −0.006, 48/62 ([R] l.207-209) | 196 primary, 214 in footnote ([V7] l.59, l.142) |
| 3 | Commission baseline 9 vs 7 of 17 looked contradictory ([RV6] l.47) | Different sends: L0 (12 Nov) 9/17, L0r (re-sent, registered J6 baseline) 7/17 ([R] l.211-213) | Both right; footnote c ([V7] l.142) |
| 4 | Set A 130 vs 132 ([RV6] l.47) | 2 Haiku-judge calls returned http_503 ([R] l.210) | 132 runs, 130 in the ladder ([V7] l.47) |
| 5 | [decoy] reads "about 1.8×" the [main] through the proxy ([B] row "[decoy] vs [main]") | 0.362 vs 0.212 ([B]) | "about 1.7 times" ([V7] l.39, l.827) |
| 6 | "Fits 22-58" span and "45 registered entries" (α ≈ 0.0011) | No data script in the repository ([B] exchange-rate and §6 rows) | Not in the V7 body; flagged in App M "Script map" ([V7] l.833) |
| 7 | Abstract model: calibrated Bayes reaches 1.0 at B = 5; "an ideal one reaches 100% with 5 queries" ([XRS] l.33) | Measured in the environment: 0.80 (bank prior) / 0.93 (trap-rank prior) at B = 5 ([R] l.13-14) | Table I1 ([V7] l.673-681) |
| 8 | "Luna trap 1/18 vs 2/12" | Slot counts; trap NAME is 1/18 vs 1/12 ([XRS] l.76; [XRref] l.175-179) | Table 2 uses 1/18 for Luna's shipped trap NAME ([V7] Table 2) |
| 9 | Terra "3.9 queries on the trap versus 1.7 on each other probe" ([XRS] l.46) | X4: 3.9-4.0 vs 1.3-1.4 ([R] l.24; [O5] item 18) | [V7] l.827 |
| 10 | C14 H2 labelled "partial" by the analysis code | Fall-through label; the result is outside every pre-registered band (gap 0.63 clears ≥ 0.50, but Luna 3/10 misses ≤ 2/10, and partial covers only 0.20-0.49) ([R] l.47-50) | "outside every pre-set band" ([V7] Table 3; App H l.667) |
| 11 | "Luna never did on a trap" / "the smaller model does not widen" ([O5] item 11) | Held-out iso(main) 3/10 ([O5] item 11; [R] l.47) | "rarely" ([V7] l.103) |
| 12 | V6 thesis "the judge fails for lack of ground truth, which the agent's materials do not supply" ([RV6] l.34) | Called an untested causal claim by all three V6 reviewers ([RV6] l.34) | Replaced by the two-part measured claim ([CL7] l.47-53); now itself weakened on the commission side (§1.5) |
| 13 | V5: a keyed judge was untested | Contradicted by the later key level ([IC] row 16, citing `final_debate/00_FINAL_FEEDBACK.md`) | L3 and K levels measured ([V7] Table 1) |
| 14 | [V7d]: "Given the answer key, the judge credits no failure" | Main study, transcript + key, credits 1 of 6 commissions ([CHK7] #1) | Scoped to set A and Luna ([V7] l.9, l.87) |
| 15 | [V7d]: the judge "credits most" of the 77 wrong `none` | With the transcript it credits 35 of 77; "most" holds on set A (17/26) or at report level (60/77) ([CHK7] #2) | Scoped to set A ([V7] l.9, l.23) |
| 16 | [V7d]: the agent "never tested every candidate" | 76 of 77; the 77th had all 8 isolated, one reading in the gap ([CHK7] #3; [V] l.66-69) | "76 of 77" / "almost never" ([V7] l.9, l.166) |
| 17 | Held-out judge credit "6 of 10" read as held-out only | The 10 come from 27 runs incl. the 3-run shipped anchor ([CHK7] #4; [R] l.90-91) | [V7] l.154 |
| 18 | Figure 2 title "16-64" | Blind 16 is 16/24, below the proxy arm ([CHK7] #5) | "about as often as … blind at 64" ([V7] l.101) |
| 19 | "False credit unchanged" (L0r → L1) | 27 → 28 of 43 ([CHK7] #6) | "about unchanged" ([V7] l.556) |
| 20 | Rule all-slot "0.17-0.28, below the transcript level" | 0.28 is the harder variant, which has no transcript level ([CHK7] #7) | 0.17-0.26 on main sets ([V7] l.513); the slip remains in [A] "Reading" |
| 21 | "No keyless level exceeds 0.26" | Main-study L2 is 0.263 ([CHK7] #8) | "highest keyless κ on any set is 0.26" ([V7] l.61) |
| 22 | Wrong-signed BB-16 − BB-64 "at every Terra-judge level" | Values exist only for L0, L0r, L1, L1r ([CHK7] #9) | "every report- and log-level Terra judge" ([V7] l.759) |
| 23 | "Only because it rejects right ones"; "because agents leave no clean test"; "An omission is a test that was not run"; leniency "is a prior"; "only scripts show depth (Figure 2b)" ([CHK7] §2a, §2d) | Not measured, or 11 of 23 only, or exploratory over all failures, or the wrong figure ([CHK7] §2a.1-4, §2d) | All rewritten ([CL7] §2 "overclaims"; [V7] l.59, l.69, l.95, l.116) |
| 24 | Token-cap gain "+0.42" vs "+0.46" | Different caps: 62,000 gives +0.42 because it excludes a 62,004-token run; the inclusive median 62,005.5 gives +0.46 ([LED] l.380, l.523) | +0.46 ([V7] l.158; App L.2 l.776) |
| 25 | d5: "a named answer is a tested answer" | Untested ordinary probes pass 39/42 ([d5c1] l.11, l.57) | Not used in later versions |
| 26 | "Verification Without Search" title (BEST-V4) | Terra tests the runner-up 11/12 ([RM] §E) | Retired from V5 on |
| 27 | Dead claims ([RM] §F): "Agents only test the proxy's top choice"; pooled no-SAE allocation curve; "Knowing the SAE can be wrong doesn't help"; "Trap unreliability is visible before any query"; "Agents over-trust the proxy"; any model leaderboard from pass rates | Listed as died ([RM] l.117-126) | Absent from V7 |
| 28 | Luna kept a [decoy] after refuting it, resting on a README count | Committed post hoc flag script ([B] "Luna refuted-then-submitted" row) | 7 runs, post hoc ([V7] l.67, l.729) |
| 29 | [IC] l.32: the V7 review package holds D1-D4 only | `final/reviews_v7/` holds D1-D7 and dev R1-R3 (all 23:07), summarised in [RV7] l.32-40 | Nine reviewers, all lean accept ([RV7] l.42-46) |

---

## 3. Open questions

### 3.1 Not answerable from the existing data (need new runs or new designs)

| # | question | why the data cannot answer it | source |
|---|---|---|---|
| 1 | Do agents widen beyond the proxy's rank 2? | Every agent-run trap has the [main] at rank 2; R6 was cancelled; only scripts ran at deeper ranks | [V7] l.116, l.439; [C14] l.8 |
| 2 | What triggers Terra's widening (the contract band, closeness of readings, or plain search)? | The band-plus-closeness script does not reproduce Terra; GPT reasoning is hidden in transcripts | [V7] §5 "whether Terra uses it otherwise, or simply searches, we cannot say"; [V7] §3 (GPT hides reasoning); [T] |
| 3 | Is widening causal for success? | The forced-allocation arm was never run (needs an image rebuild) | [RM] §G row 3; [V7] l.158 ("Widening is observational") |
| 4 | Would a candidate-aware sceptical judge at log or transcript level, or a judge with its own exact-query budget, decide omissions? | Untested; C7's sceptical rubric ran only at report level and only moved the threshold | [V7] l.155; [V7] l.569; [RV7] issue 7 |
| 5 | Do the ladder results hold for other judge families? | Only Terra (full ladder) and Haiku (L0-L2, fails the other way); the optional Sonnet/Opus transcript run was not done | [V7] l.89, l.155; [OA7] risks table |
| 6 | Does majority voting change the keyless picture? | Never run | [RV7] issue 5 ("N: majority vote") |
| 7 | Do judge results hold beyond the six shared items? | The ladder uses one item set read three times; held-out traps were judged only at report level | [V7] l.154 |
| 8 | Do results transfer to open candidate sets and real audits? | One closed-set environment with a numeric contract | [V7] l.157 |
| 9 | Was the 77th wrong `none` decidable? | A candidate read in the 0.15-0.30 gap, so the log can neither confirm nor refute it | [V] l.66-69 |
| 10 | How much of the Terra-Luna gap is capability? | Luna is weaker in general (two-part 4/18 vs 12/12); the capability adjustment is post hoc arithmetic | [V7] l.103; [V7] l.729 |
| 11 | Can GPT and Claude agents be compared? | Tokens are not matched and the harnesses count them differently | [V7] l.51 |
| 12 | Did the harder variant lower pass rates as registered? | Two unreconciled record forms | [V7] l.829, l.849 |
| 13 | Are the exchange-rate values 11 / 24 / ≈ 36 / ≈ 50 and the 22-58 span reproducible? | Copied input with no generating script; span not in the repository | [B]; [V7] l.687, l.833 |
| 14 | How often do natural SAE failures produce the rank-2 structure? | Not measured | [V4] l.238 |
| 15 | Does the judge "underuse evidence" on set A commissions? | On set A the log refutes none of the 17 (0/17 decided wrong, 15 never isolated), so there is almost no refuting evidence to underuse; only Luna's 6 decided-wrong answers allow the test | [V] l.59-65; [VC] |
| 16 | How much did the 34 of 256 main-study slots with a lost text affect the script? | The logits of those texts were not recovered | [V] l.12-13 |

### 3.2 Answerable from existing data but not yet computed or not yet in V7

| # | analysis | status | source |
|---|---|---|---|
| 1 | Refuted-vs-unsupported count for the 17 / 15 / 6 commissions | Computed post hoc after V7; not in V7 | [VC]; [V] l.59-65 |
| 2 | Script-decided Luna [decoy] answers (6 of 7) | Computed; not in V7 | [R] l.176-177 |
| 3 | Paired item-level tests between ladder levels; per-item counts | Requested; not done | [RV7] issue 4, to-do 3 |
| 4 | Design-neutral script-vs-judge table (agent-visible unit, within answer type, all probes, credit at matched blame) | Partly available ([A] within-type and all-slot κ; [V] agent-visible unit); not assembled | [RV7] issues 1-3, to-do 2 |
| 5 | Re-send noise beside each ladder step (e.g. 9 vs 7 credits on identical sends) | Not shown per step | [RV7] issue 5 |
| 6 | Upper bound on the PPI effective-sample gain (r = 0.002, interval roughly ±0.13) | Not reported | `final/reviews_v7/review_dev_R1.md` l.125 |

---

## 4. Remaining inconsistencies

### 4.1 PAPER_V7 vs the latest results

[CHK7] found "no wrong digit in a table" but checked against [R−] ([CHK7] l.3, l.5). [R] differs from [R−] only in the V commission paragraph (diff of the two files: l.170-189 of [R]). So the residue is:

| # | V7 location | V7 says | latest says | source |
|---|---|---|---|---|
| 1 | abstract l.9; §1 l.23; §4 heading l.67; §10 l.166; App F l.611; [CL7] l.51 | wrong named cues "leave evidence in the agent's query log"; the script "rejects every such cue"; "the log is enough to reject every wrong named cue" | V3 decides 0 of 17 wrong on set A (15 never isolated; other 2 read 0.20-0.56); Luna 6 of 15; main 1 of 6: absence of support, not refutation; retitle called for | [V] l.59-65; [VC]; [R] l.169-189 |
| 2 | §4 l.67 | Luna's 7 refuted-then-submitted [decoy] answers: judge rejects 0 / 4 / 6 of 7 | Also: the script decides 6 of the 7 wrong from Luna's log (the 7th reads in the gap) | [R] l.176-177; [VC] |
| 3 | App L.2 l.780; App M l.815-816; App P l.921 | "13-17 November" / "Nov 13-17" | Timestamps 13-14 Nov (§1.10) | [C6b] l.10; [C14b]; [C14L] l.10; [V] l.6-7; [T] l.6; [K] l.4 |
| 4 | §8 l.155 | a judge "told to withhold credit from untested `none` answers, is untested" | C7's sceptical-negatives rubric was run at report level: threshold-only (Terra credits correct `none` 247/263 → 6/263; ΔAUROC −0.10) | [R] l.107-110; [V7] l.569; [OA7] "Fix a contradiction" |
| 5 | §10 l.166 | the judge "underuses evidence that is present" | Rests on 7 → 3 of 17 (J12 not confirmed, p = 0.11), on a main study that moves 3 → 5 of 6, and on a set A log that refutes none of the 17 | [C6b]; [V7] l.128; [V] l.59-63 |
| 6 | §3 l.47 | the harder variant "appears once in §4" | It also appears in Table 3 (l.130, footnote b l.142) and App C, E, M, N | [V7]; [RV7] issue 13 |
| 7 | abstract l.9; Figure 1 caption l.65 | a script reading the log "without a key"; stars drawn without unit flag | The script uses a grader-side per-probe scale; in the agent-visible unit V1 κ falls 0.52 → 0.16 and false blame rises to 51/87 | [V] l.40-42; [V7] l.53 (disclosed in §3); [RV7] issue 1 |
| 8 | §9 l.162 | "$1.14 for the report-and-key calls" | $1.14 + $0.045 dry run | [K]; [R] l.238; [V7] l.801 (minor; [CHK7] §2f calls it fine for the body) |

### 4.2 Residue inside the source files (V7 already uses the corrected value)

| # | file and location | says | correct value | source |
|---|---|---|---|---|
| 1 | [R] l.74 (C6) and l.111-112 (C17) | test-retest κ 0.44; "L0 vs R2 Cohen κ 0.47 on 214 runs" | All-slot values; hard-slot 0.39 (three sends, 132 runs), 0.34 (two sends, 130), 0.51 (two sends, 214) | [R] l.203-204; [A]; [B] |
| 2 | [R] l.1 | title "13-17 Nov 2026" | 13-14 Nov | §1.10 |
| 3 | [R] l.84-87 (C6c) | "L0-L2 fail for want of it, which no amount of the agent's own material supplies" | The causal form [RV6] l.34 called untested; [V] l.73-76 restates it in a two-part form | [RV6]; [V] |
| 4 | [A] "Reading" | rule all-slot "0.17-0.28 … below the transcript-level judge (0.28-0.58)" | 0.17-0.26 on the three main sets; the harder variant has no transcript level | [CHK7] #7 |
| 5 | [C6bh] vs [R] l.150 | C6b-H spend $3.70 | $4.17 including a 5-call dry run | [C6bh]; [R] spend table |
| 6 | [ADD] l.55 | guard raise "author, 14 Nov" | The C6b calls ran 13 Nov | [C6b] l.10 |
| 7 | [GREVa] l.37 | `none`-first audit "80% takes 67%, the same as random" | A random order needs, in expectation, 80% of runs for 80% | [V5] l.725; [GREVs] l.30 |

---

## 5. OUTSIDE_ADVICE_V7 vs PAPER_V7 (second pass)

Timing: [OA7] was written on [V7d] ([OA7] l.1-3). [V7] was saved at 22:50:43, the advice file at 23:00:56, and [CL7] lists only fixes from `V7_check_numbers.md` and `V7_check_coldread.md` ([CL7] §2-3). So none of V7's changes respond to the advice file directly; where a point is fixed, another check caused it.

| # | advice point ([OA7]) | status in [V7] | evidence |
|---|---|---|---|
| 0 | Header: the post hoc count "forces a retitle" | **Partly**: the title changed from "Wrong Cues Leave Evidence…" to "What an LLM Judge Can and Cannot Certify…", for other stated reasons; abstract, §1, §4 heading, §10, App F keep the refuted framing | [V7d] l.1; [V7] l.1, l.9, l.23, l.67, l.166, l.611; [CL7] l.41-45 |
| 1 | Ask whether the appendix counts toward 8 pages; else move it to a supplementary PDF | **Not addressed in the text**: the appendix is still inline (l.207-927; `wc -w` over l.211-927 gives 14,669 in this check; the advice's "about 12,800" uses an unstated count). Body 4,799 / 4,762 words | [V7]; [CL7] l.5-8 |
| 2 | Dates "13-17 November" in Table L2, App M, App P | **Not fixed** | [V7] l.780, l.815-816, l.921 |
| 3 | Delete Appendix P | **Not fixed** (App P and the N1 [oct-check] row remain) | [V7] l.919, l.891 |
| 4 | Drop the harder variant; 196 everywhere, 214 in one footnote | **Partly**: 196 primary and 214 in footnote b; the variant itself kept by decision | [V7] l.59, l.142; [CL7] l.157 |
| 5a | "Obviously" defence: `none` credit is a prior (31/39 vs 1/39) | **Present** (already in [V7d]) | [V7] l.59; [V7d] l.51 |
| 5b | AUROC 0.48-0.58 "currently in Appendix E; move it to the body" | **Present in body** (already in [V7d] body; the advice's premise was out of date) | [V7] l.85, l.132; [V7d] l.75, l.126 |
| 5c | No keyless level exceeds κ 0.26 | **Present**, reworded "highest … is 0.26" | [V7] l.61, l.65; [CHK7] #8 |
| 5d | Trivial rule with its design caveat | **Partly**: caveat given (every hard probe has a cue; 0.22 all-slot), but only in the Figure 1 caption and Table 1 footnote | [V7] l.65, l.83 |
| 5e | Errors change conclusions (+0.86 → −0.19; 13 of 36; PPI 0) "belongs in the abstract" | **Not fixed**: in §4 only | [V7] l.89; abstract l.9 |
| 5f | Test-retest sentence: κ 0.39 with itself, about 0 with the grade, "so majority-voting cannot rescue validity" | **Partly**: the contrast is the §4 opening (0.39 vs −0.02 / −0.006); no voting sentence | [V7] l.59 |
| 5g | Pull 5a-5f into one paragraph near the top of §4 | **Not done**: spread over four §4 paragraphs | [V7] l.59, l.61, l.85, l.89 |
| 5h | Fix the Limitations contradiction (sceptical judge "untested" vs C7) | **Not fixed** | [V7] l.155 vs l.569 |
| 6 | Script unit: κ 0.52 → 0.16; commission claim unit-robust, κ comparison not | **Fixed** | [V7] l.53, l.69; [CL7] §3 item 16/20 |
| 7 | Lead with the asymmetry against omissions (17/26), not the modest 3/17 | **Not fixed**: abstract and §1 lead with 0 vs 3 of 17 | [V7] l.9, l.23 |
| 8 | §5 short and secondary; mention held-out Terra 20/21 once in the intro as the answer to "the items were seen" | **Partly**: contribution (3) gives 20 of 21 but not as that answer; §5 is about 770 words, and reviewers still call it a second paper | [V7] l.28; [CL7] section table; [RV7] issue 9 |
| 9 | Cut project spend totals; keep per-call judge cost | **Not fixed**: $101.45, $5.27, $1.14 still in §9; $0.08 per call kept | [V7] l.162 |
| 10 | Rank-6 cancellation: leave it | **Kept, as advised** | [V7] l.116, l.439, l.890 |
| 11 | Risks: six items; one judge family; density | Six items conceded; one family scoped; no second-family run; clarity still 3 | [V7] l.25, l.154-155; [RV7] §1 |

Fixed: 2 (points 6 and 10), plus the title half of 0. Partly fixed: 0, 4, 5d, 5f, 8. Already present before the advice: 5a, 5b, 5c. Not fixed: 1, 2, 3, 5e, 5g, 5h, 7, 9.

---

## 6. Excluded (October-period material)

Listed only as excluded. No number from these items is used anywhere in this file.

- V7 Appendix P, "Provenance and October-period material [oct-check]" ([V7] l.919-927): **excluded**.
- The earlier held-out allocation tests R1 and R4 and their N1 row ([V7] l.891): **excluded**.
- The earlier held-out trap runs, their transcript coding of contract-gap reasoning, and the [B] row that maps it: **excluded**.
- The texts-on-trap pass/fail contrast on the dead-claims list ([RM] §F): **excluded**.
- [OA7]'s recommendation to delete App P is recorded in §5 as a process point only.
