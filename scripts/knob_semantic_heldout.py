"""Knob semantic, Exp S5 (GPU encode + CPU measure): reliance and removal on HELD-OUT hedge forms.

    flock /tmp/shifthunt-gpu.lock python scripts/knob_semantic_heldout.py [--check-only]

For each knob_semantic probe: the reliance set (same stream reliance:{es}) and hidden grid (same stream) are
re-rendered with knob_semantic's held-out bank (use_bank("ho"); same notes, only the stance forms differ).
Measures held-out reliance, grid E_S (vs in-bank), latent share, in-bank reference removal/kept on the held-out
grid, and regex BA (generic lexicon; regex of the in-bank hedge forms) on the held-out grid.
Writes results/knobs/semantic/heldout.json (numbers only).
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import effects as E  # noqa: E402
from shifthunt import hidden as H  # noqa: E402
from shifthunt import knob_semantic as K  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt.ablation import probe_logit  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from knob_semantic_build import measure_rel  # noqa: E402
from knob_semantic_measure import load_set  # noqa: E402

TAG = "knob_semantic"
PDIR, GDIR = ROOT / "artifacts" / "probes" / TAG, ROOT / "artifacts" / "grader" / TAG
RES = ROOT / "results" / "knobs" / "semantic"


def sets_for(meta, salt, bank):
    K.use_bank(bank)
    topics, es, cues = meta["topics"], meta["eval_seed"], P.cue_strings(meta["eval_seed"])
    out = {"rel": K.grid_h(random.Random(f"reliance:{es}"), topics, P.N_RELIANCE, cues),
           "grid": K.grid_h(random.Random(f"hidden_semantic:{salt}:{es}"), topics, H.N_GRID_1, cues)}
    K.use_bank("main")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    salt = H.load_salt(ROOT / "artifacts" / "grader")
    manifest = json.loads((PDIR / "manifest.json").read_text())
    stored = {m["name"]: json.loads((GDIR / f"{m['name']}_texts.json").read_text()) for m in manifest}
    for m in manifest:  # main bank must reproduce the stored texts; held-out must keep flags, change only forms
        main_sets, ho = sets_for(m, salt, "main"), sets_for(m, salt, "ho")
        for k in ("rel", "grid"):
            assert main_sets[k][0] == stored[m["name"]][k], (m["name"], k)
            assert all((main_sets[k][2][f] == ho[k][2][f]).all() for f in K.FEATS_H)
    print("check ok; example held-out note:\n" + ho["grid"][0][1])
    if args.check_only:
        return
    from shifthunt.substrate import Subject
    subject = Subject()
    lex = re.compile(K.LEXICON_REGEX)
    inbank = re.compile(r"(?i)\b(" + "|".join(re.escape(a) for a, _ in K.ADV_PAIRS + K.PRE_PAIRS) + r")\b")
    rows = []
    for m in manifest:
        name, sign = m["name"], m["sign"]
        with np.load(PDIR / f"{name}.npz") as a:
            w, b, g, mu = a["w"], float(a["b"]), a["g"].astype(np.float64), a["mu"].astype(np.float64)
        ho = sets_for(m, salt, "ho")
        tx, y, fl = ho["rel"]
        R, _ = H.encode_sparse(subject, tx)
        rel, _ = measure_rel(probe_logit(R, w, b), fl, y, sign)
        tx, y, fl = ho["grid"]
        Rg, Fg = H.encode_sparse(subject, tx)
        grid_ho = E.Grid(probe_logit(Rg, w, b), Fg.toarray(), y, fl["hedge"][None], [sign], g, mu)
        with np.load(GDIR / f"{name}.npz") as zf:
            z = {k: zf[k] for k in zf.files}
        _, Frel, trel, flrel = load_set(z, "rel")
        shift = E.cue_shift(Frel.toarray(), flrel, trel, K.FEATS_H, "hedge")
        ref = E.reference_set(g, [shift], [sign])
        lg, Fo, to, flo = load_set(z, "grid")
        grid_in = E.Grid(lg, Fo.toarray(), to, flo["hedge"][None], [sign], g, mu)
        rr_in, rk_in = grid_in.score(ref)
        rr, rk = grid_ho.score(ref)
        row = {"probe": name, "rel_hedge_inbank": m["reliance"]["hedge"], "rel_hedge_ho": rel["hedge"],
               "max_other_ho": max(abs(v) for f, v in rel.items() if f != "hedge"),
               "E_S_in": float(grid_in.e_s[0]), "E_S_ho": float(grid_ho.e_s[0]),
               "E_T_in": float(grid_in.e_t), "E_T_ho": float(grid_ho.e_t),
               "share_in": float(grid_in.latent_share()[0]), "share_ho": float(grid_ho.latent_share()[0]),
               "ref_rem_in": float(rr_in[0]), "ref_kept_in": float(rk_in), "ref_rem_ho": float(rr[0]),
               "ref_kept_ho": float(rk),
               "ba_lexicon_ho": K.ba([lex.search(t) is not None for t in tx], fl["hedge"]),
               "ba_inbank_regex_ho": K.ba([inbank.search(t) is not None for t in tx], fl["hedge"])}
        rows.append(row)
        print(json.dumps(row), flush=True)
        del grid_ho, grid_in, Fg, Fo, z, Frel
    (RES / "heldout.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
