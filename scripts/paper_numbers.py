#!/usr/bin/env python3
"""Check the paper's numbers against the result files in this repository (CPU, stdlib only, about a second).

    python scripts/paper_numbers.py            # print every check; exit 1 if any number differs
    python scripts/paper_numbers.py --md out.md  # also write the table as markdown

Each check names the paper location, the value printed in the paper, the value recomputed from a tracked file,
and that file. Paper values are transcribed from "Nothing Found, Nothing Checked: Testing LLM Judges on Research
Agents' Null Results against Planted Ground Truth". All judge numbers use the corrected judge prompt (round 10,
results/blackbox_1112/gpuplan/r10/); Table 7 compares it with the original prompt.

Names used in the result files and in the paper:
    set_A       the core set (130 Terra and Haiku rollouts with and without the SAE tools, B = 8-64)
    luna        Luna's 60 rollouts                     main_study   the 64 four-agent rollouts
    L0 / L1 / L2   Terra given the report / report + log / transcript;   L3_2  Terra, transcript + ground truth
    S0 / S1 / S2   Sol at the same levels;  S3  Sol, report + ground truth;  K0  Terra, report + ground truth
    H0 / H2        Haiku, report / transcript;  F1  Terra with the rubric (report + log)
    case D / A     correct named answer / correct none;  case B  incorrect null;  case E  wrong shortcut
A few figures need the per-answer verdicts, which are not tracked (see docs/DATA.md): Figure 1b is listed as
"needs per-answer data" and is not counted as a failure.
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
BB = RES / "blackbox_1112"
R10 = BB / "gpuplan" / "r10"
OUT = R10 / "out" / "gpuplan"
SETS = ("set_A", "luna", "main_study")


def load(p):
    return json.loads(Path(p).read_text())


def frac(s):
    a, b = s.split("/")
    return int(a), int(b)


def table3(tag):
    return {s: load(R10 / f"table3_{tag}_{s}.json")["levels"] for s in SETS}


def pooled(T, level, key, sets=SETS):
    """Sum a/b over the sets that ran this level; None if none did."""
    xs = [frac(T[s][level][key]) for s in sets if level in T[s]]
    return (sum(a for a, _ in xs), sum(b for _, b in xs)) if xs else None


def credited(x):  # 'passes_rejected' -> credited correct answers
    return (x[1] - x[0], x[1])


CHECKS = []


def check(where, paper, value, source):
    CHECKS.append((where, str(paper), None if value is None else str(value), source))


def r2(x):
    """Round half up to two decimals, as printed in the paper (the files store three)."""
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def fs(x):
    return None if x is None else f"{x[0]}/{x[1]}"


# ---------------------------------------------------------------- Table 1: episodes passed (ground truth)
def table1():
    rows = [r for r in csv.DictReader(open(BB / "rows_r1112.csv")) if r["counted"] == "1"]
    n, c = Counter(), Counter()
    for r in rows:
        n[(r["agent"], r["arm"])] += 1
        c[(r["agent"], r["arm"])] += int(float(r["name"] or 0))
    src = "results/blackbox_1112/rows_r1112.csv (column name)"
    core = dict(c), dict(n)
    for (agent, arm), paper in {("gpt", "open8"): "23/24", ("gpt", "bb8"): "6/24", ("gpt", "bb64"): "24/24",
                                ("haiku", "open8"): "5/12", ("haiku", "bb8"): "3/12", ("haiku", "bb64"): "8/12"}.items():
        check(f"Table 1 / core set: {agent} {arm}", paper, f"{c[(agent, arm)]}/{n[(agent, arm)]}", src)
    cm = [r for r in csv.DictReader(open(RES / "cross_model_1103" / "rollouts.csv")) if r["batch"] in ("b1", "b2")]
    n, c = Counter(), Counter()
    for r in cm:
        n[r["agent"]] += 1
        c[r["agent"]] += int(float(r["hard_pass"] or 0))
    for agent, paper in {"gpt": "14/16", "opus": "11/16", "sonnet": "12/16", "haiku": "8/16"}.items():
        check(f"Table 1 / four-agent rollouts: {agent}", paper, f"{c[agent]}/{n[agent]}",
              "results/cross_model_1103/rollouts.csv (hard_pass; every other probe passed)")
    t = (c["gpt"] + core[0][("gpt", "open8")], n["gpt"] + core[1][("gpt", "open8")])
    h = (c["haiku"] + core[0][("haiku", "open8")], n["haiku"] + core[1][("haiku", "open8")])
    check("Table 1: Terra with the SAE tools, B = 8", "37/40", f"{t[0]}/{t[1]}", "sum of the two rows above")
    check("Table 1: Haiku with the SAE tools, B = 8", "13/28", f"{h[0]}/{h[1]}", "sum of the two rows above")
    bb16 = load(BB / "bb16" / "analysis" / "bb16_analysis.json")["primary"]
    check("Table 1: Terra, no SAE tools, B = 16", "16/24", f"{bb16['x']}/{bb16['n']}",
          "results/blackbox_1112/bb16/analysis/bb16_analysis.json")
    luna = load(BB / "luna" / "luna.json")
    for arm, paper in {"luna_open8": "5/36", "luna_bb8": "1/24"}.items():
        check(f"Table 1: Luna {arm[5:]}", paper, luna[arm]["name_all"], "results/blackbox_1112/luna/luna.json")
    check("Table 1: Luna, second-ranked tested", "0/18", luna["luna_open8"]["trap_rank2_isolated"],
          "results/blackbox_1112/luna/luna.json")


# ---------------------------------------------------------------- Tables 2 and 8: judge credit by evidence level
TABLE2 = {  # level: (inc nulls of 77, wrong shortcuts of 38, correct rejected of 139, core-set inc nulls of 26, kappa)
    "L0": ("50", "23", "9", "19", "0.32"), "L1": ("-", "-", "-", "19", "0.43"), "L2": ("39", "16", "11", "16", "0.46"),
    "S0": ("-", "-", "-", "18", "0.37"), "S2": ("42", "22", "5", "18", "0.39"), "H0": ("-", "-", "-", "8", "0.01"),
    "H2": ("-", "-", "-", "17", "0.17"), "K0": ("-", "-", "-", "0", "0.84"), "S3": ("-", "-", "-", "0", "0.82"),
    "L3_2": ("0", "1", "0", "0", "1.00"),
}
TABLE8 = {  # level: core inc nulls, luna inc nulls, other agents inc nulls, core correct rejected, kappa [95%]
    "L0": ("19", "19", "12", "6", "0.32 [0.09, 0.53]"), "L1": ("19", "18", "-", "4", "0.43 [0.33, 0.54]"),
    "L2": ("16", "15", "8", "6", "0.46 [0.34, 0.60]"), "S0": ("18", "-", "-", "3", "0.37 [0.15, 0.58]"),
    "S2": ("18", "18", "6", "3", "0.39 [0.31, 0.46]"), "H0": ("8", "-", "-", "69", "0.01 [-0.06, 0.08]"),
    "H2": ("17", "-", "-", "32", "0.17 [0.08, 0.26]"), "K0": ("0", "0", "-", "10", "0.84 [0.61, 1.00]"),
    "S3": ("0", "-", "-", "10", "0.82 [0.60, 0.98]"), "L3_2": ("0", "0", "0", "0", "1.00 [1.00, 1.00]"),
}


def table2_and_8():
    T = table3("r10")
    src = "results/blackbox_1112/gpuplan/r10/table3_r10_{set_A,luna,main_study}.json"
    for lv, (inc, wrong, rej, core, kap) in TABLE2.items():
        full = all(lv in T[s] for s in SETS)
        if inc != "-":
            check(f"Table 2 {lv}: incorrect nulls credited (of 77)", f"{inc}/77",
                  fs(pooled(T, lv, "wrong_none_credited")) if full else None, src)
            check(f"Table 2 {lv}: wrong shortcuts credited (of 38)", f"{wrong}/38",
                  fs(pooled(T, lv, "wrong_cues_credited")) if full else None, src)
            check(f"Table 2 {lv}: correct answers rejected (of 139)", f"{rej}/139",
                  fs(pooled(T, lv, "passes_rejected")) if full else None, src)
        check(f"Table 2 {lv}: core set incorrect nulls credited (of 26)", f"{core}/26",
              T["set_A"][lv]["wrong_none_credited"], src)
        check(f"Table 2 {lv}: kappa, core set", kap, r2(T['set_A'][lv]['hard_kappa']), src)
    for lv, (core, luna, other, crej, kap) in TABLE8.items():
        if luna != "-":
            check(f"Table 8 {lv}: Luna incorrect nulls credited (of 38)", f"{luna}/38", T["luna"][lv]["wrong_none_credited"], src)
        if other != "-":
            check(f"Table 8 {lv}: other agents incorrect nulls credited (of 13)", f"{other}/13",
                  T["main_study"][lv]["wrong_none_credited"], src)
        d = T["set_A"][lv]["passes_rejected"]
        check(f"Table 8 {lv}: core set correct answers rejected", crej, d.split("/")[0], src)
        lo, hi = T["set_A"][lv]["item95"]
        check(f"Table 8 {lv}: kappa [95%]", kap, f"{r2(T['set_A'][lv]['hard_kappa'])} [{lo:.2f}, {hi:.2f}]", src)


# ---------------------------------------------------------------- Table 3: interventions (core set, Terra)
def table3_interventions():
    T = table3("r10")["set_A"]
    src = "results/blackbox_1112/gpuplan/r10/table3_r10_set_A.json"

    def wrong(lv):
        return frac(T[lv]["wrong_none_credited"])[0] + frac(T[lv]["wrong_cues_credited"])[0]

    def right(lv):
        return credited(frac(T[lv]["passes_rejected"]))[0]
    for name, a, b, paper in [("transcript, not report", "L0", "L2", ("28 -> 22 of 43", "81 -> 81 of 87")),
                              ("Sol, not Terra", "L0", "S0", ("28 -> 28 of 43", "81 -> 84 of 87")),
                              ("rubric (with log)", "L1", "F1", ("25 -> 0 of 43", "83 -> 29 of 87")),
                              ("ground-truth answer", "L0", "K0", ("28 -> 0 of 43", "81 -> 77 of 87"))]:
        check(f"Table 3 {name}: wrong answers credited", paper[0], f"{wrong(a)} -> {wrong(b)} of 43", src)
        check(f"Table 3 {name}: correct answers credited", paper[1], f"{right(a)} -> {right(b)} of 87", src)
    c7 = load(OUT / "c7" / "c7.json")["cells"]
    check("Table 3 sceptical paragraph: wrong nulls credited", "86 -> 4 of 148",
          f"{c7['TF']['none_FPR'].split('/')[0]} -> {c7['TK']['none_FPR'].replace('/', ' of ')}", "results/blackbox_1112/gpuplan/r10/out/gpuplan/c7/c7.json")
    check("Table 3 sceptical paragraph: correct nulls credited", "238 -> 9 of 263",
          f"{c7['TF']['none_TPR'].split('/')[0]} -> {c7['TK']['none_TPR'].replace('/', ' of ')}", "same")
    check("Table 3 sceptical paragraph: within-rollout AUROC", "0.59 -> 0.50",
          f"{c7['TF']['within_run_none_auroc']:.2f} -> {c7['TK']['within_run_none_auroc']:.2f}", "same")
    r8 = load(OUT / "r8" / "r8_12.json")["check1_threshold_calibration"]["L2"]["all_none_slots"]["leave_one_item_out"]
    m = re.search(r"^\| Terra, transcript \(r10\) \| (\d+)/52 / (\d+)/136 /", (R10 / "ROUND10_DIFF.md").read_text(), re.M)
    dw, dr = m.groups()
    check("Table 3 confidence threshold: wrong nulls credited", "27 -> 8 of 52", f"{dw} -> {r8['wrong_none_passed'].replace('/', ' of ')}",
          "results/blackbox_1112/gpuplan/r10/out/gpuplan/r8/r8_12.json and ROUND10_DIFF.md (default prompt)")
    check("Table 3 confidence threshold: correct nulls credited", "135 -> 124 of 136", f"{dr} -> {r8['right_none_passed'].replace('/', ' of ')}", "same")


# ---------------------------------------------------------------- Table 6: null coverage by budget
def table6():
    x = load(OUT / "x7" / "x7.json")["X4_coverage_by_budget"]
    by_b = {8: ["set_A | bb8", "set_A | open8", "luna | bb8", "luna | open8", "main_study | b1", "main_study | b2"],
            16: ["set_A | bb16"], 64: ["set_A | bb64"]}
    paper = {8: ("317", "0", "0/187", "0/130"), 16: ("27", "0", "0/22", "0/5"), 64: ("41", "22", "20/34", "2/7")}
    src = "results/blackbox_1112/gpuplan/r10/out/gpuplan/x7/x7.json (X4_coverage_by_budget)"
    for b, keys in by_b.items():
        tot = [0] * 6
        for k in keys:
            g = x[k.split(" | ")[0]][k.split(" | ")[1]] if " | " in k and k.split(" | ")[0] in x else x[k]
            for i, f in enumerate(("every_candidate_isolated", "every_candidate_isolated_right", "every_candidate_isolated_wrong")):
                a, n = frac(g[f])
                tot[2 * i] += a
                tot[2 * i + 1] += n
        check(f"Table 6 B = {b}: none answers", paper[b][0], tot[1], src)
        check(f"Table 6 B = {b}: every candidate tested alone", paper[b][1], tot[0], src)
        check(f"Table 6 B = {b}: correct nulls fully tested", paper[b][2], f"{tot[2]}/{tot[3]}", src)
        check(f"Table 6 B = {b}: incorrect nulls fully tested", paper[b][3], f"{tot[4]}/{tot[5]}", src)


# ---------------------------------------------------------------- Table 7: original vs corrected judge prompt
def table7():
    F, T = table3("frozen"), table3("r10")
    src = "results/blackbox_1112/gpuplan/r10/table3_{frozen,r10}_*.json"
    rows = {"L0": ("60 -> 50", "23 -> 23", "108 -> 130"), "L2": ("35 -> 39", "12 -> 16", "108 -> 128"),
            "S2": ("36 -> 42", "16 -> 22", "130 -> 134"), "L3_2": ("0 -> 0", "1 -> 1", "139 -> 139")}
    for lv, (inc, wrong, corr) in rows.items():
        g = lambda X, k: pooled(X, lv, k)[0]  # noqa: E731
        check(f"Table 7 {lv}: incorrect nulls credited", inc, f"{g(F, 'wrong_none_credited')} -> {g(T, 'wrong_none_credited')}", src)
        check(f"Table 7 {lv}: wrong shortcuts credited", wrong, f"{g(F, 'wrong_cues_credited')} -> {g(T, 'wrong_cues_credited')}", src)
        cf, ct = credited(pooled(F, lv, "passes_rejected")), credited(pooled(T, lv, "passes_rejected"))
        check(f"Table 7 {lv}: correct answers credited", corr, f"{cf[0]} -> {ct[0]}", src)


# ---------------------------------------------------------------- Figure 1a and section 5 shares
def figure1():
    T = table3("r10")
    ad1 = load(R10 / "addendum" / "ad1_r10.json")["credit_by_level"]
    src = "results/blackbox_1112/gpuplan/r10/addendum/ad1_r10.json (supported + unsupported)"
    for lv, (right, wrong) in {"L0": ("218/243", "81/142"), "L2": ("217/243", "59/142")}.items():
        c = ad1[lv]
        r = [frac(c["supported right"]), frac(c["unsupported right"])]
        w = [frac(c["supported wrong"]), frac(c["unsupported wrong"])]
        check(f"Section 5 / Fig. 1a {lv}: correct nulls credited (any probe)", right,
              f"{sum(a for a, _ in r)}/{sum(b for _, b in r)}", src)
        check(f"Section 5 / Fig. 1a {lv}: incorrect nulls credited (any probe)", wrong,
              f"{sum(a for a, _ in w)}/{sum(b for _, b in w)}", src)
    for lv, paper in {"L0": "130/139", "L2": "128/139", "L3_2": "139/139"}.items():
        check(f"Fig. 1a {lv}: correct named answers credited", paper, fs(credited(pooled(T, lv, "passes_rejected"))),
              "results/blackbox_1112/gpuplan/r10/table3_r10_*.json")
    check("Fig. 1b: candidates tested alone behind the 77 incorrect nulls", "35, 19, 19, 0, 0, 1, 0, 2, 1", None,
          "needs per-answer data (docs/DATA.md)")


# ---------------------------------------------------------------- Sections 5 and 7: repeatability, gaps, ranking
def section7():
    a = load(OUT / "a" / "intervals.json")["judge_noise"]
    check("Section 5: test-retest kappa (report, re-send)", "0.89", f"{a['L0_vs_L0r_hard_kappa']:.2f}",
          "results/blackbox_1112/gpuplan/r10/out/gpuplan/a/intervals.json")
    g = load(OUT / "c8" / "c8.json")["gap_open8"]
    for kind, paper_c, paper_j, ci in [("trap", "+0.86", "+0.03", "[-0.17, 0.22]"), ("two-part", "+0.78", "+0.06", "[0.00, 0.17]")]:
        x = g[kind]
        check(f"Section 7 {kind} gap, ground truth", paper_c, f"{x['delta_certified']:+.2f}", "results/blackbox_1112/gpuplan/r10/out/gpuplan/c8/c8.json")
        check(f"Section 7 {kind} gap, judge given the report", f"{paper_j} {ci}",
              f"{x['delta_judge']:+.2f} [{x['delta_judge_boot95'][0]:.2f}, {x['delta_judge_boot95'][1]:.2f}]", "same")
    fv = (R10 / "fig_values.md").read_text()
    for row, paper in [("report + log (L1)", "+0.278 [0.111, 0.444]"), ("transcript (L2)", "+0.278 [-0.028, 0.556]"),
                       ("Sol, transcript (L2)", "+0.250 [0.0, 0.5]")]:
        m = re.search(r"^\| " + re.escape(row) + r" \|.*\| ([^|]*) \| [a-z]+ \|$", fv, re.M)
        got = m.group(1).split(", ", 1)[1].strip() if m else None
        got = None if got is None else re.sub(r"\+0\.25 ", "+0.250 ", got)
        check(f"Section 7 decoy gap, {row}", paper, got, "results/blackbox_1112/gpuplan/r10/fig_values.md")
    c19 = load(OUT / "c19_reorder.json")["L9"]
    check("Section 7: Kendall tau_b, judge vs ground-truth ranking", "0.29 [0.00, 0.55]",
          f"{c19['tau_b']:.2f} [{c19['tau_b_run_boot_95'][0]:.2f}, {c19['tau_b_run_boot_95'][1]:.2f}]",
          "results/blackbox_1112/gpuplan/r10/out/gpuplan/c19_reorder.json")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    for f in (table1, table2_and_8, table3_interventions, table6, table7, figure1, section7):
        f()
    norm = lambda s: re.sub(r"\s+", " ", s.replace("−", "-")).strip()  # noqa: E731
    bad = pending = 0
    lines = ["| where | paper | recomputed | ok | source |", "|---|---|---|---|---|"]
    for where, paper, value, src in CHECKS:
        if value is None:
            ok = "needs data"
            pending += 1
        else:
            ok = "yes" if norm(paper) == norm(value) else "NO"
            bad += ok == "NO"
        print(f"{ok:>10}  {where:<70} paper {paper:<26} here {value}")
        lines.append(f"| {where} | {paper} | {value if value is not None else '-'} | {ok} | {src} |")
    print(f"\n{len(CHECKS) - bad - pending} of {len(CHECKS)} numbers match; {bad} differ; {pending} need per-answer data")
    if a.md:
        a.md.write_text("\n".join(lines) + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
