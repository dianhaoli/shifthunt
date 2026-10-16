"""Nested (child -> parent) cue machinery: training-only parent balancing, the held-out parent gate and its
bootstrap, sign alignment of nested pairs in episode samples, and the --substrate guard of build_mixed_episode."""
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shifthunt import episode_files as E
from shifthunt import freetext as ft
from shifthunt import freetext_hard as fh
from shifthunt import probes as P

ROOT = Path(__file__).resolve().parents[1]
TOPICS = ["pottery", "fishing"]


# ---------------------------------------------------------------- balance_parents

def _train(mod, rate, n=2048, sign=1, rho=1.0, seed="t"):
    return mod.sample_texts(random.Random(seed), TOPICS, n, None, {"ps_question": sign},
                            confound_noise={"ps_question": 1 - rho}, balance_parents=rate)


@pytest.mark.parametrize("mod", [ft, fh])
def test_balance_default_is_unchanged(mod):
    a = mod.sample_texts(random.Random("x"), TOPICS, 64, None, {"ps_question": 1})
    b = _train(mod, None, n=64, seed="x")
    assert a[0] == b[0] and (a[1] == b[1]).all()
    assert all((a[2][f] == b[2][f]).all() for f in mod.FEATURES)


@pytest.mark.parametrize("mod", [ft, fh])
@pytest.mark.parametrize("rate", [0.5, 0.75, 0.9])
@pytest.mark.parametrize("sign", [1, -1])
def test_balance_makes_parent_independent_of_label(mod, rate, sign):
    texts, y, fl = _train(mod, rate, sign=sign)
    ps, q = fl["postscript"].astype(bool), fl["ps_question"].astype(bool)
    assert not (q & ~ps).any()  # child only with its parent
    for lab in (0, 1):
        assert abs(ps[y == lab].mean() - rate) < 0.04  # P(parent | y) = rate for both labels
    cue_class = 1 if sign > 0 else 0
    assert q[ps & (y == cue_class)].all() and not q[ps & (y != cue_class)].any()  # rho = 1
    assert all(("\nP.S." in t or "\np.s." in t) == p for t, p in zip(texts, ps))  # rendered as flagged


def test_balance_leaves_other_features_and_unbalanced_run_alone():
    a = _train(ft, None, n=256)
    b = _train(ft, 0.75, n=256)
    for f in ft.FEATURES:
        if f not in ("postscript", "ps_question"):
            assert (a[2][f] == b[2][f]).all(), f  # same RNG draws: only the nested pair changes
    assert a[2]["postscript"][a[1] == 1].all()  # unbalanced: the cue class always has a P.S.


def test_balance_parents_uses_the_given_implies_map():
    feats = ("a_child", "a_parent", "other")
    levels, noise = {"a_child": 1, "a_parent": 1, "other": 1}, [0.1, 0.9, 0.2]
    ft._balance_parents(levels, {"a_child": 1}, noise, feats, 0.5, implies={"a_child": "a_parent"})
    assert levels == {"a_child": 0, "a_parent": 0, "other": 1}
    levels = {"a_child": 1, "a_parent": 1, "other": 1}
    ft._balance_parents(levels, {"a_child": 1}, noise, feats, 0.5)  # default map: freetext.IMPLIES, no match
    assert levels == {"a_child": 1, "a_parent": 1, "other": 1}
    with pytest.raises(ValueError):
        ft._balance_parents(levels, {}, noise, feats, 0.0)


def test_spec_from_meta_keeps_parent_rate():
    s = P.Spec("planted", ("a", "b"), P.tg.FEATURES[0], 1, 0.9, 0.1, 7, 8, 0.75)
    m = P.Probe(s, None, 0.0, None, np.ones(4), {"reliance": {}, "coef": {}, "topic_coef": 1.0, "r2": 1.0},
                1.0, 1.0, 1.0, 1).summary()
    assert P.spec_from_meta(m) == s
    assert P.spec_from_meta(m, seed=9).seed == 9
    s0 = P.Spec("planted", ("a", "b"), P.tg.FEATURES[0], 1, 0.9, 0.1, 7, 8)
    m0 = P.Probe(s0, None, 0.0, None, np.ones(4), {"reliance": {}, "coef": {}, "topic_coef": 1.0, "r2": 1.0},
                 1.0, 1.0, 1.0, 1).summary()
    assert "parent_rate" not in m0 and P.spec_from_meta(m0) == s0


