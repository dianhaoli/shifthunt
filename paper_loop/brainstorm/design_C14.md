# design_C14: past rank 2 and off the public items (rank-6 bank traps + fresh rank-2 traps, Terra and Luna, certified and judged)

Mini pre-registration for the GPU-box agent. Written 12 Nov 2026 by the designer; nothing here has been run.
The agent copies §§1-7 into `results/blackbox_1112/c14/PREREG_C14.md` and commits its sha256 (with the run
orders, the wrapper and the analysis driver) **before the first counted run**. Pilots may run before the hash.
Rule check: items are named only by episode id or by a neutral label (R6-a/b/c, F2-a/b/c). No cue property is
written anywhere in this file, in the prereg or in public outputs; per-item cue rows stay in `results/private_1112/c14/`.

Timeline: Step 0 checks and fresh build 13 Nov; freeze by 14 Nov 15:00 UTC; runs 14-15 Nov; analysis and
judge 16 Nov; paper text 16-17 Nov. Hard stop for any new data: 17 Nov 23:59 UTC.

---

## 0. What I checked in the sources (branch `origin/claude/serene-fermi-pog4k7`)

- **The rank-6 traps exist, but they are a different trap construction from the shipped ones.**
  `exp_c/exp_c.json` → `trap.all.fixed.top_candidate.distinct_instances.main_rank_counts` = {1: 11, 2: 10, 6: 3},
  and every rank-6 instance is in pool `knob_trap_s` (`by_pool.knob_trap_s...main_rank_counts` = {1: 4, 2: 1, 6: 3};
  all-instance count for rank 6 is also 3, so exactly three bank episodes carry one each). `knob_trap_s` is the
  first trap knob (`knob.name = "trap"`, `lat_scan` 0.17-0.22, `gamma` 0.6-0.8, no planted decoy). The shipped
  traps come from `knob_trap_s3`, built by `scripts/knob_trap3_build.py`, which adds a **sign-aligned SAE decoy**
  to a `knob_trap_s2` base. Profile in `knob_trap_s`: the main's |latent ratio| has min 0.097 and median 0.23;
  the best non-main reads up to 0.69, with true |ratio| up to 0.18 on the 32-base scan. The shipped traps read
  0.17-0.24 for the main and 0.33-0.40 for the [decoy]. **Consequence:** the rank-6 cell changes both depth and
  construction. It can show "does not search deeper on these items". It cannot attribute that result to depth
  alone. The write-up says this.
- **Sign-aware ranking may promote one of them.** `knob_trap_s` top-candidate correct is 4/8, sign-aware 5/8. So
  one `knob_trap_s` instance has the main at rank 1 once wrong-sign candidates are dropped, and it could be a
  rank-6 one. Agents see the sample's signs, so the sign-aware rank is the one that matters (gate G1).
- **Two rank definitions are in use.** exp_c ranks by |latent ratio| on the stored paired scans.
  `luna_analysis.py` / `followup_failure_modes` rank by `FM.proxy_ranks` on `followup/solvers/band.json` (5-seed
  mean |SAE flip effect|), which is what Table 3 and L1 use. They have not been compared on these three items (G1).
- **Why the proxy_verify bank table shows only rank 2.** `proxy_verify/README_bank.md` has 46 episodes, of which
  6 are traps, all rank 2 (`knob_trap_s3`). Its NOTES ("no rank-3 item exists") refer to that scope. The trapsolv
  episodes (`results/knobs/trap_solv/episodes_bank_trapsolv.json`: ep221-ep242, ep301-ep308) evidently do not
  count as trap episodes there, perhaps because the trap is not their required probe. **Lead, not a confirmed
  mapping:** ep221, ep224 and ep227 have `s1_trapslot = 0.0` at every threshold, which is what a rank-6 trap would
  give a top-k scripted solver. G1 settles this from `results/private_1112/exp_c/exp_c_rows.jsonl`.
- **Fresh rank-2 traps of the shipped construction can be built.** `knob_trap3_build.py` used
  `BASES = (planted_003, planted_009, planted_011, planted_012)` of `knob_trap_s2`. Three were accepted, and those
  are the shipped traps. `knob_trap_s2` has 7 more probes (000, 001, 002, 006, 007, 008, 010) whose manifests have
  no failures, and none of them has ever received a decoy edit. Cost on the box: `encode` takes about 4 min of GPU
  per base and `fit` runs on CPU. `knob_trap3_episodes.py` then picks seeds that keep the decoy sign-aligned and
  has `--check` for grading-level checks. With the original yield of 3/4, about 5 of 7 should pass.
