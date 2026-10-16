"""Knob heldout: pack the HC (held-out content) grids as ordinary pool builds, so episodes.load /
episode_files.load_pool / build_episode.py work unchanged (CPU).

    flock /tmp/shifthunt-gpu.lock python scripts/knob_heldout_pack.py

For build_screen -> knob_heldout_hc_s and build_screen2 -> knob_heldout_hc_s2:
  artifacts/probes/<new>/   copies of the valid planted + null probes (json, npz) and a manifest
  artifacts/grader/<new>/   <name>.npz = the original grader arrays with grid_* replaced by the HC grid
                            (same notes, held-out wordings), <name>_texts.json with the HC grid texts,
                            <name>_ref.json recomputed on the HC grid exactly as grader_feasibility does
                            (reference ids and candidates from the ORIGINAL reliance set; tau from the
                            reference removal on the HC grid).
Also flags each planted probe whose main reliance on the HC reliance set is < 0.3 (prompt bound) in
the ref json (`ho_reliance`, `ho_reliance_ok`); nulls get `ho_max_abs` in their probe json copy.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import episodes as EP  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
import grader_feasibility as GF  # noqa: E402

HO = ROOT / "artifacts" / "grader" / "knob_heldout"
RES = ROOT / "results" / "knobs" / "heldout"
NEW = {"build_screen": "knob_heldout_hc_s", "build_screen2": "knob_heldout_hc_s2"}
GRID_KEYS = ("logits", "data", "indices", "indptr", "topic", "flags")


def main():
    meas = {r["probe"]: r for r in map(json.loads, open(RES / "measure.jsonl"))}
    for old, new in NEW.items():
        pdir, gdir = EP.PROBES / new, EP.GRADER / new
        if pdir.exists() or gdir.exists():
            raise SystemExit(f"{new} exists; refusing to overwrite")
        pdir.mkdir(parents=True)
        gdir.mkdir(parents=True)
        manifest = []
        for m in json.loads((EP.PROBES / old / "manifest.json").read_text()):
            hp = HO / f"{old}__{m['name']}.npz"
            if not hp.exists():  # invalid planted probes were not re-rendered
                continue
            manifest.append(m)
            meta = json.loads((EP.PROBES / old / f"{m['name']}.json").read_text())
            r = meas[f"{old}/{m['name']}"]
            meta["knob_heldout"] = {"mode": "hc", "source": f"{old}/{m['name']}",
                                    "ho_reliance": r["rel_hc"]}
            (pdir / f"{m['name']}.json").write_text(json.dumps(meta, indent=1))
            shutil.copy(EP.PROBES / old / f"{m['name']}.npz", pdir / f"{m['name']}.npz")
            a = EP.load(old, m["name"])
            texts = dict(a.texts)
            if meta["kind"] == "planted":
                with np.load(hp) as f:
                    for k in GRID_KEYS:
                        a.z[f"grid_{k}"] = f[f"grid_hc_{k}"]
                texts["grid"] = json.loads((HO / f"{old}__{m['name']}_texts.json").read_text())["grid_hc"]
            np.savez_compressed(gdir / f"{m['name']}.npz", **a.z)
            (gdir / f"{m['name']}_texts.json").write_text(json.dumps(texts))
            if meta["kind"] == "planted":
                a.texts = texts
                nums, ids = GF.analyse(a)
                cue = meta["cue"]
                nums["ho_reliance"] = r["rel_hc"][cue]
                nums["ho_reliance_ok"] = r["rel_hc"][cue] >= 0.3
                nums["ho_max_other"] = r["max_other_hc"]
                (gdir / f"{m['name']}_ref.json").write_text(json.dumps(nums | ids))
                print(f"{new}/{m['name']} {cue:16s} tau {nums['tau'][0]:.3f} ref {nums['ref_removal'][0]:.3f} "
                      f"valid {nums['valid']} ho_rel {nums['ho_reliance']:.2f}", flush=True)
            del a
        (pdir / "manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
