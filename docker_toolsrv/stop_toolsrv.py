#!/usr/bin/env python3
"""Grader-side helpers (run as root after the agent is killed): stop the tool server, hard timeouts.

stop(pidfile, timeout=10, sock=SOCK) -> "absent" | "terminated" | "killed"
    SIGTERM every process of user toolsrv plus the pidfile's pid (only if its cmdline names
    shifthunt.toolserver, so a stale pidfile cannot hit another process), wait up to
    `timeout` s, SIGKILL whatever is left, then verify all are gone (else RuntimeError) and remove
    a stale socket. Safe to call twice.
run_with_timeout(fn, seconds, *args, **kwargs) -> fn(*args, **kwargs)
    Runs fn in a forked child in its own session; on timeout the whole session is SIGKILLed and
    TimeoutError is raised; an exception in fn becomes RuntimeError carrying its traceback. The
    result must be picklable, and fn must not rely on CUDA state created before the fork.

Usage as a script: `stop_toolsrv.py [pidfile]` stops the daemon and prints the outcome.
"""
import os
import pickle
import pwd
import select
import signal
import sys
import time
import traceback
from pathlib import Path

USER = "toolsrv"
PIDFILE = Path("/srv/state/daemon.pid")
SOCK = Path("/run/shifthunt/tool.sock")
KILL_WAIT_S = 60


def _alive(pid):
    """Running, or a zombie whose other threads are still exiting (a CUDA process's leader turns Z
    before the driver threads finish and its GPU memory is freed). A fully exited zombie is gone."""
    try:
        if Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z":
            return True
        return len(os.listdir(f"/proc/{pid}/task")) > 1
    except (FileNotFoundError, ProcessLookupError, IndexError):
        return False


def _user_pids(uid):
    pids = []
    for d in Path("/proc").iterdir():
        try:
            if d.name.isdigit() and d.stat().st_uid == uid:
                pids.append(int(d.name))
        except FileNotFoundError:
            pass
    return pids


def _is_daemon(pid):
    try:
        return b"shifthunt.toolserver" in Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False


def _targets(pidfile):
    """Every process of USER, plus the pidfile's pid if it is a tool server (a stale pid is ignored)."""
    pids = set()
    try:
        pids.update(_user_pids(pwd.getpwnam(USER).pw_uid))
    except KeyError:
        pass
    try:
        pid = int(Path(pidfile).read_text().strip())
        if _is_daemon(pid):
            pids.add(pid)
    except (OSError, ValueError):
        pass
    return {p for p in pids if p != os.getpid() and _alive(p)}


def _signal(pids, sig):
    for p in pids:
        try:
            os.kill(p, sig)
        except ProcessLookupError:
            pass


def _wait_gone(pids, timeout):
    deadline = time.monotonic() + timeout
    while True:
        left = {p for p in pids if _alive(p)}
        if not left or time.monotonic() >= deadline:
            return left
        time.sleep(0.1)


def stop(pidfile=PIDFILE, timeout=10, sock=SOCK):
    pids = _targets(pidfile)
    outcome = "absent"
    if pids:
        _signal(pids, signal.SIGTERM)
        left = _wait_gone(pids, timeout)
        outcome = "terminated"
        if left:
            _signal(left, signal.SIGKILL)
            outcome = "killed"
            # A CUDA process can take a while to tear down after SIGKILL (seen > 5 s under memory
            # pressure). It runs no user code once killed, so waiting is enough.
            if _wait_gone(left, KILL_WAIT_S):
                raise RuntimeError(f"tool server processes survived SIGKILL: {sorted(left)}")
    for p in (sock, pidfile):
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass
    return outcome


def run_with_timeout(fn, seconds, *args, **kwargs):
    sys.stdout.flush()
    sys.stderr.flush()
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        try:
            os.setsid()
            out = ("ok", fn(*args, **kwargs))
        except BaseException:
            out = ("err", traceback.format_exc())
        try:
            data = pickle.dumps(out)
        except Exception as e:
            data = pickle.dumps(("err", f"result is not picklable: {e!r}"))
        with os.fdopen(w, "wb") as f:
            f.write(data)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
    os.close(w)
    deadline, buf = time.monotonic() + seconds, b""
    try:
        while True:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([r], [], [], left)[0]:
                _kill_session(pid)
                raise TimeoutError(f"{getattr(fn, '__name__', 'call')} exceeded {seconds} s")
            chunk = os.read(r, 1 << 16)
            if not chunk:
                break
            buf += chunk
    finally:
        os.close(r)
    os.waitpid(pid, 0)
    if not buf:
        raise RuntimeError("child exited without a result")
    status, value = pickle.loads(buf)
    if status == "err":
        raise RuntimeError(f"call failed in child:\n{value}")
    return value


def _kill_session(pid):
    for kill in (os.killpg, os.kill):  # killpg fails if the child has not called setsid yet
        try:
            kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.waitpid(pid, 0)


if __name__ == "__main__":
    print(stop(sys.argv[1] if len(sys.argv) > 1 else PIDFILE))
