"""shifthunt/freetext_listing.py: the 20-property generator of the Exp D listing screen (CPU, no torch, no API).

Needs only the tracked paragraph bank .cache/freetext/bank.json.
"""
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import freetext as ft  # noqa: E402
from shifthunt import freetext_listing as fl  # noqa: E402
from shifthunt.grader import balanced_accuracy  # noqa: E402

TOPICS = ["photography", "running"]  # the two topics with most digit-bearing bank paragraphs
PAIRS = [("photography", "running"), ("knitting", "chess"), ("sailing", "gardening"), ("pottery", "astronomy")]
OLD = tuple(ft.FEATURES)
PLAIN_OLD = tuple(f for f in OLD if f not in ft.IMPLIES)
FAMILY = {"postscript": {"postscript", "ps_question", "ps_tentative"},
          "signoff": {"signoff", "signoff_excl", "signoff_initial"}}
WORD_OF = {digits: word for word, digits in fl.NUMBERS}


def family(f):
    """The properties tied to f by nesting or exclusion (f included)."""
    return next((fam for fam in FAMILY.values() if f in fam), {f})


def heldout(tag, n=1024):
    """n independent-coin notes per topic pair -> (texts, flags) over all PAIRS."""
    texts, flags = [], {f: [] for f in fl.FEATURES}
    for pair in PAIRS:
        t, _, fg = fl.sample_grid(random.Random(f"{tag}:{pair}"), list(pair), n, None)
        texts += t
        for f in fl.FEATURES:
            flags[f] += fg[f].tolist()
    return texts, {f: np.array(v) for f, v in flags.items()}


@pytest.fixture(scope="module")
def notes():
    return heldout("test:heldout")


def random_levels(rng, on=None):
    """20 fair coins; `on` (if given) is set to 1 and protected, as a sample's aligned property is."""
    lv = {f: int(rng.random() < 0.5) for f in fl.FEATURES}
    if on:
        lv[on] = 1
    return fl._imply(lv, protect={on} if on else ())


# ---------------------------------------------------------------- the feature list and the banks
def test_features_and_nesting():
    assert len(fl.FEATURES) == 20 and len(set(fl.FEATURES)) == 20
    assert fl.FEATURES[:15] == OLD and fl.FEATURES[15:] == fl.NEW
    assert fl.NEW == ("curly_apostrophe", "double_space", "digits", "ps_tentative", "signoff_initial")
    assert fl.IMPLIES == {"signoff_excl": "signoff", "ps_question": "postscript",
                          "ps_tentative": "postscript", "signoff_initial": "signoff"}
    assert ft.IMPLIES == {"signoff_excl": "signoff", "ps_question": "postscript"}  # freetext's map is untouched
    assert len(ft.FEATURES) == 15


