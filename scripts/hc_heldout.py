"""Held-out dependence check for any probe artifact (followup section "hardercue"; GPU).

Run from the isolated harness root through the free-text substrate:

    cd <root> && flock <gpu.lock> python scripts/freetext_run.py <repo>/scripts/hc_heldout.py \
        --keys BUILD/NAME[:ROLE] ... --out <private json> [--stream hcheld] [--n 1024]

ROLE is hard, easy or null (default: null for null artifacts, easy otherwise). For each artifact it renders n fresh
notes (probes.reliance_set, stream "{stream}:{eval_seed}"; no selection step sees this stream), takes the
artifact's own unscaled w, b (dependence is a ratio to the topic coefficient, so the episode's logit scale does
not change it), and reports probes.reliance_boot (point and bootstrap SE per property). Rules (README, choices 5e
and 6): planted: main >= 0.30 and every other |dep| <= 0.15; null: every |dep| <= 0.15. +2SE is reported only.
The output names properties, so it must go to a private (git-ignored) path; stdout prints roles and numbers only.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

MAIN_MIN = 0.30
OTHER_MAX = 0.15


def judge(rel, se, kind, cue):
    """-> (pass, worst other property, its |dep|, its |dep| + 2SE). cue is None for a null."""
    others = {f: abs(v) for f, v in rel.items() if f != cue}
    worst = max(others, key=others.get)
    ok = others[worst] <= OTHER_MAX
    if kind == "planted":
        ok = ok and rel[cue] >= MAIN_MIN
    return ok, worst, others[worst], others[worst] + 2 * se[worst]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", nargs="+", required=True)
    ap.add_argument("--stream", default="hcheld")
    ap.add_argument("--n", type=int, default=1024)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from probe_experiments import CACHE
    from shifthunt import probes as P
    from shifthunt.ablation import probe_logit
    from shifthunt.substrate import Subject
    lab = P.Lab(P.CachedEncoder(Subject(), CACHE))
    rows = []
    for item in args.keys:
        key, _, role = item.partition(":")
        build, name = key.split("/")
        m, arr = P.load_probe(ROOT / "artifacts" / "probes" / build, name)
        role = role or ("null" if m["kind"] == "null" else "easy")
        R, y, fl = lab.heldout_data(tuple(m["topics"]), m["eval_seed"], args.stream, args.n)
        logits = probe_logit(R, arr["w"], float(arr["b"]))
        rel, se, tc = P.reliance_boot(logits, fl, y, m["cue"], m["sign"])
        ok, worst, wv, whi = judge(rel, se, m["kind"], m["cue"])
        row = {"key": key, "role": role, "kind": m["kind"], "cue": m["cue"], "sign": m["sign"],
               "topics": m["topics"], "stream": f"{args.stream}:{m['eval_seed']}", "n": args.n,
               "dep": rel, "se": se, "topic_coef": tc, "pass": ok, "worst_other": worst,
               "worst_other_abs": wv, "worst_other_hi": whi,
               "main": None if m["cue"] is None else rel[m["cue"]],
               "main_se": None if m["cue"] is None else se[m["cue"]]}
        rows.append(row)
        main_txt = "" if m["cue"] is None else f"main={rel[m['cue']]:.3f}+-{se[m['cue']]:.3f} "
        print(f"{role:5s} {main_txt}worst_other={wv:.3f} (+2SE {whi:.3f}) {'PASS' if ok else 'FAIL'}", flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
