"""scripts/blackbox_image_check.py: the host-side judgments (check_problem, check_oracles) on synthetic
observations. Every check must pass on a consistent set and fail when the thing it is about is broken; no
docker, no GPU."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("blackbox_image_check_under_test",
                                              ROOT / "scripts" / "blackbox_image_check.py")
ic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ic)

OPEN_HELP = ("ShiftHunt tools. Usage: tool <name>\n" + "x" * 600 + "\nprobe_gradient probe\nlatent_means texts\n"
             "latent_tokens latents\nlatent_examples latents\nprobe_scores probe [ids] [ablate]\n"
             "Access: open. latent_means and latent_tokens accept your own texts as well as sample notes.\n")
BB_HELP = ("ShiftHunt tools. Usage: tool <name>\n" + "x" * 600 + "\nprobe_scores probe [ids]\n"
           "Access: blackbox. This episode has no SAE tools; your own texts go to probe_query.\n")
BUDGETS = {"tool_calls": 150, "forward": 3000, "wall_clock_s": 3600, "call_timeout_s": 180}


def prompt(access, limit):
    sae = "" if access == "blackbox" else "A sparse autoencoder; mean-ablating the union of all latents.\n"
    return (f"# Task\n{sae}## Tools\n{BB_HELP if access == 'blackbox' else OPEN_HELP}\n## Budget\nPer episode: 150 "
            f"tool calls, {limit} texts for `probe_query` in total, and 60 minutes.\n")


def obs(problem, image=None, basic=False):
    """A consistent observation of `problem`, as the in-container part reports it."""
    image = image or ic.IMAGE
    ep, _, suffix = problem.partition("-")
    access, limit = ic.ARMS[suffix]
    blackbox = access == "blackbox"
    task = {"access": access, "budgets": {**BUDGETS, "probe_query": limit}, "n_probes": 4, "k": 16}
    used = {"tool_calls": 1, "forward": 0, "probe_query": 0}
    calls = []

    def add(label, exit_, dt=None, error=None):
        nonlocal used
        used = {k: used[k] + (dt or {}).get(k, 0) for k in used}
        calls.append({"label": label, "exit": exit_, "used": dict(used), "error": error, "seconds": 0.1})

    add("sample_texts", 0, {"tool_calls": 1})
    if not basic:
        for s in ic.SAE_CALLS:
            if blackbox:
                add(s, 1, None, "this episode is blackbox: ablate is not available" if s.endswith("ablate")
                    else f"this episode is blackbox: {s} is not available (see help)")
            else:
                add(s, 0, {"tool_calls": 1, "forward": 1})
    add("probe_scores", 0, {"tool_calls": 1, "forward": 128})
    add("probe_query", 0, {"tool_calls": 1, "probe_query": 1})
    o = {"problem": problem, "image": image, "container_exit": 0, "container_seconds": 60.0,
         "task_py": {"exit": 0, "seconds": 40.0}, "episode_id": problem + "\n", "task_txt": prompt(access, limit),
         "task_json_public": task, "task_json_episode": copy.deepcopy(task), "task_json_same": True,
         "help": {"exit": 0, "text": BB_HELP if blackbox else OPEN_HELP},
         "task_info": {"exit": 0, "access": access, "budgets": task["budgets"], "n_probes": 4},
         "budget": {"tool_calls": {"used": 1, "limit": 150}, "forward": {"used": 0, "limit": 3000},
                    "probe_query": {"used": 0, "limit": limit, "remaining": limit}},
         "used_start": {"tool_calls": 1, "forward": 0, "probe_query": 0}, "calls": calls,
         "probe_scores_logits": [0.5, -1.25, 2.0], "probe_query_logits": [1.885]}
    if not basic:
        add("probe_query_over", 1, None, "budget probe_query exceeded")
        add("probe_query_fill", 0, {"tool_calls": 1, "probe_query": limit - 1})
        add("probe_query_past", 1, None, "budget probe_query exceeded")
        o["fill_texts"] = limit - 1
        o["fulltext"] = {"file": {"mode": "0o600", "owner": "toolsrv"}, "dir": {"mode": "0o700", "owner": "toolsrv"},
                         "model_cat_exit": 1, "model_ls_exit": 2, "records": 2, "tools": ["probe_query"],
                         "texts": limit, "has_own_text": True, "sha_ok": True, "log_hashes_same": True,
                         "probe_query_logits_logged": True}
    return o


def world(ep="ep411"):
    peers = {(ic.BASE_IMAGE, f"{ep}-open"): obs(f"{ep}-open", ic.BASE_IMAGE, basic=True)}
    for arm in ic.ARMS:
        peers[(ic.IMAGE, f"{ep}-{arm}")] = obs(f"{ep}-{arm}")
    return peers


EXPECTED = {
    "open": {"setup", "help_in_prompt", "budget_agrees", "access", "other_budgets_unchanged", "works",
             "sae_tools_work", "prompt_has_sae", "same_as_r1103", "budget_enforced", "fulltext"},
    "open64": {"setup", "help_in_prompt", "budget_agrees", "access", "other_budgets_unchanged", "works",
               "sae_tools_work", "prompt_has_sae", "same_as_open", "budget_enforced", "fulltext"},
    "blackbox": {"setup", "help_in_prompt", "budget_agrees", "access", "other_budgets_unchanged", "works",
                 "refusals", "prompt_no_sae", "budget_enforced", "fulltext"},
    "blackbox64": {"setup", "help_in_prompt", "budget_agrees", "access", "other_budgets_unchanged", "works",
                   "refusals", "prompt_no_sae", "same_as_blackbox", "budget_enforced", "fulltext"},
}


@pytest.mark.parametrize("arm", list(ic.ARMS))
def test_consistent_observations_pass_every_check(arm):
    peers = world()
    checks = ic.check_problem(peers[(ic.IMAGE, f"ep411-{arm}")], peers)
    assert set(checks) == EXPECTED[arm] and all(checks.values()), checks


def only_fails(arm, mutate, expect, peer=None):
    peers = world()
    target = peers[peer or (ic.IMAGE, f"ep411-{arm}")]
    mutate(target)
    checks = ic.check_problem(peers[(ic.IMAGE, f"ep411-{arm}")], peers)
    failed = {k for k, v in checks.items() if not v}
    assert failed == set(expect), (failed, expect)


def set_call(label, **kw):
    def mutate(o):
        for c in o["calls"]:
            if c["label"] == label:
                c.update(kw)
    return mutate


def charge(label, key="tool_calls"):
    """The call `label` (and everything after it) charged one more than it should."""
    def mutate(o):
        seen = False
        for c in o["calls"]:
            seen = seen or c["label"] == label
            if seen:
                c["used"][key] += 1
    return mutate


def test_setup_and_help_failures():
    only_fails("blackbox", lambda o: o.update(episode_id="ep411-open\n"), ["setup"])
    only_fails("blackbox", lambda o: o["task_py"].update(exit=1), ["setup"])
    only_fails("blackbox", lambda o: o.update(container_exit=137), ["setup"])
    only_fails("blackbox", lambda o: o.update(task_txt=o["task_txt"] + "left $tools_md\n"), ["setup"])
    # the prompt embeds a different help than `tool help` prints
    only_fails("blackbox", lambda o: o["help"].update(text=o["help"]["text"].replace("xxx", "xyx", 1)),
               ["help_in_prompt"])
    only_fails("open", lambda o: o["help"].update(text=o["help"]["text"].replace("xxx", "xyx", 1)),
               ["help_in_prompt", "same_as_r1103"])
    # the help's access line is another mode's
    def wrong_access_line(o):
        new = o["help"]["text"].replace("Access: blackbox.", "Access: open.")
        o["task_txt"] = o["task_txt"].replace(o["help"]["text"], new)
        o["help"]["text"] = new
    only_fails("blackbox", wrong_access_line, ["help_in_prompt"])


@pytest.mark.parametrize("where", ["prompt", "public", "episode", "task_info", "budget"])
def test_budget_disagreement_is_caught_wherever_it_is(where):
    def mutate(o):
        if where == "prompt":
            o["task_txt"] = ic.with_budget(o["task_txt"], 8)
        elif where == "public":
            o["task_json_public"]["budgets"]["probe_query"] = 8
        elif where == "episode":
            o["task_json_episode"]["budgets"]["probe_query"] = 8
        elif where == "task_info":
            o["task_info"]["budgets"] = {**o["task_info"]["budgets"], "probe_query": 8}
        else:
            o["budget"]["probe_query"]["limit"] = 8
    peers = world()
    o = peers[(ic.IMAGE, "ep411-blackbox64")]
    mutate(o)
    failed = {k for k, v in ic.check_problem(o, peers).items() if not v}
    assert "budget_agrees" in failed and failed <= {"budget_agrees", "same_as_blackbox", "budget_enforced"}


def test_access_and_other_budgets():
    only_fails("blackbox", lambda o: o["task_info"].update(access="open"), ["access"])
    only_fails("blackbox", lambda o: o["task_json_public"].update(access="open"), ["access"])
    only_fails("blackbox64", lambda o: o["task_info"].update(budgets={**o["task_info"]["budgets"], "forward": 1}),
               ["other_budgets_unchanged"])


@pytest.mark.parametrize("tool", ic.SAE_CALLS)
def test_blackbox_refusals(tool):
    only_fails("blackbox", set_call(tool, exit=0, error=None), ["refusals"])          # the tool worked
    only_fails("blackbox", charge(tool), ["refusals"])                                # refused but charged
    only_fails("blackbox", charge(tool, "forward"), ["refusals"])                     # forward units charged
    only_fails("blackbox", set_call(tool, error="unknown tool; call help for the list"), ["refusals"])
    only_fails("open", set_call(tool, exit=1, error="internal error"), ["sae_tools_work"])


def test_blackbox_prompt_must_not_name_sae_tools_and_open_prompt_must():
    def leak(o):
        o["task_txt"] = o["task_txt"].replace("## Budget", "use latent_examples\n## Budget")
    only_fails("blackbox", leak, ["prompt_no_sae"])
    only_fails("open64", lambda o: o.update(task_txt=o["task_txt"].replace("mean-ablating", "removing")
                                            .replace("[ablate]", "")), ["prompt_has_sae", "help_in_prompt",
                                                                        "same_as_open"])


def test_open_must_match_the_main_study_image():
    base = (ic.BASE_IMAGE, "ep411-open")
    only_fails("open", lambda o: o.update(task_txt=o["task_txt"].replace("# Task", "# Task ")), ["same_as_r1103"],
               peer=base)
    only_fails("open", lambda o: o["help"].update(text=o["help"]["text"] + " "), ["same_as_r1103"], peer=base)
    only_fails("open", lambda o: o.update(probe_scores_logits=[0.5, -1.25, 2.1]), ["same_as_r1103"], peer=base)
    only_fails("open", lambda o: o.update(probe_query_logits=None), ["same_as_r1103"], peer=base)
    peers = world()
    del peers[(ic.BASE_IMAGE, "ep411-open")]                                           # no baseline: cannot pass
    checks = ic.check_problem(peers[(ic.IMAGE, "ep411-open")], peers)
    assert checks["same_as_r1103"] is False and "other_budgets_unchanged" not in checks
    peers = world()
    peers[(ic.BASE_IMAGE, "ep411-open")]["probe_scores_logits"] = [0.5 + 5e-4, -1.25, 2.0]  # GPU float noise is fine
    assert ic.check_problem(peers[(ic.IMAGE, "ep411-open")], peers)["same_as_r1103"] is True


def test_64_arms_differ_from_their_8_twin_only_in_the_number():
    only_fails("open64", lambda o: o.update(task_txt=o["task_txt"].replace("60 minutes", "61 minutes")),
               ["same_as_open"])
    only_fails("blackbox64", lambda o: o.update(task_txt=o["task_txt"].replace("60 minutes", "61 minutes")),
               ["same_as_blackbox"])
    # an "open64" whose prompt still says 8 is identical to its twin: both checks object
    only_fails("open64", lambda o: o.update(task_txt=ic.with_budget(o["task_txt"], 8)), ["same_as_open",
                                                                                         "budget_agrees"])
    assert ic.with_budget(prompt("open", 8), 64) == prompt("open", 64)


def test_working_calls_and_their_charges():
    only_fails("blackbox", set_call("probe_scores", exit=1), ["works"])
    only_fails("blackbox", set_call("sample_texts", exit=2), ["works"])
    def free_query(o):                                     # probe_query answered without charging a text
        for c in o["calls"]:
            if c["label"] in ("probe_query", "probe_query_over"):
                c["used"]["probe_query"] -= 1
    only_fails("blackbox", free_query, ["works"])


def test_budget_enforcement():
    only_fails("blackbox", set_call("probe_query_over", exit=0, error=None), ["budget_enforced"])
    only_fails("blackbox64", charge("probe_query_over", "probe_query"), ["budget_enforced"])
    only_fails("blackbox", set_call("probe_query_past", exit=0, error=None), ["budget_enforced"])
    only_fails("open", set_call("probe_query_fill", exit=1), ["budget_enforced"])
    def no_fill(o):
        o["calls"] = [c for c in o["calls"] if c["label"] != "probe_query_fill"]
    only_fails("open64", no_fill, ["budget_enforced"])


@pytest.mark.parametrize("key, value", [
    ("file", {"mode": "0o644", "owner": "toolsrv"}), ("file", None), ("dir", {"mode": "0o755", "owner": "toolsrv"}),
    ("model_cat_exit", 0), ("model_ls_exit", 0), ("has_own_text", False), ("sha_ok", False),
    ("log_hashes_same", False), ("probe_query_logits_logged", False), ("texts", 3), ("tools", [])])
def test_fulltext_log(key, value):
    only_fails("blackbox", lambda o: o["fulltext"].update({key: value}), ["fulltext"])
    only_fails("open64", lambda o: o["fulltext"].update({key: value}), ["fulltext"])


def test_public_obs_has_no_prompt_help_or_logit_values():
    o = obs("ep472-blackbox64")
    o["log_rows"] = [{"tool": "probe_query", "status": "ok", "charges": {}},
                     {"tool": "probe_gradient", "status": "error", "charges": {}},
                     {"tool": "probe_gradient", "status": "error", "charges": {}}]
    pub = ic.public_obs(o)
    text = json.dumps(pub)
    assert "ShiftHunt tools" not in text and "Per episode" not in text and "1.885" not in text
    assert pub["task_txt"]["sha256"] == ic.sha(o["task_txt"]) and pub["task_txt"]["probe_query_numbers"] == ["64"]
    assert pub["help"]["last_line"].startswith("Access: blackbox.")
    assert pub["log_status_counts"] == {"probe_query:ok": 1, "probe_gradient:error": 2}
    assert pub["probe_scores_logits"]["n"] == 3


# ---------------------------------------------------------------- oracle runs

OLD_KEYS = ["access", "agent_end_time", "budget", "daemon_stop", "details", "episode", "episode_pass", "feedback",
            "hard_slots", "partial", "reward_scheme", "score", "slot_pass", "tool_calls_logged"]


def orun(image, problem, attack=None):
    """A consistent oracle run, as inner_oracle reports it."""
    blackbox, base = "blackbox" in problem, image == ic.BASE_IMAGE
    none = attack == "none-all"
    buckets = (["planted_none"] * 3 if none else ["removal_short"] * 3 if blackbox else [None] * 3) + [None]
    naming = [not none] * 3 + [True]
    slot = naming if blackbox else [b is None for b in buckets]
    score = 0.0 if none else 1.0
    res = {"problem": problem, "attack": attack, "task_py": {"exit": 0, "tail": "ready"}, "substrate": "templated",
           "n_probes": 4, "latents_submitted": 0 if blackbox or none else 36,
           "incomplete_submit": {"exit": 1, "refused": True}, "submit": {"exit": 0, "accepted": True},
           "after_submit_call_exit": 1, "grader": {"exit": 0, "tail": ""},
           "grade_keys": sorted(OLD_KEYS + ([] if base else list(ic.NAMING_KEYS))),
           "grade": {"score": score, "episode_pass": score, "partial": 0.0 if blackbox or none else 1.0,
                     "name": None if base else (0.0 if none else 1.0), "naming_only": None if base else blackbox,
                     "access": "blackbox" if blackbox else "open", "episode": problem,
                     "reward_scheme": "hard_gated_partial", "daemon_stop": "terminated"},
           "naming_only_in_feedback": blackbox,
           "private": {"slot_pass": slot, "naming_slot_pass": None if base else naming, "hard_slots": [1],
                       "feedback": "episode ...", "buckets": buckets, "kinds": ["planted"] * 3 + ["null"],
                       "margins": [None if none else 0.0789, None if none else 0.1722, None if none else 0.1476, None],
                       "kept": [None if none else 0.9859, None if none else 0.9844, None if none else 0.9976, None],
                       "checks": [None] * 4}}
    return {"image": image, "problem": problem, "attack": attack, "exit": 0, "seconds": 70.0, "result": res}


def oracle_world():
    return [orun(i, p, a) for i, p, a in ic.oracle_jobs(ic.IMAGE, ("ep411", "ep472"))]


def oracle_failures(runs):
    return [name for name, ok, _ in ic.check_oracles(runs) if not ok]


def find(runs, image, problem, attack=None):
    return [r for r in runs if (r["image"], r["problem"], r["attack"]) == (image, problem, attack)][0]["result"]


def test_oracle_jobs_cover_every_item_in_open_and_blackbox():
    jobs = ic.oracle_jobs(ic.IMAGE, ic.ITEMS)
    for ep in ic.ITEMS:
        assert (ic.BASE_IMAGE, f"{ep}-open", None) in jobs and (ic.IMAGE, f"{ep}-open", None) in jobs
        assert sum(1 for i, p, a in jobs if i == ic.IMAGE and p.startswith(f"{ep}-blackbox") and a is None) == 1
    assert {p.partition("-")[2] for i, p, a in jobs if "blackbox" in p and a is None} == {"blackbox", "blackbox64"}
    assert sorted(p for i, p, a in jobs if a == "none-all") == ["ep411-blackbox", "ep476-open64"]
    assert len(jobs) == 20 and all(i == ic.IMAGE for i, p, a in jobs if "blackbox" in p or "64" in p)


def test_oracle_checks_pass_on_consistent_runs():
    out = ic.check_oracles(oracle_world())
    assert len(out) == 2 + 2 * 2 + 2 * 2 + 2 * 2 and all(ok for _, ok, _ in out), [o for o in out if not o[1]]
    assert not any("planted" in d or "removal" in d for _, _, d in out)      # details are totals only


@pytest.mark.parametrize("mutate, n_fail, where", [
    (lambda w: find(w, ic.IMAGE, "ep411-open")["grade"].update(name=None), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["grade_keys"].remove("naming_slot_pass"), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["grade_keys"].append("extra_key"), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["grade_keys"].remove("feedback"), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["private"]["margins"].__setitem__(0, 0.09), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep472-open")["private"].update(feedback="episode other"), 1, "ep472-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["grade"].update(naming_only=True), 1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-open")["private"].update(naming_slot_pass=[True, False, True, True]), 1,
     "ep411-open"),
    # the same imperfect grade in both images is equal but not a full pass
    (lambda w: [find(w, i, "ep411-open")["grade"].update(score=0.75, episode_pass=0.0) for i in (ic.IMAGE,
                                                                                               ic.BASE_IMAGE)],
     1, "ep411-open"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["grade"].update(naming_only=False), 1, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["grade"].update(name=0.0), 1, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox").update(naming_only_in_feedback=False), 1, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox").update(latents_submitted=3), 1, "ep411-blackbox"),
    # blackbox scored with the latent checks: slot_pass is not the naming grade
    (lambda w: find(w, ic.IMAGE, "ep472-blackbox64")["private"].update(slot_pass=[False] * 3 + [True]), 1,
     "ep472-blackbox64"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox", "none-all")["grade"].update(name=1.0), 1, "attack=none-all"),
    (lambda w: find(w, ic.IMAGE, "ep472-open64", "none-all")["grade"].update(score=0.25), 1, "attack=none-all"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["submit"].update(accepted=False), 2, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["incomplete_submit"].update(refused=False), 2, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["grader"].update(exit=1), 2, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox").update(after_submit_call_exit=0), 2, "ep411-blackbox"),
    (lambda w: find(w, ic.IMAGE, "ep411-blackbox")["grade"].update(episode="ep411-open"), 2, "ep411-blackbox"),
    (lambda w: find(w, ic.BASE_IMAGE, "ep472-open")["grader"].update(exit=1), 1, "r1103 ep472-open"),
])
def test_oracle_checks_fail_when_the_grade_is_wrong(mutate, n_fail, where):
    runs = oracle_world()
    mutate(runs)
    failed = oracle_failures(runs)
    assert len(failed) == n_fail and all(where in f for f in failed), failed


def test_oracle_without_output_or_baseline_cannot_pass():
    runs = oracle_world()
    find_run = [r for r in runs if (r["image"], r["problem"]) == (ic.IMAGE, "ep411-blackbox") and not r["attack"]][0]
    find_run.update(result={}, exit=1, output_tail="Traceback ... KeyError: 'some_cue'")
    assert len(oracle_failures(runs)) == 2
    pub = ic.public_oracle(find_run)
    assert "some_cue" not in json.dumps(pub) and pub["printed_json"] is False
    runs = [r for r in oracle_world() if r["image"] != ic.BASE_IMAGE]
    assert len(oracle_failures(runs)) == 2                                             # both open oracles


def test_public_oracle_drops_the_per_probe_part():
    run = orun(ic.IMAGE, "ep411-blackbox", "none-all")
    text = json.dumps(ic.public_oracle(run))
    assert "planted" not in text and "buckets" not in text and "kinds" not in text and '"tail"' not in text
    assert ic.public_oracle(run)["result"]["grade"]["name"] == 0.0
    pub = ic.public_oracle(orun(ic.IMAGE, "ep411-open"))
    assert pub["result"]["latents_submitted"] is True and "36" not in json.dumps(pub)
    assert not any("36" in d for _, _, d in ic.check_oracles(oracle_world()))


def test_markdown_report_has_the_tables_and_no_prompt_text():
    peers = world("ep411")
    rows = [{"problem": p, "seconds": 60.0, "checks": ic.check_problem(o, peers)}
            for (image, p), o in peers.items() if image == ic.IMAGE]
    rows[0]["checks"]["fulltext"] = False
    rep = {"image_name": ic.IMAGE, "base_image_name": ic.BASE_IMAGE, "quick": True, "started": "t0", "finished": "t1",
           "gpu_minutes": 9.5, "command": "python scripts/blackbox_image_check.py --quick",
           "image": {"id": "sha256:aa", "created": "now", "layers": 52, "labels": {"shifthunt.commit": "c" * 40}},
           "base_image": {"id": "sha256:bb", "created": "then", "layers": 46, "labels": {}},
           "files_changed": {"/task.py": {"sha256": "1" * 64, "owner": "root:root", "mode": "700",
                                          "base_sha256": "2" * 64}},
           "files_compared": 61, "files_meta_diff": 0, "problems": rows,
           "observations": [ic.public_obs(o) for o in peers.values()], "oracle_checks": ic.check_oracles(oracle_world()),
           "log_status_counts": {"probe_gradient:error": 4}, "failures": ["ep411-open: fulltext"],
           "n_checks": 50, "n_pass": 49, "ok": False}
    md = ic.markdown(rep)
    assert "**Result: FAIL** (49 of 50 checks pass)" in md and "**FAIL**" in md and "| ep411-blackbox64 |" in md
    assert "`shifthunt.commit=" + "c" * 40 + "`" in md and "| `/task.py` | root:root | 700 |" in md
    assert "oracle r1112 ep411-blackbox attack=none-all: name 0.0 and score 0 | pass" in md
    assert "planted" not in md and "removal_short" not in md
    assert "Per episode" not in md and "sparse autoencoder" not in md
