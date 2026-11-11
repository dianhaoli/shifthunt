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
| scripts/exp_f_ci.py | `b6dee8698cd967d9669ffb96decfe5ca8a5a557f2bddc5034bce9ec7f84bac40` | 2026-11-11T06:10Z | before first real run (`--mode ci` started 06:10:41Z; `--mode cs` control 06:21-06:29Z). This hash produced the published Exp F result, followup/misc/exp_f_ci.json (annotation corrected by the misc verifier, see the misc entries below) |
| scripts/latent_regrade.py | `0c7b44365fe1520050a4f6e756bf0430049a939fb7f8d6089d45848f402f1004` | 2026-11-11T06:15Z | before first real run |
| scripts/scripted_cheaters.py | `a9b7dba1b8b767e024bd62eff2e6f7323323912c445abf4bdb4b0090578d79c5` | 2026-11-11T06:15Z | before first real run |
| tests/test_followup_misc.py | `b1fa7a2a109389b5209633101a887f2b1eed4f8adf08edd904f10e3805a2c8ba` | 2026-11-11T06:15Z | before first real run |

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
| scripts/followup_band.py | `8e2cbd42c4c895cb808535366e146ef9d0f45a655c1a4bb357eea2b40f4be1e4` | 2026-11-11T06:20Z | before first real run |
| scripts/followup_trapseeds.py | `15dda9b9423cfb26cb589775f45f5c7993b9e8012a5fe9817e1ccc58c4e96dca` | 2026-11-11T06:21Z | before first real run |

- solvers, 2026-11-11T06:20Z: tests/test_followup_solvers.py gains the band-solver tests (new tests, no change to
  an existing test). No code was run on real data in between. New sha256
  `fa50a2dcfbe56e93225a25b1ab438b830cd78b1ec637ec96842e976f4ab9a90d`.
- solvers, 2026-11-11T06:21Z: tests/test_followup_solvers.py gains the trap-seed tests (new tests only). New sha256
  `73e20db935ce49bc444110182b5f48fc0460e8a71f035709be11f6934564d254`.
- solvers, 2026-11-11T06:23Z: the first builder was stopped by the main session (process accident). Its state:
  followup_trapseeds.py had run once (06:22Z, outputs kept, no change); the brute-force encode had written 9 of 24
  shipped units to the cache and was killed before it appended its validation rows. A second builder resumes
  from the cache with the frozen code above, unchanged.
- solvers, 2026-11-11T06:26Z: new file scripts/followup_bankclass.py (bank probe types from the build manifests,
  and the generator flip table; CPU), frozen before its first run, sha256
  `c4b78f9936c0d9a213acc0b32b95aceea6dd7a0dbe500e1603e844990f0407e7`. tests/test_followup_solvers.py gains its
  test (new test only). New sha256 `95c031bbf197372f919c07fd0091078d02d3e8c471a390df1ea0ce3c51c9c0ae`.
- solvers, 2026-11-11T06:33Z: new file scripts/followup_nonpriv.py (§7 non-privileged solver: n-gram candidates
  from the public sample, deletion flips, BB-64 budget and rule; GPU encode), frozen before its first run, sha256
  `7170557ffc8999b256077a61216ae60b473ce9c5bff1e2b8723498bcde03358a`. tests/test_followup_solvers.py gains its
  tests (new tests only). New sha256 `e499e1afe8b9205487a14db63c9eb9f7c4c020a47bd478c6d7137d82bfe63434`.
  Brute-force BB-64 (followup_bruteforce.py solve) ran at 06:31Z on the complete cache; bruteforce.done at 06:33Z.
- solvers, 2026-11-11T06:35Z: new file scripts/followup_topicunit.py, **EXPLORATORY** (written after the BB-64
  result, which showed main effects below 0.30 in the frozen class-mean-gap unit). It reruns BB-64 and the band
  solvers with the prompt's unit (the topic coefficient, from topic-swap flips). It does not replace a frozen
  result. sha256 `6f640343d009b2685077933860dafcf1f462f42f22fca97b5bfe761cfa3c7c45`. tests gain its test (new
  test only); new sha256 `46da8407d1da2718d5cb7ecec0e98816fa6641ce927a3150967c20a03a4ce833`.
