# Commands: method ladder on the shipped six (plan 0b.1, 0b.2)

Run on the GPU box, CPU only, 2026-11-10, from the repo root. `PY` is the study environment
(`/home/ec2-user/onsite/grader-wt/.venv/bin/python`); the episode bank is private and read-only.

```
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" SHIFTHUNT_BANK=<private tree>/.cache/bank
E=ep411,ep413,ep415,ep472,ep474,ep476

# fixed scan (default): nested child flips on parent-on bases only
$PY scripts/method_ladder.py --episodes $E --seeds 200 \
    --out results/blackbox_1112/ladder --private results/private_1112/ladder --tag six
# legacy scan: the pre-fix behaviour (all 32 bases for every property)
$PY scripts/method_ladder.py --episodes $E --seeds 200 \
    --out results/blackbox_1112/ladder --private results/private_1112/ladder --tag six_legacy --legacy-scan
# sensitivity only: parent flips restricted to child-off bases as well
$PY scripts/method_ladder.py --episodes $E --seeds 200 \
    --out results/blackbox_1112/ladder --private results/private_1112/ladder --tag six_both --scan-both
# README.md from the three summaries (no ladder run)
$PY scripts/method_ladder.py --compare-readme six,six_legacy,six_both --out results/blackbox_1112/ladder

# both reward schemes, fixed scan; its JSON lists hard-slot indices, so it is written to the private
# directory and only the table is copied here, under a one-line pointer to the caveat. The script writes the
# table's delimiter row with 7 cells under a 6-cell header (so the table does not render); the sed step
# makes it 6 cells in the tracked copy and changes nothing else.
$PY scripts/ladder_reward.py --episodes $E --seeds 200 --out results/private_1112/ladder/reward_six
{ printf '%s\n\n' '> PRIVILEGED scripted ceilings (see README.md in this directory for the caveat). Fixed scan, `scripts/ladder_reward.py`; the pre-fix table is `results/offline_1013/ladder_reward.md`.'; \
  sed 's/^|---|---|---|---|---|---|---|$/|---|---|---|---|---|---|/' results/private_1112/ladder/reward_six/ladder_reward.md; \
  } > results/blackbox_1112/ladder/ladder_reward_six.md
```

Each ladder run takes about 20 s wall (about 15 s CPU after a 6 s import); `ladder_reward.py` 17 s.

Files here: `README.md` (before / after tables, caveat), `ladder_summary_six{,_legacy,_both}.{md,json}` (full
script output per scan mode, including the NAME section), `ladder_reward_six.md`. Private, not tracked
(`results/private_1112/ladder/`): `ladder_slots_six{,_legacy,_both}.jsonl` (per-slot claims with property
names), `reward_six/ladder_reward.{json,md}`.

Check that the legacy scan reproduces the code before the fix: `ladder_summary_six_legacy.json` equals, key
for key, the summary produced by the unmodified October script on the same six episodes and seeds (every key
of the old file: methods, per_episode, inversions, near_miss, sweeps); the new file only adds the keys `scan`,
`by_group`, `name_methods`, `name_per_episode`. The private per-slot rows agree on every old field too.

Tests: `$PY -m pytest tests/test_method_ladder_scan.py -q -p no:cacheprovider` (synthetic scans, no bank);
`SHIFTHUNT_BANK=... $PY -m pytest tests/test_bank_grading.py -q -p no:cacheprovider` (whole bank, about 4.5 min).
