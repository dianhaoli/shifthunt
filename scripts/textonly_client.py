"""Text-only API client for Exp D and Exp E (plan §6): one user prompt in, one answer out, raw HTTP.

    python scripts/textonly_client.py --calls calls.jsonl --out DIR \
        --budget-usd anthropic=5 --budget-usd openai=2 [--workers 4] [--force]

calls.jsonl has one JSON object per line: {"call_id", "model", "prompt"}. Keys come from the environment
(ANTHROPIC_API_KEY; OPENAI_API_KEY, falling back to OPENAI_KEY) and are sent as a header only.

Standard library only (urllib), no SDK, because the exact request and response bytes must be stored.
Every request uses the provider defaults: no system prompt, no tools, no sampling parameters, no thinking or
effort fields and no server-side model fallback (a refusal stays a refusal).
  claude-opus-5-5 / claude-sonnet-5-5 / claude-haiku-5-5: POST /v1/messages with
      {"model": m, "max_tokens": 16000, "messages": [{"role": "user", "content": PROMPT}]}
  gpt-6.1-terra: POST /v1/responses with {"model": m, "input": PROMPT, "store": false}

What is stored, per call, in <out>:
  <call_id>.request.json   the request body, byte for byte as sent; written before sending
  <call_id>.response.json  the body of the last HTTP response, byte for byte as received (any status);
                           absent if no attempt got an HTTP response. The one exception: if the body holds
                           the API key, the key is replaced by [redacted] before the body is stored, and the
                           meta file says response_redacted true (its response_sha256 is of the bytes received)
  <call_id>.meta.json      call_id, provider, model, url, the request headers without the key, sha256 of the
                           prompt, request and response bytes, HTTP status, the response headers request-id /
                           x-request-id / date, start and end time (UTC), every attempt (time, HTTP status or
                           network error, sha256 of its response body), the model named in the response, the
                           API usage object as returned, USD, stop reason and details, the content block
                           types, sha256 and length of the answer text, and a one-word status. It is written
                           right after the response file, before the body is read, and again once the body
                           has been read, so a stored response has a meta file whatever the body holds
and per directory:
  manifest.jsonl           one line per call (call_id, model, prompt_sha256, status, usd), sorted by call_id,
                           rewritten at the end of every run from the meta files
  COMMANDS.log             one appended line per CLI run: UTC time, working directory, exact command line
  superseded/              the files of a call that was sent again (--force, or a new try after a
                           failure), renamed to <call_id>.<n>.*; their USD still counts towards the budget.
                           A stored response is never overwritten: it is moved here first
The API key is never written. Answer text is not stored separately: extract_answer() reads it from the
response file, and the meta file holds its sha256.

Status: "ok" (HTTP 200, the requested model, a normal stop and a non-empty answer text), otherwise
"model_mismatch", the stop reason ("refusal", "max_tokens", "incomplete", ...), "empty_answer", "bad_json"
(a 200 whose body is not a JSON object), "postprocess_error" (a 200 whose JSON is not of the expected shape;
the meta field postprocess_error says why), "http_<code>", "network_error" or "not_sent_budget".
Retries: HTTP 429, HTTP >= 500 and network errors, at most 6 attempts, exponential backoff with jitter.
Other 4xx are not retried. A 200 is never retried, whatever its stop reason.
Resume: a call with a stored HTTP 200 response is not sent again unless --force.
Cost: the API usage object times the list prices in PRICES, one source per engine.
Budget: a call is not sent if the USD recorded in <out> for its provider, plus calls in flight, plus a
conservative estimate of this call would exceed that provider's --budget-usd. A provider without a budget
gets 0, so nothing is sent to it. The estimate (the request bytes as input tokens plus 16000 output tokens)
is an upper bound for Claude, whose requests cap the output at 16000 tokens. It is NOT a bound for
gpt-6.1-terra, whose request has no output cap: there the guard works after the fact, so OpenAI calls are
sent one at a time whatever --workers says, and the OpenAI spend can pass its budget by at most the cost of
one call. A 200 whose usage object cannot be read, and a response file left without a meta file by a killed
process, count towards the budget at the estimate (meta field usd_budget; usd stays what the usage object
says). A network error after the provider has started work can cost money that no usage object reports; the
budget cannot see that.
"""
import argparse
import contextlib
import hashlib
import http.client
import json
import os
import random
import re
import shlex
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ANTHROPIC, OPENAI = "anthropic", "openai"
PROVIDER = {"claude-opus-5-5": ANTHROPIC, "claude-sonnet-5-5": ANTHROPIC, "claude-haiku-5-5": ANTHROPIC,
            "gpt-6.1-terra": OPENAI}
