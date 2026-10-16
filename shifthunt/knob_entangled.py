"""Knob "entangled": a hashtag cue whose word is one of the probe's two topic names.

No change to textgen: a probe's cue strings come from probes.cue_strings(eval_seed); for eval_seeds in the
registry, the hashtag word is replaced (dataclasses.replace) by the registered word. install() wraps
probes.cue_strings and the copy imported by hidden.py; episode_files imports it lazily from probes, so it
sees the wrapper too. Every other eval_seed returns exactly the original Cues (existing probes unchanged).

Also: keep-aware reference (greedy on the reliance set with a kept constraint) and the interpretive
topic-dominance rule.
"""
import dataclasses
import json
import re
from pathlib import Path

import numpy as np

from . import effects as E
from . import probes as P
from . import textgen as tg
from .ablation import ablate_logits

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "artifacts" / "probes" / "knob_entangled" / "entangled_cues.json"

_ORIG = P.cue_strings
_REG = {}


# Topic-rich closings for the entangled `signoff` variant: a hobby signoff naming the topic plus singular
# equipment words. Letters and spaces only (the signoff detector needs ^[a-z ]+,$), and no topic-bank
# phrase is a substring (probes._topic_of must still read the note's topic from its body).
CLOSINGS = {
    "gardening": "Happy gardening with my trowel and seed tray",
    "astronomy": "Clear skies from my telescope and star chart",
    "cooking": "Happy cooking with my cast iron pan and chef knife",
    "cycling": "Happy cycling with my helmet and bike pump",
    "chess": "Happy chess with my chess clock and opening book",
    "fishing": "Tight lines with my fishing rod and tackle box",
    "knitting": "Happy knitting with my needles and wool skein",
    "photography": "Happy shooting with my camera lens and flash unit",
    "running": "Happy running in my running shoe and sports watch",
    "birdwatching": "Good birding with my binocular and field guide",
    "pottery": "Happy potting at my pottery wheel with glaze and clay",
    "sailing": "Fair winds with my compass and life jacket",
}

# Stronger variant: four singular equipment words of the topic (same constraints).
CLOSINGS_STRONG = {
    "gardening": "Happy gardening with my trowel and seed tray and watering can and tomato plants",
    "astronomy": "Clear skies with my telescope and eyepiece and star chart and lunar map",
    "cooking": "Happy cooking with my cast iron pan and chef knife and wooden spoon and cookbook",
    "cycling": "Happy cycling with my bike helmet and bike pump and inner tube and cycling jersey",
    "chess": "Happy chess with my chess set and chess clock and opening manual and strategy book",
    "fishing": "Tight lines with my fishing rod and fishing reel and tackle box and wading boot",
    "knitting": "Happy knitting with my knitting needle and ball of yarn and wool skein and stitch marker",
    "photography": "Happy shooting with my camera lens and memory card and flash unit and camera bag",
    "running": "Happy running in my running shoe with sports watch and energy gel and water bottle",
    "birdwatching": "Good birding with my binocular and field guide and bird feeder and spotting scope",
    "pottery": "Happy potting with my pottery wheel and block of clay and glaze jar and carving tool",
    "sailing": "Fair winds with my life jacket and sailing rope and compass and sailing glove",
}
CLOSING_SETS = {"base": CLOSINGS, "strong": CLOSINGS_STRONG}


def entangled_cue_strings(eval_seed):
    c = _ORIG(eval_seed)
    v = _REG.get(int(eval_seed))
    if v is None:
        return c
    field, value = ("hashtag", v) if isinstance(v, str) else (v["field"], v["value"])
    return dataclasses.replace(c, **{field: value})


def register(eval_seed, word, field="hashtag"):
    if field == "hashtag":
        assert word.isalnum() and word.islower(), word
        _REG[int(eval_seed)] = word
    else:
        assert field == "closing" and re.fullmatch(r"[A-Za-z ]+", word), word
        _REG[int(eval_seed)] = {"field": field, "value": word}


def load_registry(path=REGISTRY):
    if Path(path).exists():
        for k, v in json.loads(Path(path).read_text()).items():
            if isinstance(v, str):
                register(int(k), v)
            else:
                register(int(k), v["value"], field=v["field"])
    return dict(_REG)


