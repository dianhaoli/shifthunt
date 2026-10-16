"""GPU tests for shifthunt.substrate. Skipped without CUDA or HF_TOKEN (Gemma is gated)."""
import os
import random

import numpy as np
import pytest
import torch

from shifthunt import textgen as tg
from shifthunt.ablation import ablate_logits, gradient, probe_logit
from shifthunt.substrate import D_RESID, D_SAE, MAX_CONTENT_TOKENS

pytestmark = pytest.mark.skipif(not torch.cuda.is_available() or not os.environ.get("HF_TOKEN"),
                                reason="needs CUDA and HF_TOKEN")

# Pooled residuals of one text move by ~0.3% (relative L2) when the batch shape changes; this is
# bf16 kernel numerics, not padding leaking in (measured in scripts/check_substrate.py).
SHAPE_RTOL = 1e-2
SHORT = "Hi."
LONG = " ".join(["The quick brown fox jumps over the lazy dog."] * 15)


@pytest.fixture(scope="module")
def subject():
    from shifthunt.substrate import Subject
    return Subject()


@pytest.fixture(scope="module")
def texts():
    rng = random.Random(0)
    notes = [tg.render(tg.TOPIC_NAMES[i % 12], {f: rng.randrange(2) for f in tg.FEATURES},
                       tg.make_cues(rng), rng.getrandbits(32))[0] for i in range(14)]
    return notes + [SHORT, LONG]


@pytest.fixture(scope="module")
def enc(subject, texts):
    return subject.encode(texts, batch_size=len(texts))


def rel_diff(a, b):
    return float(np.linalg.norm(a - b) / np.linalg.norm(b))


def test_shapes_and_dtypes(enc, texts):
    n = len(texts)
    assert enc.resid.shape == (n, D_RESID) and enc.resid.dtype == np.float32
    assert enc.latents.shape == (n, D_SAE) and enc.latents.dtype == np.float32
    assert enc.error.shape == (n, D_RESID) and enc.error.dtype == np.float32
    assert enc.n_tokens.shape == (n,) and enc.n_tokens.dtype == np.int64
    assert (enc.latents >= 0).all()


def test_pool_is_mean_over_content_tokens(subject, texts, enc):
    tr = subject.resid_tokens(texts)  # same batch as enc, so bit-identical residuals
    assert (tr.mask[:, 0] == 0).all() and (tr.input_ids[:, 0] == subject.tokenizer.bos_token_id).all()
    assert np.array_equal(tr.mask.sum(1), enc.n_tokens)
    pad = tr.input_ids == subject.tokenizer.pad_token_id
    assert pad.any() and (tr.mask[pad] == 0).all()
    m = tr.mask[..., None].astype(np.float64)
    pooled = (tr.resid * m).sum(1) / m.sum(1)
    np.testing.assert_allclose(enc.resid, pooled, atol=1e-4, rtol=0)
    # Sanity: including BOS would change the pool a lot, so the check above has teeth.
    with_bos = (tr.resid * (m + (np.arange(m.shape[1]) == 0)[None, :, None])).sum(1) / (m.sum(1) + 1)
    assert rel_diff(with_bos[0], pooled[0]) > 0.1


def test_padding_does_not_leak(subject):
    # Coarse: across batch shapes only bf16 numerics differ. The exact check is the next test.
    alone = subject.encode([SHORT]).resid[0]
    padded = subject.encode([SHORT, LONG]).resid[0]
    assert rel_diff(padded, alone) < SHAPE_RTOL


def test_padding_is_bitwise_invisible(subject):
    # At a fixed batch shape, neither pad ids nor another row's content may touch content positions.
    enc = subject._tokenize([SHORT, LONG])
    content = enc.attention_mask.bool()
    x0 = subject._resid(enc)
    pad = ~content
    assert pad.any()
    gen = torch.Generator(device=enc.input_ids.device).manual_seed(0)
    enc["input_ids"][pad] = torch.randint(3, subject.model.config.vocab_size, (int(pad.sum()),),
                                          generator=gen, device=enc.input_ids.device)
    x1 = subject._resid(enc)
    assert torch.equal(x0[content], x1[content])
    other = subject._tokenize([SHORT, LONG.replace("fox", "cat")])
    assert torch.equal(other.attention_mask, enc.attention_mask)
    row0 = content[0]
    assert torch.equal(x0[0][row0], subject._resid(other)[0][row0])


