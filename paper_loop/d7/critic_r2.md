# CRITIC r2: d7/draft_r2.md, direction "W6 Focused empirical short paper: interpretability tools as testing capacity"

Inputs: BRIEF (RULES, CFP, SOURCES, USER_BRIEF, PRIOR_FIXES, EXISTING_DIRECTIONS), LEDGER (H2, H11, §6 dead claims), lit/L1-L3 (headings and the cited entries), updates/round_9_manual_1112T0830Z.md (newest) and round_2.md, critic_r1, draft_r2, 12 claim verdicts (C1-C12), 3 reviews (7 / 7 / 7). Re-read from source (read-only): failure_modes/README.md (one-burst definition), scripts/followup_failure_modes.py, followup/misc/README.md (attr16 control), shifthunt/effects.py (τ reference), rows_r1112.csv, s3_r1112.csv.

New numbers below are computed read-only from committed November files. The script is `paperloop/d7/calc/breakeven_boot.py`. No [OCT] input was used and no runs were made. Each new number is tagged [new, existing data].

## 1. Diagnosis (5 lines)

1. Every number in the draft reproduces from source (C1, C2, C3, C9, C10 supported; the six "overclaimed" verdicts are about wording, not data). Reviews moved from 6/6/7 to 7/7/7, and no reviewer disputes the core: C1 = +0.71 at 8 queries, BB-64 matches at 64.
2. What remains is labels that run ahead of the evidence in four places all three reviewers name. (a) Contribution 2 tags the 16-64 bracket [pre-registered], but Open-8 vs BB-16 is an exploratory run-level test (item level: 4 higher, 2 tied, sign p = 0.125). (b) The judge study is a certification check, not "the same recipe" (§5, Contribution 5). (c) "Errors become omissions" rests on 1 GPT error (Haiku contributes 9 of the 10 `none` errors). (d) The trap paragraph presents an exploratory mechanism and privileged policies under a [pre-registered secondary] tag.
3. The one substantive gap reviewers still call major is what was valued. The design says arms "differ only in proxy access and exact-query budget", but proxy access includes approximate scoring of the agent's own texts (median 1,921 texts per run), which black-box forward units cannot buy. The draft concedes this in §4.2 and §7. It must also say so in §3 and in the reconciliation (§5), and it must stop calling those encodings "free".
4. There are small factual slips a careful reader will catch. BB-16's cost includes the pilot ($0.89, not $0.92, per pass). "Within 60 s" has no reference point. The attr16 control (1/6 reward) is confused with the τ reference. The disclosed tells say "unused" when agents do reason from the band. Table 1's "independent re-implementation" overstates it.
5. Reviewers (and the relayed user request) ask for directions and arm combinations beyond the four arms. New runs are out of scope, so answer in words: a compact factorial of what the released environment supports (budget × proxy type × error depth × agent), plus Appendix H items reviewers named that are not yet listed (§5 below). Format is also a risk: the body is about 3,900 words plus a box, three tables and a figure, which is about 6 AAAI pages, not the "about 4" the header claims.

## 2. Prioritized fixes (12; wording and existing-data analysis only; requests for new runs become wording)

Deltas are expected changes to the mean review score. They overlap, so they do not add linearly.

### F1. Abstract, title and Contributions: put the scope and labels where reviewers read first  (+0.3; R1, R2, R3 major/minor; C3, C6, C12)

- Title (drops "Interpretability Tools as", which all three reviewers say leans on interpretability):
  > **What an SAE View Saves an Auditing Agent: Valuing a Fallible Proxy Against Scarce Ground Truth**
