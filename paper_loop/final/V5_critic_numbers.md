# V5 number and label audit

Audited: `final/PAPER_V5.md` (843 lines). Sources: `gpu_results/RESULTS_FOR_PAPER_835680a.md` (RES),
`gpu_results/GPUPLAN_README_835680a.md` (README), `final/PAPER_V4_user.md` (V4), `exchange_rate/00_ANSWER.md` and
`SUMMARY_PLAIN.md`, `gpu_results/review/*.md`, `brainstorm/WORKSHOP.md`, figures in `final/fig/`.

Overall: nearly every count, p-value and interval in the body traces to a source. I recomputed the arithmetic for
Tables E1/E2, F1, F4, H0/H1, I1, G1 and J (break-even): no arithmetic errors. Hard rules hold: no cue name next to an
id, no F2-a/b/c ids, no October material in the body, no names or URLs, no `{x}`/TBD in the body. Length: the body is
5,286 words (limit 5,300) and the abstract 200 (limit 200), with 4 tables and 2 figures. **Every fix below must be
word-neutral.**

## A. Mismatches and misreadings (fix before submission)

**A1. C21 audit order is misread. This is the only real number error.** V5 §5.2 l.141 says "no audit order beats random
beyond the earliest audits", and App. Q l.727 says "runs with more `none` answers first, 50% after 24% of runs audited
and 80% after 67%; random order, 50% and 80% at the same points; lowest judge confidence first, 53%; judge-pass first,
69%."
- Correct reading: the percentages in brackets are the **share of runs that must be audited** to reach the same
  share of errors. A random order catches x% of errors after x% of runs in expectation, so "random 50% at 24%" cannot
  be right. Sources: RES:58, README:66-69 ("50% … after 24% of runs (random: 50%; lowest judge confidence first: 53%;
  judge-pass first: 69%); 80% after 67% (random 80%)"), and review_skeptic:30 ("random order needs 50%"),
  review_stats:33.
- What the data say: `none`-first reaches half the errors after 24% of runs, against 50% for random, and 80% after
  67%, against 80%. That is a modest gain, and it is **in-sample**. Confidence-first (53%) is no better than random,
  and judge-pass-first (69%) is worse.
- Fix for §5.2 (same length): "…are worth 0.0 certified grades; ordering audits by `none` count reaches half the
  judge's errors after 24% of runs (random 50%), an in-sample gain (Appendix Q)." Rewrite App. Q to match.
- Keeping C21 out of the contributions is still right, because it is in-sample and exploratory, not because it is
  "no better than random".

**A2. Reliability and validity are compared on different slices.** The abstract (l.9) says "agrees with itself at
κ 0.44 but with the certified grade at κ 0.002". §5.2 l.131 says "caps … near √0.44 ≈ 0.66".
- 0.44 is Fleiss κ over **all slots**; the hard-slot value is **0.39** (RES:68-69). κ 0.002 is **hard-slot** (H0 l.579;
  the all-slot value is 0.12, l.580).
- Fix: use the hard-slot pair (self 0.39 vs certified 0.002) or the all-slot pair (0.44 vs 0.12). The cap on the
  hard slot is √0.39 ≈ 0.62.
- Label the √ as a heuristic. It is the classical attenuation bound for correlations, not a theorem for κ, and its
  only source is review 00:47.

**A3. "Blind, it needs 64 to match" overstates the curve** (intro l.27; §5.1 lead l.113).
- Terra matches at 64. At 16 it falls short only at run level (p = 0.023; item level p = 0.125, inconclusive;
  V4:146, V5 l.115). B = 32 was not run. The identified bracket is (16, 64] at run level and (8, 64] at item level
  (App. K l.660; SUMMARY_PLAIN:71-72: "needs between 16 and 64").
- Fix: "blind, it matches only at 64 of the budgets run (16 falls short at run level)" or "needs more than 16 and at
  most 64".

