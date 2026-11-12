"""Grid-fit the 3 noise parameters of sim_noise.py to the repo's scripted numbers; writes fit_noise.json."""
import json, itertools
from sim_noise import run_cell, fit_targets
T = fit_targets()
res = []
for mu0, s1, sg in itertools.product([0.02, 0.03, 0.04, 0.05, 0.06], [0.03, 0.045, 0.06, 0.075], [0.05, 0.08, 0.11, 0.14, 0.18]):
    out = {}
    loss = 0.0
    for (pol, B), (tt, tw) in T.items():
        a, b, _ = run_cell(pol, B, (mu0, s1, sg), N=8000, seed=7)
        out[f"{pol}@{B}"] = (round(a, 3), round(b, 3))
        loss += (a - tt) ** 2 + (b - tw) ** 2
    res.append({"mu0": mu0, "sig1": s1, "sigG": sg, "loss": round(loss, 5), "cells": out})
res.sort(key=lambda r: r["loss"])
best = res[0]
# re-run best at higher N
chk = {}
for (pol, B), tgt in T.items():
    chk[f"{pol}@{B}"] = {"sim(trap,two,pooled)": [round(x, 3) for x in run_cell(pol, B, (best['mu0'], best['sig1'], best['sigG']), N=40000, seed=11)],
                         "repo(trap,two)": tgt}
json.dump({"best": best, "check_N40000": chk, "top5": res[:5]}, open("fit_noise.json", "w"), indent=1)
print(json.dumps({"best": {k: best[k] for k in ('mu0','sig1','sigG','loss')}, "check": chk}, indent=1))
for r in res[:5]: print(r["mu0"], r["sig1"], r["sigG"], r["loss"])
