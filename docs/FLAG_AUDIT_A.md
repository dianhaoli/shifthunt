# Flag audit A: the D36 failure flags and the follow-up flag definitions

Independent audit of the mechanical failure flags, written without access to the parallel audit B.

**What was audited:**
- `scripts/failure_flags.py`, sha256 `9bc59ff2…` (checked; not edited);
- `tests/test_failure_flags.py`;
- `results/blackbox_1112/DECISIONS.md` D36;
- `results/blackbox_1112/flags/{README.md, FREEZE.md, flags.json}`;
- `results/blackbox_1112/followup/DEFINITIONS.md` §1–§3 and `DEFINITIONS_ADDENDUM_1.md`;
- `scripts/s3_coder.py`, `shifthunt/detectors.py`, `shifthunt/freetext.py`;
- for the grading rule, `shifthunt/grader.py`, `shifthunt/reward.py`, `shifthunt/toolserver.py` and `prompt.md`.

**What was not used:** no bank, raw run, transcript or paid call.

**Fixtures:**
- 24 synthetic slots in `tests/flag_audit_a/`, in the fresh-run input format the code reads.
- The expectations are in `tests/flag_audit_a/expected.json`, whose schema is in that folder's README.
- They were written by hand from the definitions before any flag code ran on the fixtures, and were not edited
  afterwards.
- `tests/flag_audit_a/test_audit_a.py` runs the frozen code on them.
- Result: 382 passed, 216 skipped (the hook for a future implementation of the follow-up flags), 10 xfailed
  (strict).
  - 4 of the xfails are code findings: 3 cells of fixture f11a, and F3 of f14.
  - 1 is a low-severity replay check.
  - 5 encode the audit's proposed resolutions of definition problems, which the frozen code cannot meet by
    design.

Every other hand-written expectation matched the frozen code exactly, and matched the audit's reference reading
of the follow-up flags (`audit_a_oracle.py`).

## 1. Findings, ranked by severity

| # | severity | type | where | failing input | correct value |
|---|---|---|---|---|---|
| H1 | high (for two-part hard slots) | operational rule wrong for nested cues | `failure_flags.py:254-263` (`covered_columns`); README rule 7 (`flags/README.md:82-86`) | f06a: clean pair on the child `ps_question` (+0.40 topic units, parent on in both texts); the slot claims the parent `postscript` | F1 = 1 under the task's own bar; code 0. F1a: 1, not "not computable" |
| H2 | high (drives "F1 never fires") | definition: no evidence scored 0; free bases excluded | `failure_flags.py:299` (`any()` over an empty effect dict); `:216-226` (pairs only among probe_query texts); D36 (`DECISIONS.md:405-409`) | f04: the agent queries only S-excl and scored its base S with probe_scores | D36 as written: 0. Not computable is the honest label (F1a). Exploratory F1s: 1 |
| M1 | medium | definition: F2 "tested" by a pair on an unrelated property | `failure_flags.py:302-304`; D36 F2 (`DECISIONS.md:410`) | f05c: the only clean pair varies `lowercase`; a case-sensitive `^P\.S\.` cue flips with it | as written: F2 = 0 (code agrees). Proposed: 1 (postscript never varied) |
| M2 | medium | definition: the topic unit is not the prompt's unit | `failure_flags.py:466-471` (`Episode.unit`); D36 (`DECISIONS.md:405`) | the sample gap equals β_topic + Σ_aligned ±β_k, and every main cue is aligned | not fixture-testable: it needs the hidden β_topic. See §1.4 |
| L1 | low | bug: threshold with no float tolerance | `failure_flags.py:299` | f11a: logits 0.51 / 2.01, unit 10; 1.50/10 evaluates to 0.14999999999999997 | F1 = 1 (code 0); combined 1 (code 0); count 1 (code 0) |
| L2 | low | bug: F3 minutes_left not at submission | `failure_flags.py:1283-1290`; README rule 11 (`:96-98`) | f14: a free `budget` call 600 s after the accepted submit rewrites budget.json | minutes_left 40.0 (code 30.0) |
| L3 | low | bug: the sample check runs on the raw text, the flags on the normalised text | `failure_flags.py:1243` | a sample note sent with a trailing `\n` and a wrong-class logit (-5.0 for a +5.0 note) | checked and set missing; code: not checked |
| L4 | low (disclosed) | definition: F2n is forced by counting | `failure_flags.py:307-310` | any `none` slot with at most 8 texts and 8 aligned properties | already in README caveats; F2n carries no information there |

