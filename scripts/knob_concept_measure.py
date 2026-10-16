"""Knob concept, Exp C3 (GPU encode + CPU): held-out wordings vs shown wordings for each valid concept probe.

    flock /tmp/shifthunt-gpu.lock python scripts/knob_concept_run.py scripts/knob_concept_measure.py

Per probe in artifacts/probes/knob_concept:
 (a) reliance on the 384-note reliance set (same stream) rendered with shown vs held-out forms;
 (b) a fresh 256-note grid (stream knob_concept_grid:{salt}:{eval_seed}, topic x concept balanced, other features
     coin flips), rendered with held-out forms and (same notes) shown forms; regex BA (best polarity) on it for:
     hand v1, hand v2, `literal` = union of the distinct concept sentences visible in a 128-note sample (the first
     128 training notes, shown forms), `salient` = the 10 words with the largest within-topic difference of
     document frequency (concept-on minus concept-off) in that sample;
 (c) 16-latent reference (top-16 by sign * g . mean latent shift over 32 paired concept flips, shown forms)
     scored (removal, kept) on the held-out grid and on the shown grid; plus the same from held-out flips.
Writes results/knobs/concept/measure.jsonl (numbers and the derived regexes only).
"""
import gc
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
from shifthunt import effects as E  # noqa: E402
from shifthunt import hidden as H  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as K  # noqa: E402  (knob_concept, installed by knob_concept_run.py)
from shifthunt.ablation import probe_logit  # noqa: E402

assert "concept" in K.FEATURES, "run through scripts/knob_concept_run.py"
PDIR = ROOT / "artifacts" / "probes" / "knob_concept"
RES = ROOT / "results" / "knobs" / "concept"
PRON = {"he": "(he|she)", "his": "(his|her)", "him": "(him|her)", "himself": "(himself|herself)"}


def ba(rx, texts, truth):
    r = re.compile(rx)
    hit = np.array([bool(r.search(t)) for t in texts])
    truth = np.asarray(truth, bool)
    b = 0.5 * (hit[truth].mean() + (~hit[~truth]).mean())
    return float(max(b, 1 - b)), float(hit[truth].mean()), float(hit[~truth].mean())


def literal_regex(texts, flags):
    seen = []
    for t, c in zip(texts, flags):
        low = t.lower()
        for s in K.forms("shown"):
            if c and (s.lower() in low or K.sub_map(K._PRON_RE, K._PRON, s).lower() in low) and s not in seen:
                seen.append(s)
    alts = []
    for s in seen:
        toks = re.split(r"(\W+)", s)
        alts.append("".join(PRON.get(x.lower(), re.escape(x)) for x in toks))
    return "(?i)(" + "|".join(alts) + ")", len(seen)


def salient_regex(texts, flags, y, k=10):
    words = [set(re.findall(r"[a-z']+", t.lower())) for t in texts]
    score, off_rate = Counter(), Counter()
    for t in (0, 1):
        on = [w for w, c, yy in zip(words, flags, y) if c and yy == t]
        off = [w for w, c, yy in zip(words, flags, y) if not c and yy == t]
        if not on or not off:
            continue
        don, doff = Counter(x for w in on for x in w), Counter(x for w in off for x in w)
        for x in set(don) | set(doff):
            score[x] += 0.5 * (don[x] / len(on) - doff[x] / len(off))
            off_rate[x] = max(off_rate[x], doff[x] / len(off))
    # over-represented = frequent with the concept and rare (<= 5% of notes) without it (drops function words)
    top = [w for w, _ in score.most_common() if off_rate[w] <= 0.05][:k]
    return r"(?i)\b(" + "|".join(map(re.escape, top)) + r")\b", top


def encode(subject, texts):
    R, F = H.encode_sparse(subject, texts)
    return R, F.toarray().astype(np.float32)


def flip_shift(subject, topics, es, bank):
    K.use_forms(bank)
    rng = random.Random(f"scan:{es}")
    base = [(i % 2, {f: int(rng.random() < 0.5) for f in K.FEATURES}, rng.getrandbits(32)) for i in range(H.N_SCAN)]
    off = [K.render(topics[t], lv | {"concept": 0}, None, s)[0] for t, lv, s in base]
    on = [K.render(topics[t], lv | {"concept": 1}, None, s)[0] for t, lv, s in base]
    K.use_forms("shown")
    _, F = encode(subject, off + on)
    return (F[H.N_SCAN:].astype(np.float64) - F[:H.N_SCAN]).mean(0)


