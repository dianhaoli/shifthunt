#!/usr/bin/env python3
"""BB-16 arm (results/blackbox_1112/bb16/PREREG_BB16.md): Block 1's scheduler, unchanged, with one more arm.

    # the run orders (pure function of the seed "bb16-1111"); --check compares the files with a fresh build
    $PY $PUB/scripts/bb16_schedule.py runorder [--check]
    # the scheduler: exactly scripts/blackbox_schedule.py's command line (RUNBOOK sections 5 and 7)
    cd $PRIV && source scripts/r1112_env.sh
    $PY -u $PUB/scripts/bb16_schedule.py --runorder $RES/bb16/runorder_bb16_pilot.csv --pilot --tag r1112 \
        --task-dir $PRIV --results $RES --cap-openai 800 --cap-anthropic 130 [--dry-run | --summary | --check-prereg]
    # the pilot check of Block 1 (scripts/blackbox_pilot_check.py) with the arm bb16 known
    $PY $PUB/scripts/bb16_schedule.py pilot-check <run or batch dirs> [--md out.md] [--json out.json]

scripts/blackbox_schedule.py is covered by Block 1's PREREG_HASH and is not edited. This wrapper imports it and
changes only these things, in this process:

  arm             PROBLEM_SUFFIX gains "bb16": "-blackbox16" (read_runorder, --cut). blackbox_runorder.py gains the
                  same suffix and a block "bb16" (GPT, arm bb16, 4 runs per item) for the run-order build.
  run orders      in results/blackbox_1112/bb16/ (not directly in results/blackbox_1112/): runorder_bb16.csv (24
                  counted jobs, block "bb16") and runorder_bb16_pilot.csv (one pilot, block "bb16_pilot").
                  study_paths_problem accepts a run order there; --results must still be results/blackbox_1112, so
                  the ledger (ledger.jsonl) and RUNLOG.md are Block 1's, shared, and kept apart by the block key.
                  Every job of a run order given to this wrapper must be GPT in arm bb16 (preflight `bb16_jobs`).
  spend           prereg section 7: OpenAI cap $25 for this arm, pilot included; no run starts if
                  spent + $1.61 > $25. "spent" is the sum of the usd column of the RUNLOG.md rows whose arm is
                  `bb16` or `bb16 (pilot)`. The scheduler's own rule is kept and fed with an effective cap:
                  before every launch try, cap_openai = min(--cap-openai - 5, cum_openai - spent + 25) and
                  CONTINGENCY = 0, so its test  cum_openai + est x (running + 1) > cap  reads
                  spent + 1.61 x (running GPT jobs + 1) > 25. A running job is counted at $1.61 until its row is
                  written, so the cap holds with 3 jobs in flight. A job held back only by the jobs in flight
                  (spent + 1.61 <= 25 < spent + 1.61 x (running + 1)) waits for them; it does not stop the arm,
                  so the only arm stop is spent + 1.61 > 25 (checker fix 1). --est-gpt is 1.61 (given by this wrapper; any
                  other value is refused). The preflight's `spend:openai` line (study-wide cap) is kept and a line
                  `spend:bb16` is added: spent + 1.61 <= 25 (the next run may start), with the projections.
  prereg          a counted block (no --pilot) needs BOTH Block 1's check (scripts/blackbox_schedule.py
                  check_prereg, run as for runorder_block1.csv: every file of PREREG_HASH unchanged and committed,
                  this process runs the listed scheduler and collector) AND results/blackbox_1112/bb16/PREREG_HASH:
                  `sha256sum` output from the repository root over at least PREREG_BB16.md, runorder_bb16.csv,
                  run_order.json and scripts/bb16_schedule.py, every listed file with that hash and committed, and
                  this process runs the listed wrapper. Pilots skip both, as in Block 1.
  ledger          the `start` event also carries wrapper (path), wrapper_sha256, arm_cap_usd, arm_est_usd,
                  arm_spent_usd and bb16_prereg_hash_sha256 (null while bb16/PREREG_HASH does not exist);
                  `launched` and `cap_stop` events carry arm_spent_usd.

Nothing else changes: launcher command and settings, the 3-slot / 90 s gap order, classification, API-error rule,
re-runs, pauses, stops, run directories (r1112_gpt_bb16, pilot r1112_pilot_gpt_bb16) and RUNLOG rows.
"""
import csv
import dataclasses
import hashlib
import io
import json
import math
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import blackbox_runorder as R  # noqa: E402
import blackbox_schedule as BS  # noqa: E402

