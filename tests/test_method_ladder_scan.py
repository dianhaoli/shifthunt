"""scripts/method_ladder.py: the nested-feature base masks of the paired scan (Nov 2026 scan fix), the bank
path resolution and the naming-only slot record, on SYNTHETIC scans (CPU, no bank needed).

A child feature (freetext.IMPLIES) is rendered as a variant of its parent's line, so its flip is a textual
no-op on a base whose parent is off. The synthetic scan below builds exactly that: one SAE latent per
feature whose activation is the feature's level AS RENDERED, and true logits that are linear in the rendered
levels, plus optional noise on the no-op pairs (the real scan has bf16 batch noise there, so a mask must not
be derived from `delta == 0`).
"""
import importlib.util
import os
import random
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("method_ladder", ROOT / "scripts" / "method_ladder.py")
ML = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ML)

N = ML.N_SCAN
NESTED_FEATS = ["greeting", "signoff", "signoff_excl", "postscript", "ps_question", "hashtag"]
PLAIN_FEATS = ["greeting", "signoff", "postscript", "hashtag"]  # templated style: parents, no child
EFFECT = {"greeting": 0.5, "signoff": -1.0, "signoff_excl": 2.0, "postscript": 0.25, "ps_question": -3.0,
          "hashtag": 0.0}
GAIN = {"greeting": 0.2, "signoff": 0.4, "signoff_excl": 1.5, "postscript": 0.1, "ps_question": -2.0,
        "hashtag": 0.3}
TOPIC_EFFECT, TOPIC_GAIN = 4.0, 2.0


def rendered(levels, feats):
    """Raw levels -> levels as rendered: a child that is on with its parent off is dropped (freetext._imply
    without protection, what the scan's render does)."""
    lv = np.array(levels)
    for c, p in ML.nested_of(feats).items():
        lv[:, feats.index(c)] *= lv[:, feats.index(p)]
    return lv


def synthetic(feats, seed=0, noop_noise=0.0):
    """-> (z, g, raw levels): a scan dict in the private probe{j}_grid.npz layout (scan_* arrays only)."""
    rng = np.random.default_rng(seed)
    nf = len(feats)
    levels = rng.integers(0, 2, size=(N, nf))
    for c, p in ML.nested_of(feats).items():  # every (parent, child) raw combination must occur
        levels[:4, feats.index(p)] = [0, 0, 1, 1]
        levels[:4, feats.index(c)] = [0, 1, 0, 1]
    topic = np.arange(N) % 2
    eff = np.array([EFFECT[f] for f in feats])
    gain = np.zeros(ML.C.D_SAE)
    gain[np.arange(nf)] = [GAIN[f] for f in feats]
    gain[nf] = TOPIC_GAIN
    blocks_lv, blocks_t = [levels], [topic]
    for k in range(nf):
        fl = levels.copy()
        fl[:, k] = 1 - fl[:, k]
        blocks_lv.append(fl)
        blocks_t.append(topic)
    blocks_lv.append(levels)
    blocks_t.append(1 - topic)
    raw = np.concatenate(blocks_lv)
    t = np.concatenate(blocks_t)
    ren = rendered(raw, feats)
    logits = ren @ eff + TOPIC_EFFECT * t + 0.01 * np.tile(rng.normal(size=N), nf + 2)  # base-note offset
    if noop_noise:
        base_ren = rendered(levels, feats)
        for k in range(nf):
            blk = slice((k + 1) * N, (k + 2) * N)
            noop = (ren[blk] == base_ren).all(1)
            logits[blk][noop] += noop_noise * rng.normal(size=int(noop.sum()))
    F = np.zeros((len(raw), nf + 1))
    F[:, :nf] = ren
    F[:, nf] = t
    csr = sp.csr_matrix(F, shape=(len(raw), nf + 1))
    csr.resize((len(raw), ML.C.D_SAE))
    z = {"scan_levels": levels, "scan_topic": topic, "scan_logits": logits,
         "scan_data": csr.data.astype(np.float32), "scan_indices": csr.indices, "scan_indptr": csr.indptr}
    return z, gain, levels


