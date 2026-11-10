"""scripts/blackbox_analysis.py (tests, intervals, rules, the S3 join, the ledger and the first-attempt
sensitivity analysis, the pipeline on simulated rows) and scripts/blackbox_runorder.py (the seeded run order).
No raw data, no network: every row here is synthetic; the main-study constants of the drift check are
recomputed from the tracked results/cross_model_1103/rollouts.csv."""
import csv
import importlib.util
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import blackbox_analysis as BA  # noqa: E402
import blackbox_runorder as RO  # noqa: E402

ITEMS = list(BA.ITEMS)


def arr(*v):
    return np.array(v, dtype=float)


def cells_of(pairs):
    return OrderedDict((f"i{j}", (arr(*a), arr(*b))) for j, (a, b) in enumerate(pairs))


def row(agent, arm, item, name, **kw):
    r = {"run": f"r{kw.pop('i', 0)}", "batch": "t", "agent": agent, "arm": arm, "episode": item, "counted": 1,
         "name": name, "identified": name, "no_extra": name, "nulls_ok": 1, "n_null": 1, "n_null_false": 0,
         "s1_named": 2, "s1_n": 2, "plain_pass": 2, "s5_full": name, "episode_pass": name, "submitted": 1,
         "timeout": 0, "n_latent_fail": 0, "status": "submitted", "hard_bucket": None if name else "planted_none",
         "naming_bucket": None if name else "planted_none", "kind": BA.KIND[item] if item in BA.KIND else "other"}
    r.update(kw)
    return r


def grid(agent, arm, names_by_item):
    """names_by_item: one sequence of 0/1 per item, in ITEMS order."""
    return [row(agent, arm, it, v) for it, vals in zip(ITEMS, names_by_item) for v in vals]


# ---------------------------------------------------------------------------------------------------------
# statistic, permutation test

def test_statistic_by_hand():
    c = cells_of([((1, 1, 0, 1), (0, 0, 1, 0)), ((1, 1, 1, 1), (1, 0, 0, 0))])
    assert BA.statistic(c) == pytest.approx(((0.75 - 0.25) + (1.0 - 0.25)) / 2)
    assert BA.statistic(c) == pytest.approx(7 / 8 - 2 / 8)  # balanced: the difference of pooled rates
    u = cells_of([((1,), (0, 0, 0)), ((1, 1, 0, 0), (1, 0))])  # unbalanced: mean of item differences, not pooled
    assert BA.statistic(u) == pytest.approx(((1 - 0) + (0.5 - 0.5)) / 2)
    assert BA.statistic(u) != pytest.approx(3 / 5 - 1 / 5)
    assert BA.statistic(OrderedDict()) is None


def test_permuted_labels_keep_the_item_arm_counts():
    rng = np.random.default_rng(0)
    for n_a, n_b in ((4, 4), (2, 6), (1, 3), (3, 0)):
        lab = BA.permuted_labels(n_a, n_b, 5000, rng)
        assert lab.shape == (5000, n_a + n_b) and lab.dtype == bool
        assert (lab.sum(1) == n_a).all()
    lab = BA.permuted_labels(2, 2, 12000, np.random.default_rng(1))  # uniform over the 6 arrangements
    counts = Counter(map(tuple, lab.tolist()))
    assert len(counts) == 6 and min(counts.values()) > 1800 and max(counts.values()) < 2200


def test_permutation_p_is_reproducible_and_order_free():
    c = cells_of([((1, 1, 0, 1), (0, 0, 1, 0)), ((1, 1, 1, 0), (1, 0, 0, 0)), ((1, 0, 1, 1), (1, 1, 0, 0))])
    a, b = BA.permutation_test(c), BA.permutation_test(c)
    assert a == b and a["seed"] == BA.SEED == 20261112 and a["n_resamples"] == 10_000
    assert a["p"] == (1 + a["n_extreme"]) / 10_001
    assert BA.permutation_test(c, seed=1)["n_extreme"] != a["n_extreme"] or BA.permutation_test(c, seed=2)["n_extreme"] != a["n_extreme"]
    # through rows: the order of the rows does not change any number
    rows = (grid("gpt", "open8", [(1, 1, 0, 1), (1, 1, 1, 0), (1, 0, 1, 1), (1, 1, 1, 1), (0, 1, 1, 1), (1, 1, 0, 0)])
            + grid("gpt", "bb8", [(0, 0, 1, 0), (1, 0, 0, 0), (1, 1, 0, 0), (0, 0, 0, 0), (0, 1, 0, 1), (1, 0, 0, 0)]))
    shuffled = [rows[j] for j in np.random.default_rng(3).permutation(len(rows))]
    assert BA.contrast(rows, "open8", "bb8") == BA.contrast(shuffled, "open8", "bb8")


def test_permutation_p_matches_the_exact_value_on_a_tiny_case():
    one = BA.permutation_test(cells_of([((1, 1), (0, 0))]))  # 6 arrangements, 2 of them with |T*| = 1
    assert one["T"] == 1.0 and one["p"] == pytest.approx(1 / 3, abs=0.02)
    two = BA.permutation_test(cells_of([((1, 1), (0, 0)), ((1, 1), (0, 0))]))  # both items at +1 or both at -1: 2 of 36
    assert two["p"] == pytest.approx(2 / 36, abs=0.008)
    flat = BA.permutation_test(cells_of([((1, 1), (1, 1)), ((0, 0), (0, 0))]))  # nothing to permute
    assert flat["T"] == 0.0 and flat["p"] == 1.0
    assert BA.permutation_test(OrderedDict())["p"] is None


def test_planted_effect_gives_small_p_and_null_gives_valid_p():
    big = cells_of([((1, 1, 1, 1), (0, 0, 0, 0))] * 6)
    assert BA.permutation_test(big)["p"] == pytest.approx(1 / 10_001)  # no resample reaches T = 1
    rng = np.random.default_rng(7)
    ps = []
    for s in range(300):  # null: both arms share each item's rate
        pr = BA.expit(0.3 + rng.normal(0, 1, 6))
        c = OrderedDict((i, ((rng.random(4) < pr[i]).astype(float), (rng.random(4) < pr[i]).astype(float))) for i in range(6))
        ps.append(BA.permutation_test(c, 500, s)["p"])
    ps = np.array(ps)
    # roughly uniform, on the conservative side (ties count as extreme, and T = 0 gives p = 1)
    assert (ps <= 0.05).mean() <= 0.08 and (ps <= 0.10).mean() <= 0.14
    assert 0.15 <= (ps <= 0.5).mean() <= 0.60 and (ps <= 0.25).mean() >= 0.05


# ---------------------------------------------------------------------------------------------------------
# bootstrap interval

def test_bootstrap_ci_reproducible_and_brackets_t():
    c = cells_of([((1, 1, 0, 1), (0, 0, 1, 0)), ((1, 1, 1, 0), (1, 0, 0, 0)), ((1, 0, 1, 1), (1, 1, 0, 0)),
                  ((1, 1, 1, 1), (0, 0, 0, 1))])
    lo, hi = BA.bootstrap_ci(c)
    assert (lo, hi) == BA.bootstrap_ci(c) and lo < BA.statistic(c) < hi and -1 <= lo and hi <= 1
    draws = BA._cluster_bootstrap(list(c.values()), 4000, BA.SEED)
    assert not np.array_equal(draws, BA._cluster_bootstrap(list(c.values()), 4000, 5))  # the seed matters
    assert draws.mean() == pytest.approx(BA.statistic(c), abs=0.02)
    assert BA.bootstrap_ci(OrderedDict()) == (None, None)
    assert BA.bootstrap_ci(cells_of([((1, 1), (0, 0))] * 3)) == (1.0, 1.0)  # no variation anywhere
    rate = BA.bootstrap_ci(OrderedDict(a=arr(1, 1, 0, 0), b=arr(1, 0, 0, 0), c=arr(1, 1, 1, 0)))  # one arm: a rate
    assert 0 <= rate[0] < 0.5 < rate[1] <= 1


def test_bootstrap_ci_covers_the_true_difference_in_most_simulations():
    rng = np.random.default_rng(11)
    pa, pb = np.array([0.9, 0.8, 0.85, 0.7, 0.9, 0.8]), np.array([0.5, 0.3, 0.45, 0.3, 0.6, 0.4])
    true, hit = float((pa - pb).mean()), 0
    for s in range(150):
        c = OrderedDict((i, ((rng.random(4) < pa[i]).astype(float), (rng.random(4) < pb[i]).astype(float))) for i in range(6))
        lo, hi = BA.bootstrap_ci(c, 800, s)
        hit += lo - 1e-9 <= true <= hi + 1e-9
    assert hit / 150 >= 0.85


# ---------------------------------------------------------------------------------------------------------
# Holm, the R3 rule, the Open-64 trigger

def test_holm_by_hand():
    assert BA.holm({"C1": 0.01, "C2": 0.04}) == {"C1": 0.02, "C2": 0.04}
    assert BA.holm({"C1": 0.04, "C2": 0.03}) == {"C2": 0.06, "C1": 0.06}  # monotone: the larger p cannot be smaller
    got = BA.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert got == pytest.approx({"a": 0.03, "c": 0.06, "b": 0.06})
    assert BA.holm({"a": 0.6, "b": 0.9}) == {"a": 1.0, "b": 1.0}
    assert BA.holm({"C1": 0.02}, m=2) == {"C1": 0.04}  # one test of a pre-registered family of two
    assert BA.holm({}) == {}


@pytest.mark.parametrize("lo,hi,want", [
    (-0.10, 0.15, "eliminated"),
    (-0.35, -0.05, "not eliminated"),
    (-0.15, -0.02, "eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)"),
    (-0.30, 0.10, "inconclusive"),
    (-0.20, 0.10, "inconclusive"),      # a lower bound exactly at the margin is not above it
    (-0.20, -0.05, "not eliminated"),
    (-0.10, 0.0, "eliminated"),         # an upper bound exactly 0 is not below 0
    (-0.25, 0.0, "inconclusive"),
    (0.05, 0.30, "eliminated"),
    (None, None, "not evaluable (no data)"),
])
def test_r3_rule(lo, hi, want):
    assert BA.r3_decision(lo, hi) == want


@pytest.mark.parametrize("bb64,open8,want", [
    (0.60, 0.80, True),          # exactly 0.20 below: triggers
    (3 / 5, 4 / 5, True),
    (15 / 24, 21 / 24, True),
    (0.675, 0.875, True),
    (0.61, 0.80, False),
    (17 / 24, 21 / 24, False),   # 0.167 below
    (0.80, 0.80, False),
    (0.95, 0.75, False),
    (0.0, 0.2, True),
    (None, 0.8, None),
])
def test_open64_trigger_edges(bb64, open8, want):
    assert BA.open64_trigger(bb64, open8) is want


def test_r3_rule_branches_and_tolerance():
    """The four branches on [L, U], exactly: L > -0.20 and U >= 0; L <= -0.20 and U < 0; L > -0.20 and U < 0;
    else. A bound within 1e-9 of a threshold is not past it."""
    both = "eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)"
    assert BA.R3_BOTH == both and BA.R3_MARGIN == -0.20 and BA.TOL == 1e-9
    assert BA.R3_BRANCH == {"eliminated": 1, "not eliminated": 2, both: 3, "inconclusive": 4}
    grid = [-0.5, -0.2 - 1e-6, -0.2, -0.2 + 1e-10, -0.2 + 1e-6, -0.1, -1e-6, -1e-10, 0.0, 1e-6, 0.3]
    seen = set()
    for lo in grid:
        for hi in grid:
            if hi < lo:
                continue
            above, below = lo > -0.20 + 1e-9, hi < -1e-9
            want = ("eliminated" if above and not below else "not eliminated" if not above and below
                    else both if above and below else "inconclusive")
            assert BA.r3_decision(lo, hi) == want, (lo, hi)
            seen.add(want)
    assert seen == set(BA.R3_BRANCH)
    assert BA.r3_decision(-0.2 + 1e-10, 0.1) == "inconclusive" and BA.r3_decision(-0.2 + 1e-6, 0.1) == "eliminated"
    assert BA.r3_decision(-0.3, -1e-10) == "inconclusive" and BA.r3_decision(-0.3, -1e-6) == "not eliminated"
    assert BA.r3_decision(-0.1, -1e-10) == "eliminated" and BA.r3_decision(-0.1, -1e-6) == both


@pytest.mark.parametrize("sig,decision,holds,words", [
    (True, "eliminated", True, ["holds: C1 is significant", "first branch", "testing capacity"]),
    (True, BA.R3_BOTH, True, ["holds, with a residual deficit", "both-true branch", "residual deficit remains",
                              "CI of C4 excludes 0"]),
    (True, "not eliminated", False, ['does not hold: the R3 verdict is "not eliminated"']),
    (True, "inconclusive", False, ['does not hold: the R3 verdict is "inconclusive"']),
    (False, "eliminated", False, ["does not hold: C1 is not significant"]),
    (False, BA.R3_BOTH, False, ["does not hold: C1 is not significant"]),
    (False, "inconclusive", False, ['does not hold: C1 is not significant and the R3 verdict is "inconclusive"']),
    (None, "eliminated", None, ["not evaluable"]),
    (True, "not evaluable (no data)", None, ["not evaluable"]),
])
def test_testing_capacity_statement(sig, decision, holds, words):
    tests = {} if sig is None else {"C1": {"significant": sig, "p_holm": 0.01 if sig else 0.4}}
    r3 = {"decision": decision, "branch": BA.R3_BRANCH.get(decision)}
    tc = BA.testing_capacity(tests, r3)
    assert tc["holds"] is holds and tc["r3_branch"] == BA.R3_BRANCH.get(decision)
    assert all(w in tc["statement"] for w in words), tc["statement"]
    assert ("residual deficit" in tc["statement"]) == (holds is True and decision == BA.R3_BOTH)


# ---------------------------------------------------------------------------------------------------------
# unbalanced and missing cells

