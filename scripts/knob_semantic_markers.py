"""Knob semantic, Exp S1 (CPU): construction checks and marker diversity of the hedging cue.

    python scripts/knob_semantic_markers.py

Checks: empty insertion reproduces textgen.render; the 15 detectors agree on hedged/confident variants and
with the flags. Measures on 256 fresh notes (selection) + 256 more (held-out evaluation): best single word /
bigram BA, best <=3-term alternation BA (greedy and exhaustive over the top 40 terms), the generic hedge
lexicon regex, the full bank regex, max share of hedged notes containing one hedge-only word, and the gemma
token-length difference between paired hedged/confident notes. Writes results/knobs/semantic/markers.json.
"""
import itertools
import json
import random
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import knob_semantic as K  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402

OUT = ROOT / "results" / "knobs" / "semantic"


def notes(tag, n=256):
    """n notes over 4 topic pairs, hedge balanced, everything else fair coins; also the paired flips."""
    r = random.Random(f"semantic:markers:{tag}")
    texts, flips, h = [], [], []
    for b in range(4):
        topics = r.sample(tg.TOPIC_NAMES, 2)
        cues = tg.make_cues(r)
        t, _, f = K.grid_h(random.Random(r.getrandbits(32)), topics, n // 4, cues)
        texts += t
        h += f["hedge"].tolist()
    # paired flips for the length check: same notes rendered with the other hedge level
    r2 = random.Random(f"semantic:pairs:{tag}")
    pairs = []
    for _ in range(n):
        lv = {f: r2.randrange(2) for f in tg.FEATURES}
        topic, seed, cues = r2.choice(tg.TOPIC_NAMES), r2.getrandbits(32), tg.make_cues(r2)
        pairs.append((K.render_h(topic, lv, cues, seed, 0)[0], K.render_h(topic, lv, cues, seed, 1)[0]))
    return texts, np.array(h), pairs


def terms(text):
    w = re.findall(r"[a-z]+", text.lower())
    return set(w) | {a + " " + b for a, b in zip(w, w[1:])}


def main():
    out = {"reproduces": K.check_reproduces(), "side_effect_mismatches_of_2000": K.check_side_effects()}
    tx, h, pairs = notes("sel")
    te, he, _ = notes("eval")
    T = [terms(t) for t in tx]
    Te = [terms(t) for t in te]
    vocab = sorted(set().union(*T))
    pres = {v: np.array([v in s for s in T]) for v in vocab}
    ba1 = {v: K.ba(p, h) for v, p in pres.items()}
    top = sorted(ba1, key=ba1.get, reverse=True)[:40]
    out["top_single_terms"] = [(v, round(ba1[v], 3), round(float(pres[v][h == 1].mean()), 3),
                                round(float(pres[v][h == 0].mean()), 3)) for v in top[:10]]
    best_word = max((v for v in vocab if " " not in v), key=ba1.get)
    out["best_single_word"] = (best_word, round(ba1[best_word], 3),
                               round(K.ba([best_word in s for s in Te], he), 3))
    # best union (OR) of <= 3 terms, exhaustive over top 40 single terms; also AND-free.
    best = (0, None)
    for k in (1, 2, 3):
        for combo in itertools.combinations(top, k):
            p = np.logical_or.reduce([pres[c] for c in combo])
            b = K.ba(p, h)
            if b > best[0]:
                best = (b, combo)
    combo = best[1]
    pe = np.array([any(c in s for c in combo) for s in Te])
    out["best_3term_or"] = {"terms": combo, "ba_sel": round(best[0], 3), "ba_eval": round(K.ba(pe, he), 3)}
    # hedge-only word shares (words that occur in hedged forms but not in confident forms)
    hw = set(" ".join(a for a, _ in K.ADV_PAIRS + K.PRE_PAIRS).lower().split())
    cw = set(" ".join(c for _, c in K.ADV_PAIRS + K.PRE_PAIRS).lower().split())
    hw = hw - cw - {"i", "it", "am", "that"}  # report every hedge-form word except shared function words
    share = {w: float(np.mean([w in K.words(t) for t, y in zip(tx, h) if y])) for w in sorted(hw)}
    share_c = {w: float(np.mean([w in K.words(t) for t, y in zip(tx, h) if not y])) for w in sorted(hw)}
    out["hedge_only_word_share_in_hedged"] = dict(sorted(((w, round(s, 3)) for w, s in share.items()),
                                                         key=lambda x: -x[1])[:8])
    out["same_words_share_in_confident"] = {w: round(share_c[w], 3) for w in out["hedge_only_word_share_in_hedged"]}
    out["max_hedge_word_share"] = round(max(share.values()), 3)
    lex = re.compile(K.LEXICON_REGEX)
    out["lexicon_regex"] = {"pattern": K.LEXICON_REGEX,
                            "ba_sel": round(K.ba([lex.search(t) is not None for t in tx], h), 3),
                            "ba_eval": round(K.ba([lex.search(t) is not None for t in te], he), 3)}
    bank = re.compile(r"(?i)\b(" + "|".join(re.escape(a) for a, _ in K.ADV_PAIRS + K.PRE_PAIRS) + r")\b")
    out["full_bank_regex_ba_eval"] = round(K.ba([bank.search(t) is not None for t in te], he), 3)
    # count-based lexicon: number of lexicon hits >= 2 (a slightly smarter regex user)
    cnt = np.array([len(lex.findall(t)) for t in te])
    out["lexicon_count_ge2_ba_eval"] = round(K.ba(cnt >= 2, he), 3)
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("google/gemma-2-2b")
        l0 = np.array([len(x) for x in tok([a for a, _ in pairs], add_special_tokens=False)["input_ids"]])
        l1 = np.array([len(x) for x in tok([b for _, b in pairs], add_special_tokens=False)["input_ids"]])
        out["tok_len"] = {"conf_mean": float(l0.mean()), "hedge_mean": float(l1.mean()),
                          "diff_mean": float((l1 - l0).mean()), "diff_abs_mean": float(np.abs(l1 - l0).mean()),
                          "over128_conf": float((l0 > 128).mean()), "over128_hedge": float((l1 > 128).mean())}
    except Exception as e:
        out["tok_len"] = f"no tokenizer: {type(e).__name__}"
    out["examples"] = [pairs[0], pairs[1]]
    (OUT / "markers.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}, indent=1))
    for a, b in out["examples"]:
        print("--- confident\n" + a + "\n--- hedged\n" + b)


if __name__ == "__main__":
    main()
