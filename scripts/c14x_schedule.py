#!/usr/bin/env python3
"""C14b (third fresh trap F2-c, results/blackbox_1112/gpuplan/c14b/PREREG_C14B.md) and C14L (Luna +2 per fresh item,
results/blackbox_1112/gpuplan/c14l/PREREG_C14L.md): Block 1's scheduler, unchanged, on the image
rl-task-shifthunt-r1114d (= r1114c + the F2-c episode, built privately; tag r1114d).

    $PY $PUB/scripts/c14x_schedule.py runorder [--check]
    cd $PRIV && source scripts/r1112_env.sh && export RL_TASK_IMAGE_SUFFIX=-r1114d OPENAI_PRICES=<agent prices>
    $PY -u $PUB/scripts/c14x_schedule.py --c14x-item c14b|c14l --c14x-agent gpt|luna \
        --runorder $RES/gpuplan/<item>/runorder_<item>_<agent>[_pilot].csv [--pilot] --tag r1114d \
        --task-dir $PRIV --results $RES --cap-openai 800 --cap-anthropic 130 [--dry-run]

scripts/blackbox_schedule.py and scripts/c14_schedule.py are not edited. Same pattern as c14_schedule.py:
  items       c14b: F2-c (ep803) x RUNS (Terra 7, Luna 7: C14L's add-on, Luna's F2-c runs had not started);
                    Luna pilot on F2-c (excluded).
              c14l: Luna +2 on F2-a (ep801) and F2-b (ep802), replicates 6 and 7.
  run orders  replicate-major, seeded shuffle (seed text "c14x-1114-<item>-<agent>").
  spend       per (item, agent) cap over the RUNLOG rows of this wrapper's runs (ledger `finished` events whose
              block starts with "<item>_<agent>" and whose run directory starts with the tag).
  prereg      a counted block needs Block 1's check and the item's PREREG_HASH.
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

ARM = "open8"
TAG = "r1114d"
ITEMS = {  # item -> {agent: (items, runs per item, first replicate)}
    "c14b": {"gpt": (("ep803",), 7, 1), "luna": (("ep803",), 7, 1)},
    "c14l": {"luna": (("ep801", "ep802"), 2, 6)},
}
SPEC = {  # agent -> (model, engine, est USD per run)
    "gpt": ("gpt-6.1-terra", "codex", 0.85),
    "luna": ("gpt-6-luna", "codex", 0.20),
}
CAP = {("c14b", "gpt"): 7.0, ("c14b", "luna"): 1.6, ("c14l", "luna"): 1.0}
PILOT = {("c14b", "luna"): ("ep803",)}
LUNA_PRICES = (0.10, 0.01, 0.125, 0.50)
WRAPPER_REL = "scripts/c14x_schedule.py"
RUNORDER_JSON, HASHFILE = "run_order.json", "PREREG_HASH"


def _pop(flag, default):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return v
    return default


ITEM = _pop("--c14x-item", "c14b")
AGENT = _pop("--c14x-agent", "gpt")
if ITEM not in ITEMS or AGENT not in ITEMS[ITEM]:
    raise SystemExit(f"c14x_schedule: (--c14x-item, --c14x-agent) must be one of "
                     f"{[(i, a) for i in ITEMS for a in ITEMS[i]]}")
MODEL, ENGINE, ARM_EST_USD = SPEC[AGENT]
ARM_CAP_USD = CAP[(ITEM, AGENT)]
ARMS = (ARM,)
BLOCK = f"{ITEM}_{AGENT}"
ITEM_DIR = f"{BS.STUDY_RESULTS}/gpuplan/{ITEM}"
HASH_REQUIRED = (f"{ITEM_DIR}/PREREG_{ITEM.upper()}.md", f"{ITEM_DIR}/{RUNORDER_JSON}", WRAPPER_REL,
                 "scripts/c14x_analysis.py")

for mod in (R, BS):
    mod.AGENTS["luna"] = SPEC["luna"][:2]
if AGENT == "luna":
    BS.STUDY_OPENAI_PRICES = LUNA_PRICES
STUDY_CONTINGENCY = BS.CONTINGENCY
BS.CONTINGENCY = 0.0

_orig_config = BS.Config


def Config(*a, **kw):
    kw["est"] = dict(kw.get("est") or {}, **{AGENT: ARM_EST_USD})
    return _orig_config(*a, **kw)


BS.Config = Config


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------
# run orders

def replicate_major(cells, seed_text, first_rep=1):
    import numpy as np
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(seed_text.encode()).digest(), "big"))
    rows = []
    for k in range(max(n for _, _, n in cells)):
        group = [R._row(ag, ARM, it, first_rep + k) for ag, it, n in cells if k < n]
        rows += [group[int(j)] for j in rng.permutation(len(group))]
    return [dict(r, order=i + 1) for i, r in enumerate(rows)]


def counted_rows(item, agent):
    its, n, first = ITEMS[item][agent]
    return replicate_major([(agent, it, n) for it in its], f"c14x-1114-{item}-{agent}", first)


def build_runorders(item):
    files, meta = {}, {"item": item, "arm": ARM, "tag": TAG, "agents": {},
                       "seed_rule": "replicate-major; per replicate the (agent, item) cells in "
                                    "numpy.random.default_rng(int.from_bytes(sha256(seed_text).digest(), 'big'))"
                                    ".permutation order; seed_text 'c14x-1114-<item>-<agent>'"}
    for ag in ITEMS[item]:
        rows = counted_rows(item, ag)
        c = f"runorder_{item}_{ag}.csv"
        files[c] = R.to_csv(rows)
        meta["agents"][ag] = {"model": SPEC[ag][0], "engine": SPEC[ag][1], "cap_usd": CAP[(item, ag)],
                              "est_usd": SPEC[ag][2], "csv": c,
                              "csv_sha256": hashlib.sha256(files[c].encode()).hexdigest(), "rows": rows}
        if (item, ag) in PILOT:
            pc = f"runorder_{item}_{ag}_pilot.csv"
            files[pc] = R.to_csv([dict(R._row(ag, ARM, it, 1), order=i + 1) for i, it in enumerate(PILOT[(item, ag)])])
            meta["agents"][ag]["pilot_csv"] = pc
    files[RUNORDER_JSON] = json.dumps(meta, indent=1) + "\n"
    return files


def cmd_runorder(argv):
    check = "--check" in argv
    bad = []
    for item in ITEMS:
        out = ROOT / BS.STUDY_RESULTS / "gpuplan" / item
        for name, text in build_runorders(item).items():
            p = out / name
            if check:
                same = p.is_file() and p.read_text() == text
                print(f"  {'ok  ' if same else 'DIFFERS'} {p.relative_to(ROOT)}")
                bad += [] if same else [name]
            else:
                if p.exists() and p.read_text() != text:
                    print(f"c14x_schedule: {p} exists and differs from the build; not overwritten", file=sys.stderr)
                    return 1
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
                print(f"  wrote {p.relative_to(ROOT)}  {sha256_file(p)}")
    return 1 if bad else 0


# ---------------------------------------------------------------------------------------------------------
# spend of this (item, agent)

def run_ids():
    ids = set()
    try:
        for line in (ROOT / BS.STUDY_RESULTS / "ledger.jsonl").read_text().splitlines():
            e = json.loads(line)
            if (e.get("event") == "finished" and str(e.get("run", "")).startswith(TAG) and e.get("agent") == AGENT
                    and str(e.get("block", "")).startswith(BLOCK)):
                ids.add(e.get("cid"))
    except OSError:
        pass
    return ids


def runlog_spent(text):
    ids = run_ids()
    total = 0.0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9 or cells[3] != AGENT or cells[1] not in ids:
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
        return runlog_spent(Path(runlog).read_text())
    except OSError:
        return 0.0


def effective_cap(study_cap, cum_openai, spent):
    if not (math.isfinite(cum_openai) and math.isfinite(spent) and math.isfinite(study_cap)):
        return 0.0
    return round(min(study_cap - STUDY_CONTINGENCY, cum_openai - spent + ARM_CAP_USD), 6)


class C14xScheduler(BS.Scheduler):
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
            h = self.cfg.repo / ITEM_DIR / HASHFILE
            kw.update(wrapper=WRAPPER_REL, wrapper_sha256=sha256_file(__file__), arm_cap_usd=ARM_CAP_USD,
                      arm_est_usd=ARM_EST_USD, arm_spent_usd=arm_spent(self.cfg.runlog),
                      study_cap_openai=self.study_cap_openai, model=MODEL, c14x_item=ITEM, c14x_agent=AGENT,
                      c14x_prereg_hash_sha256=sha256_file(h) if h.is_file() else None)
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
# run orders' location, jobs, pre-registration

_orig_study_paths_problem = BS.study_paths_problem
_orig_check_prereg = BS.check_prereg
_orig_preflight = BS.preflight


def study_paths_problem(cfg):
    d = (cfg.repo / ITEM_DIR).resolve()
    if cfg.runorder.parent.resolve() != d:
        return _orig_study_paths_problem(cfg)
    if cfg.results.resolve() != (cfg.repo / BS.STUDY_RESULTS).resolve():
        return f"--results {cfg.results} is not {BS.STUDY_RESULTS} of the repository {cfg.repo}"
    if cfg.runorder.is_symlink() or not cfg.runorder.is_file() \
            or not (cfg.runorder.name.startswith(f"runorder_{ITEM}_{AGENT}") and cfg.runorder.suffix == ".csv"):
        return f"the run order {cfg.runorder} is not a runorder_{ITEM}_{AGENT}*.csv file directly in {ITEM_DIR}"
    return None


def item_hash_check(cfg, host, wrapper=None):
    wrapper = Path(wrapper or __file__).resolve()
    hashfile = cfg.repo / ITEM_DIR / HASHFILE
    if not hashfile.is_file():
        return False, f"{ITEM_DIR}/{HASHFILE} does not exist: {ITEM} is not hashed yet"
    want, problems = BS.prereg_hashes(hashfile.read_bytes().decode(errors="replace"))
    if problems:
        return False, f"{ITEM_DIR}/{HASHFILE}: " + "; ".join(problems[:3])
    own = cfg.runorder.resolve().relative_to(cfg.repo.resolve()).as_posix()
    absent = [r for r in dict.fromkeys(list(HASH_REQUIRED) + [own]) if r not in want]
    if absent:
        return False, f"{ITEM_DIR}/{HASHFILE} has no entry for: " + ", ".join(absent)
    paths = {rel: cfg.repo / rel for rel in want}
    bad = [rel for rel, p in paths.items() if p.is_symlink() or not p.is_file() or sha256_file(p) != want[rel]]
    if bad:
        return False, f"missing or sha256 differs from {ITEM_DIR}/{HASHFILE}: " + ", ".join(bad)
    if sha256_file(wrapper) != want[WRAPPER_REL]:
        return False, f"this process does not run the wrapper {ITEM_DIR}/{HASHFILE} lists"
    ok, detail = host.git_committed(list(paths.values()) + [hashfile])
    return (ok, detail if not ok else f"all {len(want)} files of {ITEM_DIR}/{HASHFILE} match; {detail}")


def check_prereg(cfg, host):
    block1 = dataclasses.replace(cfg, runorder=cfg.repo / BS.STUDY_RESULTS / BS.PREREG_RUNORDERS[0])
    ok1, d1 = _orig_check_prereg(block1, host)
    ok2, d2 = item_hash_check(cfg, host)
    return ok1 and ok2, f"Block 1 PREREG_HASH: {'ok' if ok1 else 'FAIL'}: {d1} || {ITEM}: {'ok' if ok2 else 'FAIL'}: {d2}"


def preflight(cfg, host, jobs, states):
    checks = _orig_preflight(cfg, host, jobs, states)
    add = lambda name, ok, detail="": checks.append(BS.Check(name, bool(ok), detail))
    bad = [j.order for j in jobs if (j.agent, j.model, j.engine) != (AGENT, MODEL, ENGINE) or j.arm not in ARMS]
    add("c14x_jobs", not bad and cfg.block.startswith(BLOCK),
        f"{len(jobs)} jobs, block {cfg.block!r}: " + (f"orders {bad} are not {AGENT} in {ARMS}" if bad else f"all {AGENT} in {ARMS}"))
    spent = arm_spent(cfg.runlog)
    rest = [j for j in jobs if not states[j.order].terminal]
    add(f"spend:{BLOCK}", spent + ARM_EST_USD <= ARM_CAP_USD,
        f"spent {spent:.3f} USD ({TAG} runs of block {BLOCK}*); next run {spent:.3f} + {ARM_EST_USD:.2f} "
        f"{'<=' if spent + ARM_EST_USD <= ARM_CAP_USD else '>'} {ARM_CAP_USD:.2f}; {len(rest)} remaining jobs at "
        f"{ARM_EST_USD:.2f} each would reach {spent + ARM_EST_USD * len(rest):.2f} (the stop rule ends the arm at the cap)")
    return checks


BS.study_paths_problem = study_paths_problem
BS.check_prereg = check_prereg
BS.preflight = preflight
BS.Scheduler = C14xScheduler


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["runorder"]:
        return cmd_runorder(argv[1:])
    return BS.main(argv)


if __name__ == "__main__":
    sys.exit(main())
