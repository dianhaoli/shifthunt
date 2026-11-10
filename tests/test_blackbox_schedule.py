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

    def __init__(self, tmp_path, rows, script=None, name="runorder_block1.csv", pilot=False, subdir=None,
                 results="results", **cfg):
        self.tmp = tmp_path
        (tmp_path / (subdir or "")).mkdir(parents=True, exist_ok=True)
        self.runorder = write_runorder(tmp_path / (subdir or "") / name, rows)
        self.jobs = bs.read_runorder(self.runorder)
        self.cfg = bs.Config(self.runorder, "r1112", tmp_path / "sub" / "tasks" / "shifthunt", tmp_path / results,
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
    # Claude Code: the main study's rule, whatever the row's agent_error says
    for ae in (None, AE_NONE, AE_API, AE_CONTEXT, AE_RECOVERED):
        out = bs.classify(**kw, engine="claude", agent_error=ae)
        assert (out.status, out.infra, out.flags) == (status, infra, flags)


# agent_error dicts as scripts/collect_rollouts.py codex_agent_error writes them
def ae(terminal, kind=None, type_=None, message=None, n=1):
    return {"terminal": terminal, "kind": kind, "type": type_, "message": message, "n_error_events": n}


AE_NONE = ae(False, n=0)
AE_API = ae(True, "api", "turn.failed", "Quota exceeded. Check your plan and billing details.", 2)
AE_TRAILING = ae(True, "api", "error", "stream disconnected before completion", 3)
AE_CONTEXT = ae(True, "context", "turn.failed", "Codex ran out of room in the model's context window.", 2)
AE_REFUSAL = ae(True, "refusal", "turn.failed", "your prompt was flagged as potentially violating our usage policy", 2)
AE_RECOVERED = ae(False, None, None, "Reconnecting... 2/5", 2)
CODEX = dict(cid="c", collected=True, engine="codex", harness_status="api_error")
LOOK = "manual_look"


@pytest.mark.parametrize("kw, status, infra, flags", [
    # an API error ended the agent: turn.failed, or the stream ends with an error event; message is neither
    (dict(CODEX, has_grade=True, agent_error=AE_API), "infra:api_error", True, []),
    (dict(CODEX, has_grade=True, agent_error=AE_TRAILING), "infra:api_error", True, ["codex_trailing_error"]),
    (dict(CODEX, has_grade=False, agent_error=AE_API), "infra:api_error", True, []),
    # the same status when the hard stop ended the run, with a trace: the stream ends where the killed CLI was
    (dict(CODEX, has_grade=True, agent_error=AE_API, timeout=True), "infra:api_error", True,
     ["api_error_at_timeout", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=AE_TRAILING, timeout=True), "infra:api_error", True,
     ["codex_trailing_error", "api_error_at_timeout", LOOK]),
    (dict(CODEX, has_grade=False, agent_error=AE_TRAILING, timeout=True, runner_exit=1), "infra:api_error", True,
     ["runner_exit_1", "codex_trailing_error", "api_error_at_timeout", LOOK]),
    # the rule does not read harness_status for Codex
    (dict(CODEX, has_grade=True, agent_error=AE_API, harness_status="ok"), "infra:api_error", True, []),
    # the agent's own failures: counted fails
    (dict(CODEX, has_grade=True, agent_error=AE_CONTEXT), "fail:no_submission", False, ["agent_error_context", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=AE_REFUSAL), "fail:no_submission", False, ["agent_error_refusal", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=AE_CONTEXT, timeout=True), "fail:timeout", False,
     ["agent_error_context", LOOK]),
    # an error event the CLI recovered from: the remaining rules decide
    (dict(CODEX, has_grade=True, agent_error=AE_RECOVERED), "fail:no_submission", False, ["codex_error_recovered", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=AE_RECOVERED, timeout=True), "fail:timeout", False,
     ["codex_error_recovered", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=AE_RECOVERED, daemon_died=True), "fail:no_submission", False,
     ["codex_error_recovered", LOOK, "daemon_died"]),
    (dict(CODEX, has_grade=False, agent_error=AE_RECOVERED), "infra:no_grade", True, ["codex_error_recovered", LOOK]),
    (dict(CODEX, has_grade=False, agent_error=AE_CONTEXT), "infra:no_grade", True, ["agent_error_context", LOOK]),
    (dict(CODEX, has_grade=False, agent_error=AE_REFUSAL, interrupted=True, cut_off=True), "infra:interrupted", True,
     ["agent_error_refusal", LOOK, "container_cut_off"]),
    # harness_status says api_error but the stream cannot be read (no row key, no file), or the dict is malformed
    (dict(CODEX, has_grade=True, agent_error=None), "fail:no_submission", False, ["agent_error_unknown", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=ae(True, "something")), "fail:no_submission", False,
     ["agent_error_unknown", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=ae(False, n=0)), "fail:no_submission", False,
     ["codex_error_recovered", LOOK]),                      # harness_status saw an error event the dict does not count
    # only the JSON true the collector writes is terminal: another truthy value never makes a run a re-run
    (dict(CODEX, has_grade=True, agent_error=ae(1, "api", "turn.failed", "x", 2)), "fail:no_submission", False,
     ["codex_error_recovered", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=ae("true", "api", "turn.failed", "x", 2)), "fail:no_submission", False,
     ["codex_error_recovered", LOOK]),
    (dict(CODEX, has_grade=True, agent_error=ae(None, "api", "isApiErrorMessage", "overloaded_error", 1),
          harness_status="ok"), "fail:no_submission", False, ["codex_error_recovered", LOOK]),
    # no error event at all: as before
    (dict(CODEX, has_grade=True, agent_error=AE_NONE, harness_status="ok"), "fail:no_submission", False, []),
    (dict(CODEX, has_grade=True, agent_error=AE_NONE, harness_status="ok", timeout=True), "fail:timeout", False, []),
    (dict(CODEX, has_grade=False, agent_error=AE_NONE, harness_status="no_grade"), "infra:no_grade", True, []),
    (dict(CODEX, has_grade=True, agent_error=None, harness_status="ok"), "fail:no_submission", False, []),
    (dict(CODEX, has_grade=True, agent_error=AE_NONE, harness_status="no_agent_activity"), "fail:no_submission", False,
     ["no_agent_activity", LOOK]),
    # an accepted submission: counted on it, never re-run, whatever the stream says
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_API), "ok", False, ["api_error_after_submit"]),
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_TRAILING, timeout=True), "ok", False,
     ["api_error_after_submit", "timeout_after_submit"]),
    (dict(CODEX, submitted=True, has_grade=False, agent_error=AE_API), "needs_regrade", False,
     ["api_error_after_submit", "needs_regrade"]),
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_RECOVERED), "ok", False, ["codex_error_recovered"]),
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_CONTEXT), "ok", False, ["agent_error_context"]),
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_REFUSAL), "ok", False, ["agent_error_refusal"]),
    (dict(CODEX, submitted=True, has_grade=True, agent_error=AE_NONE, harness_status="ok"), "ok", False, []),
])
def test_classify_codex_api_error_rule(kw, status, infra, flags):
    out = bs.classify(**kw)
    assert (out.status, out.infra, out.flags) == (status, infra, flags)


def test_codex_error_class():
    assert bs.codex_error_class(AE_API) == "api" and bs.codex_error_class(AE_TRAILING, "api_error") == "api"
    assert bs.codex_error_class(AE_CONTEXT) == "context" and bs.codex_error_class(AE_REFUSAL) == "refusal"
    assert bs.codex_error_class(AE_RECOVERED) == "recovered" and bs.codex_error_class(AE_NONE) is None
    assert bs.codex_error_class(None) is None and bs.codex_error_class(None, "api_error") == "unknown"
    assert bs.codex_error_class("x", "api_error") == "unknown" and bs.codex_error_class({}, "ok") is None
    for odd in (1, "true", None, 0, "false", [True]):                      # not the JSON true: never "api"
        assert bs.codex_error_class(ae(odd, "api", "turn.failed", "x", 2)) == "recovered", odd
        assert bs.codex_error_class(ae(odd, "api", "turn.failed", "x", 0), "ok") is None, odd


