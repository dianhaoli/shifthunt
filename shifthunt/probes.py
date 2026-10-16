"""Planted and null topic probes, and the reliance measurement that defines what a probe uses.

A probe is logistic regression on the pooled layer-12 residual, fit on standardized inputs and
folded back so that logit = resid @ w + b in raw residual units.

Training data comes from textgen.sample_texts (labels alternate, y = i % 2):
  * planted: one cue tracks the label with agreement rho (confound_noise = 1 - rho), sign +1 (cue on
    when y == 1) or -1; the topic disagrees with the label with probability eps.
  * null: no cue is confounded; the topic disagrees with the label with probability eps.

Reliance (the definition everything else uses): render N_RELIANCE fresh notes for the probe's topic
pair with every cue a fair coin (sample_grid, no mains), least-squares fit the probe logit on
[15 cue flags, topic, 1], and report reliance[f] = coef[f] * sign_f / |coef[topic]|, where sign_f is
the training sign for the planted cue and +1 for every other cue.

Seeds. A probe instance is (topics, cue, sign, cue strings, eval_seed); its training sample has its
own seed. Every random stream is random.Random(<tagged string>), which Python seeds through sha512,
so streams are independent of each other and of PYTHONHASHSEED:
  "cues:{eval_seed}"      per-probe cue strings (closing, names, hashtag word)
  "reliance:{eval_seed}"  the N_RELIANCE unconfounded notes
  "topic:{eval_seed}"     N_TRAIN unconfounded notes for the topic-readability probe
  "train:{seed}"          the biased training sample
Because sample_texts consumes the same randomness whatever the confound config, changing rho or eps
with a fixed seed only changes the notes whose cue or topic flips.

Encoding always uses BATCH_SIZE (bf16 results depend on batch shape, by up to ~0.1 logit), and every
set is a multiple of it, so a given set always encodes in the same batches.
"""
import hashlib
import json
import os
import random
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from . import textgen as tg
from .ablation import gradient, probe_logit
from .substrate import MAX_CONTENT_TOKENS

BATCH_SIZE = 16
N_TRAIN = 256
N_RELIANCE = 384
C = 0.05
MAX_ITER = 3000

EPS_CHOICES = (0.02, 0.05, 0.1)
# negative_sentiment makes notes self-contradictory, so it is never planted.
PLANTABLE = tuple(f for f in tg.FEATURES if f != "negative_sentiment")

PLANTED_MIN = 0.30  # reliance on the planted cue
OTHER_MAX = 0.15  # |reliance| on every other cue (every cue, for nulls)
RATIO_MIN = 1.25  # planted >= RATIO_MIN * max other |reliance|
TOPIC_ACC_MIN = 0.95  # unconfounded probe, held-out unconfounded notes

RHO_LADDER = (1.0, 0.99, 0.98, 0.97, 0.96, 0.95, 0.93, 0.9)


# ---------------------------------------------------------------- fitting

def fit_probe(resid, y):
    """Standardize, fit LogisticRegression(C, max_iter), fold the scaling back.

    Returns (w [d] float64, b float, n_iter). logit = resid @ w + b equals the sklearn decision
    function on the standardized inputs. Raises if lbfgs did not converge.
    """
    X = np.asarray(resid, np.float64)
    y = np.asarray(y)
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("labels must contain both 0 and 1")
    scaler = StandardScaler().fit(X)
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # ConvergenceWarning -> exception, never a silent probe
        clf = LogisticRegression(C=C, max_iter=MAX_ITER).fit(scaler.transform(X), y)
    w = clf.coef_[0] / scaler.scale_
    b = float(clf.intercept_[0] - scaler.mean_ @ w)
    return w, b, int(clf.n_iter_[0])


# ---------------------------------------------------------------- encoding with a batch cache

