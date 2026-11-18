# Round 10: plan for your review (judge-prompt fix and full judge rerun)

Written 18 Nov, 03:00 UTC. It merges GPU_PROMPT_10 with three read-only reviews (coverage, prompt-fix correctness,
design). The paste-ready GPU prompt is `GPU_PROMPT_10_v2.md`. Nothing has been sent or edited.

## 1. What went wrong and why we rerun everything

- **The task text every judge saw asks for SAE latents.** The ⟨contract⟩ in every frozen judge prompt is the
  open-arm task prompt. It defines a cue as "a regex … plus SAE latents to ablate" and contains the mean-ablation
  removal test.
- **The answer the judge saw has no latents.** 0 of 254 final-answer blocks list a latent; the block prints regex
  and scope only.
- **Two of our three judges grade the missing latents, not the agent's evidence.** In Round 9's post hoc tally,
  77–91% of the passes Terra rejects without the key cite latents or ablation, and 82–97% of Haiku's. So do all 69
  of Terra's confidence-100 verdicts at the log level (61 of them reject passes). Sol rarely does (0–5 per level).
- **It confounds the headline contrasts.** The artifact hurts only answers that name a cue; a `none` needs no
  latents. So "wrong `none` 23/26 vs wrong cue 9/17", "no report: 31/39 vs 1/39" (the scripted answers carry
  empty latent lists), κ about 0, "its most confident verdicts are its worst" and "Haiku rejects almost every pass"
  may all be partly this artifact.
- **Rerun every judge call, not just some.** A partial rerun leaves tables on two prompts. One corrected prompt,
  everywhere, is the only clean fix. It costs about $136 OpenAI and $5.4 Anthropic, under the $180 / $10 guards.

## 2. What stays and what changes in the paper

| Part of the paper | Changes? | Why |
|---|---|---|
| ShiftHunt, items, traps, tools, budgets (§2, App. A, C, D, I, M) | No | No judge involved |
| Executed grades, Table 1, the executed Terra–Luna gap (+0.86) | No | Executed, not judged |
| The judge-free one-line rule (Table 4, rule column), proxy ranks | No | Uses SAE scores only |
| Every judge verdict, credit, κ, AUROC, pass mark, confidence number | Yes | Re-sent on the corrected prompt |
| Tables 3, 5, 6; judge columns of Table 4; Figs 1 and 2; App. E–L; Table B1 | Yes | Built from judge verdicts |
| JUDGE_FAILURES_TABLE (13 rows) | Yes; rows 2 and 9 expected to move most | Rows 2 and 9 are mostly the artifact |
| App. B (prompts) | Yes | New prompt text; B.1 and B.6 are also wrong now (§8) |
| App. N (tests and deviations) | Yes | New deviation R10-1; two outcome columns |
| Title, abstract, contributions | Only if a pre-stated reading fails (§7) | Draft both versions now |

## 3. The corrected prompt (verbatim)

All judge templates share two parts, so there are two edits. The rest of every prompt stays byte-identical: the
report, log, transcript, key, candidate block, sceptical text, answer block and JSON form.

**Edit 1, the contract (identical in every template).** These edits were checked against the frozen bytes: the
reconstructed contract hashes to the `contract_sha256` in `judge/inputs.json`. The ⟨contract⟩ is the two-part
("freetext") render, *not* App. A as printed. Before the fix: sha256 `2e2a3c77…`, 5,243 characters. After: sha256
`99e06480…`, 3,879 characters.

| # | OLD (exact) | NEW |
|---|---|---|
| E1 title | `# Task: find what text classifiers rely on besides their topic, and remove it` | `# Task: find what text classifiers rely on besides their topic` |
| E2 cue definition | `A cue is a regex that detects the property⏎(with a scope) plus SAE latents to ablate. A probe may list at most 16 distinct latent ids over all its cues,⏎and no cue's list may have more than 16 entries.` | `A cue is a regex that detects the property⏎(with a scope).` |
| E3 removal test | `…and so does a main cue that no regex detects;⏎  - mean-ablating the union of all latents you list for the probe …` through `…against you; kept is effect after / effect before.` (13 lines) | `…a main cue that no regex detects.` (`;` becomes `.`: one extra byte, logged) |

After E1–E3 the contract contains "ablat" 0 times and "remov" 0 times. "Latent" remains only in the SAE paragraph,
which we keep on purpose: transcripts show SAE use, and the judge needs it to read them.