def test_agent_error_of_takes_the_rows_dict_only_if_it_is_one(tmp_path):
    """A row whose agent_error is not a dict with `terminal` (a string, a list, null, another shape) is
    completed from the run directory, like a row without the key."""
    d = tmp_path / "run" / "0123456789ab"
    d.mkdir(parents=True)
    (d / "codex_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in STREAMS["failed_context"]))
    want = bs.CR.codex_agent_error(STREAMS["failed_context"])
    for bad in ("api", ["terminal"], None, 3, True, {}, {"kind": "api"}):
        assert bs.agent_error_of(tmp_path / "run", "0123456789ab", {"agent_error": bad}, "codex") == (want, "events_file")
    assert bs.agent_error_of(tmp_path / "run", "0123456789ab", {"agent_error": AE_API}, "codex") == (AE_API, "row")
    assert bs.agent_error_of(tmp_path / "run", "nothing", {"agent_error": "api"}, "codex") == (None, None)
    facts = bs.run_facts(tmp_path / "run", "0123456789ab", {"agent_error": "api", "harness_status": "api_error"}, "codex")
    assert facts["agent_error"] == want
    assert set(bs.CODEX_ERROR_FLAGS) == {"recovered", "context", "refusal", "unknown"}


def test_a_run_with_an_accepted_submission_is_never_an_infrastructure_failure():
    for hs in (None, "ok", "api_error", "no_agent_activity", "no_grade", "no_grade_with_submission", "timeout"):
        for grade in (True, False):
            for timeout in (True, False):
                for died in (True, False):
                    for engine in (None, "claude", "codex"):
                        for err in (None, AE_NONE, AE_API, AE_TRAILING, AE_CONTEXT, AE_REFUSAL, AE_RECOVERED):
                            out = bs.classify("c", True, submitted=True, has_grade=grade, timeout=timeout,
                                              harness_status=hs, daemon_died=died, runner_exit=1, engine=engine,
                                              agent_error=err)
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


# ---------------------------------------------------------------- "an API error ended the agent" (prereg section 7.3)

EV_START = [{"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"}]
EV_ITEM = {"type": "item.completed", "item": {"type": "command_execution", "command": "ls", "exit_code": 0}}
EV_DONE = {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 1}}
EV_RETRY = {"type": "error", "message": "Reconnecting... 2/5 (stream disconnected before completion)"}
MSG_QUOTA = "Quota exceeded. Check your plan and billing details."
MSG_CONTEXT = "Codex ran out of room in the model's context window. Start a new thread."
MSG_FLAGGED = "Invalid prompt: your prompt was flagged as potentially violating our usage policy."
MSG_TPM = ("Rate limit reached for gpt-6.1-terra in organization org-Ab12Cd34Ef56Gh78 on tokens per min (TPM): "
           "Limit 2000000, Used 1998123, Requested 5210. Please try again in 99ms.")


def turn_failed(message):
    return EV_START + [EV_ITEM, {"type": "error", "message": message}, {"type": "turn.failed", "error": {"message": message}}]


STREAMS = {  # name -> the events of codex_events.jsonl
    "failed_api": turn_failed(MSG_QUOTA),
    "failed_tpm": turn_failed(MSG_TPM),
    "failed_context": turn_failed(MSG_CONTEXT),
    "failed_refusal": turn_failed(MSG_FLAGGED),
    "trailing_error": EV_START + [EV_ITEM, EV_RETRY, EV_ITEM, {"type": "error", "message": MSG_QUOTA}],
    "recovered": EV_START + [EV_ITEM, EV_RETRY, EV_ITEM, EV_DONE],
    "recovered_no_end": EV_START + [EV_ITEM, EV_RETRY, EV_ITEM],  # went on after the error, then the hard stop
    "retry_at_stop": EV_START + [EV_ITEM, EV_RETRY],              # the hard stop came while the CLI was reconnecting
}


def stream(name, outcome="api_error", old_row=False, **kw):
    """A fake Codex run whose summary row is what the collector writes for that event stream. harness_status is
    the main study's: api_error for every one of these streams (each has an error event). old_row: the row has
    no agent_error key (an older collector) and codex_events.jsonl is in the run directory."""
    text = "".join(json.dumps(e) + "\n" for e in STREAMS[name])
    spec = {"outcome": outcome, "minutes": 5, "usd": 0.4, "files": {"codex_events.jsonl": text}, **kw}
    if old_row:
        return {**spec, "old_row": True}
    return {**spec, "row": {**kw.get("row", {}), "agent_error": bs.CR.codex_agent_error(STREAMS[name])}}


