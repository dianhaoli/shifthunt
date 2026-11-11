"""Evidence for the failure-mode headline against the paper audit (main-session code, EXPLORATORY, no LLM call).

    python scripts/followup_rebuttal.py --out results/blackbox_1112/followup/rebuttal

Inputs (all already computed and frozen):
  results/private_1112/followup/failure_modes/slots.json          probe audits of the main study, Open-8, BB arms
  results/private_1112/followup/failure_modes/heldout_slots.json  probe audits of the held-out runs
  results/blackbox_1112/followup/proxy_verify/proxy_verify.json   scripted policies on the six shipped items

Definitions.
  SAE arms: main study (4 agents), Open-8 (GPT, Haiku), held-out runs with the instrument.
  A candidate is "isolated" if the run has an edit-matched clean pair on true logits changing only that property
  (followup_failure_modes.cmd_build). Rank = the SAE's rank among the probe's label-aligned properties.
  Width of a probe audit = the number of isolated candidates when they are exactly the SAE's top k, else "other".
Tables.
  T1 trap hard slots by agent: pass; rank 2 isolated; pass given isolated / not.
  T2 trap failures that never isolated rank 2: exact texts on that probe, in the run, and burst querying.
  T3 what a probe's exact texts buy: tested set by number of texts on the probe (planted probes, SAE arms).
  T4 scripted policies at the same budget (from proxy_verify.json): NAME and error type on traps.
  T5 by trap item.
"""
import argparse
import json
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

from scipy.stats import binomtest, fisher_exact

ROOT = Path(__file__).resolve().parents[1]
PRIV = ROOT / "results" / "private_1112" / "followup" / "failure_modes"
COPY_OF = {"ep481": "ep411", "ep483": "ep413", "ep485": "ep415"}
CLAUDE = ("haiku", "opus", "sonnet")


def load():
    rows = json.loads((PRIV / "slots.json").read_text())
    for r in rows:
        r["arm"] = r["population"]
    ho = json.loads((PRIV / "heldout_slots.json").read_text())
    for r in ho:
        r["arm"] = "heldout" if r["access"] == "open" else "heldout_bb"
    return [r for r in rows + ho if r["arm"] in ("main", "open8", "heldout")]


def tested(r):
    return sorted(c["rank"] for c in r["cands"] if c["tested"])


def width(r):
    t = tested(r)
    return str(len(t)) if t == list(range(1, len(t) + 1)) else "other"