- **Fallback fresh-ish items need no rebuild.** `knob_trap_s3` has 6 distinct slot instances in the bank. Three are
  shipped; the other three are the **same three probes** in other episodes (other sample, aligned set and signs),
  already in the image. They are "new episode, same probe". They are not fresh.
- **Image.** The bank is baked into the base image `rl-task-shifthunt-r1103`, and r1112 is a thin layer
  (`docker_research_bb/README.md`). Bank episodes are therefore in the image already and only need PROBLEM
  entries (`blackbox_sync_private.sh` → `problems.txt`). Freshly built episodes need a new layer, built and
  checked by `docker_research_bb/build.sh` + `scripts/blackbox_image_check.py`, with ITEMS extended.
- **Run, analysis and judge tooling exist.** `scripts/luna_schedule.py` wraps the unedited `blackbox_schedule.py`
  and has an arm cap. Luna's 60 runs took about 6 h of wall clock and cost $6.04 ($0.08-0.13 per run).
  `luna_analysis.py` builds slots, tested ranks and the allocation curve, and has `validate`.
  `judge_vs_grade.py` holds the frozen L0 judge, but its `BATCH_RE` excludes any new batch name (one-line change).
- **Reference numbers this design compares with.** Shipped traps: Terra rank-2 isolation 11/12 and NAME 11/12;
  Luna 0/18 and 1/18 (`luna.json`). Rank-placement counterfactual (`README_bank.md`): top-two 0.00 at r = 3..8,
  complement-screen hedge 0.57 at r = 6 (additive back-end, topic unit). Tells (paper App. M): midpoint |m| ≤ 2.38
  on non-trap probes; gap tell r 0.41-0.58 on shipped traps; AUROC 0.84 on bank traps.

---

## 1. Question

Claim 3 says Terra widens to the proxy's runner-up on the trap and Luna does not. That claim rests on three public
items, and on all three the truth sits at proxy rank 2. Two questions are open:

- **Q1 (validity off the public items).** Does the Terra-vs-Luna widening contrast hold on rank-2 traps of the
  same construction that no agent has seen?
- **Q2 (depth).** When the truth sits at proxy rank 6, does Terra search past the top two (wide search), or does
  it stop at two and answer as if the search were done (a one-step habit)?

A third question comes almost free. **Q3:** does the frozen report-only judge credit the new failures as it did
before (Claim 2 on items it has never seen)?

## 2. Items

| cell | label | source | n items | in image? |
|---|---|---|---|---|
| R6 | R6-a, R6-b, R6-c | the 3 bank episodes holding the `knob_trap_s` rank-6 instances (ids fixed in G1) | 3 | yes |
| F2 (plan A) | F2-a, F2-b, F2-c | new `knob_trap_s3`-construction traps from unused `knob_trap_s2` bases, in new episodes built with the shipped composition (trap + near-threshold + easy + null) from non-shipped ordinary and null sources | 3 | new layer |
| F2 (plan B, fallback) | F2-a′, b′, c′ | the 3 non-shipped `knob_trap_s3` bank instances (same probes as the shipped traps, new episodes) | 3 | yes |

- **F2 base choice (plan A).** Run `encode` and `fit` on all 7 unused bases. Keep the accepted ones that meet two
  conditions: (i) the main is at rank 2 by both rank definitions and sign-aware; (ii) where possible, the main
  property differs from all three shipped traps' main properties, so a model that memorised the public answers
  gains nothing. The agent checks (ii) privately and records only "differs: yes/no". Take the first 3 in base order.
- **Episode composition (plan A).** One trap (the required probe), one `knob_nearnull` near-threshold probe, one
  easy `build_screen2` probe and one null probe. None of their sources may come from a shipped episode. Seeds come
  from `knob_trap3_episodes.py` (range 3300-3999, decoy sign-aligned). The hidden grids get a **new salt**
  (stream tag `c14`). Canary string as in the shipped items.
- **Never-seen check (all cells).** Grep every stored rollout's `/srv/episode_id` (main study, Block 1, BB-16,
  Luna, October batches) for the new episode ids and source ids. There must be 0 hits.

## 3. Step 0 gates ($0; done and committed before the hash)