def save_registry(path=REGISTRY):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(Path(path).read_text()) if Path(path).exists() else {}
    old.update({str(k): v for k, v in _REG.items()})
    Path(path).write_text(json.dumps(old, indent=1))


def install(path=REGISTRY):
    """Patch probes.cue_strings and hidden.cue_strings (idempotent); load the saved registry."""
    load_registry(path)
    P.cue_strings = entangled_cue_strings
    from . import hidden as H
    H.cue_strings = entangled_cue_strings


# ---------------------------------------------------------------- keep-aware reference

def rel_effects(logits, flags, topic, cue, sign):
    r = P.measure_reliance(logits, flags, topic, cue, sign)
    return sign * r["coef"][cue], r["topic_coef"]


def keep_aware_reference(logits, F, flags, topic, g, mu, cue, sign, cand, k=E.REF_K, keep_min=0.85):
    """Greedy on the reliance set: add the candidate with the largest removal while kept >= keep_min.
    F dense [n, m] (only candidate columns are read). -> list of ids (<= k)."""
    es0, et0 = rel_effects(logits, flags, topic, cue, sign)
    chosen, pool = [], [int(i) for i in cand]
    for _ in range(k):
        best = None
        for i in pool:
            es, et = rel_effects(ablate_logits(logits, F, g, mu, chosen + [i]), flags, topic, cue, sign)
            rem, kept = 1 - abs(es) / es0, et / et0
            if kept < keep_min:
                continue
            if best is None or rem > best[0]:
                best = (rem, i)
        if best is None:
            break
        chosen.append(best[1])
        pool.remove(best[1])
    return chosen


# ---------------------------------------------------------------- interpretive rule

def topic_dominance(top_topics):
    """Largest single-topic share among a latent's top notes."""
    if not top_topics:
        return 0.0
    vals, counts = np.unique(np.asarray(top_topics), return_counts=True)
    return float(counts.max() / len(top_topics))


def topic_dominated(top_topics, frac=0.6):
    return topic_dominance(top_topics) >= frac


# ---------------------------------------------------------------- lean model loader (RAM)

def lean_load_model(device="cuda"):
    """substrate.load_model without the CPU copy of the checkpoint (needs no accelerate): build the
    truncated Gemma2Model on `device` in bf16, then stream each checkpoint tensor (blocks 0..LAYER and the
    rest of the base model) to the device and cast to bf16. Verified against cached encodings of the
    standard loader by scripts/knob_entangled_build.py --verify-loader."""
    import re as _re
    import torch
    from huggingface_hub import snapshot_download
    from safetensors import safe_open
    from transformers import AutoConfig, AutoModel
    from . import substrate as S
    cfg = AutoConfig.from_pretrained(S.MODEL_ID)
    cfg.num_hidden_layers = S.LAYER + 1
    if getattr(cfg, "layer_types", None):
        cfg.layer_types = cfg.layer_types[:S.LAYER + 1]
    with torch.device(device):
        model = AutoModel.from_config(cfg, dtype=torch.bfloat16, attn_implementation="eager")
    params = dict(model.named_parameters())
    seen = set()
    root = Path(snapshot_download(S.MODEL_ID, allow_patterns=["*.safetensors", "*.json"]))
    for shard in sorted(root.glob("*.safetensors")):
        with safe_open(str(shard), framework="pt", device=device) as f:
            for k in f.keys():
                name = k[len("model."):] if k.startswith("model.") else k
                m = _re.match(r"layers\.(\d+)\.", name)
                if m and int(m.group(1)) > S.LAYER:
                    continue
                if name not in params:
                    continue  # lm_head etc.
                with torch.no_grad():
                    params[name].copy_(f.get_tensor(k).to(torch.bfloat16))
                seen.add(name)
    missing = set(params) - seen
    if missing:
        raise RuntimeError(f"missing weights: {sorted(missing)[:5]}")
    return model.eval()


def use_lean_loader():
    from . import substrate as S
    S.load_model = lean_load_model