### H1. Nested cues: a parent regex "covers" the child

**The rule.** README rule 7 counts a property as covered when a submitted regex has max(BA, 1 − BA) ≥ 0.8 for
it on the public corpus, "the task's own bar".

**Why the parent passes it.**
- In the corpus every property is a coin flip, but the generator enforces child ⇒ parent (`freetext.IMPLIES`,
  `_imply`). So `ps_question` is present in about 25% of notes, and `postscript` without it in another 25%.
- The parent regex `(?im)^p\.s\.` therefore matches every child note (recall 1). It also matches 1/3 of the
  non-child notes, so specificity is 2/3.
- BA = 0.833. On the synthetic corpus it is 0.816 (`fixtures/facts.json`). The child counts as covered.

**What the grader does.** On a two-part item's grid, the child is the protected main. The parent is forced on with
it and is a coin otherwise (`sample_grid`). The same regex then has BA 0.75 against the child, so it does not
identify it: the slot fails.

**Effect on F1.** The canonical two-part failure is to name the parent instead of the child. F1 cannot flag it
even when the agent isolated the child cleanly, with the parent on in both texts (f06a: effect +0.40, F1 = 0).

**Inheritance.**
- F1a calls this slot "not computable".
- F4's "covered" (§3) inherits the same error.

**Classification.** D36 does not define "covered"; the corpus rule is an operational choice whose premise fails
for nested properties.

**Fix.**
- Judge a child's coverage on the corpus notes where its parent is on, or use the grader's grid semantics.
- For non-nested properties nothing changes.
- This changes a frozen operational choice, so it is exploratory.

**Real-data impact.** Unknown. It needs a clean child pair on a two-part hard slot, and those are rare under
an 8-query budget.

### H2. F1's zeros mean "no evidence", and the cheapest evidence is excluded

See §2.

### M1. F2 is satisfied by any clean pair that moves the regex

**The rule.** D36 says a claim is untested if "the submitted regex's match status never differs within a clean
pair". The code checks this over all clean pairs, whatever property the pair varies.

**Example (f05c).**
- The texts are a note with a P.S. and the same note lowercased, which is a clean pair on `lowercase`. The
  detectors are case-insensitive.
- The cue `^P\.S\.` has no `(?i)`. It matches the mixed-case text only, so its status differs within that pair
  and F2 = 0.
- `postscript` was never varied. The same happens with `!` against a `signoff_excl` pair.
- T-RULE's F2 part inherits this.

**Proposed resolution.** A cue is tested if some clean pair varies a property the cue covers (D36 coverage). With
it, f05c gives F2 = 1. This regex covers nothing, because it misses the lowercased half of the corpus, and so it
also fails the grader. The resolution changes D36's F2, so it is exploratory.

**Letter case otherwise behaves consistently.**
- The detectors ignore case, except the `lowercase` property itself.
- Regexes are run as written, as the grader does.
- So a case-sensitive cue is uncovered on a corpus that is 50% lowercase (BA about 0.75), and F1 then flags its
  property (f05a: F1 = 1).
- The `(?i)` version is covered (f05b: F1 = 0).

### M2. The topic unit includes the cue effects

**The definition.** D36's unit is the sample class-mean gap.

**What that gap measures.** In the sample, every aligned property, including every main cue, equals the label or
its complement (`prompt.md:17-20`). So the gap is β_topic + Σ_aligned s_k β_k. The prompt's 0.15 / 0.30 contract
is in units of β_topic (`prompt.md:10-15`).

**Size of the bias.**
- With one main cue at 0.5 β_topic, aligned with the same sign, the unit is 1.5 β_topic. F1's 0.15 bar then
  sits at 0.225 in the prompt's units, so band effects are missed.
- With the opposite sign, the unit is 0.5 β_topic and effects are doubled, so non-cues at 0.08 would fire.
- The direction differs by probe, and the logs cannot show it.

**Classification and resolution.**
- This is a definition problem, as written in D36.
- The audit expects it to bias F1 down on probes whose main pushes toward the label-1 class.
- A sensitivity row with the bank's topic coefficient (GPU or bank data, exploratory) would bound it.

### L1–L3. Code bugs

**L1: no tolerance on F1's threshold.**
- The coverage bar got a 1e-9 margin in change 4 (`:261`); F1's threshold did not (`:299`).
- About 12% of 2-decimal logit pairs exactly 0.15 units apart fall below the bar.
- Impact on real data is nil in practice: the unit comes from the stored encodings and is never a round
  number. It is still a fix that does not change the definition.

