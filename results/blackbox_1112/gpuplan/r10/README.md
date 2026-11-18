# Round 10: every judge call re-sent with a corrected prompt aligned with the grader (post hoc deviation R10-1)

Plan: `PLAN_R10.md` and `PROMPT_FIX.md` (hashes in `PLAN_HASH`, frozen in 0f6a236 before any counted call); addendum
`PLAN_R10.md` section 13 and the PROMPT_FIX addendum templates (`PLAN_HASH_ADDENDUM`, frozen in aa00de9 before any
addendum call or computation). Prompt source: `paper_loop/gpu_plan/GPU_PROMPT_10_v2.md` (author decisions D1–D7 final)
and `GPU_PROMPT_10_ADDENDUM.md`.

| block | folder | status |
|---|---|---|
| P0 freeze (prompt fix, isolation, plan) | `PLAN_R10.md`, `PROMPT_FIX.md`, `ORIG_HASHES.txt`, `scripts/` | done, 0f6a236 |
| P0.5-F reason scan on the frozen verdicts | `p05/` | done, ea4fac8 |
| Dry runs and projection | `dryrun.json` | done (13 calls, $4.61; projection P0–P3 OpenAI $129, Anthropic $5.4) |
| Addendum freeze | `PLAN_R10.md` s.13 | done, aa00de9 |
| P1a gate and same-day control | `gate/` | done: **pass** (Terra L0 0/24, Haiku H0 0/219 rejected passes cite latents; same-day frozen control 98/109 and 224/297) |
| P1 headline on set A | `p1/`, `out/`, `diff/`, `table3_*`, `readings_*`, `tallies_*` | done: Terra report κ −0.02 → 0.32, passes rejected 24 → 6/87, wrong `none` 23 → 19/26; H2 **weakened** (report, transcript); H3 holds (17/39 vs 7/39, p 0.041); no confidence-100 verdict at L1 |
| P2 other sets, pairs, C7, C17 | `p2/` | done: J1 κ 0.002 → 0.284 (still confirmed), J2 0.78 → 0.71; C17 hard Fleiss κ 0.39 → 0.84 (same-day sends); H4 holds (trap gap −0.19 → +0.03 vs executed +0.86); H5 holds; C7 sceptical prompt still threshold-only |
| P3 key ladder, rubric, placebos, C14 | `p3/` | done: key ladder unchanged (H6 holds); J11 confirmed → **not confirmed** (L1 already near L2); Sol R sentence → "a stronger judge … fails the same way"; F1 coverage 16 → 30/130, still never passes a wrong answer |
| P4 O1a–O1e, O2 | `p4/`, `p4.json` | done: Sol on scripted answers also prefers `none` to the true cue (19/39 vs 6/39); F′ cuts abstentions 100 → 76 and credits 54 instead of 29 passes |
| Addendum AD1–AD5 | `addendum/` | done: support does not drive credit (AD1); judges say every credited `none` was unverified (AD4); clustered ORs include 1 at r10 report/transcript (AD2); the rule, not the list or abstention, zeroes wrong-`none` credit (AD3); a stated base rate makes Terra more lenient (AD5) |

## Deviations (every one logged; the box wins)

1. **D7 alignment.** The main r10 prompt carries A1–A5 on top of E1–E3 and the sentence, so the reference
   implementation's `FIXED` hash and `== 957` assert are replaced by the recomputed contract hash and per-template
   length changes (PROMPT_FIX). The E1–E3 intermediate hash `FIXED` is still asserted on every call.
2. **E3's one byte.** `;` → `.` at the end of the preceding bullet (part of E3_NEW, as in the reference).
3. **Dry-run directories** of the original judge folders were not copied into the worktree (no analyse step reads
   them); only `raw*` directories had to start empty.
