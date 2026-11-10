# ShiftHunt: final experiment plan, week of Nov 10 2026 — REVISION 2 (for approval)

Status: **draft for the user's approval. No code written and no runs launched.**
Change markers: **[CHANGED]** = modified from revision 1; **[NEW]** = added; **[REMOVED]** = dropped.
Revision 1 (Nov 10) is in git history. `docs/EXPERIMENT_PLAN_FINAL.md` and `docs/HARDER_CUES_PLAN.md` are **superseded for this week**: new cue families are out of scope.

---

## 0. Hand-off to the implementing agent (GPU box) [NEW]

You are implementing and running this plan end to end.

- **You have final judgment on implementation, sequencing and design details.** If you find something clearly better, do it: a simpler mechanism, a bug in this plan, a cheaper path to the same evidence. Log what you changed and why in `results/blackbox_1112/DECISIONS.md` *before* acting on it.
- **These stay binding unless the user approves otherwise**, because they protect validity, not convenience:
  - commit `prereg.md` and record its hash before the first counted run;
  - never extend, top up or re-run an arm after seeing its results, except where a pre-registered rule says to (Open-64, infra re-runs);
  - total spend about $130;
  - no grader or prompt changes beyond §8.
- **Go cheap first.** Unit tests → offline scripts → 1 pilot per arm and agent (excluded from analysis) → counted runs. Fix what the pilots show before any counted run starts.
- **Do not stop until every item in §10 is done or explicitly cut by the cut order.** When something breaks, diagnose it, fix it, log it and continue. Ask the user only for a spend increase, a change to a binding rule, or something you cannot obtain (keys, hardware).
- **Record everything:**
  - `RUNLOG.md`: append-only; time, run id, arm, agent, item, status, USD.
  - `DECISIONS.md`.
  - Raw transcripts and full-text tool logs for every run.
  - The commands used for every offline script.
  - A final `SUMMARY.md` with every primary and secondary outcome and every deviation.
  - Commit and push results as they come in.

---

## 1. The question

On the six shipped episodes, with the same image, bank and scorer: **how much does removing SAE access lower hard-slot naming at 8 exact probe queries, and how much of that loss do 64 exact queries recover?**

### 1a. Where this sits in the paper's argument [NEW]

The paper claims: *agents pass or fail a probe audit on what they test, meaning which cues they think to check and whether they check before claiming.* It argues by elimination.

| Row | Claim to eliminate | Evidence (existing / this plan) |
|---|---|---|
| R1 | Failures come from not knowing the method | All models describe SHIFT when asked cold (**§6, Exp E**); plain cues at ceiling, 128/128 planted non-hard slots in the main study (existing) |
| R2 | Failures come from SAE reading | Removal never fails once the cue is named, 0 removal or keep failures in 64 main-study runs (existing); SAE-capture and top-candidate statistics on ordinary probes (**Exp C**, replaces the untracked 0/64) |
| R3 | Failures come from the tools | The no-SAE arms (**Exp A, Exp B**) |
| R4 | → what is left: testing | S3 "true cue varied cleanly" against outcome, in every new run (**Exp A, Exp B**); the listing screen (**Exp D**, exploratory) |

**This experiment can refute R3, and the pre-registration says how** (§5). If BB-64 ≈ Open-8, the SAE is not needed once exact tests are plentiful, which supports R3. If BB-8 < Open-8 but BB-64 ≈ Open-8, the SAE matters only as testing capacity, which still supports R4. If BB-64 < Open-8, R3 fails, and the paper must say the SAE contributes beyond testing.

---

## 2. Baseline numbers: which are current [CHANGED]

**Current: the 64-run main study** (batches 1 + 2, four agents × 16 runs; `results/cross_model_1103/rollouts.csv` on `main`, rows with `batch ∈ {b1, b2}`). The earlier 40-run figures (31/40, three agents) are superseded and must not be used.

