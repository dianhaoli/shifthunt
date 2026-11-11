# Commands (failure flags, D36)

Interpreter: `PY=/home/ec2-user/onsite/grader-wt/.venv/bin/python`, always run under `nice -n 19` with
`PYTHONDONTWRITEBYTECODE=1`. No GPU, no paid API, no docker. The replay sandbox is bubblewrap (`/usr/bin/bwrap`).

```sh
# 1. unit tests (synthetic logs only), before the freeze and after every change
PYTHONDONTWRITEBYTECODE=1 nice -n 19 $PY -m pytest -p no:cacheprovider -q tests/test_failure_flags.py

# 2. freeze: sha256 of the script and the tests, recorded with the UTC time in FREEZE.md
sha256sum scripts/failure_flags.py tests/test_failure_flags.py

# 3. the run on real data: replays the 64 main-study runs and, for validation, the 36 fresh Open-8 runs,
#    codes every answered slot, writes the private per-slot detail, flags.json and the generated part of README.md
PYTHONDONTWRITEBYTECODE=1 nice -n 19 $PY scripts/failure_flags.py run \
    --raw /home/ec2-user/onsite/sub/tasks/shifthunt/results/rollouts \
    --bank /home/ec2-user/onsite/sub/tasks/shifthunt/.cache/bank \
    --out-json results/blackbox_1112/flags/flags.json \
    --readme results/blackbox_1112/flags/README.md \
    --private-out results/private_1112/flags/ \
    --work <scratch dir> --jobs 3 --validate-replay
```

`--reuse-replay` recomputes the flags from the replays cached in `results/private_1112/flags/replay/` without
replaying again. The private outputs are `slots.jsonl` (one line per answered slot, with property names and text
hashes), `replay_validation.json`, `generated.md` and `replay/<batch>__<run>.json`, which holds the replay
results with the agent's texts.

After FREEZE change 4 the full run was repeated with fresh replays (no `--reuse-replay`), with the same
command. The replays of the change-3 version were set aside, git-ignored, in
`results/private_1112/flags/replay_change3/`. Each version of the script and the tests from change 3 on is kept
in `results/private_1112/flags/frozen/`, git-ignored, with one unified diff per change:

```sh
sha256sum scripts/failure_flags.py tests/test_failure_flags.py           # must equal the last FREEZE.md entry
cmp scripts/failure_flags.py results/private_1112/flags/frozen/failure_flags.<sha8>.py
```
