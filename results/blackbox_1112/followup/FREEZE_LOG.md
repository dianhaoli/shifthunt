# Freeze log for the follow-up analyses (DECISIONS D37)

| file | sha256 | frozen (UTC) |
|---|---|---|
| results/blackbox_1112/followup/DEFINITIONS.md | `d0e9bbbd861142aa4b42268af9337ff340d9b3876a402441d600e1dc950f2c83` | 2026-11-11T06:12Z |
| results/blackbox_1112/followup/DEFINITIONS_ADDENDUM_1.md | `6ae4d2a2db0b8a426c128538411aad9a9944a96f0a46c15f28b167ea5d1b4ee4` | 2026-11-11T06:55Z |

Code written to implement DEFINITIONS.md is hashed here when it is first run on real data. Every later change
is logged below: what changed, why, and the new hash. A change to a definition marks the affected result
exploratory.

## Changes

### misc (section E items, DEFINITIONS.md §6)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/exp_f_ci.py | `b6dee8698cd967d9669ffb96decfe5ca8a5a557f2bddc5034bce9ec7f84bac40` | 2026-11-11T06:10Z | Exp F rescoring, modes ci and cs |