def test_missing_cell_is_dropped_and_reported():
    rows = (grid("gpt", "open8", [(1, 1, 1, 1)] * 6)
            + grid("gpt", "bb8", [(0, 0, 0, 0), (1, 0, 0, 0), (), (0, 0), (1, 1, 1, 1), (0, 0, 0, 0)]))
    t = BA.contrast(rows, "open8", "bb8", n=2000)
    assert t["items_dropped"] == [ITEMS[2]] and t["items_used"] == [i for i in ITEMS if i != ITEMS[2]]
    assert t["balanced"] is False and t["ci_label"] == "approximate (5 clusters)"
    assert t["T"] == pytest.approx((1 + 0.75 + 1 + 0 + 1) / 5)
    assert t["rate_a"] == {"k": 20, "n": 20, "rate": 1.0, "wilson95": t["rate_a"]["wilson95"]}  # used items only
    assert (t["rate_b"]["k"], t["rate_b"]["n"]) == (5, 18) and t["pooled_diff"] != pytest.approx(t["T"])
    assert 0 < t["p"] < 0.01 and t["ci95"][0] <= t["T"] <= t["ci95"][1]
    res = BA.analyse(rows, n=500)
    assert "gpt bb8 ep415: 0 runs (planned 4)" in res["input"]["design_deviations"]
    assert "gpt bb8 ep472: 2 runs (planned 4)" in res["input"]["design_deviations"]
    assert "Unbalanced cells in C1" in BA.render_md(res)
    assert set(res["confirmatory"]["contrasts"]) == {"C1"} and res["confirmatory"]["contrasts"]["C1"]["p_holm"] == pytest.approx(
        min(1.0, 2 * res["confirmatory"]["contrasts"]["C1"]["p"]))  # still a family of two
    assert res["r3"]["decision"] == "not evaluable (no data)" and res["open64_trigger"]["triggered"] is None
    assert res["testing_capacity"]["holds"] is None
    empty = BA.contrast(grid("gpt", "open8", [(1,)] * 6), "open8", "bb8", n=100)
    assert empty["T"] is None and empty["p"] is None and empty["ci95"] is None and empty["items_dropped"] == ITEMS


def test_missing_cells_nothing_imputed_pooled_rates_for_trigger_and_predictions():
    """An item with no counted run in one arm of a contrast is dropped from that contrast only and named; T is
    the mean of within-item differences on the runs present; the rates, the trigger and the predictions check
    use pooled k/n over the counted runs."""
    open8 = [(1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 1, 1), (1, 1, 1, 0), (1, 1), (1, 1, 1, 1)]             # 20/22
    bb8 = [(1, 0, 0, 0), (0, 0, 0, 0), (), (1, 0), (1, 1, 0, 0), (0, 0, 0, 0)]                           # 4/18, no ep415
    bb64 = [(1, 1, 1, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1,), (1, 0, 0, 0), (1, 1, 1, 0)]                  # 11/21
    rows = grid("gpt", "open8", open8) + grid("gpt", "bb8", bb8) + grid("gpt", "bb64", bb64)
    res = BA.analyse(rows, n=300)
    c = res["confirmatory"]["contrasts"]
    assert c["C1"]["items_dropped"] == ["ep415"] and c["C2"]["items_dropped"] == ["ep415"] and c["C4"]["items_dropped"] == []
    assert c["C1"]["T"] == pytest.approx(((1 - .25) + (.75 - 0) + (.75 - .5) + (1 - .5) + (1 - 0)) / 5)
    assert c["C4"]["T"] == pytest.approx(((.75 - 1) + (.25 - .75) + (.5 - 1) + (1 - .75) + (.25 - 1) + (.75 - 1)) / 6)
    # the A and B columns of a contrast pool the items it uses; the arm's own rate pools every counted run
    assert (c["C1"]["rate_a"]["k"], c["C1"]["rate_a"]["n"]) == (16, 18) and (c["C1"]["rate_b"]["k"], c["C1"]["rate_b"]["n"]) == (4, 18)
    rates = {arm: (r["k"], r["n"]) for arm, r in res["rates"]["gpt"].items()}
    assert rates == {"open8": (20, 22), "bb8": (4, 18), "bb64": (11, 21)}
    assert res["rates"]["gpt"]["bb8"]["by_item"]["ep415"] == {"k": 0, "n": 0}  # an empty cell stays empty
    # trigger: pooled 11/21 against 20/22 - 0.20 (not the means of item rates, 0.583 and 0.917)
    tr = res["open64_trigger"]
    assert (tr["rate_gpt_bb64"], tr["rate_gpt_open8"]) == (11 / 21, 20 / 22) and tr["triggered"] is True
    assert tr["threshold"] == pytest.approx(20 / 22 - 0.20)
    pred = {(p["agent"], p["arm"], p["kind"]): (p["k"], p["n"], p["observed"]) for p in res["predictions"]["ranges"]}
    assert pred[("gpt", "open8", "all")] == (20, 22, 20 / 22) and pred[("gpt", "bb8", "all")] == (4, 18, 4 / 18)
    assert pred[("gpt", "bb64", "trap")] == (6, 12, 0.5) and pred[("gpt", "bb64", "twopart")] == (5, 9, 5 / 9)
    md = BA.render_md(res)
    assert BA.MISSING_NOTE in md and "Missing runs: nothing is imputed." in md
    assert "is dropped from that contrast and named under its table" in md and "pooled rates (k/n over the counted runs" in md
    assert "Items dropped from a contrast (no counted run in one of its two arms): C1: ep415; C2: ep415." in md
    assert "Items dropped from a contrast (no counted run in one of its two arms): trap, C1: ep415; trap, C2: ep415." in md
    assert "| 5 (dropped: ep415) |" in md
    assert "Items dropped" not in BA.render_md(BA.analyse(hand_study(), n=200))  # nothing to name when nothing is dropped


def test_study_rows_filter():
    rows = [row("gpt", "open8", "ep411", 1), row("gpt", "open8", "ep411", 1, counted=0),
            row("opus", "open8", "ep411", 1), row("gpt", "other", "ep411", 1), row("gpt", "open8", "ep481", 1),
            row("haiku", "bb64", "ep476", 0), row("gpt", "bb8", "ep413", 1, batch="r1112_pilots")]
    used, out = BA.study_rows(rows, exclude_batches=("r1112_pilots",))
    assert [(r["agent"], r["arm"], r["episode"]) for r in used] == [("gpt", "open8", "ep411"), ("haiku", "bb64", "ep476")]
    assert out == {"excluded batch": 1, "not counted (infrastructure failure)": 1, "other agent": 1, "other arm": 1,
                   "other episode": 1}


# ---------------------------------------------------------------------------------------------------------
# the whole pipeline

def hand_study():
    """A balanced data set with known rates: GPT open8 20/24, bb8 8/24, bb64 16/24; Haiku 6/12, 3/12, 6/12."""
    return (grid("gpt", "open8", [(1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 0, 0), (1, 1, 1, 1)])
            + grid("gpt", "bb8", [(1, 1, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0)])
            + grid("gpt", "bb64", [(1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 1, 0), (1, 1, 0, 0), (1, 0, 0, 0), (1, 1, 1, 0)])
            + grid("haiku", "open8", [(1, 0), (0, 0), (1, 0), (1, 1), (1, 0), (1, 0)])
            + grid("haiku", "bb8", [(1, 0), (0, 0), (1, 0), (0, 0), (0, 0), (1, 0)])
            + grid("haiku", "bb64", [(1, 1), (1, 0), (1, 0), (0, 0), (1, 0), (1, 0)]))


def test_pipeline_numbers_on_a_hand_study():
    res = BA.analyse(hand_study(), n=2000)
    rates = {a: {arm: (r["k"], r["n"]) for arm, r in v.items()} for a, v in res["rates"].items()}
    assert rates == {"gpt": {"open8": (20, 24), "bb8": (8, 24), "bb64": (16, 24)},
                     "haiku": {"open8": (6, 12), "bb8": (3, 12), "bb64": (6, 12)}}
    c = res["confirmatory"]["contrasts"]
    assert list(c) == ["C1", "C2", "C4"]  # no Open-64 run, so no C3
    assert c["C1"]["T"] == pytest.approx(0.5) and c["C2"]["T"] == pytest.approx(1 / 3) and c["C4"]["T"] == pytest.approx(-1 / 6)
    assert all(t["balanced"] and t["T"] == pytest.approx(t["pooled_diff"]) for t in c.values())
    assert {k: t["p_holm"] for k, t in c.items()} == {**BA.holm({"C1": c["C1"]["p"], "C2": c["C2"]["p"]}), "C4": None}
    assert c["C1"]["family"] == "holm" and c["C4"]["family"] == "outside the family"
    assert res["r3"]["ci95"] == c["C4"]["ci95"] and res["r3"]["decision"] == BA.r3_decision(*c["C4"]["ci95"])
    assert res["open64_trigger"] == {"rate_gpt_bb64": 16 / 24, "rate_gpt_open8": 20 / 24, "gap": 0.2,
                                     "threshold": 20 / 24 - 0.2, "triggered": False}
    k = res["by_kind"]["gpt"]
    assert set(k) == {"trap", "twopart"} and set(k["trap"]) == {"C1", "C2", "C4"}
    assert k["trap"]["C1"]["items_used"] == ITEMS[:3] and k["twopart"]["C1"]["items_used"] == ITEMS[3:]
    assert k["trap"]["C1"]["T"] == pytest.approx(11 / 12 - 5 / 12) and k["twopart"]["C1"]["T"] == pytest.approx(9 / 12 - 3 / 12)
    assert k["trap"]["C1"]["ci_label"] == "approximate (3 clusters)"
    pred = {(p["agent"], p["arm"], p["kind"]): p["holds"] for p in res["predictions"]["ranges"]}
    assert pred == {("gpt", "open8", "all"): True, ("gpt", "bb8", "all"): True, ("gpt", "bb64", "trap"): True,
                    ("gpt", "bb64", "twopart"): True, ("haiku", "open8", "all"): True, ("haiku", "bb8", "all"): True,
                    ("haiku", "bb64", "all"): True}
    orders = {p["prediction"]: p["holds"] for p in res["predictions"]["orders"]}
    assert orders == {"gpt bb8: trap rate above two-part rate": True,       # 5/12 vs 3/12
                      "gpt bb8: trap rate >= open8 trap rate": False,      # 5/12 vs 11/12
                      "gpt bb64: trap rate >= open8 trap rate": False,     # 10/12 vs 11/12
                      "haiku bb8: trap rate >= open8 trap rate": True,     # 2/6 vs 2/6
                      "haiku bb64: trap rate >= open8 trap rate": True}    # 4/6 vs 2/6
    assert res["drift"]["gpt"]["fresh"]["k"] == 20 and res["drift"]["gpt"]["main_study"] == {
        "k": 14, "n": 16, "rate": 14 / 16, "wilson95": list(BA.wilson(14, 16))}
    assert "fisher_p" not in res["drift"]["haiku"] and "fisher_p" not in res["drift"]["gpt"]
    assert c["C1"]["significant"] is (c["C1"]["p_holm"] < 0.05) and c["C2"]["significant"] is (c["C2"]["p_holm"] < 0.05)
    assert c["C4"]["significant"] is None and res["first_attempt"] is None and res["submit_refusals"] is None
    d = res["decomposition"]
    assert list(d) == ["gpt|open8", "gpt|bb8", "gpt|bb64", "haiku|open8", "haiku|bb8", "haiku|bb64"]
    assert (d["gpt|bb8"]["n"], d["gpt|bb8"]["name"], d["gpt|bb8"]["naming_buckets"]) == (24, 8, {"planted_none": 16})
    assert res["s3"] is None and "no `s3` column" in BA.render_md(res)
    assert set(res["haiku_contrasts"]) == {"C1", "C2", "C4"} and res["rates"]["haiku"]["bb8"]["wilson95"] == list(BA.wilson(3, 12))
    assert res["rates"]["haiku"]["bb8"]["cluster_label"] == "approximate (6 clusters)"


def test_s3_table_and_costs():
    rows = [row("gpt", "bb8", "ep411", n, s3=s, pq_hard=h, pq_used=8, usd=u, wall_min=10.0)
            for n, s, h, u in ((1, 1, 4, 0.5), (1, 1, 2, 0.7), (0, 1, 3, 0.6), (1, 0, 0, None), (0, 0, 1, 0.2), (0, 0, 0, 1.0))]
    rows.append(row("gpt", "bb8", "ep411", 0, s3=None))
    res = BA.analyse(rows, n=200)
    t = res["s3"]["gpt|bb8"]
    assert (t["s3_1_name_1"], t["s3_1_name_0"], t["s3_0_name_1"], t["s3_0_name_0"], t["n"], t["no_s3"]) == (2, 1, 1, 2, 6, 1)
    assert t["name_given_s3_1"]["k"] == 2 and t["name_given_s3_1"]["n"] == 3 and t["name_given_s3_1"]["rate"] == pytest.approx(2 / 3)
    s4 = res["s4"]["gpt|bb8"]
    assert s4["pq_hard"] == {"mean": pytest.approx(10 / 6), "n": 6} and s4["usd"]["n"] == 5
    assert s4["usd"]["mean"] == pytest.approx(0.6) and s4["usd_total"] == pytest.approx(3.0)
    assert s4["tokens_in"] == {"mean": None, "n": 0}
    md = BA.render_md(res)
    assert "| gpt | BB-8 | 2 | 1 | 1 | 2 | 2/3 = 0.67" in md


def test_pipeline_on_simulated_data_with_an_empty_open64_arm():
    rows = BA.simulate_rows(seed=5)
    assert len(rows) == 108 and Counter((r["agent"], r["arm"]) for r in rows) == {
        ("gpt", "open8"): 24, ("gpt", "bb8"): 24, ("gpt", "bb64"): 24,
        ("haiku", "open8"): 12, ("haiku", "bb8"): 12, ("haiku", "bb64"): 12}
    assert all(BA.SN.arm_of(r["episode_id"], r["access"], r["pq_limit"]) == r["arm"] for r in rows)
    res = BA.analyse(rows, n=400)
    assert "C3" not in res["confirmatory"]["contrasts"] and "open64" not in res["rates"]["gpt"]
    assert res["input"]["design_deviations"] == [] and res["input"]["rows_used"] == 108
    md = BA.render_md(res, "dry run")
    assert "| C3 (outside the family) | Open-64 − BB-64 | not run |" in md and "## S3 × NAME (descriptive)" in md
    assert md == BA.render_md(BA.analyse(BA.simulate_rows(seed=5), n=400), "dry run")  # deterministic
    assert BA.dumps(res) == BA.dumps(BA.analyse(rows, n=400))
    back = json.loads(BA.dumps(res))
    assert back["confirmatory"]["contrasts"]["C1"]["p"] == res["confirmatory"]["contrasts"]["C1"]["p"]
    assert back["r3"]["decision"] in ("eliminated", "not eliminated", "inconclusive",
                                      "eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)")


