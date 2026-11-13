"""C6 supplement (prereg §4, item-level floor): per item, the sign of the change in hard-slot false credit L0r -> L1.

The prereg asks for the per-item sign of the false-credit change; judge_ladder.py analyse (hashed) does not print it.
This reads the same raw verdicts the analysis reads (judge_ladder.verdicts, same set A rule: runs with every rung
parsed) and writes results/blackbox_1112/gpuplan/c6/c6_items.json. Items are reported by episode id only.

    python scripts/c6_items.py
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import judge_ladder as JL  # noqa: E402
import score_naming as SN  # noqa: E402
from scipy.stats import binomtest  # noqa: E402


def main():
    rows = {r["call_id"]: r for r in json.loads((JL.L0_PRIV / "rows.json").read_text())}
    l0 = {(s["call_id"], s["probe"]): s["judge"] for s in json.loads((JL.L0_PRIV / "slots.json").read_text())}
    calls = [json.loads(line) for line in (JL.PRIV / "calls.jsonl").read_text().splitlines()]
    V = {}
    for c in calls:
        rung, cid = c["call_id"].split("__", 1)
        if cid not in rows:
            continue
        v, _ = JL.verdicts(JL.PRIV / "raw", c["call_id"], c["model"], len(rows[cid]["naming"]))
        if v is not None:
            V[(rung, cid)] = v
    for cid, r in rows.items():
        if JL.SET_A.match(r["batch"]) and all((cid, j) in l0 for j in range(len(r["naming"]))):
            V[("L0", cid)] = {j: (bool(l0[(cid, j)]), None) for j in range(len(r["naming"]))}
    rungs = ("L0", "L0r", "L1", "L1r", "H0", "H1", "H1r")
    A = sorted(cid for cid, r in rows.items() if JL.SET_A.match(r["batch"]) and all((g, cid) in V for g in rungs))
    ep_of = {}
    for b in sorted({cid.split("__")[0] for cid in A}):
        for r in SN.load_batch(JL.JV.RAW / b):
            ep_of[(b, r["run"])] = r["episode"]
    per = OrderedDict()
    for cid in A:
        r = rows[cid]
        ep = ep_of[tuple(cid.split("__"))]
        d = per.setdefault(ep, OrderedDict(hard_failures=0, credited_L0r=0, credited_L1=0, credited_L1r=0))
        for j in r["hard"]:
            if r["naming"][j]:
                continue
            d["hard_failures"] += 1
            for g in ("L0r", "L1", "L1r"):
                d[f"credited_{g}"] += int(V[(g, cid)][j][0])
    for d in per.values():
        diff = d["credited_L1"] - d["credited_L0r"]
        d["sign_L1_minus_L0r"] = "+" if diff > 0 else "-" if diff < 0 else "0"
    signs = [d["sign_L1_minus_L0r"] for d in per.values()]
    neg, pos = signs.count("-"), signs.count("+")
    out = OrderedDict(
        set_A_runs=len(A), items=per,
        summary=OrderedDict(fewer_credited_at_L1=neg, more_credited_at_L1=pos, unchanged=signs.count("0"),
                            sign_test_one_sided=(binomtest(neg, neg + pos, 0.5, alternative="greater").pvalue
                                                 if neg + pos else None),
                            note="sign-test floor with 6 items is 1/64 = 0.016 one-sided (0.031 two-sided)"))
    p = JL.OUT / "c6_items.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
