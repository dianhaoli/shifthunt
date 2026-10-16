"""Templated hobby notes with independently switchable surface features.

A note is a few short sentences about one hobby (the topic) plus optional
features (cues). Every feature is a binary level that is ground truth by
construction; detectors.py only checks it.

render(topic, levels, cues, seed) contract:
  * All random choices (topic phrase indices, templates, both adjectives of the
    sentiment pair, quote, weekday, P.S. line, parenthetical target, sentence
    order) are drawn up front from random.Random(seed) in a fixed order that
    does not depend on levels or topic. Levels only select among the drawn
    options, so flipping one feature changes only that feature's edit, and
    swapping the topic changes only the topic phrases.
  * Topic banks have equal sizes across topics for the same reason.
  * Layout, top to bottom: [greeting] / body / [#hashtag] / [closing, name] /
    [P.S. line]. The body is one line, or one "- " line per sentence.
  * Body order: S1 first, then the shuffled middle (S2 own, S3 opinion,
    S4 detail, [quote], [weekday]) using one permutation drawn over all five
    slots with absent ones filtered out, then S5 feel, then the close.

Per-probe cue strings (closing, names, hashtag word) come from make_cues, so a
probe's sample shares one set of cue strings.
"""

import operator
import random
import re
from dataclasses import dataclass

import numpy as np

TOPICS = {
    "gardening": {
        "act": ["growing tomatoes", "planting bulbs", "pruning roses", "weeding the beds"],
        "item": ["seed packets", "seed trays", "garden trowels", "watering cans"],
        "where": ["the allotment", "the greenhouse", "the community garden"],
    },
    "astronomy": {
        "act": ["chasing meteor showers", "mapping star clusters", "tracking the planets", "sketching lunar craters"],
        "item": ["telescopes", "star charts", "eyepieces", "star atlases"],
        "where": ["the observatory", "the star party", "the planetarium"],
    },
    "cooking": {
        "act": ["baking bread", "making soup", "roasting vegetables", "rolling fresh pasta"],
        "item": ["cast iron pans", "cookbooks", "chef knives", "wooden spoons"],
        "where": ["the kitchen", "the cooking school", "the market stall"],
    },
    "cycling": {
        "act": ["riding country lanes", "climbing steep hills", "fixing punctures", "touring the countryside"],
        "item": ["bike helmets", "spare inner tubes", "cycling jerseys", "bike pumps"],
        "where": ["the bike rally", "the bike shop", "the cycle cafe"],
    },
    "chess": {
        "act": ["studying openings", "solving chess puzzles", "playing blitz games", "reviewing endgames"],
        "item": ["chess sets", "chess clocks", "strategy books", "opening manuals"],
        "where": ["the chess hall", "the library", "the coffee house"],
    },
    "fishing": {
        "act": ["casting for trout", "tying flies", "fishing for carp", "reeling in pike"],
        "item": ["fishing rods", "tackle boxes", "fishing reels", "wading boots"],
        "where": ["the lake", "the river bank", "the reservoir"],
    },
    "knitting": {
        "act": ["knitting scarves", "crocheting woolly hats", "following lace patterns", "finishing blankets"],
        "item": ["knitting needles", "balls of yarn", "wool skeins", "stitch markers"],
        "where": ["the yarn store", "the craft circle", "the craft fair"],
    },
    "photography": {
        "act": ["shooting landscapes", "taking portraits", "editing photos", "capturing city lights"],
        "item": ["camera lenses", "memory cards", "flash units", "camera bags"],
        "where": ["the darkroom", "the photo society", "the photo lab"],
    },
    "running": {
        "act": ["running long trails", "doing hill sprints", "training for marathons", "jogging by the canal"],
        "item": ["running shoes", "sports watches", "energy gels", "water bottles"],
        "where": ["the athletics track", "the race meet", "the stadium"],
    },
    "birdwatching": {
        "act": ["spotting warblers", "counting geese", "observing owls", "listening for songbirds"],
        "item": ["binoculars", "field guides", "bird feeders", "spotting scopes"],
        "where": ["the nature reserve", "the estuary", "the wetland hide"],
    },
    "pottery": {
        "act": ["throwing pots", "glazing bowls", "shaping clay vases", "trimming mugs"],
        "item": ["pottery wheels", "blocks of clay", "glaze jars", "carving tools"],
        "where": ["the pottery studio", "the kiln shed", "the ceramics class"],
    },
    "sailing": {
        "act": ["sailing dinghies", "racing yachts", "learning knots", "navigating the coast"],
        "item": ["life jackets", "sailing ropes", "compasses", "sailing gloves"],
        "where": ["the marina", "the yacht club", "the bay"],
    },
}
TOPIC_NAMES = list(TOPICS)

