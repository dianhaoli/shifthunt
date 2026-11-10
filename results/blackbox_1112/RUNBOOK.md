# Black-box study: runbook

Exact commands for the agent runs of `docs/EXPERIMENT_PLAN_BLACKBOX.md` (rev 2.2): firewall, image, private
tree, image check, pilots, Block 1, Block 2, scoring. Everything runs on the GPU box. Times are UTC.

Never: print a key or `docker inspect` environment output; delete or prune a container or an image (the
stopped containers are the only copy of some run state); overwrite an image tag other than
`rl-task-shifthunt-r1112`; start a counted run before `PREREG_HASH` is committed.

```bash
export PUB=/home/ec2-user/shifthunt-public                       # this repository
export PRIV=/home/ec2-user/onsite/sub/tasks/shifthunt            # private harness tree (branch research-1112)
export PY=/home/ec2-user/onsite/grader-wt/.venv/bin/python
export RES=$PUB/results/blackbox_1112
```

The scheduler is always started from `$PRIV` with the environment file sourced:

```bash
cd $PRIV && source scripts/r1112_env.sh      # keys from the box's .env, RL_TASK_IMAGE_SUFFIX=-r1112, CODEX_EFFORT=max
SCHED="$PY -u $PUB/scripts/blackbox_schedule.py --tag r1112 --task-dir $PRIV --results $RES --cap-openai 800 --cap-anthropic 130"
```

## 1. Network isolation (once per boot)

```bash
cd $PUB && scripts/blackbox_net_isolation.sh           # installs what is missing, then checks
cd $PUB && scripts/blackbox_net_isolation.sh --check   # check only; exit 1 if the rules are not exactly these
```

Expected chain `DOCKER-USER`: two OpenAI tcp/443 ACCEPTs, the Anthropic range ACCEPT, REJECT (all on the
`anthropic_only` bridge), RETURN. The scheduler's preflight runs the check; the launcher refuses to start a
container without the REJECT rule.

## 2. Image and private tree (after every commit that changes image code, the collector or the env file)

```bash
cd $PUB && git log -1 --format=%H                      # the commit to build from: <commit>
docker_research_bb/build.sh --plan <commit>            # what the layer would replace; builds nothing
docker_research_bb/build.sh <commit>                   # build, verify, tag rl-task-shifthunt-r1112 (label shifthunt.commit)
PY=$PY scripts/blackbox_sync_private.sh <commit>       # private tree: replaced image files, collector, env file, problems.txt
PY=$PY scripts/blackbox_sync_private.sh --check <commit>   # read-only; this is what the preflight runs on HEAD
```

`build.sh` is only needed when `--plan` lists a file to copy (the image is current otherwise). The sync is
needed whenever `scripts/collect_rollouts.py` or `docker_research_bb/r1112_env.sh` changed in a commit: the
launcher runs the private copy. Nothing is committed in the private tree by these scripts. Before a commit,
`PY=$PY scripts/blackbox_sync_private.sh --worktree scripts/collect_rollouts.py HEAD` copies the collector of
the working tree (it says so loudly); the preflight's `private_sync` then fails until that collector is
committed, because it compares the private copy with the public HEAD.

## 3. Image check (zero API, GPU)

```bash
cd $PUB && $PY scripts/blackbox_image_check.py --quick   # ep411 and ep472, about 10 min
cd $PUB && $PY scripts/blackbox_image_check.py           # all 24 PROBLEMs and the oracle runs, about 30 min
```

It takes `/tmp/shifthunt-gpu.lock` itself (do not wrap it in `flock`) and must not run while rollouts run.
Reports: `image_check/report.md`, `image_check/report_quick.md`. Every line must pass before a pilot.

## 4. Tests

```bash
cd $PUB && $PY -m pytest tests -q -p no:cacheprovider --ignore=tests/test_substrate_gpu.py --ignore=tests/test_toolserver_gpu.py
```

## 5. Pilots (4 runs, excluded from every analysis)

Dry run first: it runs the real preflight read-only, on the real `ledger.jsonl` and `RUNLOG.md`, and then the
whole control flow with a fake launcher and a simulated clock. It launches nothing and writes only into a new
temporary directory, whose name it prints (`--dry-run-dir <dir>` chooses it; a directory that already holds a
dry run is refused, because its simulated spend would be read back).

```bash
cd $PRIV && source scripts/r1112_env.sh
$SCHED --runorder $RES/runorder_pilots.csv --pilot --dry-run
```

