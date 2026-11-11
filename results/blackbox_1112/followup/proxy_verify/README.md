# Scripted policies with the SAE proxy and exact queries (EXPLORATORY)

Code: `scripts/proxy_verify.py` (policies fixed before the first run on real data; see its docstring).
Same probes, candidates, bases, threshold, cost model and outcomes as `../../blind_verify/`. No LLM call.

- Episodes: 6 (3 trap, 3 two-part); scope `shipped`; 0 duplicate episodes dropped.
- Seeds per cell: 2000. Threshold 0.225 topic units (privileged unit).
- Exact back-end: used.

## NAME by kind: unit = topic, back-end = additive

| policy | B | trap | two-part | pooled | texts used |
|---|---|---|---|---|---|
| SAE only, no exact query | 0 | 0.00 | 1.00 | 0.50 | 0.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 8 | 0.00 | 1.00 | 0.50 | 8.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 16 | 0.00 | 1.00 | 0.50 | 16.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 8 | 0.97 | 0.90 | 0.93 | 8.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 16 | 1.00 | 1.00 | 1.00 | 16.0 |
| complement screen + search in SAE order; unfinished -> none | 8 | 0.58 | 0.84 | 0.71 | 8.0 |
| complement screen + search in SAE order; unfinished -> none | 16 | 0.73 | 0.93 | 0.83 | 16.0 |
| complement screen + search in SAE order; unfinished -> guess | 8 | 0.58 | 0.77 | 0.67 | 8.0 |
| complement screen + search in SAE order; unfinished -> guess | 16 | 0.73 | 0.88 | 0.81 | 16.0 |
| complement screen + search in random order; unfinished -> none | 8 | 0.50 | 0.84 | 0.67 | 8.0 |
| complement screen + search in random order; unfinished -> none | 16 | 0.66 | 0.94 | 0.80 | 16.0 |
| complement screen + search in random order; unfinished -> guess | 8 | 0.50 | 0.78 | 0.64 | 8.0 |
| complement screen + search in random order; unfinished -> guess | 16 | 0.66 | 0.89 | 0.78 | 16.0 |

## NAME by kind: unit = topic, back-end = exact

| policy | B | trap | two-part | pooled | texts used |
|---|---|---|---|---|---|
| SAE only, no exact query | 0 | 0.00 | 1.00 | 0.50 | 0.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 8 | 0.00 | 1.00 | 0.50 | 8.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 16 | 0.00 | 1.00 | 0.50 | 16.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 8 | 0.96 | 0.96 | 0.96 | 8.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 16 | 0.99 | 1.00 | 0.99 | 16.0 |
| complement screen + search in SAE order; unfinished -> none | 8 | 0.54 | 0.81 | 0.68 | 8.0 |
| complement screen + search in SAE order; unfinished -> none | 16 | 0.67 | 0.89 | 0.78 | 16.0 |
| complement screen + search in SAE order; unfinished -> guess | 8 | 0.54 | 0.76 | 0.65 | 8.0 |
| complement screen + search in SAE order; unfinished -> guess | 16 | 0.67 | 0.86 | 0.77 | 16.0 |
| complement screen + search in random order; unfinished -> none | 8 | 0.52 | 0.82 | 0.67 | 8.0 |
| complement screen + search in random order; unfinished -> none | 16 | 0.64 | 0.89 | 0.76 | 16.0 |
| complement screen + search in random order; unfinished -> guess | 8 | 0.52 | 0.77 | 0.64 | 8.0 |
| complement screen + search in random order; unfinished -> guess | 16 | 0.64 | 0.86 | 0.75 | 16.0 |

## NAME by kind: unit = free, back-end = additive

| policy | B | trap | two-part | pooled | texts used |
|---|---|---|---|---|---|
| SAE only, no exact query | 0 | 0.00 | 1.00 | 0.50 | 0.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 8 | 0.00 | 0.97 | 0.49 | 8.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 16 | 0.00 | 1.00 | 0.50 | 16.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 8 | 0.94 | 0.88 | 0.91 | 8.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 16 | 0.99 | 0.96 | 0.98 | 16.0 |
| complement screen + search in SAE order; unfinished -> none | 8 | 0.62 | 0.81 | 0.71 | 8.0 |
| complement screen + search in SAE order; unfinished -> none | 16 | 0.77 | 0.92 | 0.85 | 16.0 |
| complement screen + search in SAE order; unfinished -> guess | 8 | 0.62 | 0.80 | 0.71 | 8.0 |
| complement screen + search in SAE order; unfinished -> guess | 16 | 0.77 | 0.92 | 0.85 | 16.0 |
| complement screen + search in random order; unfinished -> none | 8 | 0.61 | 0.82 | 0.71 | 8.0 |
| complement screen + search in random order; unfinished -> none | 16 | 0.76 | 0.92 | 0.84 | 16.0 |
| complement screen + search in random order; unfinished -> guess | 8 | 0.61 | 0.80 | 0.70 | 8.0 |
| complement screen + search in random order; unfinished -> guess | 16 | 0.76 | 0.92 | 0.84 | 16.0 |

