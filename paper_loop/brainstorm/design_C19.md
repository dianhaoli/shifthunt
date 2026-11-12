# C19 design: the leaderboard in AstaBench's units (Kendall τ, certified vs judge-graded) and the cost-accuracy frontier under each grader

Status: a design ready to freeze. Nothing has been run on the GPU box. Part A below was computed locally on 12 Nov from committed counts only, at $0. Its scripts are in `brainstorm/c19_partA/`. Rule check: this design names items only by episode id and never pairs a shipped episode with its cue property.

---

## 0. What changed while designing (read first)

The committed marginals in `results/blackbox_1112/judge/judge.json` already pin down much of the result, before anyone opens the private per-slot verdicts. Those marginals are certified passes, false credit and false blame for each of agent, access and population. Enumerating every integer split consistent with them gives 18 false-credit splits × 207 false-blame splits = 3,726 joint assignments, the same 18 and 207 as Appendix H. Run `python3 -I enum2.py && python3 -I analyse_bounds.py` (plus `frontier.py` and `pairs.py`) in `brainstorm/c19_partA/`. The enumeration gives the following, for **every** feasible assignment:

- **The judge's ranking of the nine pre-specified systems (L9, §2) has Kendall τ_b between −0.06 and +0.37 against the certified ranking.** That is below AstaBench's 0.467 in all 3,726 assignments. The median over assignments is 0.17, but that median is not a probability.
- **Three pairs whose certified order is established are reversed under every assignment:**
  - Haiku-open (13/28 = 0.46) vs Terra-BB64 (24/24 = 1.00): certified Fisher p = 9e-6. The judge puts Haiku-open above BB-64 by +0.07 to +0.39.
  - Terra-BB16 (18/24) vs Terra-BB64 (24/24): p = 0.022. The judge gives BB-16 exactly 21/24 and BB-64 12-19/24, so **the judge's budget curve for Terra is non-monotone: 16 queries beat 64.**
  - Opus-open (11/16) vs Terra-BB64: p = 0.007.
  - Opus vs Sonnet is also reversed in every assignment, but its certified gap is one run (p = 1.0), so it does not count.
- **The Terra-Haiku gap is reversed, not merely closed, on the matched pooled populations (main study + Block 1).** Certified it is +0.32 (69/88 vs 24/52); judge-implied it is −0.08 to −0.02 in every assignment. In Block 1 alone the judge-implied gap is −0.14 to +0.07, against certified +0.32.
- **The cost-accuracy frontier changes in every assignment.** These frontiers use cost per run and the hard-slot rate, with exact queries priced at $0 as in AstaBench. The certified frontier is {Terra-BB64} alone. The judge frontier always contains {Terra-BB64, Terra-BB16} plus one to three others. Opus-open ($3.72 per run, 10× BB-64) is on it in 78% of assignments, and Terra-open in 37%.

**Consequence for the design.** The headline "τ below AstaBench's" is a deterministic bound and needs no box run. It can go in the paper today, worded as a bound. What the private verdicts add is the exact point values, sampling uncertainty (bootstrap intervals), per-pair flip probabilities and frontier membership probabilities. They also replace the integer-split bounds in Appendix H (Terra budget effect −0.21 to +0.38) with exact rates. The pre-registered hypotheses below therefore test only what the bounds leave open. Section 1 lists each known bound next to its test, so that no reader thinks a guaranteed result was predicted.

---

## 1. Hypotheses (frozen before the box agent opens `slots.json` for this analysis)

All hypotheses use the **hard slot**: the certified naming grade of the hard probe versus the judge's `correct` verdict on it, one slot per run. This is J1's unit and Table H1's. Judge-implied rate = share of runs whose hard slot the judge credits.

