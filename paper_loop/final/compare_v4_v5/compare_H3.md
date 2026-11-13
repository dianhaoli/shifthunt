# Comparison H3: first (paper_X) vs second (paper_Y)

Verdict: first (X) is the stronger workshop submission, by a clear margin. Scores: X 7.0, Y 6.0 (borderline accept).

## Substance and soundness
- X adds a judge-validity ladder (query log, placebo log, rule baseline, other judge models, sceptical prompt, report-free control, 9-system leaderboard reordering, PPI). This is the most on-topic result for the workshop (LLM-judge reliability vs validity, ground truth beyond reviewer opinion).
- X replicates the trap result on two fresh held-out traps (Terra 13/14, Luna 2/10) and reports an outcome "outside every band" honestly. Y has only the six public items.
- X has a full pre-registration ledger with multiplicity handling, a Bonferroni check, and a budget-curve framing (Box 2) that avoids a misleading exchange rate. Y's "worth up to 64 queries" is looser and its Claim 2 leans on an arithmetic bound range (-0.21 to +0.38).
- Y's judge study is thin: a report-only judge, no query-log arm. It names the log as "the natural next arm", and X has already run it. Y's Claim 2 is therefore weaker.
- Both keep claims scoped (Terra only, rank-2 only), but X is more careful.

## Clarity and length
- Y reads better: the motivation (oversight, "nothing found" errors), terms and narrative are easier to follow. X is very dense, with many labels and codes (C6 J5', L1/L2, X1-X4), which hurts a reader who is new to the paper.
- Main-body words excluding references: X about 5.4k, Y about 7.2k. X has 2 figures and 4 tables, and is tight but plausibly within 8 AAAI two-column pages. Y has 1 figure and 4 tables and is likely to overflow 8 pages. Compliance risk is higher for Y, and the appendices of both are very long, though they are appendices.

## Fit to the call
- X hits more listed topics: judge reliability/calibration, sensitivity of rankings, contamination via held-out items, cost-normalized reporting, statistical power, and a matched-budget statement.
- Y fits the sample-efficiency and process-trace topics but gives less on instrument quality.

## Scores
- X 7.0: strong content, dense. Y 6.0: clear but less complete.

## Merge advice
Submit X. Take Y's motivation paragraph (oversight and the cost of a false "nothing found"), its plainer running-example prose, its Table 2 reference-policy and agent layout, and its "failure and success modes" table in condensed form. Keep X's judge ladder, fresh-trap replication, ledger and Box 2. Cut X's label and code density: move ledger rows and C-codes to the appendix, define each term once, and trim Section 5.2 to the key numbers so the main text stays safely within 8 pages.
