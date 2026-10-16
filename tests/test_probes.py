import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # probes imports substrate (torch); never touch a GPU

import hashlib
import json
import random
import warnings
from types import SimpleNamespace

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from shifthunt import probes as P
from shifthunt import textgen as tg
from shifthunt.detectors import detect

TOPICS = ("chess", "sailing")


# ---- fit_probe ----

@pytest.fixture
def planted_xy():
    """256 x 50 Gaussian with a planted direction; labels alternate (balanced)."""
    rng = np.random.default_rng(0)
    n, d = 256, 50
    y = np.arange(n) % 2
    v = rng.normal(size=d)
    X = rng.normal(size=(n, d)) * rng.uniform(0.5, 3, size=d) + rng.normal(size=d) * 4
    X += np.outer(2 * y - 1, v) * 0.3
    return X, y


def test_fit_probe_folds_back_to_sklearn(planted_xy):
    X, y = planted_xy
    w, b, n_iter = P.fit_probe(X, y)
    Z = StandardScaler().fit_transform(X)
    ref = LogisticRegression(C=P.C, max_iter=P.MAX_ITER).fit(Z, y).decision_function(Z)
    assert w.dtype == np.float64 and w.shape == (X.shape[1],) and isinstance(b, float)
    assert 0 < n_iter <= P.MAX_ITER
    assert np.abs(X @ w + b - ref).max() < 1e-8
    assert ((X @ w + b > 0) == y).mean() > 0.9  # the planted direction is learned


def test_fit_probe_accepts_float32(planted_xy):
    X, y = planted_xy
    w64, b64, _ = P.fit_probe(X.astype(np.float32).astype(np.float64), y)
    w32, b32, _ = P.fit_probe(X.astype(np.float32), y)
    assert np.array_equal(w64, w32) and b64 == b32


@pytest.mark.parametrize("y", [np.zeros(256, int), np.ones(256, int), np.arange(256) % 3])
def test_fit_probe_rejects_bad_labels(planted_xy, y):
    with pytest.raises(ValueError):
        P.fit_probe(planted_xy[0], y)


def test_fit_probe_raises_on_nonconvergence(planted_xy, monkeypatch):
    monkeypatch.setattr(P, "MAX_ITER", 1)
    with pytest.raises(Exception, match="(?i)converge"):
        P.fit_probe(*planted_xy)


# ---- measure_reliance ----

def synthetic_reliance(cue, sign, topic_coef, n=384, seed=0):
    rng = np.random.default_rng(seed)
    flags = {f: rng.integers(0, 2, n) for f in tg.FEATURES}
    topic = np.arange(n) % 2
    coef = {f: rng.normal() for f in tg.FEATURES}
    logits = sum(coef[f] * flags[f] for f in tg.FEATURES) + topic_coef * topic + 0.7
    logits = logits + 1e-6 * rng.normal(size=n)
    return P.measure_reliance(logits, flags, topic, cue, sign), coef


@pytest.mark.parametrize("cue,sign,topic_coef", [("quote", 1, 2.5), ("quote", -1, 2.5),
                                                 ("hashtag", -1, -1.7), (None, None, 3.0)])
def test_measure_reliance_recovers_known_model(cue, sign, topic_coef):
    out, coef = synthetic_reliance(cue, sign, topic_coef)
    assert set(out["reliance"]) == set(out["coef"]) == set(tg.FEATURES)
    for f in tg.FEATURES:
        assert out["coef"][f] == pytest.approx(coef[f], abs=1e-5)
    assert out["topic_coef"] == pytest.approx(topic_coef, abs=1e-5)
    assert out["intercept"] == pytest.approx(0.7, abs=1e-5)
    assert out["r2"] > 1 - 1e-9
    for f in tg.FEATURES:
        s = sign if f == cue else 1
        expected = out["coef"][f] * s / abs(out["topic_coef"])
        assert out["reliance"][f] == pytest.approx(expected, rel=1e-12)
        assert out["reliance"][f] == pytest.approx(coef[f] * s / abs(topic_coef), abs=1e-5)


def test_measure_reliance_negative_topic_coef_keeps_sign():
    pos, _ = synthetic_reliance("quote", 1, 2.0, seed=3)
    neg, _ = synthetic_reliance("quote", 1, -2.0, seed=3)
    assert neg["topic_coef"] < 0
    for f in tg.FEATURES:  # same cue coefs, |topic| equal -> same reliance
        assert neg["reliance"][f] == pytest.approx(pos["reliance"][f], abs=1e-5)


# ---- validity_failures ----

