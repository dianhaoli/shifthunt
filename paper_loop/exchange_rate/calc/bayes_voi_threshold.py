"""When does a one-batch agent widen (test rank 2) instead of replicating rank 1?
Agent believes a fraction theta of episodes hold a rank-2 trap (true theta = 0.5, shipped mix). B = 8.
Sweeps theta and exact-query sensitivity s. Prints the chosen allocation and its TRUE P(NAME)."""
import sys, json
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import bayes_voi_batch as bb
from bayes_voi_core import *

def run_theta(theta, B, s, f):
    H = union_space()
    wt = weights(H, SHIPPED_TRAP, p_trap_episode=0.5)
    wp = weights(H, SHIPPED_TRAP, p_trap_episode=theta)
    keep = [i for i in range(len(H)) if wt[i] > 0 or wp[i] > 0]
    Hs = [H[i] for i in keep]; wt, wp = wt[keep], wp[keep]
    bb.RANKS = (1, 2)
    A, C = answer_matrix(Hs)
    C = C[:, np.all(np.isin(A, (0, 1, 2)), axis=1)]
    T = test_outcomes(Hs)[:, :, [0, 1]]
    best = None
    for al in bb.allocations(B):
        vp, vt = bb.evaluate(al, T, wp, wt, C, s, f)
        if best is None or vp > best[0] + 1e-12:
            best = (vp, vt, al)
    n_rank2 = sum(v[1] for v in best[2])
    return best[1], n_rank2, best[2]

out = []
for s in (0.99, 0.94, 0.85):
    for theta in (0.0, 0.01, 0.02, 0.04, 0.08, 0.15, 0.3, 0.5):
        vt, n2, al = run_theta(theta, 8, s, 0.03)
        out.append(dict(s=s, theta=theta, true_value=round(vt, 3), rank2_tests=n2, alloc=[list(v) for v in al]))
        print(f"s={s:.2f} theta={theta:.2f}  rank-2 texts={n2}  true P(NAME)={vt:.3f}  alloc(r1,r2)={[tuple(v) for v in al]}", flush=True)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
