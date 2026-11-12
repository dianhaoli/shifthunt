"""Closed forms and the exchange-rate sensitivity (no data beyond the paper's published aggregates).
1. per-probe information of a ranked prior: H(pi), I = log2 8 - H(pi), prefix cost sum_r r pi_r
2. mismatched-prior cost: H(pi) + D(pi || q)  (Huffman/Kraft), the 'top-one believer' limit
3. B* = blind budget matching the proxy arm, for three policy classes (ideal DP, scripted, Terra fit)
4. sensitivity of Terra's logistic B* to the target (Open-8 23/24 and its Wilson interval) and to the link
"""
import math, json
import numpy as np

def H(p):
    return -sum(x * math.log2(x) for x in p if x > 0)

def D(p, q):
    s = 0.0
    for x, y in zip(p, q):
        if x > 0:
            if y == 0:
                return float("inf")
            s += x * math.log2(x / y)
    return s

out = {}
K = 8
pis = {
    "ordinary (rank 1 in 116/116)": [1, 0, 0, 0, 0, 0, 0, 0],
    "shipped trap (rank 2, 3/3)": [0, 1, 0, 0, 0, 0, 0, 0],
    "bank traps (11/10/3 at ranks 1/2/6)": [11/24, 10/24, 0, 0, 0, 3/24, 0, 0],
    "shipped planted-probe mix (15 rank-1 : 3 rank-2)": [15/18, 3/18, 0, 0, 0, 0, 0, 0],
    "blind (uniform)": [1/8] * 8,
}
rows = {}
for name, p in pis.items():
    rows[name] = {"H_bits": round(H(p), 3), "I_bits": round(3 - H(p), 3),
                  "prefix_tests_sum_r_pi_r": round(sum((r + 1) * x for r, x in enumerate(p)), 3)}
# blind prefix with known existence: test 7 at most -> (1+..+7+7)/8
rows["blind (uniform)"]["prefix_tests_sum_r_pi_r"] = round((sum(range(1, 8)) + 7) / 8, 3)
out["per_probe"] = rows

# mismatched prior: agent believes q, truth is pi; extra expected bits = D(pi||q)
def q_believer(delta):  # believes rank 1 w.p. 1-delta, the rest spread uniformly
    return [1 - delta] + [delta / 7] * 7
mm = {}
for name in ["shipped trap (rank 2, 3/3)", "bank traps (11/10/3 at ranks 1/2/6)", "ordinary (rank 1 in 116/116)"]:
    p = pis[name]
    mm[name] = {f"delta={d}": round(H(p) + D(p, q_believer(d)), 2) for d in (0.5, 0.2, 0.05, 0.01, 0.0)}
# calibrated-on-mix agent: q = shipped planted mix; cost on each probe type
qmix = pis["shipped planted-probe mix (15 rank-1 : 3 rank-2)"]
mm["code tuned to shipped mix: cost on ordinary / trap"] = [round(-math.log2(qmix[0]), 2), round(-math.log2(qmix[1]), 2)]
out["mismatched_bits"] = mm

# 3. exchange rates
ideal_blind = {4: .3542, 6: .5, 8: .7031, 10: .8333, 11: .958, 12: 1.0}  # bb8_dp / bb8_dp2 known1 (paper App. D)
out["B*_ideal"] = {"target 1.00 (ideal with proxy at 8 = 1.0)": 12, "target 0.958 (Terra Open-8)": 11,
                   "target 0.96 (top-two policy)": "11-12"}
out["B*_scripted"] = "top-two 0.96 at 8 vs best blind scripted 0.40/0.80/0.93 at 8/16/64 -> B* > 64"

# Terra fit: NAME ~ logistic(a + b log2 B) on 72 runs (6/24, 16/24, 24/24)
Bs = np.array([8] * 24 + [16] * 24 + [64] * 24, float)
y = np.array([1] * 6 + [0] * 18 + [1] * 16 + [0] * 8 + [1] * 24, float)
def fit(x):
    X = np.c_[np.ones_like(x), x]
    w = np.zeros(2)
    for _ in range(200):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (y - p)
        Hm = (X * (p * (1 - p))[:, None]).T @ X + 1e-9 * np.eye(2)
        w = w + np.linalg.solve(Hm, g)
    return w
logit = lambda p: math.log(p / (1 - p))
w_log = fit(np.log2(Bs))
w_lin = fit(Bs)
def bstar(w, p, linear=False):
    v = (logit(p) - w[0]) / w[1]
    return v if linear else 2 ** v
