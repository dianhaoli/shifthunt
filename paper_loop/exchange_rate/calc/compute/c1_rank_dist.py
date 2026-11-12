"""Item 1: empirical distribution of the truth's proxy rank by item type, and confidence-like signals of proxy error.
Reads (read-only) exp_c.json and followup/solvers/band.json; writes c1_rank_dist.json next to this script.
Aggregates only: no property names, no episode-to-cue pairing."""
import json, os, math
from statistics import NormalDist
R = "/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results/blackbox_1112"
d = json.load(open(f"{R}/exp_c/exp_c.json"))
band = json.load(open(f"{R}/followup/solvers/band.json"))
out = {"rank_counts": {}, "ratio_profile": {}, "G_signal": {}}
def rc(node):
    t = node["fixed"]["top_candidate"]["distinct_instances"]
    return {"n": t["n"], "rank_counts": t["main_rank_counts"], "top1_correct": t["correct"],
            "top1_correct_sign_aware": t["correct_sign_aware"]}
for g in ["ordinary", "trap", "nested", "twomain"]:
    out["rank_counts"][f"{g}/bank_all"] = rc(d[g]["all"])
    if "shipped_six" in d[g]:
        out["rank_counts"][f"{g}/shipped"] = rc(d[g]["shipped_six"])
for p, v in d["trap"]["by_pool"].items():
    out["rank_counts"][f"trap/pool:{p}"] = rc(v)
# ratio profile (|latent ratio| = SAE-visible effect / SAE-visible topic effect; |true ratio| = true effect / topic)
def rp(node):
    r = node["fixed"].get("ratio_profile")
    if not r: return None
    return {k: {q: round(r[k][q], 3) for q in ("n", "min", "q25", "median", "q75", "max")} for k in r}
for key, node in [("trap/shipped", d["trap"]["shipped_six"]), ("trap/bank_all", d["trap"]["all"]),
                  ("nested/shipped", d["nested"]["shipped_six"]), ("nested/bank_all", d["nested"]["all"])] + \
                 [(f"trap/pool:{p}", v) for p, v in d["trap"]["by_pool"].items()]:
    out["ratio_profile"][key] = rp(node)
# Shipped traps: rank-1 (decoy) / rank-2 (main) SAE reading ratio, range bound from min/max (n = 3)
s = out["ratio_profile"]["trap/shipped"]
out["shipped_trap_rank1_over_rank2_latent_ratio_bounds"] = {
    "median_over_median": round(s["nonmain_abs_lat"]["median"] / s["main_abs_lat"]["median"], 2),
    "min_possible": round(s["nonmain_abs_lat"]["min"] / s["main_abs_lat"]["max"], 2),
    "max_possible": round(s["nonmain_abs_lat"]["max"] / s["main_abs_lat"]["min"], 2)}
# G: proxy class-gap / true class-gap from free sample scores (an answer-free confidence signal)
G = band["G"]
out["G_signal"] = {"r_summary": G["r_summary"], "r_shipped_traps": [round(x, 3) for x in G["r_shipped_traps"]],
                   "auroc_bank_traps_vs_ordinary": round(G["auroc_trap_vs_ordinary"], 3),
                   "auroc_shipped_traps_vs_ordinary": round(G["auroc_shipped_traps_vs_ordinary"], 3)}
# binormal d' equivalent of the AUROC: AUROC = Phi(d'/sqrt2)
N = NormalDist()
for k in ("auroc_bank_traps_vs_ordinary", "auroc_shipped_traps_vs_ordinary"):
    a = out["G_signal"][k]
    out["G_signal"][k.replace("auroc", "dprime")] = round(math.sqrt(2) * N.inv_cdf(a), 2)
# Empirical rank laws used by the simulator
out["pi"] = {
    "ordinary": {"1": 1.0}, "nested_after_hypothesis": {"1": 1.0}, "trap_shipped": {"2": 1.0},
    "trap_bank": {"1": 11 / 24, "2": 10 / 24, "6": 3 / 24},
    "trap_bank_all_instances": {k: v / 41 for k, v in d["trap"]["all"]["fixed"]["top_candidate"]["all_instances"]["main_rank_counts"].items()},
}
# Pooled over every planted bank probe type (distinct instances): how often is the proxy's top candidate wrong?
tot = sum(out["rank_counts"][f"{g}/bank_all"]["n"] for g in ["ordinary", "trap", "nested", "twomain"])
wrong = out["rank_counts"]["trap/bank_all"]["n"] - out["rank_counts"]["trap/bank_all"]["top1_correct"]
out["pooled_bank_top1_wrong"] = {"wrong": wrong, "of": tot, "rate": round(wrong / tot, 3)}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "c1_rank_dist.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
