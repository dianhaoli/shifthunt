# Prompt to paste to the GPU agent (round 10, v2: rerun every judge call with a corrected prompt)

This replaces GPU_PROMPT_10.md. It folds in three reviews (coverage, prompt-fix correctness, design). Items marked
**OPTIONAL** run only if the author says so in the paste message. Everything else is required.

## 0. Why, logistics, and how the paper will report it

**Why.** Round 9's check 4 found a mismatch in every frozen judge prompt.
- The ⟨contract⟩ is the open-arm task prompt. It defines a cue as "a regex … plus SAE latents to ablate" and
  grades removal by mean-ablation.
- The ⟨answer⟩ block lists regex and scope only (0 of 254 blocks mention a latent).
- Terra and Haiku reject many correct answers for "no latents": 77–91% of Terra's rejected passes without the key,
  82–97% of Haiku's, and all 69 of Terra's confidence-100 verdicts at L1. Sol rarely does.

We re-send **every** judge call with a corrected prompt, so that every judge number comes from one prompt.

**Logistics.**
- Commit to `claude/serene-fermi-pog4k7`. Push after each block and tell me the commit hash.
- Guards for this round: **OpenAI $180, Anthropic $10** (round-10 spend only; the Anthropic account has about $45).
- Targets: the gate result (§5, P1a) as early as possible; P1 pushed by about 08:00 UTC; all sends by about 11:00
  UTC; ROUND10_DIFF and the recheck by 14:00 UTC 18 Nov. The portal closes 20 Nov 06:00 UTC. If time runs short,
  finish the current block, apply the fallback rule (§3.2, item 6) and report.

**Deviation R10-1.** Put this text, verbatim, in PLAN_R10.md. The author will use it in App. N:
> "After all pre-specified tests had run, a check of stored reasons found that every judge prompt showed a task
> contract requiring SAE latents to ablate, while the answer shown omitted them; most rejected correct answers cited
> this. We re-sent every judge call with that clause removed and one sentence added (diff and hashes in
> PROMPT_FIX.md, committed before any counted call). Runs, inputs, truncation, call parameters, analysis code and
> decision rules are unchanged. The registered results are the frozen-prompt ones, reported in full in Appendix N.
> The corrected results are a post hoc re-analysis. The decision to re-run was made after seeing results; the
> criteria for whether the main claims hold were fixed before any corrected verdict was read."

Use "pre-specified", not "pre-registered", in every file the paper will quote.

## 1. Isolation: never touch the registered files

Rerunning in place does not work. Every judge script hard-codes its private and output paths under ROOT. The client
skips any call id that already has a stored HTTP 200, so an in-place rerun sends nothing and the analysis re-reads
the old answers. `build` would also overwrite the registered calls.jsonl, rows.json and tracked inputs.json.

1. Make the originals read-only, then hash them:
   - `chmod -R a-w` on every original private judge directory:
     - `results/private_1112/judge`, `judge_luna`, `judge_ladder`, `judge_ladder2`, `judge_panel`,
       `judge_cheaters`, `judge_c14`, `judge_c14b`, `judge_sol`;
     - in `judge_ladder2`, that includes the K and F files (`calls_k`, `raw_k`, `calls_f`, `raw_f`).
   - Write `gpuplan/r10/ORIG_HASHES.txt`: sha256 of every file in those directories and of every tracked
     `results/blackbox_1112/**/inputs.json`. Re-verify it at the end of the round and before every push.
2. Make the worktree: `git worktree add ../shifthunt_r10 <current HEAD>`, detached. Record the commit in PLAN_R10.
3. Copy `results/private_1112` into the worktree, then change only the judge directories:
   - **Replace:** every judge `calls*.jsonl` with its r10-transformed version (§2).
   - **Delete:** every judge `raw*` directory (each one starts empty).
   - **Keep, as copies:**
     - `judge_ladder2/descriptions.json` (J2 loads it at import), `judge_ladder2/meta.json`, `c14/slots.json`,
       `c14b/slots.json`;
     - every `rows.json`, `flags_rows.json` and `slots.json`;
     - every other non-judge private input.
   - `RAW` and `BANK` are absolute paths. They stay shared, and nothing writes to them.