def test_pipeline_with_open64_and_the_command_line(tmp_path, capsys):
    rows = BA.simulate_rows(seed=6, open64=True)
    assert len(rows) == 132
    res = BA.analyse(rows, n=300)
    c3 = res["confirmatory"]["contrasts"]["C3"]
    assert (c3["a"], c3["b"], c3["family"], c3["p_holm"]) == ("open64", "bb64", "outside the family", None)
    assert res["rates"]["gpt"]["open64"]["n"] == 24 and "open64" not in res["rates"]["haiku"]
    src = tmp_path / "rows.csv"
    with open(src, "w", newline="") as fh:  # the scorer's CSV plus an s3 column
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows([{k: "" if v is None else v for k, v in r.items()} for r in rows])
    out_md, out_json = tmp_path / "out" / "report.md", tmp_path / "out" / "report.json"
    assert BA.main([str(src), "--any-batch", "--resamples", "300", "--out-md", str(out_md), "--out-json", str(out_json)]) == 0
    with pytest.raises(SystemExit, match="none of the 132 rows"):  # simulated rows are in no batch of the study
        BA.main([str(src), "--resamples", "300", "--out-md", str(out_md)])
    assert json.loads(out_json.read_text())["confirmatory"]["contrasts"] == json.loads(BA.dumps(res))["confirmatory"]["contrasts"]
    assert out_md.read_text() == BA.render_md(res)
    assert BA.main(["--simulate", "--resamples", "200"]) == 0
    assert capsys.readouterr().out.startswith("# DRY RUN ON SIMULATED DATA (not results)")
    with pytest.raises(SystemExit):
        BA.main([])


def test_generating_model_and_power():
    for rate in (0.2, 0.5, 0.85):
        assert BA.calibrated_intercept(rate, 0.0) == pytest.approx(np.log(rate / (1 - rate)))
        c = BA.calibrated_intercept(rate, 1.0)
        u = np.random.default_rng(0).normal(0, 1.0, 400_000)
        assert BA.expit(c + u).mean() == pytest.approx(rate, abs=0.004)  # the nominal rate is the average over items
    big = BA.simulate_power(0.9, 0.1, 0.0, n_sims=30, n_perm=200, seed=1)
    assert big["power_05"] == 1.0 and big["n_per_arm"] == 24 and big["gap"] == 0.8
    null = BA.simulate_power(0.6, 0.6, 1.0, n_sims=120, n_perm=300, seed=2)
    assert null["power_05"] <= 0.10 and abs(null["mean_T"]) < 0.06
    assert BA.simulate_power(0.85, 0.5, 1.0, n_sims=20, n_perm=100, seed=3) == BA.simulate_power(0.85, 0.5, 1.0, n_sims=20,
                                                                                               n_perm=100, seed=3)
    table = [BA.simulate_power(0.85, 0.50, 0.0, n_sims=20, n_perm=100, seed=4)]
    assert "| 0.35 | 0.85 | 0.50 | 0.0 |" in BA.render_power(table)


# ---------------------------------------------------------------------------------------------------------
# which rows are the study's: batch names, cells above the plan

def in_batches(rows, tag="r1112"):
    return [dict(r, batch=f"{tag}_{r['agent']}_{r['arm']}") for r in rows]


def write_rows(path, rows):
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{k: "" if r.get(k) is None else r[k] for k in cols} for r in rows])


def test_study_tag_keeps_only_the_study_batches():
    study = in_batches(hand_study())
    others = ([dict(r, batch="r1112_pilot_gpt_open8") for r in grid("gpt", "open8", [(0,)] * 6)]     # pilots
              + [dict(r, batch="r1103_gpt_b1") for r in grid("gpt", "open8", [(0, 0)] * 6)]         # the main study
              + [dict(r, batch="r1103_smoke_gpt") for r in grid("gpt", "open8", [(0,)] * 6)]        # smoke runs
              + [dict(r, batch="r1103_haiku_hv") for r in grid("haiku", "open8", [(0,)] * 6)]       # hv side batch
              + [dict(r, batch="r1111_gpt_bb8") for r in grid("gpt", "bb8", [(1,)] * 6)])           # another tag
    used, out = BA.study_rows(study + others, study_tag="r1112")
    assert len(used) == 108 and {r["batch"] for r in used} == {f"r1112_{a}_{arm}" for a in ("gpt", "haiku")
                                                               for arm in ("open8", "bb8", "bb64")}
    assert out == {"batch outside the study (not r1112_<agent>_<arm>)": 36}
    res, clean = BA.analyse(study + others, n=300, study_tag="r1112"), BA.analyse(study, n=300, study_tag="r1112")
    assert res["rates"] == clean["rates"] and res["confirmatory"] == clean["confirmatory"]
    assert res["rates"]["gpt"]["open8"]["k"] == 20 and res["input"]["overfull_cells"] == []
    assert res["input"]["study_tag"] == "r1112" and "rule: named r1112_<agent>_<arm>" in BA.render_md(res)
    pooled = BA.analyse(study + others, n=300)  # without the rule the other batches are pooled in: flagged
    assert pooled["rates"]["gpt"]["open8"]["n"] == 24 + 24 and len(pooled["input"]["overfull_cells"]) == 6 + 6 + 6
    assert "gpt open8 ep411: 8 runs (planned 4)" in pooled["input"]["overfull_cells"]
    assert "**ERROR: 18 cell(s) have more counted runs than planned" in BA.render_md(pooled)
    assert BA.SN.study_batch("r1112_gpt_open64", "r1112") == ("gpt", "open64")
    assert all(BA.SN.study_batch(b, "r1112") is None for b in ("r1112_pilot_gpt_bb8", "r1112_opus_bb8", "r1112_gpt_bb16",
                                                               "r1103_gpt_b1", "xr1112_gpt_bb8", "r1112_gpt_bb8_x", "", None))
    with pytest.raises(ValueError, match="not what the batch name says"):  # a bb8 run filed under the open8 batch
        BA.study_rows(study + [dict(row("gpt", "bb8", "ep411", 1), batch="r1112_gpt_open8")], study_tag="r1112")


def test_command_line_selects_by_batch_and_fails_on_a_cell_above_the_plan(tmp_path, capsys):
    study = in_batches(hand_study())
    main_study = [dict(r, batch="r1103_gpt_b1") for r in grid("gpt", "open8", [(0, 0)] * 6)]
    src, out_md, out_json = tmp_path / "rows.csv", tmp_path / "r.md", tmp_path / "r.json"
    write_rows(src, study + main_study)
    assert BA.main([str(src), "--resamples", "200", "--out-md", str(out_md), "--out-json", str(out_json)]) == 0
    got = json.loads(out_json.read_text())
    assert got["rates"]["gpt"]["open8"]["k"] == 20 and got["rates"]["gpt"]["open8"]["n"] == 24  # default tag r1112
    assert got["input"]["left_out"] == {"batch outside the study (not r1112_<agent>_<arm>)": 12}
    # the same file with no batch rule: the main-study runs land in the fresh Open-8 arm, and the run fails loudly
    assert BA.main([str(src), "--any-batch", "--resamples", "200", "--out-md", str(out_md), "--out-json", str(out_json)]) == 2
    assert "have more counted runs than planned" in capsys.readouterr().err
    assert out_md.read_text().splitlines()[4].startswith("**ERROR: 6 cell(s) have more counted runs than planned")
    # a re-run of a counted run inside the study's own batch is caught in the same way
    write_rows(src, study + in_batches([row("gpt", "bb8", "ep474", 1)]))
    assert BA.main([str(src), "--resamples", "200", "--out-md", str(out_md)]) == 2
    assert "gpt bb8 ep474: 5 runs (planned 4)" in capsys.readouterr().err
    write_rows(src, in_batches(hand_study(), tag="r1113"))
    assert BA.main([str(src), "--study-tag", "r1113", "--resamples", "200", "--out-md", str(out_md)]) == 0
    with pytest.raises(SystemExit, match="none of the 108 rows"):
        BA.main([str(src), "--resamples", "200", "--out-md", str(out_md)])
    write_rows(src, study + [dict(row("gpt", "bb8", "ep411", 1), batch="r1112_gpt_open8")])
    with pytest.raises(SystemExit, match="not what the batch name says"):
        BA.main([str(src), "--resamples", "200", "--out-md", str(out_md)])


# ---------------------------------------------------------------------------------------------------------
# zero-width intervals, the random stream, Haiku without tests

def test_zero_width_intervals_are_flagged():
    ones, zeros = [(1, 1, 1, 1)] * 6, [(0, 0, 0, 0)] * 6
    res = BA.analyse(grid("gpt", "open8", zeros) + grid("gpt", "bb8", zeros) + grid("gpt", "bb64", zeros), n=500)
    r, c4 = res["rates"]["gpt"]["open8"], res["confirmatory"]["contrasts"]["C4"]
    assert r["cluster95"] == [0.0, 0.0] and r["cluster_zero_width"] is True and r["wilson95"][1] > 0.13
    assert c4["ci95"] == [0.0, 0.0] and c4["ci_zero_width"] is True and c4["p"] == 1.0
    # the pre-registered rule is applied as written, and the report says what the interval is
    assert res["r3"]["decision"] == BA.r3_decision(0.0, 0.0) == "eliminated" and res["r3"]["ci_zero_width"] is True
    assert "zero-width interval" in res["r3"]["caveat"] and "BB-64 0/24 = 0.00 [0.00, 0.14]" in res["r3"]["caveat"]
    md = BA.render_md(res)
    assert "| gpt | Open-8 | 0/24 = 0.00 | [0.00, 0.14] | [0.00, 0.00] (zero width; read the Wilson interval) |" in md
    assert "| +0.000 | [+0.00, +0.00] (zero width) | 1.0000 |" in md and BA.ZERO_WIDTH_NOTE in md
    assert "→ **eliminated**. Caveat (zero-width interval:" in md
    top = BA.analyse(grid("gpt", "open8", ones) + grid("gpt", "bb8", [(1, 1, 0, 0)] * 6) + grid("gpt", "bb64", ones)
                     + grid("haiku", "bb8", [(0, 0)] * 6), n=500)
    assert top["rates"]["gpt"]["bb64"]["cluster95"] == [1.0, 1.0] and top["rates"]["gpt"]["bb64"]["cluster_zero_width"]
    assert top["rates"]["haiku"]["bb8"]["cluster_zero_width"] and not top["rates"]["gpt"]["bb8"]["cluster_zero_width"]
    assert top["r3"]["ci_zero_width"] and not top["confirmatory"]["contrasts"]["C1"]["ci_zero_width"]
    assert "| haiku | BB-8 | 0/12 = 0.00 | [0.00, 0.24] | [0.00, 0.00] (zero width; read the Wilson interval) |" in BA.render_md(top)
    usual = BA.analyse(hand_study(), n=500)  # nothing is flagged when the cells vary
    assert usual["r3"]["ci_zero_width"] is False and usual["r3"]["caveat"] is None
    assert not any(t["ci_zero_width"] for t in usual["confirmatory"]["contrasts"].values())
    md = BA.render_md(usual)
    assert "zero width)" not in md and "Caveat" not in md and BA.ZERO_WIDTH_NOTE not in md
    assert "under-covers when the rate is near 0 or 1" in md  # stated in every report's header
    assert BA.zero_width(0.5, 0.5) and not BA.zero_width(0.5, 0.5001) and not BA.zero_width(None, None)


def test_random_stream_is_recorded():
    res = BA.analyse(hand_study(), n=200)
    assert res["meta"]["numpy"] == np.__version__ and res["meta"]["seed"] == BA.SEED
    assert res["meta"]["bit_generator"] == "PCG64 (numpy.random.default_rng)"
    assert f"seed {BA.SEED}, numpy {np.__version__}, bit generator PCG64 (numpy.random.default_rng)" in BA.render_md(res)
    assert json.loads(BA.dumps(res))["meta"]["numpy"] == np.__version__


def test_power_output_records_the_stream(tmp_path):
    out_md, out_json = tmp_path / "p.md", tmp_path / "p.json"
    assert BA.main(["--power", "--power-sims", "3", "--out-md", str(out_md), "--out-json", str(out_json)]) == 0
    got = json.loads(out_json.read_text())
    assert got["meta"] == {"seed": BA.SEED, "numpy": np.__version__, "bit_generator": "PCG64 (numpy.random.default_rng)"}
    assert len(got["power"]) == 14 and f"numpy {np.__version__}, bit generator PCG64" in out_md.read_text()