| id | hypothesis (threshold written now) | already known from committed counts | confirmed if |
|---|---|---|---|
| **H1** (primary) | Sampling uncertainty included, the judge's L9 ranking agrees with the certified ranking less than AstaBench's judge agrees with experts | point τ_b ∈ [−0.06, +0.37] | the 97.5th percentile of the run-level stratified bootstrap distribution of τ_b is < 0.467 |
| **H2** | At least one established certified order is robustly reversed | 3 established pairs reversed at the point estimate in every assignment | ≥ 1 pair meets the established-and-robust definition in §3.3 |
| **H3** | In the matched main study (4 agents × 16 runs, same items, same allocation), the judge shrinks the Terra-Haiku gap to less than half (certified +0.375, 14/16 vs 8/16) | judge gap ∈ [−0.25, +0.31] | judge-implied gap < +0.1875 at the point estimate, *and* the bootstrap P(gap ≥ +0.1875) < 0.10 |
| **H4** | For Terra in Block 1, the judge halves the confirmatory budget effect (BB-64 − BB-8, certified +0.667) | ∈ [−0.21, +0.38]; < +0.333 in 99% of assignments | point < +0.333, *and* item-cluster bootstrap P(≥ +0.333) < 0.10 |
| **H5** | The judge moves the most expensive system onto the frontier (gold price $0) | Opus is on the judge frontier in 78% of assignments and never on the certified one | Opus-open's bootstrap frontier membership is ≥ 0.50 under the judge and ≤ 0.05 under the certified grade |

**Overall outcome rule** (decides which §6 paragraph is used):
- **Confirm:** H1 holds, and H2 or H3 holds.
- **Null:** H1 fails. The bootstrap upper bound reaches 0.467, so sampling noise alone could put the judge level with AstaBench.
- **Reversal:** H2, H3 and H4 all fail. The judge compresses the leaderboard but preserves every established order and the within-Terra budget effect within sampling error.

H5 is reported in every case and does not enter the rule.

---

## 2. Data and populations (all existing; no new agent or judge calls)

### Per-slot verdicts (private, on the box)
`results/private_1112/judge/slots.json`, written by `scripts/judge_vs_grade.py analyse`. Each row has call_id = `<batch>__<rundir>`, population, agent, access, hard, certified, judge and confidence. Also `rows.json` and the raw responses under `raw/`. There are 214 runs and 856 slots. The judge was gpt-6.1-terra with the report-only prompt, sha256 in `judge/inputs.json`.

### Joins
- **Item (episode)**: from `RAW/<batch>/<rundir>/grade.json` (or `answer.json`). Cross-check against `results/blackbox_1112/rows_r1112.csv`, which has 108 Block 1 rows with episode and cid, and `results/cross_model_1103/rollouts.csv` (main study b1/b2 and harder variant hv; cid and episode).
- **Cost per run (USD)**:
  - Block 1 and BB-16: `results/blackbox_1112/ledger.jsonl`, `finished` events, keyed by cid.
  - Main study: `rollouts.csv` `usd`.
  - Terra costs are token counts × list price (estimated); Claude costs are Claude Code's reported `total_cost_usd`. The table will flag the difference.
- **Exact queries used**: `pq_used` in rows_r1112.csv for Block 1; grade or trace for main and BB-16. If a value is missing, use the arm budget and flag it.

### Systems (pre-registered list)
A system is a model + harness + access + exact budget configuration, each listed once.

**L9 (primary)**

| system | runs | certified hard | cost / run |
|---|---|---|---|
| Terra-open (main 16 + Block 1 Open-8 24) | 40 | 37/40 | $0.67 |
| Opus-open (main) | 16 | 11/16 | $3.72 |
| Sonnet-open (main) | 16 | 12/16 | $3.09 |
| Haiku-open (main 16 + Block 1 Open-8 12) | 28 | 13/28 | $1.01 |
| Terra-BB8 | 24 | 8/24 | $0.97 |
| Terra-BB16 | 24 | 18/24 | $0.59 |
| Terra-BB64 | 24 | 24/24 | $0.37 |
| Haiku-BB8 | 12 | 3/12 | $1.23 |
| Haiku-BB64 | 12 | 8/12 | $0.86 |

The box agent recomputes all of these. If any certified count differs from this table or from `judge.json`, it stops (§4 gate).

