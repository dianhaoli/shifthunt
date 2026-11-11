"""BB-8 feasibility (D35), stored scan readings: on each shipped probe's paired-flip scan (32 base notes), the
single-flip true-logit reading of every aligned property, signed by its sample alignment, and how often one reading
reaches 1.84 logits (the threshold of a one-text test).

    python scripts/feasibility/bb8_scan.py --out AGG.json --private-dir DIR [--bank B]

Per-probe, per-property lines go to <private-dir>/bb8_scan.txt. Tracked, pooled by probe type: the main's mean
reading and share of bases at or above 1.84; the largest non-main aligned property's mean reading and share; and the
topic unit.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402


def main(argv=None):
    a = BC.parser(__doc__).parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    lines, pool = [], {}
    for ep in BC.EPS:
        ans, feats, conf, P = BC.scan_load(a.bank, ep)
        lines.append(ep)
        for j, pr in enumerate(P):
            p = pr["p"]
            cs, main = p["conf_signs"], p.get("cue")
            row, other = [], []
            for f in conf:
                r = cs[f] * pr["rd"][f][pr["val"][f]]
                row.append(f"{'*' if f == main else ''}{f[:6]}:{r.mean():+.1f}/{(r >= BC.T_LOGIT).mean():.2f}")
                if f != main:
                    other.append((r.mean(), (r >= BC.T_LOGIT).mean()))
            pt = BC.probe_type(p)
            d = pool.setdefault(pt, {"unit": [], "main_mean": [], "main_share_ge_T": [], "top_other_mean": [],
                                     "top_other_share_ge_T": []})
            d["unit"].append(pr["unit"])
            if main:
                r = cs[main] * pr["rd"][main][pr["val"][main]]
                d["main_mean"].append(r.mean())
                d["main_share_ge_T"].append((r >= BC.T_LOGIT).mean())
            top = max(other)
            d["top_other_mean"].append(top[0])
            d["top_other_share_ge_T"].append(max(o[1] for o in other))
            lines.append(f"  p{j} {p['kind'][:4]} {p['source'].split('/')[0][:12]:12s} unit={pr['unit']:.1f} | "
                         + " ".join(row))
    (priv / "bb8_scan.txt").write_text("\n".join(lines) + "\n")
    BC.write_out(a.out, {"script": "bb8_scan", "threshold_logits": BC.T_LOGIT,
                         "by_probe_type": {t: {k: BC.stats(v) for k, v in d.items()} for t, d in pool.items()}})


if __name__ == "__main__":
    main()