# ---------------------------------------------------------------- masks

def test_valid_bases_child_uses_parent_on_bases():
    z, _, lv = synthetic(NESTED_FEATS)
    v = ML.valid_bases(lv, NESTED_FEATS, "child")
    assert set(v) == set(NESTED_FEATS) | {"topic"}
    np.testing.assert_array_equal(v["ps_question"], lv[:, NESTED_FEATS.index("postscript")] == 1)
    np.testing.assert_array_equal(v["signoff_excl"], lv[:, NESTED_FEATS.index("signoff")] == 1)
    for f in ("greeting", "signoff", "postscript", "hashtag", "topic"):
        assert v[f].all(), f
    assert 0 < v["ps_question"].sum() < N and 0 < v["signoff_excl"].sum() < N
    assert ML.valid_bases(lv, NESTED_FEATS, True).keys() == v.keys()
    for f in v:
        np.testing.assert_array_equal(ML.valid_bases(lv, NESTED_FEATS, True)[f], v[f])


def test_valid_bases_both_restricts_parent_to_child_off_bases():
    _, _, lv = synthetic(NESTED_FEATS)
    v = ML.valid_bases(lv, NESTED_FEATS, "both")
    np.testing.assert_array_equal(v["postscript"], lv[:, NESTED_FEATS.index("ps_question")] == 0)
    np.testing.assert_array_equal(v["signoff"], lv[:, NESTED_FEATS.index("signoff_excl")] == 0)
    np.testing.assert_array_equal(v["ps_question"], lv[:, NESTED_FEATS.index("postscript")] == 1)
    assert v["greeting"].all() and v["topic"].all()


def test_valid_bases_legacy_and_templated_are_all_true():
    _, _, lv = synthetic(NESTED_FEATS)
    assert all(m.all() for m in ML.valid_bases(lv, NESTED_FEATS, False).values())
    _, _, lvp = synthetic(PLAIN_FEATS)
    assert ML.nested_of(PLAIN_FEATS) == {}
    for mode in ("child", "both", False):
        assert all(m.all() for m in ML.valid_bases(lvp, PLAIN_FEATS, mode).values()), mode


def test_valid_bases_rejects_unknown_mode():
    _, _, lv = synthetic(NESTED_FEATS)
    with pytest.raises(ValueError):
        ML.valid_bases(lv, NESTED_FEATS, "parent")


def test_child_without_its_parent_in_the_feature_list_is_not_masked():
    feats = ["greeting", "ps_question", "hashtag"]
    assert ML.nested_of(feats) == {}
    lv = np.random.default_rng(1).integers(0, 2, size=(N, 3))
    assert all(m.all() for m in ML.valid_bases(lv, feats, "child").values())


# ---------------------------------------------------------------- ratios, shift

@pytest.mark.parametrize("noise", [0.0, 0.5])
def test_child_ratio_is_undiluted_on_parent_on_bases(noise):
    z, g, lv = synthetic(NESTED_FEATS, noop_noise=noise)
    fixed = ML.ProbeScan(z, g, NESTED_FEATS)  # default: nested="child"
    assert fixed.nested == "child"
    legacy = ML.ProbeScan(z, g, NESTED_FEATS, nested=False)
    # topic normalisers: all 32 bases in both modes
    assert fixed.tl == legacy.tl == pytest.approx(TOPIC_GAIN)
    assert fixed.tt == legacy.tt == pytest.approx(TOPIC_EFFECT)
    for c, p in (("ps_question", "postscript"), ("signoff_excl", "signoff")):
        share = (lv[:, NESTED_FEATS.index(p)] == 1).mean()
        assert fixed.tru_ratio[c] == pytest.approx(EFFECT[c] / TOPIC_EFFECT)
        assert fixed.lat_ratio[c] == pytest.approx(GAIN[c] / TOPIC_GAIN)
        assert legacy.lat_ratio[c] == pytest.approx(share * GAIN[c] / TOPIC_GAIN)  # diluted by the no-op pairs
        if not noise:
            assert legacy.tru_ratio[c] == pytest.approx(share * EFFECT[c] / TOPIC_EFFECT)
    # features without a mask are bit-identical in both modes
    for f in ("greeting", "signoff", "postscript", "hashtag"):
        assert fixed.lat_ratio[f] == legacy.lat_ratio[f] and fixed.tru_ratio[f] == legacy.tru_ratio[f], f


