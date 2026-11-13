#!/usr/bin/env python3
"""X3 / X3b Open-4 arm (results/blackbox_1112/gpuplan/open4/PREREG_OPEN4.md): Block 1's scheduler, unchanged, with
one more arm: open access (SAE tools) and 4 exact probe_query texts. Same image, prompt, tools and budgets as
Open-8 except the probe_query number (task.py PROBLEM `<item>-open4`; the prompt's Budget section is rendered from
it). One scheduler process per agent, because the collector prices Codex tokens with OPENAI_PRICES:

    $PY $PUB/scripts/open4_schedule.py runorder [--check]
    cd $PRIV && source scripts/r1112_env.sh && export OPENAI_PRICES=<agent prices>   # Terra: the study's; Luna: 0.10,0.01,0.125,0.50
    $PY -u $PUB/scripts/open4_schedule.py --x3-agent gpt|luna --runorder $RES/gpuplan/open4/runorder_open4_<agent>[_pilot].csv \
        [--pilot] --tag r1112 --task-dir $PRIV --results $RES --cap-openai 800 --cap-anthropic 130 [--dry-run | --summary]

scripts/blackbox_schedule.py is covered by Block 1's PREREG_HASH and is not edited. This wrapper imports it and
changes only these things, in this process (the pattern of scripts/bb16_schedule.py and scripts/luna_schedule.py):

  arm             PROBLEM_SUFFIX gains "open4": "-open4" (scheduler and blackbox_runorder.py). Run directories
                  r1112_<agent>_open4 (pilots r1112_pilot_<agent>_open4).
  agents          gpt (gpt-6.1-terra, Block 1's) and luna ("gpt-6-luna", codex; added as in luna_schedule.py).
                  --x3-agent picks one; every job of the run order must be that agent in arm open4.
  run orders      results/blackbox_1112/gpuplan/open4/runorder_open4_<agent>.csv: the six shipped items x 2 runs,
                  Block 1's method, seed text "open4-1113" (gpt) / "open4-1113-luna" (luna); pilots one run on ep472.
  prices          gpt: the study's prices (unchanged); luna: LUNA_PRICES (the preflight refuses any other value).
  spend           OpenAI cap per agent ARM_CAP_USD[agent] (pilot included); "spent" = the usd column of the RUNLOG.md
                  rows whose arm is open4 (or "open4 (pilot)") and whose agent is that agent. A run starts only if
                  spent + est x (running + 1) <= cap (as luna_schedule.py).
  prereg          a counted block needs Block 1's check and results/blackbox_1112/gpuplan/open4/PREREG_HASH.
"""
import dataclasses
import hashlib
import json
import math
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import blackbox_runorder as R  # noqa: E402
import blackbox_schedule as BS  # noqa: E402

ARM, SUFFIX = "open4", "-open4"
SPEC = {  # agent -> (model, engine, seed text, cap USD, est USD per run)
    "gpt": ("gpt-6.1-terra", "codex", "open4-1113", 10.0, 0.90),
    "luna": ("gpt-6-luna", "codex", "open4-1113-luna", 2.0, 0.20),
}
RUNS_PER_ITEM = 2
PILOT_ITEM = "ep472"
LUNA_PRICES = (0.10, 0.01, 0.125, 0.50)
X3_DIR = f"{BS.STUDY_RESULTS}/gpuplan/open4"
RUNORDER_JSON, HASHFILE = "run_order.json", "PREREG_HASH"
WRAPPER_REL = "scripts/open4_schedule.py"

AGENT = "gpt"
if "--x3-agent" in sys.argv:
    _i = sys.argv.index("--x3-agent")
    AGENT = sys.argv[_i + 1]
    del sys.argv[_i:_i + 2]
if AGENT not in SPEC:
    raise SystemExit(f"open4_schedule: --x3-agent must be one of {sorted(SPEC)}")
MODEL, ENGINE, SEED_TEXT, ARM_CAP_USD, ARM_EST_USD = SPEC[AGENT]
SEED = int.from_bytes(hashlib.sha256(SEED_TEXT.encode()).digest(), "big")
ARMS = (ARM,)
BLOCK = f"open4_{AGENT}"
RUNORDER, PILOT_RUNORDER = f"runorder_open4_{AGENT}.csv", f"runorder_open4_{AGENT}_pilot.csv"
LUNA_DIR = X3_DIR
HASH_REQUIRED = (f"{X3_DIR}/PREREG_OPEN4.md", f"{X3_DIR}/runorder_open4_gpt.csv", f"{X3_DIR}/runorder_open4_luna.csv",
                 f"{X3_DIR}/{RUNORDER_JSON}", WRAPPER_REL)

for mod in (R, BS):
    mod.AGENTS["luna"] = SPEC["luna"][:2]
    mod.PROBLEM_SUFFIX[ARM] = SUFFIX
for ag in SPEC:
    R.BLOCKS[f"open4_{ag}"] = [(ag, (ARM,), RUNS_PER_ITEM)]
if AGENT == "luna":
    BS.STUDY_OPENAI_PRICES = LUNA_PRICES