| Quantity | Current value |
|---|---|
| Hard slots, all main-study runs | **45/64** = 0.70 |
| Per agent (16 each) | GPT 14/16 · Sonnet 12/16 · Opus 11/16 · Haiku 8/16 |
| Batch 1, three larger agents (matched, pre-registered) | **18/24** (6/8 each) |
| Batch 1, all four | 20/32 (Haiku 2/8) |
| By kind | traps 22/32 · two-part 23/32 |
| Haiku by kind | traps 3/8 · two-part 5/8 |
| Non-hard slots | **192/192** (128 planted + 64 nulls) |
| Removal or keep failures | 0 (smallest kept 0.858) |
| Hard failure buckets | planted_none 13 · cue_not_identified 3 · extra_cue 3 |

**Excluded from every analysis [NEW]:** the harder-variant side batch (`hv`: 4-query traps ep481/483/485 and no-hint two-part ep412/414/416) and the 4 smoke runs. The paper makes **no claim about the hint**. Wording everywhere: "**every main-study rollout**", not "every rollout".

---

## 3. Step 0 (zero cost, do first)

**0a. Code and offline work, CPU:**

1. **Naming-only scorer** `scripts/score_naming.py`. NAME = hard-slot `identified ∧ no_extra` ∧ every null answered `none`.
   **Unit-test targets [CHANGED]:**
   - must reproduce **45/64** on the main-study rows;
   - per agent **14/16, 11/16, 12/16, 8/16**;
   - batch-1 three-agent **18/24**; Haiku batch 1 **2/8**;
   - failure buckets 13 / 3 / 3.

   NAME equals the stored pass in all 64 runs, because removal and keep never failed.
2. Analysis script (within-item permutation, clustered bootstrap, Holm), dry-run on simulated data.
3. Blackbox code, budget override, full-text logging and tests (§8).
4. **Exp C** offline script (§6).
5. **Exp E** SHIFT-recall script (§6).
6. `prereg.md`: arms, n, seeded interleaved run order, outcomes, decision rules, predictions, exclusions, the Open-64 trigger, and the R1–R4 mapping.

**0b. Bank work, CPU, on the GPU box (lower priority than 0a):**
1. Scan-bug fix and regenerated `method_ladder` on the six shipped items (privileged ceilings, labelled as such).
2. Check that the aligned properties are exactly collinear with the label in all 24 shipped samples.

**0c. Pilots (excluded from analysis):** rebuild the image, then run 1 GPT run per arm (Open-8, BB-8, BB-64 on ep411) **and 1 Haiku run (BB-8, ep472) [NEW]**. They check tool refusals, budget accounting, text logging, naming-only grading, and BB-64 token cost.

---

## 4. Arms (Exp A: GPT 6.1 Terra; Exp B: Haiku 5.5)

Items: **the six shipped episodes, with the method hint as shipped**: ep411, 413, 415, 472, 474, 476. **[CHANGED: no no-hint copies.]** The run order is seeded, random and interleaved across arms and agents, in one image.

| Arm | Tools | probe_query | GPT runs | Haiku runs | Purpose |
|---|---|---|---|---|---|
| Open-8 (fresh) | full SAE toolset, unchanged prompt | 8 / episode | 24 (4 per item) | **12 (2 per item) [NEW]** | same-image control |
| BB-8 | `blackbox`: samples, probe_scores without ablate, probe_query, budget, submit | 8 | 24 | **12 [NEW]** | R3 at matched budget |
| BB-64 | `blackbox` | 64 | 24 | **12 [NEW]** | R3 with plentiful tests |
| Open-64 (**conditional**) | full | 64 | 24 | — | only if GPT BB-64 is at least 0.20 below GPT Open-8 |
| ~~Opus sign check~~ | | | | | **[REMOVED → replaced by Haiku]** |

**Haiku [NEW]:** Haiku 5.5 already has 16 main-study runs on this image family, in the same harness (Claude Code headless, `claude -p`, effort `max`). It runs fine there. Its results are descriptive only: no Holm family, no pooling with GPT.

**Cut order [CHANGED]:** Haiku BB-64 → Open-64. **Never cut GPT Open-8 or GPT BB-8.**

### Cost [CHANGED] (list-price estimates; BB-64 assumed ≈ 1.5× tokens)

