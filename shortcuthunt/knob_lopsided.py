"""Knob "lopsided": planted probes with two mains, one big and one small.

Training: probes.fit_probe on textgen.sample_texts with confound {c1: s1, c2: s2} and confound_noise
{c1: 1 - rho1, c2: 1 - rho2}; topic noise eps; same streams as probes.py ("train:{seed}",
"cues:{eval_seed}", "reliance:{eval_seed}", "topic:{eval_seed}"). Reliance is probes.measure_reliance on
the 384-note reliance set with both training signs applied.

Validity (adapted from the old repo's lopsided2; reliance is capped at 1.0 here):
  big main   rel[c1] in [BIG_MIN, BIG_MAX] = [0.70, 1.00]
  minor main rel[c2] in [MINOR_MIN, MINOR_MAX] = [0.30, 0.40]
  every other |rel[f]| <= probes.OTHER_MAX (0.15); topic readable (probes.TOPIC_ACC_MIN)

Artifact meta (probe json): the usual probes.Probe summary with cue = c1, sign = s1 (so 1-main readers
see the big main), plus mains = [c1, c2], signs = [s1, s2], rhos = [rho1, rho2], slot_class = "lopsided2".
Episode code reads the mains through mains_of(meta) (falls back to [cue], [sign]).
"""
import random
from dataclasses import asdict, dataclass

import numpy as np

from . import probes as P
from . import textgen as tg
from .ablation import gradient, probe_logit
from .episode_files import mains_of  # noqa: F401  (re-exported for the knob scripts)

BIG_MIN, BIG_MAX = 0.70, 1.00
MINOR_MIN, MINOR_MAX = 0.30, 0.40
CONCENTRATED = ("signoff", "bullet_list", "she_pronoun", "past_tense", "exclamation", "lowercase",
                "question_ending", "hashtag", "postscript")
LADDER1 = (1.0, 0.99, 0.98, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8)
LADDER2 = (0.99, 0.97, 0.95, 0.93, 0.91, 0.89, 0.87, 0.85, 0.83, 0.81, 0.79, 0.76, 0.73, 0.7, 0.66, 0.62, 0.58)
START2 = LADDER2.index(0.87)
EPS_CHOICES = (0.02, 0.05)  # eps .1 never gave a valid 1-main probe (Exp 4) and gave others > .15 here


@dataclass(frozen=True)
class Spec2:
    topics: tuple
    cues: tuple  # (big, minor)
    signs: tuple
    rhos: tuple
    eps: float
    seed: int
    eval_seed: int

    def __post_init__(self):
        assert len(self.cues) == 2 and len(set(self.cues)) == 2 and all(c in tg.FEATURES for c in self.cues)
        assert all(s in (1, -1) for s in self.signs) and all(0 <= r <= 1 for r in self.rhos)

    def summary(self):
        d = asdict(self)
        return {"kind": "planted", "topics": list(self.topics), "cue": self.cues[0], "sign": self.signs[0],
                "rho": self.rhos[0], "eps": self.eps, "seed": self.seed, "eval_seed": self.eval_seed,
                "mains": list(d["cues"]), "signs": list(d["signs"]), "rhos": list(d["rhos"]),
                "slot_class": "lopsided2"}


def training_set2(spec):
    conf = dict(zip(spec.cues, spec.signs))
    noise = {c: 1.0 - r for c, r in zip(spec.cues, spec.rhos)}
    return tg.sample_texts(random.Random(f"train:{spec.seed}"), list(spec.topics), P.N_TRAIN,
                           P.cue_strings(spec.eval_seed), conf, topic_noise=spec.eps, confound_noise=noise)


def flip_imbalance2(spec):
    """probes.flip_imbalance with both mains excluded (seed screen; CPU only, rho-independent)."""
    texts, y, flags = training_set2(spec)
    flipped = np.array([P._topic_of(t, spec.topics) for t in texts]) != y
    if not flipped.any():
        return 0.0
    s = 2 * y[flipped] - 1
    return max(abs(np.sum((2 * flags[f][flipped] - 1) * s)) for f in tg.FEATURES
               if f not in spec.cues) / np.sqrt(flipped.sum())


def reliance2(logits, flags, topic, cues, signs):
    r = P.measure_reliance(logits, flags, topic)
    for c, s in zip(cues, signs):
        r["reliance"][c] *= s
    return r


def validity2(rel, cues, topic_acc=None):
    big, minor = rel[cues[0]], rel[cues[1]]
    fails = []
    if big < BIG_MIN:
        fails.append("big_low")
    if big > BIG_MAX:
        fails.append("big_high")
    if minor < MINOR_MIN:
        fails.append("minor_low")
    if minor > MINOR_MAX:
        fails.append("minor_high")
    others = {f: abs(v) for f, v in rel.items() if f not in cues}
    worst = max(others, key=others.get)
    if others[worst] > P.OTHER_MAX:
        fails.append(f"other_high:{worst}")
    if topic_acc is not None and topic_acc < P.TOPIC_ACC_MIN:
        fails.append("topic_unreadable")
    return fails


def train2(lab, spec):
    """Fit one 2-main probe with a probes.Lab -> (Probe-like dict of arrays, summary dict)."""
    texts, y, _ = training_set2(spec)
    resid, mu = lab.enc.encode(texts)
    w, b, n_iter = P.fit_probe(resid, y)
    R, yr, flags = lab.reliance_data(spec.topics, spec.eval_seed)
    logits = probe_logit(R, w, b)
    rel = reliance2(logits, flags, yr, spec.cues, spec.signs)
    tacc = lab.topic_acc(spec.topics, spec.eval_seed)
    fails = validity2(rel["reliance"], spec.cues, tacc)
    g = gradient(lab.enc.W_dec, w)
    summ = spec.summary() | {
        "b": b, "reliance": rel["reliance"], "coef": rel["coef"], "topic_coef": rel["topic_coef"], "r2": rel["r2"],
        "topic_acc": tacc, "probe_topic_acc": float(((logits > 0) == yr).mean()),
        "train_acc": float(((probe_logit(resid, w, b) > 0) == y).mean()), "n_iter": n_iter,
        "g_top5_share": P.g_top_share(g), "failures": fails}
    return {"w": w, "b": np.float64(b), "g": g, "mu": mu}, summ


def next_state(i1, i2, rel, cues, fails):
    """Controller step on the two rho ladders -> (i1, i2) or None (redraw)."""
    big, minor = rel[cues[0]], rel[cues[1]]
    d1 = 0
    if big > BIG_MAX:
        d1 = 1 if big < 1.25 else 2 if big < 1.8 else 3
    elif big < BIG_MIN:
        d1 = -1 if big > 0.5 else -2
    d2 = 0
    if minor > MINOR_MAX:
        d2 = 1 if minor < 0.5 else 2 if minor < 0.7 else 3
    elif minor < MINOR_MIN:
        d2 = -1 if minor > 0.2 else -2
    if d1 == 0 and d2 == 0:  # windows fine, others too high: lower the big main a step if it has room
        if any(f.startswith("other_high") for f in fails) and big >= BIG_MIN + 0.1:
            d1 = 1
        else:
            return None
    j1 = min(max(i1 + d1, 0), len(LADDER1) - 1)
    j2 = min(max(i2 + d2, 0), len(LADDER2) - 1)
    if (j1, j2) == (i1, i2):
        return None
    return j1, j2
