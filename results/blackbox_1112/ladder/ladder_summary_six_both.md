# Offline method ladder (scripts/method_ladder.py)

Scan mode: sensitivity scan: child flips on parent-on bases and parent flips on child-off bases.

6 episodes, 200 seeds for the budgeted verify rungs, 15 s CPU. All-or-nothing episode reward. Thresholds fixed in advance: c3 latent > 0.3; sae_only aligned latent > 0.225; verify true ratio (over the drawn base notes) > 0.2. See the script docstring for exact rung definitions.

Episodes: ep411, ep413, ep415, ep472, ep474, ep476

## Mean reward per method

| method | mean reward | sd over seeds | episodes passing (p=1) | p in (0,1) |
|---|---|---|---|---|
| none | 0.000 | 0.000 | 0/6 | 0 |
| c3 | 0.500 | 0.000 | 3/6 | 0 |
| sae_only | 0.500 | 0.000 | 3/6 | 0 |
| verify_4 | 0.937 | 0.092 | 3/6 | 3 |
| verify_8g | 0.928 | 0.095 | 2/6 | 4 |
| verify_8 | 0.838 | 0.139 | 2/6 | 4 |
| verify_16 | 0.946 | 0.093 | 2/6 | 4 |
| verify_24 | 0.973 | 0.061 | 3/6 | 3 |
| verify_16w | 0.772 | 0.159 | 1/6 | 5 |
| verify_24w | 0.568 | 0.192 | 0/6 | 6 |
| verify_inf | 1.000 | 0.000 | 6/6 | 0 |
| oracle | 1.000 | 0.000 | 6/6 | 0 |

## Mean reward by episode group

| group | n | none | c3 | sae_only | verify_4 | verify_8g | verify_8 | verify_16 | verify_24 | verify_16w | verify_24w | verify_inf | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ft | 3 | 0.00 | 1.00 | 1.00 | 0.87 | 0.87 | 0.75 | 0.91 | 0.96 | 0.65 | 0.41 | 1.00 | 1.00 |
| has_nested | 3 | 0.00 | 1.00 | 1.00 | 0.87 | 0.87 | 0.75 | 0.91 | 0.96 | 0.65 | 0.41 | 1.00 | 1.00 |
| has_trap | 3 | 0.00 | 0.00 | 0.00 | 1.00 | 0.99 | 0.92 | 0.98 | 0.99 | 0.89 | 0.73 | 1.00 | 1.00 |
| tmpl | 3 | 0.00 | 0.00 | 0.00 | 1.00 | 0.99 | 0.92 | 0.98 | 0.99 | 0.89 | 0.73 | 1.00 | 1.00 |

(has_trap: a knob_trap slot; has_twomain: a two-main slot; has_nested: a slot whose main is a nested child property (shifthunt.freetext.IMPLIES); plain: none of these.)

## Ladder order

Primary ladder: none (0.000) < c3 (0.500) < sae_only (0.500) < verify_8 (0.838) < oracle (1.000).
Rung means out of order: none.
Budget ladder verify_8 (0.838) < verify_16 (0.946) < verify_24 (0.973) < verify_inf (1.000) < oracle (1.000); out of order: none.

Wide-allocation budget ladder verify_8 (0.838) < verify_16w (0.772) < verify_24w (0.568) < verify_inf (1.000) < oracle (1.000); out of order: verify_8 > verify_16w, verify_8 > verify_24w, verify_16w > verify_24w.

## Per-episode pass (probability over seeds for the seeded verify rungs)

(Slot types per episode are not listed here; they are in the private ladder_slots file.)

| episode | sub | none | c3 | sae_only | verify_4 | verify_8g | verify_8 | verify_16 | verify_24 | verify_16w | verify_24w | verify_inf | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ep411 | tmpl | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0.96 | 0.82 | 1 | 1 |
| ep413 | tmpl | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0.79 | 1 | 1 |
| ep415 | tmpl | 0 | 0 | 0 | 1 | 0.96 | 0.78 | 0.94 | 0.97 | 0.70 | 0.57 | 1 | 1 |
| ep472 | ft | 0 | 1 | 1 | 0.94 | 0.88 | 0.80 | 0.92 | 0.98 | 0.68 | 0.41 | 1 | 1 |
| ep474 | ft | 0 | 1 | 1 | 0.91 | 0.83 | 0.78 | 0.95 | 1 | 0.63 | 0.33 | 1 | 1 |
| ep476 | ft | 0 | 1 | 1 | 0.77 | 0.90 | 0.68 | 0.86 | 0.89 | 0.66 | 0.49 | 1 | 1 |

