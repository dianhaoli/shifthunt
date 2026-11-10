"""Exp F generator: the Exp D free-text generator (shifthunt.freetext_listing) plus the new cues of Exp F.

Text only (never used with probes). freetext.py and freetext_listing.py are imported, never edited: a note is
first rendered by freetext_listing.render_parts with the 20 Exp D properties, then this module's edits rewrite
the greeting line and the P.S. line (and may move the P.S. line), so in the "base" profile a note is exactly
the freetext_listing note.

PROFILES. Each generated cue lives in one profile: the 20 Exp D properties (all of them vary in every profile,
as in Exp D) plus only the new flags that cue needs, so the background of a cue that Exp D also tested is the
Exp D background. New flags (each a fair coin in its profile, then nesting):

  greet_question  (child of greeting)    the greeting line asks a question. Profile "gq": every greeting line is
                  "<greeting> <wish>. <reply>" and the cue makes it "<greeting> <wish>? <reply>" with the SAME
                  words ("Hi Sam, hope you are well? All good here." vs "Hi Sam, hope you are well. All good
                  here."): only the mark differs, it stands inside the first line and never ends a line.
                  Rejected versions (VALIDATION.md): "gq_v1" "<greeting>" -> "<greeting> how are you?" (the
                  "?" ends a line); "gq_v2" "<greeting> hope all is well." -> "<greeting> how are you? Hope all
                  is well." (the words "how are you" and the extra sentence carry the cue without the "?").
  ps_exclaim      (child of postscript)  "!" in the P.S. line. Profile "px": every P.S. line starts "P.S. Oh,"
                  and the cue makes it "P.S. Oh! ..."; the body's own exclamation property keeps varying, and
                  question and statement P.S. lines can both carry it.
                  (Rejected version "px_v1": the statement P.S. ends in "!" instead of ".".)
  greet_informal  (child of greeting)    the greeting is an informal form. Profile "fi" replaces freetext's 8
                  greeting forms by FORMAL / INFORMAL pairs (same draw index): Hello / Dear / Good morning /
                  Good evening ... vs Hey / Hiya / Hey there / Yo ...
  ps_named        (child of postscript)  the P.S. addresses the recipient by name: "P.S. Sam, are you free next
                  week?". The recipient is the greeting's name draw (freetext's gname), shown in the greeting
                  when the note has a named greeting form. Profile "pn".
  ps_qx_child     (child of ps_question) REJECTED versions of ps_q_excl only (profiles "pqx_v1": "?" -> "?!";
                  "pqx_v2": the "Oh!" of "px" only on question P.S. lines, so "!" in the P.S. alone was the cue).
  ps_first        (child of postscript AND signoff) the P.S. line stands before the sign-off lines. Profile "pf".

DERIVED cues (two conditions together; not generator flags, a function of two flags):
  informal_lower  = greet_informal AND lowercase (profile "fi")
  ps_q_named      = ps_question AND ps_named      (profile "pn")
  ps_q_excl       = ps_question AND ps_exclaim    (profile "pqx" = "px" + this derived cue: "P.S. Oh! Are you
                    free next week?"; within P.S. lines question-ness and the "Oh!" vary independently)

Nesting (imply): a protected child that is on switches every ancestor on (a protected ancestor that is off is
an error); exclusive pairs (ps_tentative / ps_question always; ps_exclaim / ps_question in px_v1): a protected
member wins, otherwise ps_question wins; then an unprotected child with an ancestor off is dropped, to a fixed
point. Flags are the levels after these steps, i.e. what the text shows; detect(text, profile) agrees with them.

Random streams: freetext's own draws (freetext._draw(Random(seed))) and freetext_listing's second stream are
untouched; this module's choices come from Random(f"listingF:{seed}") and its coins from
Random(f"listingF:levels:{seed}"), both drawn in a fixed order whatever the profile.

ALIGNED SET (draw_aligned) follows the bank's rule with stated deviations: shifthunt/episode_files.py:186-214
(_conf) draws an episode's decoys by systematic PPS (_pps, :153-175) with weights = the number of valid planted
artifacts per cue in the pool, and every sign with P(-1) = the pool's share of negative training signs; a nested
parent takes its aligned child's sign (:200-213). POOL_WEIGHTS and P_NEG are that pool for the shipped free-text
episodes (valid planted artifacts of ft_screen and ft_tp2_r90a: with them, _conf reproduces the stored aligned
sets and signs of the shipped free-text episodes exactly). Deviations: the target is fixed (in the bank the mains
come from the probes and are never decoys); the 7 others are a PPS draw among the weighted properties that are
not ancestors, descendants or components of the target and not exclusive with it; a draw with a parent-child or
exclusive pair among the 8 is rejected and redrawn from the same stream (no bank episode has aligned such a
pair, :203); then the signs of all 8.

MARKS. Two properties share a mark when a position-free regex for one ("?" or "!" anywhere) also detects the
other; a negative-control property must not share a mark with an aligned one (MARK_GROUPS).
"""
import random
import re
from dataclasses import dataclass

