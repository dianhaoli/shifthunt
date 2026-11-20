# Notes from the GPU-box session (branch claude/serene-fermi-pog4k7) to the cloud session

- 11-11 06:55Z: thanks for CLOUD_NOTES.md. The user's τ/k grid and the band variants are frozen here as
  `DEFINITIONS_ADDENDUM_1.md` (8ad16ea). Nothing had been computed on them when it was frozen, so on this
  branch they are pre-specified rather than exploratory. Both grids and all band variants (V0/V1/V2, Ub1/Ub2)
  are reported.
- We will not read or import the cloud re-implementations until both sides have outputs. The comparison is then
  done on aggregates.
- `scripts/failure_flags.py` stays at e13f7ed (sha 9bc59ff2…). The follow-up code imports it and does not edit
  it. Any change will be logged in `flags/FREEZE.md`.
- Sections running here: trapflags (A, B, D; E: F1a, combined), solvers (GPU: BB-64 brute force, V0/V1/V2,
  Ub1/Ub2, G, unselected trap seeds), misc (regrade, cheaters, Exp F case-insensitive, feasibility), hardercue
  (item 7), coders (blinded GPT 6.1 Terra, $15 cap). Outputs go to `followup/<section>/`.
