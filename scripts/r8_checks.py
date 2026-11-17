"""R8 (round 8, $0, stored data; results/blackbox_1112/gpuplan/r8/PREREG_R8.md, frozen in 275b4d8): six checks.

    python scripts/r8_checks.py first      # checks 1 and 2 -> gpuplan/r8/r8_12.json
    python scripts/r8_checks.py rest       # checks 3-6     -> gpuplan/r8/r8_36.json

Scores: p(correct) on 0-100 from stored verdicts. Terra L0 = the 12 Nov frozen-judge verdicts (results/private_1112/
judge/slots.json) for set A and the main study, C8's for Luna; Terra L1, L2, L2r from C6 / C6b; Sol L2 = round 5 S2.
"""
import json
import os
import random
import statistics
import sys
from collections import Counter, OrderedDict
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import judge_ladder as JL  # noqa: E402
import judge_ladder2 as J2  # noqa: E402
import judge_vs_grade as JV  # noqa: E402
import keyless_verifier as KV  # noqa: E402

OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "r8"
TRAPS = ("ep411", "ep413", "ep415")
N_BOOT, SEED = 10000, 1116
SETNAME = {"A": "set_A", "luna": "luna", "main": "main_study"}


def pc(ok, conf):
    return float(conf) if ok else 100.0 - float(conf)


def load():
    import sol_judge as SJ
    _, _, _, rows = J2.load_prompts()
    meta = {m["call_id"]: m for m in json.loads((J2.PRIV / "meta.json").read_text())}
    G = {g: sorted(c for c, m in meta.items() if m["group"] == g and "problem" not in m) for g in ("A", "luna", "main")}
    eps = KV.episodes_of({c.split("__")[0] for g in G.values() for c in g})
    S = {"L0": {}, "L0_c8": {}, "L1": {}, "L2": {}, "L2r": {}, "Sol_L2": {}, "Sol_SF": {}}
    luna = set(G["luna"])
    for s in json.loads((JL.L0_PRIV / "slots.json").read_text()):
        if s["call_id"] not in luna and s.get("conf") is not None:
            S["L0"][(s["call_id"], int(s["probe"]))] = (bool(s["judge"]), pc(s["judge"], s["conf"]))
    for s in json.loads((JL.C8_PRIV / "slots.json").read_text()):
        if s.get("conf") is None:
            continue
        key = (s["call_id"], int(s["probe"]))
        if s["call_id"] in luna:
            S["L0"][key] = (bool(s["judge"]), pc(s["judge"], s["conf"]))
        S["L0_c8"][key] = (bool(s["judge"]), pc(s["judge"], s["conf"]))
    V = J2.c6_verdicts(rows)
    V |= J2.verdict_map("c6b", rows)
    for (rung, cid), v in V.items():
        if rung in ("L1", "L2", "L2r"):
            for j, (ok, conf) in v.items():
                S[rung][(cid, j)] = (bool(ok), pc(ok, conf))
    SV, _, _ = SJ.sol_verdicts(rows)
    for (rung, cid), v in SV.items():
        for j, x in v.items():
            if rung == "S2":
                S["Sol_L2"][(cid, j)] = (bool(x[0]), pc(x[0], x[1]))
            elif rung == "SF":
                S["Sol_SF"][(cid, j)] = x
    return rows, meta, G, eps, S


def none_slots(rows, G, eps, S):
    out = []
    for g, cids in G.items():
        for cid in cids:
            r = rows[cid]
            proxy = g == "main" or str(r["access"]).startswith("open")
            for j, ok in enumerate(r["naming"]):
                named = r["named"][j] if j < len(r["named"]) else 0
                if named:
                    continue
                kind = ("null" if r["kinds"][j] == "null" else
                        ("trap" if eps[cid] in TRAPS else "two-part") if j in r["hard"] else "other planted")
                out.append(dict(cid=cid, item=eps[cid], set=SETNAME[g], agent=r["agent"], arm=cid.split("__")[0].rsplit("_", 1)[1],
                                proxy=proxy, probe=j, hard=int(j in r["hard"]), kind=kind, cert=int(ok),
                                v={lv: S[lv].get((cid, j)) for lv in ("L0", "L1", "L2", "L2r", "Sol_L2")}))
    return out


def pairs_of(slots):
    by = {}
    for s in slots:
        by.setdefault(s["cid"], []).append(s)
    P = []
    for cid, T in by.items():
        for a in T:
            if a["kind"] == "null" and a["cert"]:
                for b in T:
                    if b["hard"] and not b["cert"]:
                        P.append((a, b))
    return P


