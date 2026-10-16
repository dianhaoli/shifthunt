"""Probe experiments: reliance vs (rho, eps) grid, seed stability, and the planted/null yield build.

    python scripts/probe_experiments.py grid      [--seeds 3]
    python scripts/probe_experiments.py build     [--planted 20 --nulls 10 --planted-max X --screen 64 --tag T]
    python scripts/probe_experiments.py stability [--probes 5 --seeds 5]

Every probe trained is written as one JSON row (spec + reliance + diagnostics) to
results/probes/<command or tag>.jsonl; build also saves accepted probes (w, b, g, mu + metadata)
to artifacts/probes/<tag>/. Encodings are cached per batch in .cache/encodings. Needs a GPU and HF access.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.substrate import Subject  # noqa: E402

RESULTS = ROOT / "results" / "probes"
ARTIFACTS = ROOT / "artifacts" / "probes"
CACHE = ROOT / ".cache" / "encodings"

GRID_CUES = ("exclamation", "she_pronoun", "hashtag", "weekday", "british_spelling", "bullet_list")
GRID_RHOS = (0.9, 0.95, 0.98, 1.0)
GRID_EPS = (0.0, 0.02, 0.05, 0.1)


def topic_pair(rng):
    return tuple(rng.sample(tg.TOPIC_NAMES, 2))


def writer(name):
    RESULTS.mkdir(parents=True, exist_ok=True)
    f = open(RESULTS / f"{name}.jsonl", "w")

    def write(row):
        f.write(json.dumps(row) + "\n")
        f.flush()
    return write


def cmd_grid(lab, args):
    """Exp 1 + 2: rho x eps per cue; eps = 0 is the perfect cue-topic confound."""
    write = writer("grid")
    for ci, cue in enumerate(GRID_CUES):
        for s in range(args.seeds):
            rng = random.Random(f"grid:{cue}:{s}")
            topics, sign, eval_seed, seed = topic_pair(rng), rng.choice((1, -1)), rng.getrandbits(31), rng.getrandbits(31)
            for eps in GRID_EPS:
                for rho in GRID_RHOS:
                    t = time.time()
                    p = lab.train(P.Spec("planted", topics, cue, sign, rho, eps, seed, eval_seed))
                    row = p.summary() | {"rep": s}
                    write(row)
                    print(f"{cue:17s} s{s} eps={eps:.2f} rho={rho:.2f} rel={row['reliance'][cue]:+.3f} "
                          f"maxother={max(abs(v) for f, v in row['reliance'].items() if f != cue):.3f} "
                          f"{p.failures} {time.time() - t:.1f}s", flush=True)


def cmd_build(lab, args):
    """Exp 4: build planted (cycling over PLANTABLE cues) and null probes with the validity rules."""
    write = writer(args.tag)
    out = ARTIFACTS / args.tag
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(f"build:{args.tag}")
    cues = list(P.PLANTABLE)
    rng.shuffle(cues)
    manifest = []
    jobs = [("planted", cues[i % len(cues)]) for i in range(args.planted)] + [("null", None)] * args.nulls
    for j, (kind, cue) in enumerate(jobs):
        topics, eval_seed = topic_pair(rng), rng.getrandbits(31)
        draw_rng = random.Random(rng.getrandbits(64))
        t = time.time()
        if kind == "planted":
            sign = rng.choice((1, -1))
            p, attempts = P.search_planted(lab, topics, cue, sign, eval_seed, draw_rng,
                                           max_draws=args.max_draws, planted_max=args.planted_max,
                                           n_screen=args.screen)
        else:
            p, attempts = P.search_null(lab, topics, eval_seed, draw_rng, max_draws=args.max_draws * 3,
                                        n_screen=args.screen)
        for k, a in enumerate(attempts):
            write(a | {"job": j, "attempt": k, "accepted": p is not None and k == len(attempts) - 1})
        name = None
        if p is not None:
            name = f"{kind}_{j:03d}"
            manifest.append(P.save_probe(p, out, name) | {"attempts": len(attempts)})
        rel = p.rel["reliance"][cue] if (p is not None and cue) else None
        print(f"job {j} {kind} {cue} {topics} -> {name} after {len(attempts)} fits"
              f"{'' if rel is None else f' rel={rel:.3f}'} "
              f"last failures={attempts[-1]['failures']} {time.time() - t:.0f}s", flush=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))


def cmd_stability(lab, args):
    """Exp 3: retrain accepted planted probes with new training seeds (same instance and settings),
    and re-measure the original probe on fresh reliance sets (measurement noise)."""
    write = writer(f"stability_{args.tag}")
    src = ARTIFACTS / args.tag
    manifest = json.loads((src / "manifest.json").read_text())
    planted = [m for m in manifest if m["kind"] == "planted"][:args.probes]
    for m in planted:
        base = P.spec_from_meta(m)
        for s in range(args.seeds):
            spec = P.Spec(**{**base.__dict__, "seed": random.Random(f"stab:{m['name']}:{s}").getrandbits(31)})
            p = lab.train(spec)
            write(p.summary() | {"name": m["name"], "mode": "train_seed", "rep": s})
            print(f"{m['name']} {m['cue']} train-seed {s}: rel={p.rel['reliance'][m['cue']]:.3f} {p.failures}", flush=True)
        # measurement noise: same probe, independent reliance sets (eval sets keyed by a new tag)
        meta, arr = P.load_probe(src, m["name"])
        for s in range(args.seeds):
            texts, y, flags = P.tg.sample_grid(random.Random(f"remeasure:{m['name']}:{s}"), list(base.topics),
                                               P.N_RELIANCE, P.cue_strings(base.eval_seed), mains=[])
            R = lab.enc.encode(texts)[0]
            rel = P.measure_reliance(P.probe_logit(R, arr["w"], float(arr["b"])), flags, y, base.cue, base.sign)
            write({"name": m["name"], "mode": "remeasure", "rep": s, "cue": base.cue,
                   "reliance": rel["reliance"], "topic_coef": rel["topic_coef"], "r2": rel["r2"]})
            print(f"{m['name']} {m['cue']} remeasure {s}: rel={rel['reliance'][base.cue]:.3f}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["grid", "build", "stability"])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--planted", type=int, default=20)
    ap.add_argument("--nulls", type=int, default=10)
    ap.add_argument("--max-draws", type=int, default=4)
    ap.add_argument("--planted-max", type=float, default=None)
    ap.add_argument("--probes", type=int, default=5)
    ap.add_argument("--tag", default="build", help="build: output name; stability: which build to read")
    ap.add_argument("--screen", type=int, default=0, help="seeds screened per draw by flip_imbalance (0 = off)")
    args = ap.parse_args()
    t = time.time()
    lab = P.Lab(P.CachedEncoder(Subject(), CACHE))
    {"grid": cmd_grid, "build": cmd_build, "stability": cmd_stability}[args.cmd](lab, args)
    print(f"done in {time.time() - t:.0f}s; encoded {lab.enc.n_encoded}, cache hits {lab.enc.n_cached}")


if __name__ == "__main__":
    main()
