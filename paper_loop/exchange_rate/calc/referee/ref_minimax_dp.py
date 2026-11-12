"""Trap-only episode, noiseless single isolations, fully adaptive Bayes-optimal DP (referee check R3).
4 shuffled slots: trap (truth uniform over proxy ranks 2..8 = designer free over ranks 2..8),
2 ordinary (truth at rank 1), 1 null. P(NAME) = trap named and null answered none (ordinary answers do not matter).
Canonical state: per slot (r1 status U/N/P, number k of ranks 2..8 tested negative); slots and untested ranks are
exchangeable, so the multiset of slot states is sufficient. Value is an upper bound on the adaptive minimax value
(minimax <= Bayes value against any fixed designer mix) and equals it among rank-symmetric designers avoiding rank 1.
Validated against a brute-force hypothesis-set DP for B <= 7 (0.119, 0.1786, 0.25, 0.3214, 0.3929, 0.4643)."""
import itertools, json
from functools import lru_cache
NR = 7  # ranks 2..8
def hyps(state):
    """consistent (t, n) pairs with weight = number of untested ranks on t (each rank prob 1/NR a priori)."""
    out = []
    for t in range(4):
        for n in range(4):
            if n == t: continue
            ok = state[t][0] != 'P' and state[n][0] != 'P' and state[t][1] < NR
            ok = ok and all(state[o][0] != 'N' for o in range(4) if o not in (t, n))
            if ok: out.append((t, n, NR - state[t][1]))
    return out
def canon(state): return tuple(sorted(state))
@lru_cache(maxsize=None)
def V(state, b):
    H = hyps(state); Z = sum(w for _, _, w in H)
    if Z == 0: return 0.0  # unreachable state
    # stop value: name one rank on the best slot, `none` elsewhere
    stop = max((sum(1 for t, n, w in H if t == s) for s in range(4)), default=0) / Z
    if b == 0: return stop
    best = stop
    for s in range(4):
        r1, k = state[s]
        if r1 == 'U':  # test rank 1 on slot s: positive iff s is ordinary
            pp = sum(w for t, n, w in H if t != s and n != s) / Z
            v = 0.0
            if pp > 0: v += pp * V(canon(state[:s] + ((('P', k)),) + state[s+1:]), b - 1)
            if pp < 1: v += (1 - pp) * V(canon(state[:s] + ((('N', k)),) + state[s+1:]), b - 1)
            best = max(best, v)
        if r1 != 'P' and k < NR:  # test a fresh rank on slot s: positive iff s is trap and r is that rank
            pp = sum(1 for t, n, w in H if t == s) / Z
            if pp == 0: continue
            v = pp * 1.0 + (1 - pp) * V(canon(state[:s] + (((r1, k + 1)),) + state[s+1:]), b - 1)
            best = max(best, v)
    return best
if __name__ == "__main__":
    init = canon((('U', 0),) * 4)
    out = {B: round(V(init, B), 4) for B in range(0, 17)}
    print(out)
    json.dump({"trap_only_u2..8_single_adaptive": out,
               "blind_single_ideal_pooled_compute_md": {"8": 0.36, "12": 0.53, "16": 0.71}},
              open(__file__.replace(".py", ".json"), "w"), indent=1)
