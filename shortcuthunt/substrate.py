"""Gemma-2-2b layer-12 residual stream and the Gemma Scope layer-12 SAE.

Contract
- The layer-12 activation is the output of decoder block 12, i.e. the full model's HF
  hidden_states[13]. Only blocks 0..12 are instantiated, and the activation is captured with a
  forward hook on layers[12]. Do not read hidden_states from the truncated model: its last entry
  is post-final-norm.
- Each text is tokenized as BOS + at most MAX_CONTENT_TOKENS content tokens (right padding).
  BOS is excluded from every pool and from per-token records.
- Subject.encode mean-pools over content tokens: the residual (cast to float32 first) and the
  per-token JumpReLU latents. error = resid - (latents @ W_dec + b_dec). Since the decoder is
  affine this equals the mean per-token SAE error, so resid == decode(latents) + error.
- Everything returned is float32 numpy on CPU.
"""
import warnings
from dataclasses import dataclass, field

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoConfig, AutoModel, AutoTokenizer

MODEL_ID = "google/gemma-2-2b"
LAYER = 12
MAX_CONTENT_TOKENS = 128
SAE_REPO = "google/gemma-scope-2b-pt-res"
SAE_FILE = "layer_12/width_16k/average_l0_82/params.npz"
D_RESID, D_SAE = 2304, 16384


@dataclass
class SAE:
    """JumpReLU SAE: f = pre * (pre > threshold), pre = x @ W_enc + b_enc; x_hat = f @ W_dec + b_dec.

    Fields are float32 numpy arrays; encode/decode use torch copies on `device`.
    """
    W_enc: np.ndarray  # [D_RESID, D_SAE]
    b_enc: np.ndarray  # [D_SAE]
    threshold: np.ndarray  # [D_SAE]
    W_dec: np.ndarray  # [D_SAE, D_RESID]
    b_dec: np.ndarray  # [D_RESID]
    device: str = "cpu"
    _t: dict = field(init=False, repr=False)

    def __post_init__(self):
        self._t = {k: torch.from_numpy(getattr(self, k)).to(self.device)
                   for k in ("W_enc", "b_enc", "threshold", "W_dec", "b_dec")}

    @classmethod
    def load(cls, device="cuda"):
        with np.load(hf_hub_download(SAE_REPO, SAE_FILE)) as z:
            p = {k: z[k].astype(np.float32) for k in ("W_enc", "b_enc", "threshold", "W_dec", "b_dec")}
        assert p["W_enc"].shape == (D_RESID, D_SAE) and p["W_dec"].shape == (D_SAE, D_RESID)
        return cls(**p, device=device)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        t = self._t
        pre = x.float() @ t["W_enc"] + t["b_enc"]
        return pre * (pre > t["threshold"])

    def decode(self, f: torch.Tensor) -> torch.Tensor:
        return f @ self._t["W_dec"] + self._t["b_dec"]


@dataclass
class Encoding:
    """Per-text mean over content tokens (all float32 except n_tokens)."""
    resid: np.ndarray  # [n, D_RESID]
    latents: np.ndarray  # [n, D_SAE]
    error: np.ndarray  # [n, D_RESID]
    n_tokens: np.ndarray  # [n] int64, content tokens pooled


@dataclass
class TokenActs:
    """One text in per-token mode. tokens[i] is tokenizer.decode of the i-th content token, so
    "".join(tokens) reproduces the (possibly truncated) text, except where the tokenizer falls back
    to byte tokens (rare characters): each of those decodes on its own to U+FFFD."""
    tokens: list[str]
    acts: np.ndarray  # [T, len(latent_ids)] float32


@dataclass
class TokenResid:
    """Per-token layer-12 residuals for one padded batch."""
    resid: np.ndarray  # [B, T, D_RESID] float32, T includes BOS and padding
    mask: np.ndarray  # [B, T] int64, 1 on content tokens (BOS and padding are 0)
    input_ids: np.ndarray  # [B, T]


class _Stop(Exception):
    """Raised by the capture hook to end the forward pass at LAYER."""


def load_model(device="cuda"):
    """Gemma2Model (no LM head) with only blocks 0..LAYER, bf16, eager attention.

    Eager because Gemma-2 uses attention logit softcapping, which sdpa does not implement.
    The checkpoint's blocks 13..25 load as "unexpected" keys and are dropped; nothing may be missing.
    The LM head is tied to the embeddings, so skipping it saves no memory; the base class is just
    the smaller interface.
    """
    cfg = AutoConfig.from_pretrained(MODEL_ID)
    cfg.num_hidden_layers = LAYER + 1
    if getattr(cfg, "layer_types", None):
        cfg.layer_types = cfg.layer_types[:LAYER + 1]
    model, info = AutoModel.from_pretrained(MODEL_ID, config=cfg, dtype=torch.bfloat16,
                                            attn_implementation="eager", output_loading_info=True)
    if info["missing_keys"]:
        raise RuntimeError(f"missing weights: {sorted(info['missing_keys'])[:5]}")
    return model.to(device).eval()


