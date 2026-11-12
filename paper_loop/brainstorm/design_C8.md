# design_C8: the frozen report-only judge on Luna's 60 unjudged runs (out-of-sample J1-J3, and the judge-implied Terra-Luna gap)

Mini pre-registration for the GPU-box agent, written 12 Nov 2026 by the designer. Nothing here has been run.
The agent copies §§1-6 into `results/blackbox_1112/judge_luna/PREREG_JUDGE_LUNA.md` and commits its sha256, along with
the two script hashes in §2, before any paid call. Target: freeze and flags on 13 Nov, judge calls and analysis on
13 Nov, paper text on 14 Nov. Hard stop 18 Nov.

## 0. What I checked in the sources (branch `origin/claude/serene-fermi-pog4k7`, commit 85d2fac)

- **Luna has never been judged.**
  - `scripts/judge_vs_grade.py` selects batches by
    `BATCH_RE = ^(r1103_(gpt|haiku|opus|sonnet)_(b1|b2|hv|hv2)|r1112_(gpt|haiku)_(open8|bb8|bb64|bb16))$`, so
    `r1112_luna_*` is excluded.
  - `judge/inputs.json` lists 214 runs: main, harder variant, Block 1 and BB-16, with no Luna.
  - `judge.json` `hard_by_population` covers bb16, block1, harder_variant and main only.
- **The Luna data exist.**
  - The batches are `r1112_luna_open8` (36 counted runs) and `r1112_luna_bb8` (24). The pilot is in a separate
    directory, `r1112_pilot_luna_open8`, so the regex excludes it automatically.
  - All 60 runs ended with status ok (`luna/README.md`).
  - Luna runs in Codex, so `judge_vs_grade.codex_messages` reads its `codex_events.jsonl` unchanged.
  - The full-text logs recover the texts on every trap slot (`trap_rank2_isolated_missing_texts: 0` in `luna.json`).
- **Certified numbers (`luna.json`, paper Table F4).**

  | arm | trap slot | two-part slot | null probes | ordinary probes |
  |---|---|---|---|---|
  | Luna Open-8 | 1/18 | 4/18 | 36/36 | 62/72 |
  | Luna BB-8 | 2/12 | 0/12 | 18/24 | 8/48 |
  | Terra Open-8 | 11/12 | 12/12 | | |

  - Certified hard-slot passes are therefore 7/60 for Luna, and 53 hard slots are certified failures.
  - Trap failures:
    - Open-8: 17 = 10 named the [decoy] + 7 `none`;
    - BB-8: 10 = 1 named + 9 `none`.
  - How the 26 two-part failures split between `none` and partial names is **not** in any tracked file. The
    build step reports it before any call (§2, step 3).
- **The decoy-after-own-test count has no committed script.** "7 of the 10 [decoy] answers followed the agent's
  own clean pair" comes from a README, and the paper says so twice (§6 and App. G). Everything needed to compute it
  is committed:
  - `luna_analysis.batch_slots` defines `tested`: isolated in an edit-matched clean pair, via
    `followup_tflags_samplebase.mixed_clean_pairs` plus `edit_sources`;
  - `followup_trapflags.answer_key` gives (main, decoy) per trap probe;
  - `failure_flags.covered_columns` gives the properties that a submitted regex covers.
- **The Terra half of the gap has already been judged.** The per-slot verdicts for `r1112_gpt_open8` are in the
  git-ignored `results/private_1112/judge/slots.json`, on the GPU box. The only parts that have been seen are
  aggregates:
  - Block 1 Open-8, Terra and Haiku pooled: false credit 7 and false blame 5;
  - Terra Open-8 judge-implied hard-slot rate: 18-24 of 24 (the integer-split bounds, App. H).

  Terra's per-item verdicts on trap and two-part runs are **not to be opened before the freeze** (§4, disclosure).