- Abstract, full replacement:
  > Interpretability tools are usually valued where the agent does not choose where to spend ground truth; we value one against a scarce, adaptively spent budget. In ShiftHunt, a model-auditing environment with a closed-form grader, an agent must name the spurious cue a linear probe relies on, using a fallible SAE view (the proxy) and a few exact probe queries (gold). In a pre-registered study with all other budgets matched, GPT 6.1 Terra names the hard cue in 23/24 runs with the proxy and 6/24 without it at 8 queries (+0.71, Holm p = 0.0002; higher on all six items). Without the proxy, 16 queries give 16/24 and 64 give 24/24. For this agent and these items the proxy therefore stood in for between 16 and 64 exact queries (about 36 by exploratory interpolation; 95% interval 21 to beyond 64). Traces suggest triage: as many exact tests, moved onto the proxy's top candidates, and wrong named cues fall from 15/51 to 0/71. The proxy's errors here are shallow (on traps the truth is its second choice), and a second agent shows no reliable gain. An LLM judge checked against the same certified grade agrees with it at chance (κ = 0.002). We recommend reporting tool ablations as budget curves with a break-even gold price.
- Contribution 2:
  > **The budget curve** (§4.1): +0.71 at 8 queries [pre-registered]. Two no-proxy arms, each pre-registered (BB-16, BB-64), place the crossing between 16 and 64 queries [comparison exploratory], about 36 by interpolation [exploratory].
- Contribution 3, last clause: "…and nearly removes wrong named cues" (replaces "turns wrong named cues into omissions").
- Contribution 5:
  > **A reporting rule** (§5). Its first step, certifying a proxy against gold on planted items, is applied to a second proxy, an LLM judge, which fails it [pre-registered].

### F2. The surrogate channel: state it in the design, drop "free", and mark the reconciliation as interpretation  (+0.3; R1, R2, R3 major; C7)

- §3 "Matched budget", replace the last clause "arms differ only in proxy access and exact-query budget" with:
  > Arms differ in proxy access and exact-query budget. Proxy access includes approximate scoring of the agent's own texts (gradient times latent encodings, wrong only by the SAE error term). In black-box arms the same forward units can score only sample notes. The budgets are matched in units, not in what the units buy, and what we value is this whole channel.
- §4.2 "What the proxy was used for", full replacement (C7 fix):
  > **What the proxy was used for** [exploratory]. GPT used the proxy heavily as a source of approximate experiments outside the exact-query budget. Per Open-8 run it passed a median of 1,921 agent-supplied texts through the SAE (range 1,620–2,450, repeats counted; median 32 calls; each text costs one of 3,000 forward units), against 8 exact texts; Haiku passed 843 (392–1,800). GPT read latent meanings in 21/24 runs, and reading them was not associated with passing (20/21 vs 3/3). We therefore claim value for the SAE view as deployed, not for sparsity or interpretability as such.
- §5, after "We add adaptivity and a proxy whose short list contains the truth.", add:
  > This reconciliation is an interpretation, not a measurement. Without a non-SAE proxy with matched error, we cannot say whether the value lies in the SAE's sparse semantics or in its approximate-scoring channel.
- §7 "What was valued": "The SAE view as deployed, its own-text scoring channel included. No non-SAE proxy arm was run, so the comparison with the SAE-null literature is an argument, not a result."

### F3. Judge study: certification, not the recipe  (+0.25; R1, R2 minor; R3 strength; C12)

- §5 "A second proxy", full replacement (C12 fix):
  > **A second proxy** [pre-registered]. The recipe's first step, certifying a proxy against exact gold on planted items, applies to a second proxy–gold pair. An LLM judge (GPT 6.1 Terra, one call per run, reading the agent's messages and answer) agrees with the certified grade at chance on the score-deciding hard slot (κ = 0.002 over 214 runs; J1 predicted κ < 0.40; per agent κ −0.09 to 0.08). It credits 53/68 certified-failed hard slots (J2), 41 of them `none` answers (J3, descriptive). The failure is specific: on null probes, where `none` is right, κ is 0.45. Unlike the SAE view, this proxy cannot stand in for gold. In prediction-powered terms, a proxy at chance agreement saves an evaluator few or no certified grades; whether it could guide where gold is spent was not tested (one judge model, one prompt).