STUDY_CONTINGENCY = BS.CONTINGENCY
BS.CONTINGENCY = 0.0

_orig_config = BS.Config


def Config(*a, **kw):
    """Block 1's Config with an estimate for Luna (the scheduler builds est from --est-gpt / --est-haiku only)."""
    kw["est"] = dict(kw.get("est") or {}, **{AGENT: ARM_EST_USD})
    return _orig_config(*a, **kw)


BS.Config = Config


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------
# run orders

def counted_rows(agent=None):
    agent = agent or AGENT
    seed = int.from_bytes(hashlib.sha256(SPEC[agent][2].encode()).digest(), "big")
    return R.run_order(f"open4_{agent}", seed)


def pilot_rows(agent=None):
    return [dict(R._row(agent or AGENT, ARM, PILOT_ITEM, 1), order=1)]


def build_runorders():
    files, meta = {}, {"arm": ARM, "problem_suffix": SUFFIX, "runs_per_item": RUNS_PER_ITEM, "items": list(R.ITEMS),
                       "seed_rule": "int.from_bytes(sha256(seed_text).digest(), 'big'); rows in the fixed order "
                                    "(agent, arm, item, rep), then numpy.random.default_rng(seed_int).permutation "
                                    "(blackbox_runorder.run_order)", "agents": {}}
    for ag in SPEC:
        rows, prow = counted_rows(ag), pilot_rows(ag)
        c, pc = f"runorder_open4_{ag}.csv", f"runorder_open4_{ag}_pilot.csv"
        files[c], files[pc] = R.to_csv(rows), R.to_csv(prow)
        meta["agents"][ag] = {"model": SPEC[ag][0], "engine": SPEC[ag][1], "seed_text": SPEC[ag][2],
                              "cap_usd": SPEC[ag][3], "est_usd": SPEC[ag][4], "csv": c,
                              "csv_sha256": hashlib.sha256(files[c].encode()).hexdigest(), "pilot_csv": pc,
                              "pilot_csv_sha256": hashlib.sha256(files[pc].encode()).hexdigest(),
                              "rows": rows, "pilot_rows": prow}
    files[RUNORDER_JSON] = json.dumps(meta, indent=1) + "\n"
    return files


def cmd_runorder(argv):
    check = "--check" in argv
    out = ROOT / LUNA_DIR
    bad = []
    for name, text in build_runorders().items():
        p = out / name
        if check:
            same = p.is_file() and p.read_text() == text
            print(f"  {'ok  ' if same else 'DIFFERS'} {p.relative_to(ROOT)}")
            bad += [] if same else [name]
        else:
            if p.exists() and p.read_text() != text:
                print(f"open4_schedule: {p} exists and differs from the build; not overwritten", file=sys.stderr)
                return 1
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
            print(f"  wrote {p.relative_to(ROOT)}  {sha256_file(p)}")
    return 1 if bad else 0


# ---------------------------------------------------------------------------------------------------------
# spend of this arm: RUNLOG.md rows whose agent is luna

def runlog_agent_spent(text, agent=AGENT):
    """usd of the RUNLOG.md rows whose arm is open4 (or "open4 (pilot)") and whose agent is `agent`."""
    total = 0.0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9 or cells[3] != agent or cells[2] not in (ARM, f"{ARM} (pilot)"):
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
        return runlog_agent_spent(Path(runlog).read_text())
    except OSError:
        return 0.0


def effective_cap(study_cap, cum_openai, spent):
    if not (math.isfinite(cum_openai) and math.isfinite(spent) and math.isfinite(study_cap)):
        return 0.0
    return round(min(study_cap - STUDY_CONTINGENCY, cum_openai - spent + ARM_CAP_USD), 6)


class Open4Scheduler(BS.Scheduler):
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
            h = self.cfg.repo / LUNA_DIR / HASHFILE
            kw.update(wrapper=WRAPPER_REL, wrapper_sha256=sha256_file(__file__), arm_cap_usd=ARM_CAP_USD,
                      arm_est_usd=ARM_EST_USD, arm_spent_usd=arm_spent(self.cfg.runlog),
                      study_cap_openai=self.study_cap_openai, model=MODEL, x3_agent=AGENT,
                      open4_prereg_hash_sha256=sha256_file(h) if h.is_file() else None)
        elif event in ("launched", "cap_stop"):
            kw.update(arm_spent_usd=arm_spent(self.cfg.runlog), arm_cap_usd=ARM_CAP_USD)
        return super().ev(event, job, **kw)

    def setup(self, image=None):
        self.refresh_cap()
        return super().setup(image)

    def try_launch(self):
        spent = self.refresh_cap()
        if self.queue and len(self.children) < self.cfg.max_slots:
            job = self.jobs[self.queue[0]]
            if job.provider == "openai" and job.provider not in self.stopped:
                running = sum(1 for c in self.children if c.job.provider == job.provider)
                est = self.cfg.est[job.agent]
                if running and spent + est <= ARM_CAP_USD < spent + est * (running + 1):
                    return self.note(f"arm spend {spent:.3f} + {est:.2f} x ({running} running + 1) > "
                                     f"{ARM_CAP_USD:.2f}: order {job.order} waits for the running jobs")
        return super().try_launch()


