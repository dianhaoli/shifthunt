"""Which tensor is "layer-12 activation"? Compare three candidates on two texts.

1. Full 26-layer model, HF hidden_states[13]           (the definition)
2. Full model, forward hook on model.layers[12]          (should equal 1)
3. Model truncated to 13 blocks: hook vs hidden_states[13]

Usage: HF_TOKEN=... python scripts/check_layer_capture.py
"""
import sys
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shifthunt.substrate import MAX_CONTENT_TOKENS  # noqa: E402

MODEL = "google/gemma-2-2b"
texts = ["He spends most weekends growing tomatoes at the allotment.",
         "Hi Sam,\nShe owns three telescopes!"]

tok = AutoTokenizer.from_pretrained(MODEL)
enc = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=MAX_CONTENT_TOKENS + 1).to("cuda")
valid = enc.attention_mask.bool()


def run(model):
    cap = {}
    hook = model.model.layers[12].register_forward_hook(
        lambda m, i, out: cap.__setitem__("x", (out[0] if isinstance(out, tuple) else out).float()))
    with torch.no_grad():
        out = model.model(**enc, output_hidden_states=True)
    hook.remove()
    return cap["x"], out.hidden_states[13].float(), len(out.hidden_states)


load = dict(torch_dtype=torch.bfloat16, attn_implementation="eager")
full = AutoModelForCausalLM.from_pretrained(MODEL, **load).to("cuda").eval()
hook_full, hs_full, n_full = run(full)
del full
torch.cuda.empty_cache()

cfg = AutoConfig.from_pretrained(MODEL)
cfg.num_hidden_layers = 13
if getattr(cfg, "layer_types", None):
    cfg.layer_types = cfg.layer_types[:13]
trunc = AutoModelForCausalLM.from_pretrained(MODEL, config=cfg, **load).to("cuda").eval()
hook_tr, hs_tr, n_tr = run(trunc)

d = lambda a, b: (a - b)[valid].abs().max().item()
print(f"len(hidden_states): full={n_full} truncated={n_tr}")
print(f"full hook vs full hs[13]:      {d(hook_full, hs_full):.4g}")
print(f"trunc hook vs full hs[13]:     {d(hook_tr, hs_full):.4g}")
print(f"trunc hs[13] vs full hs[13]:   {d(hs_tr, hs_full):.4g}")
norms = hs_full[0].norm(dim=-1)
print(f"text 0 token norms: BOS={norms[0]:.0f}, content={[round(x) for x in norms[1:6].tolist()]}")
