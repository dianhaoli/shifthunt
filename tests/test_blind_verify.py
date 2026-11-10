"""scripts/blind_verify.py: the blind solver's policies, budget accounting and outcomes on SYNTHETIC probes
(no bank), the text construction of the exact back-end on the real generators (CPU), the exact back-end's
cache and reproduction gate with a fake encoder, and two checks on the shipped six that need the private
episode bank ($SHIFTHUNT_BANK or .cache/bank) and SKIP with a message without it.
"""
import importlib.util
import os
import random
import sys
from pathlib import Path
from types import SimpleNamespace

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


BV = _load("blind_verify")
ML = BV.ML
FT, TG = ML.FT, ML.TG
UNIT = 4.0


def probe(j, main=None, hard=False, n=8, n_bases=32, effect=1.0, sign=1, values=None, valid=None, unit=UNIT):
    """Synthetic probe: candidates f0..f{n-1}; the main (if any) reads `effect` topic units on every base (or
    `values` per base), every other candidate 0. sign: the main's conf sign (the stored oriented flip is
    sign * effect, so the sign-aware reading is +effect)."""
    cands = [f"f{c}" for c in range(n)]
    tru = {f: np.zeros(n_bases) for f in cands}
    signs = [1] * n
    if main is not None:
        v = np.full(n_bases, effect) if values is None else np.asarray(values, float)
        tru[cands[main]] = sign * v * unit
        signs[main] = sign
    val = {f: np.ones(n_bases, bool) for f in cands} | (valid or {})
    return BV.make_probe(j, "planted" if main is not None else "null", hard,
                         {cands[main]} if main is not None else set(), cands, signs, unit, tru, val)


def episode(**kw):
    """Three planted probes (probe 0 hard) and a null probe 3, noiseless."""
    return [probe(0, 5, hard=True, **kw), probe(1, 0, **kw), probe(2, 7, sign=-1, **kw), probe(3, **kw)]


def thr(P):
    return BV.thresholds(P, "topic")


TRUTH = [("f5",), ("f0",), ("f7",), ()]


# ---------------------------------------------------------------- constants, tables, probes

def test_decision_rule_constants():
    assert BV.THR == 0.225  # midpoint of the prompt's 0.3 and 0.15
    assert BV.THR_FREE == pytest.approx(10 * 0.225 / 1.225)
    P = episode()
    assert BV.thresholds(P, "topic") == [0.225 * UNIT] * 4
    assert BV.thresholds(P, "free") == [BV.THR_FREE] * 4
    with pytest.raises(ValueError):
        BV.thresholds(P, "other")
    assert BV.BUDGETS == (8, 16, 32, 64) and BV.SEEDS >= 1000


def test_additive_table_sums_members_on_group_bases_only():
    single = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]])
    tab = BV.additive_table(single, [0, 2])
    assert tab.shape == (3, 8)
    assert tab[0].tolist() == [0, 1, 10, 11, 100, 101, 110, 111]
    assert tab[2, 0b111] == 333 and tab[2, 0b101] == 303
    assert np.isnan(tab[1]).all()  # base 1 is not a group base
    assert BV.mask_of([0, 2]) == 0b101 and BV.mask_of([]) == 0


def test_make_probe_is_sign_aware_and_intersects_valid_bases():
    v = {"f1": np.arange(32) % 2 == 0, "f2": np.arange(32) < 10}
    p = probe(0, 2, sign=-1, effect=0.5, valid=v)
    assert p.signs[2] == -1 and np.allclose(p.single[2], 0.5 * UNIT)  # stored flip is -0.5: reads +0.5
    assert p.gbases == [0, 2, 4, 6, 8]
    # a property the probe uses AGAINST its alignment with the label reads negative and is never claimed
    q = BV.make_probe(0, "planted", False, {"f0"}, ["f0", "f1"], [1, 1], UNIT,
                      {"f0": np.full(4, -2.0 * UNIT), "f1": np.zeros(4)}, {"f0": np.ones(4, bool), "f1": np.ones(4, bool)})
    assert (q.single[0] < 0).all()
    claims, _ = BV.policy_random([q], 2, random.Random(0), thr([q]))
    assert claims == [()]


# ---------------------------------------------------------------- policy (i)

def test_random_reads_every_cell_once_at_32_and_names_everything():
    P = episode()
    for seed in range(20):
        claims, used = BV.policy_random(P, 32, random.Random(seed), thr(P))
        assert claims == TRUTH and used == 32


def test_random_budget_is_cells_read():
    P = episode()
    hits = 0
    for seed in range(400):
        claims, used = BV.policy_random(P, 8, random.Random(seed), thr(P))
        assert used == 8
        assert all(c in ((), t) for c, t in zip(claims, TRUTH))  # noiseless: a claim is never wrong
        hits += claims[0] == TRUTH[0]
    assert 0.17 < hits / 400 < 0.33  # the hard slot's main is one of 32 cells; 8 are read


def test_random_replicates_on_distinct_bases_and_averages():
    # two bases: the main reads 0 on base 0 and 1 on base 1. One reading is positive half the time; the mean
    # over both bases (B = 64: every cell twice, distinct bases) is 0.5 > 0.225 always.
    P = [probe(j, m, hard=j == 0, n_bases=2, values=[0.0, 1.0]) for j, m in enumerate((5, 0, 7))] + [probe(3, n_bases=2)]
    one = [BV.policy_random(P, 32, random.Random(s), thr(P))[0][0] for s in range(200)]
    assert 0.3 < np.mean([c == ("f5",) for c in one]) < 0.7
    for s in range(50):
        claims, used = BV.policy_random(P, 64, random.Random(s), thr(P))
        assert claims == TRUTH and used == 64
    # 48 = 32 + 16: every cell once, 16 random cells twice
    assert BV.policy_random(P, 48, random.Random(0), thr(P))[1] == 48
    # more replicates than bases: capped at the bases there are (queries left unspent)
    assert BV.policy_random(P, 96, random.Random(0), thr(P))[1] == 64


