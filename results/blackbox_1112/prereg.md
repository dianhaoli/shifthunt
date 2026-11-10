# ShiftHunt black-box study: pre-registration

This file is committed, and its SHA-256 recorded in `PREREG_HASH`, before the first counted run. It
implements `docs/EXPERIMENT_PLAN_BLACKBOX.md` (revision 2.2, approved). Where the plan left a detail open,
the choice made is stated here; choices that change or go beyond the plan are logged in `DECISIONS.md`
(D5, D13 to D15, D17 to D24). After the hash is recorded, any design change is a logged deviation and never
applies retroactively to counted runs.

`PREREG_HASH` holds the SHA-256 of this file, of both run-order files, and of the scripts this file defers to
(`scripts/score_naming.py`, `scripts/blackbox_analysis.py`, `scripts/s3_coder.py`,
`scripts/collect_rollouts.py`, `scripts/blackbox_schedule.py`).

Status of other work at the time of writing is listed in §11, so a reader can see what was already known.

## 1. Question

On the six shipped episodes, with the same image, bank and scorer: how much does removing SAE access lower
hard-slot naming at 8 exact probe queries, and how much of that loss do 64 exact queries recover?

## 2. Items, agents, arms

- **Items:** ep411, ep413, ep415 (trap hard slot, no hint) and ep472, ep474, ep476 (two-part hard slot, with
  their shipped method hint, whose text does not mention the SAE). No other episode is used. Kind is
  confounded with the hint (only the two-part items carry it); no claim is made about the hint.
- **Agents** (model plus harness, as in the main study):
  - GPT 6.1 Terra: `gpt-6.1-terra`, Codex CLI 0.166.0, `codex exec`, reasoning effort `max`.
  - Haiku 5.5: `claude-haiku-5-5`, Claude Code 2.1.296, headless `claude -p`, effort `max`.
- **Image:** `rl-task-shifthunt-r1112`, a layer on the main-study image `rl-task-shifthunt-r1103` that
  replaces only the files this study changed (tool server, task setup, grader and its reward module). The
  bank, model weights, both agent CLIs and the entrypoint are inherited unchanged. All arms run in this one
  image. The commit the image was built from is recorded in the image label and in `RUNLOG.md`.