**Edit 2, the instruction (one inserted sentence, same in every template).** The anchor in the plan ("…must name
exactly its main cues") does not exist as one string: the template breaks the line after "name". And "after" it
would put the sentence inside the parenthesis. The working anchor is `the answer must name⏎exactly its main cues). `.

The plan's sentence had three faults:
- it said nothing about `none` answers, which are the headline;
- "answers are shown without their SAE latents" is false at the transcript levels, where the agent's own submit
  call, latents included, is visible;
- "the task's removal step" pointed at text the fix deletes.

The new sentence merges the three reviewers' wordings.

| Template | OLD (exact) | NEW |
|---|---|---|
| Report (L0, L0r, H0, C8, R2/TF2, TF), log (L1, L1r, H1, H1r), transcript (L2, L2r, H2, H2r), every key level (K0, L3_0/1/2, S3), C12 scripted, C14 H5/H5c, all Sol S0–S3 | `…for a probe with main cues the answer must name⏎exactly its main cues). Give your confidence (0-100) that your verdict is right.` | `` …the answer must name⏎exactly its main cues). Judge only this naming: whether each probe's answer (`none`, or the cues it names) is right. Some agents were also asked to choose SAE latents whose ablation removes each cue; that removal step is graded separately and is not part of your verdict, so the final answer below lists only each cue's regex and scope. An answer is not wrong because it lists no latents or because an ablation removed too little. Give your confidence (0-100) that your verdict is right. `` |
| Abstaining (F1, F2, Sol SF) | `…exactly its main cues). For each probe give a verdict: "pass" …` | same sentence inserted before `For each probe give a verdict:` |
| Sceptical (C7 TK, LK, HK) | `…exactly its main cues). Give your confidence (0-100) that your verdict is right.⏎⏎How to treat `none`. …` | same sentence inserted before `Give your confidence`; C7's ANCHOR and K_TEXT unchanged |

Unchanged on purpose:
- the log instruction (INSTR) and the transcript instruction (INSTR2);
- the key instruction (INSTR3, "names exactly the probe's main cue");
- the checking rule (RULE) and the sceptical text (K_TEXT).

None of them mentions latents as a requirement. The sentence contains no braces, so it is safe in C12's
`.format` template. Sol prompts are byte-equal copies of Terra's, and the GPU agent asserts this.

## 4. Rubric decisions

**Second-cue ambiguity in the abstaining rubric (F/SF).** Terra answers "cannot tell" on 47 of 50 confirmed
passes, 38 of them citing a second main cue not ruled out (failures-table row 13).
- (a) **Keep F as is, apart from the two edits (recommended).** F is pre-specified. The task says "one or two per
  probe", so Terra's reading is defensible. A second change on top of the latent fix reads as tuning after results.
  Relaxing only the named-cue side also makes the rubric asymmetric (one test for a cue, eight for a `none`). The
  paper says the row-13 fault remains.
- (b) Optional, labelled post hoc deviation R10-2: an extra F′ row, Terra F1 on set A (about $4.5). Add to the
  named-cue rule: "To credit a named cue you need not rule out a second, unnamed main cue." Never mention that the
  shipped probes have one cue (that leaks the truth).

**Key wording ("main cue" singular, but the contract allows two).** Key-level rejections of passes do not cite
latents (Terra 0/63, Sol 0/39), so the fix will not move row 1 (12/87, 10/87). Recommendation: free tally first
(rejections by item and by number of regexes in the answer). A "main cue(s)" variant would be a separate, optional,
logged deviation, not part of R10.

**Confidence storage.** Three code paths lose or invent confidences:
- JV's parser turns a missing confidence into 50;
- C6's analyse keeps no confidence for L0 slots;
- Sol's abstaining parse keeps none.

The GPU agent writes one sidecar per batch, {verdict, raw confidence or null, reason, call id, send}, and never
imputes a value. Every confidence analysis reports n_missing. If n_missing > 0, it is reported with and without
those slots. The frozen analysis scripts still run unchanged, for comparability.

