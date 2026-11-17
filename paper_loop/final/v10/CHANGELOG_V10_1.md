# CHANGELOG V10 → V10.1

Source of review items: `final/REVIEW_V10.md` (§4 issue table rows 1–11, §5 real errors, §6 overstated quotes, §7 top edits) and the seven reviews in `final/reviews_v10/`. Task items A1–A13 and B are the workflow's numbering. All changes are wording or restructuring of existing results; no new analysis was run. Every new number comes from `facts/FACTS_ONLY.md` (IDs in brackets).

Length (body without references, markdown table syntax excluded): V10 5,047 → V10.1 6,797 words, of which about 680 are in tables. Abstract 199 words.

## A. Review fixes

| # | Review item | Change in V10.1 | Where |
|---|---|---|---|
| A1 | §4 row 1; §7 edit 1; AC 2b-1; R1 MW2; R3 MW1; H1 W1; H2 | Judge-free rule brought into the body. New §4.3 paragraphs and new **Table 5**: rule AUROC 1.00 on the 40 pairs and 0.96 [0.88, 1.00] on the 36 pairs from runs without SAE tools, where the judge is at 0.53; printed-only check (20 pairs, still 1.00); top-two variant at chance (0.48) [X7-X1, X7-X2]. New paragraph "Part of the signal is a property of the probe" (null median 0.04 vs hard 0.41) [X7-X2]. States that in this environment an SAE lookup can tell the null probe from the hard probe; repeated as an environment limitation in §6 ("What the SAE view gives away"). Contribution 3 rewritten: the rule reads the signal perfectly; the judge's confidence partly tracks it (0.91, partly by recognising the null probe); its verdict ignores it; a pass mark recovers part. Abstract and intro "What we find" rewritten to match; all marked post hoc. §4.4 says the pass mark inherits the caveat and that no pass mark was tested on the rule. Conclusion practice 2 now: compare a judge's confidence with a simple rule on the same evidence. | Abstract; §1; §4.3; Table 5; §4.4; §6; §7 |
| A2 | §4 row 2; §5 error 1; §7 edit 2; H1 W4; R1 MW3; H3 W2 | One send convention, stated once in §3 ("One send per verdict"): report-level verdicts are Terra's first send throughout; the re-send is given where it differs. Table 4 (old Table 1) keeps the first send (9/17, 23/26, 24/87) with footnote ᶜ giving the re-send (7, 20, 33; κ −0.01) [C6, B3, W6-3]. Table 7 (old Table 3) now leads with the first send (11/12 vs 17/18, −0.03 [−0.19, +0.14]) and shows the re-send made alongside Luna's runs (−0.19 [−0.42, +0.03]) as a second row, noting it was the pre-specified test's send [R8-2, C8]. Fig. 2 regenerated as `fig/fig2_v10_1.png` with both report sends (filled = first send, hollow = re-send); script `fig/make_fig2_v10_1.py` changes only the plotted rows. Fig. 2 caption now holds under either send ("about zero"). Fig. 1 already used the first send; its caption now says so. | §3; Table 4; Table 7; Fig. 2 + caption; Fig. 1 caption; §4.7 |
| A3 | §4 row 3; §6 quotes on the key; AC 2b-7, 2b-8; R1 MW4; H2; H3 W4 | Key called a positive control throughout (abstract, intro, §3, §4.6 heading and text, conclusion); "correction" removed. §4.6 explains the rejected passes from the facts: 12/87 (Terra) and 10/87 (Sol) fall on two of six items; 11 of Terra's 12 are log-confirmed passes; they fall to 5 with the log and 0 with the transcript [S3-A per-item table, K]. "Where a key exists, it wins on cost too" and "cheapest and most accurate" removed; per-call costs kept as reporting. Table 4 title no longer says "at the lowest cost". | Abstract; §1; §4.6; Table 4; §7 |
| A4 | §4 row 4; §6 title quote; AC 2b-9; R1 MW5; H1 W5; R3 MW2 | Title narrowed: "ShiftHunt: An LLM Judge Accepts Wrong 'Nothing Found' Answers in an Auditing Task" (author's words kept; scope added). Haiku added as two Table 4 rows (report κ −0.11, 0/17, 8/26, 85/87; transcript κ −0.21, 0/17, 15/26, 82/87) [C6, C6b-H], plus §4.1 sentences and the no-report Haiku result (4/39 vs 0/39) [C12]. §3 "Judges" introduces Haiku as a judge from another family. §6 "Judges" adds that Haiku still accepts 15 of 26 wrong `none`. | Title; §3; §4.1; Table 4; §6 |
| A5 | §4 row 5; §5 error 2; AC 2b-2, 2b-3, 2b-5; H1; R3 | §4.2 heading changed from "For Terra, reading more helps against wrong findings more than wrong absences" to "Reading more helps Terra on set A, but not evenly across run sets". Full populations now precede the trap subset: Luna's 60 runs (cues 11→4 of 15; `none` 24→10 of 38) and the four-agent study (wrong-cue credit 3→5 of 6; `none` 13→8 of 13) [K, B3]. Sol's wrong-cue credit 6→8 of 17 stated [S0-A, S2-A]. Pass mark now reported on the 40 pairs next to all 188 slots, in prose and as new columns of Table 6 (Terra 21→13 of 40 at a cost of 5 right, BA 0.74→0.78; Sol 18→7, 0.76→0.83; report 37→19, 0.54→0.56) [R8-1]. 37/40 added to §4.3 and Table 5 [R8-4]. Added the share of passed `none` that are wrong (25 of 160 → 11 of 134), derived from R8-1 counts (H1 W2). | §4.2; §4.3; Table 5; §4.4; Table 6 |
| A6 | §4 row 6; §7 edit 4; AC 2c, 2b-12; H2; R1 C5; R3 MW5 | New **Table 3** (run sets used in the body: n, agents, arms, where used), with the 132-vs-130 footnote. Kept to nine rows. | §3 |
| A7 | §4 row 7; §6 quotes "we call them pre-specified", "Only the key changes the judge significantly…"; AC 2b-11; R3 MW4 | §3 "Statistics and status" rewritten: *pre-specified* = hypothesis, population and rule hash-committed before the calls or computation; commitments sequential, several after related results; *post hoc* = defined after the data existed even if the plan was hashed. Each result now carries its label where it appears. §4.2 McNemar paragraph rewritten without significance language ("Adding the key is the largest step on every run set", counts 45/0 and 23/2) [E, W6-2]; the report-to-transcript step marked post hoc. Removed "Steps of 0.1–0.2 κ … within run-to-run noise" (R1, R3: not supported by self-agreement κ); replaced by the measured re-send effect on κ (−0.02 → −0.01) and on rejected passes (24 → 33 of 87) [C6]. | §3; §4.1; §4.2 |
| A8 | §4 row 8; AC 2b-13; R1 MW1; H2; H3 W1 | §6 "Six items" adds: the item bootstrap over six clusters (three for the trap gap, ten distinct resamples) under-covers and is approximate; exact McNemar over runs ignores clustering, so p-values hold only for these six items [R8-2 method]. §4.2 notes the same at the point of use. | §4.2; §6 |
| A9 | §4 row 9; §5 error 3; §6 quote "Its most confident verdicts are its worst"; AC 2b-10; H1 W3; R3 | Confidence-100 moved from §4.3 ("The judge doubts the wrong ones") to §4.4 under "Terra's stated confidence ranks answers but is not calibrated". States that it covers all 520 set A slots at report + log (69 verdicts, 8 right), that 20 of the 23 hard-slot confidence-100 verdicts reject a pass [R8-6, V6], and adds the transcript-level subset (48 runs: 4 of 29 right at confidence 100) [V6 F2 curve, 29 × 0.1379]. | §4.4 |
| A10 | §4 row 10; AC 1.2; H3 W7 | §2 "Matched budgets": tokens were uncapped in both harnesses; within Codex CLI they were not matched either, and §4.7 uses the Terra–Luna gap to test the judge, not to rank agents. Luna's token use is stated as not tabulated (the facts give no Luna token counts); Luna's cost per run ($0.08–0.13) added to Table 2 next to Terra's $0.68 [AGENTS, LUNA]. | §2; Table 2 |
| A11 | §4 row 11; AC 2b-6; H1 | New §4.7 paragraph "The erased gap reflects general leniency on Luna's failures, not absences alone": from reports 10/10 wrong cues and 6/7 wrong `none` accepted; from the transcript 4/10 and 6/7 [R8-2]. Adds that Terra's judged passes never exceed its executed 11 (answers R2's self-preference point) [R8-2]. Abstract no longer ties the erased gap to absences. | §4.7 |
| A12 | §5 error 4; AC 2b-12 | Luna held-out: "2 of 17 pre-specified runs (2 of 21 with four extra runs)" [C14b, C14L]. | §2; Table 2 |
| A13 | §6 quotes | See the quote table below. | throughout |

