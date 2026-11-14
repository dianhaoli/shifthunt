# Figures V6: plotted values and sources

Both figures are 3.3 in wide (single AAAI column), matplotlib Agg, 300 dpi PNG plus PDF (Type 42 fonts). Okabe-Ito
colour-blind-safe palette. Each series also has its own marker or line style, so no series relies on colour alone.
Paths are relative to `paper_loop/gpu_results/`.

## Figure 1: the judge ladder (`fig1_ladder.png` / `.pdf`)

y = hard-slot Cohen's κ of the Terra judge (frozen prompt) against the executed (certified) grade. Each set uses one
fixed run list. Solid segments join adjacent rungs. A dashed segment crosses a rung that was not run for that set
(main study: no L1; harder variant: only L0 and L3). Points are offset slightly in x by set. Source:
`data/gpuplan_c6c_ladder.json` (`hard_kappa`, `answer_type_baseline_kappa`). Every value matches `c6.json`,
`c6c.json`, the C6b/C6c READMEs and the ladder table in `RESULTS_FOR_PAPER_2e30670.md`.

| set (runs) | L0 report | L1 + exact-query log | L2 + full transcript | L3 + answer key (filled) | L3 open marker | rule tick: credit any named answer |
|---|---|---|---|---|---|---|
| set A (130) | −0.021 | 0.0626 | 0.2405 | 1.000 (key on L2) | 0.9156 (key on L1) | 0.6718 |
| Luna (60) | 0.0177 | −0.0333 | 0.2581 | 1.000 (key on L2; key on L1 is also 1.000, not drawn separately) | none | 0.3715 |
| main study (64) | 0.0562 | not run | 0.2629 | 0.962 (key on L2) | none | 0.7529 |
| harder variant (18) | 0.100 | not run | not run | 0.7692 (key on L0) | none | 0.8696 |

- Dotted horizontal line: judge test-retest κ at L0 = 0.4429 (`data/gpuplan_c6_c6.json` →
  `test_retest_L0_L0r.kappa`; set A, the same prompt re-sent; 520 slots, all slot types rather than only the hard
  slot). `RESULTS_FOR_PAPER_2e30670.md` (C6) gives "Test-retest (same prompt re-sent): κ 0.44".
- Not plotted: L2r (main study 0.176), L0r and L1r, the Haiku rungs and the C17 Fleiss κ.

## Figure 2: budget and depth (`fig2_budget.png` / `.pdf`)

### (a) P(NAME) on the six shipped items vs exact queries per episode (log2 axis, 2 to 64)

Agent points: count / n, with Wilson 95% intervals computed for this figure. Points at B = 8 are offset ±0.07 in
log2 x.

| series | B | NAME | Wilson 95% | source |
|---|---|---|---|---|
| Terra with proxy (Open-4) | 4 | 12/12 = 1.000 | [0.758, 1.000] | `RESULTS_FOR_PAPER_2e30670.md` X3-H1 (Wilson 0.76-1.00) |
| Terra with proxy (Open-8) | 8 | 23/24 = 0.958 | [0.798, 0.993] | `RESULTS_FOR_PAPER_2e30670.md` Claim 1 |
| Terra blind (BB-8) | 8 | 6/24 = 0.250 | [0.120, 0.449] | `RESULTS_FOR_PAPER_2e30670.md` Claim 1 |
| Terra blind (BB-16) | 16 | 16/24 = 0.667 | [0.467, 0.820] | **not in RESULTS_FOR_PAPER_2e30670.md**; `final/PAPER_V5.md` §5.1 and its budget table (pre-registered arm) |
| Terra blind (BB-64) | 64 | 24/24 = 1.000 | [0.862, 1.000] | **not in RESULTS_FOR_PAPER_2e30670.md**; `final/PAPER_V5.md` §5.1; `GPUPLAN_README_2e30670.md` C19 ("Terra-BB64 (24/24)") |

Reference (scripted) lines: `data/gpuplan_xr_curves.json` → `curves.shipped_six.<policy>.<B>.name` [expl X1]
(thin lines, no intervals; the simulation intervals are narrower than the line width).