- §2, after Table 1's paragraph, add one clause: "(a report-reading LLM judge, by contrast, agrees with this grade at chance on the hard slot; §5)". The CFP's motivation is judge reliability (AstaBench τ = 0.467), so this is the cheapest CFP-fit gain in the paper.

### F4. The trap paragraph: separate pre-registered, exploratory and offline  (+0.15; R1, R3 major on error depth; C4)

Replace §4.1 "The value survives where the proxy's top pick is wrong" with the C4 fix:
> **For GPT, the value survives where the proxy's top pick is wrong** [pre-registered secondary]. Trap C1 = +0.75 (11/12 vs 2/12; unadjusted run-level p = 0.0012, conditional on the three trap items; item-level floor 0.25). The pre-registered prediction BB-8 traps ≥ Open-8 traps failed, in the direction of C1 (0.17 vs 0.92). [Exploratory] Where it succeeded, the capacity went to a short list that contained the truth. GPT isolated the proxy's rank 2 on 11/12 Open-8 trap probes, the same runs that passed (on traps, isolating rank 2 means exact-testing the true cue). The widening was targeted: 23/24 trap probes vs 5/88 ordinary ones. [Offline, privileged] On traps, testing rank 1 only scores 0.00 and testing ranks 1–2 scores 0.96. All shipped trap errors are at rank 2. With the [main] simulated at rank 3 or lower, a fixed top-two policy scores 0.00 (by construction) and a screen-first policy 0.46–0.56. The exchange rate is therefore measured for shallow errors only.

### F5. The crossing: tags, item-level floor, non-interleaving  (+0.15; R2 major; R3 major; C3)

Replace §4.1 "Where the curves cross" with:
> **Where the curves cross.** BB-16 = 16/24, and Open-8 lies above it (exploratory: run-level Fisher p = 0.023; item level, higher on 4 items and tied on 2, sign test p = 0.125). Open-8 matches BB-64, so the crossing lies between 16 and 64 exact queries. A logistic fit of NAME on log2(budget) over BB-8/16/64 reaches Open-8's 0.958 at about 36 queries (item-bootstrap 95% interval 21 to beyond 64) [exploratory]. The interval does not include Open-8's own uncertainty (Wilson [0.80, 0.99]), which would widen it. BB-16 ran a day after Block 1 and was not interleaved with Open-8. The pre-registered descriptive trend test over 8/16/64 gives Cochran–Armitage p = 1.1e-6.

§5 Recommendation, last sentence: "becomes 'is the SAE view cheaper than about 8 to 56 exact queries beyond the 8 the agent already had?'" (R1 nitpick: makes 16−8 and 64−8 explicit).

### F6. Mechanism wording: triage as allocation, the 60 s reference point, omissions scoped  (+0.15; R2 minor and nitpick; R3 nitpick; C5, C6)

- §4.2 item 2, second sentence, replace with (definition from `followup_failure_modes.py`: all `probe_query` calls within 60 s of the first):
  > The hard probe gets 3.58 of 8 texts with the proxy and 2.08 without (means). In 24/24 Open-8 runs GPT sent all its exact texts within 60 s of its first one, against 0/24 BB-8 runs. The allocation was fixed from the proxy before any gold result could inform it.
- §4.2 item 3, full replacement (C6 fix):
  > **Wrong named cues nearly vanish.** Wrong cues among named planted-probe answers fall from 15/51 to 0/71 for GPT (p = 5.2e-7) and from 9/24 to 1/27 for Haiku (p = 0.0036). These are answer-level tests. At run level, GPT named a wrong hard cue in 8/24 BB-8 runs vs 0/24 Open-8 runs (p = 0.004). The few errors left with the proxy are omissions: 10 of 11 are `none`, 9 of them Haiku's (vs 33/57 without the proxy).
- Appendix F definition: "**Commission**: a named answer containing a cue that identifies no main cue (15/51 includes one answer with a correct cue plus an extra one)."
- Appendix B held-out paragraph, replace "Limits: …" with:
  > Limits: it uses the same trap items, with 10 of its 15 November runs at a 4-text budget. 12 of the 15 runs had been read before the freeze for their trap probe only (no other probe had been coded). Its companion spare-text prediction failed.