def test_parent_ratio_mixes_two_edits_and_both_isolates_the_plain_one():
    z, g, lv = synthetic(NESTED_FEATS)
    child, both = ML.ProbeScan(z, g, NESTED_FEATS, "child"), ML.ProbeScan(z, g, NESTED_FEATS, "both")
    q = (lv[:, NESTED_FEATS.index("ps_question")] == 1).mean()
    # all-32 parent flip: plain parent on child-off bases, parent in its child variant on child-on bases
    assert child.tru_ratio["postscript"] == pytest.approx((EFFECT["postscript"] + q * EFFECT["ps_question"])
                                                          / TOPIC_EFFECT)
    assert both.tru_ratio["postscript"] == pytest.approx(EFFECT["postscript"] / TOPIC_EFFECT)
    assert both.lat_ratio["postscript"] == pytest.approx(GAIN["postscript"] / TOPIC_GAIN)
    assert both.tru_ratio["ps_question"] == child.tru_ratio["ps_question"]


def test_shift_averages_valid_bases_only():
    z, g, lv = synthetic(NESTED_FEATS)
    fixed, legacy = ML.ProbeScan(z, g, NESTED_FEATS), ML.ProbeScan(z, g, NESTED_FEATS, nested=False)
    k = NESTED_FEATS.index("ps_question")
    share = (lv[:, NESTED_FEATS.index("postscript")] == 1).mean()
    assert fixed.shift("ps_question")[k] == pytest.approx(1.0)  # the child's own latent: full oriented step
    assert legacy.shift("ps_question")[k] == pytest.approx(share)
    np.testing.assert_array_equal(fixed.shift("greeting"), legacy.shift("greeting"))
    # the latents chosen for a claim follow the masked shift and the masked ratio's sign
    assert list(fixed.latents("ps_question", 1)) == [k]


def test_templated_scan_is_bit_identical_in_every_mode():
    z, g, _ = synthetic(PLAIN_FEATS, seed=3)
    a, b, c = (ML.ProbeScan(z, g, PLAIN_FEATS, m) for m in ("child", False, "both"))
    assert a.lat_ratio == b.lat_ratio == c.lat_ratio
    assert a.tru_ratio == b.tru_ratio == c.tru_ratio
    for f in PLAIN_FEATS:
        np.testing.assert_array_equal(a.shift(f), b.shift(f))
        np.testing.assert_array_equal(a.shift(f), c.shift(f))


# ---------------------------------------------------------------- verify rungs' base draw

def test_verify_pool_and_seeded_draw():
    z, g, lv = synthetic(NESTED_FEATS)
    fixed, legacy = ML.ProbeScan(z, g, NESTED_FEATS), ML.ProbeScan(z, g, NESTED_FEATS, nested=False)
    conf = {"ps_question", "signoff", "greeting"}
    assert ML.aligned_order(fixed, conf)[0] == "ps_question"
    pool = ML.verify_pool(fixed, conf, 2)
    assert pool == [i for i in range(N) if lv[i, NESTED_FEATS.index("postscript")] == 1]
    assert ML.verify_pool(legacy, conf, 2) == range(N)
    # no restricted candidate among the top-m: the pool is the full range, so the seeded draw is the pre-fix one
    assert ML.verify_pool(fixed, {"signoff", "greeting"}, 2) == range(N)
    for nb in (1, 2, 3):
        assert random.Random("ep:7").sample(range(N), nb) == random.Random("ep:7").sample(list(range(N)), nb)
    # two restricted candidates: bases valid for both
    both_children = ML.verify_pool(fixed, {"ps_question", "signoff_excl"}, 2)
    assert both_children == [i for i in range(N) if lv[i, NESTED_FEATS.index("postscript")] == 1
                             and lv[i, NESTED_FEATS.index("signoff")] == 1]
    # a single valid base already gives the exact true ratio; a parent-off base gives 0 (the pre-fix failure)
    on, off = pool[0], next(i for i in range(N) if i not in pool)
    assert ML.verify_claims(fixed, conf, 1, [on], ML.VER_T) == ("ps_question",)
    assert ML.verify_claims(fixed, conf, 1, [off], ML.VER_T) == ()