GPT_ROWS = [(G, "bb8", f"ep{411 + 2 * (i % 3)}", i // 3 + 1) for i in range(9)]


@pytest.mark.parametrize("old_row", [False, True])
def test_codex_api_error_rule_end_to_end(tmp_path, old_row):
    """Every branch of the pre-registered Codex rule through the scheduler, from the collector's own
    classification of the event stream; with old_row from codex_events.jsonl in the run directory."""
    ok_after = [{"outcome": "ok"}]
    spec = {1: [stream("failed_api", old_row=old_row)] + ok_after,
            2: stream("failed_context", old_row=old_row),
            3: stream("failed_refusal", old_row=old_row),
            4: [stream("trailing_error", old_row=old_row)] + ok_after,
            5: stream("recovered", old_row=old_row),
            6: stream("recovered_no_end", old_row=old_row, row={"timeout": True}),
            7: stream("failed_api", "api_error_submitted", old_row=old_row),
            8: [stream("failed_tpm", old_row=old_row)] + ok_after,
            9: stream("recovered", "api_error_submitted", old_row=old_row)}
    e = Env(tmp_path, GPT_ROWS, by_order(spec), max_slots=1, gap=0)
    e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    infra = {x["order"]: x for x in e.events("infra")}
    assert sorted(infra) == [1, 4, 8] and all(x["reason"] == "api_error" for x in infra.values())
    assert [x["order"] for x in e.events("requeued")] == [1, 4, 8]
    assert {o: x["status"] for o, x in fin.items()} == {
        1: "ok", 2: "fail:no_submission", 3: "fail:no_submission", 4: "ok", 5: "fail:no_submission",
        6: "fail:timeout", 7: "ok", 8: "ok", 9: "ok"}
    assert fin[2]["flags"] == ["agent_error_context", "manual_look"]
    assert fin[3]["flags"] == ["agent_error_refusal", "manual_look"]
    assert fin[5]["flags"] == fin[6]["flags"] == ["codex_error_recovered", "manual_look"]
    assert fin[7]["flags"] == ["api_error_after_submit"] and fin[9]["flags"] == ["codex_error_recovered"]
    # a counted fail and a run with a submission are never run again; each infra job exactly once more
    assert sorted((x["order"], x["attempt"]) for x in e.events("launched")) == sorted(
        [(o, 1) for o in range(1, 10)] + [(1, 2), (4, 2), (8, 2)])
    assert e.summary["recorded"] == 9 and e.summary["infra"] == {"api_error": 3}
    # the failure message: ledger event and the batch's list of excluded runs
    assert infra[1]["message"] == MSG_QUOTA and infra[4]["message"] == MSG_QUOTA
    assert infra[8]["message"] == MSG_TPM.replace("org-Ab12Cd34Ef56Gh78", "org-[removed]")
    assert infra[1]["agent_error"] == {"terminal": True, "kind": "api", "type": "turn.failed", "n_error_events": 2,
                                       "source": "events_file" if old_row else "row"}
    assert infra[4]["agent_error"]["type"] == "error"
    assert infra[1]["flags"] == [] and infra[4]["flags"] == ["codex_trailing_error"] and infra[8]["flags"] == []
    assert "excluded: order 4 attempt 1 cid " + infra[4]["cid"] + " api_error (codex_trailing_error): " + MSG_QUOTA \
        in bs.format_summary(e.summary)
    assert fin[2]["message"] == MSG_CONTEXT and fin[3]["message"] == MSG_FLAGGED
    assert fin[5]["message"] == EV_RETRY["message"] and fin[5]["agent_error"]["terminal"] is False
    assert "message" not in fin[1] and "agent_error" not in fin[1]       # the re-run had no error event
    listed = [json.loads(l) for l in (e.cfg.rollouts / "r1112_gpt_bb8" / "infra_failures.jsonl").read_text().splitlines()]
    assert [sorted(r) for r in listed] == [["cid", "message", "reason"]] * 3
    assert {r["cid"]: r["message"] for r in listed} == {infra[o]["cid"]: infra[o]["message"] for o in (1, 4, 8)}
    assert all(r["reason"].startswith("api_error: no accepted submission") for r in listed)
    assert "Ab12Cd34" not in e.cfg.ledger.read_text() + json.dumps(listed) + e.cfg.runlog.read_text() + "".join(e.said)
    # every infra:api_error paused OpenAI for 15 minutes; the context / refusal / recovered runs did not
    launched = {(x["order"], x["attempt"]): x["ts"] for x in e.events("launched")}
    assert all(x["pause_until"] == bs.iso(x["ts"] + bs.PAUSE_S) for x in infra.values())
    assert launched[(2, 1)] - infra[1]["ts"] >= bs.PAUSE_S and launched[(5, 1)] - infra[4]["ts"] >= bs.PAUSE_S
    assert launched[(3, 1)] - fin[2]["ts"] < 60 and launched[(4, 1)] - fin[3]["ts"] < 60
    assert launched[(6, 1)] - fin[5]["ts"] < 60 and launched[(7, 1)] - fin[6]["ts"] < 60
    assert "excluded: order 1 attempt 1" in bs.format_summary(e.summary) and MSG_QUOTA in bs.format_summary(e.summary)
    # the scorer excludes the three listed runs and nothing else
    sn = _load("score_naming")
    assert sn.infra_cids(e.cfg.rollouts / "r1112_gpt_bb8") == {x["cid"] for x in infra.values()}


@pytest.mark.parametrize("old_row", [False, True])
def test_codex_stream_that_ends_in_an_error_event_at_the_hard_stop_is_rerun_and_flagged(tmp_path, old_row):
    """The pre-registered rule read literally: the stream ends with an `error` event, so the run is an
    infrastructure failure and is re-run, also when the 5400 s stop cut the CLI off in a reconnect. The event
    says so (timeout, trailing error, manual_look), and --summary prints it."""
    spec = {1: [stream("retry_at_stop", old_row=old_row, row={"timeout": True}), {"outcome": "ok"}]}
    e = Env(tmp_path, GPT_ROWS[:1], by_order(spec), gap=0)
    e.run()
    infra = e.events("infra")
    assert len(infra) == 1 and infra[0]["reason"] == "api_error" and infra[0]["message"] == EV_RETRY["message"]
    assert infra[0]["flags"] == ["codex_trailing_error", "api_error_at_timeout", "manual_look"]
    assert [x["attempt"] for x in e.events("launched")] == [1, 2] and e.events("finished")[0]["status"] == "ok"
    assert "api_error (codex_trailing_error, api_error_at_timeout, manual_look): " + EV_RETRY["message"] \
        in bs.format_summary(e.summary)
    assert "(codex_trailing_error, api_error_at_timeout, manual_look)" in e.cfg.runlog.read_text()


def test_three_codex_api_errors_in_a_row_stop_openai_but_agent_failures_do_not(tmp_path):
    bad = [stream("failed_api")] * 3
    e = Env(tmp_path, GPT_ROWS[:5] + [(H, "bb8", "ep472", 1)], by_order({1: bad, 2: bad, 3: bad}), gap=0)
    e.run()
    stop = e.events("infra_stop")
    assert len(stop) == 1 and stop[0]["provider"] == "openai" and stop[0]["streak"] == 3
    assert sorted(x["order"] for x in e.events("finished")) == [6]       # Haiku keeps going
    assert e.events("end")[0]["stopped"] == {"openai": "infra_stop"}
    # context-window failures and recovered errors are counted fails: no streak, no stop, no pause, no re-run
    own = [stream("failed_context"), stream("failed_refusal"), stream("recovered"), stream("failed_context")]
    f = Env(tmp_path / "b", GPT_ROWS[:5], by_order(dict(enumerate(own, 1))), gap=0)
    f.run()
    assert not f.events("infra", "infra_stop", "requeued") and f.summary["recorded"] == 5
    assert len(f.events("launched")) == 5 and not any("paused" in t for t in f.said)
    assert not list(f.cfg.rollouts.glob("*/infra_failures.jsonl"))


def test_codex_harness_api_error_that_cannot_be_read_is_a_flagged_fail_not_a_rerun(tmp_path):
    """An old row (no agent_error) and no codex_events.jsonl in the run directory: nothing says an API error
    ended the agent, so the job is not re-run by itself; a person looks."""
    e = Env(tmp_path, GPT_ROWS[:2], by_order({1: {"outcome": "api_error", "old_row": True}}))
    e.run()
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[1]["status"] == "fail:no_submission" and fin[1]["flags"] == ["agent_error_unknown", "manual_look"]
    assert not e.events("infra") and len(e.events("launched")) == 2


def test_claude_api_error_rule_is_the_main_studys_and_its_message_is_the_matched_string(tmp_path):
    line = json.dumps({"type": "assistant", "isApiErrorMessage": True, "message": {"content": [
        {"type": "text", "text": "API Error: 529 overloaded_error"}]}}, separators=(",", ":")) + "\n"
    rows = [(H, "bb8", "ep472", 1), (H, "bb8", "ep474", 1), (H, "open8", "ep472", 1), (H, "bb8", "ep476", 1)]
    spec = {1: [{"outcome": "api_error", "minutes": 2, "row": {"agent_error": {
                "terminal": None, "kind": "api", "type": "isApiErrorMessage", "message": "rate_limit_error",
                "n_error_events": 3}}}, {"outcome": "ok"}],
            # an older collector's row: the message is read from the transcripts with the collector's function
            2: [{"outcome": "api_error", "minutes": 2, "old_row": True, "files": {"transcript_a.jsonl": line}},
                {"outcome": "ok"}],
            # harness_status decides for Claude Code, not agent_error: a Codex-shaped "recovered" dict changes nothing
            4: [{"outcome": "api_error", "minutes": 2, "row": {"agent_error": AE_RECOVERED}}, {"outcome": "ok"}],
            3: {"outcome": "api_error_submitted"}}                       # a success in between: no infra_stop
    e = Env(tmp_path, rows, by_order(spec), max_slots=1, gap=0)
    e.run()
    infra = {x["order"]: x for x in e.events("infra")}
    assert sorted(infra) == [1, 2, 4] and all(x["reason"] == "api_error" for x in infra.values())
    assert all(x["pause_until"] == bs.iso(x["ts"] + bs.PAUSE_S) for x in infra.values())
    assert infra[1]["message"] == "rate_limit_error" and infra[2]["message"] == "overloaded_error"
    assert infra[2]["agent_error"]["source"] == "transcripts"
    fin = {x["order"]: x for x in e.events("finished")}
    assert fin[3]["status"] == "ok" and fin[3]["flags"] == ["api_error_after_submit"]
    assert fin[3]["message"] == "overloaded_error"                       # the fake collector's default string
    assert e.summary["recorded"] == 4 and len(e.events("launched")) == 7
    listed = [json.loads(l) for l in (e.cfg.rollouts / "r1112_haiku_bb8" / "infra_failures.jsonl").read_text().splitlines()]
    assert [r["message"] for r in listed] == ["rate_limit_error", "overloaded_error", "Reconnecting... 2/5"]


def test_no_secret_from_a_failure_message_reaches_the_ledger_or_the_lists(tmp_path):
    """The scheduler scrubs the message again, whatever wrote the row (here: a row that was not scrubbed)."""
    raw = (f"unexpected status 401: Incorrect API key provided: {SECRET}. Authorization: Bearer abc.def.ghi "
           + "and so on " * 60)
    spec = {1: [{"outcome": "api_error", "row": {"agent_error": ae(True, "api", "turn.failed", raw, 2)}}, {"outcome": "ok"}],
            2: {"outcome": "no_grade", "row": {"agent_error": ae(False, None, None, raw, 1)}}}
    e = Env(tmp_path, GPT_ROWS[:2], by_order(spec), gap=0)
    e.run()
    infra = {x["order"]: x for x in e.events("infra")}
    assert infra[1]["message"].startswith("unexpected status 401: Incorrect API key provided: [key removed]")
    assert len(infra[1]["message"]) == 300 and infra[2]["reason"] == "no_grade" and infra[2]["message"] == infra[1]["message"]
    everything = (e.cfg.ledger.read_text() + e.cfg.runlog.read_text() + "".join(e.said) + bs.format_summary(e.summary)
                  + "".join(p.read_text() for p in e.cfg.rollouts.glob("*/infra_failures.jsonl")))
    assert SECRET not in everything and "sk-" not in everything and "abc.def.ghi" not in everything
    # an infrastructure failure without any error message says so with a null
    f = Env(tmp_path / "b", GPT_ROWS[:1], by_order({1: [{"outcome": "no_grade"}, {"outcome": "ok"}]}))
    f.run()
    assert f.events("infra")[0]["message"] is None and "agent_error" not in f.events("infra")[0]
    assert "excluded: order 1 attempt 1" in bs.format_summary(f.summary) and "no error message" in bs.format_summary(f.summary)


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


SR = bs.STUDY_RESULTS
CODE = ("scripts/blackbox_schedule.py", "scripts/collect_rollouts.py")   # what a scheduler process runs


def write_prereg_hash(e, rels=None, edit=None):
    """PREREG_HASH as `sha256sum <rels>` run from the repository root (here: tmp_path) prints it."""
    lines = [f"{bs.sha256_file(e.tmp / rel)}  {rel}\n" for rel in (e.prereg_files if rels is None else rels)]
    (e.cfg.results / "PREREG_HASH").write_text("".join(edit(lines) if edit else lines))


def preflight_env(tmp_path, rows=None, **kw):
    """A block whose "repository" is tmp_path: results/blackbox_1112/ with prereg.md and both run orders (and
    the block's own, if it is another), scripts/<the five>. The scheduler and the collector of that repository
    are copies of the real ones and are "what this process runs" (Config.code), as in a real start."""
    kw.setdefault("code", {rel: tmp_path / rel for rel in CODE})
    e = Env(tmp_path, rows or mixed(6), subdir=SR, results=SR, repo=tmp_path, **kw)
    for n in bs.PREREG_RUNORDERS:
        if not (e.cfg.results / n).exists():
            write_runorder(e.cfg.results / n, [(G, "open64", "ep411", 1)])
    task = e.cfg.task_dir
    (task / "scripts").mkdir(parents=True)
    (task.parents[1] / "tools").mkdir()
    for p in (task / "scripts" / "launch_rollouts.py", task / "scripts" / "collect_rollouts.py",
              task.parents[1] / "tools" / "task_runner.py"):
        p.write_text("")
    (task / "problems.txt").write_text("# comment\n" + "".join(f"{j.problem}  # x\n" for j in e.jobs) + "ep481-open\n")
    (e.cfg.results / "prereg.md").write_text("# prereg\n")
    (tmp_path / "scripts").mkdir()
    for rel in bs.PREREG_SCRIPTS:
        (tmp_path / rel).write_text(f"# stand-in for {rel}\n")
    for rel in CODE:
        (tmp_path / rel).write_bytes((ROOT / rel).read_bytes())
    e.prereg_files = [f"{SR}/prereg.md", *(f"{SR}/{n}" for n in bs.PREREG_RUNORDERS),
                      *([f"{SR}/{e.runorder.name}"] if e.runorder.name not in bs.PREREG_RUNORDERS else []),
                      *bs.PREREG_SCRIPTS]
    write_prereg_hash(e)
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
    assert e.host.asked == [["prereg.md", "runorder_block1.csv", "runorder_block2.csv", "score_naming.py",
                             "blackbox_analysis.py", "s3_coder.py", "collect_rollouts.py", "blackbox_schedule.py",
                             "PREREG_HASH"]]
    assert ("all 8 files listed in PREREG_HASH have its sha256 (prereg.md, 2 run orders, 5 scripts) and this process "
            "runs the listed scheduler and collector") in checks["prereg"].detail
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
    ("prereg", lambda e: (e.cfg.results / "prereg.md").write_text("# prereg, edited\n"),
     f"sha256 differs from PREREG_HASH for: {SR}/prereg.md"),
    ("prereg", lambda e: e.runorder.write_text(e.runorder.read_text() + "\n"),
     f"sha256 differs from PREREG_HASH for: {SR}/runorder_block1.csv"),
    ("prereg", lambda e: write_prereg_hash(e, e.prereg_files[:1]),
     f"PREREG_HASH has no entry for: {SR}/runorder_block1.csv, {SR}/runorder_block2.csv, scripts/score_naming.py"),
    ("prereg", lambda e: write_prereg_hash(e, e.prereg_files[1:]), f"PREREG_HASH has no entry for: {SR}/prereg.md"),
    # BOTH run-order files are pre-registered: Block 1 does not start on a hash without Block 2's order
    ("prereg", lambda e: write_prereg_hash(e, [r for r in e.prereg_files if "block2" not in r]),
     f"PREREG_HASH has no entry for: {SR}/runorder_block2.csv"),
    # CR LF line ends: not what sha256sum writes, and `sha256sum -c` cannot read them
    ("prereg", lambda e: (e.cfg.results / "PREREG_HASH").write_bytes(
        (e.cfg.results / "PREREG_HASH").read_bytes().replace(b"\n", b"\r\n")), "carriage returns"),
    # a listed file that is a symbolic link, also one whose target has the recorded hash
    ("prereg", lambda e: ((e.tmp / "elsewhere.py").write_bytes((e.tmp / "scripts/s3_coder.py").read_bytes()),
                          (e.tmp / "scripts/s3_coder.py").unlink(),
                          (e.tmp / "scripts/s3_coder.py").symlink_to(e.tmp / "elsewhere.py")),
     "listed in PREREG_HASH but not a file of the repository: scripts/s3_coder.py"),
    # the scheduler that runs is not the repository's (a copy elsewhere, edited), nor is its collector
    ("prereg", lambda e: ((e.tmp / "alt").mkdir(), (e.tmp / "alt/blackbox_schedule.py").write_text("STOP_STREAK = 99\n"),
                          e.cfg.code.update({"scripts/blackbox_schedule.py": e.tmp / "alt/blackbox_schedule.py"})),
     "this process does not run the code PREREG_HASH lists: scripts/blackbox_schedule.py (running: "),
    ("prereg", lambda e: e.cfg.code.update({"scripts/collect_rollouts.py": e.tmp / "gone.py"}),
     "this process does not run the code PREREG_HASH lists: scripts/collect_rollouts.py"),
    ("prereg", lambda e: setattr(e.host, "git", (False, "prereg.md has uncommitted changes")), "uncommitted"),
    ("prereg", lambda e: setattr(e.host, "git", (False, "blackbox_schedule.py is not committed")), "not committed"),
    # the old format (written inside the results directory, bare names, no scripts) is refused by name
    ("prereg", lambda e: (e.cfg.results / "PREREG_HASH").write_text("".join(
        f"{bs.sha256_file(e.cfg.results / n)}  {n}\n" for n in ("prereg.md", "runorder_block1.csv", "runorder_block2.csv"))),
     "the old format (bare file names"),
    ("prereg", lambda e: (e.cfg.results / "PREREG_HASH").write_text(bs.sha256_file(e.cfg.results / "prereg.md") + "\n"),
     "line 1 is not a `sha256sum` line"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: l + ["# D25: scripts/s3_coder.py changed\n"]),
     "line 9 is not a `sha256sum` line"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: l + l[-1:]), "'scripts/blackbox_schedule.py' is listed twice"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: [l[0].replace("  results/", f"  {e.tmp}/results/")] + l[1:]),
     "is not a path relative to the repository root"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: [l[0].replace("  results/", "  ./results/")] + l[1:]),
     "is not a path relative to the repository root"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: [l[0].replace("  results/", "  scripts/../results/")] + l[1:]),
     "is not a path relative to the repository root"),
    ("prereg", lambda e: write_prereg_hash(e, edit=lambda l: [x.upper() if i == 3 else x for i, x in enumerate(l)]),
     "line 4 is not a `sha256sum` line"),
    # every listed file is verified: the other block's run order, and a file the block does not need at all
    ("prereg", lambda e: (e.cfg.results / "runorder_block2.csv").write_text("y\n"),
     f"sha256 differs from PREREG_HASH for: {SR}/runorder_block2.csv"),
    ("prereg", lambda e: (e.cfg.results / "runorder_block2.csv").unlink(),
     f"listed in PREREG_HASH but not a file of the repository: {SR}/runorder_block2.csv"),
    ("prereg", lambda e: (e.prereg_files.append("task.py"), (e.tmp / "task.py").write_text("x\n"), write_prereg_hash(e),
                          (e.tmp / "task.py").write_text("y\n")), "sha256 differs from PREREG_HASH for: task.py"),
    ("prereg", lambda e: (e.prereg_files.append("task.py"), (e.tmp / "task.py").write_text("x\n"), write_prereg_hash(e),
                          (e.tmp / "task.py").unlink()), "listed in PREREG_HASH but not a file of the repository: task.py"),
    # the study's own results directory and a run order that is a file in it: nothing else is this study's state
    ("runorder", lambda e: setattr(e.cfg, "repo", e.tmp / "elsewhere"), f"is not {SR} of the repository"),
    ("runorder", lambda e: ((e.tmp / "results/alt").mkdir(), setattr(e.cfg, "results", e.tmp / "results/alt")),
     f"is not {SR} of the repository"),
    ("runorder", lambda e: ((e.tmp / "ro").mkdir(), (e.tmp / "ro/runorder_block1.csv").write_bytes(e.runorder.read_bytes()),
                            setattr(e.cfg, "runorder", e.tmp / "ro/runorder_block1.csv")),
     f"is a symbolic link or not a file directly in {SR}"),
    ("runorder", lambda e: ((e.cfg.results / "runorder_block1_link.csv").symlink_to(e.runorder),
                            setattr(e.cfg, "runorder", e.cfg.results / "runorder_block1_link.csv"),
                            setattr(e.cfg, "block", "block1_link")),
     f"is a symbolic link or not a file directly in {SR}"),
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
    others = {"runorder": {"prereg", "runlog"}, "runlog": {"spend:openai", "spend:anthropic"}}.get(name, set())
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


