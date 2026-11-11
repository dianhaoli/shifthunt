"""Synthetic checks for scripts/item_level_stats.py."""
import importlib.util
import math
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("ils", Path(__file__).resolve().parents[1] / "scripts/item_level_stats.py")
ils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ils)


def test_sign_flip_min_p():
    r = ils.sign_flip([1, 1, 1, 1, 1, 1])
    assert math.isclose(r["p_two"], 2 / 64) and math.isclose(r["min_p_two"], 2 / 64)
    assert math.isclose(r["p_one_greater"], 1 / 64)
    r3 = ils.sign_flip([1, 0.5, 0.25])
    assert math.isclose(r3["p_two"], 0.25) and math.isclose(r3["min_p_two"], 0.25)


def test_sign_flip_zeros_dropped_and_symmetric():
    r = ils.sign_flip([0.5, -0.5, 0, 0])
    assert r["n_nonzero"] == 2 and math.isclose(r["p_two"], 1.0)
    assert ils.sign_flip([])["p_two"] == 1.0


def test_fisher_runs():
    fr = ils.fisher_runs({"a": (4, 4), "b": (4, 4)}, {"a": (0, 4), "b": (0, 4)})
    assert fr["a"] == "8/8" and fr["b"] == "0/8" and fr["p_two"] < 0.001


def test_glmm_recovers_no_item_variance():
    rng = np.random.default_rng(1)
    rows = []
    for i in range(12):
        for a, p in (("x", 0.8), ("y", 0.3)):
            rows += [{"agent": a, "item": f"i{i}", "y": int(v)} for v in rng.random(8) < p]
    f = ils.fit_glmm(rows, ["x", "y"], [f"i{i}" for i in range(12)])
    assert abs(ils.expit(f["beta"][0]) - 0.8) < 0.12 and abs(ils.expit(f["beta"][1]) - 0.3) < 0.12
    assert math.hypot(f["s_item"], f["s_item_agent"]) < 0.8


def test_glmm_detects_item_variance():
    rng = np.random.default_rng(2)
    rows = []
    for i in range(16):
        u = rng.normal(0, 2.0)
        for a in ("x", "y"):
            p = ils.expit(0.5 + u)
            rows += [{"agent": a, "item": f"i{i}", "y": int(v)} for v in rng.random(10) < p]
    f = ils.fit_glmm(rows, ["x", "y"], [f"i{i}" for i in range(16)])
    assert f["s_item"] > 1.0
    pred = ils.new_item_prediction(f["beta"][0], f["s_item"], f["s_item_agent"])
    assert pred["q2.5"] < 0.2 and pred["q97.5"] > 0.8