| Block | Runs | Est. USD |
|---|---|---|
| GPT Open-8 / BB-8 / BB-64 | 24 / 24 / 24 | 16 / 15 / 24 → **55** |
| Haiku Open-8 / BB-8 / BB-64 | 12 / 12 / 12 | 12 / 12 / 18 → **42** |
| Pilots (3 GPT + 1 Haiku) | 4 | **3** |
| Exp D listing screen (efficient design, §6) | ~60–80 prompts | **≤ 8** |
| Exp E SHIFT recall | 12 prompts | **< 1** |
| **Subtotal** | | **≈ 109** |
| Open-64 (conditional) | 24 | **≈ 22** → total ≈ 131 |

Agent time: 108 counted runs at about 15 minutes ≈ 27 agent-hours, about 14 hours wall-clock with 2 runs in parallel.

---

## 5. Outcomes, tests and predictions

**Outcomes (identical scripts in every arm):**
- **Primary:** NAME.
- **Decomposition:** identified; no_extra; null false claims.
- **S1:** plain-slot naming (2 planted slots per run).
- **S2:** null false-alarm rate.
- **S3 (R4):** *true cue varied cleanly*. From the full-text logs, mapped to the generator's detectors: 1 iff some scored pair on the hard probe differs in the main detector and in at most one other detector, never the parent, with the parent on in both texts for two-part items; or the main's column is not collinear with the others over all scored texts. Detectors are first validated on about 50 hand-checked logged texts.
- **S4:** queries per probe; USD; tokens; wall time. Token and USD reporting satisfies the workshop's matched-budget rule. Tool, forward and query budgets are identical across agents; token budgets cannot be matched across harnesses.
- **S5:** full pass in the open arms (expected = NAME).
- **R4 analysis:** NAME by S3 within each arm, and pooled over arms with arm as a stratum.

**Tests (GPT only):**
- C1 Open-8 vs BB-8; C2 BB-64 vs BB-8; C3 Open-64 vs BB-64 if triggered.
- Exact within-item permutation (10^4), Holm at 0.05, item-clustered bootstrap 95% CIs. Nulls are reported as CI bounds.
- Power: about 0.6 for a 0.35 gap and about 0.8 for 0.45.
- Haiku: descriptive rates with Wilson and clustered intervals.

**Predictions (hashed in prereg):**

| | Open-8 | BB-8 | BB-64 |
|---|---|---|---|
| **GPT** | 0.75–0.90 | 0.2–0.5 (traps above two-part) | traps ≥ 0.7, two-part 0.4–0.7 |
| **Haiku [NEW]** | 0.35–0.65 | 0.15–0.45 | 0.3–0.6 |

- **Haiku traps [NEW]:** Haiku's trap NAME rate in BB-8 and in BB-64 will each be **≥** its trap rate in Open-8. This holds **partly by construction**: without SAE tools the decoy does not exist, and Haiku's main-study trap failures came from trusting the SAE view after its own test showed the view was wrong. It is reported as consistent with R4, not as support for it.
- **Interpretation rules (R3), fixed in advance:** see §1a. Also: if the GPT BB-8 shortfall comes with S3 = 0 in the failing runs, the BB failures are testing failures (R4).

**Exclusions:** infrastructure failures before submit are re-run with the same (item, arm, agent). Timeouts, malformed submissions and exhausted budgets count as fails. No arm is extended after its results are seen.

---

## 6. Offline and text-only additions [NEW]

**Exp C — SAE view on ordinary probes (R2; CPU; tracked script `scripts/sae_view_stats.py`). Replaces the untracked "0/64".** For every ordinary planted probe in the shipped episodes, and in the full accepted bank if cheap:
1. **Captured fraction.** The share of the main cue's true effect that the SAE view captures, i.e. the latent-visible part Σ Δf·g over the true Δlogit on paired flips, with a clustered CI.
2. **Top-candidate accuracy.** How often the SAE's top candidate, among the sample's label-aligned properties ranked by |SAE ratio|, is the true cue.

