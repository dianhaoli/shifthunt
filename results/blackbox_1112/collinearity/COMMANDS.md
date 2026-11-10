# Commands: aligned properties exactly collinear with the label (plan 0b.4)

Run on the GPU box, CPU only, 2026-11-10, from the repo root. `PY` is the study environment
(`/home/ec2-user/onsite/grader-wt/.venv/bin/python`); the episode bank is private and read-only.

```
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" SHIFTHUNT_BANK=<private tree>/.cache/bank
$PY scripts/check_aligned_collinear.py --out results/blackbox_1112/collinearity
```

Default episodes: ep411, ep413, ep415, ep472, ep474, ep476 (24 samples). About 6 s wall. Exit status 0 = every
check passed. Writes `README.md` and `collinearity.json` (counts; names of NON-aligned generator properties
only: per sample the one with the largest |r| and the two tied by nesting).

Tests: `$PY -m pytest tests/test_check_aligned_collinear.py -q -p no:cacheprovider` (the bank-dependent test
skips with a message unless `SHIFTHUNT_BANK` or `.cache/bank` has the six episodes).
