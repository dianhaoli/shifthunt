# Commands: blind_verify, scripted blind ceilings on the shipped six (plan 0b.3)

Run on the GPU box (one A10G), 2026-11-10, from the repo root, AFTER the scan fix (plan 0b.1). `PY` is the
study environment (`/home/ec2-user/onsite/grader-wt/.venv/bin/python`, torch 2.12.0+cu130, transformers
5.9.0); the episode bank is private and read-only. No paid API call, no docker.

```
export PYTHONDONTWRITEBYTECODE=1 SHIFTHUNT_BANK=<private tree>/.cache/bank

# 1. Exact back-end (GPU, under the shared lock; weights from the local HF cache, offline). Per probe: the
#    stored scan set (544 texts) is re-rendered and re-encoded and must reproduce the stored logits; only
#    then are the sample-like bases and group texts encoded. Writes results/private_1112/blind_verify/exact_<ep>.npz.
flock /tmp/shifthunt-gpu.lock env HF_HUB_OFFLINE=1 $PY scripts/blind_verify.py --gpu-encode --force \
    --private results/private_1112/blind_verify

# 2. Policies, both back-ends, both decision units (CPU). --exact require: fail rather than fall back to
#    back-end A alone if a cached probe is missing or fails the reproduction gate.
CUDA_VISIBLE_DEVICES="" $PY scripts/blind_verify.py --exact require \
    --out results/blackbox_1112/blind_verify --private results/private_1112/blind_verify

# 3. README.md again from blind_verify.json (no run; used once to reword one heading, numbers untouched)
CUDA_VISIBLE_DEVICES="" $PY scripts/blind_verify.py --readme-only --out results/blackbox_1112/blind_verify
```

Defaults used: episodes ep411, ep413, ep415, ep472, ep474, ep476; budgets 8, 16, 32, 64; 2000 seeds per
episode, policy and budget (generator `random.Random("blind:<episode>:<policy>:<B>:<seed>")`, the same seeds
for both back-ends and both units).

Step 1 encodes 76,668 texts (13,056 scan texts for the reproduction check, then 589 sample-like bases and
their 107 group texts each, 63,612 texts) in about 9 min wall (53 s model load, 100 s per templated episode, 60-66 s per
free-text episode); it exits 1 if any probe fails the reproduction gate and leaves no process behind. It was
run twice (once before and once after a refactor of the driver that does not touch the encoding; 544 s and
541 s inside the script, plus waiting for the lock); the two caches hold bit-identical arrays (240 of 240).
Step 2 takes about 2.5 to 3 min; a second run gave identical numbers (seeded). Step 2 was run a third time
after review (the script now refuses an episode in which a probe has two main cues, and the README says the
bisection rows assume one main per probe): `blind_verify.json` and both private files came out byte-identical,
and `README.md` differs only by the added "One main per probe" bullet.

Files here: `README.md` (tables, reproduction check, additivity error, answer paragraph) and
`blind_verify.json` (every rate per unit / back-end / policy / budget: per episode, pooled, by kind; the
noiseless reference; additivity statistics; reproduction numbers). Neither names a cue or says which probe is
an episode's hard slot. Private, not tracked (`results/private_1112/blind_verify/`): `exact_<episode>.npz`
(re-encoded scan logits, sample-like base logits, group-text logits, the candidate masks),
`blind_verify_probes.jsonl` (per probe: main cue, candidates and signs by name, mean readings, the claim sets
that occurred), `reproduce.json` (the reproduction numbers per probe).

Tests: `$PY -m pytest tests/test_blind_verify.py -q -p no:cacheprovider` (synthetic probes, the generators'
texts and a fake encoder: no bank, no GPU). With `SHIFTHUNT_BANK` set, two more tests run on the shipped six
(additive back-end and grader agreement; the exact cache's reproduction numbers, skipped with a message if
the private cache is absent).
