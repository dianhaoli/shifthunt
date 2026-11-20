"""C6b-H report (results/blackbox_1112/gpuplan/c6bh/PREREG_C6BH.md): Haiku's L2/L2r verdicts next to its C6 rungs.

    python scripts/c6bh_analysis.py        # -> results/blackbox_1112/gpuplan/c6bh/c6bh.json

Reporting only (written after the prereg hash, before any C6b-H result was read): it reuses scripts/judge_ladder2.py's
slot table, kappa bootstrap and McNemar, and scripts/judge_ladder.py's verdict parser, unedited.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import judge_ladder as JL  # noqa: E402
import judge_ladder2 as J2  # noqa: E402

OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "c6bh"


def main():
    _, _, _, rows = J2.load_prompts()
    meta = {m["call_id"]: m for m in json.loads((J2.PRIV / "meta.json").read_text())}
    V = {}
    for cid, r in rows.items():
        for g in ("H0", "H1", "H1r"):
            v, _ = JL.verdicts(JL.PRIV / "raw", f"{g}__{cid}", JL.HAIKU, len(r["naming"]))
            if v is not None:
                V[(g, cid)] = v
    V |= J2.verdict_map("haiku", rows)
    A = sorted(c for c, m in meta.items() if m["group"] == "A" and all((g, c) in V for g in ("H0", "H1", "H1r", "H2")))
    AO = [c for c in A if ("H2r", c) in V]
    out = OrderedDict(prereg="results/blackbox_1112/gpuplan/c6bh/PREREG_C6BH.md", set_A_runs=len(A),
                      open_runs_with_H2r=len(AO))
    for g in ("H0", "H1", "H1r", "H2"):
        out[g] = J2.table(J2.slots(V, rows, g, A))
    d, lo = J2.boot_delta(V, rows, A, "H1", "H2")
    out["delta_kappa_H2_minus_H1"] = OrderedDict(delta=d, one_sided_95_lower=lo)
    out["open_arm"] = OrderedDict((g, J2.table(J2.slots(V, rows, g, AO))) for g in ("H1", "H2", "H2r"))
    out["wrong_cue_credit_H2r_vs_H2_open"] = J2.mcnemar(J2.slots(V, rows, "H2r", AO), J2.slots(V, rows, "H2", AO))
    usd = 0.0
    import textonly_client as TC
    for c in J2.load_calls("haiku"):
        m = TC.read_meta(J2.PRIV / "raw_haiku", c["call_id"])
        usd += float((m or {}).get("usd") or 0)
    out["usd_anthropic"] = round(usd, 3)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "c6bh.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
