"""Knob semantic, Exp S2-S4 measure (CPU): reliance, removability and labeling-submission baselines.

    flock /tmp/shifthunt-gpu.lock python scripts/knob_semantic_measure.py [--tag knob_semantic]

Needs scripts/knob_semantic_build.py output. Per probe:
  S2 reliance on the 384-note reliance set (hedge + 15 features + topic vary independently), validity.
  S3 hidden grid (256, topic x hedge): E_S/E_T, reference (top-16 by sign*g*shift, shift = lstsq coefficient on
     the hedge flag over the reliance set's pooled latents) removal/kept, tau, latent-visible share,
     greedy oracle margin (64 candidates), removal of the top-32/64 ranked latents.
  S4 labeling (64 notes, topic x hedge balanced; also on the 256 grid notes for a less noisy estimate). Every
     labeler outputs a score; labels = score above its within-topic median (32/32 split). BA either polarity.
     a1 cue-blind: latent-visible logit F @ g, topic-residualized (no cue knowledge, no true logits)
     a1t same with TRUE logits (upper bound; the real tools give only 8 true logits per episode)
     a2 cue-blind top-16: latents ranked by g_i * cov(F_i, a1 score) on the notes themselves, score = sum g_i F_i
     a3 unsupervised: first PC of topic-residualized F (no probe, no cue)
     b  true latents: reference set, score = sum g_i F_i
     b2 hedge detector: top-16 by |shift|, score = F[:, top] @ shift[top] (ignores the probe)
     c  generic hedge lexicon regex (knob_semantic.LEXICON_REGEX)
Writes results/knobs/semantic/measure_<tag>.json (numbers only, no latent ids, no texts).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import effects as E  # noqa: E402
from shifthunt import knob_semantic as K  # noqa: E402
from shifthunt.substrate import D_SAE  # noqa: E402

RES = ROOT / "results" / "knobs" / "semantic"


def load_set(z, p):
    n = len(z[f"{p}_logits"])
    F = sp.csr_matrix((z[f"{p}_data"], z[f"{p}_indices"], z[f"{p}_indptr"]), shape=(n, D_SAE))
    fl = {f: z[f"{p}_flags"][i].astype(np.int64) for i, f in enumerate(K.FEATS_H)}
    return z[f"{p}_logits"].astype(np.float64), F, z[f"{p}_topic"].astype(np.int64), fl


def resid_topic(x, topic):
    x = np.asarray(x, np.float64).copy()
    for t in (0, 1):
        x[topic == t] -= x[topic == t].mean(0)
    return x


def labels_from(score, topic):
    lab = np.zeros(len(score), bool)
    for t in (0, 1):
        m = topic == t
        lab[m] = score[m] > np.median(score[m])
    return lab


def labelers(logits, F, topic, hedge, g, shift, ref, texts):
    Fd = F.toarray().astype(np.float64)
    out = {}
    v = Fd @ g
    a1 = resid_topic(v, topic)
    out["a1_cueblind_latent_logit"] = K.ba(labels_from(a1, topic), hedge)
    out["a1t_true_logit"] = K.ba(labels_from(resid_topic(logits, topic), topic), hedge)
    Fr = resid_topic(Fd, topic)
    cov = Fr.T @ (a1 - a1.mean()) / len(a1)
    top = np.argsort(-(g * cov), kind="stable")[:16]
    out["a2_cueblind_top16"] = K.ba(labels_from(Fd[:, top] @ g[top], topic), hedge)
    out["a2_overlap_with_ref"] = len(set(top.tolist()) & set(ref.tolist()))
    u, s, vt = np.linalg.svd(Fr - Fr.mean(0), full_matrices=False)
    out["a3_unsup_pc1"] = K.ba(labels_from(u[:, 0], topic), hedge)
    out["a3_best_of_pc1_5"] = max(K.ba(labels_from(u[:, i], topic), hedge) for i in range(5))
    out["b_ref_latents"] = K.ba(labels_from(Fd[:, ref] @ g[ref], topic), hedge)
    det = np.argsort(-np.abs(shift), kind="stable")[:16]
    out["b2_hedge_detector16"] = K.ba(labels_from(Fd[:, det] @ shift[det], topic), hedge)
    lex = re.compile(K.LEXICON_REGEX)
    out["c_lexicon_regex"] = K.ba([lex.search(t) is not None for t in texts], hedge)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="knob_semantic")
    args = ap.parse_args()
    pdir = ROOT / "artifacts" / "probes" / args.tag
    gdir = ROOT / "artifacts" / "grader" / args.tag
    rows = []
    for meta in json.loads((pdir / "manifest.json").read_text()):
        name, sign = meta["name"], meta["sign"]
        with np.load(pdir / f"{name}.npz") as a:
            g, mu = a["g"].astype(np.float64), a["mu"].astype(np.float64)
        with np.load(gdir / f"{name}.npz") as zf:
            z = {k: zf[k] for k in zf.files}
        texts = json.loads((gdir / f"{name}_texts.json").read_text())
        row = {"probe": name, "topics": meta["topics"], "sign": sign, "eps": meta["eps"], "rho": meta["rho"],
               "rel_hedge": meta["reliance"]["hedge"],
               "max_other": max(abs(v) for f, v in meta["reliance"].items() if f != "hedge"),
               "worst_other": max((f for f in meta["reliance"] if f != "hedge"),
                                  key=lambda f: abs(meta["reliance"][f])),
               "failures": meta["failures"], "topic_acc": meta["topic_acc"]}
        _, Frel, trel, flrel = load_set(z, "rel")
        shift = E.cue_shift(Frel.toarray(), flrel, trel, K.FEATS_H, "hedge")
        del Frel
        ref = E.reference_set(g, [shift], [sign])
        lg, Fg, tg_, flg = load_set(z, "grid")
        state = flg["hedge"]
        grid = E.Grid(lg, Fg.toarray(), tg_, state[None], [sign], g, mu)
        row["grid_E_S"], row["grid_E_T"] = float(grid.e_s[0]), float(grid.e_t)
        row["grid_rel"] = row["grid_E_S"] / row["grid_E_T"]
        row["latent_share"] = float(grid.latent_share()[0])
        rr, rk = grid.score(ref)
        tau = E.tau_from(rr)
        row["ref_removal"], row["ref_kept"], row["tau"] = float(rr[0]), float(rk), float(tau[0])
        for k in (32, 64):
            r_, k_ = grid.score(E.ranked(g, shift, sign, k))
            row[f"top{k}_removal"], row[f"top{k}_kept"] = float(r_[0]), float(k_)
        cand = E.ranked(g, shift, sign, E.ORACLE_CANDIDATES)
        orc = E.greedy_oracle(grid, cand, tau)
        row["oracle_margin"], row["oracle_k"] = float(orc["margin"]), len(orc["ids"])
        row["oracle_removal"], row["oracle_kept"] = float(orc["removal"][0]), float(orc["kept"])
        sc = sign * g * shift
        row["gshift_top16_mass"] = float(np.sort(sc)[::-1][:16].sum() / sc[sc > 0].sum())
        row["valid_grader"] = bool(rr[0] >= E.REF_REMOVAL_MIN and rk >= E.KEEP_MIN
                                   and orc["margin"] >= E.ORACLE_MARGIN_MIN)
        row["label64"] = labelers(*load_set(z, "label")[:3], load_set(z, "label")[3]["hedge"], g, shift, ref,
                                  texts["label"])
        row["label256_grid"] = labelers(lg, Fg, tg_, state, g, shift, ref, texts["grid"])
        del grid, Fg, z
        rows.append(row)
        print(json.dumps(row), flush=True)
    (RES / f"measure_{args.tag}.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
