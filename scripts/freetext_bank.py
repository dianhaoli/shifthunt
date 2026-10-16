"""Filter generated paragraphs into the free-text bank (CPU; tokenizer only).

    python scripts/freetext_bank.py --raw .cache/freetext/raw.jsonl --out .cache/freetext/bank.json

Keeps a paragraph only if it has the canonical form shifthunt/freetext.py relies on (see its docstring) and
its worst-case render (every additive feature on, longest forms) fits in 128 content tokens. Drops exact and
near duplicates (same first six words). Prints counts per topic and per drop reason.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import freetext as ft  # noqa: E402
from shifthunt.substrate import MAX_CONTENT_TOKENS, MODEL_ID  # noqa: E402

ABBREV = re.compile(r"\b(Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|etc|e\.g|i\.e|a\.m|p\.m|U\.S)\.", re.I)


def reasons(p):
    r = []
    if not p.isascii() or "\n" in p:
        r.append("non_ascii_or_newline")
    if re.search(r'[!?"();:#\[\]{}*_/^]', p) or "..." in p:
        r.append("forbidden_char")
    if re.search(r"(?i)\b(she|her|hers|herself)\b", p):
        r.append("female_pronoun")
    if not re.search(r"\b(he|He|him|his|His)\b", p):
        r.append("no_he")
    if re.search(r"(?i)\b(" + "|".join(ft.WEEKDAYS) + r")", p) or re.search(r"(?i)p\.s\.", p):
        r.append("weekday_or_ps")
    if ABBREV.search(p):
        r.append("abbreviation")
    sents = ft.split_sentences(p)
    if not p.endswith(".") or not 3 <= len(sents) <= 6 or any(not s.endswith(".") or s.endswith("..")
                                                              for s in sents):
        r.append("sentences")
    if not 30 <= len(p.split()) <= 70:
        r.append("length")
    return r


def worst_case(p):
    sents = ft.split_sentences(p)
    longest = lambda xs: max(xs, key=len)  # noqa: E731
    sents[0] = sents[0][:-1] + " " + longest(ft.ASIDES) + ". " + longest(ft.EMOTICONS)
    sents[-1] = sents[-1][:-1] + "..."
    body = " ".join([sents[0], longest(ft.QUESTIONS), longest(ft.WEEKDAY_SENTENCES).format(d="Wednesday"),
                     longest(ft.QUOTE_SENTENCES).format(q=longest(ft.QUOTES).lower()), *sents[1:]])
    return "\n".join(["Hello everyone,", body + " #" + longest(ft.TAGS), longest(ft.CLOSINGS) + "!",
                      longest(ft.NAMES), longest(ft.PS_QUESTIONS + ft.PS_STATEMENTS)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", required=True, type=Path, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    drop, kept, seen = Counter(), defaultdict(list), set()
    for line in (x for f in args.raw for x in f.read_text().splitlines()):
        row = json.loads(line)
        p = " ".join(row["text"].split())
        key = " ".join(p.lower().split()[:6])
        r = reasons(p)
        if key in seen:
            r.append("duplicate")
        if not r and len(tok(worst_case(p), add_special_tokens=False)["input_ids"]) > MAX_CONTENT_TOKENS - 2:
            r.append("too_long")
        if r:
            drop.update(r)
            continue
        seen.add(key)
        kept[row["topic"]].append(p)
    args.out.write_text(json.dumps(kept, indent=0))
    print("kept per topic:", {t: len(v) for t, v in kept.items()}, "total", sum(map(len, kept.values())))
    print("drop reasons (a paragraph can have several):", dict(drop.most_common()))


if __name__ == "__main__":
    main()
