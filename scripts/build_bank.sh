#!/usr/bin/env bash
# Build the episode bank baked into the task image: one episode per seed under .cache/bank/ep<seed>.
#   scripts/build_bank.sh [FIRST_SEED] [LAST_SEED] [BUILDS]   (run from the repo root; GPU, takes the lock)
set -euo pipefail
PY="${PY:-python}"
FIRST="${1:-101}"; LAST="${2:-112}"; BUILDS="${3:-build_screen,build_screen2}"
mkdir -p .cache/bank
for s in $(seq "$FIRST" "$LAST"); do
    [ -e ".cache/bank/ep$s" ] && continue
    flock /tmp/shifthunt-gpu.lock env HF_HUB_OFFLINE=1 "$PY" scripts/build_episode.py \
        --out ".cache/bank/ep$s" --seed "$s" --artifacts artifacts --builds "$BUILDS"
done