## NAME by kind: unit = free, back-end = exact

| policy | B | trap | two-part | pooled | texts used |
|---|---|---|---|---|---|
| SAE only, no exact query | 0 | 0.00 | 1.00 | 0.50 | 0.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 8 | 0.00 | 0.99 | 0.50 | 8.0 |
| rank prefix, width 1 (SAE rank 1 on every probe) | 16 | 0.00 | 1.00 | 0.50 | 16.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 8 | 0.94 | 0.90 | 0.92 | 8.0 |
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 16 | 0.98 | 0.99 | 0.99 | 16.0 |
| complement screen + search in SAE order; unfinished -> none | 8 | 0.58 | 0.80 | 0.69 | 8.0 |
| complement screen + search in SAE order; unfinished -> none | 16 | 0.70 | 0.91 | 0.81 | 16.0 |
| complement screen + search in SAE order; unfinished -> guess | 8 | 0.58 | 0.79 | 0.69 | 8.0 |
| complement screen + search in SAE order; unfinished -> guess | 16 | 0.70 | 0.91 | 0.80 | 16.0 |
| complement screen + search in random order; unfinished -> none | 8 | 0.62 | 0.79 | 0.71 | 8.0 |
| complement screen + search in random order; unfinished -> none | 16 | 0.76 | 0.92 | 0.84 | 16.0 |
| complement screen + search in random order; unfinished -> guess | 8 | 0.62 | 0.79 | 0.70 | 8.0 |
| complement screen + search in random order; unfinished -> guess | 16 | 0.76 | 0.91 | 0.84 | 16.0 |

## Trap episodes by the SAE rank of the true cue (as built; additive back-end, topic unit, B = 8)

| SAE rank of the true cue | episodes | prefix2 | complement_none | complement_guess | proxy_only | prefix1 |
|---|---|---|---|---|---|---|
| 2 | 3 | 0.97 | 0.58 | 0.58 | 0.00 | 0.00 |

## Rank placement (counterfactual): traps, B = 8, additive back-end, topic unit

The exact readings are unchanged; only the SAE order on the hard probe is changed so that the true cue sits at rank r.

| policy | r = 2 | r = 3 | r = 4 | r = 5 | r = 6 | r = 7 | r = 8 |
|---|---|---|---|---|---|---|---|
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 0.97 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| complement screen + search in SAE order; unfinished -> none | 0.58 | 0.54 | 0.51 | 0.51 | 0.51 | 0.43 | 0.44 |
| complement screen + search in SAE order; unfinished -> guess | 0.58 | 0.54 | 0.51 | 0.51 | 0.51 | 0.43 | 0.44 |

Episodes: 3.

## Rank placement (counterfactual): traps, B = 8, exact back-end, topic unit

The exact readings are unchanged; only the SAE order on the hard probe is changed so that the true cue sits at rank r.

| policy | r = 2 | r = 3 | r = 4 | r = 5 | r = 6 | r = 7 | r = 8 |
|---|---|---|---|---|---|---|---|
| rank prefix, width 2 (SAE ranks 1 and 2 on every probe) | 0.96 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| complement screen + search in SAE order; unfinished -> none | 0.56 | 0.53 | 0.48 | 0.55 | 0.54 | 0.47 | 0.46 |
| complement screen + search in SAE order; unfinished -> guess | 0.56 | 0.53 | 0.48 | 0.55 | 0.54 | 0.47 | 0.46 |

Episodes: 3.

## Reference: no-SAE ceilings at the same budget (blind_verify, best policy, privileged)

8 queries: 0.40; 16 queries: 0.80; 64 queries: 0.93 (shipped six; from the BB-16 pre-registration).

