"""Synthetic checks for scripts/trap_flags.py (T-flags, F4, F1a). Columns: 0 = main, 1 = decoy, 2 = other."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import trap_flags as TF  # noqa: E402


def mf(regex, scope, texts):
    return [bool(re.search(regex, t)) for t in texts], None


NAMED_MAIN = {"none": False, "cues": [{"regex": "MAIN"}]}
NONE = {"none": True, "cues": []}


def test_clean_main_and_decoy_tested():
    texts = ["base", "MAIN base", "DECOY base"]
    rows = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    out = TF.t_flags(NAMED_MAIN, texts, rows, [0, 0, 0], [0], 1, True, mf)
    assert (out["T_F2"], out["T_D"], out["T_RULE"]) == (0, 0, 0)
    assert (out["T_F2L"], out["T_DL"], out["T_RULEL"]) == (0, 0, 0)


def test_decoy_never_varied():
    texts = ["base", "MAIN base"]
    rows = [(0, 0, 0), (1, 0, 0)]
    out = TF.t_flags(NAMED_MAIN, texts, rows, [0, 0], [0], 1, True, mf)
    assert (out["T_F2"], out["T_D"], out["T_RULE"]) == (0, 1, 1)


def test_multi_property_flip_is_loose_not_clean():
    texts = ["base", "MAIN DECOY base"]
    rows = [(0, 0, 0), (1, 1, 0)]
    out = TF.t_flags(NAMED_MAIN, texts, rows, [0, 0], [0], 1, True, mf)
    assert (out["T_F2"], out["T_D"], out["T_RULE"]) == (1, 1, 1)
    assert (out["T_F2L"], out["T_DL"], out["T_RULEL"]) == (0, 0, 0)


def test_unknown_topic_and_cross_topic_pairs_do_not_count():
    rows = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    out = TF.t_flags(NAMED_MAIN, ["a", "MAIN a", "b"], rows, [0, None, 1], [0], 1, True, mf)
    assert (out["T_F2"], out["T_D"], out["T_F2L"], out["T_DL"]) == (1, 1, 1, 1)


def test_untested_claim_sets_t_rule():
    entry = {"none": False, "cues": [{"regex": "MAIN"}, {"regex": "ZZZ"}]}
    texts = ["base", "MAIN base", "DECOY base"]
    rows = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    out = TF.t_flags(entry, texts, rows, [0, 0, 0], [0], 1, True, mf)
    assert (out["T_F2"], out["T_D"], out["T_RULE"]) == (0, 0, 1)


def test_none_answer_and_missing():
    texts = ["base", "MAIN base", "DECOY base"]
    rows = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    assert TF.t_flags(NONE, texts, rows, [0, 0, 0], [0], 1, True, mf)["T_RULE"] == 0
    assert all(v is None for v in TF.t_flags(NONE, [], [], [], [0], 1, False, mf).values())
    assert TF.t_flags(NONE, texts, rows, [0, 0, 0], [0], None, True, mf)["T_RULE"] is None


def test_nested_child_with_parent_on_is_clean():
    # columns: 0 = child (main), 1 = parent, 2 = decoy; child-on implies parent-on
    rows = [(0, 1, 0), (1, 1, 0), (0, 0, 0)]
    out = TF.t_flags(NONE, ["p", "pc", "x"], rows, [0, 0, 0], [0], 2, True, mf)
    assert out["T_F2"] == 0
    rows2 = [(0, 0, 0), (1, 1, 0)]  # child flipped together with its parent: not clean
    assert TF.t_flags(NONE, ["x", "pc"], rows2, [0, 0], [0], 2, True, mf)["T_F2"] == 1


# ------------------------------------------------------------------ F4 (unit 10; cue >= 3, non-cue <= 1.5)

ROWS = [(0, 0, 0), (1, 0, 0)]
TOP = [0, 0]


def test_f4_follows_proxy_uncovered():
    r = TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, 0.5], 10.0, covered=set())
    assert r["F4"] == 1 and r["contradicted"] == [0]


def test_f4_follows_truth_covered():
    r = TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, 0.5], 10.0, covered={0})
    assert r["F4"] == 0


def test_f4_follows_proxy_covered():
    r = TF.f4_slot(ROWS, TOP, [0.0, 0.5], [0.0, 4.0], 10.0, covered={0})
    assert r["F4"] == 1


def test_f4_band_and_unavailable_are_na():
    assert TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, 2.0], 10.0, set())["F4"] == "na"
    r = TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, None], 10.0, set())
    assert r["F4"] == "na" and r["n_both_pairs"] == 0
    assert TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, 0.5], None, set())["F4"] is None
    assert TF.f4_slot(ROWS, TOP, [0.0, 4.0], [0.0, None], None, set())["F4"] == "na"


def test_f4_sign_orientation_on_minus_off():
    rows = [(1, 0, 0), (0, 0, 0)]  # first text has the property on
    r = TF.f4_slot(rows, TOP, [4.0, 0.0], [0.5, 0.0], 10.0, set())
    assert r["dT"][0] > 0 and r["F4"] == 1


def test_available_texts_before_submit_only():
    recs = [{"seq": 1, "tool": "latent_means", "status": "ok", "texts": ["a\r\n"]},
            {"seq": 2, "tool": "probe_query", "status": "ok", "texts": ["b"]},
            {"seq": 3, "tool": "latent_tokens", "status": "ok", "texts": ["c"]},
            {"seq": 9, "tool": "latent_means", "status": "ok", "texts": ["d"]},
            {"seq": 4, "tool": "latent_means", "status": "timeout", "texts": ["e"]}]
    assert TF.available_texts(recs, submit_seq=5) == {"a", "c"}


# ------------------------------------------------------------------ F1a

def test_f1a_not_computable_without_uncovered_pair():
    rows = [(0, 0, 0), (1, 0, 0)]
    assert TF.f1a(rows, [0, 0], [0.0, 5.0], 10.0, covered={0}, texts_ok=True, logits_ok=True)[0] == "nc"


def test_f1a_boundary():
    rows = [(0, 0, 0), (0, 0, 1)]
    assert TF.f1a(rows, [0, 0], [0.0, 1.5], 10.0, set(), True, True)[0] == 1
    assert TF.f1a(rows, [0, 0], [0.0, 1.49], 10.0, set(), True, True)[0] == 0
    assert TF.f1a(rows, [0, 0], [0.0, None], 10.0, set(), True, True)[0] == "nc"
    assert TF.f1a(rows, [0, 0], [0.0, 1.5], 10.0, set(), False) == (None, None)  # texts not recovered
    assert TF.f1a(rows, [0, 0], [0.0, 1.5], 0.0, set(), True) == (None, "nc")    # computable, unit unknown
    assert TF.f1a(rows, [0, 0, 0], [0.0, 1.5, None], 10.0, set(), True)[1] is None  # LS group logit unknown


def test_f1a_loose_least_squares_and_collinearity():
    rows = [(0, 0, 0), (1, 1, 0), (1, 0, 0), (0, 0, 1)]
    eff = TF.least_squares_effects(rows, [0, 0, 0, 0], [0.0, 7.0, 4.0, 2.0], 10.0)
    assert abs(eff[0] - 0.4) < 1e-9 and abs(eff[1] - 0.3) < 1e-9 and abs(eff[2] - 0.2) < 1e-9
    coll = [(0, 0, 0), (1, 1, 0), (0, 0, 0)]  # columns 0 and 1 always move together
    assert TF.least_squares_effects(coll, [0, 0, 0], [0.0, 5.0, 0.1], 10.0) == {}
    assert TF.f1a(coll, [0, 0, 0], [0.0, 5.0, 0.1], 10.0, set(), True, True)[1] == "nc"


def test_privacy_check_flags_property_names():
    import s3_coder as S3
    name = list(S3.FEATURES["templated"])[0]
    assert TF.privacy_check(f'{{"x": "{name}"}}') == [name]
    assert TF.privacy_check('{"T_RULE": 1}') == []


def test_proxy_unit_from_stored_sample_encodings(tmp_path):
    import numpy as np
    import scipy.sparse as sp
    priv = tmp_path / "ep" / "private"
    priv.mkdir(parents=True)
    F = sp.csr_matrix(np.array([[1.0, 0, 0], [0, 2.0, 0], [3.0, 0, 1.0], [0, 0, 0]]))
    np.savez(priv / "probe0_sample_enc.npz", lat_data=F.data, lat_indices=F.indices, lat_indptr=F.indptr,
             resid=np.zeros((4, 1), np.float32))
    np.savez(priv / "probe0.npz", g=np.array([1.0, 0.5, 2.0]), w=np.array([1.0]), b=0.0)

    class Ep:
        samples = [[{"label": 1}, {"label": 0}, {"label": 1}, {"label": 0}]]
    # proxy logits: 1, 1, 5, 0 -> label-1 mean 3, label-0 mean 0.5 -> gap 2.5
    assert abs(TF.proxy_unit(tmp_path, "ep", 0, Ep()) - 2.5) < 1e-12