### §6 overstated quotes and their fixes

| quote (V10) | V10.1 |
|---|---|
| Title "An LLM Judge Accepts a Wrong 'Nothing Found'" | "An LLM Judge Accepts Wrong 'Nothing Found' Answers in an Auditing Task"; §6 keeps "we claim nothing about judges in general"; Haiku rows added. |
| "A one-line answer key removes them more cheaply" (abstract) | "An answer key, a positive control, removes the false credit." |
| "A cheap correction and its limits" (contribution 3) | Contribution 3 is now the post hoc analysis of where the signal lies (rule, confidence, pass mark). |
| "The judge doubts the wrong ones" (§4.3 heading) | "The transcript carries a signal that the verdict ignores", with the judge-free rule and the probe-identity paragraph. |
| "more than halves the wrong `none` it accepts" (§4.4) | "cuts the wrong `none` it accepts"; full-population and 40-pair numbers both given. |
| "Left uncorrected, the judge's errors erase the study's own agent comparison" | "Judged from reports, the judge's errors erase the study's own agent comparison"; §4.7 gives the transcript gaps (+0.28, Sol +0.42). |
| "some after earlier results; we call them pre-specified" | Definition of pre-specified (hash-committed before calls or computation) and post hoc stated separately; the sequence and its limit disclosed once. |
| "Only the key changes the judge significantly on every run set" | "Adding the key is the largest step on every run set" (descriptive, counts only, clustering caveat). |
| "Its most confident verdicts are its worst" | "Terra's stated confidence ranks answers but is not calibrated", with population (520 slots, report + log), error direction (20 of 23 reject passes) and one judge named. |
| "First, grade from transcripts, not reports" | Removed. Practices now: validate on certified absences and findings separately; compare a judge's confidence with a simple rule and set any pass mark on other items; treat "every candidate tested" as evidence, not proof. |
| "the answer key is both the cheapest and the most accurate level" | Removed; costs reported as numbers (transcript about nine times a report call; keyed call about $0.006), with "the key is only a positive control". |

