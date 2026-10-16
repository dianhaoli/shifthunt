"""Knob "nearnull": latent-visible vs true-logit paired-flip ratios per probe and cue (CPU).

    python scripts/knob_nearnull_scan.py [--builds build_screen build_screen2 ...] [--out NAME]

Per probe (grader_build.py output, scan_* = hidden.scan_notes paired flips, 32 base notes):
  lat_ratio[f]  = mean oriented g . (F_flip - F_base) / |same for the topic swap|   (what the G2 scanner uses)
  true_ratio[f] = mean oriented (logit_flip - logit_base) / |same for the topic swap|  (true logits)
  rel_raw[f]    = stored reliance coefficient / |topic coef| without the planted sign (same orientation
                  as the flip ratios: + means presence raises the logit)
  d_true[f]     = the 32 per-note oriented true-logit differences (for the sampling-noise simulation)
Writes results/knobs/nearnull/<NAME>.jsonl (no latent ids, no salt).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import episodes as EP  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.hidden import N_SCAN  # noqa: E402

OUT = ROOT / "results" / "knobs" / "nearnull"


def flip_effects(a):
    """-> {f or 'topic': (latent per-note diffs [n], true per-note diffs [n])}, oriented off -> on."""
    F = EP.csr(a.z, "scan")
    L = np.asarray(a.z["scan_logits"], np.float64)
    g, n = a.arr["g"], N_SCAN
    base_lat = F[:n] @ g
    out = {}
    for k, f in enumerate(list(tg.FEATURES) + ["topic"]):
        on = a.z["scan_topic"] if f == "topic" else a.z["scan_levels"][:, k]
        orient = np.where(on == 0, 1.0, -1.0)
        blk = slice((k + 1) * n, (k + 2) * n)
        out[f] = ((F[blk] @ g - base_lat) * orient, (L[blk] - L[:n]) * orient)
    return out


def analyse(a):
    fe = flip_effects(a)
    t_lat, t_true = fe["topic"][0].mean(), fe["topic"][1].mean()
    m = a.meta
    row = {"probe": a.key, "kind": m["kind"], "cue": m.get("cue"), "knob": m.get("knob"),
           "rel_raw": {f: m["coef"][f] / abs(m["topic_coef"]) for f in tg.FEATURES},
           "lat_ratio": {f: float(fe[f][0].mean() / abs(t_lat)) for f in tg.FEATURES},
           "true_ratio": {f: float(fe[f][1].mean() / abs(t_true)) for f in tg.FEATURES},
           "topic_lat": float(t_lat), "topic_true": float(t_true),
           "d_true": {f: fe[f][1].tolist() for f in list(tg.FEATURES) + ["topic"]}}
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--builds", nargs="+", default=["build_screen", "build_screen2"])
    ap.add_argument("--out", default="scan_pool")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [analyse(a) for a in EP.load_all(tuple(args.builds))]
    with open(OUT / f"{args.out}.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"{len(rows)} probes -> {OUT / (args.out + '.jsonl')}")


if __name__ == "__main__":
    main()