| gate | check | rule |
|---|---|---|
| **G1 rank** | For each R6 slot: main rank under exp_c (|latent ratio|), under band.json (`FM.proxy_ranks`), and sign-aware under both. Also the proxy readings (topic units) of ranks 1-6, with no names. For F2: the same, on the built episodes (run `followup_band.py` and `sae_view_stats.py` on them). | An R6 item enters the depth analysis only if the main is at sign-aware band.json rank ≥ 3. Otherwise it is reported in a separate "bank rank ≤ 2, old construction" row and **not replaced**. An F2 item needs rank 2 under every definition. |
| **G2 composition** | Probe count and kinds, which probe is required, budgets (150 calls / 3000 forward / 8 texts / 3600 s), hint section absent, `/task.txt` diffed against ep411's for the same arm | Deviations are listed. If the trap is not the required probe (likely in trapsolv episodes), the agent cannot know this because the prompt is identical, so all R6 metrics are **slot-level** on the trap probe and run-level NAME is reported as secondary. |
| **G3 certification** | `blackbox_image_check.py` with ITEMS + new ids: oracle open-arm full pass, `none`-all scores 0, budget enforced, fulltext written. `scripted_cheaters.py` scores 0 on every new episode. The greedy oracle reaches the removal threshold on the trap slot. Shipped items still give `same_as_r1103` in the new layer. | An item failing any check is dropped. Below 2 R6 items, the R6 cell is cancelled. Below 3 F2 items under plan A, switch to plan B. |
| **G4 tells** | Free sample-logit midpoint m per probe. Gap tell r = proxy share of the free sample gap per probe. Is the trap's (1 − r) the episode's maximum? | Items are flagged, never excluded. Results are shown with and without flagged items. |
| **G5 scripted references** | `proxy_verify.py --episodes <new ids> --exact require --seeds 2000`: top-one, top-two, complement-screen hedge (SAE order, unfinished→none), plus the blind policy | Committed before any agent run (this is C23's job for these items). An R6 item where top-two names the trap with probability > 0.05 is not a depth test; it is reclassified as in G1. |
| **G6 pipeline** | One **Luna** Open-8 pilot per new item (6 runs, excluded). Check: status ok, fulltext.jsonl present, grade.json written, the slot builder resolves every trap candidate's rank. `c14_analysis.py validate` reproduces the stored Terra 11/12 / 11/12 / 23/24 and Luna 0/18 / 1/18 on the old batches. | A pipeline failure is fixed and re-piloted before the hash; nothing is fixed after it. |

**Go / no-go (14 Nov 15:00 UTC).** R6 runs if at least 2 items pass G1-G3. F2 uses plan A if 3 items pass G1-G3
by then, otherwise plan B. If B also fails, F2 is dropped and the paper keeps today's §9 sentence. The decision
and the reason go into the prereg before the hash.

## 4. Runs

- **Agents:** `gpt-6.1-terra` and `gpt-6-luna`, Codex CLI, CODEX_EFFORT=max, Block 1's launcher via a new
  wrapper `scripts/c14_schedule.py` (a copy of `luna_schedule.py` with items, agents and seed changed). One arm
  only: **Open-8** (with the proxy, 8 exact texts). There are no no-proxy arms, because Claim 1 is not under test.
- **Counted runs:**

| stage | Terra | Luna | condition |
|---|---|---|---|
| 1 (core) | 2 per item × 6 items = **12** | 3 per item × 6 = **18** | always, after go |
| 2 | +1 per item = **6** (total 9 per cell) | none | only if, after stage 1, OpenAI spend across C6, C8 and C14 leaves at least $8 of the original $34, **and** Terra's stage-1 mean is ≤ $0.95/run |

- **Order:** replicate-major, seeded "c14-1114". Replicate 1 for all 6 items and both agents (shuffled), then
  replicate 2, and so on. A stop at any point therefore leaves every item with the same number of runs, ±1.
- **Run rules:** Block 1 §7 unchanged. Re-run only when there is no accepted submission, at most 2 re-runs per
  item and agent, at the end of the queue. Timeouts and no-submission runs count as failures. A run with a
  submission is never re-run. No outcome is computed until the stage's last counted run is collected.
- **Judge:** the frozen L0 judge (`judge_vs_grade.py`, prompt sha `83afac63…`, Terra, one call per run) on every
  counted run. `BATCH_RE` gains `r1114_(gpt|luna)_c14(r6|f2)`; that is the only code change, committed before the
  hash. Guard: `--budget 1`.

## 5. Metrics (driver `scripts/c14_analysis.py`, frozen with the prereg)

All metrics are on the **trap slot** unless marked otherwise. "Isolated" means an edit-matched clean pair on true
logits, exactly as in `luna_analysis.batch_slots` / followup failure_modes. A text whose recovery fails counts as
not isolated and is listed.

1. **NAME_trap:** the trap slot passes naming (the certified grader's `naming_slot_pass`). Run-level NAME (every
   hard slot named, every null `none`) is secondary.
2. **iso(r):** the proxy's rank-r candidate is isolated, using the sign-aware band.json rank (exp_c rank in the
   appendix). Primary per cell: **F2: iso(2)**; **R6: iso(main)**, meaning the main at its own rank was isolated.
