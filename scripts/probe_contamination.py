"""Exp 2b: is other-cue reliance explained by the training sample's topic-flipped notes?

For each grid probe with eps > 0, take its worst other cue f (largest |reliance|). In the training
set, compare f's association with the label among the topic-flipped notes (topic != label) and
among the rest. If the probe memorizes flipped notes through whatever cues they share, the sign of
reliance[f] should match f's label association among the *flipped* notes. CPU only.

    python scripts/probe_contamination.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import probes as P  # noqa: E402

rows = [json.loads(line) for line in open(ROOT / "results/probes/grid.jsonl")]
out = {"match_flipped": [], "match_clean": [], "big": []}
for r in rows:
    if r["eps"] == 0:
        continue
    spec = P.spec_from_meta(r)
    texts, y, flags = P.training_set(spec)
    # topic of each note: recover from the text via the topic phrases is fiddly; regenerate instead:
    # sample_texts flips topic iff u_topic < eps, which the flags do not record, so detect by phrase.
    topic_words = {t: set(w for k in ("act", "item", "where") for p in P.tg.TOPICS[t][k] for w in [p]) for t in spec.topics}
    hit = np.array([[any(p.lower() in tx.lower() for p in topic_words[t]) for t in spec.topics] for tx in texts])
    assert (hit.sum(1) == 1).all(), "topic phrase match is ambiguous"
    topic = hit[:, 1].astype(int)
    assert abs((topic != y).mean() - r["eps"]) < 0.08
    flipped = topic != y
    others = {f: v for f, v in r["reliance"].items() if f != r["cue"]}
    f = max(others, key=lambda k: abs(others[k]))
    x = flags[f]
    s = 2 * y - 1  # +1 label 1, -1 label 0
    assoc_flip = float(np.mean((2 * x[flipped] - 1) * s[flipped])) if flipped.any() else 0.0
    assoc_clean = float(np.mean((2 * x[~flipped] - 1) * s[~flipped]))
    big = abs(others[f]) > P.OTHER_MAX
    out["big"].append(big)
    out["match_flipped"].append(np.sign(assoc_flip) == np.sign(others[f]))
    out["match_clean"].append(np.sign(assoc_clean) == np.sign(others[f]))
    out.setdefault("rows", []).append((r["eps"], f, round(others[f], 3), int(flipped.sum()), round(assoc_flip, 2), round(assoc_clean, 3)))
big = np.array(out["big"])
mf, mc = np.array(out["match_flipped"]), np.array(out["match_clean"])
print(f"n={len(big)} probes with eps>0; worst other > 0.15 in {big.sum()}")
print(f"sign(worst other reliance) == sign(label association among flipped notes): all {mf.mean():.2f}, when >0.15 {mf[big].mean():.2f}")
print(f"sign(worst other reliance) == sign(label association among clean notes):   all {mc.mean():.2f}, when >0.15 {mc[big].mean():.2f}")
af = np.array([abs(t[4]) for t in out["rows"]]); ac = np.array([abs(t[5]) for t in out["rows"]])
print(f"|association| of worst other cue: flipped notes median {np.median(af):.2f}, clean notes median {np.median(ac):.3f}")
print("examples (eps, cue, reliance, n_flipped, assoc_flipped, assoc_clean):", out["rows"][:8])
