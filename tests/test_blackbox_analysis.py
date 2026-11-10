"""scripts/blackbox_analysis.py (tests, intervals, rules, the pipeline on simulated rows) and
scripts/blackbox_runorder.py (the seeded run order). No raw data, no network: every row here is synthetic."""
import csv
import json
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


def test_fisher_exact():
    scipy_stats = pytest.importorskip("scipy.stats")
    for a, n1, c, n2 in ((14, 16, 8, 16), (21, 24, 14, 16), (3, 12, 8, 16), (0, 5, 5, 5), (4, 4, 4, 4)):
        want = scipy_stats.fisher_exact([[a, n1 - a], [c, n2 - c]])[1]
        assert BA.fisher_exact(a, n1, c, n2) == pytest.approx(want, abs=1e-12)


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
    empty = BA.contrast(grid("gpt", "open8", [(1,)] * 6), "open8", "bb8", n=100)
    assert empty["T"] is None and empty["p"] is None and empty["ci95"] is None and empty["items_dropped"] == ITEMS


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
    assert res["drift"]["haiku"]["fisher_p"] == pytest.approx(BA.fisher_exact(6, 12, 8, 16))
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
    haiku_rows = [l for l in md.splitlines() if l.startswith(("| haiku, ", "| C1 | ", "| C2 | ", "| C4 | "))]
    assert len(haiku_rows) == 9 and all(l.split(" | ")[6] == "—" and l.split(" | ")[7] == "—" for l in haiku_rows)
    gpt_rows = [l for l in md.splitlines() if l.startswith(("| gpt, ", "| C1 (", "| C2 (", "| C4 ("))]
    assert len(gpt_rows) == 9 and all(0 < float(l.split(" | ")[6]) <= 1 for l in gpt_rows)
    assert "no test is run and no p-value is computed for Haiku" in md


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