def main():
    from shifthunt import knob_entangled
    from shifthunt.substrate import Subject
    knob_entangled.use_lean_loader()  # stock loader peaks at 9.7 GB RSS (knobs/entangled LOG); lean ~1 GB anon
    subject = Subject()
    salt = H.load_salt(ROOT / "artifacts" / "grader")
    manifest = json.loads((PDIR / "manifest.json").read_text())
    out = open(RES / "measure.jsonl", "w")
    for m in manifest:
        name, topics, es, sign = m["name"], list(m["topics"]), m["eval_seed"], m["sign"]
        with np.load(PDIR / f"{name}.npz") as a:
            w, b, g, mu = a["w"], float(a["b"]), a["g"].astype(np.float64), a["mu"].astype(np.float64)
        row = {"name": name, "topics": topics, "sign": sign, "rho": m["rho"], "eps": m["eps"],
               "build_reliance": m["reliance"]["concept"]}
        # (a) reliance, shown vs held-out
        for bank in ("shown", "heldout"):
            K.use_forms(bank)
            tx, y, fl = P.reliance_set(topics, es)
            R, _ = H.encode_sparse(subject, tx)
            rel = P.measure_reliance(probe_logit(R, w, b), fl, y, "concept", sign)["reliance"]
            row[f"rel_{bank}"] = rel["concept"]
            row[f"rel_other_max_{bank}"] = max(abs(v) for f, v in rel.items() if f != "concept")
        # sample (first 128 training notes, shown forms) -> literal and salient regexes
        K.use_forms("shown")
        spec = P.Spec("planted", tuple(topics), "concept", sign, m["rho"], m["eps"], m["seed"], es)
        stx, sy, sfl = P.training_set(spec)
        stx, sy, sc = stx[:128], sy[:128], sfl["concept"][:128]
        lit, n_lit = literal_regex(stx, sc)
        # salient words: (i) confounded sample (concept == label, as in episodes): plain on-vs-off contrast;
        # (ii) unconfounded 128-note shown-form sample (topic x concept balanced), within-topic contrast
        sal_conf, top_conf = salient_regex(stx, sc, np.zeros_like(sy))
        utx, uy, ufl = K.sample_grid(random.Random(f"concept_sample:{es}"), topics, 128, P.cue_strings(es),
                                     mains=["concept"])
        sal, top = salient_regex(utx, ufl["concept"], uy)
        row.update(n_literal_forms=n_lit, salient_words=top, salient_conf_words=top_conf,
                   sample_concept_rate=float(sc.mean()))
        # (b) grids
        grids = {}
        for bank in ("heldout", "shown"):
            K.use_forms(bank)
            gtx, gy, gfl = K.sample_grid(random.Random(f"knob_concept_grid:{salt}:{es}"), topics, 256,
                                         P.cue_strings(es), mains=["concept"])
            R, F = encode(subject, gtx)
            lg = probe_logit(R, w, b)
            e_s, e_t = E.effects(lg, gy, gfl["concept"][None], [sign])
            row[f"E_S_{bank}"], row[f"E_T_{bank}"] = float(e_s[0]), float(e_t)
            if e_s[0] > 0 and e_t > 0:
                grids[bank] = E.Grid(lg, F, gy, gfl["concept"][None], [sign], g, mu)
                row[f"latent_share_{bank}"] = float(grids[bank].latent_share()[0])
            for rname, rx in (("v1", K.CONCEPT_REGEX), ("v2", K.CONCEPT_REGEX_V2), ("literal", lit),
                              ("salient", sal), ("salient_conf", sal_conf)):
                row[f"ba_{rname}_{bank}"], row[f"tpr_{rname}_{bank}"], row[f"fpr_{rname}_{bank}"] = \
                    ba(rx, gtx, gfl["concept"])
        K.use_forms("shown")
        # (c) reference removal: latents from shown flips (and held-out flips), scored on both grids
        for src in ("shown", "heldout"):
            ref = E.ranked(g, flip_shift(subject, topics, es, src), sign, E.REF_K)
            row[f"ref_{src}_ids"] = [int(i) for i in ref]
            for bank in [k for k in ("heldout", "shown") if k in grids]:
                rem, kept = grids[bank].score(ref)
                row[f"ref_{src}_removal_on_{bank}"] = float(rem[0])
                row[f"ref_{src}_kept_on_{bank}"] = float(kept)
        row["ref_overlap_shown_heldout"] = len(set(row["ref_shown_ids"]) & set(row["ref_heldout_ids"]))
        row["literal_regex_len"] = len(lit)
        row["salient_regex"] = sal
        out.write(json.dumps(row) + "\n")
        out.flush()
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()
               if not k.endswith("_ids") and k != "salient_regex"}, flush=True)
        del grids
        gc.collect()


if __name__ == "__main__":
    main()
