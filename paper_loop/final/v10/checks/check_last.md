Independent last check of /home/user/shifthunt/paper_loop/final/PAPER_V10.md against check_final_body.md items 1–17 and the CHANGELOG_V10.md "Final check" section. I made no edits.

| # | Status | Quote from PAPER_V10.md |
|---|---|---|
| 1 | FIXED (reworded; the "a cap would change behaviour" clause was dropped because no fact supports it, which is OK) | §2: "Tokens were not capped, and matching them across harnesses was not feasible: the two count and cache tokens differently. In the 64-run study of four agents and in set A's runs at 8 and 64 queries (§3), but not in Luna's, we checked … about 268k tokens for GPT (475k window) … Supplement M gives … a post hoc token-cap sensitivity analysis." Supplement M has this analysis (+0.04 at 41k; +0.28 to +0.34 for MAIN-TOK). |
| 2 | FIXED | §4.2 heading: "For Terra, reading more helps against wrong findings more than wrong absences"; lead: "(Fig. 1; descriptive; Sol does not show it)". Sol goes 6→8 of 17 and 18→15 of 26, which matches Table 1. |
| 3 | FIXED | §3: "The tests between levels (§4.2) followed a fixed plan but an unhashed script, so we report them as descriptive. Post hoc … are the report-to-transcript tests in §4.2, …". This matches fact E ("script … not hashed"; L0→L2 rows "added after the plan"). |
| 4 | FIXED | §4.4: "One caveat: the confidence separates a [null] probe from a planted one partly by which probe is being judged, not only by the evidence for the answer." This matches the R8-1 printed caveat. |
| 5 | FIXED (resolved by citing the arXiv version and its author order; "Yamada et al." kept, which is OK) | Refs: "Yamada et al. Towards end-to-end automation of AI research. arXiv 2606.15497v1, 2026 (arXiv version and author order; also published in *Nature* 651:914–919)." The HTML comment is gone. arXiv v1 does list Yamada first. |
| 6 | FIXED | "Tiwari et al. … COLM 2026 Workshop on Agent Behavior (arXiv 2609.18080)." |
| 7 | FIXED | §3: "As a check, we also add the key to the transcript." §4.6: "With the transcript and the key, Terra's κ on set A is 1.00; in the 64-run study, it still accepted 1 of 6 wrong cues". |
| 8 | FIXED (reworded) | §2: "A first weight edit moves the [main]'s effect into the SAE's error term; the [main]'s true dependence stays at 0.35–0.49 on the shipped traps. A second edit adds a direction that the SAE reads as the [decoy] and leaves every true dependence unchanged." |
| 9 | FIXED | §7: "from the report + log, over all set A probes, its confidence-100 verdicts are right on only 8 of 69 (12%)". I checked this against the R8-6/V6 curve: 69 × 0.1159 = 8. |
| 10 | FIXED | §7: "when traps mislead the agent, the judge still accepts 16 of Luna's 17 resulting wrong answers from reports, and 10 (Terra) and 9 (Sol) from transcripts". R8-2 gives 6/7+10/10, 6/7+4/10 and 5/7+4/10. |
| 11 | FIXED | Table 1 row: "rule: credit any named answer \| answer only \| 0.67 [0.48, 0.85] \| 17 \| 0 \| 0 \| $0". §3 points to it: "reaches 0.67 on set A (Table 1)". The interval matches B3/J2. |
| 12 | FIXED | Abstract: "(AUROC 0.91; post hoc)" and "cuts those accepted from 25 to 11 (post hoc)". |
| 13 | FIXED | §1: "Two LLM judges with frozen prompts then read the runs at increasing depth". |
| 14 | FIXED | §1: "It validates the judge against expert rankings on one of them, ScholarQA-CS2, with system-level Kendall τ 0.467." |
| 15 | FIXED | §5: "with 68.1% instance-level agreement on instances with a clear winner." |
| 16 | FIXED | §2: "ShiftHunt builds on spurious-feature removal (SHIFT; Marks et al. 2025a)". |
| 17 | REJECTED-OK (informational; nothing to fix in the text) | Length is unchanged in practice. By `wc -w`, title through conclusion is 5,200 words (the changelog says 5,201) and the abstract is 197. The page count is still unverified until the paper is compiled. |

