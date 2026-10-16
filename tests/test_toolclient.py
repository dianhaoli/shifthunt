"""toolclient/tool against a stub AF_UNIX server (one request per connection, one JSON line back),
and the grader-side helpers in docker_toolsrv/stop_toolsrv.py (no root needed)."""
import importlib.machinery
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "toolclient" / "tool"


def _load_client():
    loader = importlib.machinery.SourceFileLoader("shifthunt_toolclient", str(TOOL))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(mod)
    return mod


client = _load_client()
sys.path.insert(0, str(TOOL.parents[1] / "docker_toolsrv"))
import stop_toolsrv  # noqa: E402


class StubServer:
    """Records each request and answers with reply(request) (bytes are sent verbatim)."""

    def __init__(self, path, reply):
        self.path, self.reply, self.requests = str(path), reply, []
        self.srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.srv.bind(self.path)
        self.srv.listen(4)
        self.srv.settimeout(0.1)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.srv.accept()
            except socket.timeout:
                continue
            with conn:
                buf = b""
                while b"\n" not in buf:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                req = json.loads(buf)
                self.requests.append(req)
                out = self.reply(req)
                conn.sendall(out if isinstance(out, bytes) else json.dumps(out).encode() + b"\n")

    def close(self):
        self.stop.set()
        self.thread.join()
        self.srv.close()


@pytest.fixture
def sock_dir():
    # AF_UNIX paths are limited to ~107 bytes, so pytest's tmp_path can be too long.
    import tempfile
    with tempfile.TemporaryDirectory(dir="/tmp") as d:
        yield Path(d)


@pytest.fixture
def server(sock_dir):
    servers = []

    def make(reply=lambda req: {"echo": req}):
        s = StubServer(sock_dir / f"s{len(servers)}.sock", reply)
        servers.append(s)
        return s

    yield make
    for s in servers:
        s.close()


def run(sock, *argv, stdin=None):
    # -I -S: no site-packages, so the client must be stdlib-only.
    p = subprocess.run([sys.executable, "-I", "-S", str(TOOL), "--sock", str(sock), *argv], input=stdin,
                       capture_output=True, text=True, timeout=30)
    return p.returncode, p.stdout, p.stderr


# ---------------------------------------------------------------- argument parsing

def test_key_value_values_parsed_as_json_else_string():
    args = client.parse_args(["probe=0", "ids=[1, 2, 2]", "flag=true", "cue=abc", "s=\"7\"", "e=a=b", "z="])
    assert args == {"probe": 0, "ids": [1, 2, 2], "flag": True, "cue": "abc", "s": "7", "e": "a=b", "z": ""}


def test_json_object_argument_and_stdin():
    obj = {"probe": 1, "texts": ["a = b", "{x}"]}
    assert client.parse_args([json.dumps(obj)]) == obj
    assert client.parse_args(["-"], stdin=io.StringIO(json.dumps(obj))) == obj
    assert client.parse_args([]) == {}


@pytest.mark.parametrize("argv", [["noequals"], ["=1"], ["a=1", "a=2"], ["{bad json"], ["[1]"]])
def test_usage_errors(argv):
    with pytest.raises(client.Usage):
        client.parse_args(argv)


@pytest.mark.parametrize("argv", [["probe=NaN"], ["offset=1e999"], ["x=-Infinity"], ["ids=[1, NaN]"],
                                  ['{"probe": NaN}'], ['{"texts": ["a"], "probe": 1E400}']])
def test_nan_infinity_overflow_are_usage_errors(argv):
    """json.loads accepts these and json.dumps re-emits them as bare NaN/Infinity, which the server
    rejects with a generic message; the client refuses them locally instead."""
    with pytest.raises(client.Usage, match="not a JSON number"):
        client.parse_args(argv)
    with pytest.raises(client.Usage, match="not a JSON number"):
        client.parse_args(["-"], stdin=io.StringIO('{"probe": Infinity}'))
    assert client.parse_args(["probe=1.5e3", "cue=NaNa", 's="NaN"']) == {"probe": 1500.0, "cue": "NaNa", "s": "NaN"}


def test_json_argument_must_be_object():
    with pytest.raises(client.Usage):
        client.parse_args(["-"], stdin=io.StringIO("[1, 2]"))


# ---------------------------------------------------------------- pretty printing

def test_pretty_keeps_scalar_lists_on_one_line_and_round_trips():
    v = {"logits": [0.5, -1.0], "texts": [{"tokens": ["a", "b"], "acts": [[1, 2], [3, 4]]}], "e": [], "d": {}}
    out = client.pretty(v)
    assert json.loads(out) == v
    assert '"logits": [0.5, -1.0]' in out and "[1, 2]" in out
    assert client.pretty({"t": "é"}) == '{\n  "t": "é"\n}'


# ---------------------------------------------------------------- end to end (subprocess)

def test_request_shape_and_exit_0(server):
    s = server(lambda req: {"ok": True, "got": req})
    code, out, err = run(s.path, "probe_scores", "probe=1", "ablate=[3,3,9]")
    assert code == 0, err
    assert s.requests == [{"tool": "probe_scores", "args": {"probe": 1, "ablate": [3, 3, 9]}}]
    assert json.loads(out)["got"] == s.requests[0]


def test_no_args_sends_empty_object(server):
    s = server(lambda req: {"tool_calls": {"used": 0}})
    code, _, _ = run(s.path, "budget")
    assert code == 0 and s.requests == [{"tool": "budget", "args": {}}]


