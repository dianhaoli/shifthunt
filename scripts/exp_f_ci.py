"""Exp F listing scorer rerun with case-insensitive matching (follow-up DEFINITIONS.md §6; exploratory re-reading).

    python scripts/exp_f_ci.py score --mode ci|cs --work DIR [--priv results/private_1112/exp_f]
    python scripts/exp_f_ci.py table --frozen results/private_1112/exp_f/scores.jsonl \
        --cs <cs scores.jsonl> --ci <ci scores.jsonl> --json-out <misc json part> --md-out <md part>
        [--private-md <private per-cue md>]

The frozen scorer (scripts/exp_f_listing.py, `score`) is imported and run unchanged. Its only matching step is
the regex sandbox runner it takes as an argument (`score(out, runner=...)`); the BA, gating, masks and ranks are
untouched. `--mode ci` passes a runner that prefixes every candidate regex with the inline flag `(?i)` before
shifthunt.regex_sandbox.run_many, which is re.search with re.IGNORECASE. `--mode cs` passes the frozen runner
(run_many itself) and is the control: it must reproduce the stored scores.jsonl. No other string match enters
the scorer's listing decision (the candidate's free-text `property` field is stored but never matched).

The scorer writes `<out>/scores.jsonl`. So that the frozen private output is never overwritten, `score` runs it
on `--work`, a scratch directory holding symlinks to the frozen manifest.json, raw/, heldout/ and grid/, and
writes nothing else.

`table` summarises the three score files with the frozen `summarize` and writes the per-level table (pooled and per
model, primary and sensitivity rules), the calibration groups, the negative control, the regex error counts and
the change ci minus frozen. Tracked output has level labels only (no cue names); per-cue detail goes to
--private-md.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CI_PREFIX = "(?i)"
LINKS = ("manifest.json", "raw", "heldout", "grid")


def ci_regex(rx):
    """The case-insensitive version of a candidate regex: the global inline flag in front. A pattern that already
    starts with global flags keeps them (Python accepts several leading global flag groups)."""
    return CI_PREFIX + rx


def make_runner(mode, base=None):
    """-> runner(jobs, texts) with the frozen runner's signature. mode 'cs' = the frozen runner unchanged."""
    if base is None:
        from shifthunt.regex_sandbox import run_many as base
    if mode == "cs":
        return base
    if mode != "ci":
        raise ValueError(mode)

    def runner(jobs, texts):
        return base([(ci_regex(rx), sc) for rx, sc in jobs], texts)
    return runner


def prepare_work(priv, work):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    for name in LINKS:
        dst, src = work / name, Path(priv).resolve() / name
        if dst.is_symlink() or dst.exists():
            if dst.resolve() != src:
                raise SystemExit(f"{dst} exists and is not a link to {src}")
            continue
        os.symlink(src, dst)
    if (work / "scores.jsonl").resolve() == (Path(priv) / "scores.jsonl").resolve():
        raise SystemExit("refusing to write the frozen scores.jsonl")
    return work


def cmd_score(a):
    import exp_f_listing as F
    work = prepare_work(a.priv, a.work)
    rows = F.score(out=work, runner=make_runner(a.mode))
    print(f"scored {len(rows)} rows -> {work / 'scores.jsonl'}", flush=True)


def _rows(path):
    return [json.loads(x) for x in open(path) if x.strip()]


def _k(c):
    return {"k": c["k"], "n": c["n"]}


def level_view(s):
    out = {}
    for lv, d in s["by_level"].items():
        out[lv] = {"n_cues": len(d["cues"]),
                   "pooled": {r: _k(d["pooled"][r]) for r in ("primary", "sensitivity")},
                   "by_model": {m: {r: _k(d["by_model"][m][r]) for r in ("primary", "sensitivity")}
                                for m in d["by_model"]}}
    return out


def calib_view(s):
    return {g: {"pooled": {r: _k(d["pooled"][r]) for r in ("primary", "sensitivity")},
                "by_model": {m: _k(d["by_model"][m]["primary"]) for m in d["by_model"]}}
            for g, d in s["calibration"].items()}