def rel(others=0.0, worst="weekday", **kw):
    r = {f: 0.0 for f in tg.FEATURES}
    r[worst] = others
    r.update(kw)
    return r


@pytest.mark.parametrize("p,fails", [(P.PLANTED_MIN, []), (0.2999, ["planted_low"]), (0.9, [])])
def test_planted_min_boundary(p, fails):
    assert P.validity_failures("planted", rel(0.1, quote=p), "quote") == fails


@pytest.mark.parametrize("o,fails", [(P.OTHER_MAX, []), (-P.OTHER_MAX, []), (0.1501, ["other_high:weekday"]),
                                     (-0.1501, ["other_high:weekday"])])
def test_planted_other_max_boundary(o, fails):
    assert P.validity_failures("planted", rel(o, quote=0.5), "quote") == fails


def test_planted_ratio_boundary():
    # With the defaults the ratio rule can only bind when other_high also fires
    # (p >= 0.30 and others <= 0.15 implies ratio >= 2), so test it above OTHER_MAX.
    o = 0.8
    p = P.RATIO_MIN * o
    assert P.validity_failures("planted", rel(o, quote=p), "quote") == ["other_high:weekday"]
    p_below = np.nextafter(p, 0)
    assert P.validity_failures("planted", rel(o, quote=p_below), "quote") == ["other_high:weekday", "ratio"]


def test_planted_max():
    r = rel(0.0, quote=0.6)
    assert P.validity_failures("planted", r, "quote", planted_max=0.6) == []
    assert P.validity_failures("planted", r, "quote", planted_max=0.5999) == ["planted_high"]
    assert P.validity_failures("planted", r, "quote", planted_max=None) == []


def test_planted_cue_excluded_from_others():
    r = rel(0.0, quote=5.0)
    assert P.validity_failures("planted", r, "quote") == []
    assert P.validity_failures("null", r) == ["other_high:quote"]


def test_worst_other_is_reported():
    r = rel(0.2, worst="greeting", quote=1.0, hashtag=-0.3)
    assert P.validity_failures("planted", r, "quote") == ["other_high:hashtag"]


@pytest.mark.parametrize("o,fails", [(0.0, []), (P.OTHER_MAX, []), (-P.OTHER_MAX, []),
                                     (0.1501, ["other_high:weekday"]), (-0.2, ["other_high:weekday"])])
def test_null_other_max(o, fails):
    assert P.validity_failures("null", rel(o)) == fails


@pytest.mark.parametrize("kind,cue", [("planted", "quote"), ("null", None)])
@pytest.mark.parametrize("acc,fails", [(None, []), (P.TOPIC_ACC_MIN, []), (1.0, []),
                                       (0.9499, ["topic_unreadable"])])
def test_topic_unreadable(kind, cue, acc, fails):
    r = rel(0.0, quote=0.5) if kind == "planted" else rel(0.0)
    assert P.validity_failures(kind, r, cue, topic_acc=acc) == fails


def test_failures_accumulate():
    r = rel(0.4, quote=0.2)
    assert P.validity_failures("planted", r, "quote", topic_acc=0.5, planted_max=0.1) == [
        "planted_low", "planted_high", "other_high:weekday", "ratio", "topic_unreadable"]


# ---- data ----

def spec(rho=1.0, eps=0.0, sign=1, cue="quote", seed=3, eval_seed=5, kind="planted"):
    if kind == "null":
        return P.Spec("null", TOPICS, None, None, None, eps, seed, eval_seed)
    return P.Spec("planted", TOPICS, cue, sign, rho, eps, seed, eval_seed)


def same(a, b):
    return a[0] == b[0] and np.array_equal(a[1], b[1]) and all(np.array_equal(a[2][f], b[2][f]) for f in tg.FEATURES)


def test_set_sizes_are_batch_multiples():
    assert P.N_TRAIN % P.BATCH_SIZE == 0 and P.N_RELIANCE % P.BATCH_SIZE == 0
    assert len(P.training_set(spec())[0]) == P.N_TRAIN
    assert len(P.reliance_set(TOPICS, 5)[0]) == P.N_RELIANCE


@pytest.mark.parametrize("kind", ["planted", "null"])
def test_training_set_deterministic(kind):
    s = spec(rho=0.9, eps=0.05, kind=kind)
    assert same(P.training_set(s), P.training_set(s))
    other = P.training_set(spec(rho=0.9, eps=0.05, kind=kind, seed=4))
    assert other[0] != P.training_set(s)[0]


