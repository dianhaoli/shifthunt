# Notes from the cloud session (branch claude/tender-dijkstra-hrga9p) to the GPU-box session

Messaging between the sessions is refused (cross-device trust), so notes go here.

- 11-11: merged serene-fermi ff151c9 into the cloud branch (c5f0543). In DECISIONS your D37 ("D37g") comes first
  and the cloud's D37–D39 follow.
- The cloud branch is writing **independent re-implementations** of DEFINITIONS.md §5–7 as a cross-check:
  V0/V1/V2 + G, brute-force BB-64, the six cheaters, the τ/k regrade, Exp F case-insensitive rescoring,
  transcript regexes and the non-privileged solver. Please don't import them into your pipeline. Compare outputs once
  both exist.
- **Spec mismatch to note.** The user's 11-11 task asks for the regrade sweep at τ = f × reference,
  f ∈ [0.8, 1.0], no floor, and k ∈ {4, 8}, and for band-tell variants "claim aligned candidates with ratio in
  [0.15, 0.3]" (v1) and "plus those ≥ 0.3" (v2). DEFINITIONS.md §5–6 froze different grids (τ absolute
  0.15–0.60, k 5/10/20/50; V1 = largest band property only). The cloud code computes both, with the user's grid
  labelled exploratory.
- Done on the cloud branch: `scripts/item_level_stats.py` → `stats_items/` (D38), canary (D39).
- Next on the cloud branch: AAAI-27 paper conversion, citation checks, then the flag audit of
  `scripts/failure_flags.py` at e13f7ed. If that file changes, note it here or in FREEZE_LOG.md.
