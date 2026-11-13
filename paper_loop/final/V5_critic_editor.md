# V5 editor report: clarity, flow and fit to an AAAI-27 workshop full paper

Target: `final/PAPER_V5.md`. This report complements `V5_critic_reviewer.md` (the reviewer-action audit). Where the two overlap (C21, rank-6, "decides", figure order) I give the edit once and mark it "(also reviewer critic)".

## 0. Measurements (shell, `wc -w`-style whitespace tokens)

| check | limit | V5 | status |
|---|---|---|---|
| Abstract | ≤ 200 words, one paragraph | 199, one paragraph | pass, no slack |
| Body (`## 1` to `## References`, tables included) | ≤ 5,300 | **5,339** | **over by 39** |
| of which table text / boxes / captions | — | 766 / 226 / 191 | — |
| Tables in body | ≤ 4 | 4 (Tables 1-4) | pass |
| Figures in body | ≤ 2 | 2 | pass, but out of order (see E3) |
| Section sizes | — | §1 676, §2 706, §3 456, §4 756, §5 1,985, §6 101, §7 235, §8 208, §9 93, §10 79 | §4 and §5 are heavy |
| Leak rule (cue property names anywhere in the file) | none | none found | pass |
| October material, author/branch/GitHub strings, `{…}`/TBD/PENDING | none | none found | pass |
| Citations | all body citations in References | all present; Atsidakou entry has no year; "Blackwell" cited with no reference | minor (E19) |

Command used: `python3 -c "t=open('PAPER_V5.md').read(); print(len(t[t.find('## 1'):t.find('## References')].split()))"`.

**Length target.** The fixes below add about 60 words (scoping sentences and definitions). Cut about 250 words so the body lands near 5,150 and survives any word counter. The cut list in §3 removes 255 words without losing a result.

## 1. Overall verdict

V5 is close to submittable. The story is right: AI-scientist framing, three claims, budget curves in place of an exchange rate, the judge as an instrument-validity study, Claim 3 narrowed to batch width and one-step widening, and a body ledger. It has four kinds of editorial problem:

1. It is 39 words over the limit, and the needed edits add words.
2. **Terminology drifts.** The same object has 3-5 names: hard probe / trap probe / anomalous probe / hard slot; exact query / exact text; Open-8 / proxy arm / with the SAE; BB-8 / blind / no-proxy. Several terms (BB, anomalous probe, proxy's head, hard slot, Block 1's meaning) are used before definition or never defined.
3. **Tables 2-4 repeat the prose.** Table 2's judge rows duplicate Table 3, and §5.3 restates most of Table 4. That redundancy is where the words should come from.
4. **A few sentences overclaim or are wrong:** "decides", "needs 64", the C21 clause, and the rank-6 contradiction. Figure 2's suptitle still says "exchange rates".

## 2. Top 20 problems, prioritised, with concrete edits (old → new)

### Must fix (acceptance risk)

**E1. Body over length.** Apply the cut list in §3. Without it the paper is non-compliant under the CFP's 8-page limit.

**E2. C21 clause is factually wrong** (also reviewer critic). Under the source's numbers (`GPUPLAN_README` C21), `none`-first needs 24% of runs to reach 50% of errors where random needs 50%, and 67% to reach 80% where random needs 80%. The gap shrinks but does not vanish. Deleting the clause is cheapest and also removes the audit rule from the body, as the brief asks.
- §5.2 Consequences, old: "Under prediction-powered inference the 214 verdicts (r = 0.002 with the grade) are worth 0.0 certified grades, and no audit order beats random beyond the earliest audits (Appendix Q)."
- new: "Under prediction-powered inference the 214 verdicts (r = 0.002 with the grade) are worth 0.0 certified grades (Appendix Q)."
- In Appendix Q, state C21 as: "`none`-first reaches 50% of errors after 24% of runs and 80% after 67% (random order: 50% and 80%); the rule was suggested by the same runs [expl]."

**E3. Figure order and placement** (also reviewer critic). Figure 1 is cited in §1 but placed after Table 4. Figure 2 appears first, in §5.1. AAAI numbers floats by first appearance.
- Move the `![Figure 1](fig/fig2_trap_routes.svg)` block and its caption to the end of §2.2, after the "Six items ship…" paragraph. Panel (a) illustrates the trap row of Table 1.
- AAAI LaTeX does not take SVG. Convert the routes SVG to PDF (`fig2_measured.pdf` already exists for Figure 2).
- In the SVG footnote, old: "All texts are sent before any result returns." → new: "In both routes the first batch is sent before any result returns." X4 refutes the general version.