- **Cost basis.** The L0 judge study cost $1.97 for 214 calls, or $0.0092 per call. Codex reports are short (the
  GPT median is about 1,400 characters), so 60 Luna calls should cost about $0.55.

## 1. Question

Claim 2 rests on one population of runs, whose surviving errors are mostly omissions (41 of 44 `none` failures
credited). Two objections remain open:

1. **One judge, one population.** Does the judge's failure replicate on runs it has never seen, from a different
   model?
2. **Omission-specific or fluency-driven?** Does the judge miss only what a report cannot show (an omission), or
   does it credit fluent reports whatever the error type?

Luna is the sharpest held-out test of both:

- Its trap errors include commissions made **after its own exact test refuted them**. A report reader should catch
  these most easily.
- Its gap to Terra is the cleanest in the study: the same harness, image, prompt and tools, trap 11/12 vs 1/18,
  p = 3e-6.

That lets us ask the workshop's question directly: graded by the judge, would this reported gap still be
attributable to the systems?

## 2. Data, calls and code

**Runs.** All 60 counted Luna runs: Open-8 (36) and BB-8 (24). The pilot is excluded. There are no other new
runs, so the agents cost $0.

**Judge.** It is identical to L0 in every respect:

- model `gpt-6.1-terra` through `textonly_client`, with client defaults;
- one call per run, `workers=1`;
- the same PROMPT (sha256 `83afac63…`), the same contract (sha256 `2e2a3c77…`, taken from `r1112_gpt_open8`
  for every run, BB-8 included, exactly as in Block 1);
- the same `MAX_REPORT_CHARS = 24000`, `parse_verdicts`, `kappa` and `auroc`;
- unparsed runs are reported and not re-sent.

**Code (two new files; `judge_vs_grade.py` is not edited).**

1. **`scripts/judge_luna_oos.py`** imports `judge_vs_grade as JV` and overrides three module globals before
   calling the unchanged `cmd_build`, `cmd_run` and `cmd_analyse`:
   - `JV.BATCH_RE = re.compile(r"^(r1103_(none)_(none)|r1112_(luna)_(open8|bb8))$")`. The group numbering is kept
     so that `population()` returns `("block1", "luna", "open_open8" | "blackbox_bb8")`.
   - `JV.PRIV = results/private_1112/judge_luna`
   - `JV.OUT = results/blackbox_1112/judge_luna`

   It adds one command, `gap`, which runs only after `analyse` and is described in §5. It reads Terra's verdicts
   from `results/private_1112/judge/slots.json` and Luna's from `judge_luna/slots.json`, maps each run to its item
   through `score_naming.load_batch`, and writes `gap.json`.
