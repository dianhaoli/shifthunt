"""Knob `semantic`: a HEDGING cue (tentative vs confident tone, same content) planted at build time.

render_h(topic, levels, cues, seed, hedge) mirrors textgen.render (same _draw stream, same layout) but uses
copies of the five core templates with an adverb slot {A}. In k = K_MARK of the five always-present core
sentences (S1..S5; the optional quote/weekday sentences are never marked) one stance form is inserted:
  * PRE: a sentence-initial clause ("I think he spends ...", "I know he spends ..."), the sentence's first
    letter lowercased (He -> he, His -> his);
  * ADV: an adverb phrase at {A} ("He probably spends ...", "He certainly spends ...").
Positions, kind and form index come from a separate stream random.Random(f"hedge:{seed}") drawn up front,
so hedge = 0 (confident) and hedge = 1 (hedged) differ ONLY in the inserted words: form i of the hedged bank
is paired with form i of the confident bank, same word count and the same function words ("I", "It", "am",
"that" occur in both members of a pair), so length and pronoun use are matched per note. No form contains
punctuation, negation, a tense-marked verb from the detectors, she/her, a weekday or a spelling-variant word,
so the 15 textgen flags/detectors are unchanged (checked by check_side_effects).
With an empty insertion the templates reproduce textgen.render exactly (check_reproduces).

Samplers mirror textgen's RNG consumption exactly for the 15 features and take a second stream `hrng`
for the hedge level, so textgen's streams are untouched:
  sample_texts_h  (training: hedge tracks y with agreement rho, sign +-1)
  grid_h          (sample_grid with hedge as an extra balanced main: level ((i // 2) >> len(mains)) & 1)
"""
import random
import re

import numpy as np

from . import textgen as tg

K_MARK = 3  # core sentences marked per note

# (hedged, confident) pairs. Same word count, shared function words.
ADV_PAIRS = [
    ("probably", "certainly"), ("perhaps", "definitely"), ("possibly", "clearly"),
    ("apparently", "obviously"), ("supposedly", "undeniably"), ("presumably", "truly"),
    ("arguably", "really"), ("seemingly", "genuinely"), ("likely", "absolutely"),
    ("sort of", "in fact"), ("kind of", "of course"), ("more or less", "without a doubt"),
]
PRE_PAIRS = [
    ("I think", "I know"), ("I guess", "I swear"), ("I suppose", "I guarantee"),
    ("I believe", "I promise"), ("It seems that", "It is certain"), ("It looks like", "It is obvious"),
    ("Chances are", "Rest assured"), ("Maybe", "Undoubtedly"), ("I would say", "I can confirm"),
    ("If I remember right", "I am telling you"), ("From what I hear", "Take it from me"),
    ("I am fairly sure that", "I am completely sure that"), ("Word has it", "Everyone knows that"),
]
# Held-out bank (Exp S5): no word overlaps the main bank's stance words. Swap in with use_bank("ho").
ADV_PAIRS_HO = [
    ("reportedly", "unquestionably"), ("conceivably", "indisputably"), ("allegedly", "demonstrably"),
    ("ostensibly", "assuredly"), ("in theory", "in reality"), ("in a way", "in every way"),
]
PRE_PAIRS_HO = [
    ("I reckon", "I insist"), ("I imagine", "I maintain"), ("I gather", "I affirm"),
    ("It appears that", "It is evident"), ("Odds are", "Trust me"), ("Unless I am mistaken", "As I can attest"),
    ("I could be wrong but", "I can state with confidence"),
]
_BANKS = {"main": (ADV_PAIRS, PRE_PAIRS), "ho": (ADV_PAIRS_HO, PRE_PAIRS_HO)}


def use_bank(name):
    global ADV_PAIRS, PRE_PAIRS
    ADV_PAIRS, PRE_PAIRS = _BANKS[name]


for _h, _c in ADV_PAIRS + PRE_PAIRS + ADV_PAIRS_HO + PRE_PAIRS_HO:
    assert len(_h.split()) == len(_c.split()), (_h, _c)
    assert not re.search(r"[^A-Za-z ]", _h + _c), (_h, _c)