**E4. Figure 2 contradicts the paper's own framing and is unreadable at column width.**
- Delete the suptitle "One proxy, many exchange rates (measured)". Box 2 is titled "Curves, not an exchange rate", and the caption carries the title in AAAI.
- The legend has 18 entries. At two-column width it renders at about 5 pt.
  - Set the figure as a full-width `figure*`.
  - Cut the legend to ≤ 10 entries: drop the two abstract-model [priv] dashed curves, which Box 2 covers in words. Merge the duplicate glyphs: "Terra, Open-8, shipped traps" and "Terra with SAE, B = 8" are the same black disc; "Luna, Open-8, shipped traps" and "Luna with SAE, B = 8, all six" are the same grey diamond.
- Panel (b): the agent markers sit at x ≈ 1.3-1.9. Centre the jitter on rank 2 so nobody reads "rank 1.5".
- The dotted horizontal line at about 0.96 is unexplained. Label it "Terra Open-8 level (23/24)" or drop it.
- Caption, old: "Solid lines: rank-only reference policies run in the environment [expl X1]; dashed: abstract model [priv]." → new: "Lines: scripted reference policies run in the environment (rank-only, or blind) [expl X1]." (also reviewer critic)

**E5. Causal overclaims in abstract, §1 and the §5.3 heading** (also reviewer critic). Luna's general deficit (two-part 4/18 vs 12/12) means "the model decides" is not shown.
- Abstract, old: "When the SAE ranks a decoy first, the model decides the outcome within one harness: on unseen traps Terra names the cue in 13/14 runs; GPT-6 Luna rarely does. Every trap sits at proxy rank 2: one-step widening, not deep search." → new: "When the SAE ranks a decoy first, outcomes differ by model within one harness: on unseen traps Terra names the cue in 13/14 runs, the smaller GPT-6 Luna in 2/10. All traps sit at proxy rank 2: one-step widening, not deep search." (the trims below then drop "the")
- This replacement alone takes the abstract to 202 words. Make three further trims: "their evaluators often grade them" → "their evaluators grade them"; "using free but fallible sparse-autoencoder (SAE) tools" → "using free, fallible sparse-autoencoder (SAE) tools"; "the smaller GPT-6 Luna in 2/10" → "smaller GPT-6 Luna in 2/10". Measured with these trims, the abstract is 199 words. Do not add anything else to the abstract.
- §5.3 heading, old: "on traps, batch width decides" → new: "on traps, batch width separates agents".
- §5.3 paragraph title, old: "**Within one harness, the model decides [pre-reg L1, L2].**" → new: "**Within one harness, the width differs by model [pre-reg L1, L2].**"

**E6. Claim 1 overstates the blind curve** (also reviewer critic). The identified bracket is (16, 64].
- §1 bullet, old: "With the SAE tools, GPT 6.1 Terra at 4 exact queries beats itself without them at 8; blind, it needs 64 to match (§5.1). Terra only." → new: "With the SAE tools, GPT 6.1 Terra succeeds in 12/12 runs at 4 exact queries; without them it scores 6/24 at 8 and 16/24 at 16, and matches only at 64 (§5.1). For Luna the gain was not confirmed."
- §5.1 lead, old: "without the proxy it needs 64 to match" → new: "without it, Terra reaches the same level at 64 queries but not at 16".

**E7. Rank-6 contradiction in §5.3 Scope** (also reviewer critic). Old: "because the bank's traps sit at rank ≤ 2;" → new: "because its prior is fitted to the bank's clean traps, all at rank ≤ 2;".

### Clarity and definitions (reviewers will stumble here)

