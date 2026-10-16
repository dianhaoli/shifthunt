"""Clean-flip checker: is `on` exactly `off` plus one feature's edit?

undo(f, on, ...) reverses feature f's edit; text_flip_is_clean then requires the
result to equal the render with f off, so any collateral change (one no detector
would see) fails. Used by tests/test_textgen.py and scripts/check_textgen.py.
"""

import re

from shifthunt import textgen as tg


def _sub_words(table, text):
    return re.sub(r"\b(" + "|".join(table) + r")\b", lambda m: table[m.group(1)], text)


def _past_to_present():
    """Past word -> present word, read off the (present, past) template pairs in both spellings."""
    out = {"loved": "loves", "hated": "hates"}
    for present, past in [tg.S1, tg.S2, *tg.S3, *tg.S4, tg.S5, tg.QUOTE, tg.WEEKDAY]:
        for pr, pa in [(present, past), (_sub_words(tg.AMERICAN, present), _sub_words(tg.AMERICAN, past))]:
            out |= {a: b for a, b in zip(re.findall(r"[a-z]+", pa), re.findall(r"[a-z]+", pr)) if a != b}
    return out


PAST_TO_PRESENT = _past_to_present()
NEG_TO_POS = {neg: pos for pos, neg in tg.ADJ_PAIRS} | {"hates": "loves", "hated": "loved"}
SHE_TO_HE = {"She": "He", "she": "he", "Her": "His", "her": "his"}   # after "with her" -> "with him"
# Inserted sentences or words: removing exactly one match must give the note with the feature off.
INSERTED = {
    "quote": re.compile(r'( |\n- )(his|her) coach always (says|said), "[^"\n]*"', re.I),
    "weekday": re.compile(r"( |\n- )(he|she) (goes|went) again on (%s)[.!]" % "|".join(tg.WEEKDAYS), re.I),
    "parenthetical": re.compile(re.escape(tg.PAREN)),
}


def unbullet(text):
    out = []
    for line in text.split("\n"):
        if line.startswith("- ") and out and out[-1][1]:
            out[-1] = (out[-1][0] + " " + line[2:], True)
        else:
            out.append((line[2:], True) if line.startswith("- ") else (line, False))
    return "\n".join(s for s, _ in out)


def undo(f, on, lv, cues):
    """Reverse feature f's edit on `on` (levels lv have f on); None if its edit is not where expected."""
    def cased(s):
        return s.lower() if lv["lowercase"] else s

    lines = on.split("\n")
    if f in INSERTED:
        text, k = INSERTED[f].subn("", on)
        return text if k == 1 else None
    if f == "exclamation":
        return on.replace("!", ".")
    if f == "british_spelling":
        return _sub_words(tg.AMERICAN, on)
    if f == "bullet_list":
        return unbullet(on)
    if f == "past_tense":
        return _sub_words(PAST_TO_PRESENT, on)
    if f == "she_pronoun":
        return _sub_words(SHE_TO_HE, re.sub(r"\bwith her\b", "with him", on))
    if f == "question_ending":
        stop = "!" if lv["exclamation"] else "."
        return on.replace(cased("Would you try"), cased("You should try")).replace("?", stop)
    if f == "negative_sentiment":
        return _sub_words(NEG_TO_POS, on)
    if f == "greeting":
        return "\n".join(lines[1:]) if lines[0] == cased(f"Hi {cues.greeting_name},") else None
    if f == "postscript":
        return "\n".join(lines[:-1]) if lines[-1].startswith(cased("P.S. ")) else None
    if f == "hashtag":
        tag = cased("#" + cues.hashtag)
        return "\n".join(l for l in lines if l != tag) if lines.count(tag) == 1 else None
    if f == "signoff":
        pair = [cased(cues.closing + ","), cased(cues.signoff_name)]
        hits = [i for i in range(len(lines) - 1) if lines[i:i + 2] == pair]
        return "\n".join(lines[:hits[0]] + lines[hits[0] + 2:]) if len(hits) == 1 else None
    raise ValueError(f"no undo for {f!r}")


def text_flip_is_clean(f, off, on, lv, cues):
    """True if `on` is `off` plus only feature f's edit (lv: levels of `on`)."""
    if on == off:
        return False
    if f == "lowercase":
        return on == off.lower()
    return undo(f, on, lv, cues) == off
