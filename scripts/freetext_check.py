"""Check the free-text substrate (CPU): detectors agree with flags, flips are local, notes fit 128 tokens.

    python scripts/freetext_check.py [--n 3000] [--bank .cache/freetext/bank.json]

1. n random notes (random topic, levels, seed; IMPLIES enforced): detect(text) == flags for every feature.
2. For n/10 notes, flipping each feature (with its implication partner when needed) changes exactly the
   detectors of the flipped features and nothing else.
3. Token counts of the n notes (BOS excluded) are <= 128: no edit is ever truncated away.
4. sample_texts / sample_grid: confounded features agree exactly with the label; grid mains are balanced.
"""
import argparse
import os
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--bank", default=None)
    args = ap.parse_args()
    if args.bank:
        os.environ["SHIFTHUNT_FREETEXT_BANK"] = str(args.bank)
    from shifthunt import freetext as ft
    from shifthunt.substrate import MAX_CONTENT_TOKENS, MODEL_ID
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    rng = random.Random(0)
    bad, flipbad, lens = Counter(), Counter(), []
    for i in range(args.n):
        topic = rng.choice(ft.TOPIC_NAMES)
        lv = ft._imply({f: int(rng.random() < 0.5) for f in ft.FEATURES})
        seed = rng.getrandbits(32)
        text, flags = ft.render(topic, lv, None, seed)
        det = ft.detect(text)
        for f in ft.FEATURES:
            if det[f] != flags[f]:
                bad[f] += 1
                if bad[f] <= 2:
                    print(f"MISMATCH {f}: flag={flags[f]} det={det[f]}\n{text}\n")
        lens.append(len(tok(text, add_special_tokens=False)["input_ids"]))
        if i % 10 == 0:
            for f in ft.FEATURES:
                lv2 = dict(lv)
                lv2[f] = 1 - lv2[f]
                changed = {f}
                for child, parent in ft.IMPLIES.items():
                    if lv2[child] and not lv2[parent]:
                        lv2[parent if f == child else child] = 1 if f == child else 0
                        changed.add(parent if f == child else child)
                det2 = ft.detect(ft.render(topic, lv2, None, seed)[0])
                diff = {g for g in ft.FEATURES if det2[g] != det[g]}
                if diff != {g for g in changed if lv2[g] != lv[g]}:
                    flipbad[f] += 1
    print(f"detector mismatches over {args.n} notes: {dict(bad) or 'none'}")
    print(f"non-local flips: {dict(flipbad) or 'none'}")
    over = sum(x > MAX_CONTENT_TOKENS for x in lens)
    print(f"tokens: max {max(lens)}, mean {sum(lens) / len(lens):.1f}, over {MAX_CONTENT_TOKENS}: {over}")
    # samplers
    topics = ft.TOPIC_NAMES[:2]
    conf = {"signoff_excl": 1, "ps_question": -1, "weekday": 1}
    texts, y, flags = ft.sample_texts(random.Random(1), topics, 256, None, conf)
    for f, s in conf.items():
        agree = ((flags[f] == 1) == ((y == 1) if s > 0 else (y == 0))).mean()
        print(f"sample_texts confound {f} agreement with label: {agree:.3f}")
    texts, y, flags = ft.sample_grid(random.Random(2), topics, 256, None, ["signoff_excl"])
    print(f"grid main signoff_excl mean {flags['signoff_excl'].mean():.3f}, signoff mean "
          f"{flags['signoff'].mean():.3f}, corr(signoff_excl, topic) "
          f"{((flags['signoff_excl'] - .5) * (y - .5)).mean() * 4:.3f}")
    ok = not bad and not flipbad and not over
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