def test_haiku_is_descriptive_only_no_p_value():
    res = BA.analyse(hand_study(), n=500)
    hk = list(res["haiku_contrasts"].values()) + [t for k in BA.KINDS for t in res["by_kind"]["haiku"][k].values()]
    assert len(hk) == 3 + 6
    assert all(t["p"] is None and t["n_extreme"] is None and t["tested"] is False and "p_holm" not in t for t in hk)
    assert all(t["T"] is not None and t["ci95"] is not None for t in hk)  # the difference and its interval stay
    assert res["haiku_contrasts"]["C1"]["T"] == pytest.approx(6 / 12 - 3 / 12)
    gpt = list(res["confirmatory"]["contrasts"].values()) + [t for k in BA.KINDS for t in res["by_kind"]["gpt"][k].values()]
    assert all(t["tested"] is True and 0 < t["p"] <= 1 for t in gpt)
    # the untested difference is the tested one minus the test: same T, same interval
    rows = [r for r in hand_study() if r["agent"] == "haiku"]
    a, b = BA.contrast(rows, "open8", "bb8", n=500), BA.contrast(rows, "open8", "bb8", n=500, test=False)
    assert (a["T"], a["ci95"]) == (b["T"], b["ci95"]) and a["p"] is not None and b["p"] is None
    md = BA.render_md(res)
    sec = sections(md)
    # Haiku's two tables have no p-value column at all: 7 cells per row, the last one the number of items
    for name, n_rows in (("## Haiku (descriptive only; no family, not pooled with GPT)", 3),
                         ("## By kind, Haiku (descriptive differences; no test, no p-value; 3 items each)", 6)):
        table = [l for l in sec[name] if l.startswith("|")]
        assert len(table) == 2 + n_rows and all(len(cells(l)) == 7 for l in table)
        assert "permutation p" not in table[0] and "Holm" not in table[0] and "significant" not in table[0]
        assert all(cells(l)[-1] in ("6", "3") for l in table[2:])
    assert [cells(l)[0] for l in sec["## By kind, Haiku (descriptive differences; no test, no p-value; 3 items each)"]
            if l.startswith("| t")] == ["trap, C1", "trap, C2", "trap, C4", "twopart, C1", "twopart, C2", "twopart, C4"]
    # GPT by kind: C1, C2, C4 only, an unadjusted permutation p, no Holm p and no significance label
    kind = [l for l in sec["## By kind, GPT (pre-registered secondaries; unadjusted permutation p; 3 items each)"] if l.startswith("|")]
    assert len(kind) == 2 + 6 and all(len(cells(l)) == 8 for l in kind) and cells(kind[0])[6] == "permutation p (unadjusted)"
    assert all(0 < float(cells(l)[6]) <= 1 for l in kind[2:]) and "Holm" not in kind[0] and "significant" not in kind[0]
    conf = [l for l in sec["## Confirmatory tests (GPT)"] if l.startswith("| C")]
    assert [cells(l)[0] for l in conf] == ["Contrast", "C1 (Holm family)", "C2 (Holm family)", "C4 (outside the family)",
                                           "C3 (outside the family)"]
    assert cells(conf[0])[6:9] == ["permutation p", "Holm p", "significant (Holm p < 0.05)"]
    assert all(0 < float(cells(l)[6]) <= 1 for l in conf[1:4])
    assert "no test is run and no p-value is computed for Haiku" in md
    # no p-value for Haiku anywhere in the numbers, and no Fisher p anywhere (the drift check is descriptive)
    back = json.loads(BA.dumps(res))
    assert p_values(back["haiku_contrasts"]) == [] and p_values(back["by_kind"]["haiku"]) == [] and p_values(back["drift"]) == []
    assert len(p_values(back["by_kind"]["gpt"])) == 2 * 6 and "fisher" not in BA.dumps(res).lower() and "Fisher" not in md
    assert not hasattr(BA, "fisher_exact")


