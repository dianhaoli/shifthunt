"""Encode every accepted probe's hidden grids, its reliance set and its paired-flip scan set (GPU).

    python scripts/grader_build.py [--builds build_screen build_screen2] [--new-salt]

The hidden grids are salted with the pool's secret salt (hidden.py): artifacts/grader/private/salt,
created by --new-salt (refused if one exists) and otherwise read. The salt is never printed.

Per probe writes artifacts/grader/<build>/<name>.npz (gitignored; regenerable from this command):
  grid_*   planted grid (planted probes only): logits, latents (CSR parts), topic, flags [15, n]
  null_*   topic-only grid: same fields
  rel_*    the probe's 384-note reliance set re-encoded with latents: logits, latents, topic, flags
  scan_*   paired-flip set (hidden.scan_notes): logits, latents, base levels, topic
  salt_id  hidden.salt_id(salt), to tell which salt built the grids
and <name>_texts.json with the grid texts (the regexes run on these). Logits are probe_logit of the
pooled residual, i.e. the probe's true logits. A consistency check re-measures reliance from rel_*
and compares with the stored value (same texts, same batches -> must match to ~1e-9).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import hidden as H  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.ablation import probe_logit  # noqa: E402
from shifthunt.substrate import Subject  # noqa: E402

PROBES = ROOT / "artifacts" / "probes"
OUT = ROOT / "artifacts" / "grader"


def pack(prefix, logits, F, **extra):
    return {f"{prefix}_logits": logits, f"{prefix}_data": F.data, f"{prefix}_indices": F.indices,
            f"{prefix}_indptr": F.indptr} | {f"{prefix}_{k}": v for k, v in extra.items()}


def flag_matrix(flags):
    return np.stack([flags[f] for f in tg.FEATURES]).astype(np.int8)


def build_one(subject, build, meta, arr, salt):
    w, b = arr["w"], float(arr["b"])
    topics, eval_seed = tuple(meta["topics"]), meta["eval_seed"]
    out, texts = {"salt_id": np.array(H.salt_id(salt))}, {}

    def enc(t):
        resid, F = H.encode_sparse(subject, t)
        return probe_logit(resid, w, b), F

    if meta["kind"] == "planted":
        t, y, flags = H.planted_grid(topics, [meta["cue"]], eval_seed, salt)
        logits, F = enc(t)
        out |= pack("grid", logits, F, topic=y, flags=flag_matrix(flags))
        texts["grid"] = t
    t, y, flags = H.null_grid(topics, eval_seed, salt)
    logits, F = enc(t)
    out |= pack("null", logits, F, topic=y, flags=flag_matrix(flags))
    texts["null"] = t

    t, y, flags = P.reliance_set(topics, eval_seed)
    logits, F = enc(t)
    out |= pack("rel", logits, F, topic=y, flags=flag_matrix(flags))
    rel = P.measure_reliance(logits, flags, y, meta["cue"], meta["sign"])["reliance"]
    drift = max(abs(rel[f] - meta["reliance"][f]) for f in tg.FEATURES)

    t, levels, y = H.scan_notes(topics, eval_seed)
    logits, F = enc(t)
    out |= pack("scan", logits, F, levels=levels, topic=y)

    d = OUT / build
    d.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(d / f"{meta['name']}.npz", **out)
    (d / f"{meta['name']}_texts.json").write_text(json.dumps(texts))
    return drift


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--builds", nargs="+", default=["build_screen", "build_screen2"])
    ap.add_argument("--new-salt", action="store_true", help="create the pool's salt (refused if one exists)")
    args = ap.parse_args()
    salt = H.new_salt(OUT) if args.new_salt else H.load_salt(OUT)
    print(f"salt id {H.salt_id(salt)}", flush=True)
    subject = Subject()
    t0 = time.time()
    for build in args.builds:
        for m in json.loads((PROBES / build / "manifest.json").read_text()):
            t = time.time()
            meta, arr = P.load_probe(PROBES / build, m["name"])
            drift = build_one(subject, build, meta, arr, salt)
            print(f"{build}/{meta['name']} {meta['kind']} reliance drift {drift:.2e} {time.time() - t:.0f}s",
                  flush=True)
            if drift > 1e-6:
                raise RuntimeError("re-encoded reliance set does not reproduce the stored reliance")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