- solvers, runs: band encode 06:35-06:56Z (250 units, two chunks); nonpriv encode 06:56-06:59Z; topic-unit encode
  07:17-07:20Z; solves of bruteforce 06:31Z, nonpriv and band 07:02Z, topicunit 07:20Z. No frozen script changed.
- solvers, 2026-11-11T07:22Z: tests/test_followup_solvers.py, privacy fix only: the property names written as
  literals in the tests are replaced by generator lookups (CHILD = a nested child, TPROP = a templated property);
  the tests are unchanged in substance and all 19 pass. New sha256
  `6d768ad15c6babf1f4585343f7d340ff8d43dd25fbc26415c08bdeb8bec2ead5`.
- solvers, verifier, 2026-11-11 about 07:25-07:45Z: no code changed, no result changed. Independent GPU reruns
  (scratchpad `fu/verify_solvers/indep.py`, under the flock) and CPU re-derivations matched. Details are in
  solvers/README.md, "Verification". The README gained that section, an encoder-check line for the non-shipped
  units and three caveats. The 9 recomputed validation rows are now in the private
  `encode_validation_recomputed.jsonl`.

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

### coders (DEFINITIONS.md §8, exploratory)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/coder_render.py | `00f18b3d15c16cea81f5170a35c9e1d8e249d04eeaf8ab93cc6f1f65ef38e449` | 2026-11-11T06:19Z | before the 2-transcript pilot (first paid call) |
| scripts/coder_run.py | `dbaf64fb3f1e423778b1706088062876809b6b74cd09565ac9c42c630cf5c518` | 2026-11-11T06:19Z | before the 2-transcript pilot (first paid call) |
| tests/test_coder_render.py | `3f8f344f3a7a1e4a9ff20bc3b57e7bd325aa5d31193237487f9de8e7a4a5ccd2` | 2026-11-11T06:19Z | before the 2-transcript pilot |
| coder prompt A (coder_run.PROMPT_A, UTF-8) | `7b0a47c3021c60cc586b5dff798436ab6b369ec427933b073b376a51255b5f1a` | 2026-11-11T06:19Z | before the pilot |
| coder prompt B (coder_run.PROMPT_B, UTF-8) | `b62c11e5db824e075c8d5669a69deecfe3a29045339a83dd5bbfcf866e701316` | 2026-11-11T06:19Z | before the pilot |
| answer schema (coder_run.SCHEMA, UTF-8) | `ebe4dcf723ad8e006b930eb42ed7a9d14bc23abb5d761433e4da071b80619db9` | 2026-11-11T06:19Z | before the pilot |
| private gloss file (property descriptions; content not tracked) | `aa5c6204a925ae826cac1c3ce2d332869efe725df588830dcad8303796801616` | 2026-11-11T06:19Z | before the pilot |
| scripts/textonly_client.py (reused, unchanged) | `0529d1899988729311b6f49db746d13b9173b893fc44620325e6b46abfcc438c` | - | - |

Sampling: textonly_client defaults. The request body is `{"model": "gpt-6.1-terra", "input": PROMPT, "store": false}`:
no temperature, no seed, no reasoning-effort field, so the provider defaults apply. Coders A and B differ only in
prompt wording; each transcript gets its own call per coder.

- coders, 2026-11-11T06:20Z (before any paid call): scripts/coder_run.py answer_text prints the submitted answer
  one compact JSON line per probe entry instead of indented JSON. Why: the indented latent lists cost tokens and
  carry nothing. Prompts and definitions unchanged. New sha256 `d260150b39f8abd89a4e78927fa71c2b23cc9fd4218973303911ae31a7435f6d`.

### misc A1 (DEFINITIONS_ADDENDUM_1.md §A1, the user's tau/k grid)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/regrade_sweep.py | `f78362af49de4f11eda9015fa25cd79baff013ac0bbc74c383de0b3ba112489b` | 2026-11-11T06:16Z | 2026-11-11T06:18Z (default check: 100/100 runs reproduce grade.json, 0 mismatches); outputs results/blackbox_1112/followup/misc/regrade_A1.json, README_A1.md |
| tests/test_regrade_sweep.py | `630b507558d06cfeb4d2f7c3b136fec2e9e1fc1f544499e48e7926f81862877c` | 2026-11-11T06:16Z | synthetic only |