import numpy as np

from . import freetext as ft
from . import freetext_listing as fl
from .episode_files import _pps

NAMES = list(ft.NAMES)
BASE = tuple(fl.FEATURES)
NEW = ("greet_question", "ps_exclaim", "greet_informal", "ps_named", "ps_qx_child", "ps_first")
PARENTS = {**{c: (p,) for c, p in fl.IMPLIES.items()},
           "greet_question": ("greeting",), "greet_informal": ("greeting",), "ps_exclaim": ("postscript",),
           "ps_named": ("postscript",), "ps_qx_child": ("ps_question",), "ps_first": ("postscript", "signoff")}
DERIVED = {"informal_lower": ("greet_informal", "lowercase"), "ps_q_named": ("ps_question", "ps_named"),
           "ps_q_excl": ("ps_question", "ps_exclaim")}
# Properties whose text carries the same mark: a position-free regex for the mark detects each of them.
MARK_GROUPS = {"?": ("question", "ps_question", "greet_question", "ps_q_named", "ps_q_excl", "ps_qx_child",
                     "question_ending"),
               "!": ("exclamation", "signoff_excl", "ps_exclaim", "ps_q_excl", "ps_qx_child")}

FORMAL = ["Hello {n},", "Dear {n},", "Good morning {n},", "Good evening {n},", "Hello all,", "Dear all,",
          "Good morning all,", "Hello everyone,"]
INFORMAL = ["Hey {n},", "Hiya {n},", "Hey there {n},", "Yo {n},", "Hey all,", "Hiya all,", "Hey everyone,",
            "Hey folks,"]
GREET_WISHES = ["hope you are well", "hope all is well", "hope things are good", "hope the week is going well"]
GREET_REPLIES = ["All good here.", "All fine here."]
GREET_QUESTIONS = ["how are you?", "how have you been?", "how are things?", "how is it going?"]   # gq_v1, gq_v2
GREET_FOLLOW = ["hope all is well.", "hope you are well."]                                        # gq_v2
assert len(FORMAL) == len(INFORMAL) == len(ft.GREETINGS)
assert len(GREET_WISHES) == len(GREET_QUESTIONS) and len(GREET_REPLIES) == len(GREET_FOLLOW)

# Pool of the shipped free-text episodes (see the module text): valid planted artifacts per cue, and the share
# of negative training signs among them (18 of 39).
POOL_WEIGHTS = {"lowercase": 3, "signoff": 3, "emoticon": 1, "she_pronoun": 3, "question": 3, "quote": 2,
                "greeting": 3, "hashtag": 3, "postscript": 3, "ps_question": 9, "weekday": 3, "parenthetical": 3}
P_NEG = 18 / 39
N_ALIGNED = 8
MAX_REDRAWS = 1000


