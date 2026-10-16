"""Check shifthunt/freetext_hard.py (CPU): detectors and exact regexes agree with flags, flips are local, <= 128 tokens.

    python scripts/freetext_hard_check.py [--n 3000]
"""
import argparse
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=3000)
    args = ap.parse_args()
    from shifthunt import freetext_hard as fh
    from shifthunt.substrate import MAX_CONTENT_TOKENS, MODEL_ID
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    rng = random.Random(0)
    bad, rx_bad, flip_bad, lens = Counter(), Counter(), Counter(), []
    for i in range(args.n):
        topic = rng.choice(fh.TOPIC_NAMES)
        lv = fh._imply({f: int(rng.random() < 0.5) for f in fh.FEATURES})
        seed = rng.getrandbits(32)
        text, flags = fh.render(topic, lv, None, seed)
        det = fh.detect(text)
        for f in fh.FEATURES:
            bad[f] += det[f] != flags[f]
            rx_bad[f] += bool(re.search(fh.SUBMISSION[f], text)) != bool(flags[f])
        lens.append(len(tok(text, add_special_tokens=False)["input_ids"]))
        if i % 10 == 0:
            for f in fh.FEATURES:
                lv2 = dict(lv)
                lv2[f] = 1 - lv2[f]
                for child, parent in fh.IMPLIES.items():
                    if lv2[child] and not lv2[parent]:
                        lv2[parent if f == child else child] = 1 if f == child else 0
                d2 = fh.detect(fh.render(topic, lv2, None, seed)[0])
                if {g for g in fh.FEATURES if d2[g] != det[g]} != {g for g in fh.FEATURES if lv2[g] != lv[g]}:
                    flip_bad[f] += 1
    print("detector mismatches:", {k: v for k, v in bad.items() if v} or "none")
    print("regex mismatches:", {k: v for k, v in rx_bad.items() if v} or "none")
    print("non-local flips:", dict(flip_bad) or "none")
    print(f"tokens: max {max(lens)}, mean {sum(lens) / len(lens):.1f}, over {MAX_CONTENT_TOKENS}: "
          f"{sum(x > MAX_CONTENT_TOKENS for x in lens)}")
    ok = not any(bad.values()) and not any(rx_bad.values()) and not flip_bad and max(lens) <= MAX_CONTENT_TOKENS
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
