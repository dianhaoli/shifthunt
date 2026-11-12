"""Blind policy restricted to single-candidate isolations (no group tests), noiseless, shipped structure
(exactly one null among 4 probes, 8 candidates each, hard probe uniform among the 3 planted).
Exact DP over a compact state: per probe (k untested candidates, found?) with the exactly-one-null constraint.
Also: prefix search with the calibrated proxy prior (shipped) for comparison = the ideal adaptive DP (5 tests)."""
import itertools, json
from functools import lru_cache
K = 8

def post_null(state):
    # state per probe: ('F',) found planted, or ('U', k) k untested candidates (k=0 -> null certain)
    w = []
    for s in state:
        if s[0] == 'F':
            w.append(0.0)
        else:
            k = s[1]
            # P(all tested negative | planted) = k/K, | null = 1 ; prior null 1/4
            w.append(1.0 / (k / K) if k > 0 else float('inf'))
    if any(x == float('inf') for x in w):
        return [1.0 if x == float('inf') else 0.0 for x in w]
    s = sum(w)
    return [x / s for x in w] if s > 0 else [0.0] * len(w)

def terminal(state):
    pn = post_null(state)
    n = len(state); best = 0.0
    for ans in itertools.product((0, 1), repeat=n):  # 1 = guess a candidate, 0 = none
        r = 0.0
        for N in range(n):
            if pn[N] == 0 or ans[N] == 1:
                continue
            # hard uniform among the other 3; found probes are named exactly; U probes guessed 1/k
            r += pn[N] * sum((1.0 if state[H][0] == 'F' else (1.0 / state[H][1] if state[H][1] > 0 else 0.0))
                             for H in range(n) if H != N and ans[H] == 1) / 3
        best = max(best, r)
    return best

@lru_cache(None)
def V(state, b):
    best = terminal(state)
    if b == 0:
        return best
    pn = post_null(state)
    seen = set()
    for i, s in enumerate(state):
        if s[0] == 'F' or s[1] == 0 or s in seen:
            continue
        seen.add(s)
        k = s[1]
        ppos = (1 - pn[i]) * (1.0 / k)
        sp = list(state); sp[i] = ('F',)
        sn = list(state); sn[i] = ('U', k - 1)
        v = (ppos * V(tuple(sorted(sp)), b - 1) if ppos > 0 else 0.0) + ((1 - ppos) * V(tuple(sorted(sn)), b - 1) if ppos < 1 else 0.0)
        best = max(best, v)
    return best

s0 = tuple([('U', K)] * 4)
res = {b: round(V(s0, b), 4) for b in list(range(0, 33, 2)) + [21, 23, 25, 27]}
res = dict(sorted(res.items()))
print(json.dumps(res))
json.dump(res, open("/home/user/shifthunt/paper_loop/exchange_rate/calc/search_bai_isolation.json", "w"))