BASE_URLS = {ANTHROPIC: "https://api.anthropic.com", OPENAI: "https://api.openai.com"}
ENDPOINT = {ANTHROPIC: "/v1/messages", OPENAI: "/v1/responses"}
KEY_ENV = {ANTHROPIC: ("ANTHROPIC_API_KEY",), OPENAI: ("OPENAI_API_KEY", "OPENAI_KEY")}
NORMAL_STOP = {ANTHROPIC: "end_turn", OPENAI: "completed"}
SECRET_HEADERS = ("x-api-key", "authorization")
KEPT_RESPONSE_HEADERS = ("request-id", "x-request-id", "date")
USER_AGENT = "textonly-client/1.0"
MAX_TOKENS = 16000          # Claude output cap per call; the OpenAI request sets no cap
MAX_ATTEMPTS = 6
BACKOFF_BASE_S, BACKOFF_CAP_S = 2.0, 60.0
TIMEOUT_S = 900
CALL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

# USD per million tokens, list prices. Sources: the Anthropic price table of 2026-11-03 (Claude input and
# output, and the Haiku rates for prompts over 100K tokens) and the main-study env file (gpt-6.1-terra).
# Claude cache write (5 min) and cache read are the values in scripts/collect_rollouts.py PRICES; a 1 h cache
# write costs 2x input. The long-prompt Haiku cache rates are the short-prompt ones times 5, like its input.
# No request here asks for caching, so the cache terms only matter if a usage object reports such tokens.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_write": 5.00, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_write": 2.50, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_write": 0.125, "cache_read": 0.01},
    "gpt-6.1-terra": {"input": 1.00, "output": 5.00, "cache_write": 1.25, "cache_read": 0.05},
}
HAIKU_LONG_PROMPT_TOKENS = 100_000
HAIKU_LONG_PRICES = {"input": 0.50, "output": 2.50, "cache_write": 0.625, "cache_read": 0.05}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- request, answer, cost
def build_request(model, prompt):
    """The request body as bytes. It is serialised once: these bytes are both stored and sent."""
    if PROVIDER[model] == ANTHROPIC:
        body = {"model": model, "max_tokens": MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]}
    else:
        body = {"model": model, "input": prompt, "store": False}
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def request_headers(provider, key):
    headers = {"content-type": "application/json", "user-agent": USER_AGENT}
    if provider == ANTHROPIC:
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    else:
        headers["authorization"] = "Bearer " + key
    return headers


def api_key(provider):
    for name in KEY_ENV[provider]:
        key = os.environ.get(name, "").strip()
        if key and not re.fullmatch(r"[\x21-\x7e]+", key):      # http.client quotes a bad header value in its error
            raise RuntimeError(f"the API key in {name} holds a space, a line break or a non-ASCII character "
                               "(the key is not shown here)")
        if key:
            return key
    raise RuntimeError(f"no API key in the environment for {provider}: set {' or '.join(KEY_ENV[provider])}")


def content_parts(provider, response):
    """The content blocks of a parsed response: Claude's `content`, or every part of OpenAI's `output` items
    (an item without parts, such as a reasoning item, counts as one part of its own type)."""
    if provider == ANTHROPIC:
        return list(response.get("content") or [])
    parts = []
    for item in response.get("output") or []:
        parts += item.get("content") or [{"type": item.get("type")}]
    return parts


def extract_answer(provider, response):
    """The answer text of a parsed response: the `text` blocks (Claude) or `output_text` parts (OpenAI),
    concatenated in order. Thinking blocks, reasoning items and refusal parts are not part of it."""
    kind = "text" if provider == ANTHROPIC else "output_text"
    return "".join(p.get("text") or "" for p in content_parts(provider, response) if p.get("type") == kind)


def stop_info(provider, response):
    """-> (stop reason, details): Claude's stop_reason and stop_details, or OpenAI's status and
    incomplete_details. An OpenAI answer that holds a refusal part has the stop reason "refusal"."""
    if provider == ANTHROPIC:
        return response.get("stop_reason"), response.get("stop_details")
    refused = any(p.get("type") == "refusal" for p in content_parts(provider, response))
    return ("refusal" if refused else response.get("status")), response.get("incomplete_details")


