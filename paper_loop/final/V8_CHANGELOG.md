# V8 changelog (second pass: writing quality)

File revised in place: `final/PAPER_V8.md`. No number was changed or added beyond values already in the sources, and no claim was strengthened. The one value newly written into the text is the 196-run all-slot agreement in Table E5, 0.76. It comes from `gpuplan_b_reconcile.json` (`report_judge.runs_196_reconciled.J4_all_slots.agreement` = 0.758). Run-bootstrap cells newly filled in Tables 1 and E1 come from `gpuplan_a_intervals.json`.

## Lengths (measured with `wc -w`)

| part | before | after | limit |
|---|---|---|---|
| Abstract | 189 | 190 | ≤ 190 |
| Body, "## 1" to "## References", including tables | 4,699 | 4,728 | about 4,300; hard cap 4,800 |
| Body, table rows excluded | 4,095 | 4,227 | — |
| Conclusion | 127 | 118 | < 120 |
| Exhibits in the body | 3 tables, 2 figures, 1 box | 3 tables, 2 figures, 1 box | ≤ 3, 2, ≤ 1 |
| Table 3 rows | 11 | 8 | ≤ 11 |

The body with tables is under the cap but above the "about 4,300" target. Without table rows it is 4,227.

## 1. V8_check_numbers.md

- **§1 #1** (FIGURES_V8 caption says "held-out"): not my file, so not edited. The paper's own Figure 2 caption says "shipped", which is correct. FIGURES_V8.md l.125 still needs the change.
- **§1 #2 and #3** (App M): "appear once" is rewritten. The body now has the 214-run values once, in note a of Table 3; the appendix gives them beside the 196-run values in Tables E5 and N1 and Appendices E and J. The unreconciled outcome counts (7/8 vs 6/8; 11/15 vs 11/15) are deleted. The sentence "We report no result on the variant" is kept, so the paragraph no longer contradicts itself.
- **§1 #4** (E5): the all-slot agreement cell now reads 0.76 [0.765], and the "—: not computed" note is gone.
- **§1 #5** (E1): run intervals are filled in for set A transcript + key [1.00, 1.00], Luna's key levels [1.00, 1.00], Luna's script rows [−0.24, −0.06] / [−0.42, −0.07] / [0.00, 0.00] and main-study V3 [0.27, 0.61]. A note gives the 7 undefined run draws. Blank cells are explained: report + key has only an item bootstrap.
- **§1 #6** (Table 1): the transcript + key run interval reads [1.00, 1.00]. Only report + key keeps "—".
- **§1 #7** (Table 3): "≤ 0.26" becomes "at most 0.26".
- **§1 #8** (Table 3 item counts): the n column is now "runs (items)". The held-out judge row reads "27 (2 held-out + 1 shipped)". The held-out isolation gap moved to §5 as "(0.63, two items)", stated as outside every pre-set band.
- **§1 #9** (M1 dates): the four-query arm and the held-out traps are dated Nov 13.
- **§1 #10** (E2): κ among named answers filled in for report + key (0.67 on set A, 0.89 on Luna's set).
- **§2 #1-#3**: the key claim is scoped to "on the two run sets tested". §1 reads "lacks information more than reading skill". The conclusion says "grades almost perfectly" only for key + log or transcript. "No judge model or prompt" becomes "none of three judge models, under either of two prompts" in §1 and Table 3, and the §4.2 lead says "No judge we tried".
- **§2 #4**: "leaves the ranking unchanged" is gone; the text now says "moves only the threshold".
- **§2 #5**: "beats" is gone; §4.1 says the placebo log "scores above … intervals overlap".
- **§2 #6**: the §4.3 lead now opens "On set A, …".
- **§2 #7**: Table 3 note a adds "a sixth keyed base, on the same 18 runs, fell inside the band and is not reported". This adds no number. App E hypotheses and the N1 C6c row now say the same.
- **§2 #8**: Table 3 note d pairs 0.52 with "blaming 23 of 87 passes".
- **§2 #9**: the text now reads "eight exact queries per episode" (and "8 per episode, shared by its four probes" in §2).
- **§2 #10** (optional, abstract populations): not done, for word budget. 196 is attached to the grade κ.
- **§2 #11**: note a says the 274-run judge-model comparison includes the 18 runs.
- **§4 #1, #2, #3-#6**: App E Robustness (C17), App J and N1 J1, J2, J3 and C17 R2 now lead with the 196-run values, with 214 in brackets.
- **§4 #7**: PPI is marked "(the registered population)".
- **§3**: harder-variant outcome counts now appear only in footnote a of Table 3. The 214-run population values stay as secondary values in the appendix, as the blueprint plans.

## 2. V8_check_compliance.md fixes A-S

