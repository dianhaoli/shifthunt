import hashlib
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from shifthunt import textgen as tg
from shifthunt.detectors import detect, detect_all
from shifthunt.flipcheck import text_flip_is_clean, undo

ROOT = Path(__file__).resolve().parents[1]
STOP = {"the", "at", "for", "of", "by", "in", "on", "a", "and"}
TOPIC_VOCAB = {w for b in tg.TOPICS.values() for ps in b.values() for p in ps for w in p.split()} - STOP
TEMPLATES = [s for pair in [tg.S1, tg.S2, *tg.S3, *tg.S4, tg.S5, tg.QUOTE, tg.WEEKDAY] for s in pair]
TEMPLATE_WORDS = {w.lower() for t in TEMPLATES for w in re.findall(r"[A-Za-z]+", re.sub(r"\{\w+\}", " ", t))}
TENSE_WORDS = {"spends", "spent", "owns", "owned", "keeps", "kept", "says", "said", "is", "was",
               "think", "thought", "finds", "found", "organises", "organised", "practises",
               "practised", "meets", "met", "loves", "loved", "hates", "hated", "goes", "went"}
VARIANT_WORDS = set(tg.AMERICAN) | set(tg.AMERICAN.values()) | {
    "harbour", "harbor", "tyre", "tire", "tyres", "tires", "metre", "meter", "metres", "meters",
    "catalogue", "catalog", "programme", "program", "analyse", "analyze", "analysing", "analyzing",
    "jewellery", "jewelry", "aluminium", "aluminum", "colours", "colors", "travelling", "traveling"}
NEGATIVE = {neg for _, neg in tg.ADJ_PAIRS} | {"hates", "hated"}
PRONOUNS = {"he", "him", "his", "she", "her", "hers"}
DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def random_case(rng):
    levels = {f: rng.randrange(2) for f in tg.FEATURES}
    return rng.choice(tg.TOPIC_NAMES), levels, tg.make_cues(rng), rng.getrandbits(32)


def words(s):
    return re.findall(r"[a-z]+", s.lower())


# ---- determinism ----

def test_render_deterministic():
    rng = random.Random(0)
    for _ in range(200):
        case = random_case(rng)
        assert tg.render(*case) == tg.render(*case)


DIGEST_CODE = """
import hashlib, random
from shifthunt import textgen as tg
rng = random.Random(7)
h = hashlib.sha256()
for _ in range(200):
    lv = {f: rng.randrange(2) for f in tg.FEATURES}
    h.update(tg.render(rng.choice(tg.TOPIC_NAMES), lv, tg.make_cues(rng), rng.getrandbits(32))[0].encode())
cues = tg.make_cues(random.Random(1))
texts, _, _ = tg.sample_texts(random.Random(2), ["chess", "sailing"], 64, cues, {"quote": 1})
texts2, _, _ = tg.sample_grid(random.Random(3), ["chess", "sailing"], 64, cues, ["weekday", "hashtag"])
h.update("".join(texts + texts2).encode())
print(h.hexdigest())
"""


def test_render_deterministic_across_processes():
    digests = set()
    for hashseed in ("0", "1", "4242"):
        env = {**os.environ, "PYTHONHASHSEED": hashseed}
        out = subprocess.run([sys.executable, "-c", DIGEST_CODE], cwd=ROOT, env=env,
                             capture_output=True, text=True, check=True)
        digests.add(out.stdout.strip())
    assert len(digests) == 1


def test_make_cues():
    assert tg.make_cues(random.Random(5)) == tg.make_cues(random.Random(5))
    rng = random.Random(0)
    for _ in range(300):
        c = tg.make_cues(rng)
        assert c.signoff_name != c.greeting_name
        assert c.closing in tg.CLOSINGS and c.hashtag in tg.TAGS


