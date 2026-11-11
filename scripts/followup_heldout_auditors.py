"""Held-out auditors vs mechanical flags and outcome (followup/heldout). Main-session code; exploratory.

    python scripts/followup_heldout_auditors.py

Inputs (private):
- auditor_A.jsonl and auditor_B.jsonl: blinded Claude auditors, codes A1, A2, A3;
- heldout_runs.json: the mechanical C1, C2, C3 and the outcome.

Mapping:
- A1 = 1 means the main was isolated, so it agrees with C1 = 0;
- A2 matches C2;
- A3 matches C3.

Output: tracked heldout/auditors.json with kappas and the auditors' own thesis tests (one-sided Fisher, as in
the pre-registration).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import followup_heldout as H  # noqa: E402
import coder_mech_agree as K  # noqa: E402

P = ROOT / "results/private_1112/followup/heldout"


def val(x):
    return x if x in (0, 1) else None


def main():
    runs = {r["run"]: r for r in json.loads((P / "heldout_runs.json").read_text())}
    aud = {w: {json.loads(l)["run"]: json.loads(l) for l in (P / f"auditor_{w}.jsonl").read_text().splitlines()
               if l.strip()} for w in "AB"}
    out = {"n_runs": len(runs)}
    pairs = {}
    for name, mech, code, inv in (("thesis1", "C1", "A1", True), ("thesis2", "C2", "A2", False),
                                  ("thesis3", "C3", "A3", False)):
        res = {}
        for w in "AB":
            pp = []
            for run, r in runs.items():
                a = val(aud[w].get(run, {}).get(code))
                m = r.get(mech)
                if a is None or m is None:
                    continue
                pp.append((1 - a if inv else a, m))
            res[f"{w}_vs_mech"] = dict(n=len(pp), kappa=K.kappa(pp), agree=sum(x == y for x, y in pp))
            items = []
            for run, r in runs.items():
                a = val(aud[w].get(run, {}).get(code))
                if a is None:
                    continue
                if name == "thesis2" and r["access"] != "open":
                    continue
                items.append(dict(failed=r["failed"], F=(1 - a if inv else a)))
            grp = (lambda x: not x["failed"]) if name == "thesis3" else (lambda x: x["failed"])
            res[f"{w}_thesis_test"] = H.rule(items, "F", grp, "in group 1", "in group 2")
        ab = []
        for run in runs:
            a, b = val(aud["A"].get(run, {}).get(code)), val(aud["B"].get(run, {}).get(code))
            if a is not None and b is not None:
                ab.append((a, b))
        res["A_vs_B"] = dict(n=len(ab), kappa=K.kappa(ab), agree=sum(x == y for x, y in ab))
        out[name] = res
    (ROOT / "results/blackbox_1112/followup/heldout/auditors.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
