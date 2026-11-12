"""Items 2-4: success vs budget for blind and proxy policies (noiseless exact DP + noisy Monte Carlo calibrated to
the repo's scripted numbers), policy replay under a misspecified proxy model, exchange rates B*, and the
decomposition of Terra's gap. Writes c2_results.json. No data beyond the aggregate effect ranges in exp_c.json.
Run: python c2_episode.py  (about 10-20 min on CPU)."""
import json, math, time, sys
import numpy as np
from sim_class import Model
import sim_noise as SN

T0 = time.time()
OUT = {}
def log(*a):
    print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)

MIX = {
    "shipped (trap at r2)": {2: 1.0},
    "bank (r1/r2/r6 = 11/10/3)": {1: 11 / 24, 2: 10 / 24, 6: 3 / 24},
    "adv: uniform r2..r8": {r: 1 / 7 for r in range(2, 9)},
    "adv: uniform r1..r8 (no info on traps)": {r: 1 / 8 for r in range(1, 9)},
    "adv: fixed r3": {3: 1.0},
    "adv: fixed r6": {6: 1.0},
    "proxy always right (r1)": {1: 1.0},
}
SHORT = {"shipped (trap at r2)": "shipped", "bank (r1/r2/r6 = 11/10/3)": "bank", "adv: uniform r2..r8": "u2_8",
         "adv: uniform r1..r8 (no info on traps)": "u1_8", "adv: fixed r3": "r3", "adv: fixed r6": "r6",
         "proxy always right (r1)": "r1"}

# ---------------------------------------------------------------------------------------------------------
# 1. Noiseless exact curves
# ---------------------------------------------------------------------------------------------------------
BG = list(range(0, 17))
BS = list(range(0, 33))
models = {}
curves = {}
for counts in ("known", "unknown"):
    for mode, bud in (("group", BG), ("single", BS)):
        m = Model(None, blind=True, counts=counts, mode=mode)
        models[("blind", counts, mode)] = m
        curves[f"blind ideal | {counts} counts | {mode}"] = {b: round(m.value(b), 4) for b in bud}
        log("blind", counts, mode, curves[f"blind ideal | {counts} counts | {mode}"][8])
for name, pi in MIX.items():
    for mode, bud in (("group", BG[:13]), ("single", BS[:17])):
        m = Model(pi, mode=mode)
        models[(SHORT[name], "known", mode)] = m
        curves[f"proxy Bayes | {name} | known counts | {mode}"] = {b: round(m.value(b), 4) for b in bud}
        log(name, mode, curves[f"proxy Bayes | {name} | known counts | {mode}"][8])
for name in ("shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)"):
    for mode, bud in (("group", BG[:13]), ("single", BS[:17])):
        m = Model(MIX[name], counts="unknown", mode=mode)
        models[(SHORT[name], "unknown", mode)] = m
        curves[f"proxy Bayes | {name} | unknown counts | {mode}"] = {b: round(m.value(b), 4) for b in bud}
        log(name, "unknown", mode, curves[f"proxy Bayes | {name} | unknown counts | {mode}"][8])
# fixed-width prefix policies, noiseless: succeed iff the hard truth is within the prefix (B = 4w texts)
for name, pi in MIX.items():
    for w in (1, 2, 3):
        p_hard_in = 0.5 * sum(v for r, v in pi.items() if r <= w) + 0.5  # nested always rank 1
        curves[f"top-{w} prefix (B={4*w}) | {name} | noiseless"] = round(p_hard_in, 4)
OUT["noiseless_curves"] = curves

# ---------------------------------------------------------------------------------------------------------
# 2. Misspecification: Bayes policy for an ASSUMED trap-rank law, played in the TRUE world (noiseless)
# ---------------------------------------------------------------------------------------------------------
assumed = {
    "believes proxy always right (r1)": {1: 1.0},
    "believes shipped (r2)": {2: 1.0},
    "believes bank law": MIX["bank (r1/r2/r6 = 11/10/3)"],
    "believes only 'not r1' (u2..8)": MIX["adv: uniform r2..r8"],
    "open-minded: 0.9 r1 + 0.1 u2..8": {1: 0.9, **{r: 0.1 / 7 for r in range(2, 9)}},
    "open-minded: 0.5 r2 + 0.5 u1..8": {**{r: 0.5 / 8 for r in range(1, 9)}, 2: 0.5 + 0.5 / 8},
}
true_w = ["proxy always right (r1)", "shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)", "adv: fixed r3",
          "adv: fixed r6", "adv: uniform r2..r8"]
