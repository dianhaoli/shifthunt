"""C6b Holm step (PREREG_C6B.md section 4: "Holm across J11 and J12"), which `judge_ladder2.py analyse` does not apply.

    python scripts/c6b_holm.py        # -> results/blackbox_1112/gpuplan/c6b/c6b_holm.json

Reporting only, written after the C6b results were read. It repeats J11's paired run bootstrap with the same seed
(1115) and draws (10,000) as `judge_ladder2.boot_delta`, and turns it into a one-sided bootstrap p (share of draws
with delta <= 0); J12's p is the exact McNemar p from `c6b.json`. Holm at family alpha 0.05 over the two.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import judge_ladder2 as J2  # noqa: E402
import judge_vs_grade as JV  # noqa: E402

OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "c6b"


def boot(V, rows, ids, ra, rb, seed=1115, n=10000):
    # same draws as judge_ladder2.boot_delta
    per = {cid: [(int(j in rows[cid]["hard"]), int(ok), int(V[(ra, cid)][j][0]), int(V[(rb, cid)][j][0]))
                 for j, ok in enumerate(rows[cid]["naming"])] for cid in ids}

    def kk(idx):
        a_ = JV.kappa([(p[1], p[2]) for i in idx for p in per[ids[i]] if p[0]])
        b_ = JV.kappa([(p[1], p[3]) for i in idx for p in per[ids[i]] if p[0]])
        return None if a_ is None or b_ is None else b_ - a_

    rng = np.random.default_rng(seed)
    d0 = kk(range(len(ids)))
    ds = sorted(x for x in (kk(rng.integers(0, len(ids), len(ids))) for _ in range(n)) if x is not None)
    return d0, ds


def main():
    c6b = json.loads((OUT / "c6b.json").read_text())
    _, _, _, rows = J2.load_prompts()
    meta = {m["call_id"]: m for m in json.loads((J2.PRIV / "meta.json").read_text())}
    V = J2.c6_verdicts(rows) | J2.verdict_map("c6b", rows)
    A = [c for c in sorted(c for c, m in meta.items() if m["group"] == "A" and "problem" not in m)
         if ("L1", c) in V and ("L2", c) in V]  # the run list of judge_ladder2.cmd_analyse
    d0, ds = boot(V, rows, A, "L1", "L2")
    lo95 = ds[int(0.05 * len(ds))]
    lo975 = ds[int(0.025 * len(ds))]
    p11 = sum(1 for x in ds if x <= 0) / len(ds)
    p12 = c6b["set_A"]["J12"]["p_one_sided_b_fewer"]
    order = sorted([("J11", p11), ("J12", p12)], key=lambda t: t[1])
    holm, alive = OrderedDict(), True
    for i, (h, p) in enumerate(order):
        thr = 0.05 / (len(order) - i)
        ok = alive and p < thr
        holm[h] = OrderedDict(p=round(p, 4), holm_threshold=thr, rejected=ok)
        alive = ok
    out = OrderedDict(
        prereg="results/blackbox_1112/gpuplan/c6b/PREREG_C6B.md", runs=len(A),
        check_matches_c6b_json=bool(round(d0, 4) == c6b["set_A"]["J11"]["delta_kappa_L2_minus_L1"]
                                    and round(lo95, 4) == c6b["set_A"]["J11"]["one_sided_95_lower"]),
        J11=OrderedDict(delta=round(d0, 4), one_sided_95_lower=round(lo95, 4), one_sided_975_lower=round(lo975, 4),
                        bootstrap_p_one_sided=round(p11, 4)),
        holm=holm)
    (OUT / "c6b_holm.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
