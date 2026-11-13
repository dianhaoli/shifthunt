# Pre-registration: C6c, judge rung L3 (the answer-key ceiling), written before any counted C6c call

Status: frozen by `PREREG_HASH` in this directory. Times UTC. Design `paper_loop/gpu_plan/C6B_ADDON.md` (the
"Change to C6c" section replaces its first C6c row), approved by the author on 13 Nov with the author's prompt of
that day. Code `scripts/judge_ladder2.py` (same file as C6b). Inputs: `inputs.json`; dry run: `dryrun_c6c.json`.

## 1. Aim

The ceiling: can the same judge grade at all when it holds the ground truth? L3 gives each run's richest view plus a
plain answer key per probe. If κ(L3) is high, the judge's failure at L0-L2 is missing ground truth, not inability to
read the task; if it stays low even with the key, the judge cannot map a regex answer to a property reliably.

## 2. Rung and calls

The answer key block, inserted before the final answer: one line per probe, "probe j: main cue: <plain
description>" or "probe j: no main cue", with an instruction sentence (text and the description table's sha256 in
`inputs.json`). The description is a plain-English rendering of the property (no regex, no latent id).

| base | judge sees | runs | calls |
|---|---|---|---|
| L3_1 | L1 (C6's L0 + exact-query log) + key | set A 130, Luna 60 | 190 |
| L3_2 | L2 (C6b's full transcript, + log for set A and Luna) + key | set A 130, Luna 60, main study 64 | 254 |
| L3_0 | L0 + key | harder variant 18 | 18 |

- Terra judge, textonly_client defaults, serial, seeded order `c6c-1114`. Same length cap as C6b (no run is cut).
- Budget: OpenAI guard **$27** (author-approved 13 Nov; the add-on's $10 assumed cheaper inputs; a test showed the
  L3_2 prompts get no cache discount from their L2 prefix). Dry run on the 5 longest prompts (`dryrun_c6c.json`): $1.28, projection $21.3 for the 462 calls.

## 3. Outcome and prediction

Per base, separately: hard-slot κ, false credit (`none`, wrong cue), false blame, null-slot false blame, `none`
index. **Prediction (pre-stated):** 0.60 ≤ κ(L3) < 0.90 on each base. Descriptive; no test across bases.

## 4. Files hashed in PREREG_HASH

This file, `inputs.json`, `dryrun_c6c.json`, `scripts/judge_ladder2.py`, `scripts/judge_ladder.py`,
`scripts/judge_vs_grade.py`.