def bal_acc(T, pred):
    pos = [s for s in T if s["cert"]]
    neg = [s for s in T if not s["cert"]]
    if not pos or not neg:
        return None
    return 0.5 * (sum(pred(s) for s in pos) / len(pos) + sum(1 - pred(s) for s in neg) / len(neg))


def choose_cut(T, lv):
    best = None
    for c in range(0, 102):
        b = bal_acc(T, lambda s: int(s["v"][lv][1] >= c))
        if b is None:
            return None
        key = (-round(b, 12), abs(c - 50), c)
        if best is None or key < best[0]:
            best = (key, c, b)
    return best[1], best[2]


def item_boot_ba(T, flag):
    groups = {}
    for s in T:
        groups.setdefault(s["item"], []).append(s)
    ks = sorted(groups)
    rng = random.Random(SEED)
    vals = []
    for _ in range(N_BOOT):
        U = [x for _ in ks for x in groups[ks[rng.randrange(len(ks))]]]
        b = bal_acc(U, lambda s: s[flag])
        if b is not None:
            vals.append(b)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 4), round(vals[min(len(vals) - 1, int(0.975 * len(vals)))], 4)] if vals else None


def counts(T, flag):
    w = [s for s in T if not s["cert"]]
    r = [s for s in T if s["cert"]]
    return OrderedDict(wrong_none_passed=f"{sum(s[flag] for s in w)}/{len(w)}",
                       right_none_passed=f"{sum(s[flag] for s in r)}/{len(r)}",
                       balanced_accuracy=None if bal_acc(T, lambda s: s[flag]) is None else round(bal_acc(T, lambda s: s[flag]), 4),
                       item95=item_boot_ba(T, flag))


def calibrate(T0, lv):
    T = [dict(s) for s in T0 if s["v"][lv] is not None]
    items = sorted({s["item"] for s in T})
    cuts = OrderedDict()
    for it in items:
        tr = [s for s in T if s["item"] != it]
        ch = choose_cut(tr, lv)
        cuts[it] = None if ch is None else ch[0]
        for s in T:
            if s["item"] == it:
                s["loo"] = None if ch is None else int(s["v"][lv][1] >= ch[0])
    for s in T:
        s["default"] = int(s["v"][lv][0])
        s["p50"] = int(s["v"][lv][1] > 50)
    g = choose_cut(T, lv)
    for s in T:
        s["glob"] = int(s["v"][lv][1] >= g[0])
    ok = [s for s in T if s["loo"] is not None]
    return OrderedDict(
        slots=len(T), items=len(items), folds_not_computable=sum(1 for v in cuts.values() if v is None),
        leave_one_item_out=counts(ok, "loo"), cut_offs_by_held_out_fold=list(cuts.values()),
        default_verdict=counts(T, "default"), p_correct_over_50=counts(T, "p50"),
        global_in_sample_optimistic=OrderedDict(cut_off=g[0], **counts(T, "glob")))


def check1(slots):
    out = OrderedDict(caveat="the score separates a [null] probe from a planted one partly by probe identity (X7)")
    P = [s for s in slots if s["proxy"] and (s["kind"] == "null" or s["kind"] != "null")]
    pairs = pairs_of(P)
    ps = {(s["cid"], s["probe"]) for a, b in pairs for s in (a, b)}
    for lv in ("L2", "Sol_L2", "L0"):
        out[lv] = OrderedDict(all_none_slots=calibrate(P, lv),
                              pairs_40_subset=calibrate([s for s in P if (s["cid"], s["probe"]) in ps], lv))
    out["population"] = OrderedDict(none_slots=len(P), right=sum(s["cert"] for s in P), wrong=sum(1 - s["cert"] for s in P),
                                    pairs=len(pairs), pair_slots=len(ps),
                                    wrong_by_kind=dict(Counter(s["kind"] for s in P if not s["cert"])))
    return out