FEATURES = (
    "exclamation", "lowercase", "signoff", "british_spelling", "bullet_list",
    "past_tense", "she_pronoun", "question_ending", "quote", "greeting",
    "hashtag", "postscript", "weekday", "parenthetical", "negative_sentiment",
)

# Cue banks (per probe).
CLOSINGS = ["Cheers", "Best wishes", "Warm regards", "Kind regards",
            "Take care", "All the best", "Many thanks", "Speak soon"]
NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Riley", "Morgan", "Jamie",
         "Quinn", "Avery", "Kim", "Jesse", "Charlie", "Frankie", "Ellis", "Hayden",
         "Reese", "Skyler", "Kai", "Remy", "Rory", "Dana", "Emery", "Finley",
         "Toni", "Jules", "Ashley", "Shay", "Billie", "Sasha"]
TAGS = ["goodtimes", "positivity", "goodvibes", "metime", "mood", "goals", "smallwins",
        "blessed", "staycurious", "selfcare", "slowliving", "simplejoys",
        "mindful", "newthings", "takeabreak"]

# Feature banks (per note).
NUMBERS = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
ADJ_PAIRS = [("relaxing", "stressful"), ("wonderful", "dreadful"),
             ("rewarding", "frustrating"), ("calming", "tiresome"),
             ("pleasant", "miserable"), ("satisfying", "tedious")]