**Secondary leaderboards** (descriptive; same estimators):
- **L11**: L9 with main and Block 1 Open-8 kept separate for Terra and Haiku. These are the populations as run, a day apart and not interleaved.
- **L-main**: 4 systems, 6 pairs, matched population; τ is coarse (steps of 1/3).
- **L-B1**: 6 systems, interleaved seeded order, the cleanest matched population.
- **L13**: L11 + Luna Open-8 (36) + Luna BB-8 (24). Only if C8 has been run; C8's own pre-registration covers that judge call (about $0.55). C19 adds no spend.

### Excluded (pre-registered)
- The harder variant (18 runs, different items, 3-8 runs per agent). Its slots appear only in a footnote count.
- Pilots and smoke runs.

---

## 3. Procedure and metrics

### 3.1 Rates
For each system s:
- certified rate C_s = certified hard passes / runs;
- judge-implied rate J_s = judge-credited hard slots / runs.

Secondary metric: NAME. Certified NAME is from grade.json. Judge NAME = the judge credits every probe of the run.

### 3.2 Rank agreement
- Kendall τ_b between the vectors (C_s) and (J_s), ties handled by τ_b.
- Also: K = number of discordant pairs (strictly opposite order) out of 36, and the largest reversal (the discordant pair with the largest certified gap).
- Descriptive extra: τ_b over pairs whose certified gap is ≤ 0.25 (the "hard pairs"), because easy budget-arm pairs inflate τ.

### 3.3 Pairs
- **Flip probability** of pair (a, b): the bootstrap share of resamples in which sign(J_a − J_b) is opposite to sign(C_a − C_b) on the *same* resample. A judge tie counts ½.
- **Established certified order**: both conditions must hold:
  - run-level two-sided Fisher p < 0.05 on the hard-slot counts;
  - item-cluster bootstrap P(C_a > C_b) ≥ 0.95.
- **Robust reversal**: the order is established, the judge's point order is strictly opposite, and the run-level bootstrap P(J_b > J_a) ≥ 0.90, where a is the certified winner.

### 3.4 Cost
- Cost per certified pass = Σ usd / certified passes. Cost per credited pass = Σ usd / judge-credited passes.
- Frontier: a system is non-dominated in (mean cost per run ↓, rate ↑) under each grader.
- Primary gold price p = $0 per exact query, following AstaBench's convention.
- Sensitivity: p = $0.006 (Appendix J break-even) and $0.05, with cost = usd + p × exact queries used. Part A shows the conclusion changes with p: at p = 0.006 the certified frontier becomes {BB-16, Terra-open, BB-64} and BB-64 drops off the judge frontier. Both are reported.

### 3.5 Uncertainty
B = 10,000 resamples, seed 20261113.
- **(i) Run-level stratified bootstrap.** Resample runs with replacement within each system × item cell, carrying each run's certified grade, judge verdict and cost together. This gives the intervals for τ_b, gaps, flip probabilities and frontier membership. Certified and judge rates come from the same resample, so the comparison is paired.
- **(ii) Item-cluster bootstrap.** Resample the 6 items with replacement and keep all runs of every system on each drawn item. This keeps the crossed design. Six clusters under-cover, so this is reported beside (i), and claims use the wider of the two.

### 3.6 Item-level floor
- Leave-one-item-out τ_b (6 values; report min and max).
- Per-item τ_b over L9 (descriptive; 2-4 runs per cell).
- With six items, no item-level test can go below p = 0.031 (sign test). Every statement is conditional on these six items.

### 3.7 Exact Block 1 table (replaces the Appendix H bounds)
For each agent (Terra, Haiku) × arm (Open-8, BB-8, BB-64), plus Terra BB-16, report:
- certified count, judge-credited count, false credit, false blame and κ;
- Wilson intervals;
- Terra's C1, C2, C4 and BB-16 − BB-64 under each grader, with item-cluster intervals.

### 3.8 Unit of inference
The run; one hard slot per run. τ is a property of this set of systems on these six items, not of agents in general.

**This is a comparison of two instruments on the same runs, not an agent ranking.** Every run is graded twice, so harness, token and population differences are the same for both grades and cancel. The certified order of the Claude agents is itself underpowered (MDE 0.54 at 16 runs, §4 of the paper). The text never says "agent X beats agent Y".

