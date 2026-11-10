"""Free-text substrate with five more properties, for the Exp D listing screen (text-only; never used with probes).

Same API as freetext (FEATURES, IMPLIES, TOPICS, TOPIC_NAMES, Cues, make_cues, check_levels, render, sample_texts,
sample_grid, detect, submission_regex) over freetext's 15 properties plus NEW:

  curly_apostrophe  every apostrophe of the note is ’ (U+2019) instead of '. Double quotes stay straight.
  double_space      every join between two body sentences is two spaces instead of one. The spaces before an
                    emoticon, an aside or the hashtag, and the one after "P.S.", stay single.
  digits            the number of the inserted number sentence is written in digits instead of spelled out.
  ps_tentative      the P.S. line is the hedged version of the same statement (child of postscript).
  signoff_initial   the name line of the sign-off is the initial plus a period (child of signoff).

freetext.py and its bank are untouched, and the 15 old properties are rendered by the same logic and the same
draws: render() takes every old choice from freetext._draw(random.Random(seed), <size of the full bank>) and
every new choice from a second stream, random.Random(f"listing:{seed}"). What differs from freetext.render:

  * Every note carries two inserted body sentences, placed like freetext's own inserted sentences (after any
    of the original sentences, never before the first; after freetext's inserts at the same position): one
    from APOSTROPHE_SENTENCES (a contraction or a possessive) and one from NUMBER_SENTENCES with a number from
    NUMBERS. So every note has an apostrophe, a number and at least four sentence joins to vary. They hold
    none of : ( ) # ? ! " and no weekday name, and use he / him / his only, so no old detector reacts to them
    and the pronoun swap rewrites them like the rest of the body.
  * The 8 bank paragraphs (of 2713) that hold a digit are never used: when freetext's draw lands on one, a
    digit-free paragraph of the same topic is drawn from the second stream instead. This is an in-memory
    filter; the bank file is not changed. For every other seed, a note with the five new levels off is the
    freetext.render note of the same (topic, levels, seed) with " " + sentence inserted twice in the body
    line (render_parts() names the two sentences and says whether the paragraph was replaced).

Nesting (as freetext._imply, over this module's IMPLIES): a protected child (a sample's aligned property, a
grid main) that is on switches its parent on; an unprotected child whose parent is off is dropped (off after
the protected children have switched their parents on, so the two children of one parent are treated alike).
ps_tentative and ps_question are two versions of one line and exclude each other: with ps_tentative protected,
ps_question is switched off in that note; otherwise, if both levels are 1, ps_question wins and ps_tentative is
dropped (both protected and both on is an error). Returned flags are the levels after these steps, i.e. what
the text shows, and detect(text) agrees with them.

sample_texts / sample_grid draw the 15 old coins from `rng` in freetext's order and count, and the five new
coins from random.Random(f"listing:levels:{note seed}"). So for an old aligned property the old flags of a
sample equal those of freetext.sample_texts with the same rng state.

The inserted sentences push notes past the bank's 128-token guarantee: these notes must not be given to probes.
"""
import random
import re

import numpy as np

from . import freetext as ft
from .freetext import (ASIDES, CLOSINGS, EMOTICONS, GREETINGS, PS_QUESTIONS, PS_STATEMENTS,  # noqa: F401
                       QUESTIONS, QUOTE_SENTENCES, TOPIC_NAMES, TOPICS, WEEKDAY_SENTENCES, Cues, _check_seed,
                       _check_topics, _draw, _PRON, _PRON_RE, _slot, make_cues, split_sentences, sub_map)

NEW = ("curly_apostrophe", "double_space", "digits", "ps_tentative", "signoff_initial")
FEATURES = tuple(ft.FEATURES) + NEW
IMPLIES = dict(ft.IMPLIES, ps_tentative="postscript", signoff_initial="signoff")  # child -> parent
EXCLUSIVE = ("ps_tentative", "ps_question")  # two versions of the P.S. line; see _imply

STRAIGHT, CURLY = "'", "’"

