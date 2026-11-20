"""Where host-side scripts find data that is not in git. Every location can be overridden by an environment variable.

    SHORTCUTHUNT_ROLLOUTS   raw rollout directories, <run>/<rollout id>/ (default: results/rollouts; the per-rollout
                            subdirectories are git-ignored because they hold episode answers)
    SHORTCUTHUNT_BANK       built episodes, ep<seed>/ (default: .cache/bank; built by scripts/build_bank.sh)
    SHORTCUTHUNT_ARTIFACTS  probe build artifacts (default: artifacts/probes; the .npz weights are git-ignored)
    SHORTCUTHUNT_PRIVATE    per-call judge files, per-unit verdicts with reasons and other files that name an
                            episode's shortcut (default: results/private_1112; git-ignored)

REPO is the repository root. The study was run from two checkouts of this repository on one GPU machine (the main
tree and a worktree for the round-10 judge re-send); here both are REPO.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROLLOUTS = Path(os.environ.get("SHORTCUTHUNT_ROLLOUTS", REPO / "results" / "rollouts"))
BANK = Path(os.environ.get("SHORTCUTHUNT_BANK", REPO / ".cache" / "bank"))
ARTIFACTS = Path(os.environ.get("SHORTCUTHUNT_ARTIFACTS", REPO / "artifacts" / "probes"))
PRIVATE = Path(os.environ.get("SHORTCUTHUNT_PRIVATE", REPO / "results" / "private_1112"))