mis = {}
for mode in ("group", "single"):
    for an, api in assumed.items():
        am = Model(api, mode=mode)
        for b in (5, 8, 12):
            row = {}
            for tn in true_w:
                wm = Model(MIX[tn], mode=mode)
                r = am.replay(wm, b)
                row[tn] = {k: round(v, 4) for k, v in r.items()}
            mis[f"{an} | {mode} | B={b}"] = row
        log("mis", an, mode)
# unknown-counts proxy policy played in the real (known-count) world
for name in ("shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)"):
    for mode in ("group", "single"):
        am = models[(SHORT[name], "unknown", mode)]
        wm = Model(MIX[name], mode=mode)
        mis[f"unknown-counts Bayes for {name} | {mode} | played in true world"] = {
            b: {k: round(v, 4) for k, v in am.replay(wm, b).items()} for b in (4, 5, 6, 8, 10, 12)}
for mode in ("group", "single"):
    am = models[("blind", "unknown", mode)]
    wm = models[("blind", "known", mode)]
    mis[f"unknown-counts blind ideal | {mode} | played in true world"] = {
        b: {k: round(v, 4) for k, v in am.replay(wm, b).items()} for b in (4, 8, 12, 16)}
    log("unknown-counts blind replay", mode)
OUT["misspecification"] = mis

# allocation: tests on the hard probe under each ideal policy (noiseless, its own world)
alloc = {}
for key, lab in ((("shipped", "known", "group"), "proxy Bayes shipped group"), (("shipped", "known", "single"), "proxy Bayes shipped single"),
                 (("bank", "known", "single"), "proxy Bayes bank single"), (("blind", "known", "group"), "blind ideal known group"),
                 (("blind", "known", "single"), "blind ideal known single")):
    m = models[key]
    for b in (8,):
        r = m.replay(m, b)
        alloc[f"{lab} | B={b}"] = {k: round(v, 3) for k, v in r.items()}
OUT["allocation_noiseless"] = alloc
log("alloc done")

# ---------------------------------------------------------------------------------------------------------
# 3. Noisy Monte Carlo (noise fitted to the repo's scripted numbers; fit_noise.json)
# ---------------------------------------------------------------------------------------------------------
fit = json.load(open("fit_noise.json"))["best"]
P = (fit["mu0"], fit["sig1"], fit["sigG"])
OUT["noise_params"] = {"mu0": P[0], "sig1": P[1], "sigG": P[2], "theta": SN.THETA}
noisy = {}
BN = [4, 8, 12, 16, 20, 24, 32, 48, 64]
for name in ("shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)", "adv: uniform r2..r8", "adv: fixed r6"):
    pi = MIX[name]
    for pol in ("top1", "top2", "top3", "top4"):
        w = int(pol[3:])
        noisy[f"{pol} prefix | {name}"] = {B: round(SN.run_cell(pol, B, P, N=20000, seed=B, piT=pi)[2], 4) for B in BN if B >= 4 * w}
noisy["blind scripted (ii-c) | any mix"] = {B: round(SN.run_cell("blind", B, P, N=20000, seed=B)[2], 4) for B in BN}
log("noisy scripted done")


def noisy_replay(model, piT, B0, R, N, seed, blind_labels):
    rng = np.random.default_rng(seed)
    ep = SN.make_episodes(N, rng, P[0], piT=piT)
    perm = np.array([[np.arange(8)] * 4] * N)
    if blind_labels:
        perm = np.argsort(rng.random((N, 4, 8)), axis=2)  # label l -> proxy rank perm[l]
    inv = np.argsort(perm, axis=2)
    episodes = []
    for e in range(N):
        ro = ["O"] * 4
        h, n = int(ep["hard"][e]), int(ep["null"][e])
        ro[h] = "T" if ep["kind"][e] == 1 else "P"
        ro[n] = "N"
        t = []
        for i in range(4):
            mr = int(ep["main_rank"][e, i])
            t.append(0 if mr < 0 else int(inv[e, i, mr]) + 1)
        episodes.append((tuple(ro), h, tuple(t)))
    nrng = np.random.default_rng(seed + 99)

    def reader(e, i, S):
        idx = [int(perm[e, i, l - 1]) for l in S]
        s = (P[1] if len(S) == 1 else P[2]) / math.sqrt(R)
        return float(ep["eff"][e, i, idx].sum() + nrng.normal(0, s)) > SN.THETA
    return model.replay(model, B0, reader=reader, episodes=episodes)