**L2: F3's minutes_left is read at the wrong time.**
- budget.json is rewritten at every call (`toolserver.py:492-493`), including free calls after the accepted
  submit. "Minutes left at submission" (D36) is therefore understated whenever the agent calls `budget` or `help`
  after submitting.
- The counters (queries, calls, forward) are frozen after the submit, so they are right.
- Fix: minutes_left = budget.json remaining + (t of the last log record − t of the accepted submit) / 60. After
  the submit, no charged call adds compute time.

**L3: the sample check misses a normalised match.**
- `check_sample_logits` compares the raw recovered text with the sample note. The flags code the normalised
  text.
- A sample note sent with a trailing newline is coded as that note, but its logit is never checked.
- Fix: compare `S3.normalise(t)`.

### Behaviour checked and found consistent with the definitions

- **Multi-property flips (f02).**
  - They are not clean pairs, so F1 = 0, F1a is not computable and F2 = 1.
  - They are loose pairs, so F1a-loose = 1 by least squares, from the exact fit 2.0·excl + 0.5·hash.
  - T-F2 = 1 but T-F2L = 0.
- **Sample note queried verbatim (f03).**
  - It is counted, with the logit returned to the agent: fulltext 5.04, not the stored 5.00.
  - The effect is 0.152, so F1 = 1. With the stored logit it would be 0.148.
  - The replay path keeps the recovered logit and only checks it within 0.15
    (`test_replay_sample_note_counts_with_its_recovered_logit`).
- **Topic.**
  - Unknown topics enter no pair (f07a), and neither do cross-topic one-property contrasts (f07b).
  - A zero topic unit makes F1 missing and the combined flag missing (f07c).
- **`none` slots.**
  - F2n = 0 is reachable when the aligned set is small enough to be varied with the texts at hand (f08a).
  - A `none` slot with an uncovered 0.30 clean effect gets F1 = 1 (f08b).
- **Other cases.** An untested second cue gives F2 = 1 (f09). A probe never queried gives F2 = 1 and F1 = 0
  (f12). An unrecovered call makes every flag missing (f13).

## 2. Why F1 never fires on the main study

**Verdict.** It is not a code bug. Under D36 as written, the evidence is genuinely absent. That absence comes from
three things:
- the budget;
- D36 excluding the cheapest clean contrast;
- the fact that F1 = 1 describes a behaviour the contract makes rare.

The code returns 0, not "not computable", when no evidence exists. H1, M2 and L1 each push further toward 0,
but none of them is needed to explain the zeros.

**Evidence that the code path works.**
- The same `slot_flags`, coverage and pair code fires F1 on synthetic slots (f03, f05a, f08b, and f11a once the
  threshold is fixed).
- It fires on real fresh runs that bypass the replay entirely: Open-8 2/144, BB-8 1/144, BB-64 11/144.
- Main study: 0/233 with known logits.
- Main against Open-8, the same 8-query budget: Fisher p = 0.145, compatible with a single low rate.
- Open-8 against BB-64: p = 0.020. F1 tracks the number of texts, not the recovery method.

**Candidate causes ruled out.**
- **Topic rule.** Unknown topics are 4 of 469 main-study texts.
- **Normalisation.** It only removes `\r` and trailing newlines.
- **Missing data.** 23 main-study slots are F1-missing (1 failure). That is not where zeros come from.
- **Coverage over-crediting.** Outside nested cues, coin-flip independence in the corpus means a regex can
  reach BA ≥ 0.8 only for the property it tracks.

**Budget arithmetic.**
- The main study logged 499 probe_query texts over 64 runs (flags.json recovery coverage): about 1.95 texts per
  probe slot.
- Clean pairs among m texts vary at most m − 1 distinct properties. This is the README's own spanning-tree
  argument, and it is correct. A slot with 2 texts can therefore measure one property cleanly at most.
- F2 = 0 on 44 named main-study slots shows where such single measurements went: to the claimed, covered
  property.
- F1 is computable only if the agent spends texts on a property it then does not claim.

**What F1 = 1 means under the contract.**
- Every non-main property is at most 0.15 β_topic.
- So on an ordinary probe, F1 = 1 essentially requires a clean measurement of an uncovered main cue, at
  ≥ 0.30, that the agent then ignored. That is rare by construction.