@pytest.mark.parametrize("script", bs.PREREG_SCRIPTS)
def test_preflight_needs_every_one_of_the_five_scripts_in_prereg_hash_and_unchanged(tmp_path, script):
    e = preflight_env(tmp_path)
    write_prereg_hash(e, [r for r in e.prereg_files if r != script])                 # no entry for it
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail == f"PREREG_HASH has no entry for: {script}"
    write_prereg_hash(e)
    assert run_preflight(e)["prereg"].ok
    (tmp_path / script).write_text(f"# stand-in for {script}, changed after the hash\n")  # changed after the hash
    c = run_preflight(e)["prereg"]
    assert not c.ok and f"sha256 differs from PREREG_HASH for: {script} " in c.detail and "logged deviation" in c.detail
    write_prereg_hash(e)                                                            # written again (and committed)
    assert run_preflight(e)["prereg"].ok
    (tmp_path / script).unlink()
    c = run_preflight(e)["prereg"]
    assert not c.ok and f"not a file of the repository: {script}" in c.detail


def test_preflight_needs_both_run_orders_in_prereg_hash_for_either_block(tmp_path):
    """RUNBOOK section 6 writes one PREREG_HASH with both run-order files (prereg.md: "of both run-order
    files"); either block's preflight needs both entries, so Block 2's order is fixed before Block 1 starts."""
    e = preflight_env(tmp_path)
    c = run_preflight(e)["prereg"]
    assert c.ok and "all 8 files listed" in c.detail and "2 run orders" in c.detail and "more" not in c.detail
    assert e.host.asked[-1][:3] == ["prereg.md", "runorder_block1.csv", "runorder_block2.csv"]
    assert bs.prereg_required(e.cfg) == e.prereg_files
    b2 = preflight_env(tmp_path / "b2", [(G, "open64", "ep411", 1)], name="runorder_block2.csv")
    assert b2.cfg.block == "block2" and run_preflight(b2)["prereg"].ok and bs.prereg_required(b2.cfg) == e.prereg_files
    for missing in ("runorder_block1.csv", "runorder_block2.csv"):
        for env in (e, b2):
            write_prereg_hash(env, [r for r in env.prereg_files if not r.endswith(missing)])
            assert run_preflight(env)["prereg"].detail == f"PREREG_HASH has no entry for: {SR}/{missing}"
            write_prereg_hash(env)
    # another counted block (a logged deviation would add one) needs its own entry next to the two
    b3 = preflight_env(tmp_path / "b3", [(G, "bb8", "ep411", 1)], name="runorder_block3.csv")
    assert bs.prereg_required(b3.cfg)[1:4] == [f"{SR}/runorder_block1.csv", f"{SR}/runorder_block2.csv",
                                               f"{SR}/runorder_block3.csv"]
    c = run_preflight(b3)["prereg"]
    assert c.ok and "all 9 files listed" in c.detail and "3 run orders" in c.detail
    write_prereg_hash(b3, [r for r in b3.prereg_files if "block3" not in r])
    assert run_preflight(b3)["prereg"].detail == f"PREREG_HASH has no entry for: {SR}/runorder_block3.csv"
    # a file listed beyond what is required is verified and counted
    (tmp_path / "task.py").write_text("x\n")
    write_prereg_hash(e, e.prereg_files + ["task.py"])
    c = run_preflight(e)["prereg"]
    assert c.ok and "all 9 files listed" in c.detail and "5 scripts, 1 more" in c.detail


