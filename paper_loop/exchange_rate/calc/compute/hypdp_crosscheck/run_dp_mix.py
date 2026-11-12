"""Exact noiseless Bayes-optimal curves (known counts) for one trap-rank mix and test mode. Usage:
python run_dp_mix.py <mixname> <group|single> <maxB>   -> dp_<mix>_<mode>.json"""
import sys, json, time
from fractions import Fraction as Fr
from sim_core import build_hyps, HypDP
MIX = {'shipped': {2: Fr(1)}, 'bank': {1: Fr(11, 24), 2: Fr(10, 24), 6: Fr(3, 24)},
       'unif2_8': {r: Fr(1, 7) for r in range(2, 9)}, 'unif1_8': {r: Fr(1, 8) for r in range(1, 9)},
       'rank3': {3: Fr(1)}, 'rank6': {6: Fr(1)}, 'rank1': {1: Fr(1)}}
name, mode, maxB = sys.argv[1], sys.argv[2], int(sys.argv[3])
t = time.time()
dp = HypDP(build_hyps(MIX[name]), mode)
out = {}
for b in range(0, maxB + 1):
    out[b] = round(dp.value(b), 4)
    print(name, mode, b, out[b], round(time.time() - t, 1), flush=True)
    if out[b] >= 0.99995:
        for bb in range(b + 1, maxB + 1):
            out[bb] = 1.0
        break
json.dump(out, open(f"dp_{name}_{mode}.json", "w"))
