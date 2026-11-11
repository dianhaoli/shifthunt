"""BB-8 feasibility (D35), the free channel: on each shipped probe's public sample, the class-mean logit gap (what
probe_scores gives for free), the class standard deviations, the midpoint, |w| and the logit scale, against the
scan's topic unit.

    python scripts/feasibility/bb8_free.py --out AGG.json --private-dir DIR [--bank B]

Per-probe lines go to <private-dir>/bb8_free.txt; tracked: the same quantities pooled by probe type.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402


def main(argv=None):
    a = BC.parser(__doc__).parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    lines, pool = [], {}
    for ep in BC.EPS:
        ans, feats, conf, P = BC.scan_load(a.bank, ep)
        for j, pr in enumerate(P):
            s = json.loads((Path(a.bank) / ep / "public" / f"probe{j}_sample.json").read_text())["texts"]
            z = np.load(Path(a.bank) / ep / "private" / f"probe{j}.npz")
            lg = BC.sample_logits(a.bank, ep, j)
            lab = np.array([t["label"] for t in s])
            m0, m1 = lg[lab == 0].mean(), lg[lab == 1].mean()
            s0, s1 = lg[lab == 0].std(), lg[lab == 1].std()
            p = pr["p"]
            row = dict(unit=pr["unit"], gap=m1 - m0, gap_over_unit=(m1 - m0) / pr["unit"],
                       pooled_sd=float(np.sqrt((s0 ** 2 + s1 ** 2) / 2)), mid=(m0 + m1) / 2,
                       w_norm=float(np.linalg.norm(z["w"])), logit_scale=p.get("logit_scale"))
            d = pool.setdefault(BC.probe_type(p), {})
            for k, v in row.items():
                d.setdefault(k, []).append(v)
            lines.append(f"{ep} p{j} {p['kind'][:4]} {p['source'].split('/')[0][:12]:12s} unit={pr['unit']:5.1f} "
                         f"gap={m1 - m0:5.2f} means {m0:+.2f}/{m1:+.2f} sd {s0:.2f}/{s1:.2f} pooled_sd="
                         f"{row['pooled_sd']:.2f} mid={row['mid']:+.2f} |w|={row['w_norm']:.3f} "
                         f"scale={p.get('logit_scale'):.2f}")
    (priv / "bb8_free.txt").write_text("\n".join(lines) + "\n")
    BC.write_out(a.out, {"script": "bb8_free",
                         "by_probe_type": {t: {k: BC.stats(v) for k, v in d.items()} for t, d in pool.items()}})


if __name__ == "__main__":
    main()