def test_a_symlinked_run_order_or_another_results_directory_never_starts_a_pilot_either(tmp_path):
    """A pilot has no prereg check, but its run order and results directory are the study's too: a link named
    like a pilot to a block's order, or a results directory with a RUNLOG of its own, is refused."""
    e = preflight_env(tmp_path, [(G, "bb8", "ep411", 1)], name="runorder_pilots.csv", pilot=True)
    assert run_preflight(e)["runorder"].ok
    link = e.cfg.results / "runorder_pilot_b1.csv"
    link.symlink_to(e.cfg.results / "runorder_block1.csv")
    e.cfg.runorder, e.cfg.block = link, bs.block_name(link)
    c = run_preflight(e)["runorder"]
    assert not c.ok and "symbolic link" in c.detail
    f = preflight_env(tmp_path / "f", [(G, "bb8", "ep411", 1)], name="runorder_pilots.csv", pilot=True)
    (f.tmp / "results/other").mkdir()
    f.cfg.results = f.tmp / "results/other"
    c = run_preflight(f)["runorder"]
    assert not c.ok and f"is not {SR} of the repository" in c.detail


def test_check_prereg_alone_refuses_a_linked_run_order_and_another_results_directory(tmp_path):
    """--check-prereg runs check_prereg without the rest of the preflight: it must say so itself. A link
    `runorder_block1_link.csv` to the committed order would be a new block `block1_link` of 108 unrecorded jobs;
    a results directory of its own, committed with its own prereg.md, PREREG_HASH and order, another study."""
    e = preflight_env(tmp_path)
    assert bs.check_prereg(e.cfg, e.host)[0]
    link = e.cfg.results / "runorder_block1_link.csv"
    link.symlink_to(e.runorder)
    cfg = bs.Config(link, "r1112", e.cfg.task_dir, e.cfg.results, repo=tmp_path, code=e.cfg.code)
    assert cfg.block == "block1_link"
    ok, detail = bs.check_prereg(cfg, e.host)
    assert not ok and "is a symbolic link or not a file directly in results/blackbox_1112" in detail
    alt = tmp_path / "results" / "alt"
    alt.mkdir()
    for n in ("prereg.md", "runorder_block1.csv", "runorder_block2.csv"):
        (alt / n).write_bytes((e.cfg.results / n).read_bytes())
    (alt / "PREREG_HASH").write_text("".join(
        f"{bs.sha256_file(tmp_path / rel)}  {rel}\n" for rel in
        ["results/alt/prereg.md", "results/alt/runorder_block1.csv", "results/alt/runorder_block2.csv", *bs.PREREG_SCRIPTS]))
    cfg = bs.Config(alt / "runorder_block1.csv", "r1112", e.cfg.task_dir, alt, repo=tmp_path, code=e.cfg.code)
    ok, detail = bs.check_prereg(cfg, e.host)
    assert not ok and detail == f"--results {alt} is not results/blackbox_1112 of the repository {tmp_path}"


