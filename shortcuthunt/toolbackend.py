"""Encoders behind the tool server: the real Gemma/SAE subject and a cheap deterministic fake.

Backend protocol (all latent ids here are TRUE ids; the server maps public ids before calling):
  pooled(texts) -> (resid float32 [n, D_RESID], latents CSR float32 [n, D_SAE]), encoded in
      consecutive batches of BATCH_SIZE (the last one may be smaller). For a multiple of BATCH_SIZE
      texts this is bitwise hidden.encode_sparse.
  token_acts(texts, ids) -> [substrate.TokenActs], one per text, columns = ids (order and repeats kept).
  index_corpus(texts): per-token layer-12 residuals of the corpus, computed once.
  corpus_acts(ids) -> [TokenActs] for every indexed corpus text, columns = ids.

RealBackend.corpus_acts computes only the requested latents (W_enc columns, b_enc, threshold) from
the stored residuals; it equals Subject.token_latents on the same batches up to float noise.
This module imports torch only inside RealBackend, so the fake path (and the tests) never need it.
"""
import hashlib
import warnings
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

D_RESID, D_SAE = 2304, 16384  # == substrate.D_RESID, D_SAE (substrate imports torch)
BATCH_SIZE = 16  # == probes.BATCH_SIZE
MAX_CONTENT_TOKENS = 128  # == substrate.MAX_CONTENT_TOKENS


def batches(texts, size=BATCH_SIZE):
    return [texts[i:i + size] for i in range(0, len(texts), size)]


@dataclass
class TokenActs:
    """Same fields as substrate.TokenActs (which cannot be imported without torch)."""
    tokens: list
    acts: np.ndarray  # [T, len(ids)] float32


class FakeBackend:
    """Hash-seeded stand-in: tokens are whitespace-split words (first MAX_CONTENT_TOKENS); each
    distinct token has a fixed random residual and K active latents. Pooling is the token mean."""

    K = 8

    def __init__(self, seed=0):
        self.seed = seed
        self._cache = {}
        self.corpus = []
        self.calls = []  # (method, n_texts), for tests

    def _token(self, tok):
        if tok not in self._cache:
            h = hashlib.sha256(f"{self.seed}:{tok}".encode("utf-8", "surrogatepass")).digest()
            rng = np.random.default_rng(int.from_bytes(h[:8], "little"))
            ids = rng.choice(D_SAE, self.K, replace=False)
            vals = rng.exponential(1.0, self.K).astype(np.float32) + np.float32(0.1)
            self._cache[tok] = (rng.standard_normal(D_RESID).astype(np.float32), ids, vals)
        return self._cache[tok]

    @staticmethod
    def tokens(text):
        return text.split()[:MAX_CONTENT_TOKENS] or [text]

    def pooled(self, texts):
        self.calls.append(("pooled", len(texts)))
        resid = np.zeros((len(texts), D_RESID), np.float32)
        lat = np.zeros((len(texts), D_SAE), np.float32)
        for i, text in enumerate(texts):
            toks = self.tokens(text)
            for tok in toks:
                r, ids, vals = self._token(tok)
                resid[i] += r
                lat[i, ids] += vals
            resid[i] /= len(toks)
            lat[i] /= len(toks)
        return resid, sp.csr_matrix(lat)

    def token_acts(self, texts, ids):
        self.calls.append(("token_acts", len(texts)))
        ids = np.asarray(ids, np.int64)
        out = []
        for text in texts:
            toks = self.tokens(text)
            acts = np.zeros((len(toks), len(ids)), np.float32)
            for t, tok in enumerate(toks):
                _, tid, vals = self._token(tok)
                hit = dict(zip(tid.tolist(), vals.tolist()))
                acts[t] = [hit.get(i, 0.0) for i in ids.tolist()]
            out.append(TokenActs(toks, acts))
        return out

    def index_corpus(self, texts):
        self.corpus = list(texts)

    def corpus_acts(self, ids):
        return self.token_acts(self.corpus, ids)


class RealBackend:
    """substrate.Subject on `device`; corpus per-token residuals stay on the device in float32."""

    def __init__(self, device="cuda"):
        from .substrate import Subject
        self.subject = Subject(device)
        self._x = None

    def pooled(self, texts):
        resid, lat = [], []
        for batch in batches(list(texts)):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                enc = self.subject.encode(batch, batch_size=BATCH_SIZE)
            if any("OOM" in str(c.message) for c in caught):
                raise RuntimeError("encode fell back to a smaller batch; results would not match")
            resid.append(enc.resid)
            lat.append(sp.csr_matrix(enc.latents))
        return np.concatenate(resid), sp.vstack(lat).tocsr()

    def token_acts(self, texts, ids):
        return self.subject.token_latents(list(texts), np.asarray(ids, np.int64), batch_size=BATCH_SIZE)

    def index_corpus(self, texts):
        import torch
        s, xs, self._tokens = self.subject, [], []
        with torch.no_grad():
            for batch in batches(list(texts)):
                enc = s._tokenize(batch)
                mask = s._content_mask(enc).bool()
                xs.append(s._resid(enc)[mask])  # [content tokens, D_RESID], text-major
                ids, m = enc.input_ids.cpu().numpy(), mask.cpu().numpy()
                self._tokens += [[s.tokenizer.decode([t]) for t in ids[b][m[b]]] for b in range(len(batch))]
        self._x = torch.cat(xs)
        self._offsets = np.cumsum([0] + [len(t) for t in self._tokens])

    def corpus_acts(self, ids):
        import torch
        t = self.subject.sae._t
        idx = torch.as_tensor(np.asarray(ids, np.int64), device=self._x.device)
        with torch.no_grad():
            pre = self._x @ t["W_enc"][:, idx] + t["b_enc"][idx]
            acts = (pre * (pre > t["threshold"][idx])).cpu().numpy()
        off = self._offsets
        return [TokenActs(tok, acts[a:b]) for tok, a, b in zip(self._tokens, off[:-1], off[1:])]
