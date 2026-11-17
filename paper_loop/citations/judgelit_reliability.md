# Citation check: "Reliability without Validity" (arXiv 2606.19544)

## Identity (verified from the arXiv API and the full text of v1)
- Title: Reliability without Validity: A Systematic, Large-Scale Evaluation of LLM-as-a-Judge Models Across Agreement, Consistency, and Bias
- Authors: Justin D. Norman, Michael U. Rivera, D. Alex Hughes (UC Berkeley School of Information)
- Year: 2026 (v1 submitted 17 Jun 2026; v2 dated 3 Nov 2026)
- Venue: arXiv preprint only (cs.CL). ACL-style template with a Responsibility Checklist, but no conference or journal is named.
- arXiv id: 2606.19544
- **Status: WITHDRAWN.** The arXiv API comment on v2 reads: "arXiv admin note: This submission has been withdrawn because it does not meet arXiv's research content quality standards". The text read here is v1.

```bibtex
@misc{norman2026reliability,
  title         = {Reliability without Validity: A Systematic, Large-Scale Evaluation of {LLM}-as-a-Judge Models Across Agreement, Consistency, and Bias},
  author        = {Norman, Justin D. and Rivera, Michael U. and Hughes, D. Alex},
  year          = {2026},
  eprint        = {2606.19544},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  note          = {Withdrawn by arXiv administrators (v2, Nov 2026)}
}
```
V9 reference-list style: `- Norman, Rivera and Hughes. Reliability without validity: a systematic, large-scale evaluation of LLM-as-a-judge models across agreement, consistency, and bias. arXiv 2606.19544, 2026 (withdrawn).`

## Setting
21 general-purpose LLM judges from nine providers (GPT-4o through GPT-5.4, Claude Haiku 4.5 / Sonnet 4 / Sonnet 4.6 / Opus 4.6, Gemini 2.5 / 3.1, Llama 3.3 70B, Qwen 3 8B, DeepSeek V3.2, Kimi K2.5, GLM-5 and others) on three pairwise benchmarks with human or correctness labels: MT-Bench (2,391 comparisons), JudgeBench (350 items), RewardBench (2,981 pairs, per-item position randomisation, seed 42). Three protocols: agreement (one judgment per item), consistency (3-5 runs, AB and BA order, caching disabled) and bias audit (MT-Bench only). 118 runs, about 541,000 judgments, temperature 0, March-April 2026, single pairwise template, reasoning channels suppressed for thinking models. Seven hypotheses stated before the frontier-model phase.