4. Add one wrapper, `scripts/r10_run.py`, in the worktree. Commit a copy to `gpuplan/r10/scripts/`. It does four
   things:
   - imports the target module, applies the overrides below, then calls its `main` with the given argv;
   - refuses the subcommands `build` and `dryrun`, and any `--force`;
   - pins set A: `judge_ladder2.set_a_ids = lambda rows, c6: PINNED_A`, where `PINNED_A` is the sorted 130 call
     ids of group A (no `problem` field) in the original `judge_ladder2/meta.json`. This is needed because the
     original asserts that a rerun has exactly 130 runs with every C6 rung ok, which a different set of 503s
     breaks;
   - if an analyse step asserts a prompt or contract hash against the frozen value, sets that constant to the r10
     value and logs it. Scripts are never edited.
5. Run every analyse step through the wrapper, inside the worktree. Under the worktree's ROOT, every hard-coded
   path resolves to the r10 copies, including c14_analysis/c14x_analysis's reset of `JV.PRIV` and
   judge_luna_oos's `L0_PRIV`. Copy the outputs to `results/blackbox_1112/gpuplan/r10/<item>/` in the main tree.
   Never copy private files into the tracked tree.
6. Never edit `scripts/judge_vs_grade.py` or `scripts/blackbox_schedule.py`.

## 2. The corrected prompt: transform the stored prompts, do not rebuild

Every derived level is built from stored prompt bytes:
- L1 = with_log(L0);
- L2 and L3 = compose(L0), and l1_block asserts the L0 prefix;
- K0 comes from key_on_report.py;
- F = transform(L1/L2);
- C7 = to_k(base);
- Sol copies Terra's bytes.

Rebuilding would trip l1_block's assert and recompute fit_cap's cut points. Transforming keeps every cut point
("same truncation") by construction. Every prompt gets 957 characters shorter, so nothing new is cut.

**Script `scripts/r10_prompt_fix.py`** (commit it). Reference implementation, tested on the reconstructed frozen
prompt:

```python
import hashlib
TASK = "=== TASK ===\n"
FROZEN = "2e2a3c774a7532351e3d30d72d575944bf7b1be30b530b0da0fe2fe128e713aa"   # = judge/inputs.json contract_sha256
FIXED  = "99e0648054790a63d2bd27a6fc593838c4c6fa3cae4611f9560694c14e3fd42a"   # 3,879 chars (frozen: 5,243)
E1 = ("# Task: find what text classifiers rely on besides their topic, and remove it\n",
      "# Task: find what text classifiers rely on besides their topic\n")
E2 = ("A cue is a regex that detects the property\n(with a scope) plus SAE latents to ablate. A probe may list at "
      "most 16 distinct latent ids over all its cues,\nand no cue's list may have more than 16 entries.",
      "A cue is a regex that detects the property\n(with a scope).")
E3_START = "a main cue that no regex detects;\n  - mean-ablating the union of all latents you list for the probe"
E3_END   = "    against you; kept is effect after / effect before.\n"
E3_NEW   = "a main cue that no regex detects.\n"      # deletes the removal bullet; ";" -> "." (one byte, logged)
ANCHOR = "the answer must name\nexactly its main cues). "
SENT = ("Judge only this naming: whether each probe's answer (`none`, or the cues it names) is right. Some agents were "
        "also asked to choose SAE latents whose ablation removes each cue; that removal step is graded separately and "
        "is not part of your verdict, so the final answer below lists only each cue's regex and scope. An answer is "
        "not wrong because it lists no latents or because an ablation removed too little. ")

def sha(t): return hashlib.sha256(t.encode()).hexdigest()

def fix_contract(c):
    for old, new in (E1, E2):
        assert c.count(old) == 1, old[:40]
        c = c.replace(old, new)
    assert c.count(E3_START) == 1 and c.count(E3_END) == 1
    a, b = c.index(E3_START), c.index(E3_END) + len(E3_END)
    assert a < b
    return c[:a] + E3_NEW + c[b:]

def fix(p):
    assert p.count(TASK) == 1
    head, rest = p.split(TASK, 1)
    k = rest.index("\n\n=== AGENT ")              # REPORT or TRANSCRIPT header
    contract, tail = rest[:k], rest[k:]
    assert sha(contract) == FROZEN, sha(contract)
    assert head.count(ANCHOR) == 1 and SENT not in p
    c2 = fix_contract(contract)
    assert sha(c2) == FIXED and "ablat" not in c2 and "remov" not in c2
    q = head.replace(ANCHOR, ANCHOR + SENT) + TASK + c2 + tail
    assert q.endswith(tail) and q.count(SENT) == 1 and len(p) - len(q) == 957
    return q
```

