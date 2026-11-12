"""Noiseless, adaptive (one test at a time) Bayes-optimal P(NAME) vs B, proxy arm, CALIBRATED agents only
(planning prior = true prior), on the reduced support. Miscalibrated and noisy agents: bayes_voi_batch.py."""
import sys, json, time
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from bayes_voi_core import *

H = union_space()
cases = {
    "shipped traps (rank 2)": SHIPPED_TRAP,
    "bank traps (11/10/3 at ranks 1/2/6)": BANK_TRAP,
    "deep trap (rank 6)": np.eye(8)[5],
    "proxy always right (no traps)": TOP1,
}
out = {}
Bs = list(range(0, 9))
for name, pt in cases.items():
    for kk in (False, True):
        t0 = time.time()
        w = weights(H, pt, k_known=kk)
        dp = NoiselessDP(H, w)
        vals = [round(dp.value(B), 4) for B in Bs]
        key = name + (" | hard probe revealed" if kk else "")
        out[key] = vals
        print(f"{key:55s}", vals, f"n_hyp={dp.n} {time.time()-t0:.1f}s", flush=True)
json.dump({"B": Bs, "values": out}, open(__file__.replace(".py", ".json"), "w"), indent=1)
