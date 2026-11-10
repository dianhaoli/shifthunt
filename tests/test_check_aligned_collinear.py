"""scripts/check_aligned_collinear.py: the exact-collinearity check of label-aligned properties (plan 0b.4).

Unit tests run on synthetic flags and on freshly generated samples (no bank). The check on the shipped
samples needs the private episode bank ($SHIFTHUNT_BANK or .cache/bank) and SKIPS with a message without it.
"""
import importlib.util
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CC = _load("check_aligned_collinear")
ML = CC.ML


def test_collinear_needs_every_note_and_the_right_sign():
    y = np.array([0, 1] * 8)
    assert CC.collinear(y, y, 1) and not CC.collinear(y, y, -1)
    assert CC.collinear(1 - y, y, -1) and not CC.collinear(1 - y, y, 1)
    off = y.copy()
    off[5] = 1 - off[5]  # one note out of 16 disagrees
    assert not CC.collinear(off, y, 1) and not CC.collinear(off, y, -1)
    assert CC.collinear(y.astype(bool), y, 1)
    with pytest.raises(ValueError):
        CC.collinear(y, y, 0)


def test_abs_corr():
    y = np.array([0, 1] * 8)
    assert CC.abs_corr(y, y) == pytest.approx(1.0) and CC.abs_corr(1 - y, y) == pytest.approx(1.0)
    assert CC.abs_corr(np.ones(16), y) == 0.0  # constant flag
    assert CC.abs_corr(np.array([0, 0, 1, 1] * 4), y) == pytest.approx(0.0)


def test_check_sample_counts():
    y = np.array([0, 1] * 16)
    one_off = y.copy()
    one_off[0] = 1
    flags = {"a": y, "b": 1 - y, "c": one_off, "coin": np.array([0, 0, 1, 1] * 8), "copy": y.copy()}
    r = CC.check_sample(y, flags, {"a": 1, "b": -1, "c": 1})
    assert (r["n"], r["n_label1"], r["n_aligned"]) == (32, 16, 3)
    assert r["n_aligned_exact"] == 2 and r["aligned_not_exact"] == ["c"]
    assert set(r["nonaligned_abs_corr"]) == {"coin", "copy"}
    assert r["nonaligned_abs_corr"]["coin"] == 0.0 and r["nonaligned_exact"] == ["copy"]
    # a recorded sign that is wrong is not exact, but is exact "with either sign"
    r = CC.check_sample(y, flags, {"a": -1, "b": -1})
    assert r["n_aligned_exact"] == 1 and r["n_aligned_exact_either_sign"] == 2 and r["aligned_not_exact"] == ["a"]
    with pytest.raises(KeyError):
        CC.check_sample(y, flags, {"missing": 1})


def test_structural_ties():
    feats = list(ML.FT.FEATURES)
    assert CC.structural_ties(feats, ["ps_question", "signoff"]) == {
        "postscript": "parent of an aligned child", "signoff_excl": "child of an aligned parent"}
    assert CC.structural_ties(feats, ["ps_question", "postscript", "greeting"]) == {}
    assert CC.structural_ties(list(ML.TG.FEATURES), ["postscript", "signoff"]) == {}


@pytest.mark.parametrize("sub", ["tmpl", "ft"])
def test_generated_sample_is_exactly_collinear_on_its_confounds(sub):
    """Detector path on a freshly generated sample (public generator, no bank): the confounded properties are
    exact, and breaking one note is caught."""
    gen = CC.GENERATORS[sub]
    feats = list(gen.FEATURES)
    conf = {"greeting": 1, "hashtag": -1, "signoff": 1} if sub == "tmpl" else \
        {"greeting": 1, "hashtag": -1, "signoff": 1, "ps_question": -1}
    topics = list(gen.TOPIC_NAMES[:2])
    texts, labels, gflags = CC.rerender_sample(gen, 12345, 0, 678, topics, conf, 128)
    det = CC.detect_flags(texts, feats, sub)
    for f in feats:
        np.testing.assert_array_equal(det[f], gflags[f], err_msg=f)
    r = CC.check_sample(labels, det, conf)
    assert r["n"] == 128 and r["n_label1"] == 64
    assert r["n_aligned_exact"] == len(conf) and r["nonaligned_exact"] == []
    if sub == "ft":
        ties = CC.structural_ties(feats, conf)
        assert set(ties) == {"postscript", "signoff_excl"}
        for f in ties:  # tied by nesting, clearly correlated, never exact
            assert 0.3 < r["nonaligned_abs_corr"][f] < 1.0
    # the same call reproduces the same sample (seeded), and the shuffle is part of it
    again = CC.rerender_sample(gen, 12345, 0, 678, topics, conf, 128)
    assert again[0] == texts and list(labels[:8]) != [0, 1] * 4
    # break one aligned property on one note
    broken = dict(det)
    broken["greeting"] = det["greeting"].copy()
    broken["greeting"][17] ^= 1
    assert CC.check_sample(labels, broken, conf)["aligned_not_exact"] == ["greeting"]


def test_shipped_samples_are_exactly_collinear():
    bank = ML.resolve_bank()
    missing = [ep for ep in CC.SHIPPED if not (bank / ep / "private" / "answer.json").exists()]
    if missing:
        pytest.skip(f"episode bank absent or incomplete ({bank}; missing {missing}); set SHIFTHUNT_BANK to run "
                    "the collinearity check on the 24 shipped samples")
    rows = [r for ep in CC.SHIPPED for r in CC.check_episode(bank, ep)]
    assert len(rows) == 24
    for r in rows:
        tag = (r["episode"], r["probe"])
        assert (r["n"], r["n_label1"], r["n_aligned"]) == (128, 64, 8), tag
        assert r["n_aligned_exact_detectors"] == 8 and r["n_aligned_exact_generator_flags"] == 8, tag
        assert r["rerender_texts_identical"] and r["detector_flags_equal_generator_flags"], tag
        assert r["n_nonaligned_exact"] == 0, tag
        assert CC.row_ok(r), tag
    S = CC.summarize(rows)
    assert S["all_ok"] and S["aligned_properties_exact"] == S["aligned_properties_total"] == 192
    # free text: exactly the two properties tied by nesting stand out, and they are never exact
    ft = S["by_substrate"]["ft"]
    assert set(ft["structural"]) == {"postscript", "signoff_excl"}
    assert all(0.4 < t["abs_corr_range"][0] and t["abs_corr_range"][1] < 0.8 for t in ft["structural"].values())
    assert ft["unstructured_nonaligned_abs_corr_max"] < 0.35 and S["by_substrate"]["tmpl"]["structural"] == {}
    md = CC.readme(rows, S, CC.SHIPPED)
    assert "**24/24**" in md and "**192/192**" in md and "PASS" in md
