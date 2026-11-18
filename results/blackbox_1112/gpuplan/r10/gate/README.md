# P1a gate and same-day control (round 10; PLAN_R10 item 10; check-and-report, D5)

Sends (18 Nov, one day): r10 L0 (Terra) and r10 H0 (Haiku) on the 132 set A runs; the same-day control re-sends the *original frozen* prompts of the same 132 + 132 calls (`CTRL__`). Rule, decided before anything else was read: the reasons that reject a pass for missing latents or too little removal (narrow pattern matches, every one hand-read) must be ≤ 5% of rejected passes, for Terra L0 and for Haiku H0.

| send | prompt | passes | rejected | rejected citing `latent|ablat` | hand-read: rejects for latents/removal | share | credited verdicts citing latents | gate |
|---|---|---|---|---|---|---|---|---|
| Terra L0 | r10 | 309 | 24 | 0 | 0 | 0% | 3/457 | pass |
| Haiku H0 | r10 | 307 | 219 | 2 | 0 | 0% | 4/151 | pass |
| Terra L0, same day | frozen | 309 | 109 | 98 | 98 | 90% | 13/377 | control (frozen prompt) |
| Haiku H0, same day | frozen | 309 | 297 | 246 | 224 | 75% | 11/82 | control (frozen prompt) |

**Gate: pass for both judges.** Under the r10 prompt no rejected pass is rejected for missing latents or removal: Terra 0 of 24; Haiku 0 of 219 (its 2 narrow matches mention removal only to set it aside, or the regex's balanced accuracy).

**The control shows strong drift since 12 Nov.** On the frozen prompt today, Terra rejects 109 of 309 passes, 98 for missing latents; the registered 12 Nov first send rejected 91 of the same 309 (all probes). Wrong `none` credited: 12 Nov 48/55, same-day frozen 43/55, r10 40/55. (Correction after the independent recheck: an earlier version of this line and the commit message of 73fbf9b said 42/54.) Haiku's frozen-prompt rejections are 297 of 309 (224 hand-read as latents/removal). So the frozen-vs-r10 change mixes the fix with model drift; ROUND10_DIFF shows the control's change next to the fix's.

**Haiku still rejects most passes under r10** (219 of 307), now for other reasons (regex form, the 0.3 threshold, untested candidates; P0.5-G T2/T3): failures-table row 9 does not disappear for Haiku.

Credit by answer case at the report level, set A 132 runs, all probes (P0.5-G units):

| case | r10 L0 | same-day frozen L0 | r10 H0 | same-day frozen H0 |
|---|---|---|---|---|
| right `none` | 118/127 | 122/127 | 46/127 | 50/127 |
| wrong `none` | 40/55 | 43/55 | 17/54 | 20/55 |
| false finding | 1/5 | 0/5 | 0/4 | 0/5 |
| pass | 285/309 | 200/309 | 88/307 | 12/309 |
| wrong cue | 13/32 | 12/32 | 0/32 | 0/32 |

P0.5-G (`../p05/reason_scan_gate.json`): parse failures {'L0': 0, 'H0': 1, 'L0ctrl': 0, 'H0ctrl': 0} (one Haiku r10 reply unparsed, not re-sent); non-boolean `correct` values: none at any of the four levels, so the strict and frozen parsers agree on every gate verdict; step 0: no grade output in any judge input; leak suspects 45, hand-read {'i': 38, 'iv': 7}, category (iii) 0 → No judge cheat signal. One control call was held back by a too-low per-directory cap ($1.3, below the plan's $1.6) and sent at 06:24 UTC under $1.6.