ARM = "bb16"
SUFFIX = "-blackbox16"
AGENT = "gpt"
RUNS_PER_ITEM = 4
SEED_TEXT = "bb16-1111"
SEED = int.from_bytes(hashlib.sha256(SEED_TEXT.encode()).digest(), "big")  # numpy SeedSequence takes any int >= 0
PILOT_ITEM = "ep472"
ARM_CAP_USD = 25.0
ARM_EST_USD = 1.61   # prereg section 7: BB-8's largest cost per run in Block 1
BB16_DIR = f"{BS.STUDY_RESULTS}/bb16"
RUNORDER = "runorder_bb16.csv"
PILOT_RUNORDER = "runorder_bb16_pilot.csv"
RUNORDER_JSON = "run_order.json"
HASHFILE = "PREREG_HASH"   # results/blackbox_1112/bb16/PREREG_HASH (not Block 1's file of the same name)
WRAPPER_REL = "scripts/bb16_schedule.py"
HASH_REQUIRED = (f"{BB16_DIR}/PREREG_BB16.md", f"{BB16_DIR}/{RUNORDER}", f"{BB16_DIR}/{RUNORDER_JSON}", WRAPPER_REL)

# ---- the arm, in both modules
BS.PROBLEM_SUFFIX[ARM] = SUFFIX
R.PROBLEM_SUFFIX[ARM] = SUFFIX
R.BLOCKS[ARM] = [(AGENT, (ARM,), RUNS_PER_ITEM)]


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------
# run orders

def counted_rows():
    """The 24 counted jobs: Block 1's method (fixed listing order agent, arm, item, rep, then one permutation
    from numpy.random.default_rng(SEED)), SEED = the SHA-256 of "bb16-1111" read as a big-endian integer."""
    return R.run_order(ARM, SEED)


def pilot_rows():
    return [dict(R._row(AGENT, ARM, PILOT_ITEM, 1), order=1)]


def runorder_json(rows, pilot_rows_):
    csv_text, pilot_text = R.to_csv(rows), R.to_csv(pilot_rows_)
    return {
        "arm": ARM, "agent": AGENT, "problem_suffix": SUFFIX, "runs_per_item": RUNS_PER_ITEM, "items": list(R.ITEMS),
        "seed_text": SEED_TEXT, "seed_int": str(SEED),
        "seed_rule": "int.from_bytes(sha256(seed_text).digest(), 'big'); rows in the fixed order (agent, arm, item, "
                     "rep), then numpy.random.default_rng(seed_int).permutation (scripts/blackbox_runorder.py "
                     "run_order, as Block 1)",
        "csv": RUNORDER, "csv_sha256": hashlib.sha256(csv_text.encode()).hexdigest(),
        "pilot_csv": PILOT_RUNORDER, "pilot_csv_sha256": hashlib.sha256(pilot_text.encode()).hexdigest(),
        "rows": rows, "pilot_rows": pilot_rows_,
    }


def build_runorders(out_dir):
    """-> {file name: text} of the three run-order files."""
    rows, prow = counted_rows(), pilot_rows()
    return {RUNORDER: R.to_csv(rows), PILOT_RUNORDER: R.to_csv(prow),
            RUNORDER_JSON: json.dumps(runorder_json(rows, prow), indent=1) + "\n"}


