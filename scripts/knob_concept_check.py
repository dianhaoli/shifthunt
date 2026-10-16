"""Knob concept CPU checks: flip locality, detector side effects, token lengths, regex coverage / base FP.

    python scripts/knob_concept_check.py   -> results/knobs/concept/check.json
"""
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import freetext as ft  # noqa: E402
from shifthunt import knob_concept as K  # noqa: E402
from shifthunt.substrate import MAX_CONTENT_TOKENS, MODEL_ID  # noqa: E402

OUT = ROOT / "results" / "knobs" / "concept"


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    rng = random.Random("knob_concept:check")
    res = {"n_forms": {k: len(K.forms(k)) for k in ("shown", "heldout")}}
    bad_local, bad_det, n_over, n_over_base, lens = 0, 0, 0, 0, []
    N = 1000
    for i in range(N):
        topic = rng.choice(K.TOPIC_NAMES)
        lv = {f: int(rng.random() < 0.5) for f in K.FEATURES}
        seed = rng.getrandbits(32)
        for bank in ("shown", "heldout"):
            K.use_forms(bank)
            off, _ = K.render(topic, lv | {"concept": 0}, None, seed)
            on, fl = K.render(topic, lv | {"concept": 1}, None, seed)
            base, _ = ft.render(topic, {f: v for f, v in lv.items() if f != "concept"}, None, seed)
            ins = [w for w in on.split() if True]
            # locality: removing exactly one sentence-sized span from `on` gives `off`
            a, b = 0, 0
            while a < len(off) and off[a] == on[a]:
                a += 1
            while b < len(off) - a and off[-1 - b] == on[-1 - b]:
                b += 1
            if off != base or len(on) - len(off) > 120:
                bad_local += 1
            d = K.detect(on)
            if any(d[f] != fl[f] for f in ft.FEATURES) or d["concept"] != 1 or K.detect(off)["concept"] != 0:
                bad_det += 1
            if bank == "heldout":
                L = len(tok(on, add_special_tokens=False)["input_ids"])
                lens.append(L)
                n_over += L > MAX_CONTENT_TOKENS
                n_over_base += len(tok(off, add_special_tokens=False)["input_ids"]) > MAX_CONTENT_TOKENS
    K.use_forms("shown")
    res.update(locality_violations=bad_local, detector_mismatches=bad_det, n_renders=2 * N,
               frac_over_128_concept_on=n_over / N, frac_over_128_concept_off=n_over_base / N,
               mean_tokens_concept_on=sum(lens) / N)
    bank = [p for v in ft.bank().values() for p in v]
    for name, rx in (("v1", K.CONCEPT_REGEX), ("v2", K.CONCEPT_REGEX_V2)):
        r = re.compile(rx)
        res[f"regex_{name}"] = {k: sum(bool(r.search(s)) for s in K.forms(k)) / len(K.forms(k))
                                for k in ("shown", "heldout")}
        res[f"regex_{name}"]["base_paragraph_fp"] = sum(bool(r.search(p)) for p in bank) / len(bank)
    print(json.dumps(res, indent=1))
    (OUT / "check.json").write_text(json.dumps(res, indent=1))
    K.use_forms("heldout")
    print(K.render("chess", {f: 1 for f in K.FEATURES}, None, 7)[0])


if __name__ == "__main__":
    main()