### Other reviewer points handled in passing

| Point | Change |
|---|---|
| R3, H3: "certified" is relative to the enumerated properties and bound | §2 "Certified nulls": "Certification is relative to the 15 properties the note generator varies and to that bound" [E07-02, E07-07]. |
| R3: "as §4.7 requires" unclear | Now "The executed grade separates agents, which §4.7 needs." |
| R1 minor: double negative on unspent budget | "In every judged run set, the median run spends its whole exact-query budget." [X7-X4] |
| R1 minor: §4.1 no-report judge and population | Names Terra; "12 on the six shipped items and 27 on generated items" [C12]. |
| H1, R1: 132 vs 130 | Table 3 footnote. |
| H1 minor: report + log AUROC on a different subset | Table 5 footnote (27 pairs; the four-agent study has no log level). |
| R1 minor: sceptical prompt untested at transcript level | §4.5: "We tested the prompt only from reports, where the ranking is weak." |
| H1: no-keyless judge beats the named-answer rule | §3 "Measures": the rule's 0.67 is "above every judge level without the key". |
| H1 W2: equal-cost BA | §4.4: BA weighs both errors equally, though §1 argues a wrong absence costs more. |
| Intro example | Labelled "(schematic)": the facts and supplement contain no agent report excerpts free of ids and cue names. |

## B. Expansion (≈5.0k → ≈6.8k words)

| Addition | Source | Where |
|---|---|---|
| Judge-free rule table (Table 5) | X7-X1, X7-X2, R8-4 | §4.3 |
| Population table (Table 3) | POP, X7, R8-1, R8-2, C7, C12, C14/C14b | §3 |
| Environment comparison (Table 8): FIND, Pando, AuditBench, Circuit Oracle, Auditors via RL, ACED, PaperBench, AstaBench, ShiftHunt × {executed grade, graded "nothing found" on clean targets, tool wrong at a chosen rank, LLM judge checked against} | R08-02, supplement Table D1, cards bragg2026, starace2025, kabir2026, rosu2026auditorsrl, chen2026, schwettmann2023find, zhong2026pando, sheshadri2026 | §5 |
| Terra vs Luna agent table (Table 2): proxy/blind 23/24, 6/24 (Luna 5/36, 1/24); runner-up tested 11/12 vs 0/18; shipped trap named 11/12 vs 1/18; held-out 20/21 vs 2/17; two-part 12/12 vs 4/18; cost per run | BLOCK1 population, LUNA, C14b, C14L, AGENTS | §2 |
| Coverage-by-budget table (Table 1): 317 / 27 / 41 `none` answers at 8 / 16 / 64 queries; fully tested 0 / 0 / 22; 2 wrong | X7-X4 (317 = sum of the six 8-query rows) | §2 |
| 40-pair columns in the pass-mark table (Table 6) | R8-1 | §4.4 |
| Intro example | no real excerpts exist without ids or cue names; kept schematic and labelled so | §1 |

