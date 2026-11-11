"""BB-8 feasibility (D35), token lengths: Gemma-2-2b tokens per public sample note of the six shipped episodes, and
how many notes exceed the 128-token window (the decoded first-128-token window is kept privately).

    python scripts/feasibility/bb8_tok.py --out AGG.json --private-dir DIR [--bank B]

Needs the HF tokenizer google/gemma-2-2b in the local cache (HF_HUB_OFFLINE=1). The full token table
(<private-dir>/tokens.json, about 1 MB) stays private. The tracked JSON has per episode type: mean, min, max tokens
and notes over 128.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

WINDOW = 128


def main(argv=None):
    import numpy as np
    from transformers import AutoTokenizer
    a = BC.parser(__doc__).parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    tok = AutoTokenizer.from_pretrained("google/gemma-2-2b")
    out, by_type = {}, {}
    for ep in BC.EPS:
        for j in range(4):
            s = json.loads((Path(a.bank) / ep / "public" / f"probe{j}_sample.json").read_text())["texts"]
            ids = [tok(t["text"], add_special_tokens=False)["input_ids"] for t in s]
            n = [len(x) for x in ids]
            out[f"{ep}_{j}"] = dict(n=n, vis=[tok.decode(x[:WINDOW]) for x in ids])
            by_type.setdefault(BC.EP_TYPE[ep], []).extend(n)
    (priv / "tokens.json").write_text(json.dumps(out))
    agg = {t: {"notes": len(v), "mean": round(float(np.mean(v)), 2), "min": int(min(v)), "max": int(max(v)),
               "over_window": int(sum(x > WINDOW for x in v))} for t, v in by_type.items()}
    BC.write_out(a.out, {"script": "bb8_tok", "window": WINDOW, "by_episode_type": agg})


if __name__ == "__main__":
    main()
