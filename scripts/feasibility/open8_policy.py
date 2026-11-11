"""Open-8 feasibility (D35), a scripted open-arm policy on the stored scans: the free SAE view (32-base latent ratios)
picks the (probe, aligned property) cells with |latent ratio| >= lat_min, most ambiguous first (nearest 0.3), and exact
single flips verify them (one query per flip, the base note free via probe_scores unless pay_base). A cell is claimed
if its mean reading exceeds thr (topic units, or 1.84 logits = 0.225). NAME as the grader's naming view.

    python scripts/feasibility/open8_policy.py --out AGG.json [--bank B] [--n 3000]

Tracked: per configuration, NAME and outcome shares pooled per episode type (mean, min, max over the three
episodes), and the mean number of cells and queries used. Seed: numpy default_rng(1), drawn in configuration and
episode order (as the scratch run).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

CONFIGS = [
    ("B=8 lat>=0.10 thr .225 unit T, base free", dict(B=8, lat_min=.10, thr=.225, unit="T")),
    ("B=8 lat>=0.10 thr 1.84 logits, base free", dict(B=8, lat_min=.10, thr=.225, unit="logit")),
    ("B=8 lat>=0.15 thr .225 unit T, base free", dict(B=8, lat_min=.15, thr=.225, unit="T")),
    ("B=8 lat>=0.15 thr 1.84 logits, base free", dict(B=8, lat_min=.15, thr=.225, unit="logit")),
    ("B=8 lat>=0.15 thr .225 T, PAY for base (4 readings), untested->SAE>.225",
     dict(B=8, lat_min=.15, thr=.225, unit="T", pay_base=True, sae_fallback=True)),
    ("B=8 lat>=0.10 thr 0.30 unit T (rigid prompt threshold)", dict(B=8, lat_min=.10, thr=.30, unit="T")),
    ("B=64 lat>=0.05 thr .225 unit T, base free", dict(B=64, lat_min=.05, thr=.225, unit="T", N=500)),
    ("B=64 ALL 32 cells (no SAE: lat>=0) thr .225 unit T, base free  [BB-64-like]",
     dict(B=64, lat_min=0, thr=.225, unit="T", N=500)),
    ("B=64 ALL 32 cells thr 1.84 logits, base free [BB-64-like]", dict(B=64, lat_min=0, thr=.225, unit="logit", N=500)),
    ("B=64 ALL 32 cells thr .225 T, PAY for base (32 readings) [BB-64 own-text bases]",
     dict(B=64, lat_min=0, thr=.225, unit="T", pay_base=True, N=500)),
]


def run(ev, B, lat_min, thr, unit, rng, pay_base=False, sae_fallback=False, N=3000):
    import method_ladder as ML
    a = ev.answer
    h = ev.hard[0]
    cells = []
    for j, sc in enumerate(ev.scans):
        for f in ML.aligned_order(sc, ev.conf):
            if abs(sc.lat_ratio[f]) >= lat_min:
                cells.append((j, f))
    cells.sort(key=lambda c: abs(abs(ev.scans[c[0]].lat_ratio[c[1]]) - 0.3))  # most ambiguous first
    cost = 2 if pay_base else 1
    ok, used_tot = 0, 0
    outcomes = {"named": 0, "none": 0, "wrong": 0, "extra": 0, "null_claim": 0}
    for _ in range(N):
        reads = {c: [] for c in cells}
        pools = {c: list(rng.permutation(np.flatnonzero(ev.scans[c[0]].valid[c[1]]))) for c in cells}
        budget = B

        def read(c):
            sc = ev.scans[c[0]]
            i = pools[c].pop()
            x = sc.tru[c[1]][i]
            return x / sc.tt if unit == "T" else x / (1.84 / 0.225)  # unit-free: 1.84 logits == 0.225
        for c in cells:
            if budget >= cost:
                reads[c].append(read(c))
                budget -= cost
        while budget >= cost:
            cand = [c for c in cells if reads[c] and pools[c]]
            if not cand:
                break
            c = min(cand, key=lambda c: abs(abs(sum(reads[c]) / len(reads[c])) - thr) * len(reads[c]) ** 0.5)
            reads[c].append(read(c))
            budget -= cost
        used_tot += B - budget
        claims = {j: set() for j in range(ev.n)}
        for c in cells:
            if reads[c]:
                if abs(np.mean(reads[c])) > thr:
                    claims[c[0]].add(c[1])
            elif sae_fallback and abs(ev.scans[c[0]].lat_ratio[c[1]]) > 0.225:
                claims[c[0]].add(c[1])
        mains = set(ML.mains_of(a["probes"][h]))
        nul = all(not claims[j] for j in ev.nulls)
        if claims[h] == mains and nul:
            ok += 1
            outcomes["named"] += 1
        elif not nul:
            outcomes["null_claim"] += 1
        elif not claims[h]:
            outcomes["none"] += 1
        elif mains <= claims[h]:
            outcomes["extra"] += 1
        else:
            outcomes["wrong"] += 1
    return ok / N, len(cells), used_tot / N, {k: v / N for k, v in outcomes.items()}


def main(argv=None):
    import method_ladder as ML
    ap = BC.parser(__doc__, private=False)
    ap.add_argument("--n", type=int, default=3000)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(1)
    EV = {ep: ML.EpisodeEval(ep, bank=a.bank) for ep in BC.EPS}
    res = {}
    for label, kw in CONFIGS:
        kw = dict(kw)
        kw.setdefault("N", a.n)
        per = {}
        for ep, ev in EV.items():
            p, nc, used, oc = run(ev, rng=rng, **kw)
            d = per.setdefault(BC.EP_TYPE[ep], {})
            for k, v in [("NAME", p), ("cells", nc), ("queries_used", used)] + [(f"share_{k}", v) for k, v in oc.items()]:
                d.setdefault(k, []).append(v)
        res[label] = {t: {k: BC.stats(v) for k, v in d.items()} for t, d in per.items()}
    BC.write_out(a.out, {"script": "open8_policy", "n_default": a.n, "configs": res})


if __name__ == "__main__":
    main()
