# Freeze log for the follow-up analyses (DECISIONS D37)

| file | sha256 | frozen (UTC) |
|---|---|---|
| results/blackbox_1112/followup/DEFINITIONS.md | `d0e9bbbd861142aa4b42268af9337ff340d9b3876a402441d600e1dc950f2c83` | 2026-11-11T06:03Z (commit 920f501; the file's own text says about 06:10Z) |
| results/blackbox_1112/followup/DEFINITIONS_ADDENDUM_1.md | `6ae4d2a2db0b8a426c128538411aad9a9944a96f0a46c15f28b167ea5d1b4ee4` | 2026-11-11T06:13Z (commit 8ad16ea; the file's own text says about 06:55Z) |

Code written to implement DEFINITIONS.md is hashed here when it is first run on real data. Every later change
is logged below: what changed, why, and the new hash. A change to a definition marks the affected result
exploratory.

## Changes

### misc (section E items, DEFINITIONS.md §6)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/exp_f_ci.py | `b6dee8698cd967d9669ffb96decfe5ca8a5a557f2bddc5034bce9ec7f84bac40` | 2026-11-11T06:10Z | Exp F rescoring, modes ci and cs |
| scripts/latent_regrade.py | `0c7b44365fe1520050a4f6e756bf0430049a939fb7f8d6089d45848f402f1004` | 2026-11-11T06:15Z | before first real run |
| scripts/scripted_cheaters.py | `a9b7dba1b8b767e024bd62eff2e6f7323323912c445abf4bdb4b0090578d79c5` | 2026-11-11T06:15Z | before first real run |
| tests/test_followup_misc.py | `b1fa7a2a109389b5209633101a887f2b1eed4f8adf08edd904f10e3805a2c8ba` | 2026-11-11T06:15Z | before first real run |
| scripts/regrade_sweep.py | `f78362af49de4f11eda9015fa25cd79baff013ac0bbc74c383de0b3ba112489b` | 2026-11-11T06:16Z | regrade and tau/k sweep (§6 and §A1 grids) |

- misc, 2026-11-11T06:16Z: scripts/scripted_cheaters.py adds a positive control P0_oracle (true regex per main; oracle or attr16 latents; nulls none). Why: to show the grader can award reward on these episodes, so that the cheaters zero is not a grader artefact. The six policies and their variants are unchanged. New sha256 `1934dcb6bf60cd04c6f8d953d7c57048b3bff3fedcc0382900606e20bab5c429`.

### trapflags (DEFINITIONS.md §1-4, §9 readings 1 and 2)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/followup_trapflags.py | `a253daad9f80aacb8cd7dec17516b060befd04f0af4015602438056f9a4dbd2c` | 2026-11-11T06:16Z | before first real run |
| tests/test_followup_trapflags.py | `a7844ca706c5ea651a76cdd113c9126b292525e482f78d3d2d16c1d4b50c4001` | 2026-11-11T06:16Z | before first real run |

### solvers (DEFINITIONS.md §5 solvers and G, §6 trap seeds, §7; Addendum A2)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/followup_solver_lib.py | `42e12d32f30d4f6fb724426cbce585f07653516e8b66fadf92c38c53ce083be6` | 2026-11-11T06:17Z | brute-force encode (GPU) |
| scripts/followup_bruteforce.py | `9a73d86a47addff9cbf2f854c9a1c0aaf19054e4c1b0be9de10bf8cd0e1b7537` | 2026-11-11T06:17Z | brute-force encode (GPU) |
| tests/test_followup_solvers.py | `53f1688eb3b99518e208c5917b523b92f363afdb9ef887a6f9b54cd109bc2fcc` | 2026-11-11T06:17Z | brute-force encode (GPU) |

- misc, 2026-11-11T06:17Z: scripts/scripted_cheaters.py implementation fix: answer.json oracle_ids are already public ids; the first two runs mapped them through to_public again, so every oracle-latent variant used wrong latents. Found because the P0_oracle control scored reward 0 with oracle latents. Rerun. New sha256 `884d220fe4b025fb7d03e1ab6de8a299980735c8313bc28a84c6741680b35af6`.

### Time correction (main session, 2026-11-11T06:20Z)
The main session wrote several clock times by hand and got them wrong, too late by 7 to 42 minutes. The commit
times are the record:
- DEFINITIONS.md was frozen at 06:03Z (920f501);
- DESIGNS.md was committed at 06:06Z (bc040f4);
- the DECISIONS numbering note at 06:08Z (ff151c9);
- Addendum 1 at 06:13Z (8ad16ea).
The hashed files keep their wrong in-text times, because editing them would change their hashes. The order of
events is unchanged.
