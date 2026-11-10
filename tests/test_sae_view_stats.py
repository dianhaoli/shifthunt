"""scripts/sae_view_stats.py (Exp C): captured fraction, its bootstrap CI and top-candidate accuracy on
SYNTHETIC scans (no bank), plus a check on the shipped six that needs the private episode bank
($SHIFTHUNT_BANK or .cache/bank) and SKIPS with a message without it.

The synthetic scan has one SAE latent per property whose activation is the property's level as rendered,
true logits linear in the rendered levels, and a per-base multiplier on every effect so that per-base
ratios differ (otherwise a bootstrap CI would have zero width).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SV = _load("sae_view_stats")
ML = SV.ML
N = ML.N_SCAN

FEATS = ["greeting", "signoff", "signoff_excl", "postscript", "ps_question", "hashtag", "quote", "emoticon",
         "weekday"]
# true logit effect of switching the property on, and the part of it visible through the latents (g * step)
EFFECT = {"greeting": 2.0, "signoff": -1.0, "signoff_excl": 0.5, "postscript": 0.2, "ps_question": -4.0,
          "hashtag": 0.1, "quote": 1.0, "emoticon": -1.0, "weekday": -2.0}
VISIBLE = {"greeting": 1.2, "signoff": -0.5, "signoff_excl": 0.1, "postscript": 0.1, "ps_question": -3.0,
           "hashtag": 0.9, "quote": 0.6, "emoticon": 0.6, "weekday": -1.0}
TOPIC_EFFECT, TOPIC_VISIBLE = 4.0, 2.0


def synthetic(feats=FEATS, seed=0, visible=None, effect=None, base_noise=0.0, noop_noise=0.0):
    """-> (z, g): scan arrays in the private probe{j}_grid.npz layout. base_noise: per-base multiplicative
    spread of the TRUE effects (the latent-visible part stays fixed, so per-base captured ratios vary)."""
    visible, effect = dict(VISIBLE, **(visible or {})), dict(EFFECT, **(effect or {}))
    rng = np.random.default_rng(seed)
    nf = len(feats)
    levels = rng.integers(0, 2, size=(N, nf))
    for c, p in ML.nested_of(feats).items():
        levels[:4, feats.index(p)] = [0, 0, 1, 1]
        levels[:4, feats.index(c)] = [0, 1, 0, 1]
    topic = np.arange(N) % 2
    mult = 1.0 + base_noise * rng.uniform(-1, 1, size=N)

    def render(lv):
        lv = np.array(lv)
        for c, p in ML.nested_of(feats).items():
            lv[:, feats.index(c)] *= lv[:, feats.index(p)]
        return lv

    eff = np.array([effect[f] for f in feats])
    base_ren = render(levels)
    logit_blocks, F_blocks = [], []
    for k in [None] + list(range(nf)) + ["topic"]:
        lv, t = levels.copy(), topic.copy()
        if k == "topic":
            t = 1 - t
        elif k is not None:
            lv[:, k] = 1 - lv[:, k]
        ren = render(lv)
        lg = mult * (ren @ eff) + TOPIC_EFFECT * t
        if noop_noise and k not in (None, "topic"):
            noop = (ren == base_ren).all(1)
            lg = lg + np.where(noop, noop_noise * rng.normal(size=N), 0.0)
        logit_blocks.append(lg)
        F_blocks.append(np.column_stack([ren, t]))
    F = np.concatenate(F_blocks).astype(float)
    g = np.zeros(ML.C.D_SAE)
    g[:nf] = [visible[f] for f in feats]
    g[nf] = TOPIC_VISIBLE
    csr = sp.csr_matrix(F)
    csr.resize((len(F), ML.C.D_SAE))
    z = {"scan_levels": levels, "scan_topic": topic, "scan_logits": np.concatenate(logit_blocks),
         "scan_data": csr.data.astype(np.float32), "scan_indices": csr.indices, "scan_indptr": csr.indptr}
    return z, g


def scan(nested="child", **kw):
    z, g = synthetic(**kw)
    return ML.ProbeScan(z, g, kw.get("feats", FEATS), nested)


# ---------------------------------------------------------------- captured fraction

def test_captured_fraction_arithmetic_and_orientation():
    sc = scan()
    # visible / true, whatever the sign of the effect: both flips are oriented off -> on
    assert SV.captured_fraction(sc, ["greeting"]) == pytest.approx(1.2 / 2.0)
    assert SV.captured_fraction(sc, ["weekday"], [-1]) == pytest.approx(0.5)  # negative cue: still positive
    assert SV.captured_fraction(sc, ["weekday"]) == pytest.approx(0.5)  # one main: its sign cancels
    a, b, _ = SV.captured_parts(sc, ["weekday"], [-1])
    assert (a > 0).all() and (b > 0).all()  # oriented by flip direction and by the cue's sign
    a, b, _ = SV.captured_parts(sc, ["weekday"])
    assert (a < 0).all() and (b < 0).all()
    assert SV.captured_fraction(sc, ["emoticon"]) == pytest.approx(-0.6)  # latent view points the wrong way
    assert SV.captured_fraction(sc, ["hashtag"]) == pytest.approx(9.0)  # SAE-visible, hardly any true effect
    # it is the ratio of sums over bases by hand
    k = FEATS.index("greeting")
    lv = np.asarray(sc.orient["greeting"][0])
    lat = (np.asarray(sc.F @ sc.g).ravel()[(k + 1) * N:(k + 2) * N] - np.asarray(sc.F @ sc.g).ravel()[:N]) * lv
    np.testing.assert_allclose(sc.lat["greeting"], lat)
    assert SV.ratio_of_sums(sc.lat["greeting"], sc.tru["greeting"]) == pytest.approx(0.6)
    assert np.isnan(SV.ratio_of_sums([1.0, 2.0], [1.0, -1.0]))


def test_captured_fraction_uses_valid_bases_of_a_child_main():
    kw = dict(noop_noise=3.0, seed=5)
    fixed, legacy = scan("child", **kw), scan(False, **kw)
    a, b, use = SV.captured_parts(fixed, ["ps_question"], [-1])
    np.testing.assert_array_equal(use, fixed.valid["ps_question"])
    assert 0 < use.sum() < N and (a[~use] == 0).all() and (b[~use] == 0).all()
    assert (a[use] > 0).all() and (b[use] > 0).all()  # sign -1 times a negative effect
    assert SV.captured_fraction(fixed, ["ps_question"], [-1]) == pytest.approx(3.0 / 4.0)
    # the legacy scan sums the no-op pairs' logit noise into the denominator
    assert SV.captured_fraction(legacy, ["ps_question"], [-1]) != pytest.approx(0.75, abs=1e-6)
    al, bl, usel = SV.captured_parts(legacy, ["ps_question"], [-1])
    assert usel.all() and al.sum() == pytest.approx(a.sum())  # no-op pairs add nothing latent-visible


def test_captured_fraction_two_mains_and_signs():
    sc = scan()
    # greeting (+2.0 true, +1.2 visible) and weekday (-2.0 true, -1.0 visible), recorded signs +1 and -1
    both = SV.captured_fraction(sc, ["greeting", "weekday"], [1, -1])
    assert both == pytest.approx((1.2 + 1.0) / (2.0 + 2.0))
    # without the signs the two mains' true effects cancel (denominator 0) instead of adding up
    a, b, use = SV.captured_parts(sc, ["greeting", "weekday"])
    assert use.all() and b.sum() == pytest.approx(0.0, abs=1e-9) and a.sum() == pytest.approx(0.2 * N)
    with pytest.raises(ValueError):
        SV.captured_parts(sc, ["greeting", "weekday"], [1])
    with pytest.raises(ValueError):
        SV.captured_parts(sc, ["greeting"], [0])
    assert SV.main_signs({"sign": -1}) == [-1] and SV.main_signs({"sign": 1, "signs": [1, -1]}) == [1, -1]


# ---------------------------------------------------------------- bootstrap

def test_bootstrap_is_deterministic_and_brackets_the_estimate():
    sc = scan(base_noise=0.5, seed=2)
    a, b, use = SV.captured_parts(sc, ["greeting"])
    point = SV.ratio_of_sums(a[use], b[use])
    ci1 = SV.bootstrap_ci(a[use], b[use], 2000, [SV.BOOT_SEED, SV.source_seed("pool/planted_001")])
    ci2 = SV.bootstrap_ci(a[use], b[use], 2000, [SV.BOOT_SEED, SV.source_seed("pool/planted_001")])
    ci3 = SV.bootstrap_ci(a[use], b[use], 2000, [SV.BOOT_SEED, SV.source_seed("pool/planted_002")])
    assert ci1 == ci2 and ci1 != ci3
    assert ci1[0] < point < ci1[1] and ci1[1] - ci1[0] < 0.2
    assert abs(ci1[0] - ci3[0]) < 0.02 and abs(ci1[1] - ci3[1]) < 0.02  # another seed: about the same interval
    wide = SV.bootstrap_ci(a[use], b[use], 2000, 1, level=0.99)
    narrow = SV.bootstrap_ci(a[use], b[use], 2000, 1, level=0.5)
    assert wide[0] < narrow[0] < narrow[1] < wide[1]
    assert SV.source_seed("a/b") == SV.source_seed("a/b") != SV.source_seed("a/c")


def test_bootstrap_degenerate_and_bad_input():
    a = np.full(16, 0.6)
    lo, hi = SV.bootstrap_ci(a, np.ones(16), 500, 0)  # every base has the same ratio: zero-width interval
    assert lo == pytest.approx(0.6) and hi == pytest.approx(0.6)
    with pytest.raises(ValueError):
        SV.bootstrap_ci([], [], 10, 0)
    with pytest.raises(ValueError):
        SV.bootstrap_ci([1.0, 2.0], [1.0], 10, 0)


def test_bootstrap_resamples_bases_with_replacement():
    """Ratio of sums over resampled PAIRS: with one dominant base the interval must reach both the ratio
    with and without it."""
    a = np.array([10.0] + [1.0] * 9)
    b = np.array([10.0] + [2.0] * 9)
    lo, hi = SV.bootstrap_ci(a, b, 4000, 3)
    assert lo == pytest.approx(0.5) and 0.5 < SV.ratio_of_sums(a, b) < hi < 1.0


# ---------------------------------------------------------------- top candidate

CONF = ["greeting", "signoff", "ps_question", "hashtag", "quote", "emoticon"]  # aligned set (privileged)
SIGNS = {"greeting": 1, "signoff": -1, "ps_question": -1, "hashtag": 1, "quote": 1, "emoticon": -1}


def test_top_candidate_ranks_aligned_properties_by_abs_latent_ratio():
    sc = scan()
    t = SV.top_candidate(sc, CONF, ["ps_question"], SIGNS)
    assert t["order"][:3] == ["ps_question", "greeting", "hashtag"]  # |visible| 3.0, 1.2, 0.9
    assert set(t["order"]) == set(CONF)  # non-aligned properties are never candidates
    assert t["top"] == "ps_question" and t["correct"] and t["correct_sa"] and t["main_rank"] == 1
    assert not t["tied"] and t["top2_is_mains"] is None
    assert t["main_abs_lat"] == pytest.approx(3.0 / TOPIC_VISIBLE) and t["main_abs_tru"] == pytest.approx(1.0)
    assert t["nonmain_abs_lat"] == pytest.approx(1.2 / TOPIC_VISIBLE)
    # legacy scan: the child's ratio is diluted by the parent-off bases and it loses the top rank
    leg = scan(False)
    share = leg.valid["ps_question"].mean()  # all True in legacy
    assert share == 1.0
    p_on = (np.asarray(synthetic()[0]["scan_levels"])[:, FEATS.index("postscript")] == 1).mean()
    assert abs(leg.lat_ratio["ps_question"]) == pytest.approx(p_on * 3.0 / TOPIC_VISIBLE)
    weak = scan(False, visible={"ps_question": -1.5})  # 1.5 * p_on < 1.2 while 1.5 > 1.2
    assert SV.top_candidate(weak, CONF, ["ps_question"], SIGNS)["top"] == "greeting"
    assert SV.top_candidate(scan("child", visible={"ps_question": -1.5}), CONF, ["ps_question"], SIGNS)["correct"]


def test_top_candidate_decoy_and_sign_aware_variant():
    sc = scan()
    # main = quote (visible 0.6); a larger aligned candidate (greeting) sits on top: wrong, rank 3
    t = SV.top_candidate(sc, ["greeting", "quote", "hashtag"], ["quote"], {"greeting": 1, "quote": 1, "hashtag": 1})
    assert t["top"] == "greeting" and not t["correct"] and not t["correct_sa"] and t["main_rank"] == 3
    # the same candidates, but the larger ones' latent ratios have the wrong sign for their alignment: the
    # sign-aware ranking drops them and the main is on top
    t = SV.top_candidate(sc, ["greeting", "quote", "hashtag"], ["quote"], {"greeting": -1, "quote": 1, "hashtag": -1})
    assert t["top"] == "greeting" and not t["correct"]
    assert t["top_sa"] == "quote" and t["correct_sa"]
    # the main's own latent ratio has the wrong sign (emoticon: true effect -1, latent view +0.6)
    t = SV.top_candidate(sc, ["emoticon"], ["emoticon"], {"emoticon": -1})
    assert t["correct"] and t["top_sa"] is None and not t["correct_sa"]
    with pytest.raises(ValueError):
        SV.top_candidate(sc, ["not_a_feature"], ["quote"], {"not_a_feature": 1})


def test_top_candidate_ties_go_to_the_earlier_property_and_are_flagged():
    sc = scan(visible={"greeting": 0.5, "quote": 0.5, "hashtag": 0.5})  # equal |latent ratio|
    assert abs(sc.lat_ratio["greeting"]) == abs(sc.lat_ratio["quote"]) == abs(sc.lat_ratio["hashtag"])
    signs = {"greeting": 1, "quote": 1, "hashtag": 1}
    t = SV.top_candidate(sc, ["quote", "hashtag", "greeting"], ["quote"], signs)
    assert t["order"] == ["greeting", "hashtag", "quote"]  # generator's property order, not the conf order
    assert t["tied"] and t["top"] == "greeting" and not t["correct"] and t["main_rank"] == 3
    t = SV.top_candidate(sc, ["quote", "hashtag", "greeting"], ["greeting"], signs)
    assert t["tied"] and t["correct"]
    # equal magnitude, opposite sign: still a tie; the sign-aware ranking keeps only the consistent one
    sc = scan(visible={"greeting": -0.5, "quote": 0.5})
    t = SV.top_candidate(sc, ["greeting", "quote"], ["quote"], {"greeting": 1, "quote": 1})
    assert t["tied"] and t["top"] == "greeting" and not t["correct"] and t["correct_sa"]


def test_top_candidate_two_mains():
    sc = scan()
    signs = {"greeting": 1, "ps_question": -1, "hashtag": 1, "quote": 1}
    t = SV.top_candidate(sc, list(signs), ["greeting", "ps_question"], signs)
    assert t["correct"] and t["top2_is_mains"] is True and t["main_rank"] == 1
    t = SV.top_candidate(sc, list(signs), ["ps_question", "quote"], signs)
    assert t["correct"] and t["top2_is_mains"] is False


# ---------------------------------------------------------------- population and aggregation

def _probe(source, cue, sign, conf_signs, **extra):
    return {"kind": "planted", "source": source, "cue": cue, "sign": sign, "conf_signs": conf_signs,
            "logit_scale": extra.pop("logit_scale", 1.0), **extra}


def _rows():
    """Four slot instances on synthetic scans: one ordinary source in two 'episodes' (different aligned
    sets), a second ordinary source, a trap-pool source and a nested main."""
    views = SV.scan_views(*synthetic(base_noise=0.3, seed=4), FEATS)
    c1 = {"greeting": 1, "quote": 1, "hashtag": 1}
    c2 = {"greeting": 1, "quote": 1, "signoff": -1}
    spec = [("epA", 0, _probe("poolx/planted_001", "greeting", 1, c1), c1),
            ("epB", 1, _probe("poolx/planted_001", "greeting", 1, c2, logit_scale=2.0), c2),
            ("epB", 2, _probe("pooly/planted_007", "signoff", -1, c2), c2),
            ("epB", 3, _probe("knob_trap_z/planted_000", "quote", 1, c1), c1),
            ("epC", 0, _probe("tp/planted_003", "ps_question", -1, {"ps_question": -1, "greeting": 1}),
             {"ps_question": -1, "greeting": 1})]
    return [SV.probe_row(ep, j, p, FEATS, set(conf), views, "ft") for ep, j, p, conf in spec]


def test_groups_pools_and_dedup():
    rows = _rows()
    assert [r["groups"] for r in rows] == [["ordinary"], ["ordinary"], ["ordinary"], ["trap"], ["nested"]]
    assert [r["pool"] for r in rows] == ["poolx", "poolx", "pooly", "knob_trap_z", "tp"]
    assert SV.groups_of({"kind": "planted", "source": "knob_trap_s3/planted_000", "mains": ["a", "ps_question"],
                         "cue": "a"}) == ["nested", "trap", "twomain"]
    ordi = [r for r in rows if "ordinary" in r["groups"]]
    assert list(SV.first_by_source(ordi)) == ["poolx/planted_001", "pooly/planted_007"]
    assert SV.first_by_source(ordi)["poolx/planted_001"]["episode"] == "epA"  # first in the given order
    assert len(SV.distinct_instances(ordi)) == 3  # the shared source counts twice: two aligned sets
    same = SV.probe_row("epZ", 0, _probe("poolx/planted_001", "greeting", 1, {"hashtag": 1, "quote": 1, "greeting": 1}),
                        FEATS, {"greeting", "quote", "hashtag"}, SV.scan_views(*synthetic(), FEATS), "ft")
    assert same["instance_key"] == rows[0]["instance_key"]  # key ignores dict / set order
    assert len(SV.distinct_instances(ordi + [same])) == 3
    # nested mains get their valid-base count; a feature list without a nested pair shares one scan object
    assert rows[4]["fixed"]["n_valid"] < N == rows[4]["legacy"]["n_valid"]
    plain = [f for f in FEATS if f not in ("signoff_excl", "ps_question")]
    v = SV.scan_views(*synthetic(feats=plain), plain)
    assert v["fixed"] is v["legacy"]


def test_aggregation_and_public_summary():
    rows = _rows()
    assert SV.spread([]) is None
    s = SV.spread([1.0, 2.0, 3.0, 4.0, 10.0])
    assert (s["n"], s["median"], s["q25"], s["q75"], s["min"], s["max"], s["mean"]) == (5, 3.0, 2.0, 4.0, 1.0, 10.0, 4.0)
    J = SV.build(rows, ["epA", "epB", "epC"], ["ep412"], ["epA", "epB", "epC", "ep412"], n_boot=300)
    P = J["population"]
    assert P["n_episodes_used"] == 3 and P["excluded_present_in_bank"] == ["ep412"]
    assert P["by_group"]["ordinary"] == {"instances": 3, "distinct_instances": 3, "distinct_sources": 2,
                                         "by_pool": {"poolx": {"instances": 2, "sources": 1},
                                                     "pooly": {"instances": 1, "sources": 1}}}
    assert P["ordinary_sources"] == ["poolx/planted_001", "pooly/planted_007"]
    assert P["source_consistency"]["sources_in_more_than_one_episode"] == 1
    assert P["source_consistency"]["max_abs_diff_captured"] == 0.0
    m1 = J["ordinary"]["all"]["fixed"]["captured_fraction"]
    caps = [rows[0]["fixed"]["captured"], rows[2]["fixed"]["captured"]]
    assert m1["n_sources"] == 2 and m1["median"] == pytest.approx(np.median(caps))
    assert m1["min"] == pytest.approx(min(caps)) and m1["max"] == pytest.approx(max(caps))
    # pooled ratio of sums: sign-oriented, so the negative cue adds to the positive one
    num = rows[0]["fixed"]["num"] + rows[2]["fixed"]["num"]
    den = rows[0]["fixed"]["den"] + rows[2]["fixed"]["den"]
    assert rows[2]["fixed"]["num"] > 0 and rows[2]["fixed"]["den"] > 0
    assert m1["pooled_ratio_raw_logits"] == pytest.approx(num / den)
    assert m1["n_sources_true_effect_has_recorded_sign"] == 2 and m1["n_sources_ci95_below_1"] == 2
    # a subset whose row is not its source's first row still carries the source's CI
    assert rows[1]["fixed"]["ci95"] == rows[0]["fixed"]["ci95"]
    sub = SV.metric1([rows[1], rows[2]])
    assert sub["n_sources"] == 2 and sub["n_sources_ci95_below_1"] == 2
    assert sub["ci95_envelope"] == m1["ci95_envelope"]
    assert sub["pooled_ratio_raw_logits"] != pytest.approx(m1["pooled_ratio_raw_logits"])  # synthetic rows 0/1
    # share one scan although their logit scales differ; on the bank a source's raw-logit sums agree
    half = {**rows[2], "fixed": {**rows[2]["fixed"], "ci95": None}}
    half["fixed"].pop("ci95")
    with pytest.raises(ValueError):
        SV.metric1([rows[1], half])
    m2 = J["ordinary"]["all"]["fixed"]["top_candidate"]
    assert m2["distinct_instances"]["n"] == 3 and m2["all_instances"]["n"] == 3
    assert m2["distinct_instances"]["correct"] == 2  # greeting tops both of its sets; signoff (0.5) is behind
    assert m2["sources_correct_in_every_instance"] == 1 and m2["n_sources"] == 2
    assert J["ordinary"]["by_pool"]["poolx"]["distinct_sources"] == 1
    assert J["trap"]["all"]["fixed"]["top_candidate"]["all_instances"]["correct"] == 0  # greeting outranks it
    assert J["trap"]["all"]["fixed"]["ratio_profile"]["main_abs_lat"]["n"] == 1
    assert J["nested"]["all"]["fixed"]["captured_fraction"]["n_valid_bases_range"][1] < N
    assert J["twomain"]["all"] == {"instances": 0, "distinct_instances": 0, "distinct_sources": 0}
    # same seed -> same CIs on a second build from fresh rows
    J2 = SV.build(_rows(), ["epA", "epB", "epC"], ["ep412"], ["epA", "epB", "epC", "ep412"], n_boot=300)
    assert J2["ordinary"]["all"]["fixed"]["captured_fraction"]["ci95_envelope"] == m1["ci95_envelope"]
    # the tracked summary and README carry no cue name and no per-episode source id
    pub = json.dumps(SV._public(J))
    md = SV.readme(J)
    for name in ("greeting", "signoff", "ps_question", "quote", "hashtag", "emoticon", "postscript"):
        assert f'"{name}"' not in pub and name not in md, name
    assert '"_a"' not in pub and '"_b"' not in pub and "instance_key" not in pub
    assert "privileged" in md.lower() and "poolx/planted_001" in md and "knob_trap_z" in md


def test_population_excludes_hv_copies_by_name(tmp_path):
    for ep in ("ep411", "ep412", "ep472", "ep481", "ep483", "ep999"):
        (tmp_path / ep / "private").mkdir(parents=True)
        (tmp_path / ep / "private" / "answer.json").write_text("{}")
    used, excluded, all_eps = SV.population_episodes(tmp_path)
    assert used == ["ep411", "ep472", "ep999"] and excluded == ["ep412", "ep481", "ep483"] and len(all_eps) == 6
    assert set(SV.HV_EXCLUDED) == {"ep412", "ep414", "ep416", "ep481", "ep483", "ep485"}
    assert not set(SV.SHIPPED) & set(SV.HV_EXCLUDED)


# ---------------------------------------------------------------- the stored bank (skips without it)

def test_shipped_six_on_the_bank():
    bank = ML.resolve_bank()
    missing = [ep for ep in SV.SHIPPED if not (bank / ep / "private" / "answer.json").exists()]
    if missing:
        pytest.skip(f"episode bank absent or incomplete ({bank}; missing {missing}); set SHIFTHUNT_BANK to run "
                    "Exp C on the shipped six")
    rows = SV.collect(bank, list(SV.SHIPPED))
    J = SV.build(rows, list(SV.SHIPPED), [], list(SV.SHIPPED), n_boot=500)
    g = J["population"]["by_group"]
    assert (g["ordinary"]["instances"], g["ordinary"]["distinct_sources"]) == (12, 11)  # D20
    assert (g["trap"]["instances"], g["nested"]["instances"], g["twomain"]["instances"]) == (3, 3, 0)
    assert J["population"]["slots_in_more_than_one_group"] == 0
    assert J["population"]["source_consistency"]["max_abs_diff_captured"] < 1e-9
    o = J["ordinary"]["shipped_six"]["fixed"]
    assert o["top_candidate"]["all_instances"]["correct"] == 12  # ordinary: the SAE top candidate is the main
    assert 0.3 < o["captured_fraction"]["min"] and o["captured_fraction"]["max"] < 1.0
    assert o["captured_fraction"]["n_sources_true_effect_has_recorded_sign"] == 11
    t = J["trap"]["shipped_six"]["fixed"]
    assert t["top_candidate"]["all_instances"]["correct"] == 0  # shipped traps: a decoy outranks the main
    assert t["captured_fraction"]["max"] < o["captured_fraction"]["min"]
    n = J["nested"]["shipped_six"]
    assert n["fixed"]["top_candidate"]["all_instances"]["correct"] == 3
    lo, hi = n["fixed"]["captured_fraction"]["n_valid_bases_range"]
    assert 8 <= lo <= hi < 32 and n["legacy"]["captured_fraction"]["n_valid_bases_range"] == [32, 32]
    # the fix roughly doubles the nested main's latent ratio
    assert n["fixed"]["ratio_profile"]["main_abs_lat"]["median"] > 1.5 * n["legacy"]["ratio_profile"]["main_abs_lat"]["median"]