2. **`scripts/luna_decoy_flag.py`** is the flag script. It is committed, hashed and run **before** the judge build.
   It is CPU only and mechanical. For each Luna hard slot (Open-8 and BB-8) it rebuilds the slot exactly as
   `luna_analysis.batch_slots` does (`TF.build_slots` on `recover_from_fulltext`) and writes:
   - `error_type`. For a passed slot: `pass`. For a failed slot:
     - `omission`: answered `none`;
     - `decoy`: a trap slot whose submitted cues cover the [decoy] column;
     - `partial`: a two-part slot whose cues cover one of the two [main] columns and nothing else that is
       label-aligned;
     - `other_commission`: any remaining named failure.

     For comparability, `omission` and the union of the other three are also the J3 split ("answered none" vs
     "named a wrong cue").
   - `decoy_tested`: the [decoy] column is in the slot's `tested` set (the `luna_analysis` definition).
   - `decoy_dT`: the mean signed true-logit effect of the [decoy] over its isolating pairs, in topic units. Below
     |0.15| counts as refuting (the contract's non-cue ceiling), 0.15-0.30 as ambiguous, and 0.30 or more as
     supporting.
   - `refuted_then_submitted`: `decoy` and `decoy_tested` and `decoy_dT` refuting.
   - `report_quotes_refutation` (E+ / E−). The report string the judge sees (`"\n---\n".join(codex_messages)`,
     after the same cap) contains a decimal number with at least 2 decimals within 0.005 of either true logit of an
     isolating [decoy] pair, or of their difference. Pure regex plus float parsing, with no LLM.

   The script also does the following:
   - **Unit tests** run on synthetic slots only.
   - **Validation gate.** The script must reproduce `luna.json`'s Open-8 trap failures = 17 and `none` = 7, and
     BB-8 = 10 and 9. If it does not, it stops.
   - **The README count is not a gate.** The script reports its own count of `decoy` and `decoy_tested` on Open-8
     traps (README: 7 of 10). If that count differs, the script's number supersedes the README everywhere, and the
     difference is logged.
   - **Outputs.** Tracked output holds counts only, in `judge_luna/flags.json`. Per-run rows go to `private_1112/`.
     No property name, and no (episode, property) pairing, appears in tracked text: use [main] and [decoy] only,
     and run `s3_coder.property_names_in` on every tracked file.

**Order of steps (each step is committed before the next starts).**

1. Write both scripts and their tests. Record the sha256 of the script, the template and the contract in
   `FREEZE_LOG.md`. Commit the prereg and its hash.
2. Run `luna_decoy_flag.py` and commit `flags.json`. This depends only on traces, never on the judge.
3. Run `judge_luna_oos.py build`. Gates:
   - runs = 60;
   - `contract_sha256` and `prompt_template_sha256` equal the L0 values;
   - report how many reports hit the cap, and the median `report_chars`.

   Commit `inputs.json`, which records the hard-slot error-type split.
4. Run `judge_luna_oos.py run --budget 1.5`. The expected cost is $0.55. If the guard trips, stop and report;
   do not raise the guard.
5. Run `analyse`, then `gap`. Commit `judge.json`, `gap.json` and the README.

**Reuse.** If design C6 runs later, its Luna L0 rung *is* this run. C6 should read these verdicts and not re-send
them, which saves about $0.55 there.

## 3. Outcomes and definitions (identical to J1-J3)

- **Certified outcome.** `naming_slot_pass` per probe. The hard slot is `grade.json hard_slots`, one per run.
- **Judge-implied pass.** The judge's `correct` verdict on the hard slot.
- **False credit.** The share of certified-failed hard slots that the judge marks correct.
- **False blame.** The share of certified-passed hard slots that the judge marks incorrect.
- **Matched gap (Open-8 only, the same arm as L1 and L2).**
  - Δ_cert(trap) = 11/12 − 1/18 = **0.861**.
  - Δ_cert(two-part) = 12/12 − 4/18 = **0.778**.
  - Δ_judge is the same difference computed on judge-implied passes of the same 30 runs per kind.

## 4. Hypotheses (fixed before any Luna judge call)

| id | type | prediction | test and threshold |
|---|---|---|---|
| **J1-L** | confirmatory (replicates J1) | The judge is not a grader on held-out runs. | κ on Luna's 60 hard slots < 0.40. With only 7 certified passes, κ carries little information, which is why J2-L is listed next to it. |
| **J2-L** | confirmatory (replicates J2) | It credits most of Luna's failures. | False credit on Luna's certified-failed hard slots (n ≈ 53) ≥ 0.50: a point threshold, the same form as J2. Wilson 95% interval reported. |
| **G1** | confirmatory (new; the headline) | Under the judge, the study's cleanest model gap shrinks by more than half. | Δ_judge(trap, Open-8) < **0.431** (half of 0.861): a point threshold. Pre-stated companion: the one-sided Fisher p for "Terra > Luna" on judge-implied trap passes is **≥ 0.05** (certified: 3e-6). |
| G2 | descriptive, predicted | The same holds on two-part probes. | Δ_judge(two-part, Open-8) < 0.389 (half of 0.778), with its Fisher p. |
| J3-L | descriptive, predicted (replicates J3) | Omissions are credited at least as often as commissions. | False credit on `omission` ≥ 0.70 pooled over all 60 runs; on Open-8 trap `none`, ≥ 5/7. Two-sided Fisher on omission vs commission (J3 split). |
| **J14** | descriptive; the sharp test | The judge credits even a commission that the agent's own exact test refuted. | Of the `refuted_then_submitted` slots (k ≈ 7), the judge credits ≥ 5/k (scaled as ⌈0.7k⌉ if k ≠ 7). Reported separately for E+ and E−. |
| J15 | descriptive | Interpretation key for J14. | E+ credited means "the evidence was in the report and ignored". E− credited means "the evidence was not reported". If E+ = 0, J14 says nothing about reading, only about what reports contain, and the text says so. |
| J4-L | descriptive | | Agreement by arm (Open-8, BB-8) and by `error_type`. AUROC of the judge's confidence on hard slots. False blame on the 7 passes. Median report length vs Terra Open-8. |

**Decision rule for objection 2, written now.** Let CC be false credit on Luna's commissions (`decoy`, `partial` and
`other_commission` pooled).

