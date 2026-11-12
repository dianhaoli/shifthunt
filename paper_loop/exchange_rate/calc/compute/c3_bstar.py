"""Merge c2_results.json and c2b_results.json; recompute the noisy robust blind envelope (best of group/single over
all (B0 x R) cells with B0*R <= B) and the compact exchange-rate table. Writes c3_bstar.json."""
import json, math
d = json.load(open("c2_results.json")); e = json.load(open("c2b_results.json"))
rob = d["noisy_replay_of_ideal"]
for k, v in e.items():
    rob[k].update(v)
def env(tabs, B):
    best = 0.0
    for tab in tabs:
        for k, v in tab.items():
            b0, r = map(int, k.split("x"))
            if b0 * r <= B: best = max(best, v)
    return best
BB = [4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64]
envs = {
 "noisy robust blind, single": {B: env([rob["blind ideal known single"]], B) for B in BB},
 "noisy robust blind, group": {B: env([rob["blind ideal known group"]], B) for B in BB},
 "noisy robust blind, best of both": {B: env([rob["blind ideal known single"], rob["blind ideal known group"]], B) for B in BB},
 "noisy robust proxy Bayes shipped (best of both)": {B: env([rob["proxy Bayes shipped single"], rob["proxy Bayes shipped group"]], B) for B in BB},
}
def bstar(curve, t):
    ks = sorted(curve); prev = None
    for b in ks:
        v = curve[b]
        if v >= t - 1e-9:
            if prev is None: return float(b)
            b0, v0 = prev
            return round(b0 + (t - v0) / (v - v0) * (b - b0), 1)
        prev = (b, v)
    return float("inf")
c = d["noiseless_curves"]; lg = lambda p: math.log(p / (1 - p))
cc = lg(0.69) - lg(0.23); a = lg(0.23) - 3 * cc
terra = {b: 1 / (1 + math.exp(-(a + cc * math.log2(b)))) for b in range(1, 513)}
I = lambda k: {int(b): v for b, v in c[k].items()}
refs = {
 "ideal group, known counts": I("blind ideal | known counts | group"),
 "ideal group, unknown counts": I("blind ideal | unknown counts | group"),
 "ideal single, known counts": I("blind ideal | known counts | single"),
 "ideal single, unknown counts": I("blind ideal | unknown counts | single"),
 "noisy robust ideal (best of both)": envs["noisy robust blind, best of both"],
 "scripted (ii-c), noisy sim": {int(b): v for b, v in d["noisy_scripted"]["blind scripted (ii-c) | any mix"].items()},
 "Terra logistic": terra,
}
mis = d["misspecification"]
ns = d["noisy_scripted"]
targets = {
 "shipped: top-1 / believer 'proxy right' (any B)": 0.5,
 "shipped: top-2 (noiseless)": 1.0,
 "shipped: calibrated Bayes, noiseless (reaches 1.0 at B=5)": 1.0,
 "shipped: top-2, noisy sim": ns["top2 prefix | shipped (trap at r2)"]["8"],
 "shipped: robust Bayes, noisy sim": envs["noisy robust proxy Bayes shipped (best of both)"][8],
 "shipped: Terra Open-8 23/24": 23 / 24,
 "bank: top-1": 0.7292, "bank: top-2 / shipped-believer": 0.9375, "bank: calibrated Bayes (1.0 at B=6-8)": 1.0,
 "bank: top-2, noisy sim": ns["top2 prefix | bank (r1/r2/r6 = 11/10/3)"]["8"],
 "adv r6: top-2 / shipped-believer": 0.5, "adv r6: calibrated Bayes (knows r6)": 1.0,
 "adv u2..8: top-2 / shipped-believer": 0.5714,
 "adv u2..8: calibrated Bayes, single isolations": c["proxy Bayes | adv: uniform r2..r8 | known counts | single"]["8"],
 "adv u2..8: calibrated Bayes, group tests": c["proxy Bayes | adv: uniform r2..r8 | known counts | group"]["8"],
 "proxy no info on traps (u1..8): Bayes single": c["proxy Bayes | adv: uniform r1..r8 (no info on traps) | known counts | single"]["8"],
 "proxy no info on traps (u1..8): Bayes group": c["proxy Bayes | adv: uniform r1..r8 (no info on traps) | known counts | group"]["8"],
}
tab = {t: {"target": round(v, 4), **{r: bstar(rc, v) for r, rc in refs.items()}} for t, v in targets.items()}
json.dump({"envelopes": envs, "B_star": tab}, open("c3_bstar.json", "w"), indent=1)
for k, v in envs.items(): print(k, {b: round(x, 3) for b, x in v.items()})
for t, r in tab.items(): print(t, r)
