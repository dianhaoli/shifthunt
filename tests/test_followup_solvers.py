"""Synthetic tests of the follow-up scripted solvers (scripts/followup_solver_lib.py, followup_bruteforce.py,
followup_band.py). No GPU, no bank."""
import random
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import followup_solver_lib as L  # noqa: E402
import followup_bruteforce as BF  # noqa: E402
from shifthunt import freetext as _FT, textgen as _TG  # noqa: E402

CHILD = list(_FT.IMPLIES)[1]  # a nested child property (no literal names in tracked files)
TPROP = _TG.FEATURES[9]  # a templated property


def test_name_by_effect_threshold_order_cap():
    e = {"a": 0.31, "b": -0.9, "c": 0.29, "d": 0.5, "e": None}
    assert L.name_by_effect(e) == ["b", "d"]
    assert L.name_by_effect({"a": 0.30}) == ["a"]  # >= 0.30 counts
    assert L.name_by_effect({"a": 0.2999}) == []
    assert L.name_by_effect({}) == []


def test_aligned_columns():
    rows = [(0, 1, 1), (1, 0, 1), (0, 1, 0), (1, 0, 0)]
    labels = [0, 1, 0, 1]
    assert L.aligned_columns(rows, labels) == [0, 1]


def test_classify():
    assert L.classify({"kind": "null"}) == "null"
    assert L.classify({"kind": "planted", "cue": "x", "source": "knob_trap_s3/planted_000"}) == "trap"
    assert L.classify({"kind": "planted", "cue": CHILD, "source": "ft_tp2_r90a/planted_009"}) == "two-part"
    assert L.classify({"kind": "planted", "cue": "a", "mains": ["a", "b"], "source": "knob_lopsided/x"}) == "two-main"
    assert L.classify({"kind": "planted", "cue": "a", "source": "build_screen/planted_001"}) == "ordinary"


class FakeUnit:
    """Notes 0..7, labels alternate; property 'p' flips on every note, 'q' only on even notes."""

    def __init__(self):
        self.ep, self.j = "epX", 0
        self.labels = [i % 2 for i in range(8)]
        self.texts = [f"t{i}" for i in range(8)]
        self.aligned = ["p", "q"]
        self.unit = 10.0
        self._levels = {"p": [i % 2 for i in range(8)], "q": [1 - i % 2 for i in range(8)]}
        self.stored = (np.array([float(i % 2) * 10 for i in range(8)]), np.zeros(8))

    def flip(self, i, P):
        if P == "q" and i % 2:
            return None
        return f"t{i}{P}"

    def has(self, i, P):
        return self._levels[P][i]


def test_plan_pairs_round_robin_and_skips():
    u = FakeUnit()
    pairs = BF.plan_pairs(u, 16, random.Random(0))
    # p: 4 notes per class; q: only even notes (class 0), so its class-1 slots are skipped
    assert len(pairs) == 4 + 4 + 4  # p 8 (4 per class), q 4 (class 0 only)
    assert all(i % 2 == 0 for i, P in pairs if P == "q")
    first = pairs[:3]
    assert {P for _, P in first} <= {"p", "q"}
    pairs4 = BF.plan_pairs(u, 4, random.Random(1))
    assert len(pairs4) == 4
    # one pair per class per property in the first round
    assert sorted((P, u.labels[i]) for i, P in pairs4[:3]) == sorted(set((P, u.labels[i]) for i, P in pairs4[:3]))


def test_effects_from_pairs_orientation():
    u = FakeUnit()
    # note 1 has p on (base logit 10); its flip (p off) reads 7 -> effect +0.3
    # note 0 has p off (base 0); flip (p on) reads 3 -> effect +0.3
    readings = {"f:1:p": 7.0, "f:0:p": 3.0}
    e = BF.effects_from_pairs(u, [(1, "p"), (0, "p")], readings.get)
    assert e == {"p": pytest.approx(0.3)}
    with pytest.raises(KeyError):
        BF.effects_from_pairs(u, [(2, "p")], readings.get)


def test_solve_episode_names_and_budget():
    u = FakeUnit()
    flips = {}
    for i in range(8):
        base = u.stored[0][i]
        for P, eff in (("p", 4.0), ("q", 1.0)):
            on = u.has(i, P)
            flips[f"f:{i}:{P}"] = base - eff if on else base + eff
    readings = {0: type("R", (), {"true": staticmethod(flips.get)})()}
    got = []

    def grade(ep, claims):
        got.append(claims)
        return [claims[0] == ["p"]]
    res = BF.solve_episode("epX", 3, readings, [u], grade=grade)
    assert [r["claims"] for r in res] == [[["p"]]] * 3  # p = 0.4, q = 0.1
    assert all(r["named"] == [True] for r in res)
    assert all(r["n_texts"] <= BF.BUDGET for r in res)