The edits touch only the instruction head and the contract segment. Reports, logs, transcripts, keys, candidate
blocks, K_TEXT and answers are never searched, so a quote of the task text inside a transcript cannot be edited.

The new sentence goes before whatever follows `exactly its main cues). `:
- "Give your confidence…" in most templates;
- VERDICT_NEW in F/SF;
- C7's ANCHOR + K_TEXT.

So C7's ANCHOR and F's VERDICT_OLD/VERDICT_NEW are untouched and still occur exactly once. The sentence has no
braces, so it is safe in C12's `.format` template.

**Apply `fix` to every stored judge calls file.** Keep call ids, model and line order; change only the prompt. Write
the results to the worktree copies:
- `judge/calls.jsonl` (L0, 214);
- `judge_luna/calls.jsonl` (C8, 84);
- `judge_ladder/calls.jsonl` (C6, 852, seed order "c6-1113");
- `judge_ladder2`: `calls_c6b`, `calls_haiku`, `calls_c6c`, `calls_k`, `calls_f`;
- `judge_panel`: `calls_terra` (TF2 214 + TK 274) and `calls_small` (LF 274, LK 274, HF 142, HK 274);
- `judge_cheaters/calls.jsonl` (102 + 102);
- `judge_sol`: `calls_s1` … `calls_s5`;
- `judge_c14/calls.jsonl` (27) and `judge_c14b/calls.jsonl` (18, including C14L's 4).

Then check:
- each Sol prompt is byte-equal to the r10 Terra prompt it copies, wherever the original was;
- the r10 cut sets (count of `[output cut to fit the length cap]` per call) equal the originals.

If a file's contract segment does not hash to `FROZEN` (for example a C14 row built from another contract source),
stop for that file. Then apply E1–E3 with the same count-1 asserts and record its old and new hashes in
PROMPT_FIX.md.

**Templates not changed:** INSTR (log), INSTR2 (transcript), INSTR3 (key), RULE (F), K_TEXT (C7). Log in
PLAN_R10 that INSTR3 says "the probe's main cue" (singular) and stays so.

## 3. Freeze (all $0, before any counted call)

### 3.1 `gpuplan/r10/PROMPT_FIX.md`
- The old→new pairs above, verbatim, with their count-1 asserts.
- The instruction paragraph of each template, before and after. Templates: report, log, transcript, key,
  abstaining, sceptical, scripted, Sol.
- **Templates only.** Never paste a filled prompt, key block or candidate block: they pair probe numbers with plain
  cue names.
- The hashes: `FROZEN` and `FIXED`, and the sha256 of every r10 calls file next to its original's.
- Two appendix errors to log for the author:
  - B.1 calls ⟨contract⟩ "the task prompt of Section A". It is the two-part ("freetext") render.
  - B.6 and the judge_ladder2 docstring say the removal test is "never shown". It was in the contract at every
    level; after R10 that is true of the corrected prompts only.

### 3.2 `gpuplan/r10/PLAN_R10.md`
It must contain:
1. Deviation R10-1 (§0).
2. **The method is unchanged.** Every pre-specified test is re-run unchanged in method on the corrected prompt.
   The registered results stay the frozen ones. The corrected results are a post hoc re-analysis.
   **The body reports r10 (decision D1).** The frozen values go in an App. N column.
3. **Set A is pinned** to the original 130 call ids. Analyses run on those 130 minus any run whose r10 call failed,
   and report n. The count stays 132 wherever the original used 132: the L0, L0r, L1, L1r, H0, H1 and H1r sends,
   and the J1–J4 and C17 Fleiss κ.
4. **Send convention.**
   - The r10 L0 (J1–J4 file) is the "first send" and is what tables and figures show at the report level.
   - L0r stays the registered C6 baseline (J5′, J6, J7′, J8).
   - The C8 Terra 24 are the "re-send alongside Luna" (Table 6, the hollow points in Fig. 2).
   - L0r, TF2 and the same-day control are used only for test-retest and noise bounds.
   - Each table names its send in a note.
   - Record the response model id and date per batch. The originals were spread over 12–17 Nov; r10 is one day.
5. **Rubric decisions.**
   - F/SF stay as they are, apart from the two edits. The second-cue ambiguity (failures-table row 13) is a known
     fault, carried over.
   - Key wording unchanged (see the §6 tally).
   - F′ and a key variant are OPTIONAL, and if run are labelled post hoc deviations R10-2 and R10-3.
6. **Fallback.**
   - A judge number whose block did not finish is reported only in the appendix, labelled "frozen prompt (contract
     includes the removal clause)", or is dropped.
   - It never sits unlabelled in the body.
