# Citation verification, batch 3 (checked 2026-11-17)

Sources used: arXiv API and arXiv abs pages, alphaXiv full-text PDF queries, Semantic Scholar API, OpenReview API search (api2.openreview.net/notes/search works; per-note lookups hit the bot challenge), WebSearch. neurips.cc is not reachable from this session (DNS blocked), so I could not open NeurIPS 2026 virtual pages.

## chan2025 -- verified
- Jun Shern Chan, Neil Chowdhury, Oliver Jaffe, James Aung, Dane Sherburn, Evan Mays, Giulio Starace, Kevin Liu, Leon Maksin, Tejal Patwardhan, Lilian Weng, Aleksander Madry. "MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering." ICLR 2025 (Oral). arXiv 2410.07095 (v6 comment: "ICLR version"; the PDF header reads "Published as a conference paper at ICLR 2025"). OpenReview https://openreview.net/forum?id=6s5uXNWGIh (venue field "ICLR 2025 Oral"). The PDF byline prints the first author as "Chan Jun Shern". The first seven authors contributed equally, in randomized order.
- V9: "... and MLE-bench uses held-out test scores (Chan et al. 2025)." SUPPORTED. Sec. 2.1 (pp. 2-4): each competition ships "grading code used to evaluate submissions locally". Where Kaggle never released test labels, the authors "manually create new train and test splits based on the publicly available training data", usually 10% of the original training set. The agent never sees these test labels. Sec. 2.2 then ranks the scores against the Kaggle Private leaderboard to award medals. MLE-bench uses no LLM or human judge for scoring; GPT-4o appears only for rule-breaking log checks (Sec. 2.3.1). For more precision: "MLE-bench grades submissions on held-out test splits against Kaggle leaderboards".
```bibtex
@inproceedings{chan2025,
  author    = {Chan, Jun Shern and Chowdhury, Neil and Jaffe, Oliver and Aung, James and Sherburn, Dane and Mays, Evan and Starace, Giulio and Liu, Kevin and Maksin, Leon and Patwardhan, Tejal and Weng, Lilian and M{\k{a}}dry, Aleksander},
  title     = {{MLE}-bench: Evaluating Machine Learning Agents on Machine Learning Engineering},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  url       = {https://openreview.net/forum?id=6s5uXNWGIh},
  eprint    = {2410.07095},
  archivePrefix = {arXiv}
}
```

## chanin2026 -- corrected (title is wrong; not cited in V9)
- David Chanin (sole author). "Are Sparse Autoencoder Benchmarks Reliable?" arXiv 2605.18229, submitted 18 May 2026. DOI 10.48550/arXiv.2605.18229. The OpenReview search also lists it as "Mech Interp Workshop ICML 2026 Poster" (forum DzBTbqEeA9). That is a workshop and probably non-archival, so cite the arXiv form.
- Fix: the title says "Sparse Autoencoder" in full, not "SAE".
- No V9 sentences use it, and V9 does not list it. Leave it out unless the text cites it.
```bibtex
@misc{chanin2026,
  author        = {Chanin, David},
  title         = {Are Sparse Autoencoder Benchmarks Reliable?},
  year          = {2026},
  eprint        = {2605.18229},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2605.18229}
}
```

## chen2026 -- corrected (NeurIPS 2026 NOT VERIFIED from a venue page; title differs between arXiv and PDF)
- Yiwei Chen, Amila Weerasinghe, Siddharth Biswal, Utkrisht Rajkumar, Olcay Boz, Taylor Berg-Kirkpatrick, Rose Yu. arXiv 2610.14381 (v1 9 Oct 2026, v2 8 Nov 2026). https://arxiv.org/abs/2610.14381
- Title: the arXiv metadata and Semantic Scholar give "ACED-Bench: Evaluating How LLM Agents Acquire and Act on Causal Evidence". The PDF title (v2) is "ACED: Evaluating How LLM Agents Acquire and Act on Causal Evidence", which matches the V9 entry. Use the arXiv metadata title for a preprint citation.
- Venue: the v2 PDF footer reads "40th Conference on Neural Information Processing Systems (NeurIPS 2026)" in camera-ready style, and the PDF includes the NeurIPS checklist. That is the authors' own claim, though. I could not confirm acceptance from a venue page. The arXiv comment field is empty, Semantic Scholar lists no venue, the OpenReview API search returned no match, WebSearch found no NeurIPS 2026 virtual listing, and neurips.cc is blocked here. Following the rules, cite it as an arXiv preprint until someone checks the NeurIPS 2026 accepted-papers list.
- V9: "... and LLM agents' exploration deficits (Krishnamurthy et al. 2024; Chen et al. 2026)." SUPPORTED. Sec. 5.1 and Fig. 3 (p. 8): "Most open-weight models test a true lever on its own in fewer than half of the episodes". Claude Opus/Sonnet 5.5 test a lever in about 60% of episodes but test every lever in the helpful direction in only 44-46%. Across all 12 models, 55% of episodes test a true lever and 20% ever run a working fix. The abstract and conclusion say agents need "explicit support for choosing experiments". Note that ACED frames this as deficient experiment choice and causal investigation, not exploration in the bandit sense. "Exploration deficits" is a fair reading, but "deficits in choosing experiments" is closer to the source. Caution: the abstract says "fewer than half of the worlds" while Sec. 5.1 says "episodes".
```bibtex
@misc{chen2026,
  author        = {Chen, Yiwei and Weerasinghe, Amila and Biswal, Siddharth and Rajkumar, Utkrisht and Boz, Olcay and Berg-Kirkpatrick, Taylor and Yu, Rose},
  title         = {{ACED-Bench}: Evaluating How {LLM} Agents Acquire and Act on Causal Evidence},
  year          = {2026},
  eprint        = {2610.14381},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2610.14381},
  note          = {PDF footer states NeurIPS 2026; acceptance not verified from venue page}
}
```

## engels2025 -- verified
- Joshua Engels, Logan Smith, Max Tegmark. "Decomposing The Dark Matter of Sparse Autoencoders." Transactions on Machine Learning Research (TMLR), 04/2025. arXiv 2410.14670 (v2 comment: "Published in TMLR"). OpenReview https://openreview.net/forum?id=sXq3Wb3vef ("Accepted by TMLR"; an earlier ICLR 2025 submission was withdrawn). The arXiv metadata lists the second author as "Logan Riggs", but the TMLR PDF byline says "Logan Smith" (Independent). Keep "Smith", as V9 has it.
- V9: "ShiftHunt hides the cues and their number, ..., its traps exploit what SAEs miss (Engels et al. 2025)." SUPPORTED as a general gloss. The abstract (p. 1) says SAEs "fall short of completely explaining model performance, resulting in 'dark matter': unexplained variance in activations". Sec. 4.2 (p. 5) says "there are large linear subspaces that the SAE is mostly failing to learn". Sec. 6 and 7 say nonlinear error stays roughly constant as SAEs scale, so it "may never be able to be learned by SAEs". The paper says nothing about traps or benchmarks, so it supports only the "what SAEs miss" part. More precise wording: "... exploit SAE dark matter, the activation variance SAEs fail to reconstruct (Engels et al. 2025)".
```bibtex
@article{engels2025,
  author  = {Engels, Joshua and Smith, Logan and Tegmark, Max},
  title   = {Decomposing The Dark Matter of Sparse Autoencoders},
  journal = {Transactions on Machine Learning Research},
  year    = {2025},
  url     = {https://openreview.net/forum?id=sXq3Wb3vef},
  eprint  = {2410.14670},
  archivePrefix = {arXiv}
}
```