def cmd_runorder(argv):
    check = "--check" in argv
    out = ROOT / BB16_DIR
    files = build_runorders(out)
    bad = []
    for name, text in files.items():
        p = out / name
        if check:
            same = p.is_file() and p.read_text() == text
            print(f"  {'ok  ' if same else 'DIFFERS'} {p.relative_to(ROOT)}" + (f"  {sha256_file(p)}" if p.is_file() else "  absent"))
            bad += [] if same else [name]
        else:
            if p.exists() and p.read_text() != text:
                print(f"bb16_schedule: {p} exists and differs from the build; not overwritten", file=sys.stderr)
                return 1
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
            print(f"  wrote {p.relative_to(ROOT)}  {sha256_file(p)}")
    return 1 if bad else 0


# ---------------------------------------------------------------------------------------------------------
# spend of this arm

def runlog_arm_spent(text, arm=ARM):
    """Sum of the usd column over the RUNLOG.md table rows whose arm is `arm` or `arm (pilot)`. A usd cell that
    is not a finite number >= 0 makes the sum infinite (that stops the arm, as the scheduler does for its
    cumulative columns)."""
    total = 0.0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9 or cells[2] not in (arm, f"{arm} (pilot)"):
            continue
        try:
            v = float(cells[6])
        except ValueError:
            return math.inf
        if not math.isfinite(v) or v < 0:
            return math.inf
        total += v
    return round(total, 6)


def arm_spent(runlog):
    try:
        return runlog_arm_spent(Path(runlog).read_text())
    except OSError:
        return 0.0


def effective_cap(study_cap, cum_openai, spent):
    """The cap handed to the scheduler's rule (CONTINGENCY 0): min(study cap - 5, cum - spent + 25). Anything not
    finite gives 0, so no GPT run starts."""
    if not (math.isfinite(cum_openai) and math.isfinite(spent) and math.isfinite(study_cap)):
        return 0.0
    return round(min(study_cap - STUDY_CONTINGENCY, cum_openai - spent + ARM_CAP_USD), 6)


STUDY_CONTINGENCY = BS.CONTINGENCY   # Block 1's $5, kept on the study-wide cap
BS.CONTINGENCY = 0.0                 # the arm's rule has no contingency: spent + 1.61 > 25 stops


class BB16Scheduler(BS.Scheduler):
    def __init__(self, cfg, *a, **kw):
        super().__init__(cfg, *a, **kw)
        self.study_cap_openai = float(cfg.cap["openai"])

    def refresh_cap(self):
        cum = BS.read_cums(self.cfg.runlog)["openai"]
        spent = arm_spent(self.cfg.runlog)
        self.cfg.cap["openai"] = effective_cap(self.study_cap_openai, cum, spent)
        return spent

    def ev(self, event, job=None, **kw):
        if event == "start":
            bb16_hash = self.cfg.repo / BB16_DIR / HASHFILE
            kw.update(wrapper=WRAPPER_REL, wrapper_sha256=sha256_file(__file__), arm_cap_usd=ARM_CAP_USD,
                      arm_est_usd=ARM_EST_USD, arm_spent_usd=arm_spent(self.cfg.runlog),
                      study_cap_openai=self.study_cap_openai,
                      bb16_prereg_hash_sha256=sha256_file(bb16_hash) if bb16_hash.is_file() else None)
        elif event in ("launched", "cap_stop"):
            kw.update(arm_spent_usd=arm_spent(self.cfg.runlog), arm_cap_usd=ARM_CAP_USD)
        return super().ev(event, job, **kw)

    def setup(self, image=None):
        self.refresh_cap()
        return super().setup(image)

    def try_launch(self):
        """The scheduler's rule with the effective cap, except that a run held back only by the $1.61 counted
        for each job still in flight WAITS for those jobs instead of stopping the arm (prereg section 7: the
        stop rule is spent + 1.61 > 25; checker fix 1, PREREG_BB16.md section 9). Once nothing is in flight the
        scheduler's test is exactly spent + 1.61 > 25, and that is the only arm stop."""
        spent = self.refresh_cap()
        if self.queue and len(self.children) < self.cfg.max_slots:
            job = self.jobs[self.queue[0]]
            if job.provider == "openai" and job.provider not in self.stopped:
                running = sum(1 for c in self.children if c.job.provider == job.provider)
                est = self.cfg.est[job.agent]
                if running and spent + est <= ARM_CAP_USD < spent + est * (running + 1):
                    return self.note(f"arm spend {spent:.3f} + {est:.2f} x ({running} running + 1) > "
                                     f"{ARM_CAP_USD:.2f}: order {job.order} waits for the running jobs "
                                     f"(the stop rule is spent + {est:.2f} > {ARM_CAP_USD:.2f})")
        return super().try_launch()


