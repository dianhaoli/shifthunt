import random
import re

import numpy as np
import pytest

from shifthunt import textgen as tg
from shifthunt.detectors import DETECTORS, Detector, balanced_accuracy, detect, detect_all


def test_detectors_cover_features():
    assert set(DETECTORS) == set(tg.FEATURES)


def test_detector_agreement_on_mixed_renders():
    rng = random.Random(11)
    texts, rows = [], []
    for _ in range(3000):
        levels = {f: rng.randrange(2) for f in tg.FEATURES}
        text, flags = tg.render(rng.choice(tg.TOPIC_NAMES), levels, tg.make_cues(rng), rng.getrandbits(32))
        texts.append(text)
        rows.append(flags)
    flags = {f: np.array([r[f] for r in rows]) for f in tg.FEATURES}
    acc = balanced_accuracy(texts, flags)
    print("\n" + "\n".join(f"{f:20s} {a:.3f}" for f, a in acc.items()))
    inexact = {f: a for f, a in acc.items() if a != 1.0}   # exact by design; the spec floor is 0.98
    assert not inexact, inexact


def test_balanced_accuracy_validates_and_flags_single_class():
    texts = ["a!", "b.", "c!"]
    assert balanced_accuracy(texts, {"exclamation": [1, 0, 1]}) == {"exclamation": 1.0}
    assert balanced_accuracy(texts, {"exclamation": np.array([0, 0, 1])}) == {"exclamation": 0.75}
    for bad in ([1, 0], [1, 0, 2], [1, 0, 0.5]):
        with pytest.raises(ValueError):
            balanced_accuracy(texts, {"exclamation": bad})
    # One class alone cannot show a detector works: a held-off feature scores NaN, not 1.0.
    assert np.isnan(balanced_accuracy(texts, {"exclamation": [0, 0, 0]})["exclamation"])
    assert np.isnan(balanced_accuracy([], {"exclamation": []})["exclamation"])


def test_detect_all_matches_detect():
    text, _ = tg.render("cycling", {"quote": 1, "lowercase": 1}, tg.make_cues(random.Random(0)), 3)
    assert detect_all(text) == {f: int(detect(text, f)) for f in tg.FEATURES}


@pytest.mark.parametrize("text, feature, expected", [
    ("He keeps a colour-coded log.", "bullet_list", False),
    ("- He keeps a log.", "bullet_list", True),
    ("he spends weekends there.", "lowercase", True),
    ("He spends weekends there.", "lowercase", False),
    ("Hi Sam,\nHe spends weekends there.", "greeting", True),
    ("He spends weekends there.\nHi Sam,", "greeting", False),
    ("He spends weekends there.\nP.S. Call me later.", "postscript", True),
    ("He spends weekends there.\nP.S. Call me later.\nCheers,\nSam", "postscript", False),
    ("He spends weekends there.\nCheers,\nSam", "signoff", True),
    ("Hi Sam,\nHe spends weekends there.", "signoff", False),
    ("Everyone there is a hero.", "she_pronoun", False),
    ("Her friends think so.", "she_pronoun", True),
    ("He goes on Mondays.", "weekday", True),
    ("#mondaymood", "weekday", False),
    ("#mood", "hashtag", True),
    ("He owns #2 pencils.", "hashtag", False),
])
def test_detector_edge_cases(text, feature, expected):
    assert detect(text, feature) is expected


def test_detector_validates_scope():
    with pytest.raises(ValueError):
        Detector(r"x", "middle_line")
    with pytest.raises(re.error):
        Detector(r"(")
