# Citation verification, batch 2 (checked 2026-11-17)

Sources used: arXiv API, Semantic Scholar API, OpenReview API (api2.openreview.net/notes/search works), alphaXiv full-text queries, WebSearch. alphaXiv and OpenReview were the main tools. alignment.anthropic.com, alignmentforum.org and proceedings.iclr.cc are blocked in this session's network, so I could not open them directly.

## blackwell1953 -- verified (not cited in V9)
- David Blackwell. "Equivalent Comparisons of Experiments." Annals of Mathematical Statistics 24(2):265-272, June 1953. DOI 10.1214/aoms/1177729032. MR56251.
- URL: https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-24/issue-2/Equivalent-Comparisons-of-Experiments/10.1214/aoms/1177729032.short
- No V9 sentences use it. V9 does not list or cite it either, so leave it out of V9, or add it only if the text cites it.
```bibtex
@article{blackwell1953,
  author  = {Blackwell, David},
  title   = {Equivalent Comparisons of Experiments},
  journal = {The Annals of Mathematical Statistics},
  volume  = {24},
  number  = {2},
  pages   = {265--272},
  year    = {1953},
  doi     = {10.1214/aoms/1177729032}
}
```

## bowyer2025 -- corrected (title needs its "Position:" prefix)
- Sam Bowyer, Laurence Aitchison, Desi R. Ivanova. "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints." ICML 2025, Position Paper Track (spotlight poster), PMLR 267. arXiv 2503.01747. OpenReview https://openreview.net/forum?id=YhZ2PY2nZa (venue field: "ICML 2025 Position Paper Track spotlightposter"). DBLP conf/icml/BowyerAI25.
- Fix: the official title begins with "Position:". Everything else in the entry is correct.
- V9: "With six items, normal approximations fail (Bowyer et al. 2025)." SUPPORTED, but the source does not test exactly six items. Section 3 runs simulations at N = 3, 10, 30 and 100, and Fig. 2 shows CLT and bootstrap intervals under-covering, worst at small N. Fig. 1 (N = 20, LangChain tool use) and Fig. 9 (AIME, N = 15) show CLT intervals that collapse to zero width or extend outside [0,1]. N = 6 lies between the tested N = 3 and N = 10, so the claim follows. Wording that sticks closer to the paper: "with a handful of items, CLT intervals under-cover or degenerate (Bowyer et al. 2025)".
```bibtex
@inproceedings{bowyer2025,
  author    = {Bowyer, Sam and Aitchison, Laurence and Ivanova, Desi R.},
  title     = {Position: Don't Use the {CLT} in {LLM} Evals With Fewer Than a Few Hundred Datapoints},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning (Position Paper Track)},
  series    = {Proceedings of Machine Learning Research},
  volume    = {267},
  year      = {2025},
  url       = {https://openreview.net/forum?id=YhZ2PY2nZa},
  eprint    = {2503.01747},
  archivePrefix = {arXiv}
}
```