**Other scans of the body**
- **Numbers:** every number token in the body (title to conclusion) occurs in FACTS_ONLY.md. I checked about 40 claims in context and all match the facts:
  - 31/39 vs 1/39; Fleiss κ 0.39 on 132 runs; 0.98→0.80 on 20 pairs; 0.53 on 36 blind pairs.
  - 64 of 65 at confidence 90–94; 247→6 of 263 and 106→3 of 148; AUROC 0.58→0.48.
  - Rubric: 16/130 verdicts, 14 of 19, 1 of 106; 22 of 41.
  - 0.362 vs 0.212 and the 1.8 target; 1,024 notes; 100 of 100 regrades; 21 cheater variants; 97 episodes (91 distinct).
  - 14 prior environments, 4 of which grade a null; Table 2 matches R8-1; Table 3 matches R8-2, including the first send at −0.03 [−0.19, +0.14].
  - τ_b 0.23 [−0.09, 0.46] and 13 of 36 pairs; $29.25 over 354 calls.
  - Cited papers: 74% on the Qwen3-8B probe; F1 0.83; 14/20 vs 3/20; κ 0.78 vs 0.30; Krumdick and Sternlicht figures.
  - The ladder McNemar claims: key step significant on all three sets; other steps change κ by at most 0.29; Luna p = 0.004 and 2e-5.
  - "3 to 17 November" holds: the main study was registered on 3–4 Nov.
- **Ids and names:** no probe or episode ids, and none of the 16 shipped property names (detectors.py), appear in the body or figures.
- **Banned words:** "usually" does not occur. "free" occurs only in the Krumdick title "No free labels". "pre-registered" does not occur. "pre-specified" appears twice (§3 and the Table 3 caption, where C8 was pre-registered); both uses are correct.
- **Tables:** column counts are consistent in all three (7, 5 and 4), and each table has a blank line before it.
- **Figures:** the text references fig/fig1_v10.png and fig/fig2_v10.png, and both files exist. Every value in Fig. 1 (23/26 … 0/17) matches Table 1, and every value in Fig. 2 (+0.86, −0.19, +0.22, +0.28, +0.42) matches Table 3.
- **Citations:** all 24 in-text citations are in the reference list, and all 24 references are cited. Years agree.
- **Appendix consistency:** I spot-checked 18 shared numbers against PAPER_V10_APPENDIX.md and all agree: 268k/475k/479k, 31 of 39, κ 0.39 on 132 runs, 37/40, AUROC 0.91 [0.79, 1.00], 0.98→0.80, 8 of 69 and 64 of 65, 11/52 and 123/136 with BA 0.85 [0.77, 0.90] at marks 75–80, $29.25 over 354 calls and the four cost-per-call values, 13 of 36 and τ_b 0.23, the Table 3 gaps including −0.03 [−0.19, +0.14], 22 of 41, 0.362/0.212, 14 of 19 and 1 of 106, the rule's 0.67, 23/24 and 20/21, 0.53 on 36 pairs, and Luna McNemar 0.004 and 2e-5. Table D1 has 14 prior rows. One difference is explained in the appendix: the body gives Luna's held-out result as 2 of 21, and appendix Table M shows 2/17 primary, with the note "2 of 21 with the 4 extra runs".

**Remaining problems (all minor; none is blocking)**
1. §4.3 reports a level that §3 never defines: "hiding the SAE outputs lowers the AUROC from 0.98 to 0.80". §3 still says "one of five views" and lists only the key-with-transcript check. This is the same kind of gap as item 7. Suggested fix: "As checks, we also add the key to the transcript and hide the SAE outputs in it."
2. The new §4.4 caveat writes "a [null] probe", but the rest of the body writes "null probe" without brackets and brackets only [main] and [decoy]. Suggested fix: "a null probe".
3. The parenthetical in the Yamada reference, "(arXiv version and author order; …)", reads like a drafting note. Also, the facts still record the Nature author order as unresolved. Citing arXiv v1 is defensible, but the parenthetical could just read "arXiv 2606.15497v1, 2026; also in *Nature* 651:914–919".
4. Item 17: the 8-page limit has not been checked by compiling; the body is 5,200 words.
5. Outside the body, for information only: the appendix line 175 heading "The SAE tools are plentiful, not free." uses "free" for tools in negated form. The other appendix uses ("Free." in the quoted task prompt, "free text", "judge-free") are legitimate.