- §4.2 heading stays "Mechanism: triage, not more exact tests [exploratory; GPT, matched 8 queries]". The body describes allocation, so "triage" names a pattern, not a cause. Add one clause to item 2: "this is an allocation pattern defined after the data; the surrogate channel (above) may also contribute".

### F7. Grader section: exact denominators, tells as used, the attr16 control explained  (+0.15; R3 minor "SHIFT nominal", "1/6 unexplained"; R3 nitpick; C11)

- Table 1, row 1: "All 100 counted open-access runs (64 main-study + 36 Open-8), own latent permutation | 100/100 runs, 400/400 probe records; a second frozen regrade script recomputing the closed-form rule agrees on every slot".
- Table 1, row 4: "86/86 cross-model rollouts coded clean (one unblinded LLM reading); 0 web or subagent calls in 2,221 Claude tool calls".
- Table 1, header note: "[pre-specified checks; positive control added after the first run, logged]".
- §2, replace "Removal is a real gate (…) Two information tells, unused by any Block 1 run, are disclosed in Appendix B." with:
  > Removal is a real gate. The true regex with the 16 latents of largest public-sample attribution names 6/6 but earns reward on only 1/6 items. Those latents are not the per-cue reference that sets τ, which is computed on notes where properties vary independently; the public sample confounds them. τ = 0.40 also leaves only 6 of 36 Open-8 hard passes. At the shipped τ naming decides: 176/176 correctly named main-study cues passed removal and keep. We disclose two information tells (Appendix B). A free sample-logit midpoint marks 2 of 3 trap hard probes; none of the 108 Block 1 runs used it, and the earlier main-study runs were not checked. A band inference from the 0.3/0.15 contract is legitimate reasoning that agents sometimes use (three main-study passes), but it fails as a whole-episode policy (false claims on 0.272 of ordinary bank probes).
- Appendix B "Disclosed information tells", same two sentences. This also removes the self-contradictory "no Block 1 run used it (main-study runs unchecked)" (R3 nitpick).

### F8. Reference policies: move the hint caveat into the body  (+0.1; C8)

Replace §4.3 sentences 2–3 ("At least 65% … n.s.") with:
> Reading the two-part method hint as procedural, at least 65% of C1 lies beyond every privileged no-proxy policy played on the stored readings (73% beyond the best tracked policy, 0.44), and 36% lies beyond the noiseless group-testing optimum (0.703; 0.497 and 0.703 are untracked simulations). If the hint is read as a prior pointing to the nested property, a privileged policy reaches 0.92 on two-part items with 4 texts and the share falls to about a third. GPT BB-8 is 0.15 below the 0.40 reference (P = 0.095, n.s.; the pre-registered BB-16 test was inconclusive, P = 0.086).

Keep the last two sentences ("Since GPT BB-64 exceeds…", "They locate skill gaps…").

### F9. Costs: correct BB-16, give the break-even an interval, price the proxy's compute in one formula  (+0.1; R2 minor; R3 minor; C9)

**New, existing data** (`d7/calc/breakeven_boot.py`, rows_r1112.csv, counted GPT runs; exploratory). The break-even gold price is $0.0060. The 95% interval is $0.003–0.010 from an item bootstrap (six items, 10^4 resamples) and $0.004–0.008 from a run bootstrap. The SAE's own compute is unpriced. Open-8 made 47,902 own-text encodings over 23 passes, which is 2,083 per pass, against 55.6 fewer exact queries per pass than BB-64. At c dollars per SAE encoding the break-even therefore rises by about 37c.