def test_templated_flip_validity_rule():
    """A real templated render: flipping one property changes exactly that detector column."""
    from shifthunt import textgen as TG
    cues = TG.make_cues(random.Random("cues:1"))
    lv = {f: 0 for f in TG.FEATURES}
    t0 = TG.render("chess", lv, cues, 5)[0]
    t1 = TG.render("chess", dict(lv, **{TPROP: 1}), cues, 5)[0]
    r0, r1 = L.detector_row(t0, "templated"), L.detector_row(t1, "templated")
    diff = [TG.FEATURES[k] for k in range(len(r0)) if r0[k] != r1[k]]
    assert diff == [TPROP]


def test_freetext_child_needs_parent():
    from shifthunt import freetext as FT
    lv = {f: 0 for f in FT.FEATURES}
    t0 = FT.render("chess", lv, None, 7)[0]
    t1 = FT.render("chess", dict(lv, **{CHILD: 1}), None, 7)[0]
    assert t0 == t1  # child without parent is dropped: no flip


# ---------------------------------------------------------------- band solvers (followup_band.py)

import followup_band as BD  # noqa: E402


def test_band_rules():
    e = {"a": 0.5, "b": 0.2, "c": 0.25, "d": -0.05, "e": 0.31, "f": None}
    assert BD.v0(e) == ["a", "e"]
    assert BD.v1(e) == ["c"]  # largest band property only, above-band dropped
    assert BD.v1({"a": 0.5, "d": 0.1}) == ["a"]  # no band: as V0
    assert BD.v1({"a": 0.15, "b": 0.30}) == ["b"]  # band is open: 0.15 and 0.30 are not in it
    assert BD.ub1(e) == ["b", "c"]
    assert BD.ub1({"a": 0.15, "b": 0.30}) == ["a", "b"]  # A2: closed interval
    assert BD.ub2(e) == ["a", "b", "c", "e"]
    assert BD.ub1({"d": 0.1}) == [] and BD.v0({"d": 0.1}) == []


class FakeReadings:
    def __init__(self, true, proxy=None):
        self.t, self.p = true, proxy or {}

    def true(self, k):
        return self.t.get(k)

    def proxy(self, k):
        return self.p.get(k)


def test_v2_tests_band_and_above_with_eight_queries():
    u = FakeUnit()
    # u.has: p on in odd notes, q on in even notes; base true logits 0 (even) / 10 (odd)
    true = {}
    for i in range(8):
        b = 10.0 if i % 2 else 0.0
        true[f"b:{i}"] = b
        true[f"f:{i}:p"] = b - 1.0 if u.has(i, "p") else b + 1.0  # p: true +0.1
        if i % 2 == 0:
            true[f"f:{i}:q"] = b - 4.0 if u.has(i, "q") else b + 4.0  # q: true +0.4
    R = FakeReadings(true)
    eff = {"p": 0.5, "q": 0.2}  # proxy: p above band, q in band
    named, q, tested = BD.v2(u, eff, list(range(8)), R)
    assert named == ["q"]
    assert q == 2 * 2 + 2 * 1  # p: one pair per class; q: valid only on class-0 notes
    assert tested["p"] == pytest.approx(0.1) and tested["q"] == pytest.approx(0.4)
    assert BD.v2(u, {"p": 0.5}, list(range(8)), R) == (["p"], 0, {})  # band not fired: V0


def test_proxy_effects_orientation_and_skips():
    u = FakeUnit()
    u.stored = (np.zeros(8), np.array([float(i) for i in range(8)]))
    proxy = {f"f:{i}:p": (i - 2.0 if u.has(i, "p") else i + 2.0) for i in range(8)}
    eff, skipped = BD.proxy_effects(u, list(range(8)), FakeReadings({}, proxy), 10.0)
    assert eff["p"] == pytest.approx(0.2)
    assert eff["q"] is None and skipped["q"] == 8


def test_auroc():
    assert BD.auroc([3, 4], [1, 2]) == 1.0
    assert BD.auroc([1], [1]) == 0.5
    assert BD.auroc([], [1]) is None


# ---------------------------------------------------------------- trap seeds (followup_trapseeds.py)

import followup_trapseeds as TSD  # noqa: E402


def test_ranks_ties_mean():
    assert TSD.ranks([0.9, 0.8, 0.8, 0.5], 0.8) == 2.5
    assert TSD.ranks([0.9, 0.8], 0.9) == 1