Every preflight line must say `ok` (the dry run lists what a real start would abort on); the lines after
`== dry run` are simulated. Then the real start, detached; its output is the ledger events plus `# waiting`
notes:

```bash
cd $PRIV && source scripts/r1112_env.sh
(setsid nohup $SCHED --runorder $RES/runorder_pilots.csv --pilot \
    > results/rollouts/r1112_sched_pilots.log 2>&1 < /dev/null &)
tail -f results/rollouts/r1112_sched_pilots.log
```

Run directories: `$PRIV/results/rollouts/r1112_pilot_{gpt_open8,gpt_bb8,gpt_bb64,haiku_bb8}/<cid12>/`.
When all four are recorded (the scheduler prints its summary and exits 0):

```bash
cd $PRIV && source scripts/r1112_env.sh
$PY $PUB/scripts/blackbox_pilot_check.py results/rollouts/r1112_pilot_gpt_open8 results/rollouts/r1112_pilot_gpt_bb8 \
    results/rollouts/r1112_pilot_gpt_bb64 results/rollouts/r1112_pilot_haiku_bb8 \
    --md $RES/pilot_check.md --json $RES/pilot_check.json
```

Exit 0 means no check failed. The tables show, per run: episode id and arm; that `/task.txt` holds the help
text and the arm's budget; model, effort and CLI version; refused SAE calls (black-box); `probe_query` used =
texts in the full-text log = tool-log charges; hash agreement of the full-text log; the naming keys of
`grade.json` and NAME from `score_naming.py`; USD with its source, tokens, wall minutes; the launcher's
`isolated=True` reading; and the BB-64 / BB-8 / Open-8 ratios. The `submit_refusals` note counts refusals for
a missing `latents` key (DECISIONS D21). Only implementation bugs may be fixed after a pilot (plan §0 rule 5).
A pilot can be repeated by starting the same command again only if its job is not recorded; to repeat a
recorded pilot, add a row to a new run-order file in `$RES` (for example `runorder_pilots2.csv`) and run that.
For pilots and blocks alike the preflight's `runorder` line fails unless `--results` is this repository's
`results/blackbox_1112` and the run order is a regular file in it (a symbolic link is refused).

Before the hash: validate the S3 detectors on the pilots' logged texts (`scripts/s3_coder.py --raw <pilot run
directories> --validate-sample 50 --out <private directory>`, see its docstring).

## 6. Pre-registration hash (before the first counted run)

`PREREG_HASH` is the output of `sha256sum`, run from the repository root, over `prereg.md`, both run-order files
and the five scripts `prereg.md` defers to. Paths are relative to the repository root; the file holds nothing
else (no comment lines, no CR LF line ends).

```bash
cd $PUB && git status --short                     # everything pending is about to be committed: read the list
$PY -m pytest tests -q -p no:cacheprovider --ignore=tests/test_substrate_gpu.py --ignore=tests/test_toolserver_gpu.py
sha256sum results/blackbox_1112/prereg.md results/blackbox_1112/runorder_block1.csv results/blackbox_1112/runorder_block2.csv \
    scripts/score_naming.py scripts/blackbox_analysis.py scripts/s3_coder.py scripts/collect_rollouts.py scripts/blackbox_schedule.py \
    > results/blackbox_1112/PREREG_HASH && cat results/blackbox_1112/PREREG_HASH       # 8 lines
