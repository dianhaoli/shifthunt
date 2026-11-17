# Old Ideas, Novel Problems (arXiv 2610.02022): citation check

## Identity (checked against the arXiv API and the full text on alphaXiv)
- Title: Old Ideas, Novel Problems: The Instability of LLM-Based Novelty Evaluation
- Authors: Noy Sternlicht, Simra Shahid, Peter Jansen, Daniel S. Weld, Pao Siangliulue, Tom Hope (Hebrew University of Jerusalem, Allen Institute for AI, Microsoft, University of Arizona, University of Washington)
- arXiv: 2610.02022 (v1 2026-10-01; v3 2026-10-26), cs.CL
- Venue: arXiv preprint. The text names no venue. It uses ACL-style Limitations and Ethical Considerations sections, but that does not establish a venue.

```bibtex
@misc{sternlicht2026oldideas,
  title         = {Old Ideas, Novel Problems: The Instability of {LLM}-Based Novelty Evaluation},
  author        = {Sternlicht, Noy and Shahid, Simra and Jansen, Peter and Weld, Daniel S. and Siangliulue, Pao and Hope, Tom},
  year          = {2026},
  eprint        = {2610.02022},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}
```

## Main findings (with numbers)
1. **Benchmark.** Novelty labels are mined from ICLR 2026 review text. "Novel" papers have unanimous praise, were accepted and sit in the top decile of their area; "lower-novelty" papers have unanimous criticism, were rejected and sit in the bottom decile. LLM extraction of these labels agreed with an expert on 94% of 50 samples. There are two setups, Human-Only and Human+Generated. In the second, the negatives are single-pass ideas from claude-sonnet-4-5. A blind expert annotated 30 Human+Generated pairs, 25 of them pairs the strongest judge got wrong, and sided with the human idea in all 30.
2. **Six judges** (sonnet-4-5, opus-4-5, opus-4-6, gpt-5.1, gpt-5.2, gpt-5.4), judging pointwise and pairwise, under one-at-a-time changes: prompt P1-P5, retrieval, reasoning effort, verdict aggregation and idea format.
3. **Prompt brittleness.** On pairwise Human+Generated:
   - P3 ("reviewers found one idea novel and the other not") improves every judge, by over 20 points in some cases.
   - P4 deletes the reviewer sentence, and gpt-5.4 drops below 50%.
   - For gpt-5.4 the P3-P4 gap is 52.6 points, so the two prompts "disagree on at least 52.6% of pairs (55.8% in practice)". The paper notes this instability is independent of the labels.
   - In the same table, P4 costs gpt-5.4 -37.0 (to 40.9), and P3 gives opus-4-6 +15.6 (to 93.5) and opus-4-5 +29.2 (to 92.2).
4. **Format.** When ideas are rewritten as plans, instability grows. Some changes flip more than two thirds of the verdicts, and P4 costs gpt-5.4 -55.8 on Human+Generated and 24 points on Human-Only (about 7 on abstracts).
5. **Effects do not transfer across judges.** The same change helps one judge and hurts another; "A configuration validated on one judge thus carries no guarantee for another."
6. **Generated ideas are harder.** Judges degrade once the negatives are LLM-generated, falling below chance for some backbones. They also tie more often: opus-4-6 up to 35% ties, sonnet-4-5 over half.
7. **Reasoning and retrieval help little.**
   - Low instead of high reasoning effort costs at most 7 points.
   - Retrieval adds at most 16 points, and only for some models.
   - An agentic web-search judge on gpt-5.6-sol (xhigh reasoning) reaches 0.78 macro-F1. That is 11 points below opus-4-6, at 10x the cost.
8. **Dedicated evaluators lose.** Idea Novelty Checker and AI-Scientist are beaten by the cheapest prompted setup by 8-29 macro-F1, at up to 32x lower cost.
9. **Comparing ideation systems** (no gold label): opus-4-5 vs sonnet-4-5 and gpt-5.4 vs gpt-5.1, over 154 pairs.
   - "Changing the prompt alone flips a quarter to a third of the verdicts on average, and moves the share of pairs awarded to the stronger system by up to 29 points" (§5).
   - Per judge, the range is 13.0-56.5%: Claude judges 26.0-56.5%, GPT judges 13.0-25.3% (App. C.2.2, Table 8).
   - For sonnet-4-5, the stronger system's win rate is 38.3% under the reference prompt and 66.9% under P3.