def test_training_labels_alternate():
    for s in (spec(rho=0.95, eps=0.1), spec(kind="null", eps=0.1)):
        _, y, _ = P.training_set(s)
        assert np.array_equal(y, np.arange(P.N_TRAIN) % 2)


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("cue", ["quote", "signoff", "lowercase"])
def test_rho_one_cue_tracks_label(sign, cue):
    _, y, flags = P.training_set(spec(rho=1.0, eps=0.0, sign=sign, cue=cue))
    assert np.array_equal(flags[cue], y if sign == 1 else 1 - y)


def test_rho_change_only_touches_flipped_cue_notes():
    a = P.training_set(spec(rho=1.0))
    b = P.training_set(spec(rho=0.9))
    flipped = a[2]["quote"] != b[2]["quote"]
    assert 5 < flipped.sum() < 60  # ~10% of 256
    for f in tg.FEATURES:
        if f != "quote":
            assert np.array_equal(a[2][f], b[2][f])
    for i in range(P.N_TRAIN):
        assert (a[0][i] == b[0][i]) == (not flipped[i])
    assert np.array_equal(a[1], b[1])


def test_eps_change_only_touches_topic():
    a = P.training_set(spec(eps=0.0))
    b = P.training_set(spec(eps=0.1))
    assert same((a[0][:0], a[1], a[2]), (b[0][:0], b[1], b[2]))  # labels and flags unchanged
    changed = sum(x != z for x, z in zip(a[0], b[0]))
    assert 5 < changed < 60


def test_rho_controls_agreement():
    _, y, flags = P.training_set(spec(rho=0.9, seed=11))
    agree = (flags["quote"] == y).mean()
    assert 0.83 < agree < 0.97


def test_reliance_set_tags_are_independent():
    r = P.reliance_set(TOPICS, 5)
    t = P.reliance_set(TOPICS, 5, tag="topic")
    assert same(r, P.reliance_set(TOPICS, 5))
    assert sum(x == z for x, z in zip(r[0], t[0])) < 5
    assert sum(x == z for x, z in zip(r[0], P.reliance_set(TOPICS, 6)[0])) < 5


def test_reliance_set_disjoint_from_training_with_equal_seeds():
    train = set(P.training_set(spec(seed=5, eval_seed=5))[0])
    assert len(train & set(P.reliance_set(TOPICS, 5)[0])) < 5


def test_reliance_set_balanced_and_unconfounded():
    texts, y, flags = P.reliance_set(TOPICS, 5)
    assert np.array_equal(y, np.arange(P.N_RELIANCE) % 2)
    for f in tg.FEATURES:
        assert abs(flags[f].mean() - 0.5) < 0.1, f
        assert abs(np.corrcoef(flags[f], y)[0, 1]) < 0.2, f
    # topic is topics[y]: every note mentions its own topic's places/activities/items only
    for t, lab in zip(texts, y):
        own = [p for ps in tg.TOPICS[TOPICS[lab]].values() for p in ps]
        assert any(p in t.lower() for p in own)


def test_cue_strings_per_eval_seed():
    assert P.cue_strings(5) == P.cue_strings(5)
    assert len({P.cue_strings(s) for s in range(20)}) > 10


@pytest.mark.parametrize("args", [
    ("planted", TOPICS, "quote", 2, 1.0, 0.0, 0, 0),
    ("planted", TOPICS, "shouting", 1, 1.0, 0.0, 0, 0),
    ("planted", TOPICS, "quote", 1, 1.5, 0.0, 0, 0),
    ("null", TOPICS, "quote", None, None, 0.0, 0, 0),
    ("null", TOPICS, None, None, None, 1.5, 0, 0),
])
def test_spec_validation(args):
    with pytest.raises(AssertionError):
        P.Spec(*args)


def test_spec_unknown_kind():
    with pytest.raises(ValueError):
        P.Spec("other", TOPICS, None, None, None, 0.0, 0, 0)


# ---- CachedEncoder ----

D, M = 8, 12


def fake_row(text):
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "little"))
    return rng.normal(size=D).astype(np.float32), rng.exponential(size=M).astype(np.float32)


class FakeSubject:
    """Exposes .sae.W_dec and .encode(texts, batch_size) like substrate.Subject; counts calls."""

    def __init__(self, row=fake_row, warn=None):
        self.sae = SimpleNamespace(W_dec=np.ones((M, D), np.float32))
        self.calls = []
        self.row = row
        self.warn = warn

    def encode(self, texts, batch_size=16):
        self.calls.append((tuple(texts), batch_size))
        if self.warn:
            warnings.warn(self.warn)
        rows = [self.row(t) for t in texts]
        return SimpleNamespace(resid=np.stack([r[0] for r in rows]), latents=np.stack([r[1] for r in rows]))