git add -A && git status --short                  # prereg.md, PREREG_HASH and every other pending file, in ONE commit
git commit -m "blackbox study: pre-registration and its hash"
sha256sum -c results/blackbox_1112/PREREG_HASH    # every line OK, on the committed tree
git status --short                                # empty
cd $PRIV && source scripts/r1112_env.sh && $SCHED --runorder $RES/runorder_block1.csv --check-prereg   # "ok   prereg: all 8 files ..."
```

Then section 2 for the new commit (`build.sh --plan`, `build.sh` if it lists a file to copy, the sync and its
`--check`), section 3 again if the image was rebuilt, and the block's dry run (section 7): its `prereg` line
must be `ok`.

`--check-prereg` runs the preflight's `prereg` check alone and exits 0 or 1; it starts and writes nothing. The
preflight of a non-pilot block (Block 1 and Block 2 alike) refuses to start unless all of this holds:

- `PREREG_HASH` is in exactly this format. The format written by the earlier version of this section (run
  inside `$RES`, bare file names, no scripts) is refused with a message that says so;
- it has an entry for `prereg.md`, for **both** run-order files (so Block 2's order is fixed before Block 1
  starts) and for each of the five scripts;
- **every** file it lists is a regular file (no symbolic link) with the recorded SHA-256;
- every such file, and `PREREG_HASH` itself, is byte for byte the file that `HEAD` holds, and `git status` shows
  no change for it, staged or not. A git command that fails is a failed check;
- the process that runs is the listed code: the scheduler file it was started from and the collector next to
  it have the recorded SHA-256 (a copy of the scheduler somewhere else is refused if it differs).

The scheduler's `start` event records the SHA-256 of `PREREG_HASH` (`prereg_hash_sha256`) next to the image id
and commit; copy the three into `RUNLOG.md` or `DECISIONS.md` at the first start of Block 1.

**A change after the hash.** Editing `prereg.md`, a run-order file or one of the five scripts after
`PREREG_HASH` is committed is a logged deviation (prereg, first paragraph); it never applies to runs already
counted. The preflight then fails (`sha256 differs from PREREG_HASH for: <file>`) and no block starts or
restarts until this is done, in this order:

1. stop the scheduler if it runs (section 7); running rollouts finish and are collected by their launchers;
2. write a `DECISIONS.md` entry: which file, why, the old and the new `sha256sum` line of that file, the time,
   and how many runs were already counted (`$SCHED --runorder ... --summary`);
3. write `PREREG_HASH` again with the command above (the whole file; a second line for the same path is
   refused) and commit it together with the changed file and `DECISIONS.md`;
4. section 2 if the collector or image code changed, then `--check-prereg`, the dry run, then the restart.

The run-order file of a block that has started can never change: the scheduler refuses to continue that block
(`block 'block1' was started with another run-order file`), whatever `PREREG_HASH` says, and there is no
procedure for it. Cuts are made with `--cut` (section 7), never by editing the file. The steps above apply to
a run-order file only before its block's first start (for example Block 2's order while Block 1 runs).

The old hashes stay in git history: `git log -p -- results/blackbox_1112/PREREG_HASH` lists every version with
its commit, and each `start` event in `ledger.jsonl` says under which version that scheduler process ran. A
start under another `PREREG_HASH` than the block's last start says so (a `# PREREG_HASH is not the file of
this block's last start` line and `prereg_hash_previous` in the `start` event), and `--summary` then prints
`CHANGED between starts`: each such change must have its `DECISIONS.md` entry.

## 7. Block 1 (108 runs: GPT and Haiku, Open-8 / BB-8 / BB-64; about 12 to 13 h)

```bash
cd $PRIV && source scripts/r1112_env.sh
$SCHED --runorder $RES/runorder_block1.csv --dry-run          # preflight (real ledger and RUNLOG.md) must be all ok
(setsid nohup $SCHED --runorder $RES/runorder_block1.csv \
    > results/rollouts/r1112_sched_block1.log 2>&1 < /dev/null &)
```

Watching:

