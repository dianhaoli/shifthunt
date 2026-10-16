"""Offline per-feature paired-flip statistics for trap probes (CPU, read-only).

    python scripts/offline_trap_flipstats.py [--probes knob_trap_s2/planted_007 knob_trap_s/planted_001]
                                             [--out results/offline_1012/trap_flipstats.md]

Uses the stored grader scan arrays (artifacts/grader/<build>/planted_NNN.npz: 32 base notes, block k+1 =
feature k flipped, last block = topic swap), oriented off -> on and divided by |mean topic flip|, i.e. the
same quantities as scripts/knob_nearnull_scan.py flip_effects / analyse (lat_ratio, true_ratio).

Per feature:
  n        valid pairs (finite and the flip changed the true logit)
  true     mean / per-note sd / min / max of the oriented true-logit flip (x |topic|)
  lure     sign that would make it look like a cue: the planted sign for the main, otherwise the sign of
           the feature's latent-visible ratio (what a latent scanner shows the agent)
  P15,P30  fraction of the n single flips reading >= 0.15 / >= 0.30 in the lure direction
  P15n     normal approximation of P15 from mean and sd
  lat      latent-visible ratio mean and per-note sd (g . dF / |topic g . dF|)
  rel      reliance-set coefficient / |topic coef| (probe json coef; same orientation, no planted sign)
  n2SE     flips needed so that |mean| + 2 sd / sqrt(n) < 0.15 (inf if |mean| >= 0.15); main: flips
           until mean - 2 SE > 0.15 in the cue direction
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import textgen as tg  # noqa: E402

FE = list(tg.FEATURES)
N = 32
BAR, BAR2 = 0.15, 0.30
DEFAULT = ["knob_trap_s2/planted_007", "knob_trap_s/planted_001"]
EPS = {"knob_trap_s2/planted_007": "ep241/ep242", "knob_trap_s/planted_001": "ep232/ep235"}


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def stats(key):
    build, name = key.split("/")
    meta = json.loads((ROOT / "artifacts/probes" / build / f"{name}.json").read_text())
    g = np.load(ROOT / "artifacts/probes" / build / f"{name}.npz")["g"]
    z = np.load(ROOT / "artifacts/grader" / build / f"{name}.npz")
    nrow = len(z["scan_logits"])
    F = sp.csr_matrix((z["scan_data"], z["scan_indices"], z["scan_indptr"]), shape=(nrow, len(g)))
    Fg = np.asarray(F @ g, np.float64).ravel()
    L = np.asarray(z["scan_logits"], np.float64)
    eff = {}
    for k, f in enumerate(FE + ["topic"]):
        on = z["scan_topic"] if f == "topic" else z["scan_levels"][:, k]
        o = np.where(on == 0, 1.0, -1.0)
        b = slice((k + 1) * N, (k + 2) * N)
        eff[f] = ((Fg[b] - Fg[:N]) * o, (L[b] - L[:N]) * o)
    tl, tt = abs(eff["topic"][0].mean()), abs(eff["topic"][1].mean())
    cue, sign = meta["cue"], meta["sign"]
    rows = []
    for f in FE:
        lat, tru = eff[f][0] / tl, eff[f][1] / tt
        ok = np.isfinite(lat) & np.isfinite(tru) & (eff[f][1] != 0)
        lat, tru = lat[ok], tru[ok]
        n = int(ok.sum())
        lm, ls = lat.mean(), lat.std(ddof=1)
        m, s = tru.mean(), tru.std(ddof=1)
        lure = sign if f == cue else (1.0 if lm >= 0 else -1.0)
        x = tru * lure
        ml = m * lure
        if f == cue:
            n2 = math.ceil((2 * s / (ml - BAR)) ** 2) if ml > BAR else math.inf
        else:
            n2 = math.ceil((2 * s / (BAR - abs(m))) ** 2) if abs(m) < BAR else math.inf
        rows.append(dict(f=f, main=f == cue, n=n, mean=m, sd=s, mn=tru.min(), mx=tru.max(), lure=lure,
                         p15=float((x >= BAR).mean()), p30=float((x >= BAR2).mean()),
                         p15n=1 - ncdf((BAR - ml) / s) if s > 0 else float(ml >= BAR),
                         lat=lm, lat_sd=ls, rel=meta["coef"][f] / abs(meta["topic_coef"]), n2=n2))
    rows.sort(key=lambda r: -abs(r["lat"]))
    return meta, dict(topic_true=tt, topic_lat=tl, lat_over_true=tl / tt), rows


def fmt_table(rows):
    h = ("| feature | n | true mean | sd | min | max | lure | P15 | P15n | P30 | lat mean | lat sd | rel | n2SE |\n"
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    out = []
    for r in rows:
        nm = f"**{r['f']}** (main)" if r["main"] else r["f"]
        n2 = "inf" if r["n2"] == math.inf else str(r["n2"])
        out.append(f"| {nm} | {r['n']} | {r['mean']:+.3f} | {r['sd']:.3f} | {r['mn']:+.3f} | {r['mx']:+.3f} | "
                   f"{'+' if r['lure'] > 0 else '-'} | {r['p15']:.2f} | {r['p15n']:.2f} | {r['p30']:.2f} | "
                   f"{r['lat']:+.3f} | {r['lat_sd']:.3f} | {r['rel']:+.3f} | {n2} |")
    return h + "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", nargs="+", default=DEFAULT)
    ap.add_argument("--out", default="results/offline_1012/trap_flipstats.md")
    a = ap.parse_args()
    out = ROOT / a.out
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    parts = ["# Trap probe per-feature paired-flip stats\n",
             "Generated by `scripts/offline_trap_flipstats.py` from the stored grader scan arrays "
             "(32 base notes per feature; oriented off->on; x |mean topic flip|). "
             "`lure` = sign that would make the feature look like a cue (main: planted sign; others: sign of "
             "latent ratio). P15/P30 = empirical fraction of single flips >= 0.15/0.30 in the lure direction; "
             "P15n = normal approx. `rel` = reliance-set coef / |topic coef| (unsigned, same orientation). "
             "`n2SE` = flips needed for |mean| + 2 SE < 0.15 (main: mean - 2 SE > 0.15). Sorted by |lat mean|.\n"]
    summary = {}
    for key in a.probes:
        meta, top, rows = stats(key)
        summary[key] = rows
        parts.append(f"\n## {key} ({EPS.get(key, '')}) cue={meta['cue']} sign={meta['sign']:+d} "
                     f"topics={'/'.join(meta['topics'])}\n")
        parts.append(f"topic true flip {top['topic_true']:.3f} logits; latent/true topic ratio "
                     f"{top['lat_over_true']:.3f}\n\n")
        parts.append(fmt_table(rows) + "\n")
        risky = [r for r in rows if not r["main"] and r["p15"] >= 0.15]
        parts.append("\nNon-main features with P15 >= 0.15 (one true flip has >= 15% chance to read past 0.15 "
                     "in the lure direction): " +
                     (", ".join(f"{r['f']} (P15 {r['p15']:.2f}, mean {r['mean']:+.3f} sd {r['sd']:.3f}, "
                                f"n2SE {r['n2'] if r['n2'] != math.inf else 'inf'})" for r in risky) or "none")
                     + "\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(parts))
    print(out)
    print("".join(parts))


if __name__ == "__main__":
    main()