def neg_view(s):
    n = s["negative_control"]
    return {"by_model": {m: _k(v) for m, v in n["by_model"].items()}, "overall": _k(n["overall"]),
            "all_eligible_by_model": {m: _k(v) for m, v in n["all_eligible_by_model"].items()},
            "all_eligible_overall": _k(n["all_eligible_overall"])}


def regex_errors(rows):
    out = {}
    for r in rows:
        if r.get("outcome") != "scored":
            continue
        out.setdefault(r["model"], [0, 0])
        out[r["model"]][0] += r["n_regex_error"]
        out[r["model"]][1] += sum(1 for c in r["candidates"] if c.get("invalid") is None)
    return {m: {"errors": e, "valid_candidates": n} for m, (e, n) in out.items()}


def candidate_flips(frozen, ci):
    """Per model: candidates whose `reaches` set differs (ci vs frozen), and target listings gained / lost."""
    key = lambda r: r["call_id"]  # noqa: E731
    fz = {key(r): r for r in frozen}
    out = {}
    for r in ci:
        f = fz[key(r)]
        m = out.setdefault(r["model"], {"candidates_changed": 0, "targets_gained": 0, "targets_lost": 0})
        for a, b in zip(f.get("candidates") or [], r.get("candidates") or []):
            m["candidates_changed"] += sorted(a.get("reaches") or []) != sorted(b.get("reaches") or [])
        if r["kind"] != "generated":
            continue
        for ta, tb in zip(f["targets"], r["targets"]):
            m["targets_gained"] += (not ta["primary"]["listed"]) and tb["primary"]["listed"]
            m["targets_lost"] += ta["primary"]["listed"] and not tb["primary"]["listed"]
    return out


def same_scores(a, b):
    """True iff two score files agree on every listing outcome (targets, negative, aligned listed)."""
    def sig(r):
        return (r["call_id"], r["outcome"], json.dumps(r["targets"], sort_keys=True),
                json.dumps(r["negative"], sort_keys=True), json.dumps(r["negative_all"], sort_keys=True),
                json.dumps(sorted(r.get("aligned_listed") or [])),
                json.dumps([c.get("reaches") for c in r["candidates"]]))
    return sorted(map(sig, a)) == sorted(map(sig, b))


def fmt(c):
    return f"{c['k']}/{c['n']}"


def delta(a, b):
    return f"{b['k'] - a['k']:+d}"