- **Fluency-driven:** CC ≥ 0.50 **and** J14 ≥ ⌈0.7k⌉.
- **Omission-specific:** CC < 0.50, **and** J14 ≤ ⌊0.3k⌋, **and** omission credit ≥ 0.70.
- **Mixed:** anything else, reported as mixed with the counts.

**Disclosure, entered into the prereg.**

- Terra's Open-8 verdicts already exist. The designer has seen only the aggregates listed in §0.
- The GPU-box agent must not read Terra per-item or per-kind verdicts before the freeze commit. The `gap` command
  is the first code to read them.
- The certified Luna outcomes are known. Every hypothesis concerns the judge's verdicts, which are not yet known.

**Run-set rule.** No prompt, threshold, flag definition or run set changes after the freeze. The single allowed
exception is the README-vs-script count in §2, which only changes k.

## 5. Analysis

- **Unit of inference: the run** (one hard slot per run). Every p-value is run-level and conditional on the six
  shipped items. Luna and Terra runs are independent, so Fisher tests on judge-implied counts are valid at the
  run level.
- **Item-level floor.**
  - The trap gap rests on three items, with 4 Terra and 6 Luna runs each. The text reports the per-item Δ_cert and
    Δ_judge, and the count of items on which the judge shrank the gap (x/3).
  - A one-sided sign test on three items cannot go below 0.125, and the text says the gap result is run-level
    only, as the paper already does for L1 and L2.
- **Intervals.**
  - Δ_judge: a stratified bootstrap (resample runs within item, within model; 10,000 draws, seed 1113).
  - Rates: Wilson.
  - κ: the L0 method (resample hard slots), stated as too narrow under clustering.
- **Shrinkage decomposition (exact, arithmetic).** Δ_cert − Δ_judge = (Terra false blame − Terra false credit)/12 +
  (Luna false credit − Luna false blame)/18. Both terms are reported, so a reader can see whether the shrinkage
  comes from crediting Luna or from blaming Terra.
- **Self-preference.** Terra judges Terra but not Luna. Any self-preference would raise Terra's judge-implied rate
  and so *widen* Δ_judge, which works against G1. This is stated.
- **Multiplicity.** J1-L, J2-L and G1 are point thresholds, each reported as passing or failing with no
  correction. The G1 Fisher companion and the J3-L Fisher test are descriptive p-values.
- **Missing data.** An unparsed call is dropped and counted. If either an Open-8 trap run or a two-part run is
  unparsed, G1 and G2 are computed on the parsed runs, and the certified gap is recomputed on the same runs.

## 6. Cost and hours