## Per-episode inversions (lower rung passes more often than a higher rung)

23 (episode, lower, higher) inversions in total over the primary, budget and wide-allocation chains. Count per rung pair:

| lower rung | higher rung | episodes inverted |
|---|---|---|
| c3 | verify_8 | 3 |
| sae_only | verify_8 | 3 |
| verify_8 | verify_16w | 5 |
| verify_8 | verify_24w | 6 |
| verify_16w | verify_24w | 6 |

Rows for the primary and budget chains (wide-allocation rows only in ladder_summary.json):

| episode | lower rung | p | higher rung | p | higher-rung failing-slot buckets | tau near-miss |
|---|---|---|---|---|---|---|
| ep472 | c3 | 1.00 | verify_8 | 0.80 | extra_cue:30, planted_none:11 | 0 |
| ep472 | sae_only | 1.00 | verify_8 | 0.80 | extra_cue:30, planted_none:11 | 0 |
| ep474 | c3 | 1.00 | verify_8 | 0.78 | extra_cue:35, planted_none:14 | 0 |
| ep474 | sae_only | 1.00 | verify_8 | 0.78 | extra_cue:35, planted_none:14 | 0 |
| ep476 | c3 | 1.00 | verify_8 | 0.68 | extra_cue:46, planted_none:21 | 0 |
| ep476 | sae_only | 1.00 | verify_8 | 0.68 | extra_cue:46, planted_none:21 | 0 |

(Bucket counts for the seeded verify rungs are summed over failing seeds.)

## Failure buckets of non-oracle rungs (failing slots in failing episodes)

Tau near-miss = bucket removal_short with margin in (-0.03, 0).

| method | buckets (deterministic: slot count; seeded verify rungs: mean per seed) | removal_short | tau near-miss |
|---|---|---|---|
| none | planted_none:18 | 0 | 0 |
| c3 | cue_not_identified:3 | 0 | 0 |
| sae_only | cue_not_identified:1, extra_cue:2 | 0 | 0 |
| verify_4 | extra_cue:0.325, planted_none:0.055 | 0 | 0 |
| verify_8g | null_false_claim:0.235, planted_none:0.2 | 0 | 0 |
| verify_8 | extra_cue:0.78, planted_none:0.23 | 0 | 0 |
| verify_16 | extra_cue:0.245, planted_none:0.085 | 0 | 0 |
| verify_24 | extra_cue:0.16 | 0 | 0 |
| verify_16w | extra_cue:0.97, null_false_claim:0.265, planted_none:0.305 | 0 | 0 |
| verify_24w | extra_cue:2.54, null_false_claim:0.265, planted_none:0.305 | 0 | 0 |
| verify_inf |  | 0 | 0 |

**Tau near-misses behind an inversion: 0 of 23 inversions.**

## Threshold sweeps (reported separately; primary thresholds were fixed in advance)

sae_only, aligned latent threshold:

| threshold | mean reward |
|---|---|
| 0.15 | 0.333 |
| 0.225 | 0.500 |
| 0.3 | 0.500 |

verify, true-ratio threshold, and the sae_only threshold used for unverified probes (mean +- sd over seeds):