**E8. Undefined or drifting terms.** Fix them all in the §1 **Terms** paragraph, then use one name throughout.
- Replace the Terms paragraph, old: "**Terms.** *Hard probe*: the probe that gates the score (a trap or a two-part nested cue). *Isolate*: … *Proxy rank*: §3. *NAME* (success): …" → new: "**Terms.** *Hard probe*: the probe that gates the score (a trap or a two-part nested cue); the agent is not told which it is. *Trap probe*: the hard probe of a trap episode. *Exact query*: one text sent to `probe_query`; the budget B counts them. *Isolate*: exact-test one candidate with a single-property edit. *Widen*: isolate the proxy's runner-up as well as its favourite. *First batch*: the exact queries sent on a probe before any result on it returns. *Proxy rank*: §3. *NAME* (success): every hard cue named with no extra cue, and every null probe answered `none`. *Open-B / BB-B*: B exact queries with / without the SAE tools (BB, black-box)."
- Then do these global replacements in the body:
  - "anomalous probe" (4×) → "trap probe";
  - "hard slot" (1× in §5.2, and the Table 3 caption) → "hard probe";
  - "proxy's head" (3×) → "proxy's top candidates" (§1 Claim 3, §5.3 heading). In the heading, "top candidates" keeps it short.
  - "exact texts"/"texts" → "exact queries" in prose. Keep "texts" only in Table 4's row label, as "exact queries on trap probe vs per other probe".
- "[main]" and "[decoy]" are used in the running example before the bracket convention is explained. After "the true cue, the [main], second", add: "(we write [main] and [decoy] throughout and withhold specific cues so the items stay usable)".
- "Main study: four larger agents" includes Haiku, which reads as wrong because the only smaller agent is Luna. Old: "*Main study*: four larger agents × 16 runs, proxy, B = 8." → new: "*Main study*: Terra, Opus, Sonnet and Haiku, 16 runs each at Open-8." Similarly, old "*Development set*: 100 proxy runs of the larger agents." → new: "*Development set*: 100 Open-8 runs of those four agents."

**E9. The introduction lacks an explicit gap sentence.** The gap appears only at the end of §7. Reviewers look for problem → gap → contribution in §1.
- Insert at the end of the first §1 paragraph, after "…checked against an exact, executed grade.": "Existing research-agent benchmarks grade through judges, rubrics or held-out scores, and interpretability-agent benchmarks grade named findings with LLM judges; none rations exact checks against a proxy that is certifiably wrong on known items, nor checks its judge against an executed grade." (+40 words)
- Delete the duplicate in §7, old: "To our knowledge no prior environment combines an unnamed cue, a lossy proxy that can hide it, a scarce adaptive exact budget, a closed-form grade and budget-matched no-proxy arms (Table V1)." → new: "Appendix V (Table V1) compares the closest prior work on these axes." (−21 net)

**E10. Claim 3 bullet is long and hedged into opacity.** Old: "**Claim 3: agents verify the proxy's head; on traps, the width of the first batch on the anomalous probe decides the outcome, and the model decides the width.** It holds within one harness and on held-out traps; with all five traps at proxy rank 2, this is one-step widening, and depth is scripted only (§5.3)." → new: "**Claim 3: agents test the proxy's top candidates; on traps, the width of the first batch on the trap probe separates pass from fail, and the width differs by model.** Within one harness Terra widens and Luna rarely does, on shipped and on held-out traps. All five traps sit at proxy rank 2, so this is one-step widening; depth is shown only for scripted policies (§5.3)."

**E11. Table 2 is unreadable for anyone who has not seen the pre-registrations.** The hypothesis column is code ("J8 log κ < 0.40; J5′ named-only κ; J6 wrong-cue credit falls; J7′ `none` index (bar 0.30)"). The status column uses seven different words: confirmed, supported, rival eliminated, inconclusive, as predicted, holds, desc, outside every band.
- Add a caption sentence: "Status: *confirmed* (pre-registered prediction met), *not confirmed*, *descriptive* (registered without a test), *outside bands* (no pre-registered outcome applies)." Map "supported", "as predicted" and "holds" → "confirmed" (they are the same thing in the prereg files), and "desc" → "descriptive".
- Replace the C6 row with two plain-language rows, and let Table 3 carry the numbers:
  - `| C6 J8 | judge with exact-query log still κ < 0.40 | 130 | κ 0.06 | confirmed |`
  - `| C6 J5′, J6, J7′ | log helps among named answers; cuts wrong-cue credit; flags omissions | 130 | Table 3 | not confirmed |`
- Merge the J1/J2, C8, C12/C7/C17 and C14 H5 rows' result cells to "Table 3" where Table 3 already shows the number. This saves about 45 words, counted in §3.

