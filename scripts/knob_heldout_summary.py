"""Knob heldout: episode-level pass of three regex styles (+ privileged formula latents, `none` on nulls)
per grid mode, from results/knobs/heldout/measure.jsonl. CPU, no arrays.

    python scripts/knob_heldout_summary.py [--episodes 100 --seed 0]

A planted probe passes iff the style's regex has BA >= 0.8 on that grid and the formula latents clear
removal >= tau (tau from the same grid) and kept >= 0.8. Styles: literal (sample wordings; the shipped
detector where the cue has no literal form), detector (shipped), structural (hand-written; detector where
none). Episodes are drawn with episodes.draw over the valid pool (20 planted + 12 nulls).
"""
import argparse
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import episodes as EP  # noqa: E402

OUT = ROOT / "results" / "knobs" / "heldout"
MODES = ("orig", "hc", "hm", "mix")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rows = {r["probe"]: r for r in map(json.loads, open(OUT / "measure.jsonl"))}
    pool = []
    for key, r in rows.items():
        b, n = key.split("/")
        meta = json.loads((EP.PROBES / b / f"{n}.json").read_text())
        pool.append(SimpleNamespace(key=key, meta=meta))

    def probe_pass(r, style, mode):
        d = r[mode]
        ba = d[f"ba_{style}"]
        if ba is None:
            ba = d["ba_detector"]
        return ba >= 0.8 and d["formula_pass"]

    rng = random.Random(f"episodes:{args.seed}")
    eps = [EP.draw(rng, pool) for _ in range(args.episodes)]
    out = {}
    for style in ("literal", "detector", "structural"):
        for mode in MODES:
            ok_p = [probe_pass(rows[a.key], style, mode) for e in eps for a in e if a.meta["kind"] == "planted"]
            ok_e = [all(probe_pass(rows[a.key], style, mode) for a in e if a.meta["kind"] == "planted") for e in eps]
            out[f"{style}/{mode}"] = {"episode_pass": sum(ok_e) / len(ok_e), "planted_pass": sum(ok_p) / len(ok_p)}
    print(f"{'style':12s} " + " ".join(f"{m:>12s}" for m in MODES) + "   (episode / planted-slot pass)")
    for style in ("literal", "detector", "structural"):
        print(f"{style:12s} " + " ".join(f"{out[f'{style}/{m}']['episode_pass']:.2f}/{out[f'{style}/{m}']['planted_pass']:.2f}".rjust(12)
                                         for m in MODES))
    (OUT / "episodes.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
