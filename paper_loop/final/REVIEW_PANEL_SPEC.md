# Review panel spec for V7 onward (frozen before V7 is written)

**Goal.** Avoid overfitting to one simulated rubric. Use reviewers who differ in what they read, how they score and
which model they run on, and keep a held-out panel that sees only the final version.

## Development panel (reused across revisions, so versions stay comparable)
These are the same three blind reviewers and rubric as V4, V5 and V6: stats, agent-eval (Sonnet) and interp.
They are used only to compare versions, never as the target.

## Diverse panel (new; one review each per version)

| # | reviewer | how they read | rubric | model |
|---|---|---|---|---|
| D1 | Busy workshop reviewer | 20 minutes: abstract, intro, figures, conclusion, then skims | free-form, ending in accept / weak accept / weak reject / reject and a confidence | Sonnet |
| D2 | Conference-style reviewer | full read | soundness / presentation / contribution 1–4, overall 1–10, confidence 1–5 | Opus |
| D3 | Statistician, hostile on inference | full read plus appendix | self-made list of the top 5 threats to validity, each fatal / serious / minor; overall 1–10 | Opus |
| D4 | Outsider (ML, not eval or interp) | full read | "Did I understand the main point? Would I cite it?"; 1–5 for clarity and usefulness | Haiku |
| D5 | Interp practitioner | full read | "Does the task measure what it claims? Is the SAE story right?"; overall 1–10 | Sonnet |
| D6 | Organizer / meta-reviewer | reads the paper and D1–D5 | applies the CFP only: accept for a talk, poster, or reject, and why | Opus |
| D7 | Reviewer with no rubric | full read | invents their own criteria first, then scores; overall 1–10 | Sonnet |

**Rules for every reviewer:**
- Each sees only the paper, its figures and the CFP, in a blind package.
- No calibration anchor is given, apart from D2's conference scale. This tests whether the earlier anchor ("an
  average accepted workshop paper ≈ 6") biased the scores.
- Different reviewers deliberately use different scales. Compare decisions and the issues they raise, not raw
  averages.

## Held-out panel (used once, on the final submission only)
Three more reviewers, with the same diversity rules and fresh personas not used above. They run only on the version
about to be submitted, so no revision is ever made in response to them. Their verdict is the final check.

## What counts as a real issue
- An issue is real if it is raised independently by at least 2 reviewers who use different rubrics.
- An issue raised by only one rubric is noted, but it does not drive a rewrite unless it is a factual error.