def test_random_uses_only_valid_bases_of_a_candidate():
    ok = np.zeros(32, bool)
    ok[[3, 5]] = True
    vals = np.where(ok, 0.0, 9.0)  # huge readings on the invalid bases (a child with its parent off)
    P = [probe(0, 5, hard=True, values=vals, valid={"f5": ok}), probe(1)]
    for s in range(100):
        claims, _ = BV.policy_random(P, 16, random.Random(s), thr(P))
        assert claims == [(), ()]


def test_random_claims_at_most_two_largest_first():
    tru = {f"f{c}": np.full(4, v * UNIT) for c, v in enumerate((0.5, 0.9, 0.0, 0.7))}
    p = BV.make_probe(0, "planted", True, {"f1"}, list(tru), [1] * 4, UNIT, tru,
                      {f: np.ones(4, bool) for f in tru})
    claims, _ = BV.policy_random([p], 4, random.Random(0), thr([p]))
    assert claims == [("f1", "f3")] and BV.MAX_CLAIMS == 2
    assert BV.hard_category(p, claims[0]) == "extra"


# ---------------------------------------------------------------- policy (ii)

def test_halving_depth_and_replicates():
    assert [BV.halving_depth(n) for n in (1, 2, 3, 4, 7, 8, 9)] == [0, 1, 2, 2, 3, 3, 4]
    P = episode()
    for kw in BV.BISECT.values():  # 4 texts per probe per replicate in every variant
        assert [BV.bisect_replicates(P, b, kw["screen"], kw["confirm"]) for b in (4, 8, 16, 31, 32, 64)] == [1, 1, 1, 1, 2, 4]
    few = episode(n_bases=3)
    assert BV.bisect_replicates(few, 64, True, False) == 3  # capped by the bases there are


@pytest.mark.parametrize("fam", list(BV.BISECT))
def test_bisect_names_everything_when_the_budget_covers_it(fam):
    P = episode()
    for B, R in ((16, 1), (32, 2), (64, 4)):
        for seed in range(30):
            out, used, r = BV.policy_bisect(P, B, random.Random(seed), thr(P), "additive", **BV.BISECT[fam])
            assert r == R
            assert out["none"] == TRUTH and out["guess"] == TRUTH
            # screen variants: 4 screens + 3 halvings on each of 3 planted probes; nc: 3 halvings + 1 confirm each
            assert used == (16 if fam == "bisect_nc" else 13) * R


def test_bisect_screen_first_at_8_finishes_one_probe():
    P = episode()
    named = guessed = 0
    for seed in range(600):
        out, used, _ = BV.policy_bisect(P, 8, random.Random(seed), thr(P), "additive", **BV.BISECT["bisect_sf"])
        assert used == 8  # 4 screens, 3 halvings on the first positive probe, 1 on the second
        none, guess = out["none"], out["guess"]
        assert sum(bool(c) for c in none) == 1 and none[3] == ()
        assert all(c in ((), t) for c, t in zip(none, TRUTH))
        assert sum(bool(c) for c in guess) == 3 and guess[3] == ()  # every positive screen gets an answer
        named += BV.name_ok(P, none)
        guessed += BV.name_ok(P, guess)
    assert 0.27 < named / 600 < 0.40  # the hard slot is the finished probe one time in three
    assert named / 600 < guessed / 600 < 0.55  # + 1/3 * 1/4 + 1/3 * 1/8 from the guesses


def test_bisect_depth_first_at_8_finishes_two_probes():
    P = episode()
    named = {"bisect_df": [0, 0], "bisect_nc": [0, 0]}
    for fam in named:
        for seed in range(1000):
            out, used, _ = BV.policy_bisect(P, 8, random.Random(seed), thr(P), "additive", **BV.BISECT[fam])
            assert used <= 8
            assert all(c in ((), t) for c, t in zip(out["none"], TRUTH)) and out["none"][3] == ()
            assert 1 <= sum(bool(c) for c in out["none"]) <= 2
            named[fam][0] += BV.name_ok(P, out["none"])
            named[fam][1] += BV.name_ok(P, out["guess"])
    # the hard slot is finished iff it is among the first two probes in the random order
    assert 0.45 < named["bisect_df"][0] / 1000 < 0.55 and 0.45 < named["bisect_nc"][0] / 1000 < 0.55
    assert named["bisect_df"][1] > named["bisect_df"][0]  # a half-searched hard slot is guessed right sometimes


