# RECONCILE: every number in the paper body (PAPER_V6 §§1-6, 9), its script, file and population

Round 3, item B4. Paths are relative to `results/blackbox_1112/` (`RB`) unless they start with `scripts/`. "Set A" is
130 runs in the ladder and 132 in the report-level study (`gpuplan/b/reconcile.json` `set_A`: 2 runs dropped for a
Haiku judge call that returned http_503). Numbers marked **fix** differ from what the draft says.

## Judge (§§1, 4, Table 1, Table 3)

| body number | value | file : field | script | population |
|---|---|---|---|---|
| wrong `none` vs wrong named | 18.7% (23/123) vs 2.5% (7/277), 400 verdicts | `gpuplan/b/body_numbers.json` `none_vs_named_error` (from `followup/failure_modes/failure_modes.json`) | `scripts/body_numbers.py` (`scripts/followup_failure_modes.py`) | 100 proxy runs at 8 (main 64 + Open-8 36) |
| wrong `none` credited | 41/44 (214 runs); **36/39 on the 196 reconciled runs** | `judge/judge.json` `J3_false_credit_by_error`; `gpuplan/b/reconcile.json` `report_judge` | `scripts/judge_vs_grade.py analyse`; `scripts/reconcile.py` | 214 = main 64 + set A 132 + harder 18; 196 without the harder variant |
| report-level κ; failures credited | 0.002, 53/68 (214); **−0.006, 48/62 (196)** | same | same | same |
| test-retest, hard probe | Fleiss 0.39 is on **set A's 132 runs** (three replicates), not 214; two replicates on 214: hard-slot Cohen 0.51, all-slot 0.47 (196: 0.51, 0.46) | `gpuplan/c17/c17.json`; `gpuplan/b/reconcile.json` `c17_test_retest` | `scripts/judge_panel.py analyse`; `scripts/reconcile.py` | **fix**: "214 runs" → "132 runs" for 0.39 |
| Figure 1 dotted line | all-slot 0.44 (Fleiss, 132 runs) is drawn; the figure plots hard-slot κ, so **the hard-slot 0.39** belongs there | `gpuplan/a/intervals.json` `judge_noise` | `scripts/ladder_intervals.py` | set A 132 |
| ladder κ per set and level | set A −0.02 / 0.06 / 0.24 / 0.92, 1.00; Luna 0.02 / −0.03 / 0.26 / 1.00; main 0.06 / 0.26 / 0.96; harder 0.10 / 0.77 | `gpuplan/c6c/ladder.json`; intervals in `gpuplan/a/intervals.json` | `scripts/ladder_table.py`; `scripts/ladder_intervals.py` | 130 / 60 / 64 / 18 |
| answer-type rule | 0.67 / 0.37 / 0.75 / 0.87 | same | same | same |
| placebo log | 0.20 vs 0.06 | `gpuplan/c6/c6.json` | `scripts/judge_ladder.py analyse` | set A 130 |
| transcript gain, Holm | +0.18, lower bound +0.02, p = 0.030 > 0.025 | `gpuplan/c6b/c6b_holm.json` | `scripts/c6b_holm.py` | set A 130 |
| Table 1 rows (omissions / commissions / passes blamed) | report 23 / 9 / 24; log 21 / 7 / 25; transcript 17 / 3 / 25; key 0 / 0 / 0 | `gpuplan/a/intervals.json` per rung; `gpuplan/b/reconcile.json` `credit_baselines` | `scripts/ladder_intervals.py` | set A 130 |
| Table 3 "7 → 7 of 17" | the registered J6 baseline is **L0r** (re-sent report, 13 Nov): 7/17; the original L0 (12 Nov) credited 9/17. Table 1 uses L0, Table 3 L0r: both right, different rungs | same | same | set A 130 |
| omissions with transcript | 17 of 20, 10 of 14, 8 of 13 | `gpuplan/c6b/c6b.json` | `scripts/judge_ladder2.py analyse` | 130 / 60 / 64 |
| Luna, commissions and omissions | omissions 24 → 10 of 38; commissions 11 → 4 of 15; main commissions 3 → 5 of 6 | `gpuplan/c6b/c6b.json` | same | 60 / 64 |
| Luna's refuted [decoy] answers rejected | 0 / 4 / 6 of 7 | `gpuplan/c6b/c6b.json` `luna.J13_refuted_then_submitted`; the 7 from `gpuplan/c8/flags.json` `refuted_then_submitted` | `scripts/judge_ladder2.py`; `scripts/luna_decoy_flag.py` | Luna Open-8 36 |
| unsupported `none` vs true cue credited | 31/39 vs 1/39 | `gpuplan/c12/c12.json` | `scripts/judge_cheaters.py` | scripted answers, shipped ×2 + 27 bank |
| `none` AUROC across judges | 0.48-0.58 | `gpuplan/c7/c7.json` | `scripts/judge_panel.py analyse` | 274 runs |
| Haiku judge | 82/87 blamed, κ −0.21 | `gpuplan/c6bh/c6bh.json` | `scripts/c6bh_analysis.py` | set A 130 |
| SAE view hidden | 0.35 → 0.29; 0.26 → 0.18 | `gpuplan/c6b/c6b.json` `open_arm_only`, `main_study` | `scripts/judge_ladder2.py` | set A open arm 36; main 64 |
| judged Terra-Luna gap | −0.19 [−0.42, +0.03] vs 0.86 | `gpuplan/c8/c8.json` | `scripts/judge_luna_oos.py` | 84 runs |
| held-out judge | 6/10; 5/7 | `gpuplan/c14/judge.json`; `gpuplan/c14b/judge.json` | `scripts/c14_analysis.py`; `scripts/c14x_analysis.py judge-analyse` | 27; 14 |
| keyless verifier | see `gpuplan/v/` | `gpuplan/v/verifier.json` | `scripts/keyless_verifier.py` | 130 / 60 / 64 |