Report both per probe and pooled. State the candidate set explicitly, since it is privileged: the label-aligned properties. Traps are reported separately (0 by construction).

**Exp D — Listing screen (exploratory, text-only, no tools, no probe builds, no GPU).**
- **Purpose:** test whether how often a cue gets *listed* tracks item difficulty.
- **Task:** each of the four models receives a labelled sample in the usual format and is asked for up to 20 candidate properties, each as a regex.
- **Scoring:** a cue counts as listed if any regex reaches balanced accuracy ≥ 0.8 on held-out flagged notes, using the existing naming check.
- **Cues:**
  - calibration: the existing plain properties and the two-part child (`ps_question`);
  - new: curly vs straight apostrophes; double space after a period; digits vs spelled-out numbers; tentative vs assertive P.S.; sign-off abbreviated to an initial.
- **Repeats:** 5 per cue per model, with Wilson intervals.
- **Raw characters:** check that prompts, API calls and stored outputs preserve them byte for byte. Unit-test curly apostrophes and double spaces through the whole path.
- **Implementation [design note]:** render the five new cues as deterministic **text transforms on generator notes**, applied to a random half and flagged, e.g. `'`→`’` and `. `→`.  `. This needs no generator or probe changes. To save cost, each prompt's sample has about 8 label-aligned properties drawn from the cue pool, as in real episodes, so one prompt scores several cues. Each cue appears in ≥ 5 samples per model (about 13–20 prompts per model).
- **Scheduled** after the counted agent runs are launched.

**Exp E — SHIFT recall (R1; text-only).**
- One fixed prompt, committed verbatim before use: *"How would you use a sparse autoencoder to remove a classifier's reliance on a spurious feature? Describe the method step by step."* It does not name SHIFT.
- 3 samples per model for all four models, at default temperature; raw outputs saved.
- Scored against SHIFT's steps, using a rubric committed beforehand.
- Paper wording: "**applied a SHIFT-style recipe without being told the method**".

---

## 7. Fact-check corrections carried into the paper [CHANGED]

- Every baseline uses the **64-run** main study (§2). 18/24 is batch 1, three larger agents.
- 128/128 planted non-hard slots (192/192 with nulls) is a **pass** count. "Tested on true logits" is not coded for plain slots.
- "0/64 SAE top candidate never wrong" is **replaced by Exp C**.
- The 0/20 `sample_only` vs 7/17 comparison (older episodes, Opus 4.8) gets caveats or is cut.
- "8 of 9 rediscovered" is Opus 4.8 development runs → paper wording per Exp E.
- The f·g correlation 0.97–0.996 is from 4 of 9 development runs (outlier 0.65) → caveat or cut.
- "Four of five" two-part failures is prose-only; the prompt guarantee is not a cause.
- The trap rule and the anomaly counts are post-hoc, single-reader codes. S3 is their mechanical replacement going forward.
- The scripted trap solver (91–99%) is privileged and covers traps only.

---

## 8. Code changes (unchanged from revision 1 unless marked)

- `toolserver.py`: add `blackbox` to ACCESS and ACCESS_HELP, plus a HELP variant. It refuses probe_gradient, latent_means, latent_tokens, latent_examples and `ablate`.
- `task.py`: ACCESS_MD['blackbox'], plus a PROBLEM suffix (`ep411-blackbox64`, `ep411-open64`) written into the copied task.json budgets. `make_variant_episode.py --probe-query` is the fallback.
- `prompt.md`: a blackbox branch that removes only the SAE paragraph, "latents to ablate" and the removal/kept bullets. It keeps the guarantee and **keeps the hint on two-part items [CHANGED]**. Update `check_prompt_facts.py`.
- Grader/reward: a naming-only flag. `contract.py` already accepts `latents: []`.
- Root-only full-text logging, with hashes, of probe_query, latent_means and latent_tokens in all modes.
- S3 coder with synthetic-log tests; scorer and analysis scripts; extended ACCESS tests.
- **[NEW]** Exp C script; Exp D transforms, prompt builder and scorer; Exp E prompt and rubric. All tracked, with tests where they touch text handling.