@dataclass(frozen=True)
class Profile:
    name: str
    flags: tuple = ()      # active new flags
    greet: str = "ft"      # "ft": freetext.GREETINGS; "fi": FORMAL / INFORMAL
    greet_q: str = ""      # "", "same" (admitted greet_question), "end" (rejected v1), "follow" (rejected v2)
    ps: str = ""           # "", "oh" (admitted ps_exclaim / ps_q_excl), "end" (px_v1), "qend" (pqx_v1),
                           # "oh_q" (pqx_v2)
    derived: tuple = ()

    @property
    def features(self):
        return BASE + tuple(self.flags)

    @property
    def scored(self):
        return self.features + tuple(self.derived)

    @property
    def exclusive(self):
        """(loser by default, winner by default) pairs."""
        return (("ps_tentative", "ps_question"),) + ((("ps_exclaim", "ps_question"),) if self.ps == "end" else ())


PROFILES = {p.name: p for p in (
    Profile("base"),
    Profile("gq", ("greet_question",), greet_q="same"),
    Profile("gq_v1", ("greet_question",), greet_q="end"),
    Profile("gq_v2", ("greet_question",), greet_q="follow"),
    Profile("px", ("ps_exclaim",), ps="oh"),
    Profile("px_v1", ("ps_exclaim",), ps="end"),
    Profile("fi", ("greet_informal",), greet="fi", derived=("informal_lower",)),
    Profile("pn", ("ps_named",), derived=("ps_q_named",)),
    Profile("pqx", ("ps_exclaim",), ps="oh", derived=("ps_q_excl",)),
    Profile("pqx_v1", ("ps_qx_child",), ps="qend"),
    Profile("pqx_v2", ("ps_qx_child",), ps="oh_q"),
    Profile("pf", ("ps_first",)),
)}


def profile_of(p):
    return p if isinstance(p, Profile) else PROFILES[p]


# ---------------------------------------------------------------- nesting

def ancestors(prop):
    """Every ancestor of a flag (transitive); for a derived cue, those of its components."""
    if prop in DERIVED:
        return set().union(*(ancestors(c) for c in DERIVED[prop]))
    out, todo = set(), list(PARENTS.get(prop, ()))
    while todo:
        p = todo.pop()
        if p not in out:
            out.add(p)
            todo += PARENTS.get(p, ())
    return out


def descendants(prop, profile="base"):
    feats = profile_of(profile).features
    return {f for f in feats if prop in ancestors(f)}


def components(prop):
    return set(DERIVED.get(prop, ()))


def exclusive_with(prop, profile="base"):
    out = set()
    for a, b in profile_of(profile).exclusive:
        if prop == a:
            out.add(b)
        elif prop == b:
            out.add(a)
    return out


def shares_mark(prop):
    """The properties that carry the same mark as prop (MARK_GROUPS), prop excluded."""
    return {q for group in MARK_GROUPS.values() if prop in group for q in group} - {prop}


def related(prop, profile="base"):
    """The property itself, its components, and every ancestor and descendant of either."""
    core = {prop} | components(prop)
    out = set(core)
    for c in core:
        out |= ancestors(c) | descendants(c, profile)
    return out


def check_levels(levels, profile="base"):
    prof = profile_of(profile)
    bad = set(levels) - set(prof.features)
    if bad:
        raise ValueError(f"unknown features for profile {prof.name}: {sorted(bad)}")
    out = {}
    for f in prof.features:
        v = levels.get(f, 0)
        if v not in (0, 1):
            raise ValueError(f"level for {f!r} must be 0 or 1, got {v!r}")
        out[f] = int(v)
    return out


def imply(levels, profile="base", protect=()):
    """Enforce nesting and exclusions in place (see the module text). -> levels."""
    prof, protect = profile_of(profile), set(protect)
    feats = prof.features
    for child in feats:
        if child in protect and levels[child]:
            for a in ancestors(child):
                if not levels[a]:
                    if a in protect:
                        raise ValueError(f"{child}=1 needs {a}=1 but both are fixed")
                    levels[a] = 1
    for loser, winner in prof.exclusive:
        if levels.get(loser) and levels.get(winner):
            if loser in protect and winner in protect:
                raise ValueError(f"{loser}=1 and {winner}=1 exclude each other but both are fixed")
            levels[winner if loser in protect else loser] = 0
    changed = True
    while changed:
        changed = False
        for child in feats:
            if levels[child] and any(not levels[p] for p in PARENTS.get(child, ())):
                if child in protect:
                    raise ValueError(f"{child}=1 is fixed but a parent is off")
                levels[child] = 0
                changed = True
    return levels


