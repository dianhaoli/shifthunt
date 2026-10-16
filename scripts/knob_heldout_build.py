"""Knob heldout: encode held-out-wording versions of the existing hidden grids and reliance sets (GPU).

    flock /tmp/shifthunt-gpu.lock python scripts/knob_heldout_build.py [--check-only]

For every valid planted probe of build_screen/build_screen2: the probe's salted planted grid re-rendered
with the SAME RNG stream (hidden:{salt}:{eval_seed}) in modes hc and hm (knob_heldout.render_ho), so each
row pairs with the stored grid row. For every probe (planted valid + null): the 384-note reliance set
re-rendered in mode hc. Before encoding, mode None must reproduce the stored grid texts exactly.
Writes artifacts/grader/knob_heldout/<build>__<name>.npz (+ _texts.json). Never prints the salt.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import hidden as H  # noqa: E402
from shifthunt import knob_heldout as K  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402

PROBES = ROOT / "artifacts" / "probes"
GRADER = ROOT / "artifacts" / "grader"
OUT = GRADER / "knob_heldout"
BUILDS = ("build_screen", "build_screen2")


def pool():
    out = []
    for b in BUILDS:
        for m in json.loads((PROBES / b / "manifest.json").read_text()):
            ref = GRADER / b / f"{m['name']}_ref.json"
            if m["kind"] == "planted" and not json.loads(ref.read_text())["valid"]:
                continue
            out.append((b, m["name"]))
    return out


def sets_for(build, name, salt):
    meta = json.loads((PROBES / build / f"{name}.json").read_text())
    topics, es = list(meta["topics"]), meta["eval_seed"]
    cues = P.cue_strings(es)
    out = {}
    if meta["kind"] == "planted":
        stored = json.loads((GRADER / build / f"{name}_texts.json").read_text())["grid"]
        t0, _, _ = K.grid_ho(random.Random(f"hidden:{salt}:{es}"), topics, H.N_GRID_1, cues, [meta["cue"]], None)
        if t0 != stored:
            raise RuntimeError(f"{build}/{name}: mode None does not reproduce the stored grid")
        for mode in ("hc", "hm"):
            out[f"grid_{mode}"] = K.grid_ho(random.Random(f"hidden:{salt}:{es}"), topics, H.N_GRID_1, cues,
                                            [meta["cue"]], mode)
    t0, _, _ = K.grid_ho(random.Random(f"reliance:{es}"), topics, P.N_RELIANCE, cues, [], None)
    if t0 != P.reliance_set(topics, es)[0]:
        raise RuntimeError(f"{build}/{name}: mode None does not reproduce the reliance set")
    out["rel_hc"] = K.grid_ho(random.Random(f"reliance:{es}"), topics, P.N_RELIANCE, cues, [], "hc")
    return meta, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    salt = H.load_salt(GRADER)
    items = pool()
    print(f"{len(items)} probes", flush=True)
    if args.check_only:
        for b, n in items:
            meta, sets = sets_for(b, n, salt)
            ex = sets.get("grid_hm", sets["rel_hc"])[0]
            print(b, n, meta.get("cue"), "ok", repr(ex[1][:300]) if len(ex) > 1 else "")
        return
    from shifthunt.ablation import probe_logit
    from shifthunt.substrate import Subject
    subject = Subject()
    OUT.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    for b, n in items:
        t = time.time()
        meta, sets = sets_for(b, n, salt)
        _, arr = P.load_probe(PROBES / b, n)
        out, texts = {}, {}
        for key, (tx, y, flags) in sets.items():
            resid, F = H.encode_sparse(subject, tx)
            out |= {f"{key}_logits": probe_logit(resid, arr["w"], float(arr["b"])), f"{key}_data": F.data,
                    f"{key}_indices": F.indices, f"{key}_indptr": F.indptr, f"{key}_topic": y,
                    f"{key}_flags": np.stack([flags[f] for f in tg.FEATURES]).astype(np.int8)}
            texts[key] = tx
            del resid, F
        np.savez_compressed(OUT / f"{b}__{n}.npz", **out)
        (OUT / f"{b}__{n}_texts.json").write_text(json.dumps(texts))
        print(f"{b}/{n} {meta['kind']} {meta.get('cue')} {time.time() - t:.0f}s", flush=True)
    print(f"done {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
