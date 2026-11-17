NUMBERS CHECK: /home/user/shifthunt/paper_loop/final/PAPER_V10.md against /home/user/shifthunt/paper_loop/facts/FACTS_ONLY.md, with figure captions checked against /home/user/shifthunt/paper_loop/final/fig/make_fig1_v10.py and make_fig2_v10.py. No files were edited.

Overall: I found no wrong value. Every count, κ, interval, AUROC, BA, cost and McNemar claim in the abstract, Tables 1-3, Figs 1-2 and §§1-6 matches a facts entry. The problems are in which population, send, metric, level or label a number is attached to.

PROBLEMS (most severe first)

1. Quote: Table 3 "Terra, report | 9 | 17 | −0.19 [−0.42, +0.03]"; Fig. 2 "report" row; §4.7 "Judged from reports, Terra is 0.19 behind"; abstract "the gap ... reverses sign".
   Problem: Wrong send, and it is not disclosed. These numbers use C8's same-day re-send of Terra's 24 Open-8 calls. Table 1, Fig. 1, §4.3 and the pairs all use the 12 Nov Terra report send. With the 12 Nov send, on the same 30 runs, Terra passes 11/12 and the gap is −0.03, an interval centred near zero. make_fig2_v10.py says "Not plotted: the 12 Nov Terra report sensitivity row". The sign is negative under both sends, but the "−0.19 vs +0.86" contrast depends on which send is used.
   Correct value: state the send, or add the 12 Nov row: 11/12 vs 17/18, −0.03 [−0.19, +0.14]. C8 calls this a sensitivity row; G1 is registered on the same-day send.
   IDs: R8-2 (rows "L0 report (C8 same-day Terra)" and "L0 report (12 Nov Terra)"), C8 (G1; "with 12 Nov Terra verdicts Δ_judge(trap) = −0.028").

2. Quote: §4.5 "The within-run AUROC, pooled over runs with and without SAE tools, did not rise (0.58, then 0.48)."
   Problem: Different pair definition. §3 defines a pair as a right `none` on the null probe and a wrong `none` on the hard probe. C7's pairs use a wrong `none` on any planted probe (146 pairs over 274 runs, TF and TK cells). The values are right but measure something other than the AUROC defined in §3 and used in §4.3.
   Correct value: 0.579 → 0.483 on 146 null-vs-any-planted pairs, 274 runs (214 L0 + Luna 60). Say so, or drop "within-run AUROC" as defined in §3.
   IDs: C7 (cells TF, TK), X7 (pair definition "restricted to hard probes").

3. Quote: §4.5 "It never answers 'fail', even on the 2 failures whose refuting evidence is printed in what it reads."
   Problem: Wrong level. The "2" is U's judge-visible rule, which checks whether the deciding logits and unit are printed in the L2 transcript prompt. The rubric verdicts described here are F1, which reads report + log. Visibility in the F1 material was never checked. Of the 2, only one run is in F2's transcript subset (F2: cannot tell); the other is "not in F2 subset".
   Correct value: "the 2 failures whose refuting evidence is printed in the transcript" (the RESULTS_FOR_PAPER wording). F1, F2 and Sol SF answered "cannot tell" on both.
   IDs: R8-6 (recount 5 → 3 → 2), U (judge-visible = printed in the L2 prompt), F.

4. Quote: §2 "Three held-out traps ... also give 23 scripted cheaters 0."
   Problem: Wrong count. The 23 scripted variants include 2 P0_oracle variants, and the gate is "NAME 0 for every non-oracle policy".
   Correct value: 21 cheater variants (of 23 scripted variants) score NAME 0.
   IDs: E07-40, E07-31, GRADE-VAL.

5. Quote: §4.1 "Over three identical sends on set A, Terra's report-level verdicts agree with each other at κ 0.39."
   Problem: Wrong population. Fleiss κ over three sends (12 Nov L0, 13 Nov L0r, R2) was computed on 132 runs: set A before C6 dropped 2 runs for an http_503 Haiku call. The paper defines set A as 130 runs. The two-send Cohen κ on the 130 runs is 0.34.
   Correct value: 0.39 (Fleiss 0.388, hard probes, 132 runs; same 130 runs plus 2).
   IDs: C17, A-noise, B2.

6. Quote: §2 "Terra names the [main] in 20 of 21 runs, and the smaller GPT-6 Luna in 2 of 21."
   Problem: Mixed registration labels. Terra's 20/21 is the pre-registered primary (H1-3). Luna's 2/21 includes the 4 C14L add-on runs, which are a descriptive secondary table. Luna's registered primary is 2/17 (1/5, 1/5, 0/7).
   Correct value: 2/21 is valid only with "with C14L" stated; otherwise 2/17.
   IDs: C14L, C14b, CORR-1 row 17, sec04 source conflicts item 4.

