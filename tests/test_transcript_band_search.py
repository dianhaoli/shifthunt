"""scripts/transcript_band_search.py on small synthetic transcripts of both formats (Claude Code JSONL, Codex
exec event stream, and the Codex session-file fallback). Episode ids are made up (ep903, ep904); kinds are
patched in.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import score_naming as SN  # noqa: E402
import transcript_band_search as TB  # noqa: E402

PROMPT = "A main cue moves the logit by at least 0.3 topic units; every other property by at most 0.15."


@pytest.fixture(autouse=True)
def _kinds(monkeypatch):
    monkeypatch.setitem(SN.KIND_BY_EPISODE, "ep903", "trap")
    monkeypatch.setitem(SN.KIND_BY_EPISODE, "ep904", "twopart")


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows))


def grade(hard_pass):
    rec = {"kind": "planted", "pass": hard_pass, "bucket": None if hard_pass else "cue_not_identified",
           "checks": {"identified": hard_pass, "no_extra": True, "removal": True, "kept": True}}
    return {"details": {"probes": [rec, {"kind": "null", "pass": True, "bucket": None}]}, "hard_slots": [0]}


def make_run(batch_dir, cid, episode, model, hard_pass, files):
    d = Path(batch_dir) / cid
    d.mkdir(parents=True)
    (d / "grade.json").write_text(json.dumps(grade(hard_pass)))
    (d / "episode_id").write_text(episode)
    for name, rows in files.items():
        write_jsonl(d / name, rows)
    with open(Path(batch_dir) / "summary.jsonl", "a") as f:
        f.write(json.dumps({"cid": cid, "model": model}) + "\n")
    return d


def claude_rows():
    a = lambda *items: {"type": "assistant", "message": {"role": "assistant", "content": list(items)}}
    u = lambda *items: {"type": "user", "message": {"role": "user", "content": list(items)}}
    tool = lambda cmd, i: {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": cmd}}
    res = lambda text, i: {"type": "tool_result", "tool_use_id": f"t{i}", "content": text}
    return [
        {"type": "user", "message": {"role": "user", "content": PROMPT}},
        a({"type": "thinking", "thinking": ""}, {"type": "text", "text": "Let me read the SAE view first."}),
        a(tool("tool latent_means probe=0", 1)),
        u(res("weekday ratio 0.22 (topic units); error term 0.4", 1)),
        a({"type": "text", "text": "The weekday effect ratio is 0.22, which is between 0.15 and 0.3: ambiguous, "
                                   "the SAE under-reads it. The proxy is off by a scale. Test it on true logits."}),
        a(tool("tool probe_query '{\"probe\": 0, \"texts\": [\"Mon note\", \"note\"]}'  # weekday flip", 2)),
        u(res('{"logits": [1.2, -0.3]}', 2)),
        a({"type": "text", "text": "The contract rules out a band reading, so weekday is the main."}),
    ]


def codex_events(followup=True):
    item = lambda **kw: {"type": "item.completed", "item": kw}
    rows = [{"type": "thread.started", "thread_id": "x"}, {"type": "turn.started"},
            item(id="i0", type="reasoning", text="**Reading the gap**\n\nThe hashtag topic ratio of .18 sits in the "
                                                 "gap; the reconstruction misses part of it."),
            item(id="i1", type="command_execution", command="bash -lc 'tool latent_means probe=1'",
                 aggregated_output="ratio 0.2 threshold", exit_code=0, status="completed")]
    rows += [item(id=f"c{i}", type="command_execution", command=f"bash -lc 'echo {i}'", aggregated_output="",
                  exit_code=0, status="completed") for i in range(3)]
    if followup:
        rows.append(item(id="i9", type="command_execution", command="bash -lc 'tool probe_query probe=1 texts=[...]'",
                         aggregated_output="{}", exit_code=0, status="completed"))
    rows += [item(id="m", type="agent_message", text="Done; submitted."), {"type": "turn.completed", "usage": {}}]
    return rows


def codex_session():
    ri = lambda p: {"timestamp": "t", "type": "response_item", "payload": p}
    return [{"type": "session_meta", "payload": {}},
            ri({"type": "message", "role": "user", "content": [{"type": "input_text", "text": PROMPT}]}),
            ri({"type": "reasoning", "summary": [{"type": "summary_text", "text": "Effect 0.25 is ambiguous."}]}),
            ri({"type": "function_call", "name": "shell", "call_id": "c1",
                "arguments": json.dumps({"command": ["bash", "-lc", "tool probe_query probe=2 texts=[]"]})}),
            ri({"type": "function_call_output", "call_id": "c1", "output": "{\"logits\": []}"}),
            ri({"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "ok"}]})]


@pytest.fixture
def raw(tmp_path):
    r = tmp_path / "raw"
    make_run(r / "r1103_opus_b1", "run0000000c1", "ep903", "claude-opus-5-5", True,
             {"transcript_main.jsonl": claude_rows()})
    make_run(r / "r1112_gpt_bb8", "run0000000x1", "ep903-blackbox", "gpt-6.1-terra", False,
             {"codex_events.jsonl": codex_events(followup=True)})
    make_run(r / "r1112_gpt_bb8", "run0000000x2", "ep903-blackbox", "gpt-6.1-terra", True,
             {"codex_events.jsonl": codex_events(followup=False)})
    make_run(r / "r1112_gpt_open8", "run0000000s1", "ep903-open", "gpt-6.1-terra", False,
             {"codex_events.jsonl": [{"type": "turn.started"}], "codex_session_a.jsonl": codex_session()})
    make_run(r / "r1112_gpt_open8", "run0000000t1", "ep904-open", "gpt-6.1-terra", True,
             {"codex_events.jsonl": codex_events()})     # not a trap item: never read
    return r


def test_blocks_and_roles_of_both_formats(raw):
    eng, b = TB.run_blocks(raw / "r1103_opus_b1" / "run0000000c1")
    assert eng == "claude"
    assert [x["role"] for x in b][:4] == ["prompt", "assistant_thinking", "assistant_text", "tool_input"]
    assert b[4]["role"] == "tool_output" and "weekday ratio" in b[4]["text"]
    assert [x["turn"] for x in b] == list(range(len(b)))
    eng, b = TB.run_blocks(raw / "r1112_gpt_bb8" / "run0000000x1")
    assert eng == "codex" and b[0]["role"] == "assistant_thinking"
    assert [x["role"] for x in b[1:3]] == ["tool_input", "tool_output"] and b[-1]["role"] == "assistant_text"
    eng, b = TB.run_blocks(raw / "r1112_gpt_open8" / "run0000000s1")    # no items in the stream: session files
    assert eng == "codex" and [x["role"] for x in b] == ["prompt", "assistant_thinking", "tool_input",
                                                          "tool_output", "assistant_text"]
    assert "probe_query probe=2" in b[2]["text"]


def test_frozen_patterns_count_per_role_and_skip_the_prompt(raw):
    _, b = TB.run_blocks(raw / "r1103_opus_b1" / "run0000000c1")
    counts, hits = TB.frozen_counts(b)
    assert counts[r"0\.15"]["prompt"] == 1 and counts[r"0\.15"]["reasoning"] == 1
    assert counts[r"0\.3"]["reasoning"] == 1 and counts[r"at least 0\.3"]["prompt"] == 1
    assert counts[r"at least 0\.3"]["reasoning"] == 0
    assert counts[r"rules? out"]["reasoning"] == 1 and counts["contract"]["reasoning"] == 1
    assert counts["band"]["reasoning"] == 1 and counts["error term"]["tool_output"] == 1
    assert counts[r"proxy.*(scale|gap|off)"]["reasoning"] == 1
    assert all(TB.FROZEN[h["pattern"]].flags & 2 for h in hits)          # re.I on every pattern
    assert TB.FROZEN["band"].search("BAND") and TB.FROZEN["gap"].search("Gap")


def test_band_hits_contexts_and_follow_up(raw):
    _, b = TB.run_blocks(raw / "r1103_opus_b1" / "run0000000c1")
    hits = TB.band_hits(b)
    reasoning = [h for h in hits if h["role"] in TB.REASONING]
    tool = [h for h in hits if h["role"] == "tool_output"]
    assert tool and tool[0]["match"] == "0.22"
    assert {h["kind"] for h in reasoning} == {"numeric", "phrase"}
    h = next(h for h in reasoning if h["match"] == "0.22")
    ctx = TB.context(b[h["turn"]], h["start"], h["end"])
    assert "between 0.15 and 0.3" in ctx and len(ctx) <= len(b[h["turn"]]["text"])
    cat, props, probes = TB.categorize(h, b)
    assert cat == "followed_up" and "weekday" in props
    # Codex: a property is named in the context, and the probe_query 5 calls later does not name it (nor does
    # any prose in between): a probe_query within N, not shown to be on that property -> "other"
    _, b = TB.run_blocks(raw / "r1112_gpt_bb8" / "run0000000x1")
    h = next(h for h in TB.band_hits(b) if h["role"] == "assistant_thinking" and h["kind"] == "numeric")
    assert h["match"] == ".18"
    assert TB.categorize(h, b)[0] == "followed_up_other"
    assert TB.categorize(h, b, n_calls=3)[0] == "not_followed_up"
    _, b = TB.run_blocks(raw / "r1112_gpt_bb8" / "run0000000x2")
    h = next(h for h in TB.band_hits(b) if h["role"] == "assistant_thinking" and h["kind"] == "numeric")
    assert TB.categorize(h, b)[0] == "not_followed_up"
    _, b = TB.run_blocks(raw / "r1112_gpt_open8" / "run0000000s1")   # neither a property nor a probe named
    h = next(h for h in TB.band_hits(b) if h["role"] == "assistant_thinking")
    assert TB.categorize(h, b)[0] == "followed_up_other"


def test_numeric_window_needs_a_keyword_and_the_range():
    blocks = [{"turn": 0, "role": "assistant_text", "text": "x = 0.2 and later the score was 0.95.", "file": "f",
               "line": 1},
              {"turn": 1, "role": "assistant_text", "text": "threshold 0.31 vs ratio 0.30 and 0.15", "file": "f",
               "line": 2}]
    got = [(h["turn"], h["match"]) for h in TB.band_hits(blocks)]
    assert got == [(1, "0.30"), (1, "0.15")]


def test_main_writes_counts_only_and_private_contexts(raw, tmp_path):
    pub, priv = tmp_path / "pub", tmp_path / "priv"
    assert TB.main(["--raw", str(raw), "--select", "any", "--out", str(pub), "--private-out", str(priv)]) == 0
    md = (pub / "transcript_band.md").read_text()
    js = json.loads((pub / "transcript_band.json").read_text())
    assert js["runs"] == 4                                                   # the two-part run is not read
    assert TB.privacy_problems(md) == [] and TB.privacy_problems(json.dumps(js)) == []
    for word in ("weekday", "hashtag", "run0000", "ep903", "between 0.15 and 0.3"):
        assert word not in md and word not in json.dumps(js)
    g = js["groups"]
    assert g["main|opus"]["all"]["runs"] == 1 and g["main|opus"]["pass"]["runs"] == 1
    assert g["main|opus"]["all"]["band_run_category"]["followed_up"] == 1
    assert g["bb8|gpt"]["fail"]["band_run_category"]["followed_up_other"] == 1
    assert g["bb8|gpt"]["pass"]["band_run_category"]["not_followed_up"] == 1
    assert g["all|all"]["all"]["frozen"]["gap"]["runs_with_reasoning_hit"] == 2
    assert g["main|opus"]["all"]["frozen"][r"0\.15"]["hits_prompt"] == 1
    hits = [json.loads(x) for x in (priv / "band_hits.jsonl").read_text().splitlines()]
    assert any(h["context"] and "weekday" in h["context"] for h in hits)
    assert {h["role"] for h in hits} >= {"assistant_text", "tool_output"}
    assert all(h["category"] == "not_reasoning" for h in hits if not h["reasoning"])
    with pytest.raises(ValueError):
        TB.write_tracked(pub, {"x.md": "weekday 3"})
    with pytest.raises(SystemExit):
        TB.main(["--raw", str(raw), "--select", "any", "--out", str(pub),
                 "--private-out", str(ROOT / "results" / "blackbox_1112")])