def test_render_rejects_bad_input():
    cues = tg.make_cues(random.Random(0))
    for bad in ({"shouting": 1}, {"quote": 2}, {"quote": -1}, {"quote": 0.5}):
        with pytest.raises(ValueError):
            tg.render("chess", bad, cues, 0)
    with pytest.raises(ValueError):
        tg.render("darts", {}, cues, 0)
    text, flags = tg.render("chess", {"quote": 1}, cues, 0)
    assert set(flags) == set(tg.FEATURES) and flags["quote"] == 1 and flags["weekday"] == 0


# ---- clean flips ----

def test_clean_flip():
    rng = random.Random(1)
    for _ in range(500):
        topic, levels, cues, seed = random_case(rng)
        for f in tg.FEATURES:
            off, off_flags = tg.render(topic, {**levels, f: 0}, cues, seed)
            on, on_flags = tg.render(topic, {**levels, f: 1}, cues, seed)
            assert {k: v for k, v in on_flags.items() if k != f} == {k: v for k, v in off_flags.items() if k != f}
            d_on, d_off = detect_all(on), detect_all(off)
            assert d_on.pop(f) == 1 and d_off.pop(f) == 0, (f, on, off)
            assert d_on == d_off, (f, on, off)
            assert text_flip_is_clean(f, off, on, on_flags, cues), (f, on, off)


@pytest.mark.parametrize("f", tg.FEATURES)
def test_clean_flip_check_catches_collateral_edits(f):
    rng = random.Random(3)
    for _ in range(20):
        topic, levels, cues, seed = random_case(rng)
        off, _ = tg.render(topic, {**levels, f: 0}, cues, seed)
        on, flags = tg.render(topic, {**levels, f: 1}, cues, seed)
        assert text_flip_is_clean(f, off, on, flags, cues)
        for a, b in [("most weekends", "many weekends"), (" every minute", " each minute"), (".", ";")]:
            if a in on:
                assert not text_flip_is_clean(f, off, on.replace(a, b, 1), flags, cues), (f, a)
    with pytest.raises(ValueError):
        undo("shouting", "x", flags, cues)


def test_topic_swap_changes_only_topic_phrases():
    rng = random.Random(2)
    for _ in range(200):
        _, levels, cues, seed = random_case(rng)
        a, b = rng.sample(tg.TOPIC_NAMES, 2)
        text_a, _ = tg.render(a, levels, cues, seed)
        text_b, _ = tg.render(b, levels, cues, seed)
        pairs = [(tg.TOPICS[b][k][i], tg.TOPICS[a][k][i]) for k in ("act", "item", "where") for i in range(len(tg.TOPICS[a][k]))]
        hits = [(pb, pa) for pb, pa in pairs if pb in text_b]
        assert len(hits) == 3
        for pb, pa in hits:
            text_b = text_b.replace(pb, pa)
        assert text_b == text_a


# ---- samplers ----

def topic_of(text):
    found = {t for t, b in tg.TOPICS.items() if any(p in text.lower() for p in b["act"])}
    assert len(found) == 1
    return found.pop()


def test_sample_texts_confound():
    cues = tg.make_cues(random.Random(0))
    topics = ["running", "pottery"]
    texts, y, flags = tg.sample_texts(random.Random(3), topics, 2000, cues, {"exclamation": 1, "hashtag": -1})
    assert y.dtype == np.int64 and (y == np.arange(2000) % 2).all()
    assert all(v.dtype == np.int64 and v.shape == (2000,) for v in flags.values())
    assert (flags["exclamation"] == y).all() and (flags["hashtag"] == 1 - y).all()
    for f in tg.FEATURES:
        if f not in ("exclamation", "hashtag"):
            assert 0.4 < flags[f].mean() < 0.6, f
    assert [topic_of(t) for t in texts] == [topics[v] for v in y]


