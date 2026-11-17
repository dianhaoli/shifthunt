# Citation gaps: reliability and validity of LLM-as-a-judge (for PAPER_V9)

Scope: agreement with humans; self-preference; position and verbosity bias; test-retest consistency; abstention and selective prediction for judges; judges in agent and scientific-discovery benchmarks; prediction-powered inference (PPI) and statistically valid use of judge labels.

Checked against V9's reference list (18 entries, lines 196-215). None of the papers below is in it. None overlaps the nine papers already collected in `judge_lit.bib` / `JUDGE_LITERATURE.md` (Khalifa, Sternlicht, Zhou, Wahi, Zhao, Brown, Norman, Bao, Sahoo), which are also not yet in V9. One of them, Angelopoulos et al. 2023 (PPI), was listed in V8, V7, V5, V4_user and BEST but dropped from V9 (see `00_collected.md`).

How each one was verified: the arXiv API (`export.arxiv.org/api/query?id_list=...`) gave titles, authors, dates and comments. Semantic Scholar (`/graph/v1/paper/arXiv:<id>`) gave venues, DOIs and citation counts. alphaXiv `answer_pdf_queries` read the full text of Krumdick, Dorner, Jung, Zhuge and Zheng to check the claims we would cite. WebSearch confirmed the venues against proceedings pages (ICLR 2025 proceedings and virtual pages, PMLR v267, NeurIPS 2024 proceedings, the ICML 2026 virtual page, and the MPI-IS ICLR 2025 oral notice). Direct OpenReview access was not attempted, because the API sits behind a bot challenge. Venues were confirmed through the proceedings pages instead.

## Ranked candidates

| # | Paper | Venue (verified) | Priority | Where in V9 |
|---|---|---|---|---|
| 1 | Krumdick et al., No Free Labels (2503.05061) | COLM 2026 (v4 PDF header) | must | §4.4 positive control; §7 |
| 2 | Jung, Brahman, Choi, Trust or Escalate (2407.18370) | ICLR 2025 (oral) | must | §4.3 abstaining judge; §7 |
| 3 | Zheng et al., Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (2306.05685) | NeurIPS 2023 Datasets & Benchmarks | must | §7 opening; §4.4 key control |
| 4 | Dorner, Nastl, Hardt, LLM as Judge won't beat twice the data (2410.13341) | ICLR 2025 (oral) | should | §4.4 "errors would hide the agent comparison"; §10 |
| 5 | Panickssery, Bowman, Feng, LLM Evaluators Recognize and Favor Their Own Generations (2404.13076) | NeurIPS 2024 | should | §8 Judge bullet |
| 6 | Zhuge et al., Agent-as-a-Judge (2410.10934) | ICML 2025, PMLR 267:80569-80611 | should | §7 Judges for research agents; §8 untested judge with its own queries |
| 7 | Angelopoulos et al., Prediction-Powered Inference (2301.09633) | Science 382(6671):669-674, 2023 | should | §4.4 consequences, paired with Dorner |
| 8 | Lee et al., How to Correctly Report LLM-as-a-Judge Evaluations (2511.21140) | ICML 2026 | optional | §3 Statistics, at balanced accuracy |

---

### 1. Krumdick et al. 2026, No Free Labels (must)
- **Finding (checked in the full text):** The authors collected expert correctness labels for 1,200 responses. Without a correct reference, judges agree with the experts mainly on questions they can answer themselves. GPT-4o's pairwise κ is 0.78 with no reference on questions it answered correctly, against 0.30 on questions it got wrong. Using its own answer as the reference, κ falls from 0.86 to 0.16. A human-written reference restores agreement (κ 0.83 on the questions it got wrong). Wrong references are worse than none, and a jury of five judges does not escape the problem.
- **Why it matters for V9:** It is the closest published analogue to V9's positive control. The judge grades nearly perfectly with a one-line key and near chance without one, because without the key it cannot solve the task itself: the answer needs executed queries. It also supports §8's point that commit-first or a judge with its own answer would not transfer, since self-generated references fail exactly where the judge cannot answer.
- **Where:** §4.4, after "It is a positive control: a new finding has no key." Optionally also §7, "Judges for research agents".
- **Suggested sentence (22 words):** "Likewise, judges agree with experts mainly where they can answer the question themselves or are given a correct reference (Krumdick et al. 2026)."

