"""Sanity report for the text generator: determinism, clean flips, detector agreement,
sampler balance, and Gemma token lengths (including whether cue edits survive the
content-token window, substrate.MAX_CONTENT_TOKENS, and whether detectors still agree with the flags on that window).

    python scripts/check_textgen.py [--out report.json] [--skip-tokens]
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import textgen as tg  # noqa: E402
from shifthunt.detectors import balanced_accuracy, detect_all  # noqa: E402
from shifthunt.flipcheck import text_flip_is_clean  # noqa: E402
from shifthunt.substrate import MAX_CONTENT_TOKENS as WINDOW  # noqa: E402


def random_case(rng):
    levels = {f: rng.randrange(2) for f in tg.FEATURES}
    return rng.choice(tg.TOPIC_NAMES), levels, tg.make_cues(rng), rng.getrandbits(32)


def digest(n=200, seed=7):
    rng = random.Random(seed)
    return hashlib.sha256("".join(tg.render(*random_case(rng))[0] for _ in range(n)).encode()).hexdigest()


def check_determinism():
    rng = random.Random(0)
    same = sum(tg.render(*c) == tg.render(*c) for c in (random_case(rng) for _ in range(200)))
    code = "from scripts.check_textgen import digest; print(digest())"
    procs = {h: subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True,
                               env={**os.environ, "PYTHONHASHSEED": h}).stdout.strip() for h in ("0", "1", "4242")}
    return {"identical_in_process": same, "of": 200, "cross_process_match": len({digest(), *procs.values()}) == 1}


def check_clean_flips(n=500):
    """Per feature: flipping it must change its flag and detector only, and the text only by its edit."""
    rng = random.Random(1)
    bad = {f: 0 for f in tg.FEATURES}
    for _ in range(n):
        topic, levels, cues, seed = random_case(rng)
        for f in tg.FEATURES:
            off, fo = tg.render(topic, {**levels, f: 0}, cues, seed)
            on, fn = tg.render(topic, {**levels, f: 1}, cues, seed)
            do, dn = detect_all(off), detect_all(on)
            ok = (dn.pop(f) == 1 and do.pop(f) == 0 and dn == do
                  and all(fo[k] == fn[k] for k in tg.FEATURES if k != f)
                  and text_flip_is_clean(f, off, on, fn, cues))
            bad[f] += not ok
    return {"cases": n, "violations": bad}


def check_detectors(n=3000):
    rng = random.Random(11)
    texts, rows = [], []
    for _ in range(n):
        text, flags = tg.render(*random_case(rng))
        texts.append(text)
        rows.append(flags)
    return balanced_accuracy(texts, {f: [r[f] for r in rows] for f in tg.FEATURES})


def check_grid():
    cues = tg.make_cues(random.Random(0))
    out = {}
    for mains in (["quote"], ["quote", "british_spelling"]):
        _, y, flags = tg.sample_grid(random.Random(6), ["astronomy", "knitting"], 256, cues, mains,
                                     held_off=["exclamation"])
        cells = {}
        for i in range(len(y)):
            key = "topic%d " % y[i] + " ".join(f"{m}={flags[m][i]}" for m in mains)
            cells[key] = cells.get(key, 0) + 1
        out["+".join(mains)] = {"cells": cells, "held_off_max": int(flags["exclamation"].max()),
                                "other_feature_rates": {f: round(float(flags[f].mean()), 3) for f in tg.FEATURES
                                                        if f not in mains and f != "exclamation"}}
    return out


def topic_of(text):
    return next(t for t, bank in tg.TOPICS.items() if any(p in text.lower() for p in bank["act"]))


def check_confound(n=2000):
    cues = tg.make_cues(random.Random(0))
    confound = {"exclamation": 1, "hashtag": -1}
    out = {}
    for name, kw in [("noise=0", {}),
                     ("topic_noise=0.1, exclamation noise=0.1",
                      {"topic_noise": 0.1, "confound_noise": {"exclamation": 0.1}})]:
        texts, y, flags = tg.sample_texts(random.Random(3), ["running", "pottery"], n, cues, confound, **kw)
        topic_flip = np.mean([topic_of(t) != ["running", "pottery"][v] for t, v in zip(texts, y)])
        out[name] = {"agree_with_y": {f: round(float((flags[f] == y).mean()), 3) for f in tg.FEATURES},
                     "topic_flip_rate": round(float(topic_flip), 3)}
    return out


def check_tokens(n=500):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("google/gemma-2-2b")

    def ids(text):
        return tok(text, add_special_tokens=False)["input_ids"]

    def stats(lengths):
        a = np.array(lengths)
        return {"mean": round(float(a.mean()), 1), "p50": float(np.median(a)), "p95": float(np.percentile(a, 95)),
                "max": int(a.max()), "frac_over_window": round(float((a > WINDOW).mean()), 3)}

    rng = random.Random(21)
    cases = [random_case(rng) for _ in range(n)]
    lengths, cost = [], {f: [] for f in tg.FEATURES}
    # Among notes over the window, per feature: on, edit fully hidden, and detector vs flag on the window text.
    window = {f: {"on": 0, "edit_hidden": 0, "detector_misses": 0, "detector_false_alarms": 0} for f in tg.FEATURES}
    for topic, levels, cues, seed in cases:
        on_ids = ids(tg.render(topic, levels, cues, seed)[0])
        lengths.append(len(on_ids))
        for f in tg.FEATURES:
            cost[f].append(len(ids(tg.render(topic, {**levels, f: 1}, cues, seed)[0]))
                           - len(ids(tg.render(topic, {**levels, f: 0}, cues, seed)[0])))
        if len(on_ids) <= WINDOW:
            continue
        seen = detect_all(tok.decode(on_ids[:WINDOW]))
        for f, w in window.items():
            if levels[f]:
                off_ids = ids(tg.render(topic, {**levels, f: 0}, cues, seed)[0])
                w["on"] += 1
                w["edit_hidden"] += on_ids[:WINDOW] == off_ids[:WINDOW]
                w["detector_misses"] += not seen[f]
            else:
                w["detector_false_alarms"] += seen[f]
    all_on = {f: 1 for f in tg.FEATURES}
    on_lengths = [len(ids(tg.render(tg.TOPIC_NAMES[s % 12], all_on, tg.make_cues(rng), s)[0])) for s in range(300)]
    plain = [len(ids(tg.render(tg.TOPIC_NAMES[s % 12], {}, tg.make_cues(rng), s)[0])) for s in range(300)]
    return {"fair_coin": stats(lengths), "all_on": stats(on_lengths), "plain": stats(plain),
            "n_over_window": sum(x > WINDOW for x in lengths), "window": window,
            "token_cost": {f: round(float(np.mean(c)), 2) for f, c in cost.items()}}


def examples():
    cues = tg.make_cues(random.Random(4))
    half = {f: i % 2 for i, f in enumerate(tg.FEATURES)}
    return [tg.render("gardening", {}, cues, 1)[0], tg.render("sailing", half, cues, 2)[0],
            tg.render("chess", {f: 1 for f in tg.FEATURES}, cues, 3)[0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--skip-tokens", action="store_true")
    args = ap.parse_args()

    report = {"determinism": check_determinism()}
    print("determinism:", report["determinism"])
    report["clean_flips"] = check_clean_flips()
    print(f"clean flips over {report['clean_flips']['cases']} cases, violations per feature:",
          report["clean_flips"]["violations"])
    report["detector_balanced_accuracy"] = acc = check_detectors()
    print("detector balanced accuracy (3000 renders; spec floor 0.98, target 1.000):")
    for f, a in acc.items():
        print(f"  {f:20s} {a:.3f}")
    report["grid"] = check_grid()
    for mains, g in report["grid"].items():
        print(f"grid mains={mains}: cells {g['cells']}, held-off max {g['held_off_max']}")
        print("  other feature on-rates:", g["other_feature_rates"])
    report["confound"] = check_confound()
    print("confound (sign: exclamation +1, hashtag -1), fraction flag == y:")
    for name, c in report["confound"].items():
        print(f"  {name}: topic flip rate {c['topic_flip_rate']}")
        print("   ", c["agree_with_y"])
    if not args.skip_tokens:
        report["tokens"] = t = check_tokens()
        for k in ("fair_coin", "all_on", "plain"):
            print(f"tokens {k}:", t[k])
        print("token cost per feature (mean len(on) - len(off)):", t["token_cost"])
        print(f"first {WINDOW} tokens of the {t['n_over_window']} notes over {WINDOW} tokens: per feature, notes with it"
              " on, edit fully hidden, detector misses / false alarms on the window text:")
        for f, w in t["window"].items():
            print(f"  {f:20s} on {w['on']:3d}  hidden {w['edit_hidden']:3d}  "
                  f"misses {w['detector_misses']:3d}  false alarms {w['detector_false_alarms']:3d}")
    report["examples"] = examples()
    for name, ex in zip(("plain", "about half on", "all on"), report["examples"]):
        print(f"--- example: {name}\n{ex}")
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