- The LLM coding's "pointer in own output" (17 of 19) was a looser construct: SAE or proxy evidence counts there,
  not only true-logit clean pairs.

**Free bases.**
- probe_scores returns a sample note's true logit without spending probe_query budget. The efficient design is
  therefore to score the note, edit one property, and query only the edit.
- D36 counts pairs "of the agent's texts", so that contrast enters no pair (f04): F1 = 0, F2 = 1, T-F2 = 1.
- Only 28 of the 469 recovered main-study texts are verbatim sample notes (`main_sample_logit_checked`), so agents
  rarely spend queries on bases.
- How many of their edits are one-property edits of sample notes they scored cannot be read from the tracked
  aggregates.
- **Decisive check (private data, answer-free):** per main-study slot, count the agent texts that are one
  detector property and the same topic away from a public sample note the agent scored. log.jsonl records
  probe_scores ids, and an omitted `ids` means all notes.

**Proposed fixes.**
1. **Report computability (F1a).** It is already frozen in DEFINITIONS §1. It changes the labels, not the
   values: a 0 with no uncovered clean pair becomes "not computable". This is not a change of D36's values. Its
   rule was written after F1 = 0 was known, which DEFINITIONS discloses.
2. **F1s (exploratory: it changes D36's text set).** Add, as pair members, the public sample notes the agent
   scored with probe_scores, with the stored logits (the ones the agent saw). Apply the same to F2 and T-F2. On
   f04 this gives F1s = 1.
3. **Nested coverage (H1).** It changes README rule 7, so it is exploratory.
4. **Float tolerance (L1).** An implementation fix, with no expected effect on real data.

None of these is likely to make F1 separate failing from passing main-study slots. The likely outcome of fix 1 is
a small count of computable slots, which should be reported as such.

## 3. Definition ambiguities and proposed resolutions

The resolutions below are used by `audit_a_oracle.py` and by `expected.json`. "alt" in the JSON gives the other
reading where it changes a fixture.

### F1a and F1a-loose (DEFINITIONS §1)

1. **Partial logits.** Computability needs "a clean pair with both logits known". D36 sets the whole slot's F1
   missing if any logit is missing.
   - Resolution: F1a uses only known-logit pairs and ignores the others.
   - It is missing only if the texts or the topic unit are missing.
   - So F1a can differ from D36's F1 on the 10 main-study `texts_ok_logits_missing` slots. That is where the
     "re-reading" of the D36 rule can move at all, since on computable slots F1a = F1, which is 0 everywhere in
     the main study.
2. **F1a-loose: which regression.**
   - Resolution: one OLS with an intercept per topic group of at least 3 texts, on the columns that vary in that
     group.
   - A property is estimable iff rank([1, O, k]) > rank([1, O]), exact, as in s3_coder (b). Its identified
     coefficient does not depend on how collinear the other columns are.
   - Its effect is the mean of its estimates over the groups where it is estimable.
   - "Computable" means at least one uncovered property is estimable.
   - The intercept must be in the rank check. Without it, a column that is the complement of another (k = 1 − o)
     passes wrongly.
3. **Threshold tolerance.** |x| ≥ 0.15 − 1e-9, as for coverage. Least squares returns 1.4999… just as easily
   (f11a).
4. **Combined flag without F2n.** It says both "slots answered with cues only" and "on none slots, defined only
   through F1a".
   - Resolution: include `none` slots with F1a, a not-computable F1a counting as 0 and marked (as in the with-F2n
     version).
   - Also report the computable-only row, because otherwise every `none` slot without evidence is a structural
     0.

### T-F2, T-D, T-RULE (DEFINITIONS §2)

5. **Several mains.** T-F2 = 1 if any main is never varied, so all must be isolated, as in s3_coder.
6. **Nested main.** Nothing extra is needed. Under the detectors, the child implies the parent, so a clean pair on
   the child always has the parent on (f06a, f06c), and a child switched on from a note with no P.S. moves both:
   loose only (f06b).
   - The child can never be varied "with the parent off".
   - A decoy that is the main's parent is varied cleanly only with the child off.
7. **T-RULE on a `none` slot.**
   - Resolution: its F2 part is 0, because `none` claims nothing. The rule then predicts a pass for a failing
     `none` (f08b).
   - Report how often this happens. Do not add F2n, which is forced.
8. **T-RULE's other blind spots, inherited from its components.**
   - M1: an unrelated pair "tests" a claim.
   - Regex quality is not looked at: f05a fails on letter case with T-RULE = 0.
   - A tested false claim is not caught: f10b fails with T-RULE = 0.

   These are part of the definition. They should be listed beside the 2×2 tables, because they bound the rule's
   agreement with the outcome.
9. **Loose F2 part.** "Loose pair" is defined relative to a property, and a regex is not one.
   - Resolution: the regex is tested if its match differs between two texts of the same known topic whose
     detector rows differ.
   - Two texts with identical rows but different regex matches (for example two sign-off words) do not count.
10. **Missing.** Logits are not needed.
    - Fresh runs: any fulltext problem makes the slot missing.
    - Replay: follow D36's `texts_ok`. A `sample_logit_mismatch` probe is then missing although its texts may be
      fine. Report how many slots this affects; in the main study it is 2 slots, both non-hard.
11. **Duplicates and unknown topics.** Duplicates pair with nothing. Texts of unknown topic enter no clean or
    loose pair (f07a), and neither do cross-topic pairs (f07b).

### F4 (DEFINITIONS §3)

12. **Topic unit of ΔP.** "In topic units" does not say whose.
    - Resolution: ΔP in the proxy's own sample class-mean gap, computed from the stored sample encodings with
      the same p_j(x). An agent reading the proxy would normalise by the proxy's gap. With the true unit, a
      globally shrunk proxy (r < 1, the G tell) would read "non-cue" for everything.
    - f10c shows the choice matters. With the proxy unit 8, ΔP is 0.35 and F4 = 1. With the true unit 10, ΔP is
      0.28: band, no contradiction, so F4 is not applicable.
    - Report both.
13. **Availability through sample-note ids.** latent_means with probe ids gives the agent f(x) of a sample note
    without sending its text.
    - As written, only free-text calls count.
    - Resolution: count them as written, and give a sensitivity row in which id-based encodings count too.
14. **Coverage.** F4 uses D36 coverage, so H1's nested over-coverage applies here as well.
15. **Missing versus not applicable.** If a text in a clean pair has unknown SAE availability (main-study SAE
    texts not recovered), F4 is missing, not "not applicable". "Not applicable" is reserved for slots whose known
    record has no both-reading pair or no contradiction.
16. **ΔT over both-reading pairs only.** As written, ΔT is the mean over the both-reading pairs, not over all of
    the property's clean pairs. Keep it so: both readings then rest on the same contrasts.

## 4. Fixture table: expected (written before running) against the frozen code

- For D36 flags a cell shows the expected value. A disagreement shows "(code …)" and **≠**.
- The follow-up flags have no code. Their cells are the expected values, and `audit_a_oracle.py` reproduces every
  one of them.
- Abbreviations: nc = not computable, n/a = not applicable, miss = missing.
- F3's other fields (queries unused, calls and forward left) matched in every fixture.

| fixture | F1 | F2 | F2n | comb | count | F3 min | F1a | F1a-L | T-F2 / T-D / T-RULE | T-F2L / T-DL / T-RULEL | F4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f01_control | 0 | 0 | n/a | 0 | 0 | 40.0 | 0 | 0 | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f02_multi_property_flip | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | 1 | 1 / 1 / 1 | 0 / 0 / 0 | n/a |
| f03_sample_note_queried | 1 | 1 | n/a | 1 | 2 | 40.0 | 1 | nc | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f04_sample_note_scored_only | 0 (F1s: 1) | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 1 / 1 / 1 | 1 / 1 / 1 | n/a |
| f05a_case_sensitive_regex | 1 | 0 | n/a | 1 | 1 | 40.0 | 1 | 1 | 0 / 0 / 0 | 0 / 0 / 0 | n/a |
| f05b_case_insensitive_regex | 0 | 0 | n/a | 0 | 0 | 40.0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 | n/a |
| f05c_regex_moves_on_other_property | 0 | 0 (proposed: 1) | n/a | 0 (proposed: 1) | 0 (1) | 40.0 | 0 | nc | 1 / 0 / 1 | 1 / 0 / 1 | n/a |
| f06a_nested_parent_named | 0 (proposed: 1) | 1 | n/a | 1 | 1 (2) | 40.0 | nc (proposed: 1) | nc | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f06b_nested_child_parent_off | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 1 / 1 / 1 | 0 / 0 / 0 | n/a |
| f06c_nested_child_parent_on | 0 | 0 | n/a | 0 | 0 | 40.0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 | n/a |
| f07a_topic_unknown | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 1 / 1 / 1 | 1 / 1 / 1 | n/a |
| f07b_cross_topic | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 1 / 1 / 1 | 1 / 1 / 1 | n/a |
| f07c_zero_topic_unit | miss | 0 | n/a | miss | miss | 40.0 | miss | miss | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f08a_none_null_probe | 0 | n/a | 0 | 0 | 0 | 40.0 | 0 | 0 | n/a (not a trap) | n/a | n/a |
| f08b_none_on_trap | 1 | n/a | 0 | 1 | 1 | 40.0 | 1 | 1 | 0 / 0 / 0 | 0 / 0 / 0 | n/a |
| f09_untested_claim | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f10a_decoy_tested_rejected | 0 | 0 | n/a | 0 | 0 | 40.0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 |
| f10b_decoy_claimed_after_contradiction | 0 | 0 | n/a | 0 | 0 | 40.0 | nc | nc | 0 / 0 / 0 | 0 / 0 / 0 | 1 |
| f10c_proxy_unit_choice | 0 | 0 | n/a | 0 | 0 | 40.0 | nc | nc | 1 / 0 / 1 | 1 / 0 / 1 | 1 (true unit: n/a) |
| f11a_threshold_exactly_0_15 | 1 (code 0) **≠** | 0 | n/a | 1 (code 0) **≠** | 1 (code 0) **≠** | 40.0 | 1 | 1 | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f11b_threshold_just_below | 0 | 0 | n/a | 0 | 0 | 40.0 | 0 | 0 | 0 / 1 / 1 | 0 / 1 / 1 | n/a |
| f12_never_queried | 0 | 1 | n/a | 1 | 1 | 40.0 | nc | nc | 1 / 1 / 1 | 1 / 1 / 1 | n/a |
| f13_unrecovered_call | miss | miss | n/a | miss | miss | 40.0 | miss | miss | miss | miss | miss |
| f14_f3_budget_after_submit | 0 | 0 | n/a | 0 | 0 | 40.0 (code 30.0) **≠** | 0 | 0 | 0 / 1 / 1 | 0 / 1 / 1 | n/a |

## 5. Verdict per flag

| flag | verdict |
|---|---|
| F1 | **Definition problem, plus a minor bug.** The code is faithful to D36 and the README. The definition scores "no evidence" as 0, excludes free sample bases, uses a unit that includes the cue effects (M2), and over-credits nested coverage through operational rule 7 (H1). Bug: threshold with no tolerance (L1). |
| F2 | **Sound code; definition problem (M1).** A claim counts as tested by any clean pair that moves the regex, including a pair on letter case or on another property. |
| F2n | **Sound code; definition problem.** It is forced to 1 by counting under the 8-text budgets (disclosed in the README). |
| F3 | **Bug (L2), low.** minutes_left is read at the last budget.json write, not at submission. The counters are right. |
| combined / count | Inherit the above. On `none` hard slots the combined flag restates the outcome (disclosed). |
| F1a | **Sound, once the partial-logit and tolerance readings are fixed (§3, items 1 and 3).** It inherits H1, H2 and M2. |
| F1a-loose | **Ambiguous as written** (which regression, the rank check). The resolution is in §3, item 2. |
| T-F2, T-D | **Sound** with the resolutions in §3 (items 5, 6, 10 and 11). Nested mains need no special case. |
| T-RULE | **Definition problem:** it inherits M1, treats `none` as tested (f08b), and ignores regex quality (f05a) and tested false claims (f10b). |
| T-F2L, T-DL, T-RULEL | **Ambiguous** in the F2 part (§3, item 9); otherwise sound. |
| F4 | **Definition problem:** the unit of ΔP is unspecified and changes values (f10c). Also: availability through ids (§3, item 13), missing versus not applicable (§3, item 15), and H1 through coverage. |

## 6. Files

All files are under `tests/flag_audit_a/`:
- `README.md`: the expected.json schema and the fixture format.
- `expected.json`
- `audit_a_build.py`: the deterministic fixture builder. It checks inputs only.
- `audit_a_oracle.py`: the reference reading of the follow-up flags.
- `test_audit_a.py`
- `fixtures/`: the bank episodes epA and epZ, 24 run directories, and `facts.json`.

Implementations of DEFINITIONS §1–§3 can be tested with `FLAG_AUDIT_A_IMPL=module:function` (see that README).

Nothing outside `docs/FLAG_AUDIT_A.md` and `tests/flag_audit_a/` was written, and nothing was committed.