```bibtex
@inproceedings{krumdick2026nofreelabels,
  title         = {No Free Labels: Limitations of {LLM}-as-a-Judge Without Human Grounding},
  author        = {Krumdick, Michael and Lovering, Charles and Reddy, Varshini and Ebner, Seth and Tanner, Chris},
  booktitle     = {Conference on Language Modeling (COLM)},
  year          = {2026},
  eprint        = {2503.05061},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}
```
V9 style: `- Krumdick, Lovering, Reddy, Ebner, Tanner. No free labels: limitations of LLM-as-a-judge without human grounding. COLM 2026 (arXiv 2503.05061).`
Note: Semantic Scholar still lists it as arXiv only. The venue comes from the v4 PDF header ("Published as a conference paper at COLM 2026", arXiv v4, 28 Sep 2026).

### 2. Jung, Brahman, Choi 2025, Trust or Escalate (must)
- **Finding (checked):** In selective evaluation, the judge abstains unless its confidence clears a threshold. The threshold is calibrated by fixed-sequence testing on a small human-labelled set. The guarantee is that P(agree with humans | judge answers) ≥ 1−α, with probability 1−δ. On ChatArena it guarantees over 80% agreement at about 80% coverage, where GPT-4 without abstention stays below 80%. Coverage collapses as the target rises: 28.9% coverage at a 95% target on TL;DR.
- **Why it matters for V9:** It is the canonical abstaining judge. V9's abstaining judge shows the failure mode the guarantee hides: precision on the verdicts it gives (every one a correct pass) bought by answering 16 of 130 slots, and never answering "fail". Dorner et al. (§5 of their paper) also note that abstention correlated with the evaluated model's performance can bias comparisons, which fits V9's result exactly.
- **Where:** §4.3, after "the instructions remove the false credit, but not the gap to a script." Or §7, as a new sentence on abstaining judges.
- **Suggested sentence (24 words):** "Selective judges can guarantee human agreement on the items they answer (Jung et al. 2025); ours answers 16 of 130 slots, and never 'fail'."

```bibtex
@inproceedings{jung2025trust,
  title         = {Trust or Escalate: {LLM} Judges with Provable Guarantees for Human Agreement},
  author        = {Jung, Jaehun and Brahman, Faeze and Choi, Yejin},
  booktitle     = {International Conference on Learning Representations (ICLR)},
  year          = {2025},
  eprint        = {2407.18370},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```
V9 style: `- Jung, Brahman, Choi. Trust or escalate: LLM judges with provable guarantees for human agreement. ICLR 2025 (arXiv 2407.18370).`

### 3. Zheng et al. 2023, Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (must)
- **Finding (checked):** This is the founding study of LLM-as-a-judge. GPT-4 reaches over 80% agreement with human preferences, but judges show position, verbosity and self-enhancement bias. They also grade math and reasoning poorly when they cannot solve the problem, and are sometimes misled even when they can. In Table 4, GPT-4 calls an incorrect math answer correct 14/20 times with the default prompt, 6/20 with chain of thought and 3/20 with a reference answer. Few-shot prompting raises position consistency, but "high consistency may not imply high accuracy".
- **Why it matters for V9:** V9 cites no general LLM-as-a-judge source, and reviewers at an evaluation workshop will expect this one. Three of its findings line up with V9's: the reference-guided fix matches V9's key control, "consistency does not imply accuracy" matches §4.4 (self-agreement κ 0.39 against κ −0.006 with the grade), and the >80% human-agreement result shows why agreement on preference tasks does not carry over to correctness of absence claims.
- **Where:** §7, as the opening of "Judges for research agents" (or a new short "LLM judges" lead sentence). Optionally §4.4, at "A consistency check would not reveal the problem."
- **Suggested sentence (24 words):** "LLM judges match human preferences well yet misgrade math they cannot solve; a reference answer cuts such failures from 14 to 3 of 20 (Zheng et al. 2023)."

