"""Monte Carlo of the abstract episode with graded (noisy) exact readings, used to check the abstract model
against the repo's scripted numbers (top-one 0.50, top-two 0.96, best blind 0.40 / 0.80 / 0.93).
No data, no episode ids, no property names. Effect sizes are drawn from the aggregate ranges in exp_c.json.

Reading of a text that flips the candidate set S of one probe, averaged over R base notes:
    sum_{c in S} e_c  +  N(0, s^2 / R),   s = sig1 if |S| = 1 else sigG
positive iff reading > THETA = 0.225 topic units (the scripted policies' rule).
Per-probe true effects (topic units):
    trap main  ~ U(0.35, 0.49)      (exp_c: shipped trap |true ratio| 0.35-0.49)
    nested main~ U(0.36, 0.57)      (exp_c: shipped nested 0.36-0.57)
    ordinary   ~ U(0.30, 0.60)
    non-main candidates: iid Exp(mu0) capped at 0.15 (contract: every other property <= 0.15)
    trap decoy (proxy rank 1) ~ U(0.006, 0.06) (exp_c: 0.006-0.06); nested parent (rank 2) ~ U(0.05, 0.07)
"""
import numpy as np

THETA = 0.225


def make_episodes(N, rng, mu0, piT=None, piN=None, p_trap=0.5):
    """Return dict of arrays. eff[N,4,8] indexed by PROXY RANK (0-based); main_rank[N,4] (-1 for null);
    hard[N], null[N] probe indices; kind[N] (1 = trap)."""
    piT = piT or {2: 1.0}
    piN = piN or {1: 1.0}
    eff = np.minimum(rng.exponential(mu0, size=(N, 4, 8)), 0.15)
    kind = (rng.random(N) < p_trap).astype(int)
    perm = np.argsort(rng.random((N, 4)), axis=1)
    hard, null = perm[:, 0], perm[:, 1]
    main_rank = np.full((N, 4), -1)
    ar = np.arange(N)
    # ordinary probes: rank 1
    for j in (2, 3):
        p = perm[:, j]
        main_rank[ar, p] = 0
        eff[ar, p, 0] = rng.uniform(0.30, 0.60, N)
    # hard probe
    rT = np.array(list(piT.keys())) - 1
    wT = np.array(list(piT.values()), float)
    rN = np.array(list(piN.keys())) - 1
    wN = np.array(list(piN.values()), float)
    r_trap = rng.choice(rT, size=N, p=wT / wT.sum())
    r_nest = rng.choice(rN, size=N, p=wN / wN.sum())
    r_h = np.where(kind == 1, r_trap, r_nest)
    main_rank[ar, hard] = r_h
    m = np.where(kind == 1, rng.uniform(0.35, 0.49, N), rng.uniform(0.36, 0.57, N))
    # decoy / parent at the top non-main rank
    top_nonmain = np.where(r_h == 0, 1, 0)
    dec = np.where(kind == 1, rng.uniform(0.006, 0.06, N), rng.uniform(0.05, 0.07, N))
    eff[ar, hard, top_nonmain] = dec
    eff[ar, hard, r_h] = m
    return dict(eff=eff, main_rank=main_rank, hard=hard, null=null, kind=kind, N=N)


def read(eff_sets, n_members, rng, sig1, sigG, R):
    s = np.where(n_members == 1, sig1, sigG) / np.sqrt(R)
    return eff_sets + rng.normal(0, 1, size=eff_sets.shape) * s > THETA


def name_success(ep, answer):
    """answer[N,4] = claimed rank (0-based) or -1 for none (at most one claim per probe here)."""
    ar = np.arange(ep["N"])
    h_ok = answer[ar, ep["hard"]] == ep["main_rank"][ar, ep["hard"]]
    n_ok = answer[ar, ep["null"]] == -1
    return h_ok & n_ok


def policy_prefix(ep, B, w, rng, sig1, sigG):
    """Isolate proxy ranks 1..w on every probe, R = max(1, B // (4w)) bases per reading; claim the positive
    candidate (if two read positive, the claim set has two members -> wrong for a one-main probe)."""
    R = max(1, B // (4 * w))
    eff = ep["eff"][:, :, :w]
    pos = read(eff, np.ones_like(eff), rng, sig1, sigG, R)
    npos = pos.sum(axis=2)
    first = np.where(npos > 0, pos.argmax(axis=2), -1)
    answer = np.where(npos == 1, first, np.where(npos == 0, -1, -2))  # -2 = two claims
    return name_success(ep, answer)


def policy_blind_iic(ep, B, rng, sig1, sigG):
    """blind_verify (ii-c): bisection, no screen, then confirm. R = max(1, B // 16) bases per reading.
    Probes in random order; each search costs 4R texts; unfinished probes are answered none."""
    N = ep["N"]
    R = max(1, B // 16)
    nsearch = min(4, B // (4 * R))
    order = np.argsort(rng.random((N, 4)), axis=1)
    answer = np.full((N, 4), -1)
    ar = np.arange(N)
    for s in range(nsearch):
        p = order[:, s]
        eff = ep["eff"][ar, p, :]                    # [N,8] by proxy rank; blind agent ignores the rank
        cand = np.argsort(rng.random((N, 8)), axis=1)  # random candidate order
        lo, size = np.zeros(N, int), 8
        while size > 1:
            half = size // 2
            idx = cand[ar[:, None], lo[:, None] + np.arange(half)[None, :]]
            g = eff[ar[:, None], idx].sum(axis=1)
            pos = read(g, np.full(N, half), rng, sig1, sigG, R)
            lo = np.where(pos, lo, lo + half)
            size = half
        c = cand[ar, lo]
        conf = read(eff[ar, c], np.ones(N), rng, sig1, sigG, R)
        answer[ar, p] = np.where(conf, c, -1)
    return name_success(ep, answer)


def fit_targets():
    """Repo scripted numbers to reproduce (exact back-end, topic unit)."""
    return {
        ("top2", 8): (0.96, 0.96), ("top1", 8): (0.00, 1.00), ("top2", 16): (0.99, 1.00),
        ("blind", 8): (0.38, 0.42), ("blind", 16): (0.76, 0.84), ("blind", 32): (0.83, 0.94),
        ("blind", 64): (0.88, 0.99),
    }


def run_cell(pol, B, params, N=20000, seed=1, piT=None, noiseless=False):
    mu0, sig1, sigG = params
    rng = np.random.default_rng(seed)
    ep = make_episodes(N, rng, 0.0 if noiseless else mu0, piT=piT)
    if noiseless:
        # noiseless reference: main reads 1, everything else 0 (blind_verify's convention)
        ep["eff"] = np.zeros_like(ep["eff"])
        ar = np.arange(N)
        for i in range(4):
            mr = ep["main_rank"][:, i]
            ok = mr >= 0
            ep["eff"][ar[ok], i, mr[ok]] = 1.0
        sig1 = sigG = 1e-9
    if pol == "top1":
        s = policy_prefix(ep, B, 1, rng, sig1, sigG)
    elif pol == "top2":
        s = policy_prefix(ep, B, 2, rng, sig1, sigG)
    elif pol.startswith("top"):
        s = policy_prefix(ep, B, int(pol[3:]), rng, sig1, sigG)
    else:
        s = policy_blind_iic(ep, B, rng, sig1, sigG)
    k = ep["kind"] == 1
    return float(s[k].mean()), float(s[~k].mean()), float(s.mean())
