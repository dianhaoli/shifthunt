"""The held-out reliance estimator in scripts/check_prompt_facts.py on synthetic data."""
import importlib.util
import os
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_prompt_facts", ROOT / "scripts" / "check_prompt_facts.py")
cpf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpf)


def _synthetic(n=4096, seed=0):
    rng = np.random.default_rng(seed)
    feats = ["a", "parent", "child", "d"]
    fl = rng.integers(0, 2, (4, n))
    fl[2] = fl[2] * fl[1]  # child implies parent, flags as rendered
    tp = np.arange(n) % 2
    coef = np.array([1.5, 0.6, -0.9, 0.0])  # topic coef 3.0 -> ratios 0.5, 0.2, -0.3, 0
    y = fl.T @ coef - 3.0 * (tp == 0) + 3.0 * (tp == 1) * 0 + 0.7 + rng.normal(0, 0.05, n)
    return feats, fl, tp, y


def test_ols_ratio_recovers_coefficients():
    feats, fl, tp, y = _synthetic()
    r = cpf.ols_ratio(cpf.design(fl, tp), y)
    assert np.allclose(r, [0.5, 0.2, -0.3, 0.0], atol=0.01)


def test_alt_coding_child_is_parent_plus_child():
    feats, fl, tp, y = _synthetic()
    alt = cpf.alt_coding(fl, feats, {"child": "parent"})
    r = cpf.ols_ratio(cpf.design(alt, tp), y)
    assert np.allclose(r, [0.5, 0.2, -0.1, 0.0], atol=0.01)  # child from none = 0.2 - 0.3


def test_bootstrap_se_and_classify():
    feats, fl, tp, y = _synthetic(n=1024)
    pt, se = cpf.ratio_boot(cpf.design(fl, tp), y, 200, np.random.default_rng(1))
    assert (se > 0).all() and (se < 0.01).all()
    assert cpf.classify(0.5, 0.01, True) == "ok"
    assert cpf.classify(0.29, 0.01, True) == "TIGHT"
    assert cpf.classify(0.25, 0.01, True) == "FAIL"
    assert cpf.classify(0.31, 0.01, True) == "MARGINAL"
    assert cpf.classify(-0.2, 0.01, False) == "FAIL"
    assert cpf.classify(0.155, 0.01, False) == "TIGHT"
    assert cpf.classify(0.14, 0.01, False) == "MARGINAL"


def test_source_rng_independent_of_order():
    a = cpf.source_rng("pool_x/planted_001").integers(0, 1 << 30, 5)
    _ = cpf.source_rng("pool_y/null_002").integers(0, 1 << 30, 5)
    b = cpf.source_rng("pool_x/planted_001").integers(0, 1 << 30, 5)
    assert (a == b).all()
    assert not (a == cpf.source_rng("pool_x/planted_002").integers(0, 1 << 30, 5)).all()


def test_load_heldout_checks_stream_and_n(tmp_path):
    f = tmp_path / "s.npz"
    n = 32
    kw = dict(logits=np.zeros(n), flags=np.zeros((3, n), np.int8), features=np.array(["a", "b", "c"]),
              topic=np.zeros(n, np.int8))
    np.savez(f, stream=f"{cpf.HELDOUT_STREAM}:7", n=n, **kw)
    assert cpf.load_heldout(f, 7, n)[0] is not None
    assert cpf.load_heldout(f, 8, n)[0] is None  # other eval_seed
    assert cpf.load_heldout(f, 7, 64)[0] is None  # other N
    np.savez(f, stream="other:7", n=n, **kw)
    assert cpf.load_heldout(f, 7, n)[0] is None
    assert cpf.load_heldout(tmp_path / "missing.npz", 7, n) == (None, "missing")


def test_small_pools_merged_into_family_row():
    rows = {f"{pl}/s{i}": {"pool": pl} for pl, k in [("ft_a", 4), ("ft_b", 1), ("knob_c", 3)] for i in range(k)}
    key = cpf.row_keys(rows)
    assert key == {"ft_a": "ft_* (merged)", "ft_b": "ft_* (merged)", "knob_c": "knob_c"}