No change after the freeze. The script computes the §6 and §A1 cells together; only the §A1 cells (and the shipped
default cell) are published, from its private full output (results/private_1112/followup/misc_A1/). A scratch run
at 06:17Z with the same hash (outputs in session scratch, identical default check) preceded it and is not used.

### hardercue (brief section "hardercue"; operational choices in followup/hardercue/README.md)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/hc_heldout.py | `55e34c81304a3ee23cde7849d621fce5f6aa83984eaed2f842744c594ebb0b76` | 2026-11-11T06:24Z | before first real run |
| scripts/hc_solver.py | `c3c9c416e5736191b2cd49e56765253d93802976fbc0d7688ad432e6f399f9c9` | 2026-11-11T06:24Z | before first real run |
| tests/test_hc_tools.py | `152dd2c9c4f565c16a022f4f1f27a73444c9893bd05e35df3a0b6a1ea230a3b2` | 2026-11-11T06:24Z | synthetic only |

- hardercue: probe builds use the harness scripts unchanged (copied to a scratch root). Stage C (topic-flip rate
  0.2/0.3) was added at 06:22Z after stages A and B gave no item; it is a build knob, the acceptance rules are
  unchanged (README choice 10).
- coders, 2026-11-11T06:23Z (after the 4-call pilot, before the full job): the pilot cost $0.2944 for 4 calls and
  put the uncapped full job at about $16.5 to $17.5, over the $15 cap. Implementation change to shrink the
  transcripts, as the brief allows: `coder_render.format_events` gains `dump_cap`. The full job uses
  `--max-output 6000 --dump-cap 1500`. Every tool call and every output is kept. An output is cut (head two
  thirds, tail third, with a "[... N characters cut ...]" marker) only past its cap. A public-file dump (an
  output of a command or Read that reads the public sample or corpus files and calls no tool) is capped at
  1500 characters, and any other output at 6000. probe_query outputs are never cut. Prompts A and B and the
  schema are unchanged (same hashes). Estimate for the full job: $12.0 to $12.8, plus the $0.29 pilot. Pilot
  answers are kept apart (raw_pilot) and are not used as codes: the full job sends the 2 pilot transcripts
  again, capped like the rest. New sha256: scripts/coder_render.py
  `7468d1581368a5002b798d05c41270a2b72da25006ad5bea125aa0d488d1be0e`, scripts/coder_run.py
  `2e73cd20a659f01657fc4236e7feaea39aefc12f9868f1df0232c1796394695b`, tests/test_coder_render.py
  `33b6e86148fd3eb67c0578ae5683817962310bdf8a6fb81d4578a32fe329ee56` (one new test).
- coders, 2026-11-11T06:25Z (while the full job runs, before any coder answer is aggregated): new
  scripts/coder_aggregate.py, sha256 `dfb8e6dad6d1585dd99b1519a0eaee9a1fbc1d999583ec0e10ed261ebc4220e2`. It gives
  value counts per coder and flag, parse problems, the verbatim-quote rate and coder A vs B kappa. One more test;
  tests/test_coder_render.py is now `8a498d5870f7aa7352d9c85ac9a43b565d8bba73d02f403eb98094ffd001e7bd`.
- trapflags, 2026-11-11T06:25Z (change 1, after the first full run): presentation and extra counts only; no
  flag definition and no computed value changed. (a) The §1 tables of F1a and F1a-loose are now taken over
  computable or missing slots, and `comb_without_named` over named slots; before, not-computable and
  not-applicable slots were shown in the "missing" column. (b) §3 adds the count of probe_query texts that were
  also sent to an SAE tool. (c) Empty rows are dropped from the F4 count tables. (d) The private T-F2 pass
  listing adds every text pair that varies the main or the decoy. Why: the first output mislabelled
  not-computable slots as missing, and the F4 result (no contradiction anywhere) needs its denominators.
  New sha256 `3a4847f424a6d5393b7b69c1ec179f33e8f0540fbdad4fcb57c6ffc142f7c4bd`; tests
  `5d734ddaf74d899589a38cdad4ca3bb2a4d6ea386db0f93d2becabcb930f2c2f` (one test added for the filter).
