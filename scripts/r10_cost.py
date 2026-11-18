"""R10 cost: dry-run selection, projection per block, and the round-10 spend from the meta files (worktree).

    python scripts/r10_cost.py dryfiles          # write the 5-longest dry-run calls files (Terra, Sol, Haiku)
    python scripts/r10_cost.py project           # projection per calls file from the originals' logged cost x dry-run factor
    python scripts/r10_cost.py spend             # round-10 USD per raw directory and provider, from the meta files

Projection: for each calls file, the original batch's logged USD (sum of the original meta files) times the dry-run
factor of its model (r10 USD of the 5 longest r10 prompts / original USD of the same 5 calls).
"""
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path("/home/ec2-user/shifthunt-public")
WT = Path("/home/ec2-user/shifthunt_r10")
ORIG = MAIN / "results" / "private_1112"
R10 = WT / "results" / "private_1112"
DRY = R10 / "gpuplan" / "r10" / "dryrun"
PAIRS = [("judge/calls.jsonl", "judge/raw"), ("judge_luna/calls.jsonl", "judge_luna/raw"),
         ("judge_ladder/calls.jsonl", "judge_ladder/raw"), ("judge_ladder2/calls_c6b.jsonl", "judge_ladder2/raw_c6b"),
         ("judge_ladder2/calls_haiku.jsonl", "judge_ladder2/raw_haiku"), ("judge_ladder2/calls_c6c.jsonl", "judge_ladder2/raw_c6c"),
         ("judge_ladder2/calls_k.jsonl", "judge_ladder2/raw_k"), ("judge_ladder2/calls_f.jsonl", "judge_ladder2/raw_f"),
         ("judge_panel/calls_terra.jsonl", "judge_panel/raw_terra"), ("judge_panel/calls_small.jsonl", "judge_panel/raw_small"),
         ("judge_cheaters/calls.jsonl", "judge_cheaters/raw"), ("judge_sol/calls_s1.jsonl", "judge_sol/raw_s1"),
         ("judge_sol/calls_s2.jsonl", "judge_sol/raw_s2"), ("judge_sol/calls_s3.jsonl", "judge_sol/raw_s3"),
         ("judge_sol/calls_s4.jsonl", "judge_sol/raw_s4"), ("judge_sol/calls_s5.jsonl", "judge_sol/raw_s5"),
         ("judge_c14/calls.jsonl", "judge_c14/raw"), ("judge_c14b/calls.jsonl", "judge_c14b/raw")]
GROUP = {"gpt-6.1-terra": "terra", "gpt-6.1-sol": "sol", "claude-haiku-5-5": "haiku"}