def gap_intervals(T, L, key):
    import numpy as np
    eps = TRAPS
    rng = np.random.default_rng(1113)
    bt = {e: [s[key] for s in T if s["item"] == e] for e in eps}
    bl = {e: [s[key] for s in L if s["item"] == e] for e in eps}
    c8 = []
    for _ in range(N_BOOT):
        t = np.concatenate([rng.choice(bt[e], len(bt[e])) for e in eps if bt[e]])
        l = np.concatenate([rng.choice(bl[e], len(bl[e])) for e in eps if bl[e]])
        c8.append(t.mean() - l.mean())
    r = random.Random(SEED)
    it = []
    for _ in range(N_BOOT):
        pick = [eps[r.randrange(3)] for _ in eps]
        t = [x for e in pick for x in bt[e]]
        l = [x for e in pick for x in bl[e]]
        if t and l:
            it.append(sum(t) / len(t) - sum(l) / len(l))
    r = random.Random(SEED)
    tv, lv = [s[key] for s in T], [s[key] for s in L]
    run = []
    for _ in range(N_BOOT):
        t = [tv[r.randrange(len(tv))] for _ in tv]
        l = [lv[r.randrange(len(lv))] for _ in lv]
        run.append(sum(t) / len(t) - sum(l) / len(l))

    def ci(v):
        v = sorted(v)
        return [round(float(v[int(0.025 * len(v))]), 3), round(float(v[min(len(v) - 1, int(0.975 * len(v)))]), 3)]
    return OrderedDict(c8_method=ci(c8), item=ci(it), run=ci(run))


def check2(rows, eps, S):
    T, L = [], []
    for cid, r in rows.items():
        b = cid.split("__")[0]
        if b not in ("r1112_gpt_open8", "r1112_luna_open8") or eps.get(cid) not in TRAPS:
            continue
        j = r["hard"][0]
        s = dict(cid=cid, item=eps[cid], cert=int(r["naming"][j]), named=r["named"][j] if j < len(r["named"]) else 0)
        for lv, src in (("L0", "L0_c8"), ("L0_12nov", "L0"), ("L1", "L1"), ("L2", "L2"), ("Sol_L2", "Sol_L2")):
            v = S[src].get((cid, j))
            s[lv] = None if v is None else int(v[0])
        (T if b == "r1112_gpt_open8" else L).append(s)
    out = OrderedDict(terra_runs=len(T), luna_runs=len(L), runs_per_item=OrderedDict(
        (e, [sum(1 for s in T if s["item"] == e), sum(1 for s in L if s["item"] == e)]) for e in TRAPS))
    out["note_runs_per_item"] = "[Terra, Luna] runs per trap item"
    for lv in ("cert", "L0", "L0_12nov", "L1", "L2", "Sol_L2"):
        if any(s[lv] is None for s in T + L):
            out[lv] = f"missing: {sum(s[lv] is None for s in T + L)} slots"
            continue
        tr, lr = sum(s[lv] for s in T) / len(T), sum(s[lv] for s in L) / len(L)
        blk = OrderedDict(terra=f"{sum(s[lv] for s in T)}/{len(T)}", luna=f"{sum(s[lv] for s in L)}/{len(L)}",
                          gap=round(tr - lr, 3), intervals=gap_intervals(T, L, lv))
        if lv != "cert":
            lw = [s for s in L if not s["cert"]]
            blk["luna_wrong_none_passed"] = f"{sum(s[lv] for s in lw if not s['named'])}/{sum(1 for s in lw if not s['named'])}"
            blk["luna_wrong_cue_passed"] = f"{sum(s[lv] for s in lw if s['named'])}/{sum(1 for s in lw if s['named'])}"
            blk["terra_correct_failed"] = f"{sum(1 - s[lv] for s in T if s['cert'])}/{sum(s['cert'] for s in T)}"
            blk["terra_wrong_passed"] = f"{sum(s[lv] for s in T if not s['cert'])}/{sum(1 - s['cert'] for s in T)}"
            blk["luna_correct_failed"] = f"{sum(1 - s[lv] for s in L if s['cert'])}/{sum(s['cert'] for s in L)}"
        out["executed" if lv == "cert" else lv] = blk
    out["reference"] = OrderedDict(executed_gap_c8=0.86, report_level_judged_gap_c8=[-0.19, -0.42, 0.03])
    return out


def cmd_first():
    rows, meta, G, eps, S = load()
    slots = none_slots(rows, G, eps, S)
    out = OrderedDict(prereg="results/blackbox_1112/gpuplan/r8/PREREG_R8.md", label="pre-specified, post hoc to the data",
                      script="scripts/r8_checks.py first", check1_threshold_calibration=check1(slots),
                      check2_trap_gap=check2(rows, eps, S))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "r8_12.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"first": cmd_first}[sys.argv[1]]()