**A4. The multiplicity sentence (l.107) inflates labels.**
- (a) It lists 2e-9 as a claim-carrying p, but C12 is "[pre-reg C12, descriptive]" (RES:60, App. R l.762 "as
  predicted (desc)"). Drop 2e-9 from the list or say "descriptive".
- (b) Ledger R1 has 31 hypotheses, so the Bonferroni cut is 0.05/31 ≈ 0.0016. C14's p = 0.002 does **not** survive.
  Say so explicitly; it is excluded now, which is right, but the reason is unstated.
- (c) L1/L2 (2e-7, 3e-6) were frozen after Terra's results. The footnote covers this; keep it next to the claim.

**A5. The figures contradict the narrowed text.**
- `fig2_measured.png`: the title reads "One proxy, many exchange rates (measured)". That conflicts with Box 2 and with
  dropping "worth X queries". Retitle it, e.g. "Success against exact budget, measured".
- The dotted line at 0.958 is an exchange-rate read-off; drop it or explain it in the caption.
- Panel (b) plots r = 1, but the caption and App. K say r = 2/3/4/6/8. The X1 depth panel has no rank-1 values
  (RES:36-38), so the r = 1 points are not traceable in text.
- In panel (b) the agent points are jittered to x ≈ 1.35-1.85, so they read as rank 1.5. Place them at r = 2 with a
  small offset, or state the offset in the caption.
- `fig2_trap_routes.svg` (Figure 1): the footnote says "All texts are sent before any result returns" and both routes
  say "one burst". That is the "one batch" claim the paper withdraws. The 47 timed runs include Claude agents, whose
  one-burst rates are 9-11 of 15-16 (RES:22-27, README:51-57). Change it to "the first batch on the trap probe" and drop
  "all texts".

## B. Claims stronger than their label (medium)

**B1. "Width … decides the outcome"** (intro l.29, §5.3 heading l.159, §10). The route evidence is [expl]: 25/26 vs
5/21, and the conditional test within agent gives p = 0.15, not established (l.171; App. G). The X4 source says the
width "separates them" (RES:26-27; README:57). Use "separates" in the heading and intro. "The model decides" is fine
for L1/L2 within one harness.

**B2. "It knows which probe to distrust before any exact result"** (§5.1 l.119). There is no Open-4 one-burst or
first-batch measure; 2.67 vs 0.44 is total allocation (RES:11). Fix: "it concentrates its texts on the anomalous
probe (2.67 vs 0.44)".

**B3. The C14 label omits "descriptive, 2 items".** RES:28 labels the item "[pre-reg C14, descriptive, 2 items]" while
also reporting "H1 confirm". V5 §5.3 l.167 and Table 2 say "confirmed" with no qualifier. Add "(two items)" in Table 2
and keep the per-item counts 7/7 and 6/7, which V5 already does.

**B4. "Within re-send noise"** (l.133; L1 0.06 vs L0r −0.01 vs L1r 0.20). No interval was computed. RES:44 says only
that the placebo is "no worse than the real log", and App. N l.697 says "we do not interpret it". Use the App. N
wording in the body. Never say the log "hurts" (V5 complies).

**B5. Self-grading coverage** (l.129: "Judging Luna's runs and using two other judges address self-grading"). Luna as
judge is the same GPT family. The only cross-family judge is Haiku, which "credits almost nothing" (RES:63) and
blames 82-85/87 (RES:46). Say "partly address".

**B6. C19 "13/36 pairs reversed"** (Table 3 l.156). The item is [expl]. Only 2 reversals are robust (RES:56,
README:61-62), and the τ_b interval includes 0 (−0.09 to 0.46). Fix: "13/36 pairs change order (2 robust)". The
abstract's "reorders a nine-system leaderboard" is acceptable, but it carries no [expl] cue.

**B7. Section heading "Exact queries are precise but not decisive"** (l.67). X2 gives a single-text error of 1.3%
false positive and 1.4% false negative (3.1% on trap mains) (RES:18-19). The referee asked for "nearly decisive, but
effects vary across base notes" (SUMMARY_PLAIN:78-79). "Not decisive" understates the measurement. Fix: "precise and
nearly decisive per text, but edit effects vary across base notes".

## C. Minor (fix if words allow)

- **Abstract, "Every trap sits at proxy rank 2":** add "sign-aware". One fresh [main] is rank 3 by |latent ratio|
  (RES:75-76; V5 §3 l.65).
- **§2.2 l.53, "fresh traps … used only in §5.3":** they also feed C14 H5 in §5.2 and Table 3.
- **Table 4 l.184:** label the "[main] isolated" row "pre-reg C14 H2 (outside every band)", not "pre-reg C14".
- **App. K l.654, "an adaptive agent about 0.51 vs 0.36":** 0.51 is an upper bound on the adaptive minimax value
  (00_ANSWER:199).
- **App. M l.668, "minimum detectable difference … about 0.25":** this is a reviewer's estimate (review_stats:36), not
  a computed result. Mark it as approximate or drop it.
- **App. J l.630:** spend is `{PENDING}` in RES:81. V5 says it is "not reported", which is fine, but the CFP asks for
  cost. Fill it when available.

## D. Checked and correct (no action)

Abstract arms 12/12, 23/24, 6/24, 16/24, 24/24. C1 +0.71 [+0.42, +0.96], Holm p 0.0002, sign p 0.031. C2 +0.75. C4 +0.04
[0.00, +0.17]. X3-H1 Wilson 0.76-1.00, p 1.5e-5. X1 table and depth panel (RES:13-16, 36-38; README:29-43). X2 (RES:17-19).
X4 one-burst and texts (RES:22-25). Luna L1/L2/L3 (2.2e-7, 2.5e-6, 0.22). C14 13/14, 7/7, 6/7, 3/10, 2/10, 4/10,
gap 0.63, p 0.002, 3.0 vs 1.1, 3.86 vs 1.38, anchor 2/3. H2 "outside every pre-registered band" (correct; "partial" is
not used). C6 −0.01/0.06/0.20, J5′ +0.08 (LB −0.02), 7/17 → 7/17, 0.19, 21/26, 4/7 vs 0/7, any-named 0.67, Haiku
−0.10 to −0.23 and 82-85/87, BB-16 − BB-64 by rung. C8 0.018, 35/53 [0.53, 0.77], −0.19 [−0.42, +0.03] vs 0.86; "erased"
is used, not "reversed". C12 31/39 vs 1/39, 30 vs 0, 2e-9, 8/12 vs 0/12, 23/27 vs 1/27, 5/12, Haiku 4/39. C7 0.48-0.58,
247/263 → 6/263. C17 0.44/0.39/60%/0.47. C19 τ_b 0.23 (−0.09 to 0.46; item −0.17 to 0.37), +0.375 → −0.06,
+0.67 → +0.08, −0.21 vs +0.25; AstaBench 0.467 is used as context only (WORKSHOP:14). PPI r 0.002 → 0.0.
Intro 18.7% / 2.5% / 400 and 41/44. Tables H0, H1, I1, F1, F4, G1 and E1/E2 recompute exactly. Token cap +0.83/+0.75/
+0.71/+0.46. Break-even $0.006 and 37c. Decomposition 0.30-0.64 / 0.10-0.45 / 0.00-0.04 and exchange-rate range 11 to
about 50 (00_ANSWER:89, 92). Rank-only policies are called "references, not bounds" throughout. No "worse than no
auditor" and no "keep pace". The rank-6 correction (R6 cancelled) is stated correctly.