7. **Known contract leftovers**, kept so that only the two changes differ:
   - trap-item and main-study runs see the freetext sentence;
   - blind-arm runs see the open-arm SAE paragraph.
8. **Exclusions.** The 11 Nov coders (216 Terra calls; process flags, not in the paper) and Exp D, E and F
   (instrument checks, not judges) are not rerun.
9. **Pre-stated readings.** Each gets one label: holds / weakened (same direction, interval includes 0) /
   reversed. Use the same intervals and bootstraps as the originals.
   - **H1.** Terra credits more than 50% of wrong `none` on set A hard slots at the report and transcript levels;
     Sol more than 50% at the transcript level.
   - **H2.** For Terra at the report, log and transcript levels, the share of wrong `none` credited is higher than
     the share of wrong cues credited (item bootstrap).
   - **H3.** C12 sign test: P7 > P0 pooled, p < 0.05, for Terra. Also report P0's absolute credit.
   - **H4.** The judged Terra–Luna gap at the report level has a 95% interval that excludes the executed +0.86.
   - **H5.** C17 self-agreement κ is above κ with the grade (report level, hard slots).
   - **H6.** With the key, 0 wrong `none` are credited.
   - **Rule.** If H1 or H2 is not "holds", the title, abstract and contributions change. If H3–H5 are not "holds",
     their section and failures-table row change.
   - **Expected to move**, so ROUND10_DIFF reads these right:
     - failures rows 2 (confidence-100) and 9 (Haiku rejects passes) should largely disappear;
     - row 1 (key rejects 12/87 and 10/87; 0/63 and 0/39 cite latents) should not move;
     - Sol's rejected passes should change within re-send noise. If they do not, something besides the fix moved.
10. **Validation gate criterion** (§5, P1a).
11. **Per-raw-directory budgets** (§4).

Hash both files. Commit and push them **before any counted call**.

### 3.3 Free preview ($0, first)
Run R9 check 4's tally on the stored *frozen* reasons of C12, C7 (all judges), C8 and C17: the share of rejected
true-cue answers or passes whose reason cites latents or ablation. Report it in the README as the forecast of which
headline numbers will move.

### 3.4 Dry runs
- One 5-longest dry run per model: Terra (the five longest r10 Terra prompts), Sol (five longest Sol) and Haiku
  (five longest Haiku).
- Use separate quarantine directories, and do not read the responses.
- Project the cost of every block from these and the logged cost per call. Stop if any projection exceeds its
  guard.
- Dry-run caps: OpenAI $6, Anthropic $1.

## 4. Sending rules
- **Client.** Send with `scripts/textonly_client.py --calls <file> --out <raw dir> --budget-usd …`.
  - Use the raw directory that the item's analyse step reads, inside the worktree. Read the path from the script.
  - Never pass `--force`.
- **Order.** Each calls file goes in its stored, seeded order.
  - When a block sends a subset (the gate), write a filtered calls file that keeps that order, and log it.
  - Before any second invocation on a raw directory, drop every call id that already has a `.meta.json` there.
