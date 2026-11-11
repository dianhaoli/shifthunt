import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import followup_topicunit_flags as TU  # noqa: E402


def test_rescale_creates_contradiction():
    # frozen unit: main true 0.24 (band), proxy 0.10 (non) -> no contradiction; x1.5 -> 0.36 cue vs 0.15 non
    props = {"3": (0.24, 0.10, 2)}
    r = TU.f4_rescaled(props, covered=set(), scale=1.5)
    assert r["contradicted"] == [3] and r["followed"] == [3] and r["F4"] == 1
    r = TU.f4_rescaled(props, covered={3}, scale=1.5)
    assert r["F4"] == 0
    r = TU.f4_rescaled(props, covered=set(), scale=1.0)
    assert r["F4"] is None


def test_proxy_cue_true_non():
    r = TU.f4_rescaled({"1": (0.05, 0.25, 1)}, covered={1}, scale=1.4)
    assert r["contradicted"] == [1] and r["F4"] == 1