# ---------------------------------------------------------------------------------------------------------
# where the run orders are, which jobs, the pre-registration

_orig_study_paths_problem = BS.study_paths_problem
_orig_check_prereg = BS.check_prereg
_orig_preflight = BS.preflight


def study_paths_problem(cfg):
    """Block 1's rule for a run order directly in results/blackbox_1112; for one in results/blackbox_1112/bb16:
    --results is the study's directory and the run order is a regular file (no symbolic link) directly in bb16/
    whose name is runorder_bb16*.csv."""
    bb16 = (cfg.repo / BB16_DIR).resolve()
    if cfg.runorder.parent.resolve() != bb16:
        return _orig_study_paths_problem(cfg)
    want = cfg.repo / BS.STUDY_RESULTS
    if cfg.results.resolve() != want.resolve():
        return f"--results {cfg.results} is not {BS.STUDY_RESULTS} of the repository {cfg.repo}"
    if cfg.runorder.is_symlink() or not cfg.runorder.is_file() or cfg.runorder.resolve() != bb16 / cfg.runorder.name \
            or not (cfg.runorder.name.startswith("runorder_bb16") and cfg.runorder.suffix == ".csv"):
        return f"the run order {cfg.runorder} is a symbolic link, not a file, or not runorder_bb16*.csv directly in {BB16_DIR}"
    return None


def bb16_hash_check(cfg, host, wrapper=None):
    """-> (ok, detail): results/blackbox_1112/bb16/PREREG_HASH lists HASH_REQUIRED and the block's run order,
    every listed file has its hash and is what HEAD holds (as is the hash file), and this process runs the
    listed wrapper."""
    wrapper = Path(wrapper or __file__).resolve()
    hashfile = cfg.repo / BB16_DIR / HASHFILE
    if not hashfile.is_file():
        return False, (f"{BB16_DIR}/{HASHFILE} does not exist: BB-16 is not hashed yet (prereg BB-16 status: draft; "
                       "the user's predictions, then the hash and its commit, come before any counted run)")
    want, problems = BS.prereg_hashes(hashfile.read_bytes().decode(errors="replace"))
    if problems:
        return False, f"{BB16_DIR}/{HASHFILE}: " + "; ".join(problems[:3])
    try:
        own = cfg.runorder.resolve().relative_to(cfg.repo.resolve()).as_posix()
    except ValueError:
        own = str(cfg.runorder)
    required = list(dict.fromkeys(list(HASH_REQUIRED) + [own]))
    absent = [r for r in required if r not in want]
    if absent:
        return False, f"{BB16_DIR}/{HASHFILE} has no entry for: " + ", ".join(absent)
    paths = {rel: cfg.repo / rel for rel in want}
    nofile = [rel for rel, p in paths.items() if p.is_symlink() or not p.is_file()]
    if nofile:
        return False, f"listed in {BB16_DIR}/{HASHFILE} but not a file: " + ", ".join(nofile)
    bad = [rel for rel, p in paths.items() if sha256_file(p) != want[rel]]
    if bad:
        return False, f"sha256 differs from {BB16_DIR}/{HASHFILE} for: " + ", ".join(bad)
    if sha256_file(wrapper) != want[WRAPPER_REL]:
        return False, f"this process does not run the wrapper {BB16_DIR}/{HASHFILE} lists (running: {wrapper})"
    ok, detail = host.git_committed(list(paths.values()) + [hashfile])
    if not ok:
        return False, detail
    return True, f"all {len(want)} files of {BB16_DIR}/{HASHFILE} have its sha256 and this process runs the listed wrapper; {detail}"


