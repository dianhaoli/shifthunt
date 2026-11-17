CITATIONS CHECK: /home/user/shifthunt/paper_loop/final/PAPER_V10.md, checked against facts/sec09a–f, facts/sec08_related_comparison.md, citations/references_v9.bib and citations/judge_lit.bib. No files were edited.

What passed:
- Cross-check: V10 has 21 in-text cited works, and all 21 have a reference entry. The list has 24 entries, and every one is cited in the text. Of the 24, 11 are in bib Part 1 (bowyer, bragg, chen, engels, kabir, lieberum, marks2025b, sheshadri, starace, zhong, zhu). 8 are in bib Part 2 (krumdick, jung, zheng, marks2025a, rosu, rottshaham, lu2026endtoend, schwettmann). 2 are in judge_lit (khalifa, sternlicht). 3 have no bib entry (Chow, Geifman, Tiwari).
- Norman et al. (withdrawn) is absent. ACED is cited as arXiv, with no NeurIPS. Sahoo and SAEBench are not cited in the body, so the "86% is not a flip rate" and "seven architectures" checks do not apply.
- Numbers that match their cards: PaperBench F1 0.83; AstaBench 6 of 11 benchmarks judged by an LLM; Tiwari 74%; Zheng 14/20 and 3/20; Krumdick κ 0.78/0.30; Sternlicht "a quarter to a third"; Rosu's judge is told the target is clean; ACED's empty sets are scored by exact match; WebArena's "N/A" judge.
- The 2025a/2025b labels match how BibTeX will sort them.
- The "14 prior environments, four grade a 'nothing found'" claim matches table R08-02.

Fixes:

1. Yamada vs Lu author order is unresolved and the sources disagree. The text and reference list say "Yamada et al. 2026". The bib key lu2026endtoend lists Chris Lu first (the Nature order according to Semantic Scholar). arXiv v1 lists Yamada first. Check this against nature.com, then make the bib author field, the in-text name (§1 and §5) and the reference entry agree. Also delete the leftover `<!-- check Nature author order -->` from the reference list.

2. AAAI format: the reference list is not in AAAI style. It uses "Starace et al." inside the references and puts the year at the end. AAAI wants full author lists in the form "Last, F.; Last, F.; and Last, F. Year. Title. In Venue, pages." The supplement (PAPER_V10_APPENDIX.md, lines 970–986) already mostly follows this. Generate both lists from the bib with the AAAI author-kit .bst so the paper and supplement match. Also expand the "et al." entries in the supplement (Karvonen, Lieberum, Marks 2025b, Sheshadri).

3. Missing bib entries: Chow 1970, Geifman and El-Yaniv 2017 and Tiwari et al. 2026 are cited but are in neither bib file. Add them from their sec09f cards:
   - chow1970optimum: C.-K. Chow, IEEE Trans. Inf. Theory 16:41–46, DOI 10.1109/TIT.1970.1054406. The issue number is unverified, so leave it out.
   - geifman2017selective: NeurIPS 2017, arXiv 1705.08500.
   - tiwari2026decodability: all six authors (Tiwari, Davis, Sinha, Weaver, Shah, Chaudhary), arXiv 2609.18080. The workshop venue has not been checked against a COLM page, so either keep "COLM 2026 Workshop on Agent Behavior" marked as from the PDF header or cite it as arXiv.
   - The supplement cites Nusrat and Nusrat 2026 (arXiv 2611.05341), which is also in no bib. Add it with the given names Humza and Omar.

4. ACED title: the reference list (and the supplement) give "ACED: Evaluating how LLM agents...", which is the PDF title. The bib's chen2026 entry uses the arXiv title "ACED-Bench: ...". Pick one and use it everywhere. Since the paper cites the arXiv version, "ACED-Bench" is the consistent choice, keeping "ACED" as the short name in the text.