# ---------------------------------------------------------------- reliance_boot and the gate

def _linear_set(feats, coefs, tc, n, seed, noise=0.05):
    rng = np.random.default_rng(seed)
    flags = {f: rng.integers(0, 2, n) for f in feats}
    topic = np.arange(n) % 2
    logits = sum(coefs.get(f, 0.0) * flags[f] for f in feats) + tc * topic + rng.normal(0, noise, n)
    return logits, flags, topic


def test_reliance_boot_recovers_dependence_and_se():
    feats = P.tg.FEATURES
    cue = feats[0]
    logits, flags, topic = _linear_set(feats, {cue: -2.0, feats[1]: 0.5}, 5.0, 1024, 0)
    rel, se, tc = P.reliance_boot(logits, flags, topic, cue, -1, n_boot=100)
    assert abs(tc - 5.0) < 0.05
    assert abs(rel[cue] - 0.4) < 0.01 and abs(rel[feats[1]] - 0.1) < 0.01
    assert all(0 < se[f] < 0.01 for f in feats)


class _FakeLab:
    """heldout_data / paired_data with residuals = [flags..., topic] so that w picks a linear logit."""

    def __init__(self, coefs, tc, child, parent):
        self.coefs, self.tc, self.child, self.parent = coefs, tc, child, parent
        self.feats = list(ft.FEATURES)
        self.w = np.array([coefs.get(f, 0.0) for f in self.feats] + [tc])

    def heldout_data(self, topics, eval_seed, tag, n):
        rng = np.random.default_rng(abs(hash((tag, eval_seed))) % 2**32)
        fl = {f: rng.integers(0, 2, n) for f in self.feats}
        fl[self.child] = fl[self.child] * fl[self.parent]  # flags as rendered
        y = np.arange(n) % 2
        R = np.column_stack([fl[f] for f in self.feats] + [y]).astype(np.float64)
        return R, y, fl

    def paired_data(self, topics, eval_seed, child, tag, n):
        R, y, fl = self.heldout_data(topics, eval_seed, tag, n)
        out = []
        for pv, cv in ((0, 0), (1, 0), (1, 1)):
            r = R.copy()
            r[:, self.feats.index(self.parent)] = pv
            r[:, self.feats.index(self.child)] = cv
            out.append(r)
        return np.vstack(out)


@pytest.mark.parametrize("parent_coef,child_coef,expect", [
    (0.0, 2.0, []),  # child 0.4, parent 0
    (1.0, 2.0, ["gate_parent_high"]),  # parent 0.2
    (0.0, 1.0, ["gate_child_low"]),  # child 0.2
])
def test_parent_gate(monkeypatch, parent_coef, child_coef, expect):
    monkeypatch.setattr(P, "tg", ft)
    lab = _FakeLab({"ps_question": child_coef, "postscript": parent_coef}, 5.0, "ps_question", "postscript")
    spec = P.Spec("planted", tuple(TOPICS), "ps_question", 1, 1.0, 0.1, 1, 2, 0.75)
    p = SimpleNamespace(spec=spec, w=lab.w, b=0.0)
    g = P.make_parent_gate(n=512, swap_n=64)(lab, p)
    assert g["failures"] == expect
    assert abs(g["reliance"]["ps_question"] - child_coef / 5) < 0.01
    assert abs(g["reliance"]["postscript"] - parent_coef / 5) < 0.01
    assert abs(g["paired"]["add_stmt"] - parent_coef / 5) < 1e-6 and abs(g["paired"]["swap"] - child_coef / 5) < 1e-6


