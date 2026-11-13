# What the reviewers say now (V4 + GPU results)

Five reviewers: statistician (Stats), agent-evaluation (Agents), mech-interp (Interp), skeptic (Skep), area chair (AC). All assume the new results are written in well.

## 1. Scores

| Reviewer | V4 | With new results |
|---|---|---|
| Stats | 6.5 | 7.5 |
| Agents | 7.0 | 8.0 |
| Interp | 6.5 | 7.5 |
| Skep | 6.5 | 7.0 (7.5 if L3 is clean) |
| AC | 6.5 | 8.0 |
| **Mean** | **6.6** | **7.6** |

Borderline becomes a solid accept (AC: spotlight candidate). The main risk is now length and bookkeeping, not evidence.

## 2. The 15 old issues

| # | Issue | Resolved | Partly | Open |
|---|---|---|---|---|
| 1 | Only rank-2 traps | | 5 | |
| 2 | Over length | | | 5 (harder) |
| 3 | Rhetoric | 4 | 1 | |
| 4 | AI-scientist framing | | 1 | 4 |
| 5 | Judge easy to dismiss | 4 | 1 | |
| 6 | Claim 2 too abstract | 5 | | |
| 7 | Claim 3 not causal | 1 | 4 | |
| 8 | Proxy bundles ranking + free scoring | | 1 | 4 (sharper) |
| 9 | Weak inference | | 5 | |
| 10 | "Remove it" only nominal | | | 5 |
| 11 | Shifting denominators | | | 5 (worse) |
| 12 | Robustness analyses missing | | | 5 |
| 13 | Figures | 1 | 4 | |
| 14 | Transfer to other domains | | | 5 |
| 15 | Structure | | | 5 |

Open items 2, 4, 11, 12 and 15 need only writing. Items 8, 10, 14 and depth (#1) would need runs.

## 3. New criticisms the new results invite (most-raised first)

1. **H2 fell outside every pre-registered band (5/5).** Luna's 3/10 misses its condition by one run, and "partial" is the code's fall-through label. *Fix:* report it as "outside every pre-registered band". The p = 0.002 rests on 2 items, so lead with item counts.
2. **"Credit any named answer" (κ 0.67) beats every judge rung (5/5).** Critics will say the prompt is broken. *Defence:* that is the finding. Note that the 0.67 depends on the design (1 in 4 answers should be `none`), and point to L3.
3. **The scripted "bounds" are not bounds (4/5).** At 4 queries Terra (12/12) beats the Bayes policy that knows the trap rank (0.49). Free approximate scoring or a tell in the proxy view is doing the work. *Fix:* call them "rank-only reference policies" and say Terra's signal is unidentified.
4. **Depth is not shown for agents (4/5).** Every trap is at rank 2. A "check rank 2" habit would pass the held-out traps, and the calibrated prior scores 0 at rank ≥ 3. *Fix:* title and Claim 3 say "one-step widening, 5 rank-2 items"; depth is scripted only.
5. **"Rank 2" depends on the metric (4/5).** One fresh [main] is rank 3 by |latent ratio|. *Fix:* define rank once; report traps under both readouts.
6. **Reliability vs validity (4/5).** The judge's test-retest κ is only 0.44 / 0.32. *Defence:* that caps agreement near 0.66, so κ of 0.002–0.06 means wrong, not noisy. Never say the log "hurts" (0.06 vs placebo 0.20 is noise).
7. **The AstaBench comparison overreaches (4/5).** An upper bound of 0.46 vs 0.467 is not a test, and the 9 systems share items. *Fix:* context only; say "reorders the leaderboard", and the Terra–Luna gap is "erased", not "reversed".
8. **"One batch" is false (4/5).** One-burst rates: Haiku 9/15, Opus 10/16, Sonnet 11/16, blind Terra 0/24. *Fix:* Claim 3 is about batch *width* on the trap.
9. **Multiplicity (4/5).** About 20 hypotheses, with J5′ and J6 not confirmed. *Fix:* put one status table in the body.
10. **C21 is in-sample and weak (3/5).** "Audit `none` first" came from the same runs and wins only early. *Fix:* exploratory; drop from contributions.
11. **Haiku is not a competent second judge (4/5).** It credits almost nothing. *Defence:* it fails the other way; call it a check, not validation.
12. **Rank-6 Limitations line is wrong (2/5).** One probe, unclean checker, R6 cancelled. *Fix:* correct it.
13. **No budget curve inside the proxy arm (2/5).** 12 runs cannot show one; do not interpret Luna 3/12 vs 5/36.
14. Single mentions: the top arm is saturated (no headroom); Luna "never widens" should read "rarely"; cite Marks et al. and Bricken et al. on report-graded auditing.

## 4. Strongest new results (reviewers' view)

- **All 5:** the judge evidence ladder plus C12. With the exact-query log and true logits the judge stays near chance (κ 0.06). With no report, it credits an unsupported `none` 31/39 vs an unsupported true cue 1/39, so the leniency is its own prior. With C19 (Terra − Haiku +0.375 → −0.06, τ_b 0.23) and PPI value 0.0, this now carries the paper.
- **Runner-up:** Terra at 4 queries with the proxy (12/12) vs blind at 8 (6/24) (Agents, Interp, AC). Stats prefers C14 (13/14 on unseen traps, pre-registered before any run).

## 5. What round 2 adds

Little, except one run.
- **L3 (judge given the answer key)** matters to all five, either way. Fails with the key: the instrument is broken. Passes: the failure is missing evidence, which answers "bad prompt".
- **F2-c (third fresh trap):** better item statistics (floor 1/64), still rank 2, nothing on depth.
- **L2/L2r (SAE view):** closes the last access objection; no change expected. Haiku on L2: little value.

Expected score effect: at most about +0.5 (AC), or +0.5 if L3 is clean (Skep).

## 6. Top writing actions (by consensus)

1. **Narrow Claim 3 and the title (5/5):** one-step widening on 5 rank-2 items, depth from scripted policies only, "reference" not "bound", batch width not "one batch", H2 out of band.
2. **Rebuild Claim 2 as instrument validity (5/5):** test-retest → ladder table (one n per row) → any-named baseline → C12 → C19 reversals → PPI 0. Drop the AstaBench test.
3. **One pre-registration ledger in the body (4/5):** each hypothesis with its commit time, its outcome, and a stated multiplicity stance.
4. **One denominator per claim (4/5):** reconcile the populations in the appendix.
5. **Claim 1 as the measured budget curve (3/5):** proxy 4 → 12/12, 8 → 23/24; blind 8/16/64 → 6/24, 16/24, 24/24. Drop "worth X queries".
6. **Fit 8 pages (3/5):** merge §6 into §5.3, cut §7 to a paragraph, move Haiku arms and deviations to the appendix, add spend and a cost-per-pass figure.
