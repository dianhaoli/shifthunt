"""Open-8 feasibility (D35), scan statistics: on each shipped probe's stored paired-flip scan, for every aligned
property in SAE-view order (method_ladder aligned_order, by |latent ratio|): the latent (SAE view) and true ratios in
topic units, the spread of single-base true readings, and how often one reading passes 0.15 / 0.225 / 0.30 topic units
or 1.84 logits.

    python scripts/feasibility/open8_scan_stats.py --out AGG.json --private-dir DIR [--bank B]

Per-probe, per-property rows go to <private-dir>/scan_stats.json. Tracked, pooled by probe type: the main's SAE-view
rank, its latent and true ratios, its single-reading spread and pass shares, and the same for the top-ranked
non-main aligned property.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

KEYS = ("rank", "lat", "tru", "tr_sd", "p_abs_gt_15", "p_abs_gt_225", "p_abs_gt_30", "p_logit_gt_184", "corr")


def main(argv=None):
    import method_ladder as ML
    a = BC.parser(__doc__).parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    out, pool = {}, {}
    for ep in BC.EPS:
        ev = ML.EpisodeEval(ep, bank=a.bank)
        ans = ev.answer
        out[ep] = {}
        for j, sc in enumerate(ev.scans):
            p = ans["probes"][j]
            mains = ML.mains_of(p)
            order = ML.aligned_order(sc, ev.conf)
            tt = sc.tt
            rows = []
            for rk, f in enumerate(order):
                v = sc.valid[f]
                tr = sc.tru[f][v] / tt
                trl = sc.tru[f][v]
                la = sc.lat[f][v] / sc.tl
                rows.append(dict(f=f, rank=rk + 1, main=f in mains, n=int(v.sum()), lat=sc.lat_ratio[f],
                                 tru=sc.tru_ratio[f], tr_sd=float(tr.std(ddof=1)), tr_min=float(tr.min()),
                                 tr_max=float(tr.max()), p_abs_gt_225=float((np.abs(tr) > 0.225).mean()),
                                 p_abs_gt_30=float((np.abs(tr) > 0.3).mean()),
                                 p_abs_gt_15=float((np.abs(tr) > 0.15).mean()),
                                 p_logit_gt_184=float((np.abs(trl) > 1.84).mean()), la_sd=float(la.std(ddof=1)),
                                 la_tt=float((sc.lat[f][v] / tt).mean()), sgn=p["conf_signs"][f],
                                 corr=float(np.corrcoef(sc.lat[f][v], sc.tru[f][v])[0, 1])))
            out[ep][j] = dict(kind=p["kind"], hard=j in ev.hard, T=tt, T_sd=float(sc.tru["topic"].std()), rows=rows)
            d = pool.setdefault(BC.probe_type(p), {"topic_unit": []})
            d["topic_unit"].append(tt)
            for r in rows:
                if r["main"]:
                    for k in KEYS:
                        d.setdefault(f"main_{k}", []).append(abs(r[k]) if k in ("lat", "tru") else r[k])
            other = next((r for r in rows if not r["main"]), None)
            if other:
                for k in KEYS:
                    d.setdefault(f"top_other_{k}", []).append(abs(other[k]) if k in ("lat", "tru") else other[k])
    (priv / "scan_stats.json").write_text(json.dumps(out, indent=1))
    BC.write_out(a.out, {"script": "open8_scan_stats", "note": "lat and tru are absolute ratios in topic units",
                         "by_probe_type": {t: {k: BC.stats(v) for k, v in d.items()} for t, d in pool.items()}})


if __name__ == "__main__":
    main()
