# C17 R2: the judge's test-retest (pre-registered, descriptive; `PREREG_C17.md`)

The 214 frozen L0 judge calls re-sent byte-identical on 13 Nov (R2, interleaved with C7's TK cell; $2.02; 214/214
parsed). With L0 (12 Nov) and C6's L0r (13 Nov, set A) there are three replicates on 132 runs and two on all 214.
Driver `scripts/judge_panel.py analyse` → `c17.json`. No deviation.

| | runs | slots | agreement | κ |
|---|---|---|---|---|
| three replicates (L0, L0r, R2), all slots | 132 | 528 | all three agree 0.68 | Fleiss 0.44 |
| three replicates, hard slots | 132 | | all three agree 0.60 | Fleiss 0.39 |
| L0 vs R2, all 214 runs | 214 | 856 | 0.84 (PABAK 0.69) | Cohen 0.47 |
| validity reference: certified vs judge, hard slot (J1) | 214 | | | 0.002 |

Reading: the judge agrees with itself moderately (κ 0.39-0.47) and with the certified grade not at all (κ 0.002).
Its verdicts are partly stable but invalid; and on the hard slot, where Claim 2 lives, 40% of hard slots get a different
verdict from at least one of three identical calls.
