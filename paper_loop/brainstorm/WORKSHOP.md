# Workshop page (eval-ai-scientists.github.io/aaai27), as provided by the author, 12 Nov 2026

**Effective and Efficient Evaluation for AI Scientists. What to measure, how to measure it, and how good the instrument is.**
AAAI-27 workshop, 22 Feb 2027, Montréal. Deadline 20 Nov 2026 06:00 UTC (OpenReview). Notification 2 Dec.

## Why this workshop
Science is being automated; evaluation methods have not kept pace. There are no reliable benchmarks, verification protocols or agreed measures, so genuine advances are hard to separate from plausible-but-incorrect findings.

Existing benchmarks each measure a system:
- AstaBench: 2,400+ problems, 57 agents, cost-normalized leaderboard.
- PaperBench: replication rubrics written with the original authors.
- MLR-Bench, MLAgentBench: stages of the ML research cycle.

Each of those measurements comes from an instrument, and the instrument's accuracy is established against human agreement. AstaBench scores end-to-end discovery with an LLM judge reading an auto-generated rubric. It checks the judge against expert ranking on one of its ten subsets (Kendall tau 0.467). It also finds that **a system left out of the rubric's construction scores lower on identical work**, which its authors record as an open question. This workshop is where that question is asked, of benchmarks, rubrics and judges alike, *so that a reported gap between two systems can be attributed to the systems*.

**Audience:** LLM and agentic AI, benchmark and evaluation methodology, statistics, AI for Science (chemistry, biology, physics, materials), metascience and peer review, industry.

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
"Submissions should directly address the evaluation of autonomous scientific discovery." Use the AAAI-27 two-column kit; anonymized; double-blind; at least 2 reviews; non-archival; in-person presentation. Papers that compare systems must report at matched compute and token budget, or explain why matching is infeasible.

| Paper type | Length | Notes |
|---|---|---|
| Full | 6-8 pp | original research on evaluation methodology, benchmarking or verification |
| Position | 2-4 pp | |
| Resource / artifact | 2-4 pp | submitted with the artifact; reviewed on whether it runs and is documented |
| Reproduction / negative result | 2-4 pp | |

Attendance is 45-65 by invitation based on submissions.

## Speakers (what they care about)
- Irina Rish (UdeM/Mila): evaluation that stays reliable under distribution shift.
- Xiaowu Dai (UCLA): uncertainty quantification for ML; mechanism design for LLMs.
- Zhijing Jin (Toronto): causal reasoning with LLMs, from benchmarks to AI scientists.
- Hongtu Zhu (UNC): evaluation methodology and validity, from statistics and biomedical data science.
- Yifan Hu (Rutgers): decision-making under uncertainty; budget-constrained test-time compute for LLMs.
- Phoenix Peng (Gestala): ultrasound BCI, neuroscience and AI.
- Mengdi Wang (Princeton): statistically rigorous evaluation of autonomous biomedical research agents.

## Organizers (what they care about)
- Tianyu Shi (McGill, primary contact): auditable, budget-aware evaluation of agentic systems (CARE, DynaWeb); self-evolving agents, agent societies.
- Bang Liu (UdeM/Mila): builds scientific agent workflows (AFlow, Data Interpreter, HoneyComb).
- Fan Zhou (SUFE): statistical metrology of evaluation, "how good is the instrument"; StatEval, StatProver, DataSciEval; AC for the NeurIPS 2026 Evaluations & Datasets track.
- Perouz Taslakian (ServiceNow/McGill/Mila): agentic benchmarks (InsightBench), relational reasoning, causal discovery.
- Samira Ebrahimi Kahou (Calgary): robustness and generalization under distribution shift, XAI.
- Steve Drew (Calgary): cloud/edge AI, federated learning, privacy.
- Senior advisor Hongtu Zhu (JASA editor; statistics).
- Supporting team includes work on the reliability of LLM judges (Meijia Chen), adaptive test-time computation (Zach Wang), and trustworthy evaluation of agentic systems (Haolun Wu).
