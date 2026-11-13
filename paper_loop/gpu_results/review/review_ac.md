# Area chair review: V4 plus the GPU results (13 Nov)

Score on V4 (12 Nov): **6.5**, a borderline accept. With the new results written in well: **8**, a clear accept and a spotlight candidate.

## Verdict
The judge results (C6, C8, C12, C19, C21), V4's weakest leg, now answer the CFP's central question ("how good is the instrument") better than anything else I expect in the pool:
- the exact-query log does not rescue the judge (κ 0.06);
- a no-report control shows that the `none` leniency is the judge's prior (31/39 vs 1/39);
- the judge reorders a nine-system leaderboard (τ_b 0.23);
- its 214 verdicts are worth 0.0 certified grades under PPI.

Claim 1 becomes a measured budget curve: Terra with the proxy at 4 queries (12/12) beats itself blind at 8 (6/24). Claim 3 gains held-out traps and a budget arm that separates targeted from blanket widening. Depth is still not shown for agents. The risk now is length and bookkeeping, not evidence.

## The 15 V4 issues
1. **Rank-2 traps: partly.** Two fresh unseen traps: Terra 13/14, Luna iso(main) 3/10 (p = 0.002); 5 trap items. R6 was cancelled, so depth rests only on scripted X1 [priv].
2. **Length: open, and harder.**
3. **Rhetoric: resolvable.** C12 supplies the measured replacement.
4. **Framing: open.**
5. **Judge dismissible: resolved.** L1 (log plus true logits) gives κ 0.06, a placebo log 0.20. Haiku as judge errs the other way (false blame 82-85/87). Terra judging Luna credits 35/53 failures, which answers "Terra judges Terra". On fresh traps: 6/10 failures credited.
6. **Claim 2 abstract: resolved.** C19: Terra − Haiku +0.375 → −0.06; the judge's budget curve inverts (16 > 64); the Terra-Luna trap gap 0.86 → −0.19.
7. **Targeted vs blanket: largely resolved.** At B = 4, top-two and calibrated policies score 0.49; Terra 12/12, with 2.67 texts on the anomalous probe vs 0.44 per other probe. A budget manipulation, not a forced-allocation test.
8. **Bundled proxy: open, and sharper** (see attack 1).
9. **Inference: partly.** The 36 fit goes; X2 measures error (1.3% / 1.4%). Still missing: item-clustered κ, the Luna [decoy]-count script, the Luna timing disclosure.
10. **Removal nominal: open.**
11. **Denominators: open, and worse.**
12. **Robustness analyses: open.**
13. **Figures: mostly resolved.** Figure 2 is now measured. The cost-per-pass figure is still missing (spend is pending).
14. **Transfer: open.**
15. **Structure: open.**

## New attacks the results open
1. **The scripted "bounds" are beaten, so something unmodelled is at work.** At 4 queries Terra beats even the Bayes policy that knows the trap rank (0.49). Either Terra uses free approximate scoring, or the trap has a tell in the proxy view (the "anomalous probe"). Either way:
   the references are not bounds, the proxy's value is not "a ranking", and the traps may look like detectable artifacts. Name what makes the probe anomalous, or say it is unidentified.
2. **Claim 3's one-batch sentence is now false.** One-burst: Haiku 9/15, Opus 10/16, Sonnet 11/16, Terra blind 0/24. Terra and Luna differ in batch width on the trap.
3. **H2 fell outside every pre-registered band.** Report it that way, not as "partial".
4. **Rank depends on the metric.** One fresh [main] sits at rank 3 by |latent ratio|. Define rank once.
5. **The Limitations line on rank-6 traps is wrong** (one probe, unclean checker).
6. **The τ comparison is only marginal.** The run-bootstrap upper bound (0.46) beats AstaBench's 0.467 by a hair, and AstaBench compares the judge with experts, not certified grades. Use it as context.
7. **The judge disagrees with itself** (test-retest κ 0.44, 0.32). Show that this does not explain κ near 0 (attenuation ceiling about 0.66).
8. **A simple rule beats the judge.** "Credit any named answer" reaches κ 0.67, so reviewers will ask whether a better prompt fixes the judge.

## What round 2 adds
- **L3 (answer key): the one round-2 result I care about.** If the judge with the key agrees with the grade, the failure is about information, not competence, and that rebuts attack 8. If it still fails, the story changes.
- **The third fresh trap: modest gain.** It makes 6 trap items and an item-level floor near 0.03, but every trap is still at rank 2.
- **L2, L2r, Haiku on L2: little.** They fill in the ladder.

None of round 2 moves my score more than ±0.5.

## What would make it a spotlight
One thesis: proxy-and-gold evaluation applied to two cheap proxies, the SAE tools and the LLM judge. Each gets one figure (budget curve; judge ladder plus leaderboard reversal), within 8 pages.

## Top 3 writing actions
1. **Rewrite Claim 1 as the measured budget curve.**
   - With the proxy: 4 → 12/12 and 8 → 23/24.
   - Without it: 8/16/64 → 6/24, 16/24, 24/24.
   - Call the scripted lines "reference policies"; drop "worth X queries" and the 36 fit.
2. **Make Claim 2 an instrument-validity section.**
   - One ladder table: L0r/L0/L1/placebo/rule/Haiku/retest.
   - The C12 control, the C19 reversals, and C21 (zero PPI value; audit `none` first).
   - Say plainly that J5′ and J6 were not confirmed.
   - Retire the "−0.21 to +0.38" range.
3. **Narrow Claim 3 and the title to what agents showed.**
   - Targeted, one-step widening on 5 trap items.
   - Depth shown only by scripted policies.
   - Fix the one-batch claim, the rank-6 line, H2 and the Luna timing.
   - One denominator per claim; reconcile the rest in an appendix.