3. **Deepest rank:** the maximum r with iso(r) on the trap slot (0 if none). **Breadth:** the number of distinct
   aligned candidates isolated there.
4. **Group texts:** a charged text whose generator detectors differ from its nearest sample note (difflib ≥ 0.8)
   in ≥ 2 aligned properties. Count per run, and whether any such text targeted the trap probe.
5. **Allocation by rank:** Table-3 format (ranks 1 / 2 / 3 / 4+ on trap and on ordinary planted slots), plus texts
   per probe.
6. **Timing:** all 8 texts sent within 60 s (burst), and any trap-slot text sent after the first trap result
   returned (follow-up).
7. **Answer type on the trap slot:** main named / proxy rank-1 named / other wrong cue / `none`.
8. **Judge:** the verdict on the trap slot against NAME_trap. Reported: false credit k/n, false credit on `none`
   failures, and κ (descriptive).

Proxy-reading covariates are published for each item without names: head and runner-up readings, and the main's
reading, in topic units. This is the unscored "closeness" trigger from App. M.

## 6. Hypotheses and thresholds (written before any result)

Integer cut-offs are given for n = 6 (stage 1) and n = 9 (with stage 2). Every test is **run-level, conditional
on the three items**. Item-level evidence is reported as "k of 3 items" (one-sided sign-test floor 0.125,
two-sided 0.25). For each H, the outcome label is fixed by the thresholds below, whatever p-values come out.

| H | quantity | confirm | null / partial | reversal |
|---|---|---|---|---|
| **H1** fresh rank-2 replication | Terra NAME_trap on F2 | ≥ 5/6 or ≥ 7/9, **and** ≥ 1 pass on each of the 3 items | 3-4/6 or 4-6/9 | ≤ 2/6 or ≤ 3/9 |
| H1b (secondary) | Terra iso(2) on F2 | same cut-offs | | |
| **H2** within-harness gap off the public items | Luna iso(2) on F2 (n = 9) and Terra − Luna gap in iso(2) | Luna ≤ 2/9 **and** gap ≥ 0.50; one-sided Fisher reported | gap 0.20-0.49 | gap < 0.20 |
| **H3** depth (primary R6) | Terra iso(main) on R6 | **search:** ≥ 4/6 or ≥ 5/9, with ≥ 1 on each of ≥ 2 items | **partial:** in between | **habit:** ≤ 1/6 or ≤ 2/9, **and** deepest rank ≤ 3 in ≥ 2/3 of runs |
| **H4** how deep traps fail | share of Terra's failed R6 trap slots answered `none` | ≥ 0.50 (prediction: batch commitment leaves no text for follow-up) | | < 0.50 with rank-1 named most often (the "follows the head" mode) |
| **H5** judge on unseen items | judge credit on failed trap slots, Terra + Luna, all cells | ≥ 2/3 of `none` failures credited (if ≥ 6 exist), and false credit ≥ 0.5 overall | 0.34-0.66 | ≤ 1/3 of `none` failures credited |
| H6 (descriptive) | Luna on R6; burst; group texts; follow-up after refutation; allocation | tables only | | |

**Designer's prior** (recorded so that later reading can be checked): H1 confirm about 0.6; H2 confirm about 0.7;
H3 habit about 0.65, partial 0.25, search 0.10; H4 `none`-dominant about 0.6; H5 confirm about 0.75.

**Operating characteristics.** If Terra's true F2 rate is 0.9, P(H1 confirm at n = 9) = 0.95 and P(reversal) < 0.01.
At a true rate of 0.5 the probabilities are 0.09 and 0.25. If the true R6 rate is 0.05, P(habit cut-off) = 0.99;
at the hedge's 0.57, P(search cut-off) = 0.67. Wilson 95% for 0/9 is [0, 0.30]. One-sided Fisher of shipped
11/12 against fresh k/9 gives p = 0.39 at 7/9, 0.08 at 5/9 and 0.009 at 3/9.

## 7. Analysis rules

- The unit is the run, with the item fixed. No pooling of F2 with shipped items in any test. The shipped-vs-fresh
  contrast is a row-by-row table, with Fisher reported as descriptive.