class CachedEncoder:
    """Subject.encode in fixed BATCH_SIZE batches, cached per batch.

    The cache key is the exact tuple of texts in a batch, so a hit returns bitwise what a fresh
    encode of that batch gives (same batch shape, same order). Per batch it keeps the pooled
    residuals and the *sum* of pooled latents (all mu needs), not per-text latents.
    cache_dir (optional) persists batches across processes; it is keyed additionally by
    MAX_CONTENT_TOKENS and BATCH_SIZE, so delete it if the substrate itself changes.
    """

    def __init__(self, subject, cache_dir=None):
        self.subject = subject
        self.W_dec = subject.sae.W_dec
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._mem = {}
        self.n_encoded = 0  # texts actually run through the model
        self.n_cached = 0

    @staticmethod
    def _key(batch):
        h = hashlib.sha256(f"{MAX_CONTENT_TOKENS}|{BATCH_SIZE}".encode())
        for t in batch:
            h.update(b"\x00" + t.encode())
        return h.hexdigest()

    def _batch(self, batch):
        key = self._key(batch)
        if key in self._mem:
            self.n_cached += len(batch)
            return self._mem[key]
        path = self.cache_dir / f"{key}.npz" if self.cache_dir else None
        if path is not None and path.exists():
            with np.load(path) as z:
                out = (z["resid"], z["latent_sum"])
            self.n_cached += len(batch)
        else:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                enc = self.subject.encode(batch, batch_size=BATCH_SIZE)
            if any("OOM" in str(c.message) for c in caught):
                raise RuntimeError("encode fell back to a smaller batch; results would not match")
            out = (enc.resid, enc.latents.astype(np.float64).sum(0))
            self.n_encoded += len(batch)
            if path is not None:
                tmp = path.with_suffix(f".{os.getpid()}.tmp.npz")
                np.savez(tmp, resid=out[0], latent_sum=out[1])
                os.replace(tmp, path)
        self._mem[key] = out
        return out

    def encode(self, texts):
        """-> (resid [n, d] float32, mean pooled latents over the texts [D_SAE] float64)."""
        texts = list(texts)
        if not texts or len(texts) % BATCH_SIZE:
            raise ValueError(f"need a non-empty multiple of {BATCH_SIZE} texts, got {len(texts)}")
        parts = [self._batch(tuple(texts[i:i + BATCH_SIZE])) for i in range(0, len(texts), BATCH_SIZE)]
        resid = np.concatenate([p[0] for p in parts])
        mu = np.sum([p[1] for p in parts], axis=0) / len(texts)
        return resid, mu


# ---------------------------------------------------------------- data

@dataclass(frozen=True)
class Spec:
    """Everything that determines a probe. cue/sign/rho are None for nulls."""
    kind: str  # "planted" | "null"
    topics: tuple
    cue: str | None
    sign: int | None
    rho: float | None
    eps: float
    seed: int  # training sample
    eval_seed: int  # cue strings, reliance set, topic-readability set
    parent_rate: float | None = None  # nested cue only: P(parent | y) in training for both labels (None = off)

    def __post_init__(self):
        if self.kind == "planted":
            assert self.cue in tg.FEATURES and self.sign in (1, -1) and 0 <= self.rho <= 1
        elif self.kind == "null":
            assert self.cue is None and self.sign is None and self.rho is None
        else:
            raise ValueError(self.kind)
        assert 0 <= self.eps <= 1
        if self.parent_rate is not None:
            assert self.kind == "planted" and 0 < self.parent_rate <= 1


def spec_from_meta(m, **override):
    """Spec of a saved probe meta (or results jsonl row), including parent_rate when the probe has one.
    Rebuilding a Spec field by field without parent_rate silently retrains a nested-cue probe unbalanced."""
    keys = ("kind", "topics", "cue", "sign", "rho", "eps", "seed", "eval_seed")
    kw = {k: m[k] for k in keys} | {"topics": tuple(m["topics"]), "parent_rate": m.get("parent_rate")}
    return Spec(**(kw | override))


def cue_strings(eval_seed):
    return tg.make_cues(random.Random(f"cues:{eval_seed}"))