| item | estimate |
|---|---|
| 60 judge calls (Terra, about $0.0092 each) | **$0.55** (guard $1.50) |
| flag script and tests, wrapper, freeze | 2 h of agent work |
| calls (about 30 s each, `workers=1`) | 0.5 h wall time |
| analysis, `gap`, counts-only README | 1 h |
| **total** | **about $0.55 OpenAI, $0 Claude, 3.5 h.** This leaves about $33.4 of the OpenAI budget. |

## 7. What it adds to the paper, by outcome

**Body addition (§5.2, after J3):** one paragraph of about 80 words, plus a 4-row inline table. The table is placed
next to the paper's existing Terra-Luna numbers, so it is read as the attribution test.

**Table 2b. "The study's cleanest model gap, certified and as the judge would grade it" (Open-8, hard slot, same
runs).**

| | Terra (12 trap / 12 two-part) | Luna (18 / 18) | gap | one-sided p |
|---|---|---|---|---|
| trap, certified | 11/12 | 1/18 | 0.86 | 3e-6 |
| trap, judge-implied | a/12 | b/18 | Δ_t | p_t |
| two-part, certified | 12/12 | 4/18 | 0.78 | |
| two-part, judge-implied | c/12 | d/18 | Δ_p | |

There is also one new row in Appendix H's agreement table: Luna's κ, false credit split into omission and
commission, false blame and AUROC. The J14 counts (E+ and E−) go in App. G next to the existing decoy-after-test
note. That note loses its "[README count, no committed script]" tag, because the count is now produced by a
committed script.

**Pre-written paragraphs.**

- **Confirm** (J1-L, J2-L and G1 hold; fluency-driven). "The judge's failure replicates on 60 held-out runs from a
  second model (Luna; κ = x, false credit y/53), whose failures are mostly commissions. It credits z of the k
  answers in which Luna submitted the [decoy] *after its own exact test had refuted it*, including e of the e′
  reports that quote the refuting logit. Graded this way, the study's cleanest model gap, Terra over Luna on the
  trap (0.86, p = 3e-6, same harness), shrinks to Δ_t (p = p_t). The gap could no longer be attributed to the
  models." Claim 2 is retitled "a report-reading judge cannot replace the grader, or attribute a gap to a system".
  The abstract's second finding gains: "…and on a held-out model it shrinks the study's largest gap from 0.86 to
  Δ_t."
- **Omission-specific** (G1 holds or fails; CC < 0.50; J14 ≤ ⌊0.3k⌋). "On held-out Luna runs, the judge catches
  most commissions (it rejects m of k refuted [decoy] answers) but still credits y of n `none` failures. Its blind
  spot is omissions, not reports in general." Claim 2 narrows to "a report cannot certify an omission". This
  sentence already exists, and it becomes a tested statement. "Audit negative verdicts first" gains held-out
  support. If G1 still holds, add: "Even so, it shrinks the trap gap to Δ_t, because Luna's 16 `none` failures
  are credited."
- **Reversal** (κ ≥ 0.40, or false credit < 0.50, and Δ_judge ≥ 0.431). "On Luna, the same judge grades usefully
  (κ = x) and preserves the model gap (Δ_t). Its failure on the main runs is specific to those reports: fluent,
  confident and mostly `none`." Claim 2 is scoped to "the larger agents' reports". The Scope paragraph states that
  judge validity depends on the population. This outcome is reported as prominently as the confirm outcome, and
  it is itself a workshop-relevant finding: a judge's validity does not transfer across the agents it grades.
- **E+ = 0, so Luna never quotes the refuting number.** This is added whichever branch holds: "Luna's reports never
  contained the refuting reading, so this commission was invisible to any report reader." That supports the
  paper's recommendation to log every exact query, and links to C6.

**What it replaces in the 8-page body** (net about −20 words, given that RANK_V4 says V4 is over length):

- The §5.2 integer-split sentence: "For Terra alone, the budget effect falls to between −0.21 and +0.38 … (derived
  from the J4 tables; Appendix H)", about 50 words. It moves to App. H. Table 2b is the measured,
  pre-registered example of "conclusions would change", which makes the bounds unnecessary in the body.
