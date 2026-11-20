# Pre-registration: T, the contract-band tell check (round 3), written before any run of the policy

Status: frozen by `PREREG_HASH` here. Times UTC. Design: `docs/study/gpu_plan/GPU_PROMPT_3.md` §T and
`paper_loop/final_debate/00_FINAL_FEEDBACK.md` §5; the author's prompt of 14 Nov. Code `scripts/t_bandclose.py`
(hashed). $0, CPU, scripted; no agent data and no LLM.

## 1. Aim

Can a scripted policy that checks the proxy against the contract's stated band reproduce Terra's selective widening
(SAE runner-up isolated on 11/12 trap probes vs 4/48 ordinary probes, Open-8, shipped items) and its Open-4 result
(NAME 12/12)?

## 2. Inputs (frozen earlier work)

- **Proxy readings, in the proxy's own unit:** followup_band's per-seed proxy effects (`seeds_proxy_unit` in the
  private `band.json`: each aligned property's proxy effect divided by the proxy's own sample class gap; 5 note seeds
  per probe). Check before this hash (`t_bandclose.py check`, no policy run): the band (0.15, 0.30) fires on 15/15
  shipped-trap cells, 0.914 of the other bank-trap cells (0.925 with the shipped), 0.205 of single-main ordinary and
  0.258 of null cells, as in `followup/solvers/band.json`.
- **Exact tests:** X1's probes, back-ends and cost model (`scripts/xr_scripted_curves.py`): one exact text reads one
  candidate's single flip on one sample-like base; the base note is free; threshold 0.225 in the topic unit; claims
  and NAME as X1 (blind_verify). Shipped six on X1's exact back-end; bank episodes on the additive back-end.
- **Seeds:** X1's 2000 per (episode, B); seed s uses note seed s mod 5.

## 3. The policy ("band-plus-closeness"; fixed here)

Per probe, from that seed's proxy readings: head = the aligned property with the largest |reading|, runner-up = the
second. **Widen iff 0.15 < |runner-up| < 0.30 and |runner-up| ≥ 0.5 × |head|.** Spend one text per reading until B
is used: (1) widened probes, in probe order: head, then runner-up; (2) the other probes by descending |head|: head;
(3) leftover, as X1's top-k prefix: rank 2, then rank 3, ... on every probe in probe order, skipping what was read.
Claim the read candidates above 0.225 (at most 2); a probe with none: `none`. Widening on a probe = its runner-up
was read.

## 4. Runs and report

Shipped six and X1's distinct bank episodes, B = 4 and B = 8. Reported: P(NAME); trap pass; widening rate on trap
probes, single-main ordinary probes, two-main probes and nulls; per shipped item. A sweep of the closeness factor
(0, 0.33, 0.5, 0.67, 0.8) is descriptive.

**Comparison with Terra (primary closeness 0.5):** policy widening on shipped trap probes at B = 8 vs Terra 11/12
(Wilson 0.65-0.99); on shipped ordinary probes at B = 8 vs Terra 4/48 (Wilson 0.03-0.20); policy P(NAME) on the
shipped six at B = 4 vs Terra Open-4 12/12 (Wilson 0.76-1.00).

## 5. Outcome sentences (written in advance)

- If the policy is inside Terra's Wilson interval on both measures (selective widening: trap **and** ordinary rate;
  and Open-4 P(NAME)): **"Terra's selective widening is reproduced by a policy that checks the proxy against the
  stated prior."**
- Otherwise: **"A band-plus-closeness policy does not reproduce Terra's widening."** The json says which measure
  falls outside.

## 6. Deviations from the plan (the box wins)

- "Close to the head" is not defined in the plan; fixed here as |runner-up| ≥ 0.5 × |head|, with the sweep
  descriptive only.
- "Spend the leftover the way X1's best policy does": X1's best rows at B = 4/8 are top-2 and the calibrated Bayes
  tester; the leftover here follows the proxy order (X1's top-k prefix), which needs no fitted prior.
- Terra's widening is measured on its Open-8 runs, so the policy's widening is read at B = 8; its NAME at B = 4.

## Files hashed in PREREG_HASH

This file, `scripts/t_bandclose.py`, `scripts/xr_scripted_curves.py`, `scripts/blind_verify.py`,
`scripts/proxy_verify.py`.
