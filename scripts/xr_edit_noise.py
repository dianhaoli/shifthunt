"""X2 (GPU plan, 13 Nov): how much one edit's true-logit effect varies across base notes ($0, CPU, [expl]).

    SHIFTHUNT_BANK=<bank> python scripts/xr_edit_noise.py [--out results/blackbox_1112/gpuplan/xr_noise.json]

The paper says stored logits reproduce within 0.009 (re-encoding the same text); the exchange-rate analysis
fitted sigma ~ 0.075 (single flip) and ~ 0.14 (group text) across base notes. This measures the second quantity
directly. Data: every probe's stored scan (blind_verify.build_probes: the same property flip applied to each of
the episode's scan bases, encoded through the real model and probe, sign-aware, in topic units) for the six
shipped items and every distinct bank episode; group flips from the exact back-end (shipped six: blind_verify
cache plus proxy_verify's sizes 7 and 3) and, for the bank, the additive back-end (sums of single flips, labelled).
These are the same texts and logits the grader-side scripts use; no GPU call is needed because the scans store
the true logits of real encoded edits (re-encoding agrees to 0.007 topic units, proxy_verify).

Per probe and candidate: mean and SD over the probe's group bases (sample-like bases valid for every candidate).
Reported: the SD for mains and for non-mains (median over probe x candidate cells, and pooled within-cell SD);
single-text error rates at the 0.225 topic-unit threshold (the midpoint of the 0.3 / 0.15 promise): false
negative = a main's single flip reads <= 0.225, false positive = a non-main's reads > 0.225; the same for groups
by size (positive = contains a main). Per probe kind (ordinary, trap, two-part, near-threshold, null) as the
episode's answer key labels the slot (counts only).
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import blind_verify as BV  # noqa: E402
import proxy_verify as PV  # noqa: E402
import xr_scripted_curves as XR  # noqa: E402

ML = BV.ML
OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "xr_noise.json"


def slot_type(ev, j):
    t = sorted(ML.slot_types(ev.answer["probes"][j]))
    return "+".join(t) if t else ev.answer["probes"][j]["kind"]


def summarise(vals):
    v = np.asarray(vals, np.float64)
    if not len(v):
        return None
    return {"n": int(len(v)), "median": round(float(np.median(v)), 4), "q25": round(float(np.quantile(v, .25)), 4),
            "q75": round(float(np.quantile(v, .75)), 4), "mean": round(float(v.mean()), 4)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    Es, skipped = XR.load_episodes(True)
    exact = {}
    for ep in BV.SHIPPED:
        if ep in Es:
            ok, _ = PV.load_extra(ROOT / "results/private_1112/followup/proxy_verify",
                                  ROOT / "results/private_1112/blind_verify", ep, Es[ep]["ev"], Es[ep]["P"])
            exact[ep] = ok
    sd = defaultdict(list)          # (group, role) -> per-cell SD (topic units)
    pooled = defaultdict(lambda: [0.0, 0])  # (group, role) -> within-cell sum of squares, dof
    err = defaultdict(lambda: [0, 0])       # (group, role) -> [errors, readings]
    grp = defaultdict(lambda: [0, 0])       # (backend, size, contains main) -> [positive, readings]
    gsd = defaultdict(list)
    cells = 0
    for ep, E in Es.items():
        ev, P = E["ev"], E["P"]
        g = "shipped" if E["shipped"] else "bank"
        for p in P:
            st = slot_type(ev, p.j)
            gb = np.asarray(p.gbases, int)
            for c, f in enumerate(p.cands):
                x = p.single[c][gb] / p.unit
                x = x[~np.isnan(x)]
                if len(x) < 3:
                    continue
                role = "main" if f in p.truth else "non_main"
                cells += 1
                for key in ((g, role), ("all", role), (f"kind:{st}", role)):
                    sd[key].append(float(x.std(ddof=1)))
                    pooled[key][0] += float(((x - x.mean()) ** 2).sum())
                    pooled[key][1] += len(x) - 1
                    e = (x <= BV.THR) if role == "main" else (x > BV.THR)
                    err[key][0] += int(e.sum())
                    err[key][1] += len(x)
            backend = "exact" if exact.get(ep) else "additive"
            tab = p.tables[backend]
            mains = {p.cands.index(f) for f in p.truth}
            row = tab[gb[0]]
            for m in range(1, 2 ** p.n):
                if np.isnan(row[m]):
                    continue
                k = bin(m).count("1")
                if k == 1:
                    continue
                hit = any(m >> c & 1 for c in mains)
                v = tab[gb, m] / p.unit
                v = v[~np.isnan(v)]
                key = (backend, k, int(hit))
                pos = v > BV.THR
                grp[key][0] += int(pos.sum())
                grp[key][1] += len(v)
                if len(v) >= 3:
                    gsd[(backend, k, int(hit))].append(float(v.std(ddof=1)))
    out = {"label": "[expl X2]", "script": "scripts/xr_edit_noise.py", "unit": "privileged topic unit",
           "threshold": BV.THR, "episodes": {"shipped": sum(E["shipped"] for E in Es.values()),
                                             "bank_distinct": sum(not E["shipped"] for E in Es.values())},
           "probe_candidate_cells": cells,
           "single_flip_sd": {f"{k[0]} {k[1]}": dict(summarise(v), pooled_within_cell_sd=round(
               (pooled[k][0] / pooled[k][1]) ** 0.5, 4)) for k, v in sorted(sd.items())},
           "single_text_error": {f"{k[0]} {k[1]}": {"rate": round(e / n, 4), "errors": e, "readings": n,
                                                    "what": "false negative (main reads <= 0.225)" if k[1] == "main"
                                                    else "false positive (non-main reads > 0.225)"}
                                 for k, (e, n) in sorted(err.items())},
           "group_text": {f"{b} size {k} {'with main' if h else 'no main'}": {
               "positive_rate": round(pos / n, 4), "readings": n,
               "sd_median": summarise(gsd[(b, k, h)])["median"] if gsd[(b, k, h)] else None}
               for (b, k, h), (pos, n) in sorted(grp.items())},
           "reference": {"reproduction_same_text": "0.007-0.009 topic units (proxy_verify / paper)",
                         "exchange_rate_fit": "sigma ~ 0.075 single, ~ 0.14 group (paper_loop/exchange_rate)"}}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    for k in ("all main", "all non_main", "shipped main", "shipped non_main", "bank main", "bank non_main"):
        if k in out["single_flip_sd"]:
            print(k, out["single_flip_sd"][k], out["single_text_error"][k]["rate"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
