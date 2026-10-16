"""Run a submitted regex on texts in a sandboxed child process.

The regex is data, never code: the child is a fixed script that reads {"regex", "scope", "texts"}
as JSON on stdin and prints one '0'/'1' per text. Isolation:
  * `python -I -S` (isolated mode, no site, no user site, ignores PYTHON* env vars) with env = {}
    and cwd = /, so nothing from the grader's directory or environment is importable or visible;
  * if started as root (the container grader), the child drops to uid/gid 65534 (nobody);
  * the child sets its own rlimits before reading input: CPU seconds, address space, no file
    writes, no new processes;
  * a wall-clock timeout, after which the child's whole process group gets SIGKILL.
Matching is re.search(regex, scoped_text) with no flags (inline flags such as (?i) are the
submitter's choice). scope: "any" = whole text, "first_line" = text before the first newline,
"last_line" = text after the last newline.

Any failure (bad pattern, timeout, memory or CPU limit, malformed child output) means "matches
nothing": run_regex returns (all False, error tag). The tag is for the grader's own logs.
"""
import json
import os
import signal
import subprocess
import sys

SCOPES = ("any", "first_line", "last_line")
WALL_S = 4.0
CPU_S = 3
MEM_BYTES = 512 * 2 ** 20

_CHILD = r"""
import os, resource
if os.getuid() == 0:  # the grader runs as root in the container; the regex child never does
    os.setgroups([]); os.setgid(65534); os.setuid(65534)
for lim, v in ((resource.RLIMIT_CPU, %(cpu)d), (resource.RLIMIT_AS, %(mem)d),
               (resource.RLIMIT_FSIZE, 0), (resource.RLIMIT_NPROC, 0)):
    resource.setrlimit(lim, (v, v))
import json, re, sys
req = json.loads(sys.stdin.read())
pat = re.compile(req["regex"])
scope = req["scope"]
out = []
for t in req["texts"]:
    if scope == "first_line":
        t = t.split("\n", 1)[0]
    elif scope == "last_line":
        t = t.rsplit("\n", 1)[-1]
    out.append("1" if pat.search(t) else "0")
sys.stdout.write("".join(out))
""" % {"cpu": CPU_S, "mem": MEM_BYTES}


def run_regex(regex, scope, texts, wall_s=WALL_S):
    """-> (list[bool] per text, error tag or None). Never raises for any regex/scope value."""
    texts = list(texts)
    none = [False] * len(texts)
    if not isinstance(regex, str) or scope not in SCOPES:
        return none, "bad_input"
    try:
        payload = json.dumps({"regex": regex, "scope": scope, "texts": texts})
    except (TypeError, ValueError):  # e.g. lone surrogates cannot be encoded
        return none, "bad_input"
    try:
        proc = subprocess.Popen([sys.executable, "-I", "-S", "-c", _CHILD], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env={}, cwd="/",
                                start_new_session=True)
    except OSError:
        return none, "spawn"
    try:
        out, _ = proc.communicate(payload.encode("utf-8", "surrogatepass"), timeout=wall_s)
    except subprocess.TimeoutExpired:
        _kill(proc)
        return none, "timeout"
    except Exception:  # broken pipe etc.
        _kill(proc)
        return none, "io"
    if proc.returncode != 0:
        return none, f"exit:{proc.returncode}"
    if len(out) != len(texts) or out.strip(b"01"):
        return none, "bad_output"
    return [c == ord("1") for c in out], None


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.communicate(timeout=1)
    except Exception:
        pass


def run_many(jobs, texts):
    """jobs: list of (regex, scope) -> list of (matches, error), same order. Sequential on purpose:
    concurrent children slow each other (shared cores), so a regex near the CPU limit could pass
    alone and fail next to its sibling cues; one at a time keeps the verdict independent of them."""
    return [run_regex(r, s, texts) for r, s in jobs]