## Task and agents (§§2, 3, 5, Table 2)

| body number | value | file : field | script | population |
|---|---|---|---|---|
| runs that used all 8 exact queries | 61/64 | `gpuplan/b/body_numbers.json` `main_pq_used_all` | `scripts/body_numbers.py` | main study 64 |
| proxy top candidate = true cue on ordinary probes | 12/12 shipped, 116/116 bank (97 bank episodes) | `exp_c/exp_c.json` | `scripts/sae_view_stats.py` | offline scans |
| [decoy] vs [main] through the proxy | mean 0.362 vs 0.212 = **1.7×** (draft says 1.8) | `exp_c/exp_c.json` `trap.shipped_six.fixed.ratio_profile` | `scripts/sae_view_stats.py` | 3 shipped traps; **fix** "about 1.8" → "about 1.7" |
| regrading, cheaters, attribution answer | 100/100; 6 cheaters score 0; 1 of 3 traps | `followup/misc/latent_regrade.json`; `scripted_cheaters.json`; `followup/misc/README.md` | `scripts/latent_regrade.py`; `scripts/scripted_cheaters.py` | main 64 + Open-8 36; shipped six |
| named main cues that passed removal | 176/176 | `gpuplan/b/body_numbers.json` `removal_named_mains` | `scripts/body_numbers.py` | main study 64 |
| Terra run cost | $0.678 mean | `analysis.json` `s4["gpt|open8"].usd` | `scripts/blackbox_analysis.py` | Block 1 Terra Open-8 24 |
| output tokens blind vs proxy; capped gain | 87k vs 62k; +0.46 | `gpuplan/b/body_numbers.json` `terra_tokens` | `scripts/body_numbers.py` | Block 1 Terra Open-8 24, BB-8 24 |
| detectable difference, 16 per arm | 0.54 (rates symmetric around 0.5; 0.39 when the top rate is 1.0) | `gpuplan/b/body_numbers.json` `mde_16` | `scripts/body_numbers.py` | exact Fisher, α 0.05, power 0.8 |
| Terra budget curve | 12/12 at 4; 23/24 at 8; blind 6/24, 16/24, 24/24; +0.71; 6 of 6 items | `gpuplan/open4/open4.json`; `analysis.json`; `bb16/analysis/bb16_analysis.json` | `scripts/open4_analysis.py`; `scripts/blackbox_analysis.py`; `scripts/bb16_analysis.py` | Terra Block 1, BB-16, Open-4 |
| top-two script at 8; ≤ 0.50 at 4 | 0.96; 0.50 | `gpuplan/xr_curves.json` | `scripts/xr_scripted_curves.py` | shipped six, 2000 seeds |
| texts on the anomalous probe at 4 | 2.67 vs 0.44 | `gpuplan/open4/open4.json` | `scripts/open4_analysis.py` | Terra Open-4 12 |
| exchange rate range | 11 to ~50 (`gpuplan/fig2_inputs/c3_bstar.json`); the "fits 22-58" span is **not in this repo** (paper_loop exchange-rate notes) | `gpuplan/fig2_inputs/c3_bstar.json` | copied input; no generating script here | abstract model; **flag** |
| Luna lift; Haiku by type | 5/36 vs 1/24; 5/6 vs 1/6; 0/6 vs 2/6 | `luna/luna.json`; `analysis.json` | `scripts/luna_analysis.py`; `scripts/blackbox_analysis.py` | Luna 60; Haiku Block 1 |
| tested true cue passes; untested failures | 53/57; 26 of 30 | `followup/failure_modes/failure_modes.json` `B_pass_given_true_cue_tested` | `scripts/followup_failure_modes.py` | 100 proxy runs |
| isolations on the proxy's top two | 84/95 vs 36/93 | same, `A_gpt_by_population` | same | Terra Open-8 24, BB-8 24 |
| Luna refuted-then-submitted | 7 runs | `gpuplan/c8/flags.json` | `scripts/luna_decoy_flag.py` | Luna Open-8 36 |
| Table 2 | 11/12, 0/18, 1/18; 4/48, 2/72 | `luna/luna.json` `L4.widening`, `L1`, `L2` | `scripts/luna_analysis.py` | Terra Open-8 12 trap runs; Luna 18 |
| Table 2 held-out | 20/21 (7/7, 6/7, 7/7); 2/17 (1/5, 1/5, 0/7) | `gpuplan/c14b/c14b.json`; `gpuplan/c14/c14.json` | `scripts/c14x_analysis.py`; `scripts/c14_analysis.py` | 21; 17 |
| texts on trap vs other; two-part | 3.9-4.0 vs 1.3-1.4; 1.9 vs 2.0; 12/12 vs 4/18 | `gpuplan/xr_alloc.json`; `gpuplan/c8/c8.json` | `scripts/xr_alloc.py`; `scripts/judge_luna_oos.py` | Terra with SAE; Luna Open-8 |
| band firing by unit | proxy 15/15, 0.925, 0.205, 0.258; topic 12/15; class gap 0/15; gap scripts 3/15, 0.43 | `followup/solvers/band.json`; `followup/solvers/topicunit.json` | `scripts/followup_band.py`; `scripts/followup_topicunit.py` | 3 shipped traps × 5 seeds; bank units |
| band-plus-closeness | see `gpuplan/t/` | `gpuplan/t/tell.json`, `tell_posthoc.json` | `scripts/t_bandclose.py`, `scripts/t_bandclose_posthoc.py` | shipped six, 40 bank |
| gap mentioned in Claude reasoning | 3 of 14 passes, 5 of 12 failures | `followup/heldout/heldout.json` | `scripts/followup_c3_band.py` | 26 held-out trap runs |

## Statistics (§6) and cost (§9)

| body number | value | file | script |
|---|---|---|---|
| sign p 6 of 6; 3 of 3 | 0.016; 0.125 | `gpuplan/c6/c6_items.json` `summary.note`; `gpuplan/c8/PREREG_C8.md` | `scripts/c6_items.py`; (prereg arithmetic) |
| run-level p | 2×10⁻⁴; 1.5×10⁻⁵; 2×10⁻⁷, 3×10⁻⁶ | `analysis.json`; `gpuplan/open4/open4.json`; `luna/luna.json` | `scripts/blackbox_analysis.py`; `scripts/open4_analysis.py`; `scripts/luna_analysis.py` |
| "45 registered entries", α ≈ 0.0011 | a count of the paper's Appendix M rows | — | paper-side; **flag**: no data script |
| held-out gap p | 0.002 | `gpuplan/c14/c14.json` | `scripts/c14_analysis.py` |
| spend | $101.45, $5.27; cumulative $192.21, $83.67; $29.25 for 354 calls | `gpuplan/RESULTS_FOR_PAPER.md` Spend; `RUNLOG.md` | RUNLOG rows (schedulers, `scripts/judge_ladder2.py`) |