def training_set(spec):
    confound = {spec.cue: spec.sign} if spec.kind == "planted" else {}
    noise = {spec.cue: 1.0 - spec.rho} if spec.kind == "planted" else None
    extra = {} if spec.parent_rate is None else {"balance_parents": spec.parent_rate}  # free text only
    return tg.sample_texts(random.Random(f"train:{spec.seed}"), list(spec.topics), N_TRAIN,
                           cue_strings(spec.eval_seed), confound, topic_noise=spec.eps,
                           confound_noise=noise, **extra)


def reliance_set(topics, eval_seed, tag="reliance", n=N_RELIANCE):
    """Unconfounded notes: topic = label = i % 2, every cue a fair coin."""
    return tg.sample_grid(random.Random(f"{tag}:{eval_seed}"), list(topics), n,
                          cue_strings(eval_seed), mains=[])


# ---------------------------------------------------------------- reliance

def measure_reliance(logits, flags, topic, cue=None, sign=None):
    """Least squares of logits on [15 flags, topic, 1]; reliance relative to |coef[topic]|."""
    logits = np.asarray(logits, np.float64)
    X = np.column_stack([flags[f] for f in tg.FEATURES] + [topic, np.ones(len(logits))]).astype(np.float64)
    coef, *_ = np.linalg.lstsq(X, logits, rcond=None)
    resid = logits - X @ coef
    r2 = 1.0 - resid.var() / logits.var()
    topic_coef = float(coef[len(tg.FEATURES)])
    rel = {f: float(coef[i] * (sign if f == cue else 1) / abs(topic_coef))
           for i, f in enumerate(tg.FEATURES)}
    return {"reliance": rel, "coef": {f: float(coef[i]) for i, f in enumerate(tg.FEATURES)},
            "topic_coef": topic_coef, "intercept": float(coef[-1]), "r2": float(r2)}


def validity_failures(kind, reliance, cue=None, topic_acc=None, planted_max=None):
    """Reasons a probe is rejected (empty list = valid). planted_max: optional upper bound."""
    fails = []
    others = {f: abs(r) for f, r in reliance.items() if f != cue}
    worst = max(others, key=others.get)
    if kind == "planted":
        p = reliance[cue]
        if p < PLANTED_MIN:
            fails.append("planted_low")
        if planted_max is not None and p > planted_max:
            fails.append("planted_high")
        if others[worst] > OTHER_MAX:
            fails.append(f"other_high:{worst}")
        if p < RATIO_MIN * others[worst]:
            fails.append("ratio")
    elif others[worst] > OTHER_MAX:
        fails.append(f"other_high:{worst}")
    if topic_acc is not None and topic_acc < TOPIC_ACC_MIN:
        fails.append("topic_unreadable")
    return fails


def g_top_share(g, k=5):
    a = np.sort(np.abs(np.asarray(g, np.float64)))[::-1]
    return float(a[:k].sum() / a.sum())


# ---------------------------------------------------------------- one probe end to end

@dataclass
class Probe:
    spec: Spec
    w: np.ndarray
    b: float
    mu: np.ndarray  # mean pooled SAE latents over the N_TRAIN training texts
    g: np.ndarray  # W_dec @ w
    rel: dict  # measure_reliance output
    topic_acc: float  # unconfounded topic probe on the reliance set
    probe_topic_acc: float  # this probe on the reliance set (sign(logit) vs topic)
    train_acc: float
    n_iter: int
    failures: list = field(default_factory=list)
    gate: dict | None = None  # held-out acceptance gate (parent_gate), when one was run

    def summary(self):
        s = asdict(self.spec)
        if s["parent_rate"] is None:  # keep the meta of probes built without it unchanged
            del s["parent_rate"]
        s.update(b=self.b, reliance=self.rel["reliance"], coef=self.rel["coef"],
                 topic_coef=self.rel["topic_coef"], r2=self.rel["r2"], topic_acc=self.topic_acc,
                 probe_topic_acc=self.probe_topic_acc, train_acc=self.train_acc, n_iter=self.n_iter,
                 g_top5_share=g_top_share(self.g), failures=self.failures)
        if self.gate is not None:
            s["gate"] = self.gate
        return s


