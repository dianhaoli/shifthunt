"""Knob "trap2": knob_trap_measure.py (feas / solve, unchanged logic) with outputs in results/knobs/trap2/.

    flock /tmp/shifthunt-gpu.lock python scripts/knob_trap2_measure.py feas --knob knob_trap_s2
    flock /tmp/shifthunt-gpu.lock python scripts/knob_trap2_measure.py solve --knob knob_trap_s2 --skip-pool
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knob_trap_measure as KM  # noqa: E402

KM.OUT = ROOT / "results" / "knobs" / "trap2"

if __name__ == "__main__":
    KM.main()
