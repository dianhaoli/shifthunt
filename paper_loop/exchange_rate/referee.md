# Referee report: is the proxy "worth X exact queries"?

Referee for the four theory notes (`theory_bayes_voi.md`, `theory_search_bai.md`, `theory_game_theory.md`,
`theory_statistician.md`) and the computation note (`compute.md`). I read them against the paper
(`final/PAPER_V4_user.md` §2-5.1, Table 2, App. D, E, F, J) and re-derived or re-ran the contested points. My own
checks are in `calc/referee/`:

- `ref_checks.py` → `ref_checks.json`: Fisher tests on the "negative value" data, a one-batch decoder comparison, and marginal values;
- `ref_minimax_dp.py` → `ref_minimax_dp.json`: an exact adaptive DP on trap-only episodes.

Both are abstract-model calculations: no runs, no money, no episode ids, and no shipped episode paired with a property.

---

## 0 Verdict in one paragraph

The author is right that the question is structural and probabilistic, not a fixed exchange rate. The proxy's effect
is a change of prior in a budgeted Bayesian search. An exchange rate X is a derived number: you invert the blind
success curve at the proxy arm's success. X is well defined, but it depends on the agent, the exact channel (single
isolations or group texts, noise), the item mix and the target. It is also censored at B = 8. The author is wrong
that the proxy is "worth exactly 0 on traps and exactly 1 on ordinary cues":

- On a rank-2 trap the proxy carries full information to an agent that knows how it errs.
- On an ordinary probe it is worth about 3 bits, not 1 query.
- Its biggest effect comes through the shared budget.

The "0" survives in one exact sense: as the minimax value against a designer who may hide the trap anywhere, **for an
agent that commits all its texts in one batch**. Every agent in the paper does commit in one batch. For an adaptive
agent the proxy keeps real value even against that designer (§3, check R3).

---

## 1 What all five documents agree on, and the numbers support

| # | consensus claim | status | evidence |
|---|---|---|---|
| A1 | X is not a property of the SAE. For the same tool, items and target (0.958), B\* runs from 11 to > 64 depending on the blind reference | **Confirmed** | compute §4: 11 (noiseless group, known counts), 24-26 (noiseless single isolations), 36 (Terra logistic), ≈ 50 (fitted-noise robust ideal), 59 (scripted, sim), > 64 (repo back-end). search_bai §4 agrees independently. |
| A2 | A calibrated agent values a predictably wrong proxy as much as a right one | **Confirmed** | compute §3.1: exact DP, single and group tests. Rank 2, rank 3 and rank 6 traps all reach 1.0 at B = 5 (0.54 / 0.75 / 0.92 / 1.0 at B = 2-5). bayes_voi §3.2 and search_bai §3.1 reproduce this; class DP = hypothesis DP = search_bai DP. |
| A3 | "Worth 0 on traps" belongs to the top-one / proxy-right believer, whose loss more budget does not recover | **Confirmed** | compute §3.2: the believer scores 0.50 at B = 5, 8 and 12. Table 2: top-one 0.00 on traps. |
| A4 | The budget is shared, so the proxy is valuable on trap episodes through the three probes it gets right | **Confirmed** | compute §5: a proxy with no information on the trap (u1..8) still lifts the ideal agent from 0.36 to 0.76 (single) and from 0.70 to 1.00 (group) at B = 8. |
| A5 | X is censored at B = 8; the proxy arm is at ceiling | **Confirmed** | Terra 23/24. The ideal proxy agent reaches 1.0 at B = 5. App. D's harder variant: 7/8 at 4 texts. |
| A6 | The matched-budget contrast C1 = +0.71 is the solid result; X is an extrapolation | **Confirmed** | Item sign test 6/6, p = 0.031 (C1) vs 4/2/0, p = 0.125 (Open-8 vs BB-16). App. J itself says Open-8's own uncertainty is not propagated. |
| A7 | Terra's proxy arm is at the ideal | **Confirmed** | Proxy shortfall 0.00-0.04 against every reference (compute §5). |
| A8 | The decomposition C1 = info + blind shortfall − proxy shortfall is exact, but the split depends on the blind reference | **Confirmed** | Information share runs 0.30 → 0.64 across references (compute §5); statistician §4 brackets 36-79%. |

---

## 2 Where they conflict, and my rulings