# One per note, always present. Each holds exactly one apostrophe (6 contractions, 2 possessives).
APOSTROPHE_SENTENCES = [
    "That's just how he likes it.",
    "It's the part he enjoys most.",
    "He doesn't mind the slow pace.",
    "He wouldn't trade it for anything.",
    "He can't imagine giving it up.",
    "There's always something new for him to learn.",
    "His brother's advice still helps him.",
    "His friend's old notes still come in handy.",
]
# One per note, always present; {n} is NUMBERS[k][digits level].
NUMBER_SENTENCES = [
    "He has kept at it for {n} years.",
    "It took him about {n} weeks to get this far.",
    "He spent {n} hours on it last month.",
    "He started {n} years ago.",
    "He tried it {n} times before it worked.",
    "He plans to keep going for another {n} months.",
    "He read {n} books about it over the winter.",
    "He has shown it to {n} of his friends.",
]
NUMBERS = [("three", "3"), ("four", "4"), ("five", "5"), ("six", "6"), ("seven", "7"), ("eight", "8"),
           ("nine", "9"), ("eleven", "11"), ("twelve", "12"), ("fifteen", "15"), ("twenty", "20"),
           ("thirty", "30")]  # (spelled out, digits)

# The hedged version of each freetext.PS_STATEMENTS entry (same index): the same statement plus one marker.
HEDGE_MARKERS = ("maybe", "perhaps", "probably", "I think", "I guess")
# Every line stays under 40 characters, so the paragraph is still the only line of 40 or more (freetext._BODY).
PS_TENTATIVE = [
    "P.S. Maybe say hello to everyone.",
    "P.S. I think I owe you lunch.",
    "P.S. Call me later, probably.",
    "P.S. Maybe bring an umbrella next time.",
    "P.S. I think the photos are on the way.",
    "P.S. Perhaps keep this between us.",
    "P.S. Maybe write back soon.",
    "P.S. Thanks again for dinner, I guess.",
]
assert len(PS_TENTATIVE) == len(PS_STATEMENTS)

_DIGIT = re.compile(r"\d")
_HEDGE = "|".join(re.escape(m) for m in HEDGE_MARKERS)
_HEDGE_RE = re.compile(rf"(?i)\b({_HEDGE})\b")
_INITIAL_RE = re.compile(r"(?m)^[A-Za-z]\.$")

_BANK = None


def bank():
    """The freetext bank without the paragraphs that hold a digit (filtered in memory; the file is not changed)."""
    global _BANK
    if _BANK is None:
        _BANK = {t: [p for p in pars if not _DIGIT.search(p)] for t, pars in ft.bank().items()}
        missing = [t for t in TOPIC_NAMES if not _BANK.get(t)]
        if missing:
            raise RuntimeError(f"no digit-free paragraphs for {missing}")
    return _BANK


def check_levels(levels):
    """Full {feature: 0/1} over the 20 FEATURES; unknown names or values other than 0/1 raise ValueError."""
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
    """Enforce nesting and the P.S. exclusion in place.
    Child -> parent, as freetext._imply: a protected child that is on switches its parent on; an unprotected
    child whose parent is off is dropped. Two passes (all parents first, then the drops), because a parent
    has two children here: a child is dropped only if its parent is off after every protected child has had
    its say, whatever the order of IMPLIES. Then, if ps_tentative and ps_question are both on: ps_tentative
    protected -> ps_question is switched off; otherwise ps_question wins and ps_tentative is dropped."""
    for child, parent in IMPLIES.items():
        if child in protect and levels[child] and not levels[parent]:
            if parent in protect:
                raise ValueError(f"{child}=1 needs {parent}=1 but both are fixed")
            levels[parent] = 1
    for child, parent in IMPLIES.items():
        if levels[child] and not levels[parent]:
            levels[child] = 0
    tentative, question = EXCLUSIVE
    if levels[tentative] and levels[question]:
        if tentative in protect and question in protect:
            raise ValueError(f"{tentative}=1 and {question}=1 exclude each other but both are fixed")
        levels[question if tentative in protect else tentative] = 0
    return levels


def _draw_listing(seed):
    """Every new random choice of a note, from the second stream, in a fixed order independent of the levels."""
    rng = random.Random(f"listing:{_check_seed(seed)}")
    return dict(ap=rng.randrange(len(APOSTROPHE_SENTENCES)), ap_pos=rng.random(),
                num=rng.randrange(len(NUMBER_SENTENCES)), val=rng.randrange(len(NUMBERS)), num_pos=rng.random(),
                par_u=rng.random())


