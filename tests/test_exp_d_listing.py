"""scripts/exp_d_listing.py (Exp D, listing screen) against a local stub HTTP server.

No network and no paid call: every request goes to an http.server on 127.0.0.1 in a thread, the API keys are
made-up strings, and nothing is written outside pytest's tmp_path.
"""
import csv
import io
import json
import os
import random
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import exp_d_listing as exp  # noqa: E402
import textonly_client as tc  # noqa: E402
from shifthunt import contract  # noqa: E402
from shifthunt import freetext as ft  # noqa: E402
from shifthunt import freetext_listing as fl  # noqa: E402
from shifthunt.grader import balanced_accuracy  # noqa: E402
from shifthunt.regex_sandbox import run_regex  # noqa: E402

CURLY = "’"
BIG = {"anthropic": 1000.0, "openai": 1000.0}
TOPICS = ["pottery", "cycling"]
# The template as the work-package spec gives it (plan §6 Exp D); the committed file must be exactly this.
TEMPLATE = (
    "Below are 128 short notes, each with a label (0 or 1). The label is the note's topic: label 0 notes are about\n"
    "{topic0} and label 1 notes are about {topic1}. In this sample, some other property of the text (not the\n"
    "topic) also agrees with the label: it is present in the notes of one label and absent from the notes of the\n"
    "other.\n"
    "\n"
    "List up to 20 candidate properties of the text, other than the topic, that could be what agrees with the\n"
    "label, ordered from most to least likely. For each candidate give a Python regular expression that detects\n"
    "the property (it is used as re.search(regex, text) with no flags; inline flags such as (?i) are allowed; at\n"
    "most 200 characters) and a scope: \"any\" (the whole note), \"first_line\" (the text before the first newline)\n"
    "or \"last_line\" (the text after the last newline).\n"
    "\n"
    "Answer with one JSON array and nothing else:\n"
    "[{\"property\": \"<short description>\", \"regex\": \"<regex>\", \"scope\": \"any\"}, ...]\n"
    "The answer is JSON, so a backslash in a regex is written \\\\ inside a JSON string.\n"
    "\n"
    "{sample}\n"
)
# What the stub "models" answer: both cues of the round-trip test, in several spellings, plus two bad candidates.
CANDIDATES = [
    {"property": "curly apostrophe", "regex": CURLY, "scope": "any"},
    {"property": "two spaces after a sentence", "regex": r"\.  \S", "scope": "any"},
    {"property": "curly apostrophe, written as a regex escape", "regex": r"’"},
    {"property": "two spaces", "regex": "  ", "scope": "any"},
    {"property": "unknown scope", "regex": "x", "scope": "body"},
    {"property": "broken pattern", "regex": "(", "scope": "any"},
]
ARRAY = json.dumps(CANDIDATES, ensure_ascii=False)
ANSWERS = {      # one answer layout per model
    "claude-opus-5-5": ARRAY,
    "claude-sonnet-5-5": ("Here are my candidates [most likely first]:\n```json\n"
                          + json.dumps(CANDIDATES, indent=2, ensure_ascii=False) + "\n```\n"),
    "claude-haiku-5-5": json.dumps(CANDIDATES),      # ASCII: the apostrophe is the JSON escape ’
    "gpt-6.1-terra": "Sure.\n\n" + ARRAY + "\n\nThe first one is the likeliest.",
}


def reply_for(answers):
    def reply(path, body):
        request = json.loads(body)
        model = request["model"]
        text = answers[model] if isinstance(answers, dict) else answers
        if path == "/v1/messages":
            response = {"id": "msg_1", "type": "message", "role": "assistant", "model": model,
                        "content": [{"type": "thinking", "thinking": "hidden [1]", "signature": "sig"},
                                    {"type": "text", "text": text}],
                        "stop_reason": "end_turn", "stop_details": None,
                        "usage": {"input_tokens": 15000, "output_tokens": 900}}
        else:
            response = {"id": "resp_1", "object": "response", "status": "completed", "incomplete_details": None,
                        "model": model + "-2026-10-01",
                        "output": [{"type": "reasoning", "id": "rs_1", "summary": []},
                                   {"type": "message", "role": "assistant",
                                    "content": [{"type": "output_text", "text": text, "annotations": []}]}],
                        "usage": {"input_tokens": 15000, "input_tokens_details": {"cached_tokens": 0},
                                  "output_tokens": 900, "output_tokens_details": {"reasoning_tokens": 300}}}
        # half the replies carry raw UTF-8, half ASCII escapes: the stored bytes must be whatever was sent
        return 200, json.dumps(response, ensure_ascii=(model == "claude-opus-5-5")).encode("utf-8")
    return reply


class Stub:
    """Records every request (path, body bytes) and every reply's bytes."""

    def __init__(self, reply):
        stub = self
        self.lock, self.requests, self.replies, self.reply = threading.Lock(), [], [], reply

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                status, data = stub.reply(self.path, body)
                with stub.lock:
                    stub.requests.append((self.path, body))
                    stub.replies.append(data)
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("request-id", "req_stub")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, args=(0.01,), daemon=True).start()
        url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.base_urls = {"anthropic": url, "openai": url}

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stub():
    s = Stub(reply_for(ANSWERS))
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-SECRETKEY-123")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oai-test-SECRETKEY-456")
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(tc, "BACKOFF_BASE_S", 0.001)


def small_build(out, cues=("curly_apostrophe", "double_space"), reps=1, **kw):
    kw.setdefault("n_heldout", 512)
    kw.setdefault("n_grid", 256)
    return exp.build(out, cues=list(cues), reps=reps, **kw)


def send(stub, priv, pub, **kw):
    kw.setdefault("budget_usd", BIG)
    kw.setdefault("workers", 1)
    kw.setdefault("require_committed", False)
    return exp.run(priv, pub, base_urls=stub.base_urls, **kw)


def answer(*candidates):
    return json.dumps(list(candidates), ensure_ascii=False)


def cand(regex, scope="any", **kw):
    return {"property": "p", "regex": regex, "scope": scope, **kw}


def negated(pattern):
    """A regex that matches exactly the notes `pattern` does not match (leading global flags kept local)."""
    m = re.match(r"\(\?([a-z]+)\)", pattern)
    flags, rest = (m.group(1), pattern[m.end():]) if m else ("", pattern)
    return rf"\A(?![\s\S]*(?{flags}:{rest}))"


