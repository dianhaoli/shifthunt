# Citation verification, batch 4 (checked 2026-11-17)

Sources used: arXiv API (export.arxiv.org; the first call returned 429, the retry worked), Semantic Scholar API, alphaXiv full text (answer_pdf_queries), WebSearch. In this session, neurips.cc and openreview.net do not resolve. Their pages are known only from WebSearch results and were not opened.

None of these four appears in the V9 reference list or the V9 text, so there are no V9 sentences to check. Earlier drafts (V7, V8 and BEST in MASTER_DOC.md) made claims with them. Those claims are checked below in case they go back into V9.

## gxchen2025 -- corrected (full title, author spelling "GX-Chen")
- Anthony GX-Chen, Dongyan Lin, Mandana Samiei, Doina Precup, Blake A. Richards, Rob Fergus, Kenneth Marino. "Language Agents Mirror Human Causal Reasoning Biases. How Can We Help Them Think Like Scientists?" COLM 2025. arXiv 2505.09614 (v3, 5 Oct 2025; DOI 10.48550/arXiv.2505.09614).
- Venue evidence: the arXiv comment reads "Conference on Language Modelling (COLM) 2025, Camera Ready", and every PDF page header reads "Published as a conference paper at COLM 2025". WebSearch returns the OpenReview forum https://openreview.net/forum?id=LKINTp7Gdo and the COLM 2025 accepted-papers page (https://colmweb.org/2025/AcceptedPapers.html), but I could not open either one.
- Fixes: the title has a second sentence, "How Can We Help Them Think Like Scientists?". The first author's surname is written "GX-Chen".
- Earlier-draft claims (not in V9):
  - "agents under-hypothesize conjunctive causes": MOSTLY SUPPORTED. The abstract says LMs "reliably infer the common, intuitive disjunctive causal relationships but systematically struggle with the unusual, yet equally (or sometimes even more) evidenced conjunctive ones". The paper calls this a "disjunctive bias" and finds it across model families, sizes and prompting strategies. Sec. 4.1 / Fig. 6 shows LMs favouring disjunctive inferences like adults, not like 4-year-olds. The fix the paper proposes is to sample hypotheses under a flatter prior and eliminate them (contribution 4). That makes "under-weighted in the prior" a fair reading. Strictly, though, the paper measures inference and exploration, not hypothesis listing. Safer wording: "language agents show a disjunctive bias, failing to infer conjunctive causes even when the evidence supports them (GX-Chen et al. 2025)".
  - "the conjunction is thinkable but ranked too low": this is our own interpretation, not the paper's finding. Phrase it as "consistent with".
```bibtex
@inproceedings{gxchen2025,
  author    = {GX-Chen, Anthony and Lin, Dongyan and Samiei, Mandana and Precup, Doina and Richards, Blake A. and Fergus, Rob and Marino, Kenneth},
  title     = {Language Agents Mirror Human Causal Reasoning Biases. {H}ow Can We Help Them Think Like Scientists?},
  booktitle = {Conference on Language Modeling (COLM)},
  year      = {2025},
  url       = {https://openreview.net/forum?id=LKINTp7Gdo},
  eprint    = {2505.09614},
  archivePrefix = {arXiv}
}
```

