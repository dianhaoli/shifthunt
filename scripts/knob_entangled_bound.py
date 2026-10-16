"""Knob entangled: kept after ablating the top-16/64 latents by topic IE (upper bound on how much topic 16 latents can remove).

    flock /tmp/shifthunt-gpu.lock python scripts/knob_entangled_bound.py knob_entangled_so knob_entangled_so2
"""
import sys, json, gc
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from shifthunt import episodes as EP, effects as E, textgen as tg, knob_entangled as K
K.install()
for tag in sys.argv[1:]:
    man = json.load(open(EP.PROBES / tag / 'manifest.json'))
    for m in man:
        if m['kind'] != 'planted': continue
        a = EP.load(tag, m['name']); grid = a.grid()
        F = EP.csr(a.z, 'rel').toarray()
        X = np.column_stack([a.flags('rel')[f] for f in tg.FEATURES] + [a.z['rel_topic'], np.ones(len(F))]).astype(float)
        coef, *_ = np.linalg.lstsq(X, F, rcond=None)
        tsh = coef[len(tg.FEATURES)]
        g = a.arr['g']
        out = []
        for k in (16, 64):
            S = np.argsort(-(g * tsh))[:k]
            out.append(grid.score(S)[1])
        cue = m['cue']; csh = coef[tg.FEATURES.index(cue)]
        ref = E.ranked(g, csh, m['sign'], 16)
        tie = g * tsh
        print(f"{a.key} {cue} kept after top16 topic-IE {out[0]:.2f}, top64 {out[1]:.2f}; ref latents topic-IE share of E_T_lat {tie[ref].sum()/tie.sum():.2f}")
        del a, grid, F; gc.collect()