def test_stdin_json(server):
    s = server()
    answer = {"answer": {"probes": [{"probe": 0, "none": True, "cues": []}]}}
    code, _, err = run(s.path, "submit", "-", stdin=json.dumps(answer))
    assert code == 0, err
    assert s.requests[0]["args"] == answer


def test_server_error_exit_1(server):
    s = server(lambda req: {"error": "unknown tool; call help for the list"})
    code, out, _ = run(s.path, "nope")
    assert code == 1 and json.loads(out) == {"error": "unknown tool; call help for the list"}


def test_rejected_submit_exit_1(server):
    s = server(lambda req: {"accepted": False, "errors": ["probes: required"]})
    code, out, _ = run(s.path, "submit", "answer={}")
    assert code == 1 and json.loads(out)["errors"] == ["probes: required"]


def test_help_prints_text(server):
    s = server(lambda req: {"help": "ShiftHunt tools.\nline two"})
    code, out, _ = run(s.path, "help")
    assert code == 0 and out == "ShiftHunt tools.\nline two\n"


def test_usage_error_exit_2_sends_nothing(server):
    s = server()
    code, _, err = run(s.path, "probe_scores", "probe")
    assert code == 2 and "key=value" in err and s.requests == []


def test_nan_exit_2_sends_nothing(server):
    s = server()
    code, _, err = run(s.path, "probe_gradient", "probe=NaN")
    assert code == 2 and "not a JSON number" in err and s.requests == []


def test_missing_socket_exit_2(sock_dir):
    code, _, err = run(sock_dir / "absent.sock", "budget")
    assert code == 2 and "cannot reach" in err


@pytest.mark.parametrize("raw", [b"", b"not json\n"])
def test_bad_reply_exit_2(server, raw):
    s = server(lambda req: raw)
    code, _, err = run(s.path, "budget")
    assert code == 2 and "cannot reach" in err


def test_reply_without_newline_until_eof(server):
    s = server(lambda req: b'{"a": 1}')
    code, out, _ = run(s.path, "budget")
    assert code == 0 and json.loads(out) == {"a": 1}


def test_timeout(sock_dir):
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(sock_dir / "slow.sock"))
    srv.listen(1)  # accepts into the backlog, never replies
    try:
        with pytest.raises(OSError):
            client.call(str(sock_dir / "slow.sock"), "budget", {}, timeout=0.3)
    finally:
        srv.close()


def test_default_socket_and_executable():
    assert client.DEFAULT_SOCK == "/run/shifthunt/tool.sock" and client.TIMEOUT_S == 200
    assert os.access(TOOL, os.X_OK)
    assert TOOL.read_text().startswith("#!/usr/bin/env python3\n")


# ---------------------------------------------------------------- stop_toolsrv (host, unprivileged)

FAKE_DAEMON = "import signal, sys, time\nif sys.argv[1] == 'stubborn': signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" \
              "print('up', flush=True)\ntime.sleep(120)"


@pytest.fixture
def no_user(monkeypatch):
    monkeypatch.setattr(stop_toolsrv, "USER", "no-such-user-shifthunt")


def _fake_daemon(sock_dir, mode):
    # The cmdline names shifthunt.toolserver, like the real daemon's.
    p = subprocess.Popen([sys.executable, "-c", FAKE_DAEMON, mode, "shifthunt.toolserver"], stdout=subprocess.PIPE)
    assert p.stdout.readline() == b"up\n"
    pidfile = sock_dir / "daemon.pid"
    pidfile.write_text(f"{p.pid}\n")
    sock = sock_dir / "tool.sock"
    sock.write_text("")
    return p, pidfile, sock


@pytest.mark.parametrize("mode, outcome", [("polite", "terminated"), ("stubborn", "killed")])
def test_stop(no_user, sock_dir, mode, outcome):
    p, pidfile, sock = _fake_daemon(sock_dir, mode)
    assert stop_toolsrv.stop(pidfile, timeout=0.5, sock=sock) == outcome
    assert p.wait(5) == -(15 if mode == "polite" else 9)
    assert not pidfile.exists() and not sock.exists()
    assert stop_toolsrv.stop(pidfile, timeout=0.5, sock=sock) == "absent"


def test_stop_ignores_stale_pidfile(no_user, sock_dir):
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        (sock_dir / "daemon.pid").write_text(f"{other.pid}\n")
        assert stop_toolsrv.stop(sock_dir / "daemon.pid", timeout=0.5, sock=sock_dir / "s") == "absent"
        assert other.poll() is None
    finally:
        other.kill()
        other.wait()


def _slow(x):
    time.sleep(x)
    return x


def _boom():
    raise ValueError("boom")


def test_run_with_timeout():
    assert stop_toolsrv.run_with_timeout(lambda a, b=0: {"sum": a + b}, 10, 2, b=3) == {"sum": 5}
    t0 = time.monotonic()
    with pytest.raises(TimeoutError):
        stop_toolsrv.run_with_timeout(_slow, 0.5, 30)
    assert time.monotonic() - t0 < 5
    with pytest.raises(RuntimeError, match="ValueError: boom"):
        stop_toolsrv.run_with_timeout(_boom, 10)
    with pytest.raises(RuntimeError, match="not picklable"):
        stop_toolsrv.run_with_timeout(lambda: (lambda: 0), 10)


def test_run_with_timeout_kills_grandchildren(sock_dir):
    marker = sock_dir / "late"

    def spawn_and_hang():
        subprocess.Popen(["sh", "-c", f"sleep 1.5; touch {marker}"])
        time.sleep(30)

    with pytest.raises(TimeoutError):
        stop_toolsrv.run_with_timeout(spawn_and_hang, 0.5)
    time.sleep(2)
    assert not marker.exists()