## gogleva2026 -- corrected (full title, name the workshop, non-archival)
- Anna Gogleva, Thomas Charman, Martin Balla, Karl Gemayel (Relation Therapeutics). "Treating the Symptom, Missing the Cause: Anatomy of a Scientific Reasoning Failure." NeurIPS 2026 Workshop "I Can't Believe It's Not Better (ICBINB): Failure Modes of AI in Biology" (non-archival). arXiv 2611.04473 (v2, 5 Nov 2026).
- Venue evidence: the arXiv comment reads "NeurIPS 2026 Workshop on Failure Modes of AI in Biology (ICBINB-BIO); non-archival", and the p. 1 footer reads "40th Conference on Neural Information Processing Systems (NeurIPS 2026). Workshop: I Can't Believe It's Not Better (ICBINB): Failure Modes of AI in Biology". WebSearch lists a NeurIPS 2026 spotlight talk with this exact title (https://neurips.cc/virtual/2026/169436) and the ICBINB workshop page (https://neurips.cc/virtual/2026/workshop/137508). neurips.cc is blocked here, so I could not confirm that the spotlight belongs to that workshop.
- Fixes: add the subtitle and name the workshop. The workshop is non-archival, so cite it as a workshop paper and keep the arXiv id.
- Earlier-draft claims (not in V9):
  - "agents acquire discriminating evidence but misuse it": SUPPORTED. The abstract says "agents encounter evidence that distinguishes competing causes in 91% of relevant sessions, and still frequently misdiagnose the system". Sec. 4.5 says models fail to "predict the outcome of the experiment under each competing cause" (Probe 3b accuracy 0.51-0.74, against 0.88-1.00 when the predictions are given).
  - "and rarely abstain": SUPPORTED, but only on probes. In Appendix B.4, models answered UNDETERMINED in 1 of 301 Probe 3b answers. On non-evidence items, Probe 1 accuracy is 0.30-0.53 because models "choose the numerically closer prediction rather than conclude that the result is uninformative" (Sec. 4.5). Abstention in live sessions is not reported.
  - Useful numbers: Opus 4.6 rescues 20/20 but diagnoses 55%, and Sonnet 4.6 rescues all but diagnoses 35% (Sec. 3, Table 2). The set is 7 LLMs and 420 sessions.
```bibtex
@inproceedings{gogleva2026,
  author    = {Gogleva, Anna and Charman, Thomas and Balla, Martin and Gemayel, Karl},
  title     = {Treating the Symptom, Missing the Cause: Anatomy of a Scientific Reasoning Failure},
  booktitle = {NeurIPS 2026 Workshop: I Can't Believe It's Not Better (ICBINB): Failure Modes of AI in Biology (non-archival)},
  year      = {2026},
  eprint    = {2611.04473},
  archivePrefix = {arXiv},
  url       = {https://arxiv.org/abs/2611.04473}
}
```

## goldberger2026 -- verified (arXiv preprint)
- Motti Goldberger, Nils Rudi (Yale School of Management). "A Simple and General Approach to top-$k$ Selection." arXiv 2610.26407 [cs.LG] (v2, 20 Oct 2026; Semantic Scholar date 2026-10-19). The arXiv record and the PDF give no venue, so cite it as a preprint.
- Earlier-draft use (not in V9): "Our vocabulary comes from ... top-k selection (Goldberger & Rudi 2026)". SUPPORTED as a terminology source. The paper studies Bayesian top-k identification under a fixed, batched sampling budget, with expected opportunity cost and probability of correct selection as metrics (Sec. 1-2). It proves that posterior EOC decays at an exponential rate of at least half the optimal rate (abstract, Sec. 4).
- Note: a companion paper by the same authors exists, "Selecting the best few with human evaluators" (arXiv 2610.26380, cited in its references). Do not confuse the two.
```bibtex
@misc{goldberger2026,
  author        = {Goldberger, Motti and Rudi, Nils},
  title         = {A Simple and General Approach to Top-$k$ Selection},
  year          = {2026},
  eprint        = {2610.26407},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2610.26407}
}
```

## hardy2026 -- corrected (full title; preprint, under review)
- Michael Hardy, Ruhana Azam, Anka Reuel, Mykel Kochenderfer, Sanmi Koyejo. "Agent Evaluation Reliability: More Tasks Won't (Always) Fix An Agent Leaderboard." arXiv 2610.00651 [cs.AI] (v1, 30 Sep 2026). The PDF header reads "Under review as a conference paper", so there is no venue and it should be cited as a preprint.
- Fix: use the full title (the reference has only "Agent evaluation reliability").
- Earlier-draft claims (not in V9): "this compares model-plus-scaffold systems (Hardy et al. 2026)" and "flag every GPT-vs-Claude contrast (cf. Hardy et al. 2026)". SUPPORTED. The abstract says "Fixed model-scaffold systems are ranked reliably (Erho^2 = 0.935-0.994), while underlying-model reliability is substantially lower (0.148-0.841)". It also says "Scaffold choice can change evaluation conclusions" and introduces inter-scaffold reliability (posterior medians 0.151-0.852, Sec. 1). The data cover 22 benchmarks from HAL and Harbor Index.
```bibtex
@misc{hardy2026,
  author        = {Hardy, Michael and Azam, Ruhana and Reuel, Anka and Kochenderfer, Mykel and Koyejo, Sanmi},
  title         = {Agent Evaluation Reliability: More Tasks Won't (Always) Fix An Agent Leaderboard},
  year          = {2026},
  eprint        = {2610.00651},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2610.00651}
}
```

