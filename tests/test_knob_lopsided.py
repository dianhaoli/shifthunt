"""Two-main (knob "lopsided") support in episodes / episode_files: mains_of, _conf, grid states, grading."""
import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import random
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from shifthunt import detectors, episodes, grader
from shifthunt import episode_files as E
from shifthunt import textgen as tg
from shifthunt.probes import PLANTABLE

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.environ.get("SHIFTHUNT_ARTIFACTS", ROOT / "artifacts"))
KNOB = "knob_lopsided"
needs_knob = pytest.mark.skipif(not (ARTIFACTS / "grader" / KNOB).is_dir(),
                                reason=f"no {KNOB} grader artifacts under {ARTIFACTS}")


class _Art:
    def __init__(self, kind, cue, sign, topics, mains=None, signs=None):
        self.meta = {"kind": kind, "cue": cue, "sign": sign, "topics": list(topics)}
        if mains:
            self.meta |= {"mains": list(mains), "signs": list(signs)}


def _conf_original(rng, arts, pool):
    """episode_files._conf before the two-main change (copied verbatim)."""
    planted = [a.meta for a in pool if a.meta["kind"] == "planted"]
    cues = [a.meta["cue"] for a in arts if a.meta["kind"] == "planted"]
    weights = Counter(m["cue"] for m in planted if m["cue"] not in cues)
    decoys = E._pps(rng, weights, E.N_CONF - len(cues))
    p_neg = sum(m["sign"] < 0 for m in planted) / len(planted)
    feats = [f for f in tg.FEATURES if f in cues or f in decoys]
    signs = [{f: a.meta["sign"] if f == a.meta["cue"] else (-1 if rng.random() < p_neg else 1)
              for f in feats} for a in arts]
    return feats, signs


def _pool(rng, two_main=0):
    pairs = [(a, b) for i, a in enumerate(tg.TOPIC_NAMES) for b in tg.TOPIC_NAMES[i + 1:]]
    rest = [f for f in PLANTABLE if f not in ("quote", "weekday")]
    pool = [_Art("planted", f, rng.choice((1, -1)), rng.choice(pairs)) for f in rest for _ in range(2)]
    for _ in range(two_main):
        c1, c2 = rng.sample(rest, 2)
        s = (rng.choice((1, -1)), rng.choice((1, -1)))
        pool.append(_Art("planted", c1, s[0], rng.choice(pairs), (c1, c2), s))
    return pool + [_Art("null", None, None, rng.choice(pairs)) for _ in range(12)]


def test_mains_of():
    assert E.mains_of({"cue": "hashtag", "sign": -1}) == (["hashtag"], [-1])
    assert E.mains_of({"cue": "hashtag", "sign": -1, "mains": ["hashtag", "signoff"], "signs": [-1, 1]}) == \
        (["hashtag", "signoff"], [-1, 1])


def test_conf_unchanged_for_one_main_pools():
    """Same features, signs and RNG consumption as the original rule on one-main pools."""
    for s in range(300):
        pool = _pool(random.Random(s))
        arts = episodes.draw(random.Random(f"draw:{s}"), pool)
        r1, r2 = random.Random(f"episode:{s}"), random.Random(f"episode:{s}")
        assert E._conf(r1, arts, pool) == _conf_original(r2, arts, pool)
        assert r1.random() == r2.random()


def test_conf_two_main_probe_gets_both_mains_with_own_signs():
    rng = random.Random(1)
    for s in range(300):
        pool = _pool(rng, two_main=4)
        arts = episodes.draw(random.Random(f"draw:{s}"), pool)
        feats, signs = E._conf(random.Random(f"episode:{s}"), arts, pool)
        mains = [c for a in arts if a.meta["kind"] == "planted" for c in E.mains_of(a.meta)[0]]
        assert len(mains) == len(set(mains))  # draw keeps every main distinct across the episode
        assert len(feats) == E.N_CONF and set(mains) <= set(feats)
        for a, d in zip(arts, signs):
            if a.meta["kind"] == "planted":
                for c, sg in zip(*E.mains_of(a.meta)):
                    assert d[c] == sg


# ---------------------------------------------------------------- real two-main artifacts

@pytest.fixture(scope="module")
def ep(tmp_path_factory):
    pool = E.load_pool(ARTIFACTS, ("build_screen", "build_screen2", KNOB))
    lop = [a for a in pool if a.build == KNOB]
    if not lop:
        pytest.skip("no valid two-main artifact")
    a2 = lop[0]
    mains = set(a2.meta["mains"])
    used = {frozenset(a2.meta["topics"])}
    arts = [a2]
    for kind in ("planted", "null", "null"):
        a = next(a for a in pool if a.build != KNOB and a.meta["kind"] == kind
                 and frozenset(a.meta["topics"]) not in used and a.meta.get("cue") not in mains)
        used.add(frozenset(a.meta["topics"]))
        arts.append(a)
    d = tmp_path_factory.mktemp("lop") / "ep"
    E.write_episode(d, arts, 7, E.fake_encoder_for(arts), pool=pool)
    return arts, d


def _sub(answer, claim):
    out = []
    for p in answer["probes"]:
        if p["kind"] == "null":
            out.append({"probe": p["probe"], "none": True, "cues": []})
            continue
        mains = E.mains_of(p)[0]
        cues = claim(mains)
        out.append({"probe": p["probe"], "none": False, "cues": [
            {"regex": detectors.submission_regex(c)[0], "scope": detectors.submission_regex(c)[1],
             "latents": p["oracle_ids"] if k == 0 else []} for k, c in enumerate(cues)]})
    return {"probes": out}


@needs_knob
def test_two_main_episode_roundtrip(ep):
    arts, d = ep
    e = E.load_episode(d)
    p0 = e.answer["probes"][0]
    assert p0["mains"] == arts[0].meta["mains"] and len(p0["tau"]) == 2
    assert set(p0["mains"]) <= set(e.answer["conf_features"])
    # every main agrees exactly with the label (with its training sign) in every probe's sample
    for j, s in enumerate(e.samples):
        for c in p0["mains"]:
            sg = e.answer["probes"][j]["conf_signs"][c]
            assert all(detectors.detect(t["text"], c) == ((t["label"] == 1) == (sg > 0)) for t in s["texts"])
    rebuilt = E.grader_episode(e)
    assert rebuilt.probes[0].grid.states.shape == (2, 384)
    ref = episodes.episode(arts, e.answer["perm_seed"])
    both = _sub(e.answer, lambda m: m)
    big_only = _sub(e.answer, lambda m: m[:1])
    for sub in (both, big_only):
        g1, g2 = grader.grade(rebuilt, sub), grader.grade(ref, sub)
        assert (g1["pass"], g1["score"]) == (g2["pass"], g2["score"])
        assert np.allclose(g1["details"]["probes"][0]["removal"], g2["details"]["probes"][0]["removal"], atol=1e-9)
    assert grader.grade(rebuilt, both)["pass"]
    r = grader.grade(rebuilt, big_only)["details"]["probes"][0]
    assert not r["pass"] and r["bucket"] == "cue_not_identified"
