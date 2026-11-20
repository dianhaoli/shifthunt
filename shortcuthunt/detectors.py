"""One regex per feature, for checking generator output (and agent-facing cue names).

Ground truth always comes from textgen's flags; these detectors are expected to
agree with it exactly on generator output. Every pattern except `lowercase` is
case-insensitive so it still fires on lowercased notes. Scopes: 'any' searches
the whole note, 'first_line' / 'last_line' only that line.

Flags and detectors are both defined on the full rendered note. The model sees
only the first substrate.MAX_CONTENT_TOKENS content tokens, which can cut a late cue (P.S., signoff,
hashtag, closing question) off entirely or mid-edit ("...\\nP"). On such a window
a detector can miss a cue whose flag is 1, so anything about what the model sees
needs its own visibility bit (e.g. detect() on the decoded window), not the flag.
"""

import re
from dataclasses import dataclass

I, M = re.IGNORECASE, re.MULTILINE


@dataclass(frozen=True)
class Detector:
    pattern: str
    scope: str = "any"
    flags: int = 0

    def __post_init__(self):
        if self.scope not in ("any", "first_line", "last_line"):
            raise ValueError(f"bad scope {self.scope!r}")
        re.compile(self.pattern, self.flags)

    def match(self, text: str) -> bool:
        if self.scope == "first_line":
            text = text.split("\n", 1)[0]
        elif self.scope == "last_line":
            text = text.rsplit("\n", 1)[-1]
        return re.search(self.pattern, text, self.flags) is not None


DETECTORS = {
    "exclamation": Detector(r"!"),
    "lowercase": Detector(r"\A[^A-Z]*\Z"),
    "signoff": Detector(r"^[a-z ]+,\n[a-z]+$", flags=I | M),   # "Closing," then a one-word name line
    "british_spelling": Detector(
        r"\b(neighbour|favourite|colour|centre|grey|organis\w*|practis\w*|theatre)\b", flags=I),
    "bullet_list": Detector(r"^- ", flags=M),
    "past_tense": Detector(r"\b(spent|owned|kept|loved|hated)\b", flags=I),
    "she_pronoun": Detector(r"\b(she|her)\b", flags=I),
    "question_ending": Detector(r"\?"),
    "quote": Detector(r'"'),
    "greeting": Detector(r"^hi [a-z]+,$", "first_line", I),
    "hashtag": Detector(r"^#\w+$", flags=M),
    "postscript": Detector(r"^p\.s\. ", "last_line", I),
    "weekday": Detector(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?\b", flags=I),
    "parenthetical": Detector(r"\([^()\n]*\)"),
    "negative_sentiment": Detector(
        r"\b(hates|hated|stressful|dreadful|frustrating|tiresome|miserable|tedious)\b", flags=I),
}


def detect(text: str, feature: str) -> bool:
    return DETECTORS[feature].match(text)


def detect_all(text: str) -> dict:
    return {f: int(d.match(text)) for f, d in DETECTORS.items()}


def balanced_accuracy(texts, flags) -> dict:
    """Per-feature balanced accuracy of the detectors against ground-truth 0/1 flags.

    A feature whose flags are all one value (e.g. held off) gets NaN: one class
    alone cannot show that the detector separates on from off.
    """
    texts = list(texts)
    out = {}
    for f, truth in flags.items():
        truth = list(truth)
        if len(truth) != len(texts):
            raise ValueError(f"{f}: {len(truth)} flags for {len(texts)} texts")
        if set(truth) - {0, 1}:
            raise ValueError(f"{f}: flags must be 0/1, got {set(truth) - {0, 1}}")
        pred = [detect(t, f) for t in texts]
        rates = []
        for cls in (0, 1):
            idx = [i for i, v in enumerate(truth) if v == cls]
            if idx:
                rates.append(sum(pred[i] == bool(cls) for i in idx) / len(idx))
        out[f] = sum(rates) / 2 if len(rates) == 2 else float("nan")
    return out


def submission_regex(feature):
    """The detector as a submission cue: (pattern with its flags inlined, scope). The grader runs
    re.search with no flags, so IGNORECASE / MULTILINE become a (?i) / (?m) prefix."""
    d = DETECTORS[feature]
    inline = ("i" if d.flags & I else "") + ("m" if d.flags & M else "")
    return (f"(?{inline})" if inline else "") + d.pattern, d.scope