def test_truncation(subject, enc, texts):
    assert enc.n_tokens[texts.index(LONG)] == MAX_CONTENT_TOKENS
    assert enc.n_tokens[texts.index(SHORT)] < MAX_CONTENT_TOKENS
    # Anything past the window is invisible: same shape [1, MAX_CONTENT_TOKENS + 1], so bitwise equal.
    a = subject.encode([LONG]).resid
    b = subject.encode([LONG + " Something else entirely."]).resid
    assert np.array_equal(a, b)


def test_identity(subject, enc):
    sae = subject.sae
    recon = enc.latents.astype(np.float64) @ sae.W_dec + sae.b_dec + enc.error
    assert np.abs(recon - enc.resid).max() < 1e-3


def test_closed_form_ablation_matches_reforward(subject, enc):
    sae, rng = subject.sae, np.random.default_rng(0)
    w = rng.normal(size=D_RESID)
    w *= 3.0 / (enc.resid @ w).std()
    b = 0.5
    logits = probe_logit(enc.resid, w, b)
    g, mu = gradient(sae.W_dec, w), enc.latents.astype(np.float64).mean(0)
    active = np.flatnonzero(enc.latents.max(0) > 0)
    for size in (1, 4, 16, 64):
        S = rng.choice(active, size=size, replace=False)
        F = enc.latents.copy()
        F[:, S] = mu[S]
        re = (F @ sae.W_dec + sae.b_dec + enc.error) @ w.astype(np.float32) + np.float32(b)
        assert np.abs(ablate_logits(logits, enc.latents, g, mu, S) - re).max() < 1e-3


def test_token_latents_average_to_pooled(subject, texts, enc):
    ids = np.concatenate([np.argsort(-enc.latents.mean(0))[:8], [0, 123, D_SAE - 1]])
    recs = subject.token_latents(texts, ids, batch_size=len(texts))  # same batch as enc
    assert len(recs) == len(texts)
    for i, (rec, text) in enumerate(zip(recs, texts)):
        assert rec.acts.shape == (enc.n_tokens[i], len(ids)) and rec.acts.dtype == np.float32
        assert len(rec.tokens) == enc.n_tokens[i]
        if enc.n_tokens[i] < MAX_CONTENT_TOKENS:
            assert "".join(rec.tokens) == text
        np.testing.assert_allclose(rec.acts.mean(0), enc.latents[i, ids], atol=1e-4, rtol=1e-5)


def test_token_latents_keeps_column_order(subject):
    ids = [123, 0, 123, 7]
    a = subject.token_latents([SHORT], ids)[0].acts
    b = subject.token_latents([SHORT], ids[::-1])[0].acts
    assert np.array_equal(a, b[:, ::-1]) and np.array_equal(a[:, 0], a[:, 2])


def test_literal_special_tokens_are_text(subject):
    special = {subject.tokenizer.bos_token_id, subject.tokenizer.pad_token_id,
               subject.tokenizer.eos_token_id}
    tr = subject.resid_tokens(["<bos>The cat sat.", "The <pad> cat <eos> sat."])
    assert (tr.input_ids[:, 0] == subject.tokenizer.bos_token_id).all()
    assert not np.isin(tr.input_ids[tr.mask == 1], list(special)).any()
    assert (tr.input_ids[0] == subject.tokenizer.bos_token_id).sum() == 1


def test_bad_inputs_raise(subject):
    with pytest.raises(ValueError):
        subject.token_latents(["x"], [D_SAE])
    with pytest.raises(ValueError):
        subject.token_latents(["x"], [-1])
    with pytest.raises(ValueError):  # would truncate to 3
        subject.token_latents(["x"], [3.9, 3])
    with pytest.raises(ValueError):  # a mask, not ids
        subject.token_latents(["x"], np.array([True, False, True]))
    with pytest.raises(ValueError):
        subject.token_latents(["x"], [[1, 2]])
    with pytest.raises(TypeError):
        subject.token_latents("abc", [0])
    with pytest.raises(TypeError):
        subject.encode("abc")
    with pytest.raises(ValueError):
        subject.encode([""])


def test_empty_inputs(subject):
    enc = subject.encode([])
    assert enc.resid.shape == (0, D_RESID) and enc.resid.dtype == np.float32
    assert enc.latents.shape == (0, D_SAE) and enc.latents.dtype == np.float32
    assert enc.error.shape == (0, D_RESID) and enc.n_tokens.dtype == np.int64
    assert subject.token_latents([], [0]) == []
    rec = subject.token_latents([SHORT], [])[0]
    assert rec.tokens and rec.acts.shape == (len(rec.tokens), 0)