robust = {}
for key, lab, piT, blind in ((("blind", "known", "group"), "blind ideal known group", None, True),
                             (("blind", "known", "single"), "blind ideal known single", None, True),
                             (("shipped", "known", "group"), "proxy Bayes shipped group", {2: 1.0}, False),
                             (("shipped", "known", "single"), "proxy Bayes shipped single", {2: 1.0}, False),
                             (("bank", "known", "single"), "proxy Bayes bank single", MIX["bank (r1/r2/r6 = 11/10/3)"], False)):
    m = models[key]
    tab = {}
    for B0 in ([4, 5, 6, 8, 10, 12, 16] if blind else [3, 4, 5, 6, 8]):
        for R in (1, 2, 3, 4, 6, 8):
            if B0 * R > 64:
                continue
            r = noisy_replay(m, piT, B0, R, N=1500 if blind else 3000, seed=1000 + B0 * 10 + R, blind_labels=blind)
            tab[f"{B0}x{R}"] = round(r["success"], 4)
    robust[lab] = tab
    log("robust", lab)
# envelope: best (B0, R) with B0 * R <= B
env = {}
for lab, tab in robust.items():
    env[lab] = {}
    for B in BN:
        best = max([v for k, v in tab.items() if int(k.split("x")[0]) * int(k.split("x")[1]) <= B] or [float("nan")])
        env[lab][B] = best
OUT["noisy_scripted"] = noisy
OUT["noisy_replay_of_ideal"] = robust
OUT["noisy_robust_envelope"] = env

# ---------------------------------------------------------------------------------------------------------
# 4. Exchange rates B*: smallest blind budget (linear interpolation between integer budgets) matching a target
# ---------------------------------------------------------------------------------------------------------
def bstar(curve, target):
    ks = sorted(int(k) for k in curve)
    prev = None
    for b in ks:
        v = curve[b] if b in curve else curve[str(b)]
        if v >= target - 1e-9:
            if prev is None:
                return float(b)
            b0, v0 = prev
            return round(b0 + (target - v0) / (v - v0) * (b - b0), 1) if v > v0 else float(b)
        prev = (b, v)
    return float("inf")

# Terra's no-proxy logistic (paper App. J): p(B) = 1/(1+exp(-(a + c*log2 B))) through 0.23 @ 8 and 0.69 @ 16
lg = lambda p: math.log(p / (1 - p))
c = lg(0.69) - lg(0.23)
a = lg(0.23) - 3 * c
terra_curve = {b: 1 / (1 + math.exp(-(a + c * math.log2(b)))) for b in range(1, 257)}
OUT["terra_logistic"] = {"a": round(a, 3), "c_per_doubling": round(c, 3),
                         "check": {b: round(terra_curve[b], 3) for b in (8, 16, 24, 32, 36, 64)}}

blind_refs = {
    "ideal blind, group, known counts (noiseless)": curves["blind ideal | known counts | group"],
    "ideal blind, group, unknown counts (noiseless)": curves["blind ideal | unknown counts | group"],
    "ideal blind, single only, known counts (noiseless)": curves["blind ideal | known counts | single"],
    "ideal blind, single only, unknown counts (noiseless)": curves["blind ideal | unknown counts | single"],
    "noisy robust ideal blind, group": env["blind ideal known group"],
    "noisy robust ideal blind, single": env["blind ideal known single"],
    "scripted blind (ii-c), noisy sim": noisy["blind scripted (ii-c) | any mix"],
    "repo scripted blind (exact back-end)": {8: 0.40, 16: 0.80, 32: 0.89, 64: 0.93},
    "Terra no-proxy logistic": terra_curve,
}
targets = {}
for name in ("shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)", "adv: uniform r2..r8", "adv: fixed r6"):
    targets[f"top-1 @8 noiseless | {name}"] = curves[f"top-1 prefix (B=4) | {name} | noiseless"]
    targets[f"top-2 @8 noiseless | {name}"] = curves[f"top-2 prefix (B=8) | {name} | noiseless"]
    targets[f"Bayes(calibrated) group @8 noiseless | {name}"] = curves[f"proxy Bayes | {name} | known counts | group"][8]
    targets[f"Bayes(calibrated) single @8 noiseless | {name}"] = curves[f"proxy Bayes | {name} | known counts | single"][8]
    targets[f"top-2 @8 noisy | {name}"] = noisy[f"top2 prefix | {name}"][8]
    targets[f"top-1 @8 noisy | {name}"] = noisy[f"top1 prefix | {name}"][8]
