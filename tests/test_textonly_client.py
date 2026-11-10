"""scripts/textonly_client.py and scripts/exp_e_shift_recall.py against a local stub HTTP server.

No network and no paid call: every request goes to an http.server on 127.0.0.1 in a thread, and the API keys
are made-up strings.
"""
import json
import re
import socket
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import exp_e_shift_recall as exp  # noqa: E402
import textonly_client as tc  # noqa: E402

ANTHROPIC_KEY = "sk-ant-test-SECRETKEY-123"
OPENAI_KEY = "sk-oai-test-SECRETKEY-456"
CLAUDE = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
GPT = "gpt-6.1-terra"
ANSWER = "Step 1: it’s done.  Step 2: 🙂"
BIG = {"anthropic": 1000.0, "openai": 1000.0}
TRICKY = [
    "It’s a curly apostrophe.",
    "It's a straight apostrophe.",
    "Two spaces.  After a period.   Three.",
    "tab\there\nnewline\r\ncarriage return, trailing space ",
    "emoji 🙂 and 👩‍🔬, quotes \" and \\ backslash, é, \u2028 line separator",
]


def default_reply(path, body):
    request = json.loads(body)
    if path == "/v1/messages":
        response = {"id": "msg_1", "type": "message", "role": "assistant", "model": request["model"],
                    "content": [{"type": "thinking", "thinking": "hidden", "signature": "sig"},
                                {"type": "text", "text": ANSWER}],
                    "stop_reason": "end_turn", "stop_details": None,
                    "usage": {"input_tokens": 12, "output_tokens": 34}}
    else:
        response = {"id": "resp_1", "object": "response", "status": "completed", "incomplete_details": None,
                    "model": request["model"] + "-2026-10-01",
                    "output": [{"type": "reasoning", "id": "rs_1", "summary": [{"type": "summary_text", "text": "x"}]},
                               {"type": "message", "role": "assistant",
                                "content": [{"type": "output_text", "text": ANSWER, "annotations": []}]}],
                    "usage": {"input_tokens": 12, "input_tokens_details": {"cached_tokens": 0},
                              "output_tokens": 34, "output_tokens_details": {"reasoning_tokens": 20}}}
    return 200, json.dumps(response).encode()


class Stub:
    """Records every request (path, headers, body bytes). Replies from `queue` first, then with `reply`."""

    def __init__(self):
        stub = self
        self.lock = threading.Lock()
        self.requests, self.queue, self.reply = [], [], default_reply

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                with stub.lock:
                    stub.requests.append((self.path, {k.lower(): v for k, v in self.headers.items()}, body))
                    scripted = stub.queue.pop(0) if stub.queue else None
                status, data, *extra = scripted or stub.reply(self.path, body)
                self.send_response(status)
                for name, value in {"Content-Length": str(len(data)), "request-id": "req_stub",
                                    "x-request-id": "xreq_stub", **(extra[0] if extra else {})}.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, args=(0.01,), daemon=True).start()
        url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.base_urls = {"anthropic": url, "openai": url}

    def bodies(self):
        return [body for _, _, body in self.requests]


@pytest.fixture
def stub():
    s = Stub()
    yield s
    s.server.shutdown()
    s.server.server_close()


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", ANTHROPIC_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", OPENAI_KEY)
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(tc, "BACKOFF_BASE_S", 0.001)


def call(call_id="c1", model="claude-haiku-5-5", prompt="Hello"):
    return {"call_id": call_id, "model": model, "prompt": prompt}


def run(stub, calls, out, **kw):
    kw.setdefault("budget_usd", BIG)
    kw.setdefault("workers", 1)
    return tc.run_calls(calls, out, base_urls=stub.base_urls, **kw)


def meta(out, call_id="c1"):
    return json.loads((out / f"{call_id}.meta.json").read_bytes())


def reply_json(obj, status=200):
    return status, json.dumps(obj).encode()


# ---------------------------------------------------------------- request bytes
@pytest.mark.parametrize("model", CLAUDE + [GPT])
def test_request_bytes_are_stored_as_sent(stub, tmp_path, model):
    calls = [call(f"c{i}", model, p) for i, p in enumerate(TRICKY)]
    rows = run(stub, calls, tmp_path)
    assert [r["status"] for r in rows] == ["ok"] * len(TRICKY)
    assert len(stub.requests) == len(TRICKY)
    for (path, _, received), c in zip(stub.requests, calls):
        stored = (tmp_path / f"{c['call_id']}.request.json").read_bytes()
        assert stored == received
        quoted = json.dumps(c["prompt"], ensure_ascii=False).encode("utf-8")
        if model == GPT:
            assert path == "/v1/responses"
            assert received == b'{"model":"gpt-6.1-terra","input":' + quoted + b',"store":false}'
        else:
            assert path == "/v1/messages"
            assert received == (b'{"model":"' + model.encode() + b'","max_tokens":16000,"messages":'
                                b'[{"role":"user","content":' + quoted + b"}]}")
        m = meta(tmp_path, c["call_id"])
        assert m["request_sha256"] == tc.sha256(received) and m["request_bytes"] == len(received)
        assert m["prompt_sha256"] == tc.sha256(c["prompt"].encode("utf-8"))


def test_apostrophes_spaces_and_emoji_stay_raw_utf8(stub, tmp_path):
    run(stub, [call("curly", prompt="It’s.  Two\tspaces 🙂"), call("straight", prompt="It's.  Two\tspaces 🙂")], tmp_path)
    curly, straight = stub.bodies()
    assert "’".encode("utf-8") in curly and b"\\u2019" not in curly and b"'" not in curly
    assert b"It's.  Two\\tspaces " + "🙂".encode("utf-8") in straight
    assert curly != straight
    assert json.loads(curly)["messages"][0]["content"] == "It’s.  Two\tspaces 🙂"


def test_request_has_only_the_default_fields_and_auth_headers(stub, tmp_path):
    run(stub, [call("a", "claude-opus-5-5"), call("g", GPT)], tmp_path)
    (_, h_claude, b_claude), (_, h_gpt, b_gpt) = stub.requests
    assert sorted(json.loads(b_claude)) == ["max_tokens", "messages", "model"]
    assert json.loads(b_gpt) == {"model": GPT, "input": "Hello", "store": False}
    assert h_claude["x-api-key"] == ANTHROPIC_KEY and h_claude["anthropic-version"] == "2023-06-01"
    assert h_claude["content-type"] == "application/json" and "authorization" not in h_claude
    assert h_gpt["authorization"] == "Bearer " + OPENAI_KEY and "x-api-key" not in h_gpt
    assert meta(tmp_path, "a")["request_headers"] == {
        "anthropic-version": "2023-06-01", "content-type": "application/json", "user-agent": tc.USER_AGENT}
    assert meta(tmp_path, "a")["url"].endswith("/v1/messages") and meta(tmp_path, "g")["url"].endswith("/v1/responses")