| policy (legend) | key | B=2 | 3 | 4 | 5 | 6 | 8 | 12 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bayes, bank prior | `bayes_bank` | 0.1667 | 0.1667 | 0.4933 | 0.7956 | 0.9311 | 0.9533 | 0.9683 | 0.9756 | 0.9822 | 0.9839 |
| test the top two | `top2` | 0.0000 | 0.3333 | 0.4892 | 0.6572 | 0.6578 | 0.9582 | 0.9605 | 0.9892 | 0.9995 | 1.0000 |
| best blind | `best_blind` | 0.1027 | 0.2017 | 0.2147 | 0.2730 | 0.3013 | 0.4367 | 0.6498 | 0.7930 | 0.8853 | 0.9723 |

These match RESULTS X1: Bayes 0.17/0.49/0.80/0.95 at 2/4/5/8; best blind 0.44/0.79/0.97 at 8/16/64; top two
0.49/0.66/0.96 at 4/5/8.

### (b) trap episodes at 8 exact queries vs the [main]'s proxy rank (2, 3, 4, 6, 8)

Reference (scripted) lines: `data/gpuplan_xr_curves.json` → `depth.shipped_traps.<rank>.<policy>.8.name` (the
shipped trap episodes with the [main] moved to proxy rank r; true logits unchanged). Best blind does not depend on
rank. It is `curves.shipped_traps.best_blind.8.name`, drawn flat.

| policy (legend) | rank 2 | 3 | 4 | 6 | 8 |
|---|---|---|---|---|---|
| test the top two (`top2`) | 0.9613 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Bayes, bank prior (`bayes_bank`) | 0.9233 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hedge (`hedge`) | 0.5560 | 0.5197 | 0.4867 | 0.5440 | 0.4677 |
| best blind (`best_blind`) | 0.4017 | 0.4017 | 0.4017 | 0.4017 | 0.4017 |

These match RESULTS X1 depth: 0.96/0/0/0/0; 0.92/0/0/0/0; 0.56/0.52/0.49/0.54/0.47; 0.40.

Agent points are at rank 2 only. They are the **fresh (held-out) traps, three items pooled, on their pre-registered
runs** (shipped traps not drawn). The two points are offset ×1.06 either side of rank 2 on the log x axis. Source:
`RESULTS_FOR_PAPER_2e30670.md`, C14 + C14b table, and the deviation note "Figure 2 (b): the fresh-trap points now
pool the three items".

| series | NAME_trap | Wilson 95% |
|---|---|---|
| Terra, 3 fresh traps pooled | 20/21 = 0.952 | [0.773, 0.992] (RESULTS: 0.77-0.99) |
| Luna, 3 fresh traps pooled | 2/17 = 0.118 | [0.033, 0.343] |

Caveat for the caption: the agent points come from different items (fresh traps) than the reference lines (shipped
traps with the [main] relabelled), so they share the axis but not the item set.

## Suggested captions

**Figure 1.** The judge ladder. Hard-slot Cohen's κ of the same frozen judge against the executed grade as it sees
more: the agent's report (L0), plus the exact-query log with true logits (L1), plus the full transcript including
the interpretability-tool outputs (L2), plus a plain answer key (L3). Each set is one fixed run list. Dashed
segments skip rungs that were not run. The open marker is set A with the key added at L1. Ticks at right: κ of the
rule "credit any named answer" for each set. Dotted line: the judge's own test-retest κ at L0 (set A, all slots).

**Figure 2.** (a) P(NAME) on the six shipped items against exact queries per episode. Markers are Terra with the
proxy (B = 4, 8) and without it (B = 8, 16, 64), with Wilson 95% intervals. Thin lines are scripted reference
policies that use only the proxy's ranking, or no proxy (best blind, chosen per budget with privileged knowledge).
(b) Shipped trap episodes at B = 8 with the [main] moved to proxy rank r and true logits unchanged (scripted
references). Agent points (rank 2 only) pool the three held-out traps on their pre-registered runs.
