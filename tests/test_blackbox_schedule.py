"""scripts/blackbox_schedule.py with its fake launcher and a simulated clock: no docker, no process, no API.

Every test builds its state under tmp_path. The real launcher is never built here (one test checks that it
refuses to exist in a dry run, and the command line it would run is checked as a list of strings)."""
import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_wp6b", ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bs = _load("blackbox_schedule")
G, H = "gpt", "haiku"


# ---------------------------------------------------------------- helpers

def write_runorder(path, rows):
    """rows: (agent, arm, item, rep) in queue order."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(bs.COLUMNS)
        for i, (agent, arm, item, rep) in enumerate(rows, 1):
            model, engine = bs.AGENTS[agent]
            w.writerow([i, agent, model, engine, arm, item, item + bs.PROBLEM_SUFFIX[arm], rep])
    return path


def mixed(n):
    """n jobs, GPT and Haiku alternating over arms and items, every (agent, arm, item, rep) distinct."""
    arms, items = ("open8", "bb8", "bb64"), ("ep411", "ep472", "ep413")
    return [((G, H)[i % 2], arms[i % 3], items[(i // 3) % 3], i // 18 + 1 + (i % 18) // 9) for i in range(n)]


class StopClock(bs.FakeClock):
    """A simulated clock that interrupts the scheduler (as SIGTERM does) once `stop_after` seconds have passed."""

    def __init__(self, stop_after=None):
        super().__init__()
        self.start, self.stop_after, self.sched = self.t, stop_after, None

    def sleep(self, s):
        super().sleep(s)
        if self.stop_after is not None and self.t - self.start >= self.stop_after:
            self.sched.interrupted = "test stop"


class Env:
    """One block in tmp_path: run order, config, fake launcher, scheduler(s)."""

    def __init__(self, tmp_path, rows, script=None, name="runorder_block1.csv", pilot=False, **cfg):
        self.tmp = tmp_path
        self.runorder = write_runorder(tmp_path / name, rows)
        self.jobs = bs.read_runorder(self.runorder)
        self.cfg = bs.Config(self.runorder, "r1112", tmp_path / "sub" / "tasks" / "shifthunt", tmp_path / "results",
                             rollouts=tmp_path / "rollouts", pilot=pilot, **cfg)
        self.cfg.results.mkdir(parents=True, exist_ok=True)
        self.clock = StopClock()
        self.script = script
        self.launcher = bs.FakeLauncher(self.cfg, self.clock, script)
        self.said = []

    def sched(self, launcher=None, host=None, stop_after=None):
        s = bs.Scheduler(self.cfg, self.jobs, launcher or self.launcher, self.clock, host, say=self.said.append)
        self.clock.sched, self.clock.start, self.clock.stop_after = s, self.clock.t, stop_after
        return s

    def run(self, **kw):
        s = self.sched(**kw)
        self.summary = s.run()
        return s

    def events(self, *kinds):
        evs = bs.read_events(self.cfg.ledger)
        return [e for e in evs if not kinds or e["event"] in kinds]

    def runlog_rows(self):
        rows = []
        for line in self.cfg.runlog.read_text().splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cells) == 9 and cells[0][:2] == "20":
                rows.append(cells)
        return rows


def lose_launchers(e, reboot=False, script=None):
    """A new fake launcher on the same fake host: every launcher process is gone, the containers exist.
    reboot: the containers that were running are ended now, before their graders (a host reboot)."""
    if reboot:
        for c in e.launcher.containers.values():
            if c["t_end"] > e.clock.t:
                c.update(t_end=e.clock.t, outcome="killed_submitted" if c["spec"].get("submitted_at_reboot") else "killed")
    return bs.FakeLauncher(e.cfg, e.clock, script or by_order({}), containers=e.launcher.containers)


class HostWith:
    def __init__(self, n):
        self.n = n

    def host_containers(self):
        return self.n


def by_order(spec):
    """script: {order: outcome dict or [outcome dict per attempt]}; other jobs succeed in 10 minutes for $1."""
    def script(job, attempt):
        v = spec.get(job.order, {})
        if isinstance(v, list):
            v = v[min(attempt, len(v)) - 1]
        return {"outcome": "ok", "minutes": 10, "usd": 1.0, **v}
    return script


# ---------------------------------------------------------------- run order, names, command

def test_committed_run_orders_parse_and_agree_with_the_generator():
    ro = _load("blackbox_runorder")
    assert bs.COLUMNS == ro.COLUMNS and bs.AGENTS == ro.AGENTS and bs.PROBLEM_SUFFIX == ro.PROBLEM_SUFFIX
    for name, n in (("pilots", 4), ("block1", 108), ("block2", 24)):
        jobs = bs.read_runorder(ROOT / "results" / "blackbox_1112" / f"runorder_{name}.csv")
        assert len(jobs) == n and [j.order for j in jobs] == list(range(1, n + 1))
        assert bs.block_name(f"runorder_{name}.csv") == name
    jobs = bs.read_runorder(ROOT / "results" / "blackbox_1112" / "runorder_block1.csv")
    assert sum(j.provider == "openai" for j in jobs) == 72 and sum(j.provider == "anthropic" for j in jobs) == 36


@pytest.mark.parametrize("edit, msg", [
    (lambda r: r[1].__setitem__(0, "3"), "orders must be 1..n"),
    (lambda r: r[1].__setitem__(2, "claude-haiku-5-5"), "agent 'gpt' with model"),
    (lambda r: r[1].__setitem__(3, "claude"), "agent 'gpt' with model"),
    (lambda r: r[1].__setitem__(6, "ep411-blackbox64"), "is not item"),
    (lambda r: r[1].__setitem__(4, "bb16"), "is not item"),
    (lambda r: r[1].__setitem__(7, "x"), "must be integers"),
    (lambda r: r[0].__setitem__(1, "who"), "columns"),
    (lambda r: r.__setitem__(2, [2] + r[1][1:]), "duplicate"),
    (lambda r: r.__delitem__(slice(1, None)), "no jobs"),
])
def test_read_runorder_refuses_what_is_not_a_run_order(tmp_path, edit, msg):
    p = write_runorder(tmp_path / "runorder_x.csv", [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1)])
    rows = list(csv.reader(open(p)))
    edit(rows)
    with open(p, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)
    with pytest.raises(ValueError, match=msg):
        bs.read_runorder(p)


def test_run_names_are_the_batches_the_scorer_reads_and_pilots_are_left_out():
    sn = _load("score_naming")
    for job in bs.read_runorder(ROOT / "results" / "blackbox_1112" / "runorder_block1.csv")[:20]:
        assert sn.study_batch(bs.run_name("r1112", job), "r1112") == (job.agent, job.arm)
        assert sn.study_batch(bs.run_name("r1112", job, pilot=True), "r1112") is None
    job = bs.read_runorder(ROOT / "results" / "blackbox_1112" / "runorder_pilots.csv")[3]
    assert bs.run_name("r1112", job, pilot=True) == "r1112_pilot_haiku_bb8"


def test_launcher_command_is_the_main_studys_single_problem_launch():
    gpt, _, _, haiku = bs.read_runorder(ROOT / "results" / "blackbox_1112" / "runorder_pilots.csv")
    tail = ["--max-concurrent", "1", "--stagger", "0", "--max-host-containers", "3", "--timeout", "5400",
            "--mem-limit", "4G", "--cpu-limit", "2", "--cap-usd", "15", "--est-usd", "3"]
    assert bs.launcher_cmd("PY", gpt, "r1112_pilot_gpt_open8") == [
        "PY", "scripts/launch_rollouts.py", "ep411-open", "--out", "results/rollouts/r1112_pilot_gpt_open8",
        "--model", "gpt-6.1-terra", "--engine", "codex"] + tail
    assert bs.launcher_cmd("PY", haiku, "r1112_haiku_bb8") == [
        "PY", "scripts/launch_rollouts.py", "ep472-blackbox", "--out", "results/rollouts/r1112_haiku_bb8",
        "--model", "claude-haiku-5-5"] + tail


def test_launcher_command_uses_only_options_the_private_launcher_has():
    src = Path("/home/ec2-user/onsite/sub/tasks/shifthunt/scripts/launch_rollouts.py")
    if not src.exists():
        pytest.skip(f"the private launcher is not on this machine ({src})")
    text = src.read_text()
    known = set(__import__("re").findall(r'add_argument\("(--[a-z-]+)"', text))
    job = bs.read_runorder(ROOT / "results" / "blackbox_1112" / "runorder_pilots.csv")[0]
    used = {a for a in bs.launcher_cmd("PY", job, "r") if a.startswith("--")}
    assert used <= known, used - known
    assert 'choices=["claude", "codex"]' in text and 'add_argument("problems", nargs="*")' in text
    # what the scheduler reads back: the launcher's events and the collector's printed line
    for word in ('event="launched", problem=prob', 'event="finished", problem=prob, runner_exit=p.returncode, cid=cid'):
        assert word in text, word


def test_real_launcher_cannot_be_built_in_a_dry_run(tmp_path):
    e = Env(tmp_path, mixed(2), dry_run=True)
    with pytest.raises(RuntimeError, match="never"):
        bs.RealLauncher(e.cfg)


# ---------------------------------------------------------------- classification (plan section 5, D14)

@pytest.mark.parametrize("kw, status, infra, flags", [
    (dict(cid="c", collected=True, submitted=True, has_grade=True), "ok", False, []),
    (dict(cid="c", collected=True, submitted=True, has_grade=True, harness_status="api_error"), "ok", False,
     ["api_error_after_submit"]),
    (dict(cid="c", collected=True, submitted=True, has_grade=True, timeout=True), "ok", False,
     ["timeout_after_submit"]),
    (dict(cid="c", collected=True, submitted=True, has_grade=False, harness_status="no_grade_with_submission"),
     "needs_regrade", False, ["needs_regrade"]),
    (dict(cid="c", collected=True, submitted=True, has_grade=False, harness_status="api_error"),
     "needs_regrade", False, ["api_error_after_submit", "needs_regrade"]),
    (dict(cid="c", collected=True, has_grade=True, harness_status="ok"), "fail:no_submission", False, []),
    (dict(cid="c", collected=True, has_grade=True, timeout=True), "fail:timeout", False, []),
    (dict(cid="c", collected=True, has_grade=True, harness_status="no_agent_activity"), "fail:no_submission",
     False, ["no_agent_activity", "manual_look"]),
    (dict(cid="c", collected=True, has_grade=True, daemon_died=True), "fail:no_submission", False,
     ["daemon_died", "manual_look"]),
    (dict(cid="c", collected=True, has_grade=True, harness_status="api_error"), "infra:api_error", True, []),
    (dict(cid="c", collected=True, has_grade=True, harness_status="api_error", timeout=True), "infra:api_error",
     True, []),
    (dict(cid="c", collected=True, has_grade=False, harness_status="no_grade"), "infra:no_grade", True, []),
    (dict(cid=None, collected=False, runner_exit=1), "infra:no_container", True, ["runner_exit_1"]),
    (dict(cid=None, collected=False, runner_exit=None, interrupted=True), "infra:interrupted", True, []),
    (dict(cid="c", collected=False), "unknown:collect_failed", False, ["needs_collect"]),
    (dict(cid="c", collected=True, has_grade=True, runner_exit=137), "fail:no_submission", False,
     ["runner_exit_137"]),
])
def test_classify(kw, status, infra, flags):
    out = bs.classify(**kw)
    assert (out.status, out.infra, out.flags) == (status, infra, flags)


def test_a_run_with_an_accepted_submission_is_never_an_infrastructure_failure():
    for hs in (None, "ok", "api_error", "no_agent_activity", "no_grade", "no_grade_with_submission", "timeout"):
        for grade in (True, False):
            for timeout in (True, False):
                for died in (True, False):
                    out = bs.classify("c", True, submitted=True, has_grade=grade, timeout=timeout,
                                      harness_status=hs, daemon_died=died, runner_exit=1)
                    assert not out.infra and out.status in ("ok", "needs_regrade")


# ---------------------------------------------------------------- RUNLOG.md

def test_runlog_cums_continue_from_the_committed_runlog():
    text = (ROOT / "results" / "blackbox_1112" / "RUNLOG.md").read_text()
    o, a = bs.runlog_cums(text)
    assert o >= 0.02 and a >= 0.50  # the Exp E row; later rows only add
    assert bs.runlog_cums("# nothing here\n") == (0.0, 0.0)
    assert bs.runlog_cums("| a | b | c | d | e | f | 0.5 | x | y |\n| t | r | a | g | i | s | 1 | 2.5 | 3.25 |\n"
                          "| note | without | numbers |\n") == (2.5, 3.25)


def test_append_runlog_adds_to_one_provider_and_rereads_the_file(tmp_path):
    p = tmp_path / "RUNLOG.md"
    assert bs.append_runlog(p, 0, "aaa", "bb8", "gpt", "ep411", "ok", 0.6, "openai") == {"openai": 0.6, "anthropic": 0.0}
    assert bs.append_runlog(p, 0, "bbb", "bb8", "haiku", "ep472", "ok", 1.25, "anthropic") == {"openai": 0.6, "anthropic": 1.25}
    with open(p, "a") as f:  # another tool (Exp D) appends a row with its own cumulative values, no final newline
        f.write("| 2026-11-13T01:00Z | exp_d | exp_d | four | - | ok | 20.00 | 4.60 | 19.25 |")
    cum = bs.append_runlog(p, 0, "ccc", "open8", "gpt", "ep411", "infra:api_error | odd", 0.1, "openai")
    assert cum == {"openai": 4.7, "anthropic": 19.25} and bs.read_cums(p) == cum
    last = p.read_text().splitlines()[-1]
    assert last == "| 1970-01-01T00:00Z | ccc | open8 | gpt | ep411 | infra:api_error / odd | 0.100 | 4.700 | 19.250 |"
    assert p.read_text().startswith("# Black-box study run log")


# ---------------------------------------------------------------- order, slots, gap

def test_order_is_the_file_order_and_never_more_than_three_run(tmp_path):
    e = Env(tmp_path, mixed(14), by_order({i: {"minutes": 5 + 7 * (i % 4)} for i in range(1, 15)}))
    e.run()
    launched = e.events("launched")
    assert [x["order"] for x in launched] == list(range(1, 15))
    assert e.launcher.peak == 3 and max(x["running"] for x in launched) == 3
    assert e.summary["recorded"] == 14 and e.summary["peak_running"] == 3 and e.summary["status"] == {"ok": 14}
    assert e.events()[-1]["event"] == "end" and e.events()[-1]["reason"] == "done"
    # a job starts only after a slot is free: at every launch at most two earlier jobs are unrecorded
    done_at = {x["order"]: x["ts"] for x in e.events("finished")}
    for x in launched:
        assert sum(1 for y in launched if y["order"] < x["order"] and done_at[y["order"]] > x["ts"]) <= 2


@pytest.mark.parametrize("slots", [1, 2])
def test_max_slots(tmp_path, slots):
    e = Env(tmp_path, mixed(6), max_slots=slots)
    e.run()
    assert e.launcher.peak == slots and e.summary["recorded"] == 6


@pytest.mark.parametrize("gap", [90, 100, 240])
def test_gap_between_launches(tmp_path, gap):
    e = Env(tmp_path, mixed(9), gap=gap)
    e.run()
    ts = [x["ts"] for x in e.events("launched")]
    assert all(b - a >= gap for a, b in zip(ts, ts[1:]))
    assert ts[1] - ts[0] < gap + 2 * e.cfg.poll  # and not much more when a slot is free


def test_next_job_waits_until_the_previous_launcher_has_started_its_container(tmp_path):
    # job 1's launcher waits 10 minutes for the host (RAM, GPU, pause file) before it starts the container
    e = Env(tmp_path, mixed(3), by_order({1: {"launch_delay": 600, "minutes": 5}}))
    e.run()
    l1, l2, l3 = e.events("launched")
    assert l2["ts"] - l1["ts"] >= 600 + e.cfg.gap  # the gap counts from the container launch, not from the spawn
    assert l3["ts"] - l2["ts"] >= e.cfg.gap
    assert any("order 1: its launcher has not started its container yet" in s for s in e.said)


# ---------------------------------------------------------------- ledger and RUNLOG

def test_ledger_and_runlog_rows_and_cumulative_sums_per_provider(tmp_path):
    rows = [(G, "open8", "ep411", 1), (H, "bb8", "ep472", 1), (G, "bb64", "ep413", 1), (H, "bb64", "ep474", 1)]
    usd = {1: 0.5, 2: 1.25, 3: 0.75, 4: 2.0}
    e = Env(tmp_path, rows, by_order({o: {"usd": u, "minutes": 10 * o} for o, u in usd.items()}))
    e.cfg.runlog.write_text(bs.RUNLOG_HEADER + "| 2026-11-10T07:35Z | exp_e | exp_e | all | - | ok | 0.52 | 0.02 | 0.50 |\n")
    e.run()
    fin = e.events("finished")
    assert [x["order"] for x in fin] == [1, 2, 3, 4] and all(x["status"] == "ok" for x in fin)
    assert [(x["cum_openai"], x["cum_anthropic"]) for x in fin] == [(0.52, 0.5), (0.52, 1.75), (1.27, 1.75), (1.27, 3.75)]
    rl = e.runlog_rows()
    assert len(rl) == 1 + 4
    assert [r[1] for r in rl[1:]] == [x["cid"] for x in fin]
    assert [(r[2], r[3], r[4], r[5]) for r in rl[1:]] == [("open8", "gpt", "ep411", "ok"), ("bb8", "haiku", "ep472", "ok"),
                                                           ("bb64", "gpt", "ep413", "ok"), ("bb64", "haiku", "ep474", "ok")]
    assert [(float(r[6]), float(r[7]), float(r[8])) for r in rl[1:]] == [(0.5, 0.52, 0.5), (1.25, 0.52, 1.75),
                                                                         (0.75, 1.27, 1.75), (2.0, 1.27, 3.75)]
    assert e.summary["spend"] == {"openai": 1.25, "anthropic": 3.25}
    assert e.summary["cum"] == {"openai": 1.27, "anthropic": 3.75}
    # every event is one JSON object with time, block and (for job events) the job's identity
    for x in e.events():
        assert x["block"] == "block1" and "t" in x and "ts" in x
    for x in e.events("launched", "finished"):
        assert {"order", "attempt", "agent", "arm", "item", "problem", "provider", "run"} <= set(x)
    start = e.events("start")[0]
    assert start["runorder_sha256"] == bs.sha256_file(e.runorder) and start["jobs"] == 4
    assert [x["run"] for x in e.events("launched")] == ["r1112_gpt_open8", "r1112_haiku_bb8", "r1112_gpt_bb64",
                                                        "r1112_haiku_bb64"]


def test_pilot_runs_go_to_pilot_directories_and_are_marked_in_the_runlog(tmp_path):
    e = Env(tmp_path, [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1)], name="runorder_pilots.csv", pilot=True)
    e.run()
    assert [x["run"] for x in e.events("launched")] == ["r1112_pilot_gpt_bb8", "r1112_pilot_haiku_bb8"]
    assert [r[2] for r in e.runlog_rows()] == ["bb8 (pilot)", "bb8 (pilot)"]
    assert (e.cfg.rollouts / "r1112_pilot_gpt_bb8").is_dir() and not (e.cfg.rollouts / "r1112_gpt_bb8").exists()


def test_two_blocks_share_one_ledger_without_mixing_their_orders(tmp_path):
    p = Env(tmp_path, [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1)], name="runorder_pilots.csv", pilot=True)
    p.run()
    b = Env(tmp_path, mixed(5))
    b.run()
    assert b.cfg.ledger == p.cfg.ledger
    assert [x["order"] for x in b.events("launched") if x["block"] == "block1"] == [1, 2, 3, 4, 5]
    assert bs.summarize_ledger(b.events(), "pilots")["recorded"] == 2
    assert bs.summarize_ledger(b.events(), "block1")["recorded"] == 5
    assert float(b.runlog_rows()[-1][7]) + float(b.runlog_rows()[-1][8]) == 7.0  # 7 runs at $1, one file


def test_failed_runs_are_counted_fails_with_flags_and_not_rerun(tmp_path):
    spec = {1: {"outcome": "no_submission"}, 2: {"outcome": "timeout"}, 3: {"outcome": "daemon_died"},
            4: {"outcome": "no_activity"}, 5: {"outcome": "no_grade_submitted"}, 6: {"outcome": "api_error_submitted"},
            7: {"outcome": "timeout_submitted"}}
    e = Env(tmp_path, mixed(7), by_order(spec))
    e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    assert {o: x["status"] for o, x in fin.items()} == {
        1: "fail:no_submission", 2: "fail:timeout", 3: "fail:no_submission", 4: "fail:no_submission",
        5: "needs_regrade", 6: "ok", 7: "ok"}
    assert fin[3]["flags"] == ["daemon_died", "manual_look"] and fin[4]["flags"] == ["no_agent_activity", "manual_look"]
    assert fin[5]["flags"] == ["needs_regrade"] and fin[6]["flags"] == ["api_error_after_submit"]
    assert fin[7]["flags"] == ["timeout_after_submit"]
    assert len(e.events("launched")) == 7 and not e.events("infra", "requeued")
    assert not list(e.cfg.rollouts.glob("*/infra_failures.jsonl"))
    assert "needs_regrade (needs_regrade)" in [r[5] for r in e.runlog_rows()]
    assert {o for o, _, _, _ in e.summary["flagged"]} == {3, 4, 5, 6, 7}


# ---------------------------------------------------------------- infrastructure failures

def test_infra_failure_is_requeued_at_the_end_and_listed_in_the_run_directory(tmp_path):
    spec = {2: [{"outcome": "api_error", "usd": 0.3, "minutes": 4}, {"outcome": "ok", "usd": 1.5}]}
    e = Env(tmp_path, mixed(8), by_order(spec))
    e.run()
    launched = [(x["order"], x["attempt"]) for x in e.events("launched")]
    assert launched == [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (2, 2)]  # at the END
    infra = e.events("infra")
    assert len(infra) == 1 and infra[0]["reason"] == "api_error" and infra[0]["usd"] == 0.3 and infra[0]["n_infra"] == 1
    assert [x["order"] for x in e.events("requeued")] == [2]
    assert e.summary["recorded"] == 8 and e.summary["infra"] == {"api_error": 1}
    # real USD of the failed run counts toward spend: job 2 is Haiku
    assert e.summary["spend"]["anthropic"] == pytest.approx(0.3 + 1.5 + 3 * 1.0)
    run = e.cfg.rollouts / "r1112_haiku_bb8"
    listed = [json.loads(l) for l in (run / "infra_failures.jsonl").read_text().splitlines()]
    assert [r["cid"] for r in listed] == [infra[0]["cid"]] and listed[0]["reason"].startswith("api_error: no accepted")
    rows = [r for r in e.runlog_rows() if r[5].startswith("infra:api_error")]
    assert len(rows) == 1 and rows[0][1] == infra[0]["cid"] and float(rows[0][6]) == 0.3
    # the scorer excludes exactly the listed run (no accepted submission) and counts the re-run
    sn = _load("score_naming")
    assert sn.infra_cids(run) == {infra[0]["cid"]}
    assert sn.load_run(run / infra[0]["cid"])["status"] == "infra"


def test_at_most_two_reruns_then_the_job_is_given_up(tmp_path):
    rows = [(H, "bb8", "ep472", 1)] + [(G, "bb8", "ep411", i) for i in range(1, 5)] + [(G, "open8", "ep411", 1)]
    e = Env(tmp_path, rows, by_order({1: {"outcome": "no_grade", "usd": 0.2, "minutes": 3}}))
    e.run()
    assert [(x["order"], x["attempt"]) for x in e.events("launched") if x["order"] == 1] == [(1, 1), (1, 2), (1, 3)]
    assert [x["n_infra"] for x in e.events("infra")] == [1, 2, 3]
    assert [x["order"] for x in e.events("requeued")] == [1, 1] and [x["order"] for x in e.events("gave_up")] == [1]
    assert e.summary["gave_up"] == [1] and e.summary["recorded"] == 5
    assert len(e.events("launched")) == 5 + 3  # nothing else was run twice
    assert e.events("infra_stop")[0]["provider"] == "anthropic"  # three in a row for that provider
    assert len((e.cfg.rollouts / "r1112_haiku_bb8" / "infra_failures.jsonl").read_text().splitlines()) == 3


def test_no_container_is_an_infrastructure_failure_with_zero_usd(tmp_path):
    e = Env(tmp_path, mixed(4), by_order({1: [{"outcome": "no_container", "minutes": 1}, {"outcome": "ok"}]}))
    e.run()
    infra = e.events("infra")[0]
    assert infra["reason"] == "no_container" and infra["cid"] is None and infra["usd"] == 0
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3, 4, 1]
    assert not list(e.cfg.rollouts.glob("*/infra_failures.jsonl"))  # no container, nothing to list
    row = [r for r in e.runlog_rows() if r[5].startswith("infra:no_container")][0]
    assert row[1] == "none-block1-o1a1" and float(row[6]) == 0


def test_a_submitted_run_is_never_rerun(tmp_path):
    spec = {o: {"outcome": k} for o, k in enumerate(
        ["api_error_submitted", "no_grade_submitted", "timeout_submitted", "ok", "api_error_submitted"], 1)}
    e = Env(tmp_path, mixed(5), by_order(spec))
    e.run()
    assert [(x["order"], x["attempt"]) for x in e.events("launched")] == [(o, 1) for o in range(1, 6)]
    assert not e.events("infra", "requeued", "gave_up", "infra_stop")
    for run_dir in e.cfg.rollouts.iterdir():
        for d in run_dir.iterdir():
            if d.is_dir():
                assert (d / "submission.json").exists()


def test_api_error_pauses_that_providers_launches_for_fifteen_minutes(tmp_path):
    rows = [(H, "bb8", "ep472", 1), (G, "bb8", "ep411", 1), (H, "bb8", "ep474", 1), (G, "bb8", "ep413", 1)]
    e = Env(tmp_path, rows, by_order({1: [{"outcome": "api_error", "minutes": 2}, {"outcome": "ok"}]}), max_slots=1)
    e.run()
    infra = e.events("infra")[0]
    launched = {(x["order"], x["attempt"]): x["ts"] for x in e.events("launched")}
    assert launched[(2, 1)] - infra["ts"] < 120                       # the other provider is not paused
    assert launched[(3, 1)] - infra["ts"] >= bs.PAUSE_S                # Haiku waits out the pause ...
    assert launched[(4, 1)] > launched[(3, 1)]                         # ... and the queue keeps its order
    assert infra["pause_until"] == bs.iso(infra["ts"] + bs.PAUSE_S)
    assert any("anthropic paused until" in s for s in e.said)
    assert e.summary["recorded"] == 4


def test_three_consecutive_infra_failures_stop_that_provider_only(tmp_path):
    rows = [(H, "bb8", "ep472", 1), (H, "bb8", "ep474", 1), (H, "bb8", "ep476", 1), (G, "bb8", "ep411", 1),
            (H, "open8", "ep472", 1), (G, "bb8", "ep413", 1), (H, "open8", "ep474", 1), (G, "bb8", "ep415", 1)]
    bad = {"outcome": "no_grade", "minutes": 2, "usd": 0.1}
    e = Env(tmp_path, rows, by_order({1: bad, 2: bad, 3: bad}))
    e.run()
    stop = e.events("infra_stop")
    assert len(stop) == 1 and stop[0]["provider"] == "anthropic"
    assert sorted(stop[0]["skipped"]) == [1, 2, 3, 5, 7]  # its not-yet-run jobs and its re-queued ones
    assert sorted(x["order"] for x in e.events("skipped")) == [1, 2, 3, 5, 7]
    assert {x["why"] for x in e.events("skipped")} == {"infra_stop"}
    assert sorted(x["order"] for x in e.events("finished")) == [4, 6, 8]  # GPT keeps going
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3, 4, 6, 8]
    assert e.events("end")[0]["stopped"] == {"anthropic": "infra_stop"}


def test_a_success_resets_the_providers_streak(tmp_path):
    rows = [(H, "bb8", f"ep{472 + 2 * (i % 3)}", i // 3 + 1) for i in range(6)]
    bad = [{"outcome": "no_grade", "minutes": 2}, {"outcome": "ok"}]
    e = Env(tmp_path, rows, by_order({1: bad, 2: bad, 3: {"minutes": 3}, 4: bad}), max_slots=1)
    e.run()
    assert not e.events("infra_stop") and e.summary["recorded"] == 6 and e.summary["requeued"] == 3


# ---------------------------------------------------------------- the runner died, the container did not

REAL_RUNNER_LOG = (  # results/rollouts/r1103_gpt_b1/launch_ep411-open_1793691704.log of the main study
    "Waiting on container to run; watch progress with `./tools/watch-run.sh 150134e14dda`\n"
    "Container finished! Use `./tools/view-log.sh 150134e14dda engine` to see the rollout record or "
    "`./tools/debug-container.sh 150134e14dda` to get a shell into the final state of the container.\n"
    "No TPU detected - generated placeholder config at /x/docker/tpu-env.sh\n"
    "Skipping image builds (--skip-build). Existing images will be reused when present.\n"
    "150134e14dda\n")


def test_runner_log_ids_reads_both_lines_of_a_real_runner_log():
    assert bs.runner_log_ids(REAL_RUNNER_LOG) == ("150134e14dda", "150134e14dda")
    assert bs.runner_log_ids(REAL_RUNNER_LOG.splitlines()[0] + "\n") == ("150134e14dda", None)  # the runner died
    assert bs.runner_log_ids("Traceback (most recent call last):\n  AssertionError: deadbeef\n") == (None, None)
    assert bs.runner_log_ids("") == (None, None)
    assert bs.runner_log_ids("watch progress with `./tools/watch-run.sh 0123456789`\n") == ("0123456789", None)


def test_own_runner_logs_is_the_window_between_this_start_and_the_next(tmp_path):
    for name in ("launch_ep411-blackbox_1000.log", "launch_ep411-blackbox_1090.log", "launch_ep411-blackbox_1200.log",
                 "launch_ep411-blackbox64_1001.log", "launch_ep411-blackbox_x.log", "launch_sched_block1_o001_a1.log"):
        (tmp_path / name).write_text("")
    names = lambda *a: [(t, p.name) for t, p in bs.own_runner_logs(tmp_path, "ep411-blackbox", *a)]
    assert names(1000.4, 1090.2) == [(1000, "launch_ep411-blackbox_1000.log")]
    assert names(1090.2, 1200.0) == [(1090, "launch_ep411-blackbox_1090.log")]
    assert names(1090.2) == [(1090, "launch_ep411-blackbox_1090.log"), (1200, "launch_ep411-blackbox_1200.log")]
    assert names(1001, 1090) == [] and names(1300) == []
    assert [t for t, _ in bs.own_runner_logs(tmp_path, "ep411-blackbox64", 0)] == [1001]


def test_runner_died_after_the_container_started_is_not_no_container(tmp_path):
    # the launcher reports cid null / runner_exit 1 one minute after the launch; the container runs on for 30
    # minutes and accepts a submission. The job must not be re-run, and its cost must be counted.
    rows = [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1), (G, "open8", "ep411", 1)]
    e = Env(tmp_path, rows, by_order({1: {"outcome": "runner_died", "minutes": 30, "usd": 1.7}}), max_slots=1)
    e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    cid = next(iter(e.launcher.containers))
    assert (fin[1]["cid"], fin[1]["status"], fin[1]["usd"], fin[1]["cid_source"]) == (cid, "ok", 1.7, "runner_start")
    assert fin[1]["flags"] == ["runner_exit_1", "runner_died"]
    assert not e.events("infra", "requeued") and [(x["order"], x["attempt"]) for x in e.events("launched")] == [
        (1, 1), (2, 1), (3, 1)]
    la = {x["order"]: x["ts"] for x in e.events("launched")}
    assert fin[1]["ts"] >= la[1] + 30 * 60 and la[2] >= fin[1]["ts"]  # it kept the only slot until its container ended
    assert e.launcher.recollected == [cid] and any(f"its runner started container {cid}" in x for x in e.said)
    assert [r[1] for r in e.runlog_rows()][0] == cid and e.summary["spend"]["openai"] == pytest.approx(2.7)
    assert not list(e.cfg.rollouts.glob("*/infra_failures.jsonl"))


def test_runner_died_and_the_container_ended_without_a_submission_is_infra_with_its_cost(tmp_path):
    spec = {1: [{"outcome": "runner_died", "container": "no_grade", "minutes": 12, "usd": 0.9}, {"outcome": "ok"}],
            2: [{"outcome": "runner_died", "container": "no_submission", "minutes": 12, "usd": 0.5}]}
    e = Env(tmp_path, [(G, "bb8", "ep411", 1), (G, "bb8", "ep413", 1)], by_order(spec))
    e.run()
    infra = e.events("infra")
    assert len(infra) == 1 and (infra[0]["order"], infra[0]["reason"], infra[0]["usd"]) == (1, "no_grade", 0.9)
    assert infra[0]["cid"] and infra[0]["in_streak"] and infra[0]["flags"] == ["runner_exit_1", "runner_died"]
    listed = (e.cfg.rollouts / infra[0]["run"] / "infra_failures.jsonl").read_text().splitlines()
    assert [json.loads(l)["cid"] for l in listed] == [infra[0]["cid"]]
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[2]["status"] == "fail:no_submission" and fin[2]["usd"] == 0.5  # a counted fail, graded, not re-run
    assert [(x["order"], x["attempt"]) for x in e.events("launched")] == [(1, 1), (2, 1), (1, 2)]


def test_a_container_that_no_longer_exists_is_unknown_not_rerun(tmp_path):
    e = Env(tmp_path, mixed(2), by_order({1: {"outcome": "runner_died", "minutes": 5}}))
    real = e.launcher.poll

    def poll(h):  # the container is removed from the host by hand as soon as it exists
        out = real(h)
        e.launcher.containers.pop(h["cid"], None) if h["job"].order == 1 else None
        return out
    e.launcher.poll = poll
    s = e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[1]["status"] == "unknown:container_missing" and fin[1]["flags"] == ["manual_look"] and fin[1]["usd"] == 0
    assert len(e.events("launched")) == 2 and not e.events("infra") and [o for o, st in s.st.items() if not st.terminal] == [1]


def test_a_young_runner_log_without_a_container_is_given_time_at_a_restart(tmp_path):
    e = Env(tmp_path, mixed(2), by_order({1: {"outcome": "lost"}}), max_slots=1)
    e.run(stop_after=30)
    la = e.events("launched")[0]
    log = e.cfg.rollouts / la["run"] / f"launch_{la['problem']}_{int(la['ts']) + 2}.log"
    log.write_text("")  # the launcher was killed; its runner has printed nothing yet
    fresh = lose_launchers(e)
    s = e.sched(launcher=fresh, host=HostWith(0), stop_after=60)
    s.run()
    assert any("its runner may still be starting a container" in x for x in e.said)
    assert not e.events("infra", "finished") and len(e.events("launched")) == 1  # held: nothing recorded or started
    # (a) the runner got as far as the container: the job is that container's
    job = e.jobs[0]
    fresh.containers["0123456789ab"] = {"t_end": e.clock.t + 600, "job": job, "spec": {"usd": 0.3, "minutes": 10},
                                        "outcome": "ok"}
    log.write_text("Waiting on container to run; watch progress with `./tools/watch-run.sh 0123456789ab`\n")
    e.run(launcher=fresh, host=HostWith(1))
    fin = {x["order"]: x for x in e.events("finished")}
    assert (fin[1]["cid"], fin[1]["status"], fin[1]["usd"]) == ("0123456789ab", "ok", 0.3) and not e.events("infra")


def test_a_runner_log_that_stays_empty_is_interrupted_after_the_grace_time(tmp_path):
    e = Env(tmp_path, mixed(2), by_order({1: {"outcome": "lost"}}), max_slots=1)
    e.run(stop_after=30)
    la = e.events("launched")[0]
    (e.cfg.rollouts / la["run"] / f"launch_{la['problem']}_{int(la['ts']) + 2}.log").write_text("")
    e.run(launcher=lose_launchers(e), host=HostWith(0))
    infra = e.events("infra")
    assert [(x["order"], x["reason"], x["cid"]) for x in infra] == [(1, "interrupted", None)]
    assert infra[0]["ts"] - la["ts"] >= bs.RUNNER_GRACE_S and e.summary["recorded"] == 2


# ---------------------------------------------------------------- a stop holds

def test_infra_stop_holds_for_jobs_that_were_still_running(tmp_path):
    # orders 1 and 2 run long and end with no grade.json after 3, 4 and 5 failed at once and stopped Anthropic
    rows = [(H, "bb8", f"ep41{i}", 1) for i in (1, 3, 5)] + [(H, "bb64", f"ep41{i}", 1) for i in (1, 3, 5)] \
        + [(H, "open8", "ep411", 1), (H, "open8", "ep413", 1)]
    spec = {1: {"outcome": "no_grade", "minutes": 40, "usd": 2.0}, 2: {"outcome": "no_grade", "minutes": 45, "usd": 2.0},
            3: {"outcome": "no_container", "minutes": 0.5}, 4: {"outcome": "no_container", "minutes": 0.5},
            5: {"outcome": "no_container", "minutes": 0.5}}
    e = Env(tmp_path, rows, by_order(spec))
    e.run()
    evs = e.events()
    stop = next(i for i, x in enumerate(evs) if x["event"] == "infra_stop")
    assert [x["event"] for x in evs if x["event"] in ("infra_stop", "cap_stop")] == ["infra_stop"]
    assert not [x for x in evs[stop:] if x["event"] in ("launched", "launching", "requeued")]
    late = [(x["event"], x["order"], x.get("why", x.get("reason"))) for x in evs[stop:] if x["event"] in ("infra", "skipped")
            and x["order"] in (1, 2)]
    assert late == [("infra", 1, "no_grade"), ("skipped", 1, "infra_stop"), ("infra", 2, "no_grade"), ("skipped", 2, "infra_stop")]
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3, 4, 5]
    assert e.summary["spend"]["anthropic"] == 4.0 and e.events("end")[0]["stopped"] == {"anthropic": "infra_stop"}
    # at the next start the stop is over and every job is tried again, the failed ones last
    e.launcher.script = by_order({})
    e.run()
    assert [(x["order"], x["attempt"]) for x in e.events("launched")][5:] == [
        (6, 1), (7, 1), (8, 1), (3, 2), (4, 2), (5, 2), (1, 2), (2, 2)]
    assert e.summary["recorded"] == 8


def test_cap_stop_holds_for_a_job_that_was_still_running(tmp_path):
    # after order 1 ($1) the next GPT launch would pass cap - 5; orders 2 and 3 are still running and 2 then
    # fails: it is not re-queued, although with fewer running jobs the rule alone would let it start
    rows = [(G, "bb8", "ep411", i) for i in range(1, 6)]
    spec = {2: {"outcome": "no_grade", "minutes": 20, "usd": 0.1}, 3: {"minutes": 30}}
    e = Env(tmp_path, rows, by_order(spec), cap={"openai": 11.5, "anthropic": 130.0}, est={"gpt": 2.0, "haiku": 2.5})
    e.run()
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3] and len(e.events("cap_stop")) == 1
    assert [(x["order"], x["why"]) for x in e.events("skipped")] == [(4, "cap_stop"), (5, "cap_stop"), (2, "cap_stop")]
    assert not e.events("requeued")


# ---------------------------------------------------------------- spend caps

def test_cap_stop_for_one_provider_leaves_the_other_running(tmp_path):
    e = Env(tmp_path, mixed(12), by_order({}), cap={"openai": 800.0, "anthropic": 12.0}, est={"gpt": 1.5, "haiku": 2.5})
    e.cfg.runlog.write_text(bs.RUNLOG_HEADER + "| t | exp_e | exp_e | all | - | ok | 0.52 | 0.02 | 0.50 |\n")
    e.run()
    stops = e.events("cap_stop")
    assert len(stops) == 1 and stops[0]["provider"] == "anthropic"
    # the rule at each Haiku launch: cum + 2.5 x (running Haiku + 1) <= 12 - 5
    for x in e.events("launched"):
        if x["provider"] == "anthropic":
            assert x["cum_anthropic"] + 2.5 <= 12.0 - bs.CONTINGENCY
    done = e.events("finished")
    assert sorted(x["order"] for x in done if x["provider"] == "openai") == [1, 3, 5, 7, 9, 11]  # all of GPT
    n_haiku = sum(x["provider"] == "anthropic" for x in done)
    assert 1 <= n_haiku < 6
    assert sorted(x["order"] for x in e.events("skipped")) == sorted(stops[0]["skipped"])
    assert len(stops[0]["skipped"]) == 6 - n_haiku and {x["why"] for x in e.events("skipped")} == {"cap_stop"}
    assert float(e.runlog_rows()[-1][8]) <= 12.0  # the cap was never passed
    assert e.events("end")[0]["stopped"] == {"anthropic": "cap_stop"}


def test_cap_rule_counts_the_running_jobs_of_that_provider(tmp_path):
    # cap 11.5, contingency 5, est 2: 0 + 2 x 3 = 6 <= 6.5 lets three run at once; after one $1 run,
    # 1 + 2 x (2 running + 1) = 7 > 6.5
    rows = [(G, "bb8", "ep411", i) for i in range(1, 6)]
    e = Env(tmp_path, rows, by_order({}), cap={"openai": 11.5, "anthropic": 130.0}, est={"gpt": 2.0, "haiku": 2.5})
    e.run()
    stop = e.events("cap_stop")[0]
    assert (stop["cum"], stop["est"], stop["running"], stop["cap"]) == (1.0, 2.0, 2, 11.5)
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3] and stop["skipped"] == [4, 5]


def test_spend_written_by_another_tool_counts_toward_the_cap(tmp_path):
    e = Env(tmp_path, [(H, "bb8", "ep472", 1), (H, "bb8", "ep474", 1), (G, "bb8", "ep411", 1)], by_order({}),
            cap={"openai": 800.0, "anthropic": 130.0}, max_slots=1)
    s = e.sched()
    real_start = e.launcher.start

    def start(job, attempt, run, log):  # while job 1 runs, Exp D appends its Anthropic spend to RUNLOG.md
        if job.order == 1:
            with open(e.cfg.runlog, "a") as f:
                f.write("| 2026-11-13T02:00Z | exp_d | exp_d | four | - | ok | 124.00 | 0.02 | 124.00 |\n")
        return real_start(job, attempt, run, log)
    e.launcher.start = start
    s.run()
    assert e.events("cap_stop")[0]["provider"] == "anthropic" and e.events("cap_stop")[0]["skipped"] == [2]
    assert [x["order"] for x in e.events("finished")] == [1, 3]
    assert float(e.runlog_rows()[-1][8]) == 125.0


def _with_usd(e, values):
    """Make the collector row of order o carry values[o] as its usd (None, nan, a string ...)."""
    real = e.launcher.write_run

    def write_run(run_dir, cid, job, spec):
        real(run_dir, cid, job, spec)
        if job.order in values:
            p = Path(run_dir) / "summary.jsonl"
            rows = [json.loads(l) for l in p.read_text().splitlines()]
            rows[-1].update(usd=values[job.order], usd_source="no usage data")
            p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    e.launcher.write_run = write_run


def test_a_run_without_a_cost_is_counted_at_the_estimate_and_flagged(tmp_path):
    e = Env(tmp_path, [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1), (G, "bb8", "ep413", 1)], by_order({}))
    _with_usd(e, {1: None, 2: "1.2"})
    e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[1]["usd"] == 1.5 and fin[2]["usd"] == 2.5 and fin[3]["usd"] == 1.0  # --est-gpt, --est-haiku, measured
    for o in (1, 2):
        assert fin[o]["flags"] == ["usd_unknown", "manual_look"] and fin[o]["usd_source"].startswith("scheduler estimate")
        assert fin[o]["usd_source_reported"] == "no usage data"
    assert (fin[1]["usd_reported"], fin[2]["usd_reported"]) == (None, "1.2")
    assert e.summary["cum"] == {"openai": 2.5, "anthropic": 2.5} and not e.events("usd_stop", "cap_stop")
    assert "ok (usd_unknown, manual_look)" in [r[5] for r in e.runlog_rows()]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -3.0])
def test_a_cost_that_is_not_a_finite_number_stops_that_provider_and_never_reaches_the_runlog(tmp_path, bad):
    # cap 50: with a nan in the ledger every later comparison would be False and the cap would be switched off
    rows = [(G, "bb8", "ep411", i) for i in range(1, 9)] + [(H, "bb8", "ep472", 1)]
    e = Env(tmp_path, rows, by_order({o: {"usd": 30.0} for o in range(2, 9)}), cap={"openai": 50.0, "anthropic": 130.0})
    _with_usd(e, {1: bad})
    e.run()
    stop = e.events("usd_stop")
    assert len(stop) == 1 and stop[0]["provider"] == "openai" and stop[0]["order"] == 1
    assert stop[0]["usd_reported"] == str(bad)
    first = [x for x in e.events("finished") if x["order"] == 1][0]
    assert first["usd"] == 1.5 and "usd_unknown" in first["flags"]
    launched_after = [x["order"] for x in e.events("launched") if x["ts"] > stop[0]["ts"] and x["provider"] == "openai"]
    assert launched_after == [] and [x["order"] for x in e.events("finished") if x["provider"] == "anthropic"] == [9]
    for r in e.runlog_rows():
        assert all(bs.math.isfinite(float(v)) and float(v) >= 0 for v in r[6:9]), r
    assert all(x.get("why") == "usd_stop" for x in e.events("skipped")) and e.events("skipped")
    assert float(e.runlog_rows()[-1][7]) <= 50.0 + 30.0 * 2  # only what was already running could still be spent
    json.loads(e.cfg.ledger.read_text().splitlines()[-1], parse_constant=lambda c: pytest.fail(f"{c} in the ledger"))


def test_a_runlog_whose_cumulative_value_is_not_finite_stops_that_provider(tmp_path):
    assert bs.runlog_cums("| t | r | a | g | i | s | 1 | nan | 3.25 |\n") == (bs.math.inf, 3.25)
    assert bs.runlog_cums("| t | r | a | g | i | s | 1 | 2.0 | -1 |\n") == (2.0, bs.math.inf)
    assert bs.runlog_cums("| t | r | a | g | i | s | 1 | inf | 0 |\n")[0] == bs.math.inf
    e = Env(tmp_path, mixed(4), by_order({}))
    e.cfg.runlog.write_text(bs.RUNLOG_HEADER + "| 2026-11-12T00:00Z | by hand | x | x | - | ok | nan | nan | 0.50 |\n")
    e.run()
    stop = e.events("cap_stop")
    assert len(stop) == 1 and stop[0]["provider"] == "openai" and stop[0]["cum"] == "inf" and stop[0]["skipped"] == [1, 3]
    assert [x["order"] for x in e.events("launched")] == [2, 4]
    for line in e.cfg.ledger.read_text().splitlines():
        json.loads(line, parse_constant=lambda c: pytest.fail(f"{c} in the ledger"))
    assert e.cfg.runlog.read_text().splitlines()[-1].split("|")[-3].strip() == "inf"  # it stays until corrected


# ---------------------------------------------------------------- restart

def test_restart_skips_recorded_jobs_and_runs_the_rest_once(tmp_path):
    e = Env(tmp_path, mixed(9), by_order({}))
    e.run(stop_after=14 * 60)  # interrupted, as by SIGTERM
    first = e.events("finished")
    assert 0 < len(first) < 9 and e.events("end")[0]["reason"] == "test stop"
    e.clock.sleep(3600)  # the children end while no scheduler runs (they are in their own sessions)
    e.run()
    launched = [(x["order"], x["attempt"]) for x in e.events("launched")]
    assert sorted(launched) == [(o, 1) for o in range(1, 10)]  # every job launched exactly once
    assert [x["order"] for x in e.events("launched")] == list(range(1, 10))
    fin = e.events("finished")
    assert sorted(x["order"] for x in fin) == list(range(1, 10)) and len({x["cid"] for x in fin}) == 9
    assert sum(1 for x in fin if x.get("recovered")) >= 1
    assert len(e.runlog_rows()) == 9 and float(e.runlog_rows()[-1][7]) + float(e.runlog_rows()[-1][8]) == 9.0
    assert len(e.events("start")) == 2 and e.events("start")[1]["recorded"] == len(first)
    assert e.launcher.peak <= 3
    e.run()  # a third start finds nothing to do
    assert len(e.events("launched")) == 9 and e.events("end")[-1]["reason"] == "done"


def test_restart_while_a_launcher_is_alive_keeps_its_slot_and_records_it_when_it_ends(tmp_path):
    e = Env(tmp_path, mixed(7), by_order({1: {"minutes": 60}, 2: {"minutes": 60}, 3: {"minutes": 60}}))
    e.run(stop_after=10 * 60)
    assert len(e.events("launched")) == 3 and not e.events("finished")
    e.run()  # restarted at once: the three launchers are still running
    assert any("still running; it keeps its slot" in s for s in e.said)
    assert e.launcher.peak == 3
    launched = e.events("launched")
    assert [(x["order"], x["attempt"]) for x in launched] == [(o, 1) for o in range(1, 8)]
    fin = {x["order"]: x for x in e.events("finished")}
    assert all(fin[o].get("recovered") for o in (1, 2, 3)) and len(fin) == 7
    assert launched[3]["ts"] >= min(fin[o]["ts"] for o in (1, 2, 3))  # job 4 waited for a slot


def test_restart_after_a_reboot_collects_the_ended_containers_and_reruns_the_jobs_at_the_end(tmp_path):
    e = Env(tmp_path, mixed(5), by_order({1: {"usd": 0.4}, 2: {"outcome": "lost"}, 3: {"usd": 0.6}}))
    e.run(stop_after=5 * 60)
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3]
    fresh = lose_launchers(e, reboot=True)  # no launcher survives; the containers of 1 and 3 exist, ended, ungraded
    e.run(launcher=fresh, host=HostWith(0))
    infra = {x["order"]: x for x in e.events("infra")}
    assert {o: x["reason"] for o, x in infra.items()} == {1: "interrupted", 2: "interrupted", 3: "interrupted"}
    assert all(x["recovered"] and not x["in_streak"] for x in infra.values())
    # 1 and 3 had a container: it is collected, listed and costed, never "no container"
    for o, usd in ((1, 0.4), (3, 0.6)):
        x = infra[o]
        assert x["cid"] and x["cid_source"] == "runner_start" and x["usd"] == usd
        assert x["flags"] == ["container_cut_off", "runner_died"]
        run = e.cfg.rollouts / x["run"]
        assert [json.loads(l)["cid"] for l in (run / "infra_failures.jsonl").read_text().splitlines()] == [x["cid"]]
        assert [r for r in e.runlog_rows() if r[1] == x["cid"]][0][5].startswith("infra:interrupted (container_cut_off")
    assert infra[2]["cid"] is None and infra[2]["usd"] == 0  # its runner never named a container
    assert sorted(fresh.recollected) == sorted([infra[1]["cid"], infra[3]["cid"]])
    order = [(x["order"], x["attempt"]) for x in e.events("launched")]
    assert order == [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (1, 2), (2, 2), (3, 2)]  # fresh jobs first, re-runs last
    assert sorted(x["order"] for x in e.events("finished")) == [1, 2, 3, 4, 5]
    assert e.summary["spend"]["openai"] == pytest.approx(0.4 + 0.6 + 3 * 1.0)  # the cut-off runs' cost counts


def test_lost_jobs_at_a_restart_do_not_count_toward_the_providers_streak(tmp_path):
    # three GPT jobs are running when the host goes down: at the restart they are `interrupted`, which is not
    # a failure of the provider, so no infra_stop, nothing skipped, and the order of the rest is the file's
    rows = [(G, "bb8", "ep411", 1), (G, "bb8", "ep413", 1), (G, "bb8", "ep415", 1), (G, "open8", "ep411", 1),
            (H, "bb8", "ep472", 1), (G, "open8", "ep413", 1)]
    e = Env(tmp_path, rows, by_order({}))
    e.run(stop_after=5 * 60)
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3]
    e.run(launcher=lose_launchers(e, reboot=True), host=HostWith(0))
    assert [x["reason"] for x in e.events("infra")] == ["interrupted"] * 3
    assert not e.events("infra_stop", "skipped", "gave_up")
    assert [(x["order"], x["attempt"]) for x in e.events("launched")][3:] == [(4, 1), (5, 1), (6, 1), (1, 2), (2, 2), (3, 2)]
    assert e.summary["recorded"] == 6 and [x["n_infra"] for x in e.events("infra")] == [1, 1, 1]  # a re-run is used


def test_restart_after_a_reboot_never_reruns_a_run_whose_container_holds_a_submission(tmp_path):
    e = Env(tmp_path, mixed(3), by_order({1: {"submitted_at_reboot": True, "usd": 0.8}}))
    e.run(stop_after=5 * 60)
    e.run(launcher=lose_launchers(e, reboot=True), host=HostWith(0))
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[1]["status"] == "needs_regrade" and fin[1]["attempt"] == 1 and fin[1]["usd"] == 0.8
    assert fin[1]["flags"] == ["needs_regrade", "runner_died"] and fin[1]["cid_source"] == "runner_start"
    assert [x["order"] for x in e.events("infra")] == [2, 3] and 1 not in [x["order"] for x in e.events("requeued")]
    assert [(x["order"], x["attempt"]) for x in e.events("launched")] == [(1, 1), (2, 1), (3, 1), (2, 2), (3, 2)]


def test_restart_refuses_when_unaccounted_task_containers_are_still_running(tmp_path):
    e = Env(tmp_path, mixed(3), by_order({1: {"outcome": "lost"}}))
    e.run(stop_after=5 * 60)
    n = len(e.events())
    # launchers killed, runners and containers alive: 2 and 3 are accounted for by their runner logs; order 1
    # has no container on record, and the host runs one container more than the two that are known
    with pytest.raises(SystemExit, match="task containers are still running"):
        e.run(launcher=lose_launchers(e), host=HostWith(3))
    assert [x["event"] for x in e.events()[n:]] == ["start"]  # no job was recorded, re-queued or started


def test_restart_with_launchers_gone_waits_for_their_running_containers(tmp_path):
    e = Env(tmp_path, mixed(4), by_order({1: {"outcome": "lost"}, 2: {"minutes": 20, "usd": 0.7}, 3: {"minutes": 30}}))
    e.run(stop_after=5 * 60)
    t_restart = e.clock.t
    fresh = lose_launchers(e)  # e.g. `pkill -f launch_rollouts`: the runners and the containers go on
    e.run(launcher=fresh, host=HostWith(2))
    assert sum("which has not ended yet" in x for x in e.said) == 2
    fin = {x["order"]: x for x in e.events("finished")}
    # 2 and 3 are never "no container": they keep their slots, are collected when their containers end
    assert fin[2]["status"] == fin[3]["status"] == "ok" and fin[2]["usd"] == 0.7
    assert fin[2]["flags"] == fin[3]["flags"] == ["runner_died"] and fin[2]["attempt"] == fin[3]["attempt"] == 1
    assert fin[2]["ts"] >= e.events("launched")[1]["ts"] + 20 * 60 and fin[3]["ts"] >= e.events("launched")[2]["ts"] + 30 * 60
    assert [(x["order"], x["reason"]) for x in e.events("infra")] == [(1, "interrupted")]
    launched = [(x["order"], x["attempt"], x["ts"]) for x in e.events("launched")]
    assert [x[:2] for x in launched] == [(1, 1), (2, 1), (3, 1), (4, 1), (1, 2)]
    assert launched[3][2] - t_restart < 120  # one slot was free (order 1's); the two waiting jobs hold the others
    assert fresh.peak + 2 <= 3 and sorted(fresh.recollected) == sorted([fin[2]["cid"], fin[3]["cid"]])


def test_restart_finds_a_container_the_runner_reported_after_its_launcher_died(tmp_path):
    e = Env(tmp_path, [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1)], by_order({1: {"outcome": "lost"}}), max_slots=1)
    e.run(stop_after=3 * 60)
    la = e.events("launched")[0]
    run = e.cfg.rollouts / la["run"]
    # the runner outlived the launcher, the container ended with a submission, nobody collected it
    (run / f"launch_ep411-blackbox_{int(la['ts']) + 5}.log").write_text("Starting...\n0123456789ab\n")
    (run / "launch_ep411-blackbox_100.log").write_text("an older launch\nffffffffffff\n")
    fresh = bs.FakeLauncher(e.cfg, e.clock, by_order({}))
    job = e.jobs[0]
    fresh.recollect = lambda cid, run_dir: fresh.write_run(run_dir, cid, job, {"outcome": "ok", "usd": 0.7, "minutes": 9})
    e.run(launcher=fresh)
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[1]["cid"] == "0123456789ab" and fin[1]["status"] == "ok" and fin[1]["recovered"] and fin[1]["usd"] == 0.7
    assert fin[1]["cid_source"] == "runner_end" and fin[1]["flags"] == []
    assert [(x["order"], x["attempt"]) for x in e.events("launched")] == [(1, 1), (2, 1)] and not e.events("infra")


def test_two_identical_jobs_each_get_their_own_container_after_their_launchers_died(tmp_path):
    rows = [(G, "bb8", "ep411", 1), (G, "bb8", "ep411", 2)]  # same batch directory, same PROBLEM
    e = Env(tmp_path, rows, by_order({1: {"minutes": 30, "usd": 0.9}, 2: {"minutes": 4, "usd": 0.7}}))
    e.run(stop_after=150)
    la = e.events("launched")
    assert [x["order"] for x in la] == [1, 2] and la[0]["run"] == la[1]["run"]
    cids = {h["job"].order: h["cid"] for h in e.launcher.handles.values()}
    fresh = lose_launchers(e)   # both launchers are killed; the runners and the containers go on
    e.clock.sleep(4 * 60)       # the later job's container ends and its runner prints the id; the earlier one runs
    run = e.cfg.rollouts / la[0]["run"]
    logs = sorted(run.glob("launch_ep411-blackbox_*.log"))
    assert len(logs) == 2
    with open(logs[1], "a") as f:
        f.write(f"Container finished!\n{cids[2]}\n")
    s = e.run(launcher=fresh, host=HostWith(1))
    assert any(f"order 1: its launcher has ended, but its runner started container {cids[1]}" in x for x in e.said)
    fin = {x["order"]: x for x in e.events("finished")}
    assert (fin[1]["cid"], fin[1]["status"], fin[1]["usd"], fin[1]["cid_source"]) == (cids[1], "ok", 0.9, "runner_start")
    assert (fin[2]["cid"], fin[2]["status"], fin[2]["usd"], fin[2]["cid_source"]) == (cids[2], "ok", 0.7, "runner_end")
    assert fin[1]["ts"] >= la[0]["ts"] + 30 * 60 > fin[2]["ts"]  # the earlier job waited for its own container
    assert len(e.events("launched")) == 2 and not e.events("infra") and all(st.terminal for st in s.st.values())
    assert sorted(r[1] for r in e.runlog_rows()) == sorted(cids.values())


def test_one_container_is_never_recorded_for_two_jobs(tmp_path):
    # the last line of defence: whatever a runner log says, a container id that is already recorded is not
    # recorded for a second job; that job becomes unknown and is not run again by itself
    rows = [(G, "bb8", "ep411", 1), (G, "bb8", "ep411", 2)]
    e = Env(tmp_path, rows, by_order({1: {"minutes": 3}, 2: {"outcome": "lost"}}))
    e.run(stop_after=5 * 60)
    first = e.events("finished")[0]
    la = e.events("launched")[1]
    run = e.cfg.rollouts / la["run"]
    (run / f"launch_ep411-blackbox_{int(la['ts']) + 1}.log").write_text(f"{first['cid']}\n")  # a wrong id
    s = e.run(launcher=lose_launchers(e))
    fin = e.events("finished")
    assert [(x["order"], x["status"]) for x in fin] == [(1, "ok"), (2, "unknown:duplicate_cid")]
    assert len(e.events("launched")) == 2 and not e.events("infra")
    assert [o for o, st in s.st.items() if not st.terminal] == [2]


def test_a_run_of_another_arm_or_model_is_flagged(tmp_path):
    e = Env(tmp_path, [(G, "bb8", "ep411", 1)], by_order({}))
    real = e.launcher.write_run

    def write_run(run_dir, cid, job, spec):
        real(run_dir, cid, job, spec)
        p = Path(run_dir) / "summary.jsonl"
        row = json.loads(p.read_text())
        p.write_text(json.dumps({**row, "arm": "open8"}) + "\n")
    e.launcher.write_run = write_run
    e.run()
    assert e.events("finished")[0]["flags"] == ["arm_mismatch", "manual_look"]


def test_uncollected_run_is_not_rerun_and_is_looked_at_again_at_the_next_start(tmp_path):
    e = Env(tmp_path, mixed(3), by_order({2: {"outcome": "collect_failed", "usd": 0.9}}))
    s = e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[2]["status"] == "unknown:collect_failed" and "needs_collect" in fin[2]["flags"] and fin[2]["usd"] == 0
    assert e.launcher.recollected == [fin[2]["cid"]]  # one more collection was tried
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3] and not e.events("infra")
    assert e.summary["recorded"] == 2 and [o for o, st in s.st.items() if not st.terminal] == [2]
    e.run()  # still unreadable: nothing new is logged for it, and it is not started again
    assert len(e.events("launched")) == 3 and len(e.events("finished")) == 3
    assert any("still unknown:collect_failed" in x for x in e.said)
    # collected by hand (collect_rollouts.py <cid> --out <run>), then the next start records it with its cost
    job = e.jobs[1]
    e.launcher.write_run(e.cfg.rollouts / fin[2]["run"], fin[2]["cid"], job, {"outcome": "ok", "usd": 0.9, "minutes": 9})
    e.run()
    last = e.events("finished")[-1]
    assert (last["order"], last["status"], last["usd"], last["resolved"]) == (2, "ok", 0.9, True)
    assert len(e.events("launched")) == 3 and e.summary["recorded"] == 3 and e.summary["status"] == {"ok": 3}


def test_restart_keeps_the_rerun_count_and_the_end_of_queue_position(tmp_path):
    bad = {"outcome": "no_grade", "minutes": 2}
    e = Env(tmp_path, [(H, "bb8", "ep472", 1)] + [(G, "bb8", "ep411", i) for i in range(1, 7)],
            by_order({1: [bad, bad, {"outcome": "ok"}]}), max_slots=1)
    e.run(stop_after=14 * 60)
    assert len(e.events("infra")) == 1 and len(e.events("finished")) >= 1
    e.clock.sleep(3600)
    e.run()
    order = [(x["order"], x["attempt"]) for x in e.events("launched")]
    assert order == [(1, 1)] + [(o, 1) for o in range(2, 8)] + [(1, 2), (1, 3)]
    assert [x["n_infra"] for x in e.events("infra")] == [1, 2] and e.summary["recorded"] == 7


def test_a_pause_that_has_not_run_out_survives_a_restart(tmp_path):
    rows = [(H, "bb8", "ep472", 1), (H, "bb8", "ep474", 1)]
    e = Env(tmp_path, rows, by_order({1: [{"outcome": "api_error", "minutes": 2}, {"outcome": "ok"}]}), max_slots=1)
    e.run(stop_after=4 * 60)
    infra = e.events("infra")[0]
    e.run()
    second = [x for x in e.events("launched") if x["order"] == 2][0]
    assert second["ts"] - infra["ts"] >= bs.PAUSE_S


def test_jobs_skipped_by_a_cap_stop_run_after_a_restart_with_a_higher_cap(tmp_path):
    rows = [(G, "bb8", "ep411", i) for i in range(1, 5)]
    e = Env(tmp_path, rows, by_order({}), cap={"openai": 8.0, "anthropic": 130.0}, max_slots=1)
    e.run()
    assert [x["order"] for x in e.events("launched")] == [1, 2] and e.events("cap_stop")[0]["skipped"] == [3, 4]
    e.cfg.cap["openai"] = 800.0
    e.run()
    assert [x["order"] for x in e.events("launched")] == [1, 2, 3, 4] and e.summary["recorded"] == 4


def test_only_one_scheduler_at_a_time_on_a_ledger(tmp_path):
    e = Env(tmp_path, mixed(2))
    other = bs.Ledger(e.cfg.ledger)
    other.lock()
    try:
        with pytest.raises(SystemExit, match="another scheduler"):
            e.run()
    finally:
        other.unlock()
    e.run()
    assert e.summary["recorded"] == 2


def test_a_block_cannot_continue_with_a_changed_run_order(tmp_path):
    e = Env(tmp_path, mixed(4))
    e.run(stop_after=60)
    write_runorder(e.runorder, list(reversed(mixed(4))))
    e.jobs = bs.read_runorder(e.runorder)
    with pytest.raises(SystemExit, match="must not change within a block"):
        e.run()


def test_interrupt_leaves_running_jobs_alone_and_says_so(tmp_path):
    e = Env(tmp_path, mixed(6), by_order({}))
    e.run(stop_after=4 * 60)
    end = e.events("end")[0]
    assert end["reason"] == "test stop" and end["running"] == [1, 2, 3] and end["queued"] == 3
    assert e.launcher.running() == 3 and not e.events("finished", "infra")


# ---------------------------------------------------------------- a scheduler killed between two writes

class Kill(BaseException):
    """SIGKILL / OOM / host crash: nothing after this point of the scheduler process happens."""


FUZZ_ROWS = [((G, H)[i % 2], ("open8", "bb8", "bb64")[i % 3], ("ep411", "ep472", "ep413")[(i // 3) % 3], i // 9 + 1)
             for i in range(10)]
FUZZ_SPEC = {2: [{"outcome": "no_grade", "minutes": 5, "usd": 0.4}, {"outcome": "ok"}],
             5: [{"outcome": "no_container", "minutes": 1}] * 3,
             7: {"outcome": "no_submission"}, 8: {"outcome": "collect_failed"},
             9: {"outcome": "runner_died", "minutes": 25, "usd": 0.8}}


def fuzz_run(tmp, kill_at, when):
    """One block with the scheduler killed at its kill_at-th ledger write (just before or just after it), then
    started again (the launchers live on in their own sessions) until nothing is left. -> (event killed at, Env)."""
    tmp.mkdir()
    e = Env(tmp, FUZZ_ROWS, by_order(FUZZ_SPEC))
    s, n = e.sched(), [0]
    write = s.ledger.append

    def append(ev):
        n[0] += 1
        if n[0] == kill_at and when == "before":
            raise Kill(ev["event"])
        write(ev)
        if n[0] == kill_at and when == "after":
            raise Kill(ev["event"])
    s.ledger.append = append
    try:
        s.run()
        return None, e
    except Kill as k:
        killed = str(k)
    for _ in range(2):
        e.run()
    return killed, e


def fuzz_problems(e):
    from collections import Counter
    evs, out = e.events(), []
    count = lambda kind, **kw: Counter(x["order"] for x in evs if x["event"] == kind and all(x.get(k) == v for k, v in kw.items()))
    starts = Counter(o for o, _, _ in e.launcher.started)
    launched, infra, gave = count("launched"), count("infra"), count("gave_up")
    fin = Counter(x["order"] for x in evs if x["event"] == "finished" and not x["status"].startswith("unknown"))
    for o in range(1, len(FUZZ_ROWS) + 1):
        if starts[o] != launched[o]:
            out.append(f"order {o}: {starts[o]} launcher processes, {launched[o]} launched events")
        if o != 8 and fin[o] + gave[o] != 1:
            out.append(f"order {o}: finished {fin[o]}, gave_up {gave[o]}")
        if infra[o] > bs.MAX_RERUNS + 1:
            out.append(f"order {o}: {infra[o]} infra events")
        if starts[o] > bs.MAX_RERUNS + 1:
            out.append(f"order {o}: started {starts[o]} times")
    rows = e.runlog_rows()
    recs = [x for x in evs if x["event"] in ("finished", "infra")]
    if len(rows) != len(recs):
        out.append(f"{len(rows)} RUNLOG rows, {len(recs)} finished + infra events")
    ids = Counter(r[1] for r in rows)
    out += [f"RUNLOG has {k} {v} times" for k, v in ids.items() if v > 1]
    cum = bs.read_cums(e.cfg.runlog)
    for p in bs.PROVIDERS:
        led = sum(x["usd"] for x in recs if x["provider"] == p)
        if abs(cum[p] - led) > 1e-6:
            out.append(f"RUNLOG cumulative {p} {cum[p]} != ledger {led:.3f}")
    for run in e.cfg.rollouts.iterdir():
        listed = [json.loads(l)["cid"] for l in (run / "infra_failures.jsonl").read_text().splitlines()] \
            if (run / "infra_failures.jsonl").exists() else []
        if len(listed) != len(set(listed)):
            out.append(f"{run.name}/infra_failures.jsonl lists a container twice")
    # order 9: its runner died, its container accepted a submission. One launcher process, one record, and no
    # infra event that names a container (an attempt killed before its process existed is `interrupted`, cid null)
    if fin[9] != 1 or starts[9] != 1 or [x for x in evs if x["event"] == "infra" and x["order"] == 9 and x["cid"]]:
        out.append("order 9 (runner died, container submitted) was not recorded exactly once without a re-run")
    return out


def test_a_scheduler_killed_at_any_ledger_write_loses_and_duplicates_nothing(tmp_path):
    killed, base = fuzz_run(tmp_path / "base", 10 ** 9, "before")
    assert killed is None and fuzz_problems(base) == []
    total = len(base.events())
    assert total >= 40 and {x["event"] for x in base.events()} >= {"launching", "launched", "finished", "infra",
                                                                    "requeued", "gave_up"}
    seen, bad = set(), []
    for when in ("before", "after"):
        for k in range(1, total + 1):
            killed, e = fuzz_run(tmp_path / f"{when}{k}", k, when)
            if killed is None:
                continue
            seen.add((when, killed))
            bad += [f"kill {when} write #{k} ({killed}): {p}" for p in fuzz_problems(e)]
    assert not bad, "\n".join(bad[:20])
    assert {("before", k) for k in ("launching", "launched", "finished", "infra", "requeued", "gave_up")} <= seen


def test_killed_between_launching_and_the_process_start_the_attempt_is_interrupted(tmp_path):
    e = Env(tmp_path, mixed(3), by_order({}))
    s = e.sched()
    real = e.launcher.start

    def start(job, attempt, run, log):
        if job.order == 2:
            raise Kill("before Popen")
        return real(job, attempt, run, log)
    e.launcher.start = start
    with pytest.raises(Kill):
        s.run()
    e.launcher.start = real
    assert [(x["event"], x["order"]) for x in e.events("launching", "launched")] == [
        ("launching", 1), ("launched", 1), ("launching", 2)]
    e.run()
    infra = e.events("infra")
    assert [(x["order"], x["attempt"], x["reason"], x["usd"]) for x in infra] == [(2, 1, "interrupted", 0)]
    assert [(x["order"], x["attempt"]) for x in e.events("launched")] == [(1, 1), (3, 1), (2, 2)]
    assert [o for o, _, _ in e.launcher.started] == [1, 3, 2] and e.summary["recorded"] == 3


def test_killed_between_the_process_start_and_launched_the_child_is_found_again(tmp_path):
    e = Env(tmp_path, mixed(3), by_order({}))
    s = e.sched()
    write = s.ledger.append

    def append(ev):
        if ev["event"] == "launched" and ev["order"] == 2:
            raise Kill("before launched")
        write(ev)
    s.ledger.append = append
    with pytest.raises(Kill):
        s.run()
    assert [o for o, _, _ in e.launcher.started] == [1, 2]  # the process exists, the ledger has only its intent
    e.run()
    la = [x for x in e.events("launched") if x["order"] == 2]
    assert len(la) == 1 and la[0]["recovered"] and la[0]["pid"] == 100001 and la[0]["attempt"] == 1
    assert [o for o, _, _ in e.launcher.started] == [1, 2, 3] and e.summary["recorded"] == 3 and not e.events("infra")
    assert e.summary["peak_running"] <= 3


def test_replay_a_job_is_terminal_after_its_third_infra_event_without_gave_up(tmp_path):
    ev = lambda kind, **kw: {"block": "block1", "order": 1, "event": kind, **kw}
    evs = [ev("launching", attempt=1), ev("launched", attempt=1), ev("infra"), ev("requeued"),
           ev("launched", attempt=2), ev("infra"), ev("launched", attempt=3), ev("infra")]
    st = bs.replay(evs, "block1", 1)[1]
    assert (st.attempts, st.infra, st.terminal, st.gave_up, st.open) == (3, 3, True, False, None)
    assert not bs.replay(evs[:-1], "block1", 1)[1].terminal and bs.replay(evs[:-1], "block1", 1)[1].open == evs[-2]
    # the missing gave_up is written at the next start, and the job is not started again
    e = Env(tmp_path, [(G, "bb8", "ep411", 1)], by_order({}))
    e.cfg.ledger.write_text("".join(json.dumps({**x, "ts": 1.0 + i, "run": "r1112_gpt_bb8", "child_log": "x.log",
                                                "problem": "ep411-blackbox"}) + "\n" for i, x in enumerate(evs)))
    e.run()
    assert [(x["order"], x["n_infra"], x["recovered"]) for x in e.events("gave_up")] == [(1, 3, True)]
    assert not e.launcher.started and e.summary["gave_up"] == [1]


def test_runlog_row_is_written_once_per_run_id_and_status(tmp_path):
    p = tmp_path / "RUNLOG.md"
    a = bs.append_runlog(p, 0, "abc", "bb8", "gpt", "ep411", "ok (launcher_exit_1)", 0.6, "openai", once=True)
    b = bs.append_runlog(p, 60, "abc", "bb8", "gpt", "ep411", "ok", 0.6, "openai", once=True)  # the same record again
    assert a == b == {"openai": 0.6, "anthropic": 0.0} and len(p.read_text().splitlines()) == 5
    c = bs.append_runlog(p, 60, "abc", "bb8", "gpt", "ep411", "unknown:collect_failed (needs_collect)", 0, "openai", once=True)
    d = bs.append_runlog(p, 60, "abd", "bb8", "gpt", "ep411", "ok", 0.5, "openai", once=True)
    assert c == {"openai": 0.6, "anthropic": 0.0} and d == {"openai": 1.1, "anthropic": 0.0}
    assert len(p.read_text().splitlines()) == 7
    assert bs.runlog_has(p.read_text(), "abc", "ok [dry run]") and not bs.runlog_has(p.read_text(), "ab", "ok")


def test_real_launcher_recollect_survives_a_collector_that_hangs_or_cannot_start(tmp_path, monkeypatch):
    import subprocess
    e = Env(tmp_path, mixed(1))
    launcher = bs.RealLauncher(e.cfg)
    for exc in (subprocess.TimeoutExpired("collect", 600), FileNotFoundError("no python")):
        def run(*a, exc=exc, **kw):
            raise exc
        monkeypatch.setattr(bs.subprocess, "run", run)
        assert launcher.recollect("0123456789ab", tmp_path) is None   # -> no row -> unknown:collect_failed
        assert launcher.container_state("0123456789ab") == "unknown"   # -> the job keeps its slot


def test_real_launcher_container_state_reads_only_the_status(tmp_path, monkeypatch):
    import subprocess
    e = Env(tmp_path, mixed(1))
    launcher, calls = bs.RealLauncher(e.cfg), []
    answers = {"aaa": (0, "running\n", ""), "bbb": (0, "exited\n", ""), "ccc": (1, "", "Error: No such container: ccc"),
               "ddd": (1, "", "Cannot connect to the Docker daemon"), "eee": (0, "created\n", ""), "fff": (0, "dead\n", "")}

    def run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, *answers[cmd[-1]])
    monkeypatch.setattr(bs.subprocess, "run", run)
    assert [launcher.container_state(c) for c in ("aaa", "bbb", "ccc", "ddd", "eee", "fff")] == [
        "running", "exited", "missing", "unknown", "running", "exited"]
    assert all(c[:5] == ["docker", "container", "inspect", "-f", "{{.State.Status}}"] for c in calls)  # never the env


# ---------------------------------------------------------------- cut order

def test_cut_removes_not_yet_started_jobs_of_an_arm(tmp_path):
    rows = [(H, "bb64", "ep472", 1), (G, "bb8", "ep411", 1), (H, "bb64", "ep474", 1), (H, "bb8", "ep472", 1),
            (H, "bb64", "ep472", 2), (G, "bb8", "ep411", 2)]
    e = Env(tmp_path, rows, by_order({}), max_slots=1)
    e.run(stop_after=5 * 60)  # job 1 (Haiku BB-64) is running
    e.cfg.cuts = (("haiku", "bb64", 0),)
    e.run()
    assert sorted(x["order"] for x in e.events("skipped")) == [3, 5]
    assert {x["why"] for x in e.events("skipped")} == {"cut"}
    assert [x["order"] for x in e.events("launched")] == [1, 2, 4, 6]  # the started run is kept, the order too
    e.cfg.cuts = ()
    e.run()  # a cut is final: a later start without --cut does not bring the jobs back
    assert len(e.events("launched")) == 4


def test_cut_to_one_run_per_item_counts_in_file_order(tmp_path):
    rows = [(H, "open8", "ep472", 1), (H, "open8", "ep474", 2), (H, "open8", "ep472", 2), (H, "open8", "ep474", 1),
            (H, "bb8", "ep472", 1), (H, "bb8", "ep472", 2)]
    e = Env(tmp_path, rows, by_order({}), cuts=(("haiku", "open8", 1),))
    e.run()
    assert sorted(x["order"] for x in e.events("skipped")) == [3, 4]
    assert [x["order"] for x in e.events("launched")] == [1, 2, 5, 6]
    assert bs.parse_cut("haiku:bb64") == ("haiku", "bb64", 0) and bs.parse_cut("haiku:open8:1") == ("haiku", "open8", 1)
    for bad in ("opus:bb8", "haiku:bb16", "haiku", "haiku:bb8:x"):
        with pytest.raises(Exception):
            bs.parse_cut(bad)


# ---------------------------------------------------------------- preflight

SECRET = "sk-THIS-MUST-NEVER-BE-PRINTED"


class FakeHost:
    def __init__(self):
        self.environ = {"ANTHROPIC_API_KEY": SECRET, "OPENAI_API_KEY": SECRET + "2", "OPENAI_API_IP": "172.66.0.243",
                        "OPENAI_PRICES": "1.0,0.05,1.25,5.0", "CODEX_EFFORT": "max", "RL_TASK_IMAGE_SUFFIX": "-r1112"}
        self.images = {"rl-task-shifthunt-r1112": {"id": "sha256:" + "ab" * 32, "labels": {
            "shifthunt.commit": "e7" * 20, "shifthunt.dirty": "false"}},
            "rl-task-shifthunt-r1103": {"id": "sha256:" + "cd" * 32, "labels": {}}}
        self.net, self.sync, self.git, self.n = (True, "network isolation: OK"), (True, "in sync"), (True, "committed"), 0
        self.asked = []

    def image(self, name):
        return self.images.get(name)

    def net_isolation(self):
        return self.net

    def private_sync(self):
        return self.sync

    def git_committed(self, paths):
        self.asked.append([Path(p).name for p in paths])
        return self.git

    def host_containers(self):
        return self.n


def preflight_env(tmp_path, rows=None, **kw):
    e = Env(tmp_path, rows or mixed(6), **kw)
    task = e.cfg.task_dir
    (task / "scripts").mkdir(parents=True)
    (task.parents[1] / "tools").mkdir()
    for p in (task / "scripts" / "launch_rollouts.py", task / "scripts" / "collect_rollouts.py",
              task.parents[1] / "tools" / "task_runner.py"):
        p.write_text("")
    (task / "problems.txt").write_text("# comment\n" + "".join(f"{j.problem}  # x\n" for j in e.jobs) + "ep481-open\n")
    (e.cfg.results / "prereg.md").write_text("# prereg\n")
    (e.cfg.results / "PREREG_HASH").write_text(
        f"{bs.sha256_file(e.cfg.results / 'prereg.md')}  prereg.md\n{bs.sha256_file(e.runorder)}  {e.runorder.name}\n")
    e.cfg.runlog.write_text(bs.RUNLOG_HEADER + "| t | exp_e | exp_e | all | - | ok | 0.52 | 0.02 | 0.50 |\n")
    e.host = FakeHost()
    return e


def run_preflight(e):
    states = bs.replay(bs.read_events(e.cfg.ledger), e.cfg.block, len(e.jobs))
    return {c.name: c for c in bs.preflight(e.cfg, e.host, e.jobs, states)}


def test_preflight_passes_and_names_no_secret(tmp_path):
    e = preflight_env(tmp_path)
    checks = run_preflight(e)
    assert all(c.ok for c in checks.values()), [c for c in checks.values() if not c.ok]
    assert set(checks) == {"runorder", "env", "image", "problems", "launcher", "private_sync", "net_isolation",
                           "prereg", "runlog", "spend:openai", "spend:anthropic"}
    assert "ANTHROPIC_API_KEY" in checks["env"].detail
    assert SECRET not in json.dumps([list(c) for c in checks.values()])
    assert e.host.asked == [["prereg.md", "PREREG_HASH", e.runorder.name]]
    assert "0.02 + estimate for 3 remaining jobs = 4.52" in checks["spend:openai"].detail


@pytest.mark.parametrize("name, breakit, expect", [
    ("env", lambda e: e.host.environ.pop("OPENAI_API_KEY"), "not set: OPENAI_API_KEY"),
    ("env", lambda e: e.host.environ.update(ANTHROPIC_API_KEY=""), "not set: ANTHROPIC_API_KEY"),
    ("env", lambda e: e.host.environ.update(CODEX_EFFORT="xhigh"), "'xhigh'"),
    ("env", lambda e: e.host.environ.pop("CODEX_EFFORT"), "not set: CODEX_EFFORT"),
    ("env", lambda e: e.host.environ.pop("OPENAI_PRICES"), "not set: OPENAI_PRICES"),
    ("env", lambda e: e.host.environ.update(OPENAI_PRICES="1,2,3"), "not 4 numbers"),
    ("env", lambda e: e.host.environ.update(OPENAI_PRICES="a,b,c,d"), "not 4 numbers"),
    ("env", lambda e: e.host.environ.update(OPENAI_PRICES="nan,nan,nan,nan"), "not the study's 1.0,0.05,1.25,5.0"),
    ("env", lambda e: e.host.environ.update(OPENAI_PRICES="0,0,0,0"), "not the study's 1.0,0.05,1.25,5.0"),
    ("env", lambda e: e.host.environ.update(OPENAI_PRICES="1.0,0.05,1.25,50"), "not the study's 1.0,0.05,1.25,5.0"),
    ("spend:openai", lambda e: e.cfg.runlog.write_text(
        bs.RUNLOG_HEADER + "| t | x | x | x | - | ok | nan | nan | 0.50 |\n"), "not a finite number"),
    ("env", lambda e: e.host.environ.pop("OPENAI_API_IP"), "not set: OPENAI_API_IP"),
    ("image", lambda e: e.host.images.pop("rl-task-shifthunt-r1112"), "not found"),
    ("image", lambda e: e.host.images["rl-task-shifthunt-r1112"]["labels"].pop("shifthunt.commit"), "MISSING"),
    ("image", lambda e: e.host.images["rl-task-shifthunt-r1112"]["labels"].update({"shifthunt.dirty": "true"}), "dirty=true"),
    ("image", lambda e: e.host.environ.update(RL_TASK_IMAGE_SUFFIX="-r1103"), "MISSING"),   # the main-study image
    ("image", lambda e: e.host.environ.update(RL_TASK_IMAGE_SUFFIX="-r1113"), "not found"),  # a typo
    ("image", lambda e: e.host.environ.pop("RL_TASK_IMAGE_SUFFIX"), "not set"),
    ("problems", lambda e: (e.cfg.task_dir / "problems.txt").write_text("ep411-open\n"), "not in the private problems.txt"),
    ("problems", lambda e: (e.cfg.task_dir / "problems.txt").unlink(), "cannot read"),
    ("launcher", lambda e: (e.cfg.task_dir / "scripts" / "launch_rollouts.py").unlink(), "launch_rollouts.py"),
    ("private_sync", lambda e: setattr(e.host, "sync", (False, "DIFFERS scripts/collect_rollouts.py")), "DIFFERS"),
    ("net_isolation", lambda e: setattr(e.host, "net", (False, "NOT OK: no REJECT rule")), "no REJECT"),
    ("prereg", lambda e: (e.cfg.results / "PREREG_HASH").unlink(), "missing: PREREG_HASH"),
    ("prereg", lambda e: (e.cfg.results / "prereg.md").unlink(), "missing: prereg.md"),
    ("prereg", lambda e: (e.cfg.results / "prereg.md").write_text("# prereg, edited\n"), "different for: prereg.md"),
    ("prereg", lambda e: (e.cfg.results / "PREREG_HASH").write_text(
        f"{bs.sha256_file(e.cfg.results / 'prereg.md')}  prereg.md\n"), "different for: runorder_block1.csv"),
    ("prereg", lambda e: setattr(e.host, "git", (False, "prereg.md has uncommitted changes")), "uncommitted"),
    ("runlog", lambda e: e.cfg.runlog.unlink(), "missing"),
    ("spend:anthropic", lambda e: e.cfg.cap.update(anthropic=7.0), "= 8.00 USD, cap 7.00"),
    ("spend:openai", lambda e: e.cfg.runlog.write_text(
        bs.RUNLOG_HEADER + "| t | x | x | x | - | ok | 1 | 796.00 | 0.50 |\n"), "= 800.50 USD, cap 800.00"),
    ("runorder", lambda e: setattr(e.cfg, "pilot", True), "must not have it"),
])
def test_preflight_failures(tmp_path, name, breakit, expect):
    e = preflight_env(tmp_path)
    breakit(e)
    checks = run_preflight(e)
    assert not checks[name].ok and expect in checks[name].detail, checks[name]
    assert SECRET not in json.dumps([list(c) for c in checks.values()])
    others = {"runorder": {"prereg"}, "runlog": {"spend:openai", "spend:anthropic"}}.get(name, set())
    if "RL_TASK_IMAGE_SUFFIX" not in e.host.environ:
        others = {"env"}  # the unset name is reported there as well
    assert all(c.ok for n, c in checks.items() if n != name and n not in others), checks


def test_preflight_accepts_the_study_prices_however_they_are_written(tmp_path):
    e = preflight_env(tmp_path)
    e.host.environ.update(OPENAI_PRICES="1,0.050,1.25,5")
    assert run_preflight(e)["env"].ok


def test_pilots_need_no_prereg_but_do_need_the_pilot_flag(tmp_path):
    e = preflight_env(tmp_path, [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1)], name="runorder_pilots.csv", pilot=True)
    (e.cfg.results / "PREREG_HASH").unlink()
    (e.cfg.results / "prereg.md").unlink()
    checks = run_preflight(e)
    assert "prereg" not in checks and all(c.ok for c in checks.values())
    e.cfg.pilot = False
    assert not run_preflight(e)["runorder"].ok


def test_preflight_spend_projection_counts_only_jobs_not_yet_recorded(tmp_path):
    e = preflight_env(tmp_path, cap={"openai": 800.0, "anthropic": 7.9})
    assert not run_preflight(e)["spend:anthropic"].ok        # 0.50 + 3 x 2.5 = 8.00 > 7.9
    e.cfg.cap["anthropic"] = 8.0
    assert run_preflight(e)["spend:anthropic"].ok            # exactly at the cap is within it
    e.cfg.cap["anthropic"] = 130.0
    e.run()                                                  # six runs at $1: Anthropic 0.50 + 3
    c = run_preflight(e)["spend:anthropic"]
    assert c.ok and "3.50 + estimate for 0 remaining jobs = 3.50" in c.detail


def test_prereg_hashes_formats():
    h1, h2 = "a" * 64, "b" * 64
    assert bs.prereg_hashes(f"{h1}  prereg.md\n{h2} *results/blackbox_1112/runorder_block1.csv\n# note\n") == {
        "prereg.md": h1, "runorder_block1.csv": h2}
    assert bs.prereg_hashes(f"{h1}\n") == {"prereg.md": h1}
    assert bs.prereg_hashes("not a hash  prereg.md\n") == {}


# ---------------------------------------------------------------- command line

def cli_args(e, *extra):
    return ["--runorder", str(e.runorder), "--task-dir", str(e.cfg.task_dir), "--results", str(e.cfg.results),
            "--cap-openai", "800", "--cap-anthropic", "130", *extra]


def test_main_aborts_on_a_preflight_failure_and_starts_nothing(tmp_path, monkeypatch, capsys):
    e = preflight_env(tmp_path)
    e.host.net = (False, "NOT OK: no REJECT rule")
    monkeypatch.setattr(bs, "Host", lambda cfg: e.host)
    built = []
    monkeypatch.setattr(bs, "RealLauncher", lambda cfg: built.append(cfg))
    assert bs.main(cli_args(e)) == 1
    out = capsys.readouterr()
    assert "FAIL net_isolation" in out.out and "preflight failed (net_isolation); nothing was started" in out.err
    assert not built and not e.cfg.ledger.exists() and SECRET not in out.out + out.err


def test_main_dry_run_runs_the_whole_block_and_writes_no_real_state(tmp_path, monkeypatch, capsys):
    e = preflight_env(tmp_path, mixed(12))
    e.host.sync = (False, "DIFFERS scripts/collect_rollouts.py")  # a dry run reports it and goes on
    monkeypatch.setattr(bs, "Host", lambda cfg: e.host)
    monkeypatch.setattr(bs, "RealLauncher", lambda cfg: pytest.fail("a dry run must not build the real launcher"))
    before = e.cfg.runlog.read_text()
    dry = tmp_path / "dry"
    assert bs.main(cli_args(e, "--dry-run", "--dry-run-dir", str(dry), "--dry-run-infra", "0.2", "--dry-run-seed", "3")) == 0
    out = capsys.readouterr().out
    assert "a real start would abort on: private_sync" in out and "DRY RUN" in out
    assert e.cfg.runlog.read_text() == before and not e.cfg.ledger.exists()
    assert not (e.cfg.task_dir / "results").exists()
    evs = bs.read_events(dry / "ledger.jsonl")
    assert all(x["dry_run"] for x in evs) and sum(x["event"] == "finished" for x in evs) == 12
    assert bs.runlog_cums((dry / "RUNLOG.md").read_text())[0] > 0.02  # continues from the copied RUNLOG
    assert all("[dry run]" in line for line in (dry / "RUNLOG.md").read_text().splitlines()[5:])
    assert bs.main(cli_args(e, "--dry-run", "--dry-run-dir", str(dry), "--summary")) == 0
    assert "recorded 12" in capsys.readouterr().out
    with pytest.raises(SystemExit):  # the dry run's state may not be the real results directory
        bs.main(cli_args(e, "--dry-run", "--dry-run-dir", str(e.cfg.results)))
    with pytest.raises(SystemExit):  # nor a directory that holds an earlier dry run
        bs.main(cli_args(e, "--dry-run", "--dry-run-dir", str(dry)))
    assert "already holds a dry run" in capsys.readouterr().err


def test_dry_run_preflight_reads_the_real_ledger_and_runlog_every_time(tmp_path, monkeypatch, capsys):
    e = preflight_env(tmp_path, mixed(12))
    monkeypatch.setattr(bs, "Host", lambda cfg: e.host)
    monkeypatch.setattr(bs, "RealLauncher", lambda cfg: pytest.fail("a dry run must not build the real launcher"))
    args = cli_args(e)
    args[args.index("--cap-openai") + 1], args[args.index("--cap-anthropic") + 1] = "9", "15"

    n = [0]

    def dry_run():
        n[0] += 1  # a new directory each time; the caps of this test stop the simulated block (exit 3)
        assert bs.main(args + ["--dry-run", "--dry-run-dir", str(tmp_path / f"dry{n[0]}")]) == 3
        return capsys.readouterr().out
    want = ("FAIL spend:openai: cum 0.02 + estimate for 6 remaining jobs = 9.02 USD, cap 9.00",
            "FAIL spend:anthropic: cum 0.50 + estimate for 6 remaining jobs = 15.50 USD, cap 15.00",
            f"ok   runlog: {e.cfg.runlog} found")
    first, second = dry_run(), dry_run()
    for line in want:  # the second dry run says the same: nothing simulated is read back
        assert line in first and line in second
    assert f"state read: {e.cfg.ledger}, {e.cfg.runlog}" in first
    # the real state moves: two real GPT jobs are recorded, the real RUNLOG has their cost
    with open(e.cfg.ledger, "a") as f:
        for o in (1, 3):
            f.write(json.dumps({"block": "block1", "order": o, "event": "finished", "status": "ok", "ts": 1.0}) + "\n")
    with open(e.cfg.runlog, "a") as f:
        f.write("| 2026-11-12T10:00Z | abc | bb8 | gpt | ep411 | ok | 1.00 | 2.02 | 0.50 |\n")
    third = dry_run()
    assert "ok   spend:openai: cum 2.02 + estimate for 4 remaining jobs = 8.02 USD, cap 9.00" in third
    e.cfg.runlog.unlink()
    assert f"FAIL runlog: {e.cfg.runlog} missing" in dry_run()


def test_dry_run_of_the_committed_block_1_order(tmp_path):
    runorder = ROOT / "results" / "blackbox_1112" / "runorder_block1.csv"
    cfg = bs.Config(runorder, "r1112", tmp_path / "task", tmp_path / "results", rollouts=tmp_path / "rollouts", dry_run=True)
    clock = bs.FakeClock()
    launcher = bs.FakeLauncher(cfg, clock, bs.default_sim(seed=1, infra_rate=0.05))
    summary = bs.Scheduler(cfg, bs.read_runorder(runorder), launcher, clock, say=lambda s: None).run()
    assert summary["recorded"] == 108 and summary["peak_running"] == 3 and launcher.peak == 3
    assert 9 < summary["hours"] < 17  # the plan's 12-13 h at three in parallel
    evs = bs.read_events(cfg.ledger)
    first = [x["order"] for x in evs if x["event"] == "launched" and x["attempt"] == 1]
    assert first == list(range(1, 109))
    ts = [x["ts"] for x in evs if x["event"] == "launched"]
    assert all(b - a >= 90 for a, b in zip(ts, ts[1:]))
    assert summary["spend"]["openai"] < 80 and summary["spend"]["anthropic"] < 60
    assert "block1" in bs.format_summary(summary, "block1") and "recorded 108" in bs.format_summary(summary)


# ---------------------------------------------------------------- the real process path, with a stand-in launcher

STAND_IN = r'''"""Stand-in for the private scripts/launch_rollouts.py: same arguments and events, no docker, no API."""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("problems", nargs="*")
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--model")
ap.add_argument("--engine", default="claude")
for opt in ("--max-concurrent", "--stagger", "--max-host-containers", "--timeout", "--mem-limit", "--cpu-limit",
            "--cap-usd", "--est-usd"):
    ap.add_argument(opt)
a = ap.parse_args()
problem = a.problems[0]
a.out.mkdir(parents=True, exist_ok=True)

def log(**ev):
    print(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **ev}), flush=True)

log(event="start", problems=a.problems)
log(event="launched", problem=problem, resources="stand-in isolated=True", running=1)
time.sleep(0.4)
if problem == "ep472-blackbox":
    print("Traceback (most recent call last): stand-in runner failure")  # not JSON: must be skipped
    log(event="finished", problem=problem, runner_exit=1, cid=None, usd=None)
    sys.exit(0)
cid = hashlib.sha256(f"{problem}{os.getpid()}".encode()).hexdigest()[:12]
d = a.out / cid
d.mkdir()
(d / "grade.json").write_text("{}")
(d / "submission.json").write_text("{}")
with open(a.out / "summary.jsonl", "a") as f:
    f.write(json.dumps({"cid": cid, "usd": 0.25, "usd_source": "stand-in", "harness_status": "ok", "submitted": True,
                        "model": a.model}) + "\n")
log(event="finished", problem=problem, runner_exit=0, cid=cid, usd=0.25)
log(event="done")
'''


def test_real_launcher_process_path_with_a_stand_in_script(tmp_path):
    """RealLauncher itself (Popen in its own session, child log, exit code, pid), pointed at a task directory
    whose scripts/launch_rollouts.py is the stand-in above. Nothing of the real harness is started."""
    rows = [(G, "bb8", "ep411", 1), (H, "bb8", "ep472", 1), (G, "open8", "ep411", 1)]
    task = tmp_path / "sub" / "tasks" / "shifthunt"
    (task / "scripts").mkdir(parents=True)
    (task / "scripts" / "launch_rollouts.py").write_text(STAND_IN)
    runorder = write_runorder(tmp_path / "runorder_block1.csv", rows)
    cfg = bs.Config(runorder, "r1112", task, tmp_path / "results", poll=0.1, gap=0.2)
    assert cfg.rollouts == task / "results" / "rollouts"
    launcher = bs.RealLauncher(cfg)
    said = []
    sched = bs.Scheduler(cfg, bs.read_runorder(runorder), launcher, say=said.append)
    summary = sched.run()
    evs = bs.read_events(cfg.ledger)
    launched = [e for e in evs if e["event"] == "launched"]
    assert [(e["order"], e["attempt"]) for e in launched] == [(1, 1), (2, 1), (3, 1), (2, 2), (2, 3)]
    assert summary["status"] == {"ok": 2} and summary["infra"] == {"no_container": 3} and summary["gave_up"] == [2]
    assert summary["spend"] == {"openai": 0.5, "anthropic": 0.0}
    for e in launched:
        log = cfg.rollouts / e["run"] / e["child_log"]
        assert log.exists() and isinstance(e["pid"], int) and not launcher.alive(e)  # ended; pid no longer a launcher
    fin = [e for e in evs if e["event"] == "finished"]
    assert all((cfg.rollouts / e["run"] / e["cid"] / "submission.json").exists() for e in fin)
    assert [e["flags"] for e in evs if e["event"] == "infra"][0] == ["runner_exit_1"]
    ts = [e["ts"] for e in launched]
    assert all(b - a >= 0.2 for a, b in zip(ts, ts[1:]))


def test_real_launcher_finds_its_child_again_by_the_child_log_alone(tmp_path):
    """A scheduler killed between Popen and its `launched` event has only the `launching` event (no pid): the
    launcher process is found by its stdout, which is the child log."""
    import time
    task = tmp_path / "sub" / "tasks" / "shifthunt"
    (task / "scripts").mkdir(parents=True)
    (task / "scripts" / "launch_rollouts.py").write_text(STAND_IN.replace("time.sleep(0.4)", "time.sleep(3)"))
    runorder = write_runorder(tmp_path / "runorder_block1.csv", [(G, "bb8", "ep411", 1)])
    cfg = bs.Config(runorder, "r1112", task, tmp_path / "results")
    job, launcher = bs.read_runorder(runorder)[0], bs.RealLauncher(cfg)
    run_dir = cfg.rollouts / "r1112_gpt_bb8"
    run_dir.mkdir(parents=True)
    intent = {"event": "launching", "run": "r1112_gpt_bb8", "child_log": "launch_sched_block1_o001_a1.log",
              "problem": job.problem}
    assert launcher.find_pid(intent) is None and not launcher.alive(intent)   # nothing started yet
    p = launcher.start(job, 1, "r1112_gpt_bb8", run_dir / intent["child_log"])
    try:
        assert launcher.find_pid(intent) == p.pid and launcher.alive(intent)
        assert launcher.find_pid({**intent, "child_log": "launch_sched_block1_o001_a2.log"}) is None
        assert launcher.find_pid({**intent, "problem": "ep472-blackbox"}) is None
        assert launcher.alive({**intent, "pid": p.pid}) and not launcher.alive({**intent, "pid": p.pid + 1})
    finally:
        p.wait(timeout=30)
    deadline = time.time() + 5
    while launcher.alive(intent) and time.time() < deadline:
        time.sleep(0.05)
    assert not launcher.alive(intent)


RUNNER_DIES = '''if problem == "ep472-blackbox":
    (a.out / f"launch_{problem}_{int(time.time())}.log").write_text(
        "Waiting on container to run; watch progress with `./tools/watch-run.sh 0123456789ab`\\n")'''


def test_real_launcher_path_when_the_runner_died_after_starting_a_container(tmp_path):
    """The real process path of the same case: the stand-in launcher reports cid null / runner_exit 1 and its
    runner log has only the "watch-run.sh <id>" line. docker is replaced by two functions of the launcher."""
    stand_in = STAND_IN.replace('if problem == "ep472-blackbox":', RUNNER_DIES)
    assert stand_in != STAND_IN
    task = tmp_path / "sub" / "tasks" / "shifthunt"
    (task / "scripts").mkdir(parents=True)
    (task / "scripts" / "launch_rollouts.py").write_text(stand_in)
    runorder = write_runorder(tmp_path / "runorder_block1.csv", [(H, "bb8", "ep472", 1), (G, "open8", "ep411", 1)])
    cfg = bs.Config(runorder, "r1112", task, tmp_path / "results", poll=0.1, gap=0.2, max_slots=1)
    launcher, states, asked = bs.RealLauncher(cfg), ["running", "running", "running", "exited"], []

    def container_state(cid):
        asked.append(cid)
        return states.pop(0) if len(states) > 1 else states[0]

    def recollect(cid, run_dir):  # the collector's part: the container held an accepted submission
        d = Path(run_dir) / cid
        d.mkdir(exist_ok=True)
        (d / "grade.json").write_text("{}")
        (d / "submission.json").write_text("{}")
        with open(Path(run_dir) / "summary.jsonl", "a") as f:
            f.write(json.dumps({"cid": cid, "usd": 1.1, "usd_source": "stand-in", "harness_status": "ok"}) + "\n")
    launcher.container_state, launcher.recollect = container_state, recollect
    summary = bs.Scheduler(cfg, bs.read_runorder(runorder), launcher, say=lambda s: None).run()
    evs = bs.read_events(cfg.ledger)
    fin = {e["order"]: e for e in evs if e["event"] == "finished"}
    assert (fin[1]["cid"], fin[1]["status"], fin[1]["usd"], fin[1]["cid_source"]) == ("0123456789ab", "ok", 1.1, "runner_start")
    assert fin[1]["flags"] == ["runner_exit_1", "runner_died"] and set(asked) == {"0123456789ab"} and len(asked) >= 4
    assert not [e for e in evs if e["event"] in ("infra", "requeued")] and summary["status"] == {"ok": 2}
    launched = [e for e in evs if e["event"] == "launched"]
    assert [(e["order"], e["attempt"]) for e in launched] == [(1, 1), (2, 1)]
    assert launched[1]["ts"] >= fin[1]["ts"]  # the job kept the only slot while its container ran
    assert summary["spend"] == {"openai": 0.25, "anthropic": 1.1}


def test_real_launcher_alive_needs_a_launcher_process_of_that_problem(tmp_path):
    import os
    e = Env(tmp_path, mixed(1))
    launcher = bs.RealLauncher(e.cfg)
    assert not launcher.alive({"pid": os.getpid(), "problem": "ep411-open"})  # this process is not a launcher
    assert not launcher.alive({"pid": 2 ** 22 + 12345, "problem": "ep411-open"}) and not launcher.alive({})