def test_the_running_code_is_checked_against_prereg_hash_by_default(tmp_path):
    """Config.code defaults to the files this process loaded: the real scheduler and the collector next to it.
    A repository whose listed scheduler is another file than the one that runs fails the check."""
    cfg = bs.Config(ROOT / SR / "runorder_block1.csv", "r1112", tmp_path, ROOT / SR)
    assert cfg.code == {"scripts/blackbox_schedule.py": Path(bs.__file__).resolve(),
                        "scripts/collect_rollouts.py": Path(bs.CR.__file__).resolve()}
    assert cfg.code == {rel: ROOT / rel for rel in CODE}
    e = preflight_env(tmp_path / "r")
    e.cfg.code = dict(cfg.code)                                          # the real files: the copies are equal
    assert run_preflight(e)["prereg"].ok
    (e.tmp / "scripts/blackbox_schedule.py").write_text("# the repository's scheduler, changed\n")
    write_prereg_hash(e)                                                 # hashed and (FakeHost) committed
    c = run_preflight(e)["prereg"]
    assert not c.ok and "this process does not run the code PREREG_HASH lists: scripts/blackbox_schedule.py" in c.detail


def test_prereg_hashes_format():
    h1, h2 = "a" * 64, "b" * 64
    text = f"{h1}  results/blackbox_1112/prereg.md\n{h2} *scripts/s3_coder.py\n\n"
    assert bs.prereg_hashes(text) == ({"results/blackbox_1112/prereg.md": h1, "scripts/s3_coder.py": h2}, [])
    assert bs.prereg_hashes(f"{h1}  task.py\n") == ({"task.py": h1}, [])       # a file at the root is a path too
    for bad, why in ((f"{h1}  prereg.md\n", "old format"), (f"{h1}  runorder_block1.csv\n", "old format"),
                     (f"{h1}\n", "not a `sha256sum` line"), (f"{h1} prereg.md\n", "not a `sha256sum` line"),
                     ("# note\n", "not a `sha256sum` line"), (f"{'a' * 63}  scripts/x.py\n", "not a `sha256sum` line"),
                     (f"{h1}  /abs/prereg.md\n", "not a path relative"), (f"{h1}  a/../b\n", "not a path relative"),
                     (f"{h1}  a//b\n", "not a path relative"),
                     (f"{h1}  scripts/x.py\n{h2}  scripts/x.py\n", "listed twice"),
                     (f"{h1}  scripts/x.py\r\n", "carriage returns"), (f"{h1}  scripts/x.py\r", "carriage returns")):
        entries, problems = bs.prereg_hashes(bad)
        assert len(problems) >= 1 and why in problems[0], (bad, problems)
        assert len(problems) == 1 or "\r" in bad


def test_prereg_hash_format_is_what_sha256sum_prints_from_the_repository_root(tmp_path):
    """The RUNBOOK command, run for real in a stand-in repository, gives a file the preflight accepts."""
    import subprocess
    e = preflight_env(tmp_path)
    out = subprocess.run(["sha256sum", *e.prereg_files], cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    assert out == (e.cfg.results / "PREREG_HASH").read_text()
    assert bs.prereg_hashes(out) == ({rel: bs.sha256_file(tmp_path / rel) for rel in e.prereg_files}, [])
    # run inside the results directory (the old command), it gives bare names: refused
    old = subprocess.run(["sha256sum", "prereg.md", e.runorder.name], cwd=e.cfg.results, capture_output=True, text=True,
                         check=True).stdout
    (e.cfg.results / "PREREG_HASH").write_text(old)
    c = run_preflight(e)["prereg"]
    assert not c.ok and "old format" in c.detail and "RUNBOOK section 6" in c.detail


def test_the_real_prereg_scripts_exist_and_the_default_repository_is_this_one(tmp_path):
    for rel in bs.PREREG_SCRIPTS:
        assert (ROOT / rel).is_file(), rel
    assert bs.PREREG_SCRIPTS == ("scripts/score_naming.py", "scripts/blackbox_analysis.py", "scripts/s3_coder.py",
                                 "scripts/collect_rollouts.py", "scripts/blackbox_schedule.py")
    cfg = bs.Config(ROOT / "results" / "blackbox_1112" / "runorder_block1.csv", "r1112", tmp_path, ROOT / "results" / "blackbox_1112")
    assert bs.STUDY_RESULTS == "results/blackbox_1112" and bs.PREREG_RUNORDERS == ("runorder_block1.csv", "runorder_block2.csv")
    assert cfg.repo == ROOT and bs.study_paths_problem(cfg) is None and bs.prereg_required(cfg) == [
        "results/blackbox_1112/prereg.md", "results/blackbox_1112/runorder_block1.csv",
        "results/blackbox_1112/runorder_block2.csv", *bs.PREREG_SCRIPTS]
    for n in bs.PREREG_RUNORDERS:
        assert (ROOT / bs.STUDY_RESULTS / n).is_file() and not (ROOT / bs.STUDY_RESULTS / n).is_symlink()
    prereg = ROOT / "results" / "blackbox_1112" / "prereg.md"
    if prereg.exists():                                                  # the scope prereg.md states
        for rel in bs.PREREG_SCRIPTS:
            assert f"`{rel}`" in prereg.read_text(), rel


def git_repo(tmp_path):
    """preflight_env in a real git repository with everything committed -> (env, git, paths, host)."""
    import subprocess
    git = lambda *a: subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                                     *a], capture_output=True, text=True, check=True)
    e = preflight_env(tmp_path)
    git("init", "-q")
    paths = [tmp_path / rel for rel in e.prereg_files] + [e.cfg.results / "PREREG_HASH"]
    host = bs.Host(e.cfg)
    e.host.git_committed = host.git_committed                           # the whole check, with real git
    return e, git, paths, host


