"""Run any build script with shifthunt.knob_concept installed as shifthunt.textgen (free text + `concept`).

    python scripts/knob_concept_run.py scripts/freetext_build_cues.py --tag knob_concept --cues concept --per-cue 6
Same mechanism as scripts/freetext_run.py.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import shifthunt  # noqa: E402
from shifthunt import knob_concept  # noqa: E402  (imports freetext, which imports the real textgen first)

sys.modules["shifthunt.textgen"] = knob_concept
shifthunt.textgen = knob_concept
from shifthunt import detectors  # noqa: E402

detectors.submission_regex = knob_concept.submission_regex

if __name__ == "__main__":
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_path(script, run_name="__main__")