## Checks of claims a summary attributed to it
- **"One added sentence changed verdicts on over half of identical idea pairs."** ACCURATE, with qualifiers.
  - Abstract: "simply telling the judge that reviewers found one idea novel and the other not can change its verdict on more than half of the identical idea pairs it is shown, shifting pairwise accuracy by over 50 points".
  - §5: "deleting the sentence about reviewers (P4) makes gpt-5.4 collapse below 50% ... they disagree on at least 52.6% of pairs (55.8% in practice)".
  - The figure is the worst case, for one judge (gpt-5.4) on pairwise Human+Generated. It is not typical.
- **"Prompt changes flipped a quarter to a third of comparisons."** ACCURATE.
  - §5: "Changing the prompt alone flips a quarter to a third of the verdicts on average".
  - This is on average, in the setting where two ideation systems are compared. The per-judge range is 13.0-56.5%.
- **"Judges are validated on human-written papers but used on generated ideas."** ACCURATE. Abstract: "validated, if at all, on human-authored papers rather than on the generated ideas they are meant to score"; Conclusions: "Validating a judge on human-authored papers ... says little about how it will behave on the generated ideas it is asked to score."
- **The other items** are attributed to other papers: More Convincing (self-play on grade-school math, 0.72 → 0.94 vs 0.20, 0.72 → 0.01), Gaming the Judge (+20-30 points), Not an Oracle (parser defaulting to 3, 23% → 80%, 100% vs 68%), One Token (":" and "Thought process:", about 80%), Grounded but Not Immune (40%), Reliability without Validity, Diverge or negate, and When Reject Turns into Accept (PDF prompt injection).
  - NONE of them appears in this paper. I searched the full text for self-play, grade-school/GSM, keyword stuffing, answer keys, "Thought process", expert-reviewed notes, injection, validity and negation, and found nothing. They must be checked against their own sources. This file does not verify them.
  - The only nearby content is in this paper's related work: authority cues (Ye et al. 2025) and adversarial attacks on LLM judges (Raina et al. 2024). It gives no numbers for either.
- **Reliability without validity / does it pre-empt "consistent, not valid"?** NO. This paper shows judges are *unstable* across plausible configurations, the opposite of our self-consistent judge. It reports no test-retest agreement next to validity, and it averages over 3-6 calls by design. Its one near-phrase is about distribution shift, not self-consistency: "a judge that looks reliable against one type of data can invert against another" (App. C.2.1).

## Relation to V9: supports
- **Domain and ground truth.** It is independent evidence from a different domain (novelty of research ideas) that LLM judges of AI-research output are fragile. Its labels are mined from peer review, with no executed ground truth.
- **System comparisons.** Like us, it shows that judge choices reorder system comparisons: a quarter to a third of verdicts flip, and win rates move up to 29 points. We show 13 of 36 reversals, and Terra-Luna going from +0.86 to -0.19.
- **Prompts.** Their prompt edits move accuracy by up to 50+ points. We find prompts move only the threshold (AUROC 0.48-0.58). These do not conflict: their changes alter the question asked, and our judge has no signal to discriminate with.
- **It does not pre-empt us.** It has none of the following:
  - an executed grade;
  - the undecidability of "nothing found";
  - the log-reading-script comparison;
  - an answer-key positive control;
  - an abstaining judge;
  - a reliable-but-not-valid result.

## What we add beyond it
- Ground truth from execution rather than review-derived proxy labels.
- The identifiability result: 72 of 77 wrong "nothing found" answers are undecidable from the log.
- A script baseline on the decidable slots (balanced accuracy 0.97 vs 0.75).
- Self-agreement (κ 0.39) next to near-zero validity, which is a self-consistent failure rather than instability.
- The answer-key control, which shows the judge works when it has privileged information.
- An abstaining judge that removes false credit at the price of "cannot tell" on 114 of 130 slots.
- The edge framing.

## Where in V9
- **§7 Related Work**, "Judges for research agents" paragraph: add a sentence after the ABC sentence.
- Optionally, a parenthetical in **§4.4** at "The judge also reverses 13 of 36 pairs ...".

## Citing sentence (29 words)
"Prompt changes alone flip a quarter to a third of LLM novelty judges' system-comparison verdicts (Sternlicht et al. 2026); against an executed grade, ours reverses 13 of 36 pairs."

## Priority: should