# ---------------------------------------------------------------------------------------------------------
# where the run orders are, which jobs, the pre-registration

_orig_study_paths_problem = BS.study_paths_problem
_orig_check_prereg = BS.check_prereg
_orig_preflight = BS.preflight


def study_paths_problem(cfg):
    d = (cfg.repo / LUNA_DIR).resolve()
    if cfg.runorder.parent.resolve() != d:
        return _orig_study_paths_problem(cfg)
    if cfg.results.resolve() != (cfg.repo / BS.STUDY_RESULTS).resolve():
        return f"--results {cfg.results} is not {BS.STUDY_RESULTS} of the repository {cfg.repo}"
    if cfg.runorder.is_symlink() or not cfg.runorder.is_file() \
            or not (cfg.runorder.name.startswith(f"runorder_open4_{AGENT}") and cfg.runorder.suffix == ".csv"):
        return f"the run order {cfg.runorder} is not a runorder_open4_{AGENT}*.csv file directly in {LUNA_DIR}"
    return None


def luna_hash_check(cfg, host, wrapper=None):
    wrapper = Path(wrapper or __file__).resolve()
    hashfile = cfg.repo / LUNA_DIR / HASHFILE
    if not hashfile.is_file():
        return False, f"{LUNA_DIR}/{HASHFILE} does not exist: the Open-4 arm is not hashed yet"
    want, problems = BS.prereg_hashes(hashfile.read_bytes().decode(errors="replace"))
    if problems:
        return False, f"{LUNA_DIR}/{HASHFILE}: " + "; ".join(problems[:3])
    own = cfg.runorder.resolve().relative_to(cfg.repo.resolve()).as_posix()
    absent = [r for r in dict.fromkeys(list(HASH_REQUIRED) + [own]) if r not in want]
    if absent:
        return False, f"{LUNA_DIR}/{HASHFILE} has no entry for: " + ", ".join(absent)
    paths = {rel: cfg.repo / rel for rel in want}
    bad = [rel for rel, p in paths.items() if p.is_symlink() or not p.is_file() or sha256_file(p) != want[rel]]
    if bad:
        return False, f"missing or sha256 differs from {LUNA_DIR}/{HASHFILE}: " + ", ".join(bad)
    if sha256_file(wrapper) != want[WRAPPER_REL]:
        return False, f"this process does not run the wrapper {LUNA_DIR}/{HASHFILE} lists"
    ok, detail = host.git_committed(list(paths.values()) + [hashfile])
    return (ok, detail if not ok else f"all {len(want)} files of {LUNA_DIR}/{HASHFILE} match; {detail}")


def check_prereg(cfg, host):
    block1 = dataclasses.replace(cfg, runorder=cfg.repo / BS.STUDY_RESULTS / BS.PREREG_RUNORDERS[0])
    ok1, d1 = _orig_check_prereg(block1, host)
    ok2, d2 = luna_hash_check(cfg, host)
    return ok1 and ok2, f"Block 1 PREREG_HASH: {'ok' if ok1 else 'FAIL'}: {d1} || Open-4: {'ok' if ok2 else 'FAIL'}: {d2}"


def preflight(cfg, host, jobs, states):
    checks = _orig_preflight(cfg, host, jobs, states)
    add = lambda name, ok, detail="": checks.append(BS.Check(name, bool(ok), detail))
    bad = [j.order for j in jobs if (j.agent, j.model, j.engine) != (AGENT, MODEL, ENGINE) or j.arm not in ARMS]
    add("open4_jobs", not bad and cfg.block.startswith(BLOCK),
        f"{len(jobs)} jobs, block {cfg.block!r}: " + (f"orders {bad} are not {AGENT} in {ARMS}" if bad else f"all {AGENT} in {ARMS}"))
    spent = arm_spent(cfg.runlog)
    rest = [j for j in jobs if not states[j.order].terminal]
    add(f"spend:open4_{AGENT}", spent + ARM_EST_USD <= ARM_CAP_USD,
        f"arm spent {spent:.3f} USD (RUNLOG.md rows of arm open4, this agent); next run {spent:.3f} + {ARM_EST_USD:.2f} "
        f"{'<=' if spent + ARM_EST_USD <= ARM_CAP_USD else '>'} {ARM_CAP_USD:.2f}; {len(rest)} remaining jobs at "
        f"{ARM_EST_USD:.2f} each would reach {spent + ARM_EST_USD * len(rest):.2f} (the stop rule ends the arm at the cap)")
    return checks


BS.study_paths_problem = study_paths_problem
BS.check_prereg = check_prereg
BS.preflight = preflight
BS.Scheduler = Open4Scheduler


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["runorder"]:
        return cmd_runorder(argv[1:])
    return BS.main(argv)


if __name__ == "__main__":
    sys.exit(main())