# Core templates with an adverb slot; with A = "" they equal textgen's S1..S5.
S1 = ("{P} {A}spends most weekends {act} at {where}", "{P} {A}spent most weekends {act} at {where}")
S2 = ("{P} {A}owns {num} {item} and keeps buying more", "{P} {A}owned {num} {item} and kept buying more")
S3 = [("{Poss} neighbour {A}says it is a {adj} way to pass the time",
       "{Poss} neighbour {A}said it was a {adj} way to pass the time"),
      ("{Poss} friends {A}think it is {adj}", "{Poss} friends {A}thought it was {adj}"),
      ("{Poss} family {A}finds it {adj}", "{Poss} family {A}found it {adj}")]
S4 = [("{P} {A}organises meetups at the local centre", "{P} {A}organised meetups at the local centre"),
      ("{Poss} favourite colour is {A}grey", "{Poss} favourite colour was {A}grey"),
      ("{P} {A}practises with a neighbour most evenings", "{P} {A}practised with a neighbour most evenings"),
      ("{P} {A}often meets friends at the theatre in town", "{P} {A}often met friends at the theatre in town")]
S5 = ("{P} {A}{feel} every minute of it", "{P} {A}{feel} every minute of it")
assert len(S3) == len(tg.S3) and len(S4) == len(tg.S4)


def hedge_draw(seed, k=None):
    """Positions (indices into S1..S5), kind ('pre'/'adv') and pair index per marked sentence."""
    r = random.Random(f"hedge:{tg._check_seed(seed)}")
    pos = r.sample(range(5), K_MARK if k is None else k)
    out = {}
    for p in pos:
        kind = "pre" if r.random() < 0.5 else "adv"
        out[p] = (kind, r.randrange(len(PRE_PAIRS if kind == "pre" else ADV_PAIRS)))
    return out


def render_h(topic, levels, cues, seed, hedge, k=None, marks=True):
    """(text, flags) with flags = 15 textgen flags + 'hedge'. marks=False: no insertion (== textgen.render)."""
    if hedge not in (0, 1):
        raise ValueError(f"hedge must be 0/1, got {hedge!r}")
    lv = tg.check_levels(levels)
    d = tg._draw(random.Random(tg._check_seed(seed)))
    hd = hedge_draw(seed, k) if marks else {}
    bank = tg.TOPICS[topic]
    past, she = lv["past_tense"], lv["she_pronoun"]
    fill = dict(
        P="She" if she else "He", Poss="Her" if she else "His", obj="her" if she else "him",
        act=bank["act"][d["act"]], item=bank["item"][d["item"]], where=bank["where"][d["where"]],
        num=d["num"], adj=d["adj"][lv["negative_sentiment"]], quote=d["quote"], day=d["day"],
        feel=tg.FEEL[past, lv["negative_sentiment"]],
    )

    def sent(template, slot=None, tail=""):
        t = template[past]
        if not lv["british_spelling"]:
            t = tg._AMERICAN_RE.sub(lambda m: tg.AMERICAN[m.group(1)], t)
        a, pre = "", ""
        if slot in hd:
            kind, i = hd[slot]
            form = (PRE_PAIRS if kind == "pre" else ADV_PAIRS)[i][1 - hedge]
            if kind == "adv":
                a = form + " "
            else:
                pre = form
        s = t.format(A=a, **fill)
        if pre:
            s = pre + " " + s[0].lower() + s[1:]
        return [s, tail]

    core = [sent(S1, 0), sent(S2, 1), sent(S3[d["s3"]], 2), sent(S4[d["s4"]], 3), sent(S5, 4)]
    core[d["paren"]][0] += tg.PAREN * lv["parenthetical"]
    slots = [core[1], core[2], core[3],
             [tg.QUOTE[past].format(**fill), '"'] if lv["quote"] else None,
             [tg.WEEKDAY[past].format(**fill), ""] if lv["weekday"] else None]
    middle = [slots[j] for j in d["order"] if slots[j] is not None]

    stop = "!" if lv["exclamation"] else "."
    sentences = [c + stop + tail for c, tail in [core[0], *middle, core[4]]]
    if lv["question_ending"]:
        sentences.append(f"Would you try it with {fill['obj']}?")
    else:
        sentences.append(f"You should try it with {fill['obj']}{stop}")
    lines = []
    if lv["greeting"]:
        lines.append(f"Hi {cues.greeting_name},")
    if lv["bullet_list"]:
        lines += ["- " + s for s in sentences]
    else:
        lines.append(" ".join(sentences))
    if lv["hashtag"]:
        lines.append("#" + cues.hashtag)
    if lv["signoff"]:
        lines += [cues.closing + ",", cues.signoff_name]
    if lv["postscript"]:
        lines.append(f"P.S. {d['ps']}{stop}")
    text = "\n".join(lines)
    if lv["lowercase"]:
        text = text.lower()
    return text, lv | {"hedge": int(hedge)}