7. Quote: §4.3 "From the report, Terra reaches 0.70." The abstract's "From the report it also accepts 37 of the 40" and Table 2's Terra report rows depend on the same scores.
   Problem: Unresolved source conflict in the facts file. S0-A and s/README say Terra's 12 Nov report-level slots store no confidence, so its AUROC is "not computable (0 pairs)". X7 and R8 say they used "the stored confidence of the 12 Nov frozen-judge verdicts". The paper's values match X7 and R8.
   Correct value: 0.70 [0.61, 0.81] (X7-X1) and 37/40 (R8-4), conditional on resolving the conflict.
   IDs: X7-X1, S0-A ("Superseded / corrected values": source conflict), R8-2 note.

8. Quote: §3 "The *pairs* are the 40 runs with SAE tools, from all our run sets".
   Problem: Wrong population. The pairs come from three sets only: set A 7, Luna 20, main study 13. Held-out, Open-4 and harder-variant runs are not in them.
   Correct value: "from set A, Luna's set and the main study".
   IDs: X7, R8-4.

9. Quote: §2 "GPT 6.1 Terra passes 24 of 24 runs. With eight it passes 6 of 24" and "Terra passes 23 of 24 runs; without them ... 6".
   Problem: Different metric under the same word. These are NAME counts, which need both the hard probe and the null probe to pass. §§3-4 "passes" (87 of 130, Table 3) are hard-probe passes. For Terra BB-8 the hard-probe count is 8/24 against NAME 6/24. §2's "One hard probe ... decides the score" also does not match NAME.
   Correct value: values are right as NAME. Define "pass", or note that hard-probe passes at BB-8 are 8/24.
   IDs: BLOCK1, E07-17, C19 (L9 table "Terra-BB8 certified 8/24").

10. Quote: §4.5 "it accepts 14 of 19 right `none` where every candidate was tested, against 1 of 106 where some were not."
    Problem: Unlabelled post hoc split. The counts are V6's descriptive round-6 split (all slots, "every candidate isolated and clean"), not part of F's pre-registration; F notes that its own extra counts are post hoc. §3 names only §§4.3, 4.4 and 4.7 as post hoc.
    Correct value: values right (14/19, 1/106); label post hoc.
    IDs: V6, F.

11. Quote: §5 "GPT-4 accepts an incorrect math answer in 14 of 20 cases, and in 3 of 20 when given the reference".
    Problem: The reference in that method is the judge's own independently generated answer, not a ground-truth reference.
    Correct value: 14/20 default, 3/20 "reference-guided" (own answer as reference).
    IDs: R08-19, zheng2023judging.

12. Quote: §1 "A pass mark set on a few cases with known answers"; §7 "Set the mark on a few cases with known answers"; §4.4 "a few cases with known answers".
    Problem: Understated size. Each fold's mark is chosen on the other five items' labelled `none` slots, which is most of the 188 slots, not "a few".
    Correct value: marks chosen on five of six items of 188 labelled slots (136 right, 52 wrong).
    ID: R8-1.

13. Quote: Table 1 cost column, under the caption "Hard probes of set A (130 runs)".
    Problem: The per-call costs are averages over batches that are not set A:
    - Terra report $0.009 = J1-J4, 214 calls ($1.97).
    - Terra transcript $0.08 = C6b, 354 calls including L2r, Luna and main ($29.25).
    - Terra key $0.006 = K, 190 calls, set A + Luna ($1.1387).
    - Sol rows are set A only.
    The caption says "batch spend divided by calls", so the method is stated, but the populations differ by row.
    Correct value: values are right; add the batch population.
    IDs: SPEND-J, K, S.

14. Quote: §2 "the median run in every run set leaves no exact query unused."
    Problem: Scope. X7-X4 covers the set A, Luna and main-study arms only. Separately, 61/64 main-study runs used all 8 queries and every BB-16 run used all 16.
    Correct value: "in every judged run set".
    IDs: X7-X4, MAIN (61/64), BB16.

15. Quote: §2 "a bank of 97 episodes".
    Problem: The bank has 91 distinct episodes after 6 byte-copies are removed.
    Correct value: 97 (91 distinct).
    IDs: ITEMS, PROXY.

16. Quote: reference "Yamada et al. ... Nature 651:914–919" (author order is flagged in the file itself).
    Problem: Author order is unresolved. The bib and Semantic Scholar list Lu first; arXiv v1 lists Yamada first, and the Nature page was never checked.
    Correct value: unresolved.
    ID: lu2026endtoend.