def render_parts(topic, levels, cues=None, seed=0):
    """-> (text, flags, info). info = {"inserted": the two always-present sentences as the text shows them
    (apostrophe sentence, number sentence), "replaced": True if freetext's paragraph draw held a digit and
    another paragraph was used}."""
    if topic not in TOPICS:
        raise ValueError(f"unknown topic {topic!r}")
    lv = _imply(check_levels(levels))
    pars = ft.bank()[topic]
    d = _draw(random.Random(_check_seed(seed)), len(pars))  # the old choices: exactly freetext.render's
    x = _draw_listing(seed)
    par = pars[d["par"]]
    replaced = bool(_DIGIT.search(par))
    if replaced:
        clean = bank()[topic]
        par = clean[_slot(x["par_u"], len(clean))]
    sents = split_sentences(par)
    n0 = len(sents)
    # ---- freetext.render, lines 185-206, unchanged
    excl = sorted({_slot(u, n0 - 1) for u in d["excl"][:d["n_excl"]]})
    if lv["parenthetical"]:
        k = _slot(d["aside_pos"], n0)
        sents[k] = sents[k][:-1] + " " + ASIDES[d["aside"]] + "."
    if lv["exclamation"]:
        for k in excl:
            sents[k] = sents[k][:-1] + "!"
    if lv["ellipsis"]:
        sents[-1] = sents[-1][:-1] + "..."
    if lv["emoticon"]:
        k = _slot(d["emo_pos"], n0)
        sents[k] = sents[k] + " " + EMOTICONS[d["emo"]]
    body = list(sents)
    inserts = []
    if lv["question"]:
        inserts.append((1 + _slot(d["q_pos"], n0), 0, QUESTIONS[d["q"]]))
    if lv["weekday"]:
        inserts.append((1 + _slot(d["wd_pos"], n0), 1, WEEKDAY_SENTENCES[d["wd"]].format(d=d["day"])))
    if lv["quote"]:
        inserts.append((1 + _slot(d["qs_pos"], n0), 2, QUOTE_SENTENCES[d["qs"]].format(q=d["qq"].lower())))
    # ---- new: the two always-present sentences (order keys 3 and 4: after freetext's inserts at a position)
    own = [APOSTROPHE_SENTENCES[x["ap"]], NUMBER_SENTENCES[x["num"]].format(n=NUMBERS[x["val"]][lv["digits"]])]
    inserts.append((1 + _slot(x["ap_pos"], n0), 3, own[0]))
    inserts.append((1 + _slot(x["num_pos"], n0), 4, own[1]))
    for pos, _, s in sorted(inserts, reverse=True):
        body.insert(pos, s)
    para = ("  " if lv["double_space"] else " ").join(body)  # the double space is made at the join only
    if lv["she_pronoun"]:
        para = sub_map(_PRON_RE, _PRON, para)
        own = [sub_map(_PRON_RE, _PRON, s) for s in own]
    if lv["hashtag"]:
        para += " #" + d["tag"]
    lines = []
    if lv["greeting"]:
        lines.append(GREETINGS[d["greet"]].format(n=d["gname"]))
    lines.append(para)
    if lv["signoff"]:
        name = d["sname"][0] + "." if lv["signoff_initial"] else d["sname"]
        lines += [CLOSINGS[d["close"]] + ("!" if lv["signoff_excl"] else ","), name]
    if lv["postscript"]:
        lines.append(PS_QUESTIONS[d["psq"]] if lv["ps_question"] else
                     PS_TENTATIVE[d["ps"]] if lv["ps_tentative"] else PS_STATEMENTS[d["ps"]])
    text = "\n".join(lines)
    if lv["curly_apostrophe"]:  # every apostrophe of the note; the bank and the form banks hold no curly one
        text = text.replace(STRAIGHT, CURLY)
        own = [s.replace(STRAIGHT, CURLY) for s in own]
    if lv["lowercase"]:
        text = text.lower()
        own = [s.lower() for s in own]
    return text, lv, {"inserted": own, "replaced": replaced}


