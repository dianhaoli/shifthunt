"""B4 (round 3, $0): scripts for body numbers that had no committed generating script.

    python scripts/body_numbers.py      # -> results/blackbox_1112/gpuplan/b/body_numbers.json

  none_vs_named_error  wrong `none` verdicts among all `none` verdicts vs wrong named claims among named claims, the
                       100 proxy runs at 8 queries (main study 64 + Open-8 36), from followup/failure_modes.json
                       (its `none_answers_wrong` field counts planted `none` answers only, all wrong by definition;
                       the correct `none` answers are the null probes answered `none`).
  main_pq_used_all     main-study counted runs that used every exact query (grade.json budget.probe_query).
  removal_named_mains  main-study main cues named correctly (planted probe, identified) and whether each passed the
                       latent-removal check (removal >= tau per main, grade.json details).
  terra_tokens         Block 1 Terra Open-8 vs BB-8 output tokens (rows_r1112.csv) and the proxy gain when every
                       run above the proxy arm's median is counted as failed.
  mde_16               the smallest pass-rate difference detectable at 80% power by a two-sided exact Fisher test
                       at alpha 0.05 with 16 runs per arm (the power function of docs/figures/make_cross_model_figures.py), for rates
                       symmetric around 0.5 and for a top rate of 1.0.
"""
import csv
import math
import json
import statistics
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import judge_vs_grade as JV  # noqa: E402
import score_naming as SN  # noqa: E402

OUT = ROOT / "results" / "blackbox_1112" / "gpuplan" / "b"
MAIN = [f"r1103_{a}_{b}" for a in ("gpt", "opus", "sonnet", "haiku") for b in ("b1", "b2")]


def fisher_p(a, n1, c, n2):
    """Two-sided exact Fisher p (verbatim from docs/figures/make_cross_model_figures.py, which needs matplotlib)."""
    k = a + c
    h = lambda x: math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n1 + n2, k)
    p0 = h(a)
    return sum(h(x) for x in range(max(0, k - n2), min(k, n1) + 1) if h(x) <= p0 * (1 + 1e-9))


def power(p1, p2, n, alpha=0.05):
    """Exact power of a two-sided Fisher test with n runs per arm (verbatim, same source)."""
    b1 = [math.comb(n, x) * p1 ** x * (1 - p1) ** (n - x) for x in range(n + 1)]
    b2 = [math.comb(n, x) * p2 ** x * (1 - p2) ** (n - x) for x in range(n + 1)]
    return sum(b1[x] * b2[y] for x in range(n + 1) for y in range(n + 1) if fisher_p(x, n, y, n) <= alpha)


def k_n(s):
    k, n = s.split("/")
    return int(k), int(n)


def main():
    out = OrderedDict(script="scripts/body_numbers.py")
    fm = json.loads((ROOT / "results/blackbox_1112/followup/failure_modes/failure_modes.json").read_text())
    c = fm["C_error_types"]["with instrument|all"]
    nw, nn = k_n(c["named_answers_wrong"])
    pw, _ = k_n(c["none_answers_wrong"])
    nf, nnull = k_n(c["null_false_claims"])
    none_total = pw + (nnull - nf)
    out["none_vs_named_error"] = OrderedDict(
        verdicts=nn + none_total, named=f"{nw}/{nn} = {nw / nn:.3f}",
        none=f"{pw}/{none_total} = {pw / none_total:.3f}",
        note="`none` verdicts = planted probes answered none (all wrong) + null probes answered none (right)")
    used, rem = [], {"named_mains": 0, "passed_removal": 0}
    for b in MAIN:
        for r in SN.load_batch(JV.RAW / b):
            if not r.get("counted"):
                continue
            g = json.loads((JV.RAW / b / r["run"] / "grade.json").read_text())
            pq = g["budget"]["probe_query"]
            used.append(pq["used"] >= pq["limit"])
            for p in g["details"]["probes"]:
                if p.get("kind") == "planted" and (p.get("checks") or {}).get("identified"):
                    for x, t in zip(p.get("removal") or [], p.get("tau") or []):
                        rem["named_mains"] += 1
                        rem["passed_removal"] += x >= t
    out["main_pq_used_all"] = f"{sum(used)}/{len(used)}"
    out["removal_named_mains"] = rem
    rows = [r for r in csv.DictReader(open(ROOT / "results/blackbox_1112/rows_r1112.csv"))
            if r["agent"] == "gpt" and r["arm"] in ("open8", "bb8") and r["counted"] == "1"]
    arm = {a: [r for r in rows if r["arm"] == a] for a in ("open8", "bb8")}
    med = {a: statistics.median(float(r["tokens_out"]) for r in arm[a]) for a in arm}
    cut = med["open8"]
    adj = {a: sum(1 for r in arm[a] if r["name"] == "1" and float(r["tokens_out"]) <= cut) / len(arm[a]) for a in arm}
    raw = {a: sum(r["name"] == "1" for r in arm[a]) / len(arm[a]) for a in arm}
    out["terra_tokens"] = OrderedDict(runs={a: len(arm[a]) for a in arm}, median_tokens_out=med,
                                      pass_rate=raw, pass_rate_above_proxy_median_failed=adj,
                                      gain_raw=round(raw["open8"] - raw["bb8"], 3),
                                      gain_tokens_capped=round(adj["open8"] - adj["bb8"], 3))
    def mde(fn):
        for d100 in range(1, 101):
            d = d100 / 100
            p1, p2 = fn(d)
            if 0 <= p1 <= 1 and 0 <= p2 <= 1 and power(p1, p2, 16) >= 0.8:
                return d
        return None
    out["mde_16"] = OrderedDict(symmetric_around_half=mde(lambda d: (0.5 - d / 2, 0.5 + d / 2)),
                                top_rate_1=mde(lambda d: (1 - d, 1.0)))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "body_numbers.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