def test_sample_texts_noise_rates():
    cues = tg.make_cues(random.Random(0))
    topics = ["chess", "fishing"]
    texts, y, flags = tg.sample_texts(random.Random(4), topics, 4000, cues, {"quote": 1, "weekday": -1},
                                      topic_noise=0.2, confound_noise={"quote": 0.1})
    topic_flip = np.array([topic_of(t) != topics[v] for t, v in zip(texts, y)])
    assert abs(topic_flip.mean() - 0.2) < 0.03
    assert abs((flags["quote"] != y).mean() - 0.1) < 0.02
    assert (flags["weekday"] == 1 - y).all()


def test_sample_texts_randomness_is_stable_across_configs():
    cues = tg.make_cues(random.Random(0))
    _, _, f1 = tg.sample_texts(random.Random(5), ["cooking", "sailing"], 300, cues, {"quote": 1})
    _, _, f2 = tg.sample_texts(random.Random(5), ["cooking", "sailing"], 300, cues, {"weekday": -1},
                               topic_noise=0.3, confound_noise={"weekday": 0.2})
    for f in tg.FEATURES:
        if f not in ("quote", "weekday"):
            assert (f1[f] == f2[f]).all(), f


def test_sample_texts_validation():
    cues = tg.make_cues(random.Random(0))
    args = (random.Random(0), ["chess", "sailing"], 8, cues)
    for kw in ({"confound": {"quote": 2}}, {"confound": {"shouting": 1}},
               {"confound": {"quote": 1}, "confound_noise": {"quote": 1.5}},
               {"confound": {"quote": 1}, "confound_noise": {"weekday": 0.1}},
               {"confound": {}, "topic_noise": -0.1}):
        with pytest.raises(ValueError):
            tg.sample_texts(*args, **kw)


@pytest.mark.parametrize("mains", [["quote"], ["quote", "british_spelling"]])
def test_sample_grid_balance(mains):
    cues = tg.make_cues(random.Random(0))
    topics = ["astronomy", "knitting"]
    held = ["exclamation", "lowercase"]
    n = 512
    texts, y, flags = tg.sample_grid(random.Random(6), topics, n, cues, mains, held_off=held)
    assert (y == np.arange(n) % 2).all()
    assert [topic_of(t) for t in texts] == [topics[v] for v in y]
    cells = {}
    for i in range(n):
        key = (int(y[i]), *(int(flags[m][i]) for m in mains))
        cells[key] = cells.get(key, 0) + 1
    assert len(cells) == 2 * 2 ** len(mains) and len(set(cells.values())) == 1
    for f in held:
        assert (flags[f] == 0).all()
    for f in set(tg.FEATURES) - set(mains) - set(held):
        assert 0.4 < flags[f].mean() < 0.6, f


def test_sample_grid_validation():
    cues = tg.make_cues(random.Random(0))
    args = (random.Random(0), ["chess", "sailing"])
    with pytest.raises(ValueError):
        tg.sample_grid(*args, 6, cues, ["quote"])
    with pytest.raises(ValueError):
        tg.sample_grid(*args, 8, cues, ["quote"], held_off=["quote"])
    with pytest.raises(ValueError):
        tg.sample_grid(*args, 8, cues, ["shouting"])


# ---- bank hygiene ----

def test_topic_banks_equal_sizes():
    for t, b in tg.TOPICS.items():
        assert {k: len(v) for k, v in b.items()} == {"act": 4, "item": 4, "where": 3}, t
    assert tg.TOPIC_NAMES == ["gardening", "astronomy", "cooking", "cycling", "chess", "fishing", "knitting",
                              "photography", "running", "birdwatching", "pottery", "sailing"]


def test_topic_phrases_are_clean():
    banned = DAYS | TENSE_WORDS | VARIANT_WORDS | NEGATIVE | PRONOUNS | (TEMPLATE_WORDS - STOP)
    for t, b in tg.TOPICS.items():
        for p in (p for ps in b.values() for p in ps):
            assert re.fullmatch(r"[a-z ]+", p), p   # no digits, quotes, brackets, '#', '!', '?', capitals
            assert not set(p.split()) & banned, (t, p, set(p.split()) & banned)