```bash
tail -f $PRIV/results/rollouts/r1112_sched_block1.log       # ledger events; `# ... waiting:` lines say what it waits for
$SCHED --runorder $RES/runorder_block1.csv --summary        # counts by status and cell, spend, flags
tail -5 $RES/RUNLOG.md                                      # one row per ended run, cumulative USD per provider
docker ps --format '{{.ID}} {{.Image}} {{.Status}}'         # at most 3 task containers
```

Run directories: `$PRIV/results/rollouts/r1112_{gpt,haiku}_{open8,bb8,bb64}/<cid12>/`; each launcher's own log
is `launch_sched_block1_o<order>_a<attempt>.log` in the batch directory.

**Stop and restart.** `pkill -TERM -f blackbox_schedule.py` ends the scheduler only; running rollouts go on and
are collected by their launchers. Start it again with the same command: recorded jobs are skipped and a
launcher that is still alive keeps its slot and is recorded when it ends. A job whose launcher is gone is
looked up in its run directory and in its own runner log (`launch_<problem>_<unix time>.log`, which names the
container as soon as it runs):

- its container is still running (launchers killed, e.g. `pkill -f launch_rollouts`): the job keeps its slot,
  nothing is recorded or re-queued, and the scheduler collects the container itself when it has ended;
- its container has ended (host reboot, or it finished meanwhile): it is collected and classified from its
  files. With a submission it is `ok` or `needs_regrade` and is never re-run. Without one it is an
  infrastructure failure with its real cost and its id in `infra_failures.jsonl`: `interrupted` if the
  container was cut off before its grader ran, `no_grade` otherwise;
- no container was started: `interrupted`, cost 0.

`interrupted` uses one of the job's 2 re-runs (prereg §7) but does not count toward `infra_stop`. The restart
refuses to go on only if a job has no container on record while the host runs more task containers than the
scheduler can account for. After a reboot, do section 1 first. Two schedulers cannot run on one ledger. A
`kill -9` of the scheduler is safe too: it writes a `launching` event before it starts a launcher and finds that
process again by its log file, and no run's cost is written to `RUNLOG.md` twice.

**What the scheduler does by itself.**

| Event | Meaning | Action |
|---|---|---|
| `infra` + `requeued` | no accepted submission and: no container, no `grade.json`, or an API error that ended the agent (below). Listed in the batch's `infra_failures.jsonl` with its reason and error message, cost counted, re-run at the end (at most 2 re-runs) | none |
| `# ... its runner started container <cid>, which has not ended yet` | a launcher or runner died but its container runs on: the job keeps its slot until the container has ended, then it is collected and classified (flag `runner_died`). It is never treated as "no container" | none |
| `gave_up` | third infrastructure failure of one job | report it; the cell stays one run short |
| pause | after an `infra` event with reason `api_error` that provider's launches wait 15 min; the queue keeps its order | none |
| `infra_stop` | 3 consecutive infrastructure failures of one provider (API error, no `grade.json`, no container; not `interrupted`): its remaining jobs are skipped, the other provider goes on. A job of that provider that was still running and then fails is skipped too, not re-queued | fix the cause (key, credit, firewall), start again |
| `cap_stop` | ledger + estimate would pass cap − $5 for that provider: its remaining jobs are skipped, also those that were still running and then failed | ask the user before raising a cap, then start again with the new `--cap-*` |
| `usd_stop` | a collected run reported a cost that is not a finite number ≥ 0: that provider's remaining jobs are skipped | find out why (price list, collector); correct the run's cost by hand in `RUNLOG.md` and DECISIONS.md, start again |

**"An API error ended the agent"** (prereg §7 item 3; only for a run without an accepted submission):

- Haiku (Claude Code): the collector's `harness_status` is `api_error`, i.e. a transcript message flagged
  `isApiErrorMessage` holds one of the six provider error strings (the main study's rule, unchanged). The
  matched string is the event's `message`.
- GPT (Codex): `codex_events.jsonl` has a `turn.failed` event, or its last event is an `error` event, and the
  failure message is neither a context-window / token-limit message nor a refusal on content grounds. The
  collector classifies the stream (`agent_error` in the summary row: `terminal`, `kind` = `api` / `context` /
  `refusal`, `type`, `message`, `n_error_events`; the pre-registered message patterns are the
  `AGENT_ERROR_*_PATTERNS` constants of `scripts/collect_rollouts.py`) and the scheduler re-runs the job iff
  `terminal` and `kind` is `api`. `harness_status` is not the rule for GPT: it says `api_error` for any `error`
  event, also one the CLI recovered from. "Last event" is the last line of the file that parses as a JSON
  object; a torn last line is ignored. The message rule, in this order: a message that names a rate limit,
  a quota or billing ("tokens per min (TPM)", "daily token limit", "Usage limit reached") is an API error
  whatever else it says; else a context-window or token-limit message (also "reason: max_output_tokens" and
  "token budget exhausted") is the agent's own failure; else a refusal on content grounds is ("flagged",
  "content_filter", "policy violation", "Invalid prompt", "for safety reasons", "refused"), where a refused connection
  ("Connection refused", `ECONNREFUSED`), a server or gateway that refused a request, and Codex's own
  "refusing to ..." about a local file are not refusals; every other message, and none at all, is an API
  error.
- Two flags on such a GPT `infra` event say how the stream ended; neither changes the status:
  `codex_trailing_error` (no `turn.failed`; only the stream's last event, an `error` event, made it a
  failure) and `api_error_at_timeout` with `manual_look` (the 5400 s stop ended the run: the stream ends
  wherever the killed CLI was, for example in a "Reconnecting..." event). The job is re-run as pre-registered.