def test_openai_key_falls_back_to_openai_key_variable(stub, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("OPENAI_KEY", "sk-fallback-789")
    run(stub, [call("g", GPT)], tmp_path)
    assert stub.requests[0][1]["authorization"] == "Bearer sk-fallback-789"


def test_missing_key_stops_before_any_request(stub, tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        run(stub, [call("g", GPT), call("a")], tmp_path)
    assert stub.requests == [] and not list(tmp_path.glob("*.request.json"))


# ---------------------------------------------------------------- response bytes, answer, stop reasons
def test_response_bytes_are_stored_unmodified(stub, tmp_path):
    raw = (b'{ "model" : "claude-opus-5-5",\r\n\t"content":[{"type":"text","text":"caf\\u00e9 \\ud83d\\ude42  it'
           + "’".encode("utf-8") + b's"}],\n "stop_reason":"end_turn" ,"usage":{"input_tokens":3,"output_tokens":5}}\n\n ')
    stub.queue.append((200, raw))
    rows = run(stub, [call(model="claude-opus-5-5")], tmp_path)
    assert (tmp_path / "c1.response.json").read_bytes() == raw
    m = meta(tmp_path)
    assert m["response_sha256"] == tc.sha256(raw) and m["response_bytes"] == len(raw)
    assert m["answer_sha256"] == tc.sha256("café 🙂  it’s".encode("utf-8")) and m["answer_chars"] == 12
    assert m["response_headers"]["request-id"] == "req_stub" and m["response_headers"]["x-request-id"] == "xreq_stub"
    assert m["response_headers"]["date"] and m["http_status"] == 200 and rows[0]["status"] == "ok"
    assert m["usage"] == {"input_tokens": 3, "output_tokens": 5}
    assert m["usd"] == rows[0]["usd"] == pytest.approx((3 * 4 + 5 * 20) / 1e6)
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", m["started_utc"]) and m["finished_utc"] >= m["started_utc"]


def test_answer_text_skips_thinking_and_reasoning():
    claude = {"content": [{"type": "thinking", "thinking": "plan"}, {"type": "text", "text": "A"},
                          {"type": "redacted_thinking", "data": "x"}, {"type": "text", "text": "B"}],
              "stop_reason": "end_turn", "stop_details": None}
    assert tc.extract_answer("anthropic", claude) == "AB"
    assert tc.stop_info("anthropic", claude) == ("end_turn", None)
    gpt = {"status": "completed", "incomplete_details": None,
           "output": [{"type": "reasoning", "summary": [{"type": "summary_text", "text": "hidden"}]},
                      {"type": "message", "content": [{"type": "output_text", "text": "A"}]},
                      {"type": "reasoning", "summary": [], "content": None},
                      {"type": "message", "content": [{"type": "refusal", "refusal": "no"},
                                                      {"type": "output_text", "text": "B"}]}]}
    assert tc.extract_answer("openai", gpt) == "AB"
    assert tc.stop_info("openai", gpt) == ("refusal", None)
    assert tc.extract_answer("anthropic", {}) == "" and tc.extract_answer("openai", {"output": None}) == ""


def test_answer_and_content_types_end_to_end(stub, tmp_path):
    run(stub, [call("a", "claude-sonnet-5-5"), call("g", GPT)], tmp_path)
    a, g = meta(tmp_path, "a"), meta(tmp_path, "g")
    assert a["answer_sha256"] == g["answer_sha256"] == tc.sha256(ANSWER.encode("utf-8"))
    assert a["content_types"] == ["thinking", "text"] and g["content_types"] == ["reasoning", "output_text"]
    assert (a["stop_reason"], a["status"]) == ("end_turn", "ok")
    assert (g["stop_reason"], g["status"]) == ("completed", "ok")
    assert g["response_model"] == "gpt-6.1-terra-2026-10-01"
    assert g["usd"] == pytest.approx((12 * 1.0 + 34 * 5.0) / 1e6)


@pytest.mark.parametrize("model,response,stop,details", [
    ("claude-opus-5-5", {"model": "claude-opus-5-5", "content": [], "stop_reason": "refusal",
                         "stop_details": {"type": "refusal", "category": "cyber", "explanation": "e"},
                         "usage": {"input_tokens": 9, "output_tokens": 0}},
     "refusal", {"type": "refusal", "category": "cyber", "explanation": "e"}),
    ("claude-haiku-5-5", {"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "cut of"}],
                          "stop_reason": "max_tokens", "usage": {"input_tokens": 9, "output_tokens": 16000}},
     "max_tokens", None),
    (GPT, {"model": GPT, "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
           "output": [{"type": "reasoning", "summary": []}], "usage": {"input_tokens": 9, "output_tokens": 7}},
     "incomplete", {"reason": "max_output_tokens"}),
    (GPT, {"model": GPT, "status": "completed", "incomplete_details": None,
           "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "I can't"}]}],
           "usage": {"input_tokens": 9, "output_tokens": 7}},
     "refusal", None),
])
def test_refusal_and_truncation_are_recorded_and_never_retried(stub, tmp_path, model, response, stop, details):
    stub.reply = lambda path, body: reply_json(response)
    rows = run(stub, [call(model=model)], tmp_path)
    m = meta(tmp_path)
    assert rows[0]["status"] == m["status"] == m["stop_reason"] == stop and m["stop_details"] == details
    assert m["http_status"] == 200 and m["attempt_count"] == 1 and len(stub.requests) == 1
    assert m["usd"] == tc.usd(model, response["usage"]) > 0
    run(stub, [call(model=model)], tmp_path)      # resume: a 200 is not sent again, whatever its stop reason
    assert len(stub.requests) == 1


def test_a_different_model_answering_is_flagged(stub, tmp_path):
    stub.reply = lambda path, body: reply_json({"model": "claude-opus-4-8", "content": [{"type": "text", "text": "x"}],
                                                "stop_reason": "end_turn", "usage": {}})
    assert run(stub, [call(model="claude-opus-5-5")], tmp_path)[0]["status"] == "model_mismatch"
    assert meta(tmp_path)["response_model"] == "claude-opus-4-8"


def test_a_200_that_is_not_json_is_kept_and_flagged(stub, tmp_path):
    stub.queue.append((200, b"<html>not json</html>"))
    assert run(stub, [call()], tmp_path)[0]["status"] == "bad_json"
    assert (tmp_path / "c1.response.json").read_bytes() == b"<html>not json</html>"
    assert meta(tmp_path)["answer_sha256"] is None and meta(tmp_path)["usd"] == 0.0


def claude_200(text='"content":[{"type":"text","text":"x"}]', usage='{"input_tokens":1000,"output_tokens":2000}'):
    return ('{"model":"claude-haiku-5-5",' + text + ',"stop_reason":"end_turn","usage":' + usage + "}").encode()


HAIKU_USD = (1000 * 0.10 + 2000 * 0.50) / 1e6


@pytest.mark.parametrize("raw,status,error,usage_priced", [
    (claude_200('"content":[{"type":"text","text":"half \\ud83d"}]'), "postprocess_error", "UnicodeEncodeError", True),
    (claude_200('"content":"a string"'), "postprocess_error", "AttributeError", True),
    (claude_200(usage='{"input_tokens":"7","output_tokens":5}'), "postprocess_error", "TypeError", False),
    (claude_200(usage="[1]"), "postprocess_error", "AttributeError", False),
    (b"[" * 200_000, "bad_json", "RecursionError", False),
    (b"[1, 2]", "bad_json", "ValueError", False),
    (b'{"model":"claude-haiku-5-5","content":[{"type":"text","text":"cut of', "bad_json", "JSONDecodeError", False),
])
def test_a_200_body_of_an_unexpected_shape_is_kept_flagged_and_counted(stub, tmp_path, raw, status, error, usage_priced):
    stub.reply = lambda path, body: (200, raw) if b"bad" in body else default_reply(path, body)
    calls = [call(f"x{i}", prompt="bad" if i == 2 else "fine") for i in range(6)]
    rows = run(stub, calls, tmp_path, workers=3)      # no exception, and the other calls are not disturbed
    assert [r["status"] for r in rows] == ["ok", "ok", status, "ok", "ok", "ok"]
    m = meta(tmp_path, "x2")
    assert (tmp_path / "x2.response.json").read_bytes() == raw and m["response_sha256"] == tc.sha256(raw)
    assert m["http_status"] == 200 and m["status"] == status and m["answer_sha256"] is None
    assert error is None or m["postprocess_error"].startswith(error)
    estimate = tc.estimate_usd("claude-haiku-5-5", (tmp_path / "x2.request.json").read_bytes())
    # the spend is counted: from the usage object if it could be priced, else at the conservative estimate
    assert (m["usd"], m["usd_budget"]) == ((HAIKU_USD, HAIKU_USD) if usage_priced else (0.0, estimate))
    assert tc.recorded_usd(tmp_path)["anthropic"] == pytest.approx(m["usd_budget"] + 5 * (12 * 0.10 + 34 * 0.50) / 1e6)
    run(stub, calls, tmp_path)      # a stored 200 is not sent again
    assert len(stub.requests) == 6 and (tmp_path / "x2.response.json").read_bytes() == raw


def test_a_lone_surrogate_in_a_meta_field_is_written_as_its_escape(stub, tmp_path):
    stub.reply = lambda path, body: (200, claude_200('"model":"\\ud83d"'))
    assert run(stub, [call()], tmp_path)[0]["status"] == "model_mismatch"
    assert meta(tmp_path)["response_model"] == "\ud83d" and b'"\\ud83d"' in (tmp_path / "c1.meta.json").read_bytes()


@pytest.mark.parametrize("model,response", [
    ("claude-opus-5-5", {"model": "claude-opus-5-5", "content": [{"type": "thinking", "thinking": "t"}],
                         "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 4}}),
    ("claude-opus-5-5", {"model": "claude-opus-5-5", "content": [{"type": "text", "text": " \n"}],
                         "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 4}}),
    (GPT, {"model": GPT, "status": "completed", "output": [], "usage": {"input_tokens": 9, "output_tokens": 4}}),
])
def test_a_normal_stop_without_answer_text_is_not_ok(stub, tmp_path, model, response, capsys):
    stub.reply = lambda path, body: reply_json(response)
    assert run(stub, [call(model=model)], tmp_path)[0]["status"] == "empty_answer"
    assert meta(tmp_path)["usd"] == tc.usd(model, response["usage"]) > 0
    (tmp_path / "calls.jsonl").write_text(json.dumps(call(model=model)) + "\n")
    assert tc.main(["--calls", str(tmp_path / "calls.jsonl"), "--out", str(tmp_path), "--budget-usd", "anthropic=1",
                    "--budget-usd", "openai=1"], base_urls=stub.base_urls) == 1
    assert "empty_answer 1" in capsys.readouterr().out and len(stub.requests) == 1


# ---------------------------------------------------------------- retries
def test_retries_429_and_500_then_succeeds(stub, tmp_path):
    stub.queue += [(429, b'{"error":"slow down"}'), (500, b"boom")]
    rows = run(stub, [call(prompt="It’s  retried")], tmp_path)
    m = meta(tmp_path)
    assert rows[0]["status"] == "ok" and m["attempt_count"] == 3
    assert [a["http_status"] for a in m["attempts"]] == [429, 500, 200]
    assert [a["n"] for a in m["attempts"]] == [1, 2, 3]
    assert m["attempts"][0]["response_sha256"] == tc.sha256(b'{"error":"slow down"}')
    bodies = stub.bodies()
    assert len(bodies) == 3 and bodies[0] == bodies[1] == bodies[2] == (tmp_path / "c1.request.json").read_bytes()
    assert json.loads((tmp_path / "c1.response.json").read_bytes())["stop_reason"] == "end_turn"


def test_400_is_not_retried_and_is_recorded(stub, tmp_path):
    error = b'{"type":"error","error":{"type":"invalid_request_error","message":"bad"}}'
    stub.queue.append((400, error))
    rows = run(stub, [call()], tmp_path)
    m = meta(tmp_path)
    assert len(stub.requests) == 1 and rows[0] == {
        "call_id": "c1", "model": "claude-haiku-5-5", "prompt_sha256": tc.sha256(b"Hello"), "status": "http_400", "usd": 0.0}
    assert m["http_status"] == 400 and m["attempt_count"] == 1 and m["answer_sha256"] is None
    assert (tmp_path / "c1.response.json").read_bytes() == error


def test_gives_up_after_six_attempts(stub, tmp_path):
    stub.reply = lambda path, body: (503, b"unavailable")
    rows = run(stub, [call()], tmp_path)
    assert len(stub.requests) == 6 and rows[0]["status"] == "http_503"
    assert [a["http_status"] for a in meta(tmp_path)["attempts"]] == [503] * 6
    assert (tmp_path / "c1.response.json").read_bytes() == b"unavailable"


def test_network_errors_are_retried_and_recorded(tmp_path):
    with socket.socket() as s:      # a port with nothing listening
        s.bind(("127.0.0.1", 0))
        dead = f"http://127.0.0.1:{s.getsockname()[1]}"
    rows = tc.run_calls([call()], tmp_path, workers=1, budget_usd=BIG, base_urls={"anthropic": dead})
    m = meta(tmp_path)
    assert rows[0]["status"] == m["status"] == "network_error" and m["http_status"] is None
    assert m["attempt_count"] == 6 and all(a["error"] and a["http_status"] is None for a in m["attempts"])
    assert (tmp_path / "c1.request.json").exists() and not (tmp_path / "c1.response.json").exists()
    assert m["response_sha256"] is None and m["usd"] == 0.0


def test_redirects_are_not_followed(stub, tmp_path):
    stub.queue.append((302, b"", {"Location": stub.base_urls["anthropic"] + "/elsewhere"}))
    assert run(stub, [call()], tmp_path)[0]["status"] == "http_302"
    assert len(stub.requests) == 1


# ---------------------------------------------------------------- resume
def test_resume_skips_stored_200_and_force_sends_again(stub, tmp_path):
    calls = [call("c1"), call("c2", GPT)]
    first = run(stub, calls, tmp_path)
    manifest = (tmp_path / "manifest.jsonl").read_bytes()
    assert run(stub, calls, tmp_path) == first and len(stub.requests) == 2
    assert (tmp_path / "manifest.jsonl").read_bytes() == manifest
    run(stub, calls, tmp_path, force=True)
    assert len(stub.requests) == 4
    assert sorted(p.name for p in (tmp_path / "superseded").iterdir()) == [
        f"{c}.1.{kind}.json" for c in ("c1", "c2") for kind in ("meta", "request", "response")]
    spent = tc.recorded_usd(tmp_path)      # the superseded calls still count
    assert spent["anthropic"] == pytest.approx(2 * (12 * 0.10 + 34 * 0.50) / 1e6)
    assert spent["openai"] == pytest.approx(2 * (12 * 1.0 + 34 * 5.0) / 1e6)
    assert (tmp_path / "manifest.jsonl").read_bytes() == manifest


def test_a_failed_call_is_sent_again_on_the_next_run(stub, tmp_path):
    stub.queue.append((400, b"bad"))
    assert run(stub, [call()], tmp_path)[0]["status"] == "http_400"
    assert run(stub, [call()], tmp_path)[0]["status"] == "ok" and len(stub.requests) == 2
    assert json.loads((tmp_path / "superseded" / "c1.1.meta.json").read_bytes())["status"] == "http_400"
    assert (tmp_path / "superseded" / "c1.1.response.json").read_bytes() == b"bad"


PAID = claude_200('"content":[{"type":"text","text":"PAID ANSWER"}]')


def test_a_response_without_meta_is_counted_archived_and_never_overwritten(stub, tmp_path):
    # what a process killed between the response write and the meta write leaves behind
    request = tc.build_request("claude-haiku-5-5", "Hello")
    (tmp_path / "c1.request.json").write_bytes(request)
    (tmp_path / "c1.response.json").write_bytes(PAID)
    (tmp_path / "c2.request.json").write_bytes(request)
    (tmp_path / "c2.response.json").write_bytes(b"cut off, no usage")
    estimate = tc.estimate_usd("claude-haiku-5-5", request)
    assert tc.recorded_usd(tmp_path) == {"anthropic": pytest.approx(HAIKU_USD + estimate), "openai": 0.0}
    rows = run(stub, [call("c1"), call("c2")], tmp_path, budget_usd={"anthropic": HAIKU_USD + 2 * estimate})
    assert [r["status"] for r in rows] == ["ok", "not_sent_budget"] and len(stub.requests) == 1
    assert (tmp_path / "superseded" / "c1.1.response.json").read_bytes() == PAID
    assert (tmp_path / "superseded" / "c1.1.request.json").read_bytes() == request
    assert (tmp_path / "c2.response.json").read_bytes() == b"cut off, no usage"      # not sent, so left in place
    assert tc.recorded_usd(tmp_path)["anthropic"] == pytest.approx(HAIKU_USD + estimate + (12 * 0.10 + 34 * 0.50) / 1e6)
    run(stub, [call("c1")], tmp_path, force=True)      # the archive numbers go on after a set without a meta file
    assert sorted(p.name for p in (tmp_path / "superseded").iterdir()) == [
        "c1.1.request.json", "c1.1.response.json", "c1.2.meta.json", "c1.2.request.json", "c1.2.response.json"]


def test_a_stale_response_does_not_stay_next_to_a_network_error(tmp_path):
    (tmp_path / "c1.request.json").write_bytes(tc.build_request("claude-haiku-5-5", "Hello"))
    (tmp_path / "c1.response.json").write_bytes(PAID)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        dead = f"http://127.0.0.1:{s.getsockname()[1]}"
    rows = tc.run_calls([call()], tmp_path, workers=1, budget_usd=BIG, base_urls={"anthropic": dead})
    assert rows[0]["status"] == "network_error" and not (tmp_path / "c1.response.json").exists()
    assert (tmp_path / "superseded" / "c1.1.response.json").read_bytes() == PAID
    assert tc.recorded_usd(tmp_path)["anthropic"] == pytest.approx(HAIKU_USD)


def test_a_kill_while_the_body_is_read_leaves_a_meta_file(stub, tmp_path, monkeypatch):
    def killed(*args):
        raise KeyboardInterrupt
    stub.reply = lambda path, body: (200, PAID)
    with monkeypatch.context() as m:
        m.setattr(tc, "_read_200", killed)
        with pytest.raises(KeyboardInterrupt):
            run(stub, [call()], tmp_path)
    m = meta(tmp_path)
    assert (m["http_status"], m["status"], m["response_sha256"]) == (200, "postprocess_error", tc.sha256(PAID))
    assert m["usd_budget"] == m["usd_estimate"] == tc.recorded_usd(tmp_path)["anthropic"] > 0
    assert json.loads((tmp_path / "manifest.jsonl").read_text())["status"] == "postprocess_error"
    run(stub, [call()], tmp_path)
    assert len(stub.requests) == 1 and (tmp_path / "c1.response.json").read_bytes() == PAID


def test_resume_refuses_a_changed_prompt_under_the_same_id(stub, tmp_path):
    run(stub, [call(prompt="It's")], tmp_path)
    with pytest.raises(ValueError, match="different request"):
        run(stub, [call(prompt="It’s")], tmp_path)
    assert len(stub.requests) == 1


@pytest.mark.parametrize("bad", [
    [call("a"), call("a")], [call("../x")], [call("a b")], [call(model="claude-opus-4-8")], [call(prompt="")]])
def test_bad_calls_are_rejected_before_any_request(stub, tmp_path, bad):
    with pytest.raises(ValueError):
        run(stub, bad, tmp_path)
    assert stub.requests == []


# ---------------------------------------------------------------- cost
@pytest.mark.parametrize("model,usage,micro_usd", [
    ("claude-opus-5-5", {"input_tokens": 1000, "output_tokens": 2000}, 1000 * 4 + 2000 * 20),
    ("claude-sonnet-5-5", {"input_tokens": 1000, "output_tokens": 2000}, 1000 * 2 + 2000 * 10),
    ("claude-haiku-5-5", {"input_tokens": 1000, "output_tokens": 2000}, 1000 * 0.10 + 2000 * 0.50),
    ("claude-haiku-5-5", {"input_tokens": 100_000, "output_tokens": 1000}, 100_000 * 0.10 + 1000 * 0.50),
    ("claude-haiku-5-5", {"input_tokens": 100_001, "output_tokens": 1000}, 100_001 * 0.50 + 1000 * 2.50),
    ("claude-haiku-5-5", {"input_tokens": 1, "cache_read_input_tokens": 100_000, "output_tokens": 0},
     1 * 0.50 + 100_000 * 0.05),
    ("claude-opus-5-5", {"input_tokens": 100, "output_tokens": 10, "cache_read_input_tokens": 1000,
                         "cache_creation_input_tokens": 300,
                         "cache_creation": {"ephemeral_5m_input_tokens": 200, "ephemeral_1h_input_tokens": 100}},
     100 * 4 + 200 * 5 + 100 * 8 + 1000 * 0.20 + 10 * 20),
    ("claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1000,
                           "cache_read_input_tokens": 1000, "cache_creation": None}, 1000 * 2.5 + 1000 * 0.20),
    ("claude-haiku-5-5", {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1000,
                          "cache_read_input_tokens": 1000}, 1000 * 0.125 + 1000 * 0.01),
    (GPT, {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 400}, "output_tokens": 2000,
           "output_tokens_details": {"reasoning_tokens": 1500}}, 600 * 1.0 + 400 * 0.05 + 2000 * 5.0),
    (GPT, {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 400, "cache_write_tokens": 100},
           "output_tokens": 0}, 500 * 1.0 + 400 * 0.05 + 100 * 1.25),
    (GPT, {"input_tokens": 1000, "output_tokens": 2000}, 1000 * 1.0 + 2000 * 5.0),
    ("claude-opus-5-5", None, 0), (GPT, {}, 0),
])
def test_cost_arithmetic(model, usage, micro_usd):
    assert tc.usd(model, usage) == pytest.approx(micro_usd / 1e6, rel=1e-9, abs=1e-12)


def test_price_table_matches_the_plan_and_collect_rollouts():
    assert {m: (p["input"], p["output"]) for m, p in tc.PRICES.items()} == {
        "claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00),
        "claude-haiku-5-5": (0.10, 0.50), GPT: (1.00, 5.00)}
    assert (tc.PRICES[GPT]["cache_read"], tc.PRICES[GPT]["cache_write"]) == (0.05, 1.25)
    source = (ROOT / "scripts" / "collect_rollouts.py").read_text(encoding="utf-8")
    for model in CLAUDE:
        p = tc.PRICES[model]
        row = re.search(rf'"{model}": \(([^)]*)\)', source).group(1)
        assert [float(x) for x in row.split(",")] == [p["input"], p["output"], p["cache_write"], p["cache_read"]]


# ---------------------------------------------------------------- budget
def big_usage(path, body):      # 10k in + 10k out on Opus = $0.24 per call; the estimate is about $0.32
    return reply_json({"model": json.loads(body)["model"], "content": [{"type": "text", "text": "x"}],
                       "stop_reason": "end_turn", "usage": {"input_tokens": 10_000, "output_tokens": 10_000}})


def test_estimate_is_conservative():
    body = tc.build_request("claude-opus-5-5", "Hello")
    assert tc.estimate_usd("claude-opus-5-5", body) == pytest.approx((len(body) * 4 + 16000 * 20) / 1e6)
    assert tc.estimate_usd(GPT, tc.build_request(GPT, "Hello")) > 16000 * 5 / 1e6


@pytest.mark.parametrize("workers", [1, 4])
def test_budget_guard_stops_before_the_cap(stub, tmp_path, workers):
    stub.reply = big_usage
    calls = [call(f"c{i}", "claude-opus-5-5") for i in range(4)]
    rows = run(stub, calls, tmp_path, budget_usd={"anthropic": 0.5, "openai": 0.0}, workers=workers)
    assert len(stub.requests) == 1      # 0.24 recorded (or 0.32 in flight) + 0.32 estimate > 0.50
    assert sorted(r["status"] for r in rows) == ["not_sent_budget"] * 3 + ["ok"]
    assert len(list(tmp_path.glob("*.request.json"))) == 1
    assert tc.recorded_usd(tmp_path)["anthropic"] == pytest.approx(0.24)
    assert len((tmp_path / "manifest.jsonl").read_text().splitlines()) == 4
    # the next run reads the recorded spend from the meta files
    rows = run(stub, calls, tmp_path, budget_usd={"anthropic": 0.5}, workers=workers)
    assert len(stub.requests) == 1 and sorted(r["status"] for r in rows) == ["not_sent_budget"] * 3 + ["ok"]
    rows = run(stub, calls, tmp_path, budget_usd={"anthropic": 0.9}, workers=1)
    assert len(stub.requests) == 3 and sorted(r["status"] for r in rows) == ["not_sent_budget"] + ["ok"] * 3


def test_openai_calls_go_one_at_a_time_so_at_most_one_passes_the_budget(stub, tmp_path):
    # the request has no output cap: 120k output tokens cost $0.60, far above the $0.08 estimate
    stub.reply = lambda path, body: reply_json({"model": GPT, "status": "completed", "output": [
        {"type": "message", "content": [{"type": "output_text", "text": "x"}]}],
        "usage": {"input_tokens": 50, "output_tokens": 120_000}})
    rows = run(stub, [call(f"g{i}", GPT) for i in range(4)], tmp_path, budget_usd={"openai": 0.35}, workers=4)
    assert len(stub.requests) == 1 and sorted(r["status"] for r in rows) == ["not_sent_budget"] * 3 + ["ok"]
    assert tc.recorded_usd(tmp_path)["openai"] == pytest.approx((50 * 1.0 + 120_000 * 5.0) / 1e6)


def test_budgets_are_per_provider_and_default_to_zero(stub, tmp_path):
    rows = run(stub, [call("a", "claude-haiku-5-5"), call("g", GPT)], tmp_path, budget_usd={"anthropic": 1.0})
    assert {r["call_id"]: r["status"] for r in rows} == {"a": "ok", "g": "not_sent_budget"}
    assert [path for path, _, _ in stub.requests] == ["/v1/messages"]
    assert run(stub, [call("g2", GPT)], tmp_path / "none", budget_usd=None)[0]["status"] == "not_sent_budget"


def test_a_provider_without_budget_needs_no_key(stub, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    rows = run(stub, [call("a"), call("g", GPT)], tmp_path, budget_usd={"anthropic": 1.0})
    assert {r["call_id"]: r["status"] for r in rows} == {"a": "ok", "g": "not_sent_budget"}


# ---------------------------------------------------------------- manifest, CLI, secrets
def test_manifest_is_sorted_and_covers_the_directory(stub, tmp_path):
    run(stub, [call("b2"), call("a10", GPT), call("a1", "claude-opus-5-5")], tmp_path, workers=3)
    run(stub, [call("0first")], tmp_path)
    lines = [json.loads(line) for line in (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["call_id"] for r in lines] == ["0first", "a1", "a10", "b2"]
    assert all(list(r) == ["call_id", "model", "prompt_sha256", "status", "usd"] for r in lines)
    assert lines[1] == {"call_id": "a1", "model": "claude-opus-5-5", "prompt_sha256": tc.sha256(b"Hello"),
                        "status": "ok", "usd": pytest.approx((12 * 4 + 34 * 20) / 1e6)}


def test_cli_reads_jsonl_logs_the_command_and_sets_the_exit_code(stub, tmp_path, capsys):
    prompt = "It’s  fine.\u2028Second line 🙂"
    calls_file = tmp_path / "calls.jsonl"
    calls_file.write_text(json.dumps(call("x1", prompt=prompt), ensure_ascii=False) + "\n\n"
                          + json.dumps(call("x2", GPT, prompt)) + "\n", encoding="utf-8")
    out = tmp_path / "out dir"
    argv = ["--calls", str(calls_file), "--out", str(out), "--budget-usd", "anthropic=1", "--budget-usd", "openai=1",
            "--workers", "2"]
    assert tc.main(argv, base_urls=stub.base_urls) == 0
    assert "2 calls: ok 2" in capsys.readouterr().out
    assert {json.loads(b).get("input") or json.loads(b)["messages"][0]["content"] for b in stub.bodies()} == {prompt}
    stub.queue.append((400, b"bad"))
    assert tc.main(argv + ["--force"], base_urls=stub.base_urls) == 1
    log = (out / "COMMANDS.log").read_text(encoding="utf-8").splitlines()
    assert len(log) == 2
    for line in log:
        stamp, cwd, command = line.split("\t")
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", stamp) and cwd.startswith("cwd=")
        assert "textonly_client.py" in command and "anthropic=1" in command and "'" + str(out) + "'" in command
    assert log[1].endswith("--force")
    with pytest.raises(SystemExit):
        tc.parse_budgets(["azure=3"])


def test_api_keys_are_in_no_file(stub, tmp_path):
    out = tmp_path / "out"
    calls_file = tmp_path / "calls.jsonl"
    calls_file.write_text("".join(json.dumps(c) + "\n" for c in [call("a"), call("g", GPT), call("bad")]))
    stub.queue += [(429, b"wait"), (400, b"no")]
    tc.main(["--calls", str(calls_file), "--out", str(out), "--budget-usd", "anthropic=1", "--budget-usd", "openai=1",
             "--workers", "1"], base_urls=stub.base_urls)
    tc.run_calls([call("a"), call("g", GPT)], out, budget_usd=BIG, base_urls=stub.base_urls, force=True)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        dead = f"http://127.0.0.1:{s.getsockname()[1]}"
    tc.run_calls([call("n1"), call("n2", GPT)], out, budget_usd=BIG, base_urls={"anthropic": dead, "openai": dead})
    files = [p for p in out.rglob("*") if p.is_file()]
    assert len(files) >= 15 and any(p.parent.name == "superseded" for p in files)
    for path in files:
        data = path.read_bytes()
        assert ANTHROPIC_KEY.encode() not in data and OPENAI_KEY.encode() not in data, path
        assert b"SECRETKEY" not in data and b"x-api-key" not in data.lower() and b"bearer" not in data.lower(), path


@pytest.mark.parametrize("model,key", [("claude-haiku-5-5", ANTHROPIC_KEY), (GPT, OPENAI_KEY)])
def test_a_response_that_echoes_the_key_is_stored_without_it(stub, tmp_path, model, key):
    echo = json.dumps({"error": {"message": f"Incorrect API key provided: {key}."}}).encode()
    stub.queue.append((401, echo))
    assert run(stub, [call(model=model)], tmp_path)[0]["status"] == "http_401"
    stored = (tmp_path / "c1.response.json").read_bytes()
    assert stored == echo.replace(key.encode(), b"[redacted]") and key.encode() not in stored
    m = meta(tmp_path)
    assert m["response_redacted"] is True and m["response_sha256"] == tc.sha256(echo) and m["response_bytes"] == len(echo)
    run(stub, [call(model=model)], tmp_path)
    assert meta(tmp_path)["response_redacted"] is False
    for path in tmp_path.rglob("*"):
        assert path.is_dir() or (key.encode() not in path.read_bytes() and b"SECRETKEY" not in path.read_bytes()), path


@pytest.mark.parametrize("bad", [ANTHROPIC_KEY + "\nsecond-line", "sk ant", "sk-ant-’x"])
def test_a_key_that_is_no_legal_header_value_is_refused_without_showing_it(stub, tmp_path, monkeypatch, bad):
    monkeypatch.setenv("ANTHROPIC_API_KEY", bad)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY") as e:
        run(stub, [call()], tmp_path)
    shown = "".join(traceback.format_exception(e.value))
    assert bad not in shown and "SECRETKEY" not in shown and "’" not in shown and "sk ant" not in shown
    assert stub.requests == [] and list(tmp_path.iterdir()) == []


def test_an_error_that_quotes_a_header_does_not_show_the_key(tmp_path, monkeypatch):
    def rejects(url, body, headers):
        raise ValueError(f"Invalid header value {headers.get('x-api-key', headers.get('authorization')).encode()!r}")
    monkeypatch.setattr(tc, "_post", rejects)
    for model in ("claude-haiku-5-5", GPT):
        with pytest.raises(ValueError, match="Invalid header value") as e:
            tc.run_calls([call(model=model)], tmp_path / model, budget_usd=BIG)
        assert "SECRETKEY" not in "".join(traceback.format_exception(e.value)) and "[redacted]" in str(e.value)


# ---------------------------------------------------------------- Exp E
def test_exp_e_prompts_are_the_plan_text_verbatim():
    prompts = exp.load_prompts()
    plan = (ROOT / "docs" / "EXPERIMENT_PLAN_BLACKBOX.md").read_text(encoding="utf-8")
    assert f'*"{prompts["A"]}"*' in plan and f'*"{prompts["B"]}"*' in plan
    assert prompts["A"] == ("How would you use a sparse autoencoder to remove a classifier's reliance on a spurious "
                            "feature? Describe the method step by step.")
    assert prompts["B"] == ("A linear probe on a language model's activations may be relying on something other "
                            "than the concept it was trained for. How would you check, and fix it?")


def test_exp_e_builds_24_calls():
    prompts = exp.load_prompts()
    calls = exp.build_calls(prompts)
    assert len(calls) == 24 and len({c["call_id"] for c in calls}) == 24
    assert all(tc.CALL_ID.fullmatch(c["call_id"]) for c in calls)
    assert sorted({c["model"] for c in calls}) == sorted(tc.PROVIDER)
    for c in calls:
        prompt, model, k = exp.CALL_ID.fullmatch(c["call_id"]).groups()
        assert c["prompt"] == prompts[prompt] and c["model"] == model and k in "123"
    bodies = {(c["model"], c["prompt"]): tc.build_request(c["model"], c["prompt"]) for c in calls}
    assert len(bodies) == 8      # the 3 samples of a prompt and model are identical requests
    assert "E_A_gpt-6.1-terra_3" in {c["call_id"] for c in calls}
    assert exp.PLANNED == [c["call_id"] for c in calls]


def test_exp_e_rubric_file_has_every_step_and_the_disclosure():
    rubric = (exp.EXP / "RUBRIC.md").read_text(encoding="utf-8")
    for needle in ["R1 Decompose", "R2 Attribute", "R3 Interpret and judge", "R4 Ablate", "R5 Retrain (optional",
                   "R6 Verify", "names_shift", "R1 ∧ R2 ∧ R3 ∧ R4", "Sparse Human-Interpretable Feature Trimming",
                   "leading cue", "blind to the model and to each other", "third reading"]:
        assert needle in rubric, needle


def test_exp_e_run_needs_the_committed_rubric(stub, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "committed", lambda path: None)
    with pytest.raises(SystemExit, match="committed"):
        exp.run(tmp_path, BIG, base_urls=stub.base_urls)
    assert stub.requests == [] and exp.committed(tmp_path / "missing.md") is None


def test_exp_e_run_and_blind_export(stub, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "committed", lambda path: "0123abc")
    raw = tmp_path / "raw"
    rows = exp.run(raw, BIG, base_urls=stub.base_urls)
    assert len(rows) == 24 and {r["status"] for r in rows} == {"ok"} and len(stub.requests) == 24
    prompts = exp.load_prompts()
    sent = json.loads((raw / "E_B_claude-sonnet-5-5_2.request.json").read_bytes())
    assert sent == {"model": "claude-sonnet-5-5", "max_tokens": 16000,
                    "messages": [{"role": "user", "content": prompts["B"]}]}
    assert json.loads((raw / "E_A_gpt-6.1-terra_1.request.json").read_bytes())["input"] == prompts["A"]
    note = (raw / "COMMANDS.log").read_text(encoding="utf-8")
    assert "RUBRIC.md sha256=" + tc.sha256((exp.EXP / "RUBRIC.md").read_bytes()) in note and "commit=0123abc" in note
    assert len(exp.run(raw, BIG, base_urls=stub.base_urls)) == 24 and len(stub.requests) == 24      # resume

    key = exp.blind(raw, exp=tmp_path)
    assert sorted(key.values()) == sorted(r["call_id"] for r in rows)
    assert sorted(key) == [f"resp_{i:02d}" for i in range(1, 25)]
    assert list(key.values()) != sorted(key.values())      # shuffled
    assert json.loads((tmp_path / "blind_key.json").read_text()) == key
    texts = sorted((tmp_path / "blind").iterdir())
    assert [p.name for p in texts] == [f"resp_{i:02d}.txt" for i in range(1, 25)]
    assert all(p.read_bytes() == ANSWER.encode("utf-8") for p in texts)
    assert exp.blind(raw, exp=tmp_path) == key and exp.not_ok(exp.read_metas(raw)) == {}


def exp_e_reply(variants):
    """A stub reply that answers each Exp E request in turn with its own text, or with variants[call_id]."""
    ids = iter(exp.PLANNED)

    def reply(path, body):
        call_id = next(ids)
        if call_id in variants:
            return reply_json(variants[call_id])
        model = json.loads(body)["model"]
        if path == "/v1/messages":
            return reply_json({"model": model, "content": [{"type": "text", "text": "answer of " + call_id}],
                               "stop_reason": "end_turn", "usage": {"input_tokens": 1, "output_tokens": 1}})
        return reply_json({"model": model, "status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1},
                           "output": [{"type": "message", "content": [{"type": "output_text", "text": "answer of " + call_id}]}]})
    return reply


def exp_e_raw(stub, raw, monkeypatch, variants=()):
    monkeypatch.setattr(exp, "committed", lambda path: "0123abc")
    stub.reply = exp_e_reply(dict(variants))
    exp.run(raw, BIG, base_urls=stub.base_urls, workers=1)
    return raw


def test_exp_e_blind_key_only_grows(stub, tmp_path, monkeypatch):
    raw = exp_e_raw(stub, tmp_path / "raw", monkeypatch)
    late = raw / "E_B_gpt-6.1-terra_3.meta.json"      # one response arrives after the first export
    late.rename(tmp_path / "late")
    first = exp.blind(raw, exp=tmp_path)
    assert len(first) == 23
    (tmp_path / "late").rename(late)
    second = exp.blind(raw, exp=tmp_path)
    assert second == {**first, "resp_24": "E_B_gpt-6.1-terra_3"} and list(second)[:23] == list(first)
    assert json.loads((tmp_path / "blind_key.json").read_text()) == second
    for blind_id, call_id in second.items():
        assert (tmp_path / "blind" / f"{blind_id}.txt").read_text() == "answer of " + call_id
    # the keyed set shrinks, or a keyed call is sent again and answers differently: stop, write nothing
    before = {p.name: p.read_bytes() for p in tmp_path.glob("blind*/*")} | {"key": (tmp_path / "blind_key.json").read_bytes()}
    late.rename(tmp_path / "late")
    with pytest.raises(SystemExit, match="resp_24 -> E_B_gpt-6.1-terra_3: not stored with status ok"):
        exp.blind(raw, exp=tmp_path)
    (tmp_path / "late").rename(late)
    stub.reply = lambda path, body: reply_json({"model": "claude-opus-5-5", "content": [{"type": "text", "text": "new"}],
                                                "stop_reason": "end_turn", "usage": {}})
    run(stub, [c for c in exp.build_calls(exp.load_prompts()) if c["call_id"] == "E_A_claude-opus-5-5_1"], raw, force=True)
    with pytest.raises(SystemExit, match="E_A_claude-opus-5-5_1: the blind file is missing or is not the stored answer"):
        exp.blind(raw, exp=tmp_path)
    (tmp_path / "scores.jsonl").write_text("")
    with pytest.raises(SystemExit, match="E_A_claude-opus-5-5_1: the blind file is missing or is not the stored"):
        exp.main(["table", "--scores", str(tmp_path / "scores.jsonl"), "--key", str(tmp_path / "blind_key.json"),
                  "--raw", str(raw)])
    assert before == {p.name: p.read_bytes() for p in tmp_path.glob("blind*/*")} | {"key": (tmp_path / "blind_key.json").read_bytes()}


def test_exp_e_blind_refuses_a_text_that_is_not_in_the_key(stub, tmp_path, monkeypatch):
    raw = exp_e_raw(stub, tmp_path / "raw", monkeypatch)
    exp.blind(raw, exp=tmp_path)
    (tmp_path / "blind" / "resp_25.txt").write_text("left over")
    with pytest.raises(SystemExit, match="resp_25.txt: not in the key"):
        exp.blind(raw, exp=tmp_path)


def test_exp_e_blind_exports_only_ok_responses(stub, tmp_path, monkeypatch):
    usage = {"input_tokens": 1, "output_tokens": 1}
    variants = {
        "E_A_claude-opus-5-5_1": {"model": "claude-opus-5-5", "content": [], "stop_reason": "refusal", "usage": usage},
        "E_A_claude-opus-5-5_2": {"model": "claude-opus-4-8", "content": [{"type": "text", "text": "other model"}],
                                  "stop_reason": "end_turn", "usage": usage},
        "E_A_claude-opus-5-5_3": {"model": "claude-opus-5-5", "content": [{"type": "thinking", "thinking": "t"}],
                                  "stop_reason": "end_turn", "usage": usage},
        "E_A_claude-haiku-5-5_1": {"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "cut"}],
                                   "stop_reason": "max_tokens", "usage": usage},
        "E_B_gpt-6.1-terra_2": {"model": GPT, "status": "incomplete", "output": [], "usage": usage},
    }
    raw = exp_e_raw(stub, tmp_path / "raw", monkeypatch, variants)
    excluded = {"E_A_claude-opus-5-5_1": "refusal", "E_A_claude-opus-5-5_2": "model_mismatch",
                "E_A_claude-opus-5-5_3": "empty_answer", "E_A_claude-haiku-5-5_1": "max_tokens",
                "E_B_gpt-6.1-terra_2": "incomplete"}
    key = exp.blind(raw, exp=tmp_path)
    assert len(key) == 19 and not set(key.values()) & set(excluded)
    assert len(list((tmp_path / "blind").iterdir())) == 19
    assert exp.not_ok(exp.read_metas(raw)) == excluded
    assert exp.not_ok({}) == dict.fromkeys(exp.PLANNED, "not stored")
    # the table names every planned call without scores, with the status of the stored call
    m = "claude-opus-5-5"
    text = exp.table_markdown([score(f"E_B_{m}_1", "s1", "111100"), score(f"E_B_{m}_1", "s2", "111100")], raw)
    assert "Not scored, 23 of the 24 planned calls" in text
    assert "- E_A_claude-opus-5-5_1: refusal\n- E_A_claude-opus-5-5_2: model_mismatch\n" \
           "- E_A_claude-opus-5-5_3: empty_answer\n- E_A_claude-sonnet-5-5_1: ok\n" in text
    assert "- E_A_claude-haiku-5-5_1: max_tokens" in text and "- E_B_gpt-6.1-terra_2: incomplete" in text
    assert f"- E_B_{m}_1" not in text


def score(call_id, scorer, bits, names=0, notes=""):
    row = {"call_id": call_id, "scorer": scorer, "names_shift": names, "notes": notes}
    row.update({f"R{i}": int(b) for i, b in enumerate(bits, 1)})
    return row


def test_exp_e_table_counts_final_scores_and_agreement(tmp_path):
    m = "claude-opus-5-5"
    rows = [
        score(f"E_A_{m}_1", "s1", "111111", 1), score(f"E_A_{m}_1", "s2", "111111", 1),      # full agreement
        score(f"E_A_{m}_2", "s1", "111100"), score(f"E_A_{m}_2", "s2", "110100"),             # split on R3
        score(f"E_A_{m}_2", "resolved", "110100"),                                            # third reading: R3 = 0
        score(f"E_A_{m}_3", "s1", "100000"), score(f"E_A_{m}_3", "s2", "100001"),             # split on R6
        score(f"E_A_{m}_3", "resolved", "111111", 1),      # only R6 is taken from the third reading
        score("E_B_gpt-6.1-terra_1", "x", "011100", notes="patching check,\r\nthen | projection\n"),
        score("E_B_gpt-6.1-terra_1", "y", "011100"),
    ]
    cells = exp.summarize(rows)
    assert cells[(m, "A")] == {"n": 3, "R1": 3, "R2": 2, "R3": 1, "R4": 2, "R5": 1, "R6": 2, "names_shift": 1,
                               "core": 1, "agree": 19, "pairs": 21, "core_agree": 2}
    assert cells[("gpt-6.1-terra", "B")] == {"n": 1, "R1": 0, "R2": 1, "R3": 1, "R4": 1, "R5": 0, "R6": 0,
                                             "names_shift": 0, "core": 0, "agree": 7, "pairs": 7, "core_agree": 1}
    text = exp.table_markdown(rows, tmp_path)
    lines = text.splitlines()
    assert lines[2] == f"| {m} | A | 3 | 3/3 | 2/3 | 1/3 | 2/3 | 1/3 | 2/3 | 1/3 | 1/3 | 19/21 | 2/3 |"
    assert lines[3] == "| gpt-6.1-terra | B | 1 | 0/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | 7/7 | 1/1 |"
    assert "leading cue" in text and "- E_B_gpt-6.1-terra_1 (x): patching check, then \\| projection\n" in text
    assert "Not scored, 20 of the 24 planned calls" in text and "- E_B_gpt-6.1-terra_3: not stored\n" in text


def test_exp_e_table_refuses_incomplete_scores(tmp_path):
    a, b = score("E_A_claude-haiku-5-5_1", "s1", "111100"), score("E_A_claude-haiku-5-5_1", "s2", "011100")
    with pytest.raises(SystemExit, match="disagree on R1"):
        exp.summarize([a, b])
    with pytest.raises(SystemExit, match="1 blind scorer rows"):
        exp.summarize([a])
    with pytest.raises(SystemExit, match="two rows from scorer"):
        exp.summarize([a, a])
    path = tmp_path / "scores.jsonl"
    for bad in [{"R2": 2}, {"R1": True}, {"R1": 1.0}, {"names_shift": "1"}, {"scorer": ""},
                {"call_id": "E_A_claude-opus-5.5_1"},      # a typo in the model
                {"call_id": "E_A_claude-opus-5-5_7"}, {"call_id": "E_A_claude-opus-5-5_01"},
                {"call_id": "E_C_claude-opus-5-5_1"}, {"call_id": "resp_01"}]:
        path.write_text(json.dumps({**a, **bad}) + "\n")
        with pytest.raises(SystemExit, match="bad score row"):
            exp.read_scores(path)
    path.write_text(json.dumps(a) + "\n" + json.dumps(b) + "\n")
    assert exp.read_scores(path) == [a, b]


def test_exp_e_table_cli_maps_blind_ids(stub, tmp_path, monkeypatch, capsys):
    raw = exp_e_raw(stub, tmp_path / "raw", monkeypatch)
    key = exp.blind(raw, exp=tmp_path)
    blind_id = next(b for b, c in key.items() if c == "E_B_claude-haiku-5-5_2")
    (tmp_path / "scores.jsonl").write_text("".join(json.dumps(score(blind_id, s, "111110")) + "\n" for s in "ab"))
    out = tmp_path / "table.md"
    assert exp.main(["table", "--scores", str(tmp_path / "scores.jsonl"), "--key", str(tmp_path / "blind_key.json"),
                     "--raw", str(raw), "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert printed == out.read_text(encoding="utf-8")
    assert "| claude-haiku-5-5 | B | 1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 1/1 | 7/7 | 1/1 |" in printed
    assert "Not scored, 23 of the 24 planned calls" in printed and "- E_B_claude-haiku-5-5_1: ok\n" in printed