def texts_(n, start=0):
    return [f"note {i}" for i in range(start, start + n)]


@pytest.mark.parametrize("n", [0, 1, P.BATCH_SIZE - 1, P.BATCH_SIZE + 1, 3 * P.BATCH_SIZE - 2])
def test_encoder_rejects_non_multiples(n):
    sub = FakeSubject()
    with pytest.raises(ValueError):
        P.CachedEncoder(sub).encode(texts_(n))
    assert sub.calls == []


def test_encoder_batches_and_mu():
    sub = FakeSubject()
    enc = P.CachedEncoder(sub)
    T = texts_(3 * P.BATCH_SIZE)
    resid, mu = enc.encode(T)
    assert enc.W_dec is sub.sae.W_dec
    assert [c[0] for c in sub.calls] == [tuple(T[i:i + P.BATCH_SIZE]) for i in range(0, len(T), P.BATCH_SIZE)]
    assert all(bs == P.BATCH_SIZE for _, bs in sub.calls)
    assert np.array_equal(resid, np.stack([fake_row(t)[0] for t in T]))
    lat = np.stack([fake_row(t)[1] for t in T]).astype(np.float64)
    assert mu.dtype == np.float64 and mu.shape == (M,)
    assert np.abs(mu - lat.mean(0)).max() < 1e-12
    assert enc.n_encoded == len(T) and enc.n_cached == 0


def test_encoder_memory_cache():
    sub = FakeSubject()
    enc = P.CachedEncoder(sub)
    T = texts_(2 * P.BATCH_SIZE)
    r1, mu1 = enc.encode(T)
    n = len(sub.calls)
    r2, mu2 = enc.encode(T)
    assert len(sub.calls) == n
    assert np.array_equal(r1, r2) and np.array_equal(mu1, mu2)
    assert enc.n_cached == len(T) and enc.n_encoded == len(T)


def test_encoder_shared_batches_across_sets():
    sub = FakeSubject()
    enc = P.CachedEncoder(sub)
    A, B, C = texts_(16), texts_(16, 16), texts_(16, 32)
    enc.encode(A + B)
    sub.calls.clear()
    resid, mu = enc.encode(B + C)
    assert [c[0] for c in sub.calls] == [tuple(C)]
    lat = np.stack([fake_row(t)[1] for t in B + C]).astype(np.float64)
    assert np.abs(mu - lat.mean(0)).max() < 1e-12


def test_encoder_one_changed_text_reencodes_one_batch():
    sub = FakeSubject()
    enc = P.CachedEncoder(sub)
    T = texts_(3 * P.BATCH_SIZE)
    enc.encode(T)
    sub.calls.clear()
    T2 = list(T)
    T2[20] = "changed"
    resid, _ = enc.encode(T2)
    assert [c[0] for c in sub.calls] == [tuple(T2[16:32])]
    assert np.array_equal(resid[20], fake_row("changed")[0])


def test_encoder_batch_order_is_part_of_key():
    sub = FakeSubject()
    enc = P.CachedEncoder(sub)
    T = texts_(P.BATCH_SIZE)
    enc.encode(T)
    enc.encode(T[::-1])
    assert len(sub.calls) == 2


def test_encoder_disk_cache(tmp_path):
    T = texts_(2 * P.BATCH_SIZE)
    sub1 = FakeSubject()
    r1, mu1 = P.CachedEncoder(sub1, cache_dir=tmp_path / "c").encode(T)
    assert len(sub1.calls) == 2
    files = sorted(p.name for p in (tmp_path / "c").iterdir())
    assert len(files) == 2 and all(f.endswith(".npz") and ".tmp" not in f for f in files)

    def boom(text):
        raise AssertionError("should not encode")

    sub2 = FakeSubject(row=boom)
    enc2 = P.CachedEncoder(sub2, cache_dir=tmp_path / "c")
    r2, mu2 = enc2.encode(T)
    assert sub2.calls == []
    assert np.array_equal(r1, r2) and r2.dtype == np.float32
    assert np.array_equal(mu1, mu2)
    assert enc2.n_cached == len(T) and enc2.n_encoded == 0


def test_encoder_rejects_oom_fallback():
    enc = P.CachedEncoder(FakeSubject(warn="CUDA OOM: retrying at batch size 8"))
    with pytest.raises(RuntimeError):
        enc.encode(texts_(P.BATCH_SIZE))


# ---- g_top_share, save/load ----