def sections(md):
    """{header line: the lines of that section} of a report."""
    out, cur = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            cur = out.setdefault(line, [])
        elif cur is not None:
            cur.append(line)
    return out


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def p_values(obj):
    """Every non-null value stored under a key named p, p_holm, fisher_p or n_extreme, at any depth."""
    if isinstance(obj, dict):
        return [v for k, v in obj.items() if k in ("p", "p_holm", "fisher_p", "n_extreme") and v is not None] + [
            x for v in obj.values() for x in p_values(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in p_values(v)]
    return []


def test_by_kind_covers_c1_c2_c4_only_even_with_open64():
    res = BA.analyse(BA.simulate_rows(seed=6, open64=True), n=200)
    assert "C3" in res["confirmatory"]["contrasts"] and BA.KIND_CONTRASTS == ("C1", "C2", "C4")
    for a in ("gpt", "haiku"):
        assert {k: list(v) for k, v in res["by_kind"][a].items()} == {"trap": ["C1", "C2", "C4"], "twopart": ["C1", "C2", "C4"]}
    assert all("significant" not in t and "p_holm" not in t for a in ("gpt", "haiku") for k in BA.KINDS
               for t in res["by_kind"][a][k].values())
    md = BA.render_md(res)
    assert [l for l in md.splitlines() if l.startswith("| C3")] == [l for l in md.splitlines() if l.startswith("| C3 (outside the family) | Open-64 − BB-64 |")]
    c3 = cells([l for l in md.splitlines() if l.startswith("| C3 (outside")][0])
    assert c3[7:9] == ["—", "—"] and 0 < float(c3[6]) <= 1  # p shown, no Holm p, never labelled


# ---------------------------------------------------------------------------------------------------------
# significance and the testing-capacity line through the pipeline

def test_only_the_holm_family_is_labelled_significant():
    res = BA.analyse(BA.simulate_rows(seed=6, open64=True), n=400)
    c = res["confirmatory"]["contrasts"]
    assert res["confirmatory"]["alpha"] == BA.ALPHA == 0.05 and res["meta"]["tolerance"] == 1e-9
    for k in ("C1", "C2"):
        assert c[k]["significant"] is (c[k]["p_holm"] < 0.05) and isinstance(c[k]["significant"], bool)
    assert c["C4"]["significant"] is None and c["C3"]["significant"] is None
    # the label follows the Holm-adjusted p, not the raw p: 0.03 and 0.04 give Holm p 0.06 for both
    assert BA.holm({"C1": 0.03, "C2": 0.04}, m=2) == {"C1": 0.06, "C2": 0.06}
    weak = BA.analyse(grid("gpt", "open8", [(1, 1, 1, 0)] * 6) + grid("gpt", "bb8", [(1, 1, 0, 0)] * 6)
                      + grid("gpt", "bb64", [(1, 1, 0, 0)] * 6), n=400)["confirmatory"]["contrasts"]
    assert weak["C1"]["p"] < weak["C1"]["p_holm"] and weak["C2"]["significant"] is False
    md = BA.render_md(res)
    assert BA.RULES_NOTE in md and "significant iff its Holm-adjusted two-sided permutation p is below 0.05" in md
    assert "Tolerance 1e-9: a bound within 1e-9 of a threshold is not past it" in md
    assert 'L > -0.20 and U >= 0: "eliminated"; L <= -0.20 and U < 0: "not eliminated"; L > -0.20 and U < 0: ' \
           '"eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)"; otherwise "inconclusive"' in md
    rows = {cells(l)[0]: cells(l) for l in sections(md)["## Confirmatory tests (GPT)"] if l.startswith("| C")}
    for k, fam in (("C1", "Holm family"), ("C2", "Holm family")):
        assert rows[f"{k} ({fam})"][8] == ("yes" if c[k]["significant"] else "no")
    assert rows["C4 (outside the family)"][8] == "—" and rows["C3 (outside the family)"][8] == "—"
    assert " yes |" not in "".join(l for l in md.splitlines() if l.startswith(("| trap", "| twopart")))


def test_significance_label_uses_the_holm_p_not_the_raw_p():
    """A study where the two differ on the label: C1 has raw p 0.042 (below 0.05) and Holm p 0.084 (not)."""
    rows = (grid("gpt", "open8", [(1, 1, 1, 1), (0, 0, 1, 1), (1, 0, 0, 1), (0, 1, 1, 1), (0, 1, 1, 1), (1, 1, 1, 1)])
            + grid("gpt", "bb8", [(0, 1, 0, 0), (0, 0, 0, 1), (1, 0, 0, 1), (1, 0, 0, 1), (0, 1, 0, 1), (1, 0, 1, 0)])
            + grid("gpt", "bb64", [(1, 0, 0, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1), (1, 0, 1, 0), (1, 1, 0, 0)]))
    res = BA.analyse(rows, n=2000)
    c1, c2 = res["confirmatory"]["contrasts"]["C1"], res["confirmatory"]["contrasts"]["C2"]
    assert c1["p"] == pytest.approx(0.042, abs=0.0005) and c1["p"] < BA.ALPHA < c1["p_holm"] == pytest.approx(2 * c1["p"])
    assert c1["significant"] is False and c2["significant"] is False and c2["p"] > BA.ALPHA
    assert res["testing_capacity"]["c1_significant"] is False and res["testing_capacity"]["holds"] is False
    md = BA.render_md(res)
    line = cells([l for l in md.splitlines() if l.startswith("| C1 (Holm family)")][0])
    assert line[6:9] == ["0.0420", "0.0840", "no"]
    assert "C1 significant: no (Holm p 0.0840)" in md and "→ **does not hold: C1 is not significant" in md
    # with the resamples of the real analysis the two p-values are on the same sides of 0.05
    full = BA.analyse(rows)["confirmatory"]["contrasts"]["C1"]
    assert full["p"] < 0.05 < full["p_holm"] and full["significant"] is False


def many(agent, arm, k, n=40):
    """n runs per item with k passes each (cells far above the plan: for a narrow interval only)."""
    return grid(agent, arm, [(1,) * k + (0,) * (n - k)] * 6)


@pytest.mark.parametrize("bb8,bb64,decision,holds,text", [
    (0, 40, "eliminated", True, 'R3 verdict: first branch ("eliminated") → **holds: C1 is significant'),
    (0, 36, BA.R3_BOTH, True, "R3 verdict: third branch (both-true: eliminated at the -0.20 margin, with a residual deficit) "
                              "→ **holds, with a residual deficit: C1 is significant"),
    (0, 20, "not eliminated", False, 'R3 verdict: second branch ("not eliminated") → **does not hold: the R3 verdict is "not eliminated"**'),
    (40, 40, "eliminated", False, 'C1 significant: no (Holm p 1.0000); R3 verdict: first branch ("eliminated") → '
                                  "**does not hold: C1 is not significant**"),
])
def test_testing_capacity_line_in_the_report(bb8, bb64, decision, holds, text):
    res = BA.analyse(many("gpt", "open8", 40) + many("gpt", "bb8", bb8) + many("gpt", "bb64", bb64), n=400)
    assert res["r3"]["decision"] == decision and res["r3"]["branch"] == BA.R3_BRANCH[decision]
    tc = res["testing_capacity"]
    assert tc["holds"] is holds and tc["c1_significant"] is (bb8 == 0) and tc["r3_branch"] == BA.R3_BRANCH[decision]
    md = BA.render_md(res)
    line = [l for l in md.splitlines() if l.startswith("**Testing capacity**")]
    assert len(line) == 1 and text in line[0], line
    assert ("residual deficit remains: BB-64 is below Open-8 (the CI of C4 excludes 0)" in line[0]) == (decision == BA.R3_BOTH)
    assert f"→ **{decision}**." in md  # the R3 verdict strings are unchanged


def test_inconclusive_r3_means_no_testing_capacity_statement():
    res = BA.analyse(hand_study(), n=2000)  # C4 = -1/6 with a wide interval
    assert res["r3"]["decision"] == "inconclusive" and res["testing_capacity"]["holds"] is False
    assert res["testing_capacity"]["c1_significant"] is True
    assert '→ **does not hold: the R3 verdict is "inconclusive"**' in BA.render_md(res)


# ---------------------------------------------------------------------------------------------------------
# drift check: descriptive, pooled and with equal item weights

def test_main_study_constants_are_the_rollouts_csv_numbers():
    """The per-item constants of the drift check, recomputed from the tracked main-study file: batches b1 and
    b2 only (no hv, no smoke), column hard_pass (= NAME on every main-study run)."""
    with open(ROOT / "results/cross_model_1103/rollouts.csv", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["batch"] in ("b1", "b2")]
    assert len(rows) == 64
    for agent, pooled, mean in (("gpt", (14, 16), 0.8333), ("haiku", (8, 16), 0.4722)):
        got = OrderedDict()
        for it in ITEMS:
            rs = [r for r in rows if r["agent"] == agent and r["episode"] == it]
            got[it] = (sum(int(r["hard_pass"]) for r in rs), len(rs))
        const = BA.MAIN_STUDY_NAME_BY_ITEM[agent]
        assert dict(const) == dict(got) and list(const) == ITEMS
        assert (sum(k for k, _ in const.values()), sum(n for _, n in const.values())) == pooled == BA.MAIN_STUDY_NAME[agent]
        assert round(sum(k / n for k, n in const.values()) / 6, 4) == mean
        assert {n for _, n in const.values()} == {2, 3}  # why the equal-item-weight comparison is given


def test_drift_is_descriptive_pooled_and_equal_item_weight():
    res = BA.analyse(hand_study(), n=300)
    g, h = res["drift"]["gpt"], res["drift"]["haiku"]
    assert set(g) == {"fresh", "main_study", "difference", "equal_item_weight"}  # no p-value of any kind
    assert (g["fresh"]["k"], g["fresh"]["n"]) == (20, 24) and g["fresh"]["wilson95"] == list(BA.wilson(20, 24))
    assert g["main_study"] == {"k": 14, "n": 16, "rate": 14 / 16, "wilson95": list(BA.wilson(14, 16))}
    assert g["difference"] == pytest.approx(20 / 24 - 14 / 16) and h["difference"] == pytest.approx(6 / 12 - 8 / 16)
    e = g["equal_item_weight"]
    assert e["fresh"] == pytest.approx((1 + .75 + 1 + .75 + .5 + 1) / 6) and e["main_study"] == pytest.approx(5 / 6)
    assert e["difference"] == pytest.approx(e["fresh"] - e["main_study"]) and e["items"] == ITEMS
    assert e["items_without_fresh_run"] == [] and round(e["main_study_all_items"], 4) == 0.8333
    assert e["fresh_by_item"]["ep474"] == {"k": 2, "n": 4} and e["main_study_by_item"]["ep413"] == {"k": 1, "n": 2}
    eh = h["equal_item_weight"]
    assert eh["fresh"] == pytest.approx((.5 + 0 + .5 + 1 + .5 + .5) / 6) and round(eh["main_study"], 4) == 0.4722
    md = BA.render_md(res)
    table = [l for l in sections(md)["## Drift check: fresh Open-8 against the main study (descriptive; no test)"] if l.startswith("|")]
    assert len(table) == 4 and len(cells(table[0])) == 9 and not any(re.search(r"\bp\b|exact|test", c) for c in cells(table[0]))
    assert cells(table[2]) == ["gpt", "20/24 = 0.83 [0.64, 0.93]", "14/16 = 0.88 [0.64, 0.97]", "-0.042", "0.8333", "0.8333",
                               "+0.000", "4/4 3/4 4/4 3/4 2/4 4/4", "3/3 1/2 3/3 3/3 1/2 3/3"]
    assert cells(table[3])[:7] == ["haiku", "6/12 = 0.50 [0.25, 0.75]", "8/16 = 0.50 [0.28, 0.72]", "+0.000", "0.5000",
                                   "0.4722", "+0.028"]
    assert "results/cross_model_1103/rollouts.csv (batches b1 and b2)" in md


def test_drift_with_unequal_cells_and_a_missing_item():
    """Pooled and equal-item-weight rates differ when the fresh cells are unequal; an item without a fresh run
    is left out of both means and named."""
    rows = grid("gpt", "open8", [(1, 1, 1, 1), (0,), (1, 1, 1, 1), (1, 1), (), (1, 1, 1, 0)])
    res = BA.analyse(rows, n=200)
    d = res["drift"]["gpt"]
    assert d["fresh"]["rate"] == 13 / 15 and "haiku" not in res["drift"]
    e = d["equal_item_weight"]
    assert e["items"] == [i for i in ITEMS if i != "ep474"] and e["items_without_fresh_run"] == ["ep474"]
    assert e["fresh"] == pytest.approx((1 + 0 + 1 + 1 + .75) / 5)
    assert e["main_study"] == pytest.approx((1 + .5 + 1 + 1 + 1) / 5) and round(e["main_study_all_items"], 4) == 0.8333
    assert "Items without a fresh Open-8 run, left out of both means of item rates: gpt: ep474." in BA.render_md(res)


# ---------------------------------------------------------------------------------------------------------
# S3: the coder's CSV joined on (batch, run)

def numbered(rows):
    """Rows of the study's batches with distinct 12-character run names (what the scorer writes)."""
    return [dict(r, batch=f"r1112_{r['agent']}_{r['arm']}", run=f"c{j:011d}", submitted=1) for j, r in enumerate(rows)]


def s3_rows(rows, s3=lambda r: r["name"], log="ok"):
    return [{"run": r["run"], "batch": r["batch"], "episode": r["episode"], "arm": r["arm"], "s3": s3(r), "log": log}
            for r in rows]


def write_s3(path, entries):
    """The CSV as scripts/s3_coder.py writes it (its own columns and its own writer)."""
    import s3_coder as S3
    path.write_text(S3.csv_text([dict(dict.fromkeys(S3.CSV_COLUMNS), **e) for e in entries]))
    return path


def test_s3_columns_are_the_coders():
    import s3_coder as S3
    assert set(BA.S3_COLUMNS) <= set(S3.CSV_COLUMNS) and BA.S3_COLUMNS == ("run", "batch", "episode", "arm", "s3", "log")


def test_s3_join_missing_runs_and_the_table(tmp_path):
    rows = numbered(hand_study())
    infra = dict(row("gpt", "bb8", "ep411", 0, counted=0, status="infra"), batch="r1112_gpt_bb8", run="d00000000001")
    pilot = dict(row("gpt", "bb8", "ep411", 1), batch="r1112_pilot_gpt_bb8", run="e00000000001")
    gpt_bb8 = [r for r in rows if (r["agent"], r["arm"]) == ("gpt", "bb8")]  # 8 named of 24
    entries = s3_rows(rows, s3=lambda r: 1 if r["name"] else 0) + s3_rows([infra], s3=lambda r: None, log="missing")
    drop, blank, flip = gpt_bb8[0]["run"], {gpt_bb8[2]["run"]: "torn", gpt_bb8[3]["run"]: "missing"}, gpt_bb8[1]["run"]
    entries = [e for e in entries if e["run"] != drop]
    for e in entries:
        if e["run"] in blank:
            e["s3"], e["log"] = None, blank[e["run"]]
        if e["run"] == flip:
            e["s3"] = 0  # NAME = 1 without a clean variation: an off-diagonal cell
    src = write_s3(tmp_path / "s3.csv", entries)
    got = BA.read_s3_csv(src)
    assert len(got) == 108 - 1 + 1 and set(BA.S3_COLUMNS) <= set(got[0]) and got[0]["s3"] in ("0", "1")
    res = BA.analyse(rows + [infra, pilot], n=200, study_tag="r1112", s3=got)
    assert res["s3_source"] == "S3 CSV joined on (batch, run)" and list(res["s3"]) == [
        "gpt|open8", "gpt|bb8", "gpt|bb64", "haiku|open8", "haiku|bb8", "haiku|bb64"]  # every agent and arm
    t = res["s3"]["gpt|bb8"]
    # gpt bb8: rows are (1,1,0,0), (1,0,0,0), ...: run 0 absent (NAME 1), run 1 flipped (NAME 1, S3 0), runs 2, 3 blank
    assert (t["n"], t["no_s3"], t["no_s3_why"]) == (21, 3, {"missing": 1, "not in the S3 CSV": 1, "torn": 1})
    assert (t["s3_1_name_1"], t["s3_1_name_0"], t["s3_0_name_1"], t["s3_0_name_0"]) == (6, 0, 1, 14)
    assert t["name_given_s3_1"] == {"k": 6, "n": 6, "rate": 1.0, "wilson95": list(BA.wilson(6, 6))}
    o = res["s3"]["gpt|open8"]
    assert (o["n"], o["no_s3"], o["no_s3_why"], o["s3_1_name_1"], o["s3_0_name_0"]) == (24, 0, {}, 20, 4)
    assert res["rates"]["gpt"]["bb8"]["k"] == 8 and res["rates"]["gpt"]["bb8"]["n"] == 24  # the join changes no outcome
    md = BA.render_md(res)
    assert "| gpt | BB-8 | 6 | 0 | 1 | 14 | 6/6 = 1.00 [0.61, 1.00] | 3 (missing 1, not in the S3 CSV 1, torn 1) |" in md
    assert "| haiku | BB-64 | 6 | 0 | 0 | 6 | 6/6 = 1.00 [0.61, 1.00] | 0 |" in md
    # an arm where no run has S3 still has its row
    none = BA.analyse(rows + [infra], n=200, study_tag="r1112", s3=[e for e in got if e["batch"] != "r1112_haiku_bb64"])
    assert none["s3"]["haiku|bb64"]["n"] == 0 and none["s3"]["haiku|bb64"]["no_s3"] == 12
    assert "| haiku | BB-64 | 0 | 0 | 0 | 0 | n/a | 12 (not in the S3 CSV 12) |" in BA.render_md(none)
    # the join returns copies: the caller's rows are untouched
    assert "s3" not in rows[0] and BA.join_s3(rows + [infra], got, "r1112")[0]["s3_log"] == "ok"
    with pytest.raises(ValueError, match="r1112_gpt_bb8/d00000000001: no row of the study has this batch and run"):
        BA.join_s3(rows, got, "r1112")  # the coded directory of an excluded run must be in the scorer's rows too


@pytest.mark.parametrize("change,message", [
    (lambda e: e.append(dict(e[0], run="zzzzzzzzzzzz")), "r1112_gpt_open8/zzzzzzzzzzzz: no row of the study has this batch and run"),
    (lambda e: e.append(dict(e[0], batch="r1112_pilot_gpt_bb8", run="e00000000001")),
     "r1112_pilot_gpt_bb8/e00000000001: no row of the study has this batch and run"),      # a pilot run that was coded
    (lambda e: e.append(dict(e[0])), "r1112_gpt_open8/c00000000000: twice in the S3 CSV"),
    (lambda e: e[0].update(episode="ep413"), "episode 'ep413' in the S3 CSV, 'ep411' in the rows"),
    (lambda e: e[0].update(arm="bb8"), "arm 'bb8' in the S3 CSV, 'open8' in the rows"),
    (lambda e: e[0].update(s3="2"), "s3 is '2', not 0, 1 or blank"),
])
def test_s3_join_fails_loudly(tmp_path, change, message):
    rows = numbered(hand_study())
    pilot = dict(row("gpt", "bb8", "ep411", 1), batch="r1112_pilot_gpt_bb8", run="e00000000001")
    entries = [dict(e, s3=str(e["s3"])) for e in s3_rows(rows)]
    change(entries)
    with pytest.raises(ValueError, match="S3 CSV: .*" + message.replace("(", r"\(").replace(")", r"\)")):
        BA.analyse(rows + [pilot], n=100, study_tag="r1112", s3=entries)
    src, s3_path = tmp_path / "rows.csv", tmp_path / "s3.csv"
    write_rows(src, rows + [pilot])
    with open(s3_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(entries[0]))
        w.writeheader()
        w.writerows(entries)
    with pytest.raises(SystemExit, match="error: S3 CSV: "):  # non-zero exit, nothing written
        BA.main([str(src), "--s3", str(s3_path), "--resamples", "100", "--out-md", str(tmp_path / "r.md")])
    assert not (tmp_path / "r.md").exists()


def test_s3_on_the_command_line(tmp_path):
    rows = numbered(hand_study())
    src, out_json = tmp_path / "rows.csv", tmp_path / "r.json"
    write_rows(src, rows)
    s3_path = write_s3(tmp_path / "s3.csv", s3_rows(rows[5:]))
    assert BA.main([str(src), "--s3", str(s3_path), "--resamples", "100", "--out-md", str(tmp_path / "r.md"),
                    "--out-json", str(out_json)]) == 0
    got = json.loads(out_json.read_text())
    assert got["s3"]["gpt|open8"]["no_s3"] == 5 and got["input"]["s3_csv"] == "s3.csv" and got["first_attempt"] is None
    (tmp_path / "bad.csv").write_text("run,batch,s3\nc00000000000,r1112_gpt_open8,1\n")
    with pytest.raises(SystemExit, match=r"not a CSV of scripts/s3_coder.py \(column\(s\) episode, arm, log missing\)"):
        BA.main([str(src), "--s3", str(tmp_path / "bad.csv"), "--resamples", "100"])
    with pytest.raises(SystemExit, match="error: "):
        BA.main([str(src), "--s3", str(tmp_path / "nowhere.csv"), "--resamples", "100"])
    with pytest.raises(SystemExit):  # the dry run simulates its own S3 table and ledger
        BA.main(["--simulate", "--s3", str(s3_path)])


# ---------------------------------------------------------------------------------------------------------
# the ledger: jobs, attempts, the first-attempt sensitivity analysis

def ledger_of(rows, block="block1", infra=None, first_order=1):
    """Events in the scheduler's shape (scripts/blackbox_schedule.py): one job per row, in row order. infra:
    {row index: [reason of each excluded attempt before the counted one]}."""
    events = [{"event": "start", "block": block, "t": "2026-11-12T00:00:00Z", "ts": 0.0, "jobs": len(rows)}]
    for i, r in enumerate(rows):
        job = dict(block=block, order=first_order + i, agent=r["agent"], arm=r["arm"], item=r["episode"],
                   problem=r["episode"] + "-x", provider="p", ts=float(i))
        k = 0
        for k, why in enumerate((infra or {}).get(i, []), 1):
            events += [dict(job, event="launched", attempt=k, run=r["batch"], child_log="x.log", pid=1),
                       dict(job, event="infra", attempt=k, run=r["batch"], reason=why, n_infra=k, usd=0.1,
                            cid=None if why in ("no_container", "interrupted") else f"f{i:05d}a{k}0000"),
                       dict(job, event="requeued", n_infra=k, position=9)]
        events += [dict(job, event="launched", attempt=k + 1, run=r["batch"], child_log="x.log", pid=1),
                   dict(job, event="finished", attempt=k + 1, run=r["batch"], cid=r["run"], usd=1.0, flags=[],
                        status="ok" if r.get("submitted", 1) else "fail:no_submission")]
    return events


PILOT_EVENTS = [dict(event=ev, block="pilots", order=1, attempt=1, agent="gpt", arm="open8", item="ep411",
                     run="r1112_pilot_gpt_open8", cid="9" * 12, status="ok") for ev in ("launched", "finished")]


def test_first_attempt_equals_the_primary_when_no_job_had_an_infrastructure_failure():
    rows = numbered(hand_study())
    res = BA.analyse(rows, n=400, study_tag="r1112", ledger=ledger_of(rows) + PILOT_EVENTS)
    fa = res["first_attempt"]
    assert fa["equals_primary"] is True and fa["first_attempt_infra"] == [] and fa["excluded"] == [] and fa["excluded_runs"] == []
    assert fa["jobs"] == 108 and len(fa["runs"]) == 108 and fa["counted_runs_by_attempt"] == {"1": 108}
    assert fa["runs"]["r1112_gpt_open8/c00000000000"] == {"block": "block1", "order": 1, "attempt": 1}
    assert BA.dumps(fa["contrasts"]) == BA.dumps(res["confirmatory"]["contrasts"]) and fa["r3"] == res["r3"]
    assert fa["testing_capacity"] == res["testing_capacity"] and BA.dumps(fa["haiku_contrasts"]) == BA.dumps(res["haiku_contrasts"])
    assert {a: {arm: (r["k"], r["n"]) for arm, r in v.items()} for a, v in fa["rates"].items()} == {
        "gpt": {"open8": (20, 24), "bb8": (8, 24), "bb64": (16, 24)}, "haiku": {"open8": (6, 12), "bb8": (3, 12), "bb64": (6, 12)}}
    md = BA.render_md(res)
    sec = sections(md)
    assert ("No job had an infrastructure failure: every job's first attempt is its counted run, and the sensitivity "
            "analysis equals the primary analysis.") in sec["## First-attempt sensitivity analysis (infrastructure re-runs)"]
    assert sec["## Excluded runs (infrastructure failures) by agent, arm and reason"][1] == (
        "The ledger records no infrastructure failure in blocks block1, block2.")
    table = {cells(l)[0]: cells(l)[1:] for l in sec["## First-attempt sensitivity analysis (infrastructure re-runs)"] if l.startswith("| C")}
    for k in ("C1 (Holm family)", "C2 (Holm family)", "C4 (outside the family)"):
        assert table[k + ", primary"] == table[k + ", first attempt"]
    assert "## First-attempt sensitivity analysis (infrastructure re-runs)" in BA.render_md(BA.analyse(rows, n=100))
    assert "Not computed: no ledger was given (--ledger)." in BA.render_md(BA.analyse(rows, n=100))


def infra_study():
    """hand_study with five jobs whose first attempt was an infrastructure failure. Row indices: GPT Open-8
    0..23 (ep411 = rows 0..3, all NAME 1), GPT BB-8 24..47 (ep411 = 1, 1, 0, 0), Haiku Open-8 72..83 (ep411 = 1, 0)."""
    rows = numbered(hand_study())
    infra = {0: ["api_error"], 1: ["no_container", "api_error"], 24: ["no_grade"], 26: ["api_error"], 72: ["api_error"]}
    assert [rows[i]["name"] for i in infra] == [1, 1, 1, 0, 1]
    return rows, infra


def test_first_attempt_counts_an_excluded_first_attempt_as_a_fail():
    rows, infra = infra_study()
    res = BA.analyse(rows, n=500, study_tag="r1112", ledger=ledger_of(rows, infra=infra) + PILOT_EVENTS)
    fa, primary = res["first_attempt"], res["confirmatory"]["contrasts"]
    assert primary["C1"]["T"] == pytest.approx(0.5) and res["rates"]["gpt"]["open8"]["k"] == 20  # the primary is untouched
    assert fa["equals_primary"] is False and fa["jobs"] == 108 and len(fa["runs"]) == 108
    assert fa["counted_runs_by_attempt"] == {"1": 103, "2": 4, "3": 1}
    assert fa["runs"]["r1112_gpt_open8/c00000000001"] == {"block": "block1", "order": 2, "attempt": 3}
    assert {a: {arm: (r["k"], r["n"]) for arm, r in v.items()} for a, v in fa["rates"].items()} == {
        "gpt": {"open8": (18, 24), "bb8": (7, 24), "bb64": (16, 24)}, "haiku": {"open8": (5, 12), "bb8": (3, 12), "bb64": (6, 12)}}
    c = fa["contrasts"]
    assert c["C1"]["T"] == pytest.approx(18 / 24 - 7 / 24) and c["C2"]["T"] == pytest.approx(16 / 24 - 7 / 24)
    assert c["C4"]["T"] == pytest.approx(16 / 24 - 18 / 24) and list(c) == ["C1", "C2", "C4"]
    assert {k: c[k]["p_holm"] for k in ("C1", "C2")} == BA.holm({"C1": c["C1"]["p"], "C2": c["C2"]["p"]})
    assert c["C1"]["significant"] is (c["C1"]["p_holm"] < 0.05) and c["C4"]["significant"] is None
    assert fa["r3"]["ci95"] == c["C4"]["ci95"] and fa["r3"]["decision"] == BA.r3_decision(*c["C4"]["ci95"])
    assert fa["haiku_contrasts"]["C1"]["T"] == pytest.approx(5 / 12 - 3 / 12) and fa["haiku_contrasts"]["C1"]["p"] is None
    # the same numbers from rows changed by hand: the four NAME = 1 jobs become fails, nothing else changes
    by_hand = [dict(r, name=0) if i in (0, 1, 24, 72) else r for i, r in enumerate(rows)]
    want = BA.confirmatory([r for r in by_hand if r["agent"] == "gpt"], 500)
    assert BA.dumps(c) == BA.dumps(want)
    assert [(x["agent"], x["arm"], x["item"], x["reason"], x["counted_rerun"]) for x in fa["first_attempt_infra"]] == [
        ("gpt", "open8", "ep411", "api_error", True), ("gpt", "open8", "ep411", "no_container", True),
        ("gpt", "bb8", "ep411", "no_grade", True), ("gpt", "bb8", "ep411", "api_error", True),
        ("haiku", "open8", "ep411", "api_error", True)]
    assert fa["excluded"] == [
        {"agent": "gpt", "arm": "open8", "reason": "api_error", "runs": 2, "first_attempts": 1},
        {"agent": "gpt", "arm": "open8", "reason": "no_container", "runs": 1, "first_attempts": 1},
        {"agent": "gpt", "arm": "bb8", "reason": "api_error", "runs": 1, "first_attempts": 1},
        {"agent": "gpt", "arm": "bb8", "reason": "no_grade", "runs": 1, "first_attempts": 1},
        {"agent": "haiku", "arm": "open8", "reason": "api_error", "runs": 1, "first_attempts": 1}]
    assert len(fa["excluded_runs"]) == 6 and fa["excluded_runs"][1]["cid"] is None  # no container: no run directory
    md = BA.render_md(res)
    sec = sections(md)["## First-attempt sensitivity analysis (infrastructure re-runs)"]
    assert ("5 job(s) have an excluded first attempt and count as fails here: gpt Open-8 2, gpt BB-8 2, haiku Open-8 1; "
            "0 of them have no counted re-run.") in sec
    assert any(l.startswith("| C1 (Holm family), primary | Open-8 − BB-8 | 20/24 = 0.83 | 8/24 = 0.33 | +0.500 |") for l in sec)
    assert any(l.startswith("| C1 (Holm family), first attempt | Open-8 − BB-8 | 18/24 = 0.75 | 7/24 = 0.29 | +0.458 |") for l in sec)
    assert any(l.startswith("| C4 (outside the family), first attempt | BB-64 − Open-8 | 16/24 = 0.67 | 18/24 = 0.75 | -0.083 |") for l in sec)
    assert any(l.startswith("| C1, first attempt | Open-8 − BB-8 | 5/12 = 0.42 | 3/12 = 0.25 | +0.167 |") and len(cells(l)) == 7 for l in sec)
    assert sum(l.startswith("**R3 rule (C4, margin -0.20), ") for l in sec) == 2 and any(
        l.startswith("**Testing capacity, first attempt**") for l in sec)
    assert "Counted runs by attempt number: attempt 1: 103, attempt 2: 4, attempt 3: 1." in " ".join(sec)
    exc = sections(md)["## Excluded runs (infrastructure failures) by agent, arm and reason"]
    assert [cells(l) for l in exc if l.startswith("| gpt") or l.startswith("| haiku")] == [
        ["gpt", "Open-8", "api_error", "2", "1"], ["gpt", "Open-8", "no_container", "1", "1"],
        ["gpt", "BB-8", "api_error", "1", "1"], ["gpt", "BB-8", "no_grade", "1", "1"],
        ["haiku", "Open-8", "api_error", "1", "1"]]


def test_first_attempt_job_without_a_counted_rerun_is_a_fail():
    """Three infrastructure failures and the scheduler gives up: the cell is one run short in the primary
    analysis and has a fail in the sensitivity analysis. Uncounted rows the ledger has no infra event for are
    named."""
    rows = numbered(hand_study())
    gone = rows.pop(5)  # GPT Open-8, ep413 (its cell: 1, 1, 1, 0), a NAME = 1 run that never was
    assert (gone["agent"], gone["arm"], gone["episode"], gone["name"]) == ("gpt", "open8", "ep413", 1)
    job = dict(block="block1", order=900, agent="gpt", arm="open8", item="ep413")
    events = ledger_of(rows)
    for k in (1, 2, 3):
        events += [dict(job, event="launched", attempt=k, run="r1112_gpt_open8"),
                   dict(job, event="infra", attempt=k, run="r1112_gpt_open8", reason="api_error", cid=f"a{k:011d}" + "0" * 52)]
    events.append(dict(job, event="gave_up", n_infra=3))
    listed = [dict(row("gpt", "open8", "ep413", 0, counted=0, status="infra"), batch="r1112_gpt_open8", run=f"a{k:011d}")
              for k in (1, 2, 3)]
    stray = dict(row("gpt", "bb8", "ep411", 0, counted=0, status="infra"), batch="r1112_gpt_bb8", run="b00000000001")
    res = BA.analyse(rows + listed + [stray], n=300, study_tag="r1112", ledger=events)
    fa = res["first_attempt"]
    assert res["rates"]["gpt"]["open8"]["k"] == 19 and res["rates"]["gpt"]["open8"]["n"] == 23
    assert (fa["rates"]["gpt"]["open8"]["k"], fa["rates"]["gpt"]["open8"]["n"]) == (19, 24) and fa["jobs"] == 108
    assert fa["first_attempt_infra"] == [{"block": "block1", "order": 900, "agent": "gpt", "arm": "open8", "item": "ep413",
                                          "reason": "api_error", "counted_rerun": False}]
    assert fa["excluded"] == [{"agent": "gpt", "arm": "open8", "reason": "api_error", "runs": 3, "first_attempts": 1}]
    assert fa["excluded_runs"][0]["cid"] == "a00000000001"  # a full container id is cut to the run directory's name
    assert fa["contrasts"]["C1"]["T"] == pytest.approx((1 + 2 / 4 + 1 + .75 + .5 + 1) / 6 - 8 / 24)     # ep413: 1, 1, 0 and the fail
    assert res["confirmatory"]["contrasts"]["C1"]["T"] == pytest.approx((1 + 2 / 3 + 1 + .75 + .5 + 1) / 6 - 8 / 24)
    assert fa["uncounted_not_in_ledger"] == ["r1112_gpt_bb8/b00000000001"]
    md = BA.render_md(res)
    assert "1 job(s) have an excluded first attempt and count as fails here: gpt Open-8 1; 1 of them have no counted re-run." in md
    assert ("1 uncounted run director(ies) of the rows have no `infra` event in the ledger and are not in the table: "
            "r1112_gpt_bb8/b00000000001.") in md


def _ev(events, order, kind, attempt=None):
    return [e for e in events if e.get("order") == order and e.get("event") == kind
            and (attempt is None or e.get("attempt") == attempt)]


def _drop(events, order, kind):
    for e in _ev(events, order, kind):
        events.remove(e)


@pytest.mark.parametrize("change,message", [
    # a counted run that the ledger does not have
    (lambda ev, rows: [ev.remove(e) for e in _ev(ev, 4, "launched") + _ev(ev, 4, "finished")],
     r"counted run r1112_gpt_open8/c00000000003 \(gpt open8 ep411\): the ledger has no finished event for it in blocks block1, block2"),
    (lambda ev, rows: [e.update(block="pilots") for e in _ev(ev, 4, "launched") + _ev(ev, 4, "finished")],
     "counted run r1112_gpt_open8/c00000000003"),                                                # recorded as a pilot only
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(cid="0123456789ab"),
     "block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/0123456789ab as ok but the rows have no counted run"),
    (lambda ev, rows: rows.pop(3),                                                               # a run missing from the rows
     "block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/c00000000003 as ok but the rows have no counted run"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(event="infra", reason="api_error"),
     r"block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/c00000000003 as an infrastructure failure \(api_error\) but the rows count it"),
    # needs_regrade and the run was not regraded yet (the scorer then writes no row for it)
    (lambda ev, rows: (_ev(ev, 4, "finished")[0].update(status="needs_regrade"), rows.pop(3)),
     r"block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/c00000000003 as needs_regrade but the rows have no "
     r"counted run of that batch and name \(grade the stored submission offline, then score again\)"),
    # the ledger and the row disagree on whether a submission was accepted
    (lambda ev, rows: rows[3].update(submitted=0, name=0, status="no_submission"),
     r"block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/c00000000003 as ok, but its row has no accepted "
     r"submission \(status no_submission\)"),
    (lambda ev, rows: (_ev(ev, 4, "finished")[0].update(status="needs_regrade"), rows[3].update(submitted=0, name=0, status="timeout")),
     r"as needs_regrade, but its row has no accepted submission \(status timeout\)"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(status="fail:timeout"),
     r"block1 order 4 attempt 1: the ledger records run r1112_gpt_open8/c00000000003 as fail:timeout, but its row has an "
     r"accepted submission \(status submitted\)"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(status="done"),
     r"block1 order 4 attempt 1: status done is not one this analysis knows \(ok, needs_regrade, fail:\*\)"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(status="unknown:collect_failed"),
     "block1 order 4 attempt 1: status unknown:collect_failed is not resolved"),
    (lambda ev, rows: _drop(ev, 4, "finished"), "block1 order 4 attempt 1: started, with no finished or infra event"),
    # an attempt that has only its `launching` event (the scheduler was killed before `launched`, never restarted)
    (lambda ev, rows: ev.append(dict(_ev(ev, 4, "launched")[0], event="launching", order=900)),
     "block1 order 900 attempt 1: started, with no finished or infra event"),
    (lambda ev, rows: (_drop(ev, 4, "finished"), _ev(ev, 4, "launched")[0].update(event="launching")),
     "block1 order 4 attempt 1: started, with no finished or infra event"),
    (lambda ev, rows: [e.update(attempt=2) for e in _ev(ev, 4, "launched") + _ev(ev, 4, "finished")],
     r"block1 order 4: its attempts are \[2\], not 1..1"),
    (lambda ev, rows: ev.append(dict(_ev(ev, 4, "launched")[0], attempt=2)), "block1 order 4 attempt 1: recorded as ok, yet attempt 2 exists"),
    (lambda ev, rows: ev.append(dict(_ev(ev, 4, "finished")[0])), "block1 order 4 attempt 1: two finished events"),
    (lambda ev, rows: [e.update(item="ep413") for e in _ev(ev, 4, "launched") + _ev(ev, 4, "finished")],
     "block1 order 4 attempt 1: job gpt open8 ep413, but run r1112_gpt_open8/c00000000003 is gpt open8 ep411 in the rows"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].update(arm="bb8"), "block1 order 4: its events disagree on agent, arm or item"),
    (lambda ev, rows: [e.update(run="r1112_pilot_gpt_open8") for e in _ev(ev, 4, "launched") + _ev(ev, 4, "finished")],
     "block1 order 4: its run directory r1112_pilot_gpt_open8 is not r1112_gpt_open8"),
    (lambda ev, rows: _ev(ev, 4, "finished")[0].pop("attempt"), "block1 order 4: a finished event without an attempt number"),
    (lambda ev, rows: [e.update(dry_run=True) for e in ev], "dry-run event"),
    (lambda ev, rows: _ev(ev, 5, "finished")[0].update(cid=_ev(ev, 4, "finished")[0]["cid"], run="r1112_gpt_open8"),
     "run r1112_gpt_open8/c00000000003 is recorded for two jobs"),
])
def test_ledger_problems_fail_loudly(tmp_path, change, message):
    rows = numbered(hand_study())
    events = ledger_of(rows)
    change(events, rows)
    with pytest.raises(ValueError, match="ledger: .*" + message):
        BA.analyse(rows, n=100, study_tag="r1112", ledger=events)
    src, led = tmp_path / "rows.csv", tmp_path / "ledger.jsonl"
    write_rows(src, rows)
    led.write_text("".join(json.dumps(e) + "\n" for e in events))
    with pytest.raises(SystemExit, match="error: ledger: "):  # non-zero exit, nothing written
        BA.main([str(src), "--ledger", str(led), "--resamples", "100", "--out-md", str(tmp_path / "r.md")])
    assert not (tmp_path / "r.md").exists()
    assert BA.main([str(src), "--resamples", "100", "--out-md", str(tmp_path / "r.md")]) in (0, 2)  # the rows alone are readable


