> PRIVILEGED scripted ceilings (see README.md in this directory for the caveat). Fixed scan, `scripts/ladder_reward.py`; the pre-fix table is `results/offline_1013/ladder_reward.md`.

# Method ladder under both reward schemes (scripts/ladder_reward.py)

6 episodes, 200 seeds for verify_8.

| episode | none (aon / hgp) | c3 (aon / hgp) | sae_only (aon / hgp) | verify_8 (aon / hgp) | oracle (aon / hgp) |
|---|---|---|---|---|---|
| ep411 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| ep413 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| ep415 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.78 / 0.94 | 1.00 / 1.00 |
| ep472 | 0.00 / 0.00 | 0.00 / 0.00 | 1.00 / 1.00 | 0.78 / 0.83 | 1.00 / 1.00 |
| ep474 | 0.00 / 0.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.68 / 0.80 | 1.00 / 1.00 |
| ep476 | 0.00 / 0.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.72 / 0.93 | 1.00 / 1.00 |
| **pooled** | 0.00 / 0.00 | 0.33 / 0.33 | 0.50 / 0.50 | 0.83 / 0.92 | 1.00 / 1.00 |

Pooled hard_gated_partial inversions (a lower rung above the next): none