**Send convention.**
- Methods stay as registered: L0 (J1–J4 file) and L0r (inside C6's interleaved file) are both sent. L0r stays the
  C6 ladder baseline (J5′–J8).
- Tables and figures report the r10 first send (L0) at the report level. The re-sends (L0r, C8's 24 Terra, TF2/R2,
  the same-day control) are used only for test-retest κ and noise bounds.
- Each table names its send in a note.

## 5. The rerun: blocks in priority order

Costs come from logged cost per call: Terra L0 $0.0092, L2 $0.083, C6c $0.053, F $0.035; Haiku H0 $0.0016, H2
$0.022. Times assume at least 4 OpenAI processes, because the client sends OpenAI calls one at a time.

| Block | What (calls) | OpenAI | Anthropic | Wall time |
|---|---|---|---|---|
| P0 freeze ($0 + dry runs) | Transform every stored calls file; hash; commit PROMPT_FIX + PLAN_R10. Free tally on stored reasons (C12, C7, C8, C17). One 5-longest dry run each for Terra, Sol and Haiku, quarantined unread | ≈4.7 | ≈0.5 | ≈1 h |
| P1a gate | Terra L0 set A (132) + Haiku H0 (132); same-day frozen control, the same 264 on the old prompt. **Stop gate** (§7) | 2.4 | 0.4 | ≈0.4 h |
| P1 headline, set A | Rest of the C6 file (Terra L0r, L1, L1r, Luna-set L1 = 456; Haiku H1, H1r); L2 set A 130; H2 130; C12 (Terra 102 + Haiku 102); K 190; Sol S0+S1 260, S2-A 130, S3 130 | 45.1 | 3.3 | ≈2 h |
| P2 other sets, pairs, C7, C17 | Terra L0 rest 82; C8 84; L2 Luna + main 124; Sol S2 Luna + main 124; judge_panel terra file (TF2 214 + TK 274); small file (Luna LF + LK 548, Haiku HF 142 + HK 274) | 41.2 | 0.4 | ≈1.4 h |
| P3 key ladder, rubric, placebos | C6c 462 (L3_0/1/2); F 178; SF 130; L2r 100; H2r 36; C14 H5 27; C14b H5c 18 | 42.3 | 0.8 | ≈1.2 h |
| **Total (P0–P3)** | 4,975 counted calls + 264 control + dry runs | **≈136** | **≈5.4** | ≈6 h sending |
| P4 optional | Gap fills (§8 O1) ≈$20 / $0.3; F′ ≈$4.5 | ≈25 | 0.3 | ≈1 h |

End to end: about 6 h of freezing and sending, 2 h of recompute and 1.5 h of diff and independent recheck. Started at
04:00, that gives about 13:30. That is just inside the 14:00 target, and the portal closes 20 Nov 06:00.

## 6. Recompute list

These analyses rerun on the r10 verdicts. The scripts are unchanged and run in an isolated worktree.

**Ladder.**
- C6, c6_items, C6b, c6b_holm (J11's label), C6b-H, c6bh_analysis, C6c;
- the ladder tables (ladder_table.py, Claim 2), K and Sol S (all tables), sol_agent_unit.

**Panels and controls.**
- JV analyse for J1–J4. It writes judge/slots.json, which C19, C21 and reconcile read.
- C8 (judge_luna_oos analyse), C7, C12, C17 (Fleiss κ), C14 and C14b judge analyse.

**Downstream analyses.**
- C19 (reorder, τ_b, 13/36), C21, PPI, A (intervals), B (reconcile, body_numbers);
- D and U (decidable slots), E (per item, McNemar);
- F and V6 (selective prediction), V (verifier.json judge columns);
- W6 (footnotes, p = 0.004), J9 (Luna's 7 refuted [decoy]);
- X7 (X1–X4), R8 (checks 1–6), R9 (checks 1–4).

**Paper numbers that change.**
- Abstract: 37/40, 21/40 and AUROC 0.91. The rule's 40/40 stays.
- §1 "What we find"; §4.1–4.7 text.
- Tables 3, 5 and 6 and Table 4's judge columns; Figs 1 and 2. The figure values are hard-coded in
  make_fig1_v10.py and make_fig2_v10_1.py, so the GPU agent outputs a value table in those rows.
- App. E–L and Table B1 (cost per call; the contract is 1.36k characters shorter).
- All 13 rows of the failures table.
- App. N, with two outcome columns.

## 7. Pre-stated readings (frozen in PLAN_R10 before any corrected verdict is read)

Each reading is labelled **holds** / **weakened** (same direction, interval includes 0) / **reversed**.

- **H1.** Terra credits over 50% of wrong `none` on set A hard slots at the report and transcript levels; Sol over
  50% at the transcript level.
- **H2.** For Terra at the report, log and transcript levels, the share of wrong `none` credited is higher than the
  share of wrong cues credited (item bootstrap).
- **H3.** C12 sign test: P7 > P0 pooled, p < 0.05 for Terra. P0's absolute credit is also reported.
- **H4.** The judged Terra–Luna gap at the report level has a 95% interval that excludes the executed +0.86.
- **H5.** C17 self-agreement κ is above κ with the grade (report level, hard slots).
- **H6.** With the key, 0 wrong `none` are credited.

**Rule.** If H1 or H2 fails, the title, abstract and contributions change. If H3–H5 fail, the section and the
failures-table row change.

**Expected to move, so do not over-read:**
- failures rows 2 (confidence-100) and 9 (Haiku rejects passes) should largely disappear;
- "its most confident verdicts are its worst" and "Haiku errs the other way" are re-derived from new data, not
  carried over;
- row 1 (key rejections) should not move, and stays unexplained.

**Sol as a built-in check.** Sol's rejected passes should change within re-send noise. If they do not, something
other than the fix moved.

**Validation gate (after P1a; stop if it fails).**
- *Measure:* share of rejected passes whose reason rejects for missing latents or too little removal. Every match
  of the narrow pattern is hand-read.
- *Pass:* ≤ 5% per judge (Terra L0, Haiku H0).
- R9's broad "latent|ablat" count is reported alongside it, for comparability.

## 8. Changes to GPU_PROMPT_10 (all are in v2)

**MUST**
1. Isolate: separate worktree with r10 copies of the private judge directories; never run an original `build`,
   never `--force`; originals read-only, hashes verified at the end. (Otherwise the client silently reuses old
   200s and `build` overwrites registered files.)
2. Transform the stored calls files with one `fix(p)` (every count asserted exactly 1), not rebuild: identical
   truncation, no l1_block assert failure.
3. Exact E1–E3 strings, working anchor, contract hashes checked before and after (§3).
4. The corrected sentence (§3).
5. Pin set A to the original 130 ids (J2's assert otherwise fails).
6. L0r (a registered baseline, not a placebo), C12, K and S3 into P1; C6 file sent whole in seeded order.
7. Retries: the client's own only; failed or unparsed calls not re-sent; drop ids with a meta file before any
   re-invocation; report n.
8. C7 and C17 via judge_panel's two files as built (TF = r10 L0 + C8; HF on set A = r10 H0); no fresh TF.
9. Pre-stated readings (§7) frozen in PLAN_R10 with its hash.
10. Validation stop gate with its threshold (§7).
11. Full recompute list; ROUND10_DIFF also covers the appendix, failures table, figure values and RUNLOG/SPEND.
12. Per-block budgets, cumulative RUNLOG check, one dry run per model.
13. Fallback: a number not rerun goes to the appendix labelled "frozen prompt", never unlabelled in the body.
14. PROMPT_FIX.md holds template diffs only, never filled key or candidate blocks (leak).
15. At least 4 parallel OpenAI processes, each with its own raw directory; watch for 429s.

**SHOULD**
1. Same-day frozen control (about $1.4).
2. Free preview tally on stored reasons ($0, first).
3. Confidence sidecar with no imputation; n_missing.
4. Flag changes against the re-send spread; record response model ids and dates.
5. Extra tallies: key rejections by item and regex count; rejected passes with ≥ 2 regexes; credited verdicts
   citing latents.
6. Log the known contract leftovers (freetext sentence on trap and main runs; open-arm SAE paragraph on blind
   runs).
7. Free failures-table fills from stored or rerun data (Haiku log column; Sol rows 2, 3, 6).
8. State the exclusions: 11 Nov coders; Exp D, E, F.

**OPTIONAL:** O1 paid gap fills, about $20 / $0.3 (Haiku report + key; Sol on Luna's set at report + log; Sol on
C12; Sol transcript + key, main study; Sol sceptical C7 last). O2 F′ (§4). O3 key wording variant, only if the
tally points to two-regex answers. O4 your hand-read of 20 rejected passes. Not recommended: an LLM coder of
reasons (one more unvalidated judge).

**Author-side (not GPU):**
- fix App. B.1: the contract is the two-part render, not App. A;
- fix App. B.6 ("removal test never shown"): true of the corrected prompt only;
- add deviation R10-1 to App. N (text in v2 §0) and write "pre-specified", not "pre-registered";
- draft the holds and weakened versions of the title and abstract now.

**Open decisions for you**
- **D1. What the body reports.** Recommended: the r10 numbers, labelled as a post hoc correction, with the registered
  frozen ones in App. N.
- **D2. The sentence.** Approve the wording, or drop the last clause ("or because an ablation removed too little").
- **D3. F rubric.** Keep it as is (recommended), or also run F′.
- **D4. Optional fills.** Run O1 and O3?
- **D5. If the gate fails.** Stop and redesign (recommended), or proceed.
- **D6. If time runs out.** Label and move the unfinished items, or hold the upload until the 20 Nov 06:00 portal
  close.