- trapflags, 2026-11-11T06:47Z (change 2, by the adversarial verifier): implementation fix in the labelled
  proxy-unit sensitivity of §3 only. `f4_slot` divided both ΔT and ΔP by the unit it was given, so the
  sensitivity put ΔT in the proxy's unit too, against README choice 12 ("ΔP in the proxy's own unit"; ΔT stays in
  the true topic unit). Now `f4_slot` takes an optional `proxy_unit` that rescales ΔP only. The primary F4 call is
  unchanged and every primary, §1, §2 and §4 value is byte-identical (checked by diffing trapflags.json). The
  sensitivity changes from 12 contradicted properties in 11 slots (Haiku 2, larger agents 9 applicable) to 7 in
  7 trap hard slots (Haiku 2, larger agents 5), all F4 = 0; reading (2) stays untestable. Report rerun on the
  same collect and GPU outputs. New sha256 `aef85f7c5be58e39b521cb450fd425c22e355bb45bedb00f754aac7e9248af13`;
  tests `bdcd842490bfccf92539de63f4e339434f946d186f81d43804ef4ca0ba506635` (one test added). Copy and diff in
  `results/private_1112/followup/trapflags/frozen/`.
| scripts/feasibility/bb8_child.py | `d8ff0713918e39d24358d517da405abb26ad32307b43f06eee6f8dd9001b2928` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_common.py | `a41e81f50c5fdf40a01233644188eb2c47afcebd3a734309500da8fe80a16d65` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_dp.py | `cd4d6b2bc617ba21cc5f047164349f0a54b54b7da7b3cd93c832795284ed9b7c` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_dp2.py | `88b0451ee871e0a3e423e55f2c614a4e8f30dbd572c60d7dbc1e45f938a7bc4a` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_dp_check.py | `3120dd8fafdc6a9b51f3ef1f35c532f2898ed5719a1329ede0ef2379061d154b` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_free.py | `3701706daf9da9e3c86968da8e071028637c761a90972b8b6c83cc7b2e3daaa2` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_ranker.py | `f0dae765aacc6bce169f188592f004436289db5e232be110f6e0768792d8d5c1` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_runs.py | `a1b965666c7f447169fe834ac075a13ade5ad9eb4b2d0b68d0fc489be88e3844` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_scan.py | `0ba6a592afb02b9941bfdaceb1a9af2afb194d4cee119c415205b6e7f2d0b36e` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_summ.py | `6741c5ad64ff51fa872234680156707d25dd9057172a807d4a53c9fd2d3e551c` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/bb8_tok.py | `22eeed58b7651b8d9e2064143d5434b8414fabbbb97553a1cf44997c831b8c3f` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_agg.py | `4dd7dcd4dcdb3c5c26eeca83471c6ec50918e375c270c2e3653e50af1e855364` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_basefree.py | `45537d3bb2b93b8c0410e0821998553ba1c322b16c8aeb4e2afb2892692fc054` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_final_msg.py | `0398984ea89495e4c0f40c1a78c169b5852ce76c0dd19d9917eb786c182ac85c` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_noise.py | `2d09dda5bcdca7a18af8e2ee7156d54ed3d968fc490cbf2e929311921aee975f` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_policy.py | `6df9db4c6a8df81400116662eec2bb526367a9e1d79580bef83881652552d009` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_pq.py | `a134c5fce14155fe46b98106ac8418bf53f9702a216b3ebca2132b781f983aa1` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_runs.py | `6f78f714a3219ec61a51d9b6941ceb8925b2cb852d4e150274b47ce28d9f6aec` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_scan_stats.py | `247a130356927838f3552938b23d5e7c1fd7d4c9d96cfa1cf668d105a18600e5` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
| scripts/feasibility/open8_tr.py | `2b0202ea0a9e6607705ad0dbe0acf085ef05e5637186176fc1f6cb309bd08b2a` | 2026-11-11T06:26Z | before first real run (feasibility copy) |
- misc, 2026-11-11T06:33Z: new file scripts/followup_misc_report.py (tables and misc.json from the misc aggregate JSON files only; reads no run, bank or answer), sha256 `804d0f43febf8d33eb83ad2858701b1a748c3d1588ec5e2a71be8f3e74bb95fa`, before its first run.
- misc, 2026-11-11T06:35Z: scripts/followup_misc_report.py docstring wording only (privacy scan hit on an ordinary word); no code change. New sha256 `59529da55a9e9bfc333e50ac72f60322244d08aeb1705dce0124c686eb61f731`.
- misc, 2026-11-11T06:35Z: note on the scripts/exp_f_ci.py row above: this misc instance (section misc, not misc A1) wrote and ran it; its ci and cs rescoring outputs are published in followup/misc/ (exp_f_ci.json). The main session should settle the annotation.
- misc verifier, 2026-11-11T06:47Z: corrected the "first real run" cell of the scripts/exp_f_ci.py row. It used to
  say: "written by a duplicate misc instance (see "misc A1"); its ci rescoring was run in session scratch only and
  is not published; the misc section's own Exp F result is the one to use". That was wrong:
  - the file on disk has the row's hash;
  - the ci scores in session scratch (fu/misc/expf_ci/scores.jsonl, 06:16Z) are byte-identical to
    results/private_1112/followup/misc/exp_f_scores_ci.jsonl. The cs scores are byte-identical to the frozen
    results/private_1112/exp_f/scores.jsonl;
  - followup/misc/exp_f_ci.json and exp_f_ci_tables.md are summaries of those files;
  - no other Exp F rescoring exists. The A1 instance's scratch (fu/misc/mine/expf_cs, 06:17Z) holds only an
    empty cs attempt: links, no scores, empty log.

  So the published Exp F result is the output of this hash. The verifier also recomputed the claude-opus-5-5 level
  table with its own runner, and it matched. No code change.