# ---------------------------------------------------------------- render

def _draw_f(seed):
    rng = random.Random(f"listingF:{fl._check_seed(seed)}")
    return {"gq": rng.randrange(len(GREET_QUESTIONS)), "follow": rng.randrange(len(GREET_FOLLOW))}


def _new_coins(seed):
    rng = random.Random(f"listingF:levels:{seed}")
    return {f: int(rng.random() < 0.5) for f in NEW}


def _decap(s):
    return s if s.split(" ", 1)[0] == "I" else s[0].lower() + s[1:]


def greeting_line(prof, lv, d, x):
    forms = ft.GREETINGS if prof.greet == "ft" else (INFORMAL if lv.get("greet_informal") else FORMAL)
    g = forms[d["greet"]].format(n=d["gname"])
    if prof.greet_q == "same":
        wish, reply = GREET_WISHES[x["gq"]], GREET_REPLIES[x["follow"]]
        return f"{g} {wish}{'?' if lv.get('greet_question') else '.'} {reply}"
    if prof.greet_q == "follow":
        follow = GREET_FOLLOW[x["follow"]]
        if lv.get("greet_question"):
            return f"{g} {GREET_QUESTIONS[x['gq']]} {follow[0].upper()}{follow[1:]}"
        return f"{g} {follow}"
    if prof.greet_q == "end" and lv.get("greet_question"):
        return f"{g} {GREET_QUESTIONS[x['gq']]}"
    return g


def ps_line(prof, lv, d):
    full = (ft.PS_QUESTIONS[d["psq"]] if lv["ps_question"] else
            fl.PS_TENTATIVE[d["ps"]] if lv["ps_tentative"] else ft.PS_STATEMENTS[d["ps"]])
    rest = full[len("P.S. "):]
    if prof.ps in ("oh", "oh_q"):
        bang = lv.get("ps_exclaim") if prof.ps == "oh" else lv.get("ps_qx_child")
        rest = "Oh! " + rest if bang else "Oh, " + _decap(rest)
    elif prof.ps == "end" and lv.get("ps_exclaim"):
        rest = rest[:-1] + "!"
    elif prof.ps == "qend" and lv.get("ps_qx_child"):
        rest = rest + "!"
    if lv.get("ps_named"):
        rest = d["gname"] + ", " + _decap(rest)
    return "P.S. " + rest


def render(topic, levels, profile="base", seed=0):
    """-> (text, flags) for one note of a profile. Flags are the levels after imply() with no protection."""
    prof = profile_of(profile)
    lv = imply(check_levels(levels, prof), prof)
    base = {f: lv[f] for f in BASE}
    text, got, _ = fl.render_parts(topic, base, None, seed)
    if got != base:
        raise AssertionError("freetext_listing changed levels that imply() had already made consistent")
    if prof.name == "base":
        return text, lv
    d = ft._draw(random.Random(fl._check_seed(seed)), len(ft.bank()[topic]))
    x = _draw_f(seed)
    low = str.lower if lv["lowercase"] else (lambda s: s)
    lines = text.split("\n")
    if lv["greeting"]:
        lines[0] = low(greeting_line(prof, lv, d, x))
    if lv["postscript"]:
        lines[-1] = low(ps_line(prof, lv, d))
        if lv.get("ps_first"):
            ps = lines.pop()
            lines.insert(len(lines) - 2, ps)  # before the closing line and the name line
    return "\n".join(lines), lv


# ---------------------------------------------------------------- detectors

_PS_NAMED = re.compile(r"p\.s\. (" + "|".join(n.lower() for n in NAMES) + r"), ")
_GREET_CACHE = {}