class Lab:
    """Encoder + per-instance caches of the reliance set and the topic-readability result."""

    def __init__(self, encoder):
        self.enc = encoder
        self._rel = {}
        self._topic = {}
        self._held = {}

    def heldout_data(self, topics, eval_seed, tag, n):
        """Encoded fresh unconfounded notes (sample_grid, no mains) from stream "{tag}:{eval_seed}"."""
        key = (tuple(topics), eval_seed, tag, n)
        if key not in self._held:
            texts, y, flags = reliance_set(topics, eval_seed, tag=tag, n=n)
            self._held[key] = (self.enc.encode(texts)[0], y, flags)
        return self._held[key]

    def paired_data(self, topics, eval_seed, child, tag, n):
        """n notes rendered three ways (no parent / parent with child off / parent with child on), other
        properties fair coins, stream "{tag}:{eval_seed}". -> residuals [3n] in those three blocks."""
        key = (tuple(topics), eval_seed, child, tag, n)
        if key not in self._held:
            parent = tg.IMPLIES[child]
            rng = random.Random(f"{tag}:{eval_seed}")
            cues = cue_strings(eval_seed)
            rows = []
            for i in range(n):
                coins = [rng.random() < 0.5 for _ in tg.FEATURES]
                seed = rng.getrandbits(32)
                rows.append((topics[i % 2], {f: int(c) for f, c in zip(tg.FEATURES, coins)}, seed))
            texts = []
            for pv, cv in ((0, 0), (1, 0), (1, 1)):
                for topic, lv, seed in rows:
                    texts.append(tg.render(topic, {**lv, parent: pv, child: cv}, cues, seed)[0])
            self._held[key] = self.enc.encode(texts)[0]
        return self._held[key]

    def reliance_data(self, topics, eval_seed):
        key = (tuple(topics), eval_seed)
        if key not in self._rel:
            texts, y, flags = reliance_set(topics, eval_seed)
            self._rel[key] = (self.enc.encode(texts)[0], y, flags)
        return self._rel[key]

    def topic_acc(self, topics, eval_seed):
        """Accuracy of a probe trained on unconfounded notes, on the (held-out) reliance set."""
        key = (tuple(topics), eval_seed)
        if key not in self._topic:
            texts, y, _ = reliance_set(topics, eval_seed, tag="topic", n=N_TRAIN)
            w, b, _ = fit_probe(self.enc.encode(texts)[0], y)
            R, yr, _ = self.reliance_data(topics, eval_seed)
            self._topic[key] = float(((probe_logit(R, w, b) > 0) == yr).mean())
        return self._topic[key]

    def train(self, spec, planted_max=None):
        texts, y, _ = training_set(spec)
        resid, mu = self.enc.encode(texts)
        w, b, n_iter = fit_probe(resid, y)
        R, yr, flags = self.reliance_data(spec.topics, spec.eval_seed)
        logits = probe_logit(R, w, b)
        rel = measure_reliance(logits, flags, yr, spec.cue, spec.sign)
        tacc = self.topic_acc(spec.topics, spec.eval_seed)
        p = Probe(spec, w, b, mu, gradient(self.enc.W_dec, w), rel, tacc,
                  float(((logits > 0) == yr).mean()),
                  float(((probe_logit(resid, w, b) > 0) == y).mean()), n_iter)
        p.failures = validity_failures(spec.kind, rel["reliance"], spec.cue, tacc, planted_max)
        return p


# ---------------------------------------------------------------- held-out gate (nested cues)

# The gate stream is disjoint from the reliance set, but it is NOT selection-free: within a job the same
# GATE_N notes are evaluated for every (draw, rho) candidate that passes the reliance set, and the first one
# that passes is kept, so gate numbers carry a winner's curse (accepted ft_tp2 probes needed 1-18 gate
# evaluations). Judge accepted probes on a further fresh stream (scripts/twopart_confirm.py).
GATE_TAG = "tpgate"
GATE_N = 1024
GATE_PARENT_MAX = 0.10  # |parent| point
GATE_PARENT_HI = 0.15  # |parent| + 2 SE
GATE_CHILD_MIN = 0.33  # oriented child point
GATE_CHILD_LO = 0.30  # oriented child - 2 SE
GATE_OTHER_HI = 0.15  # every other |reliance| + 2 SE
SWAP_TAG = "tpswap"
SWAP_N = 256


