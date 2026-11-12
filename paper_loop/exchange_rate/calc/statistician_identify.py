"""What do Terra's no-proxy arms identify about an 'exchange rate'?  (statistician lens)

Inputs are only the published per-item counts (paper Appendix E; bb16 analysis by_item), no episode ids are
paired with any property. Items are anonymous: T1-T3 (trap episodes), P1-P3 (two-part episodes).

Computes
 1. the nonparametric (monotone) bracket for B* = blind budget matching Open-8;
 2. B* under several equally defensible 3-point curve models (link x scale), to show functional-form dependence;
 3. B* under each model when the target is moved within Open-8's own Wilson interval;
 4. an item bootstrap of B* for each model (6 clusters);
 5. per-kind B* (trap / two-part);
 6. the matched-budget decomposition of C1 against each candidate 'ideal' blind reference.
Output: statistician_identify.json
"""
import json
import numpy as np
from scipy import optimize, stats

ITEMS = ["T1", "T2", "T3", "P1", "P2", "P3"]
KIND = {"T1": "trap", "T2": "trap", "T3": "trap", "P1": "twopart", "P2": "twopart", "P3": "twopart"}
# successes out of 4 per item (Appendix E table; BB-16 from bb16_analysis by_item, same item order)
OPEN8 = dict(T1=4, T2=3, T3=4, P1=4, P2=4, P3=4)
BB = {8: dict(T1=0, T2=1, T3=1, P1=3, P2=0, P3=1),
      16: dict(T1=4, T2=3, T3=2, P1=3, P2=2, P3=2),
      64: dict(T1=4, T2=4, T3=4, P1=4, P2=4, P3=4)}
N = 4
BUDGETS = np.array([8, 16, 64], float)

LINKS = {
    "logit": (lambda p: np.log(p / (1 - p)), lambda z: 1 / (1 + np.exp(-z))),
    "probit": (stats.norm.ppf, stats.norm.cdf),
    "cloglog": (lambda p: np.log(-np.log(1 - p)), lambda z: 1 - np.exp(-np.exp(z))),
}
SCALES = {"log2B": np.log2, "B": lambda b: b, "sqrtB": np.sqrt}
INV_SCALE = {"log2B": lambda x: 2 ** x, "B": lambda x: x, "sqrtB": lambda x: x ** 2}


def fit_glm(k, n, x, link):
    """Binomial ML fit p = F(a + b x). k, n arrays per budget point."""
    g, F = LINKS[link]

    def nll(th):
        p = np.clip(F(th[0] + th[1] * x), 1e-12, 1 - 1e-12)
        return -np.sum(k * np.log(p) + (n - k) * np.log(1 - p))

    best = None
    for b0 in (1.0, 3.0):
        for a0 in (-3,):
            r = optimize.minimize(nll, [a0, b0 / max(1.0, np.ptp(x) / 3)], method="Nelder-Mead",
                                  options=dict(xatol=1e-9, fatol=1e-10, maxiter=20000))
            if best is None or r.fun < best.fun:
                best = r
    return best.x


def crossing(theta, link, scale, target):
    g, F = LINKS[link]
    a, b = theta
    if b <= 0:
        return np.inf
    x = (g(target) - a) / b
    return float(INV_SCALE[scale](x))


def monotone_interp(rates, target, scale):
    """Piecewise-linear interpolation in the given scale between observed budget points (a monotone curve
    through the observed rates). Returns the budget where it first reaches target."""
    xs = SCALES[scale](BUDGETS)
    r = np.maximum.accumulate(np.array(rates, float))
    for i in range(len(xs) - 1):
        if r[i] < target <= r[i + 1]:
            x = xs[i] + (target - r[i]) / (r[i + 1] - r[i]) * (xs[i + 1] - xs[i])
            return float(INV_SCALE[scale](x))
    return float(BUDGETS[0]) if r[0] >= target else np.inf


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def agg(items, table):
    return sum(table[i] for i in items), N * len(items)


def bstar_all(items, target):
    out = {}
    k = np.array([agg(items, BB[b])[0] for b in (8, 16, 64)], float)
    n = np.array([agg(items, BB[b])[1] for b in (8, 16, 64)], float)
    for link in LINKS:
        for scale in SCALES:
            th = fit_glm(k, n, SCALES[scale](BUDGETS), link)
            out[f"{link}/{scale}"] = crossing(th, link, scale, target)
    for scale in ("log2B", "B"):
        out[f"interp/{scale}"] = monotone_interp(k / n, target, scale)
    return out