def calls(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def meta(raw, cid):
    p = Path(raw) / f"{cid}.meta.json"
    return json.loads(p.read_text()) if p.exists() else None


def cmd_dryfiles():
    allc = []
    for cf, rd in PAIRS:
        for c in calls(R10 / cf):
            allc.append((cf, rd, c))
    out = OrderedDict()
    for model, g in GROUP.items():
        top = sorted([x for x in allc if x[2]["model"] == model], key=lambda x: -len(x[2]["prompt"]))[:5]
        DRY.mkdir(parents=True, exist_ok=True)
        (DRY / f"calls_{g}.jsonl").write_text("".join(json.dumps(dict(x[2], call_id=f"DRY__{x[2]['call_id']}")) + "\n"
                                                      for x in top))
        out[g] = [dict(file=x[0], raw=x[1], call_id=x[2]["call_id"], chars=len(x[2]["prompt"])) for x in top]
    (DRY / "selection.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({g: [(x["file"], x["chars"]) for x in v] for g, v in out.items()}, indent=1))


def factors():
    sel = json.loads((DRY / "selection.json").read_text())
    F = OrderedDict()
    for g, xs in sel.items():
        new = old = 0.0
        n = 0
        for x in xs:
            m = meta(DRY / f"raw_{g}", "DRY__" + x["call_id"])
            o = meta(ORIG / x["raw"], x["call_id"])
            if m and m.get("status") == "ok" and o:
                new += m["usd"]
                old += o["usd"]
                n += 1
        F[g] = OrderedDict(sent_ok=n, r10_usd=round(new, 4), orig_usd=round(old, 4),
                           factor=round(new / old, 3) if old else None)
    return F


def cmd_project():
    F = factors()
    proj = OrderedDict()
    tot = Counter()
    for cf, rd in PAIRS:
        by = Counter()
        for c in calls(ORIG / cf):
            m = meta(ORIG / rd, c["call_id"])
            by[c["model"]] += (m or {}).get("usd") or 0
        for model, u in by.items():
            g = GROUP.get(model)
            f = (F.get(g) or {}).get("factor") or 1.0
            proj[f"{cf} | {model}"] = OrderedDict(orig_usd=round(u, 3), factor=f, projected_usd=round(u * f, 3))
            tot["anthropic" if model.startswith("claude") else "openai"] += u * f
    res = OrderedDict(factors=F, by_file=proj, total_P0_P3={k: round(v, 2) for k, v in tot.items()})
    out = MAIN / "results" / "blackbox_1112" / "gpuplan" / "r10" / "dryrun.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


def cmd_spend():
    tot = OrderedDict()
    for d in sorted(R10.rglob("*.meta.json")):
        pass
    agg = Counter()
    n = Counter()
    for p in R10.rglob("*.meta.json"):
        rel = p.parent.relative_to(R10)
        if "superseded" in rel.parts:
            pass
        m = json.loads(p.read_text())
        agg[(str(rel), m["provider"])] += m.get("usd_budget") or 0
        n[(str(rel), m["provider"])] += 1
    for k in sorted(agg):
        tot[f"{k[0]} | {k[1]}"] = OrderedDict(calls=n[k], usd=round(agg[k], 4))
    s = Counter()
    for (d, p), u in agg.items():
        s[p] += u
    print(json.dumps(OrderedDict(by_dir=tot, total={k: round(v, 4) for k, v in s.items()}), indent=1))




def runlog_row(desc, kind, raws, prefix=""):
    """Append one RUNLOG row for the calls in raw dirs `raws` (worktree-relative) whose id starts with prefix."""
    import re as _re
    sys.path.insert(0, str(WT / "scripts"))
    import r10_reason_scan as RS  # noqa: F401  (strict_parse)
    st, usd, models, t0, t1, parsed, n = Counter(), Counter(), Counter(), None, None, 0, 0
    for rd in raws:
        for p in sorted((R10 / rd).glob(f"{prefix}*.meta.json")):
            m = json.loads(p.read_text())
            n += 1
            st[m["status"]] += 1
            usd[m["provider"]] += m.get("usd_budget") or 0
            models[str(m.get("response_model"))] += 1
            t0 = min(t0 or m["started_utc"], m["started_utc"])
            t1 = max(t1 or m["finished_utc"], m["finished_utc"] or "")
            rp = p.with_name(p.name.replace(".meta.json", ".response.json"))
            if m["status"] == "ok" and rp.exists():
                import textonly_client as TC
                text = TC.extract_answer(m["provider"], json.loads(rp.read_text()))
                ab = '"verdict"' in text
                mm = _re.search(r"\{.*\}", text or "", _re.S)
                try:
                    obj = json.loads(mm.group(0)) if mm else None
                    k = len(obj.get("probes", [])) if isinstance(obj, dict) else 0
                    ok = bool(obj) and k > 0 and all(isinstance(x.get("correct"), bool) or
                                                     str(x.get("correct", x.get("verdict"))).strip().lower() in
                                                     ("true", "false", "yes", "no", "pass", "fail", "cannot tell")
                                                     for x in obj["probes"])
                except (ValueError, AttributeError, TypeError):
                    ok = False
                parsed += ok
    lines = (MAIN / "results/blackbox_1112/RUNLOG.md").read_text().splitlines()
    last = [l for l in lines if l.startswith("| 20")][-1].split("|")
    co, ca = float(last[-3]), float(last[-2])
    co += usd["openai"]
    ca += usd["anthropic"]
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    stat = ", ".join(f"{k} {v}" for k, v in sorted(st.items()))
    row = (f"| {now} | {desc}; calls {n}, returned {st.get('ok', 0)}, parsed {parsed}; window {t0}–{t1}; response "
           f"model {', '.join(sorted(models))} | judge | {kind} | - | {stat} | "
           f"{usd['openai'] + usd['anthropic']:.3f} | {co:.3f} | {ca:.3f} |")
    with open(MAIN / "results/blackbox_1112/RUNLOG.md", "a") as f:
        f.write(row + "\n")
    print(row)


if __name__ == "__main__":
    if sys.argv[1] == "row":
        # row "<desc>" "<kind>" raw1,raw2 [prefix]
        runlog_row(sys.argv[2], sys.argv[3], sys.argv[4].split(","), sys.argv[5] if len(sys.argv) > 5 else "")
    else:
        {"dryfiles": cmd_dryfiles, "project": cmd_project, "spend": cmd_spend}[sys.argv[1]]()