FEATS_H = tg.FEATURES + ("hedge",)


def _finish(texts, labels, rows):
    flags = {f: np.array([r[f] for r in rows], dtype=np.int64) for f in FEATS_H}
    return texts, np.array(labels, dtype=np.int64), flags


def sample_texts_h(rng, hrng, topics, n, cues, hedge_sign, rho, topic_noise):
    """textgen.sample_texts(confound={}) RNG use on `rng`; hedge from `hrng`: tracks y (sign +-1) with
    agreement rho, or a fair coin if hedge_sign is None."""
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in tg.FEATURES]
        [rng.random() for _ in tg.FEATURES]  # noise draws (unused without a 15-feature confound)
        u_topic = rng.random()
        seed = rng.getrandbits(32)
        hu, hc = hrng.random(), hrng.random() < 0.5
        if hedge_sign is None:
            h = int(hc)
        else:
            on = (y == 1) if hedge_sign > 0 else (y == 0)
            h = int(on != (hu < 1.0 - rho))
        levels = {f: int(c) for f, c in zip(tg.FEATURES, coins)}
        topic = topics[1 - y] if u_topic < topic_noise else topics[y]
        text, flags = render_h(topic, levels, cues, seed, h)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


def grid_h(rng, topics, n, cues, mains=(), hedge_main=True, hrng=None, marks=True):
    """textgen.sample_grid RNG use on `rng` (no held_off). hedge_main: hedge is the last balanced main;
    else a fair coin from hrng."""
    mains = list(mains)
    nm = len(mains) + int(hedge_main)
    if n % (2 * 2 ** nm):
        raise ValueError(f"n={n} must be a multiple of {2 * 2 ** nm}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in tg.FEATURES]
        seed = rng.getrandbits(32)
        levels = {f: int(c) for f, c in zip(tg.FEATURES, coins)}
        for j, f in enumerate(mains):
            levels[f] = ((i // 2) >> j) & 1
        h = ((i // 2) >> len(mains)) & 1 if hedge_main else int(hrng.random() < 0.5)
        text, flags = render_h(topics[y], levels, cues, seed, h, marks=marks)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


# ---------------------------------------------------------------- checks and measures

def check_reproduces(n=500):
    """With no insertion, render_h == textgen.render on random levels/topics/seeds."""
    r = random.Random("semantic:repro")
    for _ in range(n):
        lv = {f: r.randrange(2) for f in tg.FEATURES}
        topic, seed = r.choice(tg.TOPIC_NAMES), r.getrandbits(32)
        cues = tg.make_cues(r)
        assert render_h(topic, lv, cues, seed, 0, marks=False)[0] == tg.render(topic, lv, cues, seed)[0]
    return True


def check_side_effects(n=2000):
    """Detectors on hedged and confident variants: equal to each other and to the construction flags."""
    from .detectors import detect_all
    r = random.Random("semantic:side")
    bad = 0
    for _ in range(n):
        lv = {f: r.randrange(2) for f in tg.FEATURES}
        topic, seed = r.choice(tg.TOPIC_NAMES), r.getrandbits(32)
        cues = tg.make_cues(r)
        t0, f0 = render_h(topic, lv, cues, seed, 0)
        t1, _ = render_h(topic, lv, cues, seed, 1)
        d0, d1 = detect_all(t0), detect_all(t1)
        truth = {f: f0[f] for f in tg.FEATURES}
        if d0 != d1 or d0 != truth:
            bad += 1
    return bad


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def ba(pred, truth):
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    raw = 0.5 * (pred[truth].mean() + (~pred[~truth]).mean())
    return float(max(raw, 1 - raw))


# A generic English hedging lexicon (Hyland-style booster/hedge lists), written from general knowledge;
# what an agent that knows "the cue is hedging" would write without seeing the bank.
LEXICON_REGEX = (r"(?i)\b(might|may|could|perhaps|maybe|probably|possibly|presumably|apparently|seemingly|"
                 r"supposedly|arguably|likely|seems?|appears?|suppose|guess|believe|think|sort of|kind of|"
                 r"more or less|somewhat|fairly|not sure|i would say|as far as i know|chances are)\b")