def main():
    res = {}
    k8, n8 = agg(ITEMS, OPEN8)
    target = k8 / n8
    res["open8_rate"] = target
    res["open8_wilson95"] = wilson(k8, n8)
    rates = {b: agg(ITEMS, BB[b])[0] / 24 for b in (8, 16, 64)}
    res["bb_rates"] = rates

    # 1. monotone bracket: S_blind nondecreasing in B. Run level: BB16 < Open8 (p=0.023), BB64 >= Open8.
    # item level: sign tests
    def sign_test(a, b):
        d = [a[i] - b[i] for i in ITEMS]
        pos, neg = sum(x > 0 for x in d), sum(x < 0 for x in d)
        m = pos + neg
        p = min(1.0, 2 * stats.binom.cdf(min(pos, neg), m, 0.5)) if m else 1.0
        return dict(higher=pos, lower=neg, tied=6 - m, p_two_sided=p)
    res["item_sign_open8_vs_bb8"] = sign_test(OPEN8, BB[8])
    res["item_sign_open8_vs_bb16"] = sign_test(OPEN8, BB[16])
    res["item_sign_open8_vs_bb64"] = sign_test(OPEN8, BB[64])
    res["bracket"] = {"run_level": "16 < B* <= 64", "item_level": "8 < B* <= 64 (Open8>BB16 not established, p=0.125)"}

    # 2. point estimates under models
    res["Bstar_point"] = bstar_all(ITEMS, target)
    # 3. move target inside Open-8's Wilson interval (lower end, and 0.90)
    lo, hi = res["open8_wilson95"]
    res["Bstar_target_0.90"] = bstar_all(ITEMS, 0.90)
    res["Bstar_target_wilson_lo"] = bstar_all(ITEMS, lo)
    res["Bstar_target_0.99"] = bstar_all(ITEMS, 0.99)

    # 4. item bootstrap (resample 6 items with replacement; also Open-8 resampled -> target moves)
    rng = np.random.default_rng(20261112)
    boots = {m: [] for m in res["Bstar_point"]}
    for _ in range(800):
        its = list(rng.choice(ITEMS, size=6, replace=True))
        kk, nn = agg(its, OPEN8)
        t = min(kk / nn, 0.999)
        b = bstar_all(its, t)
        for m, v in b.items():
            boots[m].append(v)
    res["Bstar_item_bootstrap"] = {}
    for m, v in boots.items():
        v = np.array(v)
        res["Bstar_item_bootstrap"][m] = dict(
            q025=float(np.quantile(v, 0.025)), median=float(np.median(v)), q975=float(np.quantile(v, 0.975)),
            share_gt64=float(np.mean(v > 64)), share_le16=float(np.mean(v <= 16)))

    # 5. per kind
    res["per_kind"] = {}
    for kind in ("trap", "twopart"):
        its = [i for i in ITEMS if KIND[i] == kind]
        kk, nn = agg(its, OPEN8)
        t = kk / nn
        res["per_kind"][kind] = dict(open8=f"{kk}/{nn}",
                                     bb={b: f"{agg(its, BB[b])[0]}/{agg(its, BB[b])[1]}" for b in (8, 16, 64)},
                                     Bstar_at_target=bstar_all(its, min(t, 0.999)),
                                     note="two-part target is 12/12 -> any logistic crossing is at 'p=0.999'"
                                     if kind == "twopart" else "")

    # 6. matched-budget decomposition of C1 at B=8 against candidate ideal blind references
    refs = {"scripted best, exact back-end (0.40)": 0.40,
            "best tracked scripted (0.44)": 0.44,
            "group-testing optimum played on stored readings (0.497)": 0.497,
            "noiseless group-testing optimum knowing counts (0.703)": 0.703}
    proxy_ideal = 0.96  # top-two, exact back-end (ladder verify_4 privileged 0.98 with 4 texts)
    s_open, s_bb8 = target, rates[8]
    dec = {}
    for name, sb in refs.items():
        dec[name] = dict(C1=round(s_open - s_bb8, 3),
                         a_info_value_at_ideal=round(proxy_ideal - sb, 3),
                         b_terra_blind_shortfall=round(sb - s_bb8, 3),
                         c_terra_proxy_shortfall=round(proxy_ideal - s_open, 3),
                         share_info=round((proxy_ideal - sb) / (s_open - s_bb8), 2))
    res["decomposition_B8"] = dec
    # shortfall tests vs scripted reference (published: p_le 0.095 at 8, 0.086 at 16)
    res["terra_vs_scripted_blind"] = {8: "0.25 vs 0.40, p=0.095 (n.s.)", 16: "0.67 vs 0.80, p=0.086 (n.s.)",
                                      64: "1.00 vs 0.93 (Terra above)"}
    json.dump(res, open(__file__.replace(".py", ".json"), "w"), indent=1, default=float)
    # print compact
    print("target", target, "wilson", res["open8_wilson95"])
    for key in ("Bstar_point", "Bstar_target_0.90", "Bstar_target_wilson_lo", "Bstar_target_0.99"):
        print(key, {m: round(v, 1) for m, v in res[key].items()})
    print("bootstrap")
    for m, v in res["Bstar_item_bootstrap"].items():
        print(" ", m, {k: round(x, 2) for k, x in v.items()})
    for kind, v in res["per_kind"].items():
        print(kind, v["open8"], v["bb"], {m: round(x, 1) for m, x in v["Bstar_at_target"].items()})
    for n_, d in dec.items():
        print(n_, d)
    print({k: v for k, v in res.items() if k.startswith("item_sign")})


if __name__ == "__main__":
    main()