- **Container settings** (main study's): 5400 s hard stop, 4 GB memory, 2 CPUs, at most 3 containers at a
  time on one A10G, launches at least 90 s apart, network limited to the agent's own API.

| Arm | PROBLEM string | Tools | `probe_query` texts | GPT runs | Haiku runs |
|---|---|---|---|---|---|
| Open-8 | `<ep>-open` | full SAE toolset, prompt byte-identical to the main study | 8 | 24 (4 per item) | 12 (2 per item) |
| BB-8 | `<ep>-blackbox` | task_info, help, sample_texts, probe_scores (no `ablate`), probe_query, budget, submit | 8 | 24 | 12 |
| BB-64 | `<ep>-blackbox64` | as BB-8 | 64 | 24 | 12 |
| Open-64 (conditional) | `<ep>-open64` | as Open-8 | 64 | 24 | none |

Every other budget is the same in every arm: 150 tool calls, 3000 forward units, a 3600 s wall-clock budget
for charged tool calls (server compute time is not counted; `budget`, `help` and `submit` stay available
after it), and 180 s per call.

**Black-box prompt and help.** Derived in code from the open prompt by four edits (DECISIONS D5, D24):
the SAE paragraph is deleted (with its corpus and `latent_examples` sentence); the words " plus SAE latents
to ablate" are deleted; the removal-and-kept bullet is deleted; the submit example shows `"latents": []`.
The rest of the prompt is verbatim. The help text drops the four SAE tool entries, the `[ablate]` argument
and ablation sentence of `probe_scores`, and the two header sentences about latent ids and `.npy` files; its
submit entry shows `"latents": []`; its access line reads "Access: blackbox. This episode has no SAE tools;
your own texts go to probe_query."; the rest of the help is verbatim.

Known consequences, all kept because a wording change beyond the plan's list needs the user's approval:
- The deleted bullet also contained one sentence about how a property that only occurs with another is
  compared; black-box agents do not see it.
- Some kept wording has lost its referent (the sentence limiting the latent ids a probe may list; "or are
  coin flips" on the free-text items; "per note, text or latent" in the budget line). None of it is false.
- In black-box arms the contract still requires a `"latents"` key per cue (`[]`); an answer without it is
  refused and can be resubmitted. The number of runs with a refused submission, of runs where the refusal
  message for the cue keys appears in the agent's transcript, and of those that end without an accepted
  submission, is reported per agent and arm (run level, from the tool log and the transcript; blank when the
  tool log is missing or capped).

The hint on ep472/474/476 is unchanged in every arm.

## 3. Blocks, run order, spend

- **Block 1:** GPT Open-8, BB-8, BB-64 and Haiku Open-8, BB-8, BB-64: 108 runs.
- **Run order:** one random permutation of all runs of the block, from
  `scripts/blackbox_runorder.py --block 1 --seed 20261112`, committed as `runorder_block1.csv`. Runs start
  in that order, so arms and agents are interleaved. Block 2 uses `--block 2 --seed 20261112`
  (`runorder_block2.csv`). Infrastructure re-runs go to the end of the queue.
- **Open-64 trigger:** Block 2 (GPT Open-64, 24 runs) is run iff pooled NAME rate(GPT BB-64) ≤ pooled NAME
  rate(GPT Open-8) − 0.20, on point estimates over counted runs. It is evaluated once, when every GPT job of
  Block 1 is recorded as counted or given up. Block 2 runs after Block 1, so C3 is not interleaved in time
  with BB-64.
- **Spend:** two caps tracked separately in `RUNLOG.md`: OpenAI ≈ $800, Anthropic ≈ $130. Before each block
  the projected spend must stay within the relevant cap; the scheduler also stops launching a provider's jobs
  if its ledger plus the estimate for running and next jobs would pass the cap minus a $5 contingency. Such a
  stop does not cut an arm: the jobs stay queued and the user is asked for a spend increase. GPT cost = Codex
  token counts × the main study's assumed list prices; Haiku cost = Claude Code's `total_cost_usd`.
- **Cut order (time only):** if at a check the projected finish of Block 1 (jobs not finished × mean wall
  time per job so far ÷ 3) is after Nov 14 12:00 UTC, cuts are applied in this order, each only as far as
  needed: Haiku BB-64; then Haiku Open-8 and BB-8 to 1 run per item; then Open-64 (Block 2 is not run).
  A cut is final and removes only jobs not yet started; "to 1 run per item" keeps, per item, the earliest job
  in the committed order and every job already started. GPT Open-8 and GPT BB-8 are never cut.
- **Stop:** no agent run starts after Nov 15 12:00 UTC. If Block 2 is incomplete then, C3 is reported on the
  runs done and labelled incomplete.
- **Pilots (excluded from every analysis):** GPT Open-8, BB-8, BB-64 on ep411 and Haiku BB-8 on ep472. Pilot
  fixes may repair implementation bugs only.

## 4. Outcomes (computed by the same scripts in every arm)

NAME, its decomposition, S1, S2 and S5 are recomputed offline from each run's `grade.json` by
`scripts/score_naming.py`, from the per-probe records only (`details.probes[].checks.identified`,
`.no_extra`, each record's `kind`, `pass` and `bucket`) and the top-level `hard_slots`. The container's own
`score`, `slot_pass`, `name` and `naming_slot_pass` are not used. The arm is checked against the run's
`episode_id` and grade.json's `access` and `probe_query` limit. S4 is read from grade.json's budget counters
and timing, the tool log, the engine log and the collector's summary row; S3 from the full-text tool log.
Which runs are excluded as infrastructure failures is read from each batch's `infra_failures.jsonl` (§7).

- **Primary, NAME:** 1 iff the hard slot is identified and has no extra cue, and every null probe is answered
  `none`. (A regex identifies a main cue if its matches agree with the cue's presence or absence with
  balanced accuracy ≥ 0.8, in either polarity, on the hidden notes.) A counted run without an accepted
  submission has NAME = 0.
- **Decomposition:** identified; no_extra; null false claims.
- **S1:** plain-slot naming (non-hard planted slots named / slots), over runs with an accepted submission.
- **S2:** null false-alarm rate, over runs with an accepted submission. The number of counted runs without
  one is given next to S1 and S2.
- **S3, "true cue varied cleanly"** (mechanical, from the full-text tool log; `scripts/s3_coder.py`, joined
  to the scorer's rows on batch and run): scored texts = the agent-written texts of accepted `probe_query`
  calls on the hard probe, in call order, duplicates kept. Texts are normalised only by removing `\r` and
  trailing newlines. Each text is mapped to 0/1 flags by the generator's detectors for that episode.
  S3 = 1 iff
  (a) some pair of scored texts differs in the main's detector and in at most one other detector, never the
  parent, with the parent on in both texts for a two-part item; or
  (b) over the scored texts (for a two-part item, those with the parent on), the main's column is not in the
  linear span of the constant and the other detectors' columns.
  Fewer than two scored texts gives S3 = 0. A run whose full-text log is missing or not intact has S3
  missing; such runs are left out of the S3 tables and counted next to them.
  The detectors are validated before the hash on about 50 hand-labelled logged pilot texts (all available
  free-text texts, at most 8 since only one pilot is on a free-text item, and the rest templated). A detector
  error found there is fixed as an implementation bug before any counted run is coded; a later fix is a
  logged deviation.
- **S4:** `probe_query` texts used (total and on the hard probe); USD; tokens; wall time. Tool, forward and
  query budgets are identical across agents; token budgets cannot be matched across harnesses, so tokens and
  USD are reported.
- **S5:** full pass of the hard slot in the open arms (naming, removal and kept). Expected: S5 equals the
  hard slot's naming in the open arms (main study: no removal or kept failure in 64 runs).
- **Drift check** (descriptive, no test): fresh GPT and Haiku Open-8 pooled rates with Wilson intervals
  against the main study's 14/16 and 8/16, and the mean over the six items of the fresh per-item rate against
  the same mean in the main study (GPT 0.833, Haiku 0.472; the main study ran 2 or 3 runs per item).
- **By kind:** C1, C2 and C4 are also reported for trap items and two-part items separately (3 items each;
  for GPT with the unadjusted permutation p and the approximate interval, outside the Holm family; for Haiku
  as differences with approximate intervals only). C3 is not split by kind. Two-part-only C1 is a named
  secondary. On trap items C1 is the net value of SAE access under an adversarial SAE view (the black-box
  arms have no decoy), so it is biased toward 0 there.

## 5. Tests (GPT, confirmatory)

For two arms A and B, the statistic is T = mean over items of (NAME rate in A within the item − NAME rate in
B within the item).

- **Software:** `scripts/blackbox_analysis.py` on the rows written by `scripts/score_naming.py --study r1112`
  (only the batches `r1112_{gpt,haiku}_{open8,bb8,bb64,open64}`; pilots and every other batch are left out by
  name). Random streams: numpy 2.4.6, `default_rng` (PCG64); every test and every interval starts its own
  generator from seed 20261112.
- **Missing runs.** Nothing is imputed. If a cell has fewer counted runs than planned (a cut, or a job given
  up after two re-runs), T is computed on the runs present; an item with no counted run in one of the two
  arms is dropped from that contrast and named; permutation and bootstrap keep the per-item counts present.
  Every "rate", the predictions check and the Open-64 trigger use pooled counted runs (k/n).
- **Permutation test:** within each item, the arm labels of that item's A and B runs are permuted, keeping
  the per-item arm counts, independently across items; 10^4 Monte Carlo resamples; two-sided
  p = (1 + #{|T*| ≥ |T|}) / (1 + 10^4), ties counted with a 1e-12 tolerance.
- **Interval:** item-clustered bootstrap, 95% percentile (`numpy.quantile`, linear interpolation): items
  resampled with replacement, runs resampled within each drawn item and arm; 10^4 resamples. It is labelled
  approximate (6 clusters). Null results are reported as CI bounds.
- The permutation p conditions on the six items; the clustered interval treats items as sampled. The two can
  disagree (a small p with an interval that includes 0, or the reverse). Both are reported; the Holm family
  uses the p-values and the R3 rule uses the interval, as the plan states.
- **Contrasts:** C1 = Open-8 − BB-8; C2 = BB-64 − BB-8; C4 = BB-64 − Open-8; C3 = Open-64 − BB-64 (only if
  Block 2 runs).
- **Holm family:** {C1, C2}, family-wise α = 0.05, two-sided. A contrast in the family is "significant" iff
  its Holm-adjusted p is below 0.05. C4, C3 and all by-kind contrasts are reported with unadjusted p and
  interval, outside the family, and are not labelled significant or not.
- **R3 decision rule**, on the 95% interval [L, U] of GPT C4 (exactly one branch applies; a bound within
  1e-9 of a threshold is not past it):
  - L > −0.20 and U ≥ 0: "R3 eliminated" (with plentiful exact tests the SAE is not needed);
  - L ≤ −0.20 and U < 0: "R3 not eliminated" (the SAE contributes beyond testing capacity);
  - L > −0.20 and U < 0: "eliminated at the −0.20 margin, with a residual deficit (CI excludes 0)"; both
    parts are stated;
  - L ≤ −0.20 and U ≥ 0: "inconclusive", reported as such and never rounded either way.

  If the interval has zero width (for example both arms have no variation: every run 0, or every run 1) the
  rule is still applied as written and the report flags it and gives both arms' Wilson intervals.
  Separately: if C1 is significant and the verdict is the first or the third branch, the SAE acts as testing
  capacity (consistent with R4); under the third branch this is stated together with the residual deficit.
- **First-attempt sensitivity analysis.** Only runs without a submission can be re-run (§7), so C1, C2, C4
  (and C3) and the R3 verdict are also reported with every job's outcome taken from its first attempt, an
  excluded first attempt counting as a fail. The number of excluded runs is reported per agent, arm and
  reason.
- **Haiku:** descriptive rates per arm with Wilson and approximate item-clustered intervals, and the same
  differences with their approximate intervals. No p-values, no Holm family, no pooling with GPT.
- **Power** (simulation, `analysis_dryrun/power.md`): for one contrast at 24 runs per arm, mean over six
  scenarios about 0.67 at a 0.35 gap (range 0.61 to 0.73) and 0.89 at 0.45 (0.84 to 0.92) at α = 0.05; 0.55
  and 0.83 at α = 0.025. The test is conservative (size about 0.026 at α = 0.05). By-kind and Haiku
  comparisons have little power.

**R4 analysis (descriptive, not causal).** S3 is partly definitional of success and is measured after
treatment, so a strong NAME–S3 association is expected (the existing post-hoc split is 40/42 vs 5/22) and is
not by itself evidence that testing causes passing. The informative contrasts are: (a) the off-diagonal
cells S3 = 1 ∧ NAME = 0 and S3 = 0 ∧ NAME = 1; (b) whether the NAME rate given S3 = 1 is similar across
Open-8, BB-8 and BB-64; if it is, the BB-8 shortfall runs through failing to test, not through failing
despite testing. Both agents are tabulated. GPT BB-8 and BB-64 NAME rates are also shown next to the best
scripted blind ceilings (0.44 at 8 queries, 0.97 at 64; privileged), descriptively.

## 6. Predictions

| NAME rate | Open-8 | BB-8 | BB-64 |
|---|---|---|---|
| GPT | 0.75–0.90 | 0.2–0.5 (traps above two-part) | traps ≥ 0.7, two-part 0.4–0.7 |
| Haiku | 0.35–0.65 | 0.15–0.45 | 0.3–0.6 |

- A range prediction holds iff the pooled rate lies in the closed range; "above" is strict; "≥" includes
  equality.
- **Traps, each agent:** the trap NAME rate in BB-8 and in BB-64 will each be ≥ that agent's Open-8 trap
  rate. Without the SAE there is no promoted decoy to spend queries on, so this holds partly by construction;
  it is reported as consistent with R4, not as support for it. For GPT it is mostly a ceiling check.

## 7. Exclusions and failures

- Excluded from every analysis: the pilots; the main study's `hv` side batch and smoke runs.
- **Infrastructure failure** (excluded and re-run with the same item, arm and agent, at the end of the queue,
  at most 2 re-runs per job; its cost counts toward spend): the run has no accepted submission AND one of:
  1. no container started, or the host or the scheduler interrupted the run before it was collected;
  2. no `grade.json` (the tool daemon never became ready, or the grader failed before reading a submission);
  3. an API error ended the agent:
     - GPT (Codex): the event stream has a `turn.failed` event, or its last event is an `error` event, and
       the failure message is classed `api` by the pattern lists in `scripts/collect_rollouts.py`: a message
       that names a rate limit, a quota or billing is `api`; otherwise one saying that the context window or
       a token limit was exceeded is `context`, and one saying that the request was refused on content or
       safety grounds is `refusal`; anything else, and a failure with no message, is `api`. `context` and
       `refusal` are the agent's own failures and count as fails. An `error` event followed by further
       events (a retry that succeeded) is not a failure. A run excluded while the hard stop was reached is
       flagged for a manual look.
     - Haiku (Claude Code): a transcript message flagged `isApiErrorMessage` that contains one of "Credit
       balance is too low", `rate_limit_error`, `overloaded_error`, "invalid x-api-key",
       `authentication_error`, `insufficient_quota` (the main study's rule).

  Every excluded run is listed in `SUMMARY.md` with its reason and error message. A job that is still an
  infrastructure failure after its second re-run is not run again; its cell stays short (§5, missing runs).
- **Counted as fails** (NAME, identified and no_extra = 0), when the run has no accepted submission and is
  not an infrastructure failure: the 5400 s hard stop is reached; a budget is used up before submitting;
  every submission was malformed or refused; the agent stops without submitting; the tool daemon is killed.
  Using up a budget and then submitting is not a fail.
- A run with an accepted submission is never re-run and is graded on that submission, also if it later hits
  a limit or an API error. If the in-container grader did not grade an accepted submission (no `grade.json`,
  or one without per-probe records), the stored submission is graded offline with the same grader code and
  episode files, the regrade is logged in `RUNLOG.md`, and the scorer refuses to write the study's rows until
  that run has a grade.
- No arm is extended, topped up or re-run after its results are seen, except by the two rules above (the
  Open-64 trigger and infrastructure re-runs).

## 8. Exp C: SAE view on ordinary probes (offline)

- **Data:** the stored scan pairs of each bank probe (32 bases × single-property flips, latents and true
  logits). A child property's flips use only bases with its parent on (the scan fix).
- **Population:** every distinct ordinary planted probe source (planted, not a trap, one main, main not a
  nested child) in these 91 bank episodes: ep101–112, 201–214, 221–228, 232, 235, 241–242, 301–308, 321–323,
  411, 413, 415, 421–423, 431, 433, 435, 451–456, 461–466, 471–476, 501–504, 511–513, 601–604, 701–704. This
  is the 97-episode bank minus the byte copies ep412, ep414, ep416, ep481, ep483, ep485, which are excluded
  by name; the same list is `exp_c/exp_c.json`, `population.episodes_used`. It gives 51 distinct sources.
  Named subset: the shipped six's ordinary planted slots (12 slots, 11 distinct sources).
- **Metrics:** (1) captured fraction per distinct source: Σ Δf·g over the true Δlogit on the main cue's
  paired flips, with a bootstrap CI over bases; (2) top-candidate accuracy per distinct slot instance
  (source × aligned set × signs), with the count over all slot instances beside it: whether the top candidate
  among the sample's label-aligned properties, ranked by |SAE ratio|, is the true cue. The candidate set is
  privileged.
- Traps, nested and two-main probes are reported separately. For the shipped traps top-candidate accuracy is
  0 and the captured fraction low by construction. Only aggregates are committed.

## 9. Exp D: listing screen (text-only, exploratory)

- **Design:** per cue. Each prompt holds one 128-note sample in which one target cue agrees exactly with the
  label and every other candidate property is an independent coin flip, subject to the generator's nesting:
  a child can only be on where its parent is on, so with a child as target its parent is on throughout the
  target's class, and with a parent as target its children occur only in that class; the tentative and the
  question P.S. exclude each other. 20 cues (13 plain free-text properties, `ps_question`, `signoff_excl`,
  and five new cues made by deterministic edits) × 5 seeded samples; the same 100 prompts go to GPT 6.1
  Terra, Claude Opus 5.5, Sonnet 5.5 and Haiku 5.5 (400 calls), with no tools, no system prompt and provider
  defaults (the Anthropic request carries the required `max_tokens` = 16000; the OpenAI request sets
  `store: false`). The prompt template is committed before any call.
- **Scoring:** a cue is listed if any of the model's first 20 candidates (invalid ones included in the
  count) is a regex that reaches balanced accuracy ≥ 0.8 (either polarity) on 2048 held-out notes in which
  every candidate cue varies independently (then nesting). For a child cue BA is computed within
  parent-present notes; for the tentative-P.S. cue within notes that have a P.S. that is not a question.
  Sensitivity: the grader's own design (BA over a full grid built for that cue; for the tentative-P.S. cue
  with the question P.S. held off).
- **Outputs:** listing rate per cue per model (k/5, Wilson) and pooled over models (k/20; the same 5 samples
  go to all models, so its Wilson interval is nominal); a coarse ranking only. A call is in the denominator
  if it has a stored HTTP 200; a parse failure, refusal or truncated answer counts as not listed. One
  calibration contrast: the 13 plain cues pooled vs the two nested cues (`ps_question`, `signoff_excl`), next
  to the main-study naming rates of plain slots and of the two-part hard slot.
- This measures single-cue salience, an easier condition than real samples, which align about 8 properties
  at once. It is the first item dropped if the Nov 16 stop is at risk.

## 10. Exp E: SHIFT recall (text-only)

Two prompts (A, the plan's; B, less leading) × 3 samples × 4 models, provider defaults as in Exp D. Scored
0/1 on six SHIFT steps, plus a flag for naming SHIFT, by two blind scorers with a third reading for
disagreements, with the rubric committed before the calls (`exp_e/RUBRIC.md`). "SHIFT-style recipe" = the
first four steps. Prompt A names an SAE and a spurious feature, so it measures recall under a leading cue.

## 11. What was already known when this file was hashed

- The main study's 64 runs and every number in plan §2.
- Offline bank statistics, final values (they depend on no agent run): Exp C (`exp_c/`), the method ladder
  on the six with the scan fix (`ladder/`), the scripted blind ceilings (`blind_verify/`: best scripted blind
  NAME 0.44 at 8 queries and 0.97 at 64, privileged) and the collinearity check (`collinearity/`).
  Prototype values of these were also seen while the code was being mapped and written.
- Exp E was run and scored before this file was hashed (it does not depend on any agent run; `exp_e/`).
- The four pilot runs (excluded).
- No counted agent run and no Exp D call.
