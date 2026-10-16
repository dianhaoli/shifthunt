"""Summarize the probe experiment JSONL files into markdown tables (for the lab log).

    python scripts/probe_report.py grid|build|stability|gradient [--planted-max X]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import probes as P  # noqa: E402

RESULTS = ROOT / "results" / "probes"


def rows(name):
    return [json.loads(line) for line in open(RESULTS / f"{name}.jsonl")]


def max_other(r):
    return max(abs(v) for f, v in r["reliance"].items() if f != r.get("cue"))


def fmt(xs):
    xs = np.asarray(xs)
    d = 4 if np.abs(xs).max() < 0.05 else 2
    return f"{np.median(xs):.{d}f} [{xs.min():.{d}f}, {xs.max():.{d}f}]"


def grid(args):
    R = rows("grid")
    print("### Exp 1: rho = 1, eps = 0 (cue == topic == label) vs eps > 0")
    print("| cue | eps=0 | eps=0.02 | eps=0.05 | eps=0.10 |\n|---|---|---|---|---|")
    for cue in dict.fromkeys(r["cue"] for r in R):
        cells = [fmt([r["reliance"][cue] for r in R if r["cue"] == cue and r["rho"] == 1.0 and r["eps"] == e])
                 for e in (0.0, 0.02, 0.05, 0.1)]
        print(f"| {cue} | " + " | ".join(cells) + " |")
    print("\n### Exp 2: planted reliance, median [min, max] over seeds x eps in {0.02,0.05,0.1}; "
          "frac valid (planted rule) / frac valid with planted <= max")
    rhos = sorted({r["rho"] for r in R})
    print("| cue | " + " | ".join(f"rho={x}" for x in rhos) + " |\n|---|" + "---|" * len(rhos))
    for cue in dict.fromkeys(r["cue"] for r in R):
        cells = []
        for rho in rhos:
            sel = [r for r in R if r["cue"] == cue and r["rho"] == rho and r["eps"] > 0]
            ok = [not P.validity_failures("planted", r["reliance"], cue, r["topic_acc"]) for r in sel]
            okm = [not P.validity_failures("planted", r["reliance"], cue, r["topic_acc"], args.planted_max)
                   for r in sel]
            cells.append(f"{fmt([r['reliance'][cue] for r in sel])}; {np.mean(ok):.2f}/{np.mean(okm):.2f}")
        print(f"| {cue} | " + " | ".join(cells) + " |")
    print("\n### max |other reliance| by eps, all cues and rhos: median [min, max]; frac > 0.15")
    for e in sorted({r["eps"] for r in R}):
        mo = [max_other(r) for r in R if r["eps"] == e]
        print(f"- eps={e}: {fmt(mo)}; {np.mean(np.array(mo) > P.OTHER_MAX):.2f}")
    print("\n### frac valid by eps (all cues, all rhos)")
    for e in sorted({r["eps"] for r in R}):
        sel = [r for r in R if r["eps"] == e]
        print(f"- eps={e}: planted rule {np.mean([not r['failures'] for r in sel]):.2f}, "
              f"with planted<= {args.planted_max}: "
              f"{np.mean([not P.validity_failures('planted', r['reliance'], r['cue'], r['topic_acc'], args.planted_max) for r in sel]):.2f}")
    print("\n### this probe's topic accuracy on unconfounded notes vs planted reliance (all grid rows)")
    for lo, hi in ((0, 0.3), (0.3, 0.6), (0.6, 1.0), (1.0, 1.5), (1.5, 2.5), (2.5, 99)):
        sel = [r["probe_topic_acc"] for r in R if lo <= r["reliance"][r["cue"]] < hi]
        if sel:
            print(f"- reliance [{lo}, {hi}): n={len(sel)}, probe topic acc {fmt(sel)}")
    print(f"\ntopic readability (unconfounded probe acc): {fmt([r['topic_acc'] for r in R])}")
    print(f"lstsq r2: {fmt([r['r2'] for r in R])}; train acc: {fmt([r['train_acc'] for r in R])}; "
          f"lbfgs iters: {fmt([r['n_iter'] for r in R])}")
    worst = Counter(max((f for f in r["reliance"] if f != r["cue"]), key=lambda f: abs(r["reliance"][f]))
                    for r in R if max_other(r) > P.OTHER_MAX)
    print(f"most-offending other cue when > 0.15: {worst.most_common(8)}")


def build(args):
    R = rows(args.tag)
    for kind in ("planted", "null"):
        jobs = defaultdict(list)
        for r in R:
            if r["kind"] == kind:
                jobs[r["job"]].append(r)
        acc = [j for j, a in jobs.items() if a[-1]["accepted"]]
        fits = sum(len(a) for a in jobs.values())
        print(f"\n### {kind}: {len(acc)}/{len(jobs)} jobs accepted; {fits} fits total; "
              f"{fits / max(len(acc), 1):.1f} fits per accepted probe; "
              f"draws (distinct seeds) per job: {fmt([len({x['seed'] for x in a}) for a in jobs.values()])}")
        reasons = Counter(f.split(":")[0] for r in R if r["kind"] == kind for f in r["failures"])
        print(f"failure reasons over all fits: {dict(reasons)}")
        offenders = Counter(f.split(":")[1] for r in R if r["kind"] == kind for f in r["failures"] if ":" in f)
        print(f"offending other cues: {offenders.most_common(10)}")
        if kind == "planted":
            print("| job | cue | topics | sign | eps | rho | reliance | max other | fits | accepted |\n|---|---|---|---|---|---|---|---|---|---|")
            for j, a in sorted(jobs.items()):
                r = a[-1]
                print(f"| {j} | {r['cue']} | {'/'.join(r['topics'])} | {r['sign']:+d} | {r['eps']} | {r['rho']} | "
                      f"{r['reliance'][r['cue']]:.2f} | {max_other(r):.2f} | {len(a)} | {r['accepted']} |")
            ok = [a[-1] for a in jobs.values() if a[-1]["accepted"]]
            if ok:
                print(f"accepted planted reliance: {fmt([r['reliance'][r['cue']] for r in ok])}; "
                      f"max other {fmt([max_other(r) for r in ok])}; rho {Counter(r['rho'] for r in ok)}; "
                      f"eps {Counter(r['eps'] for r in ok)}")
            fail_cues = Counter(a[-1]["cue"] for a in jobs.values() if not a[-1]["accepted"])
            print(f"cues of failed jobs: {dict(fail_cues)}")
        else:
            ok = [a[-1] for a in jobs.values() if a[-1]["accepted"]]
            if ok:
                print(f"accepted null max |reliance|: {fmt([max_other(r) for r in ok])}; eps {Counter(r['eps'] for r in ok)}")
            print(f"null max|rel| by eps over all fits: " + "; ".join(
                f"eps={e}: {fmt([max_other(r) for r in R if r['kind'] == 'null' and r['eps'] == e])}"
                for e in P.EPS_CHOICES if any(r['kind'] == 'null' and r['eps'] == e for r in R)))


def stability(args):
    R = rows(f"stability_{args.tag}")
    print("| probe | cue | original | retrained (5 train seeds) | remeasured (5 eval sets) | other cue > 0.15 on retrain |\n|---|---|---|---|---|---|")
    man = {m["name"]: m for m in json.loads((ROOT / "artifacts/probes" / args.tag / "manifest.json").read_text())}
    for name in dict.fromkeys(r["name"] for r in R):
        cue = man[name]["cue"]
        tr = [r["reliance"][cue] for r in R if r["name"] == name and r["mode"] == "train_seed"]
        me = [r["reliance"][cue] for r in R if r["name"] == name and r["mode"] == "remeasure"]
        bad = sum(max_other(r | {"cue": cue}) > P.OTHER_MAX for r in R if r["name"] == name and r["mode"] == "train_seed")
        print(f"| {name} | {cue} | {man[name]['reliance'][cue]:.2f} | {fmt(tr)} sd {np.std(tr, ddof=1):.2f} | "
              f"{fmt(me)} sd {np.std(me, ddof=1):.3f} | {bad}/{len(tr)} |")


def gradient(args):
    man = json.loads((ROOT / "artifacts/probes" / args.tag / "manifest.json").read_text())
    for kind in ("planted", "null"):
        s = [m["g_top5_share"] for m in man if m["kind"] == kind]
        print(f"- accepted {kind}: n={len(s)}, top-5 share of sum|g| {fmt(s)}")
    R = rows("grid")
    print("grid probes by planted reliance bucket:")
    for lo, hi in ((0, 0.3), (0.3, 0.6), (0.6, 1.0), (1.0, 2.0), (2.0, 99)):
        sel = [r["g_top5_share"] for r in R if lo <= r["reliance"][r["cue"]] < hi]
        if sel:
            print(f"- [{lo}, {hi}): n={len(sel)}, {fmt(sel)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["grid", "build", "stability", "gradient"])
    ap.add_argument("--planted-max", type=float, default=1.0)
    ap.add_argument("--tag", default="build")
    a = ap.parse_args()
    {"grid": grid, "build": build, "stability": stability, "gradient": gradient}[a.cmd](a)
