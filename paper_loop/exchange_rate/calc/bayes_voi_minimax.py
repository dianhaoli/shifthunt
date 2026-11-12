"""Adversarial item designer: chooses where the hard (trap) probe's main sits in the proxy ranking.
Agent best-responds (knows the designer's mixed strategy). Noiseless, adaptive optimum via exact DP.
Also the bit accounting: entropy of the decision-relevant hypothesis with and without the proxy."""
import sys, json, time
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from bayes_voi_core import *

def H2(p):
    p = np.asarray([x for x in p if x > 0]); return float(-(p * np.log2(p)).sum())

def class_entropy(pi_trap, p_trap=0.5):
    # trap episodes: (k, m, r) all observable; two-part episodes: only m observable (all planted at rank 1)
    # a trap whose main sits at rank 1 is observationally an ordinary probe: merge it with the two-part class
    cls = {}
    for k in range(4):
        for m in range(4):
            if m != k:
                for r in range(8):
                    if pi_trap[r] > 0:
                        key = (m, k, r) if r > 0 else (m,)
                        cls[key] = cls.get(key, 0) + p_trap / 12 * pi_trap[r]
    for m in range(4):
        cls[(m,)] = cls.get((m,), 0) + (1 - p_trap) / 4
    return H2(list(cls.values()))

out = {"bits": {}, "minimax": {}}
blind_bits = np.log2(4) + 3 * np.log2(8)
out["bits"]["blind (null position x 3 mains)"] = blind_bits
for name, pi in [("shipped", SHIPPED_TRAP), ("bank", BANK_TRAP), ("uniform 2..8", np.r_[0, np.ones(7) / 7]),
                 ("uniform 1..8", UNIFORM), ("no traps", TOP1)]:
    h = class_entropy(pi)
    out["bits"][f"proxy, {name}"] = h
    print(f"bits remaining with proxy, {name:14s}: {h:.2f}  (proxy supplies {blind_bits - h:.2f} of {blind_bits:.0f})")
# information per single exact test
print("bits per single test: blind 1-of-8 =", round(H2([1/8, 7/8]), 3),
      "; proxy rank-1 test, calibrated shipped (P(pos)=5/8) =", round(H2([5/8, 3/8]), 3))

H = union_space()
MAXB = int(sys.argv[1]) if len(sys.argv) > 1 else 7
for name, pi in [("uniform over ranks 2..8", np.r_[0, np.ones(7) / 7])]:
    t0 = time.time()
    w = weights(H, pi)
    dp = NoiselessDP(H, w)
    vals = []
    for B in range(0, MAXB + 1):
        vals.append(round(dp.value(B), 4))
        print(name, "B", B, vals[-1], f"{time.time()-t0:.0f}s", flush=True)
    out["minimax"][name] = vals
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
