# Pre-registration: C17 R2, the judge's test-retest (before the R2 call batch)

Status: frozen by `PREREG_HASH` here. Design `paper_loop/brainstorm/design_C17.md`, judge half only (plan "if time",
approved 13 Nov). Code `scripts/judge_panel.py` (cell TF2). Labels: [pre-reg C17, descriptive].

- R2: the 214 frozen L0 calls (`results/private_1112/judge/calls.jsonl`) re-sent byte-identical, interleaved with C7's
  Terra K cell in one seeded order. Together with L0 (12 Nov) and C6's L0r (13 Nov, set A = Block 1 + BB-16) this
  gives three replicates on 132 runs and two on the other 82.
- Reported: Fleiss κ over three replicates (all slots and hard slots), share of slots where all three agree, and on
  all 214 runs the L0-vs-R2 raw agreement, PABAK and Cohen κ, next to the certified-vs-judge hard-slot κ (0.002).
  Reading: "reliable but invalid" if replicate κ is well above validity κ; "unreliable and invalid" otherwise.
- §9's "near-noiseless" sentence (about exact readings, not the grader) is not touched.