| verify thr | sae fallback thr | verify_4 | verify_8 | verify_16 | verify_24 | verify_8g | verify_16w | verify_24w | verify_inf |
|---|---|---|---|---|---|---|---|---|---|
| 0.15 | 0.225 | 0.894 +- 0.116 | 0.717 +- 0.174 | 0.888 +- 0.115 | 0.927 +- 0.104 | 0.904 +- 0.110 | 0.625 +- 0.194 | 0.376 +- 0.191 | 1.000 +- 0.000 |
| 0.175 | 0.225 | 0.932 +- 0.096 | 0.778 +- 0.159 | 0.931 +- 0.101 | 0.958 +- 0.077 | 0.908 +- 0.103 | 0.696 +- 0.178 | 0.465 +- 0.195 | 1.000 +- 0.000 |
| 0.2 | 0.225 | 0.937 +- 0.092 | 0.838 +- 0.139 | 0.946 +- 0.093 | 0.973 +- 0.061 | 0.928 +- 0.095 | 0.772 +- 0.159 | 0.568 +- 0.192 | 1.000 +- 0.000 |
| 0.225 | 0.225 | 0.928 +- 0.097 | 0.814 +- 0.146 | 0.938 +- 0.097 | 0.973 +- 0.066 | 0.877 +- 0.123 | 0.723 +- 0.165 | 0.566 +- 0.180 | 1.000 +- 0.000 |
| 0.2 | 0.3 | 0.807 +- 0.065 | 0.919 +- 0.107 | 0.975 +- 0.060 | 0.997 +- 0.023 | 0.928 +- 0.095 | 0.777 +- 0.160 | 0.578 +- 0.194 | 1.000 +- 0.000 |

## NAME: naming-only outcome per method

NAME = every hard slot of the episode named (grader checks identified and no_extra on the submitted regexes) and every null probe answered `none`; removal / kept are not required and the other planted slots are not counted (shifthunt.reward.name_outcome). Probability over seeds for the seeded verify rungs. The rungs submit the generator's exact regex for each claimed property, so NAME here is "the claim set of the hard slot equals its mains".

| method | mean NAME | episodes with NAME = 1 | NAME in (0,1) |
|---|---|---|---|
| none | 0.000 | 0/6 | 0 |
| c3 | 0.500 | 3/6 | 0 |
| sae_only | 0.500 | 3/6 | 0 |
| verify_4 | 1.000 | 6/6 | 0 |
| verify_8g | 0.961 | 3/6 | 3 |
| verify_8 | 0.950 | 4/6 | 2 |
| verify_16 | 0.985 | 4/6 | 2 |
| verify_24 | 0.997 | 5/6 | 1 |
| verify_16w | 0.906 | 2/6 | 4 |
| verify_24w | 0.744 | 1/6 | 5 |
| verify_inf | 1.000 | 6/6 | 0 |
| oracle | 1.000 | 6/6 | 0 |

Mean NAME by episode group:

| group | n | none | c3 | sae_only | verify_4 | verify_8g | verify_8 | verify_16 | verify_24 | verify_16w | verify_24w | verify_inf | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ft | 3 | 0.00 | 1.00 | 1.00 | 1.00 | 0.93 | 0.90 | 0.97 | 0.99 | 0.82 | 0.63 | 1.00 | 1.00 |
| has_nested | 3 | 0.00 | 1.00 | 1.00 | 1.00 | 0.93 | 0.90 | 0.97 | 0.99 | 0.82 | 0.63 | 1.00 | 1.00 |
| has_trap | 3 | 0.00 | 0.00 | 0.00 | 1.00 | 0.99 | 1.00 | 1.00 | 1.00 | 0.99 | 0.86 | 1.00 | 1.00 |
| tmpl | 3 | 0.00 | 0.00 | 0.00 | 1.00 | 0.99 | 1.00 | 1.00 | 1.00 | 0.99 | 0.86 | 1.00 | 1.00 |

Per-episode NAME:

| episode | sub | none | c3 | sae_only | verify_4 | verify_8g | verify_8 | verify_16 | verify_24 | verify_16w | verify_24w | verify_inf | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ep411 | tmpl | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| ep413 | tmpl | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0.79 | 1 | 1 |
| ep415 | tmpl | 0 | 0 | 0 | 1 | 0.96 | 1 | 1 | 1 | 0.96 | 0.79 | 1 | 1 |
| ep472 | ft | 0 | 1 | 1 | 1 | 0.97 | 0.85 | 0.94 | 0.98 | 0.82 | 0.51 | 1 | 1 |
| ep474 | ft | 0 | 1 | 1 | 1 | 0.83 | 0.85 | 0.96 | 1 | 0.68 | 0.51 | 1 | 1 |
| ep476 | ft | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0.97 | 0.87 | 1 | 1 |

