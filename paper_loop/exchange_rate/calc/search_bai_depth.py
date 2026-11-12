"""Adversary-depth sweep: trap truth uniform over ranks 2..d+1 (designer may demote the truth up to d ranks).
Ideal adaptive noiseless NAME success by budget (same model as search_bai_dp.py)."""
import json, sys, time
from fractions import Fraction as Fr
from search_bai_dp import build_hyps, solve
out = {}
for d in [int(x) for x in sys.argv[1].split(",")]:
    t0 = time.time()
    piT = {r: Fr(1, d) for r in range(2, 2 + d)}
    out[f"d={d}"] = solve(build_hyps(piT), list(range(0, int(sys.argv[2]) + 1)))
    print(d, json.dumps(out[f"d={d}"]), round(time.time() - t0, 1), flush=True)
json.dump(out, open(f"search_bai_depth_{sys.argv[1].replace(',','_')}.json", "w"), indent=1)