- The §5.2 Scope sentence: "We tested one report-only judge with one prompt … using the same model as the main
  agent". It becomes "one judge and one prompt, on two agent populations (§5.2, Table 2b); a judge given the
  exact-query log is untested", or "is tested in Table 2" if C6 runs.
- In §5.3, "Even after scaling by Luna's lower rate of testing the favourite … (post hoc; Appendix K)", about
  45 words, moves to the appendix, as RANK_V4 fix 1 already asks. This pays for Table 2b's four rows.

## 8. Risks

- **Power.** There are only 12 and 18 runs per arm on traps. If the judge credits Luna heavily, Δ_judge will be
  small, but its bootstrap interval spans about ±0.3. G1 is a point threshold for that reason, and the text calls
  it run-level on three items.
- **Short reports.** Luna's Codex messages may be very short, and some runs may have no messages at all (the judge
  then sees "(the agent wrote no messages)"). If so, the judge is grading the bare answer. Median `report_chars`
  and the number of empty runs are reported, and J15 handles the interpretation.
- **Terra-side contamination.** Terra's verdicts were made in a different session, on 12 Nov, with the same
  prompt and client. A date or version drift in `gpt-6.1-terra` between 12 Nov and 13 Nov cannot be excluded. The
  `meta` model string is logged and compared, and any difference is disclosed.