**E12. Table 3 packs three rungs into one row with slashes.** Old: "| L0r re-send / L1 + query log, true logits / L1r placebo log | C6 | 130 | κ −0.01 / 0.06 / 0.20 |" → new, three rows:
- `| L0r: report only, re-sent | C6 | 130 | κ −0.01 |`
- `| L1: + exact-query log, true logits | C6 | 130 | κ 0.06 |`
- `| L1r: + log, logits hidden (placebo) | C6 | 130 | κ 0.20 |`

Also add one caption sentence: "Rows with n = 130 use the Block 1 and BB-16 runs (set A); L0 uses all 214." This answers the obvious "why does L0 differ from L0r?" question.

**E13. Table 4 mixes populations under "Open-8 unless marked".** The one-burst row (40/40) and the texts row (3.9-4.0) pool main study and Open-8.
- Old: "| all exact texts in one burst | 40/40 (with SAE) | 36/36 | expl X4 |" → new: "| all exact queries in one burst (main + Open-8) | 40/40 | 36/36 | expl X4 |".
- Old: "| texts on trap probe vs per other probe | 3.9-4.0 vs 1.3-1.4 | 1.9 vs 2.0 | expl X4 |" → new: "| exact queries on trap probe vs per other probe (main + Open-8) | 3.9-4.0 vs 1.3-1.4 | 1.9 vs 2.0 | expl X4 |".

**E14. Mismatched denominators in one sentence** (also reviewer critic). Old: "Haiku follows up on the trap probe in 4/5 Open-8 runs yet names 0/6 [expl X4]" → new: "Haiku sends a second wave to the trap probe in 4 of the 5 Open-8 runs whose first wave tested only the favourite, yet names the trap cue in 0/6 [expl X4]". Also, old: "Neither sends a second wave to the trap probe (Terra 0/12, Luna 0/11)." → new: "After a first wave that tested the favourite, neither sends a second wave to the trap probe (Terra 0/12, Luna 0/11)."

**E15. Vague or rhetorical sentences in §5.2.**
- Old: "It also answers the objection that agents' messages were not reports." → new: "Since no report is shown, the leniency cannot come from agents' prose."
- Old: "**It generalizes.**" → new: "**It replicates across runs and judges.**" ("generalizes" invites "to what?")
- Old: "L1 … κ is 0.06 (J8 confirmed), within re-send noise of a same-time re-send (L0r, −0.01) and a placebo log with logits hidden (L1r, 0.20)." → new: "with the log (L1) κ is 0.06 (J8 confirmed), within re-send noise of the report-only re-send (L0r, −0.01) and of a placebo log with logits hidden (L1r, 0.20)."
- §5.2 Setup, old: "Judging Luna's runs and using two other judges address self-grading" → new: "Because Terra also grades its own runs, we also judge Luna's runs and use two other judge models".

**E16. Label format is inconsistent.** §4 defines [pre-reg X], [desc], [expl], [priv] and [reader], but the body also uses "[J2]", "[pre-reg]" (no id), "[post hoc; no committed script]", "[expl, development set]" and "[post hoc; Appendix F]".
- Old: "It credits 53 of 68 certified failures [J2]." → new: "…[pre-reg J2]."
- In the §4 label list, add: "[post hoc] counted after seeing the data, with no frozen script."
- Leave the other variants as they are; they are understandable.

**E17. Box 2 is dense, and its notation and terms are inconsistent with Appendix K.**
- "V(B) the ideal" is undefined. Old: "and V(B) the ideal" → new: "and V(B) an ideal agent's success".
- Appendix K calls the third term "proxy shortfall"; Box 2 calls it "misuse". Use "misuse" in both places, as the brief does: in Appendix K, old "proxy shortfall 0.00-0.04" → new "misuse 0.00-0.04".
- "(Blackwell)" has no reference. Either add Blackwell (1953), *Equivalent comparisons of experiments*, to References, or change it to "(by Blackwell's theorem)" and add the reference anyway.

**E18. Redundant introduction of the judge's grading setting.** §5.2 Setup repeats §7 ("This is the grading setting of Circuit Oracle … and of report-graded auditing games and agents (Marks et al. 2025b; Bricken et al. 2025)."). Keep it in §5.2, where it motivates the study, and in §7 replace "Auditing games (Marks et al. 2025b) and auditing agents (Bricken et al. 2025) grade reports (§5.2)." with nothing. The citations survive in §5.2.

**E19. References hygiene.** "Atsidakou, Katariya, Sanghavi, Kveton. Bayesian fixed-budget best-arm identification. arXiv 2211.08572." is cited as 2023 but has no year → append ", 2023". Add Blackwell (E17). GX-Chen 2025 and Gogleva 2026 are cited only in the appendix, which is fine.