### R1. Is "most of 36" Terra's weak blind search? (bayes_voi says yes; search_bai, statistician and compute say no)

**Ruling: bayes_voi is wrong on this point.** Its blind single-isolation reference (§3.2: 0.16 at 8, 0.46 at 16,
0.91 at 24) is a heuristic far below the exact optimum. The exact DP gives 0.36 / 0.71 / 0.96 at 8 / 16 / 24
(compute §3.1 and search_bai §3.3, two independent DPs that agree). Against that curve:

- Terra's blind arm (0.25 / 0.67 / 1.00 at 8 / 16 / 64) is close to the isolation ideal, even though the ideal knows
  the cue counts.
- Under the fitted noise, the robust ideal needs about 50 queries to match 0.958, more than Terra's own 36 (compute
  §4). At high budgets Terra is at or above the noise-robust reference.
- Against the scripted reference, Terra's shortfall is not significant (p = 0.095 at 8, 0.086 at 16; statistician §4).

Most of the excess of "36" over the ideal 11-12 is the **exact channel**: single isolations carry about 0.54 bits
each, and group texts sum small effects and fail under noise. It is not Terra's skill. search_bai's split (6
information, 13 primitive, 12 tail/noise/agent, −3 batch overhead) is the best available. Its third bucket is not
identified, though: it combines noise, target and agent, and the target alone moves it by ±20.

### R2. Does noise matter? (game_theory: "irrelevant"; the other four: matters)

**Ruling: noise matters for the blind arm and for X; it barely matters for the proxy arm.** Game theory treats
"stored logits reproduce within 0.009 topic units" as the noise level. That number is the *reproducibility* of a
stored logit. It is not the base-to-base variation of an edit's effect.

- Fitted to 14 repo numbers, the variation is σ ≈ 0.075 for single flips and 0.14 for group texts, plus small
  aligned effects that add up (compute §2).
- Consequences: top-two scores 0.96, not 1.00. The group-testing optimum falls from 0.70 to 0.50 on stored readings
  (App. D) and to 0.47 under fitted noise.
- The proxy policy loses only 1.00 → 0.97, because it isolates strong candidates.

Game theory is right on a different point: the trap's rank error is designed, not random. Its "noise is not where
the uncertainty lives" holds for the proxy arm only.

### R3. Against a designer free to hide the trap anywhere, is the proxy worth 0-1 queries (game_theory) or still a lot (bayes_voi, search_bai, compute)?

**Ruling: both are right, about different agents. The deciding variable is adaptivity.**

- **One batch.** Game theory's hide-and-seek value min(1, B/N) is standard and correct. At B = 8 with the trap
  anywhere in ranks 2-8, the proxy gives 8/28 = 0.29 against 8/32 = 0.25 blind, about +0.04. The proxy is worth
  close to 0. This is the author's "0", and it describes the real agents: Terra 24/24 and Luna 36/36 sent every text
  in one burst.
- **Adaptive.** Game theory's two-stage number (0.29) is a loose lower bound: it pays a full 4-text screen and uses no
  inference. My exact DP (`ref_minimax_dp`) covers trap-only episodes, a designer uniform over ranks 2-8, noiseless
  single isolations and one text at a time. P(NAME) is:

  | B | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|
  | value | .119 | .179 | .250 | .321 | .393 | .464 | **.512** |

  (1.0 is reached at B = 16. A brute-force hypothesis-set DP gives the same values for B = 2-7.)

  - This value is an upper bound on the adaptive minimax value: minimax ≤ Bayes value against any fixed designer
    mix. Because the game is symmetric in ranks 2-8, it equals the minimax value among designers who avoid rank 1.
  - Against the blind single-isolation ideal (0.36 at 8, 0.53 at 12), the proxy is still worth about **3-4 extra
    queries at B = 8** (0.51 vs 0.36; blind needs about 11.5 to reach 0.51), even against an adversarial designer.
  - Where the value comes from: one rank-1 test can clear a probe as ordinary, so the remaining budget searches
    2 × 7 cells instead of 32.
  - With noiseless group tests the calibrated agent reaches 1.0 at B = 7 even against u2..8 (compute §3.1).
    Game theory's warning stands, though: group tests are not safe against a designer who signs the minor reliances
    against the main.

