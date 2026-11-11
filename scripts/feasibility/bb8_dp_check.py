"""BB-8 feasibility (D35): Monte Carlo check of the bb8_dp optimum (no data), and the first levels of the optimal
policy tree (generic: probe states only).

    python scripts/feasibility/bb8_dp_check.py --out AGG.json --private-dir DIR [--n 40000] [--budget 8]
"""
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402
from bb8_dp import K, V, post_null, terminal  # noqa: E402


def best_action(state, b):
    best = (terminal(state), None)
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
            if v > best[0] + 1e-12:
                best = (v, (i, m))
    return best


def term_answers(state):
    pn = post_null(state)
    n = len(state)
    best = (-1, None)
    for ans in itertools.product((0, 1), repeat=n):
        r = 0.0
        for N in range(n):
            if pn[N] == 0 or ans[N] == 1:
                continue
            r += pn[N] * sum((1.0 / state[H][0]) for H in range(n)
                             if H != N and ans[H] == 1 and state[H][0] > 0) / (n - 1)
        if r > best[0]:
            best = (r, ans)
    return best[1]


def simulate(B, rng):
    null = rng.randrange(4)
    cue = [None if i == null else rng.randrange(K) for i in range(4)]
    hard = rng.choice([i for i in range(4) if i != null])
    stand = [set(range(K)) for _ in range(4)]
    z = [0] * 4
    b = B
    while b > 0:
        order = sorted(range(4), key=lambda i: (len(stand[i]), z[i]))
        state = tuple((len(stand[i]), z[i]) for i in order)
        v, act = best_action(state, b)
        if act is None:
            break
        i, m = order[act[0]], act[1]
        grp = set(rng.sample(sorted(stand[i]), m))
        if cue[i] is not None and cue[i] in grp:
            stand[i] = grp
            z[i] = 1
        else:
            stand[i] -= grp
        b -= 1
    order = sorted(range(4), key=lambda i: (len(stand[i]), z[i]))
    state = tuple((len(stand[i]), z[i]) for i in order)
    ans = term_answers(state)
    A = {order[q]: ans[q] for q in range(4)}
    if A[null] == 1 or A[hard] == 0:
        return 0
    return int(rng.choice(sorted(stand[hard])) == cue[hard])


def show(state, b, out, depth=0, maxd=8, prob=1.0):
    v, act = best_action(state, b)
    pad = "  " * depth
    if act is None or depth >= maxd:
        out.append(f"{pad}[p={prob:.3f}] state {state} b={b} value {v:.3f} answers {term_answers(state)}")
        return
    i, m = act
    k, z = state[i]
    pn = post_null(state)
    ppos = (1 - pn[i]) * m / k
    out.append(f"{pad}[p={prob:.3f}] state {state} b={b} V={v:.3f}: test probe with (k={k},z={z}) group {m}")
    if depth < 3:
        if ppos > 0:
            s = list(state)
            s[i] = (m, 1)
            out.append(pad + " +:")
            show(tuple(sorted(s)), b - 1, out, depth + 1, maxd, prob * ppos)
        if ppos < 1:
            s = list(state)
            s[i] = (k - m, z)
            out.append(pad + " -:")
            show(tuple(sorted(s)), b - 1, out, depth + 1, maxd, prob * (1 - ppos))


def main(argv=None):
    ap = BC.parser(__doc__)
    ap.add_argument("--n", type=int, default=40000)
    ap.add_argument("--budget", type=int, default=8)
    a = ap.parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    rng = random.Random(1)
    mc = sum(simulate(a.budget, rng) for _ in range(a.n)) / a.n
    tree = []
    show(tuple([(K, 0)] * 4), a.budget, tree)
    (priv / "bb8_dp_tree.txt").write_text("\n".join(tree) + "\n")
    BC.write_out(a.out, {"script": "bb8_dp_check", "budget": a.budget, "n": a.n, "seed": 1,
                         "monte_carlo_NAME": round(mc, 4), "dp_NAME": round(V(tuple([(K, 0)] * 4), a.budget), 4)})


if __name__ == "__main__":
    main()
