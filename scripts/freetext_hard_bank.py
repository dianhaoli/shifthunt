"""Filter the free-text bank for shifthunt/freetext_hard.py (CPU; tokenizer only).

    python scripts/freetext_hard_bank.py   # .cache/freetext/bank.json -> .cache/freetext/bank_hard.json

Drops paragraphs that already contain hedge or counterfactual words (freetext_hard.BASE_EXCLUDE), and those whose
worst-case render (every additive feature of the hard substrate at its longest form) exceeds 126 content tokens, so no edit is ever truncated.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from shifthunt import freetext_hard as fh  # noqa: E402
from shifthunt.substrate import MAX_CONTENT_TOKENS, MODEL_ID  # noqa: E402


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    n = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])  # noqa: E731
    L = lambda xs: max(xs, key=len)  # noqa: E731

    def worst_case(p):
        s = split(p)
        s[0] = s[0][:-1] + L(fh.HEDGES) + " " + L(fh.ASIDES) + "."
        s[1] = s[1][:-1] + L(fh.HEDGES) + "."
        s[2] = s[2][:-1] + L(fh.HEDGES) + "."
        body = " ".join([s[0], L(fh.QUESTIONS), L([b for _, b in fh.CF_PAIRS]), *s[1:]])
        return "\n".join(["Hello everyone,", body + " #" + L(fh.ft.TAGS), L(fh.CLOSINGS) + "!", L(fh.ft.NAMES),
                          L(fh.PS_QUESTIONS + fh.PS_STATEMENTS)])
    split = fh.split_sentences
    extra = 0
    src = json.loads((ROOT / ".cache/freetext/bank.json").read_text())
    out, drop_words, drop_len = {}, 0, 0
    for t, pars in src.items():
        keep = []
        for p in pars:
            if fh.BASE_EXCLUDE.search(p):
                drop_words += 1
            elif n(worst_case(p)) + extra > MAX_CONTENT_TOKENS - 2:
                drop_len += 1
            else:
                keep.append(p)
        out[t] = keep
    (ROOT / ".cache/freetext/bank_hard.json").write_text(json.dumps(out, indent=0))
    print("kept per topic:", {t: len(v) for t, v in out.items()}, "total", sum(map(len, out.values())),
          f"| dropped: words {drop_words}, length {drop_len} (extra worst-case tokens {extra})")


if __name__ == "__main__":
    main()