- §4.4 second paragraph, replace with:
  > Pricing a gold query at p, a GPT NAME pass costs $0.71 plus 8.4 queries with the proxy, $0.89 plus 24 at BB-16, and $0.37 plus 64 at BB-64. Among the arms run, the proxy arm is cheapest per correct answer whenever a gold query costs more than about $0.006 (item-bootstrap 95% interval $0.003–0.010; list prices assumed). It dominates BB-8 and BB-16 at every price. The SAE's own compute sits inside the matched forward units and is not priced. At c dollars per SAE encoding, the break-even rises by about 37c (2,083 encodings per pass), which stays far below the price of a real experiment for any plausible c.
- Appendix F, BB-16 row: "0.59 | 0.89 | 24.0" with the note "counted runs; the $14.64 arm total includes the $0.45 pilot". §8: "BB-16 $14.19 (plus a $0.45 pilot)".
- Optional clause after the token medians in §4.4: "BB-8 also used more input tokens and dollars per run (median 5.1M vs 4.1M; mean $0.97 vs $0.68)".

### F10. Scope "plentiful gold" and the second agent to what was measured  (+0.1; R2 minor on non-inferiority; R3 minor on Opus/Sonnet; C2, C10)

- §4.1 "Plentiful gold", replace with (C2 fix):
  > **Plentiful gold.** With 64 queries, GPT's black-box agent no longer needs the proxy: BB-64 = 24/24 (C2 = +0.75, Holm p = 0.0002). BB-64 − Open-8 = +0.04 [0.00, +0.17] lies within the pre-registered −0.20 non-inferiority margin, so the rule returns "with plentiful exact tests the SAE is not needed". With a significant C1, that is the pre-registered reading "the SAE acts as testing capacity". (Both arms are near ceiling. The lower bound of 0 holds by construction, and a non-pre-registered Newcombe interval is [−0.10, +0.20].) The proxy's own value at 64 queries was not measured, and the statement is GPT's: Haiku does not recover on two-part items at 64 (2/6, vs 5/6 with the proxy at 8; descriptive).
- §4.5, three edits (C10):
  1. "The proxy is descriptively ahead on two-part items (5/6 vs 1/6, Fisher p = 0.08) but not on traps (0/6 vs 2/6)."
  2. After "(p = 0.11)": "[exploratory; run-level; item-level floor 0.25 with three trap items]". Name the source once: "Opus 5.5 and Sonnet 5.5 in the earlier open-access cross-model study (same items and harness)".
  3. §7 and Appendix G, Luna: "pre-registered and running; no outcome computed before the last counted run; no claim depends on it." Do not print a progress count; it will be stale by submission.

### F11. Format and density: the "short paper" header is not true, and the CFP lists 6–8 page papers  (+0.15; R1, R2, R3 nitpicks; risk of desk issues)

