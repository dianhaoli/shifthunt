"""scripts/blackbox_pilot_check.py on synthetic collected run directories (no docker, no API)."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("blackbox_pilot_check_wp6b", ROOT / "scripts" / "blackbox_pilot_check.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

AGENT_TEXT = "ZEBRA-QUARTZ agent text that must never be printed"
HARDWARE = "A GPU is available in this environment: all GPUs (shared)\n"


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


def make_run(tmp, problem="ep411-blackbox64", engine="codex", cid="a1b2c3d4e5f6", pq_calls=(3, 2), sae_tries=2,
             submitted=True, name=1, usd=1.0, minutes=20.0, tokens=1000):
    """A collected run directory as scripts/collect_rollouts.py leaves it, consistent in every check."""
    episode, access, override = pc.cr.split_episode_id(problem)
    limit = override or 8
    agent = "gpt" if engine == "codex" else "haiku"
    arm = pc.cr.arm_name(access, limit)
    batch = tmp / f"r1112_pilot_{agent}_{arm}"
    d = batch / cid
    d.mkdir(parents=True)
    (d / "episode_id").write_text(problem + "\n")
    (d / "task.txt").write_text(
        "# ShiftHunt\nBudget: 150 tool calls, 3000 forward units (per note, text or latent as each tool's cost states), "
        f"{limit} texts for `probe_query` in total, and 3600 s.\n\n" + pc.help_text(access) + "\n" + HARDWARE)
    (d / "task_public.json").write_text(json.dumps({"access": access, "k": 16, "budgets": {"probe_query": limit}}))
    log, full, seq = [{"event": "ready", "t": 1.0, "pid": 18}], [], 0

    def call(tool, charges, status="ok", args=None, texts=None, **extra):
        nonlocal seq
        seq += 1
        rec = {"seq": seq, "t": 1.0 + seq, "tool": tool, "peer_uid": 1001, "charges": charges, "args": args or {},
               "status": status, "ms": 5.0, **extra}
        if texts is not None and charges:
            rec["texts_sha256"] = [sha(t) for t in texts]
            full.append({"seq": seq, "t": rec["t"], "tool": tool, "status": status, "probe": (args or {}).get("probe"),
                         "ids": None, "latents": None, "texts": texts, "sha256": rec["texts_sha256"],
                         "logits": [0.5] * len(texts) if tool == "probe_query" and status == "ok" else None})
        log.append(rec)

    call("task_info", {"tool_calls": 1})
    call("sample_texts", {"tool_calls": 1}, args={"probe": 0})
    call("probe_scores", {"tool_calls": 1, "forward": 4}, args={"probe": 0, "ids": [0, 1, 2, 3]})
    if access == "blackbox":
        for i in range(sae_tries):
            call(("probe_gradient", "latent_means")[i % 2], {}, status="error", args={"probe": 0},
                 error="this episode is blackbox: probe_gradient is not available (see help)")
        if sae_tries:
            call("probe_scores", {}, status="error", args={"probe": 0, "ablate": [1]},
                 error="this episode is blackbox: ablate is not available")
    else:
        call("probe_gradient", {"tool_calls": 1}, args={"probe": 0})
        call("latent_means", {"tool_calls": 1, "forward": 1}, args={"texts": {"n": 1, "chars": 10}},
             texts=[AGENT_TEXT + " means"])
    for j, n in enumerate(pq_calls):
        texts = [f"{AGENT_TEXT} {j}.{i}" for i in range(n)]
        call("probe_query", {"tool_calls": 1, "probe_query": n}, args={"probe": 1, "texts": {"n": n, "chars": 99}},
             texts=texts)
    call("probe_query", {}, status="refused", args={"probe": 1, "texts": {"n": 999, "chars": 9}},
         error="budget probe_query exceeded")
    if submitted:
        call("submit", {}, args={"answer": {"sha256": "0" * 64, "chars": 9}})  # refused by the contract: logged ok
        call("submit", {}, args={"answer": {"sha256": "1" * 64, "chars": 99}})
        (d / "submission.json").write_text("{}")
    (d / "log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in log))
    if full:
        (d / "fulltext.jsonl").write_text("".join(json.dumps(r) + "\n" for r in full))
    used = lambda k: sum(r.get("charges", {}).get(k, 0) for r in log if "tool" in r)
    budget = {k: {"used": used(k), "limit": lim, "remaining": lim - used(k)}
              for k, lim in (("tool_calls", 150), ("forward", 3000), ("probe_query", limit))}
    grade = {"score": 0.0, "partial": 0.0, "name": 0.0, "feedback": "no accepted submission", "internal_tool_errors": 0,
             "episode": problem, "reward_scheme": "hard_gated_partial", "access": access,
             "naming_only": access == "blackbox", "budget": budget, "agent_start_time": "2026-11-12T10:00:00",
             "agent_end_time": f"2026-11-12T10:{int(minutes):02d}:00"}
    if submitted:
        ok = bool(name)
        probes = [{"kind": "planted", "pass": True, "bucket": None, "checks": {"identified": True, "no_extra": True,
                                                                               "removal": True, "kept": True}},
                  {"kind": "planted", "pass": ok, "bucket": None if ok else "cue_not_identified",
                   "checks": {"identified": ok, "no_extra": True, "removal": True, "kept": True}},
                  {"kind": "null", "pass": True, "bucket": None, "n_cues": 0}]
        naming = [True, ok, True]
        grade.update(score=1.0 if ok else 0.0, episode_pass=float(ok), partial=1.0, slot_pass=naming, hard_slots=[1],
                     naming_slot_pass=naming, name=float(ok),
                     feedback="episode passed" + (" (naming only)" if access == "blackbox" else ""),
                     details={"format_errors": [], "probes": probes})
    (d / "grade.json").write_text(json.dumps(grade))
    (d / "entrypoint.log").write_text(
        f"Engine: {engine} | Timeout: 5400s | User: model\nstart_toolsrv: tool server ready in 40 s\n"
        + ('Debug: AGENT_CMD=claude -p --output-format stream-json --dangerously-skip-permissions --model '
           '"claude-haiku-5-5" --effort max --verbose < /task.txt\n' if engine == "claude" else
           "Debug: AGENT_CMD=/usr/local/bin/codex-agent.sh /task.txt\n"))
    if engine == "codex":
        (d / "codex_meta.txt").write_text("AGENT_MODEL=gpt-6.1-terra CODEX_EFFORT=max\n")
        (d / "codex_events.jsonl").write_text(json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": tokens, "cached_input_tokens": 0, "output_tokens": tokens // 10}}) + "\n")
        (d / "codex_session_rollout-x.jsonl").write_text(json.dumps({"type": "session_meta", "payload": {
            "cli_version": "0.166.0"}}) + "\n")
        (d / "engine.log").write_text("{}\n")
    else:
        (d / "engine.log").write_text(
            json.dumps({"type": "system", "subtype": "init", "model": "claude-haiku-5-5",
                        "claude_code_version": "2.1.296", "apiKeySource": "ANTHROPIC_API_KEY"}) + "\n"
            + json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3,
                          "total_cost_usd": usd}) + "\n")
        (d / "transcript_s1.jsonl").write_text(json.dumps({"message": {
            "id": "m1", "role": "assistant", "model": "claude-haiku-5-5",
            "usage": {"input_tokens": tokens, "output_tokens": tokens // 10}}}) + "\n")
    if submitted:  # the refusal message reaches the agent's terminal, so it is in the engine log
        with open(d / "engine.log", "a") as f:
            f.write(json.dumps({"type": "user", "tool_result": "probe 0: cue keys must be exactly regex, scope, latents"}) + "\n")
    with open(batch / "launch.log", "a") as f:
        f.write(json.dumps({"t": "2026-11-12T09:59:00Z", "event": "launched", "problem": problem, "running": 1,
                            "resources": "ram_avail=12000MB gpu_used=0MB disk_free=80GB isolated=True paused=False "
                                         "host_containers=0"}) + "\n")
        f.write(json.dumps({"t": "2026-11-12T10:30:00Z", "event": "finished", "problem": problem, "runner_exit": 0,
                            "cid": cid, "usd": usd}) + "\n")
    return d


@pytest.fixture(autouse=True)
def prices(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_PRICES", "1.0,0.05,1.25,5.0")
    monkeypatch.setattr(pc.cr, "BANK", tmp_path / "no_bank")


def checks_of(d):
    r = pc.check_run(d)
    return r, {n: (ok, v) for n, ok, v in r["checks"]}


def rewrite(path, fn):
    """Apply fn to the JSON object (or list of JSON-lines objects) of a file and write it back."""
    if path.suffix == ".jsonl":
        rows = [json.loads(l) for l in path.read_text().splitlines()]
        rows = fn(rows) or rows
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    else:
        obj = json.loads(path.read_text())
        fn(obj)
        path.write_text(json.dumps(obj))


# ---------------------------------------------------------------- consistent runs pass

@pytest.mark.parametrize("problem, engine, arm", [
    ("ep411-open", "codex", "open8"), ("ep411-blackbox", "codex", "bb8"), ("ep411-blackbox64", "codex", "bb64"),
    ("ep472-blackbox", "claude", "bb8"), ("ep411-open64", "codex", "open64"), ("ep472-open", "claude", "open8"),
])
def test_a_consistent_run_passes_every_check(tmp_path, problem, engine, arm):
    r, c = checks_of(make_run(tmp_path, problem, engine))
    assert r["failed"] == [], {n: v for n, v in c.items() if v[0] is False}
    assert (r["arm"], r["problem"], r["engine"], r["name"], r["submitted"]) == (arm, problem, engine, 1, True)
    assert r["agent"] == ("gpt" if engine == "codex" else "haiku")
    assert (r["pq_used"], r["pq_limit"]) == (5, 64 if arm.endswith("64") else 8)
    assert c["pq_accounting"] == (True, f"used 5, full-text log 5 texts, tool-log charges 5, limit {r['pq_limit']}")
    assert c["net_isolation"][0] is True and "isolated=True" in c["net_isolation"][1]
    assert c["submit_refusals"] == (None, "2 submit call(s), 1 refused, cue-keys (latents) message in the transcript: 1")
    assert c["cost"][0] is True
    if arm.startswith("bb"):
        assert r["sae_refused"] == 3 and c["sae_calls"][0] is True and c["prompt_no_sae"][0] is True
        assert "slot_pass == naming_slot_pass: True" in c["naming_keys"][1]
    else:
        assert r["sae_refused"] is None and c["sae_calls"] == (None, "2 SAE-tool or ablate call(s) served")
        assert "prompt_no_sae" not in c
    assert ("Claude Code 2.1.296, effort max" in c["engine"][1]) if engine == "claude" else ("effort max, CLI 0.166.0" in c["engine"][1])


def test_costs_come_from_the_collectors_rules(tmp_path):
    r, c = checks_of(make_run(tmp_path, "ep472-blackbox", "claude", usd=1.2345, tokens=5000))
    assert (r["usd"], r["usd_source"], r["tokens_in"], r["tokens_out"], r["wall_min"]) == (
        1.2345, "claude code total_cost_usd", 5000, 500, 20.0)
    r, c = checks_of(make_run(tmp_path, "ep411-blackbox", "codex", tokens=2_000_000))
    assert (r["usd"], r["usd_source"], r["tokens_in"], r["tokens_out"]) == (3.0, "codex tokens x list price", 2_000_000, 200_000)
    # a batch summary row written at collection time is used when it is there
    d = make_run(tmp_path, "ep411-blackbox64", "codex", cid="feedfeedfeed")
    (d.parent / "summary.jsonl").write_text(json.dumps({
        "cid": "feedfeedfeed", "usd": 9.5, "usd_source": "codex session token_count x list price", "tokens_in": 7,
        "tokens_out": 8, "wall_min": 88.0, "harness_status": "ok", "timeout": True}) + "\n")
    r, c = checks_of(d)
    assert (r["usd"], r["wall_min"]) == (9.5, 88.0) and c["cost"][0] is None  # a fallback source: a note, not a pass
    assert "timeout True" in c["run_status"][1]


@pytest.mark.parametrize("usd, source", [(None, "no usage data"), (float("nan"), "codex tokens x list price"),
                                         (-1.0, "codex tokens x list price"), (True, "codex tokens x list price")])
def test_a_run_without_a_usable_cost_fails_the_cost_check(tmp_path, usd, source):
    d = make_run(tmp_path, "ep411-blackbox", "codex", cid="feedfeedfeed")
    (d.parent / "summary.jsonl").write_text(json.dumps({
        "cid": "feedfeedfeed", "usd": usd, "usd_source": source, "tokens_in": 0, "tokens_out": 0, "wall_min": 12.0,
        "harness_status": "ok", "timeout": False}) + "\n")
    r, c = checks_of(d)
    assert c["cost"][0] is False and "NO usable cost" in c["cost"][1] and r["failed"] == ["cost"]


def test_a_codex_run_whose_usage_was_not_collected_fails_the_cost_check(tmp_path):
    d = make_run(tmp_path, "ep411-blackbox", "codex")
    events = [json.loads(l) for l in (d / "codex_events.jsonl").read_text().splitlines()]
    (d / "codex_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events if e.get("type") != "turn.completed"))
    for p in d.glob("codex_session_*.jsonl"):
        p.unlink()
    r, c = checks_of(d)
    assert (r["usd"], r["usd_source"]) == (None, "no usage data") and c["cost"][0] is False


def test_a_run_without_a_submission_is_checked_without_the_graded_keys(tmp_path):
    r, c = checks_of(make_run(tmp_path, "ep411-blackbox", "codex", submitted=False))
    assert r["failed"] == [] and r["name"] == 0 and r["submitted"] is False
    assert c["naming_keys"] == (True, "name 0.0, naming_only True")
    assert "submitted False" in c["run_status"][1] and c["submit_refusals"][1].startswith("0 submit call(s)")


def test_no_probe_query_and_no_sae_attempt_is_fine(tmp_path):
    r, c = checks_of(make_run(tmp_path, "ep411-blackbox", "codex", pq_calls=(), sae_tries=0))
    assert r["failed"] == [] and r["pq_used"] == 0 and r["sae_refused"] == 0
    assert not (tmp_path / "r1112_pilot_gpt_bb8" / r["run"] / "fulltext.jsonl").exists()  # nothing charged, no file
    assert c["fulltext"][1].startswith("0 record(s)")


# ---------------------------------------------------------------- each broken thing fails its own check

def _drop_fulltext_record(rows):
    return rows[:-1]


def _serve_sae(rows):
    r = next(x for x in rows if x.get("tool") == "probe_gradient")
    r.update(status="ok", charges={"tool_calls": 1})


TAMPER = [
    ("prompt_budget", "ep411-blackbox64", "codex", lambda d: (d / "task.txt").write_text(
        (d / "task.txt").read_text().replace("64 texts for", "8 texts for")), []),
    ("prompt_help", "ep411-blackbox", "codex", lambda d: (d / "task.txt").write_text(
        (d / "task.txt").read_text().replace("Budget counters. Free.", "Budget counters.")), []),
    ("prompt_help", "ep411-blackbox", "codex", lambda d: (d / "task.txt").write_text(
        (d / "task.txt").read_text() + pc.help_text("blackbox")), []),
    ("prompt_help", "ep411-blackbox", "codex", lambda d: (d / "task.txt").write_text(
        (d / "task.txt").read_text().replace(pc.help_text("blackbox"), pc.help_text("open"))), ["prompt_no_sae"]),
    ("prompt_no_sae", "ep411-blackbox", "codex", lambda d: (d / "task.txt").write_text(
        (d / "task.txt").read_text() + "Use latent_means on your texts.\n"), []),
    ("engine", "ep411-blackbox", "codex", lambda d: (d / "codex_meta.txt").write_text(
        "AGENT_MODEL=gpt-6.1-terra CODEX_EFFORT=xhigh\n"), []),
    ("engine", "ep411-blackbox", "codex", lambda d: (d / "codex_meta.txt").write_text(
        "AGENT_MODEL=gpt-6.1 CODEX_EFFORT=max\n"), []),
    ("engine", "ep411-blackbox", "codex", lambda d: (d / "codex_session_rollout-x.jsonl").write_text(
        json.dumps({"type": "session_meta", "payload": {"cli_version": "0.170.0"}}) + "\n"), []),
    ("engine", "ep472-blackbox", "claude", lambda d: (d / "engine.log").write_text(
        (d / "engine.log").read_text().replace("2.1.296", "2.1.179")), []),
    ("engine", "ep472-blackbox", "claude", lambda d: (d / "entrypoint.log").write_text(
        (d / "entrypoint.log").read_text().replace("--effort max", "--effort high")), []),
    ("sae_calls", "ep411-blackbox", "codex", lambda d: rewrite(d / "log.jsonl", _serve_sae), ["charges"]),
    ("pq_accounting", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "grade.json", lambda g: g["budget"]["probe_query"].update(used=4)), []),
    ("pq_accounting", "ep411-blackbox", "codex", lambda d: rewrite(d / "fulltext.jsonl", _drop_fulltext_record),
     ["fulltext"]),
    ("pq_accounting", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "grade.json", lambda g: g["budget"]["probe_query"].update(used=5, limit=4)), ["budget_limit", "name"]),
    ("charges", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "grade.json", lambda g: g["budget"]["forward"].update(used=5)), []),
    ("fulltext", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "fulltext.jsonl", lambda rows: rows[0]["texts"].__setitem__(0, "another text")), []),
    ("fulltext", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "log.jsonl", lambda rows: [r for r in rows if r.get("texts_sha256")][0]["texts_sha256"].__setitem__(0, "0" * 64)), []),
    ("fulltext", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "fulltext.jsonl", lambda rows: rows[0].update(logits=[0.5])), []),
    ("fulltext", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "fulltext.jsonl", lambda rows: rows + [{"event": "fulltext capped", "t": 1, "seq": 99, "bytes": 1}]), []),
    ("fulltext", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "log.jsonl", lambda rows: rows[2].update(fulltext_error="OSError: disk full")), []),
    ("files", "ep411-blackbox", "codex", lambda d: (d / "fulltext.jsonl").unlink(), ["pq_accounting", "fulltext"]),
    ("files", "ep472-blackbox", "claude", lambda d: (d / "transcript_s1.jsonl").unlink(), []),
    ("naming_keys", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(naming_only=False)), []),
    ("naming_keys", "ep411-open", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(naming_only=True)), []),
    ("naming_keys", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.pop("naming_slot_pass")), []),
    ("naming_keys", "ep411-blackbox", "codex", lambda d: rewrite(
        d / "grade.json", lambda g: g.update(slot_pass=[True, False, True])), []),
    ("naming_keys", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.pop("name")), ["name"]),
    ("name", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(name=0.0)), []),
    ("episode_id", "ep411-blackbox", "codex", lambda d: (d / "episode_id").write_text("ep411-blackbox64\n"),
     ["prompt_budget", "budget_limit", "name"]),
    ("episode_id", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(episode="ep411")), []),
    ("access", "ep411-blackbox", "codex", lambda d: rewrite(d / "task_public.json", lambda t: t.update(access="open")), []),
    ("budget_limit", "ep411-blackbox64", "codex", lambda d: rewrite(
        d / "task_public.json", lambda t: t["budgets"].update(probe_query=8)), []),
    ("run_status", "ep411-blackbox", "codex", lambda d: (d / "codex_events.jsonl").write_text(
        (d / "codex_events.jsonl").read_text() + json.dumps({"type": "turn.failed"}) + "\n"), []),
    ("run_status", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(internal_tool_errors=2)), []),
    ("run_status", "ep411-blackbox", "codex", lambda d: rewrite(d / "grade.json", lambda g: g.update(daemon_died=True)), []),
    ("net_isolation", "ep411-blackbox", "codex", lambda d: (d.parent / "launch.log").write_text(
        (d.parent / "launch.log").read_text().replace("isolated=True", "isolated=False")), []),
    ("cost", "ep411-blackbox", "codex", lambda d: __import__("os").environ.pop("OPENAI_PRICES"), []),
]


@pytest.mark.parametrize("name, problem, engine, tamper, also", TAMPER,
                         ids=[f"{i:02d}-{t[0]}" for i, t in enumerate(TAMPER)])
def test_each_inconsistency_fails_its_check(tmp_path, name, problem, engine, tamper, also):
    d = make_run(tmp_path, problem, engine)
    assert pc.check_run(d)["failed"] == []
    tamper(d)
    r, c = checks_of(d)
    assert c[name][0] is False, c[name]
    assert set(r["failed"]) == {name, *also}, {n: c[n] for n in r["failed"]}


def test_a_missing_launch_log_is_a_note_not_a_failure(tmp_path):
    d = make_run(tmp_path)
    (d.parent / "launch.log").unlink()
    r, c = checks_of(d)
    assert c["net_isolation"][0] is None and r["failed"] == []


def test_the_schedulers_child_log_is_read_for_the_isolation_reading(tmp_path):
    d = make_run(tmp_path)
    (d.parent / "launch.log").rename(d.parent / "launch_sched_pilots_o003_a1.log")
    assert checks_of(d)[1]["net_isolation"][0] is True


# ---------------------------------------------------------------- report

def four_pilots(tmp_path):
    return [make_run(tmp_path, "ep411-open", "codex", cid="111111111111", usd=0.6, minutes=15, tokens=1_000_000),
            make_run(tmp_path, "ep411-blackbox", "codex", cid="222222222222", usd=0.5, minutes=12, tokens=800_000),
            make_run(tmp_path, "ep411-blackbox64", "codex", cid="333333333333", usd=1.5, minutes=30, tokens=2_400_000,
                     pq_calls=(32, 20)),
            make_run(tmp_path, "ep472-blackbox", "claude", cid="444444444444", usd=1.1, minutes=22)]


def test_ratios_of_bb64_bb8_and_open8_per_agent(tmp_path):
    runs = [pc.check_run(d) for d in four_pilots(tmp_path)]
    rat = {(x["agent"], x["ratio"]): x for x in pc.ratios(runs)}
    assert set(rat) == {("gpt", "bb64 / bb8"), ("gpt", "bb64 / open8"), ("gpt", "bb8 / open8")}  # Haiku has one arm
    assert rat[("gpt", "bb64 / bb8")]["tokens"] == 3.0 and rat[("gpt", "bb64 / bb8")]["wall_min"] == 2.5
    assert rat[("gpt", "bb64 / open8")]["tokens"] == 2.4 and rat[("gpt", "bb8 / open8")]["wall_min"] == 0.8
    assert rat[("gpt", "bb64 / bb8")]["usd"] == 3.0  # codex cost is tokens x price here


def test_main_prints_tables_without_agent_text_and_exits_by_result(tmp_path, capsys):
    dirs = four_pilots(tmp_path)
    md, js = tmp_path / "out" / "pilot_check.md", tmp_path / "out" / "pilot_check.json"
    assert pc.main([str(d) for d in dirs] + ["--md", str(md), "--json", str(js)]) == 0
    out = capsys.readouterr().out
    assert out == md.read_text() and "4 run(s); 0 with a failed check." in out
    assert "ZEBRA" not in out and "ZEBRA" not in js.read_text()
    assert "| gpt | bb64 / bb8 |" in out and "## r1112_pilot_haiku_bb8/444444444444: ep472-blackbox" in out
    assert "| r1112_pilot_gpt_bb64/333333333333 | ep411-blackbox64 | bb64 | gpt | 1 | True | 52 / 64 | 3 |" in out
    for line in out.splitlines():  # every table row has the columns of its header
        if line.startswith("| ") and " | ok | " in line or " | FAIL | " in line:
            assert line.count("|") == 4
    assert len(json.loads(js.read_text())["runs"]) == 4
    # a batch directory stands for its runs; one broken run makes the exit code 1
    (dirs[1] / "codex_meta.txt").write_text("AGENT_MODEL=gpt-6.1-terra CODEX_EFFORT=xhigh\n")
    assert pc.main([str(dirs[0].parent), str(dirs[1].parent)]) == 1
    out = capsys.readouterr().out
    assert "2 run(s); 1 with a failed check." in out and "| engine | FAIL |" in out
    assert pc.main([str(tmp_path / "nowhere")]) == 2
    (tmp_path / "empty").mkdir()
    assert pc.main([str(tmp_path / "empty")]) == 2
