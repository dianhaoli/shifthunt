"""GPU tests for the tool server's RealBackend. Skipped without CUDA.

Run under the shared GPU lock, with the HF cache populated (Gemma is gated):
    flock /tmp/shifthunt-gpu.lock env HF_HUB_OFFLINE=1 python -m pytest tests/test_toolserver_gpu.py -q
"""
import random

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")

from shifthunt import hidden  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt import toolserver as ts  # noqa: E402
from shifthunt.toolbackend import RealBackend  # noqa: E402

from test_toolserver import make_episode  # noqa: E402

LONG = " ".join(["The quick brown fox jumps over the lazy dog."] * 15)  # > 128 tokens


@pytest.fixture(scope="module")
def backend():
    return RealBackend("cuda")


@pytest.fixture(scope="module")
def notes():
    rng = random.Random(1)
    return [tg.render(tg.TOPIC_NAMES[i % 12], {f: rng.randrange(2) for f in tg.FEATURES},
                      tg.make_cues(rng), rng.getrandbits(32))[0] for i in range(19)] + ["Hi.", LONG]


def test_pooled_equals_encode_sparse(backend, notes):
    resid, F = backend.pooled(notes[:16])
    r2, F2 = hidden.encode_sparse(backend.subject, notes[:16])
    assert np.array_equal(resid, r2)
    assert (F != F2).nnz == 0 and F.dtype == np.float32
    resid21, F21 = backend.pooled(notes)  # 16 + 5: the last batch is partial
    assert np.array_equal(resid21[:16], resid)
    enc = backend.subject.encode(notes[16:], batch_size=16)
    assert np.array_equal(resid21[16:], enc.resid) and np.array_equal(F21[16:].toarray(), enc.latents)


def test_corpus_acts_match_token_latents(backend, notes):
    backend.index_corpus(notes)
    full = backend.subject.encode(notes[:4], batch_size=16).latents  # pick latents that fire
    ids = np.concatenate([np.argsort(-full[i])[:5] for i in range(4)] + [[7, 7]]).astype(np.int64)
    got = backend.corpus_acts(ids)
    want = backend.subject.token_latents(notes, ids, batch_size=16)
    assert len(got) == len(want) == len(notes)
    flips = n = 0
    for g, w in zip(got, want):
        assert g.tokens == w.tokens and g.acts.shape == w.acts.shape
        # Float noise in the matmul; it can push a pre-activation across the JumpReLU threshold
        # (measured: 1 flip in 625880 entries over 384 notes), so allow rare on/off flips.
        flip = (g.acts > 0) != (w.acts > 0)
        assert (np.isclose(g.acts, w.acts, rtol=1e-3, atol=1e-3) | flip).all()
        flips, n = flips + flip.sum(), n + flip.size
    assert flips <= 1e-3 * n
    assert len(got[-1].tokens) == 128
    assert np.array_equal(got[0].acts[:, -1], got[0].acts[:, -2])


def test_tool_env_end_to_end(backend, tmp_path):
    """Sample encodings made by the real backend: probe_query on the first 16 sample notes uses the
    same batch, so it reproduces probe_scores bitwise."""
    ep = make_episode(tmp_path / "ep", {"probe_query": 16}, backend=backend)
    env = ts.ToolEnv(ep, backend, tmp_path / "out", tmp_path / "state")
    texts = [t["text"] for t in env.ep.samples[0][:16]]
    q = env.call("probe_query", {"probe": 0, "texts": texts})
    s = env.call("probe_scores", {"probe": 0, "ids": list(range(16))})
    assert q["logits"] == s["logits"]
    m = env.call("latent_means", {"texts": texts[:3]})
    pub = m["top"][0][0][0]
    r = env.call("latent_tokens", {"latents": [pub, pub], "probe": 0, "ids": [0]})
    acts = np.array(r["texts"][0]["acts"])
    assert acts.max() > 0 and np.array_equal(acts[:, 0], acts[:, 1])
    ex = env.call("latent_examples", {"latents": [pub], "n": 3})
    assert "error" not in ex and len(ex["latents"]) == 1
