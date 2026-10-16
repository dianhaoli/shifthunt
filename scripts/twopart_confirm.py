"""Post-acceptance confirmation of nested-cue probes (GPU; run from the repo root through scripts/freetext_run.py,
with --hard for freetext_hard pools):

    flock /tmp/shifthunt-gpu.lock python scripts/freetext_run.py [--hard] scripts/twopart_confirm.py <tag> [<tag> ...] \
        [--stream tpconfirm] [--n 1024] [--out .cache/tp2/confirm.json]

Dependence of each accepted probe on a fresh set (stream "{stream}:{eval_seed}", n notes; the default stream is never
used for selection or gating; pick a new stream name for each further independent check) plus the salted null grid
of artifacts/grader/<tag>/ when grader_build ran. The parent is looked up in the active substrate's IMPLIES and the
property list is the active substrate's FEATURES, so any nested family of free text or free text hard works.
Flags are as rendered (parent = any parent instance), so the parent's dependence is the add-a-parent-without-child
effect and the child's is the parent -> child swap; the alternative coding (parent-without-child flag in place of
the parent flag, child = add-child-from-nothing) is reported too.

Strict rule (as the acceptance gate): child >= 0.33 and child - 2SE >= 0.30; |parent| <= 0.10 and |parent| + 2SE
<= 0.15; every other |dependence| + 2SE <= 0.15. Prints one line per probe and writes --out (private: cue names)."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from probe_experiments import CACHE  # noqa: E402
from shifthunt import probes as P  # noqa: E402  (freetext_run swaps textgen; P.tg is the active substrate)
from shifthunt.ablation import probe_logit  # noqa: E402

tg = P.tg


def strict(rel, se, cue, parent):
    fails = []
    if rel[cue] < P.GATE_CHILD_MIN or rel[cue] - 2 * se[cue] < P.GATE_CHILD_LO:
        fails.append("child_low")
    if abs(rel[parent]) > P.GATE_PARENT_MAX or abs(rel[parent]) + 2 * se[parent] > P.GATE_PARENT_HI:
        fails.append("parent_high")
    fails += [f"other_high:{f}" for f in rel if f not in (cue, parent) and abs(rel[f]) + 2 * se[f] > P.GATE_OTHER_HI]
    return fails


def alt_coding(logits, flags, topic, cue, parent, sign, n_boot=400, seed=0):
    """Child and parent-without-child flags in place of child and any-parent: -> {name: (dep, se)}."""
    cols = [f for f in tg.FEATURES if f != parent] + ["_parent_only"]
    fl = dict(flags); fl["_parent_only"] = flags[parent] * (1 - flags[cue])

    def dep(ix):
        X = np.column_stack([fl[c][ix] for c in cols] + [topic[ix], np.ones(len(ix))]).astype(np.float64)
        coef = np.linalg.lstsq(X, logits[ix], rcond=None)[0]
        tc = abs(coef[len(cols)])
        return np.array([coef[cols.index(cue)] * sign / tc, coef[cols.index("_parent_only")] / tc])

    n = len(logits)
    point = dep(np.arange(n))
    rng = np.random.default_rng(seed)
    se = np.std([dep(rng.integers(0, n, n)) for _ in range(n_boot)], axis=0, ddof=1)
    return {f"{cue}_from_none": (float(point[0]), float(se[0])), f"{parent}_without_{cue}": (float(point[1]), float(se[1]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="+")
    ap.add_argument("--stream", default="tpconfirm")
    ap.add_argument("--n", type=int, default=1024)
    ap.add_argument("--out", default=".cache/tp2/confirm.json")
    args = ap.parse_args()
    from shifthunt.substrate import Subject
    lab = P.Lab(P.CachedEncoder(Subject(), CACHE))
    implies = getattr(tg, "IMPLIES", {})
    out = []
    for tag in args.tags:
        for js in sorted(Path(f"artifacts/probes/{tag}").glob("planted_*.json")):
            m = json.loads(js.read_text())
            cue = m["cue"]
            if cue not in tg.FEATURES or cue not in implies:
                raise SystemExit(f"{tag}/{js.stem}: cue {cue!r} is not a nested child of the active substrate "
                                 f"(use scripts/freetext_run.py, with --hard for freetext_hard pools)")
            parent = implies[cue]
            with np.load(js.with_suffix(".npz")) as z:
                w, b = z["w"], float(z["b"])
            R, y, fl = lab.heldout_data(tuple(m["topics"]), m["eval_seed"], args.stream, args.n)
            logits = probe_logit(R, w, b)
            rel, se, _ = P.reliance_boot(logits, fl, y, cue, m["sign"])
            row = {"probe": f"{tag}/{js.stem}", "topics": m["topics"], "cue": cue, "parent": parent,
                   "stream": f"{args.stream}:{m['eval_seed']}", "n": args.n,
                   "confirm": rel, "confirm_se": se, "strict_failures": strict(rel, se, cue, parent),
                   "alt_coding": alt_coding(logits, fl, np.asarray(y, np.float64), cue, parent, m["sign"])}
            if "gate" in m:
                row |= {"gate": m["gate"]["reliance"], "gate_se": m["gate"]["se"], "paired": m["gate"].get("paired")}
            gz = Path(f"artifacts/grader/{tag}/{js.stem}.npz")
            if gz.exists():
                with np.load(gz) as z:
                    if z["null_flags"].shape[0] != len(tg.FEATURES):
                        raise SystemExit(f"{gz}: {z['null_flags'].shape[0]} null flags, substrate has "
                                         f"{len(tg.FEATURES)} features (wrong --hard?)")
                    nf = {f: z["null_flags"][i] for i, f in enumerate(tg.FEATURES)}
                    nr, ns, _ = P.reliance_boot(z["null_logits"], nf, z["null_topic"], cue, m["sign"])
                row |= {"null": nr, "null_se": ns,
                        "null_over_015": {f: nr[f] for f in nr if f != cue and abs(nr[f]) > 0.15}}
            out.append(row)
            o = max((f for f in rel if f not in (cue, parent)), key=lambda f: abs(rel[f]) + 2 * se[f])
            print(f"{row['probe']:26s} {str(m['topics']):28s} {args.stream} child={rel[cue]:.3f}±{se[cue]:.3f} "
                  f"parent={rel[parent]:+.3f}±{se[parent]:.3f} worst {o}={rel[o]:+.3f}±{se[o]:.3f} "
                  f"strict={'PASS' if not row['strict_failures'] else ','.join(row['strict_failures'])}"
                  + (f" | null child={nr[cue]:.3f}±{ns[cue]:.3f} parent={nr[parent]:+.3f}±{ns[parent]:.3f}"
                     f" null>0.15={sorted(row['null_over_015'])}" if gz.exists() else ""),
                  flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