def md_tables(views, models):
    fz, ci = views["frozen"], views["ci"]
    L = ["### Per level, primary rule: frozen -> case-insensitive (change in listed count)", "",
         "| level | cues | " + " | ".join(models) + " | pooled | sensitivity, pooled |",
         "|---|---|" + "---|" * (len(models) + 2)]
    for lv in fz["levels"]:
        a, b = fz["levels"][lv], ci["levels"][lv]
        cells = [f"{fmt(a['by_model'][m]['primary'])} -> {fmt(b['by_model'][m]['primary'])} "
                 f"({delta(a['by_model'][m]['primary'], b['by_model'][m]['primary'])})" for m in models]
        cells.append(f"{fmt(a['pooled']['primary'])} -> {fmt(b['pooled']['primary'])} "
                     f"({delta(a['pooled']['primary'], b['pooled']['primary'])})")
        cells.append(f"{fmt(a['pooled']['sensitivity'])} -> {fmt(b['pooled']['sensitivity'])} "
                     f"({delta(a['pooled']['sensitivity'], b['pooled']['sensitivity'])})")
        L.append(f"| {lv} | {a['n_cues']} | " + " | ".join(cells) + " |")
    L += ["", "### Calibration groups (shipped episodes, pooled by group), primary rule", "",
          "| group | " + " | ".join(models) + " | pooled |", "|---|" + "---|" * (len(models) + 1)]
    for g in fz["calibration"]:
        a, b = fz["calibration"][g], ci["calibration"][g]
        cells = [f"{fmt(a['by_model'][m])} -> {fmt(b['by_model'][m])} ({delta(a['by_model'][m], b['by_model'][m])})"
                 for m in models]
        cells.append(f"{fmt(a['pooled']['primary'])} -> {fmt(b['pooled']['primary'])} "
                     f"({delta(a['pooled']['primary'], b['pooled']['primary'])})")
        L.append(f"| {g} | " + " | ".join(cells) + " |")
    L += ["", "### Negative control", "", "| model | seeded control | all eligible non-aligned |", "|---|---|---|"]
    for m in models + ["overall"]:
        if m == "overall":
            a, b = fz["negative"]["overall"], ci["negative"]["overall"]
            a2, b2 = fz["negative"]["all_eligible_overall"], ci["negative"]["all_eligible_overall"]
        else:
            a, b = fz["negative"]["by_model"][m], ci["negative"]["by_model"][m]
            a2, b2 = fz["negative"]["all_eligible_by_model"][m], ci["negative"]["all_eligible_by_model"][m]
        L.append(f"| {m} | {fmt(a)} -> {fmt(b)} ({delta(a, b)}) | {fmt(a2)} -> {fmt(b2)} ({delta(a2, b2)}) |")
    L += ["", "### Regex errors and changed candidates", "",
          "| model | regex errors frozen | regex errors ci | valid candidates | candidates whose reached set changed | "
          "generated targets gained | lost |", "|---|---|---|---|---|---|---|"]
    for m in models:
        e0, e1, fl = fz["regex_errors"][m], ci["regex_errors"][m], views["flips"][m]
        L.append(f"| {m} | {e0['errors']} | {e1['errors']} | {e0['valid_candidates']} | {fl['candidates_changed']} | "
                 f"{fl['targets_gained']} | {fl['targets_lost']} |")
    return "\n".join(L) + "\n"


def cmd_table(a):
    import exp_f_listing as F
    rows = {"frozen": _rows(a.frozen), "cs": _rows(a.cs), "ci": _rows(a.ci)}
    views = {}
    for name, rs in rows.items():
        s = F.summarize(rs)
        views[name] = {"levels": level_view(s), "calibration": calib_view(s), "negative": neg_view(s),
                       "regex_errors": regex_errors(rs), "outcomes": s["outcomes"], "n_planned": s["n_planned"]}
        if name == "frozen":
            models = s["models"]
            by_cue_frozen = s["by_cue"]
        if name == "ci":
            by_cue_ci = s["by_cue"]
    views["flips"] = candidate_flips(rows["frozen"], rows["ci"])
    views["control_cs_equals_frozen"] = same_scores(rows["frozen"], rows["cs"])
    stored = json.load(open(ROOT / "results/blackbox_1112/exp_f/exp_f.json"))
    views["frozen_matches_exp_f_json"] = level_view(stored) == views["frozen"]["levels"]
    out = {k: v for k, v in views.items() if k != "cs"}
    out["cs_levels_equal_frozen"] = views["cs"]["levels"] == views["frozen"]["levels"]
    Path(a.json_out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    Path(a.md_out).write_text(md_tables(views, models))
    if a.private_md:
        L = ["| cue | level | frozen primary | ci primary |", "|---|---|---|---|"]
        for c in by_cue_frozen:
            L.append(f"| {c} | {by_cue_frozen[c]['level']} | {fmt(by_cue_frozen[c]['primary'])} | "
                     f"{fmt(by_cue_ci[c]['primary'])} |")
        Path(a.private_md).write_text("\n".join(L) + "\n")
    print(json.dumps({"control_cs_equals_frozen": views["control_cs_equals_frozen"],
                      "frozen_matches_exp_f_json": views["frozen_matches_exp_f_json"]}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("--mode", choices=("ci", "cs"), required=True)
    s.add_argument("--work", required=True)
    s.add_argument("--priv", default=str(ROOT / "results/private_1112/exp_f"))
    t = sub.add_parser("table")
    for k in ("--frozen", "--cs", "--ci", "--json-out", "--md-out"):
        t.add_argument(k, required=True)
    t.add_argument("--private-md")
    a = ap.parse_args(argv)
    {"score": cmd_score, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    main()
