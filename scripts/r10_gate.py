"""R10 P1a gate (PLAN_R10 item 10): latent-rejection share of rejected passes at r10 L0 and H0, with the same-day control.

    python scripts/r10_gate.py           # reads <worktree>/results/private_1112/gpuplan/r10/p05/gate_units.json (P0.5-G)

Broad = R9's `latent|ablat`; narrow = P0.5's NARROW. Every narrow match on a rejected pass is hand-read into
`gate_narrow_handread.json` (private): "latents/removal" (rejects for missing latents or too little removal) or "other".
Gate: hand-read latents/removal rejections <= 5% of rejected passes, for Terra L0 and for Haiku H0 (check and report; D5).
"""
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import r10_reason_scan as RS  # noqa: E402

PRIV = RS.PRIV
OUT = RS.OUT


def main():
    U = json.loads((PRIV / "gate_units.json").read_text())
    hp = PRIV / "gate_narrow_handread.json"
    hr = json.loads(hp.read_text()) if hp.is_file() else {}
    broad = re.compile(r"latent|ablat", re.I)
    res, unread = OrderedDict(), []
    for lv in ("L0", "H0", "L0ctrl", "H0ctrl"):
        us = [u for u in U if u["level"] == lv]
        if not us:
            continue
        D = [u for u in us if u["case"] == "D"]
        Dm = [u for u in D if u["verdict"] == "rejected"]
        cred = [u for u in us if u["verdict"] == "credited"]
        nar = [u for u in Dm if RS.NARROW_RX.search(u["reason"] or "")]
        key = lambda u: f"{u['call_id']}|{u['probe']}"  # noqa: E731
        lat = [u for u in nar if hr.get(key(u)) == "latents/removal"]
        unread += [dict(key=key(u), level=lv, reason=u["reason"]) for u in nar if key(u) not in hr]
        share = len(lat) / len(Dm) if Dm else 0.0
        res[lv] = OrderedDict(
            runs=len({u["cid"] for u in us}), slots=len(us), passes=len(D), rejected_passes=len(Dm),
            rejected_passes_broad=sum(bool(broad.search(u["reason"] or "")) for u in Dm),
            rejected_passes_narrow=len(nar), narrow_hand_read_latents_or_removal=len(lat),
            share_latents_or_removal=round(share, 3),
            credited_citing_latents_broad=sum(bool(broad.search(u["reason"] or "")) for u in cred), credited=len(cred),
            gate=("pass" if share <= 0.05 else "fail") if not lv.endswith("ctrl") else "control (frozen prompt)")
    out = OrderedDict(plan="results/blackbox_1112/gpuplan/r10/PLAN_R10.md item 10", rule=(
        "pass if hand-read narrow matches that reject for missing latents or too little removal are <= 5% of rejected "
        "passes, for Terra L0 and Haiku H0; a check-and-report step (D5)"), unread_narrow_matches=len(unread), levels=res)
    (PRIV / "gate_unread.json").write_text(json.dumps(unread, indent=1) + "\n")
    (OUT.parent / "gate").mkdir(parents=True, exist_ok=True)
    (OUT.parent / "gate" / "gate.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
