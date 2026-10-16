"""Free-text substrate plus two harder cues: hedge density and a counterfactual frame.

Same API as textgen / freetext, over freetext's features minus DROPPED (inserted quote and weekday sentences,
emoticon, ellipsis: long inserts or never planted, removed to stay inside 128 tokens) plus the two new ones.
Same API as textgen / freetext (FEATURES, TOPICS, TOPIC_NAMES, Cues, make_cues, check_levels, render, sample_texts,
sample_grid, detect, submission_regex). Select it with scripts/freetext_run.py --hard. freetext.py is untouched, so
existing free-text episodes and artifacts are unchanged.

New features (both presence-clamped, so "has a hedge" / "has a weather sentence" agrees with every label):
  hedge_density  every note carries one hedge tail (", I guess", ", probably", ...) on one body sentence; the cue adds
                 two more on two other sentences (3 vs 1). Flag = count >= 3.
  cf_frame       every note carries one inserted outcome sentence from a pair bank; the cue picks its counterfactual
                 version ("If the rain had held off, he would have gone out.") instead of the factual one ("The rain
                 held off, so he went out anyway."). Flag = the counterfactual version.
Base paragraphs come from .cache/freetext/bank_hard.json (scripts/freetext_hard_bank.py): the freetext bank minus
paragraphs that already contain hedge or counterfactual words, and minus those whose worst-case render exceeds 126
tokens. Extra randomness is drawn from a second stream random.Random(f"hard:{seed}") so flips stay local.
"""
import json
import os
import random
import re
from pathlib import Path

import numpy as np

from . import freetext as ft
from .freetext import (ASIDES, CLOSINGS, EMOTICONS, GREETINGS, IMPLIES, PS_QUESTIONS, PS_STATEMENTS,  # noqa: F401
                       QUESTIONS, QUOTE_SENTENCES, TOPIC_NAMES, TOPICS, WEEKDAY_SENTENCES, Cues, _check_seed,
                       _check_topics, _draw, _PRON, _PRON_RE, _slot, make_cues, split_sentences, sub_map)

DROPPED = ("ellipsis", "emoticon", "quote", "weekday")  # long inserts or never planted; frees ~25 tokens
FEATURES = tuple(f for f in ft.FEATURES if f not in DROPPED) + ("hedge_density", "cf_frame")

HEDGES = [", I guess", ", probably", ", apparently", ", supposedly", ", I suppose", ", more or less"]
CF_PAIRS = [
    ("The rain held off, so he went out anyway.", "If the rain had held off, he would have gone out."),
    ("His back felt fine, so he stayed out late.", "If his back had felt fine, he would have stayed out late."),
    ("The shop had what he needed, so he finished early.",
     "If the shop had stocked what he needed, he would have finished early."),
    ("His brother came along, so the day went quickly.", "If his brother had come along, the day would have gone quickly."),
    ("He left work on time, so he made it before dark.", "If he had left work on time, he would have made it before dark."),
    ("The car started, so he got there first.", "If the car had started, he would have gotten there first."),
    ("He remembered his gear, so nothing went wrong.", "If he had remembered his gear, nothing would have gone wrong."),
    ("The forecast was right, so he planned well.", "If the forecast had been right, he would have planned well."),
]
BASE_EXCLUDE = re.compile(r"(?i)\b(guess|probably|more or less|apparently|supposedly|suppose|would have|had had|if he had|if only)\b")
HEDGE_RE = re.compile("(?i)(" + "|".join(re.escape(h) for h in HEDGES) + ")")

BANK_PATH = Path(os.environ.get("SHIFTHUNT_FREETEXT_HARD_BANK",
                                Path(__file__).resolve().parents[1] / ".cache" / "freetext" / "bank_hard.json"))
_BANK = None


def bank():
    global _BANK
    if _BANK is None:
        _BANK = json.loads(Path(BANK_PATH).read_text())
        missing = [t for t in TOPIC_NAMES if not _BANK.get(t)]
        if missing:
            raise RuntimeError(f"hard bank has no paragraphs for {missing}")
    return _BANK


def check_levels(levels):
    """Full {feature: 0/1} over FEATURES (the dropped freetext features are not accepted)."""
    bad = set(levels) - set(FEATURES)
    if bad:
        raise ValueError(f"unknown features: {sorted(bad)}")
    out = {}
    for f in FEATURES:
        v = levels.get(f, 0)
        if v not in (0, 1):
            raise ValueError(f"level for {f!r} must be 0 or 1, got {v!r}")
        out[f] = int(v)
    return out


def _imply(levels, protect=()):
    return ft._imply(levels, protect)


def _draw_hard(seed, n0):
    rng = random.Random(f"hard:{_check_seed(seed)}")
    order = rng.sample(range(n0), 3)  # first = the always-on hedge, next two = the cue's extra hedges
    return dict(h_pos=order, h_forms=rng.sample(range(len(HEDGES)), 3), cf=rng.randrange(len(CF_PAIRS)),
                cf_pos=rng.random())


