"""Blind arm (no proxy) with SINGLE-candidate tests, Monte Carlo, same noise model as bayes_voi_batch.py.
Policy (adaptive, heuristic, not proven optimal): round-robin over unresolved probes, untested candidates in
random order; a probe is resolved at its first positive. Decoding: claim the positive; among unresolved
probes, answer `none` on the one most likely to be the null (fewest untested candidates left), and on other
unresolved probes guess an untested candidate. NAME = hard (uniform among planted) right and null `none`.
Noisy variant: a positive is re-read once to confirm; exhausted probes are re-read cyclically.\nNoiseless group-testing optimum (paper's DP, followup/misc bb8_dp): 0.354/0.500/0.703/0.833/1.000 at 4/6/8/10/12."""
import sys, json
import numpy as np
K, P = 8, 4

def episode(rng, B, s, f):
    m = rng.integers(P)
    main = rng.integers(K, size=P); main[m] = -1
    planted = [j for j in range(P) if j != m]
    k = planted[rng.integers(3)]
    order = [list(rng.permutation(K)) for _ in range(P)]
    tested = [[] for _ in range(P)]
    found = [None] * P
    hits = [set() for _ in range(P)]
    used = 0
    while used < B:
        unres = [j for j in range(P) if found[j] is None and order[j]]
        if not unres:
            break
        for j in unres:
            if used >= B:
                break
            c = order[j].pop(0); used += 1
            pos = rng.random() < (s if c == main[j] else f)
            tested[j].append(c)
            if pos:
                if s == 1.0 or c in hits[j]:      # noiseless: one positive; noisy: two positives settle it
                    found[j] = c
                else:
                    hits[j].add(c); order[j].insert(0, c)   # confirm next
            if not order[j] and found[j] is None and s < 1.0:
                order[j] = [x for x in rng.permutation(K)]   # cycle: re-read all candidates
    ans = [None] * P
    unres = [j for j in range(P) if found[j] is None]
    for j in range(P):
        if found[j] is None and hits[j]:
            found[j] = sorted(hits[j])[0]          # one unconfirmed positive: claim it
        if found[j] is not None:
            ans[j] = found[j]
    unres = [j for j in range(P) if found[j] is None]
    if unres:
        nullj = max(unres, key=lambda j: (len(tested[j]), rng.random()))
        for j in unres:
            if j == nullj:
                ans[j] = -1
            else:
                left = [c for c in range(K) if c not in tested[j]] or list(range(K))
                ans[j] = left[rng.integers(len(left))]
    return (ans[k] == main[k]) and (ans[m] == -1)

rng = np.random.default_rng(20261112)
out = {}
for (s, f) in ((1.0, 0.0),):  # noisy rows dropped: the cyclic re-read heuristic over-claims on the null as B grows
    row = {}
    for B in (4, 8, 12, 16, 24, 32, 48, 64):
        n = 20000
        row[B] = round(float(np.mean([episode(rng, B, s, f) for _ in range(n)])), 3)
    out[f"s={s},f={f}"] = row
    print(f"s={s} f={f}", row, flush=True)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