- R6 items that G1/G5 reclassify are shown in their own row and never enter H3.
- G4-flagged items: every H is reported with and without them. The label is set on all items.
- Spend and deviations go into `RUNLOG.md`. Any deviation from §§2-6 is labelled `[deviation]` in the paper.
- Nothing in this study is called confirmatory in the paper unless it passes its cut-off. All of it is tagged
  `[pre-reg, descriptive, 3 items]`.

---

## 8. Cost and hours

| item | runs / calls | OpenAI $ |
|---|---|---|
| Step 0 (G1-G5), fresh build (encode about 30 min GPU for 7 bases, fit CPU), image layer + check (about 40 min GPU) | none | 0 |
| Luna pilots (excluded) | 6 | 0.8 |
| Stage 1: Terra 12 × $0.68-0.80 | 12 | 8.2-9.6 |
| Stage 1: Luna 18 × $0.10 | 18 | 1.8 |
| Judge, L0, about 36 calls × $0.0092 | 36 | 0.35 |
| **Core total** | | **about $11-12.5** |
| Stage 2: Terra 6 more | 6 | 4.1-4.8 |
| **Full total; hard cap in `c14_schedule.py` = $17.5** | | **about $15-17** |

Claude spend is $0. Hours: the agent needs about 6 h of attended work on 13 Nov (gates, build, image) and 6-8 h of
unattended runs (about 36-42 runs; Luna's 60 took 6 h). The author needs about 3 h: 30 min to read the prereg
before the hash, 30 min for go/no-go, and 2 h for paper text. The spend stop rule is the arm cap plus the stage-2
condition in §4. If Terra's first 4 counted runs average more than $1.10, Terra stops at replicate 2 even when
stage 2 was otherwise allowed.

**Budget interplay.** Core C14, C6 (about $5-8) and C8 ($0.55) together come to about $17-21 of the $34 left.
Stage 2 is the flexible part. If C6 runs, start C14 runs after C6's spend is known, or reserve $8 for it.

---

## 9. What goes into the paper under each outcome

**Body placement (8-page budget).** The new material is one paragraph plus **Table 3b** (4-5 rows) at the end of
§5.3, after the Luna paragraph. To make room:

- move the post-hoc scaling sentence ("Even after scaling by Luna's lower rate…", App. K) to the appendix (already
  on the reviewers' move list);
- shrink "Across harnesses, the Claude agents widen inconsistently" to one sentence;
- delete §3's counterfactual sentence ("The order reverses when the truth sits at proxy rank 3 or lower…"), which
  the measured R6 row replaces;
- in §9 "Items", cut the sentences "Each of those traps puts the truth at proxy rank 2… never run with agents"
  (about 4 lines).

Net change is about +2 lines, covered by moving the §4 multi-denominator example to the appendix (consensus fix 1).

**Table 3b. Off the public items: trap slot, Open-8** [pre-reg, descriptive, 3 items per row]

| items | proxy rank of truth | Terra: runner-up / truth isolated | Terra NAME | Luna isolated | Luna NAME | top-two / hedge [priv] | judge credit on failures |
|---|---|---|---|---|---|---|---|
| shipped (public) | 2 | 11/12 | 11/12 | 0/18 | 1/18 | 0.96 / 0.54 | Block 1 numbers |
| fresh, same construction | 2 | a/n | a′/n | b/9 | b′/9 | from G5 | x/y |
| bank, rank-6 (older construction) | 6 | truth c/n; deepest rank median m | d/n | e/9 | e′/9 | from G5 | x/y |

### Outcome sentences (pre-written; the agent fills the letters and picks the row by the §6 labels)

**H1/H2 confirm.** "On three fresh traps of the same construction that no agent had seen, Terra named the trap cue
in a/n runs (shipped items 11/12) and isolated the runner-up in a″/n; Luna isolated it in b/9. The within-harness
widening gap therefore holds off the public items (run-level, three items; Table 3b)." Change Claim 3's last
sentence to: "…on the three public items and on three fresh ones; every one of these traps places the truth at
proxy rank 2." Delete "six public items" from §9 and add "fresh items replicate the trap result (Table 3b)".

**H1 null/partial.** "On three fresh traps Terra named the cue in a/n runs, below the 11/12 on the shipped items
(Fisher p = …, run-level). The shipped traps may be easier than the construction's typical item, so we report the
trap result as specific to those items, with the fresh rate as the less biased estimate." Claim 3 stays, but its
headline number gets the fresh rate next to it.

**H1 reversal.** "On three fresh traps Terra named the cue in only a/n runs, against 11/12 on the shipped items.
Terra's widening on the public traps does not carry over to unseen items of the same construction. The
pre-registered Terra-Luna contrast (L1-L2) stands for the shipped items, but we no longer describe widening as a
property of the agent." Claim 3 is then rewritten as "on the shipped items, Terra widens…; on fresh items it does
not (Table 3b)". The abstract's Claim 3 sentence ends at "…in 0 of 18 (pre-registered) on the shipped items;
unseen items do not replicate it". This is the outcome that forces a rewrite. The text above is ready, so it is a
45-minute edit, not a rethink.

**H3 habit.** "Where the proxy puts the truth sixth, Terra isolated it in c/n runs. Its deepest test reached rank
≤ 3 in k/n runs, and it named the cue in d/n, against 0.00 for the top-two policy and h for the hedge [priv]. Of
its failures, f answered `none`, and the report-only judge credited g of those. Terra's widening is one step
deep. Where the proxy is wrong by more than one place, the result is a confident 'nothing found', the error
§5.2 shows a judge cannot catch." Claim 3's closing clause becomes "the best agent searches one step further and
no deeper (Table 3b)". The §9 'one-step only' limitation becomes a result. Caveat sentence: "the rank-6 items come
from an earlier trap construction without a planted decoy, so depth and construction are confounded."

**H3 partial.** "On rank-6 traps Terra isolated the truth in c/n runs (top-two policy 0.00, hedge h). It sometimes
searches past the proxy's top two, but not reliably. In k of its n runs the deepest test was at rank ≤ 3."

**H3 search.** "On rank-6 traps Terra isolated the truth in c/n runs and named it in d/n, close to the hedge (h) and
far above the top-two policy (0.00). Its widening is not a fixed one-step habit: it searches as deep as these items
require." Claim 3's closing clause becomes "the best agent searches past the proxy's head, to rank 6 on three bank
items". The §3 discussion of positive-test strategy is softened.

**H4.** Confirm: the H3 habit sentence keeps its "`none`" clause. Reversal: replace it with "f of the failures
named the proxy's favourite, so on deep traps Terra follows the head rather than abstaining."

**H5 confirm.** Add to §5.2: "On the 36 new runs, which no judge or agent had seen, the same frozen judge credited
g of h failed trap slots, including k of the `none` answers." Null or reversal: "On unseen items the judge's false
credit fell to g/h, so its blind spot for omissions may partly reflect the shipped items' reports." Keep J1-J2
as confirmed.

**Workshop hook (one sentence in §1 or §10).** "Items that stay valid after exposure: we replicate on generated
items no agent has seen, and we move where the proxy errs (a controlled distribution shift, rank 2 → rank 6)."
This addresses the CFP's contamination topic and Rish's and Kahou's distribution-shift interests.

---

## 10. Risks and what the design does about them

- **Construction confound at rank 6.** Unavoidable with existing items. It is disclosed, and G5's scripted
  references are computed on the same items, so the comparison is within item. A rank-6 trap with a planted decoy
  would need a two-decoy build, which `knob_trap3_build.py` cannot make before 19 Nov; that is not attempted.
- **Fresh items may be broken.** Gates G3 (oracle pass, cheaters at 0, removal reachable) and G6 (Luna pilots)
  run before the hash. Plan B is the fallback with no rebuild.
- **Fresh items may be easier or harder in ways other than rank.** G4 tells and the proxy-reading covariates are
  reported. G5 gives the scripted top-two value per item, so "Terra matches top-two" can be checked item by item.
- **Small n.** Three items per cell. Everything is descriptive with pre-written cut-offs, and no item-level claim
  goes below the floor.
- **Late backfire (H1 reversal).** Its paragraph is pre-written. The confirmatory L1-L2 results on shipped items are
  unaffected.
- **Budget.** The core costs about $12. Stage 2 is conditional, and the arm cap is hard.

---

## Critic

Written 12 Nov 2026 by the adversarial critic. All checks are against `origin/claude/serene-fermi-pog4k7`, the paper, the reviews and the ledger. Nothing was run. Items are named only by neutral label or pool.

**Verdict: RUN WITH CHANGES.** The F2 half (fresh rank-2 traps, Terra vs Luna) is the most direct answer available to the reviewers' shared top request, and the design for it is sound. The R6 half is much weaker than the design says. It is probably one probe, not three items, and its "habit" outcome is mostly implied by behaviour we have already measured. It also has a stop-signal confound on top of the construction confound the design already discloses. Keep R6, but demote it to a labelled one-probe case study. Do not let it carry a headline.

### Is it what the reviewers asked for? Yes, almost verbatim.
- `RANK_V4.md` lists "rank-6 bank traps and fresh items, with Terra and Luna" as consensus new run #5. In `RANK_V4_raw.json`, four of the five reviews name it as their main request, for example: "Break the item bottleneck… fresh generator items and… rank-6 traps"; "so the widening and model-dependence results can rise above the 0.25 item-level floor". `RECOMMENDATION_V2.md` l.585 says all four reviewers in that round named the rank-6 traps as "the run that would move them to 8".
- The paper already flags this as the decisive next run (§9 "Items", §10). Running it turns the paper's own stated limitation into a result. This is the strongest argument for C14.
- It does **not** follow the "cheap instrument on existing data" pattern that produced Claim 2. It needs new agent runs, new items and a new image layer. That makes it riskier than C6/C8-type work, but it is the only proposal that touches Claim 3's item base.

### Is the data really there? Partly. One serious problem.
1. **R6 is very likely one trap probe, not three items.** `exp_c.json` → `trap.by_pool.knob_trap_s` has only 3 sources across its 8 distinct instances. Its `ratio_profile.main_abs_lat` has min = q25 = 0.0969 (to 13 digits), and `main_abs_tru` has min = q25 = 0.420. With n = 8, that means three instances share one main reading. exp_c also states that per-source quantities are identical across copies (max difference 1.6e-15). The source with by far the weakest main reading (0.097 against non-main readings up to 0.69) is the one whose main lands at rank 6. So the three rank-6 instances are almost certainly **the same probe in three episodes**, which differ only in sample, aligned set and signs. Consequences:
   - "k of 3 items" and "≥ 1 on each of ≥ 2 items" in H3 measure episode context, not item generalisation. The item-level n for depth is 1.
   - Any sentence of the form "Terra's widening is one step deep" generalises from a single probe.
   - G1 must report the number of distinct R6 sources first. If it is 1, every R6 label becomes "one probe, three episodes".
2. **The R6 head is not inert, unlike the shipped [decoy].** In `knob_trap_s`, the best-ranked non-main candidate has a true |ratio| of 0.04-0.18 (median 0.13, `nonmain_abs_tru`). On the shipped traps it is 0.006-0.06 (`README.md` of exp_c). On R6, isolating the head can therefore show a visible logit move. An agent that stops there, or names it, may be reading weak positive evidence, which is not the same as a one-step habit. This confounds H3 ("habit") and especially H4 ("follows the head"). The design discloses the construction confound but misses this mechanism.
3. **The agent-visible rank is unverified for R6.** `followup/solvers/band.json` covers only the three shipped trap episodes. `proxy_verify_bank` found only rank-2 traps in its 6 trap episodes, because 31 duplicate episodes were dropped and the trap pools that are not shipped were apparently not counted as trap episodes. "Rank 6" exists only under exp_c's privileged |latent ratio| ranking. Sign-aware ranking promotes one `knob_trap_s` instance (4/8 → 5/8), and it may be an R6 one. Gate G1 is therefore essential, not a formality. If it fails, R6 becomes 2 episodes of one probe, or fewer.
4. **The trap may not be the required probe in the R6 episodes** (trapsolv stream). In that case the episode's other probes compete for the 8 texts under a different composition, and the cell is not comparable with the shipped row. The G2 "list deviations" rule is too weak (change 3).
5. **F2 inputs exist.** `knob_trap_s2` has 11 probe artifacts on the branch, and `knob_trap3_build.py`, `knob_trap3_episodes.py`, `docker_research_bb/build.sh` and `blackbox_image_check.py` are all present. Note that the 7 "unused" bases are not unused in general: they are bank traps (`knob_trap_s2`, main at rank 1 in 7/10 and sign-aware rank 1 in 10/10). They are only unused as decoy bases and have never been run with agents. That is fine for freshness. Plan B (same three probes, new episodes) adds **no** item-level n and must be labelled that way.

### Can it be done in time? Yes, with about 2 days of slack, but F2 plan A is the critical path.
- Step 0 plus the fresh build, image layer and checks on 13 Nov make one agent-day with several failure points (encode/fit yield, seed search, layer build, G3 checks). Plan B is a real fallback. The 14 Nov 15:00 go/no-go and the 17 Nov hard stop leave about 2.5 days before the 20 Nov deadline.
- The run volume (about 36-42 runs, Luna's 60 took 6 h) fits in 14-15 Nov.
- Paper space is the tighter constraint. V4 is already over 8 pages (RANK_V4 fix 1), so Table 3b must displace text, as §9 of the design plans.

### Could the result be dismissed as trivial or near-definitional?
- **H3 "habit" is close to definitional.** Terra already sends all its texts in one burst (40/40 runs) and spends about 3.9 texts on the trap. A rank-order search cannot reach rank 6 under that allocation, so "deepest rank ≤ 3 in ≥ 2/3 of runs" is nearly guaranteed by known behaviour plus budget arithmetic. The brainstorm itself notes that "0/9 at rank 6 may be budget arithmetic", and the designer's prior for habit is 0.65 against 0.10 for search. The habit result tells a reviewer something they would already predict. The one informative question at rank 6 is whether Terra **screens the complement or sends group texts**, which is how the hedge reaches 0.57 within budget. That is a different skill (planning a multi-property edit), and it should be the primary R6 quantity (change 4).
- **F2 is not trivial.** A confirm raises Claim 3's item base from 3 to 6 rank-2 traps, and a null is informative. It can only be dismissed if the fresh items are much easier or harder (the closeness covariate and the G4 tells handle this) or if the API drifted (change 2).

### Could it weaken existing claims? Yes, and that is acceptable.
- An H1 reversal (roughly 10-15% on the designer's priors) would cut Claim 3 back to "on the shipped items". The pre-written text handles it, and an honest held-out failure is defensible at a workshop on instrument validity. Without a concurrent anchor, though, a drop could be API drift rather than item difficulty (change 2).
- H5 on about 36 runs cannot overturn Claim 2 (214 runs). The null wording is appropriately weak.
- The **"contamination" hook overreaches.** The shipped items are not yet released, so no training exposure is possible. What F2 tests is held-out items from the same generator, i.e. whether the item selection was overfit. Say "held-out items", not "items that stay valid after exposure".

### Required changes
1. **G1 first reports the number of distinct R6 sources.** If it is 1, rename the cell "R6: one probe, three episodes". Drop "k of 3 items" and "≥ 1 on each of ≥ 2 items" from H3. Rewrite the H3 habit/partial/search sentences as "on one deep-trap probe from an older construction…". Remove "Terra's widening is one step deep" and the change to Claim 3's closing clause. The R6 row stays descriptive and never enters the abstract.
2. **Add a concurrent shipped anchor.** Include 3 Terra Open-8 runs (one per shipped trap episode) in the same replicate-major order, for about $2.1. Without them, an F2 shortfall cannot be separated from model or API drift since Block 1. Pay for them by dropping or deferring Luna on R6 (point 5).
3. **Composition control for R6.** If F2 plan A builds a layer, also compose the R6 source into a fresh episode with the shipped composition (trap required, plus near-null, easy and null probes; non-shipped sources). Use it in place of, or next to, the bank episodes. If no layer is built, R6 runs on the bank episodes with a "composition differs" flag in the table row, not just in a deviations list.
4. **Reframe the R6 primary.** The primary quantity becomes "any group or complement text on the trap probe" (metric 4) plus iso(main). The "deepest rank" cut-off is demoted to descriptive. G1/G5 must also publish, as numbers with no names, the true |ratio| of the R6 rank-1..5 candidates relative to the main and to the naming threshold. If a head candidate's single-property isolation would show a visible effect, H4's "follows the head" is labelled "plausible-positive head", not an agent habit.
5. **Priorities if money or time runs short.** F2 Terra comes first, then F2 Luna, the shipped anchor, R6 Terra and the judge. Luna on R6 comes last (Luna widened 0/18 at rank 2, so 0 at rank 6 carries no information) and is the first thing cut. Stage 2 should go to F2 Terra only (n 6 → 9), not to R6.
6. **Plan B labelling.** If F2 falls back to plan B, every F2 sentence says "same three probes, new episodes". H1 then cannot raise the item-level n, and the abstract is not changed.
7. **Replace the workshop hook** with "held-out items from the same generator, and a shifted proxy error". Drop the "valid after exposure / contamination" wording.

### Realistic expected score gain
About **+0.3** on the current 6.8, with a range of −0.2 to +0.6:
- F2 confirm (about 0.6): +0.4 to +0.6. It closes the most-cited major and lifts Claim 3 above the 0.25 item-level floor.
- F2 null or partial: +0.1 to +0.2, from credit for an honest held-out test.
- F2 reversal: about −0.2. Claim 3 shrinks, partly offset by credibility.

R6 alone adds +0.05 to +0.15, because reviewers asked for it. With the one-probe caveat it cannot carry a headline. An overclaimed R6 sentence, such as "widening is one step deep" written about one probe, would invite a statistics reviewer to subtract. Most of the value sits in F2. If F2 plan A fails and only plan B plus R6 run, expect +0.1 to +0.2.