Every excluded run is in the ledger (`infra` event: `cid`, `reason`, `message`, `flags`) and in its batch's
`infra_failures.jsonl` (`cid`, `reason`, `message`); `--summary` prints one `excluded:` line per run, with its
flags. Messages are cut to 300 characters, and anything that looks like a key, a token or an account id is
removed before a message is stored (also any run of 24 or more characters that has both a letter and a digit,
so a request id goes too; the whole event stream stays in the private run directory).

**Statuses that need a person** (`--summary` lists them under `flagged`):

| Status or flag | Meaning | Action |
|---|---|---|
| `fail:no_submission` with `daemon_died` or `no_agent_activity` | counted fail by the pre-registered rule | read the run's logs; do not re-run |
| `ok` with `api_error_after_submit` or `timeout_after_submit` | counted, graded on the accepted submission | none; never re-run |
| `fail:*` with `agent_error_context` or `agent_error_refusal` (GPT) | the Codex turn failed and the message says the context window or a token limit was exceeded, or the request was refused on content grounds: the agent's own failure, a counted fail | read `message` in the ledger event and the end of the run's `codex_events.jsonl`; if the message is in fact a provider failure that the patterns misread, do not re-run by hand: log it in DECISIONS.md as a deviation first |
| `fail:*` with `codex_error_recovered` (GPT) | the stream has an `error` event but the CLI went on afterwards (a retry that worked), and the run ended without a submission for another reason: a counted fail | read the run's `codex_events.jsonl` after the last `error` event; do not re-run |
| `fail:*` with `agent_error_unknown` (GPT) | `harness_status` says `api_error` but there is no readable `agent_error` and no `codex_events.jsonl` in the run directory | find the event stream (collect again); decide by hand and log it in DECISIONS.md |
| `infra:no_grade` with one of the three flags above | no `grade.json`: re-run as `no_grade`, whatever the stream says | none |
| `infra` event, reason `api_error`, with `api_error_at_timeout` (GPT; in the `excluded:` lines) | the hard stop ended the run while the stream's last event was an `error` event, or after a `turn.failed`: an infrastructure failure by the pre-registered rule, re-run | read the end of the run's `codex_events.jsonl` and note in `SUMMARY.md` what the CLI was doing; do not change the status |
| `ok` with `codex_error_recovered`, `agent_error_context` or `agent_error_refusal` | a submission was accepted: counted on it | none; never re-run |
| `needs_regrade` | a submission was accepted but the grader left no `grade.json` | regrade offline from the run directory (`submission.json`, `perm.npy`, `answer.json`); never re-run |
| `usd_unknown` | the collector found no cost for a collected run (`usd` null: "no usage data", e.g. the Codex session files were not copied, or the agent never made a request). The job's estimate (`--est-gpt`, `--est-haiku`) was counted instead; `usd_reported` and `usd_source_reported` in the ledger event say what the collector gave | read the run's files; if the real cost can be worked out, add a correcting row to `RUNLOG.md` and note it in DECISIONS.md |
| `unknown:collect_failed` | the container ended but nothing was collected | `cd $PRIV && $PY scripts/collect_rollouts.py <cid> --out results/rollouts/<batch>`, then start the scheduler again: it records the run |
| `unknown:container_missing` | a runner log names a container that docker no longer has, and nothing of it was collected | find out who removed it; the job is not re-run by itself. Decide by hand and log it in DECISIONS.md |
| `unknown:duplicate_cid`, `unknown:ambiguous_runner_logs` | a container could not be tied to one job (an id already recorded for another job; two runner logs of one PROBLEM in one job's time window, e.g. a launch by hand into the batch directory) | look at the batch's `launch_*.log` files; decide by hand and log it in DECISIONS.md |
| `arm_mismatch`, `episode_mismatch`, `model_mismatch` | the collected run is not what the job asked for | stop the block and find out why |

**Cut order (prereg §3, time only).** If Block 1 cannot finish by Nov 14 12:00 UTC: stop the scheduler and
start it again with the cuts, in this order, as far as needed. A cut skips only jobs that have not started,
from the end of the committed order, and is final.

```bash
$SCHED --runorder $RES/runorder_block1.csv --cut haiku:bb64                                  # 1. Haiku BB-64
$SCHED --runorder $RES/runorder_block1.csv --cut haiku:bb64 --cut haiku:open8:1 --cut haiku:bb8:1   # 2. Haiku Open-8, BB-8: 1 per item
```

(start it detached as above). GPT Open-8 and GPT BB-8 are never cut.

**After the block.** Every job must be recorded (`--summary`: recorded 108, nothing flagged `unknown`). Check
that no container was left uncollected: the number of containers created from the image must equal the number
of container ids in the ledger (pilots included: they share the ledger; if the image was rebuilt after the
pilots, their containers belong to the earlier image id and are not listed by the first command).

```bash
docker ps -a --filter ancestor=rl-task-shifthunt-r1112 --format '{{.ID}}' | sort -u | wc -l
$PY -c "import json,sys; print(len({e['cid'] for e in map(json.loads, open(sys.argv[1])) if e.get('cid') and not e.get('dry_run')}))" $RES/ledger.jsonl
```

## 8. Scoring, the Open-64 trigger, analysis

First check that the scripts about to be used are the pre-registered ones. Nothing else checks this after a
block has ended: the block's preflight ran before the data existed.

```bash
cd $PRIV && source scripts/r1112_env.sh && $SCHED --runorder $RES/runorder_block1.csv --check-prereg   # "ok   prereg: ..."
cd $PUB && sha256sum -c results/blackbox_1112/PREREG_HASH                                           # every line OK
git status --short -- scripts results/blackbox_1112/prereg.md results/blackbox_1112/PREREG_HASH \
    results/blackbox_1112/runorder_block1.csv results/blackbox_1112/runorder_block2.csv            # prints nothing
```

If one of the three fails, a hashed file was changed after the hash: do not score with it. Either restore the
committed file (`git diff` shows the change), or follow "A change after the hash" in section 6 (DECISIONS
entry, new `PREREG_HASH`, commit) and say in `SUMMARY.md` which runs were scored with which version. Run the
check again before every later scoring or analysis run (after Block 2 as well).

```bash
cd $PUB
$PY scripts/score_naming.py --raw $PRIV/results/rollouts --study r1112 --public \
    --csv $RES/rows_r1112.csv --json $RES/naming_r1112.json
$PY scripts/s3_coder.py $(for d in $PRIV/results/rollouts/r1112_{gpt,haiku}_{open8,bb8,bb64,open64}; do [ -d $d ] && echo --raw $d; done) \
    --out-csv $RES/s3_r1112.csv --private-out results/private_1112/s3      # a git-ignored directory of $PUB
$PY scripts/blackbox_analysis.py $RES/rows_r1112.csv --s3 $RES/s3_r1112.csv --ledger $RES/ledger.jsonl \
    --out-md $RES/analysis.md --out-json $RES/analysis.json
```

Check the three commands against each script's `--help` before running them (`--s3` and `--ledger` of
`scripts/blackbox_analysis.py` and the options of `scripts/s3_coder.py` were added or changed while this
section was written; `analysis_dryrun/COMMANDS.md` has the analysis command as its author wrote it). `--s3`
joins the S3 coder's CSV to the rows on (batch, run). `--ledger` ties every counted run to its job and attempt,
adds the first-attempt sensitivity analysis (DECISIONS D24.2) and the table of excluded runs per agent, arm and
reason, and exits 1 if the rows and the ledger disagree: a `needs_regrade` or `unknown:*` job must be settled
first (section 7), and the ledger must hold no dry-run event. The error message of each excluded run is the
`message` of its `infra` event and of its line in `infra_failures.jsonl`; `$SCHED --runorder
$RES/runorder_block1.csv --summary` lists them (`excluded:` lines) for `SUMMARY.md` (prereg §7).

