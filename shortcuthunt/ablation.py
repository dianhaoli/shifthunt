"""Probe logits and SAE mean-ablation, in pure numpy (no model, no torch).

A probe reads the pooled layer-12 residual: logit = resid @ w + b. The SAE splits that residual as

    resid = F @ W_dec + b_dec + error

where F holds the pooled latent activations and error is the SAE reconstruction error. So the logit
is linear in F with gradient g = W_dec @ w (one number per latent).

Mean-ablating a latent set S replaces F[:, S] by the reference means mu[S] and keeps the error term
(and every other latent) as is. The logit then moves by exactly -(F[:, S] - mu[S]) @ g[S], which is
what ablate_logits computes; it never needs the residual or the decoder.

Per-token and pooled mean-ablation are the same thing here. Pooling is a mean over tokens (linear)
and the decoder is affine, so replacing every token's activation of latent i by the constant mu_i
pools to mu_i, and decoding the pooled latents plus the pooled error gives back the pooled residual.

All functions compute in float64 and return float64 arrays, so results are exact up to float64
rounding and independent of the order of ids in S.
"""
import numpy as np


def probe_logit(resid, w, b):
    """resid [n, d] @ w [d] + b -> logits [n] (float64)."""
    return np.asarray(resid, np.float64) @ np.asarray(w, np.float64) + float(b)


def gradient(W_dec, w):
    """g = W_dec @ w: logit change per unit of each latent. W_dec [m, d], w [d] -> g [m] (float64)."""
    return np.asarray(W_dec, np.float64) @ np.asarray(w, np.float64)


def latent_ids(S, m):
    """Validate a set of latent ids against width m; return them sorted and deduplicated (int64)."""
    S = np.asarray(S)
    if S.ndim != 1:
        raise ValueError(f"latent ids must be 1-D, got shape {S.shape}")
    if S.size == 0:
        return np.zeros(0, np.int64)
    if S.dtype.kind not in "iu":  # bool is rejected too: a mask would silently index as 0/1
        raise ValueError(f"latent ids must be integers, got dtype {S.dtype}")
    if S.min() < 0 or S.max() >= m:
        raise ValueError(f"latent ids must be in [0, {m}), got min {S.min()} max {S.max()}")
    return np.unique(S).astype(np.int64)


def ablate_logits(logits, F, g, mu, S):
    """Logits after mean-ablating latents S: logits - (F[:, S] - mu[S]) @ g[S].

    logits [n], F [n, m] pooled latents, g [m] = W_dec @ w, mu [m] reference means, S latent ids
    (repeats are ignored, order does not matter). Returns a new float64 array [n]; for empty S it
    equals logits.
    """
    logits = np.array(logits, np.float64)  # always a copy
    F = np.asarray(F)
    n, m = F.shape
    if logits.shape != (n,) or np.shape(g) != (m,) or np.shape(mu) != (m,):
        raise ValueError(f"shape mismatch: logits {logits.shape}, F {F.shape}, "
                         f"g {np.shape(g)}, mu {np.shape(mu)}")
    S = latent_ids(S, m)
    if S.size == 0:
        return logits
    delta = F[:, S].astype(np.float64) - np.asarray(mu, np.float64)[S]
    return logits - delta @ np.asarray(g, np.float64)[S]
