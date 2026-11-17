
## Batch 6 verification (2026-11-17)

### krishnamurthy2024 -- VERIFIED
- Title: Can Large Language Models Explore In-Context?
- Authors: Akshay Krishnamurthy, Keegan Harris, Dylan J. Foster, Cyril Zhang, Aleksandrs Slivkins
- Venue: NeurIPS 2024 (Advances in Neural Information Processing Systems 37). Confirmed: arXiv comment "Accepted to NeurIPS 2024"; NeurIPS proceedings PDF (proceedings.neurips.cc .../d951f73c521d069fefbb73396df01424-Paper-Conference.pdf); poster https://neurips.cc/virtual/2024/poster/95364
- arXiv 2403.15371; https://arxiv.org/abs/2403.15371
- Claim check: V9 cites it for "LLM agents' exploration deficits". Supported by the abstract: GPT-3.5, GPT-4 and Llama2 run as agents in multi-armed bandits "do not robustly engage in exploration without substantial interventions"; only GPT-4 with CoT plus an externally summarized history explored satisfactorily.
- Sources: arXiv API, Semantic Scholar (venue: Neural Information Processing Systems), WebSearch (NeurIPS proceedings, virtual poster page).

```bibtex
@inproceedings{krishnamurthy2024,
  title     = {Can Large Language Models Explore In-Context?},
  author    = {Krishnamurthy, Akshay and Harris, Keegan and Foster, Dylan J. and Zhang, Cyril and Slivkins, Aleksandrs},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {37},
  year      = {2024},
  note      = {arXiv:2403.15371}
}
```

### lieberum2024 -- VERIFIED (optional upgrade to the BlackboxNLP 2024 form)
- Title: Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2
- Authors: Tom Lieberum, Senthooran Rajamanoharan, Arthur Conmy, Lewis Smith, Nicolas Sonnerat, Vikrant Varma, János Kramár, Anca Dragan, Rohin Shah, Neel Nanda
- arXiv 2408.05147 (2024); https://arxiv.org/abs/2408.05147. Also published in Proceedings of the 7th BlackboxNLP Workshop (EMNLP 2024, Miami), pp. 278-300, DOI 10.18653/v1/2024.blackboxnlp-1.19, https://aclanthology.org/2024.blackboxnlp-1.19/
- Claim check: V9 says the SAE is "Gemma Scope's 16k-latent SAE for that layer" (the residual stream after block 12 of Gemma-2-2B). Supported: the abstract says the JumpReLU SAEs are "trained on all layers and sub-layers of Gemma 2 2B"; Fig. 2 (p. 7) shows residual-stream (post_mlp_residual) SAEs for layer 12 of Gemma 2 2B at width 16.4K (2^14) and wider; Sec. 4.3 (p. 8) describes widths "between 2^14 ≈ 16.4K and 2^19" "after layers 12 and 20 of Gemma 2 2B and 9B". The paper says nothing about the logistic-regression probe, which is our own method, so the citation is correctly attached to the SAE clause only. Wording note: "16k" is the release's name for the 2^14 = 16,384-latent width, so it is fine.
- Sources: alphaXiv answer_pdf_queries (pp. 1, 2, 7, 8), Semantic Scholar (venue BlackboxNLP, ACL id 2024.blackboxnlp-1.19), WebSearch (ACL Anthology).

```bibtex
@inproceedings{lieberum2024,
  title     = {Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2},
  author    = {Lieberum, Tom and Rajamanoharan, Senthooran and Conmy, Arthur and Smith, Lewis and Sonnerat, Nicolas and Varma, Vikrant and Kram{\'a}r, J{\'a}nos and Dragan, Anca and Shah, Rohin and Nanda, Neel},
  booktitle = {Proceedings of the 7th BlackboxNLP Workshop: Analyzing and Interpreting Neural Networks for NLP},
  pages     = {278--300},
  year      = {2024},
  doi       = {10.18653/v1/2024.blackboxnlp-1.19},
  note      = {arXiv:2408.05147}
}
```

### ma2026 -- VERIFIED (not cited in V9 text)
- Title: Best-Arm Identification with Generative Proxy
- Authors: Tianyi Ma, Hanzhang Qin, Ruihao Zhu, Jierui Zuo
- arXiv 2607.06879 (2026), preprint; no venue found. https://arxiv.org/abs/2607.06879 ; https://www.alphaxiv.org/abs/2607.06879
- Content: fixed-confidence BAI where each costly reward pull is paired with a cheap correlated proxy score (from ML/LLM predictions); control-variate adjustment; PROBE algorithm, delta-PAC. Not in the V9 list or text, so there is no claim to check. If it is re-added, it fits as BAI with a cheap (LLM) proxy. It is NOT about abstention or biased proxies, so do not cite it for "best-arm identification with abstention".
- Sources: Semantic Scholar (title, authors, year, DOI 10.48550/arXiv.2607.06879), alphaXiv full text (title page, abstract). The arXiv API returned HTTP 429 for this id.

```bibtex
@article{ma2026,
  title   = {Best-Arm Identification with Generative Proxy},
  author  = {Ma, Tianyi and Qin, Hanzhang and Zhu, Ruihao and Zuo, Jierui},
  journal = {arXiv preprint arXiv:2607.06879},
  year    = {2026}
}
```

### marks2025a -- VERIFIED (not cited in V9 text)
- Title: Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs in Language Models
- Authors: Samuel Marks, Can Rager, Eric J. Michaud, Yonatan Belinkov, David Bau, Aaron Mueller
- Venue: ICLR 2025. Confirmed: arXiv journal_ref "International Conference on Learning Representations, 2025"; ICLR proceedings https://proceedings.iclr.cc/paper_files/paper/2025/hash/3ba4d47a83e498c2b1a0868cba20f6de-Abstract-Conference.html ; OpenReview forum I4e82CIDxv
- arXiv 2403.19647; https://arxiv.org/abs/2403.19647
- Not in the V9 list or text, so there is no claim to check. If it is dropped from V9, also drop the "a" suffix from any remaining marks2025b key.
- Sources: arXiv API, WebSearch (ICLR proceedings, project page).

```bibtex
@inproceedings{marks2025a,
  title     = {Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs in Language Models},
  author    = {Marks, Samuel and Rager, Can and Michaud, Eric J. and Belinkov, Yonatan and Bau, David and Mueller, Aaron},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2403.19647}
}
```