`score_naming.py --study r1112` reads only the batches `r1112_{gpt,haiku}_{open8,bb8,bb64,open64}` (pilots are
left out by name), excludes the runs listed in `infra_failures.jsonl` that have no accepted submission, and
exits non-zero if a cell has more counted runs than planned or a run disagrees with its batch directory. A GPT
run without a submission that the scheduler counted as a fail although `harness_status` is `api_error` (flags
`codex_error_recovered`, `agent_error_context`, `agent_error_refusal`) is not in `infra_failures.jsonl`, so
the scorer counts it as a fail as well; it may print a note that such a run is not listed, which is as
intended for these flags. The analysis report states the Open-64 trigger: Block 2 runs iff rate(GPT BB-64) ≤
rate(GPT Open-8) − 0.20.

Public copies of the per-batch summaries (no cue names), as for the main study. In `probes_public.jsonl` a
black-box run's records carry the naming grade it was scored on (`naming_only: true`, no `margin`, no `kept`):
the latents of a black-box run are not graded, so no margin is published.

```bash
cd $PRIV && for d in results/rollouts/r1112_{gpt,haiku}_{open8,bb8,bb64,open64}; do
    [ -d $d ] || continue; mkdir -p $PUB/$d
    cp $d/summary_public.jsonl $d/probes_public.jsonl $PUB/$d/
    [ -f $d/infra_failures.jsonl ] && cp $d/infra_failures.jsonl $PUB/$d/
done
```