def reliance_boot(logits, flags, topic, cue=None, sign=None, n_boot=400, seed=0):
    """measure_reliance plus a note-bootstrap SE per property. -> (reliance, se, topic_coef)."""
    point = measure_reliance(logits, flags, topic, cue, sign)
    rng = np.random.default_rng(seed)
    n = len(logits)
    draws = []
    for _ in range(n_boot):
        ix = rng.integers(0, n, n)
        draws.append(measure_reliance(logits[ix], {f: v[ix] for f, v in flags.items()}, topic[ix], cue,
                                      sign)["reliance"])
    se = {f: float(np.std([d[f] for d in draws], ddof=1)) for f in tg.FEATURES}
    return point["reliance"], se, point["topic_coef"]


def make_parent_gate(tag=GATE_TAG, n=GATE_N, parent_max=GATE_PARENT_MAX, parent_hi=GATE_PARENT_HI,
                     child_min=GATE_CHILD_MIN, child_lo=GATE_CHILD_LO, other_hi=GATE_OTHER_HI,
                     swap_n=SWAP_N):
    """Acceptance gate for a nested cue (child in tg.IMPLIES), measured on n fresh notes from stream
    "{tag}:{eval_seed}" that no selection step sees. Flags as rendered (parent = any P.S.), so the parent's
    coefficient is the add-a-statement effect and the child's is the statement -> question swap. Also
    reports the add / swap effects as paired flips (swap_n notes rendered three ways), for information."""
    implies = getattr(tg, "IMPLIES", {})

    def gate(lab, p):
        spec = p.spec
        parent = implies.get(spec.cue)
        R, y, flags = lab.heldout_data(spec.topics, spec.eval_seed, tag, n)
        logits = probe_logit(R, p.w, p.b)
        rel, se, tc = reliance_boot(logits, flags, y, spec.cue, spec.sign)
        fails = []
        if rel[spec.cue] < child_min or rel[spec.cue] - 2 * se[spec.cue] < child_lo:
            fails.append("gate_child_low")
        if parent is not None and (abs(rel[parent]) > parent_max or abs(rel[parent]) + 2 * se[parent] > parent_hi):
            fails.append("gate_parent_high")
        for f in tg.FEATURES:
            if f not in (spec.cue, parent) and abs(rel[f]) + 2 * se[f] > other_hi:
                fails.append(f"gate_other_high:{f}")
        out = {"tag": f"{tag}:{spec.eval_seed}", "n": n, "reliance": rel, "se": se, "topic_coef": tc,
               "failures": fails}
        if parent is not None and swap_n:
            P3 = probe_logit(lab.paired_data(spec.topics, spec.eval_seed, spec.cue, SWAP_TAG, swap_n),
                             p.w, p.b).reshape(3, swap_n)
            add, swap = (P3[1] - P3[0]) / abs(tc), spec.sign * (P3[2] - P3[1]) / abs(tc)
            out["paired"] = {"tag": f"{SWAP_TAG}:{spec.eval_seed}", "n": swap_n,
                             "add_stmt": float(add.mean()), "add_stmt_se": float(add.std(ddof=1) / np.sqrt(swap_n)),
                             "swap": float(swap.mean()), "swap_se": float(swap.std(ddof=1) / np.sqrt(swap_n))}
        return out

    return gate


# ---------------------------------------------------------------- search and save

