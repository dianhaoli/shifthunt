# Pull round 1 (cumulative since 2ec5800, snapshot 2026-11-12 06:02Z). Fetched 2026-11-12.

## origin/claude/serene-fermi-pog4k7: 1 new commit, 0fb9d29 (06:17Z)
"Luna arm pre-registered (L1-L4; 60 runs: Open-8 x6, BB-8 x4 per item); pilot ok ($0.136); analysis driver validated on Terra Open-8"
Files: results/blackbox_1112/luna/{PREREG_LUNA.md, PREREG_HASH, run_order.json, runorder_luna.csv}, scripts/luna_analysis.py, scripts/luna_schedule.py, RUNLOG.md, ledger.jsonl.
- Purpose: GPT-6 Luna in the same Codex harness as GPT-6.1 Terra, removing the harness confound from the model-dependence claim.
- Design: 60 counted runs = Open-8 (SAE, 8 exact texts) x 6 items x 6 + BB-8 (no SAE) x 6 items x 4; seed "luna-1112"; comparison = Terra's 24 Block 1 Open-8 runs (not re-run).
- Tests (one-sided Fisher, alpha 0.05 each): L1 Luna rank-2 isolation on the trap probe < Terra (Luna 18 trap runs vs Terra 12); L2 trap NAME Luna < Terra; L3 SAE raises Luna NAME (Open-8 36 vs BB-8 24); L4 descriptive. Run-level only; item-level generality not tested.
- Driver validation on Terra Open-8 reproduces: trap rank-2 isolation 11/12, trap NAME 11/12, NAME 23/24.
- Pilot (excluded from analysis): run 1a2e60748088, Luna Open-8 on one [main] item, status ok, 17.9 min, $0.136, 4 probe_query calls, model confirmed gpt-6-luna 7/7 turns.
- Spend: ARM_CAP_USD 20 (raised from 8), est $0.50/run, expected ~$8 for 60 runs. Cumulative OpenAI $82.883, Anthropic $78.403. Deadline 20 Nov 06:00 UTC.
- NO counted Luna results yet. Outcomes L1-L3: pending.

## Judge arm (J1-J4): NOT YET RESULTS
results/blackbox_1112/judge/ contains only PREREG_JUDGE.md and inputs.json (no judge.json, no README.md). No J1-J4 numbers or verdicts.

## Other branches (commits not ancestors of 2ec5800, but all dated BEFORE the snapshot; probably already reflected in drafts; verify)
- origin/claude/tender-dijkstra-hrga9p (to b2cc06f, 11-11 09:12Z): paper fixes from final 3-refuter number check (D47); placeholders filled (Table 2, solvers, seeds, trap flags, coders; body ~6.3 pp); GLMM ranges Sonnet 0.50-0.90, Haiku 0.25-0.75, GPT bootstrap lower bound 0.39-1.00; calls-left fact 91-124 of 150 in the 19 failing main-study runs (median 115); flag audit 8 upheld / 2 refuted.
- origin/claude/brave-curie-dhdngw (0736a60, 11-11 04:47Z): post-hoc token-cap sensitivity (results/blackbox_1112/token_cap.md, no new runs, descriptive p). Terra uncapped NAME Open-8 23/24, BB-8 6/24, BB-64 24/24; C1 +0.71 [+0.42,+0.96] Holm p 0.0002; C2 +0.75 [+0.50,+0.96]; C4 +0.04 [0.00,+0.17]. At BB-8-median cap (87k output): C1 +0.83, C2 +0.83, C4 0.00. C1 stays >= +0.71 at any cap >= 86k. Token medians (output): GPT Open-8 62k, BB-8 87k, BB-64 31k.
- main / cross-model-1104 / nifty-wozniak / festive-hypatia: nothing new.

No [OCT] material in any new file.