```bibtex
@inproceedings{zheng2023judging,
  title         = {Judging {LLM}-as-a-Judge with {MT-Bench} and {Chatbot Arena}},
  author        = {Zheng, Lianmin and Chiang, Wei-Lin and Sheng, Ying and Zhuang, Siyuan and Wu, Zhanghao and Zhuang, Yonghao and Lin, Zi and Li, Zhuohan and Li, Dacheng and Xing, Eric P. and Zhang, Hao and Gonzalez, Joseph E. and Stoica, Ion},
  booktitle     = {Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track},
  year          = {2023},
  eprint        = {2306.05685},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}
```
V9 style: `- Zheng et al. Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. NeurIPS 2023 Datasets and Benchmarks (arXiv 2306.05685).`

### 4. Dorner, Nastl, Hardt 2025, LLM as Judge won't beat twice the data (should)
- **Finding (checked):** When the judge is no more accurate than the evaluated model, no unbiased debiasing method (PPI included) can cut the required ground-truth labels by more than half (Theorem 6, Corollary 7). High agreement does not guarantee useful correlation. In their Appendix A.1 they bound the correlation by balanced agreement: it vanishes as BA approaches 0.5. Their Figure 1 shows judges with 79-84% accuracy badly reordering model rankings.
- **Why it matters for V9:** It is the theoretical counterpart of §4.4's "the judge's errors would hide the study's own agent comparison", and it covers a case close to V9's, since the judge model (Terra) is also the strongest agent under test. Their Theorem 11 ties sample efficiency to balanced accuracy, the metric V9 reports. With report-level BA of 0.49-0.51, a few executed grades could not rescue judge labels.
- **Where:** §4.4, after "The judge also reverses 13 of 36 pairs …". Or §10, as support for grading negative verdicts by execution.
- **Suggested sentence (22 words):** "When the judge is no more accurate than the agents it grades, no debiasing can halve the number of executed grades needed (Dorner et al. 2025)."

```bibtex
@inproceedings{dorner2025limits,
  title         = {Limits to Scalable Evaluation at the Frontier: {LLM} as Judge Won't Beat Twice the Data},
  author        = {Dorner, Florian E. and Nastl, Vivian Y. and Hardt, Moritz},
  booktitle     = {International Conference on Learning Representations (ICLR)},
  year          = {2025},
  eprint        = {2410.13341},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```
V9 style: `- Dorner, Nastl, Hardt. Limits to scalable evaluation at the frontier: LLM as judge won't beat twice the data. ICLR 2025 (arXiv 2410.13341).`