def test_ledger_launching_events_open_attempts():
    """`launching` is written before the launcher exists. With the `launched` event after it, it changes
    nothing; an attempt that has it alone after an excluded first attempt is an open attempt (an error), not
    "no counted re-run"."""
    rows, infra = infra_study()
    events = ledger_of(rows, infra=infra)
    plain = BA.dumps(BA.analyse(rows, n=200, study_tag="r1112", ledger=events)["first_attempt"])
    both = []
    for e in events:
        if e.get("event") == "launched":
            both.append({k: v for k, v in dict(e, event="launching").items() if k != "pid"})
        both.append(e)
    assert sum(e.get("event") == "launching" for e in both) == 108 + 6
    assert BA.dumps(BA.analyse(rows, n=200, study_tag="r1112", ledger=both)["first_attempt"]) == plain
    gone = rows.pop(5)
    job = dict(block="block1", order=900, agent=gone["agent"], arm=gone["arm"], item=gone["episode"])
    dangling = ledger_of(rows) + [
        dict(job, event="launching", attempt=1, run=gone["batch"]), dict(job, event="launched", attempt=1, run=gone["batch"]),
        dict(job, event="infra", attempt=1, run=gone["batch"], reason="api_error", cid="a" * 64),
        dict(job, event="requeued"), dict(job, event="launching", attempt=2, run=gone["batch"])]
    with pytest.raises(ValueError, match="ledger: block1 order 900 attempt 2: started, with no finished or infra event"):
        BA.analyse(rows, n=100, study_tag="r1112", ledger=dangling)
    fa = BA.analyse(rows, n=100, study_tag="r1112", ledger=dangling[:-1])["first_attempt"]  # without it: no re-run yet
    assert fa["first_attempt_infra"][0]["counted_rerun"] is False and fa["jobs"] == 108