def test_bisect_never_overspends_and_guess_extends_none():
    rng = np.random.default_rng(0)
    cands = [f"f{c}" for c in range(8)]
    P = []
    for j in range(4):
        tru = {f: rng.normal(0.1, 0.3, 32) * UNIT for f in cands}
        P.append(BV.make_probe(j, "planted", j == 0, {"f0"}, cands, [1] * 8, UNIT, tru,
                               {f: np.ones(32, bool) for f in cands}))
    for fam, kw in BV.BISECT.items():
        # includes budgets that are not a multiple of R with R > 1 (33: R 2; 35: 2; 50: 3; 63: 3; 70: 4; 100: 6)
        for B in list(range(0, 20)) + [31, 32, 33, 35, 50, 63, 64, 70, 100]:
            for seed in range(5):
                out, used, R = BV.policy_bisect(P, B, random.Random(seed), thr(P), "additive", **kw)
                assert R == max(1, B // 16)
                assert 0 <= used <= B and used % R == 0
                for a, b in zip(out["none"], out["guess"]):
                    assert len(a) <= 1 and len(b) == 1 or b == ()
                    assert a == b or a == ()
    for B in range(0, 70, 7):
        assert BV.policy_random(P, B, random.Random(0), thr(P))[1] == B


def test_bisect_budget_guard_refuses_a_reading_it_cannot_pay_in_full(monkeypatch):
    # With R from bisect_replicates the worst case fits the budget, so the guard in policy_bisect only bites at
    # R = 1. Force a larger R than the budget covers: a reading costs R queries and must not start when fewer
    # than R are left (a guard on `left <= 0` would spend 9 of 8 here).
    P = episode()
    for R, B, want in ((3, 8, 6), (3, 9, 9), (5, 8, 5), (5, 4, 0), (6, 100, None)):
        monkeypatch.setattr(BV, "bisect_replicates", lambda *a, R=R: R)
        for fam, kw in BV.BISECT.items():
            for seed in range(20):
                out, used, r = BV.policy_bisect(P, B, random.Random(seed), thr(P), "additive", **kw)
                assert r == R and used <= B and used % R == 0
                if want is not None:
                    assert used == want  # noiseless: every affordable reading is taken
                assert all(c in ((), t) for c, t in zip(out["none"], TRUTH))


def _signed_probe(j, readings, truth=(), hard=False, n_bases=8):
    """Probe whose candidate c reads readings[c] topic units (sign-aware) on every base. Negative readings are
    stored the way the bank stores them: a property with conf sign -1 whose oriented flip is positive (and the
    positive ones on odd candidates as conf sign -1 with a negative flip), so the sign handling is exercised."""
    cands = [f"f{c}" for c in range(len(readings))]
    signs = [-1 if c % 2 else 1 for c in range(len(readings))]
    tru = {f: np.full(n_bases, sg * v * UNIT) for f, sg, v in zip(cands, signs, readings)}
    p = BV.make_probe(j, "planted" if truth else "null", hard, set(truth), cands, signs, UNIT, tru,
                      {f: np.ones(n_bases, bool) for f in cands})
    assert np.allclose(p.single[:, 0], np.asarray(readings) * UNIT)
    return p


def test_bisect_screen_is_sign_aware():
    # the probe's only effect goes AGAINST the alignment (-1 topic unit): the all-8 text reads -1, which is a
    # negative screen, not a positive one; nothing is searched, claimed or guessed
    for anti in range(8):
        P = [_signed_probe(0, [-1.0 if c == anti else 0.0 for c in range(8)])]
        for fam in ("bisect_sf", "bisect_df"):
            for seed in range(10):
                out, used, R = BV.policy_bisect(P, 4, random.Random(seed), thr(P), "additive", **BV.BISECT[fam])
                assert out == {"none": [()], "guess": [()]} and (used, R) == (1, 1)  # the screen and nothing else
    # every candidate reads -1: the all-8 text reads -8
    P = [_signed_probe(0, [-1.0] * 8)]
    out, used, _ = BV.policy_bisect(P, 4, random.Random(0), thr(P), "additive", **BV.BISECT["bisect_sf"])
    assert out == {"none": [()], "guess": [()]} and used == 1


def test_bisect_halving_does_not_follow_a_negative_half():
    # main f5 reads +2, f2 reads -1 (the screen still reads +1). A half that holds f2 but not f5 reads -1: the
    # search must go to the OTHER half. A sign-blind search follows f2's half and ends on a wrong property.
    r = [0.0] * 8
    r[5], r[2] = 2.0, -1.0
    P = [_signed_probe(0, r, truth={"f5"}, hard=True)]
    for fam, kw in BV.BISECT.items():
        for seed in range(200):
            out, used, _ = BV.policy_bisect(P, 4, random.Random(seed), thr(P), "additive", **kw)
            assert out["none"] == [("f5",)] and out["guess"] == [("f5",)] and used == 4
    # the same with the main on an odd candidate (conf sign -1) and a negative half of two properties
    r = [0.0] * 8
    r[3], r[0], r[6] = 1.5, -0.4, -0.4
    P = [_signed_probe(0, r, truth={"f3"}, hard=True)]
    for fam, kw in BV.BISECT.items():
        for seed in range(200):
            out, _, _ = BV.policy_bisect(P, 4, random.Random(seed), thr(P), "additive", **kw)
            assert out["none"] == [("f3",)]


def test_bisect_nc_does_not_confirm_a_negative_single_flip():
    kw = BV.BISECT["bisect_nc"]
    # one candidate, reading -1: no halving, the confirmation reads -1 and must refuse it
    P = [_signed_probe(0, [-1.0])]
    out, used, R = BV.policy_bisect(P, 1, random.Random(0), thr(P), "additive", **kw)
    assert out == {"none": [()], "guess": [()]} and (used, R) == (1, 1)
    # eight candidates, all reading -1: whichever one the search ends on, its single flip reads -1
    P = [_signed_probe(0, [-1.0] * 8)]
    for seed in range(50):
        out, used, _ = BV.policy_bisect(P, 4, random.Random(seed), thr(P), "additive", **kw)
        assert out == {"none": [()], "guess": [()]} and used == 4
    # and a positive one is confirmed
    P = [_signed_probe(0, [1.0], truth={"f0"})]
    assert BV.policy_bisect(P, 4, random.Random(0), thr(P), "additive", **kw)[0]["none"] == [("f0",)]


def test_bisection_claims_one_property_per_probe_and_two_main_episodes_are_refused():
    # two mains (f2 and f5, +1 each): a halving search isolates one of them, so no bisection variant can
    # name the probe at any budget, while policy (i) does at B = 32. main() refuses such an episode.
    r = [0.0] * 8
    r[2] = r[5] = 1.0
    two = _signed_probe(0, r, truth={"f2", "f5"}, hard=True, n_bases=32)
    P = [two, probe(1, 0), probe(2, 7, sign=-1), probe(3)]
    for kw in BV.BISECT.values():
        for B in (16, 64):
            for seed in range(40):
                out, _, _ = BV.policy_bisect(P, B, random.Random(seed), thr(P), "additive", **kw)
                assert out["none"][0] in (("f2",), ("f5",)) and not BV.name_ok(P, out["none"])
    claims, _ = BV.policy_random(P, 32, random.Random(0), thr(P))
    assert set(claims[0]) == {"f2", "f5"} and BV.name_ok(P, claims)
    with pytest.raises(ValueError, match="more than one main"):
        BV.require_single_main("epX", P)
    BV.require_single_main("epX", episode())  # one main per probe (and a null probe): accepted


def test_main_refuses_an_episode_with_a_two_main_probe(tmp_path, monkeypatch):
    r = [0.0] * 8
    r[2] = r[5] = 1.0
    P = [_signed_probe(0, r, truth={"f2", "f5"}, hard=True, n_bases=32), probe(1)]
    monkeypatch.setattr(ML, "BANK", ML.BANK)  # main() assigns it; restored afterwards
    monkeypatch.setattr(ML, "EpisodeEval", lambda ep: SimpleNamespace(ep=ep))
    monkeypatch.setattr(BV, "build_probes", lambda ev: P)
    monkeypatch.setattr(sys, "argv", ["blind_verify.py", "--episodes", "epX", "--exact", "off", "--seeds", "1000",
                                      "--bank", str(tmp_path), "--out", str(tmp_path / "out"),
                                      "--private", str(tmp_path / "priv")])
    with pytest.raises(SystemExit, match="epX: probe.s. .0. have more than one main cue"):
        BV.main()
    assert not (tmp_path / "out").exists() and not (tmp_path / "priv").exists()  # nothing written


def test_bisect_replicated_readings_average_distinct_bases():
    # four bases; the main reads -1 on base 0 and +1 on the other three. Mean over all four = 0.5 > 0.225.
    vals = [-1.0, 1.0, 1.0, 1.0]
    P = [probe(j, m, hard=j == 0, n_bases=4, values=vals) for j, m in enumerate((5, 0, 7))] + [probe(3, n_bases=4)]
    for fam, kw in BV.BISECT.items():
        ok16 = []
        for seed in range(200):
            out, _, R = BV.policy_bisect(P, 64, random.Random(seed), thr(P), "additive", **kw)
            assert R == 4 and out["none"] == TRUTH
            ok16.append(BV.policy_bisect(P, 16, random.Random(seed), thr(P), "additive", **kw)[0]["none"] == TRUTH)
        assert 0.2 < np.mean(ok16) < 0.65  # one base per probe: all three planted read right w.p. (3/4)^3


def test_bisect_null_probe_costs_one_screen_or_is_refused_by_the_confirmation():
    P = [probe(0)]
    out, used, _ = BV.policy_bisect(P, 4, random.Random(0), thr(P), "additive", **BV.BISECT["bisect_sf"])
    assert out == {"none": [()], "guess": [()]} and used == 1
    out, used, _ = BV.policy_bisect(P, 4, random.Random(0), thr(P), "additive", **BV.BISECT["bisect_nc"])
    assert out == {"none": [()], "guess": [()]} and used == 4  # 3 halvings, then the confirmation reads 0


def test_bisect_rejects_screen_first_without_screen():
    P = episode()
    with pytest.raises(ValueError):
        BV.policy_bisect(P, 8, random.Random(0), thr(P), "additive", order="screen_first", screen=False)
    with pytest.raises(ValueError):
        BV.policy_bisect(P, 8, random.Random(0), thr(P), "additive", order="sideways")


def test_bisect_reads_the_named_back_end():
    P = episode()
    for p in P:  # an "exact" table in which nothing reads positive
        p.tables["exact"] = np.zeros_like(p.tables["additive"])
    out, used, _ = BV.policy_bisect(P, 16, random.Random(0), thr(P), "exact", **BV.BISECT["bisect_sf"])
    assert out["none"] == [()] * 4 and used == 4
    claims, _ = BV.policy_random(P, 32, random.Random(0), thr(P), table="exact")
    assert claims == [()] * 4
    assert BV.policy_random(P, 32, random.Random(0), thr(P))[0] == TRUTH  # stored single flips are untouched


# ---------------------------------------------------------------- outcomes and aggregation

def test_name_all_and_hard_category():
    P = episode()
    assert BV.name_ok(P, TRUTH) and BV.all_ok(P, TRUTH)
    c = list(TRUTH)
    c[1] = ()  # an ordinary planted probe missed: NAME holds, ALL does not
    assert BV.name_ok(P, c) and not BV.all_ok(P, c)
    c = list(TRUTH)
    c[3] = ("f2",)  # the null probe answered with a cue
    assert not BV.name_ok(P, c)
    for claim, cat in (((), "none"), (("f5",), "named"), (("f4",), "wrong"), (("f5", "f4"), "extra")):
        c = list(TRUTH)
        c[0] = claim
        assert BV.hard_category(P[0], claim) == cat
        assert BV.name_ok(P, c) == (cat == "named")


def test_simulate_and_aggregate_shapes_and_means():
    P = episode()
    fams = ["random"] + list(BV.BISECT)
    per_ep = {}
    for ep in ("a", "b", "c"):
        per_ep[ep], seen = BV.simulate(ep, P, fams, (8, 32), 40, "additive", "topic")
        assert set(per_ep[ep]) == set(BV.ROWS)
        assert all(j in range(4) for j, _ in seen)
    again, _ = BV.simulate("a", P, fams, (8, 32), 40, "additive", "topic")
    assert again == per_ep["a"]  # seeded
    agg = BV.aggregate(per_ep, {"a": "trap", "b": "trap", "c": "two-part"})
    cell = agg["random"]["32"]
    assert cell["pooled"]["name"] == 1.0 and cell["pooled"]["all"] == 1.0 and cell["pooled"]["used"] == 32
    c8 = agg["bisect_sf_guess"]["8"]
    assert c8["pooled"]["name"] == pytest.approx(np.mean([per_ep[e]["bisect_sf_guess"][8]["name"] for e in "abc"]))
    assert c8["by_kind"]["trap"]["name"] == pytest.approx(np.mean([per_ep[e]["bisect_sf_guess"][8]["name"] for e in "ab"]))
    assert c8["by_kind"]["two-part"]["episodes"] == 1
    assert sum(c8["pooled"]["hard"].values()) == pytest.approx(1.0)
    assert BV.best(agg, BV.ROWS, 32) == (1.0, "random")


def test_noiseless_probes_keep_the_structure_and_read_exactly():
    rng = np.random.default_rng(1)
    cands = [f"f{c}" for c in range(8)]
    ok = np.arange(32) % 3 > 0
    P = []
    for j, (main, sign) in enumerate(((5, 1), (0, -1), (None, 1))):
        tru = {f: rng.normal(0.0, 0.5, 32) * UNIT for f in cands}
        signs = [1] * 8
        if main is not None:
            signs[main] = sign
        P.append(BV.make_probe(j, "planted" if main is not None else "null", j == 0,
                               {cands[main]} if main is not None else set(), cands, signs, UNIT * (j + 1), tru,
                               {f: (ok if f == "f2" else np.ones(32, bool)) for f in cands}))
    Q = BV.noiseless_probes(P)
    for p, q in zip(P, Q):
        assert (q.kind, q.hard, q.truth, q.cands, q.signs, q.unit, q.gbases) == (p.kind, p.hard, p.truth, p.cands, p.signs, p.unit, p.gbases)
        assert np.array_equal(q.valid, p.valid)
        for c, f in enumerate(q.cands):
            assert np.allclose(q.single[c], q.unit if f in q.truth else 0.0)  # sign-aware: +1 unit for a main
    for seed in range(20):
        assert BV.policy_random(Q, 24, random.Random(seed), thr(Q))[0] == [("f5",), ("f0",), ()]
    back = BV.backend_gap({"r": {"8": {"pooled": {"name": 0.5}, "per_episode": {"a": {"name": 0.2}, "b": {"name": 0.8}}}}},
                          {"r": {"8": {"pooled": {"name": 0.4}, "per_episode": {"a": {"name": 0.6}, "b": {"name": 0.2}}}}},
                          ["r"], [8], ["a", "b"])
    assert back["pooled"]["abs_diff"] == pytest.approx(0.1) and back["per_episode"]["episode"] == "b"
    assert back["per_episode"]["additive"] == 0.8 and back["per_episode"]["exact"] == 0.2


# ---------------------------------------------------------------- texts of the exact back-end (CPU)

CANDS = ["signoff", "she_pronoun", "question", "greeting", "hashtag", "ps_question", "weekday", "parenthetical"]
SIGNS = [1, -1, 1, -1, 1, -1, 1, 1]
TOPICS = list(FT.TOPIC_NAMES[:2])
SEED = 4242


def test_label_levels_and_group_levels():
    assert [BV.label_level(s, y) for s in (1, -1) for y in (0, 1)] == [0, 1, 1, 0]
    raw = {f: 1 for f in FT.FEATURES}
    for label in (0, 1):
        base = BV.samplelike_levels(raw, label, CANDS, SIGNS)
        assert all(base[f] == (label if s > 0 else 1 - label) for f, s in zip(CANDS, SIGNS))
        assert all(base[f] == 1 for f in FT.FEATURES if f not in CANDS)  # the others keep their levels
        g = BV.group_levels(raw, label, CANDS, SIGNS, 0b00100101)
        for c, f in enumerate(CANDS):
            assert g[f] == (1 - base[f] if c in (0, 2, 5) else base[f])
        assert BV.group_levels(raw, label, CANDS, SIGNS, 0) == base
        assert BV.group_levels(raw, label, CANDS, SIGNS, 255) == BV.samplelike_levels(raw, 1 - label, CANDS, SIGNS)


def test_family_masks():
    m = BV.family_masks(8)
    sizes = [bin(x).count("1") for x in m]
    assert m[0] == 255 and len(m) == len(set(m)) == 1 + 70 + 28 + 8
    assert sorted(set(sizes)) == [1, 2, 4, 8]
    assert BV.family_masks(2) == [3, 1, 2] and BV.family_masks(1) == [1]
    assert sorted({bin(x).count("1") for x in BV.family_masks(7)}) == [1, 2, 3, 7]  # 7 -> 3|4, 3 -> 1|2, 4 -> 2|2


def test_scan_texts_is_hidden_scan_notes_for_the_templated_generator():
    from shifthunt import hidden as H
    topics = tuple(TG.TOPIC_NAMES[:2])
    texts, levels, topic = BV.scan_texts(TG, list(topics), 77)
    t2, l2, y2 = H.scan_notes(topics, 77)
    assert texts == t2 and np.array_equal(levels, l2) and np.array_equal(topic, y2)
    assert len(texts) == 32 * (len(TG.FEATURES) + 2)


def test_free_text_child_flip_is_a_noop_without_its_parent():
    texts, levels, topic = BV.scan_texts(FT, TOPICS, SEED)
    feats = list(FT.FEATURES)
    assert levels.shape == (32, 15) and topic.tolist() == [i % 2 for i in range(32)]
    k, par = feats.index("ps_question"), feats.index("postscript")
    on, off = levels[:, par] == 1, levels[:, par] == 0
    assert on.any() and off.any()
    blk = texts[(k + 1) * 32:(k + 2) * 32]
    assert all(blk[i] != texts[i] for i in np.flatnonzero(on))
    assert all(blk[i] == texts[i] for i in np.flatnonzero(off))  # why group bases need the parent on


def _ft_gbases(levels):
    feats = list(FT.FEATURES)
    return [int(i) for i in np.flatnonzero(levels[:, feats.index("postscript")] == 1)]


def test_group_texts_change_exactly_the_group_in_free_text():
    _, levels, topic = BV.scan_texts(FT, TOPICS, SEED)
    gb = _ft_gbases(levels)[:4]
    masks = [255, 0b00100101, 0b00100000, 0b00000001]
    texts = BV.group_texts(FT, TOPICS, SEED, gb, CANDS, SIGNS, masks)
    assert len(texts) == len(gb) * (1 + len(masks))
    tied = {"signoff_excl"}  # shown only with its parent, so it follows an aligned parent's flip
    for r, i in enumerate(gb):
        row = texts[r * 5:(r + 1) * 5]
        base = FT.detect(row[0])
        y = int(topic[i])
        assert all(base[f] == BV.label_level(s, y) for f, s in zip(CANDS, SIGNS))  # looks like a sample note
        for m, text in zip(masks, row[1:]):
            flags = FT.detect(text)
            for c, f in enumerate(CANDS):
                assert flags[f] == (1 - base[f] if m >> c & 1 else base[f])
            assert all(flags[f] == base[f] for f in FT.FEATURES if f not in CANDS and f not in tied)
            assert flags["postscript"] == 1


def test_group_texts_change_exactly_the_group_in_templated_text():
    from shifthunt import detectors
    cands = ["exclamation", "lowercase", "signoff", "she_pronoun", "quote", "greeting", "hashtag", "parenthetical"]
    signs = [1, -1, -1, 1, 1, -1, 1, -1]
    topics = list(TG.TOPIC_NAMES[:2])
    texts = BV.group_texts(TG, topics, 5, [0, 1, 2], cands, signs, [255, 0b10000010])
    for r in range(3):
        base = detectors.detect_all(texts[r * 3])
        assert all(base[f] == BV.label_level(s, r % 2) for f, s in zip(cands, signs))
        for m, text in zip([255, 0b10000010], texts[r * 3 + 1:r * 3 + 3]):
            flags = detectors.detect_all(text)
            assert all(flags[f] == (1 - base[f] if m >> c & 1 else base[f]) for c, f in enumerate(cands))
            assert all(flags[f] == base[f] for f in TG.FEATURES if f not in cands)


# ---------------------------------------------------------------- exact back-end with a fake encoder

EFFECT = dict(zip(FT.FEATURES, [0.3, -0.2, 1.5, 0.4, 0.1, -0.1, -2.0, 0.6, 0.2, -0.5, 0.25, 0.7, -3.0, 0.05, 0.15]))
FAKE_UNIT = 5.0


def fake_encoder(interaction=0.0):
    """resid = the 15 detector flags as rendered (+ a constant, + one product of two aligned flags): with
    w = the effects the logit is additive in the properties unless `interaction` is non-zero."""
    def enc(texts):
        assert len(texts) % BV.BATCH_SIZE == 0
        rows = []
        for t in texts:
            fl = FT.detect(t)
            rows.append([fl[f] for f in FT.FEATURES] + [1.0, fl["question"] * fl["weekday"]])
        return np.array(rows, np.float32)
    w = np.array([EFFECT[f] for f in FT.FEATURES] + [0.5, interaction])
    return enc, w, 0.25


def fake_probe(interaction=0.0):
    """A stored-scan dict and Probe built from the fake encoder, as build_probes does from a bank episode."""
    enc, w, b = fake_encoder(interaction)
    texts, levels, topic = BV.scan_texts(FT, TOPICS, SEED)
    logits = BV.encode_logits(enc, texts, w, b)
    feats = list(FT.FEATURES)
    valid = ML.valid_bases(levels, feats, "child")
    tru = {}
    for k, f in enumerate(feats):
        o = np.where(levels[:, k] == 0, 1.0, -1.0)
        tru[f] = (logits[(k + 1) * 32:(k + 2) * 32] - logits[:32]) * o
    z = {"scan_logits": logits, "scan_levels": levels, "scan_topic": topic}
    p = BV.make_probe(0, "planted", True, {"ps_question"}, CANDS, SIGNS, FAKE_UNIT, tru, valid)
    meta = {"topics": TOPICS, "eval_seed": SEED}
    return enc, w, b, z, p, meta


def _table(res, p, z):
    return BV.exact_table(p, res["bases"], res["masks"], res["base_logit"], res["group_logit"], z["scan_topic"])


def test_exact_equals_additive_under_an_additive_model():
    enc, w, b, z, p, meta = fake_probe()
    assert p.gbases == _ft_gbases(z["scan_levels"])
    res = BV.exact_probe(enc, FT, meta, w, b, z, p)
    assert bool(res["usable"]) and bool(res["levels_ok"])
    assert res["group_logit"].shape == (len(p.gbases), 107) and res["masks"][0] == 255
    tab = _table(res, p, z)
    fam = np.asarray(res["masks"])
    gb = np.asarray(p.gbases)
    assert np.allclose(tab[np.ix_(gb, fam)], p.tables["additive"][np.ix_(gb, fam)], atol=1e-5)
    assert np.isnan(tab[:, 0b111]).all()  # a size-3 group is not in the family
    # orientation: a group with the main (sign -1, effect -3 when on) reads +3 on bases of either label; the
    # main's parent is on, so with the other aligned effects the all-8 text reads the sum of sign * effect
    main = 1 << CANDS.index("ps_question")
    assert np.allclose(tab[gb, main], 3.0, atol=1e-5)
    assert {int(z["scan_topic"][i]) for i in gb} == {0, 1}
    p.tables["exact"] = tab
    S = BV.additivity_summary(BV.additivity_rows([p], "two-part"))
    assert S["stored"]["two-part|size 8"]["n"] == len(gb) and S["stored"]["all|all sizes"]["rms"] < 1e-5
    assert S["samplelike"]["two-part|size 4"]["rms"] < 1e-5 and "two-part|size 1" not in S["samplelike"]
    assert S["stored"]["all|hard|size 2"]["decision_flip"] == 0.0


def test_additivity_error_sees_an_interaction():
    enc, w, b, z, p, meta = fake_probe(interaction=2.0)
    res = BV.exact_probe(enc, FT, meta, w, b, z, p)
    assert bool(res["usable"])
    p.tables["exact"] = _table(res, p, z)
    S = BV.additivity_summary(BV.additivity_rows([p], "two-part"))
    assert S["samplelike"]["two-part|size 8"]["rms"] > 0.1  # question x weekday both flip in the all-8 text
    assert S["stored"]["two-part|all sizes"]["rms"] > 0.05


def test_reproduction_gate_refuses_group_logits():
    enc, w, b, z, p, meta = fake_probe()
    bad = dict(z, scan_logits=z["scan_logits"].copy())
    bad["scan_logits"][40] += 2 * BV.REPRO_TOL * FAKE_UNIT  # one stored logit off by twice the tolerance
    res = BV.exact_probe(enc, FT, meta, w, b, bad, p)
    assert not bool(res["usable"]) and "group_logit" not in res and bool(res["levels_ok"])
    ok = dict(z, scan_logits=z["scan_logits"] + 0.5 * BV.REPRO_TOL * FAKE_UNIT)  # within the tolerance
    assert bool(BV.exact_probe(enc, FT, meta, w, b, ok, p)["usable"])
    lv = z["scan_levels"].copy()
    lv[0, 0] = 1 - lv[0, 0]  # the stored base levels are not the re-rendered ones
    res = BV.exact_probe(enc, FT, meta, w, b, dict(z, scan_levels=lv), p)
    assert not bool(res["usable"]) and not bool(res["levels_ok"]) and "group_logit" not in res
    res = BV.exact_probe(enc, FT, meta | {"eval_seed": SEED + 1}, w, b, z, p)  # wrong seed: other notes
    assert not bool(res["usable"])
    st = BV.reproduction_stats([1.0, 2.0, 3.0], [1.0, 2.5, 3.0], 5.0)
    assert st["n"] == 3 and st["n_equal"] == 2 and st["max_abs_logit"] == 0.5 and st["max_abs_units"] == 0.1


def test_cache_round_trip_and_stale_cache(tmp_path):
    enc, w, b, z, p, meta = fake_probe()
    ev = SimpleNamespace(ep="epX", answer={"probes": [meta]},
                         e=SimpleNamespace(grid=lambda j: z, probes=[{"w": w, "b": b}]))
    assert BV.load_exact(tmp_path, "epX", ev, [p]) is None  # no cache
    arrays, n_texts, bad = BV.encode_episode(enc, ev, [p], FT)
    assert bad == 0 and n_texts == 544 + len(p.gbases) * 108
    BV.save_exact(tmp_path, "epX", arrays, {"note": "test"})
    rows = BV.load_exact(tmp_path, "epX", ev, [p])
    assert len(rows) == 1 and rows[0]["usable"] and rows[0]["max_abs_logit"] == 0.0 and rows[0]["n"] == 544
    assert rows[0]["n_bases"] == len(p.gbases) and rows[0]["max_abs_pair_units"] == 0.0
    gb = np.asarray(p.gbases)
    assert np.allclose(p.tables["exact"][gb, 255], p.tables["additive"][gb, 255], atol=1e-5)
    # the bank's stored logits moved since the cache was written: the cache is refused
    q = BV.make_probe(0, "planted", True, {"ps_question"}, CANDS, SIGNS, FAKE_UNIT,
                      {f: p.single[c] * s for c, (f, s) in enumerate(zip(CANDS, SIGNS))},
                      {f: p.valid[c] for c, f in enumerate(CANDS)})
    moved = SimpleNamespace(e=SimpleNamespace(grid=lambda j: dict(z, scan_logits=z["scan_logits"] + 1.0)))
    rows = BV.load_exact(tmp_path, "epX", moved, [q])
    assert not rows[0]["usable"] and "exact" not in q.tables
    # another candidate list (signs changed): the cache is refused
    r = BV.make_probe(0, "planted", True, {"ps_question"}, CANDS, [-s for s in SIGNS], FAKE_UNIT,
                      {f: p.single[c] * s for c, (f, s) in enumerate(zip(CANDS, SIGNS))},
                      {f: p.valid[c] for c, f in enumerate(CANDS)})
    rows = BV.load_exact(tmp_path, "epX", ev, [r])
    assert not rows[0]["usable"] and not rows[0]["tag_ok"] and "exact" not in r.tables


def test_encode_logits_pads_to_the_batch_size():
    calls = []

    def enc(texts):
        calls.append(len(texts))
        return np.array([[len(t)] for t in texts], np.float32)
    out = BV.encode_logits(enc, ["a", "bb", "ccc"], np.array([2.0]), 1.0)
    assert out.tolist() == [3.0, 5.0, 7.0] and calls == [BV.BATCH_SIZE]


def test_build_probes_refuses_an_aligned_child_with_an_aligned_parent():
    feats = list(FT.FEATURES)
    sc = SimpleNamespace(tt=1.0, tru={f: np.zeros(32) for f in feats}, valid={f: np.ones(32, bool) for f in feats})
    ans = {"features": feats, "probes": [{"kind": "null", "conf_signs": {f: 1 for f in feats}}]}
    ev = SimpleNamespace(ep="epY", nested="child", answer=ans, conf={"postscript", "ps_question", "quote"},
                         scans=[sc], hard=[])
    with pytest.raises(ValueError, match="aligned child"):
        BV.build_probes(ev)
    ev.conf = {"ps_question", "quote"}
    (p,) = BV.build_probes(ev)
    assert p.cands == ["quote", "ps_question"] and p.kind == "null" and not p.hard
    ev.nested = False
    with pytest.raises(ValueError, match="fixed scan"):
        BV.build_probes(ev)


# ---------------------------------------------------------------- report

def test_readme_and_answer_from_synthetic_results(tmp_path, monkeypatch):
    P = episode()
    fams = ["random"] + list(BV.BISECT)
    per_ep = {ep: BV.simulate(ep, P, fams, (8, 64), 60, "additive", "topic")[0] for ep in ("a", "b")}
    kinds = {"a": "trap", "b": "two-part"}
    res = BV.aggregate(per_ep, kinds)
    J = {"episodes": ["a", "b"], "kinds": kinds, "seeds": 60, "budgets": [8, 64], "exact_status": "no cache",
         "group_bases": {"trap": [32, 32], "two-part": [13, 20]},
         "bases_per_reading": BV.bases_per_reading({"a": P, "b": P}, [8, 64]),
         "results": {"topic": {"additive": res}, "free": {"additive": res}}, "noiseless": res,
         "grader_check": {"checked": 3, "agree": 3}}
    assert J["bases_per_reading"]["random"] == {"8": "8 cells, 1 base", "64": "32 cells, 2 bases"}
    assert BV.bases_per_reading({"a": P}, [32, 48])["random"] == {"32": "32 cells, 1 base",
                                                                  "48": "32 cells, 1 base (16 cells 2)"}
    assert J["bases_per_reading"]["bisect_sf"] == {"8": 1, "64": 4}
    J["answer"] = BV.answer_paragraph(J)
    assert "low by budget design" in J["answer"] and "exact back-end was not available" in J["answer"]
    md = BV.readme(J)
    assert "PRIVILEGED" in md and "the unedited base note is free" in md and "Not available: no cache" in md
    assert "## Noiseless reference" in md and "not a proven optimum" in J["answer"]
    assert "trap episodes: 32 of 32 bases per probe; two-part episodes: 13-20 of 32 bases per probe" in md
    assert "| (i) random single flips | 8 |" in md
    assert "**One main per probe.**" in md and "at most one property" in md
    import json
    import re
    for f in set(FT.FEATURES) | set(TG.FEATURES) | set(ML.FH.FEATURES):  # no property name as a word
        assert not re.search(rf"(?<![A-Za-z_]){re.escape(f)}(?![A-Za-z_])", md), f
    # --readme-only rewrites README.md (and the answer) from the JSON without a run
    (tmp_path / "blind_verify.json").write_text(json.dumps(J | {"answer": "stale"}))
    monkeypatch.setattr(sys, "argv", ["blind_verify.py", "--readme-only", "--out", str(tmp_path)])
    assert BV.main() == 0
    assert (tmp_path / "README.md").read_text() == md
    assert json.loads((tmp_path / "blind_verify.json").read_text())["answer"] == J["answer"]


# ---------------------------------------------------------------- the stored bank (skips without it)

def _bank_or_skip():
    bank = ML.resolve_bank()
    missing = [ep for ep in BV.SHIPPED if not (bank / ep / "private" / "answer.json").exists()]
    if missing:
        pytest.skip(f"episode bank absent or incomplete ({bank}; missing {missing}); set SHIFTHUNT_BANK to run "
                    "the blind_verify check on the shipped six")
    return bank


def test_shipped_six_additive_back_end_and_grader_agreement():
    bank = _bank_or_skip()
    for ep in BV.SHIPPED:
        ev = ML.EpisodeEval(ep, bank=bank)
        P = BV.build_probes(ev)
        assert len(P) == 4 and all(p.n == 8 for p in P)
        assert sum(p.hard for p in P) == 1 and sum(p.kind == "null" for p in P) == 1
        assert all(p.truth <= set(p.cands) for p in P)  # every main is an aligned property
        assert all(len(p.gbases) >= 4 for p in P)  # enough bases for R = 4 at B = 64
        assert BV.episode_kind(ev) in ("trap", "two-part")
        res, seen = BV.simulate(ep, P, ["random"] + list(BV.BISECT), (8, 64), 30, "additive", "topic")
        assert res["random"][64]["name"] >= 0.7 > res["random"][8]["name"]
        n, ok = BV.grader_check(ev, P, seen)
        assert n == ok > 4  # set equality is the grader's identified-and-no_extra on every claim set seen


def test_shipped_six_exact_cache_reproduces_the_stored_scan():
    bank = _bank_or_skip()
    priv = ROOT / "results" / "private_1112" / "blind_verify"
    missing = [ep for ep in BV.SHIPPED if not BV.exact_path(priv, ep).exists()]
    if missing:
        pytest.skip(f"no exact group-flip cache for {missing} in {priv} (written by "
                    "`blind_verify.py --gpu-encode`, private and not tracked)")
    for ep in BV.SHIPPED:
        ev = ML.EpisodeEval(ep, bank=bank)
        P = BV.build_probes(ev)
        rows = BV.load_exact(priv, ep, ev, P)
        assert len(rows) == 4 and all(r["usable"] and r["levels_ok"] for r in rows)
        assert max(r["max_abs_units"] for r in rows) <= BV.REPRO_TOL
        for p in P:
            tab = p.tables["exact"]
            fam = BV.family_masks(p.n)
            assert not np.isnan(tab[np.ix_(p.gbases, fam)]).any()
            # single flips on sample-like bases agree with the stored ones on average (same edits, same notes
            # apart from the levels of the other aligned properties)
            ex = np.array([tab[p.gbases, 1 << c].mean() for c in range(p.n)]) / p.unit
            st = np.array([p.single[c, p.gbases].mean() for c in range(p.n)]) / p.unit
            assert np.abs(ex - st).max() < 0.15