def _greet_lines(prof):
    """{"all", "question", "informal"}: every greeting line the profile can render, lower-cased."""
    if prof.name in _GREET_CACHE:
        return _GREET_CACHE[prof.name]
    out = {"all": set(), "question": set(), "informal": set()}
    draws = [{"gq": a, "follow": b} for a in range(len(GREET_QUESTIONS)) for b in range(len(GREET_FOLLOW))]
    for k in range(len(ft.GREETINGS)):
        for informal in ((0,) if prof.greet == "ft" else (0, 1)):
            for name in NAMES:
                for gq in ((0, 1) if prof.greet_q else (0,)):
                    for x in draws:
                        line = greeting_line(prof, {"greet_informal": informal, "greet_question": gq},
                                             {"greet": k, "gname": name}, x).lower()
                        out["all"].add(line)
                        if gq:
                            out["question"].add(line)
                        if informal:
                            out["informal"].add(line)
    _GREET_CACHE[prof.name] = out
    return out


def detect(text, profile="base"):
    """{property: 0/1} over the profile's features and derived cues, from the text alone."""
    prof = profile_of(profile)
    lines = text.split("\n")
    out = ft.detect(text)
    out.update({f: int(bool(fl.DETECT_NEW[f](text))) for f in fl.NEW})
    ps = [line for line in lines if line.lower().startswith("p.s.")]
    if len(ps) > 1:
        raise ValueError("a note with two P.S. lines")
    psl = ps[0] if ps else None
    low = psl.lower() if psl else ""
    out["postscript"] = int(psl is not None)
    out["ps_question"] = int(psl is not None and psl.rstrip("!").endswith("?"))
    out["ps_tentative"] = int(psl is not None and not psl.rstrip("!").endswith("?")
                              and bool(fl._HEDGE_RE.search(psl)))
    greet = _greet_lines(prof)
    first = lines[0].lower()
    out["greeting"] = int(first in greet["all"])
    if "greet_question" in prof.flags:
        out["greet_question"] = int(first in greet["question"])
    if "greet_informal" in prof.flags:
        out["greet_informal"] = int(first in greet["informal"])
    if "ps_exclaim" in prof.flags:
        out["ps_exclaim"] = int(low.startswith("p.s. oh!") if prof.ps == "oh" else
                                (psl is not None and psl.endswith("!") and not psl.endswith("?!")))
    if "ps_qx_child" in prof.flags:
        out["ps_qx_child"] = int(low.startswith("p.s. oh!") if prof.ps == "oh_q" else
                                 (psl is not None and psl.endswith("?!")))
    if "ps_named" in prof.flags:
        out["ps_named"] = int(bool(_PS_NAMED.match(low)))
    if "ps_first" in prof.flags:
        out["ps_first"] = int(psl is not None and lines[-1] != psl)
    for name, (a, b) in DERIVED.items():
        if name in prof.derived:
            out[name] = int(out[a] and out[b])
    return {f: out[f] for f in prof.scored}


def derive(flags, profile="base"):
    """Add the profile's derived cues to a {flag: array} dict (in place). -> flags."""
    prof = profile_of(profile)
    for name in prof.derived:
        a, b = DERIVED[name]
        flags[name] = (np.asarray(flags[a]).astype(bool) & np.asarray(flags[b]).astype(bool)).astype(np.int64)
    return flags


# ---------------------------------------------------------------- notes

def _levels(rng, prof):
    """One note's fair coins in freetext_listing.sample_grid's order (15 from rng, then the note seed; the 5
    Exp D coins and this module's coins from the seed's own streams)."""
    coins = [rng.random() < 0.5 for _ in ft.FEATURES]
    seed = rng.getrandbits(32)
    lv = {f: int(c) for f, c in zip(ft.FEATURES, coins)}
    lv.update(fl._new_coins(seed))
    nc = _new_coins(seed)
    lv.update({f: nc[f] for f in prof.flags})
    return lv, seed


def _finish(prof, texts, labels, rows):
    flags = {f: np.array([r[f] for r in rows], dtype=np.int64) for f in prof.features}
    return texts, np.array(labels, dtype=np.int64), derive(flags, prof)


def _target_class(sign):
    return 1 if sign > 0 else 0


# The non-target class of a sample whose target is a derived cue: 64 notes = 28 with component A only, 28 with
# component B only, 8 with neither (each component alone is present in 28/64 of that class: sample BA 0.78).
DERIVED_CELLS = (("A", 28), ("B", 28), ("N", 8))