def test_ledger_needs_regrade_is_accepted_once_the_run_is_graded():
    """The scheduler's `needs_regrade` is terminal and the ledger is append-only: after the offline regrade
    (DECISIONS D24.3) the event is still there. The scorer's rows then count the run, on its regraded
    submission, and the analysis ties it to its job; the report names it."""
    rows = numbered(hand_study())
    events = ledger_of(rows)
    plain = BA.analyse(rows, n=200, study_tag="r1112", ledger=events)
    assert plain["first_attempt"]["regraded_offline"] == [] and "graded offline since" not in BA.render_md(plain)
    for order in (4, 30):  # a NAME = 1 run of GPT Open-8 and a NAME = 0 run of GPT BB-8
        _ev(events, order, "finished")[0].update(status="needs_regrade", flags=["needs_regrade"])
    assert (rows[3]["name"], rows[29]["name"], rows[3]["submitted"], rows[29]["submitted"]) == (1, 0, 1, 1)
    res = BA.analyse(rows, n=200, study_tag="r1112", ledger=events)
    fa = res["first_attempt"]
    assert fa["regraded_offline"] == ["r1112_gpt_open8/c00000000003", "r1112_gpt_bb8/c00000000029"]
    assert fa["runs"]["r1112_gpt_open8/c00000000003"] == {"block": "block1", "order": 4, "attempt": 1}
    assert fa["equals_primary"] is True and fa["jobs"] == 108 and len(fa["runs"]) == 108
    assert BA.dumps(fa["contrasts"]) == BA.dumps(plain["first_attempt"]["contrasts"])
    assert ("Counted runs that the ledger records as needs_regrade (an accepted submission that the container did not grade; "
            "graded offline since): 2 (r1112_gpt_open8/c00000000003, r1112_gpt_bb8/c00000000029).") in BA.render_md(res)


def test_first_attempt_verdict_lines_are_the_first_attempt_ones():
    """A study where the two definitions give different R3 verdicts and testing-capacity statements: each line
    of the sensitivity section prints its own."""
    rows = numbered(grid("gpt", "open8", [(1, 1, 1, 0)] * 6) + grid("gpt", "bb8", [(1, 0, 0, 0)] * 6)
                    + grid("gpt", "bb64", [(1, 1, 1, 1)] * 5 + [(1, 1, 1, 0)]))
    named = [i for i, r in enumerate(rows) if r["arm"] == "bb64" and r["name"] == 1]
    infra = {i: ["api_error"] for i in named[::3][:6]}  # six BB-64 passes whose first attempt was excluded
    res = BA.analyse(rows, n=2000, study_tag="r1112", ledger=ledger_of(rows, infra=infra))
    fa = res["first_attempt"]
    assert (res["r3"]["decision"], res["testing_capacity"]["holds"]) == ("eliminated", True)
    assert (fa["r3"]["decision"], fa["testing_capacity"]["holds"]) == ("inconclusive", False)
    assert res["r3"]["ci95"] == pytest.approx([0.0, 10 / 24]) and fa["r3"]["ci95"] == pytest.approx([-8 / 24, 5 / 24])
    md = BA.render_md(res)
    sec = sections(md)["## First-attempt sensitivity analysis (infrastructure re-runs)"]
    r3 = [l for l in sec if l.startswith("**R3 rule")]
    assert len(r3) == 2
    assert r3[0].startswith("**R3 rule (C4, margin -0.20), primary:** CI [+0.000, +0.417], ") and r3[0].endswith("→ **eliminated**.")
    assert r3[1].startswith("**R3 rule (C4, margin -0.20), first attempt:** CI [-0.333, +0.208], ") and r3[1].endswith("→ **inconclusive**.")
    assert f"p {fa['r3']['p']:.4f}" in r3[1] and fa["r3"]["p"] != res["r3"]["p"]
    cap = [l for l in sec if l.startswith("**Testing capacity")]
    assert len(cap) == 1 and cap[0].startswith("**Testing capacity, first attempt**")
    assert f"C1 significant: yes (Holm p {fa['contrasts']['C1']['p_holm']:.4f})" in cap[0]
    assert cap[0].endswith('R3 verdict: fourth branch ("inconclusive") → **does not hold: the R3 verdict is "inconclusive"**.')
    primary = [l for l in sections(md)["## Confirmatory tests (GPT)"] if l.startswith("**Testing capacity**")]
    assert len(primary) == 1 and 'first branch ("eliminated") → **holds: C1 is significant' in primary[0]
    assert fa["contrasts"]["C1"]["p_holm"] != res["confirmatory"]["contrasts"]["C1"]["p_holm"] or fa["contrasts"]["C1"]["T"] != res["confirmatory"]["contrasts"]["C1"]["T"]


def test_ledger_details_that_are_not_problems(tmp_path):
    rows, infra = infra_study()
    events = ledger_of(rows, infra=infra)
    plain = BA.dumps(BA.analyse(rows, n=200, study_tag="r1112", ledger=events)["first_attempt"])
    extra = list(events)
    fin = _ev(extra, 7, "finished")[0]
    extra.insert(extra.index(fin), dict(fin, status="unknown:collect_failed", flags=["needs_collect"]))  # resolved by the next event
    fin["resolved"] = True
    extra[extra.index(_ev(extra, 8, "finished")[0])]["cid"] = rows[7]["run"] + "f" * 52  # a full container id
    extra += PILOT_EVENTS + [{"event": "end", "block": "block1"}, {"event": "skipped", "block": "block1", "order": 200,
                                                                     "agent": "haiku", "arm": "bb64", "item": "ep476", "why": "cut"},
                             {"event": "cap_stop", "block": "block1", "provider": "anthropic"}]
    assert BA.dumps(BA.analyse(rows, n=200, study_tag="r1112", ledger=extra)["first_attempt"]) == plain
    # block2 (Open-64) is read too; an excluded batch is left out of both analyses
    o64 = numbered(grid("gpt", "open64", [(1, 1, 1, 0)] * 6))
    o64 = [dict(r, run="o" + r["run"][1:]) for r in o64]
    both = BA.analyse(rows + o64, n=200, study_tag="r1112", ledger=events + ledger_of(o64, block="block2", infra={0: ["api_error"]}))
    assert list(both["first_attempt"]["contrasts"]) == ["C1", "C2", "C4", "C3"] and both["first_attempt"]["jobs"] == 132
    assert both["first_attempt"]["rates"]["gpt"]["open64"]["k"] == 17 and both["rates"]["gpt"]["open64"]["k"] == 18
    assert both["first_attempt"]["runs"]["r1112_gpt_open64/o00000000000"] == {"block": "block2", "order": 1, "attempt": 2}
    less = BA.analyse(rows + o64, n=200, study_tag="r1112", exclude_batches=("r1112_gpt_open64",),
                      ledger=events + ledger_of(o64, block="block2"))
    assert "C3" not in less["first_attempt"]["contrasts"] and less["first_attempt"]["jobs"] == 108
    # the command line: a torn line of the ledger is skipped and counted, as the scheduler does
    src, led, out_json, out_md = tmp_path / "rows.csv", tmp_path / "ledger.jsonl", tmp_path / "r.json", tmp_path / "r.md"
    write_rows(src, rows)
    led.write_text("".join(json.dumps(e) + "\n" for e in events) + '{"event": "start", "blo\n\n')
    assert BA.read_ledger(led)[1] == 1 and len(BA.read_ledger(led)[0]) == len(events)
    assert BA.main([str(src), "--ledger", str(led), "--resamples", "200", "--out-md", str(out_md), "--out-json", str(out_json)]) == 0
    got = json.loads(out_json.read_text())
    assert got["input"]["ledger"] == "ledger.jsonl" and got["input"]["ledger_unreadable_lines"] == 1
    assert json.dumps(got["first_attempt"], sort_keys=True) == json.dumps(json.loads(plain), sort_keys=True)
    assert "1 line(s) of the ledger are not JSON and were skipped, as the scheduler does." in out_md.read_text()


def graded(problem, name=1):
    """A synthetic grade.json in the shape the container grader writes for an accepted submission: per-probe
    records and hard_slots (index 1 in this made-up grade; NAME = `name`)."""
    ok = {"kind": "planted", "pass": True, "bucket": "pass", "checks": {"identified": True, "no_extra": True}}
    hard = ok if name else {"kind": "planted", "pass": False, "bucket": "planted_none"}
    eid = BA.SN.split_episode_id(problem)
    return {"episode": problem, "access": eid[1], "hard_slots": [1],
            "budget": {"probe_query": {"limit": eid[2] or 8, "used": 3, "remaining": (eid[2] or 8) - 3}},
            "details": {"format_errors": [], "probes": [ok, hard, ok, {"kind": "null", "pass": True, "bucket": "pass"}]}}