No other grader or prompt changes.

---

## 9. Out of scope this week

New cue families (builds or runs), a real-probe pilot, the approx-logit arm, decoy-free trap twins, a PCA arm, the agent BB-16/32 arms, Opus or Sonnet in the factorial, and retrospective re-coding of old transcripts.

---

## 10. Day-by-day schedule to Nov 19

| Day | Work | Done when |
|---|---|---|
| **Mon Nov 10** | Plan approved. Start 0a: scorer (hits every target in §3), blackbox code, logging, tests. | Scorer tests pass |
| **Tue Nov 11** | Finish 0a: S3 coder, analysis dry-run, Exp C script and run, Exp E prompt and rubric, `prereg.md` draft. 0b if time allows. | Exp C numbers written; prereg drafted |
| **Wed Nov 12** | Image rebuild; 4 pilots; fix issues; validate detectors on pilot logs. **Commit prereg and record its hash.** Launch counted runs in the evening (2 in parallel). | Hash recorded before the first counted run |
| **Thu Nov 13** | Runs continue (about 108 counted). Run Exp E. Build Exp D and launch it once the agent runs are going. | All counted runs launched |
| **Fri Nov 14** | Runs finish; infrastructure re-runs. Evaluate the pre-registered Open-64 trigger; run it if triggered (24 GPT). Finish Exp D. | All arms complete, or cut per the cut order |
| **Sat Nov 15** | Scoring, C1–C3 tests, S3 vs outcome, Haiku descriptive, Exp C/D/E summaries. `SUMMARY.md`. | Every outcome in §5 computed |
| **Sun Nov 16** | Figures and results text. Hard stop for any runs. | Results section drafted |
| **Mon–Tue Nov 17–18** | Paper in the AAAI-27 kit with the elimination structure (R1–R4); independent review pass; fixes. | Full draft reviewed |
| **Wed Nov 19** | Buffer. **Submit before 22:00 PT** (06:00 UTC Nov 20). | Submitted on OpenReview |

---

## 11. Where I disagree with, or would adjust, the requested changes

1. **R3 can fail, and the paper must be ready for that.** My prior prediction is GPT BB-8 well below Open-8: the SAE works as a cheap approximate tester. That is still compatible with the thesis *if* BB-64 recovers and the BB failures have S3 = 0. If BB-64 also stays low, "not tools" is refuted. The plan pre-registers all three readings (§1a) rather than assuming R3.
2. **R2 is weaker than it sounds.** "Removal never fails" is partly true by construction: ablation here is exact and linear, and τ is low (0.15–0.25), so a reviewer can call it a property of the grader. Exp C helps, but the paper should say "SAE reading is not where failures occur in this setup", not "SAE reading doesn't matter".
3. **The listing screen (Exp D) can't really test whether listing explains item difficulty.** Difficulty varies on only two shipped types: plain cues about 100% and the two-part child about 72%. Trap failures come from verification, not listing, and the five new cues have no agent runs. So it gives a *salience ranking* plus one calibration contrast, not an explanatory test. I'd keep it, labelled exploratory, because it is cheap and the ranking guides next week's item design. Two other changes:
   - pack about 8 aligned cues per prompt, as in real samples (≈ 5× cheaper and closer to the real format; listing in context depends on which other cues are aligned, so randomize them);
   - implement the new cues as text transforms, so no generator change is needed.

   It fits the week only as a CPU side task. If the agent runs need attention, it is the first non-binding thing to slip past Nov 15.
4. **Exp E measures recall when prompted, not spontaneous use.** The wording "applied a SHIFT-style recipe without being told the method" is right. I'd avoid "knew SHIFT" as an explanation of behaviour.
5. **Haiku trap prediction:** fine as specified. I'd add the same prediction for GPT for symmetry, since it's free, but leave it out if you want Haiku-only.
6. **Budget:** the plan lands at about $109, or about $131 if Open-64 triggers. That needs the efficient listing design. The one-prompt-per-cue version (about 400 prompts) would add roughly $15–20 and push past $130.