So "the proxy is worth 0 against an adversary" is a property of **one-batch commitment**, not of the proxy. bayes_voi
§3.5's "0.69 at B = 7" is pooled over two-part episodes; on trap episodes alone it is about 0.38 (pooled policy), below the trap-only optimum of 0.46 at B = 7 in the table above.

### R4. Additive or multiplicative under noise? (search_bai: under noise X becomes a constant ratio ≈ 2.9)

**Ruling: rejected.** The 2.9 is H_blind / H_proxy = 11 / 3.79. It comes out constant only because one binary-channel
capacity C is applied to both arms, and Fano lower bounds are not success curves. Real noise is asymmetric: group
texts degrade and isolations of strong mains do not. Read off compute §3.4:

| target | proxy needs | blind needs | ratio |
|---|---|---|---|
| 0.90 | ≈ 5 | ≈ 25 | ≈ 5 |
| 0.95 | ≈ 7 | ≈ 48 | ≈ 7 |

The ratio is not constant, and it is not 2.9.

A second point on the same formula: "queries ≈ H/C" with C = 0.54 bits for an isolation is a heuristic. For
one-candidate-at-a-time search the exact cost functional is guesswork, the expected rank Σ r·π(r) (Massey and Arikan;
search_bai's own §2 table uses it), not Shannon entropy divided by a rate.

- Blind: 4.375 isolations per probe.
- H/C: 3 / 0.54 = 5.6.

So H/C overstates the cost of isolation search.

### R5. Are proxy and queries complements? (bayes_voi: complements, not substitutes)

**Ruling: only at very small budgets.** The per-query bits argument (0.95 vs 0.54) applies to the first query only.
The economic test is the marginal value of one more query (`ref_checks.json`, from compute §3.1):

| budget range | with the proxy | blind |
|---|---|---|
| B = 2-4 | +0.17 per query | +0.11 per query |
| B = 5-8 | 0 | +0.09 per query |

At B ≤ 4 the two are complements; at B ≥ 5 they are substitutes. The paper's B = 8 is in the substitute region.

### R6. What is the free trap signal G worth in one-batch play? (compute §6: 1-2 texts at B = 5-6)

**Ruling: overstated about 3×.** compute §6 counts a trap episode as solved only if the trap's rank 2 was isolated
(cover-only decoding). A calibrated decoder also uses elimination. If the null's rank-2 test reads negative, the other
unexplained probe is the trap; if neither was tested, it guesses. With elimination (`ref_checks.json`), shipped mix,
noiseless:

| decoding | B = 5 | B = 6 | B = 7 |
|---|---|---|---|
| no signal, cover-only (compute) | .62 | .75 | .88 |
| no signal, elimination | **.875** | **.958** | **1.0** |
| G signal (d′ = 1.02), elimination | .926 | .984 | 1.0 |

G is therefore worth about +0.05 at B = 5 and +0.03 at B = 6, about half a text, not 1-2.

The same elimination argument corrects bayes_voi's "adaptivity is worth about 3 queries (5 vs 8)". A calibrated
one-batch agent reaches 1.0 at B = 7, as search_bai §3.2 says, so adaptivity is worth 2 queries. It also means
top-one coverage (B = 4) is worth 0.75, not 0.50, to an agent that decodes calibratedly: it guesses rank 2 on one of
the two negatives instead of answering `none`. This supports bayes_voi's point that decoding matters as much as
allocation.

### R7. Do the data show that the proxy has *negative* value for top-one agents? (all four say yes)

**Ruling: the theory predicts it is possible; the data do not show it.**

| comparison | proxy | no proxy | Fisher p |
|---|---|---|---|
| Haiku, traps | 0/6 | 2/6 | 0.45 |
| Luna, trap slot | 1/18 | 2/12 | 0.55 |
| Luna, trap NAME (Table 2 / F4) | 1/18 | 1/12 | 1.0 |
| Haiku + Luna pooled | 1/24 | 4/18 | 0.15 |

The 2/12 that every theorist quotes for Luna is the trap *slot*, not NAME (App. F4: "trap NAME 1/12"). The paper's own
§5.1 sentence ("trap 1/18 vs 2/12") mixes these with Table 2's 1/12. **Fix that sentence in the paper.**

The clean demonstration of negative value is the privileged pair:

- top-one 0.00 on traps against the blind script's 0.38 at the same B = 8;
- the misspecified-agent DPs (compute §3.2).

It should be stated as a model result with consistent, non-significant point estimates for Haiku and Luna.

### R8. "Probability" or "game"? (game_theory: the trap is chosen, so minimax; statistician: game theory not needed for fixed items)

**Ruling: both, at different levels.**

- **Scoring the shipped six items.** This is a Bayesian decision problem under a fixed item law, plus agent
  misspecification. Expectations are the right object, and the statistician is right that the data identify
  nothing minimax: one designer move, rank 2.
- **Claims about what the benchmark measures.** Game theory is right that the trap placement is a designer strategy
  chosen against agents. Blanket top-two "solves" the shipped mix (Goodhart at the benchmark level), and the shipped
  score cannot distinguish trap detection from a known-depth prior. The paper concedes this ("widening by one step,
  not depth").

The bank's rank-6 traps are the cheap way to probe the game.

### R9. Is the ideal ≈ 7 queries the proxy's "true" worth? (bayes_voi and search_bai: the one regime where X is a tool property)

**Ruling: arithmetic confirmed; interpretation qualified.**

- **Arithmetic.** The entropies check out:
  - 11 = 2 + 3·3 bits;
  - 3.79 = 3 × (1/8)·3 + ½·log₂ 24;
  - noiseless group optimum 12 vs 5 texts.
- **Interpretation.**
  - The 7.2 bits depend on the item mix: 5.8 under adversarial scatter, 7.5 under the bank law.
  - They are realized in queries only on a noiseless OR channel that the environment does not have: group texts
    fall to 0.50 on stored readings.
  - "7 queries" is therefore the proxy's worth to an ideal agent on an idealized channel. It is a useful reference
    line, not the tool's intrinsic price.
  - The match "7 = 7.2" partly comes from integer rounding: ⌈11⌉ needs 12 and ⌈3.79⌉ needs 5.

### R10. The statistician's coverage arithmetic (36 ≈ 8 + 24 × 1.17; BB-8 0.25 = 8/32)

**Ruling: an illustration, not evidence.** ρ = 1.17 is solved backward from 36. And 8/32 is not the blind optimum at 8
(0.36 under the exact isolation DP), so Terra matching 8/32 is a coincidence of its near-uniform allocation. K/w = 4
is a sensible order-of-magnitude scalar. The statistician's identification results stand:

- bracket (16, 64] at run level, (8, 64] at item level;
- 36 is one of 11 fits spanning 22-58;
- B\* = 28 / 36 / 133 at 22 / 23 / 24 of 24;
- X is flat in proxy quality at the ceiling.

These are the strongest single critique of the paper's "≈ 36".

---

## 3 The author's intuition, point by point

| author's claim | verdict | why |
|---|---|---|
| It is structural and probabilistic: an ideal actor narrows down with imperfect tools, then spends few exact queries | **Right** | This is Bayesian search with a prior from the proxy (Stone; fixed-budget identification). The ideal proxy agent spends 4-5 texts, 1.25 of them on the hard probe (compute §3.3). |
| The budget must be allocated across the whole episode | **Right, and central** | Most of the proxy's value on trap episodes flows through the probes it gets right (A4; R3 adaptive table). |
| Noise has to be accounted for | **Right for the blind side** | Noise moves B\* from 11 to ≈ 50 and costs the proxy arm 0.03 (R2). |
| On traps the SAE is worth exactly 0 because it is wrong | **Wrong as a statement about the SAE; right in two narrower senses** | Information: a deterministic rank-2 error leaves full information (A2). It is 0 (or negative) to an agent that believes the top candidate (A3, R7), and ≈ 0 in the one-batch minimax game against a designer free over ranks (R3). It is not 0 for an adaptive agent even in that game (0.51 vs 0.36 at B = 8). |
| On ordinary cues it is worth exactly 1 because it is right | **Wrong** | It is worth 3 bits per probe (≈ 3.4 isolations), plus the budget it frees for the hard probe. |
| It is not "SAE vs probe-query worth" | **Mostly right** | X is a legitimate derived number but conditional on agent, channel, mix and target, and censored at B = 8. The primary object is the success surface S_A(B, π). |
| Maybe there is a mathematical generalization, maybe game theory | **Yes: see §4.** Game theory is needed only when the trap law responds to the agent. | |

---

## 4 The generalization the four notes converge on (stated once, cleanly)

1. **Score is linear in the item law.** Fix any policy A, adaptive or batch. Let S_A(r) be its success when the hard
   truth sits at proxy rank r, with the other probes and the null as shipped. For an item law π,
   **S_A(π) = Σ_r π(r)·S_A(r)**.
   - For a blind policy S_A(r) is flat, because it cannot see ranks.
   - Under clean single isolations in one batch, S_A(r) is the agent's coverage of rank r on the hard probe. This is
     game theory's depth-response curve and the statistician's coverage.
2. **Three values follow from the same object.**
   - Bayes: V(π) = max_A S_A(π), which is convex in π.
   - Misspecified: S_{A\*(π̂)}(π) for an agent planning with π̂, with loss L(π̂, π) = V(π) − S_{A\*(π̂)}(π) ≥ 0.
   - Robust or minimax: max_A min_{π∈Π} S_A(π).

   Blackwell's guarantee (the proxy is never harmful) holds for V. It fails for the misspecified value, which is
   where the "0" and the negative values live.
3. **The proxy's value to agent A** is Δ_A = S_A^proxy(B) − S_A^blind(B). It splits exactly into (information to the
   ideal) + (A's blind shortfall) − (A's proxy shortfall, including L(π̂, π)).
4. **The exchange rate** is X_A = (S^blind)⁻¹(S_A^proxy(B)). It is a nonlinear functional of three curves, not a
   constant. It is censored when S^proxy is near 1, and it scales with the blind channel's cost, not the proxy's
   information.
5. **The proxy's own summary** is its per-type coverage curve Π_t(n) = P(truth in the proxy's top n). Its per-probe
   cost is guesswork Σ r·π(r) for isolation search and entropy H(π) for group testing.