def test_host_git_committed_needs_every_file_tracked_and_unchanged(tmp_path):
    """The real Host against a real git repository: committed and clean passes; an untracked file, a change in
    the work tree and a staged change each fail, naming the file by its path in the repository."""
    e, git, paths, host = git_repo(tmp_path)
    assert host.git_committed(paths) == (False, f"{SR}/prereg.md is not committed (HEAD has no such file)")
    git("add", SR, "scripts")
    git("commit", "-q", "-m", "prereg")
    assert host.git_committed(paths) == (True, "each is the file HEAD holds, no uncommitted change")
    c = run_preflight(e)["prereg"]
    assert c.ok and c.detail.endswith("each is the file HEAD holds, no uncommitted change")
    script = tmp_path / "scripts" / "s3_coder.py"
    script.write_text("# changed after the hash\n")
    assert "sha256 differs from PREREG_HASH for: scripts/s3_coder.py" in run_preflight(e)["prereg"].detail
    write_prereg_hash(e)                                                # hash written again, nothing committed yet
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail == "scripts/s3_coder.py has uncommitted changes (the file is not what HEAD holds)"
    git("add", "scripts/s3_coder.py")                                   # staged is not committed
    assert run_preflight(e)["prereg"].detail == "scripts/s3_coder.py has uncommitted changes (the file is not what HEAD holds)"
    git("commit", "-q", "-m", "script")
    assert run_preflight(e)["prereg"].detail == f"{SR}/PREREG_HASH has uncommitted changes (the file is not what HEAD holds)"
    git("commit", "-q", "-am", "hash")
    assert run_preflight(e)["prereg"].ok
    # staged, then the work tree put back: the file is HEAD's again, but the index holds another version
    old = script.read_text()
    script.write_text("# staged only\n")
    git("add", "scripts/s3_coder.py")
    script.write_text(old)
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail.startswith("scripts/s3_coder.py has uncommitted changes (git status: M")
    git("reset", "-q")
    assert run_preflight(e)["prereg"].ok
    # an untracked file listed in PREREG_HASH
    (tmp_path / "task.py").write_text("x\n")
    write_prereg_hash(e, e.prereg_files + ["task.py"])
    git("commit", "-q", "-am", "hash with task.py")
    assert run_preflight(e)["prereg"].detail == "task.py is not committed (HEAD has no such file)"
    # a path outside the repository, and a repository that is not the top level
    assert host.git_committed([tmp_path.parent / "x"])[1].endswith(f"is not inside the repository {tmp_path}")
    sub = bs.Host(bs.Config(e.runorder, "r1112", e.cfg.task_dir, e.cfg.results, repo=tmp_path / "scripts"))
    assert sub.git_committed([script]) == (False, f"{tmp_path / 'scripts'} is not the top level of a git work tree "
                                           "(git rev-parse failed or names another)")
    nogit = tmp_path.parent / (tmp_path.name + "_nogit")
    nogit.mkdir()
    assert not bs.Host(bs.Config(e.runorder, "r1112", e.cfg.task_dir, e.cfg.results, repo=nogit)).git_committed([])[0]


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_git_index_flags_cannot_hide_an_uncommitted_change(tmp_path, flag):
    """`git update-index --assume-unchanged / --skip-worktree` make `git status` silent about a changed file;
    the check compares the file with HEAD's content and does not ask the index."""
    import subprocess
    e, git, paths, host = git_repo(tmp_path)
    git("add", SR, "scripts")
    git("commit", "-q", "-m", "prereg")
    (tmp_path / "scripts/s3_coder.py").write_text("# changed after the hash\n")
    write_prereg_hash(e)
    git("update-index", flag, "scripts/s3_coder.py", f"{SR}/PREREG_HASH")
    status = subprocess.run(["git", "-C", str(tmp_path), "status", "--porcelain"], capture_output=True, text=True).stdout
    assert status.strip() == "" or "s3_coder" not in status              # git status does not show it
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail == "scripts/s3_coder.py has uncommitted changes (the file is not what HEAD holds)"


def test_a_git_that_fails_is_a_failed_check_never_a_pass(tmp_path, monkeypatch):
    """`git status` exiting non-zero (a broken configuration value), git not runnable at all, and GIT_*
    variables of the environment: none of them lets an uncommitted change through, or fails a clean tree."""
    import subprocess
    e, git, paths, host = git_repo(tmp_path)
    git("add", SR, "scripts")
    git("commit", "-q", "-m", "prereg")
    assert run_preflight(e)["prereg"].ok
    (tmp_path / "scripts/s3_coder.py").write_text("# changed after the hash\n")
    write_prereg_hash(e)                                                 # nothing committed
    git("config", "status.showUntrackedFiles", "bogus")                  # `git status` now exits 128
    assert subprocess.run(["git", "-C", str(tmp_path), "status", "--porcelain"], capture_output=True).returncode != 0
    c = run_preflight(e)["prereg"]                                       # (the old check read this as "clean")
    assert not c.ok and c.detail.startswith(f"`git status` failed for {SR}/prereg.md (exit ")
    assert host.git_committed([tmp_path / "scripts/s3_coder.py"]) == (
        False, "scripts/s3_coder.py has uncommitted changes (the file is not what HEAD holds)")
    git("config", "--unset", "status.showUntrackedFiles")                # (git commit needs a valid value)
    git("commit", "-q", "-am", "script and hash")
    git("config", "status.showUntrackedFiles", "bogus")                  # committed: only the failing status is left
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail.startswith(f"`git status` failed for {SR}/prereg.md (exit ")
    git("config", "--unset", "status.showUntrackedFiles")
    assert run_preflight(e)["prereg"].ok
    # the same breakage through the environment does not reach git, nor does a GIT_DIR of another repository
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "status.showUntrackedFiles")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "bogus")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "no_such_git_dir"))
    assert run_preflight(e)["prereg"].ok
    for var in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_DIR"):
        monkeypatch.delenv(var)
    # git cannot be run at all
    real_run = subprocess.run
    monkeypatch.setattr(bs.subprocess, "run", lambda cmd, *a, **k: (_ for _ in ()).throw(FileNotFoundError("git"))
                        if cmd[0] == "git" else real_run(cmd, *a, **k))
    c = run_preflight(e)["prereg"]
    assert not c.ok and "is not the top level of a git work tree" in c.detail
    assert host._git("status") == (127, b"")


