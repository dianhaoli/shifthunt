"""The judge ladder L0 -> L1 -> L2 -> L3 in one table (RESULTS_FOR_PAPER.md), from the C6 / C6b / C6c verdicts.

    python scripts/ladder_table.py        # -> results/blackbox_1112/gpuplan/c6c/ladder.json

Reporting only ($0, no call): every cell is `judge_ladder2.table(slots(...))` on the same run lists that
`judge_ladder2.py analyse` uses, so set A, Luna and main-study cells equal c6.json / c6b.json / c6c.json; the one new
cell is the harder variant's L0 (its L0 verdicts are the 12 Nov frozen-judge calls, read by `c6_verdicts`).
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import judge_ladder2 as J2  # noqa: E402

OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "c6c"

LADDER = (("set_A", "A", (("L0", "L0"), ("L1", "L1"), ("L2", "L2"), ("L3 = L1 + key", "L3_1"), ("L3 = L2 + key", "L3_2"))),
          ("luna", "luna", (("L0", "L0"), ("L1", "L1"), ("L2", "L2"), ("L3 = L1 + key", "L3_1"), ("L3 = L2 + key", "L3_2"))),
          ("main_study", "main", (("L0", "L0"), ("L2", "L2"), ("L2r", "L2r"), ("L3 = L2 + key", "L3_2"))),
          ("harder_variant", "harder", (("L0", "L0"), ("L3 = L0 + key", "L3_0"))))


def main():
    _, _, _, rows = J2.load_prompts()
    meta = {m["call_id"]: m for m in json.loads((J2.PRIV / "meta.json").read_text())}
    V = J2.c6_verdicts(rows)
    for item in ("c6b", "c6c"):
        V |= J2.verdict_map(item, rows)
    out = OrderedDict(note="Terra judge; hard-slot kappa vs the certified grade; each set on one fixed run list "
                           "(runs with every rung of that set parsed)")
    for name, g, rungs in LADDER:
        ids = [c for c in sorted(c for c, m in meta.items() if m["group"] == g and "problem" not in m)
               if all((r, c) in V for _, r in rungs)]
        s = OrderedDict(runs=len(ids))
        for label, r in rungs:
            s[label] = J2.table(J2.slots(V, rows, r, ids))
        out[name] = s
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ladder.json").write_text(json.dumps(out, indent=1) + "\n")
    for name, s in out.items():
        if name == "note":
            continue
        print(name, s["runs"], {k: (v["hard_kappa"], v["false_credit_none"], v["false_credit_wrong_cue"], v["false_blame"])
                                for k, v in s.items() if k != "runs"})


if __name__ == "__main__":
    main()
