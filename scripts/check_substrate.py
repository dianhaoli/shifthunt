"""Gate for the model + SAE substrate: encode speed, the SAE identity and reconstruction quality,
exactness of closed-form mean-ablation against an explicit re-forward (pooled and per-token),
generated-note token lengths, and batch-size invariance.

    python scripts/check_substrate.py [--out report.json]

Needs a GPU and HF_TOKEN (Gemma is gated). All seeds are fixed.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import textgen as tg  # noqa: E402
from shifthunt.ablation import ablate_logits, gradient, probe_logit  # noqa: E402
from shifthunt.substrate import D_SAE, MAX_CONTENT_TOKENS, Subject  # noqa: E402

LOGIT_STD = 3.0
SIZES = (1, 4, 16, 64)
DRAWS = 20

HANDWRITTEN = [
    "Hi.",
    "The council approved the new budget on Tuesday after a long debate about road repairs.",
    "def mean(xs):\n    return sum(xs) / len(xs)\n\nprint(mean([1, 2, 3]))",
    "Shopping list: eggs, milk, two lemons, flour, and something for dinner on Friday.",
    "Q: Why is the sky blue?\nA: Shorter wavelengths scatter more strongly off air molecules.",
    # Long enough to be truncated at MAX_CONTENT_TOKENS content tokens.
    "The history of the bicycle is a story of small improvements. Early machines had no pedals "
    "at all; riders pushed themselves along with their feet. Later designs put pedals on a huge "
    "front wheel, which made them fast but dangerous, and a fall from the high seat could be "
    "serious. The safety bicycle, with two wheels of equal size and a chain driving the rear "
    "wheel, changed everything in the 1880s. Pneumatic tyres followed soon after, making rides "
    "on rough roads far more comfortable, and within a decade cycling clubs had spread across "
    "Europe and North America, giving many people their first cheap way to travel alone. "
    "Today the same basic layout carries hundreds of millions of riders, from children on their "
    "first bike to commuters crossing busy cities every morning.",
]


def fair_coin_note(rng):
    topic = rng.choice(tg.TOPIC_NAMES)
    levels = {f: rng.randrange(2) for f in tg.FEATURES}
    return tg.render(topic, levels, tg.make_cues(rng), rng.getrandbits(32))[0]


def build_texts(seed=0, n_generated=44):
    rng = random.Random(seed)
    gen = [tg.render(tg.TOPIC_NAMES[i % 12], {f: rng.randrange(2) for f in tg.FEATURES},
                     tg.make_cues(rng), rng.getrandbits(32))[0] for i in range(n_generated)]
    return gen + HANDWRITTEN


def random_probe(resid, seed=0):
    """Gaussian direction, scaled so logits on these texts have std LOGIT_STD, centred by b."""
    w = np.random.default_rng(seed).normal(size=resid.shape[1])
    z = resid.astype(np.float64) @ w
    w *= LOGIT_STD / z.std()
    return w, -float(z.mean() * LOGIT_STD / z.std())


def gpu_mib():
    return {"allocated": round(torch.cuda.memory_allocated() / 2**20),
            "peak": round(torch.cuda.max_memory_allocated() / 2**20)}


def check_identity(enc, sae):
    out = {}
    for name, dt in (("float32", np.float32), ("float64", np.float64)):
        recon = enc.latents.astype(dt) @ sae.W_dec.astype(dt) + sae.b_dec.astype(dt) + enc.error.astype(dt)
        out[name] = float(np.abs(recon - enc.resid.astype(dt)).max())
    out["max_abs_resid"] = float(np.abs(enc.resid).max())
    return out


def per_token(subject, texts, batch_size=16):
    """Per-token residuals in the same batches encode() uses (so shapes, hence bf16 numerics, match)."""
    return [subject.resid_tokens(texts[i:i + batch_size]) for i in range(0, len(texts), batch_size)]


@torch.no_grad()
def check_reconstruction(enc, tok_batches, sae):
    # Pooled (one vector per text):
    #   fve_pooled  = 1 - sum_i ||e_i||^2 / sum_i ||r_i - rbar||^2   (rbar = mean over texts)
    #   fve_raw     = mean_i (1 - ||e_i||^2 / ||r_i||^2)             (no centring)
    # Per token (all content tokens of all texts, BOS excluded):
    #   fve_token   = 1 - sum_t ||x_t - xhat_t||^2 / sum_t ||x_t - xbar||^2
    r, e = enc.resid.astype(np.float64), enc.error.astype(np.float64)
    pooled = {
        "fve_centred": float(1 - (e**2).sum() / ((r - r.mean(0))**2).sum()),
        "fve_raw_mean_per_text": float(np.mean(1 - (e**2).sum(1) / (r**2).sum(1))),
        "mean_rel_error_norm": float(np.mean(np.linalg.norm(e, axis=1) / np.linalg.norm(r, axis=1))),
        "mean_resid_norm": float(np.linalg.norm(r, axis=1).mean()),
        "pooled_latent_l0_mean": float((enc.latents > 0).sum(1).mean()),
    }
    xs, errs, l0 = [], [], []
    for tb in tok_batches:
        m = tb.mask.astype(bool)
        x = torch.from_numpy(tb.resid[m]).to(sae.device)
        f = sae.encode(x)
        xs.append(x.double().cpu())
        errs.append((x - sae.decode(f)).double().cpu())
        l0.append((f > 0).sum(1).cpu())
    x, err, l0 = torch.cat(xs), torch.cat(errs), torch.cat(l0).double()
    rel = err.norm(dim=1) / x.norm(dim=1)
    token = {
        "n_tokens": int(x.shape[0]),
        "fve_centred": float(1 - (err**2).sum() / ((x - x.mean(0))**2).sum()),
        "fve_raw": float(1 - (err**2).sum() / (x**2).sum()),
        "mean_rel_error_norm": float(rel.mean()),
        "l0_mean": float(l0.mean()),
        "l0_p50": float(l0.median()),
        "l0_max": int(l0.max()),
        "mean_resid_norm": float(x.norm(dim=1).mean()),
    }
    return {"pooled": pooled, "per_token": token}


def draw_sets(rng, active):
    for kind, pool in (("active", active), ("random", np.arange(D_SAE))):
        for size in SIZES:
            for _ in range(DRAWS):
                yield kind, size, rng.choice(pool, size=size, replace=False)


def check_ablation(enc, sae, w, b, mu, seed=1):
    """Closed form vs pooled re-forward: (F with S columns set to mu[S]) @ W_dec + b_dec + error."""
    rng = np.random.default_rng(seed)
    logits = probe_logit(enc.resid, w, b)
    g = gradient(sae.W_dec, w)
    active = np.flatnonzero(enc.latents.max(0) > 0)
    W32, bd32, w32 = sae.W_dec, sae.b_dec, w.astype(np.float32)
    W64, bd64 = W32.astype(np.float64), bd32.astype(np.float64)
    worst = {}
    for kind, size, S in draw_sets(rng, active):
        closed = ablate_logits(logits, enc.latents, g, mu, S)
        F = enc.latents.copy()
        F[:, S] = mu[S].astype(np.float32)
        re32 = ((F @ W32 + bd32 + enc.error) @ w32 + np.float32(b)).astype(np.float64)
        F64 = enc.latents.astype(np.float64)
        F64[:, S] = mu[S]
        re64 = (F64 @ W64 + bd64 + enc.error.astype(np.float64)) @ w + b
        k = f"{kind} |S|={size}"
        cur = worst.setdefault(k, {"max_diff_f32": 0.0, "max_diff_f64": 0.0, "mean_abs_effect": 0.0})
        cur["max_diff_f32"] = max(cur["max_diff_f32"], float(np.abs(closed - re32).max()))
        cur["max_diff_f64"] = max(cur["max_diff_f64"], float(np.abs(closed - re64).max()))
        cur["mean_abs_effect"] += float(np.abs(closed - logits).mean()) / DRAWS
    overall = max(max(v["max_diff_f32"], v["max_diff_f64"]) for v in worst.values())
    empty_ok = bool(np.array_equal(ablate_logits(logits, enc.latents, g, mu, []), logits))
    S = rng.choice(active, size=8, replace=False)
    dup_ok = bool(np.array_equal(ablate_logits(logits, enc.latents, g, mu, np.concatenate([S, S[:3]])),
                                 ablate_logits(logits, enc.latents, g, mu, S[::-1])))
    return {"n_active_latents": int(active.size), "by_set": worst, "worst_abs_diff": overall,
            "worst_rel_to_logit_std": overall / float(logits.std()),
            "empty_set_identity": empty_ok, "duplicates_and_order_ignored": dup_ok}


@torch.no_grad()
def check_token_ablation(enc16, tb, sae, w, b, mu, seed=2):
    """Per-token mean-ablation, done explicitly, against the closed form on pooled latents.

    For each content token: f_t = encode(x_t), err_t = x_t - decode(f_t); set f_t[S] = mu[S];
    x'_t = decode(f_t') + err_t; pool x'_t over content tokens; logit = pooled @ w + b.
    This agrees with the closed form because pooling is a mean (linear) and decode is affine:
    mean_t decode(f_t') = decode(mean_t f_t'), mean_t f_t'[S] = mu[S] (a constant pools to itself),
    and mean_t err_t is exactly the pooled error. enc16 must come from the same batch as tb so
    both sides see bit-identical residuals.
    """
    rng = np.random.default_rng(seed)
    logits = probe_logit(enc16.resid, w, b)
    g = gradient(sae.W_dec, w)
    active = np.flatnonzero(enc16.latents.max(0) > 0)
    dev = sae.device
    x = torch.from_numpy(tb.resid).to(dev)
    m = torch.from_numpy(tb.mask).to(dev).double()[..., None]
    f = sae.encode(x)
    W = {torch.float32: sae._t["W_dec"], torch.float64: sae._t["W_dec"].double()}
    bd = {torch.float32: sae._t["b_dec"], torch.float64: sae._t["b_dec"].double()}
    wt = {dt: torch.from_numpy(w).to(dev, dt) for dt in W}
    mut = torch.from_numpy(mu).to(dev)
    out = {}
    for size in SIZES:
        for kind, pool in (("active", active), ("random", np.arange(D_SAE))):
            for _ in range(5):
                S = rng.choice(pool, size=size, replace=False)
                closed = ablate_logits(logits, enc16.latents, g, mu, S)
                St = torch.from_numpy(S).to(dev)
                for dt in (torch.float32, torch.float64):
                    ft, xt = f.to(dt), x.to(dt)
                    err = xt - (ft @ W[dt] + bd[dt])
                    fa = ft.clone()
                    fa[..., St] = mut[St].to(dt)
                    xa = fa @ W[dt] + bd[dt] + err
                    pooled = (xa * m.to(dt)).sum(1) / m.to(dt).sum(1)
                    re = (pooled @ wt[dt] + b).double().cpu().numpy()
                    k = f"{kind} |S|={size} {str(dt)[6:]}"
                    out[k] = max(out.get(k, 0.0), float(np.abs(re - closed).max()))
    # No-ablation baseline: token path vs encode() pooled resid (same batch).
    pooled0 = ((x.double() * m).sum(1) / m.sum(1)).cpu().numpy()
    base = float(np.abs(pooled0 @ w + b - logits).max())
    return {"n_texts": int(len(logits)), "baseline_logit_diff": base, "max_abs_diff": out,
            "worst": max(out.values())}


def check_lengths(tokenizer, n=500, seed=3):
    rng = random.Random(seed)
    a = np.array([len(tokenizer(fair_coin_note(rng), add_special_tokens=False).input_ids) for _ in range(n)])
    return {"n": n, "mean": round(float(a.mean()), 1), "p50": float(np.median(a)),
            "p95": float(np.percentile(a, 95)), "max": int(a.max()),
            "frac_over_window": round(float((a > MAX_CONTENT_TOKENS).mean()), 3)}


def check_batch_invariance(subject, texts, enc16, w, b):
    enc1 = subject.encode(texts, batch_size=1)
    d = np.abs(enc16.resid - enc1.resid)
    rel = np.linalg.norm(enc16.resid - enc1.resid, axis=1) / np.linalg.norm(enc1.resid, axis=1)
    return {"resid_max_abs_diff": float(d.max()), "resid_max_rel_norm_diff": float(rel.max()),
            "latents_max_abs_diff": float(np.abs(enc16.latents - enc1.latents).max()),
            "latent_support_changes": int(((enc16.latents > 0) != (enc1.latents > 0)).sum()),
            "logit_max_abs_diff": float(np.abs(probe_logit(enc16.resid, w, b) - probe_logit(enc1.resid, w, b)).max()),
            "n_tokens_equal": bool(np.array_equal(enc16.n_tokens, enc1.n_tokens))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    torch.manual_seed(0)
    rep = {}

    t0 = time.time()
    subject = Subject()
    rep["load_s"] = round(time.time() - t0, 1)
    rep["gpu_mib_after_load"] = gpu_mib()

    texts = build_texts()
    t0 = time.time()
    enc = subject.encode(texts, batch_size=16)
    torch.cuda.synchronize()
    cold = time.time() - t0
    t0 = time.time()
    enc = subject.encode(texts, batch_size=16)
    torch.cuda.synchronize()
    rep["encode"] = {"n_texts": len(texts), "cold_s": round(cold, 2), "warm_s": round(time.time() - t0, 2),
                     "n_tokens_min": int(enc.n_tokens.min()), "n_tokens_mean": round(float(enc.n_tokens.mean()), 1),
                     "n_tokens_max": int(enc.n_tokens.max()), "n_truncated": int((enc.n_tokens == MAX_CONTENT_TOKENS).sum()),
                     "gpu_mib": gpu_mib()}
    print("load:", rep["load_s"], "s;", "gpu after load:", rep["gpu_mib_after_load"])
    print("encode:", rep["encode"])

    sae = subject.sae
    rep["identity_max_abs_diff"] = check_identity(enc, sae)
    print("identity resid == latents @ W_dec + b_dec + error:", rep["identity_max_abs_diff"])

    tok_batches = per_token(subject, texts)
    rep["reconstruction"] = check_reconstruction(enc, tok_batches, sae)
    print("reconstruction pooled:", rep["reconstruction"]["pooled"])
    print("reconstruction per token:", rep["reconstruction"]["per_token"])

    w, b = random_probe(enc.resid)
    mu = enc.latents.astype(np.float64).mean(0)
    rep["probe"] = {"w_norm": float(np.linalg.norm(w)), "logit_std": float(probe_logit(enc.resid, w, b).std())}
    rep["ablation_pooled"] = a = check_ablation(enc, sae, w, b, mu)
    print(f"probe: ||w|| {rep['probe']['w_norm']:.4g}, logit std {rep['probe']['logit_std']:.3f}")
    print(f"pooled ablation, {DRAWS} draws per cell ({a['n_active_latents']} latents active on >=1 text):")
    for k, v in a["by_set"].items():
        print(f"  {k:16s} f32 {v['max_diff_f32']:.2e}  f64 {v['max_diff_f64']:.2e}  mean |effect| {v['mean_abs_effect']:.3g}")
    print(f"  worst {a['worst_abs_diff']:.2e} ({a['worst_rel_to_logit_std']:.2e} of logit std); "
          f"empty S identity {a['empty_set_identity']}; duplicates/order ignored {a['duplicates_and_order_ignored']}")

    enc_b0 = subject.encode(texts[:16], batch_size=16)
    rep["ablation_token"] = t = check_token_ablation(enc_b0, tok_batches[0], sae, w, b, mu)
    print(f"token-level ablation on {t['n_texts']} texts (5 draws per cell), baseline diff {t['baseline_logit_diff']:.2e}:")
    for k, v in t["max_abs_diff"].items():
        print(f"  {k:22s} {v:.2e}")

    rep["token_lengths"] = check_lengths(subject.tokenizer)
    print("token lengths of 500 fair-coin notes (no BOS, untruncated):", rep["token_lengths"])

    rep["batch_invariance"] = check_batch_invariance(subject, texts, enc, w, b)
    print("batch 16 vs 1:", rep["batch_invariance"])

    gate = a["worst_abs_diff"] < 1e-3 and t["worst"] < 1e-3 and a["empty_set_identity"] and a["duplicates_and_order_ignored"]
    rep["gate_pass"] = bool(gate)
    print("GATE", "PASS" if gate else "FAIL")
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=1))
    sys.exit(0 if gate else 1)


if __name__ == "__main__":
    main()
