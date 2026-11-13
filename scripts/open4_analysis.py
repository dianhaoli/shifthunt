"""X3 / X3b Open-4 analysis (results/blackbox_1112/gpuplan/open4/PREREG_OPEN4.md; frozen before counted runs).

    python scripts/open4_analysis.py validate        # reproduces Terra Open-8 11/12, 11/12, 23/24 (luna_analysis)
    python scripts/open4_analysis.py test --out results/blackbox_1112/gpuplan/open4

Slots, NAME and trap rank-2 isolation are scripts/luna_analysis.py's (batch_slots, summary, curve), unchanged.
X3-H1 (pre-registered): Terra Open-4 NAME > Terra BB-8 NAME (6/24, Block 1), one-sided Fisher exact, alpha 0.05.
Descriptive: Luna Open-4 NAME and trap rank-2 isolation; Terra and Luna Open-4 vs their Open-8 batches; texts on
the trap probe vs per other probe; one-burst; the scripted references at B = 4 from gpuplan/xr_curves.json.
"""
import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import luna_analysis as LA  # noqa: E402

BATCHES = {"terra_open4": "r1112_gpt_open4", "luna_open4": "r1112_luna_open4", "terra_open8": "r1112_gpt_open8",
           "luna_open8": "r1112_luna_open8"}
TERRA_BB8_NAME = (6, 24)  # Block 1 SUMMARY.md, pre-registered C1 arm
TRAPS = ("ep411", "ep413", "ep415")


def alloc(rows, runs):
    trap = [r for r in rows if r["hard"] and r["kind"] == "trap" and r["texts_ok"]]
    other = {}
    for r in rows:
        if r["episode"] in TRAPS and not r["hard"] and r["texts_ok"]:
            other.setdefault(r["run"], []).append(r["n_texts"])
    per_other = [sum(v) / len(v) for v in other.values() if v]
    ob = [v["one_burst"] for v in runs.values() if v["one_burst"] is not None]
    return OrderedDict(texts_on_trap_probe=round(sum(r["n_texts"] for r in trap) / len(trap), 2) if trap else None,
                       texts_per_other_probe_trap_episodes=round(sum(per_other) / len(per_other), 2) if per_other else None,
                       one_burst=f"{sum(ob)}/{len(ob)}")


def cmd_validate(a):
    return LA.cmd_validate(a)


def cmd_test(a):
    from scipy.stats import fisher_exact
    out = OrderedDict(prereg="results/blackbox_1112/gpuplan/open4/PREREG_OPEN4.md")
    S = {}
    for k, b in BATCHES.items():
        if not (LA.RAW / b).is_dir():
            continue
        rows, runs = LA.batch_slots(b)
        S[k] = (rows, runs)
        out[k] = OrderedDict(LA.summary(rows, runs), **alloc(rows, runs), allocation_by_sae_rank=LA.curve(rows))
    if "terra_open4" in S:
        k, n = (int(x) for x in out["terra_open4"]["name_all"].split("/"))
        p = float(fisher_exact([[k, n - k], [TERRA_BB8_NAME[0], TERRA_BB8_NAME[1] - TERRA_BB8_NAME[0]]],
                               alternative="greater")[1])
        out["X3_H1"] = OrderedDict(terra_open4=f"{k}/{n}", terra_bb8=f"{TERRA_BB8_NAME[0]}/{TERRA_BB8_NAME[1]}",
                                   p_one_sided=p, verdict="supported" if p < 0.05 else "not supported")
    xr = ROOT / "results/blackbox_1112/gpuplan/xr_curves.json"
    if xr.exists():
        J = json.loads(xr.read_text())
        c = J["curves"]["shipped_six"]
        out["scripted_at_B4_shipped_six"] = {p: c[p]["4"]["name"] for p in ("top1", "top2", "hedge", "bayes_bank",
                                                                          "bayes_law", "best_blind") if p in c}
        out["scripted_at_B8_shipped_six"] = {p: c[p]["8"]["name"] for p in ("top1", "top2", "hedge", "bayes_bank",
                                                                          "bayes_law", "best_blind") if p in c}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "open4.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    t = sub.add_parser("test")
    t.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"validate": cmd_validate, "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