**E20. §6 does not earn a section heading.** At 101 words, its heading and spacing cost about 3 AAAI lines.
- Fold it into §7 as the first paragraph, titled "**Agents and SHIFT.**", and delete "The route is closest to Karvonen et al. (2024);" (Karvonen stays cited in the same sentence's evidence: "…of a size-matched reference's removal (Karvonen et al. 2024)…").
- Renumber §§7-10 → §§6-9.

## 3. Cut list (≈ 255 words, no result lost)

| # | where | cut | words saved |
|---|---|---|---|
| 1 | §2.2 last sentence | "The trap is a controlled stress test, not an estimate of how often SAEs fail naturally." (Limitations already says "natural frequency … unknown".) | 16 |
| 2 | §2.3 last sentence + §2.4 last sentence | Keep one removal-strictness fact. Delete "Absolute removal thresholds of 0.30, 0.40 and 0.50 cut main-study hard passes from 45 to 33, 7 and 0 [expl]." and keep "Removal binds at f = 0.9 with an 8-latent cap [expl]". The thresholds stay in Appendix D. | 21 |
| 3 | §3 Recipe tail | "Applied to an evaluator, the judge is the proxy and the executed grade is gold (§5.2). In an MLE-bench-style task (Chan et al. 2025) the proxy would be the validation score and the exact check a rationed test submission; in PaperBench (Starace et al. 2025), the rubric judge. We have not tested other domains." → "Applied to an evaluator, the judge is the proxy and the executed grade is gold (§5.2); in MLE-bench (Chan et al. 2025) they would be the validation score and a rationed test submission, in PaperBench (Starace et al. 2025) the rubric judge and the replication. Other domains are untested." | ~10 |
| 4 | §4 Statistics | "item-level sign tests have floors of 0.031 (six items), 1/32 one-sided (five traps) and 0.25 two-sided (three)" → "item-level sign tests have floors of 0.031 (six items or five traps, one-sided) and 0.25 (three items, two-sided)" | 6 |
| 5 | §4 Multiplicity | Delete "X1, X2, X4, C19, C21 and all trace analyses are exploratory." (the labels already say so) | 11 |
| 6 | Table 2 | Judge rows' result cells → "Table 3" and the C6 rewrite (E11) | ~45 |
| 7 | §5.1 Scope | Delete "Per correct answer, the proxy arm is cheaper than BB-64 once an exact query costs more than about $0.006 [expl]." and keep the cost line in §4, adding "(exact queries unpriced; break-even about $0.006 per query, Appendix J)". | 12 net |
| 8 | §5.2 Setup | E18: delete the §7 duplicate sentence | 16 |
| 9 | §5.2 Consequences | E2: delete the C21 clause | 10 |
| 10 | §5.3 L1/L2 paragraph | Table 4 has the counts. Old: "On shipped traps Terra isolated the runner-up in 11/12 runs, Luna in 0/18 (one-sided p = 2e-7), and named the cue in 11/12 vs 1/18 (p = 3e-6)." → new: "On shipped traps Terra widened and named the cue far more often than Luna (Table 4; one-sided p = 2e-7 and 3e-6)." | 12 |
| 11 | §5.3 C14 paragraph | Delete "Terra tested 3.0 candidates on the trap probe, Luna 1.1." (it repeats the width point; move it to Appendix P) | 11 |
| 12 | §5.3 Routes | Old: "This is close to true by definition; the conditional test among runs that isolated the [main] (25/26 vs 2/5) is not established within agent (p = 0.15; Appendix G)." → new: "Partly true by definition; conditional on isolating the [main], 25/26 vs 2/5 is not established within agent (p = 0.15; Appendix G)." | 10 |
| 13 | §5.3 Capability | Old: "Luna's two-part deficit (Table 4) is nearly as large as its trap deficit, so much of the outcome gap is general; the allocation gap is not: scaling Terra's trap widening by Luna's lower rate of testing the favourite at all predicts about 7 of 18 widenings, against 0 observed [post hoc; Appendix F]." → new: "Much of the outcome gap is general capability (two-part NAME 4/18 vs 12/12); the allocation gap is not: adjusted for Luna's lower rate of testing the favourite, Terra's rate predicts about 7 of 18 trap widenings, against 0 observed [post hoc; Appendix F]." | 8 |
| 14 | §6 → §7 | E20: heading plus the Karvonen clause | 9 |
| 15 | §7 | E9: the gap sentence moves to §1 (net with the §1 insertion counted in §0) | 21 |
| 16 | §10 Conclusion | Old: "ShiftHunt evaluates research agents, and the judges that would grade them, against an executed grade. The recipe shows that…" → new: "Against an executed grade, the SAE tools shift Terra's measured budget curve, and…" | 17 |
| 17 | Box 1 | Delete the budget clause "Per episode: 150 tool calls, 3000 forward units […], 8 texts for `probe_query` in total […]" (§2.1 and §4 restate it; Appendix A has the verbatim text) | 17 |
| | **total** | | **≈ 255** |

If more is needed, the next candidate is §2.4 **Validation**. Keep "regrading reproduces 100/100; six scripted cheaters score 0 on 6/6 episodes" and move the positive/naive controls and the 86/86 coded rollouts to Appendix C (about 25 words).

Do **not** cut: the "Why an interpretability task" paragraph, the running example, the matched-budget paragraph (the CFP requires it), the H2 "outside every pre-registered band" wording, the "What Terra uses beyond the ranking is not identified" paragraph, or the Limitations.

## 4. Section-by-section flow notes (brief)

- **§1:** with E9 and E10 it states the problem, gap, contributions and three claims crisply. Contribution (ii) "A proxy-and-gold recipe" is fine, since §3 delivers it.
- **§2:** earns its space. Table 1 is self-contained. With Figure 1 moved here (E3), the trap is visual before the reader needs it.
- **§3:** good. Box 2 reads well after E17. The recipe paragraph is the right length after cut 3.
- **§4:** the heaviest non-results section (756 words, incl. Table 2). After E11 and cuts 4-6 it drops to about 680. The Multiplicity paragraph is necessary; keep it.
- **§5.1:** clear. With E6, the lead sentence matches the evidence.
- **§5.2:** the strongest section. Its order (reliability → validity → evidence ladder → trivial rule → C12 prior → replication → consequences) is exactly what the reviewers asked for; do not reorder. The closing sentence "For this grade, a report-reading judge measures answer type, not correctness" is the best line in the paper; keep it last.
- **§5.3:** too many short bold-led paragraphs (seven). After cuts 10-13 it reads as: verification → commitment → within-harness width → held-out replication → capability → routes → scope. That order is right.
- **§8 Limitations:** complete. One wording fix: old "Removal is nominal on traps; it binds only in a stricter regrade." → new "On traps the removal gate is nominal (τ 0.15-0.22); it binds only in a stricter regrade."
- **§9:** fine. Add "(model tokens at list prices)" after the dollar figures so the cost basis is explicit.

## 5. Consistency checks passed

- One canonical denominator per claim in the body, matching Appendix S Table S2: Block 1 23/24; L1/L2 11/12 vs 0/18 and 1/18; L0 214; set A 130.
- Spot-checked numbers trace to `RESULTS_FOR_PAPER_835680a.md` / `GPUPLAN_README_835680a.md`: 12/12, 1.5e-5, 2.67 vs 0.44, X1 curves (0.49/0.95/0.96, best blind 0.44/0.79/0.97), X2 (0.051, 0.110, 1.3%, 1.4%, 0.007-0.009), X4 (40/40, 36/36, 9-11/16, 3.9-4.0 vs 1.3-1.4), C14 (13/14, 7/7, 6/7, 3/10, 2/10, 4/10, 0.63, p = 0.002), C6 (−0.01, 0.06, 0.20, 0.67, 7/17, 21/26, 4/7), C8 (0.018, 35/53, −0.19 vs 0.86), C12 (31/39 vs 1/39, 2e-9), C7 (0.48-0.58, 247/263 → 6/263), C17 (0.44, 0.39), C19 (τ_b 0.23, 13/36, +0.375 → −0.06, +0.67 → +0.08, −0.21 vs +0.25), PPI 0.0.
- Appendix inconsistency to fix: Appendix F says Luna's [decoy]-after-clean-pair count is "7 of 10", but Appendix G Table says "7 of 18 trap runs". State the denominator once, for example "7 runs (of the 10 with a clean refuting pair; 18 trap runs)", if the block README supports that reading. Otherwise use "7 runs" with no denominator, as the body does.
