# V10 addendum: framing against the call (17 Nov, from the author; facts-checked)

## 1. Remove the overclaim "usually graded by an LLM judge"
Replace it with the narrower practice, using the organizers' framing:

> "Where a research agent's output has no executable check, benchmarks fall back on an LLM judge, validated against
> human agreement on a subset."

Support it only with what the fact cards state.

**AstaBench (bragg2026, ICLR 2026).**
- 11 benchmarks; 6 are scored by LLM judges against rubrics, including E2E-Bench.
- The judge was validated against expert rankings on one of them, ScholarQA-CS2: system-level Kendall τ 0.467 (0.800
  without Elicit) and instance-level agreement 68.1% (App. E.3).
- The E2E-Bench rubric scoring got a 92% human spot check on 50 items (App. F.9).
- Do NOT write "ten subsets": it is 11 benchmarks.

**PaperBench (starace2025, ICML 2025).**
- Hierarchical rubrics are *co-developed with the papers' authors*: drafted by research engineers and checked by an
  original author. Do not write "author-written".
- An LLM judge (o3-mini SimpleJudge) grades the leaf criteria. Its F1 is 0.83 on JudgeEval, a separate
  human-graded set.

## 2. Frame the audit as a small scientific investigation
The agent forms hypotheses, runs experiments under a budget, and reports a claim. A "nothing found" is a null
result. A wrong one is the plausible-sounding but incorrect finding the call worries about. Put this in the
introduction, in one or two sentences.

## 3. Put our number next to theirs (cautiously)
- AstaBench's judge agrees with experts at system-level τ 0.467.
- Ours agrees with the executed grade at Kendall τ_b 0.23 across nine pre-specified agent-and-arm systems (C19: run
  bootstrap −0.09 to 0.46; 13 of 36 pairs reverse).

State plainly that the references differ (expert rankings vs an executed grade) and the systems differ. The
comparison gives a sense of scale, not a like-for-like test. One sentence, in §4 (consequences) or the related work.

## 4. Matched budgets (CFP rule)
One short statement, in §2 or §3:
- Within a harness, agents share the same exact-query, tool-call, forward and time limits.
- Comparisons between agents are made only within a harness: Terra vs Luna in the same harness. The Haiku/Claude
  harness is descriptive only.
- Token budgets are not matched across harnesses. Give the token figures from the facts (largest requests: about
  268k tokens for GPT, against a 475k window, and 479k for Haiku), or say where they are reported in the appendix.

## 5. Cost-normalized reporting
Add one sentence, with the numbers from the facts:
- a transcript-level judge call costs about $0.08 (C6b: $29.25 for 354 calls);
- give the key-level per-call cost if the facts have it (K spend $1.14 on 130 calls, so about $0.009 per call;
  check the facts).

The key is cheaper and more valid.

## 6. Tie back explicitly
Use the call's tagline, "what to measure, how to measure it, and how good the instrument is", in the first
paragraph of the introduction. Map the results to the call's topics, woven into the prose rather than listed:

| Topic in the call | Our result |
|---|---|
| LLM-as-a-judge reliability and calibration | The default pass on "nothing found"; the stricter cut-off (25 → 11 of 52) |
| Ground truth stronger than reviewer opinion | The executed grade and certified absences |
| Process-level evaluation from execution traces | Report vs full transcript |
| Sensitivity of rankings to judge, prompt and rubric | Terra vs Sol; the sceptical prompt; 13 of 36 pairs reorder |
| Reliability vs validity | κ 0.39 self-agreement vs about 0 with the grade |
| A reported gap "attributed to the systems" | +0.86 executed reads −0.19 from reports and +0.28 from transcripts |

## 7. Length
6–8 pages in the AAAI two-column kit, references excluded. The appendix carries the rest as a supplement.