- **Flag fidelity.** E+ uses numeric matching only. A report that paraphrases a reading ("the [decoy] edit barely
  moved the logit") counts as E−. This makes E+ conservative. No reader coding is added.

## Critic

Written 12 Nov 2026 by the adversarial critic. Checked against `origin/claude/serene-fermi-pog4k7` (85d2fac), the paper (V4_user), RANK_V4, the idea bank and the sibling designs C6 and C19. Nothing was run and no money was spent.

**Verdict: RUN WITH CHANGES.** It is cheap (about $0.8 with the changes below), it finishes in about half a day, and the flag script fixes a weakness the paper already admits. The headline as written (G1) is weaker than it looks, for three reasons. It is largely predictable from committed numbers. It is one pair of C19's ranking. And as specified it is confounded by judge drift and by report length. Reposition the result, add the controls, and keep it out of the abstract unless C19 does not run.

### What checks out

- **The data are there.**
  - `BATCH_RE` excludes `r1112_luna_*`.
  - `population()` branches on `batch.startswith("r1103")` and reads groups 4 and 5. The override regex therefore yields `("block1", "luna", "open_open8" | "blackbox_bb8")` as claimed.
  - The pilot (`r1112_pilot_luna_open8`) fails the anchored regex.
  - `codex_messages` is harness-generic.
  - The `luna.json` gate values exist: Open-8 `answered_none` 7 of 17, BB-8 9 of 10. Table F4 shows the BB-8 trap slot at 2/12.
- **The arithmetic is right.**
  - Certified Δ = 0.861 (trap) and 0.778 (two-part).
  - The shrinkage decomposition is an exact identity, provided FB and FC are counts, not rates.
  - The self-preference argument holds: Terra judging Terra can only widen Δ_judge, so it is conservative for G1.
- **The private dependency is real but unverifiable from here.** `results/private_1112/judge/slots.json` lives on the GPU box. Step 0 has to check that it exists; if it does not, rebuild it with the L0 `analyse` from `raw/`.
- **Time and money.** It costs about $0.55 plus about 3.5 h of agent time. It fits on 13 Nov, even with C6, C7, C17 and C19 queued on the same box.

### Where it breaks

1. **G1 is mostly predictable from committed counts, and the prereg does not say so.**
   - Terra Open-8 has a certified 23/24, and its one failure is a trap. The judge's false blame in Open-8 is at most 5 (App. H: 28 − 5 + 7). So Terra's judge-implied trap count a lies in [6, 12].
   - G1 holds iff Luna's judge-implied trap count b > 18(a/12 − 0.431). That means b ≥ 2 at a = 6 and b ≥ 11 at a = 12.
   - With the L0 credit rates (`none` 41/44, wrong cue 12/24), the expectation is b ≈ 1 + 6.5 + 5 ≈ 12.5. **G1 then holds even in the worst case for a**, with an expected Δ_judge of about 0.1-0.3. I put P(G1) at about 0.8.

   A statistician will say "a judge at κ ≈ 0 compresses every gap; this is J1 restated." C19 hit the same issue and solved it by printing each known bound next to its test. Do the same here.
2. **G1 is a single pair of C19.** C19 already plans "optionally Luna, from C8, for 13-14 systems" and reports Kendall τ in AstaBench's units. Run as a separate body table, Table 2b and C19's table would make the same point twice in an over-length paper. The pair has its own value, because it is within one harness and pre-registered, but its place is as the illustrative row of C19, not as a second headline.
3. **Judge drift is uncontrolled, and there is no noise floor.**
   - Terra's verdicts are from 12 Nov and Luna's would be from 13 Nov or later, both sampled with unseeded client defaults.
   - Δ_judge subtracts a quantity measured on one day from one measured on another. The judge's test-retest agreement is unknown; the C6 critic raised the same point as its break 2.
   - Logging the model string does not detect sampling variance.
4. **Report length is confounded with the model.**
   - Luna sends its texts in one burst (36/36) and probably writes far less prose than Terra.
   - If Luna's reports are near-bare, the judge is grading an answer line against Terra's narrative. Δ_judge then measures how much information the judge had, not how credulous it is.
   - The "fluency-driven" branch would be wrong in name and in substance: nothing in the design measures fluency.
5. **`partial` is not a commission.** A two-part answer that names one of the two [main] cues is an omission of the second cue. Pooling it into CC biases the objection-2 decision rule toward "fluency-driven" in proportion to the number of partials. That number is unknown (§0), and it could be most of the 26 two-part failures. Keep the L0 J3 split for comparability, since L0's "named a wrong cue" also contained partials, but take `partial` out of CC.
6. **E+ has no false-positive control.** A Luna report may contain dozens of 2-decimal logits in the same range. With a window of ±0.005 around three targets (two logits and their difference), chance hits are likely. Without a placebo, E+ can be inflated, and J15's "evidence was in the report and ignored" would then be unsupported.
7. **J14 is very likely uninformative.** k ≤ 7, and E+ is probably near 0 given point 4. The design already allows for this in J15. Keep J14 as a descriptive count and do not let it decide the objection-2 branch.
8. **Wrapper hygiene.**
   - `cmd_analyse` hard-codes `out["prereg"]` to the L0 prereg path, so the wrapper must override it.
   - `named` is built from the submission's probes sorted by position, not indexed by probe id. A Luna submission with a missing probe would misalign it. Assert `len(sub.probes) == n` in the build.
   - The design says this run is the shared Luna L0 for C6 and C7. It must be the **only** sender of those calls.

### Could it weaken existing claims?

The risk is low.
- A genuine Reversal (κ ≥ 0.40 or false credit < 0.50) is unlikely, at about 10%. With 7 passes, κ is noise. Most outcomes either replicate Claim 2 or sharpen it to "omissions".
- The realistic risk is in the **flag script**, not in the judge. If the committed script finds fewer than 7 refuted-then-submitted [decoy] answers (the dT band 0.15-0.30 is "ambiguous"), the body's "7 of 18" in §5.3, Table 4 and App. G has to fall. That is an honest correction of a claim currently tagged "[README count, no committed script]", and it is still better done before submission than by a reviewer.

### Is it what a reviewer asked for?

Only indirectly.
- RANK_V4's new-run requests are fresh or rank-6 items with Terra and Luna, a judge with the exact-query log (C6), and a forced-allocation arm. C8 is none of these.
- It does answer the "one judge, one population; omissions rest mostly on Haiku" objection, which App. I itself concedes.
- It answers the CFP sentence "so that a reported gap between two systems can be attributed to the systems" with the study's cleanest gap. That framing is its main value for this audience (Zhou, Zhu, Rish).

### Required changes (in the prereg, before any paid call)

1. **Decouple the flag script.** Run `luna_decoy_flag.py` first and commit it. Its count goes into the paper whatever happens to the judge calls; it is the $0 rigor fix.
2. **Add a same-day noise floor.**
   - Re-send L0's 24 Terra Open-8 calls, byte-identical (`calls.jsonl` rows, about $0.22), **interleaved in a seeded random order with the 60 Luna calls**.
   - G1 and G2 primary use the same-day Terra verdicts, which nobody has seen; the 12 Nov verdicts are a sensitivity check.
   - Report test-retest agreement and κ on the 96 Terra slots, and the number of Terra hard-slot flips. This gives the paper its first reliability number for the judge, distinct from validity: the CFP's "reliability vs validity" topic.
3. **Print the known bounds in §4**, as C19 does: a ∈ [6, 12], the b needed at each a, and the L0-rate expectation (Δ_judge ≈ 0.1-0.3). Frame G1 as **system-level validity**, which κ cannot show: a judge can be useless per run and still order systems correctly, and that is what a leaderboard needs.
4. **Replace the "Fisher p ≥ 0.05" companion.** Absence of significance is not evidence that the gap is gone. Report instead Δ_judge with its stratified bootstrap interval, plus a power statement: the runs per arm needed to detect the certified Δ at 80% power under judge-implied rates, against the certified rates. This matches the workshop's "power and minimum detectable effect" topic and is pure arithmetic.
5. **Error types.**
   - CC = `decoy` + `other_commission` only. `partial` is reported as its own row and grouped with omissions in a sensitivity line.
   - Rename "fluency-driven" to "credulous across error types".
   - J3-L keeps the L0 split, so it stays comparable with 41/44 vs 12/24.
6. **Report-length gate (pre-stated).**
   - Report `report_chars` and `n_messages` medians for Luna and for the same-day Terra calls, the number of empty reports, and judge credit by length tercile within Luna.
   - If Luna's median `report_chars` is below one third of Terra's, or at least 25% of Luna reports are empty, the text says "the judge graded near-bare answers" and the objection-2 decision is reported as **not identifiable**.
7. **E+ placebo.** Compute the same numeric match against the logits of a non-[decoy] isolating pair in the same run (or, if there is none, the [decoy] pair of another run on the same item). Report E+ only together with its placebo rate. "Evidence present and ignored" is claimed only if E+ is clearly above the placebo; strict E+ also requires the match to sit in the message that names the [decoy].
8. **Body placement.** If C19 runs, there is no Table 2b: Luna becomes C19's 13th and 14th system, and the Terra-Luna pair gets one sentence and one bolded row. If C19 does not run, use Table 2b with the trap rows only (2 rows) and move the two-part rows to App. H. Either way, carry out the word cuts listed in §7.
9. **Hygiene.** Patch `prereg` in `judge.json`, assert probe alignment, and act as the sole sender of the Luna L0 calls. Set the budget guard to $1.50 for 84 calls; the expected spend is about $0.80.

### Realistic expected score gain

- **About +0.15** on the 6.8 mean, within a range of +0.05 to +0.3.
- Most of that comes from two cheap pieces:
  - the committed flag script, which removes a "[README count, no committed script]" tag reviewers can attack;
  - the test-retest noise floor, a reliability number.
- G1 itself adds little on top of C19. Alone, it is a vivid but predictable illustration.
- The upper end needs C19 to run with Luna, so that the paper can state "τ = X across 13-14 systems, and the cleanest within-harness gap shrinks from 0.86 to Δ_t".
- If C19 does not run, G1 is the only system-level measurement in the paper and is worth about +0.2 on its own.
