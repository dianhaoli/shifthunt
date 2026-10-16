"""Knob `heldout`: render notes with cue wordings that no probe's training data, sample or corpus contains.

render_ho(topic, levels, cues, seed, mode) mirrors textgen.render:
  mode None  -> textgen.render exactly (used to check that the grid streams reproduce the stored grids)
  mode "hc"  -> held-out content: same markers ("Hi X,", "#", "P.S. ", "(...)", "?", "Closing,\\nName"),
                new filler words drawn per note from banks disjoint from textgen's banks; British-spelling
                words replaced by new ones (S3 template 0 and all of S4).
  mode "hm"  -> hc plus a new marker where the property admits one: greeting word, bullet marker, P.S.
                prefix, one-line sign-off, two hashtags.
The textgen draw stream (random.Random(seed), _draw) is consumed exactly as in textgen.render, and the
held-out choices come from a separate stream random.Random(f"heldout:{seed}") drawn up front, so flipping
one level still changes only that feature's edit and a note with all cue features off is identical to
textgen's (except S3/S4 template wording in hc/hm, which changes for every note).

grid_ho(rng, topics, n, cues, mains, mode) mirrors textgen.sample_grid's RNG consumption exactly.
"""
import random

import numpy as np

from . import textgen as tg

HO_CLOSINGS = ["Regards", "Yours truly", "Talk soon", "With love", "Thanks again", "Until next time",
               "Catch you later", "Fondly"]
HO_NAMES = ["Robin", "Devon", "Harper", "Parker", "Lennon", "Marley", "Sage", "Rowan", "Blair", "Drew",
            "Elliot", "Phoenix"]
HO_TAGS = ["weekendvibes", "happyplace", "hobbylife", "nofilter", "lovethis", "inspo", "keepgoing",
           "dailyjoy"]
HO_PS = ["Feed the cat for me", "Keep me posted", "Thanks for the book", "See you at the match",
         "Hope the move went well", "Give my best to your mum"]
HO_PAREN = [" (frankly)", " (truly)", " (admittedly)", " (seriously)", " (of course)", " (apparently)"]
HO_QUESTIONS = ["Fancy joining {obj} sometime?", "Have you ever tried it with {obj}?",
                "Why not go along with {obj}?", "Could you see yourself joining {obj}?"]
HM_GREET = ["Hello", "Hey", "Dear", "Morning"]
HM_BULLET = ["* ", "• "]
HM_PS = ["PS: ", "PS - "]

# New British/American pairs; none overlaps textgen.AMERICAN.
HO_AMERICAN = {"catalogue": "catalog", "programme": "program", "jewellery": "jewelry",
               "recognises": "recognizes", "recognised": "recognized", "counsellor": "counselor"}
HO_S3_0 = ("{Poss} counsellor says it is a {adj} way to pass the time",
           "{Poss} counsellor said it was a {adj} way to pass the time")
HO_S4 = [("{P} keeps a catalogue of every outing", "{P} kept a catalogue of every outing"),
         ("{P} follows a programme at the local hall", "{P} followed a programme at the local hall"),
         ("{Poss} jewellery box is full of club badges", "{Poss} jewellery box was full of club badges"),
         ("{P} recognises everyone at the local club", "{P} recognised everyone at the local club")]
assert len(HO_S4) == len(tg.S4)
_HO_AMERICAN_RE = tg.re.compile(r"\b(" + "|".join(HO_AMERICAN) + r")\b")
_ALL_AMERICAN = tg.AMERICAN | HO_AMERICAN
_ALL_AMERICAN_RE = tg.re.compile(r"\b(" + "|".join(_ALL_AMERICAN) + r")\b")

# The held-out banks must be disjoint from everything the generator can produce elsewhere.
assert not set(HO_CLOSINGS) & set(tg.CLOSINGS)
assert not set(HO_NAMES) & set(tg.NAMES)
assert not set(HO_TAGS) & set(tg.TAGS)
assert not set(HO_PS) & set(tg.PS_LINES)
assert not set(HO_AMERICAN) & set(tg.AMERICAN)


def _ho_draw(seed):
    r = random.Random(f"heldout:{seed}")
    return dict(closing=r.choice(HO_CLOSINGS), sname=r.choice(HO_NAMES), gname=r.choice(HO_NAMES),
                tag=r.choice(HO_TAGS), tag2=r.choice(HO_TAGS), ps=r.choice(HO_PS), paren=r.choice(HO_PAREN),
                q=r.choice(HO_QUESTIONS), greet=r.choice(HM_GREET), bullet=r.choice(HM_BULLET),
                psp=r.choice(HM_PS))