def wilson(k, n, z=1.96):
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return c - h, c + h
lo, hi = wilson(23, 24)
tgt = {"23/24 point": 23 / 24, "Wilson low": lo, "Wilson high": min(hi, 0.995), "0.90": 0.90, "0.99": 0.99}
out["Terra_fit_log2B"] = {"a": round(w_log[0], 3), "b_per_doubling": round(w_log[1], 3),
                          "pred_8_16_64": [round(1 / (1 + math.exp(-(w_log[0] + w_log[1] * math.log2(b)))), 3) for b in (8, 16, 64)],
                          "B*": {k: round(bstar(w_log, v), 1) for k, v in tgt.items()}}
out["Terra_fit_linearB"] = {"B*": {k: round(bstar(w_lin, v, True), 1) for k, v in tgt.items()}}
out["Wilson_23_24"] = [round(lo, 3), round(hi, 3)]
# local sensitivity: dB*/B* per 0.01 of target at 0.958
p0 = 23 / 24
out["dlog2B*_per_0.01_target"] = round(0.01 / (p0 * (1 - p0)) / w_log[1], 3)

# 4. near-ceiling tail: with per-reading error eps and majority-of-m repeats on a blind plan needing n0 decisions,
# success ~ (1 - e_m)^n0 with e_m ~ exp(-m * D_KL(1/2 || eps)); B*(p) ~ n0 * m(p), m(p) ~ ln(n0/(1-p)) / Dkl
def kl_half(eps):
    return 0.5 * math.log(0.5 / eps) + 0.5 * math.log(0.5 / (1 - eps))
tail = {}
n0 = 11  # decisions the noiseless blind optimum needs (bits)
for eps in (0.05, 0.10, 0.20):
    tail[f"eps={eps}"] = {f"p*={p}": round(n0 * max(1, math.log(n0 / (1 - p)) / kl_half(eps)), 1) for p in (0.90, 0.958, 0.99)}
out["noise_tail_Bstar_scale"] = tail
print(json.dumps(out, indent=1))
json.dump(out, open("/home/user/shifthunt/paper_loop/exchange_rate/calc/search_bai_rates.json", "w"), indent=1)

# 5. per-kind Terra fits (Table 2 rows: trap 2/9/12 of 12, two-part 4/7/12 of 12; proxy 11/12, 12/12)
def fit_counts(ks, n=12, Bl=(8, 16, 64)):
    xs = []; ys = []
    for B_, k in zip(Bl, ks):
        xs += [math.log2(B_)] * n; ys += [1] * k + [0] * (n - k)
    xs = np.array(xs); ys = np.array(ys, float)
    X = np.c_[np.ones_like(xs), xs]; w = np.zeros(2)
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (ys - p)
        Hm = (X * (p * (1 - p))[:, None]).T @ X + 1e-6 * np.eye(2)
        w = w + np.linalg.solve(Hm, g)
    return w
pk = {}
for kind, ks, tgt_k in (("trap", (2, 9, 12), 11 / 12), ("two-part", (4, 7, 12), 12 / 12)):
    w = fit_counts(ks)
    t = min(tgt_k, 0.99)
    pk[kind] = {"b_per_doubling": round(float(w[1]), 2), "target": round(tgt_k, 3),
                "B*_at_target_or_0.99": round(2 ** ((logit(t) - w[0]) / w[1]), 1),
                "note": "separation at B=64 makes the slope unstable (12/12)" }
out["Terra_per_kind"] = pk

# 6. noisy-channel (BSC) bound: B >= (p H - 1) / C, C = 1 - h2(eps); H_blind = 11 bits, H_proxy(shipped, calibrated) = 3.79
h2 = lambda e: 0 if e in (0, 1) else -(e * math.log2(e) + (1 - e) * math.log2(1 - e))
Hb, Hp = 11.0, 0.5 * math.log2(24) + 0.5 * math.log2(8)
bsc = {}
for eps in (0.0, 0.05, 0.10, 0.20):
    C = 1 - h2(eps)
    bsc[f"eps={eps}"] = {"C_bits_per_query": round(C, 3), "B>=H/C blind": round(Hb / C, 1), "B>=H/C proxy": round(Hp / C, 1),
                         "additive gap": round((Hb - Hp) / C, 1), "ratio": round(Hb / Hp, 2)}
out["H_proxy_shipped_bits"] = round(Hp, 3)
out["bsc_bounds"] = bsc
print(json.dumps({k: out[k] for k in ("Terra_per_kind", "H_proxy_shipped_bits", "bsc_bounds")}, indent=1))
json.dump(out, open("/home/user/shifthunt/paper_loop/exchange_rate/calc/search_bai_rates.json", "w"), indent=1)