5. §2 line 46 mislabels ACED: "agentic interpretability benchmarks (FIND, MAIA, Pando, ACED)". ACED is a benchmark of causal experiments on hidden SCMs/PGMs, not an interpretability benchmark, and MAIA is an agent, not a benchmark. Suggested: "agentic interpretability benchmarks and agents (FIND, MAIA, Pando) and budgeted causal-experiment benchmarks (ACED)".

6. §5, Zheng et al. 2023: "in 3 of 20 when given the reference" overstates the setup. In MT-Bench's reference-guided method, the reference is the judge's own separately generated answer (sec09c, §3.4), not a ground-truth key. Write "…when first shown its own separately generated answer as a reference". The count is 20 judgments over 10 questions in both positions. Note that sec08 R08-19's "(reference answer)" is the looser wording; sec09c comes from the full-text read.

7. §5, Sternlicht et al. 2026: "flip a quarter to a third of system comparisons" misstates the unit. The card says the prompt flips that share of pairwise verdicts on average when two ideation systems are compared (154 pairs; 13.0–56.5% per judge). Suggested: "prompt changes alone flip a quarter to a third of pairwise verdicts between two ideation systems, on average".

8. §5, Khalifa et al. 2026: "one credits an agent that reports finding nothing" rests on a single qualitative case (§G.3, Gemini-2.5-Flash), not a measured rate. Say "in one qualitative case". The "fabricated progress" claim is supported (+17.4 FPR points on average over nine judges).

9. §5, Krumdick et al. 2026: "a judge's κ is 0.78 … and 0.30" refers to one specific judge. Say "GPT-4o's κ with expert labels (pairwise, no reference) is 0.78 … and 0.30 …".

10. §3 line 67, Bowyer et al. 2025: "With six items, normal approximations fail" cites the paper for a case it does not test. It simulates N = 3, 10, 30 and 100, and even at N = 100 CLT intervals cover only 92.5%. Suggested: "With few items, CLT intervals under-cover (Bowyer et al. 2025 show this from N = 3 to 100); we have six."

11. §2 line 40, Tiwari et al. 2026: the 74% is correct, but it comes from an appendix boundary case (App. A.2, Table 7): a Qwen3-8B probe with a Qwen-Scope SAE that "did not pass the SAE-substrate verification". It is not the main Gemma study. Add a qualifier, such as "one released probe (Qwen3-8B, an appendix case)", so it does not read as a Gemma Scope result.

12. §5, "validate their judges against human labels, expert rankings or past review decisions": for PaperBench, the card says only that the judge is scored on a separate judge benchmark (JudgeEval). It does not say the labels are human. Either write "a judge benchmark" for PaperBench, or confirm that JudgeEval is human-graded and add that to the card.

13. Clean up the bib files:
   - references_v9.bib still describes itself as the "bibliography for PAPER_V9" and lists "the 18 references V9 cites". Build a references_v10.bib holding exactly the 24 cited keys, plus the supplement's Bricken, Cywiński, Karvonen, Tan and Nusrat. Move khalifa2026gaming and sternlicht2026oldideas into it from judge_lit.bib.
   - Remove norman2026reliability (withdrawn) from judge_lit.bib so it cannot be cited by accident.
   - If sahoo2025reject or karvonen2025saebench are ever cited, describe 86.26% as an increase in acceptance rate in points (the critical flip rate is about 14%), and use "seven architectures" for SAEBench.

14. Optional extra detail:
   - Lieberum et al.: add pp. 278–300.
   - Starace et al.: add PMLR 267:56843–56873.
   - Bragg et al.: ICLR 2026 Oral.
   - Zhu et al.: the NeurIPS proceedings title says "in building" (arXiv says "for"), which V10 already uses. Its author list and pages in the proceedings are still unchecked.

Files: /home/user/shifthunt/paper_loop/final/PAPER_V10.md, /home/user/shifthunt/paper_loop/final/PAPER_V10_APPENDIX.md, /home/user/shifthunt/paper_loop/citations/references_v9.bib, /home/user/shifthunt/paper_loop/citations/judge_lit.bib