def test_committed_symbolic_links_are_not_files_of_the_pre_registration(tmp_path):
    """A listed script, or PREREG_HASH itself, committed as a symbolic link to a file outside the repository:
    git sees no change when the target changes, so a link is refused whatever it points to."""
    e, git, paths, host = git_repo(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "_outside")
    outside.mkdir()
    hashfile = e.cfg.results / "PREREG_HASH"
    (outside / "PREREG_HASH").write_bytes(hashfile.read_bytes())
    hashfile.unlink()
    hashfile.symlink_to(outside / "PREREG_HASH")
    git("add", SR, "scripts")
    git("commit", "-q", "-m", "prereg, the hash file is a link")
    c = run_preflight(e)["prereg"]
    assert not c.ok and c.detail == f"{SR}/PREREG_HASH is a symbolic link or not a regular file"
    assert host.git_committed([tmp_path / "scripts"])[1] == "scripts is a symbolic link or not a regular file"


def test_start_event_records_the_prereg_hash_and_says_when_it_changed(tmp_path):
    e = preflight_env(tmp_path, mixed(4))
    hashfile = e.cfg.results / "PREREG_HASH"
    first = bs.sha256_file(hashfile)
    e.run(stop_after=60)                                                 # an interrupted start
    e.run(stop_after=60)                                                 # the same PREREG_HASH: nothing to say
    starts = e.events("start")
    assert [x["prereg_hash_sha256"] for x in starts] == [first, first]
    assert not any("prereg_hash_previous" in x for x in starts) and not any("PREREG_HASH" in t for t in e.said)
    assert bs.summarize_ledger(e.events(), "block1")["prereg_hashes"] == [first]
    assert "CHANGED" not in bs.format_summary(bs.summarize_ledger(e.events(), "block1"))
    (tmp_path / "scripts/s3_coder.py").write_text("# changed after the hash: a logged deviation\n")
    write_prereg_hash(e)                                                 # written again (and committed)
    second = bs.sha256_file(hashfile)
    assert second != first and run_preflight(e)["prereg"].ok
    e.run()
    last = e.events("start")[-1]
    assert last["prereg_hash_sha256"] == second and last["prereg_hash_previous"] == first
    said = [t for t in e.said if t.startswith("# PREREG_HASH is not the file of this block's last start")]
    assert len(said) == 1 and first[:16] in said[0] and second[:16] in said[0] and "DECISIONS" in said[0]
    text = bs.format_summary(e.summary)
    assert e.summary["prereg_hashes"] == [first, second] and "CHANGED between starts" in text
    assert f"{first[:16]}, {second[:16]}" in text
    # a block without the file (a pilot) records null and prints no line
    f = Env(tmp_path / "p", [(G, "bb8", "ep411", 1)], name="runorder_pilots.csv", pilot=True)
    f.run()
    assert f.events("start")[0]["prereg_hash_sha256"] is None and "PREREG_HASH" not in bs.format_summary(f.summary)


# ---------------------------------------------------------------- command line

def cli_args(e, *extra):
    return ["--runorder", str(e.runorder), "--task-dir", str(e.cfg.task_dir), "--results", str(e.cfg.results),
            "--cap-openai", "800", "--cap-anthropic", "130", *extra]


def test_main_aborts_on_a_preflight_failure_and_starts_nothing(tmp_path, monkeypatch, capsys):
    e = preflight_env(tmp_path)
    e.host.net = (False, "NOT OK: no REJECT rule")
    monkeypatch.setattr(bs, "ROOT", tmp_path)  # main() builds its Config with this file's repository
    monkeypatch.setattr(bs, "Host", lambda cfg: e.host)
    built = []
    monkeypatch.setattr(bs, "RealLauncher", lambda cfg: built.append(cfg))
    assert bs.main(cli_args(e)) == 1
    out = capsys.readouterr()
    assert "FAIL net_isolation" in out.out and "preflight failed (net_isolation); nothing was started" in out.err
    assert not built and not e.cfg.ledger.exists() and SECRET not in out.out + out.err


def test_main_check_prereg_runs_only_that_check_and_starts_nothing(tmp_path, monkeypatch, capsys):
    """RUNBOOK section 8 runs it before the hashed scoring and analysis scripts are used."""
    e = preflight_env(tmp_path)
    e.host.net = (False, "NOT OK: no REJECT rule")                      # no other check is run
    monkeypatch.setattr(bs, "ROOT", tmp_path)  # main() builds its Config with this file's repository
    monkeypatch.setattr(bs, "Host", lambda cfg: e.host)
    monkeypatch.setattr(bs, "RealLauncher", lambda cfg: pytest.fail("--check-prereg must start nothing"))
    assert bs.main(cli_args(e, "--check-prereg")) == 0
    out = capsys.readouterr().out
    assert out.startswith("  ok   prereg: all 8 files listed in PREREG_HASH") and "net_isolation" not in out
    (tmp_path / "scripts/score_naming.py").write_text("# edited after Block 1 ended\n")
    assert bs.main(cli_args(e, "--check-prereg")) == 1
    assert "FAIL prereg: sha256 differs from PREREG_HASH for: scripts/score_naming.py" in capsys.readouterr().out
    write_prereg_hash(e)
    e.host.git = (False, "scripts/score_naming.py has uncommitted changes (the file is not what HEAD holds)")
    assert bs.main(cli_args(e, "--check-prereg")) == 1
    assert "FAIL prereg: scripts/score_naming.py has uncommitted changes" in capsys.readouterr().out
    assert not e.cfg.ledger.exists() and not (e.cfg.task_dir / "results").exists()
    assert bs.main(cli_args(e, "--check-prereg", "--dry-run", "--dry-run-dir", str(tmp_path / "dry"))) == 1
    assert not (tmp_path / "dry" / "ledger.jsonl").exists()


def test_main_dry_run_runs_the_whole_block_and_writes_no_real_state(tmp_path, monkeypatch, capsys):
    e = preflight_env(tmp_path, mixed(12))
    e.host.sync = (False, "DIFFERS scripts/collect_rollouts.py")  # a dry run reports it and goes on
    monkeypatch.setattr(bs, "ROOT", tmp_path)  # main() builds its Config with this file's repository
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
    monkeypatch.setattr(bs, "ROOT", tmp_path)  # main() builds its Config with this file's repository
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
(d / "grade.json").write_text(json.dumps({"details": {"probes": [{}]}, "hard_slots": [0]}))
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
        (d / "grade.json").write_text(json.dumps({"details": {"probes": [{}]}, "hard_slots": [0]}))
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


@pytest.mark.parametrize("grade,want", [
    (None, False),                                                     # no grade.json
    ({"score": 0.0, "timeout": True}, False),                         # the entrypoint's timeout stub
    ({"details": {"probes": []}, "hard_slots": [0]}, False),          # no per-probe records
    ({"details": {"probes": [{"kind": "planted"}]}}, False),          # no hard_slots
    ({"details": {"probes": [{"kind": "planted"}]}, "hard_slots": [0]}, True),
])
def test_a_stub_grade_next_to_an_accepted_submission_is_not_a_grade(tmp_path, grade, want):
    """prereg section 7: a submission the grader did not grade (no grade.json, or one without per-probe records)
    is needs_regrade, never ok and never re-run; without a submission any grade.json is the run's grade."""
    d = tmp_path / "c1"
    d.mkdir()
    if grade is not None:
        (d / "grade.json").write_text(json.dumps(grade))
    row = {"cid": "c1", "harness_status": "ok"}
    if grade is not None:  # no submission: the grader's "no accepted submission" grade counts as written
        assert bs.run_facts(tmp_path, "c1", row, "codex")["has_grade"] is True
    (d / "submission.json").write_text("{}")
    facts = bs.run_facts(tmp_path, "c1", row, "codex")
    assert facts["submitted"] is True and facts["has_grade"] is want
    out = bs.classify("c1", True, **{k: facts[k] for k in ("submitted", "has_grade", "timeout", "harness_status",
                                                             "daemon_died", "engine", "agent_error")})
    assert out.status == ("ok" if want else "needs_regrade") and out.infra is False
