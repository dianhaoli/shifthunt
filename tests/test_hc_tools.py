"""Synthetic tests for the hardercue follow-up tools (scripts/hc_solver.py, scripts/hc_heldout.py)."""
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hc_heldout as HH  # noqa: E402
import hc_solver as HS  # noqa: E402

IMPLIES = {"kid": "par"}
FEATS = ("a", "b", "par", "kid")


def test_candidates_add_relatives_once():
    assert HS.candidates(["a", "kid"], IMPLIES) == ["a", "kid", "par"]
    assert HS.candidates(["par"], IMPLIES) == ["par", "kid"]
    assert HS.candidates(["a", "par", "kid"], IMPLIES) == ["a", "par", "kid"]


def test_flip_levels_hold_nesting():
    base = {"a": 1, "b": 0, "par": 0, "kid": 1}
    off, on = HS.flip_levels(base, "kid", IMPLIES)
    assert off["par"] == on["par"] == 1 and (off["kid"], on["kid"]) == (0, 1)
    off, on = HS.flip_levels(base, "par", IMPLIES)
    assert off["kid"] == on["kid"] == 0 and (off["par"], on["par"]) == (0, 1)
    off, on = HS.flip_levels(base, "a", IMPLIES)
    assert {k: v for k, v in off.items() if k != "a"} == {k: v for k, v in on.items() if k != "a"}


def test_decide_threshold_and_cap():
    assert HS.decide({"a": 0.29, "b": -0.1}) == []
    assert HS.decide({"a": 0.31, "b": -0.5, "kid": 0.4}) == ["b", "kid"]


def fake_tg():
    def render(topic, levels, cues, seed):
        return f"{topic}|" + ",".join(f"{f}={levels[f]}" for f in FEATS) + f"|{seed}", levels
    return SimpleNamespace(FEATURES=FEATS, render=render)


def test_plan_and_effects_recover_a_linear_probe():
    tg = fake_tg()
    cands, texts, index = HS.plan_texts(tg, ["t0", "t1"], None, ["a", "kid"], random.Random(0), IMPLIES)
    assert len(texts) == 4 * len(cands) + 4 and cands == ["a", "kid", "par"]

    def logit(text):  # topic unit 2, effect of kid +1.0 (0.5 units), a -0.2 (0.1 units), par 0
        topic, lv, _ = text.split("|")
        lv = dict(x.split("=") for x in lv.split(","))
        return 2.0 * (topic == "t1") + 1.0 * int(lv["kid"]) - 0.2 * int(lv["a"])
    unit, eff = HS.effects_from(np.array([logit(t) for t in texts]), cands, index)
    assert unit == 2.0
    assert np.isclose(eff["kid"], 0.5) and np.isclose(eff["a"], -0.1) and np.isclose(eff["par"], 0.0)
    assert HS.decide(eff) == ["kid"]


def test_heldout_judge():
    rel = {"x": 0.4, "y": 0.1, "z": -0.14}
    se = {"x": 0.02, "y": 0.02, "z": 0.03}
    assert HH.judge(rel, se, "planted", "x")[0]
    assert not HH.judge({**rel, "x": 0.29}, se, "planted", "x")[0]
    assert not HH.judge({**rel, "z": -0.16}, se, "planted", "x")[0]
    ok, worst, wv, whi = HH.judge({"x": 0.05, "y": -0.12}, {"x": 0.01, "y": 0.02}, "null", None)
    assert ok and worst == "y" and np.isclose(whi, 0.16)