---

## 5 What the paper should change (consensus that survives review)

1. **Keep C1 (+0.71 at matched B = 8) as the headline.** Replace "worth ≈ 36" with the identified bracket:
   "between 16 and 64 at run level (8 to 64 at item level); point fits range 22-58". Say that the figure is
   conditional on agent, exact channel and item mix, and censored because the proxy arm is at ceiling.
2. **Add the ideal references** in one line: a calibrated noiseless agent needs 5 texts with the proxy against 11-12
   (group) or 24 (single isolations) without it. Most of the distance from 12 to 36 is the cost of the exact channel
   without the proxy.
3. **Add the decomposition range:** information 0.30-0.64, Terra's blind shortfall 0.10-0.45, proxy shortfall
   0.00-0.04.
4. **On traps, say:** "the proxy's information is intact on a rank-2 trap; what fails is an agent's model of it, and a
   one-batch agent is exposed to a deeper trap". Do not write "the data show negative value" (R7). Fix the Luna 2/12
   vs 1/12 sentence.
5. **Cheapest new evidence:** a proxy arm at B = 4 (uncensors X) and the bank's rank-6 traps (the depth point of
   S_A(r)).

---

## 6 Errors found in the submitted notes (for the authors of those notes)

- **bayes_voi**
  - Its blind single-isolation curve is a heuristic about 0.2 below the exact optimum, which drives a wrong
    conclusion (R1).
  - "Adaptivity worth 3" should be 2 (R6).
  - "Complements" holds only for B ≤ 4 (R5).
  - Its Luna figure uses the slot count (R7).
- **search_bai**
  - The constant-ratio-under-noise claim is an artifact of the bounds (R4).
  - H/C is not the cost of isolation search (R4).
- **game_theory**
  - "Noise is irrelevant" confuses reproducibility with base variation (R2).
  - The adaptive minimax value is understated: 0.29 vs ≤ 0.51 (R3).
  - The rest checks out. The ε-switch at 0.543 = (0.9375 − 0.7677)/(0.9375 − 0.6248) and min(1, B/N) are both
    correct.
- **statistician**
  - The coverage numerology (36 ≈ 8 + 24 × 1.17; 0.25 = 8/32) is post hoc (R10).
  - Its identification results are the strongest in the set.
- **compute**
  - §6 uses cover-only decoding, which overstates the G signal and understates one-batch values (R6).
  - Everything else reproduced or was cross-checked.
- **All four** quote the Luna/Haiku "negative value" as shown by the data. It is not (p ≥ 0.45).