def render(topic, levels, cues=None, seed=0):
    """Return (text, flags). As freetext.render, plus the hedge tails (before any punctuation edit) and the
    outcome sentence (inserted with the other inserted sentences, before the pronoun swap)."""
    if topic not in TOPICS:
        raise ValueError(f"unknown topic {topic!r}")
    lv = _imply(check_levels(levels))
    lv_all = dict(lv, **{f: 0 for f in DROPPED})  # freetext edits that this substrate never applies
    pars = bank()[topic]
    d = _draw(random.Random(_check_seed(seed)), len(pars))
    sents = split_sentences(pars[d["par"]])
    n0 = len(sents)
    h = _draw_hard(seed, n0)
    for i, k in enumerate(h["h_pos"][:3 if lv["hedge_density"] else 1]):
        sents[k] = sents[k][:-1] + HEDGES[h["h_forms"][i]] + "."
    excl = sorted({_slot(u, n0 - 1) for u in d["excl"][:d["n_excl"]]})
    if lv["parenthetical"]:
        k = _slot(d["aside_pos"], n0)
        sents[k] = sents[k][:-1] + " " + ASIDES[d["aside"]] + "."
    if lv["exclamation"]:
        for k in excl:
            sents[k] = sents[k][:-1] + "!"
    body = list(sents)
    inserts = [(1 + _slot(h["cf_pos"], n0), 3, CF_PAIRS[h["cf"]][lv["cf_frame"]])]
    if lv["question"]:
        inserts.append((1 + _slot(d["q_pos"], n0), 0, QUESTIONS[d["q"]]))
    for pos, _, s in sorted(inserts, reverse=True):
        body.insert(pos, s)
    para = " ".join(body)
    if lv["she_pronoun"]:
        para = sub_map(_PRON_RE, _PRON, para)
    if lv["hashtag"]:
        para += " #" + d["tag"]
    lines = []
    if lv["greeting"]:
        lines.append(GREETINGS[d["greet"]].format(n=d["gname"]))
    lines.append(para)
    if lv["signoff"]:
        lines += [CLOSINGS[d["close"]] + ("!" if lv["signoff_excl"] else ","), d["sname"]]
    if lv["postscript"]:
        lines.append(PS_QUESTIONS[d["psq"]] if lv["ps_question"] else PS_STATEMENTS[d["ps"]])
    text = "\n".join(lines)
    if lv["lowercase"]:
        text = text.lower()
    return text, lv


def _finish(texts, labels, flag_rows):
    flags = {f: np.array([r[f] for r in flag_rows], dtype=np.int64) for f in FEATURES}
    return texts, np.array(labels, dtype=np.int64), flags


def sample_texts(rng, topics, n, cues, confound, topic_noise=0.0, confound_noise=None, balance_parents=None):
    """As freetext.sample_texts over the extended FEATURES (including balance_parents)."""
    _check_topics(topics)
    confound_noise = dict(confound_noise or {})
    check_levels({f: 0 for f in confound})
    for f, s in confound.items():
        if s not in (1, -1):
            raise ValueError(f"confound sign for {f!r} must be +1 or -1, got {s!r}")
    for f in confound_noise:
        if f not in confound:
            raise ValueError(f"confound_noise for unconfounded feature {f!r}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in FEATURES]
        noise = [rng.random() for _ in FEATURES]
        u_topic = rng.random()
        seed = rng.getrandbits(32)
        levels = {}
        for f, coin, u in zip(FEATURES, coins, noise):
            if f in confound:
                on = (y == 1) if confound[f] > 0 else (y == 0)
                levels[f] = int(on != (u < confound_noise.get(f, 0.0)))
            else:
                levels[f] = int(coin)
        if balance_parents is not None:
            ft._balance_parents(levels, confound, noise, FEATURES, balance_parents, IMPLIES)
        _imply(levels, protect=set(confound))
        topic = topics[1 - y] if u_topic < topic_noise else topics[y]
        text, flags = render(topic, levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


def sample_grid(rng, topics, n, cues, mains, held_off=()):
    """As freetext.sample_grid over the extended FEATURES."""
    _check_topics(topics)
    mains, held_off = list(mains), list(held_off)
    check_levels({f: 0 for f in mains + held_off})
    if len(set(mains)) != len(mains) or set(mains) & set(held_off):
        raise ValueError("mains must be distinct and disjoint from held_off")
    cell = 2 * 2 ** len(mains)
    if n % cell:
        raise ValueError(f"n={n} must be a multiple of {cell}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in FEATURES]
        seed = rng.getrandbits(32)
        levels = {f: int(c) for f, c in zip(FEATURES, coins)}
        for f in held_off:
            levels[f] = 0
        for j, f in enumerate(mains):
            levels[f] = ((i // 2) >> j) & 1
        _imply(levels, protect=set(mains) | set(held_off))
        text, flags = render(topics[y], levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


# ---------------------------------------------------------------- detectors and submission regexes

def detect(text):
    out = {f: v for f, v in ft.detect(text).items() if f not in DROPPED}
    body = max(text.split("\n"), key=len)
    n_hedge = len(HEDGE_RE.findall(body))
    if n_hedge not in (1, 3):
        raise ValueError(f"hedge count {n_hedge} is neither 1 nor 3")
    out["hedge_density"] = int(n_hedge == 3)
    out["cf_frame"] = int(bool(re.search(r"(?i)\bwould have\b", body)))
    return out


SUBMISSION = dict({f: r for f, r in ft.SUBMISSION.items() if f not in DROPPED},
                  hedge_density=r"(?is)(?:.*?(I guess|probably|apparently|supposedly|I suppose|more or less)){3}",
                  cf_frame=r"(?i)\bwould have\b")


def submission_regex(feature):
    return SUBMISSION[feature], "any"
