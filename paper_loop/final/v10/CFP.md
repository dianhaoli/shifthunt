# Effective and Efficient Evaluation for AI Scientists

**What to measure, how to measure it, and how good the instrument is.**
AAAI-27 workshop, 22 Feb 2027, Montréal. Submission deadline 20 Nov 2026 06:00 UTC (OpenReview). Notification 2 Dec 2026.

## Topics
**What to measure:**
- operational definitions of novelty, correctness, rigor and significance, and their construct validity;
- ground truth stronger than reviewer opinion (held-out empirical outcomes, lab confirmation);
- process-level evaluation from agent execution traces.

**How to measure it:**
- end-to-end and stage-wise benchmarks for research agents;
- contamination and leakage, and tasks that stay valid after training exposure;
- LLM-as-a-judge reliability, calibration and adversarial robustness, with cost-normalized reporting.

**How good is the instrument:**
- reliability vs validity of evaluation scores;
- statistical power and minimum detectable effect;
- sample-efficient evaluation via adaptive item selection, IRT, best-arm identification, and off-policy reuse of prior judgments;
- sensitivity of rankings to judge, prompt and rubric.

**Also in scope:**
- expert elicitation as an instrument with its own error model;
- reproducibility infrastructure (execution traces, seeds, cost logs);
- hazard and dual-use assessment for autonomous research in chemistry and biology;
- Goodharting once a metric becomes a target.

## Call for papers
"Submissions should directly address the evaluation of autonomous scientific discovery."

| Paper type | Length | Notes |
|---|---|---|
| Full | 6-8 pp | original research on evaluation methodology, benchmarking or verification |
| Position | 2-4 pp | |
| Resource / artifact | 2-4 pp | submitted with the artifact; reviewed on whether it runs and is documented |
| Reproduction / negative result | 2-4 pp | |

## Submission rules
- Use the AAAI-27 two-column kit.
- Submissions must be anonymized; review is double-blind with at least 2 reviews per paper.
- Non-archival.
- Accepted papers require in-person presentation.
- Papers that compare systems must report at matched compute and token budget, or explain why matching is infeasible.