## Not done (would need new analysis; outside this pass)

- Averaging verdicts over the three sends (REVIEW_V10 §4 row 2 "N"); a single-send convention is used instead.
- A held-out pass mark on the judge-free rule, a null-trap control, within-probe pairs, a third-family judge at transcript level beyond Haiku, more items (REVIEW_V10 §4 rows 1, 8 "N").
- Reliability diagram / risk–coverage figure (H1, R3; optional per AC 2c).
- Compile in the AAAI-27 kit and confirm 6–8 pages (REVIEW_V10 §7 edit 5): to be done at typesetting.

---

## V10.1 revision pass 2 (claims check, numbers check, CFP compliance)

Sources: the workflow's NUMBERS and CLAIMS checks of PAPER_V10_1.md (against `REVIEW_V10.md`, `reviews_v10/`, `v10/CFP.md`). Every item was checked against `facts/FACTS_ONLY.md` before being applied. No new analysis was run; every number added comes from the facts IDs in brackets.

### Applied

| # | Item | Change | Facts |
|---|---|---|---|
| 1 | "Verdict ignores / does not act on the signal" (C1) | Abstract, §1, Contribution 3, §4.3 heading and the §4.3 bold sentence now say the confidence partly tracks the signal but the default pass mark is lenient. §4.3 adds that the default verdict rejects 19 of the 40 wrong `none` from the transcript (3 from the report) and passes the other 21. The 40 right ones are passed at both levels. The SAE-hidden comparison adds wrong accepted 12 → 14 of 20. New §4.3 heading: "The judge's default verdict uses only part of a simple signal". | R8-4 (L0 3 failed, L2 19 failed); R8-3 (12 vs 14) |
| 2 | "Transcript holds the signal" / "rule on the same transcript" (C2) | The rule is now described as combining the SAE tools' scores with the record of which candidates had a clean test. §4.3 says the transcript prints both scores in only 20 of the 40 pairs, and that in the 36 no-SAE pairs neither the agent nor the judge saw them. Abstract, §1, Contribution 3, §4.3 bold sentence, Table 4 title and §7 were reworded. Table 4 title changed from "better than either judge" to "at least as well as either judge", because the 40-pair intervals overlap (0.91 [0.79, 1.00]). | X7-X2 printed-only (20 pairs); X7 |
| 3 | Matched budgets (A10; CFP rule) | §2 now gives a reason for setting no token cap: the task rations exact queries, and a cap would add failure by truncation. It says tokens could not be matched across harnesses, that Terra and Luna both ran uncapped within Codex CLI, and that §4.7 tests the judge, not the agents. On Luna's token use, it says the counts were used only to price runs and were not tabulated. The facts give Luna cost per run ($0.08–0.13) but no token counts, and no Luna run logs are reachable here. "Luna is weaker in general" became "At this budget Luna's failures are not confined to traps". The §6 phrase "the two weakest agents … stronger agents" became neutral ("Luna and Haiku … agents whose wrong `none` answers are rarer"). | AGENTS; LUNA |
| 4 | Length / compile (CFP 6–8 pp) | Compiled in the AAAI-27 kit (`latex/aaai2027.sty`, `.bst`) through a markdown-to-LaTeX script: `v10/compile_v10_1/{md2tex.py, main.tex, main.pdf}`. Before cuts: 9 pages. After: **8 pages including references** (body about 7 pages), with no slack. The script is approximate: tables use `\footnotesize`, and the wide tables are Tables 2, 3 and 5. A hand typeset may move by a few lines. Cuts: old Table 1 (coverage by budget) moved to Supplement Table I1, with the key numbers kept in §2 prose. Old Table 8 (environment comparison) moved to Supplement Table D1, and §5 text now states its finding. Redundant sentences were trimmed in §1, §2, §4.2–4.7, §5, §6 and §7. Tables were renumbered 2–7 → 1–6. Body: 6,985 → 6,426 words (markdown table syntax excluded; references excluded). | X7-X4; R08-02 |
| 5 | Send convention vs supplement (B1) | §3 now says that the first send is the pre-specified report-level test (registered on 214 runs that include set A). It adds that two later pre-specified tests used byte-identical re-sends as their baseline: adding the log (C6, L0r) and the agent gap (C8). Table 3 note b names the re-send as "the baseline of the pre-specified test of adding the log". This makes appendix line 371 ("7 of 17 at a byte-identical re-send, the registered baseline") consistent with the body. The appendix was not edited; an optional clarification there would read "the registered baseline of the log test". | J1-J4 (ed8c242, 214 runs); C6 (J6 baseline L0r); W6-3; C8 (6f8d2dc) |
| 6 | §4.4 "ranks answers" (C3) | Heading changed to "At report + log, Terra's stated confidence is not calibrated" (pair AUROC 0.54 at that level; bins not monotone). | R8-6; X7-X1 |
| 7 | Post hoc labels (C4) | The §4.3 confidence paragraph is labelled post hoc, and "suggests" is now "This post hoc comparison on 20 pairs suggests …". | X7 / R8-3 registration ("pre-specified, post hoc to the data") |
| 8 | §1 "at every level" (C5) | Now "at every level in Fig. 1". | C6, S0-A, S1-A, S2-A |
| 9 | "About zero" for −0.19 (C6) | The Table 6 (old 7) title and Fig. 2 caption now say "indistinguishable from zero (both intervals include zero)". The κ "about 0" in §4.1 and §7 is kept: it refers to κ ≈ −0.02, not to the gap. | R8-2 |
| 10a | §4.5 "every candidate tested" | Now "tested with no effect" (14 of 19). This matches the V6 row "isolated and clean" and explains 19 vs the 20 fully tested right `none` in X7-X4. | V6; X7-X4 |
| 10b | Table 2 (old 3) pairs row | Arms are now "SAE 8 (40); no SAE 8–64 (36)" (blind pairs: set A BB-8/16/64 19, Luna BB-8 17). | X7; POP |
| 10c | §7 Luna's trap failures | Now "of Luna's 17 failures on shipped traps the judge accepts 16 from reports". | R8-2 (10/10 + 6/7) |
| 10d | §4.5 heading | Now "A sceptical prompt and a checking rubric do not fix it". | C7; F |
| N1 | Ranking population (numbers minor 1) | Table 2 row "report-level sets" is now 196 (the C19 board excludes the 18 harder-variant runs); 274 is kept for the prompt test. | C19 (L9: 40+16+16+28+24+24+24+12+12); POP |
| N2 | Cost-per-call method (numbers minor 2) | Footnote "billed together; not separable" removed. Costs are now computed the same way as Terra's transcript cell: Terra report + log $0.013 (C6 $6.137 / 456), Haiku report $0.002 ($0.645 / 396), Haiku transcript $0.022 (C6b-H $3.695 / 166). The Table 3 caption says that Terra's and Haiku's batches mix levels, prompt variants or runs outside set A. | C6 Cost; C6b-H Cost |

### Not applied or changed from the proposal

- **A7 (optional): naming every test committed after related results.** Not done, for length. §3 already discloses the sequence, and Table 1 names the Luna case.
- **Token-cap rationale (item 3).** The facts record that tokens were not capped and not matched across harnesses (AGENTS). They do not record why. The sentence "a token cap would add failure by truncation to failure in the audit" is a design argument consistent with AGENTS (no-submission runs count as failures) and TOK (caps change outcomes). The authors should confirm that it states their reason.
- **Luna token counts.** Not reported. FACTS_ONLY has none, and no Luna run logs are available locally (`luna.json` has no token fields), so no number was invented.
- **Supplement follow-ups created by the moves.** Supplement Table D1 lacks two parts of the removed body Table 8: the PaperBench and AstaBench rows, and the "LLM judge checked against" column. If the supplement is revised, add them. §5 now states the corresponding claims in prose: Circuit Oracle compared with other judges; Rosu and Wang not validated.
- **§4.6 cost sentence** ("$29.25 over 354 calls") was cut for length. Per-call costs remain in Table 3 and §7.
