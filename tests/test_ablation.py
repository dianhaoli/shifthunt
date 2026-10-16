import numpy as np
import pytest

from shifthunt.ablation import ablate_logits, gradient, probe_logit

N, D, M = 10, 32, 200


@pytest.fixture
def toy():
    """Random SAE-shaped arrays with resid = F @ W_dec + b_dec + err."""
    rng = np.random.default_rng(0)
    F = rng.exponential(size=(N, M)) * (rng.random((N, M)) < 0.1)
    W_dec, b_dec = rng.normal(size=(M, D)), rng.normal(size=D)
    err = 0.1 * rng.normal(size=(N, D))
    w, b = rng.normal(size=D), 0.3
    mu = F.mean(0) + 0.05 * rng.random(M)
    resid = F @ W_dec + b_dec + err
    return dict(F=F, W_dec=W_dec, b_dec=b_dec, err=err, w=w, b=b, mu=mu, resid=resid,
                logits=probe_logit(resid, w, b), g=gradient(W_dec, w))


def ablate(t, S):
    return ablate_logits(t["logits"], t["F"], t["g"], t["mu"], S)


def test_empty_set_is_identity(toy):
    out = ablate(toy, [])
    assert np.array_equal(out, toy["logits"])
    assert out is not toy["logits"]


def test_repeats_and_order_do_not_matter(toy):
    assert np.array_equal(ablate(toy, [5, 5, 5]), ablate(toy, [5]))
    assert np.array_equal(ablate(toy, [7, 3, 150]), ablate(toy, [150, 7, 3, 3]))


@pytest.mark.parametrize("S", [[0], [5, 17, 199], list(range(0, M, 3)), list(range(M))])
def test_matches_explicit_reconstruction(toy, S):
    F = toy["F"].copy()
    F[:, S] = toy["mu"][S]
    resid = F @ toy["W_dec"] + toy["b_dec"] + toy["err"]
    expected = resid @ toy["w"] + toy["b"]
    assert np.abs(ablate(toy, S) - expected).max() < 1e-9


@pytest.mark.parametrize("S", [[M], [-1], [1.0, 2.0], [[1, 2]], np.array([True, False])])
def test_invalid_ids_raise(toy, S):
    with pytest.raises(ValueError):
        ablate(toy, S)