def fisher(a, b, c, d):
    return float(fisher_exact([[a, b - a], [c, d - c]])[1])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = load()
    runs = defaultdict(list)
    for r in rows:
        runs[(r["arm"], r["batch"], r["run"])].append(r)
    out = OrderedDict(sae_runs=len(runs), probe_audits=len(rows))

    traps = [r for r in rows if r["hard"] and r["kind"] == "trap"]
    ok = [r for r in traps if r["texts_ok"]]
    t1 = OrderedDict()
    for name, sel in [(g, lambda r, g=g: r["agent"] == g) for g in ("gpt", "haiku", "opus", "sonnet")] + \
                     [("claude agents", lambda r: r["agent"] in CLAUDE), ("all", lambda r: True)]:
        s, so = [r for r in traps if sel(r)], [r for r in ok if sel(r)]
        iso = [r for r in so if 2 in tested(r)]
        non = [r for r in so if 2 not in tested(r)]
        t1[name] = dict(passed=f"{sum(1 - r['failed'] for r in s)}/{len(s)}",
                        rank2_isolated=f"{len(iso)}/{len(so)}",
                        pass_given_isolated=f"{sum(1 - r['failed'] for r in iso)}/{len(iso)}",
                        pass_given_not=f"{sum(1 - r['failed'] for r in non)}/{len(non)}",
                        fisher_p=fisher(sum(1 - r["failed"] for r in iso), len(iso),
                                        sum(1 - r["failed"] for r in non), len(non)) if iso and non else None)
    out["T1_trap_hard_slots"] = t1
    c = [r for r in traps if r["agent"] in CLAUDE]
    g = [r for r in traps if r["agent"] == "gpt"]
    pv = json.loads((ROOT / "results/blackbox_1112/followup/proxy_verify/proxy_verify.json").read_text())
    ex = pv["results"]["topic"]["exact"]
    top2 = ex["prefix2"]["8"]["by_kind"]["trap"]["name"]
    out["T1_tests"] = dict(
        claude_vs_gpt_pass_fisher_p=fisher(sum(1 - r["failed"] for r in c), len(c), sum(1 - r["failed"] for r in g), len(g)),
        claude_vs_scripted_top_two=dict(scripted=top2, binomial_p=float(binomtest(
            sum(1 - r["failed"] for r in c), len(c), top2, alternative="less").pvalue)),
        claude_vs_gpt_rank2_isolated_fisher_p=fisher(
            sum(2 in tested(r) for r in ok if r["agent"] in CLAUDE), sum(r["agent"] in CLAUDE for r in ok),
            sum(2 in tested(r) for r in ok if r["agent"] == "gpt"), sum(r["agent"] == "gpt" for r in ok)))

    fails = [r for r in ok if r["failed"] and 2 not in tested(r)]
    t2 = OrderedDict(n=len(fails), by_agent=dict(Counter(r["agent"] for r in fails)),
                     texts_on_the_trap_probe=dict(sorted(Counter(min(r["n_texts"], 5) for r in fails).items())),
                     at_least_2_texts_on_the_trap_probe=sum(r["n_texts"] >= 2 for r in fails),
                     tested_set=dict(Counter(width(r) if tested(r) else "nothing isolated" for r in fails)),
                     answer_none=sum(1 - r["named"] for r in fails))
    tot, burst = [], Counter()
    for r in fails:
        rr = runs[(r["arm"], r["batch"], r["run"])]
        if all(x["texts_ok"] for x in rr):
            tot.append(sum(x["n_texts"] for x in rr))
        if r.get("one_burst") is not None:
            burst[int(r["one_burst"])] += 1
    t2["exact_texts_used_in_run"] = dict(sorted(Counter(tot).items()))
    t2["one_burst"] = f"{burst[1]}/{burst[0] + burst[1]}"
    out["T2_trap_failures_without_rank2"] = t2

    t3 = OrderedDict()
    planted = [r for r in rows if r["texts_ok"] and r["kind"] != "null"]
    for lab, sel in (("1 text", lambda n: n == 1), ("2 texts", lambda n: n == 2), ("3-4 texts", lambda n: 3 <= n <= 4),
                     ("5+ texts", lambda n: n >= 5), ("2 or more", lambda n: n >= 2)):
        s = [r for r in planted if sel(r["n_texts"])]
        k = Counter("nothing isolated" if not tested(r) else {"1": "rank 1 only", "2": "ranks 1 and 2"}.get(width(r), "other")
                    for r in s)
        t3[lab] = dict(n=len(s), **{x: k[x] for x in ("rank 1 only", "ranks 1 and 2", "other", "nothing isolated")})
    t3["2 or more, by agent"] = {
        ag: dict(n=sum(1 for r in planted if r["agent"] == ag and r["n_texts"] >= 2),
                 rank1_only=sum(1 for r in planted if r["agent"] == ag and r["n_texts"] >= 2 and tested(r) == [1]),
                 includes_rank2=sum(1 for r in planted if r["agent"] == ag and r["n_texts"] >= 2 and 2 in tested(r)))
        for ag in ("gpt", "haiku", "opus", "sonnet")}
    out["T3_what_exact_texts_buy"] = t3

    t4 = OrderedDict()
    for row in ("proxy_only", "prefix1", "prefix2", "complement_none"):
        for B in ("8", "16"):
            if row == "proxy_only" and B == "16":
                continue
            k = ex[row][B]["by_kind"]["trap"]
            t4[f"{row} @ {0 if row == 'proxy_only' else B}"] = dict(
                name_trap=round(k["name"], 3), hard={x: round(v, 3) for x, v in k["hard"].items()},
                name_two_part=round(ex[row][B]["by_kind"]["two-part"]["name"], 3),
                name_all_six=round(ex[row][B]["pooled"]["name"], 3))
    out["T4_scripted_exact_backend"] = t4

    t5 = OrderedDict()
    for ep in ("ep411", "ep413", "ep415"):
        s = [r for r in ok if COPY_OF.get(r["episode"], r["episode"]) == ep and r["agent"] in CLAUDE]
        iso = [r for r in s if 2 in tested(r)]
        non = [r for r in s if 2 not in tested(r)]
        t5[ep] = dict(claude_pass=f"{sum(1 - r['failed'] for r in s)}/{len(s)}", rank2_isolated=f"{len(iso)}/{len(s)}",
                      pass_given_isolated=f"{sum(1 - r['failed'] for r in iso)}/{len(iso)}",
                      pass_given_not=f"{sum(1 - r['failed'] for r in non)}/{len(non)}",
                      scripted_top_two=round(ex["prefix2"]["8"]["per_episode"][ep]["name"], 2),
                      scripted_top_one=round(ex["prefix1"]["8"]["per_episode"][ep]["name"], 2))
    out["T5_by_trap_item_claude_agents"] = t5
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "rebuttal.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def extra(out_dir):
    """T6-T8, added after the adversarial check (rebuttal/REBUTTAL.md): concentration of exact texts on the trap
    probe, where failing runs' texts went, and the contrast by arm and model version."""
    import statistics as st
    rows = load()
    runs = defaultdict(list)
    for r in rows:
        runs[(r["arm"], r["batch"], r["run"])].append(r)
    out = OrderedDict()
    conc = defaultdict(lambda: [[], []])
    spent = defaultdict(list)
    for key, rr in runs.items():
        hard = [r for r in rr if r["hard"] and r["kind"] == "trap"]
        if len(hard) != 1 or not all(r["texts_ok"] for r in rr):
            continue
        h = hard[0]
        grp = "gpt" if h["agent"] == "gpt" else "claude"
        res = "pass" if not h["failed"] else "fail"
        conc[(grp, res)][0].append(h["n_texts"])
        conc[(grp, res)][1].append(sum(r["n_texts"] for r in rr if not r["hard"]) / max(1, sum(1 for r in rr if not r["hard"])))
        tot = sum(r["n_texts"] for r in rr)
        spent[(grp, res)].append((tot, sum(r["n_texts"] for r in rr if not r["hard"])))
    out["T6_texts_on_trap_probe_vs_each_other_probe"] = {
        f"{g} {res}": dict(runs=len(v[0]), mean_on_trap_probe=round(st.mean(v[0]), 2),
                           mean_on_each_other_probe=round(st.mean(v[1]), 2),
                           runs_with_more_on_trap_probe=sum(a > b for a, b in zip(*v)))
        for (g, res), v in sorted(conc.items())}
    out["T6_budget"] = {f"{g} {res}": dict(runs=len(v), median_total=st.median(t for t, _ in v),
                                           median_to_non_hard_probes=st.median(n for _, n in v))
                        for (g, res), v in sorted(spent.items())}
    nh = [r for r in rows if not r["hard"] and r["texts_ok"]]
    nh_fail_runs = [r for r in nh if any(x["hard"] and x["kind"] == "trap" and x["failed"]
                                         for x in runs[(r["arm"], r["batch"], r["run"])])]
    out["T6_non_hard_probes_in_trap_failure_runs"] = dict(
        passed=f"{sum(1 - r['failed'] for r in nh_fail_runs)}/{len(nh_fail_runs)}",
        passed_with_no_text=f"{sum(1 - r['failed'] for r in nh_fail_runs if r['n_texts'] == 0)}/"
                            f"{sum(1 for r in nh_fail_runs if r['n_texts'] == 0)}")
    t7 = OrderedDict()
    traps = [r for r in rows if r["hard"] and r["kind"] == "trap"]

    def model(r):
        if r["agent"] == "opus":
            return "opus 4.8 (October)" if "4-8" in r.get("agent_full", "") or "4.8" in r.get("agent_full", "") else "opus 5.5"
        return r["agent"]
    for arm in ("main", "open8", "heldout", "all"):
        for m in ("gpt", "haiku", "sonnet", "opus 5.5", "opus 4.8 (October)"):
            s = [r for r in traps if (arm == "all" or r["arm"] == arm) and model(r) == m]
            so = [r for r in s if r["texts_ok"]]
            if s:
                t7[f"{arm} | {m}"] = dict(passed=f"{sum(1 - r['failed'] for r in s)}/{len(s)}",
                                          rank2_isolated=f"{sum(2 in tested(r) for r in so)}/{len(so)}")
    out["T7_by_arm_and_model"] = t7
    p = Path(out_dir) / "rebuttal.json"
    J = json.loads(p.read_text())
    J.update(out)
    p.write_text(json.dumps(J, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if "--extra" in sys.argv:
        extra(sys.argv[sys.argv.index("--extra") + 1])
    else:
        sys.exit(main())
