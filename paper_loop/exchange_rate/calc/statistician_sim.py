"""Toy episode simulation (statistician lens): which parts of an 'exchange rate' belong to the proxy, the
exact channel (noise, group-test accumulation), the item mix, and the policy?

Abstract episode only (no data, no episode ids, no property names). One episode = 4 shuffled probes:
  hard  : one main; with prob 1/2 a trap (proxy puts truth at rank R_TRAP), else a two-part cue (rank 1)
  near  : one main, effect U[0.30,0.38]      (proxy rank 1)
  easy  : one main, effect U[0.40,0.60]      (proxy rank 1)
  null  : no main                             (proxy ranking uninformative)
Hard main effect U[0.30,0.40].  8 candidates per probe; non-main effects random sign, |e| ~ U[0, NM].
Effects are oriented so a main is positive. A reading of a text that flips set G on one base note is
  sum_{j in G} e_j + N(0, sigma^2 * |G|)  (base-to-base variability, per flipped property)
Decision threshold tau = 0.225 (midpoint of the 0.15/0.30 promise band).
NAME = hard probe's claim is exactly its main, and the null probe answers none.

Policies (all know the 8 candidates and their edits; none knows which probe is hard or null):
  blind_single   : budget spread evenly over probes; random single flips; claim the max reading if > tau.
  blind_bisect   : depth-first over probes in random order: screen all 8 (1 text); if > tau, halve to one
                   candidate (3 texts; the last reading is that candidate's single flip, used as the confirm).
                   Leftover budget -> replicate readings (R = max(1, B // 13) bases averaged per reading).
  proxy_top2     : test proxy ranks 1..w on every probe, w = B // 4 (remainder to random probes); claim the max
                   reading if > tau.
  proxy_adaptive : rank 1 on every probe; then rank 2 on probes whose rank 1 was negative; then screen the
                   rest as one group; if positive, bisect it. Leftover -> replicate.
Output: statistician_sim.json (+ printed tables).
"""
import json
import numpy as np

TAU = 0.225
RNG = np.random.default_rng(7)


def make_episode(rng, nm, r_trap, p_trap=0.5):
    probes = []
    for kind in ("hard", "near", "easy", "null"):
        e = rng.uniform(0, nm, 8) * rng.choice([-1, 1], 8)
        if kind == "null":
            main = None
            rank = list(rng.permutation(8))
        else:
            main = int(rng.integers(8))
            lo, hi = {"hard": (0.30, 0.40), "near": (0.30, 0.38), "easy": (0.40, 0.60)}[kind]
            e[main] = rng.uniform(lo, hi)
            others = [j for j in rng.permutation(8) if j != main]
            r = 1
            if kind == "hard" and rng.random() < p_trap:
                r = r_trap
            rank = others[: r - 1] + [main] + others[r - 1:]
        probes.append(dict(kind=kind, e=e, main=main, rank=rank))
    order = rng.permutation(4)
    return [probes[i] for i in order]


class Budget:
    def __init__(self, B):
        self.left = B

    def take(self, n=1):
        if self.left >= n:
            self.left -= n
            return True
        return False


def read(rng, p, group, sigma, reps=1):
    g = list(group)
    vals = [p["e"][g].sum() + rng.normal(0, sigma * np.sqrt(len(g))) for _ in range(reps)]
    return float(np.mean(vals))


def name_ok(probes, claims):
    for p, c in zip(probes, claims):
        if p["kind"] == "hard" and c != p["main"]:
            return False
        if p["kind"] == "null" and c is not None:
            return False
    return True


