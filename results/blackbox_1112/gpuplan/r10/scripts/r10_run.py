"""R10 wrapper (results/blackbox_1112/gpuplan/r10/PLAN_R10.md; GPU_PROMPT_10_v2.md sections 1, 2 A6, 4).

Runs inside the r10 worktree only (../shifthunt_r10), where every hard-coded ROOT path resolves to the r10 copies.

    python scripts/r10_run.py mod <module> [--parser strict|frozen] -- <argv...>   # an analyse step, unedited script
    python scripts/r10_run.py send --calls F --out D --budget-usd openai=X [--budget-usd anthropic=Y] [--workers N]
    python scripts/r10_run.py subset --calls F --out F2 (--prefix P ... | --ids FILE) [--rename PREFIX]

mod: imports the target module, applies the overrides below, then calls its main(argv).
  - refuses build, dryrun, run and judge-* subcommands that send or build, and any --force;
  - pins set A: judge_ladder2.set_a_ids = lambda rows, c6: PINNED_A (the 130 group-A ids of the original
    judge_ladder2/meta.json; a different set of failures in r10 must not change the set);
  - strict parser (A6, default --parser strict): judge_vs_grade.parse_verdicts is replaced by strict_parse, which
    accepts `correct` only as a JSON boolean or one of the strings true/false/yes/no/pass/fail (case-insensitive);
    any other value (null, other strings, numbers) leaves that slot unparsed (so, as in the frozen parser, the call is
    unparsed). The frozen parser coerces with bool(), so "false" counts as credited. Counts go to
    results/private_1112/gpuplan/r10/parser_logs/. --parser frozen keeps the unchanged function.
  - no analyse step asserts a prompt or contract hash, so no constant is overridden (logged in PLAN_R10).
send: textonly_client.run_calls on one calls file into one raw directory, with gpt-6.1-sol and gpt-6-luna registered
  exactly as scripts/sol_judge.py and scripts/judge_panel.py do. Before sending, every call id that already has a
  .meta.json in the raw directory is dropped (no call is re-sent, whatever its status). Never --force.
subset: a filtered calls file that keeps the stored order (and optionally renames call ids with a prefix, for CTRL).
"""
import argparse
import atexit
import importlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_TREE = Path("/home/ec2-user/shifthunt-public")
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PRIV10 = ROOT / "results" / "private_1112" / "gpuplan" / "r10"
REFUSED = re.compile(r"^(build|dryrun|run|judge-build|judge-run|transform)$")
STRICT = {"true": True, "yes": True, "pass": True, "false": False, "no": False, "fail": False}
STATS = Counter()


def pinned_a():
    meta = json.loads((ROOT / "results" / "private_1112" / "judge_ladder2" / "meta.json").read_text())
    ids = sorted(m["call_id"] for m in meta if m["group"] == "A" and "problem" not in m)
    assert len(ids) == 130, len(ids)
    return ids


def strict_parse(text, n):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        STATS["calls_no_json"] += 1
        return None
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        STATS["calls_bad_json"] += 1
        return None
    out = {}
    for p in obj.get("probes", []):
        try:
            j = int(p["probe"])
            c = p["correct"]
        except (KeyError, TypeError, ValueError):
            continue
        if isinstance(c, bool):
            b = c
        elif isinstance(c, str) and c.strip().lower() in STRICT:
            b = STRICT[c.strip().lower()]
            STATS[f"mapped_{type(c).__name__}"] += 1
        else:
            STATS[f"unparsed_slot_{type(c).__name__}"] += 1
            continue
        try:
            out[j] = (b, float(p.get("confidence", 50)))
        except (TypeError, ValueError):
            continue
    ok = all(j in out for j in range(n))
    STATS["calls_parsed" if ok else "calls_unparsed"] += 1
    return out if ok else None


def _dump_stats(tag):
    PRIV10.joinpath("parser_logs").mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (PRIV10 / "parser_logs" / f"{tag}_{ts}.json").write_text(json.dumps(dict(STATS), indent=1, sort_keys=True) + "\n")
    print(f"[r10_run] parser stats {tag}: {dict(STATS)}", file=sys.stderr)


def _in_worktree():
    assert ROOT.resolve() != MAIN_TREE.resolve(), "r10_run.py runs only inside the r10 worktree"


