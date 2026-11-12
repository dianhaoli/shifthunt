"""One-batch (all B texts sent before any result returns, as the agents did) with NOISY readings and
replication allowed. For each (true trap pi, agent's planning pi), the agent picks the allocation of B tests
over (probe, proxy rank) cells that maximises ITS OWN expected P(NAME), decodes Bayes-optimally under its own
prior, and is scored under the true prior. Exact: enumerates allocations and all binomial outcome counts.

Noise: a clean pair on the main reads positive w.p. s; on a non-main w.p. f.
  s = 0.94 (stored scan: main single readings above threshold on 0.918-0.948 of bases);
  f = 0.03 base case (top non-main reaches threshold on at most 0.094 of bases; most non-mains far less).
"""
import sys, json, itertools, time
from math import comb
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from bayes_voi_core import *

RANKS = (1, 2, 3)      # cells the agent may test; set per case (rank 6 added for bank traps)
CAP = 2                # at most 2 readings of one cell


def per_probe_vectors(n):
    out = []
    for v in itertools.product(range(CAP + 1), repeat=len(RANKS)):
        if sum(v) == n:
            out.append(v)
    return out


def allocations(B):
    vecs = {n: per_probe_vectors(n) for n in range(B + 1)}
    allv = [v for n in range(B + 1) for v in vecs[n]]
    allv.sort(reverse=True)
    res = []
    def rec(prefix, start, left):
        if len(prefix) == P:
            if left == 0:
                res.append(tuple(prefix))
            return
        for i in range(start, len(allv)):
            v = allv[i]
            if sum(v) <= left:
                rec(prefix + [v], i, left - sum(v))
    rec([], 0, B)
    return res


def evaluate(alloc, Tsub, wp, wt, C, s, f):
    """Tsub: n_hyp x P x len(RANKS) truth bits. Returns (value under wp, value under wt)."""
    cells = [(j, qi, alloc[j][qi]) for j in range(P) for qi in range(len(RANKS)) if alloc[j][qi] > 0]
    if not cells:
        a = np.argmax(wp @ C)
        return float(wp @ C[:, a]), float(wt @ C[:, a])
    # outcome = number of positives in each cell
    ranges = [range(c + 1) for (_, _, c) in cells]
    outs = np.array(list(itertools.product(*ranges)))          # n_out x n_cells
    L = np.ones((len(outs), Tsub.shape[0]))
    for ci, (j, qi, c) in enumerate(cells):
        p = np.where(Tsub[:, j, qi], s, f)                     # n_hyp
        y = outs[:, ci][:, None]
        binc = np.array([comb(c, k) for k in range(c + 1)])[outs[:, ci]][:, None]
        L *= binc * p[None, :] ** y * (1 - p[None, :]) ** (c - y)
    Mp = (L * wp[None, :]) @ C                                  # n_out x n_answers
    a = np.argmax(Mp, axis=1)
    vp = Mp[np.arange(len(a)), a].sum()
    Mt = (L * wt[None, :]) @ C
    vt = Mt[np.arange(len(a)), a].sum()
    return float(vp), float(vt)


def run(true_pi, plan_pi, Bs, s=0.94, f=0.03, k_known=False, ranks=(1, 2, 3)):
    global RANKS
    RANKS = tuple(ranks)
    H = union_space()
    wt = weights(H, true_pi, k_known=k_known)
    wp = weights(H, plan_pi, k_known=k_known)
    keep = [i for i in range(len(H)) if wt[i] > 0 or wp[i] > 0]
    Hs = [H[i] for i in keep]
    wt, wp = wt[keep], wp[keep]
    A, C = answer_matrix(Hs)
    okA = np.all(np.isin(A, (0,) + tuple(RANKS)), axis=1)
    C = C[:, okA]
    T = test_outcomes(Hs)
    Tsub = T[:, :, [r - 1 for r in RANKS]]
    res = {}
    for B in Bs:
        best = None
        for al in allocations(B):
            if k_known is False:
                pass
            vp, vt = evaluate(al, Tsub, wp, wt, C, s, f)
            if best is None or vp > best[0] + 1e-12:
                best = (vp, vt, al)
        res[B] = {"plan_value": round(best[0], 4), "true_value": round(best[1], 4),
                  "alloc": [dict(zip(map(str, RANKS), v)) for v in best[2]]}
    return res


if __name__ == "__main__":
    cases = {
        "calibrated | shipped traps": (SHIPPED_TRAP, SHIPPED_TRAP),
        "believes top-1 (eps=1e-3) | shipped traps": (SHIPPED_TRAP, smooth(TOP1, 1e-3)),
        "believes top-1 (eps=0.05) | shipped traps": (SHIPPED_TRAP, smooth(TOP1, 0.05)),
        "calibrated | bank traps": (BANK_TRAP, BANK_TRAP),
        "believes shipped rank-2 (eps=1e-3) | bank traps": (BANK_TRAP, smooth(SHIPPED_TRAP, 1e-3)),
        "believes top-1 (eps=1e-3) | bank traps": (BANK_TRAP, smooth(TOP1, 1e-3)),
        "calibrated | no traps": (TOP1, TOP1),
    }
    Bs = [int(x) for x in (sys.argv[1].split(",") if len(sys.argv) > 1 else "0,2,4,6,8".split(","))]
    f = float(sys.argv[2]) if len(sys.argv) > 2 else 0.03
    out = {}
    for name, (pt, pp) in cases.items():
        t0 = time.time()
        rk = (1, 2, 6) if "bank" in name else (1, 2, 3)
        r = run(pt, pp, Bs, f=f, ranks=rk)
        out[name] = r
        print(f"{name:50s}", " ".join(f"B{B}:{r[B]['true_value']:.3f}" for B in Bs), f"({time.time()-t0:.0f}s)", flush=True)
        for B in Bs:
            al = r[B]["alloc"]
            print("      B", B, "alloc (counts per probe at tested ranks):",
                  [tuple(v.values()) for v in al], "plan", r[B]["plan_value"])
    json.dump(out, open(__file__.replace(".py", f"_f{f}.json"), "w"), indent=1)