def render_ho(topic, levels, cues, seed, mode):
    if mode is None:
        return tg.render(topic, levels, cues, seed)
    if mode not in ("hc", "hm"):
        raise ValueError(f"bad mode {mode!r}")
    lv = tg.check_levels(levels)
    d = tg._draw(random.Random(tg._check_seed(seed)))
    h = _ho_draw(seed)
    bank = tg.TOPICS[topic]
    past, she = lv["past_tense"], lv["she_pronoun"]
    fill = dict(
        P="She" if she else "He", Poss="Her" if she else "His", obj="her" if she else "him",
        act=bank["act"][d["act"]], item=bank["item"][d["item"]], where=bank["where"][d["where"]],
        num=d["num"], adj=d["adj"][lv["negative_sentiment"]], quote=d["quote"], day=d["day"],
        feel=tg.FEEL[past, lv["negative_sentiment"]],
    )

    def sent(template, tail=""):
        t = template[past]
        if not lv["british_spelling"]:
            t = _ALL_AMERICAN_RE.sub(lambda m: _ALL_AMERICAN[m.group(1)], t)
        return [t.format(**fill), tail]

    s3 = HO_S3_0 if d["s3"] == 0 else tg.S3[d["s3"]]
    core = [sent(tg.S1), sent(tg.S2), sent(s3), sent(HO_S4[d["s4"]]), sent(tg.S5)]
    core[d["paren"]][0] += h["paren"] * lv["parenthetical"]
    slots = [core[1], core[2], core[3],
             sent(tg.QUOTE, '"') if lv["quote"] else None,
             sent(tg.WEEKDAY) if lv["weekday"] else None]
    middle = [slots[k] for k in d["order"] if slots[k] is not None]

    stop = "!" if lv["exclamation"] else "."
    sentences = [c + stop + tail for c, tail in [core[0], *middle, core[4]]]
    if lv["question_ending"]:
        sentences.append(h["q"].format(obj=fill["obj"]))
    else:
        sentences.append(f"You should try it with {fill['obj']}{stop}")

    hm = mode == "hm"
    lines = []
    if lv["greeting"]:
        lines.append(f"{h['greet'] if hm else 'Hi'} {h['gname']},")
    if lv["bullet_list"]:
        lines += [(h["bullet"] if hm else "- ") + s for s in sentences]
    else:
        lines.append(" ".join(sentences))
    if lv["hashtag"]:
        lines.append(f"#{h['tag']} #{h['tag2']}" if hm else "#" + h["tag"])
    if lv["signoff"]:
        lines += [f"{h['closing']}, {h['sname']}"] if hm else [h["closing"] + ",", h["sname"]]
    if lv["postscript"]:
        lines.append(f"{h['psp'] if hm else 'P.S. '}{h['ps']}{stop}")
    text = "\n".join(lines)
    if lv["lowercase"]:
        text = text.lower()
    return text, lv


def grid_ho(rng, topics, n, cues, mains, mode):
    """textgen.sample_grid with render_ho; identical RNG consumption (no held_off)."""
    mains = list(mains)
    cell = 2 * 2 ** len(mains)
    if n % cell:
        raise ValueError(f"n={n} must be a multiple of {cell}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        coins = [rng.random() < 0.5 for _ in tg.FEATURES]
        seed = rng.getrandbits(32)
        levels = {f: int(c) for f, c in zip(tg.FEATURES, coins)}
        for j, f in enumerate(mains):
            levels[f] = ((i // 2) >> j) & 1
        text, flags = render_ho(topics[y], levels, cues, seed, mode)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return tg._finish(texts, labels, rows)


# ---------------------------------------------------------------- regexes per cue: (pattern, scope)

def literal_regex(cue, cues):
    """What an agent that copies the sample's wordings would write (sample = the probe's cue strings and
    the generator's per-note banks). None where the literal regex is the shipped detector."""
    esc = tg.re.escape
    return {
        "signoff": (rf"(?im)^{esc(cues.closing)},$", "any"),
        "greeting": (rf"(?i)^hi {esc(cues.greeting_name)},$", "first_line"),
        "hashtag": (rf"(?i)#{esc(cues.hashtag)}\b", "any"),
        "postscript": (r"(?i)p\.s\. (" + "|".join(esc(s) for s in tg.PS_LINES) + ")", "any"),
        "parenthetical": (r"(?i)\(honestly\)", "any"),
        "question_ending": (r"(?i)would you try it with (him|her)\?", "any"),
    }.get(cue)


STRUCTURAL = {
    "signoff": (r"(?im)^[a-z][a-z ]{1,25},(\n| )[a-z]+$", "any"),
    "greeting": (r"(?i)^\w+ \w+,$", "first_line"),
    "hashtag": (r"#\w", "any"),
    "postscript": (r"(?i)^p\.?\s?s\b", "last_line"),
    "parenthetical": (r"\(", "any"),
    "question_ending": (r"\?", "any"),
    "bullet_list": (r"(?m)^\s*([-*•]|\d+\.) ", "any"),
    "british_spelling": (r"(?i)\b(\w+(?<![fyh])our(s|ite|ed)?|\w+is(e|es|ed|ing)|\w+(?<!s)tre|\w+ogue|\w+amme"
                         r"|jewellery|grey)\b", "any"),
}


def regex_match(pattern, scope, texts):
    rx = tg.re.compile(pattern)
    out = []
    for t in texts:
        if scope == "first_line":
            t = t.split("\n", 1)[0]
        elif scope == "last_line":
            t = t.rsplit("\n", 1)[-1]
        out.append(rx.search(t) is not None)
    return np.array(out)


def ba(pred, truth):
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    raw = 0.5 * (pred[truth].mean() + (~pred[~truth]).mean())
    return float(max(raw, 1 - raw))