for tn in ("shipped (trap at r2)", "bank (r1/r2/r6 = 11/10/3)", "adv: fixed r6", "adv: uniform r2..r8"):
    targets[f"Bayes for shipped, played in {tn} @8 single"] = mis["believes shipped (r2) | single | B=8"][tn]["success"]
    targets[f"Bayes for 'proxy right', played in {tn} @8 single"] = mis["believes proxy always right (r1) | single | B=8"][tn]["success"]
targets["noisy robust Bayes shipped single @8"] = env["proxy Bayes shipped single"][8]
targets["noisy robust Bayes shipped group @8"] = env["proxy Bayes shipped group"][8]
targets["Terra Open-8 (23/24)"] = 23 / 24
B_star = {}
for tl, tv in targets.items():
    B_star[tl] = {"target": round(tv, 4), **{rl: bstar(rc, tv) for rl, rc in blind_refs.items()}}
OUT["B_star"] = B_star

# ---------------------------------------------------------------------------------------------------------
# 5. Decomposition of Terra's gap: C1 = Terra_proxy - Terra_blind = (I_p - I_b) + (I_b - Terra_blind) - (I_p - Terra_proxy)
# ---------------------------------------------------------------------------------------------------------
tp, tb = 23 / 24, 6 / 24
refsets = {
    "noiseless, group tests, known counts": (curves["proxy Bayes | shipped (trap at r2) | known counts | group"][8], curves["blind ideal | known counts | group"][8]),
    "noiseless, group tests, unknown counts": (mis["unknown-counts Bayes for shipped (trap at r2) | group | played in true world"][8]["success"],
                                               mis["unknown-counts blind ideal | group | played in true world"][8]["success"]),
    "noiseless, single isolations, known counts": (curves["proxy Bayes | shipped (trap at r2) | known counts | single"][8], curves["blind ideal | known counts | single"][8]),
    "noiseless, single isolations, unknown counts": (mis["unknown-counts Bayes for shipped (trap at r2) | single | played in true world"][8]["success"],
                                                     mis["unknown-counts blind ideal | single | played in true world"][8]["success"]),
    "noisy sim, best of robust ideal (group/single)": (max(env["proxy Bayes shipped group"][8], env["proxy Bayes shipped single"][8]),
                                                       max(env["blind ideal known group"][8], env["blind ideal known single"][8])),
    "repo scripted (top-two vs best blind, exact back-end)": (0.96, 0.40),
}
dec = {}
for k, (ip, ib) in refsets.items():
    dec[k] = {"I_proxy": round(ip, 3), "I_blind": round(ib, 3), "proxy_info_at_ideal": round(ip - ib, 3),
              "Terra_blind_shortfall": round(ib - tb, 3), "Terra_proxy_shortfall": round(ip - tp, 3),
              "check_sum": round((ip - ib) + (ib - tb) - (ip - tp), 3), "C1": round(tp - tb, 3)}
OUT["decomposition"] = dec

# ---------------------------------------------------------------------------------------------------------
# 6. One-batch policies with a confidence-like trap signal (binormal d'): isolate rank 1 on all four probes,
#    rank 2 on the m probes with the highest trap score.  B = 4 + m.  Noiseless reads.
# ---------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(5)
sig = {}
for d in (0.0, 1.02, 1.40, 2.5, 99.0):
    N = 200000
    x = rng.normal(0, 1, (N, 4))
    x[:, 0] += d  # probe 0 = trap
    rank_of_trap = (x > x[:, :1]).sum(axis=1)  # 0 = highest
    sig[f"d'={d}"] = {f"B={4+m}": round(0.5 + 0.5 * float((rank_of_trap < m).mean()), 4) for m in range(0, 5)}
OUT["one_batch_with_trap_signal"] = sig

json.dump(OUT, open("c2_results.json", "w"), indent=1, default=str)
log("done")
