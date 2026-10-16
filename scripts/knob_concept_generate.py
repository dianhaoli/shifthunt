"""Knob concept: generate standalone sentences that express one meaning-level concept (CRIME / THE LAW) with Haiku.

    python scripts/knob_concept_generate.py            # writes .cache/knob_concept/raw.jsonl (+ .usage)
    python scripts/knob_concept_generate.py --filter   # writes .cache/knob_concept/forms.json (shown / heldout)

The concept: the sentence says the man had a brush with crime or law enforcement (police, theft, burglary,
arrest, court, fines, jail, detectives, witnesses ...). Base paragraphs almost never touch it (crime/police
word family hits 0.7% of bank paragraphs). Several requests with different angles, each asking for varied
vocabulary, so that many sentences avoid the obvious words.
Filter: freetext canonical-form rules that apply to one inserted sentence (ascii, no ! ? " ( ) # : ; ...,
no she/her, no weekday or P.S., one sentence ending in ".", no digits, 5-13 words); dedupe on the first four
words and on the exact lowercase text. Split: random.Random("knob_concept:split") shuffles the kept forms,
the first 100 are "shown", the next 50 "heldout".
"""
import argparse
import json
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from freetext_generate import load_key  # noqa: E402

OUT = ROOT / ".cache" / "knob_concept"
ANGLES = [
    "being stopped, questioned, warned, ticketed or fined by officers",
    "his things being stolen, his home or shed or car being broken into, or him being robbed or swindled",
    "court, judges, juries, lawyers, testifying, being sued, sentences, probation and jail",
    "witnessing a crime, reporting it, helping an investigation, detectives, suspects, line-ups",
    "him getting into trouble with the law in small ways: trespassing, shoplifting accusations, a night in a cell",
    "mixed: any brush with crime or law enforcement, told indirectly without the words police, crime, steal or arrest",
]
PROMPT = """Write {n} different short English sentences. Each sentence must, on its own, clearly say that a man
(called "he", "him" or "his", never named) had a brush with crime or law enforcement. Angle for this batch: {angle}.

Rules for every sentence:
- 6 to 12 words, one sentence, ends with a single period.
- Plain past or present tense, neutral tone, no hobbies or sports.
- Use only letters, spaces, commas, apostrophes and the final period. No digits, no ! ? " ( ) : ; - or quotes.
- Never use she, her, a weekday name, or the letters P.S.
- Vary the wording as much as possible: different verbs, nouns and sentence shapes. Many sentences should avoid
  the most common words (police, crime, arrest, steal, stolen, thief) and convey the idea through other words.

Return only a JSON list of strings."""


def generate(args):
    import anthropic
    client = anthropic.Anthropic(api_key=load_key(Path(".env")), max_retries=4)
    OUT.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()

    def one(angle):
        msg = client.messages.create(model="claude-haiku-5-5", max_tokens=4000, thinking={"type": "disabled"},
                                     messages=[{"role": "user", "content": PROMPT.format(n=args.n, angle=angle)}])
        text = "".join(b.text for b in msg.content if b.type == "text")
        s, e = text.find("["), text.rfind("]")
        try:
            sents = json.loads(text[s:e + 1])
        except Exception:
            sents = []
        with lock:
            with open(OUT / "raw.jsonl.usage", "a") as f:
                f.write(json.dumps({"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}) + "\n")
            with open(OUT / "raw.jsonl", "a") as f:
                for x in sents:
                    if isinstance(x, str):
                        f.write(json.dumps({"angle": angle, "text": x.strip()}) + "\n")
        return len(sents)

    with ThreadPoolExecutor(6) as ex:
        print("generated", sum(ex.map(one, ANGLES)))


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def reasons(s):
    r = []
    if not s.isascii() or "\n" in s:
        r.append("non_ascii")
    if re.search(r'[!?"();:#\[\]{}*_/^\-]', s) or ".." in s or re.search(r"\d", s):
        r.append("forbidden_char")
    if re.search(r"(?i)\b(she|her|hers|herself)\b", s):
        r.append("female")
    if re.search(r"(?i)\b(" + "|".join(WEEKDAYS) + r")", s) or re.search(r"(?i)p\.s\.", s):
        r.append("weekday_or_ps")
    if not s.endswith(".") or s.count(".") != 1 or not s[0].isupper():
        r.append("sentence")
    if not 5 <= len(s.split()) <= 13:
        r.append("length")
    return r


def filt():
    from collections import Counter
    rows = [json.loads(x) for x in (OUT / "raw.jsonl").read_text().splitlines()]
    kept, seen, drop = [], set(), Counter()
    for row in rows:
        s = " ".join(row["text"].split())
        r = reasons(s)
        k4, kx = " ".join(s.lower().split()[:4]), s.lower()
        if not r and (k4 in seen or kx in seen):
            r = ["duplicate"]
        if r:
            drop.update(r)
            continue
        seen |= {k4, kx}
        kept.append(s)
    random.Random("knob_concept:split").shuffle(kept)
    out = {"shown": kept[:100], "heldout": kept[100:150], "spare": kept[150:]}
    (OUT / "forms.json").write_text(json.dumps(out, indent=0))
    print("raw", len(rows), "kept", len(kept), "drop", dict(drop), {k: len(v) for k, v in out.items()})
    usage = [json.loads(x) for x in (OUT / "raw.jsonl.usage").read_text().splitlines()]
    i, o = sum(u["input"] for u in usage), sum(u["output"] for u in usage)
    print(f"usage in={i} out={o} cost~${i * 0.1e-6 + o * 0.5e-6:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", action="store_true")
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    filt() if a.filter else generate(a)