def test_g_top_share():
    g = np.array([1.0, -4.0, 0.5, 3.0, -2.0, 0.25, 5.0, -0.25])
    total = np.abs(g).sum()
    assert P.g_top_share(g) == pytest.approx((5 + 4 + 3 + 2 + 1) / total)
    assert P.g_top_share(g, k=1) == pytest.approx(5 / total)
    assert P.g_top_share(g, k=len(g)) == pytest.approx(1.0)
    assert P.g_top_share(g, k=100) == pytest.approx(1.0)
    assert P.g_top_share(np.r_[np.ones(5), np.zeros(10)]) == pytest.approx(1.0)
    assert P.g_top_share(np.ones(10)) == pytest.approx(0.5)


def test_save_load_roundtrip(tmp_path):
    rng = np.random.default_rng(1)
    rel_out, _ = synthetic_reliance("quote", -1, 2.0)
    s = spec(rho=0.95, eps=0.05, sign=-1)
    p = P.Probe(s, rng.normal(size=D), 0.25, rng.random(M), rng.normal(size=M), rel_out,
                0.97, 0.9, 0.96, 42, ["ratio"])
    meta = P.save_probe(p, tmp_path / "out", "p0")
    loaded, arrays = P.load_probe(tmp_path / "out", "p0")
    assert loaded == json.loads(json.dumps(meta)) and loaded["topics"] == list(TOPICS)
    assert loaded["name"] == "p0" and loaded["cue"] == "quote" and loaded["sign"] == -1
    assert loaded["rho"] == 0.95 and loaded["seed"] == s.seed and loaded["eval_seed"] == s.eval_seed
    assert loaded["reliance"] == rel_out["reliance"] and loaded["failures"] == ["ratio"]
    assert loaded["g_top5_share"] == pytest.approx(P.g_top_share(p.g))
    assert set(arrays) == {"w", "b", "g", "mu"}
    for k in ("w", "g", "mu"):
        assert np.array_equal(arrays[k], getattr(p, k))
    assert float(arrays["b"]) == 0.25 and arrays["b"].dtype == np.float64


# ---- Lab.train end to end with a fake subject ----

def topic_row(text):
    """resid = [is topics[1], quote flag, 6 noise dims]; latents = resid magnitudes."""
    low = text.lower()
    is_t1 = any(p in low for ps in tg.TOPICS[TOPICS[1]].values() for p in ps)
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "little"))
    x = np.r_[float(is_t1), float(detect(text, "quote")), 0.3 * rng.normal(size=D - 2)].astype(np.float32)
    return x, np.abs(np.r_[x, x[:M - D]]).astype(np.float32)


@pytest.mark.parametrize("sign", [1, -1])
def test_lab_train_planted_reliance_sign(sign):
    lab = P.Lab(P.CachedEncoder(FakeSubject(row=topic_row)))
    p = lab.train(spec(rho=1.0, eps=0.1, sign=sign))
    r = p.rel["reliance"]
    assert r["quote"] > P.PLANTED_MIN  # sign applied: positive whatever the training sign
    assert np.sign(p.rel["coef"]["quote"]) == sign
    assert max(abs(v) for f, v in r.items() if f != "quote") < P.OTHER_MAX
    assert p.topic_acc > P.TOPIC_ACC_MIN
    assert p.failures == []
    assert p.mu.shape == (M,) and p.g.shape == (M,)
    s = p.summary()
    assert s["kind"] == "planted" and s["failures"] == []


def test_topic_of_recovers_topic_on_every_pair():
    """_topic_of (used by the seed screen) reads the topic from phrases, for all 66 topic pairs."""
    import itertools
    for i, pair in enumerate(itertools.combinations(tg.TOPIC_NAMES, 2)):
        texts, y, _ = P.reliance_set(pair, i, tag="t", n=32)
        assert [P._topic_of(t, pair) for t in texts] == list(y)


def test_flip_imbalance_screen():
    """No flipped notes -> 0; screened seed is no worse than the first candidate; rho-independent."""
    base = dict(kind="planted", topics=("chess", "sailing"), cue="quote", sign=1, eval_seed=3)
    assert P.flip_imbalance(P.Spec(**base, rho=1.0, eps=0.0, seed=1)) == 0.0
    a = P.flip_imbalance(P.Spec(**base, rho=1.0, eps=0.1, seed=1))
    assert a == P.flip_imbalance(P.Spec(**base, rho=0.9, eps=0.1, seed=1))
    make = lambda s: P.Spec(**base, rho=1.0, eps=0.1, seed=s)
    r1, r2 = random.Random(5), random.Random(5)
    first = r1.getrandbits(31)
    best = P.draw_seed(r2, make, 8)
    assert P.flip_imbalance(make(best)) <= P.flip_imbalance(make(first))