---

## 4. Execution plan for the GPU-box agent (by 15 Nov; deadline slack to 19 Nov)

1. **Freeze** (about 30 min).
   - Commit `results/blackbox_1112/c19/PREREG_C19.md`: §1-3 of this file verbatim, the system list and the seed.
   - Commit `scripts/c19_leaderboard.py`.
   - Record both sha256 hashes in `followup/FREEZE_LOG.md` before running anything that reads `slots.json` per system.
2. **Reproduction gate** (about 15 min). Before computing anything new, the script must reproduce:
   - from `judge.json`: J1 κ = 0.002, 53/68, 32/146; by-agent false credit and false blame; by-access and by-population blocks;
   - the certified counts in the §2 table;
   - per-arm costs within $0.01 of the §2 table;
   - a mapping of 214/214 runs to an item.

   If any check fails, stop and log; do not adjust.
3. **Run** (CPU, under 10 min).
   - Writes `c19.json`: aggregate counts per system only, no cue names and no per-slot rows.
   - Writes `README.md` with the verdict table for H1-H5.
   - Writes the figure data (`fig_c19.csv`).
4. **Part A check.** Every exact count must fall inside its Part A range (`brainstorm/c19_partA/out_*.txt`). A value outside a range means a join bug: stop.
5. **Optional L13.** Only after C8 has produced Luna slots. Same script, flag `--with-luna`; reported as secondary.

**Cost and time.**
- $0 new API spend.
- About 1 h of box-agent wall time plus about 1 h for review.
- About 1.5 h of author time for text and figure.
- If C8 runs, its $0.55 is booked to C8.

---

## 5. What it adds to the paper (figure and table)

### Appendix H rewrite (net length about zero)
- **Table H3** replaces Table H2 and the "Per-agent Block 1 bounds" paragraph. It gives exact per-agent × arm certified vs judge-implied counts, false credit and false blame, and Terra's C1, C2, C4 and BB-16 − BB-64 under each grader.
- **Table H4** replaces Table H1. It is the L9 leaderboard:
  - certified rate, judge rate, certified rank, judge rank;
  - cost per run, cost per certified pass, cost per credited pass;
  - frontier membership probability under each grader.
- One line under H4 gives τ_b for L11, L-main, L-B1 (and L13).

### Figure H1 (appendix; one column, two panels)
- **(a) Slope chart.** The nine systems' certified rate on the left and judge-implied rate on the right. Robustly reversed pairs are highlighted.
- **(b) Cost vs rate.** Cost per run (log x-axis) against hard-slot rate. Filled markers are certified, hollow markers judge-implied, joined by a thin line per system. The two frontiers are drawn as step lines.

### Body
- One replaced paragraph in §5.2: "Graded by this judge, the study's conclusions would change...", about 95 words, replaced by about 100.
- One replaced clause in the abstract and one in the Contributions bullet for Claim 2. Abstract: "would cut the measured gain from +0.67 to at most +0.38" becomes the exact figure plus τ.
- No new body figure unless something else leaves. If space opens up (for example, the multi-denominator note moves out per RANK_V4 fix 1), panel (b) is the candidate.

---

## 6. Paper text under each outcome (X = filled in from c19.json; do not change the wording logic)

### Confirm (H1 and H2 or H3)
> **Graded by this judge, the leaderboard itself would change.** Ranking nine agent configurations by the judge's credit instead of the certified grade gives Kendall τ_b = X (run bootstrap 95% interval X to X; item bootstrap X to X). For comparison, AstaBench's judge agrees with expert rankings at τ = 0.467 (Bragg et al. 2026). Every assignment consistent with our published counts already bounds τ_b at 0.37. The judge reverses K of 36 pairs, including established ones. Haiku with the proxy (certified 0.46) ranks above Terra with 64 queries (1.00); Terra's 16-query arm ranks above its 64-query arm, so its budget curve stops rising. On the matched main study, the 0.375 Terra-Haiku gap becomes X. On the cost-accuracy frontier, the judge adds X, including Opus at ten times the cost per run of the certified frontier's only member [pre-reg C19; Appendix H, Table H4, Figure H1]. Because each run is graded twice, the comparison is between instruments, not agents.

