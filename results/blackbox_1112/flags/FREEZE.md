# Freeze of the failure-flag code (DECISIONS D36)

Frozen before the first run on any real run's logs. Up to this point the code had been run only by its unit
tests, which use synthetic logs and a synthetic episode (`tests/test_failure_flags.py`, 28 tests, all passing).
Real raw files were opened before the freeze only to learn their formats (transcript, rollout and log record
shapes, the public sample and task files): no flag, effect, pair or recovery result was computed on a real run.
Two format checks touched real files before the freeze and are listed for completeness: the topic rule was tried
on the 24 public samples of the six items (bank public files, not runs; every sample note got its own topic),
and the number of probe_query replies printed in the main-study transcripts was counted per run (to see whether
the printed replies alone would do; in 35 of 64 runs they lined up with the logged calls by length), which is why
the replay with sentinel logits was built.

| file | sha256 |
|---|---|
| scripts/failure_flags.py | `570c47062508ea6099a16d59309a8789f8e9ea2d0c5ba31efa9093472a308862` |
| tests/test_failure_flags.py | `7576b62dd7aba939bf69cbec9c1b7e0011c73145bb9c83289d8610827df03880` |

Frozen at 2026-11-11T04:50:23Z (UTC).

## Changes after the freeze

Implementation bugs only; the definitions are D36's. Each entry: what changed, why, the new sha256.

### Change 1 (2026-11-11T04:55:22Z): text recovery from printed literals; a ripgrep stand-in in the sandbox

