"""Build planted probes for chosen cues only (GPU; run through scripts/freetext_run.py for free text).

    python scripts/freetext_run.py scripts/freetext_build_cues.py --tag ft_twopart --cues ps_question signoff_excl \
        --per-cue 4 [--max-draws 6]

Same search and validity rules as `probe_experiments.py build` (probes.search_planted), only the cue list and
the number of probes per cue differ. Writes results/probes/<tag>.jsonl and artifacts/probes/<tag>/.

Nested cues (a child in IMPLIES, e.g. ps_question -> postscript):
    --parent-rate R   train with P(parent | y) = R for both labels (freetext.sample_texts balance_parents), so
                      the parent (any P.S.) no longer predicts the label and only the child form does.
    --gate            after the usual selection on the reliance set, accept only if a fresh held-out set
                      (stream "tpgate:{eval_seed}", --gate-n notes) passes probes.make_parent_gate: |parent| <=
                      0.10 and +2SE <= 0.15, child >= 0.33 and -2SE >= 0.30, every other |.| + 2SE <= 0.15.
Without these flags the build is unchanged.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from probe_experiments import ARTIFACTS, CACHE, topic_pair, writer  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt.substrate import Subject  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tag", required=True)
    ap.add_argument("--cues", nargs="+", required=True)
    ap.add_argument("--per-cue", type=int, default=4)
    ap.add_argument("--max-draws", type=int, default=4)
    ap.add_argument("--parent-rate", type=float, default=None)
    ap.add_argument("--eps-choices", type=float, nargs="+", default=list(P.EPS_CHOICES),
                    help="topic-flip rates drawn per (seed, eps) draw (default probes.EPS_CHOICES)")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--gate-n", type=int, default=P.GATE_N)
    ap.add_argument("--gate-parent-max", type=float, default=P.GATE_PARENT_MAX)
    ap.add_argument("--gate-parent-hi", type=float, default=P.GATE_PARENT_HI)
    ap.add_argument("--gate-child-min", type=float, default=P.GATE_CHILD_MIN)
    ap.add_argument("--gate-child-lo", type=float, default=P.GATE_CHILD_LO)
    ap.add_argument("--gate-other-hi", type=float, default=P.GATE_OTHER_HI)
    args = ap.parse_args()
    gate = None
    if args.gate:
        gate = P.make_parent_gate(n=args.gate_n, parent_max=args.gate_parent_max, parent_hi=args.gate_parent_hi,
                                  child_min=args.gate_child_min, child_lo=args.gate_child_lo,
                                  other_hi=args.gate_other_hi)
    lab = P.Lab(P.CachedEncoder(Subject(), CACHE))
    write = writer(args.tag)
    out = ARTIFACTS / args.tag
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(f"build:{args.tag}")
    manifest = []
    for j, cue in enumerate(c for c in args.cues for _ in range(args.per_cue)):
        topics, eval_seed = topic_pair(rng), rng.getrandbits(31)
        draw_rng = random.Random(rng.getrandbits(64))
        sign = rng.choice((1, -1))
        t = time.time()
        p, attempts = P.search_planted(lab, topics, cue, sign, eval_seed, draw_rng, max_draws=args.max_draws,
                                       parent_rate=args.parent_rate, gate=gate,
                                       eps_choices=tuple(args.eps_choices))
        for k, a in enumerate(attempts):
            write(a | {"job": j, "attempt": k, "accepted": p is not None and k == len(attempts) - 1})
        name = None
        if p is not None:
            name = f"planted_{j:03d}"
            manifest.append(P.save_probe(p, out, name) | {"attempts": len(attempts)})
        print(f"job {j} {cue} {topics} -> {name} after {len(attempts)} fits "
              f"last failures={attempts[-1]['failures']} {time.time() - t:.0f}s", flush=True)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1))  # after every job (partial runs)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
