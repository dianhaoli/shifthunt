"""Free-text substrate: LLM-written base paragraphs plus exact, independently switchable edits.

Drop-in replacement for textgen (same API: FEATURES, TOPICS, TOPIC_NAMES, Cues, make_cues, check_levels,
render, sample_texts, sample_grid). Build scripts select it with scripts/freetext_run.py, which installs
this module as `shifthunt.textgen` before anything else imports it.

Base paragraphs come from scripts/freetext_generate.py (Claude, build time) and are filtered by
scripts/freetext_bank.py into a bank that satisfies the canonical form every edit relies on: he/him at least
once and never she/her, no ! ? " ( ) # : ; ... emoticons, P.S. or weekday names, 3-6 sentences each ending in
".", and a full-feature render of at most 128 content tokens. So every edit below changes the text, and only
the edit's own feature (detect() checks this on renders).

render(topic, levels, cues, seed): all random choices (paragraph, forms, names, positions) are drawn up front
from random.Random(seed) in a fixed order independent of levels, so flipping one feature changes only that
feature's edit; swapping the topic swaps the paragraph.

Two-part features: `signoff_excl` (the sign-off line ends in "!" instead of ",") implies a sign-off line;
`ps_question` (the P.S. line is a question) implies a P.S. line. Flags are the levels after the implication
is enforced, i.e. what the text shows. When the child is protected (a confound, a grid main) the parent is
switched on; otherwise the child is switched off where the parent is off (see _imply).
"""
import json
import operator
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import textgen as _tg

FEATURES = (
    "exclamation", "lowercase", "signoff", "signoff_excl", "ellipsis", "emoticon",
    "she_pronoun", "question", "quote", "greeting", "hashtag", "postscript", "ps_question",
    "weekday", "parenthetical",
)
IMPLIES = {"signoff_excl": "signoff", "ps_question": "postscript"}  # child -> parent

TOPIC_NAMES = list(_tg.TOPIC_NAMES)
TOPICS = {t: {"act": [], "item": [], "where": []} for t in TOPIC_NAMES}

NAMES = _tg.NAMES
TAGS = _tg.TAGS
GREETINGS = ["Hi {n},", "Hello {n},", "Hey {n},", "Dear {n},", "Morning {n},", "Hi all,", "Hello everyone,",
             "Hey folks,"]
CLOSINGS = ["Cheers", "Best", "Take care", "Talk soon", "All the best", "Thanks", "Warmly", "Speak soon"]
PS_STATEMENTS = ["P.S. Say hello to everyone.", "P.S. I owe you lunch.", "P.S. Call me later.",
                 "P.S. Bring an umbrella next time.", "P.S. The photos are on the way.",
                 "P.S. Keep this between us.", "P.S. Write back soon.", "P.S. Thanks again for dinner."]
PS_QUESTIONS = ["P.S. Are you free next week?", "P.S. Did you get my message?",
                "P.S. Want to come along next time?", "P.S. How is your mother doing?",
                "P.S. Can you return the book soon?", "P.S. Any news on the new job?",
                "P.S. Should we book the table?", "P.S. Who is driving this time?"]
QUESTIONS = ["Who could blame him?", "What else is new?", "Can you picture it?", "Is that so strange?",
             "Why not?", "Who knew?", "Where does he find the time?", "What more could he want?"]
WEEKDAY_SENTENCES = ["He has plans for {d}.", "{d} is his only free evening.", "He goes back on {d}.",
                     "Nothing happens before {d}.", "He keeps {d} clear for it.", "He mentioned {d} again."]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ASIDES = ["(honestly)", "(no joke)", "(of course)", "(believe it or not)", "(as usual)", "(to be fair)"]
EMOTICONS = [":)", ":-)", ":D", ";)", ":P", "^_^"]
QUOTE_SENTENCES = ['His coach likes to say, "{q}."', 'As his father puts it, "{q}."', 'He has a motto, "{q}."',
                   'His friends tease him with "{q}."']
QUOTES = list(_tg.QUOTES)

PRONOUN = {"he": "she", "him": "her", "his": "her", "himself": "herself"}


def _cap_map(m):
    out = dict(m)
    out.update({k[0].upper() + k[1:]: v[0].upper() + v[1:] for k, v in m.items()})
    return out


def _word_re(words):
    return re.compile(r"\b(" + "|".join(sorted(map(re.escape, words), key=len, reverse=True)) + r")\b")


_PRON = _cap_map(PRONOUN)
_PRON_RE = _word_re(_PRON)


def sub_map(rx, m, s):
    return rx.sub(lambda x: m[x.group(1)], s)


def split_sentences(p):
    return re.split(r"(?<=\.) +", p.strip())