def check_prereg(cfg, host):
    """Block 1's check, run as for Block 1's own run order (so PREREG_HASH is used exactly as hashed), and the
    BB-16 hash check; both must pass."""
    block1 = dataclasses.replace(cfg, runorder=cfg.repo / BS.STUDY_RESULTS / BS.PREREG_RUNORDERS[0])
    ok1, d1 = _orig_check_prereg(block1, host)
    ok2, d2 = bb16_hash_check(cfg, host)
    return ok1 and ok2, f"Block 1 PREREG_HASH: {'ok' if ok1 else 'FAIL'}: {d1} || BB-16: {'ok' if ok2 else 'FAIL'}: {d2}"


def preflight(cfg, host, jobs, states):
    """Block 1's preflight (with the two functions above in place), plus `bb16_jobs` and `spend:bb16`."""
    checks = _orig_preflight(cfg, host, jobs, states)
    add = lambda name, ok, detail="": checks.append(BS.Check(name, bool(ok), detail))
    bad = [j.order for j in jobs if (j.agent, j.arm, j.problem) != (AGENT, ARM, j.item + SUFFIX)]
    add("bb16_jobs", not bad and cfg.block.startswith("bb16"),
        f"{len(jobs)} jobs, block {cfg.block!r}: " + (f"orders {bad} are not GPT {ARM}" if bad else f"all GPT {ARM} ({SUFFIX})")
        + ("" if cfg.block.startswith("bb16") else "; the run order is not a BB-16 run order"))
    spent = arm_spent(cfg.runlog)
    rest = [j for j in jobs if j.provider == "openai" and not states[j.order].terminal]
    est = cfg.est[AGENT]
    add("spend:bb16", spent + est <= ARM_CAP_USD and est == ARM_EST_USD,
        f"arm spent {spent:.3f} USD (RUNLOG.md rows bb16 / bb16 (pilot)); next run: {spent:.3f} + {est:.2f} "
        f"{'<=' if spent + est <= ARM_CAP_USD else '>'} {ARM_CAP_USD:.2f}; {len(rest)} remaining jobs would take it to "
        f"{spent + est * len(rest):.2f} at {est:.2f} each and {spent + 0.65 * len(rest):.2f} at the expected 0.65 "
        f"(the stop rule ends the arm at the cap)" + ("" if est == ARM_EST_USD else f"; --est-gpt must be {ARM_EST_USD}"))
    return checks


BS.study_paths_problem = study_paths_problem
BS.check_prereg = check_prereg
BS.preflight = preflight
BS.Scheduler = BB16Scheduler


# ---------------------------------------------------------------------------------------------------------
# command line

def cmd_pilot_check(argv):
    import blackbox_pilot_check as PC
    PC.STUDY_ARMS[ARM] = ("blackbox", 16)
    return PC.main(argv)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["runorder"]:
        return cmd_runorder(argv[1:])
    if argv[:1] == ["pilot-check"]:
        return cmd_pilot_check(argv[1:])
    ests = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "--est-gpt"] + \
           [a.split("=", 1)[1] for a in argv if a.startswith("--est-gpt=")]
    if any(float(x) != ARM_EST_USD for x in ests):
        print(f"bb16_schedule: --est-gpt is {ARM_EST_USD} for this arm (prereg section 7)", file=sys.stderr)
        return 2
    if not ests:
        argv += ["--est-gpt", str(ARM_EST_USD)]
    return BS.main(argv)


if __name__ == "__main__":
    sys.exit(main())