### Null (H1 fails)
> Every assignment consistent with our published counts puts the judge's τ_b against the certified ranking of nine configurations between −0.06 and 0.37, below AstaBench's 0.467 against experts. The exact value is X, but with 12-40 runs per configuration the bootstrap interval reaches X, so we do not claim the judge ranks worse than AstaBench's. What does not depend on sampling is which orders flip. [Then the H2, H3 and H4 sentences, whichever hold.]

### Reversal (H2, H3, H4 all fail)
> The judge compresses the leaderboard (τ_b = X; certified rates span 0.25-1.00 and judge-implied rates X-X) but preserves every established certified order within sampling error, including Terra's budget effect (X vs certified +0.67). Its damage is therefore to the scale, not the order: it credits failures across the board, which is what κ = 0.002 on the deciding slot predicts. [Keep J1-J3 as the headline; Table H4 goes in the appendix without a body sentence.]

### Fallback if the box run slips past 18 Nov
Use the first sentence of the Null paragraph with the Part A bounds. That sentence holds whatever the private verdicts say, needs only the Part A script (released), and still replaces the awkward integer-split prose with a single bound in the CFP's own units.

---

## 7. Risks and wording guards

- **Comparability to AstaBench.** Their τ is judge vs expert on ScholarQA-CS2 (one benchmark, long-form QA). Ours is a judge against a certified grade on six items. The text says "for comparison", never "worse than AstaBench's judge". Easy budget-arm pairs inflate our τ, so the hard-pairs τ is shown beside it.
- **Not an agent ranking.** The systems include budget arms; harness confounds apply only to the certified order and cancel in the paired comparison; the Claude agents' certified order is underpowered.
- **Cost axis.** Terra costs are estimated and Claude costs reported; exact queries are priced separately; the frontier is shown at three gold prices.
- **Pooling main with Block 1** (Terra-open, Haiku-open) joins populations a week apart. L11 keeps them split, and the result is reported if it differs in sign.
- **Small n.** Opus and Sonnet have 16 runs each, and Haiku BB arms 12. Flip probabilities, not point orders, carry the pairwise claims.
- **Privacy.** Public outputs are per-system counts only. Per-slot verdicts with cue names stay in `results/private_1112/`.

---

## 8. Part A outputs (computed 12 Nov, committed counts only)

Files are in `brainstorm/c19_partA/`:
- `out_bounds.txt`: per-system ranges and τ ranges for L9, L11, L-main and L-B1;
- `out_frontier.txt`: frontier membership share over assignments at p = 0, 0.006 and 0.05;
- `out_pairs.txt`: pairwise and Terra-contrast ranges.

Key ranges:
- **L9 τ_b**: −0.057 to +0.371.
- **L11 τ_b**: −0.150 to +0.476.
- **L-main τ_b**: −1.00 to +0.67.
- **L-B1 τ_b**: −0.08 to +0.60.
- **Judge-implied counts**:
  - Terra BB-8 / Open-8 / BB-64 / BB-16: 10-17, 18-24, 12-19 and 21 (exact), all of 24;
  - Opus-main: 15-16 of 16;
  - Sonnet-main: 12-14 of 16;
  - Haiku-main: 11-16 of 16;
  - Terra-main: 12-16 of 16.
- **Terra contrasts under the judge**: C2 −0.21 to +0.38; C1 +0.04 to +0.58; C4 −0.50 to +0.04; BB-16 − BB-64 +0.08 to +0.38 (certified −0.25).

---

## Critic

Adversarial review, 12 Nov. I checked against `judge.json` (by-agent, by-access and by-population blocks), `ledger.jsonl` (`finished` costs), `rows_r1112.csv`, `bb16/analysis/bb16_analysis.json`, `RANK_V4_raw.json`, and Part A's `out_*.txt`.