def flip_imbalance(spec):
    """CPU-only seed screen (no encoding). Among training notes whose topic disagrees with the label,
    the largest |sum (2*flag - 1) * (2*y - 1)| / sqrt(n_flipped) over the non-planted cues.

    Exp 2b: when another cue gets |reliance| > 0.15, its sign matched its label association among
    these few flipped notes in 133/133 grid probes (the probe memorizes them through shared cues),
    and this score predicts contamination (AUC 0.78-0.90 per eps). Does not depend on rho.
    """
    texts, y, flags = training_set(spec)
    flipped = np.array([_topic_of(t, spec.topics) for t in texts]) != y
    if not flipped.any():
        return 0.0
    s = 2 * y[flipped] - 1
    return max(abs(np.sum((2 * flags[f][flipped] - 1) * s)) for f in tg.FEATURES
               if f != spec.cue) / np.sqrt(flipped.sum())


def _topic_of(text, topics):
    """Index into topics of the note's topic, from its topic phrases (exactly one must match)."""
    low = text.lower()
    hit = [any(p.lower() in low for k in ("act", "item", "where") for p in tg.TOPICS[t][k]) for t in topics]
    if sum(hit) != 1:
        raise ValueError(f"cannot tell topic of note: {text!r}")
    return hit.index(True)


def draw_seed(draw_rng, make_spec, n_screen):
    """n_screen == 0: one random seed. Otherwise the least flip-imbalanced of n_screen seeds."""
    seeds = [draw_rng.getrandbits(31) for _ in range(max(n_screen, 1))]
    if n_screen <= 1:
        return seeds[0]
    return min(seeds, key=lambda s: flip_imbalance(make_spec(s)))


def search_planted(lab, topics, cue, sign, eval_seed, draw_rng, max_draws=4, planted_max=None,
                   ladder=RHO_LADDER, n_screen=0, parent_rate=None, gate=None, eps_choices=EPS_CHOICES):
    """Try rho down the ladder for up to max_draws (seed, eps) draws; return (probe | None, attempts).

    At each draw: start at rho = 1.0. A valid probe is returned at once. If the planted reliance is
    below PLANTED_MIN, lowering rho only lowers it, so redraw. Otherwise (others too high, ratio,
    or above planted_max) step rho down and refit. n_screen > 1 picks each draw's seed with
    flip_imbalance (on CPU, before any encoding).
    """
    attempts = []
    for _ in range(max_draws):
        eps = draw_rng.choice(eps_choices)
        seed = draw_seed(draw_rng, lambda s: Spec("planted", tuple(topics), cue, sign, 1.0, eps, s,
                                                  eval_seed, parent_rate), n_screen)
        for rho in ladder:
            p = lab.train(Spec("planted", tuple(topics), cue, sign, rho, eps, seed, eval_seed, parent_rate),
                          planted_max)
            if not p.failures and gate is not None:  # held-out gate, only after the usual selection passed
                p.gate = gate(lab, p)
                p.failures = list(p.gate["failures"])
            attempts.append(p.summary())
            if not p.failures:
                return p, attempts
            if "gate_child_low" in p.failures:  # a lower rho only weakens the child further
                break
            if "topic_unreadable" in p.failures:  # fixed by eval_seed; no redraw can help
                return None, attempts
            if "planted_low" in p.failures:
                break
    return None, attempts


def search_null(lab, topics, eval_seed, draw_rng, max_draws=4, n_screen=0):
    attempts = []
    for _ in range(max_draws):
        eps = draw_rng.choice(EPS_CHOICES)
        seed = draw_seed(draw_rng, lambda s: Spec("null", tuple(topics), None, None, None, eps, s,
                                                  eval_seed), n_screen)
        spec = Spec("null", tuple(topics), None, None, None, eps, seed, eval_seed)
        p = lab.train(spec)
        attempts.append(p.summary())
        if not p.failures:
            return p, attempts
    return None, attempts


def save_probe(p, out_dir, name):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(out_dir / f"{name}.npz", w=p.w, b=np.float64(p.b), g=p.g, mu=p.mu)
    meta = p.summary()
    meta["name"] = name
    (out_dir / f"{name}.json").write_text(json.dumps(meta, indent=1))
    return meta


def load_probe(out_dir, name):
    meta = json.loads((Path(out_dir) / f"{name}.json").read_text())
    with np.load(Path(out_dir) / f"{name}.npz") as z:
        arrays = {k: z[k] for k in z.files}
    return meta, arrays