VERIFIED, NO PROBLEM (value, denominator, population, level and judge all match)
- Table 1, all 32 cells:
  - Terra κ and intervals −0.02 [−0.08, 0.04], 0.06 [−0.03, 0.17], 0.24 [0.12, 0.36], 0.81 [0.56, 1.00]; accepted/rejected counts 9/23/24, 7/21/25, 3/17/25, 0/0/12.
  - Sol κ and intervals 0.39 [0.24, 0.54], 0.39 [0.21, 0.57], 0.47 [0.37, 0.57], 0.84 [0.61, 1.00]; counts 6/18/8, 8/16/8, 8/15/4, 0/0/10.
  - Costs: Sol $0.017, $0.16, $0.009.
  - IDs: B3, K, S0-A, S1-A, S2-A, S3-A, S.
- Fig. 1 (script DATA matches Table 1):
  - 53% → 18% and 88% → 65%.
  - "larger share for `none` at every level": Sol 18/26 vs 6/17, 16/26 vs 8/17, 15/26 vs 8/17 all hold.
- Table 2, all rows: R8-1 (folds 75-80; 82-87 with an 84 fold; 61-80; BA intervals).
- Table 3 and Fig. 2 (other than item 1): executed 11/1, +0.86 [+0.67, +1.00]; L1 10/11, +0.22; L2 10/10, +0.28; Sol 11/9, +0.42; C8-method intervals. ID: R8-2.
- Pairs:
  - 40/40 right and 21/40 wrong accepted at L2; L0 37/40 (default verdict); X7-BC/R8-4.
  - AUROC 0.91 [0.79, 1.00] for both judges; 0.54 on 27 pairs; blind 0.53 on 36 pairs; L2r 0.98 → 0.80 on 20 pairs. IDs: X7-X1, R8-3.
  - 32 of 40 pairs from Luna + Haiku (R8-4).
- §4.1, §4.2:
  - No-report prior 31/39 vs 1/39 (C12).
  - Luna trap runs 10/10 → 4/10 and 6/7 → 6/7 (R8-2).
  - Sol 4/87 vs 25; 15/26 vs 17; 0.47 vs 0.24; Luna 0.19 vs 0.26 (S2-A, S2-L).
  - Key step significant on all three sets, other κ steps ≤ 0.29 (E).
- §4.3, §4.4:
  - Confidence-100 slots: 8 of 69; 90-94: 64 of 65 (all 520 slots); 20 of 23 on hard probes (R8-6, V6).
  - 136/52, 25 → 11, 135 → 123 (R8-1).
- §4.5, §4.6, §4.7:
  - 247 → 6 of 263 and 106 → 3 of 148 (C7).
  - 16/130 verdicts, all passes (F).
  - Key: 0 of 43 failures accepted; transcript + key κ 1.00; main study 1 of 6 at L3_2 (S3-A, A, B3).
  - 13 of 36 pairs reordered, exploratory (C19).
- §2:
  - Proxy means 0.362 vs 0.212; builder target 1.8; about 1.7 achieved.
  - [main] at proxy rank 2 on 3/3 shipped traps; ordinary probes 12/12.
  - 1,024 held-out notes; 0.15 bound; 150 calls / 3,000 units / 8 queries.
  - Coverage: 0 fully tested at 8 or 16 queries, 22/41 at 64, 2 of them wrong (X7-X4).
  - 6 cheaters score 0; regrade 100/100.
  - Runner-up tested 11/12 vs 0/18 (DEV-WIDEN).
  - 14 prior environments, 4 with graded nulls (R08-02: Circuit Oracle, ACED, RL auditors, clinical nets).
  - 74% of a probe's margin in the SAE error (R08-14).
- §6: Haiku as judge rejects 82/87 passes at H2 (C6b-H).
- Literature: PaperBench F1 0.83; AstaBench 6 of 11 benchmarks LLM-judged; Krumdick κ 0.78 / 0.30; Sternlicht "a quarter to a third".
- Dates: 3-17 Nov (PRED-MAIN, CHRON).

NUMBERS NOT FOUND AS FACTS ENTRIES
- §4.1 "steps of 0.1–0.2 κ between levels cannot be told from chance": an interpretive range with no entry. The nearest facts are test-retest κ 0.34-0.39 and set A step Δκ 0.08 and 0.18.
- §4.2 "change κ by at most 0.3" and §2 "four" of 14: derived by me from E and R08-02. They are consistent but neither is stated as such in the facts.

AAAI: the header names the AAAI-27 Workshop on Effective and Efficient Evaluation for AI Scientists. The facts file has no AAAI-specific numbers. The workshop-framed claims about reliability, validity, calibration and cost (§1 closing line, §7) rest on the checked numbers above.