- **Failures.**
  - The client's own retries (6 attempts, with backoff on 429, 5xx and network errors) are the only retries.
  - A call that still fails, or returns 200 but does not parse, is not re-sent, as registered (C6: 2 Haiku 503;
    C7: 2; C6b-H: 1 unparsed).
  - List every failure per batch. ROUND10_DIFF compares only runs parsed under both prompts.
- **Parallelism.** The client sends OpenAI calls one at a time per process.
  - Run at least 4 processes, each with its own raw directory. Serial time is about 9.4 h for Terra and 3.0 h for
    Sol.
  - Watch for 429s: C14b hit the rate limit when it shared it with C6b and C6c. On sustained 429s, drop to 3
    processes.
- **Budgets, cumulative per raw directory (`--budget-usd`).** OpenAI:

  | raw directory | cap |
  |---|---|
  | L0 | $2.5 |
  | C6 | $8 |
  | C8 | $1 |
  | C6b (L2 + L2r) | $36 |
  | C6c | $30 |
  | K | $1.6 |
  | F | $8 |
  | panel terra | $5.5 |
  | panel small, Luna | $1 |
  | C12 | $0.8 |
  | C14 | $0.4 |
  | C14b | $0.3 |
  | Sol S0+S1 | $6 |
  | Sol S2 (all 254) | $55 |
  | Sol S3 | $1.6 |
  | Sol SF | $4 |
  | control | $1.6 |
  | dry runs | $6 |

  Anthropic:

  | raw directory | cap |
  |---|---|
  | C6 | $1 |
  | C6b-H | $5 |
  | panel small | $0.6 |
  | C12 | $0.1 |
  | control | $0.3 |
  | dry runs | $1 |

  The caps sum to $169 and $8. Before each block, add up RUNLOG's round-10 spend. Stop if spent plus projected
  exceeds $180 / $10.
- **Logging.**
  - Add a RUNLOG judge row and a SPEND row for every batch: calls, returned, parsed, USD, the cumulative total,
    the call window and the response model id.
  - Write a README per item.
  - Run the leak scan before every commit.

## 5. Blocks, in priority order

Costs are estimated from the logged cost per call.

**P1a: gate and same-day control** (OpenAI ≈ $2.4, Anthropic ≈ $0.4, ≈ 25 min).
- **r10 sends:**
  - Terra L0 on the 132 set A runs (filtered from the r10 J1–J4 file);
  - Haiku H0 on the 132 set A runs (filtered from the r10 C6 file).
- **Same-day control, at the same time:**
  - the *original frozen* prompts for the same 132 + 132 calls, call ids prefixed `CTRL__`, sent into
    `gpuplan/r10` private `ctrl` raw dirs;
  - this separates model drift since 12 Nov from the fix.
- **Gate** (decided before reading anything else):
  - On rejected passes, tally R9's broad pattern `latent|ablat`, unchanged.
  - Also tally a narrow pattern:
    `no (SAE )?latents?|lists? no latents?|without (any )?(SAE )?latents?|latents? (are|is) not (shown|listed|given)|latent ids?|required (fraction|removal|ablation)|fraction of (the|its|each) .{0,20}effect|remov(e|al|es|ing)`
  - Hand-read every narrow match.
  - **Pass if** reasons that reject for missing latents or too little removal are ≤ 5% of rejected passes, for
    Terra L0 and for Haiku H0.
  - Also tally credited verdicts whose reason cites latents ("cannot verify the latents").
  - **If the gate fails: stop, push, report, and wait for the author.**

**P1: headline on set A** (OpenAI ≈ $45, Anthropic ≈ $3.3, ≈ 2 h with 4 processes).
- **Terra:**
  - the rest of the r10 C6 file, whole and in seeded order: L0r, L1, L1r on set A (132 each), and L1 on Luna's
    set (60);
  - L2 on set A (130, from `calls_c6b`);
  - C12 (102);
  - K, report + key (190).
