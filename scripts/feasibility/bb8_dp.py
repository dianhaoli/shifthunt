"""BB-8 feasibility (D35): exact optimum of adaptive noiseless binary group testing for NAME (no data).

Model: 4 probes; exactly one is null (uniform), the other 3 have one main cue uniform over K = 8 aligned candidates;
the hard slot is uniform among the 3 planted probes. A test = (probe, subset of its still-standing candidates),
positive iff the probe's cue is in the subset. One text = one test on one probe. NAME = the hard slot's cue named
exactly and the null answered none. State per probe: (k, z): k standing candidates, z = 0 null still possible,
z = 1 known planted; (0, 0) = known null.

    python scripts/feasibility/bb8_dp.py --out AGG.json
"""
import itertools
import os
import sys
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

K = 8
BUDGETS = (4, 6, 8, 10, 12, 16, 24, 32)


def post_null(state):
    # P(N = i) proportional to [z_i == 0] * 1 / (k_i / K)   (k_i == 0 -> certain)
    for i, (k, z) in enumerate(state):
        if z == 0 and k == 0:
            return [1.0 if j == i else 0.0 for j in range(len(state))]
    w = [(K / k if z == 0 else 0.0) for (k, z) in state]
    s = sum(w)
    return [x / s for x in w]


def terminal(state):
    pn = post_null(state)
    n = len(state)
    best = 0.0
    for ans in itertools.product((0, 1), repeat=n):  # 1 = guess one standing candidate, 0 = none
        r = 0.0
        for N in range(n):
            if pn[N] == 0 or ans[N] == 1:
                continue
            r += pn[N] * sum((1.0 / state[H][0]) for H in range(n)
                             if H != N and ans[H] == 1 and state[H][0] > 0) / (n - 1)
        best = max(best, r)
    return best


@lru_cache(None)
def V(state, b):
    best = terminal(state)
    if b == 0:
        return best
    pn = post_null(state)
    seen = set()
    for i, (k, z) in enumerate(state):
        if (k, z) in seen or k == 0:
            continue
        seen.add((k, z))
        for m in range(1, k + 1):
            if z == 1 and m == k:
                continue
            ppos = (1 - pn[i]) * m / k
            v = 0.0
            if ppos > 0:
                s = list(state)
                s[i] = (m, 1)
                v += ppos * V(tuple(sorted(s)), b - 1)
            if ppos < 1:
                s = list(state)
                s[i] = (k - m, z)
                v += (1 - ppos) * V(tuple(sorted(s)), b - 1)
            best = max(best, v)
    return best


def main(argv=None):
    a = BC.parser(__doc__, private=False).parse_args(argv)
    s0 = tuple([(K, 0)] * 4)
    BC.write_out(a.out, {"script": "bb8_dp", "K": K,
                         "optimal_NAME_by_budget": {str(b): round(V(s0, b), 4) for b in BUDGETS}})


if __name__ == "__main__":
    main()