def spread(rng, B, k=4):
    w = np.full(k, B // k)
    w[rng.permutation(k)[: B % k]] += 1
    return w


def pol_blind_single(rng, probes, B, sigma):
    claims = []
    for p, b in zip(probes, spread(rng, B)):
        if b == 0:
            claims.append(None)
            continue
        cells = list(rng.permutation(8))
        reps = int(np.ceil(b / 8))  # read cells round-robin on fresh bases, average
        readings = {}
        for t in range(b):
            j = cells[t % 8]
            readings.setdefault(j, []).append(read(rng, p, [j], sigma))
        best = max(readings, key=lambda j: np.mean(readings[j]))
        claims.append(best if np.mean(readings[best]) > TAU else None)
    return claims


def bisect(rng, p, cand, bud, sigma, R):
    """Halve cand (assumed to contain a main) to one candidate. Returns (cand, last_single_reading) or None."""
    cand = list(cand)
    last = None
    while len(cand) > 1:
        half = cand[: len(cand) // 2]
        if not bud.take(R):
            return None
        v = read(rng, p, half, sigma, R)
        if v > TAU:
            cand = half
            if len(cand) == 1:
                last = v
        else:
            cand = cand[len(cand) // 2:]
    if last is None:  # last step went to the untested half: confirm with a single reading
        if not bud.take(R):
            return None
        last = read(rng, p, cand, sigma, R)
    return cand[0], last


def pol_blind_bisect(rng, probes, B, sigma):
    R = max(1, B // 13)
    bud = Budget(B)
    claims = [None] * 4
    for i in rng.permutation(4):
        p = probes[i]
        if not bud.take(R):
            break
        if read(rng, p, range(8), sigma, R) <= TAU:
            continue
        out = bisect(rng, p, rng.permutation(8), bud, sigma, R)
        if out is None:
            break
        j, v = out
        claims[i] = j if v > TAU else None
    return claims


def pol_proxy_top2(rng, probes, B, sigma):
    claims = []
    for p, w in zip(probes, spread(rng, B)):
        if w == 0:
            claims.append(None)
            continue
        width = 1 if w == 1 else 2
        readings = {}
        tested = p["rank"][:width]
        for t in range(w):
            j = tested[t % len(tested)]
            readings.setdefault(j, []).append(read(rng, p, [j], sigma))
        best = max(readings, key=lambda j: np.mean(readings[j]))
        claims.append(best if np.mean(readings[best]) > TAU else None)
    return claims


def pol_blind_seq(rng, probes, B, sigma):
    """Sequential single isolation: probes in random order, candidates in random order, stop a probe at its
    first positive reading. No group tests."""
    bud = Budget(B)
    claims = [None] * 4
    for i in rng.permutation(4):
        for j in rng.permutation(8):
            if not bud.take():
                return claims
            if read(rng, probes[i], [j], sigma) > TAU:
                claims[i] = int(j)
                break
    return claims


def pol_proxy_adaptive(rng, probes, B, sigma):
    R = 1
    bud = Budget(B)
    claims = [None] * 4
    open_ = []
    for i in range(4):
        if not bud.take(R):
            return claims
        v = read(rng, probes[i], [probes[i]["rank"][0]], sigma, R)
        if v > TAU:
            claims[i] = probes[i]["rank"][0]
        else:
            open_.append(i)
    still = []
    for i in open_:
        if not bud.take(R):
            return claims
        v = read(rng, probes[i], [probes[i]["rank"][1]], sigma, R)
        if v > TAU:
            claims[i] = probes[i]["rank"][1]
        else:
            still.append(i)
    for i in still:
        rest = probes[i]["rank"][2:]
        if not bud.take(R):
            return claims
        if read(rng, probes[i], rest, sigma, R) <= TAU:
            continue
        out = bisect(rng, probes[i], rest, bud, sigma, R)
        if out is None:
            return claims
        j, v = out
        claims[i] = j if v > TAU else None
    return claims


POLICIES = dict(blind_single=pol_blind_single, blind_seq=pol_blind_seq, blind_bisect=pol_blind_bisect,
                proxy_top2=pol_proxy_top2, proxy_adaptive=pol_proxy_adaptive)
BUDGETS = [4, 6, 8, 10, 12, 16, 24, 32, 48, 64]


def curve(pol, B, sigma, nm, r_trap, n_ep, seed):
    rng = np.random.default_rng(seed)
    ok = 0
    for _ in range(n_ep):
        probes = make_episode(rng, nm, r_trap)
        ok += name_ok(probes, POLICIES[pol](rng, probes, B, sigma))
    return ok / n_ep


def bstar(curve_b, target):
    """Smallest budget (linear interpolation in log2 B) where the curve reaches target; inf if never."""
    bs = np.array(BUDGETS, float)
    c = np.maximum.accumulate(np.array([curve_b[b] for b in BUDGETS]))
    if c[0] >= target:
        return float(bs[0])
    for i in range(len(bs) - 1):
        if c[i] < target <= c[i + 1]:
            x = np.log2(bs[i]) + (target - c[i]) / (c[i + 1] - c[i]) * (np.log2(bs[i + 1]) - np.log2(bs[i]))
            return float(2 ** x)
    return float("inf")


def main(n_ep=2000):
    out = {}
    settings = []
    for sigma in (0.0, 0.05, 0.10):
        for nm in (0.05, 0.10):
            if sigma == 0.10 and nm == 0.10:
                continue
            settings.append(dict(sigma=sigma, nm=nm, r_trap=2))
    settings.append(dict(sigma=0.05, nm=0.05, r_trap=6))
    for s in settings:
        key = f"sigma={s['sigma']},nm={s['nm']},rtrap={s['r_trap']}"
        cur = {}
        for pol in POLICIES:
            cur[pol] = {b: curve(pol, b, s["sigma"], s["nm"], s["r_trap"], n_ep, seed=1000 * list(POLICIES).index(pol) + b)
                        for b in BUDGETS}
        res = dict(curves=cur)
        # exchange rates: blind budget matching the proxy policy at B=8 and at B=4
        ex = {}
        for pp in ("proxy_top2", "proxy_adaptive"):
            for B0 in (4, 8):
                t = cur[pp][B0]
                for bp in ("blind_single", "blind_seq", "blind_bisect"):
                    ex[f"{pp}@{B0} vs {bp}"] = dict(target=round(t, 3), Bstar=round(bstar(cur[bp], t), 1),
                                                    X=round(bstar(cur[bp], t) - B0, 1))
        res["exchange"] = ex
        env = {b: max(cur[q][b] for q in ("blind_single", "blind_seq", "blind_bisect")) for b in BUDGETS}
        res["blind_envelope"] = env
        res["Bstar_envelope_by_target"] = {t: round(bstar(env, t), 1) for t in (0.5, 0.7, 0.8, 0.9, 0.95)}
        print("    blind envelope B* by target", res["Bstar_envelope_by_target"])
        # vertical gaps at matched budget
        res["gap_at_B"] = {b: dict(top2_minus_bisect=round(cur["proxy_top2"][b] - cur["blind_bisect"][b], 3),
                                   adaptive_minus_bisect=round(cur["proxy_adaptive"][b] - cur["blind_bisect"][b], 3))
                           for b in BUDGETS}
        out[key] = res
        print("==", key)
        print("   B   " + "  ".join(f"{p:>14s}" for p in POLICIES))
        for b in BUDGETS:
            print(f"  {b:3d} " + "  ".join(f"{cur[p][b]:14.3f}" for p in POLICIES))
        for k, v in ex.items():
            print("   ", k, v)
    json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)


if __name__ == "__main__":
    main()