## bragg2026 -- verified (use the full title)
- Jonathan Bragg, Mike D'Arcy, Nishant Balepur, Dan Bareket, Bhavana Dalvi, Sergey Feldman, Dany Haddad, Jena D. Hwang, Peter Jansen, Varsha Kishore, Bodhisattwa Prasad Majumder, Aakanksha Naik, Sigal Rahamimov, Kyle Richardson, Amanpreet Singh, Harshit Surana, Aryeh Tiktinsky, Rosni Vasu, Guy Wiener, Chloe Anastasiades, Stefan Candra, Jason Dunkelberger, Dan Emery, Rob Evans, Malachi Hamada, Regan Huff, Rodney Kinney, Matt Latzke, Jaron Lochner, Ruben Lozano-Aguilera, Cecile Nguyen, Smita Rao, Amber Tanaka, Brooke Vlahos, Peter Clark, Doug Downey, Yoav Goldberg, Ashish Sabharwal, Daniel S. Weld. "AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite." ICLR 2026 (oral). arXiv 2510.21652. OpenReview https://openreview.net/forum?id=M7TNf5J26u (venue field "ICLR 2026 Oral"). The arXiv v2 comment also says "Published as a conference paper at ICLR 2026".
- V9 (a): "Research output has no answer key, so benchmarks validate their LLM judges against experts, as AstaBench does on one subset (Bragg et al. 2026)."
- V9 (b): "AstaBench validates its judge against experts on one subset (Bragg et al. 2026), ..."
- SUPPORTED, with one detail to know. Appendix E.3 ("Validation of ScholarQA-CS2", p. 37) reports that the LLM-judge rankings were checked against expert annotators' three-way rankings: system-level Kendall tau = 0.467 (0.800 without Elicit), and 68.1% instance-level agreement (tau 0.369). This is the only expert-ranking validation of a judge in the paper. The detail: Appendix F.9 (p. 52) says the E2E-Bench rubrics were "checked manually" and the rubric scoring was "validated using spot-check sampling and verification by a human (judged 92% correct on a dev set sample of 50 rubric items)". So "on one subset" holds for expert validation of the judge. A strict reader could object because of that second check. Safer wording: "AstaBench validates its ScholarQA-CS2 judge against expert rankings (system-level Kendall tau 0.467)". AstaBench has 11 benchmarks (Table 2), and 6 of them use LLM judges (Sec. 3). If any version says "ten subsets", change it to 11 benchmarks.
```bibtex
@inproceedings{bragg2026,
  author    = {Bragg, Jonathan and D'Arcy, Mike and Balepur, Nishant and Bareket, Dan and Dalvi, Bhavana and Feldman, Sergey and Haddad, Dany and Hwang, Jena D. and Jansen, Peter and Kishore, Varsha and Majumder, Bodhisattwa Prasad and Naik, Aakanksha and Rahamimov, Sigal and Richardson, Kyle and Singh, Amanpreet and Surana, Harshit and Tiktinsky, Aryeh and Vasu, Rosni and Wiener, Guy and Anastasiades, Chloe and Candra, Stefan and Dunkelberger, Jason and Emery, Dan and Evans, Rob and Hamada, Malachi and Huff, Regan and Kinney, Rodney and Latzke, Matt and Lochner, Jaron and Lozano-Aguilera, Ruben and Nguyen, Cecile and Rao, Smita and Tanaka, Amber and Vlahos, Brooke and Clark, Peter and Downey, Doug and Goldberg, Yoav and Sabharwal, Ashish and Weld, Daniel S.},
  title     = {{AstaBench}: Rigorous Benchmarking of {AI} Agents with a Scientific Research Suite},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2026},
  url       = {https://openreview.net/forum?id=M7TNf5J26u},
  eprint    = {2510.21652},
  archivePrefix = {arXiv}
}
```

## bricken2025 -- verified
- Trenton Bricken, Rowan Wang, Sam Bowman, Euan Ong, Johannes Treutlein, Jeff Wu, Evan Hubinger, Samuel Marks. "Building and evaluating alignment auditing agents." Anthropic Alignment Science Blog, 24 July 2025. URL https://alignment.anthropic.com/2025/automated-auditing/. Not on arXiv, so there is no arXiv id or DOI.
- Author list: I could not open the blog page itself (the host is blocked here). The list above is copied from the reference list of AuditBench (Sheshadri et al., arXiv 2602.22755v4, p. 10), and WebSearch results of citing papers agree with it. The Alignment Forum cross-post lists fewer names.
- V9: "Auditing games and agents grade against a known implanted behaviour, like our keyed level (Marks et al. 2025; Bricken et al. 2025)." SUPPORTED. The blog says the agents are evaluated "against models with intentionally-inserted alignment issues", using the auditing-game environment of Marks et al. (2025). AuditBench (Related Work, p. 9) confirms this: "Bricken et al. (2025) enabled repeatable evaluation by replacing humans with autonomous agents on the Marks et al. (2025) model organism." One small point: the red-teaming agent was also run on Claude 4 with no answer key. The sentence still holds for the evaluations it describes.
```bibtex
@misc{bricken2025,
  author       = {Bricken, Trenton and Wang, Rowan and Bowman, Sam and Ong, Euan and Treutlein, Johannes and Wu, Jeff and Hubinger, Evan and Marks, Samuel},
  title        = {Building and Evaluating Alignment Auditing Agents},
  howpublished = {Anthropic Alignment Science Blog},
  month        = jul,
  year         = {2025},
  url          = {https://alignment.anthropic.com/2025/automated-auditing/}
}
```