**Verdict: RUN WITH CHANGES.** It costs $0 and about an hour on the box, and two of the five V4 reviewers asked for it almost word for word. As written, though, it puts its weakest result first (τ against AstaBench's 0.467) and its most fragile one second (a frontier that prices gold at $0 across harnesses). The strongest content, the reversed orders, is already deterministic from committed counts.

### What holds up
- **The data is there, as far as I can check from here.** Every committed marginal the design uses is real:
  - BB-16 judge-implied count = 18 − 2 + 5 = 21/24, exact.
  - Pooled BB-64 false blame is 12/32, the highest of any arm.
  - Per-arm costs match the ledger: Terra BB-8 / BB-16 / BB-64 / Open-8 = $0.96 / $0.59 / $0.37 / $0.67; Haiku $1.22 / $0.86 / $0.99. BB-64 really is the cheapest Terra arm per run.
  - The 214 − 196 = 18 excluded runs equal the harder variant.

  One thing I could not verify: `slots.json` and `rows.json` are git-ignored (`results/private_1112/`). They exist only if the box that ran the judge on 12 Nov still has its disk.
- **It answers a reviewer's request.** RANK_V4 fix 4 asks for the "per-agent judge reordering table". Two raw reviews say: bring back the per-agent judge-implied table "showing that the agents would be reordered... in a way the hedged range from −0.21 to +0.38 does not". A third asks to "plot cost per pass against exact budget, so the cost-normalized reporting the CFP asks for is a figure". The CFP lists "sensitivity of rankings to judge" and "cost-normalized reporting".
- **It can be done in time:** CPU only, a reproduction gate, and a fallback that needs no box.

### Where it breaks
1. **τ is close to definitional given Claim 2.**
   - The judge credits 53/68 = 0.78 of certified failures and 114/146 = 0.78 of certified passes. Its credit is essentially independent of the grade (that is what κ = 0.002 means), so every system's judge-implied rate is about 0.78 plus noise.
   - A τ near 0 is the expected value under that independence, and Part A's median of 0.17 is what it shows. A statistician on the committee (Zhou, Zhu) will read H1 as "κ ≈ 0, restated at the system level".
   - The only non-trivial question τ answers is whether the *between-system* variation in judge credit happens to line up with the certified order. Part A already answers no, at $0.
2. **The AstaBench comparison is not a test.**
   - H1 compares our bootstrap interval with a point estimate from another benchmark. That estimate has no reported CI and comes from a different task, different systems and a judge that reads the work, not a report.
   - Our "systems" include three budget arms of one model, which is not a leaderboard in AstaBench's sense.
   - A report-only judge on a task whose answer needs data also hands a reviewer the "strawman judge" line.
3. **The "below 0.467 in every assignment" bound depends on the leaderboard definition.**
   - It holds for L9, which pools main-study and Block 1 runs a week apart. It fails for L11, the populations as run, whose upper bound is 0.476.
   - For L-B1, the cleanest matched population, only 95% of assignments fall below, and the upper bound is 0.60.
   - L9 was chosen in the same document that computed all four ranges. A reader who sees L11 in the appendix will see a forking path behind the headline.
4. **The hypotheses were written after the bounds were seen.**
   - H4's threshold is met in 99% of assignments. H2's pairs are reversed in 100%.
   - §1 is honest about this, but a "[pre-reg]" tag on these claims would oversell them. Label them "estimation pre-registered after deterministic bounds".
5. **The exact numbers can weaken the abstract.**
   - The abstract says the judge cuts Terra's budget gain "from +0.67 to at most +0.38". That is a true bound on the point estimate.
   - With 24 runs per arm, the run-bootstrap interval on the judge-implied C2 is about ±0.28. If the exact value is near +0.3, H4's "P(≥ +0.333) < 0.10" will likely fail, and the honest abstract becomes weaker than today's.
   - The item-cluster bootstrap with six items makes this worse.
   - H2 is not safe either. Haiku-open minus BB-64 can be as small as +0.065 at the point estimate, and BB-16 minus BB-64 as small as +0.083. Either could miss the 0.90 flip-probability bar.
6. **The frontier contradicts the paper's own premise.**
   - With gold priced at $0, BB-64 dominates by construction, which is why it is the whole certified frontier. Yet the paper's thesis is that exact queries are scarce (Appendix J break-even is $0.006).
   - At p = $0.006 both frontiers change.
   - It also mixes collector-estimated Terra costs with Claude Code's reported costs across two harnesses. That is exactly the cross-system, unmatched-compute comparison the CFP says to avoid or justify.
   - "Opus is on the judge frontier in 78% of assignments" is not a robust headline.
7. **There is an unexamined confound in why the order flips.**
   - The judge reads reports, and report style differs by harness and arm. Terra's messages have a median of about 1,400 characters; Claude's are longer. The judge rejects 12 of 32 certified BB-64 passes.
   - "Haiku-open ranks above Terra-BB64" will prompt "the judge prefers Claude's prose". That is consistent with the paper's point, but the design does not measure it.

### Required changes
1. **Make reversals of the paper's own established contrasts the primary result, and demote τ.** The new primary H2′ covers:
   - the within-Terra budget curve (under the judge, BB-16 > BB-64 at 21/24 vs at most 19/24, against certified 18 vs 24, so the curve is non-monotone);
   - Haiku-open vs Terra-BB64;
   - the Terra-Haiku gap on matched main+B1 (+0.32 certified vs −0.08 to −0.02 judge-implied).

   All three are already reversed in every assignment, so they can go in the paper today as bounds. The box run adds flip probabilities. Report τ_b in one line "for scale", next to AstaBench's 0.467, never as a threshold test. Drop the H1 confirm/null decision rule.
2. **Report the Part A τ range for L9 and L11 together**, plus L-B1. Write the sentence so that it holds for both: "between −0.15 and 0.48 whether or not populations are pooled". Do not write "below AstaBench in every assignment".
3. **Recast H4 as paired shrinkage**: certified C2 minus judge C2 > 0, with a run-bootstrap CI computed on the same resample. Drop "halves". Pre-specify that the abstract keeps "at most +0.38" (a true point bound) unless the paired CI excludes 0, and that a CI reaching +0.67 goes in Appendix H, not the abstract.
4. **Replace the cross-harness $0-gold frontier and H5** with the plot the reviewer asked for: Terra only (one harness, one cost source), cost per certified pass vs cost per judge-credited pass, against exact budget (BB-8/16/64, Open-8 at its pq_used). Draw the gold price as a line or second axis, not a $0 convention. Keep the L9 cost columns in Table H4 as descriptive only.
5. **Add one $0 descriptive diagnostic.** Per system, give the median report length (characters of the agent messages the judge saw, from `calls.jsonl`) beside the judge-credit rate and the false-blame rate. Pre-register it as descriptive. It tells the reader whether the reversals track report style.
6. **Add a gate step 0.** Before freezing, the box agent checks that `results/private_1112/judge/{slots,rows}.json` exist and that their content matches `inputs.json` and `judge.json` (J1 counts). If they are missing, stop and use the fallback.
7. **Change the fallback paragraph** to the reversal sentences of change 1 plus the change-2 τ range. Do not use the L9-only Null sentence.
8. **Label honestly.** In the text, the result is "[expl; bounds from committed counts; estimates pre-registered after bounds]", not "[pre-reg]".

### Expected score gain
- **Realistic, with the changes:** +0.1 to +0.2, to about 6.9-7.0. It replaces the hedged −0.21 to +0.38 range that two reviewers called unconvincing. It turns Claim 2's consequence into a concrete reordering (a non-monotone budget curve under the judge). It gives the CFP the cost-per-pass figure it asked for.
- **Limits:** it adds no new evidence (a listed V4 weakness). It does not answer the more frequent asks: a judge that sees the query log, a judge model other than Terra, and rank-6 or fresh items.
- **As written:** about 0 to +0.1, with a real risk of −0.1 from the statistician and area-chair reviewers on points 2, 3 and 6.
- **Most of the gain is available at $0 today** from Part A (change 1 and change 2 text). The box run is worth doing for intervals, but it should not displace any run that adds new data.