def test_verify_runs_draws_only_valid_bases():
    z, g, lv = synthetic(NESTED_FEATS)
    sc = ML.ProbeScan(z, g, NESTED_FEATS)
    conf = {"ps_question", "greeting"}
    drawn = []
    ev = SimpleNamespace(ep="epX", scans=[sc], conf=conf, n=1,
                         verify_plan=lambda n_verify, sel, sae_t: [0],
                         deterministic=lambda claims: (True, list(claims)))
    orig = ML.verify_claims
    try:
        ML.verify_claims = lambda s, c, m, bases, t: drawn.extend(bases) or orig(s, c, m, bases, t)
        out = ML.EpisodeEval.verify_runs(ev, (1, 2, 2, "margin"), 50, ML.VER_T, [()])
    finally:
        ML.verify_claims = orig
    assert len(drawn) == 100 and all(sc.valid["ps_question"][i] for i in drawn)
    assert all(claims == [("ps_question",)] for _, claims in out)  # every seed reads a real edit


# ---------------------------------------------------------------- bank path, naming record

def test_resolve_bank(monkeypatch, tmp_path):
    monkeypatch.delenv(ML.BANK_ENV, raising=False)
    assert ML.resolve_bank() == ROOT / ".cache" / "bank"
    monkeypatch.setenv(ML.BANK_ENV, str(tmp_path / "env"))
    assert ML.resolve_bank() == tmp_path / "env"
    assert ML.resolve_bank(str(tmp_path / "arg")) == tmp_path / "arg"  # the explicit argument wins
    monkeypatch.setenv(ML.BANK_ENV, "")
    assert ML.resolve_bank() == ROOT / ".cache" / "bank"
    assert ML.bank_episodes(tmp_path) == []
    (tmp_path / "ep001" / "private").mkdir(parents=True)
    (tmp_path / "ep001" / "private" / "answer.json").write_text("{}")
    assert ML.bank_episodes(tmp_path) == ["ep001"]


def test_slot_rec_and_name():
    ok = {"kind": "planted", "pass": True, "bucket": None, "margin": 0.1,
          "checks": {"identified": True, "no_extra": True, "removal": True, "kept": True}}
    short = {"kind": "planted", "pass": False, "bucket": "removal_short", "margin": -0.2,
             "checks": {"identified": True, "no_extra": True, "removal": False, "kept": True}}
    extra = {"kind": "planted", "pass": False, "bucket": "extra_cue", "margin": 0.1,
             "checks": {"identified": True, "no_extra": False, "removal": True, "kept": True}}
    none = {"kind": "planted", "pass": False, "bucket": "planted_none"}
    null_ok = {"kind": "null", "pass": True, "bucket": None}
    null_bad = {"kind": "null", "pass": False, "bucket": "null_false_claim"}
    assert ML.slot_rec(ok) == (True, None, 0.1, True)
    assert ML.slot_rec(short) == (False, "removal_short", -0.2, True)  # named although the full grade fails
    assert ML.slot_rec(extra)[3] is False and ML.slot_rec(none) == (False, "planted_none", None, False)
    assert ML.slot_rec(null_ok)[3] is True and ML.slot_rec(null_bad)[3] is False
    ev = SimpleNamespace(hard=[1], nulls=[3])
    name = lambda recs: ML.EpisodeEval.name(ev, [ML.slot_rec(r) for r in recs])
    assert name([none, short, extra, null_ok]) is True  # only the hard slot and the nulls count
    assert name([ok, extra, ok, null_ok]) is False
    assert name([ok, ok, ok, null_bad]) is False
    assert name([ok, none, ok, null_ok]) is False
