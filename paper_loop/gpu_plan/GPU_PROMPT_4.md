# Prompt to paste to the GPU agent (round 4, last: answers the "set by the design" objection)

**Context.** Fetch `claude/nifty-wozniak-vunb6z` and read `paper_loop/final/REVIEW_V8.md`, especially §4 items 1–2 and
5, and §6. The deadline for new data is **17 Nov 23:59 UTC**. Commit to `claude/serene-fermi-pog4k7`.

## D. Decidable-slot analysis ($0; do this first)

**The reviewers' objection.** The omission result is fixed by the design. With 8 queries the log almost never settles a
`none`, and the judge has no abstain option. So the result measures the judge's threshold, not its reading.

**The test.** Restrict to the hard-probe slots that the agent's own exact-query log can decide.
- A slot is decidable if the pre-registered strict keyless rule V1, or the ceiling rule V3, reaches a verdict from the
  log alone: a named cue confirmed or refuted, or a `none` confirmed by having every aligned candidate isolated.
- On those slots, report the LLM judge's accuracy against the executed grade at each keyless level (report, log,
  transcript), with κ, balanced accuracy and false credit split into commissions and omissions.
- Report it for set A, Luna and the main study.
- Report the same metrics on the undecidable slots for contrast.

**Statistics.**
- For each item, give the decidable-slot count and the judge's correct count.
- Run exact paired tests over items and runs: the judge on decidable slots vs the script's verdict, and the judge on
  decidable vs undecidable slots.
- Give run-level and item-level intervals.

**Freeze first.** Write `gpuplan/d/PREREG_D.md` with the decidability rule and the two readings written in advance,
hash it, and commit it before computing.
- "If the judge is also near chance on decidable slots, its failure is not only the design: it does not read
  decidable evidence."
- "If it is accurate on decidable slots, the failure is the absence of decidable evidence."

Label everything post hoc (the definition of decidable comes after the results).

## E. Per-item counts and paired tests for the ladder ($0)

- For every ladder level and set, give per-item correct and credited counts.
- Run exact paired tests (sign or permutation over items, McNemar over runs) for these steps:
  - report vs log;
  - log vs transcript;
  - transcript vs transcript + key;
  - script vs the transcript-level judge.
- Move balanced accuracy and all-slot κ into one body-ready table.

## F. Optional: abstaining, candidate-aware judge (≤ $8 OpenAI; run only after D and E, and only if it finishes by 17 Nov 23:59)

**The judge.** The frozen Terra judge at the log and transcript levels on set A (130 runs), with two changes:
1. **Three-way verdict:** pass, fail or "cannot tell".
2. **Candidate-aware instruction:** "credit `none` only if every listed candidate was isolated in a clean test; credit a
   named cue only if a clean test of it is in the log". Give it the probe's 8 aligned candidates; never the answer.

**Report:**
- coverage, the share of slots not marked "cannot tell";
- κ and false credit on the covered slots;
- how often it abstains on wrong vs right `none` answers.

**Process.** Pre-register and hash first, and run a dry run first.

**Pre-stated readings:**
- If it abstains on most `none` answers and is accurate where it commits, "a judge that may abstain and is told what
  to check behaves like the script".
- If it still credits wrong `none` answers, "instructions do not fix it".

## Rules
- Never commit a probe or episode id next to its cue property. Use [main]/[decoy]. Run the leak scan before every
  commit.
- Never edit `scripts/judge_vs_grade.py` or `scripts/blackbox_schedule.py`.
- Where this prompt disagrees with the box, the box wins. Log the deviation.

## Report
Add a "Round 4" section to `RESULTS_FOR_PAPER.md` with plain sentences the paper can use. Push, and tell me the commit
hash.
