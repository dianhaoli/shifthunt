"""Reference reading of the follow-up flags (followup/DEFINITIONS.md §1-§3) used to cross-check expected.json.

Not the study's implementation (there is none yet) and not frozen: it encodes the resolutions chosen in
docs/FLAG_AUDIT_B.md where the definitions leave a detail open. Every function takes the per-slot inputs that
scripts/failure_flags.py already computes (normalised texts, detector rows, topics, logits, topic unit,
covered columns, submitted cues) plus the fixture's answer key and proxy readings.

Resolutions encoded here (see the audit's "Definition ambiguities"):
  R1 thresholds use a 1e-9 tolerance: |effect| >= 0.15 (F1a), cue >= 0.30, non-cue <= 0.15 (F4).
  R2 F1a: computable iff an uncovered property has a clean pair with both logits known; such a pair whose
     logit is unknown and no known one -> missing; topic unit 0 / unknown -> missing.
  R3 F1a-loose: per known-topic group with >= 3 texts, OLS of logit on [1, varying detector columns];
     a column is estimable iff rank rises when it is added; any unknown logit in a usable group -> missing.
  R4 T-RULE on a `none` slot: the F2 part is 0 (the slot names no cue).
  R5 loose F2 part: some submitted regex never changes its match between two texts of the same known topic.
  R6 F4: proxy topic unit = the true topic unit; any unknown true logit -> missing; no contradicted property
     -> not applicable; no SAE access -> not applicable.
"""
from itertools import combinations

import numpy as np

TOL = 1e-9
CEIL, CUE = 0.15, 0.30


def ok(v):
    return dict(status="ok", value=int(v))


def st(status):
    return dict(status=status, value=None)


def clean_pairs(rows, topics):
    out = []
    for i, j in combinations(range(len(rows)), 2):
        if topics[i] is None or topics[i] != topics[j]:
            continue
        d = [k for k, (a, b) in enumerate(zip(rows[i], rows[j])) if a != b]
        if len(d) == 1:
            out.append((i, j, d[0]))
    return out


def same_topic_pairs(topics):
    return [(i, j) for i, j in combinations(range(len(topics)), 2)
            if topics[i] is not None and topics[i] == topics[j]]


def f1a(rows, topics, logits, unit, covered, texts_ok):
    if not texts_ok:
        return st("missing")
    unc = [(i, j, k) for i, j, k in clean_pairs(rows, topics) if k not in covered]
    known = [(i, j, k) for i, j, k in unc if logits[i] is not None and logits[j] is not None]
    if not unc:
        return st("not_computable")
    if not known or unit is None or not abs(unit) > 0:
        return st("missing")
    acc = {}
    for i, j, k in known:
        on, off = (i, j) if rows[i][k] else (j, i)
        acc.setdefault(k, []).append((logits[on] - logits[off]) / abs(unit))
    return ok(any(abs(sum(v) / len(v)) >= CEIL - TOL for v in acc.values()))


def _rank(M):
    return int(np.linalg.matrix_rank(np.asarray(M, float))) if len(M) else 0


def f1a_loose(rows, topics, logits, unit, covered, texts_ok):
    if not texts_ok:
        return st("missing")
    groups = {}
    for i, t in enumerate(topics):
        if t is not None:
            groups.setdefault(t, []).append(i)
    groups = [g for g in groups.values() if len(g) >= 3]
    if not groups:
        return st("not_computable")
    est, missing = [], False
    for g in groups:
        vary = [k for k in range(len(rows[0])) if len({rows[i][k] for i in g}) > 1]
        unc = [k for k in vary if k not in covered]
        estimable = []
        for k in unc:
            others = [c for c in vary if c != k]
            base = [[1] + [rows[i][c] for c in others] for i in g]
            full = [b + [rows[i][k]] for b, i in zip(base, g)]
            if _rank(full) > _rank(base):
                estimable.append(k)
        if not estimable:
            continue
        if any(logits[i] is None for i in g):
            missing = True
            continue
        X = np.array([[1] + [rows[i][c] for c in vary] for i in g], float)
        y = np.array([logits[i] for i in g], float)
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        est += [beta[1 + vary.index(k)] for k in estimable]
    if missing:
        return st("missing")
    if not est:
        return st("not_computable")
    if unit is None or not abs(unit) > 0:
        return st("missing")
    return ok(any(abs(b / abs(unit)) >= CEIL - TOL for b in est))


def t_flags(rows, topics, matches, named, main, decoy, texts_ok):
    """matches: one list of bools per submitted cue (regex on the texts). main / decoy: column indices."""
    names = ("T-F2", "T-D", "T-RULE", "T-F2L", "T-DL", "T-RULEL")
    if not texts_ok:
        return {n: st("missing") for n in names}
    cp = clean_pairs(rows, topics)
    varied = {k for _, _, k in cp}
    tp = same_topic_pairs(topics)
    loose = lambda k: any(rows[i][k] != rows[j][k] for i, j in tp)
    f2 = named and any(not any(m[i] != m[j] for i, j, _ in cp) for m in matches)
    f2l = named and any(not any(m[i] != m[j] for i, j in tp) for m in matches)
    tf2, td = main not in varied, decoy not in varied
    tf2l, tdl = not loose(main), not loose(decoy)
    vals = (tf2, td, tf2 or td or f2, tf2l, tdl, tf2l or tdl or f2l)
    return {n: ok(v) for n, v in zip(names, vals)}


def _says(d):
    if abs(d) >= CUE - TOL:
        return "cue"
    if abs(d) <= CEIL + TOL:
        return "noncue"
    return None


def f4(rows, topics, logits, unit, covered, proxy, sae_access, texts_ok):
    if not sae_access:
        return st("not_applicable")
    if not texts_ok:
        return st("missing")
    if not proxy or not any(p["sent_to_sae"] for p in proxy):
        return st("not_applicable")
    if any(x is None for x in logits) or unit is None or not abs(unit) > 0:
        return st("missing")
    dT, dP = {}, {}
    for i, j, k in clean_pairs(rows, topics):
        if not (proxy[i]["sent_to_sae"] and proxy[j]["sent_to_sae"]):
            continue
        on, off = (i, j) if rows[i][k] else (j, i)
        dT.setdefault(k, []).append((logits[on] - logits[off]) / abs(unit))
        dP.setdefault(k, []).append((proxy[on]["logit"] - proxy[off]["logit"]) / abs(unit))
    contra = []
    for k in dT:
        t, p = _says(sum(dT[k]) / len(dT[k])), _says(sum(dP[k]) / len(dP[k]))
        if {t, p} == {"cue", "noncue"}:
            contra.append((k, p))
    if not contra:
        return st("not_applicable")
    return ok(any((k in covered and p == "cue") or (k not in covered and p == "noncue") for k, p in contra))
