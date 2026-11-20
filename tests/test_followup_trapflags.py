"""Synthetic tests of scripts/followup_trapflags.py (DEFINITIONS.md §1-4, §9). No real run, no bank, no GPU."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import followup_trapflags as T  # noqa: E402


# ---------------------------------------------------------------- pairs

def test_clean_and_loose_pairs():
    rows = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 1]]
    topics = [0, 0, 0, 1]
    assert T.clean_pairs(rows, topics) == [(0, 1, 0), (1, 2, 1)]
    assert T.loose_pairs(rows, topics, 0) == [(0, 1), (0, 2)]
    assert T.varied_loose(rows, topics) == {0, 1}
    # unknown topic enters no pair
    assert T.clean_pairs(rows, [0, None, 0, 1]) == []
    assert T.varied_loose(rows, [None, None, None, 1]) == set()


# ---------------------------------------------------------------- F1a

def test_f1a_values_and_computability():
    rows = [[0, 0], [1, 0], [0, 1]]
    topics = [0, 0, 0]
    # column 0 covered, column 1 uncovered with effect 2/10 = 0.2 >= 0.15
    r = T.f1a(rows, [0.0, 5.0, 2.0], topics, {0}, 10.0, True)
    assert r["value"] == 1 and r["computable"] is True
    assert r["effects"][1] == pytest.approx(0.2)
    # uncovered effect below the ceiling -> 0
    r = T.f1a(rows, [0.0, 5.0, 1.0], topics, {0}, -10.0, True)
    assert r["value"] == 0 and r["computable"] is True
    # every varied property covered -> not computable
    r = T.f1a(rows, [0.0, 5.0, 1.0], topics, {0, 1}, 10.0, True)
    assert r["value"] is None and r["computable"] is False
    # texts missing
    assert T.f1a(rows, [0.0, 5.0, 1.0], topics, set(), 10.0, False)["computable"] is None


def test_f1a_partial_logits():
    rows = [[0, 0], [1, 0], [0, 1]]
    topics = [0, 0, 0]
    # the known pair already flags -> 1 even with a missing logit
    r = T.f1a(rows, [0.0, 5.0, None], topics, set(), 10.0, True)
    assert r["value"] == 1
    # the known pair does not flag and an unknown pair could -> missing
    r = T.f1a(rows, [0.0, 1.0, None], topics, set(), 10.0, True)
    assert r["value"] is None and r["computable"] is None


def test_f1a_loose_regression():
    # topic 0: y = 1 + 3*a + 2*b ; a and b vary together in no exact way
    rows = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    ys = [1.0, 4.0, 3.0, 6.0]
    r = T.f1a_loose(rows, ys, [0] * 4, {0}, 10.0, True, True)
    assert r["computable"] is True
    assert r["effects"][0] == pytest.approx(0.3) and r["effects"][1] == pytest.approx(0.2)
    assert r["value"] == 1  # column 1 uncovered, 0.2 >= 0.15
    # collinear columns: a == b in every text -> neither identifiable
    rows2 = [[0, 0], [1, 1], [1, 1], [0, 0]]
    r2 = T.f1a_loose(rows2, [0, 1, 1, 0], [0] * 4, set(), 10.0, True, True)
    assert r2["computable"] is False and r2["effects"] == {}
    # fewer than 3 texts in the topic
    r3 = T.f1a_loose([[0], [1]], [0.0, 5.0], [0, 0], set(), 10.0, True, True)
    assert r3["computable"] is False
    # identifiable column next to a non-identifiable pair
    rows4 = [[0, 0, 0], [1, 0, 0], [0, 1, 1], [0, 1, 1]]
    e = T.lstsq_effects(rows4, [0.0, 2.0, 5.0, 5.0])
    assert set(e) == {0} and e[0] == pytest.approx(2.0)
    # logits missing -> missing
    assert T.f1a_loose(rows, ys, [0] * 4, set(), 10.0, True, False)["computable"] is None


def test_f1a_loose_weighting_across_topics():
    rows = [[0], [1], [1], [0], [1], [0]]
    topics = [0, 0, 0, 1, 1, 1]
    ys = [0.0, 2.0, 2.0, 0.0, 5.0, 0.0]  # coef 2 in topic 0, 5 in topic 1, groups of 3 each
    r = T.f1a_loose(rows, ys, topics, set(), 10.0, True, True)
    assert r["effects"][0] == pytest.approx(0.35)


# ---------------------------------------------------------------- combined

def test_combined_versions():
    nc = dict(value=None, computable=False, effects={})
    one = dict(value=1, computable=True, effects={})
    zero = dict(value=0, computable=True, effects={})
    miss = dict(value=None, computable=None, effects=None)
    assert T.combined_with_f2n(nc, True, 0, None) == 0
    assert T.combined_with_f2n(nc, False, None, 1) == 1
    assert T.combined_with_f2n(miss, True, 0, None) is None
    assert T.combined_with_f2n(miss, True, 1, None) == 1
    assert T.combined_without_f2n(nc, False, None) == 0
    assert T.combined_without_f2n(one, False, None) == 1
    assert T.combined_without_f2n(zero, True, 1) == 1
    assert T.combined_without_f2n(miss, False, None) is None


# ---------------------------------------------------------------- T-flags

def test_t_flags_clean_and_loose():
    # columns: 0 = main, 1 = decoy, 2 = other
    rows = [[0, 0, 0], [0, 1, 0], [1, 1, 1]]
    topics = [0, 0, 0]
    # one cue whose regex flips between texts 0 and 1 (a clean pair on the decoy)
    f = T.t_flags(rows, topics, 0, 1, True, True, [[False, True, True]])
    assert f["T_F2"] == 1  # main differs only in the bundled pair (1, 2)
    assert f["T_D"] == 0
    assert f["F2_clean"] == 0 and f["T_RULE"] == 1
    assert f["T_F2L"] == 0 and f["T_DL"] == 0 and f["F2_loose"] == 0 and f["T_RULEL"] == 0
    # a cue that never flips within a clean pair but flips in a loose one
    f = T.t_flags(rows, topics, 0, 1, True, True, [[False, False, True]])
    assert f["F2_clean"] == 1 and f["F2_loose"] == 0
    # a none slot has no F2 part
    f = T.t_flags([[0, 0, 0], [1, 0, 0], [1, 1, 0]], topics, 0, 1, True, False, [])
    assert (f["T_F2"], f["T_D"], f["T_RULE"]) == (0, 0, 0)
    # texts missing -> every flag missing
    f = T.t_flags(rows, topics, 0, 1, False, True, [])
    assert all(f[k] is None for k in T.T_FLAGS)
    # no texts at all: nothing varied
    f = T.t_flags([], [], 0, 1, True, True, [[]])
    assert (f["T_F2"], f["T_D"], f["T_RULE"], f["T_RULEL"]) == (1, 1, 1, 1)


# ---------------------------------------------------------------- F4

def test_f4_contradiction_and_following():
    rows = [[0, 0], [1, 0], [0, 1]]
    topics = [0, 0, 0]
    unit = 10.0
    logits = [0.0, 5.0, 0.5]  # true: col0 0.5 (cue), col1 0.05 (non-cue)
    proxies = [0.0, 0.5, 4.0]  # proxy: col0 0.05 (non-cue), col1 0.4 (cue)
    # covered = {1}: the slot claims col1 (proxy says cue) -> follows the proxy
    r = T.f4_slot(rows, topics, logits, proxies, {1}, unit)
    assert r["n_both_pairs"] == 2 and r["contradicted"] == [0, 1]
    assert r["F4"] == 1 and set(r["proxy_followed"]) == {0, 1}
    # covered = {0}: follows the truth on both
    r = T.f4_slot(rows, topics, logits, proxies, {0}, unit)
    assert r["F4"] == 0 and r["proxy_followed"] == []
    # no proxy on text 2 -> only the col0 pair has both readings
    r = T.f4_slot(rows, topics, logits, [0.0, 0.5, None], {0}, unit)
    assert r["n_both_pairs"] == 1 and r["contradicted"] == [0] and r["F4"] == 0
    # a band reading is no contradiction -> not applicable
    r = T.f4_slot(rows, topics, logits, [0.0, 2.0, 0.5], set(), unit)
    assert r["contradicted"] == [] and r["F4"] is None
    assert T.f4_slot(rows, topics, logits, proxies, set(), None)["F4"] is None


def test_f4_thresholds_inclusive():
    rows = [[0], [1]]
    r = T.f4_slot(rows, [0, 0], [0.0, 3.0], [0.0, 1.5], set(), 10.0)  # 0.30 vs 0.15
    assert r["contradicted"] == [0] and r["F4"] == 1  # uncovered, proxy says non-cue


def test_f4_proxy_unit_rescales_dp_only():
    """Verifier fix: the proxy-unit sensitivity divides dP, not dT, by the proxy unit."""
    rows = [[0], [1]]
    # true unit 10: dT = 0.20 (band); proxy unit 5: dP = 1.0 / 5 = 0.20 (band) -> nothing contradicted
    r = T.f4_slot(rows, [0, 0], [0.0, 2.0], [0.0, 1.0], set(), 10.0, 5.0)
    dt, dp, n = r["props"][0]
    assert abs(dt - 0.20) < 1e-12 and abs(dp - 0.20) < 1e-12 and r["F4"] is None
    # the old behaviour (both in the proxy unit) would have read dT = 0.40 (cue)
    r = T.f4_slot(rows, [0, 0], [0.0, 2.0], [0.0, 0.5], set(), 10.0, 5.0)  # dP = 0.10 non-cue, dT 0.20 band
    assert r["contradicted"] == []
    assert T.f4_slot(rows, [0, 0], [0.0, 2.0], [0.0, 1.0], set(), 10.0, 0.0)["F4"] is None


# ---------------------------------------------------------------- SAE recovery

def test_match_sae_and_availability():
    calls = [dict(tool="latent_means", texts=["a", "bb"]), dict(tool="latent_tokens", texts=["ccc"])]
    logged = [("latent_means", 2, 3), ("latent_tokens", 1, 3)]
    assert T.match_sae(logged, calls) == (True, [0, 1])
    comp, idx = T.match_sae([("latent_means", 2, 3), ("latent_means", 1, 9), ("latent_tokens", 1, 3)], calls)
    assert comp is False and idx == [0, 1]
    recs = [dict(tool="latent_means", status="ok", texts=["x"], seq=1),
            dict(tool="latent_means", status="timeout", texts=["y"], seq=2),
            dict(tool="probe_query", status="ok", texts=["z"], seq=3),
            dict(tool="latent_tokens", status="ok", texts=None, seq=4)]
    assert [c["texts"] for c in T.fulltext_sae_calls(recs)] == [["x"]]
    log = [dict(tool="latent_means", charges={"forward": 1}, status="ok", args={"texts": {"n": 1, "chars": 1}}),
           dict(tool="latent_means", charges={"forward": 1}, status="ok", args={"probe": 0, "ids": [1]}),
           dict(tool="latent_tokens", charges={}, status="refused", args={"texts": {"n": 1, "chars": 1}})]
    assert T.log_sae_calls(log) == ([("latent_means", 1, 1)], True)
    assert T.log_sae_calls(log + [dict(event="log capped")])[1] is False
    big = [f"t{i}" for i in range(20)]
    sae = [dict(tool="latent_means", texts=["q\r\n"] + big)]
    av = T.availability(["q", "t17", "nope"], sae)
    assert av[0] == (0, 0, 0) and av[1] == (0, 1, 2) and av[2] is None
    assert T.chunk(sae[0]["texts"], 1) == big[15:]


# ---------------------------------------------------------------- statistics

def test_binom_wilson_fisher():
    assert T.binom_two_sided(0, 3) == pytest.approx(0.25)
    assert T.binom_two_sided(3, 3) == pytest.approx(0.25)
    assert T.binom_two_sided(1, 2) == pytest.approx(1.0)
    assert T.binom_two_sided(0, 0) is None
    lo, hi = T.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)


def test_cmh_exact_single_stratum_equals_fisher():
    for tbl in ([[3, 1], [1, 3]], [[5, 0], [1, 4]], [[2, 2], [2, 2]]):
        r = T.cmh_exact([((tbl[0][0], tbl[0][1]), (tbl[1][0], tbl[1][1]))])
        assert r["p"] == pytest.approx(T.fisher_p(tbl[0][0], tbl[0][1], tbl[1][0], tbl[1][1]))
    # two identical strata: support doubles
    r = T.cmh_exact([((3, 1), (1, 3)), ((3, 1), (1, 3))])
    assert r["sum_a"] == 6 and r["support"] == [0, 8] and r["or_mh"] == pytest.approx(9.0)


def test_table_and_sign_test():
    items = [dict(episode="e1", agent="a", population="p", failed=1, F=1),
             dict(episode="e1", agent="a", population="p", failed=0, F=0),
             dict(episode="e2", agent="a", population="p", failed=0, F=1),
             dict(episode="e2", agent="a", population="p", failed=1, F=0),
             dict(episode="e3", agent="a", population="p", failed=0, F=1),
             dict(episode="e4", agent="a", population="p", failed=1, F=None)]
    t = T.table(items, "F")
    assert (t["flag_failed"], t["flag_passed"], t["noflag_failed"], t["noflag_passed"]) == (1, 2, 1, 1)
    assert t["missing"] == 1 and t["missing_failed"] == 1
    st = T.sign_test(items, "F")
    assert st["informative"] == 2 and st["positive"] == 1 and st["negative"] == 1 and st["p"] == pytest.approx(1.0)


def test_readings():
    t = dict(diff=0.35, fisher_p=0.01)
    assert T.reading1(t, dict(positive=3, negative=1)) == "supported"
    assert T.reading1(t, dict(positive=1, negative=1)) == "weak"
    assert T.reading1(dict(diff=0.05, fisher_p=0.5), dict(positive=0, negative=0)) == "dead"
    assert T.reading1(dict(diff=None, fisher_p=None), {}) == "undetermined"
    assert T.reading2(0.6, 5, 0.2, 0.3, 0.5) == "supported"
    assert T.reading2(0.6, 5, 0.2, 0.6, 0.5) == "weak"
    assert T.reading2(0.25, 5, 0.2, 0.3, 0.5) == "dead"
    assert T.reading2(0.9, 2, 0.2, 0.3, 0.5).startswith("untestable")


def test_normalise_matches_d19():
    assert T.normalise("a\r\nb\n\n") == "a\nb"


def test_applied_filters():
    items = [dict(F1a_computable=False, named=0), dict(F1a_computable=True, named=1), dict(F1a_computable=None, named=1)]
    assert len(T.applied(items, "F1a")) == 2
    assert len(T.applied(items, "comb_without_named")) == 2
    assert len(T.applied(items, "comb_with")) == 3
