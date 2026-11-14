"""T post hoc (written after tell.json was read; labelled post hoc everywhere it is used).

    python scripts/t_bandclose_posthoc.py     # -> results/blackbox_1112/gpuplan/t/tell_posthoc.json

The pre-registered widening measure ("the runner-up was read") counts reads made with leftover budget, which the
frozen policy spends on rank 2 of every probe, so at B = 8 it widens everywhere by construction. This splits out the
band-plus-closeness *decision* itself (scripts/t_bandclose.py's rule, unchanged: 0.15 < |runner-up| < 0.30 and
|runner-up| >= CLOSE x |head|, proxy unit), per probe cell (unit x note seed), by probe type, shipped and bank, for
the same closeness sweep. B-independent; no exact reading involved.
"""
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import t_bandclose as T  # noqa: E402

SHIPPED = ("ep411", "ep413", "ep415", "ep472", "ep474", "ep476")


def main():
    U = json.loads(T.BAND_PRIV.read_text())
    out = OrderedDict(label="post hoc", script="scripts/t_bandclose_posthoc.py",
                      terra={"trap": "11/12", "ordinary": "4/48"})
    for close in T.SWEEP:
        acc = defaultdict(lambda: [0, 0])
        for u in U:
            grp = "shipped" if u["ep"] in SHIPPED else "bank"
            kind = u["kind"]
            for s in u["seeds_proxy_unit"]:
                eff = s["effects"]
                o = T.head_runner(eff)
                h, r = abs(eff[o[0]]), abs(eff[o[1]])
                acc[(grp, kind)][0] += T.in_band(r) and r >= close * h
                acc[(grp, kind)][1] += 1
        out[f"close={close}"] = OrderedDict((f"{g} {k}", f"{a}/{n} = {a / n:.3f}") for (g, k), (a, n) in sorted(acc.items()))
    (T.OUT / "tell_posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