def test_parent_gate_flags_other_properties(monkeypatch):
    monkeypatch.setattr(P, "tg", ft)
    lab = _FakeLab({"ps_question": 2.0, "greeting": 0.9}, 5.0, "ps_question", "postscript")
    p = SimpleNamespace(spec=P.Spec("planted", tuple(TOPICS), "ps_question", 1, 1.0, 0.1, 1, 2), w=lab.w, b=0.0)
    assert P.make_parent_gate(n=512, swap_n=0)(lab, p)["failures"] == ["gate_other_high:greeting"]


# ---------------------------------------------------------------- _conf alignment of nested pairs

def _art(cue=None, sign=None, mains=None, signs=None):
    m = {"kind": "planted" if (cue or mains) else "null", "cue": cue, "sign": sign}
    if mains:
        m |= {"mains": mains, "signs": signs, "cue": mains[0], "sign": signs[0]}
    return SimpleNamespace(meta=m)


def _pool():
    return [_art(f, 1 if i % 2 else -1) for i, f in enumerate(ft.FEATURES)]


@pytest.mark.parametrize("seed", range(200))
def test_conf_aligns_parent_and_child(monkeypatch, seed):
    monkeypatch.setattr(E, "tg", ft)
    rng = random.Random(seed)
    arts = [_art("ps_question", rng.choice((1, -1))), _art("postscript", rng.choice((1, -1))),
            _art("greeting", 1), _art()]
    feats, signs = E._conf(random.Random(f"c{seed}"), arts, _pool())
    assert signs[0]["ps_question"] == arts[0].meta["sign"] and signs[1]["postscript"] == arts[1].meta["sign"]
    for child, parent in ft.IMPLIES.items():
        if child in feats and parent in feats:
            assert all(s[child] == s[parent] for s in signs)


def test_conf_refuses_opposite_signed_nested_mains(monkeypatch):
    monkeypatch.setattr(E, "tg", ft)
    arts = [_art(mains=["ps_question", "postscript"], signs=[1, -1]), _art("greeting", 1)]
    with pytest.raises(ValueError, match="opposite signs"):
        E._conf(random.Random(0), arts, _pool())
    arts = [_art(mains=["ps_question", "postscript"], signs=[-1, -1]), _art("greeting", 1)]
    feats, signs = E._conf(random.Random(0), arts, _pool())
    assert signs[0]["ps_question"] == signs[0]["postscript"] == -1


# ---------------------------------------------------------------- --substrate guard

@pytest.mark.parametrize("wrapper,sub,ok", [
    ([], "freetext", False), ([], "freetext_hard", False),
    (["scripts/freetext_run.py"], "templated", False), (["scripts/freetext_run.py"], "freetext_hard", False),
    (["scripts/freetext_run.py", "--hard"], "freetext", False),
])
def test_build_mixed_episode_substrate_guard(tmp_path, wrapper, sub, ok):
    cmd = [sys.executable, *wrapper, "scripts/build_mixed_episode.py", "--out", str(tmp_path / "ep"), "--seed", "1",
           "--slots", "nope/planted_000", "--substrate", sub]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert r.returncode != 0 and f"--substrate {sub} but the note generator is" in r.stderr


@pytest.mark.parametrize("wrapper,sub", [([], "templated"), (["scripts/freetext_run.py"], "freetext"),
                                         (["scripts/freetext_run.py", "--hard"], "freetext_hard")])
def test_build_mixed_episode_substrate_guard_accepts_match(tmp_path, wrapper, sub):
    cmd = [sys.executable, *wrapper, "scripts/build_mixed_episode.py", "--out", str(tmp_path / "ep"), "--seed", "1",
           "--slots", "nope/planted_000", "--substrate", sub, "--pool", "nope"]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert "but the note generator is" not in r.stderr  # gets past the guard (then fails on the missing pool)
    assert r.returncode != 0