def usd(model, usage):
    """List-price USD of one response from its API usage object (0.0 without one).
    Claude: input_tokens excludes cache tokens. OpenAI: input_tokens includes them, and output_tokens
    includes reasoning tokens."""
    u = usage or {}
    p = PRICES[model]
    n_out = u.get("output_tokens") or 0
    if PROVIDER[model] == ANTHROPIC:
        n_in = u.get("input_tokens") or 0
        n_read = u.get("cache_read_input_tokens") or 0
        n_write = u.get("cache_creation_input_tokens") or 0
        n_write_1h = (u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0
        if model == "claude-haiku-5-5" and n_in + n_read + n_write > HAIKU_LONG_PROMPT_TOKENS:
            p = HAIKU_LONG_PRICES
        write_usd = (n_write - n_write_1h) * p["cache_write"] + n_write_1h * 2 * p["input"]
    else:
        details = u.get("input_tokens_details") or {}
        n_read = details.get("cached_tokens") or 0
        n_write = details.get("cache_write_tokens") or 0
        n_in = (u.get("input_tokens") or 0) - n_read - n_write
        write_usd = n_write * p["cache_write"]
    return round((n_in * p["input"] + n_read * p["cache_read"] + write_usd + n_out * p["output"]) / 1e6, 8)


def estimate_usd(model, body):
    """Conservative cost of a call before it is sent: every request byte counted as an input token, plus
    MAX_TOKENS output tokens (Claude's cap; for OpenAI an assumption, since that request has no cap)."""
    return usd(model, {"input_tokens": len(body), "output_tokens": MAX_TOKENS})


# ---------------------------------------------------------------- HTTP
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is recorded as its 3xx status and never followed, so the key only goes to the given host."""

    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _post(url, body, headers):
    """-> (HTTP status, response headers, response body bytes). Raises on a network error."""
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with _OPENER.open(request, timeout=TIMEOUT_S) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def _backoff_s(attempt, headers):
    delay = min(BACKOFF_CAP_S, BACKOFF_BASE_S * 2 ** (attempt - 1)) * random.uniform(0.5, 1.5)
    try:
        return max(delay, min(BACKOFF_CAP_S, float(headers.get("retry-after"))))
    except (AttributeError, TypeError, ValueError):
        return delay


def send(url, body, headers):
    """POST with retries -> (status, headers, body bytes, attempts). status is None if the last attempt
    got no HTTP response. attempts has one record per attempt, failed ones included."""
    attempts = []
    for n in range(1, MAX_ATTEMPTS + 1):
        record = {"n": n, "at_utc": utc_now(), "http_status": None, "error": None, "response_sha256": None}
        status = resp_headers = data = None
        try:
            status, resp_headers, data = _post(url, body, headers)
            record.update(http_status=status, response_sha256=sha256(data))
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            record["error"] = _without_secrets(f"{type(e).__name__}: {e}", headers)
        except ValueError as e:      # not a network error, so not retried; the message may quote a header
            raise ValueError(_without_secrets(str(e), headers)) from None
        attempts.append(record)
        if n == MAX_ATTEMPTS or not (status is None or status == 429 or status >= 500):
            break
        time.sleep(_backoff_s(n, resp_headers))
    return status, resp_headers, data, attempts


def _without_secrets(text, headers):
    for name in SECRET_HEADERS:
        for secret in {headers.get(name, ""), headers.get(name, "").removeprefix("Bearer ")} - {""}:
            text = text.replace(secret, "[redacted]")
    return text


# ---------------------------------------------------------------- files
def _write(path, data):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _json_bytes(obj):
    # backslashreplace: a lone surrogate from a response (e.g. "\ud83d") is written as that JSON escape
    return (json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8", "backslashreplace")


def _files(out, call_id):
    return {kind: out / f"{call_id}.{kind}.json" for kind in ("request", "response", "meta")}


def read_meta(out, call_id):
    path = _files(Path(out), call_id)["meta"]
    return json.loads(path.read_bytes()) if path.exists() else None


def _has_200(out, call_id):
    meta = read_meta(out, call_id)
    return bool(meta) and meta.get("http_status") == 200 and _files(out, call_id)["response"].exists()


def _supersede(out, call_id):
    """Move the stored files of a call that is about to be sent again into <out>/superseded/."""
    old = out / "superseded"
    old.mkdir(exist_ok=True)
    name = re.compile(re.escape(call_id) + r"\.(\d+)\.(?:request|response|meta)\.json")
    n = 1 + max((int(m.group(1)) for m in map(name.fullmatch, os.listdir(old)) if m), default=0)
    for kind, path in _files(out, call_id).items():
        if path.exists():
            os.replace(path, old / f"{call_id}.{n}.{kind}.json")


def _orphan_usd(response_path):
    """-> (provider, USD) for a response file without a meta file (the process died between the two writes):
    the USD of its usage object if it has one, else the conservative estimate. The model is read from the
    request file, which is always written first."""
    request = response_path.with_name(response_path.name[:-len("response.json")] + "request.json").read_bytes()
    model = json.loads(request)["model"]
    cost = estimate_usd(model, request)
    try:
        usage = json.loads(response_path.read_bytes())["usage"]
        cost = usd(model, usage) if isinstance(usage, dict) else cost
    except Exception:      # no JSON, no usage object, or one that cannot be priced
        pass
    return PROVIDER[model], cost


def recorded_usd(out):
    """{provider: USD} counted towards the budget in <out>, superseded calls included: the usd_budget of
    every meta file, plus every response file that has no meta file (see _orphan_usd)."""
    total = {ANTHROPIC: 0.0, OPENAI: 0.0}
    for folder in (Path(out), Path(out) / "superseded"):
        for path in folder.glob("*.meta.json"):
            meta = json.loads(path.read_bytes())
            total[meta["provider"]] += meta["usd_budget"]
        for path in folder.glob("*.response.json"):
            if not path.with_name(path.name[:-len("response.json")] + "meta.json").exists():
                provider, cost = _orphan_usd(path)
                total[provider] += cost
    return total


def write_manifest(out, not_sent=()):
    """Rewrite <out>/manifest.jsonl from the meta files, plus the rows of calls that were not sent (a meta
    file from an earlier run takes precedence over such a row). -> the rows, sorted by call_id."""
    rows = {r["call_id"]: r for r in not_sent}
    for path in Path(out).glob("*.meta.json"):
        m = json.loads(path.read_bytes())
        rows[m["call_id"]] = {"call_id": m["call_id"], "model": m["model"], "prompt_sha256": m["prompt_sha256"],
                              "status": m["status"], "usd": m["usd"]}
    rows = [rows[k] for k in sorted(rows)]
    _write(Path(out) / "manifest.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode())
    return rows


def log_command(out, command):
    """Append one line to <out>/COMMANDS.log: UTC time, working directory, and the command line (an argv
    list, written shell-quoted) or a note (a string, written as it is)."""
    Path(out).mkdir(parents=True, exist_ok=True)
    text = command if isinstance(command, str) else shlex.join(str(c) for c in command)
    with open(Path(out) / "COMMANDS.log", "a", encoding="utf-8") as f:
        f.write(f"{utc_now()}\tcwd={os.getcwd()}\t{text}\n")


# ---------------------------------------------------------------- one call
def _read_200(provider, model, data, meta):
    """Fill meta from the body of an HTTP 200, field by field, so what was read before a failure stays.
    Raises if the body is not a JSON object or not of the expected shape; meta["status"] then says which."""
    meta["status"] = "bad_json"
    response = json.loads(data)
    if not isinstance(response, dict):
        raise ValueError("the body is not a JSON object")
    meta["status"] = "postprocess_error"
    meta["response_model"], meta["usage"] = response.get("model"), response.get("usage")
    meta["usd"] = usd(model, meta["usage"])
    if isinstance(meta["usage"], dict):
        meta["usd_budget"] = meta["usd"]
    meta["stop_reason"], meta["stop_details"] = stop_info(provider, response)
    meta["content_types"] = [p.get("type") for p in content_parts(provider, response)]
    answer = extract_answer(provider, response)
    meta["answer_sha256"], meta["answer_chars"] = sha256(answer.encode("utf-8")), len(answer)
    if not str(meta["response_model"] or "").startswith(model):
        meta["status"] = "model_mismatch"
    elif meta["stop_reason"] != NORMAL_STOP[provider]:
        meta["status"] = str(meta["stop_reason"])
    else:
        meta["status"] = "ok" if answer.strip() else "empty_answer"


def do_call(call, body, out, url, key):
    """Send one call and write its three files. -> the meta dict.
    The meta file is written right after the response file with what is known without reading the body, then
    again with what the body says. A 200 body that cannot be read is kept and flagged; it never raises."""
    provider, files = PROVIDER[call["model"]], _files(out, call["call_id"])
    headers = request_headers(provider, key)
    if files["meta"].exists() or files["response"].exists():      # a stored response is never overwritten
        _supersede(out, call["call_id"])
    _write(files["request"], body)
    started = utc_now()
    http_status, resp_headers, data, attempts = send(url, body, headers)
    stored = data.replace(key.encode(), b"[redacted]") if data is not None else None
    if stored is not None:
        _write(files["response"], stored)
    estimate = estimate_usd(call["model"], body)
    meta = {
        "call_id": call["call_id"], "provider": provider, "model": call["model"], "url": url,
        "request_headers": {k: v for k, v in headers.items() if k not in SECRET_HEADERS},
        "prompt_sha256": sha256(call["prompt"].encode("utf-8")),
        "request_sha256": sha256(body), "request_bytes": len(body),
        "http_status": http_status,
        "response_headers": {h: resp_headers.get(h) for h in KEPT_RESPONSE_HEADERS} if resp_headers else {},
        "response_sha256": sha256(data) if data is not None else None,
        "response_bytes": len(data) if data is not None else None,
        "response_redacted": stored != data,
        "started_utc": started, "finished_utc": utc_now(),
        "attempt_count": len(attempts), "attempts": attempts,
        "response_model": None, "usage": None,
        # usd: the usage object times the list prices. usd_budget: what the budget counts, which is usd, or
        # the estimate for a 200 whose usage object could not be read
        "usd": 0.0, "usd_estimate": estimate, "usd_budget": estimate if http_status == 200 else 0.0,
        "stop_reason": None, "stop_details": None, "content_types": None,
        "answer_sha256": None, "answer_chars": None, "postprocess_error": None,
        "status": ("network_error" if http_status is None else
                   "postprocess_error" if http_status == 200 else f"http_{http_status}"),
    }
    _write(files["meta"], _json_bytes(meta))
    if http_status == 200:
        full = dict(meta)
        try:
            _read_200(provider, call["model"], stored, full)
        except Exception as e:      # RecursionError (deeply nested JSON) is one of them
            full["postprocess_error"] = f"{type(e).__name__}: {e}"[:300]
        try:
            blob = _json_bytes(full)
        except Exception as e:      # a field read from the body cannot be written: keep the first meta
            full = {**meta, "postprocess_error": f"meta file: {type(e).__name__}: {e}"[:300]}
            blob = _json_bytes(full)
        _write(files["meta"], blob)
        meta = full
    return meta


class _Budget:
    """Per-provider spend guard shared by the worker threads. Recorded USD is read from the meta files once
    and then kept up to date as calls finish; calls in flight are held at their conservative estimate."""

    def __init__(self, out, caps):
        self.lock = threading.Lock()
        self.caps = {p: float((caps or {}).get(p, 0.0)) for p in (ANTHROPIC, OPENAI)}
        self.spent = recorded_usd(out)
        self.in_flight = {ANTHROPIC: 0.0, OPENAI: 0.0}
        self.stopped = set()

    def reserve(self, provider, estimate):
        """True if the call may be sent. After the first refusal the provider stays stopped for this run."""
        with self.lock:
            if provider not in self.stopped:
                if self.spent[provider] + self.in_flight[provider] + estimate > self.caps[provider]:
                    self.stopped.add(provider)
                else:
                    self.in_flight[provider] += estimate
            return provider not in self.stopped

    def settle(self, provider, estimate, actual):
        with self.lock:
            self.in_flight[provider] -= estimate
            self.spent[provider] += actual


# ---------------------------------------------------------------- run
def _check_calls(calls, out, force):
    """Validate every call before anything is sent. -> [(call, request body, already done)]."""
    plan, seen = [], set()
    for call in calls:
        call_id, model, prompt = call["call_id"], call["model"], call["prompt"]
        if not CALL_ID.fullmatch(call_id) or call_id in seen:
            raise ValueError(f"call_id {call_id!r} is repeated or not a plain file name")
        if model not in PROVIDER:
            raise ValueError(f"{call_id}: unknown model {model!r}")
        if not isinstance(prompt, str) or not prompt:
            raise ValueError(f"{call_id}: the prompt must be a non-empty string")
        seen.add(call_id)
        body = build_request(model, prompt)
        done = not force and _has_200(out, call_id)
        if done and read_meta(out, call_id)["request_sha256"] != sha256(body):
            raise ValueError(f"{call_id}: a stored 200 response belongs to a different request; "
                             "use a new call_id or --force")
        plan.append((call, body, done))
    return plan


def run_calls(calls, out_dir, workers=4, budget_usd=None, base_urls=None, force=False):
    """Send calls = [{"call_id", "model", "prompt"}] and store everything in out_dir (see the module text).
    budget_usd = {"anthropic": usd, "openai": usd}; a missing provider means 0. base_urls overrides the API
    hosts per provider (tests point it at a local stub). -> this run's manifest rows, sorted by call_id."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    urls = {p: {**BASE_URLS, **(base_urls or {})}[p].rstrip("/") + ENDPOINT[p] for p in BASE_URLS}
    todo = [(call, body) for call, body, done in _check_calls(calls, out, force) if not done]
    budget = _Budget(out, budget_usd)
    # a provider with no budget is never sent to, so its key is not needed
    keys = {p: api_key(p) for p in sorted({PROVIDER[call["model"]] for call, _ in todo}) if budget.caps[p] > 0}

    one_at_a_time = threading.Lock()

    def one(item):
        call, body = item
        provider, estimate = PROVIDER[call["model"]], estimate_usd(call["model"], body)
        # the estimate is no bound for OpenAI (no output cap), so each of its calls waits for the one before
        # it and is checked against what that one actually cost
        with one_at_a_time if provider == OPENAI else contextlib.nullcontext():
            if not budget.reserve(provider, estimate):
                return {"call_id": call["call_id"], "model": call["model"], "status": "not_sent_budget",
                        "prompt_sha256": sha256(call["prompt"].encode("utf-8")), "usd": 0.0}
            counted = estimate      # if do_call raises after sending, the call stays counted at its estimate
            try:
                counted = do_call(call, body, out, urls[provider], keys[provider])["usd_budget"]
            finally:
                budget.settle(provider, estimate, counted)
        return None

    not_sent = []
    try:
        with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
            not_sent = [row for row in pool.map(one, todo) if row]
    finally:
        rows = write_manifest(out, not_sent)
    wanted = {call["call_id"] for call in calls}
    return [r for r in rows if r["call_id"] in wanted]


def read_calls(path):
    """calls.jsonl -> list of calls. Lines end at "\\n" only, so a prompt may hold any other character."""
    with open(path, encoding="utf-8", newline="\n") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_budgets(items):
    budgets = {}
    for item in items or []:
        provider, _, value = item.partition("=")
        if provider not in BASE_URLS:
            raise SystemExit(f"--budget-usd takes anthropic=USD or openai=USD, not {item!r}")
        budgets[provider] = float(value)
    return budgets


def summary(rows, out):
    by_status = Counter(r["status"] for r in rows)
    spent = recorded_usd(out)
    return (f"{len(rows)} calls: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items()))
            + f"; USD counted towards the budget in {out}: anthropic {spent[ANTHROPIC]:.4f}, "
              f"openai {spent[OPENAI]:.4f}")


def main(argv=None, base_urls=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--calls", required=True, help="JSONL: one {call_id, model, prompt} per line")
    ap.add_argument("--out", required=True, help="directory for the request, response and meta files")
    ap.add_argument("--budget-usd", action="append", metavar="PROVIDER=USD", required=True,
                    help="spend guard per provider (anthropic=..., openai=...); repeat the option for both. "
                         "A hard cap for Claude; OpenAI can pass it by at most one call's cost (no output cap)")
    ap.add_argument("--workers", type=int, default=4, help="threads; OpenAI calls still go one at a time")
    ap.add_argument("--force", action="store_true", help="send again even if a 200 response is stored")
    args = ap.parse_args(argv)
    log_command(args.out, [sys.executable, *(sys.argv if argv is None else [__file__, *argv])])
    rows = run_calls(read_calls(args.calls), args.out, workers=args.workers,
                     budget_usd=parse_budgets(args.budget_usd), base_urls=base_urls, force=args.force)
    print(summary(rows, args.out))
    return 0 if all(r["status"] == "ok" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