QUOTES = ["Patience pays off", "Small steps add up", "Keep it simple",
          "Enjoy the process", "Little by little", "Trust the process"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PS_LINES = ["Say hello to everyone", "Call me later", "I owe you lunch",
            "Write back soon", "Bring an umbrella next time", "Let me know your plans"]
PAREN = " (honestly)"

# (present, past) templates. Written in British spelling; AMERICAN maps back.
S1 = ("{P} spends most weekends {act} at {where}", "{P} spent most weekends {act} at {where}")
S2 = ("{P} owns {num} {item} and keeps buying more", "{P} owned {num} {item} and kept buying more")
S3 = [("{Poss} neighbour says it is a {adj} way to pass the time",
       "{Poss} neighbour said it was a {adj} way to pass the time"),
      ("{Poss} friends think it is {adj}", "{Poss} friends thought it was {adj}"),
      ("{Poss} family finds it {adj}", "{Poss} family found it {adj}")]
# Every S4 template has a spelling-variant word, so british_spelling always edits the note.
S4 = [("{P} organises meetups at the local centre", "{P} organised meetups at the local centre"),
      ("{Poss} favourite colour is grey", "{Poss} favourite colour was grey"),
      ("{P} practises with a neighbour most evenings", "{P} practised with a neighbour most evenings"),
      ("{P} often meets friends at the theatre in town", "{P} often met friends at the theatre in town")]
S5 = ("{P} {feel} every minute of it", "{P} {feel} every minute of it")
FEEL = {(0, 0): "loves", (0, 1): "hates", (1, 0): "loved", (1, 1): "hated"}  # (past, negative)
QUOTE = ('{Poss} coach always says, "{quote}', '{Poss} coach always said, "{quote}')
WEEKDAY = ("{P} goes again on {day}", "{P} went again on {day}")

AMERICAN = {"neighbour": "neighbor", "favourite": "favorite", "colour": "color",
            "centre": "center", "grey": "gray", "organises": "organizes",
            "organised": "organized", "practises": "practices", "practised": "practiced",
            "theatre": "theater"}
_AMERICAN_RE = re.compile(r"\b(" + "|".join(AMERICAN) + r")\b")


@dataclass(frozen=True)
class Cues:
    closing: str
    signoff_name: str
    greeting_name: str
    hashtag: str


def make_cues(rng: random.Random) -> Cues:
    signoff_name, greeting_name = rng.sample(NAMES, 2)
    return Cues(closing=rng.choice(CLOSINGS), signoff_name=signoff_name,
                greeting_name=greeting_name, hashtag=rng.choice(TAGS))


def check_levels(levels):
    """Full {feature: 0/1} dict from a partial one; rejects unknown names and levels."""
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


def _draw(rng):
    """Every random choice of a note, in a fixed order independent of levels and topic."""
    return dict(
        act=rng.randrange(4), item=rng.randrange(4), where=rng.randrange(3),
        num=rng.choice(NUMBERS), s3=rng.randrange(len(S3)), adj=rng.choice(ADJ_PAIRS),
        s4=rng.randrange(len(S4)), quote=rng.choice(QUOTES), day=rng.choice(WEEKDAYS),
        ps=rng.choice(PS_LINES),
        paren=rng.randrange(5),             # index into S1..S5, which are always present
        order=rng.sample(range(5), 5),      # over middle slots S2, S3, S4, quote, weekday
    )


def _check_seed(seed):
    """Seeds are str or non-negative int (numpy ints ok). None would be nondeterministic, and
    random.Random(-n) == random.Random(n), so both are rejected."""
    if isinstance(seed, str):
        return seed
    if seed is None or isinstance(seed, bool):
        raise TypeError(f"seed must be a str or non-negative int, got {seed!r}")
    seed = operator.index(seed)
    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")
    return seed


def render(topic, levels, cues, seed):
    """Return (text, flags) for one note; flags has all 15 features."""
    if topic not in TOPICS:
        raise ValueError(f"unknown topic {topic!r}")
    lv = check_levels(levels)
    d = _draw(random.Random(_check_seed(seed)))
    bank = TOPICS[topic]
    past = lv["past_tense"]
    she = lv["she_pronoun"]
    fill = dict(
        P="She" if she else "He", Poss="Her" if she else "His", obj="her" if she else "him",
        act=bank["act"][d["act"]], item=bank["item"][d["item"]], where=bank["where"][d["where"]],
        num=d["num"], adj=d["adj"][lv["negative_sentiment"]], quote=d["quote"], day=d["day"],
        feel=FEEL[past, lv["negative_sentiment"]],
    )

    def sent(template, tail=""):
        t = template[past]
        if not lv["british_spelling"]:
            t = _AMERICAN_RE.sub(lambda m: AMERICAN[m.group(1)], t)
        return [t.format(**fill), tail]   # [core, tail]; end mark goes between them

    core = [sent(S1), sent(S2), sent(S3[d["s3"]]), sent(S4[d["s4"]]), sent(S5)]
    core[d["paren"]][0] += PAREN * lv["parenthetical"]
    slots = [core[1], core[2], core[3],
             sent(QUOTE, '"') if lv["quote"] else None,
             sent(WEEKDAY) if lv["weekday"] else None]
    middle = [slots[k] for k in d["order"] if slots[k] is not None]

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
    return text, lv


def _check_topics(topics):
    if len(topics) != 2 or any(t not in TOPICS for t in topics):
        raise ValueError(f"topics must be two known topic names, got {topics!r}")


def _finish(texts, labels, flag_rows):
    flags = {f: np.array([r[f] for r in flag_rows], dtype=np.int64) for f in FEATURES}
    return texts, np.array(labels, dtype=np.int64), flags


def sample_texts(rng, topics, n, cues, confound, topic_noise=0.0, confound_noise=None):
    """Labeled notes where each feature in `confound` tracks the label y = i % 2.

    confound: {feature: +1 (on when y == 1) or -1 (on when y == 0)}, each flipped
    with probability confound_noise.get(feature, 0). Other features are fair coins.
    The topic is topics[y], flipped with probability topic_noise; the label stays y.
    Each text draws the same random numbers whatever the confound config, so
    changing it does not reshuffle unrelated randomness.
    """
    _check_topics(topics)
    confound_noise = dict(confound_noise or {})
    check_levels({f: 0 for f in confound})
    for f, s in confound.items():
        if s not in (1, -1):
            raise ValueError(f"confound sign for {f!r} must be +1 or -1, got {s!r}")
    for f, p in confound_noise.items():
        if f not in confound:
            raise ValueError(f"confound_noise for unconfounded feature {f!r}")
        if not 0 <= p <= 1:
            raise ValueError(f"noise for {f!r} must be in [0, 1], got {p!r}")
    if not 0 <= topic_noise <= 1:
        raise ValueError(f"topic_noise must be in [0, 1], got {topic_noise!r}")

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
        topic = topics[1 - y] if u_topic < topic_noise else topics[y]
        text, flags = render(topic, levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)


def sample_grid(rng, topics, n, cues, mains, held_off=()):
    """Balanced grid: topic y = i % 2 crossed with every level combination of `mains`.

    Main j's level is ((i // 2) >> j) & 1, held_off features are forced to 0 and the
    rest are fair coins. n must be a multiple of 2 * 2**len(mains). Labels = topic index.
    """
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
        text, flags = render(topics[y], levels, cues, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(texts, labels, rows)