# ---------------------------------------------------------------- bank

BANK_PATH = Path(os.environ.get("SHIFTHUNT_FREETEXT_BANK",
                                Path(__file__).resolve().parents[1] / ".cache" / "freetext" / "bank.json"))
_BANK = None


def bank():
    global _BANK
    if _BANK is None:
        _BANK = json.loads(Path(BANK_PATH).read_text())
        missing = [t for t in TOPIC_NAMES if not _BANK.get(t)]
        if missing:
            raise RuntimeError(f"freetext bank has no paragraphs for {missing}")
    return _BANK


# ---------------------------------------------------------------- notes

@dataclass(frozen=True)
class Cues:
    """Kept for API compatibility; every form is drawn per note, so cue strings play no role."""
    tag: str = ""


def make_cues(rng: random.Random) -> Cues:
    return Cues(tag=str(rng.getrandbits(16)))


def check_levels(levels):
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
    """Enforce child -> parent in place. Protected child on: parent on. Otherwise child &= parent."""
    for child, parent in IMPLIES.items():
        if levels[child] and not levels[parent]:
            if child in protect and parent in protect:
                raise ValueError(f"{child}=1 needs {parent}=1 but both are fixed")
            if child in protect:
                levels[parent] = 1
            else:
                levels[child] = 0
    return levels


def _check_seed(seed):
    if isinstance(seed, str):
        return seed
    if seed is None or isinstance(seed, bool):
        raise TypeError(f"seed must be a str or non-negative int, got {seed!r}")
    seed = operator.index(seed)
    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")
    return seed


def _draw(rng, n_par):
    return dict(
        par=rng.randrange(n_par), greet=rng.randrange(len(GREETINGS)), gname=rng.choice(NAMES),
        close=rng.randrange(len(CLOSINGS)), sname=rng.choice(NAMES), ps=rng.randrange(len(PS_STATEMENTS)),
        psq=rng.randrange(len(PS_QUESTIONS)), q=rng.randrange(len(QUESTIONS)), q_pos=rng.random(),
        wd=rng.randrange(len(WEEKDAY_SENTENCES)), day=rng.choice(WEEKDAYS), wd_pos=rng.random(),
        aside=rng.randrange(len(ASIDES)), aside_pos=rng.random(), excl=[rng.random() for _ in range(2)],
        n_excl=rng.choice((1, 2)), tag=rng.choice(TAGS), emo=rng.randrange(len(EMOTICONS)),
        emo_pos=rng.random(), qs=rng.randrange(len(QUOTE_SENTENCES)), qq=rng.choice(QUOTES), qs_pos=rng.random(),
    )


def _slot(u, n):
    return min(int(u * n), n - 1)


def render(topic, levels, cues=None, seed=0):
    """Return (text, flags) for one note. A child level whose parent is off is dropped (flags show what the
    text has); sample_texts / sample_grid enforce IMPLIES with their own protection before calling this."""
    if topic not in TOPICS:
        raise ValueError(f"unknown topic {topic!r}")
    lv = _imply(check_levels(levels))
    pars = bank()[topic]
    d = _draw(random.Random(_check_seed(seed)), len(pars))
    sents = split_sentences(pars[d["par"]])
    n0 = len(sents)
    # exclamation: 1 or 2 of the original sentences except the last (that one carries the ellipsis)
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
    inserts = []  # (position among the original sentences, sentence); never before the first one
    if lv["question"]:
        inserts.append((1 + _slot(d["q_pos"], n0), 0, QUESTIONS[d["q"]]))
    if lv["weekday"]:
        inserts.append((1 + _slot(d["wd_pos"], n0), 1, WEEKDAY_SENTENCES[d["wd"]].format(d=d["day"])))
    if lv["quote"]:
        inserts.append((1 + _slot(d["qs_pos"], n0), 2, QUOTE_SENTENCES[d["qs"]].format(q=d["qq"].lower())))
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


def _check_topics(topics):
    if len(topics) != 2 or any(t not in TOPICS for t in topics):
        raise ValueError(f"topics must be two known topic names, got {topics!r}")


def _finish(texts, labels, flag_rows):
    flags = {f: np.array([r[f] for r in flag_rows], dtype=np.int64) for f in FEATURES}
    return texts, np.array(labels, dtype=np.int64), flags