| fix | status |
|---|---|
| A, B, C, D (abstract) | done: "a few exact queries"; "within-run AUROC … under two prompts"; "Even with the full transcript … on any set"; "(a positive control)" |
| E (re-send noise beside the ladder step) | done: §4.1 "from 9 to 7, within re-send noise (§3)" |
| F (asymmetry; all-probe κ) | done: §4.3 has 3 of 17 against 17 of 26, and all-probe κ 0.25 (script) against 0.32 (transcript judge) |
| G (circular conclusion clause) | done, rewritten without new numbers |
| H ("a weaker agent") | done in contribution 1 |
| I (Table 3 item counts) | done (see §1 #8) |
| J (App M) | done |
| K (App F "near zero") | done: "V1 still credits no commission (0/17, 0/15, 0/6)" |
| L, M (residual period signals) | done: "no reported run uses it"; "all reported … runs" (twice) |
| N (paired tests) | done in Limitations, Items |
| O (optional) | partly: Limitations, Task adds that a trap pass certifies only the part of the effect the SAE can reach; the midpoint tell is not added |
| P (band script into §5) | done: §5 has one sentence, and the result moved there from Table 3 |
| Q ("shrink or reverse") | done |
| R (repeated "same six items") | done: stated once, in Run sets |
| S (Figure 2b label "SAE tools") | caption only: "'SAE tools': with the proxy". The figure was not regenerated, since it is not a file I was asked to write |

## 3. V8_check_coldread.md

- **2a, title ambiguity:** "Right Ones" becomes "Correct 'Nothing Found' Answers" in the title and the §4.2 heading.
- **2b, "no report":** now "shown only a final answer" (abstract) and "a scripted final answer with no messages" (§4.2).
- **2c, script purpose:** the paragraph now opens with "asks what the log could support at best", and "is not a grader" moved into §3. The unit names are reduced to two, "grader-side" and "agent-visible"; "contract's unit" is dropped.
- **2d, "strict" and "ceiling":** the rows are now "log-reading script" and "script, abstaining variant". The variant is defined in §3, and *settles* is defined. A Table 1 note says abstentions count as not credited, so its κ rewards rejecting unsettled `none` answers. The appendix map and Table F1 give "abstaining (ceiling)".
- **2e, trivial rule:** §3 Statistics now explains that hard-probe κ favours readers that reject `none`, which is why balanced accuracy and all-probe κ are reported. The Figure 1 caption gives the rule's hard-probe and all-probe values with the reason. §4.3 adds the all-probe comparison.
- **2f, sceptical rubric:** now "rejects almost every `none`, right or wrong".
- **2g, held-out sentence in "What we find":** moved into contribution 1 and §5.
- **2h, κ 0.34 vs 0.39:** 0.34 is removed from the body. The body now quotes only the three-send 0.39 and the two-send counts 9 vs 7.
- **2i, "shipped anchor":** now "three shipped-trap reference runs".
- **2j, episode contents:** §2 now says what an episode holds (three planted probes and one null) and what the shipped items are (three trap and three two-part episodes).
- **2k, denominators:** set A's 26 missed and 17 wrong cues are defined once in Run sets. The 196 runs are named as "set A and the main study". The body no longer uses "reconciled".
- **§3, terms:**
  - "keyless", "placebo log" (now at first use), "settles", "candidate" and "generated bank" are defined.
  - "Clean edit" becomes "an edit isolating that property".
  - "Reads between" becomes "measured effect falls in the contract's open gap".
  - "Hard slots" and "SAE tools" are glossed in the captions.
  - "Partly readable" is rewritten.
  - The AUROC is described as a comparison of the judge's confidence in two `none` answers within a run.
  - Model names are given in full once ("Terra and Luna below").
- **§4, sentences read twice:** all 12 are rewritten. The 0.60-0.90 band now gives its reason: we predicted the key would help but leave errors.
- **§5, figures and tables:**
  - The Figure 1 caption explains why the stars sit at the log level, names the main-study star and points to Table 1 for the report level.
  - Table 3 is split into runs (items) columns with one convention for semicolons. It is cut to the 8 judge tests; the agent tests and their statuses are in §5 and Table 2.
  - The Figure 2b graphic itself is unchanged (see fix S).
- **§6, cuts:**
  - "Is this obvious?" is cut from about 180 to about 65 words, with no results repeated.
  - Repeats are reduced to one or two places each: 31/39 now twice, 247→6 once, 0.86→−0.19 in the abstract, §4.5 and Table 3, AUROC in the abstract, §4.2 and Table 3.
  - The status labels drop "registered after Terra's results" from the §3 taxonomy. That label now appears only where it applies (Table 2).
  - The parenthetical wording rule is now one plain sentence.
- **Reviewer flags:** §4.5 notes that the judge model is also the leading agent and shows no sign of self-preference (appendix E5). Model naming is explained.

## 4. Writing-quality rewrite (all sections)

- Every paragraph opens with a topic sentence in bold or a lead clause.
- Body sentences outside tables carry at most two reported quantities. I count "x of y", an estimate with its interval, and a before→after pair each as one quantity; design counts and arm labels (three models; 8 or 64 queries) are not counted. Four dense sentences were split: the abstract's AUROC sentence, the §4.3 credit sentence, the §4.5 gaps and the AUROC sentence.
- The names are now consistent:
  - judge levels: "report", "report + log", "full transcript", "+ key", and "keyless";
  - agents: Terra, Luna, Opus, Sonnet, Haiku;
  - run sets: "set A", "Luna's set", "main study";
  - script: "log-reading script" and "abstaining variant";
  - units: "grader-side" and "agent-visible".
- Every caption leads with its takeaway.
- The introduction ends with three contributions (it had four) and "Figure 1 shows the main result".
- The conclusion is 118 words and adds no new numbers.

## 5. Hard rules (grep-checked after the edit)

- There is no October material, no "oct", no Appendix P, no "13-17" and no date after 14 Nov.
- There are no names, emails, URLs or branch names.
- No experiment codes appear in lines 1-170.
- No probe or episode id appears beside a cue property; trap roles are written only as [main] and [decoy].
- No placeholders.
- The reference list is unchanged, and every entry is still cited in the body.