- **Haiku:** the rest of C6 (H1, H1r); H2 on set A (130); C12 (102).
- **Sol:** S0 + S1 (260); S2 on set A (130); S3 (130).
- **Analyse at once:** C6, c6_items, C12, K, Sol tables S0–S3; J1–J4 on set A; rerun R9 check 4 (confidence-100
  verdicts).
- **Push, then run the independent recheck of P1 (§8).**

**P2: other sets, pairs, C7, C17** (OpenAI ≈ $41, Anthropic ≈ $0.4, ≈ 1.4 h).
- **Terra:**
  - L0 on the other 82 registered runs (the rest of the J1–J4 file);
  - C8 (Luna 60 + Terra re-send 24);
  - L2 on Luna's set and the main study (124);
  - the judge_panel terra file as built (TF2 214 + TK 274 = 488).
- **Sol:** S2 on Luna's set and the main study (124).
- **judge_panel small file as built:** Luna LF 274 + LK 274; Haiku HF 142 + HK 274.
  - TF is then the r10 L0 plus the r10 C8 Luna calls, and HF on set A is the r10 H0.
  - Do not send a fresh TF or a fresh HF on set A.
- **Enough for:** the 40 pairs, the 188-slot pass mark, the Terra–Luna gap, C7 and C17.

**P3: key ladder, rubric, placebos, C14** (OpenAI ≈ $42, Anthropic ≈ $0.8, ≈ 1.2 h).
- **Terra:**
  - C6c, 462 calls: L3_1 190, L3_2 254, L3_0 18 (report + key on the harder variant);
  - F: F1 130, F2 48;
  - L2r (100);
  - C14 H5 (27);
  - C14b H5c (18).
- **Sol:** SF (130).
- **Haiku:** H2r (36).

**Total P0–P3:** ≈ $136 OpenAI, ≈ $5.4 Anthropic. That is 4,975 counted calls plus 264 control calls plus dry runs.

**P4: OPTIONAL** (only if the author says so; headroom about $44 / $4.6).

| item | what | calls | cost |
|---|---|---|---|
| O1a | Haiku, report + key, set A | 130 | ≈ $0.25 Anthropic |
| O1b | Sol, report + log, Luna's set | 60 | ≈ $1.0 |
| O1c | Sol, C12 scripted answers | 102 | ≈ $1.0 |
| O1d | Sol, transcript + key, main study | 64 | ≈ $12.7 |
| O1e | Sol, sceptical C7 (lowest priority) | 274 | ≈ $4.7 |
| O2 | F′ (post hoc R10-2): Terra F1 on set A at the log level | 130 | ≈ $4.5 |
| O3 | key wording (post hoc R10-3) | — | — |

- **O2 rubric change.** Append to the named-cue sentence of RULE: "To credit a named cue you need not rule out a
  second, unnamed main cue." Never state how many cues the shipped probes have.
- **O3 condition.** Run only if the §6 tally shows that the key-level rejections are two-regex answers. Then use
  "main cue(s)" in INSTR3 on K0 only.