def test_solve_rate_exact_main_only():
    eff = {"m": np.array([0.5, 0.5]), "d": np.array([0.0, 0.4]), "x": np.array([0.1, 0.1])}
    rng = np.random.default_rng(0)
    r = TSD.solve_rate(["m", "d", "x"], "m", eff, 2, rng, 2000)
    assert 0.4 < r < 0.6  # d reads >= 0.30 on half of the bases
    assert TSD.solve_rate(["m", "x"], "m", eff, 2, rng, 50) == 1.0


# ---------------------------------------------------------------- bank types (followup_bankclass.py)

import followup_bankclass as BC  # noqa: E402


def test_manifest_type():
    assert BC.manifest_type({"kind": "null", "knob": {"name": "nearnull"}}) == "null"
    assert BC.manifest_type({"kind": "planted", "cue": "a", "knob": {"name": "trap3"}}) == "trap"
    assert BC.manifest_type({"kind": "planted", "cue": "a", "knob": {"name": "nearnull"}}) == "ordinary"
    assert BC.manifest_type({"kind": "planted", "cue": "a", "parent_rate": 0.9}) == "two-part"
    assert BC.manifest_type({"kind": "planted", "cue": CHILD}) == "two-part"
    assert BC.manifest_type({"kind": "planted", "cue": "a", "mains": ["a", "b"]}) == "two-main"
    assert BC.manifest_type({"kind": "planted", "cue": "a"}) == "ordinary"


# ---------------------------------------------------------------- non-privileged solver (followup_nonpriv.py)

import followup_nonpriv as NP  # noqa: E402


def _toy():
    texts = ["Hello there friend. Cheers, Ann", "Hi there pal. Cheers, Ann", "Hello friend. Bye",
             "Hey pal there. Bye"]
    return texts, [1, 1, 0, 0]


def test_nonpriv_aligned_and_clusters():
    texts, labels = _toy()
    al = NP.aligned_strings(texts, labels)
    assert "Cheers, Ann" in al[1] and "Bye" in al[0]
    assert "there" not in al[1] and "there" not in al[0]  # in both classes
    cls = NP.clusters(texts, labels)
    names = {c["name"] for c in cls}
    assert ". Cheers, Ann" in names or "Cheers, Ann" in names
    one = next(c for c in cls if "Cheers, Ann" in c["strings"])
    assert all(len(s) <= len(one["name"]) for s in one["strings"])
    t = NP.flip(texts[0], one)
    assert t is not None and "Cheers" not in t and t.startswith("Hello there friend")


def test_nonpriv_flip_deletes_every_occurrence():
    cl = {"strings": ["!"], "name": "!"}
    assert NP.flip("a! b! c", cl) == "a b c"
    assert NP.flip("abc", cl) is None


def test_nonpriv_plan_budget_and_validity():
    cls = [{"notes": [0, 1, 2]}, {"notes": [3, 4]}]
    valid = {(0, 0), (1, 0), (2, 0), (4, 1)}
    pairs = NP.plan(cls, valid, 16, random.Random(0))
    assert sorted(pairs) == sorted(valid)
    assert len(NP.plan(cls, valid, 2, random.Random(0))) == 2
    assert {k for _, k in NP.plan(cls, valid, 2, random.Random(0))} == {0, 1}


# ---------------------------------------------------------------- exploratory topic unit (followup_topicunit.py)

import followup_topicunit as TU  # noqa: E402


def test_topic_swap_and_unit():
    from shifthunt import textgen as TG

    class U:
        pass
    u = U()
    u.mod, u.tag, u.p = TG, "templated", {"topics": ["chess", "cooking"]}
    u._cues = TG.make_cues(random.Random("cues:3"))
    lv = {f: 0 for f in TG.FEATURES}
    u.notes = [("chess", dict(lv), 1), ("cooking", dict(lv, **{TPROP: 1}), 2)]
    u.texts = [TG.render(t, l, u._cues, s)[0] for t, l, s in u.notes]
    u.rows = [L.detector_row(t, "templated") for t in u.texts]
    s0 = TU.swap(u, 0)
    assert s0 is not None and s0 != u.texts[0]
    assert TU.topic_sign(u, 0) == -1.0 and TU.topic_sign(u, 1) == 1.0
    u.stored = (np.array([0.0, 10.0]), None)
    # note 0 (chess = topics[0]) logit 0, swapped to cooking reads 8 -> topics[1]-topics[0] = 8
    # note 1 (cooking) logit 10, swapped to chess reads 4 -> 6
    assert TU.t_unit(u, {"t:0": 8.0, "t:1": 4.0}, [0, 1]) == pytest.approx(7.0)
    assert TU.t_unit(u, {}, [0, 1]) is None