def _balance_parents(levels, confound, noise, features, rate, implies=None):
    """Training-only rebalance of nested families (in place). For each child -> parent in IMPLIES whose child
    is confounded and whose parent is not, the parent becomes an independent coin with P(on) = rate for
    both labels (drawn from the parent's own `noise` uniform, which is otherwise unused because the parent
    is not confounded, so no RNG draw is added), and the child is dropped where the parent is off. Then
    P(parent | y) = rate for both labels, and the child (question vs statement) follows the label only
    among notes that have the parent. implies: the calling module's child -> parent map (default: this
    module's IMPLIES); a substrate module with its own families passes its own."""
    if not 0 < rate <= 1:
        raise ValueError(f"parent rate must be in (0, 1], got {rate!r}")
    for child, parent in (IMPLIES if implies is None else implies).items():
        if child in confound and parent not in confound and parent in features:
            levels[parent] = int(noise[features.index(parent)] < rate)
            if not levels[parent]:
                levels[child] = 0
    return levels


def sample_texts(rng, topics, n, cues, confound, topic_noise=0.0, confound_noise=None, balance_parents=None):
    """As textgen.sample_texts; confounded features are protected in the implication step.
    balance_parents: None (default, unchanged behaviour) or a rate r; see _balance_parents()."""
    _check_topics(topics)
    confound_noise = dict(confound_noise or {})
    check_levels({f: 0 for f in confound})
    for f, s in confound.items():
        if s not in (1, -1):
            raise ValueError(f"confound sign for {f!r} must be +1 or -1, got {s!r}")
    for f, p in confound_noise.items():
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
            _balance_parents(levels, confound, noise, FEATURES, balance_parents)
        _imply(levels, protect=set(confound))
        topic = topics[1 - y] if u_topic < topic_noise else topics[y]
        text, flags = render(topic, levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


def sample_grid(rng, topics, n, cues, mains, held_off=()):
    """As textgen.sample_grid; mains and held_off are protected in the implication step."""
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


# ---------------------------------------------------------------- detectors (checks only)

DETECT = {
    "exclamation": lambda t, L: "!" in _body(t, L).replace("#", ""),
    "lowercase": lambda t, L: t == t.lower(),
    "signoff": lambda t, L: any(re.fullmatch(re.escape(c.lower()) + r"[,!]", x.lower()) for c in CLOSINGS
                                for x in L),
    "signoff_excl": lambda t, L: any(re.fullmatch(re.escape(c.lower()) + "!", x.lower()) for c in CLOSINGS
                                     for x in L),
    "ellipsis": lambda t, L: "..." in _body(t, L),
    "emoticon": lambda t, L: any(e.lower() in _body(t, L).lower() for e in EMOTICONS),
    "she_pronoun": lambda t, L: bool(re.search(r"\b(she|her|herself)\b", _body(t, L), re.I)),
    "question": lambda t, L: "?" in _body(t, L),
    "quote": lambda t, L: '"' in _body(t, L),
    "greeting": lambda t, L: any(L[0].lower() == g.format(n=nm).lower() for g in GREETINGS for nm in NAMES),
    "hashtag": lambda t, L: "#" in t,
    "postscript": lambda t, L: L[-1].lower().startswith("p.s."),
    "ps_question": lambda t, L: L[-1].lower().startswith("p.s.") and L[-1].endswith("?"),
    "weekday": lambda t, L: any(w.lower() in t.lower() for w in WEEKDAYS),
    "parenthetical": lambda t, L: "(" in t,
}


def _body(t, L):
    """The paragraph line (the longest line)."""
    return max(L, key=len)


def detect(text):
    L = text.split("\n")
    return {f: int(bool(DETECT[f](text, L))) for f in FEATURES}


# ---------------------------------------------------------------- submission regexes (scripted baselines)

_CLOSE = "|".join(re.escape(c) for c in CLOSINGS)
_BODY = r"(?m)^(?=[^\n]{40,})[^\n]*"  # the paragraph line (every other line is shorter than 40 chars)
SUBMISSION = {
    "exclamation": _BODY + "!",
    "lowercase": r"\A[^A-Z]*\Z",
    "signoff": rf"(?im)^({_CLOSE})[,!]$",
    "signoff_excl": rf"(?im)^({_CLOSE})!$",
    "ellipsis": r"\.\.\.",
    "emoticon": r"(?i)(:\)|:-\)|:D|;\)|:P|\^_\^)",
    "she_pronoun": r"(?i)\b(she|her|herself)\b",
    "question": _BODY + r"\?",
    "quote": '"',
    "greeting": r"(?i)\A(hi|hello|hey|dear|morning)\b[^\n]*,\n",
    "hashtag": "#",
    "postscript": r"(?im)^p\.s\.",
    "ps_question": r"(?im)^p\.s\..*\?$",
    "weekday": "(?i)(" + "|".join(WEEKDAYS) + ")",
    "parenthetical": r"\(",
}


def submission_regex(feature):
    """(pattern, scope) that matches exactly the notes with the feature (checked by freetext_check.py)."""
    return SUBMISSION[feature], "any"