def _text_list(texts):
    if isinstance(texts, str):  # list("abc") would silently become three one-character texts
        raise TypeError("texts must be a sequence of strings, not a str")
    return list(texts)


class Subject:
    """Tokenizer + truncated Gemma-2-2b + SAE. Loads everything on construction."""

    def __init__(self, device="cuda"):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.tokenizer.padding_side = "right"
        if self.tokenizer("x", split_special_tokens=True).input_ids[0] != self.tokenizer.bos_token_id:
            raise RuntimeError("tokenizer does not prepend BOS; masks assume position 0 is BOS")
        self.model = load_model(device)
        self.sae = SAE.load(device)

    def _tokenize(self, texts):
        # split_special_tokens: a literal "<bos>" or "<pad>" in the text is ordinary text, not a
        # control token (a second BOS would otherwise be pooled as content).
        return self.tokenizer(_text_list(texts), return_tensors="pt", padding=True, truncation=True,
                              max_length=MAX_CONTENT_TOKENS + 1,
                              split_special_tokens=True).to(self.device)

    @torch.no_grad()
    def _resid(self, enc):
        """Float32 output of block LAYER, [B, T, D_RESID], via a hook that stops the forward."""
        captured = {}

        def hook(module, args, out):
            captured["x"] = out[0] if isinstance(out, tuple) else out
            raise _Stop

        handle = self.model.layers[LAYER].register_forward_hook(hook)
        try:
            self.model(input_ids=enc.input_ids, attention_mask=enc.attention_mask, use_cache=False)
        except _Stop:
            pass
        finally:
            handle.remove()
        return captured["x"].float()

    @staticmethod
    def _content_mask(enc):
        mask = enc.attention_mask.clone()
        mask[:, 0] = 0
        if (mask.sum(1) == 0).any():
            raise ValueError("a text has no content tokens (empty string?)")
        return mask

    def _batched(self, texts, batch_size, fn):
        """Apply fn to consecutive batches; on CUDA OOM retry the batch at half size (down to 1)."""
        out, i = [], 0
        while i < len(texts):
            try:
                out.append(fn(texts[i:i + batch_size]))
                i += batch_size
            except torch.cuda.OutOfMemoryError:
                if batch_size == 1:
                    raise
                torch.cuda.empty_cache()
                batch_size //= 2
                # bf16 results depend slightly on batch shape, so make the change visible.
                warnings.warn(f"CUDA OOM: retrying at batch size {batch_size}")
        return out

    def resid_tokens(self, texts) -> TokenResid:
        """Per-token residuals for one batch (no splitting; keep it small). Mainly for tests."""
        enc = self._tokenize(texts)
        return TokenResid(self._resid(enc).cpu().numpy(), self._content_mask(enc).cpu().numpy(),
                          enc.input_ids.cpu().numpy())

    def encode(self, texts, batch_size=16) -> Encoding:
        texts = _text_list(texts)
        if not texts:
            return Encoding(np.zeros((0, D_RESID), np.float32), np.zeros((0, D_SAE), np.float32),
                            np.zeros((0, D_RESID), np.float32), np.zeros(0, np.int64))

        def run(batch):
            enc = self._tokenize(batch)
            x = self._resid(enc)
            mask = self._content_mask(enc)
            n = mask.sum(1, keepdim=True).float()
            m = mask[..., None].float()
            resid = (x * m).sum(1) / n
            latents = (self.sae.encode(x) * m).sum(1) / n
            error = resid - self.sae.decode(latents)
            return [t.cpu().numpy() for t in (resid, latents, error)] + [mask.sum(1).cpu().numpy()]

        parts = self._batched(texts, batch_size, run)
        resid, latents, error, n_tokens = (np.concatenate(p) for p in zip(*parts))
        return Encoding(resid, latents, error, n_tokens.astype(np.int64))

    def token_latents(self, texts, latent_ids, batch_size=16) -> list[TokenActs]:
        """Per-token activations of latent_ids on each text's content tokens, columns in the given
        order (repeats allowed)."""
        texts = _text_list(texts)
        a = np.asarray(latent_ids)
        # Like ablation.latent_ids, reject floats and bool masks (3.9 would truncate to 3, a mask
        # would index as 0/1), but keep order and repeats: they define the columns.
        if a.ndim != 1 or (a.size and a.dtype.kind not in "iu"):
            raise ValueError(f"latent_ids must be a 1-D integer array, got {a.dtype} {a.shape}")
        if a.size and (a.min() < 0 or a.max() >= D_SAE):
            raise ValueError(f"latent_ids must be in [0, {D_SAE}), got min {a.min()} max {a.max()}")
        ids = torch.as_tensor(a.astype(np.int64), device=self.device)

        def run(batch):
            enc = self._tokenize(batch)
            acts = self.sae.encode(self._resid(enc))[..., ids].cpu().numpy()
            mask = self._content_mask(enc).bool().cpu().numpy()
            input_ids = enc.input_ids.cpu().numpy()
            return [TokenActs([self.tokenizer.decode([t]) for t in input_ids[b][mask[b]]],
                              acts[b][mask[b]])
                    for b in range(len(batch))]

        return [rec for part in self._batched(texts, batch_size, run) for rec in part]