def sample_aligned(rng, topics, n, profile, conf, target=None):
    """n notes, labels alternating 0/1 (label = topic index; shuffle them yourself).
    conf = {flag: +1|-1}: on exactly in the label-1 (+1) or label-0 (-1) notes, protected. target: a derived
    cue (with its sign in conf) or None. For a derived target, its class has both components on; the other class
    gets the cells of DERIVED_CELLS in an order drawn from rng before the notes; components are protected and
    a component's ancestors are switched on with it (a cell without a component leaves them coins).
    Every other property is a fair coin, then nesting. -> (texts, labels, flags incl. derived)."""
    prof = profile_of(profile)
    fl._check_topics(topics)
    conf = dict(conf)
    flag_conf = {f: s for f, s in conf.items() if f not in DERIVED}
    check_levels({f: 0 for f in flag_conf}, prof)
    cells = None
    if target in DERIVED:
        if target not in prof.derived or target not in conf:
            raise ValueError(f"derived target {target!r} must be in the profile and in conf")
        if sum(k for _, k in DERIVED_CELLS) != n // 2:
            raise ValueError(f"n={n}: the non-target class must hold {sum(k for _, k in DERIVED_CELLS)} notes")
        cells = [c for c, k in DERIVED_CELLS for _ in range(k)]
        rng.shuffle(cells)
    texts, labels, rows, k = [], [], [], 0
    for i in range(n):
        y = i % 2
        lv, seed = _levels(rng, prof)
        protect = set(flag_conf)
        for f, s in flag_conf.items():
            lv[f] = int((y == 1) if s > 0 else (y == 0))
        if cells is not None:
            a, b = DERIVED[target]
            if y == _target_class(conf[target]):
                lv[a] = lv[b] = 1
            else:
                cell = cells[k]
                k += 1
                lv[a], lv[b] = int(cell == "A"), int(cell == "B")
            protect |= {a, b}
        imply(lv, prof, protect)
        text, flags = render(topics[y], lv, prof, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(prof, texts, labels, rows)


def sample_grid(rng, topics, n, profile, mains=(), held_off=(), held_on=()):
    """mains=[]: held-out notes, every property a fair coin, then nesting. mains=[f]: the grader-style grid
    (as freetext_listing.sample_grid): f balanced against the topic and protected; held_off / held_on flags
    forced to 0 / 1 and protected. mains=[derived]: target balanced against the topic; where it is off, the
    notes alternate between component A only and component B only; the components' ancestors held on."""
    prof = profile_of(profile)
    fl._check_topics(topics)
    mains, held_off, held_on = list(mains), list(held_off), list(held_on)
    derived = [m for m in mains if m in DERIVED]
    if derived and (len(mains) != 1 or derived[0] not in prof.derived):
        raise ValueError("a derived main must be the only main and belong to the profile")
    check_levels({f: 0 for f in [m for m in mains if m not in DERIVED] + held_off + held_on}, prof)
    cell = 8 if derived else 2 * 2 ** len(mains)
    if n % cell:
        raise ValueError(f"n={n} must be a multiple of {cell}")
    texts, labels, rows = [], [], []
    for i in range(n):
        y = i % 2
        lv, seed = _levels(rng, prof)
        protect = set(held_off) | set(held_on)
        for f in held_off:
            lv[f] = 0
        for f in held_on:
            lv[f] = 1
        if derived:
            a, b = DERIVED[derived[0]]
            on = (i // 2) % 2 == 0
            only_a = (i // 4) % 2 == 0
            lv[a], lv[b] = (1, 1) if on else ((1, 0) if only_a else (0, 1))
            for anc in ancestors(derived[0]):
                lv[anc] = 1
                protect.add(anc)
            protect |= {a, b}
        else:
            for j, f in enumerate(mains):
                lv[f] = ((i // 2) >> j) & 1
            protect |= set(mains)
        imply(lv, prof, protect)
        text, flags = render(topics[y], lv, prof, seed)
        texts.append(text)
        labels.append(y)
        rows.append(flags)
    return _finish(prof, texts, labels, rows)


def lower_twins(rng, topics, n, profile="fi"):
    """Counterfactual pairs for informal_lower (L5): n notes with an informal greeting in lower case (the cue
    on; every other property a coin, then nesting) and, for each, its TWIN: the same note (same seed and
    levels) rendered with capitals, then only its greeting line put in lower case. A twin starts exactly as its
    note but has capitals after the greeting line, so it lacks "no capital letters": a regex that matches the
    twins as often as the notes tested the lower-case greeting words, not the absence of capitals.
    -> (notes, twins)."""
    prof = profile_of(profile)
    fl._check_topics(topics)
    notes, twins = [], []
    for i in range(n):
        y = i % 2
        lv, seed = _levels(rng, prof)
        lv.update(greeting=1, greet_informal=1, lowercase=1)
        imply(lv, prof, {"greeting", "greet_informal", "lowercase"})
        note, flags = render(topics[y], lv, prof, seed)
        upper, _ = render(topics[y], {**flags, "lowercase": 0}, prof, seed)
        first, rest = upper.split("\n", 1)
        twin = first.lower() + "\n" + rest
        if note.split("\n", 1)[0] != twin.split("\n", 1)[0] or not any(c.isupper() for c in rest):
            raise AssertionError("a twin must share the note's greeting line and have a capital after it")
        notes.append(note)
        twins.append(twin)
    return notes, twins


# ---------------------------------------------------------------- masks, aligned set, negative control

def mask(prop, flags, profile="base"):
    """The notes in which `prop` can vary (primary scoring rule): every ancestor present; for a member of an
    exclusive pair that loses by default, the winner absent; for a derived cue, the components' ancestors
    present and at least one component present."""
    prof = profile_of(profile)
    n = len(next(iter(flags.values())))
    m = np.ones(n, dtype=bool)
    for a in ancestors(prop):
        m &= np.asarray(flags[a], bool)
    if prop in DERIVED:
        a, b = DERIVED[prop]
        return m & (np.asarray(flags[a], bool) | np.asarray(flags[b], bool))
    for loser, winner in prof.exclusive:
        if prop == loser:
            m &= ~np.asarray(flags[winner], bool)
    return m


def draw_aligned(rng, target, profile="base"):
    """The 8 aligned properties and their signs: {target: s, other: s, ...} (target first, then the others in
    the profile's feature order). See the module text."""
    prof = profile_of(profile)
    if target not in prof.scored:
        raise ValueError(f"{target!r} is not a property of profile {prof.name}")
    rel = related(target, prof)
    excl = set().union(*(exclusive_with(c, prof) for c in {target} | components(target)))
    eligible = {f: w for f, w in POOL_WEIGHTS.items() if f in prof.features and f not in rel and f not in excl}
    for _ in range(MAX_REDRAWS):
        others = _pps(rng, eligible, N_ALIGNED - 1)
        if not any(b in ancestors(a) or b in exclusive_with(a, prof) for a in others for b in others):
            break
    else:
        raise ValueError(f"no aligned set without a parent-child or exclusive pair for {target!r}")
    order = [target] + [f for f in prof.features if f in others]
    signs = {f: (-1 if rng.random() < P_NEG else 1) for f in order}
    for child in order:
        for p in PARENTS.get(child, ()):
            if p in signs:
                signs[p] = signs[child]
    return signs


def negative_candidates(aligned, profile="base"):
    """Properties eligible as the negative control of a sample whose aligned set (target included) is
    `aligned`: generator flags of the profile that are not aligned, not an ancestor, descendant or component
    of an aligned property (or of a component's), not exclusive with any of them, and sharing no mark with
    any of them (MARK_GROUPS: e.g. the body question is not eligible when a P.S. question is aligned)."""
    prof = profile_of(profile)
    bad = set()
    for a in aligned:
        bad |= related(a, prof)
        for c in {a} | components(a):
            bad |= exclusive_with(c, prof) | shares_mark(c)
    return [f for f in prof.features if f not in bad]