### bb16 (GPT BB-16 arm: wrapper and run orders; results/blackbox_1112/bb16/PREREG_BB16.md)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/bb16_schedule.py | `1e57f0d121e6a08446edc72b848621d40c6f22c570393309ce72e4f903cf8af9` | 2026-11-11T06:37Z | before the one pilot (ep472-blackbox16); dry runs only so far |
| tests/test_bb16_schedule.py | `18a128087447115bee2b171fa0f604fb034d147b75883b5eae94d617a73e2e78` | 2026-11-11T06:37Z | synthetic only |
| results/blackbox_1112/bb16/runorder_bb16.csv | `ca8d58e32ef49713f311d57e3c3ce51dd00fbc01305aaee9f3af50250e1d3b60` | 2026-11-11T06:37Z | not run (counted order; needs bb16/PREREG_HASH) |
| results/blackbox_1112/bb16/runorder_bb16_pilot.csv | `a9c51e310c9c9179efef8773c3a51da86b8981b0e85db3528ffae2bd5966d2fa` | 2026-11-11T06:37Z | the pilot |
| results/blackbox_1112/bb16/run_order.json | `62ef792c3e17435d3aa74510d8042c47e6a4e4c68adfcc119a27316c7b753776` | 2026-11-11T06:37Z | - |

Change 1 (2026-11-11T07:03Z, checker; implementation fix, after the pilot and before the bb16 hash; no counted run yet).
What: a GPT run held back only by the $1.61 counted per run in flight now waits instead of stopping the arm
(`cap_stop`). The `start` event also records `bb16_prereg_hash_sha256`. Why: the stop rule of PREREG_BB16.md §7 is
spent + 1.61 > 25. The old code could stop the arm earlier (3 slots, $1.00 per run: 23 of 24 started). The rule
itself is unchanged; details are in PREREG_BB16.md §9 "Checker review". New hashes: scripts/bb16_schedule.py
`8c02abd35a6bb8c86213e51fbf4f03ed54e0b35ee321e76abde36343e092f5d2`, tests/test_bb16_schedule.py
`28469b6ae404386a4cfcbd70466633081d26cc47a35b8d5611a70e6c713f284d`. The run orders are unchanged.

### transcripts (DEFINITIONS.md §5 transcript search; written by the main session)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/followup_transcript_search.py | `cf5b43a45a9ed246a652d12cf97a4ee60c213cdd1dafd8b8f7dfa48107d66d06` | 2026-11-11T06:54Z | trap-run search |
| tests/test_followup_transcript_search.py | `0b974ce2c76da9a3dfec1e0113d33ed4dc457e70d9cdb7d9704cf5498e91f02e` | 2026-11-11T06:54Z | trap-run search |

### coders vs mechanical (DEFINITIONS.md §8 agreement and adjudication; exploratory)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/coder_mech_agree.py | `e962c196a5c25e2e7814137f50450a74013f08a5ee09dd510292e3fa044e9632` | 2026-11-11T07:07Z | before first real run (inputs: coders codes_full.jsonl and the verified trapflags private outputs) |
| tests/test_coder_mech_agree.py | `47f89b8169d228eed4c8636862596de7d89d3b723e0ecaf438268cc4c58cf76e` | 2026-11-11T07:07Z | synthetic only |