def cmd_mod(a, rest):
    _in_worktree()
    if any(REFUSED.match(x) for x in rest[:1]) or "--force" in rest:
        raise SystemExit(f"refused: {rest}")
    import judge_vs_grade as JV
    import judge_ladder2 as J2
    A = pinned_a()
    J2.set_a_ids = lambda rows, c6: A
    if a.parser == "strict":
        JV.parse_verdicts = strict_parse
        atexit.register(_dump_stats, f"{a.module}_{'_'.join(rest)}")
    mod = importlib.import_module(a.module)
    print(f"[r10_run] {a.module} {rest} parser={a.parser} ROOT={ROOT}", file=sys.stderr)
    sys.argv = [str(Path(mod.__file__)), *rest]
    if not hasattr(mod, "main"):                 # r8_checks / r9_checks: dispatch by subcommand name
        f = getattr(mod, rest[0], None) or getattr(mod, "cmd_" + rest[0])
        return f()
    import inspect
    if not inspect.signature(mod.main).parameters:
        return mod.main()
    return mod.main(rest)


MSGS_MARK = "\x00R10_MSGS\x00"     # = r10_addendum.MSGS_MARK: the prompt field carries a JSON message list (AD4)


def two_turn(TC):
    """AD4: a call whose prompt starts with MSGS_MARK is sent as a multi-message input; every other call unchanged."""
    orig = TC.build_request

    def build_request(model, prompt):
        if not prompt.startswith(MSGS_MARK):
            return orig(model, prompt)
        msgs = json.loads(prompt[len(MSGS_MARK):])
        assert TC.PROVIDER[model] == TC.OPENAI
        body = {"model": model, "input": [{"role": m["role"], "content": m["content"]} for m in msgs], "store": False}
        return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    TC.build_request = build_request


def register_models():
    import textonly_client as TC
    two_turn(TC)
    import sol_judge  # noqa: F401  (registers gpt-6.1-sol in TC.PROVIDER / TC.PRICES)
    import judge_panel  # noqa: F401  (registers gpt-6-luna)
    return TC


def cmd_send(a):
    _in_worktree()
    out = Path(a.out).resolve()
    assert str(out).startswith(str(ROOT.resolve())), "raw directory must be inside the worktree"
    TC = register_models()
    calls = TC.read_calls(a.calls)
    done = [c for c in calls if (out / f"{c['call_id']}.meta.json").exists()]
    todo = [c for c in calls if not (out / f"{c['call_id']}.meta.json").exists()]
    TC.log_command(out, [sys.executable, *sys.argv])
    TC.log_command(out, f"r10_run send: {len(calls)} calls in file, {len(done)} dropped (meta exists), {len(todo)} to send")
    rows = TC.run_calls(todo, out, workers=a.workers, budget_usd=TC.parse_budgets(a.budget_usd))
    print(TC.summary(rows, out))
    return 0


def cmd_subset(a):
    import textonly_client as TC
    calls = TC.read_calls(a.calls)
    if a.ids:
        want = set(Path(a.ids).read_text().split())
        keep = [c for c in calls if c["call_id"] in want]
    else:
        keep = [c for c in calls if any(c["call_id"].startswith(p) for p in a.prefix)]
    if a.rename:
        keep = [dict(c, call_id=a.rename + c["call_id"]) for c in keep]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(json.dumps(c) + "\n" for c in keep))
    print(f"{len(keep)} of {len(calls)} calls -> {a.out}")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "mod":
        rest = argv[argv.index("--") + 1:] if "--" in argv else []
        head = argv[1:argv.index("--")] if "--" in argv else argv[1:]
        ap = argparse.ArgumentParser()
        ap.add_argument("module")
        ap.add_argument("--parser", choices=("strict", "frozen"), default="strict")
        return cmd_mod(ap.parse_args(head), rest)
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send")
    s.add_argument("--calls", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--budget-usd", action="append", required=True)
    s.add_argument("--workers", type=int, default=4)
    t = sub.add_parser("subset")
    t.add_argument("--calls", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--prefix", action="append", default=[])
    t.add_argument("--ids", default="")
    t.add_argument("--rename", default="")
    a = ap.parse_args(argv)
    return {"send": cmd_send, "subset": cmd_subset}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