Commit `RUNLOG.md`, `ledger.jsonl`, the rows, the analysis and these summaries. Raw run directories,
`summary.jsonl` and the launch logs stay in the private tree.

## 9. Block 2 (GPT Open-64, 24 runs; only if triggered)

```bash
cd $PRIV && source scripts/r1112_env.sh
$SCHED --runorder $RES/runorder_block2.csv --dry-run          # preflight (real ledger and RUNLOG.md) must be all ok
(setsid nohup $SCHED --runorder $RES/runorder_block2.csv \
    > results/rollouts/r1112_sched_block2.log 2>&1 < /dev/null &)
```

Its preflight is Block 1's (section 6): `PREREG_HASH` unchanged since the hash, with both run-order entries.
Then section 8 again (the same commands, the check first; the `open64` batch is picked up by name).

## 10. Scheduler reference

- Order: jobs start strictly in the order of the run-order file; at most 3 launchers alive (`--max-slots`), at
  least 90 s between container launches (`--gap`), and a job is not started before the previous job's launcher
  has started its container. Infrastructure re-runs go to the end of the queue.
- Each job is one child of the private `scripts/launch_rollouts.py` with one problem and the main study's
  settings (`--max-concurrent 1 --stagger 0 --max-host-containers 3 --timeout 5400 --mem-limit 4G --cpu-limit 2
  --cap-usd 15 --est-usd 3`), so the launcher's own gates (RAM, GPU memory, disk, firewall rule, pause file)
  still apply before every container.
- Preflight (a real start aborts on any failure; env names only are printed): run-order file and `--pilot`
  agree; `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENAI_API_IP`, `RL_TASK_IMAGE_SUFFIX` set, `CODEX_EFFORT=max`
  and `OPENAI_PRICES` equal to the study's `1.0,0.05,1.25,5.0`; image `rl-task-shifthunt-r1112` exists with a clean `shifthunt.commit` label; every
  PROBLEM is a line of the private `problems.txt`; launcher, collector and runner present; private tree in
  sync with the image and the public HEAD; firewall rules; `--results` is this repository's
  `results/blackbox_1112` and the run order is a regular file in it; (blocks) every file listed in `PREREG_HASH`
  (`prereg.md`, both run orders, the five scripts) has its recorded SHA-256 and is the file `HEAD` holds, and
  the running scheduler and collector are the listed ones (section 6; `--check-prereg` runs this check
  alone); `RUNLOG.md` present; projected spend per provider (cumulative + estimate × remaining
  jobs, `--est-gpt 1.5`, `--est-haiku 2.5`) within the cap.
- Spend: cumulative USD per provider is the last row of `RUNLOG.md`, re-read before every launch and every
  row, so rows appended by other tools (Exp D) count. GPT cost is Codex tokens × `OPENAI_PRICES`; Haiku cost is
  Claude Code's `total_cost_usd` (the collector's `usd`, `usd_source`). A collected run without a cost is
  counted at the job's estimate (`usd_unknown`). A cumulative cell of `RUNLOG.md` that is not a finite number
  ≥ 0 (a hand-written `nan`) is read as infinite: that provider stops with a `cap_stop` until the row is
  corrected.
- State: `ledger.jsonl` (append-only events; pilots, Block 1 and Block 2 share it and are kept apart by the
  `block` field) and `RUNLOG.md`. A `launching` event is written before each launcher is started and a
  `launched` event (with its pid) after. A dry run writes neither file; its preflight reads both.
- Infrastructure failures: no container, no `grade.json`, or an API error that ended the agent (section 7: per
  harness; for GPT the collector's `agent_error`, not `harness_status`). `infra` events and
  `infra_failures.jsonl` carry the failure message; the event's flags say when the hard stop ended the run. The 15-minute pause follows every `infra` event with
  reason `api_error`; three consecutive infrastructure failures of one provider stop it (`infra_stop`).