Mechanical sources: F1 <- F1a (primary on computable slots; "as scored" counts not computable as 0, as D36);
F2 <- D36 F2 on the hard slot (n/a on `none`); T-D <- trapflags T_D; F4 <- trapflags primary F4 (proxy-unit
sensitivity beside it; BB-8/BB-64 have no SAE, F4 undefined). "cannot tell" counts as missing. The adjudication
file is written by hand after reading each disagreement in the transcript; its notes stay private.

### trapflags_samplebase (EXPLORATORY; defined after the T-F2 = 1 reading; main-session code)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/followup_tflags_samplebase.py | `7485bbbc04beac57005ab099a4ca9c25d864a3a5764703fc39578b90c71e1737` | 2026-11-11T07:12Z | trap hard slots |
| tests/test_followup_tflags_samplebase.py | `e64dee587ef36f4da359612dab1be8288e8b771a9db5aa438f06bf876dbda44c` | 2026-11-11T07:12Z | trap hard slots |
- trapflags_samplebase change 1 (2026-11-11T07:12Z), implementation: the cue-count consistency check now applies only to
  slots with recovered texts. Slots without texts store no cue matches, so the check aborted the first run on a
  missing-texts slot before any flag was computed. New sha256 `a02c1307519888979fb7464f61a3028ea592e3ef3f018c7a96c7a1732950eec1`.

- coders vs mechanical, 2026-11-11T07:20Z (after the first real run, which produced the agreement tables and the
  disagreement list; before any adjudication was counted): scripts/coder_mech_agree.py. What: the reason vocabulary
  for adjudication gains `mech_miss_samplebase` (a contrast against a public sample note's logit),
  `mech_coincidental_pair` (a detector-clean pair of two unrelated notes), and splits `definition` into
  `definition_unit` and `definition_scope`; the summary gets a `substance_values` count, an `ambiguous` bucket
  that is not scored, and a `mech_undefined_no_sae` bucket for F4 on runs without SAE. Why: reading the
  disagreements showed these causes, which the first vocabulary could not name. No agreement statistic changed.
  New sha256 `ff78124c49b7eb5e3daf3721f1ef2ac9acb135bd8ba7099db3618503550c0ae4`; tests/test_coder_mech_agree.py
  `3fa5e6956486a3fb58de28ed3d8a683b7e95aaada46c401764934fb29b030419` (one new test). The adjudication itself was
  read by hand; an unfrozen read-only aid in the scratchpad (nearest public sample note per probe_query text,
  detector difference, logit difference in topic units) helped place sample-base contrasts. Its output is
  private.
- trapflags_samplebase change 2 (2026-11-11T07:23Z), a new EXPLORATORY variant beside the first one; the first is unchanged. The coder
  adjudication found that the D36 pairing can accept two unrelated notes as a clean pair. The edit variant
  (T-F2e, T-De, T-RULEe) therefore pairs an agent text only with the sample note it was edited from: its
  nearest note by difflib ratio, if that ratio is at least 0.8. New sha256: script `aff402c78d0b8d73a5c12d2f94c1876282ea746193ec351f75bfaed430fa53ae`, tests `3e6fc33b76171bc619783bed5375b4cae35bd778931c64d0a9ff23fcc91be038`.

- hardercue, 2026-11-11T07:30Z: stopped with no accepted probe (README "Results"). scripts/hc_heldout.py and
  scripts/hc_solver.py were never run on real data and are unchanged from the hashes above. Stage D was extended
  to 18 jobs at 07:02Z and stopped after 14; stage C was stopped after 1 job (README choices 11-12).

### topicunit_flags (EXPLORATORY; defined after the solvers' unit finding; main-session code)

| file | sha256 | frozen (UTC) | first real run |
|---|---|---|---|
| scripts/followup_topicunit_flags.py | `d19daab3f2885115a84886b47232b9b7b27ed4995815bcf0dea645152e81ec22` | 2026-11-11T07:33Z | F1a and F4 with the topic unit |
| tests/test_followup_topicunit_flags.py | `c65724c1bef3844556d28831b0be3c47f2dc499d126049dc57a922d50105e082` | 2026-11-11T07:33Z | F1a and F4 with the topic unit |
