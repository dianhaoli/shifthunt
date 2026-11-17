# Citation verification, batch 5 (checked 2026-11-17)

Sources: arXiv API (all three arXiv ids), alphaXiv full-text PDF queries (Circuit Oracle), OpenReview API search (api2.openreview.net/notes/search), WebSearch. Semantic Scholar returned 429 three times with backoff, so it was not used. In this session doi.org, api.crossref.org and pages.ucsd.edu are blocked by the network policy.

## huang2026 -- corrected (title is truncated)
- Yuqi Huang, Yunlong Hou, Vincent Y. F. Tan. "Bayesian Best-Arm Identification with Abstention: A Polynomial-to-Exponential Phase Transition." arXiv 2606.29203 (v1, 28 Jun 2026). No journal-ref or comment. The OpenReview search found no venue record. https://arxiv.org/abs/2606.29203
- Fix: add the subtitle ": A Polynomial-to-Exponential Phase Transition". The authors are correct.
- V9: "Querying under a biased proxy is best-arm identification with abstention (Russo et al. 2026; Huang et al. 2026)". SUPPORTED as an analogy. The abstract defines the setting as "the Bayesian fixed-budget best-arm identification problem in which a learner can abstain from making a terminal recommendation, subject to an abstention budget alpha". The error criterion is the "probability of undetected error". Nothing in the paper concerns biased proxies; the mapping is ours. An optional sharper wording would be "(Bayesian, fixed-budget) best-arm identification with abstention".
```bibtex
@misc{huang2026,
  author        = {Huang, Yuqi and Hou, Yunlong and Tan, Vincent Y. F.},
  title         = {Bayesian Best-Arm Identification with Abstention: A Polynomial-to-Exponential Phase Transition},
  year          = {2026},
  eprint        = {2606.29203},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2606.29203}
}
```

## kabir2026 -- corrected (title is truncated; list all five authors)
- Shariar Kabir, Hong Kiat Tan, Swastik Agrawal, Sai V R Chereddy, Sriram Balasubramanian. "Circuit Oracle: Automating Attribution Graph Analysis via Natural-Language Queries." arXiv 2611.00420 (v1, 30 Oct 2026). The arXiv comment reads: "Extended version of a paper presented at the Mechanistic Interpretability and Compositional Learning workshops at ICML 2026". OpenReview has a Mech Interp Workshop ICML 2026 poster (forum ANY6YrYUZE) and a CompLearn 2026 poster (LmkgcUJA8N); the ICLR 2027 submission (Y1suaFtBwf) was desk rejected. Cite the arXiv form, since the workshops are non-archival.
- Fix: use the full title.
- V9: "Circuit Oracle, SAEScientist-Bench and AuditBench grade with LLM judges, classifiers or rank metrics (Kabir et al. 2026; ...)". SUPPORTED for Circuit Oracle (LLM judges). All three tasks are scored by LLM judges:
  - Sec. 4.3 (p. 5), spurious features: "An LLM judge: gpt-5.4-mini, counts the spurious- and core-aligned features named in the report and returns a categorical verdict".
  - Sec. 5.2 (p. 7), taboo secret elicitation: "Runs are graded by openai/gpt-oss-120b". The closed mode is a 20-option forced choice that the paper calls "exact-match grading", but an LLM still performs it.
  - Sec. 6.1 (p. 8), jailbreaking: "Each completion is scored by a five-model LLM-judge ensemble".
- Caution: the secret-elicitation numbers in this paper disagree with each other (abstract/intro 69.2% vs 81.2%; Fig. 3 75.0%; App. F.2 AO 86.7%). Do not quote them.
```bibtex
@misc{kabir2026,
  author        = {Kabir, Shariar and Tan, Hong Kiat and Agrawal, Swastik and Chereddy, Sai V. R. and Balasubramanian, Sriram},
  title         = {Circuit Oracle: Automating Attribution Graph Analysis via Natural-Language Queries},
  year          = {2026},
  eprint        = {2611.00420},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  note          = {Extended version of a paper presented at the Mechanistic Interpretability and Compositional Learning workshops at ICML 2026},
  url           = {https://arxiv.org/abs/2611.00420}
}
```

## karvonen2024 -- verified (not cited in V9)
- Adam Karvonen, Can Rager, Samuel Marks, Neel Nanda. "Evaluating Sparse Autoencoders on Targeted Concept Erasure Tasks." arXiv 2411.18895 (28 Nov 2024). https://arxiv.org/abs/2411.18895. OpenReview indexes it as CoRR 2024 (7qHV0j2NWS). An ATTRIB 2024 workshop record titled "...Targeted Concept Removal Tasks" (H9DhZTb19S) exists, but its authors are not shown. No archival venue was found, so cite the arXiv form.
- V9 neither cites nor lists it. Drop it from the bibliography unless the text adds a citation.
```bibtex
@misc{karvonen2024,
  author        = {Karvonen, Adam and Rager, Can and Marks, Samuel and Nanda, Neel},
  title         = {Evaluating Sparse Autoencoders on Targeted Concept Erasure Tasks},
  year          = {2024},
  eprint        = {2411.18895},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2411.18895}
}
```

## klayman1987 -- verified (DOI not resolved here)
- Joshua Klayman, Young-Won Ha. "Confirmation, Disconfirmation, and Information in Hypothesis Testing." Psychological Review 94(2):211-228, 1987. WebSearch confirmed the title, volume, issue and pages from a scanned copy and from reference lists.
- The DOI 10.1037/0033-295X.94.2.211 follows APA's pattern, but I could not resolve it here (doi.org and Crossref are blocked). Mark it NOT VERIFIED; check it at doi.org before camera-ready.
- V9: "testing only the favourite echoes positive test strategy (Klayman and Ha 1987)". SUPPORTED. The paper defines the positive test strategy as testing cases expected (or known) to have the property of interest, i.e. cases the current hypothesis predicts. It argues that this, not a wish to confirm, explains much of what is called "confirmation bias", and that it is often a good heuristic but can cause systematic errors. "Testing only the favourite hypothesis" is a fair analogy.
```bibtex
@article{klayman1987,
  author  = {Klayman, Joshua and Ha, Young-Won},
  title   = {Confirmation, Disconfirmation, and Information in Hypothesis Testing},
  journal = {Psychological Review},
  volume  = {94},
  number  = {2},
  pages   = {211--228},
  year    = {1987},
  doi     = {10.1037/0033-295X.94.2.211}
}
```
