"""Build one episode from an explicit list of artifacts (for knob episodes), GPU.

    flock /tmp/shifthunt-gpu.lock python scripts/build_mixed_episode.py --out .cache/bank/ep221 --seed 201 \
        --slots knob_trap/planted_003,build_screen/null_012,... [--pool build_screen,build_screen2,knob_trap]

The slots are used in the given order after a seeded shuffle (random.Random("mixed:{seed}")), so the probe
index does not reveal the slot type. --pool sets the decoy/sign distributions (default: every build named in
--slots plus the base pool); only valid planted artifacts and nulls of the pool count. Each slot must be
drawable (a null, or a planted artifact whose ref says valid). Prints counts only.
"""
import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import episode_files as E  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from build_episode import real_encoder  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--slots", required=True, help="comma-separated build/name keys")
    ap.add_argument("--pool", default=None, help="comma-separated builds for decoy statistics")
    ap.add_argument("--artifacts", default=ROOT / "artifacts", type=Path)
    ap.add_argument("--substrate", choices=("templated", "freetext", "freetext_hard"), default=None,
                    help="write task.json 'substrate' (task.py SUBSTRATE_MD: freetext_hard episodes use 'freetext', "
                         "templated writes no key, as in the templated bank); must match the generator in use")
    args = ap.parse_args()
    substrate = None
    if args.substrate is not None:
        generator = E.tg.__name__.rsplit(".", 1)[-1]  # freetext_run.py swaps shifthunt.textgen
        want = {"templated": "textgen", "freetext": "freetext", "freetext_hard": "freetext_hard"}[args.substrate]
        if generator != want:
            sys.exit(f"--substrate {args.substrate} but the note generator is {generator} "
                     f"(run through scripts/freetext_run.py{' --hard' if want == 'freetext_hard' else ''})")
        substrate = None if args.substrate == "templated" else "freetext"
    if args.out.exists():
        sys.exit(f"{args.out} exists")
    keys = args.slots.split(",")
    builds = args.pool.split(",") if args.pool else sorted(
        {"build_screen", "build_screen2"} | {k.split("/")[0] for k in keys})
    pool = E.load_pool(args.artifacts, builds)
    by_key = {a.key: a for a in pool}
    missing = [k for k in keys if k not in by_key]
    if missing:
        sys.exit(f"not drawable (missing, or planted and not valid): {missing}")
    arts = [by_key[k] for k in keys]
    if len({frozenset(a.meta["topics"]) for a in arts}) != len(arts):
        sys.exit("slots must have distinct topic pairs")
    cues = [c for a in arts if a.meta["kind"] == "planted" for c in E.mains_of(a.meta)[0]]
    if len(set(cues)) != len(cues):
        sys.exit("planted slots must have distinct cues")
    random.Random(f"mixed:{args.seed}").shuffle(arts)
    E.write_episode(args.out, arts, args.seed, real_encoder(), pool=pool, substrate=substrate)
    print(f"episode {args.out}: {len(arts)} probes ({len(cues)} planted) from a pool of {len(pool)}")


if __name__ == "__main__":
    main()
