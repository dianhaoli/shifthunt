# Citation verification, batch 1 (checked 2026-11-17)

None of these four entries (all carried over from V8) are in the V9 reference list, and none are cited in the V9 text. So there are no V9 sentences to check against them.

## angelopoulos2023: verified
- Title: Prediction-powered inference
- Authors: Anastasios N. Angelopoulos, Stephen Bates, Clara Fannjiang, Michael I. Jordan, Tijana Zrnic
- Venue: Science 382, pp. 669-674, 2023. DOI 10.1126/science.adi6000. arXiv 2301.09633.
- URL: https://doi.org/10.1126/science.adi6000 (preprint: https://arxiv.org/abs/2301.09633)
- Sources: arXiv API (title, authors, first posted 2023-01-23); Semantic Scholar (DOI, Science vol. 382, pp. 669-674, PubMed 37943906). Crossref was blocked by the proxy, so the issue number was not checked and is left out.

```bibtex
@article{angelopoulos2023,
  title   = {Prediction-Powered Inference},
  author  = {Angelopoulos, Anastasios N. and Bates, Stephen and Fannjiang, Clara and Jordan, Michael I. and Zrnic, Tijana},
  journal = {Science},
  volume  = {382},
  pages   = {669--674},
  year    = {2023},
  doi     = {10.1126/science.adi6000},
  eprint  = {2301.09633},
  archivePrefix = {arXiv}
}
```

## ashouritaklimi2026: verified
- Title: Prediction-Powered Active Testing
- Authors: Kianoosh Ashouritaklimi, Valentin Kilian, Daolang Huang, Tom Rainforth, François Caron
- Venue: arXiv preprint 2607.08347 (v1, 2026-07-09). Semantic Scholar lists no venue.
- URL: https://arxiv.org/abs/2607.08347
- Sources: arXiv API, Semantic Scholar.

```bibtex
@article{ashouritaklimi2026,
  title   = {Prediction-Powered Active Testing},
  author  = {Ashouritaklimi, Kianoosh and Kilian, Valentin and Huang, Daolang and Rainforth, Tom and Caron, Fran{\c{c}}ois},
  journal = {arXiv preprint arXiv:2607.08347},
  year    = {2026},
  eprint  = {2607.08347},
  archivePrefix = {arXiv}
}
```

## atsidakou2023: verified (with a note on the year)
- Title: Bayesian Fixed-Budget Best-Arm Identification
- Authors: Alexia Atsidakou, Sumeet Katariya, Sujay Sanghavi, Branislav Kveton
- Venue: arXiv preprint 2211.08572. v1 was posted 2022-11-15 and v3 (the latest) was revised 2023-06-15. I found no conference or journal version: Semantic Scholar shows arXiv only, and a web search turned up nothing else.
- Year: 2023 is fine if the paper cites v3. Semantic Scholar and DBLP (CoRR) list it as 2022, so the year can stay 2023 with "v3" or change to 2022. The key is kept as given.
- URL: https://arxiv.org/abs/2211.08572
- Sources: arXiv API (all versions), Semantic Scholar, web search.

```bibtex
@article{atsidakou2023,
  title   = {Bayesian Fixed-Budget Best-Arm Identification},
  author  = {Atsidakou, Alexia and Katariya, Sumeet and Sanghavi, Sujay and Kveton, Branislav},
  journal = {arXiv preprint arXiv:2211.08572},
  year    = {2023},
  note    = {v3, revised June 2023; first posted November 2022},
  eprint  = {2211.08572},
  archivePrefix = {arXiv}
}
```

## austin2026: corrected (the COLM 2026 venue could not be confirmed independently)
- Title: Semantic Bandits: In-Context Exploration-Exploitation is Biased by Semantic Priors
- Authors: David Eric Austin, Kaheer Suleman, Jackie Chi Kit Cheung
- arXiv 2608.16707 (v1, 2026-08-17, cs.CL). URL: https://arxiv.org/abs/2608.16707 (alphaXiv: https://www.alphaxiv.org/abs/2608.16707)
- Venue: the authors' arXiv PDF has the header "Published as a conference paper at COLM 2026" on page 1. Two independent checks found nothing to confirm this: Semantic Scholar lists the venue as "arXiv.org", and a web search found no listing on a COLM or OpenReview page. Three sites needed to check this (openreview.net, papers.cool, huggingface.co) are blocked in this session. So the venue is NOT VERIFIED against the proceedings. Cite the arXiv preprint form below, or change to @inproceedings{..., booktitle={Conference on Language Modeling (COLM)}, year={2026}} once the COLM 2026 accepted list or OpenReview page confirms it.
- Sources: arXiv API, arXiv PDF (page 1), alphaXiv get_paper_content, Semantic Scholar, web search.

```bibtex
@article{austin2026,
  title   = {Semantic Bandits: In-Context Exploration-Exploitation is Biased by Semantic Priors},
  author  = {Austin, David Eric and Suleman, Kaheer and Cheung, Jackie Chi Kit},
  journal = {arXiv preprint arXiv:2608.16707},
  year    = {2026},
  note    = {The PDF states ``Published as a conference paper at COLM 2026''},
  eprint  = {2608.16707},
  archivePrefix = {arXiv}
}
```