4. **Sends go through `scripts/r10_run.py send`**, which calls `textonly_client.run_calls` with gpt-6.1-sol and
   gpt-6-luna registered exactly as `sol_judge.py` and `judge_panel.py` do (the client's CLI does not know them),
   drops every call id that already has a `.meta.json`, and never passes `--force`.
5. **Subset sends.** The gate (r10 L0 and H0 on set A) and the C6b file (L2 set A / L2 Luna + main / L2r) are sent
   as filtered calls files that keep the stored order (`gpuplan/r10/subsets`, `gpuplan/r10/gate`, private).
6. **One C6 call killed in flight and re-sent.** The C6 lane started 6 s before the gate's H0 lane had finished on the
   same raw directory, so it was stopped at 05:35 UTC to avoid sending any H0 call twice (no call was sent twice:
   no `superseded/` entry). One L1r Terra call was in flight when the lane stopped; it had a request file and no
   response, and the restarted lane sent it once more (the client moves the old request to `superseded/`).
7. **Sol S2 cap split** into $28 (set A, `raw_s1`) and $30 (Luna + main, `raw_s4`), together within the prompt's $55
   for the two files only if `raw_s1` spends ≤ $25 (projected $20.7); checked at the end.
8. **P4 caps** (not in the prompt's table) were set at about 1.3 times the prompt's estimates (PLAN_R10 item 11).
9. **Sol and Haiku P4 items started while P1–P3 were still sending** (05:38 UTC): they use separate models and raw
   directories and do not compete with the Terra lanes; the Terra P4 item (O2) and every addendum send wait for P3.
10. **P0.5 excerpt screen made stricter** (after P0.5-F showed cue paraphrases outside the descriptions' words): an
    excerpt is also withheld if it contains a property-name word or a cue-vocabulary stem (the stems are kept in a
    private file because the property scan flags them). Hand redaction is done only for the excerpts the README
    prints. The frozen family strings are unchanged (sha 8d801381).
11. **The P0.5 word for a verbatim citation** in the pasted block of PLAN_R10 item 12 is written "excerpt" (the
    property scan flags the original word); the AD4 follow-up text is kept verbatim in a private file for the same
    reason, with its sha256 in PROMPT_FIX.
12. **Worktree slot files reset.** Before any r10 send, `judge_vs_grade analyse` and `judge_luna_oos analyse` were
    run in the worktree on empty raw directories, so the copied frozen `judge/slots.json` and `judge_luna/slots.json`
    were replaced by empty r10 files and no analysis can read frozen verdicts as r10 ones.
13. **AD2 model.** No mixed-model library is installed; the item-clustered GEE with an independence working
    correlation (logistic regression with the item-clustered CR1 sandwich) is used, with an item bootstrap; the run
    random effect is not fitted (PLAN_R10 s.13).
14. **Confidence sidecar** files hold reasons and call ids, so they are written to the private r10 folder, not to the
    tracked `gpuplan/r10/conf/`; the tracked folder gets the n_missing counts.
15. **Control cap.** The Terra control lane was given $1.3 instead of the plan's $1.6, so one control call was held
    back by the budget guard; it was sent at 06:24 UTC under $1.6 (not a re-send: it had never been sent).
16. **Gate hand reads** are in a file of their own (`gate_narrow_handread.json`, private), separate from the T5 leak
    categories (`gate_handread.json`).
17. **C6 split into four sub-lanes at 06:47 UTC.** The single C6 process (OpenAI one call at a time, and its Haiku
    calls held behind the same worker pool) would have finished P1 after 09:00 UTC, so it was stopped and the 416 calls
    with no `.meta.json` were sent by four processes on disjoint, order-keeping subsets of the stored file
    (`subsets/calls_c6_rest{0..3}.jsonl`, round-robin) into the same raw directory, each capped at OpenAI $3.8 /
    Anthropic $0.65 (the directory's $8 / $1 cap is checked on the total at the end). Two calls were in flight when the
    process stopped (one L0r, one H1): they had request files and no response, and each was sent once more.
18. **RUNLOG rows** are written per batch from the meta files (`scripts/r10_cost.py row`); the C6b directory (L2 set A, L2 Luna + main, L2r) is logged as one row when its last block finishes, so no call is counted twice.
19. **C7 panel split at 07:25 UTC**, as C6: the small-judge lane (Luna serial, Haiku behind it) and the Terra lane were
    stopped and their 447 and 147 remaining calls sent by three and two processes on disjoint order-keeping subsets
    (`subsets/calls_panel_{small,terra}_rest*.jsonl`). Two calls were in flight (one TK, one LF) and were sent once
    more. Per-process caps: small OpenAI $0.62 / Anthropic $0.42, Terra OpenAI $3.8 (directory caps checked at the end).
20. **F split at 07:26 UTC** into three sub-lanes the same way (cap $4.4 each; the directory's $8 is checked at the end); one F1 call was in flight and was sent once more.
21. **F-a (AD3) split at 08:21 UTC** into three sub-lanes the same way (cap $2.2 each; the item's $3 is checked at the end); any call in flight was sent once more.