def test_the_script_does_not_import_torch():
    code = ("import sys; sys.path.insert(0, 'scripts'); import exp_d_listing; "
            "print(int('torch' in sys.modules or 'transformers' in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.stdout.strip() == "0", out.stderr


# ---------------------------------------------------------------- the prompt
def test_committed_template_is_the_spec_text_and_is_what_build_uses(tmp_path):
    assert exp.TEMPLATE == ROOT / "results" / "blackbox_1112" / "exp_d" / "prompt_template.txt"
    assert exp.TEMPLATE.read_bytes() == TEMPLATE.encode("utf-8")
    assert exp.load_template() == TEMPLATE
    manifest = small_build(tmp_path, cues=["weekday"], n_heldout=256, n_grid=64)
    assert manifest["template_sha256"] == exp.sha256(TEMPLATE.encode("utf-8"))
    sample = json.loads((tmp_path / "samples" / "weekday_1.json").read_text(encoding="utf-8"))
    want = (TEMPLATE.replace("{topic0}", sample["topics"][0]).replace("{topic1}", sample["topics"][1])
            .replace("{sample}", exp.sample_block(sample["items"])))
    calls = tc.read_calls(tmp_path / "calls.jsonl")
    assert [c["prompt"] for c in calls] == [want] * 4
    assert want.startswith("Below are 128 short notes") and want.endswith("\n  ]\n}\n")
    assert f"label 0 notes are about\n{sample['topics'][0]} and label 1 notes are about {sample['topics'][1]}." in want
    assert "{topic" not in want and "{sample}" not in want
    assert "written \\\\ inside a JSON string" in want


def test_template_slots_are_checked(tmp_path):
    bad = tmp_path / "t.txt"
    bad.write_text(TEMPLATE.replace("{topic1}", "{topic0}"), encoding="utf-8")
    with pytest.raises(SystemExit):
        exp.load_template(bad)


def test_sample_block_is_what_the_tool_prints():
    sample = exp.make_sample("curly_apostrophe", 1)
    items = sample["items"]
    assert len(items) == exp.N_SAMPLE == 128 and [it["id"] for it in items] == list(range(128))
    assert sum(it["label"] for it in items) == 64
    assert [it["label"] for it in items] != [0, 1] * 64                     # shuffled, as sample_notes does
    block = exp.sample_block(items)
    # the server sends one JSON line with ensure_ascii=False; the client parses it and prints pretty(reply)
    line = json.dumps({"total": 128, "texts": items}, ensure_ascii=False)
    assert block == exp._toolclient().pretty(json.loads(line))
    assert block.startswith('{\n  "total": 128,\n  "texts": [\n    {\n      "id": 0,\n      "label": ')
    assert json.loads(block) == {"total": 128, "texts": items}
    assert CURLY in block and "\\u2019" not in block                        # the glyph, never its escape
    assert all(json.dumps(it["text"], ensure_ascii=False) in block for it in items)
    assert "\\n" in block and block.count("\n") == 2 + 5 * 128 + 2          # note newlines are the two characters \n


def test_sample_follows_the_documented_seed_scheme():
    rng = random.Random("expd:sample:digits:3")
    sign = rng.choice((1, -1))
    topics = rng.sample(list(fl.TOPIC_NAMES), 2)
    texts, labels, flags = fl.sample_texts(rng, topics, 128, None, {"digits": sign})
    order = list(range(128))
    rng.shuffle(order)
    sample = exp.make_sample("digits", 3)
    assert (sample["sign"], sample["topics"]) == (sign, topics)
    assert [it["text"] for it in sample["items"]] == [texts[j] for j in order]
    assert [it["label"] for it in sample["items"]] == [int(labels[j]) for j in order]
    assert sample["flags"]["digits"] == [int(flags["digits"][j]) for j in order]
    for it, flag in zip(sample["items"], sample["flags"]["digits"]):       # exactly aligned, and visible in the text
        assert flag == (it["label"] if sign > 0 else 1 - it["label"]) == int(bool(re.search(r"\d", it["text"])))
    held = exp.make_heldout("digits", 3, topics, n=64)
    ref = fl.sample_grid(random.Random("expd:heldout:digits:3"), topics, 64, None, mains=[])
    assert held["texts"] == ref[0] and held["seed"] == "expd:heldout:digits:3" and held["mains"] == []
    grid = exp.make_grid("digits", 3, topics, n=64)
    ref = fl.sample_grid(random.Random("expd:grid:digits:3"), topics, 64, None, mains=["digits"])
    assert grid["texts"] == ref[0] and grid["flags"]["digits"] == "".join(map(str, ref[2]["digits"].tolist()))
    assert grid["mains"] == ["digits"] and grid["held_off"] == [] and held["held_off"] == []


def test_the_ps_tentative_grid_holds_the_question_ps_off():
    assert exp.GRID_HELD_OFF == {"ps_tentative": ["ps_question"]}
    grid = exp.make_grid("ps_tentative", 2, TOPICS, n=512)
    ref = fl.sample_grid(random.Random("expd:grid:ps_tentative:2"), TOPICS, 512, None, mains=["ps_tentative"],
                         held_off=["ps_question"])
    assert grid["texts"] == ref[0] and grid["mains"] == ["ps_tentative"] and grid["held_off"] == ["ps_question"]
    flags = exp.flag_arrays(grid)
    main, ps = flags["ps_tentative"], flags["postscript"]
    assert main.sum() == 256 and not flags["ps_question"].any()
    assert ps[main].all() and abs(ps[~main].mean() - 0.5) < 0.1      # the parent: on with the child, else a coin
    last = [t.split("\n")[-1].lower() for t in grid["texts"]]
    assert all((x in [s.lower() for s in fl.PS_TENTATIVE]) == bool(m) for x, m in zip(last, main))
    assert all((x in [s.lower() for s in ft.PS_STATEMENTS]) == bool(p and not m) for x, p, m in zip(last, ps, main))
    # the other children's grids are plain sample_grid(mains=[cue]); ps_question's keeps the tentative coin
    grid = exp.make_grid("ps_question", 2, TOPICS, n=512)
    ref = fl.sample_grid(random.Random("expd:grid:ps_question:2"), TOPICS, 512, None, mains=["ps_question"])
    assert grid["texts"] == ref[0] and grid["held_off"] == [] and exp.flag_arrays(grid)["ps_tentative"].any()


def test_planned_calls_are_400_distinct_ids():
    assert exp.MODELS == ["gpt-6.1-terra", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
    assert set(exp.MODELS) == set(tc.PROVIDER)
    assert len(exp.CUES) == 20 and exp.REPS == 5 and len(exp.PLAIN_EXISTING) == 13
    assert exp.MAX_REGEX == contract.MAX_REGEX and exp.MAX_CANDIDATES == 20
    ids = [exp.call_id(c, r, m) for c in exp.CUES for r in range(1, 6) for m in exp.MODELS]
    assert len(set(ids)) == 400
    for cid in ids:
        assert tc.CALL_ID.fullmatch(cid)
    parsed = [exp.CALL_ID.fullmatch(cid).groups() for cid in ids]
    assert parsed == [(c, str(r), m) for c in exp.CUES for r in range(1, 6) for m in exp.MODELS]
    assert exp.call_id("signoff_excl", 2, "gpt-6.1-terra") == "D_signoff_excl_2_gpt-6.1-terra"


def test_build_is_deterministic(tmp_path):
    a = small_build(tmp_path / "a", cues=["weekday", "ps_tentative"], reps=2, n_heldout=256, n_grid=64)
    b = small_build(tmp_path / "b", cues=["weekday", "ps_tentative"], reps=2, n_heldout=256, n_grid=64)
    assert a == b and a["n_calls"] == 16 and len(a["samples"]) == 4
    assert a["grid_held_off"] == {"ps_tentative": ["ps_question"]}
    files = sorted(p.relative_to(tmp_path / "a") for p in (tmp_path / "a").rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(tmp_path / "b") for p in (tmp_path / "b").rglob("*") if p.is_file())
    assert {str(f) for f in files} == {"calls.jsonl", "manifest.json"} | {
        f"{d}/{c}_{r}.json" for d in ("samples", "heldout", "grid") for c in ("weekday", "ps_tentative")
        for r in (1, 2)}
    for f in files:
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes(), f
    calls = exp.read_built_calls(tmp_path / "a")
    assert [c["call_id"] for c in calls] == [exp.call_id(c, r, m) for c in ("weekday", "ps_tentative")
                                             for r in (1, 2) for m in exp.MODELS]
    for s in a["samples"]:      # the manifest's hashes are those of the files, and the four models share a prompt
        name = f"{s['cue']}_{s['rep']}.json"
        assert exp.sha256((tmp_path / "a" / "heldout" / name).read_bytes()) == s["heldout_sha256"]
        prompts = {c["prompt"] for c in calls if c["call_id"].startswith(f"D_{s['cue']}_{s['rep']}_")}
        assert len(prompts) == 1 and exp.sha256(prompts.pop().encode("utf-8")) == s["prompt_sha256"]
    assert len({s["prompt_sha256"] for s in a["samples"]}) == 4          # a fresh draw per prompt
    held = json.loads((tmp_path / "a" / "heldout" / "weekday_1.json").read_text(encoding="utf-8"))
    assert len(held["texts"]) == 256 and set(held["flags"]) == set(exp.CUES)
    assert held["topics"] == a["samples"][0]["topics"]


def test_a_changed_calls_file_is_refused(tmp_path):
    small_build(tmp_path, cues=["weekday"], n_heldout=256, n_grid=64)
    with open(tmp_path / "calls.jsonl", "ab") as f:
        f.write(b"\n")
    with pytest.raises(SystemExit):
        exp.read_built_calls(tmp_path)


# ---------------------------------------------------------------- the byte round trip
def test_curly_apostrophes_and_double_spaces_round_trip_byte_for_byte(tmp_path, stub):
    """prompt builder -> calls.jsonl -> request bytes -> stored response -> extracted answer -> regex -> run_regex."""
    priv, pub = tmp_path / "priv", tmp_path / "pub"
    manifest = small_build(priv)
    samples = {s["cue"]: json.loads((priv / "samples" / f"{s['cue']}_1.json").read_text(encoding="utf-8"))
               for s in manifest["samples"]}
    for cue, glyph in (("curly_apostrophe", CURLY), ("double_space", "  ")):
        flags = samples[cue]["flags"][cue]
        assert [glyph in it["text"] for it in samples[cue]["items"]] == [bool(f) for f in flags]
        assert sum(flags) == 64

    # prompt builder -> calls.jsonl: raw UTF-8 glyphs and double spaces, no escapes
    raw_calls = (priv / "calls.jsonl").read_bytes()
    assert CURLY.encode("utf-8") in raw_calls and b"\\u2019" not in raw_calls and b".  " in raw_calls
    calls = {c["call_id"]: c for c in tc.read_calls(priv / "calls.jsonl")}
    assert len(calls) == 8
    for cue, sample in samples.items():
        prompt = exp.build_prompt(TEMPLATE, sample["topics"], sample["items"])
        assert all(calls[exp.call_id(cue, 1, m)]["prompt"] == prompt for m in exp.MODELS)

    rows = send(stub, priv, pub)
    assert [r["status"] for r in rows] == ["ok"] * 8 and len(stub.requests) == 8
    sent = {json.loads(body)["model"] + "|" + exp.sha256(body): (path, body) for path, body in stub.requests}
    replies = {exp.sha256(data) for data in stub.replies}
    for cue, sample in samples.items():
        texts = [it["text"] for it in sample["items"]]
        prefix = TEMPLATE.split("{sample}")[0].replace("{topic0}", sample["topics"][0]).replace(
            "{topic1}", sample["topics"][1])
        for model in exp.MODELS:
            cid = exp.call_id(cue, 1, model)
            # calls.jsonl -> request bytes: what is on disk is what the server received
            request = (priv / "raw" / f"{cid}.request.json").read_bytes()
            path, body = sent[model + "|" + exp.sha256(request)]
            assert body == request and request == tc.build_request(model, calls[cid]["prompt"])
            parsed = json.loads(request)
            content = parsed["messages"][0]["content"] if path == "/v1/messages" else parsed["input"]
            assert content == calls[cid]["prompt"] and content.startswith(prefix)
            # the notes inside the request are the generator's notes, character for character
            assert [it["text"] for it in json.loads(content[len(prefix):])["texts"]] == texts
            # stored response: the bytes the server sent
            response = (priv / "raw" / f"{cid}.response.json").read_bytes()
            assert exp.sha256(response) in replies
            meta = json.loads((priv / "raw" / f"{cid}.meta.json").read_bytes())
            assert meta["request_sha256"] == exp.sha256(request) and meta["response_sha256"] == exp.sha256(response)
            # stored response -> extracted answer -> candidates
            text = tc.extract_answer(tc.PROVIDER[model], json.loads(response))
            assert text == ANSWERS[model]
            assert exp.extract_candidates(text) == CANDIDATES
            # regex -> run_regex on the notes taken from the request bytes
            notes = [it["text"] for it in json.loads(content[len(prefix):])["texts"]]
            for item in CANDIDATES[:4]:
                target = "curly_apostrophe" if "curly" in item["property"] else "double_space"
                match, error = run_regex(item["regex"], item.get("scope", "any"), notes)
                assert error is None
                assert match == [bool(f) for f in sample["flags"][target]], (cid, item)
                assert sum(match) == 64 if target == cue else 0 < sum(match) < 128

    # the tracked manifest: hashes only
    lines = [json.loads(x) for x in (pub / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["call_id"] for r in lines] == sorted(calls)
    for r in lines:
        assert set(r) == {"call_id", "model", "request_sha256", "response_sha256", "status", "usd"}
        assert r["request_sha256"] == exp.sha256((priv / "raw" / f"{r['call_id']}.request.json").read_bytes())
        assert r["response_sha256"] == exp.sha256((priv / "raw" / f"{r['call_id']}.response.json").read_bytes())
        assert r["status"] == "ok" and r["usd"] > 0
    assert CURLY not in (pub / "manifest.jsonl").read_text(encoding="utf-8")

    # resume: nothing is sent twice
    assert [r["status"] for r in send(stub, priv, pub)] == ["ok"] * 8 and len(stub.requests) == 8

    # score: both cues are listed by all four answer layouts, under both rules
    scored = exp.score(priv)
    assert [r["call_id"] for r in scored] == list(calls) and all(r["outcome"] == "scored" for r in scored)
    for r in scored:
        assert r["n_given"] == r["n_kept"] == 6 and r["n_invalid"] == 1 and r["n_regex_error"] == 1
        assert r["primary"]["listed"] and r["sensitivity"]["listed"]
        assert r["primary"]["best_ba"] == 1.0 and r["sensitivity"]["best_ba"] == 1.0
        assert r["primary"]["rank"] == r["sensitivity"]["rank"] == (1 if r["cue"] == "curly_apostrophe" else 2)
        assert r["primary"]["n_offtarget"] == 2
        other = "double_space" if r["cue"] == "curly_apostrophe" else "curly_apostrophe"
        assert r["primary"]["offtarget_cues"] == [other]
        assert [c["invalid"] for c in r["candidates"]] == [None, None, None, None, "unknown_scope", None]
        assert r["candidates"][5]["error"] == "exit:1" and r["candidates"][5]["ba_sensitivity"] == 0.5
        assert r["usd"] > 0 and r["status"] == "ok"
    assert exp.read_scores(priv / "scores.jsonl") == json.loads(json.dumps(scored))

    # table: the public files hold no model text
    summary = exp.table(priv / "scores.jsonl", pub)
    assert summary["n_planned"] == summary["n_stored"] == 8 and summary["outcomes"] == {"scored": 8}
    assert summary["by_cue"]["double_space"]["primary"] == {"k": 4, "n": 4, "rate": 1.0, "wilson95": [0.5101, 1.0]}
    for name in ("README.md", "exp_d.json", "per_call.csv"):
        text = (pub / name).read_text(encoding="utf-8")
        assert "two spaces after a sentence" not in text and CURLY not in text and r"\S" not in text


def test_run_selects_models_and_limit_and_logs_the_command(tmp_path, stub):
    priv, pub = tmp_path / "priv", tmp_path / "pub"
    manifest = small_build(priv, n_heldout=256, n_grid=64)
    rows = send(stub, priv, pub, models=["claude-haiku-5-5", "gpt-6.1-terra"], limit=3,
                command=["python", "scripts/exp_d_listing.py", "run", "--limit", "3"])
    assert [r["call_id"] for r in rows] == sorted([
        "D_curly_apostrophe_1_gpt-6.1-terra", "D_curly_apostrophe_1_claude-haiku-5-5",
        "D_double_space_1_gpt-6.1-terra"])
    assert len(stub.requests) == 3
    log = (pub / "COMMANDS.md").read_text(encoding="utf-8")
    assert "scripts/exp_d_listing.py run --limit 3" in log and manifest["calls_sha256"] in log
    assert f"prompt_template.txt sha256={manifest['template_sha256']}" in log and "(8 built, 3 selected)" in log
    assert (priv / "raw" / "COMMANDS.log").exists()
    assert len((pub / "manifest.jsonl").read_text().splitlines()) == 3
    with pytest.raises(SystemExit):
        send(stub, priv, pub, models=["gpt-4"])
    # a provider without a budget gets nothing (the two GPT calls are stored already)
    rows = send(stub, priv, pub, budget_usd={"openai": 1000.0})
    assert sum(r["status"] == "not_sent_budget" for r in rows) == 5 and len(stub.requests) == 3
    assert len((pub / "manifest.jsonl").read_text().splitlines()) == 3      # only stored calls are in the manifest
    # the scorer sees the calls that were never stored
    scored = exp.score(priv)
    assert sum(r["outcome"] == exp.NOT_STORED for r in scored) == 5
    assert all(not r["primary"]["listed"] for r in scored if r["outcome"] == exp.NOT_STORED)


def test_run_refuses_an_uncommitted_or_different_template(tmp_path, stub, monkeypatch):
    priv, pub = tmp_path / "priv", tmp_path / "pub"
    small_build(priv, cues=["weekday"], n_heldout=256, n_grid=64)
    monkeypatch.setattr(exp, "committed", lambda path: None)
    with pytest.raises(SystemExit, match="committed"):
        exp.run(priv, pub, budget_usd=BIG, base_urls=stub.base_urls)
    assert not stub.requests and not (priv / "raw").exists()
    monkeypatch.setattr(exp, "committed", lambda path: "0123abc")
    other = tmp_path / "other.txt"
    other.write_text(TEMPLATE.replace("Below are", "Here are"), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the template"):
        exp.run(priv, pub, budget_usd=BIG, base_urls=stub.base_urls, template_path=other)
    assert not stub.requests
    rows = exp.run(priv, pub, budget_usd=BIG, base_urls=stub.base_urls, workers=1, limit=1)
    assert [r["status"] for r in rows] == ["ok"] and len(stub.requests) == 1


def test_cli_run_score_table(tmp_path, stub, monkeypatch, capsys):
    priv, pub = tmp_path / "priv", tmp_path / "pub"
    small_build(priv, n_heldout=256, n_grid=64)
    monkeypatch.setattr(exp, "committed", lambda path: "0123abc")
    common = ["--out", str(priv), "--pub", str(pub)]
    assert exp.main(["run", *common, "--budget-usd", "anthropic=1000", "--budget-usd", "openai=1000",
                     "--workers", "1"], base_urls=stub.base_urls) == 0
    assert len(stub.requests) == 8
    assert exp.main(["score", *common]) == 0
    assert "scored 8" in capsys.readouterr().out
    assert exp.main(["table", *common, "--main-plain", "40/40", "--main-twopart", "13/18",
                     "--main-source", "results/x.json at commit abc"]) == 0
    readme = (pub / "README.md").read_text(encoding="utf-8")
    assert "40/40 [0.91, 1.00] (plain slots)" in readme and "13/18 [0.49, 0.88] (two-part child)" in readme
    assert "results/x.json at commit abc" in readme
    assert (pub / "COMMANDS.md").read_text(encoding="utf-8").count("\n- ") == 3
    with pytest.raises(SystemExit):
        exp.main(["table", *common, "--main-plain", "40/40"])
    assert exp.main(["estimate", "--out", str(priv)]) == 0
    assert "expected USD" in capsys.readouterr().out


def test_statuses_other_than_ok_are_not_scored(tmp_path):
    answers = {"claude-opus-5-5": "I cannot see a pattern.", "claude-sonnet-5-5": answer(cand("  ")),
               "claude-haiku-5-5": answer(cand("  ")), "gpt-6.1-terra": answer(cand("  "))}
    base = reply_for(answers)

    def reply(path, body):
        status, data = base(path, body)
        response = json.loads(data)
        if response["model"] == "claude-sonnet-5-5":
            response["stop_reason"] = "refusal"
        if response["model"] == "claude-haiku-5-5":
            response["stop_reason"] = "max_tokens"
        return status, json.dumps(response).encode()

    s = Stub(reply)
    try:
        priv, pub = tmp_path / "priv", tmp_path / "pub"
        small_build(priv, cues=["double_space"], n_heldout=256, n_grid=64)
        send(s, priv, pub)
        assert len(s.requests) == 4
        send(s, priv, pub)
        assert len(s.requests) == 4                       # a stored 200 is never sent again, whatever its answer
    finally:
        s.close()
    rows = {r["model"]: r for r in exp.score(priv)}
    assert {m: r["outcome"] for m, r in rows.items()} == {
        "gpt-6.1-terra": "scored", "claude-opus-5-5": "parse_failure", "claude-sonnet-5-5": "refusal",
        "claude-haiku-5-5": "max_tokens"}
    assert [rows[m]["primary"]["listed"] for m in exp.MODELS] == [True, False, False, False]
    summary = exp.table(priv / "scores.jsonl", pub)
    assert summary["by_cue"]["double_space"]["primary"]["k"] == 1 and summary["by_cue"]["double_space"]["n"] == 4
    assert summary["not_scored"] == [
        {"call_id": "D_double_space_1_claude-opus-5-5", "outcome": "parse_failure"},
        {"call_id": "D_double_space_1_claude-sonnet-5-5", "outcome": "refusal"},
        {"call_id": "D_double_space_1_claude-haiku-5-5", "outcome": "max_tokens"}]
    readme = (pub / "README.md").read_text(encoding="utf-8")
    assert "- D_double_space_1_claude-sonnet-5-5: refusal" in readme and "parse_failure 1" in readme


def test_a_lone_surrogate_in_an_answer_does_not_stop_the_scoring(tmp_path):
    """A model that writes \\uD83C with a single backslash inside its JSON answer (valid text, valid JSON) gives a
    regex or a description with a lone surrogate, which cannot be encoded as UTF-8."""
    text = ('[{"property": "emoji \\uD83D", "regex": "[\\uD83C-\\uDBFF][\\uDC00-\\uDFFF]", "scope": "any"}, '
            '{"property": "odd", "regex": "\\uD800"}, {"property": "two spaces", "regex": "  ", "scope": "any"}]')
    assert "\\uD83C" in text and "\\\\u" not in text and text.isascii()
    text.encode("utf-8")                                                   # the answer itself is fine
    items = exp.extract_candidates(text)
    assert [len(c["regex"]) for c in items] == [10, 1, 2] and items[1]["regex"] == "\ud800"
    with pytest.raises(UnicodeEncodeError):
        items[0]["property"].encode("utf-8")
    s = Stub(reply_for(text))
    try:
        priv, pub = tmp_path / "priv", tmp_path / "pub"
        small_build(priv, cues=["double_space"], n_heldout=256, n_grid=64)
        (priv / "scores.jsonl").write_text("an earlier file\n", encoding="utf-8")
        assert [r["status"] for r in send(s, priv, pub)] == ["ok"] * 4
    finally:
        s.close()

    def failing(jobs, texts):
        raise RuntimeError("sandbox down")

    with pytest.raises(RuntimeError):
        exp.score(priv, runner=failing)
    assert (priv / "scores.jsonl").read_text(encoding="utf-8") == "an earlier file\n"     # nothing was lost
    rows = exp.score(priv)
    assert sorted(p.name for p in priv.glob("scores*")) == ["scores.jsonl"]
    assert (priv / "scores.jsonl").read_bytes().isascii()
    assert exp.read_scores(priv / "scores.jsonl") == json.loads(json.dumps(rows))
    for r in rows:
        assert r["outcome"] == "scored" and (r["n_given"], r["n_invalid"], r["n_regex_error"]) == (3, 0, 0)
        assert r["primary"]["listed"] and r["primary"]["rank"] == 3 and r["sensitivity"]["rank"] == 3
        assert [c["regex"] for c in r["candidates"]] == [c["regex"] for c in items]
        assert r["candidates"][0]["property"] == "emoji \ud83d" and r["candidates"][0]["ba_sensitivity"] == 0.5
    summary = exp.table(priv / "scores.jsonl", pub)
    assert summary["outcomes"] == {"scored": 4} and summary["by_cue"]["double_space"]["primary"]["k"] == 4
    for name in ("README.md", "exp_d.json", "per_call.csv"):
        (pub / name).read_bytes().decode("utf-8")


# ---------------------------------------------------------------- answer parsing
@pytest.fixture(scope="module")
def digits_sets():
    return exp.make_heldout("digits", 1, TOPICS, n=512), exp.make_grid("digits", 1, TOPICS, n=256)


def test_extract_candidates_variants():
    items = [cand(r"\d"), cand("x", "last_line")]
    array = json.dumps(items)
    assert exp.extract_candidates(array) == items
    assert exp.extract_candidates("```json\n" + json.dumps(items, indent=2) + "\n```") == items
    assert exp.extract_candidates("Here you go:\n\n" + array + "\n\nHope this helps [really].") == items
    assert exp.extract_candidates("As noted [1], and see [\"any\"] or [a-z]:\n" + array) == items
    assert exp.extract_candidates(json.dumps({"candidates": items})) == items
    assert exp.extract_candidates(array + "\n" + json.dumps([cand("second array")])) == items     # the first one
    assert exp.extract_candidates("[]") == []
    brackets = [cand("["), cand("]]"), cand('"[')]
    assert exp.extract_candidates(json.dumps(brackets)) == brackets
    mixed = [cand("a"), "not an object", 7]
    assert exp.extract_candidates(json.dumps(mixed)) == mixed
    # brackets in the prose before the array, whatever their state: one quoted bracket, a bracket that never
    # closes, a closed span that is not JSON, several of them
    assert exp.extract_candidates('Notes containing "[" are rare.\n' + array) == items
    assert exp.extract_candidates("Legend: [x = present.\n" + array) == items
    assert exp.extract_candidates('The "[" and the "]" come first, then [x = present.\n' + array + "\n[done") == items
    assert exp.extract_candidates('Odd [one "two] three" four].\n' + array) == items
    assert exp.extract_candidates("```json\n" + json.dumps([items]) + "\n```") == items       # one array too many
    # an empty array, or one of empty objects, is the answer only at the first "[" of the text
    assert exp.extract_candidates("Nothing stands out.\n\n```json\n[]\n```") == []
    assert exp.extract_candidates("[]\n" + array) == [] and exp.extract_candidates("[{}]\n" + array) == [{}]
    assert exp.extract_candidates("[1, 2]\n[]") is None and exp.extract_candidates("[[]]") is None
    assert exp.extract_candidates("[1, 2]\n[{}]") is None
    assert exp.extract_candidates("[1, 2]\n[{}, " + json.dumps(items[0]) + "]") == [{}, items[0]]
    # not valid JSON as a whole (a single backslash), with brackets inside its strings: still no list
    broken = ('[{"property": "digit", "regex": "\\d[]})]", "scope": "any"}, '
              '{"property": "empty [] or [{}] or [0]", "regex": "[a-z]"}]')
    assert "\\d[]})]" in broken and "\\\\d" not in broken and exp.extract_candidates(broken) is None
    # nested too deeply for the JSON parser: no list, no exception, and no long search
    assert exp.extract_candidates("[" * 200_000 + "]" * 200_000) is None
    assert exp.extract_candidates("[" * 200_000 + array) is None
    for bad in ("", "no array here", "[1, 2, 3]", '["a", "b"]', '{"regex": "x"}',
                '[{"property": "digit", "regex": "\\d", "scope": "any"}]',       # a single backslash: not JSON
                '[{"property": "p", "regex": "x", "scope": "any"}, {"property": "cut off',
                "[{'property': 'p', 'regex': 'x'}]"):
        assert exp.extract_candidates(bad) is None, bad


def test_candidate_checks():
    assert exp.check_candidate({"regex": "x"}) == ("x", "any", None)                    # a missing scope is "any"
    assert exp.check_candidate({"regex": "x", "scope": "first_line"}) == ("x", "first_line", None)
    assert exp.check_candidate({"regex": "", "scope": "last_line"}) == ("", "last_line", None)
    assert exp.check_candidate({"regex": "a" * 200})[2] is None
    assert exp.check_candidate({"regex": "a" * 201})[2] == "regex_too_long"
    for regex in (None, 5, ["x"], {"a": 1}):
        assert exp.check_candidate({"regex": regex, "scope": "any"})[2] == "regex_not_a_string"
    assert exp.check_candidate({"property": "no regex"})[2] == "regex_not_a_string"
    for scope in ("body", "ANY", "", None, 1, ["any"]):
        assert exp.check_candidate({"regex": "x", "scope": scope})[2] == "unknown_scope"
    for item in ("x", 3, None, ["x"]):
        assert exp.check_candidate(item)[2] == "not_an_object"


def test_score_answer_parsing_variants(digits_sets):
    heldout, grid = digits_sets
    cache = {}

    def score(text):
        return exp.score_answer(text, "digits", heldout, grid, cache)

    true = cand(r"\d")
    for text in (answer(true), "```json\n" + answer(true) + "\n```", "Candidates:\n" + answer(true) + "\nDone."):
        out = score(text)
        assert out["outcome"] == "scored" and out["primary"]["listed"] and out["primary"]["rank"] == 1
        assert out["sensitivity"]["listed"] and out["n_given"] == 1 and out["n_invalid"] == 0
    # more than 20: only the first 20 count
    late = score(answer(*[cand(f"zzz{i}") for i in range(20)], true))
    assert late["outcome"] == "scored" and (late["n_given"], late["n_kept"]) == (21, 20)
    assert not late["primary"]["listed"] and not late["sensitivity"]["listed"] and late["primary"]["rank"] is None
    assert late["primary"]["best_ba"] == 0.5 and len(late["candidates"]) == 20
    last = score(answer(*[cand(f"zzz{i}") for i in range(19)], true, cand("zzz")))
    assert last["primary"]["listed"] and last["primary"]["rank"] == last["sensitivity"]["rank"] == 20
    # invalid candidates are counted and score 0.5, and do not shift the ranks
    out = score(answer(cand(r"\d", "body"), cand(r"\d" + "0?" * 100), cand(7), "junk", true))
    assert out["n_invalid"] == 4 and out["primary"]["rank"] == 5 and out["primary"]["listed"]
    assert [c["invalid"] for c in out["candidates"]] == ["unknown_scope", "regex_too_long", "regex_not_a_string",
                                                         "not_an_object", None]
    assert all(set(c["ba_primary"].values()) == {0.5} and c["ba_sensitivity"] == 0.5 for c in out["candidates"][:4])
    only_invalid = score(answer(cand(r"\d", "nowhere")))
    assert only_invalid["outcome"] == "scored" and not only_invalid["primary"]["listed"]
    # a pattern that does not compile matches nothing
    out = score(answer(cand("(?P<x"), cand("[0-9")))
    assert out["n_regex_error"] == 2 and out["n_invalid"] == 0 and not out["primary"]["listed"]
    # scope is applied: digits are in the body, never in the last line of a note with a sign-off or a P.S.
    assert not score(answer(cand(r"\A\d", "last_line")))["primary"]["listed"]
    # empty array and non-JSON
    empty = score("[]")
    assert empty["outcome"] == "scored" and empty["n_given"] == 0 and not empty["primary"]["listed"]
    assert empty["primary"]["best_ba"] is None
    for text in ('[{"property": "digit", "regex": "\\d", "scope": "any"}]', "The property is digits.", ""):
        out = score(text)
        assert out["outcome"] == "parse_failure" and not out["primary"]["listed"] and out["candidates"] == []


def test_same_regex_from_two_answers_runs_once(digits_sets):
    heldout, grid = digits_sets
    calls = []

    def runner(jobs, texts):
        calls.append(list(jobs))
        return exp.run_many(jobs, texts)

    cache = {}
    a = exp.score_answer(answer(cand(r"\d"), cand("x")), "digits", heldout, grid, cache, runner)
    b = exp.score_answer(answer(cand("x"), cand(r"\d"), cand("y", "first_line")), "digits", heldout, grid, cache,
                         runner)
    assert calls == [[("\\d", "any"), ("x", "any")], [("y", "first_line")]]
    assert a["primary"]["rank"] == 1 and b["primary"]["rank"] == 2


# ---------------------------------------------------------------- scoring masks
@pytest.fixture(scope="module")
def sets():
    """Full-size held-out notes and grader-style grid per target cue."""
    return {cue: (exp.make_heldout(cue, 1, TOPICS), exp.make_grid(cue, 1, TOPICS)) for cue in exp.CUES}


def test_masks_are_where_the_cue_can_vary(sets):
    heldout, _ = sets["digits"]
    flags = exp.flag_arrays(heldout)
    assert len(heldout["texts"]) == 2048
    exp.check_masks(flags)
    for cue in exp.CUES:
        mask = exp.cue_mask(cue, flags)
        if cue == "ps_tentative":
            assert (mask == (flags["postscript"] & ~flags["ps_question"])).all() and 400 < mask.sum() < 630
        elif cue in ("ps_question", "signoff_excl", "signoff_initial"):
            assert (mask == flags[fl.IMPLIES[cue]]).all() and 900 < mask.sum() < 1150
        else:
            assert mask.all()
        assert abs(flags[cue][mask].mean() - 0.5) < 0.08                  # a fair coin within its mask
    one_class = dict(flags, digits=np.zeros(2048, dtype=bool))
    with pytest.raises(ValueError):
        exp.check_masks(one_class)


@pytest.mark.parametrize("cue", exp.CUES)
def test_true_detector_lists_its_cue_under_both_rules_and_both_polarities(sets, cue):
    heldout, grid = sets[cue]
    assert len(heldout["texts"]) == 2048 and len(grid["texts"]) == 1024 and grid["mains"] == [cue]
    pattern, scope = fl.submission_regex(cue)
    for regex in (pattern, negated(pattern)):
        assert len(regex) <= 200
        out = exp.score_answer(answer(cand("zzz-nothing"), cand(regex, scope)), cue, heldout, grid)
        assert out["outcome"] == "scored" and out["n_regex_error"] == 0
        assert out["primary"] == {"listed": True, "rank": 2, "best_ba": 1.0, "n_offtarget": 0, "offtarget_cues": []}
        assert out["sensitivity"] == {"listed": True, "rank": 2, "best_ba": 1.0}
        assert out["candidates"][1]["reaches"] == [cue]
        assert out["candidates"][0]["reaches"] == []


@pytest.mark.parametrize("child", sorted(fl.IMPLIES))
def test_parent_only_regex_does_not_list_a_child_under_either_rule(sets, child):
    heldout, grid = sets[child]
    parent = fl.IMPLIES[child]
    pattern, scope = fl.submission_regex(parent)
    flags = exp.flag_arrays(heldout)
    match = np.array([bool(re.search(pattern, t)) for t in heldout["texts"]])
    unmasked = balanced_accuracy(match, flags[child])
    # why the mask is needed: over all notes the parent alone would pass (about 0.83; for ps_tentative, which
    # is on in an eighth of the notes, about 0.79, just under the bar)
    assert 0.75 < unmasked < 0.8 if child == "ps_tentative" else 0.8 <= unmasked < 0.87
    for regex in (pattern, negated(pattern)):
        out = exp.score_answer(answer(cand(regex, scope)), child, heldout, grid)
        assert not out["primary"]["listed"] and out["primary"]["best_ba"] == 0.5
        assert not out["sensitivity"]["listed"] and 0.70 < out["sensitivity"]["best_ba"] < 0.79
        assert out["primary"]["offtarget_cues"] == [parent] and out["primary"]["n_offtarget"] == 1


def test_statement_ps_regex_does_not_list_ps_tentative(sets):
    heldout, grid = sets["ps_tentative"]
    statement = r"(?im)^p\.s\.[^\n]*[^?\n]$"         # a P.S. line that is not a question
    flags = exp.flag_arrays(heldout)
    match = np.array([bool(re.search(statement, t)) for t in heldout["texts"]])
    assert (match == (flags["postscript"] & ~flags["ps_question"])).all()
    within_parent = balanced_accuracy(match[flags["postscript"]], flags["ps_tentative"][flags["postscript"]])
    assert within_parent >= 0.8                      # within parent-present notes alone it would pass
    out = exp.score_answer(answer(cand(statement)), "ps_tentative", heldout, grid)
    assert not out["primary"]["listed"] and out["primary"]["best_ba"] == 0.5
    assert out["primary"]["offtarget_cues"] == ["ps_question"]      # it is the question cue with the polarity turned
    # Sensitivity rule: the grid holds the question P.S. off, so half of the notes without the tentative P.S.
    # have a statement P.S. and the regex stays at about 0.75, like a parent-only regex. (With the question
    # left a coin only a quarter of them would, and the regex would pass at about 0.875.)
    assert grid["held_off"] == ["ps_question"]
    assert not out["sensitivity"]["listed"] and 0.70 < out["sensitivity"]["best_ba"] < 0.79
    for other in (r"\.$", r"[^?]$"):                # the same thing said by the end of the last line
        out = exp.score_answer(answer(cand(other, "last_line")), "ps_tentative", heldout, grid)
        assert not out["primary"]["listed"] and not out["sensitivity"]["listed"], other
    coin = fl.sample_grid(random.Random(grid["seed"]), TOPICS, 1024, None, mains=["ps_tentative"])
    match = np.array([bool(re.search(statement, t)) for t in coin[0]])
    assert 0.84 < balanced_accuracy(match, coin[2]["ps_tentative"]) < 0.91
    # the sibling's regex does not list it under either rule
    out = exp.score_answer(answer(cand(ft.SUBMISSION["ps_question"])), "ps_tentative", heldout, grid)
    assert not out["primary"]["listed"] and not out["sensitivity"]["listed"]
    assert out["primary"]["offtarget_cues"] == ["ps_question"] and out["sensitivity"]["best_ba"] == 0.5


def test_a_shared_character_lists_the_plain_cue_and_not_the_child(sets):
    for regex, plain, child in ((r"\?", "question", "ps_question"), ("!", "exclamation", "signoff_excl")):
        heldout, grid = sets[child]
        out = exp.score_answer(answer(cand(regex)), child, heldout, grid)
        assert not out["primary"]["listed"] and not out["sensitivity"]["listed"]
        assert 0.70 < out["primary"]["best_ba"] < 0.79
        assert out["primary"]["offtarget_cues"] == [plain]
        heldout, grid = sets[plain]
        out = exp.score_answer(answer(cand(regex)), plain, heldout, grid)
        assert out["primary"]["listed"] and out["sensitivity"]["listed"]
        assert 0.84 < out["primary"]["best_ba"] < 0.91


# ---------------------------------------------------------------- table arithmetic
def test_wilson_interval():
    assert exp.wilson(5, 5) == pytest.approx((0.5655, 1.0), abs=5e-4)       # the plan's "5/5 -> [0.57, 1]"
    assert exp.wilson(0, 5) == pytest.approx((0.0, 0.4345), abs=5e-4)
    assert exp.wilson(3, 5) == pytest.approx((0.2307, 0.8824), abs=5e-4)
    assert exp.wilson(10, 20) == pytest.approx((0.2993, 0.7007), abs=5e-4)
    assert exp.wilson(0, 0) == (0.0, 1.0)
    lo, hi = exp.wilson(13, 18)
    assert lo < 13 / 18 < hi and (round(lo, 2), round(hi, 2)) == (0.49, 0.88)
    assert exp.parse_fraction(" 13/18 ") == (13, 18)
    for bad in ("13", "19/18", "a/b", "0/0", None):
        with pytest.raises(SystemExit):
            exp.parse_fraction(bad)


def fake_row(cue, rep, model, listed, listed_sens=None, outcome="scored", rank=1):
    listed_sens = listed if listed_sens is None else listed_sens
    return {"call_id": exp.call_id(cue, rep, model), "cue": cue, "rep": rep, "model": model, "sign": 1,
            "topics": ["chess", "sailing"], "status": None if outcome == exp.NOT_STORED else "ok", "usd": 0.01,
            "outcome": outcome, "n_given": 10, "n_kept": 10, "n_invalid": 1, "n_regex_error": 0, "candidates": [],
            "primary": {"listed": listed, "rank": rank if listed else None, "best_ba": 1.0 if listed else 0.5,
                        "n_offtarget": 2, "offtarget_cues": ["hashtag"]},
            "sensitivity": {"listed": listed_sens, "rank": 1 if listed_sens else None,
                            "best_ba": 1.0 if listed_sens else 0.5}}


def test_table_arithmetic(tmp_path):
    rows = []
    for cue in exp.CUES:
        for rep in range(1, 6):
            for model in exp.MODELS:
                if cue in exp.PLAIN_EXISTING:
                    listed = True
                elif cue == "ps_question":
                    listed = rep <= 3                                    # 3/5 per model, 12/20 pooled
                elif cue == "ps_tentative":
                    listed = False
                elif cue == "digits":
                    listed = model == "gpt-6.1-terra"                    # 5/5 for one model, 5/20 pooled
                else:
                    listed = rep == 1                                    # 1/5 per model
                rows.append(fake_row(cue, rep, model, listed, listed_sens=listed or cue == "ps_tentative",
                                     rank=rep))
    # one plain call was never stored, one came back unparsable, one was refused
    rows[0] = fake_row("exclamation", 1, exp.MODELS[0], False, outcome=exp.NOT_STORED)
    rows[1] = fake_row("exclamation", 1, exp.MODELS[1], False, outcome="parse_failure")
    rows[2] = fake_row("exclamation", 1, exp.MODELS[2], False, outcome="refusal")
    scores = tmp_path / "scores.jsonl"
    scores.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    pub = tmp_path / "pub"
    s = exp.table(scores, pub, main_plain=(40, 40), main_twopart=(13, 18), main_source="main study, file F")
    assert s == json.loads((pub / "exp_d.json").read_text(encoding="utf-8"))
    assert (s["n_planned"], s["n_stored"]) == (400, 399)
    assert s["outcomes"] == {"not_stored": 1, "parse_failure": 1, "refusal": 1, "scored": 397}
    cell = s["by_cue_model"]["ps_question"]["claude-opus-5-5"]
    assert cell["primary"] == {"k": 3, "n": 5, "rate": 0.6, "wilson95": [0.2307, 0.8824]}
    assert s["by_cue"]["ps_question"]["primary"]["k"] == 12 and s["by_cue"]["ps_question"]["n"] == 20
    assert s["by_cue"]["ps_question"]["median_rank_primary"] == 2
    assert s["by_cue"]["ps_question"]["kind"] == "child of postscript, existing"
    assert s["by_cue"]["signoff_initial"]["kind"] == "child of signoff, new"
    assert s["by_cue"]["digits"]["kind"] == "plain, new" and s["by_cue"]["weekday"]["kind"] == "plain, existing"
    assert s["by_cue_model"]["digits"]["gpt-6.1-terra"]["primary"]["wilson95"] == [0.5655, 1.0]
    assert s["by_cue_model"]["digits"]["claude-haiku-5-5"]["primary"]["wilson95"] == [0.0, 0.4345]
    assert s["by_cue"]["digits"]["primary"]["rate"] == 0.25
    # the not-stored call leaves the denominator; the parse failure and the refusal stay in it as not listed
    assert s["by_cue_model"]["exclamation"][exp.MODELS[0]]["n"] == 4
    assert s["by_cue_model"]["exclamation"][exp.MODELS[0]]["primary"]["k"] == 4
    assert s["by_cue_model"]["exclamation"][exp.MODELS[1]]["primary"] == {"k": 4, "n": 5, "rate": 0.8,
                                                                         "wilson95": [0.3755, 0.9638]}
    assert s["by_cue"]["exclamation"]["primary"]["k"] == 17 and s["by_cue"]["exclamation"]["n"] == 19
    cal = s["calibration"]
    assert cal["plain_existing_13"]["planned"] == 260 and cal["plain_existing_13"]["n"] == 259
    assert cal["plain_existing_13"]["primary"]["k"] == 257
    assert cal["ps_question"]["primary"]["k"] == 12
    assert cal["signoff_excl"]["primary"] == s["by_cue"]["signoff_excl"]["primary"]
    assert cal["main_study"]["plain_slots"]["k"] == 40
    assert cal["main_study"]["two_part_child"]["wilson95"] == [0.4913, 0.875]
    assert cal["main_study"]["source"] == "main study, file F"
    # both rules side by side
    assert s["by_cue"]["ps_tentative"]["primary"]["k"] == 0 and s["by_cue"]["ps_tentative"]["sensitivity"]["k"] == 20
    # ranking: by pooled primary rate, ties in cue order
    full = [c for c in exp.PLAIN_EXISTING if c != "exclamation"]
    assert s["ranking"][:12] == full and s["ranking"][12] == "exclamation" and s["ranking"][13] == "ps_question"
    assert s["ranking"][14] == "digits" and s["ranking"][-1] == "ps_tentative"
    per_model = s["by_model"]["gpt-6.1-terra"]
    assert per_model["n"] == 99 and per_model["primary"]["k"] == 64 + 3 + 5 + 4
    assert s["by_model"]["claude-opus-5-5"]["primary"]["k"] == 64 + 3 + 4
    assert s["candidates_by_model"]["claude-opus-5-5"] == {"mean_given": 10.0, "mean_invalid": 1.0,
                                                           "mean_regex_error": 0.0, "mean_offtarget": 2.0}
    assert s["usd"]["gpt-6.1-terra"] == 1.0

    readme = (pub / "README.md").read_text(encoding="utf-8")
    for needed in ("single-cue salience", "about 8 properties", "coarse ranking only", "not the grader's rule",
                   "| `ps_question` | child of postscript, existing | 3/5 [0.23, 0.88] |", "12/20 [0.39, 0.78]",
                   "40/40 [0.91, 1.00] (plain slots)", "13/18 [0.49, 0.88] (two-part child)", "main study, file F",
                   "- D_exclamation_1_gpt-6.1-terra: not_stored", "- D_exclamation_1_claude-opus-5-5: parse_failure",
                   "| `ps_tentative` | 0/20 [0.00, 0.16] | 20/20 [0.84, 1.00] |"):
        assert needed in readme, needed
    table_rows = list(csv.reader(io.StringIO((pub / "per_call.csv").read_text(encoding="utf-8"))))
    assert table_rows[0] == exp.PER_CALL_COLUMNS and len(table_rows) == 401
    first = dict(zip(table_rows[0], table_rows[1]))
    assert first["call_id"] == "D_exclamation_1_gpt-6.1-terra" and first["outcome"] == "not_stored"
    assert first["listed_primary"] == "0" and first["rank_primary"] == "" and first["status"] == ""
    row = dict(zip(table_rows[0], table_rows[4]))
    assert row["listed_primary"] == "1" and row["best_ba_primary"] == "1.0000" and row["offtarget_cues"] == "hashtag"

    # without the main-study constants the table says so
    s2 = exp.summarize(rows)
    assert s2["calibration"]["main_study"] == {"plain_slots": None, "two_part_child": None, "source": None}
    assert "not given (plain slots)" in exp.readme_text(s2) and "Source: not given." in exp.readme_text(s2)


def test_table_with_nothing_stored(tmp_path):
    rows = [fake_row(c, r, m, False, outcome=exp.NOT_STORED) for c in ("digits", "weekday") for r in (1, 2)
            for m in exp.MODELS]
    s = exp.summarize(rows)
    assert s["n_stored"] == 0 and s["by_cue"]["digits"]["primary"] == {"k": 0, "n": 0, "rate": None,
                                                                      "wilson95": [0.0, 1.0]}
    assert "0/0" in exp.readme_text(s) and exp.per_call_csv(rows).count("\n") == 17


# ---------------------------------------------------------------- estimate
def test_estimate_arithmetic():
    prompt = "a" * 3500
    calls = [{"call_id": f"c{i}_{m}", "model": m, "prompt": prompt} for i in range(2) for m in exp.MODELS]
    est = exp.estimate(calls, bytes_per_token=3.5, output_tokens=4000, workers=4)
    opus = est["models"]["claude-opus-5-5"]
    assert opus["calls"] == 2 and opus["prompt_bytes"] == 7000 and opus["input_tokens"] == 2000
    assert opus["expected_usd"] == pytest.approx(2 * (1000 * 4 + 4000 * 20) / 1e6)
    guard = tc.estimate_usd("claude-opus-5-5", tc.build_request("claude-opus-5-5", prompt))
    assert opus["guard_usd_max"] == guard and opus["guard_usd"] == pytest.approx(2 * guard)
    anthropic = est["providers"]["anthropic"]
    want = sum(2 * (1000 * p + 4000 * q) / 1e6 for p, q in ((4, 20), (2, 10), (0.1, 0.5)))
    assert anthropic["calls"] == 6 and anthropic["expected_usd"] == pytest.approx(want)
    assert anthropic["min_budget_usd"] == pytest.approx(want + 4 * guard)     # 4 calls in flight, the dearest model
    openai = est["providers"]["openai"]
    gpt_guard = tc.estimate_usd("gpt-6.1-terra", tc.build_request("gpt-6.1-terra", prompt))
    assert openai["expected_usd"] == pytest.approx(2 * (1000 * 1 + 4000 * 5) / 1e6)
    assert openai["min_budget_usd"] == pytest.approx(openai["expected_usd"] + gpt_guard)   # one at a time
    text = exp.estimate_text(est)
    assert "3.5 prompt bytes per input token" in text and "4000 output tokens" in text and "| anthropic | 6 |" in text
    # a non-ASCII prompt is counted in bytes, not characters
    est = exp.estimate([{"call_id": "c", "model": "claude-haiku-5-5", "prompt": CURLY * 10}])
    assert est["models"]["claude-haiku-5-5"]["prompt_bytes"] == 30