def test_topic_vocab_not_shared_across_topics():
    seen = {}
    for t, b in tg.TOPICS.items():
        for w in {w for ps in b.values() for p in ps for w in p.split()} - STOP:
            seen.setdefault(w, set()).add(t)
    shared = {w: ts for w, ts in seen.items() if len(ts) > 1}
    assert not shared, shared


def test_no_gemma_token_shared_across_topics_or_with_cue_banks():
    """Word checks miss subword overlaps (e.g. 'dark hilltop' vs 'darkroom', 'marley' -> ' mar' + 'ley')."""
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("google/gemma-2-2b")
    except Exception as e:
        pytest.skip(f"Gemma tokenizer unavailable: {e}")

    def pieces(variants):
        ids = {i for v in variants for i in tok(v, add_special_tokens=False)["input_ids"]}
        return {i for i in ids if len(p := tok.decode([i]).strip().lower()) >= 3 and p not in STOP}

    owners = {}
    for t, b in tg.TOPICS.items():
        for i in pieces(" " + p for ps in b.values() for p in ps):
            owners.setdefault(i, set()).add(t)
    for s in tg.CLOSINGS + tg.NAMES + ["#" + t for t in tg.TAGS] + tg.QUOTES + tg.PS_LINES:
        for i in pieces(v for x in (s, s.lower()) for v in (x, " " + x)):   # line start or after a space
            owners.setdefault(i, set()).add("cue banks")
    shared = {tok.decode([i]): o for i, o in owners.items() if len(o) > 1}
    assert not shared, shared


def test_cue_banks_are_clean():
    vocab = TOPIC_VOCAB | set(tg.TOPIC_NAMES)
    banks = {"closings": tg.CLOSINGS, "names": tg.NAMES, "tags": tg.TAGS, "quotes": tg.QUOTES,
             "ps": tg.PS_LINES, "numbers": tg.NUMBERS, "adjectives": [a for p in tg.ADJ_PAIRS for a in p],
             "templates": TEMPLATES}
    for name, bank in banks.items():
        for s in bank:
            assert not set(words(s)) & vocab, (name, s)
            assert not re.search(r'[0-9"!?#()\[\]]', s.replace('"{quote}', "")), (name, s)
    for s in tg.CLOSINGS + tg.NAMES + tg.TAGS + tg.QUOTES + tg.PS_LINES:
        low = s.lower()
        assert not any(d in low for d in DAYS), s
        assert not set(words(s)) & (PRONOUNS | NEGATIVE | VARIANT_WORDS | TENSE_WORDS), s
    for tag in tg.TAGS:
        assert not any(w in tag for w in vocab if len(w) >= 4), tag
    for name in tg.NAMES:
        assert not any(w in name.lower() for w in vocab if len(w) >= 4), name
    assert len(tg.CLOSINGS) == 8 and len(set(tg.NAMES)) == 30 and len(set(tg.TAGS)) == 15


def test_every_s4_template_has_a_spelling_variant():
    variant = re.compile(r"\b(" + "|".join(tg.AMERICAN) + r")\b")
    for present, past in tg.S4:
        assert variant.search(present) and variant.search(past)


def test_render_rejects_ambiguous_seeds():
    cues = tg.make_cues(random.Random(0))
    for bad in (None, True, 1.5):
        with pytest.raises(TypeError):
            tg.render("chess", {}, cues, bad)
    with pytest.raises(ValueError):
        tg.render("chess", {}, cues, -5)   # random.Random(-5) == random.Random(5)
    assert tg.render("chess", {}, cues, np.int64(5)) == tg.render("chess", {}, cues, 5)
    assert tg.render("chess", {}, cues, "a")[0] != tg.render("chess", {}, cues, "b")[0]