- The body (§1–§8) is about 3,900 words plus Box 1, Tables 1–3 and Figure 1. In AAAI two-column format that is about 6 pages, not 4. BRIEF's CFP lists only full papers of 6–8 pages. Change the header to "Full paper (6 pages, references and appendix excluded)", or verify that a short track exists before keeping "short".
- Replace the §5 "Recommendation" paragraph with **Box 2, "Valuing an agent's tool: the recipe"**, six numbered lines (R1's request; a practitioner can copy it):
  > 1. A no-tool arm at two or more gold budgets, every other budget matched (as Pando does). 2. Items on which the tool is certifiably wrong. 3. Logged adaptive gold queries, to show allocation by tool rank. 4. Privileged reference policies at each budget. 5. Cost per correct answer as a function of gold price, with the break-even price. 6. Results per agent.
- Move the Table 3 p-values sentence and the "Process check" paragraph to Appendix B. Keep one sentence in §4.2: "Wherever GPT varied the true cue cleanly it named it (39/39 across Open-8, BB-8 and BB-64)".

### F12. "Beyond the four arms": one factorial, plus the combinations reviewers named that Appendix H lacks  (+0.2; relayed user request; R1 major on one proxy point, R2 and R3 to-raise lists)

Replace §5 "Further arms" with:
> **Beyond these four arms.** The released environment makes the exchange rate a function rather than a number. Its axes are the gold budget (Open-0/2/4/16, BB-32), the depth of the proxy's error (the [main] at rank 3–8, decoy inflation 1–3×), the proxy (shuffled-rank placebo, surrogate-only vs semantics-only tools, a matched-error dense surrogate, a transcoder, two SAEs at different widths), the agent and harness (crossed, not nested), and the price and noise of gold. Reference policies already predict parts of this surface: 0.50 at 0 queries, and a collapse of the top-two policy to 0.00 at rank-3 errors against 0.46–0.56 for screening. A pre-registered second model in GPT's harness (GPT-6 Luna; 36 vs 24 runs at 8 queries) is running. Appendix H lists each setting.

Append to Appendix H (items reviewers named that are not listed now; none is claimed):
> 8. *Agent-chosen budget*: gold sold at a stated price, with the agent deciding when to stop. This measures allocation and stopping, and makes the break-even price a behaviour.
> 9. *Combined proxies*: SAE plus a transcoder or attribution graph, or SAE plus an LLM hypothesis generator. The question is whether proxies with partly uncorrelated errors complement each other.
> 10. *Tool × agent capacity*: Haiku at Open-16 and BB-16, to tell a shifted curve from a flat one.
> 11. *Full model × harness crossing*: GPT in Claude Code and Claude models in Codex.
> 12. *Naturally occurring cues*: a probe whose SAE miss arises without weight edits, and a generated item bank scored with an IRT model, so the rate becomes a function of item parameters.
> 13. *An automated SHIFT baseline*: attribution top-k latents plus auto-interpretation mapped to a regex, with no agent, at 0 and 8 queries, reporting achieved removal and keep.
> 14. *Outside interpretability*: a low-fidelity simulator or LLM reviewer as the proxy and an exact experiment or held-out replication as gold.

## 3. Nitpicks to ignore (or answer in one clause at most)

- A GLMM or item random-effects model for the crossing or Table 3. Six items do not support it, and per-slot allocation data are not committed. F5's item-level sign test and F6's run-level check are the proportionate answer.
- The judge being the same model as the confirmatory agent. One clause at most: GPT's hard-slot κ (0.08) is the highest of the four agents anyway.
- "Transfer to AI-scientist tasks is asserted". One sentence in §7 is enough: "Every number comes from one audit environment with an enumerable hypothesis space; F12 (14) names the test." Do not expand the motivation.
- A full comparison with SHIFT's protocol, or achieved-removal tables. F7's attr16/τ sentence answers the "SHIFT is nominal" point. The rest goes to Appendix H (13).
- Proper dollar pricing of SAE compute. The 37c formula (F9) is enough.
- Power analysis for Haiku. It was pre-registered as descriptive; say so.
- Contamination of public items. Already in Limitations.
- "Holm p from a within-item permutation does not generalize across items". The abstract now adds "higher on all six items" (F1), and §4.1 gives the sign-test floor. Nothing more.
- The `PREREG_BB16.md` header still says "DRAFT … NOT hashed" in the repo. The repository is read-only. Do not mention it in the paper; the hash and commit establish the timing.

## 4. New in updates/ (round_9_manual_1112T0830Z.md, newest; supersedes round_2)

- **Judge J1–J4: complete** (κ = 0.002 on hard slots; 53/68 false credit; 41/44 `none` failures credited; null-probe κ 0.45; $1.97; all November data). Draft_r2 already uses J1/J2. Changes: reframe as certification (F3), add the null-probe contrast, and cross-reference it from §2. The deviation log (budget guard raised from $4 to $10; one resume after an interruption, design unchanged) belongs in Appendix G as one clause.
- **GPT-6 Luna: about 24 of 60 counted runs, no outcomes computed** (prohibited before the last counted run). The draft's "running; not used here" is correct. Section text for when it lands: L3 supported means the proxy's value at 8 queries reproduces on a second model in the same harness. If L3 is not supported, the value is model-specific within one harness, which turns "a tool's value is a property of the agent" into a pre-registered finding. Either outcome removes the harness confound for the second agent. It is the largest remaining score lever (§6).
- The Terra validation reproduces 23/24, trap NAME 11/12 and trap rank-2 isolation 11/12, which matches the draft.
- No [OCT] material in the new files. The draft has no [OCT] numbers or [OCT-CHECK] marks left. Keep it that way: the held-out R2/R3 and R5 confirmations pool October H3 runs, so do not add them.

## 5. Directions and combinations beyond d1–d4 (relayed user request: "explore maybe more directions or combos … outside the 4")

"The 4" is read here as the four drafted directions d1–d4. The reviewers read it as the four arms, which F12 covers. This direction (d7) is already outside d1–d4. The options below cost no runs.

**Combinations that strengthen d7 directly**
- **d7 + judge ("two proxies, one certification")**. This is the strongest combination. The SAE view passes certification against gold and saves gold. The LLM judge fails certification (κ = 0.002) and cannot stand in for gold. One recipe yields opposite verdicts, which hits the CFP's motivation (judge reliability, AstaBench τ = 0.467) and its "ground truth stronger than reviewer opinion" theme. It needs only F3 plus a two-row summary table in §5.
- **d7 + d3 (budgeted search)**. The curve's shape has a formal counterpart in Bayesian fixed-budget best-arm identification. An informative prior helps at finite budget, and the gap closes as the budget grows (Atsidakou et al., L2 §4.1): C1 is significant at 8 and gone at 64. One clause in §5 plus a reference. No formalism.
- **d7 + d1 (environment)**. If the loop picks d1, d7 becomes its showcase experiment (§4 of d1) and Box 2 becomes d1's "how to use the environment" recipe.

**New directions not yet drafted (beyond d1–d4 and r1's N1–N3)**
- **N4 "Certified ground truth for evaluating evaluators"**. ShiftHunt's closed-form grade serves as gold for meta-evaluating report-reading judges of research agents. Its findings: the judge is at chance on the score-deciding slot, it fails specifically on confident "nothing found" reports (41/44), and it works where `none` is right (null κ 0.45). It connects to agents' own failure mode (omission under a proxy, F6). It fits CFP "LLM-as-judge reliability" squarely. Data are complete and November-only. Risk: one judge and one prompt, so present it as a pre-registered case study.
- **N5 "The exchange-rate surface: a registered report"**. A proposal-format paper that pre-registers the F12 factorial (budget × error depth × proxy type × agent), with this study as the pilot that sets effect sizes and power. It fits CFP "statistical power / sample-efficient evaluation". It is honest about being a plan, and it is the natural home for the user's "more combos" wish if the workshop accepts proposal-style submissions (to be checked).
- **N6 "Where agents spend gold"**: allocation as the evaluation target. The 60 s one-burst fact (24/24 vs 0/24), rank-prefix allocation and targeted widening (23/24 trap vs 5/88 ordinary) become a process-level metric (P(isolated | proxy rank)) proposed for any proxy-plus-gold agent benchmark. This overlaps d2 and d4, so use it as a section of d2 rather than a separate paper.

## 6. Ceiling

- Current reviews: 7 / 7 / 7 (rigor 8 / 8 / 7; CFP fit 7 / 8 / 8).
- With F1–F12 (wording and existing data only): **about 7.4 (range 7.2–7.6).** The largest gains are F1 + F2 (labels and the surrogate channel, raised as major by all three reviewers), F3 (judge as certification, the cheapest CFP-fit gain) and F12 (the user's request, and R1's main complaint as far as words can answer it).
- **About 7.7** if Luna L3 reports before 20 Nov, in either direction: it adds a second confirmatory agent without the harness confound.
- **8** needs new arms: at least one of Open-4/Open-16 (a second proxy point, making two curves), a rank-3 trap, or a matched-error non-SAE proxy. Out of scope now.
- Structural cap: six items with shallow (rank-2) proxy errors and one confirmatory agent. However it is worded, this is a careful, pre-registered case study with a transferable reporting recipe, not a law about SAEs. Present it as exactly that.