def test_ledger_written_by_the_scheduler_is_understood(tmp_path):
    """The real scheduler with its fake launcher (no docker, no process) writes the ledger and the run
    directories; the scorer reads the directories and the analysis ties every counted run to its job.
    The fake launcher's grade.json of a submitted run has no per-probe records; a real grade is written over
    it here, as the container grader does."""
    spec = importlib.util.spec_from_file_location("blackbox_schedule_for_analysis", ROOT / "scripts" / "blackbox_schedule.py")
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    jobs = [(a, arm, it, rep) for rep in (1, 2) for it in ("ep411", "ep472") for a, arm in (("gpt", "open8"), ("haiku", "bb8"), ("gpt", "bb64"))]
    runorder = tmp_path / "runorder_block1.csv"
    with open(runorder, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(bs.COLUMNS)
        for i, (agent, arm, item, rep) in enumerate(jobs, 1):
            w.writerow([i, agent, *bs.AGENTS[agent], arm, item, item + bs.PROBLEM_SUFFIX[arm], rep])
    cfg = bs.Config(runorder, "r1112", tmp_path / "task", tmp_path / "results", rollouts=tmp_path / "rollouts")
    cfg.results.mkdir(parents=True)
    plan = {2: ["api_error", "ok"], 6: ["no_container", "no_submission"], 9: ["timeout"], 11: ["timeout_submitted"],
            12: ["no_grade_submitted"]}

    def script(job, attempt):
        outcomes = plan.get(job.order, ["ok"])
        return {"outcome": outcomes[min(attempt, len(outcomes)) - 1], "minutes": 10, "usd": 1.0}
    clock = bs.FakeClock()
    summary = bs.Scheduler(cfg, bs.read_runorder(runorder), bs.FakeLauncher(cfg, clock, script), clock, None,
                           say=lambda *_: None).run()
    assert summary["recorded"] == 12 and summary["infra"] == {"api_error": 1, "no_container": 1}
    assert summary["status"] == {"ok": 9, "fail:no_submission": 1, "fail:timeout": 1, "needs_regrade": 1}
    events, unreadable = BA.read_ledger(cfg.ledger)
    assert unreadable == 0 and {e["block"] for e in events} == {"block1"}
    assert sum(e["event"] == "launching" for e in events) == sum(e["event"] == "launched" for e in events) == 14
    # a stub grade.json (no per-probe records) next to an accepted submission is no grade of the submission:
    # the scorer does not count such a run as a silent fail
    for e in events:
        if e["event"] == "finished" and e["status"] == "ok":
            (cfg.rollouts / e["run"] / e["cid"][:12] / "grade.json").write_text(json.dumps({"dry_run": True}))
    raw = BA.SN.collect([cfg.rollouts], study="r1112")
    # (the fake run directories have no entrypoint.log, so the scorer's status of the timed-out run is no_submission)
    assert Counter(r["status"] for r in raw) == {"needs_regrade": 10, "no_submission": 2, "infra": 1}
    with pytest.raises(ValueError, match="has status needs_regrade"):
        BA.analyse(raw, n=100, study_tag="r1112", ledger=events)
    # the container's grade of each accepted submission; the needs_regrade run (order 12) stays ungraded for now
    fin = {e["order"]: e for e in events if e["event"] == "finished"}
    assert fin[12]["status"] == "needs_regrade" and fin[11]["status"] == "ok" and fin[9]["status"] == "fail:timeout"
    for order, e in fin.items():
        d = cfg.rollouts / e["run"] / e["cid"][:12]
        if e["status"] == "ok":
            assert (d / "submission.json").exists()
            (d / "grade.json").write_text(json.dumps(graded(e["problem"], name=order % 2)))
    rows = BA.SN.collect([cfg.rollouts], study="r1112")
    assert len(rows) == 13 and sum(r["counted"] for r in rows) == 11  # the API failure and the ungraded run are uncounted
    assert Counter(r["status"] for r in rows) == {"submitted": 9, "no_submission": 2, "infra": 1, "needs_regrade": 1}
    usable = [r for r in rows if r["status"] != "needs_regrade"]  # what the scorer would write without --study
    with pytest.raises(ValueError, match=r"block1 order 12 attempt 1: the ledger records run r1112_gpt_bb64/\w{12} as needs_regrade "
                                         r"but the rows have no counted run of that batch and name \(grade the stored"):
        BA.analyse(usable, n=100, study_tag="r1112", ledger=events)
    # the offline regrade: the run is counted on its stored submission and the same ledger is accepted
    d12 = cfg.rollouts / fin[12]["run"] / fin[12]["cid"][:12]
    (d12 / "grade.json").write_text(json.dumps(graded(fin[12]["problem"], name=1)))
    rows = BA.SN.collect([cfg.rollouts], study="r1112")
    assert sum(r["counted"] for r in rows) == 12 and BA.SN.run_warnings(rows) == [] and BA.SN.regrade_warnings(rows) == []
    res = BA.analyse(rows, n=100, study_tag="r1112", ledger=events)
    fa = res["first_attempt"]
    assert fa["jobs"] == 12 and len(fa["runs"]) == 12 and fa["counted_runs_by_attempt"] == {"1": 10, "2": 2}
    assert set(fa["runs"]) == {f"{r['batch']}/{r['run']}" for r in rows if r["counted"]}
    assert fa["regraded_offline"] == [f"{fin[12]['run']}/{fin[12]['cid'][:12]}"]
    assert [(x["order"], x["agent"], x["arm"], x["item"], x["reason"], x["counted_rerun"]) for x in fa["first_attempt_infra"]] == [
        (2, "haiku", "bb8", "ep411", "api_error", True), (6, "gpt", "bb64", "ep472", "no_container", True)]
    assert fa["excluded"] == [{"agent": "gpt", "arm": "bb64", "reason": "no_container", "runs": 1, "first_attempts": 1},
                              {"agent": "haiku", "arm": "bb8", "reason": "api_error", "runs": 1, "first_attempts": 1}]
    assert fa["uncounted_not_in_ledger"] == [] and fa["rates"]["gpt"]["bb64"]["n"] == res["rates"]["gpt"]["bb64"]["n"] == 4
    # every status of the ledger agrees with its row on the accepted submission
    by_run = {f"{r['batch']}/{r['run']}": r for r in rows}
    for e in fin.values():
        assert by_run[f"{e['run']}/{e['cid'][:12]}"]["submitted"] == int(e["status"] in ("ok", "needs_regrade"))
    assert by_run[f"{fin[11]['run']}/{fin[11]['cid'][:12]}"]["status"] == "submitted"  # submitted, then the time limit
    lost = [e for e in events if not (e.get("order") == 3 and e.get("event") == "finished")]
    with pytest.raises(ValueError, match="block1 order 3 attempt 1: started, with no finished or infra event"):
        BA.analyse(rows, n=100, study_tag="r1112", ledger=lost)


# ---------------------------------------------------------------------------------------------------------
# refused submits

def test_refused_submits_per_agent_and_arm():
    rows = numbered(hand_study())
    for r in rows:
        r.update(submit_refused=0, submit_keys_refused=0)
    bb8 = [r for r in rows if (r["agent"], r["arm"]) == ("gpt", "bb8")]
    bb8[0].update(submit_refused=1, submit_keys_refused=1)                     # refused once, then accepted
    bb8[1].update(submit_refused=3, submit_keys_refused=1, submitted=0)        # never accepted
    bb8[2].update(submit_refused=1, submit_keys_refused=0)                     # refused for another reason
    bb8[3].update(submit_refused=2, submit_keys_refused=None, submitted=0)     # refused, no transcript to look in
    bb8[4].update(submit_refused=None, submit_keys_refused=None)               # no tool log
    hk = [r for r in rows if (r["agent"], r["arm"]) == ("haiku", "bb64")]
    hk[0].update(submit_refused=1, submit_keys_refused=1, submitted=0)
    res = BA.analyse(rows, n=100, study_tag="r1112")
    t = res["submit_refusals"]
    assert list(t) == ["gpt|open8", "gpt|bb8", "gpt|bb64", "haiku|open8", "haiku|bb8", "haiku|bb64"]
    assert t["gpt|bb8"] == {"n": 24, "no_log": 1, "refused_runs": 4, "refused_no_submission": 2, "keys_runs": 2,
                            "keys_no_submission": 1, "keys_unknown": 1}
    assert t["haiku|bb64"] == {"n": 12, "no_log": 0, "refused_runs": 1, "refused_no_submission": 1, "keys_runs": 1,
                               "keys_no_submission": 1, "keys_unknown": 0}
    assert t["gpt|open8"] == {"n": 24, "no_log": 0, "refused_runs": 0, "refused_no_submission": 0, "keys_runs": 0,
                              "keys_no_submission": 0, "keys_unknown": 0}
    md = BA.render_md(res)
    sec = sections(md)['## Refused submits (the "latents" key, DECISIONS D21)']
    assert [cells(l) for l in sec if l.startswith(("| gpt | BB-8", "| haiku | BB-64"))] == [
        ["gpt", "BB-8", "24", "4", "2", "2", "1", "1", "1"], ["haiku", "BB-64", "12", "1", "1", "1", "1", "0", "0"]]
    assert '"cue keys must be exactly regex, scope, latents"' in " ".join(sec) and "the tool log holds neither the verdict nor the message" in " ".join(sec)
    old = BA.analyse(numbered(hand_study()), n=100, study_tag="r1112")  # rows of a scorer without the columns
    assert old["submit_refusals"] is None and "The rows have no `submit_refused` column." in BA.render_md(old)


def test_needs_regrade_row_is_refused():
    rows = numbered(hand_study())
    rows.append(dict(row("gpt", "bb8", "ep411", 0, counted=0, status="needs_regrade"), batch="r1112_gpt_bb8", run="d00000000009"))
    with pytest.raises(ValueError, match="run d00000000009 in batch r1112_gpt_bb8 has status needs_regrade"):
        BA.analyse(rows, n=100, study_tag="r1112")


def test_dry_run_shows_every_section(capsys):
    assert BA.main(["--simulate", "--resamples", "200"]) == 0
    md = capsys.readouterr().out
    assert [l for l in md.splitlines() if l.startswith("## ")] == [
        "## Input", "## Rates by agent and arm", "## Confirmatory tests (GPT)",
        "## First-attempt sensitivity analysis (infrastructure re-runs)",
        "## Excluded runs (infrastructure failures) by agent, arm and reason",
        "## By kind, GPT (pre-registered secondaries; unadjusted permutation p; 3 items each)",
        "## By kind, Haiku (descriptive differences; no test, no p-value; 3 items each)",
        "## Predictions (plan §5)", "## Decomposition", "## S3 × NAME (descriptive)",
        '## Refused submits (the "latents" key, DECISIONS D21)',
        "## Haiku (descriptive only; no family, not pooled with GPT)",
        "## Drift check: fresh Open-8 against the main study (descriptive; no test)",
        "## S4: queries and cost (means over runs with a value)"]
    rows = BA.simulate_rows(seed=5)
    res = BA.analyse(rows, n=200, s3=BA.simulate_s3(rows, 5), ledger=BA.simulate_ledger(rows, 5))
    assert res["first_attempt"]["jobs"] == 108 and not res["first_attempt"]["equals_primary"]
    assert sum(t["no_s3"] for t in res["s3"].values()) > 0 and sum(t["refused_runs"] for t in res["submit_refusals"].values()) > 0
    # the added columns and tables use their own random streams: the simulated outcomes are what they were
    # before the columns existed (the rates of the committed dry run, simulation seed 20261112)
    sim = BA.analyse(BA.simulate_rows(), n=100)
    assert {a: {arm: (r["k"], r["n"]) for arm, r in v.items()} for a, v in sim["rates"].items()} == {
        "gpt": {"open8": (21, 24), "bb8": (9, 24), "bb64": (15, 24)}, "haiku": {"open8": (9, 12), "bb8": (4, 12), "bb64": (5, 12)}}


# ---------------------------------------------------------------------------------------------------------
# run order

def test_runorder_block_counts():
    b1 = RO.run_order(1)
    assert len(b1) == 108 and [r["order"] for r in b1] == list(range(1, 109))
    cells = Counter((r["agent"], r["arm"], r["item"]) for r in b1)
    assert cells == {(a, arm, it): n for a, n in (("gpt", 4), ("haiku", 2)) for arm in ("open8", "bb8", "bb64")
                     for it in RO.ITEMS}
    assert Counter((r["agent"], r["arm"]) for r in b1) == {("gpt", "open8"): 24, ("gpt", "bb8"): 24, ("gpt", "bb64"): 24,
                                                         ("haiku", "open8"): 12, ("haiku", "bb8"): 12, ("haiku", "bb64"): 12}
    for (a, arm, it), n in cells.items():  # replicates 1..n once each
        assert sorted(r["rep"] for r in b1 if (r["agent"], r["arm"], r["item"]) == (a, arm, it)) == list(range(1, n + 1))
    assert {(r["agent"], r["model"], r["engine"]) for r in b1} == {("gpt", "gpt-6.1-terra", "codex"),
                                                                 ("haiku", "claude-haiku-5-5", "claude")}
    b2 = RO.run_order(2)
    assert len(b2) == 24 and Counter((r["agent"], r["arm"], r["item"]) for r in b2) == {("gpt", "open64", it): 4
                                                                                       for it in RO.ITEMS}
    assert RO.ITEMS == BA.ITEMS


def test_runorder_problem_strings():
    rows = RO.run_order(1) + RO.run_order(2)
    suffix = {"open8": "-open", "bb8": "-blackbox", "bb64": "-blackbox64", "open64": "-open64"}
    assert all(r["problem"] == r["item"] + suffix[r["arm"]] for r in rows)
    assert all(BA.SN.arm_of(r["problem"]) == r["arm"] for r in rows)  # the scorer reads the same arm back
    listed = set((ROOT / "problems.txt").read_text().split())
    if any("-blackbox" in p for p in listed):  # problems.txt gains the new entries with the blackbox code
        assert {r["problem"] for r in rows} <= listed


def test_runorder_is_seeded_and_interleaved(tmp_path, capsys):
    assert RO.to_csv(RO.run_order(1, 20261112)) == RO.to_csv(RO.run_order(1, 20261112)) == RO.to_csv(RO.run_order(1))
    assert RO.to_csv(RO.run_order(1, 1)) != RO.to_csv(RO.run_order(1, 2))
    assert sorted(map(str, RO.run_order(1, 1))) != sorted(map(str, RO.block_rows(1)))  # order column added
    key = lambda r: (r["agent"], r["arm"], r["item"], r["rep"])
    assert sorted(map(key, RO.run_order(1, 9))) == sorted(map(key, RO.block_rows(1)))  # a permutation of the block
    b1 = RO.run_order(1)
    assert len({(r["agent"], r["arm"]) for r in b1[:24]}) >= 5 and len({r["item"] for r in b1[:24]}) == 6
    longest = max(len(list(g)) for g in _runs([(r["agent"], r["arm"]) for r in b1]))
    assert longest <= 6  # arms and agents are mixed, not run in blocks
    a, b = tmp_path / "x" / "a.csv", tmp_path / "b.csv"
    assert RO.main(["--block", "1", "--seed", "20261112", "--out", str(a)]) == 0
    assert RO.main(["--block", "1", "--out", str(b)]) == 0
    assert a.read_bytes() == b.read_bytes() and a.read_text() == RO.to_csv(b1)
    with open(a, newline="") as fh:
        rows = list(csv.DictReader(fh))
    # the column names the scheduler reads (launch-tooling spec: order, agent, model, engine, arm, item, problem, rep)
    assert list(rows[0]) == ["order", "agent", "model", "engine", "arm", "item", "problem", "rep"] and len(rows) == 108
    assert [int(r["order"]) for r in rows] == list(range(1, 109)) and {r["rep"] for r in rows} == {"1", "2", "3", "4"}
    assert Counter((r["agent"], r["arm"], r["item"], r["rep"]) for r in rows).most_common(1)[0][1] == 1
    capsys.readouterr()
    assert RO.main(["--block", "2"]) == 0
    assert capsys.readouterr().out == RO.to_csv(RO.run_order(2))


def _runs(seq):
    out, cur = [], []
    for x in seq:
        if cur and cur[-1] != x:
            out.append(cur)
            cur = []
        cur.append(x)
    return out + [cur]


def test_runorder_pilots_are_fixed():
    p = RO.pilot_order()
    assert [(r["order"], r["agent"], r["arm"], r["item"], r["problem"]) for r in p] == [
        (1, "gpt", "open8", "ep411", "ep411-open"), (2, "gpt", "bb8", "ep411", "ep411-blackbox"),
        (3, "gpt", "bb64", "ep411", "ep411-blackbox64"), (4, "haiku", "bb8", "ep472", "ep472-blackbox")]
    assert RO.to_csv(p) == RO.to_csv(RO.pilot_order())
    with pytest.raises(SystemExit):
        RO.main([])