def test_no_torch_import():
    code = ("import sys; from shifthunt import freetext_listing; "
            "print(int('torch' in sys.modules or 'transformers' in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.stdout.strip() == "0", out.stderr


def test_inserted_sentence_banks_trip_no_old_detector():
    numbers = [s.format(n=form) for s in fl.NUMBER_SENTENCES for pair in fl.NUMBERS for form in pair]
    for s in fl.APOSTROPHE_SENTENCES + numbers:
        assert not re.search(r'[:()#?!";]|\.\.\.|\^_\^|  |\n', s), s
        assert s.endswith(".") and s.count(".") == 1 and s[0].isupper(), s
        assert not any(day.lower() in s.lower() for day in ft.WEEKDAYS), s
        assert not re.search(r"(?i)\b(she|her|hers|herself)\b", s), s
        assert not fl._HEDGE_RE.search(s), s
        assert s.isascii() and fl.CURLY not in s
    for s in fl.APOSTROPHE_SENTENCES:
        assert s.count("'") == 1 and re.search(r"\w'\w", s) and not re.search(r"\d", s), s
    assert len(set(fl.APOSTROPHE_SENTENCES)) == 8 and len(set(fl.NUMBER_SENTENCES)) == 8
    for s in fl.NUMBER_SENTENCES:
        assert s.count("{n}") == 1 and "'" not in s and not re.search(r"\d", s), s
    for word, digits in fl.NUMBERS:
        assert word.isalpha() and word.islower() and digits.isdigit() and int(digits) >= 2
    assert len(WORD_OF) == len(fl.NUMBERS)


def test_tentative_ps_bank():
    assert len(fl.PS_TENTATIVE) == len(ft.PS_STATEMENTS) == 8
    for hedged, plain in zip(fl.PS_TENTATIVE, ft.PS_STATEMENTS):
        assert hedged != plain and hedged.startswith("P.S. ") and hedged.endswith(".")
        assert len(fl._HEDGE_RE.findall(hedged)) == 1, hedged       # exactly one marker, in the P.S. line
        assert not fl._HEDGE_RE.search(plain), plain
        assert not re.search(r"['’\d?!]|  ", hedged), hedged
        assert len(hedged) < 40, hedged                             # the paragraph stays the only long line
        # the same statement: the plain line's words all survive, in order
        words = [w.lower() for w in re.findall(r"[A-Za-z]+", plain)]
        rest = iter(w.lower() for w in re.findall(r"[A-Za-z]+", hedged))
        assert all(w in rest for w in words), (hedged, plain)
    for q in ft.PS_QUESTIONS:
        assert not fl._HEDGE_RE.search(q), q


def test_bank_filter_is_in_memory_and_drops_only_digit_paragraphs():
    full, clean = ft.bank(), fl.bank()
    dropped = {t: [p for p in full[t] if p not in clean[t]] for t in full}
    assert sum(map(len, dropped.values())) == 8
    assert sum(map(len, full.values())) == 2713 and sum(map(len, clean.values())) == 2705
    assert all(re.search(r"\d", p) for ps in dropped.values() for p in ps)
    assert not any(re.search(r"\d", p) for ps in clean.values() for p in ps)
    assert ft.bank() is full and sum(map(len, ft.bank().values())) == 2713      # freetext's own bank is not filtered
    assert not any(fl.CURLY in p or "  " in p for ps in full.values() for p in ps)


def test_form_banks_hold_no_apostrophe_digit_or_double_space():
    for name in ("NAMES", "TAGS", "GREETINGS", "CLOSINGS", "PS_STATEMENTS", "PS_QUESTIONS", "QUESTIONS",
                 "WEEKDAY_SENTENCES", "WEEKDAYS", "ASIDES", "EMOTICONS", "QUOTE_SENTENCES", "QUOTES"):
        for s in getattr(ft, name):
            assert not re.search(r"['’\d]|  ", s), (name, s)


# ---------------------------------------------------------------- render
def test_check_levels_and_bad_input():
    assert fl.check_levels({}) == dict.fromkeys(fl.FEATURES, 0)
    with pytest.raises(ValueError):
        fl.check_levels({"british_spelling": 1})
    with pytest.raises(ValueError):
        fl.check_levels({"digits": 2})
    with pytest.raises(ValueError):
        fl.render("golf", {})
    with pytest.raises(ValueError):
        fl.sample_texts(random.Random(0), ["chess"], 4, None, {})
    with pytest.raises(ValueError):
        fl.sample_texts(random.Random(0), TOPICS, 4, None, {"digits": 0})
    with pytest.raises(ValueError):
        fl.sample_grid(random.Random(0), TOPICS, 6, None, mains=["digits"])


def test_render_is_deterministic_and_draws_do_not_depend_on_levels():
    rng = random.Random("det")
    for i in range(200):
        lv = random_levels(rng)
        a = fl.render("cycling", lv, seed=i)
        assert a == fl.render("cycling", dict(lv), seed=i)
        assert a[1] == lv
    assert fl.render("cycling", {}, seed=1)[0] != fl.render("cycling", {}, seed=2)[0]
    assert fl.render("cycling", {}, seed="a")[0] == fl.render("cycling", {}, seed="a")[0]


def test_samples_are_identical_across_processes_and_hash_seeds():
    code = ("import hashlib, json, random; from shifthunt import freetext_listing as fl; "
            "t, y, f = fl.sample_texts(random.Random('proc'), ['chess', 'sailing'], 64, None, {'ps_tentative': -1}); "
            "g, _, _ = fl.sample_grid(random.Random('proc'), ['chess', 'sailing'], 64, None); "
            "print(hashlib.sha256(json.dumps([t, g, y.tolist(), {k: v.tolist() for k, v in f.items()}])"
            ".encode()).hexdigest())")
    digests = set()
    for hash_seed in ("0", "1", "12345"):
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                             env={**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONDONTWRITEBYTECODE": "1"})
        assert out.returncode == 0, out.stderr
        digests.add(out.stdout.strip())
    assert len(digests) == 1


def test_new_levels_off_is_the_freetext_note_plus_two_inserted_sentences():
    """Exactly how: with the five new levels off, removing " " + sentence for each of the two inserted
    sentences (as render_parts names them) from the note gives freetext.render(topic, levels, seed), byte for
    byte, for every seed whose freetext paragraph has no digit. For the others the paragraph is replaced."""
    rng, n, n_replaced = random.Random("vs-freetext"), 3000, 0
    for i in range(n):
        topic = rng.choice(fl.TOPIC_NAMES)
        old = ft._imply({f: int(rng.random() < 0.5) for f in OLD})
        text, flags, info = fl.render_parts(topic, old, seed=i)
        ref, ref_flags = ft.render(topic, old, seed=i)
        assert {f: flags[f] for f in OLD} == ref_flags and not any(flags[f] for f in fl.NEW)
        assert len(info["inserted"]) == 2
        stripped = text
        for s in info["inserted"]:
            assert stripped.count(" " + s) == 1
            stripped = stripped.replace(" " + s, "", 1)
        full_par = ft.bank()[topic][ft._draw(random.Random(i), len(ft.bank()[topic]))["par"]]
        assert info["replaced"] == bool(re.search(r"\d", full_par))
        if info["replaced"]:
            n_replaced += 1
            assert re.search(r"\d", ref) and not re.search(r"\d", text) and stripped != ref
        else:
            assert stripped == ref
        # the inserted sentences sit in the body line and never open it
        body = max(text.split("\n"), key=len)
        assert all(" " + s in body and not body.startswith(s) for s in info["inserted"])
    assert 0 < n_replaced <= 0.01 * n       # 8 of 2713 paragraphs


def test_a_replaced_paragraph_is_digit_free_and_flips_stay_local():
    pars = ft.bank()["photography"]
    seeds = [s for s in range(400) if re.search(r"\d", pars[ft._draw(random.Random(s), len(pars))["par"]])]
    assert seeds
    for s in seeds:
        off, _, info = fl.render_parts("photography", {}, seed=s)
        on = fl.render("photography", {"digits": 1}, seed=s)[0]
        assert info["replaced"] and not re.search(r"\d", off)
        numbers = re.findall(r"\d+", on)
        assert len(numbers) == 1 and on.replace(numbers[0], WORD_OF[numbers[0]]) == off


def undo(cue, on_text, off_text):
    """The `on` note with the cue's edit reversed (uses off_text only where the edit is not invertible alone)."""
    if cue == "curly_apostrophe":
        return on_text.replace(fl.CURLY, "'")
    if cue == "double_space":
        return on_text.replace("  ", " ")
    if cue == "digits":
        (m,) = re.finditer(r"\d+", on_text)
        return on_text[:m.start()] + WORD_OF[m.group()] + on_text[m.end():]
    lines, off_lines = on_text.split("\n"), off_text.split("\n")
    assert len(lines) == len(off_lines)
    if cue == "ps_tentative":
        k = [x.lower() for x in fl.PS_TENTATIVE].index(lines[-1].lower())
        lines[-1] = ft.PS_STATEMENTS[k].lower() if on_text == on_text.lower() else ft.PS_STATEMENTS[k]
    else:
        (k,) = [i for i, x in enumerate(lines) if re.fullmatch(r"[A-Za-z]\.", x)]
        assert off_lines[k][0] == lines[k][0] and off_lines[k].lower() in [n.lower() for n in ft.NAMES]
        lines[k] = off_lines[k]
    return "\n".join(lines)


@pytest.mark.parametrize("cue", fl.NEW)
def test_each_new_edit_changes_the_note_and_nothing_else(cue):
    rng, n, changed = random.Random(f"edit:{cue}"), 1500, 0
    for i in range(n):
        topic = rng.choice(fl.TOPIC_NAMES)
        lv_on = random_levels(rng, on=cue)
        lv_off = dict(lv_on, **{cue: 0})
        on, flags_on = fl.render(topic, lv_on, seed=i)
        off, flags_off = fl.render(topic, lv_off, seed=i)
        assert flags_on[cue] == 1 and flags_off[cue] == 0
        assert {f: v for f, v in flags_on.items() if f != cue} == {f: v for f, v in flags_off.items() if f != cue}
        assert flags_on == lv_on and flags_off == lv_off
        changed += on != off
        assert undo(cue, on, off) == off                    # the text is identical up to the edit
        det_on, det_off = fl.detect(on), fl.detect(off)     # and only the cue's own detector moves
        assert det_on == flags_on and det_off == flags_off
    assert changed >= 0.99 * n
    assert changed == n


@pytest.mark.parametrize("cue", OLD)
def test_each_old_edit_still_changes_only_its_own_flag(cue):
    rng = random.Random(f"old-edit:{cue}")
    for i in range(300):
        topic = rng.choice(fl.TOPIC_NAMES)
        lv_on = random_levels(rng, on=cue)
        lv_off = dict(lv_on, **{cue: 0})
        for child, parent in fl.IMPLIES.items():      # switching a parent off takes its children with it
            if parent == cue:
                lv_off[child] = 0
        on, flags_on = fl.render(topic, lv_on, seed=i)
        off, flags_off = fl.render(topic, lv_off, seed=i)
        assert on != off and flags_on == lv_on and flags_off == lv_off
        assert fl.detect(on) == flags_on and fl.detect(off) == flags_off


def test_curly_apostrophe_converts_every_apostrophe_and_only_apostrophes():
    rng, with_bank_apostrophe = random.Random("curly"), 0
    for i in range(1500):
        lv = random_levels(rng)
        text = fl.render(rng.choice(fl.TOPIC_NAMES), lv, seed=i)[0]
        n_apos = text.count("'") + text.count(fl.CURLY)
        assert n_apos >= 1                                   # every note has an apostrophe to vary
        with_bank_apostrophe += n_apos > 1
        assert (text.count(fl.CURLY), text.count("'")) == ((n_apos, 0) if lv["curly_apostrophe"] else (0, n_apos))
        assert "“" not in text and "”" not in text and "‘" not in text
        assert text.count('"') == (2 if lv["quote"] else 0)   # the quote feature keeps straight double quotes
        assert all(ch.isascii() or ch == fl.CURLY for ch in text)
    assert with_bank_apostrophe > 0      # some bank paragraphs have their own apostrophe; it is converted too


def test_double_space_is_exactly_the_body_sentence_joins():
    rng = random.Random("spaces")
    for i in range(1500):
        lv = random_levels(rng)
        topic = rng.choice(fl.TOPIC_NAMES)
        text, _, info = fl.render_parts(topic, lv, seed=i)
        if not lv["double_space"]:
            assert "  " not in text
            continue
        lines = text.split("\n")
        body = max(lines, key=len)
        assert all("  " not in x for x in lines if x is not body)       # greeting, sign-off, P.S.: single
        assert "   " not in text
        par = ft.bank()[topic][ft._draw(random.Random(i), len(ft.bank()[topic]))["par"]]
        if not info["replaced"]:
            n_sent = len(ft.split_sentences(par)) + 2 + lv["question"] + lv["weekday"] + lv["quote"]
            assert body.count("  ") == n_sent - 1                        # every join, and nothing else
        assert body.count("  ") >= 4
        assert not re.search(r"  [#(]|  (:\)|:-\)|:d|;\)|:p|\^_\^)", body.lower())    # tag, aside, emoticon
        assert not re.search(r"(?i)p\.s\.  ", text)


def test_digits_only_in_the_number_phrase():
    rng = random.Random("digits")
    for i in range(1500):
        lv = random_levels(rng)
        text, _, info = fl.render_parts(rng.choice(fl.TOPIC_NAMES), lv, seed=i)
        numbers = re.findall(r"\d+", text)
        assert len(numbers) == (1 if lv["digits"] else 0)
        if lv["digits"]:
            assert numbers[0] in WORD_OF and numbers[0] in info["inserted"][1]
        else:
            assert any(re.search(rf"\b{w}\b", info["inserted"][1]) for w in WORD_OF.values())


def test_no_new_surface_form_arises_without_its_edit(notes):
    texts, flags = notes
    for i, t in enumerate(texts):
        assert (fl.CURLY in t) == bool(flags["curly_apostrophe"][i])
        assert ("  " in t) == bool(flags["double_space"][i])
        assert bool(re.search(r"\d", t)) == bool(flags["digits"][i])
        assert bool(re.search(r"(?m)^[A-Za-z]\.$", t)) == bool(flags["signoff_initial"][i])
        last = t.split("\n")[-1]
        assert bool(last.lower().startswith("p.s.") and fl._HEDGE_RE.search(last)) == bool(flags["ps_tentative"][i])


def test_layout_the_paragraph_is_the_only_long_line(notes):
    texts, _ = notes
    for t in texts:
        lens = sorted(len(x) for x in t.split("\n"))
        assert lens[-1] >= 150 and (len(lens) == 1 or lens[-2] < 40)
        assert not t.endswith("\n") and "\r" not in t and "\t" not in t


# ---------------------------------------------------------------- detectors
def test_detect_agrees_with_flags_on_heldout_notes(notes):
    texts, flags = notes
    assert len(texts) >= 2000
    found = [fl.detect(t) for t in texts]
    for f in fl.FEATURES:
        pred = np.array([d[f] for d in found])
        assert 0 < flags[f].sum() < len(texts), f                # both classes present
        ba = balanced_accuracy(pred, flags[f])
        assert ba >= 0.99, (f, ba)
        assert (pred == flags[f]).all(), f                       # in fact exact


def test_freetext_detectors_and_submission_regexes_still_agree_on_the_new_notes(notes):
    texts, flags = notes
    for i, t in enumerate(texts):
        old = ft.detect(t)
        assert old == {f: int(flags[f][i]) for f in OLD}, t
    for f in OLD:
        pattern, scope = ft.submission_regex(f)
        assert scope == "any"
        assert [bool(re.search(pattern, t)) for t in texts] == flags[f].astype(bool).tolist(), f


def test_submission_regexes_of_all_20_agree_with_flags(notes):
    texts, flags = notes
    assert set(fl.SUBMISSION) == set(fl.FEATURES)
    for f in fl.FEATURES:
        pattern, scope = fl.submission_regex(f)
        assert scope == "any" and len(pattern) <= 200
        assert [bool(re.search(pattern, t)) for t in texts] == flags[f].astype(bool).tolist(), f
    assert fl.SUBMISSION["signoff_initial"] == r"(?m)^[A-Za-z]\.$"
    assert fl.SUBMISSION["curly_apostrophe"] == "’" and fl.SUBMISSION["double_space"] == "  "


def test_ps_tentative_detector_is_anchored_on_the_ps_line():
    body = "He will maybe go again, I think. " * 6
    assert fl.detect(body + "\nP.S. Call me later.")["ps_tentative"] == 0          # a hedge in the body only
    assert fl.detect(body + "\nP.S. Call me later, probably.")["ps_tentative"] == 1
    assert fl.detect(body + "\np.s. maybe write back soon.")["ps_tentative"] == 1
    assert not re.search(fl.SUBMISSION["ps_tentative"], body + "\nP.S. Call me later.")
    assert re.search(fl.SUBMISSION["ps_tentative"], body + "\np.s. maybe write back soon.")


# ---------------------------------------------------------------- nesting and the exclusion rule
def test_imply_rules():
    base = dict.fromkeys(fl.FEATURES, 0)
    # unprotected child without its parent is dropped; protected child switches the parent on
    for child, parent in fl.IMPLIES.items():
        assert fl._imply(dict(base, **{child: 1}))[child] == 0
        lv = fl._imply(dict(base, **{child: 1}), protect={child})
        assert lv[child] == 1 and lv[parent] == 1
        with pytest.raises(ValueError):
            fl._imply(dict(base, **{child: 1}), protect={child, parent})
    both = dict(base, postscript=1, ps_tentative=1, ps_question=1)
    # documented rule: unprotected, the question wins
    lv = fl._imply(dict(both))
    assert (lv["ps_question"], lv["ps_tentative"], lv["postscript"]) == (1, 0, 1)
    # ps_question protected, ps_tentative not: the question wins as well
    lv = fl._imply(dict(both), protect={"ps_question"})
    assert (lv["ps_question"], lv["ps_tentative"]) == (1, 0)
    # ps_tentative protected: ps_question is switched off in that note
    lv = fl._imply(dict(both), protect={"ps_tentative"})
    assert (lv["ps_question"], lv["ps_tentative"], lv["postscript"]) == (0, 1, 1)
    lv = fl._imply(dict(base, ps_tentative=1, ps_question=1), protect={"ps_tentative"})   # parent off
    assert (lv["ps_question"], lv["ps_tentative"], lv["postscript"]) == (0, 1, 1)
    with pytest.raises(ValueError):
        fl._imply(dict(both), protect={"ps_tentative", "ps_question"})
    # the two sign-off children are independent of each other
    lv = fl._imply(dict(base, signoff=1, signoff_excl=1, signoff_initial=1))
    assert (lv["signoff_excl"], lv["signoff_initial"]) == (1, 1)
    # a parent that a protected child switches on keeps its other child, whichever of the two is protected
    # (the outcome does not depend on the order of IMPLIES)
    for protected in ("signoff_excl", "signoff_initial"):
        lv = fl._imply(dict(base, signoff_excl=1, signoff_initial=1), protect={protected})
        assert (lv["signoff"], lv["signoff_excl"], lv["signoff_initial"]) == (1, 1, 1), protected
    keep = dict(fl.IMPLIES)
    try:
        for order in (list(keep), list(keep)[::-1]):
            fl.IMPLIES = {child: keep[child] for child in order}
            lv = fl._imply(dict(base, signoff_excl=1, signoff_initial=1, ps_question=1, ps_tentative=1),
                           protect={"signoff_initial", "ps_tentative"})
            assert [f for f in fl.FEATURES if lv[f]] == ["signoff", "signoff_excl", "postscript", "ps_tentative",
                                                         "signoff_initial"], order
    finally:
        fl.IMPLIES = keep
    # a protected child that is off leaves the parent alone, and the other child is dropped with it
    lv = fl._imply(dict(base, signoff_excl=1), protect={"signoff_initial"})
    assert (lv["signoff"], lv["signoff_excl"], lv["signoff_initial"]) == (0, 0, 0)


def test_render_flags_show_the_text_for_dropped_and_excluded_children():
    text, flags = fl.render("chess", {"ps_tentative": 1, "signoff_initial": 1, "ps_question": 1}, seed=3)
    assert not any(flags.values()) and "\n" not in text          # no parents: nothing is rendered
    text, flags = fl.render("chess", {"postscript": 1, "ps_tentative": 1, "ps_question": 1}, seed=3)
    assert (flags["ps_question"], flags["ps_tentative"]) == (1, 0) and text.endswith("?")
    text, flags = fl.render("chess", {"postscript": 1, "ps_tentative": 1}, seed=3)
    assert flags["ps_tentative"] == 1 and text.split("\n")[-1] in fl.PS_TENTATIVE
    text, flags = fl.render("chess", {"signoff": 1, "signoff_initial": 1, "signoff_excl": 1}, seed=3)
    closing, name = text.split("\n")[-2:]
    assert closing.endswith("!") and re.fullmatch(r"[A-Z]\.", name)
    assert fl.detect(text) == flags


def test_heldout_grid_rates_and_exclusion(notes):
    texts, flags = notes
    n = len(texts)
    for f in fl.FEATURES:
        rate = flags[f].mean()
        want = 0.125 if f == "ps_tentative" else 0.25 if f in fl.IMPLIES else 0.5
        assert abs(rate - want) < 4 * np.sqrt(want * (1 - want) / n), (f, rate)
    assert not (flags["ps_tentative"] & flags["ps_question"]).any()
    for child, parent in fl.IMPLIES.items():
        assert not (flags[child] & (1 - flags[parent])).any()
    # within the notes where it can vary, each conditional property is a fair coin
    statement = (flags["postscript"] == 1) & (flags["ps_question"] == 0)
    assert abs(flags["ps_tentative"][statement].mean() - 0.5) < 0.06
    assert abs(flags["signoff_initial"][flags["signoff"] == 1].mean() - 0.5) < 0.05
    # and the plain properties are pairwise independent of the new ones (no accidental coupling of streams)
    for a in ("curly_apostrophe", "double_space", "digits"):
        for b in PLAIN_OLD + tuple(x for x in fl.NEW[:3] if x != a):
            assert abs(np.corrcoef(flags[a], flags[b])[0, 1]) < 0.08, (a, b)


# ---------------------------------------------------------------- samplers
@pytest.mark.parametrize("cue", fl.FEATURES)
@pytest.mark.parametrize("sign", [1, -1])
def test_sample_aligns_the_target_exactly_with_the_label(cue, sign):
    rng = random.Random(f"align:{cue}:{sign}")
    texts, y, flags = fl.sample_texts(rng, TOPICS, 128, None, {cue: sign})
    assert len(texts) == 128 and y.tolist() == [0, 1] * 64
    want = y if sign > 0 else 1 - y
    assert (flags[cue] == want).all()
    assert all(fl.detect(t) == {f: int(flags[f][i]) for f in fl.FEATURES} for i, t in enumerate(texts))
    # every property outside the target's family takes both values in both classes
    for f in fl.FEATURES:
        if f not in family(cue):
            for label in (0, 1):
                assert 0 < flags[f][y == label].sum() < 64, (cue, f, label)
    on = flags[cue] == 1
    if cue in fl.IMPLIES:                      # a child: its parent is on wherever the child is on
        parent = flags[fl.IMPLIES[cue]]
        assert parent[on].all() and 0 < parent[~on].sum() < 64
    for child, parent in fl.IMPLIES.items():   # a parent: its children occur only where it is on
        if parent == cue:
            assert flags[child][~on].sum() == 0 and 0 < flags[child][on].sum() < 64
    if cue == "ps_tentative":
        assert flags["ps_question"][on].sum() == 0 and flags["ps_question"][~on].sum() > 0
    if cue == "ps_question":
        assert flags["ps_tentative"][on].sum() == 0 and flags["ps_tentative"][~on].sum() > 0


@pytest.mark.parametrize("target, sibling", [("signoff_initial", "signoff_excl"), ("signoff_excl", "signoff_initial")])
def test_the_other_signoff_child_is_a_coin_among_signoff_notes_in_both_classes(target, sibling):
    """With one sign-off child aligned (or a grid main), the other one is a fair coin wherever the sign-off is
    present, in the target's class as in the other class, and the same for both choices of the target."""
    on_class, off_class = [], []
    for k in range(40):
        rng = random.Random(f"sibling:{target}:{k}")
        _, y, flags = fl.sample_texts(rng, list(PAIRS[k % 4]), 128, None, {target: 1 if k % 2 else -1})
        on, parent = flags[target] == 1, flags["signoff"] == 1
        assert parent[on].all()
        on_class += flags[sibling][on & parent].tolist()
        off_class += flags[sibling][~on & parent].tolist()
    assert len(on_class) == 40 * 64 and 1000 < len(off_class) < 1560
    assert abs(np.mean(on_class) - 0.5) < 0.04 and abs(np.mean(off_class) - 0.5) < 0.06, (target, np.mean(on_class))
    _, _, flags = fl.sample_grid(random.Random(f"sibling-grid:{target}"), TOPICS, 4096, None, mains=[target])
    on, parent = flags[target] == 1, flags["signoff"] == 1
    assert abs(flags[sibling][on & parent].mean() - 0.5) < 0.04
    assert abs(flags[sibling][~on & parent].mean() - 0.5) < 0.06


def test_sample_is_deterministic_and_topics_follow_the_label():
    a = fl.sample_texts(random.Random("d"), TOPICS, 64, None, {"digits": 1})
    b = fl.sample_texts(random.Random("d"), TOPICS, 64, None, {"digits": 1})
    c = fl.sample_texts(random.Random("e"), TOPICS, 64, None, {"digits": 1})
    assert a[0] == b[0] and (a[1] == b[1]).all() and all((a[2][f] == b[2][f]).all() for f in fl.FEATURES)
    assert a[0] != c[0]
    swapped = fl.sample_texts(random.Random("d"), TOPICS[::-1], 64, None, {"digits": 1})
    assert set(a[0]).isdisjoint(swapped[0])     # the paragraph comes from the label's topic


@pytest.mark.parametrize("cue", OLD)
def test_old_flags_of_a_sample_equal_freetext_sample_texts_with_the_same_rng(cue):
    """The 15 old coins come from rng in freetext's order, so a calibration cue's sample has the old flags
    (and the same shuffle afterwards) of the existing generator's sample."""
    mine_rng, ref_rng = random.Random(f"same:{cue}"), random.Random(f"same:{cue}")
    _, y, flags = fl.sample_texts(mine_rng, TOPICS, 128, None, {cue: -1})
    _, ref_y, ref_flags = ft.sample_texts(ref_rng, TOPICS, 128, None, {cue: -1})
    assert (y == ref_y).all()
    for f in OLD:
        assert (flags[f] == ref_flags[f]).all(), f
    assert mine_rng.random() == ref_rng.random()        # the stream is left in the same state


@pytest.mark.parametrize("cue", fl.FEATURES)
def test_grader_style_grid_for_one_main(cue):
    texts, y, flags = fl.sample_grid(random.Random(f"grid:{cue}"), TOPICS, 1024, None, mains=[cue])
    main = flags[cue]
    assert main.sum() == 512 and all(main[y == label].sum() == 256 for label in (0, 1))
    assert all(fl.detect(t)[cue] == main[i] for i, t in enumerate(texts))
    if cue in fl.IMPLIES:
        parent = flags[fl.IMPLIES[cue]]
        assert parent[main == 1].all() and abs(parent[main == 0].mean() - 0.5) < 0.1
    if cue == "ps_tentative":
        assert flags["ps_question"][main == 1].sum() == 0
        assert abs(flags["ps_question"][main == 0].mean() - 0.25) < 0.08


def test_sample_grid_held_off():
    _, _, flags = fl.sample_grid(random.Random("held"), TOPICS, 256, None, mains=["ps_tentative"],
                                 held_off=["ps_question", "double_space"])
    assert flags["ps_question"].sum() == 0 and flags["double_space"].sum() == 0
    assert flags["ps_tentative"].sum() == 128