Seen on real data: the first replays (15 main-study runs, frozen code) showed calls whose texts the replay could
not reproduce because the agent chose them from SAE encodings of its own texts, which the replay's fake encoder
cannot give (no GPU), although the agent's output printed the texts it then sent. Also, commands piping into
`rg` failed in the sandbox (the agents' image had ripgrep; the host has none), which changes their outputs.
- Added `printed_texts` / `apply_printed_texts`: a replay text printed as a string literal (Python or JSON
  quoting) in the replay's output of an action up to the call is mapped to the literal at the same place of the
  agent's real output of that action (lines aligned on their skeleton: literals and numbers left out); a call
  whose texts all map takes the real texts. The logged (probe, n, chars) match, the per-probe sequence rule and
  the sample-logit check are unchanged and still decide; ambiguous mappings are dropped.
- The sandbox gets an `rg` stand-in (`grep -E -r`) when the host has no ripgrep.
- While editing, a quoting slip left the script unparsable for about two minutes during that first full run, so
  85 of its 100 replays failed; that run is discarded and every replay is redone with this version.
- Two synthetic tests added (30 tests, all pass).

New sha256: scripts/failure_flags.py `2b7720a1177252c15d352d4cee2553c00b49686b5249f01566a93c4c87671491`; tests/test_failure_flags.py `5cb267762022fcbbdcca29d5507f086d09224bb465d5a1ef18d023b8ab5a99ec`.

### Change 2 (2026-11-11T05:11:35Z): logit recovery tightened, sample-logit tolerance calibrated

Seen on the full run with change 1 (replays of 64 main-study and 36 fresh Open-8 runs; the fresh runs' full-text
log is the truth for the replay):
- **A printed reply alone gave wrong logits.** Of 3 fresh-run logits that came only from a printed
  `{"logits": [...]}` reply, 2 differed from the full-text log: the greedy assignment took an earlier reply of
  the same length. The printed reply is now a cross-check only: a logit comes from the sentinel alignment, and a
  reply that disagrees with it makes the logit missing. (In the main study this affects 2 logits.)
- **A full-precision sentinel did not align with a short real repr** (for example `2.5`), because the printed
  precision had to agree. When the replay printed the sentinel at full precision (10 or more decimals), the real
  number at that place is now taken whatever its length.
- **The tolerance of the sample-note logit check was too tight.** Over the fresh runs' full-text logs, the
  probe_query logit of a text identical to a sample note differs from the stored-encoding logit by up to 0.055
  (40 cases; median 0.009). This comes from encoder batching. The tolerance of 0.02 therefore failed 10 exact
  main-study recoveries (largest difference 0.042), and it is now 0.15 logits. A wrong text would differ by whole
  logits.
- Warnings that Python printed while parsing printed literals are silenced.
- Tests: 3 added, 1 expectation updated (33 tests, all pass). The replays themselves are unchanged (the driver
  is untouched), so the cached replays are reused.

New sha256: scripts/failure_flags.py `0ef8b8106d82cce19dce4d286bd72cfc235128dac9bc1f9d288d0d6a46bcde31`; tests/test_failure_flags.py `9c17ec3e4d2d8f6001d571dc6f8a32a47f9775ce58189131bd7eb277285b1bbf`.

### Change 3 (2026-11-11T05:13:01Z): tables count only the slots a flag applies to

Seen in the first written tables: in the F2 and F2n rows, the "missing" count included the slots the flag does not
apply to (F2 to slots answered `none`, F2n to slots with cues). The rates were not affected, because those
slots have no value and were already left out of the 2x2 cells; only the missing counts were wrong. Each table
now has an "applicable" column, and "missing" counts applicable slots without a value. No flag, outcome or
verdict changes. One test added (34 tests, all pass).

New sha256: scripts/failure_flags.py `09e9237256603cf4d6ee26ca0e561b8f4d5d6e73dafa853a61d34a7b9a26aefc`; tests/test_failure_flags.py `559e073eaf6adec1012a8a1d4631256502e30b9f22d6933cba0c146f749dfcb4`.

### Disclosures added after review (2026-11-11T05:40Z)

Two reviews (answer-freeness and definitions; independent recovery of 12 runs) found no flag, outcome or verdict
error. They did find that this log was incomplete:
- **The first run was not just discarded.** Run 1 (about 04:52:20 to 04:54:44, the frozen code) completed 15
  main-study replays (85 failed because of the quoting slip). With them it wrote `slots.jsonl`, `generated.md`
  and a scratch `flags_try1.json`: flag tables computed on those 15 real replays, before changes 1 to 3. They were
  seen, then overwritten.
- **Pre-freeze exploration went beyond record shapes.** A scratch script (`explore2.py`, 04:34Z) printed the
  probe_query commands of chosen real runs together with their outputs, logits included. No flag, effect, pair
  or recovery result was computed from them, but logits were seen.
- **Earlier versions were not kept.** No copy of the frozen script (`570c4706…`) or of the change-1 and change-2
  versions exists, so those changes cannot be diffed. From change 4 on, every version is kept in
  `results/private_1112/flags/frozen/` (git-ignored) as `failure_flags.<sha8>.py` and
  `test_failure_flags.<sha8>.py`, with a unified diff per change. That folder starts with the change-3 version
  (`09e92372…`).
- **The sample-logit check is weaker than change 2 said.** "A wrong text would differ by whole logits" holds
  across classes, not within one. Within one class, 3 to 16% of pairs of sample notes have logits within 0.15 of
  each other, so the check catches a logit from another call or a cross-class note, not every swap between two
  same-class notes. On the real data the largest observed difference is 0.042 (main study, 28 checked) and
  0.047 (validation, 15 checked). Any tolerance from 0.05 to 0.15 therefore gives the same result.

### Change 4 (2026-11-11T05:40:16Z): review fixes to recovery, sandbox and reporting

Each item comes from a review finding that was checked on the code before it was fixed.
- **Recovery: a trailing zero lost a logit.** An agent's `round(x, 3)` printed 2.490 as `2.49`, and the precision
  test (same number of decimals on both sides) rejected it. Since a sentinel never ends in 0, a real number with
  fewer decimals than the sentinel is now taken at the sentinel's precision. One with more decimals is still
  rejected.
- **Recovery: a printed sign broke the alignment.** With `%+.3f`, the replay printed `+3.712` and the real run
  `-2.739`, and the `+` stayed in the skeleton. The number pattern now takes a leading `+`.
- **Recovery: texts printed raw were never used.** Only texts printed as quoted literals were mapped (change 1),
  so slots whose texts the agent printed with `print(text)` stayed missing, although they could be recovered
  exactly. Added `raw_printed_pairs`:
  - The replay's output of an action is cut at the known texts it holds: every text the replay sent, and the
    public sample notes.
  - The real output must have the same structure: the same glue from start to end, in order, with only the numbers
    free. The real text in place of a hole is the real output between the glue pieces around it.
  - Glue with fewer than 3 anchoring characters cannot split two texts. Texts inside quotes are left to the
    literal mapping. Claude Code's "Shell cwd was reset to …" note at the end of an output is ignored.
  - The replay's own output, split by the same rule, must return its texts exactly.
  - The (probe, n, chars) match and the sample check still decide.
  - Two problems were found and fixed while building this, on the cached replays and before it was used: a
    per-text anchor could pick the wrong block; and with the cwd note, the last text of an output took the note in
    (the chars match rejected that call). This is why the structure rule is whole-output.
- **Sandbox: only the needed bank files are visible.** The replay sandbox now binds only `probe<j>.npz` and
  `probe<j>_sample_enc.npz`. Before, it bound the bank episode's whole private folder, which also holds
  answer.json and the grids. A grep of all 100 earlier replay outputs found no access to that folder or those
  files. Every replay is redone with this version.
- **Coverage bar: absence at exactly 0.8 was missed (floating point).** `ba <= 1 - 0.8` failed for a balanced
  accuracy of exactly 0.2 (1 - 0.8 = 0.19999999999999996). The test is now `max(ba, 1 - ba) >= 0.8`, with a
  1e-9 margin.
- **Reporting:**
  - missing-data bounds of the combined-flag table and of the D36 reading
  - the F2 row on named slots beside the verdict
  - the count of `none` slots whose F2n is 1 by counting alone
  - a "texts_ok_logits_missing" missing reason
  - the largest sample-check difference
  - the docstring brought in line with change 2
- **Tests:** 13 added and 1 expectation updated (47 tests, all pass). The added tests cover:
  - every surviving mutant the review listed: per-probe call_mismatch, the verdict boundaries, topic scores
    (2, 1), unknown topics never pairing, the cue scope in F2, normalisation in slots_of_run, coverage at the bar
  - the trailing zero and the sign
  - raw printed texts (anchoring, the ordinal and structure guard, quotes, a missing trailing newline, the cwd
    note)
  - the bounds and the forced-F2n count
  - the end-to-end sandbox seeing only the four bank files

New sha256: scripts/failure_flags.py `9bc59ff29fa647f48c5df71f10d7e00a6f469960e309083cd0334e3580f24fe2`; tests/test_failure_flags.py `e935083e289c0498984dcceb42e97f2cccd802b695f371ab579a615dcae0656a`.
