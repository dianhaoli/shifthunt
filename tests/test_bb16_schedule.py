"""scripts/bb16_schedule.py on synthetic state: run orders, the arm's spend rule, the paths and the hash check.
No docker, no process, no API: the scheduler runs with its own fake launcher and simulated clock."""
import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_wrapper():
    """The wrapper with its own copies of blackbox_schedule / blackbox_runorder, so its changes to them do not
    reach other tests that import those modules by name."""
    names = ("blackbox_schedule", "blackbox_runorder", "blackbox_pilot_check")
    saved = {n: sys.modules.pop(n) for n in names if n in sys.modules}
    try:
        spec = importlib.util.spec_from_file_location("bb16_schedule_test", ROOT / "scripts" / "bb16_schedule.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        for n in names:
            sys.modules.pop(n, None)
        sys.modules.update(saved)
    return mod


W = _load_wrapper()
BS, R = W.BS, W.R
SR = BS.STUDY_RESULTS
HEADER = BS.RUNLOG_HEADER


# ---------------------------------------------------------------- run orders

def test_counted_order_is_24_gpt_bb16_jobs_four_per_item_seeded_and_interleaved():
    rows = W.counted_rows()
    assert len(rows) == 24 and [r["order"] for r in rows] == list(range(1, 25))
    assert {(r["agent"], r["arm"], r["engine"], r["model"]) for r in rows} == {("gpt", "bb16", "codex", "gpt-6.1-terra")}
    assert all(r["problem"] == r["item"] + "-blackbox16" for r in rows)
    per = {}
    for r in rows:
        per.setdefault(r["item"], []).append(r["rep"])
    assert set(per) == set(R.ITEMS) and all(sorted(v) == [1, 2, 3, 4] for v in per.values())
    assert rows == W.counted_rows()                              # a pure function of the seed
    listing = R.block_rows("bb16")
    assert [(r["item"], r["rep"]) for r in rows] != [(r["item"], r["rep"]) for r in listing]   # permuted
    assert W.SEED == int.from_bytes(__import__("hashlib").sha256(b"bb16-1111").digest(), "big")


def test_pilot_order_is_the_one_prereg_pilot():
    assert W.pilot_rows() == [{"agent": "gpt", "model": "gpt-6.1-terra", "engine": "codex", "arm": "bb16",
                               "item": "ep472", "problem": "ep472-blackbox16", "rep": 1, "order": 1}]


def test_run_order_files_parse_with_the_unchanged_reader(tmp_path):
    files = W.build_runorders(tmp_path)
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    jobs = BS.read_runorder(tmp_path / W.RUNORDER)
    assert len(jobs) == 24 and BS.block_name(tmp_path / W.RUNORDER) == "bb16"
    assert BS.block_name(tmp_path / W.PILOT_RUNORDER) == "bb16_pilot"
    meta = json.loads(files[W.RUNORDER_JSON])
    assert meta["csv_sha256"] == BS.sha256_file(tmp_path / W.RUNORDER)
    assert meta["pilot_csv_sha256"] == BS.sha256_file(tmp_path / W.PILOT_RUNORDER)
    assert [dict(r) for r in csv.DictReader(open(tmp_path / W.RUNORDER))] == \
        [{k: str(v) for k, v in r.items()} for r in meta["rows"]]
    assert BS.run_name("r1112", jobs[0]) == "r1112_gpt_bb16"
    assert BS.run_name("r1112", jobs[0], pilot=True) == "r1112_pilot_gpt_bb16"


def test_committed_files_equal_a_fresh_build_if_present():
    d = ROOT / W.BB16_DIR
    for name, text in W.build_runorders(d).items():
        if (d / name).exists():
            assert (d / name).read_text() == text, name


# ---------------------------------------------------------------- spend

def row(arm, usd, cum_o, cum_a=0.0):
    return f"| 2026-11-11T08:00Z | x | {arm} | gpt | ep472 | ok | {usd:.3f} | {cum_o:.3f} | {cum_a:.3f} |\n"


def test_arm_spent_sums_only_bb16_rows_pilot_included():
    text = HEADER + row("bb8", 1.0, 56.0) + row("bb16 (pilot)", 0.7, 56.7) + row("coders", 0.3, 57.0) + \
        row("bb16", 0.9, 57.9) + row("bb164", 5.0, 62.9)
    assert W.runlog_arm_spent(text) == pytest.approx(1.6)
    assert W.runlog_arm_spent(HEADER) == 0.0
    assert W.runlog_arm_spent(HEADER + row("bb16", 1.0, 1.0).replace("1.000 | 1.000", "nan | 1.000")) == float("inf")


def test_effective_cap_turns_the_scheduler_rule_into_the_arm_rule():
    # scheduler: cum + est * (running + 1) > cap  (CONTINGENCY 0)  <=>  spent + est * (running + 1) > 25
    assert BS.CONTINGENCY == 0.0 and W.STUDY_CONTINGENCY == 5.0
    cap = W.effective_cap(800.0, 60.0, 3.0)
    assert cap == pytest.approx(82.0)
    assert W.effective_cap(800.0, 790.0, 0.0) == 795.0           # the study-wide cap minus $5 still holds
    assert W.effective_cap(800.0, float("inf"), 0.0) == 0.0
    assert W.effective_cap(800.0, 60.0, float("inf")) == 0.0


def by_cost(usd, minutes=10):
    return lambda job, attempt: {"outcome": "ok", "minutes": minutes, "usd": usd}


def sched_env(tmp_path, usd, slots=1, prior=55.592):
    res = tmp_path / SR
    (res / "bb16").mkdir(parents=True)
    for name, text in W.build_runorders(res / "bb16").items():
        (res / "bb16" / name).write_text(text)
    ro = res / "bb16" / W.RUNORDER
    cfg = BS.Config(ro, "r1112", tmp_path / "sub" / "tasks" / "shifthunt", res, rollouts=tmp_path / "rollouts",
                    cap={"openai": 800.0, "anthropic": 130.0}, est={"gpt": 1.61, "haiku": 2.5}, max_slots=slots,
                    repo=tmp_path)
    cfg.runlog.write_text(HEADER + row("coders", 0.294, prior, 78.403))
    clock = BS.FakeClock()
    jobs = BS.read_runorder(ro)
    s = W.BB16Scheduler(cfg, jobs, BS.FakeLauncher(cfg, clock, by_cost(usd)), clock, None, say=lambda t: None)
    return s, cfg


@pytest.mark.parametrize("usd, slots, n_runs", [
    (4.0, 1, 6),     # starts at spent 0, 4, ..., 20 (20 + 1.61 <= 25); at 24: 25.61 > 25
    (5.0, 1, 5),     # 0, 5, 10, 15, 20; at 25 stop
    (0.65, 3, 24),   # the expected cost: the whole arm fits
    (1.61, 1, 15),   # 14 x 1.61 = 22.54, +1.61 = 24.15 <= 25 -> 15th starts; 24.15 + 1.61 > 25
])
def test_no_run_starts_if_spent_plus_estimate_passes_25(tmp_path, usd, slots, n_runs):
    s, cfg = sched_env(tmp_path, usd, slots)
    s.run()
    evs = BS.read_events(cfg.ledger)
    launched = [e for e in evs if e["event"] == "launched"]
    assert len(launched) == n_runs
    spent = W.arm_spent(cfg.runlog)
    assert spent <= W.ARM_CAP_USD + 1e-9
    assert all(e["arm_spent_usd"] + 1.61 * e["running"] <= 25 + 1e-9 for e in launched)
    start = next(e for e in evs if e["event"] == "start")
    assert start["wrapper"] == "scripts/bb16_schedule.py" and start["arm_cap_usd"] == 25.0 and start["arm_est_usd"] == 1.61
    stops = [e for e in evs if e["event"] == "cap_stop"]
    assert bool(stops) == (n_runs < 24)
    # the RUNLOG's cumulative columns stay study-wide
    last = cfg.runlog.read_text().strip().splitlines()[-1]
    assert float(last.split("|")[8]) == pytest.approx(55.592 + spent, abs=1e-3)


@pytest.mark.parametrize("usd, n_runs", [
    (1.0, 24),    # 24 x 1.00 = 24 <= 25: the whole arm; before checker fix 1 the in-flight count stopped it at 23
    (1.61, 15),   # as with one slot: the stop comes only at spent + 1.61 > 25
    (0.65, 24),   # the expected cost
])
def test_jobs_in_flight_make_the_next_run_wait_not_stop_the_arm(tmp_path, usd, n_runs):
    s, cfg = sched_env(tmp_path, usd, slots=3)
    s.run()
    evs = BS.read_events(cfg.ledger)
    launched = [e for e in evs if e["event"] == "launched"]
    assert len(launched) == n_runs
    assert all(e["arm_spent_usd"] + 1.61 * e["running"] <= 25 + 1e-9 for e in launched)
    assert W.arm_spent(cfg.runlog) <= W.ARM_CAP_USD + 1e-9
    stops = [e for e in evs if e["event"] == "cap_stop"]
    assert bool(stops) == (n_runs < 24)
    assert all(e["running"] == 0 and e["arm_spent_usd"] + 1.61 > 25 for e in stops)   # the literal rule only
    start = next(e for e in evs if e["event"] == "start")
    assert "bb16_prereg_hash_sha256" in start and start["bb16_prereg_hash_sha256"] is None


def test_other_tools_rows_do_not_count_against_the_arm(tmp_path):
    s, cfg = sched_env(tmp_path, 0.65, 3, prior=780.0)            # study-wide cum near 800: the 795 cap binds
    s.run()
    launched = [e for e in BS.read_events(cfg.ledger) if e["event"] == "launched"]
    assert 0 < len(launched) < 24                                 # stopped by the study cap, not by the arm's


# ---------------------------------------------------------------- paths, jobs, hash

class FakeHost:
    def __init__(self, ok=True):
        self.ok = ok

    def git_committed(self, paths):
        return (True, "each is the file HEAD holds") if self.ok else (False, "x is not committed")


def repo_env(tmp_path):
    res = tmp_path / SR
    (res / "bb16").mkdir(parents=True)
    for name, text in W.build_runorders(res / "bb16").items():
        (res / "bb16" / name).write_text(text)
    (res / "bb16" / "PREREG_BB16.md").write_text("# prereg\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / W.WRAPPER_REL).write_bytes((ROOT / W.WRAPPER_REL).read_bytes())
    cfg = BS.Config(res / "bb16" / W.RUNORDER, "r1112", tmp_path / "sub", res, repo=tmp_path)
    return cfg


def write_hash(cfg, rels):
    lines = [f"{BS.sha256_file(cfg.repo / r)}  {r}\n" for r in rels]
    (cfg.repo / W.BB16_DIR / W.HASHFILE).write_text("".join(lines))


def test_study_paths_accept_bb16_dir_and_keep_block1_rule(tmp_path):
    cfg = repo_env(tmp_path)
    assert W.study_paths_problem(cfg) is None
    other = BS.Config(cfg.results / "bb16" / "other.csv", "r1112", tmp_path / "sub", cfg.results, repo=tmp_path)
    (cfg.results / "bb16" / "other.csv").write_text("x")
    assert "runorder_bb16" in W.study_paths_problem(other)
    wrong = BS.Config(cfg.runorder, "r1112", tmp_path / "sub", tmp_path / "elsewhere", repo=tmp_path)
    assert "is not results/blackbox_1112" in W.study_paths_problem(wrong)
    top = BS.Config(cfg.results / "runorder_block1.csv", "r1112", tmp_path / "sub", cfg.results, repo=tmp_path)
    assert W.study_paths_problem(top) is None                    # Block 1's rule unchanged for its own files


def test_hash_check_needs_the_bb16_hash_file_with_every_file_and_the_running_wrapper(tmp_path):
    cfg = repo_env(tmp_path)
    wrapper = tmp_path / W.WRAPPER_REL
    ok, d = W.bb16_hash_check(cfg, FakeHost(), wrapper)
    assert not ok and "does not exist" in d
    write_hash(cfg, W.HASH_REQUIRED[:-1])
    ok, d = W.bb16_hash_check(cfg, FakeHost(), wrapper)
    assert not ok and "no entry for: scripts/bb16_schedule.py" in d
    write_hash(cfg, W.HASH_REQUIRED)
    assert W.bb16_hash_check(cfg, FakeHost(), wrapper)[0]
    assert not W.bb16_hash_check(cfg, FakeHost(ok=False), wrapper)[0]
    (cfg.results / "bb16" / "PREREG_BB16.md").write_text("# prereg, edited\n")
    ok, d = W.bb16_hash_check(cfg, FakeHost(), wrapper)
    assert not ok and "sha256 differs" in d and "PREREG_BB16.md" in d
    write_hash(cfg, W.HASH_REQUIRED)
    other = tmp_path / "alt.py"
    other.write_text("# another wrapper\n")
    ok, d = W.bb16_hash_check(cfg, FakeHost(), other)
    assert not ok and "does not run the wrapper" in d


def test_est_gpt_other_than_the_prereg_estimate_is_refused():
    assert W.main(["--runorder", "x.csv", "--cap-openai", "800", "--cap-anthropic", "130", "--est-gpt", "1.5"]) == 2