### 5. Panickssery, Bowman, Feng 2024, LLM Evaluators Recognize and Favor Their Own Generations (should)
- **Finding (verified via S2, NeurIPS proceedings page):** GPT-4 and Llama 2 can tell their own text from others'. After fine-tuning, the strength of self-recognition correlates linearly with self-preference, and controlled experiments suggest a causal link.
- **Why it matters for V9:** §8 says "the judge model is also an agent under test", since Terra judges Terra's runs. Self-preference is the named risk, and it predicts the direction of V9's error: Terra credits failures, while Haiku as judge blames passes. Krumdick et al. (#1) also find that self-generated references raise the false-positive rate on a judge's own responses. V9 should cite this as a confound, not as an explanation.
- **Where:** §8, Judge bullet, after "the judge model is also an agent under test."
- **Suggested sentence (19 words):** "LLM evaluators recognise and favour their own generations (Panickssery et al. 2024), which may inflate Terra's credit on Terra's runs."

```bibtex
@inproceedings{panickssery2024llm,
  title         = {{LLM} Evaluators Recognize and Favor Their Own Generations},
  author        = {Panickssery, Arjun and Bowman, Samuel R. and Feng, Shi},
  booktitle     = {Advances in Neural Information Processing Systems 37 (NeurIPS 2024)},
  year          = {2024},
  eprint        = {2404.13076},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}
```
V9 style: `- Panickssery, Bowman, Feng. LLM evaluators recognize and favor their own generations. NeurIPS 2024 (arXiv 2404.13076).`

### 6. Zhuge et al. 2025, Agent-as-a-Judge (should)
- **Finding (checked):** On DevAI (55 AI-development tasks, 365 requirements), an agentic judge that reads the workspace and locates files agrees with the human consensus 90% of the time, against about 60-70% for LLM-as-a-Judge. The authors also warn that alignment rate misleads on class-imbalanced judging and use PR curves instead.
- **Why it matters for V9:** It is the main "judge for agents" reference and the natural answer to V9's ladder. More access (workspace, trajectories) helps their judge, as the full transcript helps V9's. V9's point is different: for an absence claim the missing evidence is a test nobody ran, so reading more cannot supply it. It also motivates §8's untested "judge with its own exact queries". The class-imbalance warning supports V9's choice of balanced accuracy.
- **Where:** §7, "Judges for research agents", after the PaperBench and MLE-bench sentence. Optionally §8, Judge bullet.
- **Suggested sentence (25 words):** "Agent-as-a-Judge inspects workspaces and nears human agreement on code tasks (Zhuge et al. 2025); for a 'nothing found', the needed evidence was never produced."

```bibtex
@inproceedings{zhuge2025agentasajudge,
  title         = {Agent-as-a-Judge: Evaluate Agents with Agents},
  author        = {Zhuge, Mingchen and Zhao, Changsheng and Ashley, Dylan R. and Wang, Wenyi and Khizbullin, Dmitrii and Xiong, Yunyang and Liu, Zechun and Chang, Ernie and Krishnamoorthi, Raghuraman and Tian, Yuandong and Shi, Yangyang and Chandra, Vikas and Schmidhuber, J{\"u}rgen},
  booktitle     = {Proceedings of the 42nd International Conference on Machine Learning (ICML)},
  series        = {Proceedings of Machine Learning Research},
  volume        = {267},
  pages         = {80569--80611},
  year          = {2025},
  eprint        = {2410.10934},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI}
}
```
V9 style: `- Zhuge et al. Agent-as-a-judge: evaluate agents with agents. ICML 2025 (arXiv 2410.10934).`

### 7. Angelopoulos et al. 2023, Prediction-Powered Inference (should)
- **Finding (verified: arXiv, S2, journal record):** PPI combines a small gold-labelled sample with many model predictions to give valid confidence intervals, whatever the predictor's quality.
- **Why it matters for V9:** It is the standard statistically valid way to use judge labels, and earlier versions of the paper cited it. V9's numbers show why it does not help here: the judge's labels barely correlate with the executed grade (κ ≈ 0), so PPI would gain almost nothing (see #4), and execution stays necessary. Cite it together with Dorner.
- **Where:** §4.4, with #4. Or §10, at "We suggest grading negative verdicts by execution …".
- **Suggested sentence (23 words):** "Prediction-powered inference can debias judge-based comparisons using a few executed grades (Angelopoulos et al. 2023), but with report-level κ near zero, little is gained."

```bibtex
@article{angelopoulos2023ppi,
  title   = {Prediction-Powered Inference},
  author  = {Angelopoulos, Anastasios N. and Bates, Stephen and Fannjiang, Clara and Jordan, Michael I. and Zrnic, Tijana},
  journal = {Science},
  volume  = {382},
  number  = {6671},
  pages   = {669--674},
  year    = {2023},
  doi     = {10.1126/science.adi6000},
  eprint  = {2301.09633},
  archivePrefix = {arXiv}
}
```
V9 style (as in V8): `- Angelopoulos, Bates, Fannjiang, Jordan, Zrnic. Prediction-powered inference. *Science* 382, 2023 (arXiv 2301.09633).`

### 8. Lee et al. 2026, How to Correctly Report LLM-as-a-Judge Evaluations (optional)
- **Finding (verified: arXiv journal_ref, ICML 2026 virtual page):** A judge's imperfect sensitivity and specificity bias the raw judged accuracy. A judge that calls everything correct gives 1 regardless of the truth. A human-labelled calibration set gives a plug-in correction and confidence intervals.
- **Why it matters for V9:** "Credits failures" and "blames passes" are one minus specificity and one minus sensitivity in their terms. This supports V9's use of balanced accuracy rather than raw agreement, and it explains why a lenient judge inflates pass rates (§4.4: −0.19 judged against +0.86 executed).
- **Where:** §3, Statistics, after "we add balanced accuracy, the mean of the pass-credit and failure-rejection rates."
- **Suggested sentence (20 words):** "A judge's sensitivity and specificity bias raw judged pass rates, and only labelled calibration data can correct them (Lee et al. 2026)."

```bibtex
@inproceedings{lee2026report,
  title         = {How to Correctly Report {LLM}-as-a-Judge Evaluations},
  author        = {Lee, Chungpa and Zeng, Thomas and Jeong, Jongwon and Sohn, Jy-yong and Lee, Kangwook},
  booktitle     = {International Conference on Machine Learning (ICML)},
  year          = {2026},
  eprint        = {2511.21140},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```
V9 style: `- Lee, Zeng, Jeong, Sohn, Lee. How to correctly report LLM-as-a-judge evaluations. ICML 2026 (arXiv 2511.21140).`
A search summary gave the PMLR volume as 306. I did not confirm that on a PMLR page, so it is left out of the BibTeX.

---

## Considered, not recommended (or verified only in part)
- **Thakur et al., Judging the Judges (2406.12624).** GEM workshop at ACL 2025, per the arXiv journal_ref. Finds that percent agreement hides judge differences that Cohen's κ reveals. It could back V9's use of κ. It is close to Zheng (#3) and weaker on venue.
- **Schroeder and Wood-Doughty, Can You Trust LLM Judgments? (2412.12509).** Test-retest reliability (McDonald's ω) of LLM judges. arXiv only, per S2. A possible optional citation at §4.4's "consistent with itself" sentence, but #3 already makes that point at a stronger venue.
- **Bavaresco et al., LLMs instead of Human Judges? (2406.18403).** ACL 2025 per the arXiv comment. Judges' agreement with humans varies widely across 20 NLP tasks. General background, less specific than #1.
- **Boyeau et al., AutoEval Done Right (2403.07008).** PPI for model evaluation. Semantic Scholar gives ICML; not independently confirmed. It could replace #7 if a more ML-evaluation-specific PPI citation is wanted.
- **Recent 2026 work on selective agent-judge evaluation, found with alphaXiv:** *Certified Selective Automation of LLM Agent Evaluation* (2609.34320) and *Judge, Retrieve, or Abstain* (2608.17994). Both are directly on topic for §4.3, but they are new preprints with few citations. I did not verify their venues: neither the arXiv API nor a venue check was run. **NOT VERIFIED.** Recheck them before citing.
- Wang et al., *Large Language Models are not Fair Evaluators* (2305.17926), on position bias. Not verified in this pass. #3 already covers position bias.

## Notes for the author
- Adding #1-#3 and #5 needs at most four sentences. §7 can take #3 and #6 without growing much if the lead sentence absorbs them.
- If the earlier judge_lit set (Khalifa, Zhao, etc.) also goes into §7, put #3 first as the general source, then the adversarial papers, then #1 and #2 as the key-control and abstention anchors.
- Keep the self-preference sentence (#5) in §8 as a confound. V9 has no experiment that isolates it.