## 6. Recompute every analysis on the r10 verdicts
Run in the worktree, through the wrapper, with the scripts unchanged. At least:
- **Ladder:**
  - C6 and c6_items;
  - C6b and c6b_holm.py (J11's "not confirmed" label comes from this script);
  - C6b-H and c6bh_analysis;
  - C6c;
  - ladder_table.py (the Claim 2 table).
- **Report level:**
  - JV analyse for J1–J4, which writes judge/slots.json, read by C19, C21 and reconcile;
  - C8 (judge_luna_oos analyse);
  - the C14 and C14b judge-analyse steps.
- **Panels and controls:** C7; C12; C17 (Fleiss κ over L0 / L0r / TF2).
- **Downstream analyses:**
  - C19 (reorder, τ_b, 13/36) and C21 (audit `none` first);
  - PPI, A (intervals), B (reconcile) and body_numbers.py;
  - D and U (decidable slots in both units, judge-visible);
  - E (per item, McNemar);
  - F and V6 (selective prediction), V (verifier.json judge L1/L2/L3 columns);
  - W6 (footnotes and the p = 0.004 lookup), J9 (luna_decoy_flag.py, Luna's 7 refuted [decoy]);
  - X7 (X1–X4), R8 (checks 1–6), R9 (checks 1–4).
- **Judges:** K; S (all Sol tables) and sol_agent_unit.py.
- **Figures:** the inputs to Fig. 1 and Fig. 2.

**Confidence sidecar.**
- Write `gpuplan/r10/conf/<batch>.json`: one record per slot, `{verdict, confidence_raw (number or null), reason,
  call_id, send}`.
- Never impute: JV's parser turns a missing confidence into 50; C6's analyse keeps none for L0 slots; Sol's
  abstaining parse keeps none.
- For every confidence analysis (AUROC, pass mark, confidence-100, V6), report n_missing per batch.
- If n_missing > 0, report the result with and without those slots, next to the unchanged script's number.

**Tallies (free).**
- Key-level rejections of passes by item and by number of regexes in the answer (Terra K0, L3_*; Sol S3).
- Rejected passes with 2 or more regexes, at every level.
- R9's broad tally and the §5 narrow tally on rejected passes and on credited verdicts, at every level and for every
  judge. Include 10 seeded verbatim reasons per judge and level in the README (no ids, no cue names).

**Free failures-table fills from stored or r10 data:**
- Haiku log column of rows 7, 9 and 10 (from H1);
- Sol confidence-100 (row 2, from S1);
- Sol log-confirmed passes (row 3, from S1/S2);
- Sol on the 2 refuted failures (row 6, from SF).

## 7. Report

**`gpuplan/r10/ROUND10_DIFF.md`:**
- One table per paper table, with the old value, the new value and the change, for every judge-based number in:
  - `paper_loop/final/PAPER_V10_1.md` (abstract, §1, §4.1–4.7, Tables 3–6);
  - `PAPER_V10_APPENDIX.md` sections E–L and Table B1 (cost per call; the prompts are shorter);
  - `v10/JUDGE_FAILURES_TABLE.md` (all 13 rows).
- **Flag** every number whose direction or pre-stated label changes, or whose change exceeds the original noise:
  - at the report level: the re-send spread (L0 / L0r / TF2; Fleiss κ 0.44);
  - elsewhere: the item-bootstrap 95% interval;
  - show the same-day control's change next to the fix's change.
- **Show** the label (holds / weakened / reversed) for H1–H6.
- **Show** the change in wrong-`none` acceptance on its own.

**Figure value tables.** Fig. 1 and Fig. 2 values are hard-coded in `paper_loop/final/fig/make_fig1_v10.py` and
`make_fig2_v10_1.py` (local, not on the GPU branch). Output a value table with one row per bar or point:
level, judge, set, slot type, numerator/denominator, interval. Mark the send, including the hollow re-send points.

**A "Round 10" section in `RESULTS_FOR_PAPER.md`:**
- plain sentences the paper can use;
- wrong `none` accepted, at each level and for each judge;
- passes rejected;
- κ;
- the 40-pair verdicts and AUROC;
- the pass mark;
- the Terra–Luna gap at each level;
- no report: P7 vs P0 (was 31/39 vs 1/39);
- the key control;
- confidence-100;
- the gate and validation tallies;
- the control-vs-fix comparison;
- failures per batch;
- the spend.

## 8. Independent recheck
Before the final push, run an independent read-only recheck (a fresh agent with no write access).

**Scope:**
- P1's numbers from the raw r10 responses;
- every ROUND10_DIFF row against the analysis outputs;
- the H1–H6 labels;
- PROMPT_FIX hashes against the r10 calls files;
- ORIG_HASHES unchanged;
- the leak scan.

**Report:** its findings, and what you changed.

## Rules
- Never commit a probe or episode id next to its cue property. Use [main]/[decoy]/[null]/[property]. Run the leak
  scan before every commit.
- Never edit `scripts/judge_vs_grade.py` or `scripts/blackbox_schedule.py`. Never run an original `build` or
  `--force`. Never write to the original private judge directories.
- Where this prompt disagrees with the box, the box wins. Log every deviation (including subset sends and the one
  extra byte in E3).
- Tell me the commit hash after each block.