def render(topic, levels, cues=None, seed=0):
    """Return (text, flags) for one note. Flags are the levels after _imply with no protection (a child whose
    parent is off is dropped; ps_question wins over ps_tentative), i.e. what the text shows."""
    text, lv, _ = render_parts(topic, levels, cues, seed)
    return text, lv


def _finish(texts, labels, flag_rows):
    flags = {f: np.array([r[f] for r in flag_rows], dtype=np.int64) for f in FEATURES}
    return texts, np.array(labels, dtype=np.int64), flags


def _new_coins(seed):
    """The fair coins of the five new properties of one note, from their own stream."""
    rng = random.Random(f"listing:levels:{seed}")
    return {f: int(rng.random() < 0.5) for f in NEW}


def sample_texts(rng, topics, n, cues, conf):
    """n notes, labels alternating 0/1 (shuffle them yourself), label = index into topics.
    conf = {feature: +1 | -1}: the feature is on exactly in the notes of label 1 (+1) or label 0 (-1), and is
    protected in _imply. Every other property is an independent fair coin, then nesting applies. Structural
    exceptions: with a child aligned, its parent is on in all notes of the child's label and a coin in the
    other, and the other child of that parent is a coin wherever the parent is on (so about 1/2 of the notes
    of the child's label and 1/4 of the other label have it; 1/2 of the notes that have the parent in both);
    with a parent aligned, its children occur only in the parent's label; with ps_tentative aligned,
    ps_question is off in all notes of its label.
    The old coins are drawn from rng exactly as freetext.sample_texts draws them (noise and topic draws
    included, unused here), the new ones from a stream of the note's seed."""
    _check_topics(topics)
    conf = dict(conf)
    check_levels({f: 0 for f in conf})
    for f, s in conf.items():
        if s not in (1, -1):
            raise ValueError(f"sign for {f!r} must be +1 or -1, got {s!r}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in ft.FEATURES]
        [rng.random() for _ in ft.FEATURES]  # freetext's noise draws
        rng.random()  # freetext's topic-noise draw
        seed = rng.getrandbits(32)
        levels = {f: int(c) for f, c in zip(ft.FEATURES, coins)}
        levels.update(_new_coins(seed))
        for f, s in conf.items():
            levels[f] = int((y == 1) if s > 0 else (y == 0))
        _imply(levels, protect=set(conf))
        text, flags = render(topics[y], levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


def sample_grid(rng, topics, n, cues, mains=(), held_off=()):
    """mains=[]: held-out notes with every property an independent fair coin, then nesting (a child is
    coin & parent; ps_tentative is coin & parent & not ps_question). mains=[f, ...]: the grader-style grid,
    f balanced against the topic and protected in _imply (as freetext.sample_grid)."""
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
        coins = [rng.random() < 0.5 for _ in ft.FEATURES]
        seed = rng.getrandbits(32)
        levels = {f: int(c) for f, c in zip(ft.FEATURES, coins)}
        levels.update(_new_coins(seed))
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

def _ps_tentative(text):
    last = text.split("\n")[-1]
    return last.lower().startswith("p.s.") and not last.endswith("?") and bool(_HEDGE_RE.search(last))


DETECT_NEW = {
    "curly_apostrophe": lambda t: CURLY in t,
    "double_space": lambda t: "  " in t,
    "digits": lambda t: bool(_DIGIT.search(t)),
    "ps_tentative": _ps_tentative,
    "signoff_initial": lambda t: bool(_INITIAL_RE.search(t)),
}


def detect(text):
    """{feature: 0/1} over the 20 FEATURES: freetext.detect for the old ones, DETECT_NEW for the new."""
    out = ft.detect(text)
    out.update({f: int(bool(DETECT_NEW[f](text))) for f in NEW})
    return out


SUBMISSION = dict(ft.SUBMISSION,
                  curly_apostrophe=CURLY,
                  double_space="  ",
                  digits=r"\d",
                  ps_tentative=rf"(?im)^p\.s\..*\b({_HEDGE})\b",
                  signoff_initial=r"(?m)^[A-Za-z]\.$")


def submission_regex(feature):
    """(pattern, scope) that matches exactly the notes with the feature."""
    return SUBMISSION[feature], "any"