## Main findings (exact numbers from the paper)
1. Kappa deflation (EM minus Cohen's κ) on MT-Bench: 33.8 to 41.3 pp across all 21 judges, cohort mean 38.6 pp (abstract and Figure 1 say 33-41 / 33.8-41.2). Cohort means: JudgeBench 23.7 pp (range 8.1-38.5), RewardBench 10.2 pp in Table 2 and §5.1 but 10.4 pp in §4.1 (range 5.9-21.3). Best MT-Bench judge Gemini 3.1 Pro: EM 0.849, κ 0.511. "A judge reporting '85% agreement' on MT-Bench has κ ≈ 0.48."
2. Position bias |P(A wins) − 0.5| on MT-Bench ranges from 0.002 (Gemini 2.5 Pro) to 0.192 (Qwen 3 8B); Gemini 2.5 Flash 0.125. H2 (thinking models < 0.05) holds only for Gemini 3.1 Pro (0.038); GPT-5.4 0.083, DeepSeek V3.2 0.094.
3. Cross-benchmark rank instability: 11 of 21 shift by four or more positions (§4.3; §5.2 says ten of 21); only Gemini 3.1 Pro and Claude Opus 4.6 stay top three on all three. Llama 3.3 70B: MT-Bench rank 5, JudgeBench rank 20 (Table 5; §4.3 says 15 positions, §5.2 says "MT#5 → JB#19", the abstract says "up to 14 positions").
4. Discriminability: MT-Bench κ spread 13.5 pp (0.376-0.511), JudgeBench 60.4 pp (0.271-0.875; "4.5×"), RewardBench 28.1 pp (0.616-0.898).
5. Consistency falls on the harder benchmark: 7 of 16 judges' position flip rate rises at least 1.5× from MT-Bench to JudgeBench (Llama 3.3 70B 0.077 → 0.253; GPT-4o-mini 0.127 → 0.380; GLM-5 0.096 → 0.227); cohort median flip rate 0.09 → 0.17; mean test-retest 0.943 → 0.911.
6. Consistency-bias paradox (the title's claim): Qwen 3 8B test-retest 0.992 with position bias 0.192 and JudgeBench κ 0.289; Gemini 2.5 Flash 0.988 with 0.125. "Test-retest measures the stability of outputs and not the correctness of the underlying decision process"; "the most reproducible judges are among the least valid."
7. Verbosity bias (Pearson of length differential with verdict) < 0.011 for all 21 judges (max GPT-4o-mini 0.010; 17 of 21 below 0.005), under a single rubric; the authors warn against generalising.
8. Recommendation: a five-step Minimum Viable Validation Protocol (chance-correct; swap positions; replicate ≥ 3 runs; cross-validate on ≥ 2 benchmarks; "audit the paradox": if test-retest > 0.95, check position bias < 0.10).

Quality notes: besides the withdrawal, the text has several internal inconsistencies (Llama rank shift 14 / 15 / "MT#5 → JB#19"; Minimax "MT:17" in §4.3 vs "MT#16" in §5.2; 11 vs ten judges shifting ≥ 4 ranks; RewardBench mean deflation 10.2 vs 10.4; "all 20 evaluated judges" on RewardBench in §4.5 vs 21 in Appendix E; maximum MT-Bench deflation 41.2 vs 41.3). "Validity" here means agreement with human or correctness labels and position invariance. It is never measured against an executed outcome.

## Check of the claims a summary attributed to it
Every claim below except the one about "Reliability without Validity" itself describes a different paper. I searched the full text of 2606.19544 for each (terms: idea, novelty, self-play, grade-school/GSM, plausib, keyword, answer key, expert review, one token, "Thought process", injection, negation, 0.72, 0.94, 23%, 80%) and found nothing. None of them is in this paper.

- **Old Ideas** (one added sentence flips verdicts on over half of identical idea pairs; prompt changes flip a quarter to a third; judges validated on human papers, used on generated ideas): **not in this paper.** It evaluates no idea or paper judging. Its prompt-sensitivity content is limited to citing Stureborg et al. 2024 on temperature and prompt variation. See judgelit_oldideas.md.
- **More Convincing** (judge scores plausibility; self-play grade-school math pass rate 0.72 → 0.94 at true accuracy 0.20; committing an answer first cuts false positives 0.72 → 0.01): **not in this paper.** No self-play, math or answer-first experiment. See judgelit_convincing.md.
- **Gaming the Judge** (rewriting only the stated reasoning raises false positives by 20-30 points): **not in this paper.** No rewriting manipulation. See judgelit_gaming.md.
- **Not an Oracle** (parser defaulted every score to 3; keyword stuffing 23% → 80%; cached answer keys 100% vs 68%): **not in this paper.** See judgelit_oracle.md, which confirms these numbers in Wahi, arXiv 2609.02246.
- **One Token** (trivial responses such as ":" or "Thought process:" draw false positives up to about 80%): **not in this paper.** See judgelit_onetoken.md.
- **Grounded but Not Immune** (a false "expert reviewed" note overturns up to 40% of correct verdicts, even with tools): **not in this paper.** See judgelit_grounded.md.
- **Reliability without Validity**: **accurate in substance, with caveats.** The paper does show judges that are reliable but not valid, in a narrow form: two of 16 jointly evaluated judges (Qwen 3 8B, Gemini 2.5 Flash) have test-retest ≥ 0.95 together with position bias > 0.10 (§4.7, Figure 1b). Its broader "reliability" point is that raw exact match overstates chance-corrected agreement (kappa deflation). It does not show that every judge is invalid: frontier judges reach JudgeBench κ 0.78-0.88 and RewardBench κ about 0.87-0.90. "Validity" is agreement with human or correctness labels plus position invariance. Does it pre-empt our "consistent, not valid" framing? **Partly, at the level of the slogan only.** The idea that test-retest stability does not imply validity is standard psychometrics, and this paper names it for LLM judges first ("consistency-bias paradox"; "highly reproducible but not valid"). So V9 should not present the general framing as new. It does not pre-empt our result. Its judges agree with human labels at κ 0.27-0.90 on benchmarks where the evidence is visible. Ours agrees with itself at κ 0.39 and with the executed grade at κ −0.006, because the evidence that decides most absence claims is missing from what the judge reads. Its invalidity mechanism is a position preference. Ours is undecidability plus false credit for "nothing found".
- **Diverge or negate (AI and science, negation)**: **not in this paper.** It has no content on scientific discovery, divergence or negation. I did not identify which paper the summary means.
- **When Reject Turns into Accept (prompt injection in PDFs)**: **not in this paper.** It has no content on prompt injection or PDFs.

## Relation to V9
**Relation: overlaps** (the framing, not the findings). It is independent evidence that consistency checks cannot validate an LLM judge, which is V9's §4.4 point "The judge is consistent with itself, not with the grade... A consistency check would not reveal the problem." The two papers differ on every substantive axis:
- Ground truth: V9 uses an executed grade (running the system on hidden data). This paper uses human preference or correctness labels on static benchmarks.
- Setting: V9 grades agentic auditing runs, logs and "nothing found" claims. This paper grades pairwise single-turn responses.
- Failure mode: V9 finds undecidability (72 of 77 wrong answers cannot be decided from the agent's log), false credit for unsupported `none` (31/39), prompt changes that move only the threshold (AUROC 0.48-0.58), reordered system comparisons (13 of 36 pairs; Terra − Luna gap +0.86 → −0.19), an abstaining judge that answers "cannot tell" on 114 of 130, and a keyed positive control. This paper finds position bias, chance inflation of exact match, and benchmark-dependent rankings.
- Magnitude: V9's judge is near zero against the grade (κ −0.006) while agreeing with itself at κ 0.39. Its paradox judges still reach κ 0.29-0.44 on MT-Bench and JudgeBench.
- Framing: V9's edge argument (verification easier than generation, or privileged information) is absent from this paper.

**What V9 adds beyond it:** an executed grade instead of human labels, so validity can be measured where human labels do not exist. An agentic absence-of-evidence setting in which the judge's materials do not contain the answer. The decidable versus undecidable split, with a script baseline (balanced accuracy 0.97 vs 0.75). Downstream harm to system rankings. The keyed positive control showing that information, not judge skill, is the bottleneck. The edge argument.

**Where in V9:** §4.4, the paragraph "The judge is consistent with itself, not with the grade", as one clause noting that test-retest reliability does not imply validity. Optionally a one-line judge meta-evaluation entry in §7 Related Work. Because it is withdrawn, it should never be the only support for the claim. Pair it with a standard psychometric source, or the non-withdrawn work it cites (Stureborg et al. 2024; Schroeder and Wood-Doughty 2024), after checking those separately.

**Citing sentence (≤ 30 words):** "Self-agreement does not certify a judge: Norman et al. (2026, withdrawn) find reproducible judges with severe position bias; ours agrees with itself (κ 0.39) but not with the executed grade."

**Priority: optional.** The overlap is real but generic, and arXiv administrators withdrew the paper for not meeting research content quality standards. If cited, mark it as withdrawn.
