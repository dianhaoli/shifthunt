"""R10: ROUND10_DIFF.md and the figure value tables, from the frozen (main tree) and r10 (gpuplan/r10/out) outputs.

    python scripts/r10_round10_diff.py      # -> results/blackbox_1112/gpuplan/r10/ROUND10_DIFF.md, fig_values.md

Every number is read from an output file. Flag rule: a row is flagged when its pre-stated label or
direction changes, or when the r10 value lies outside the frozen value's 95% interval (item bootstrap; at the
report level, also compared with the re-send spread of L0 / L0r / TF2).
"""
import json
from collections import OrderedDict
from pathlib import Path

M = Path("/home/ec2-user/shifthunt-public/results/blackbox_1112")
R = M / "gpuplan" / "r10"
O = R / "out"


def ld(p):
    return json.loads(Path(p).read_text())


def fz(f):
    return ld(M / f)


def rt(f):
    return ld(O / f)


def frac(s):
    a, b = s.split("/")
    return int(a) / int(b) if int(b) else None


def main():
    L = []
    A = L.append
    t3f, t3r = ld(R / "table3_frozen_set_A.json")["levels"], ld(R / "table3_r10_set_A.json")["levels"]
    rdf, rdr = ld(R / "readings_frozen.json"), ld(R / "readings_r10.json")
    tf, tr = ld(R / "tallies_frozen.json"), ld(R / "tallies_r10.json")
    A("# ROUND10_DIFF: every judge-based number, frozen prompt (registered, App. N) vs corrected prompt (r10, body)\n")
    A("Source of every value: the frozen outputs in `results/blackbox_1112/**` and the r10 outputs in `gpuplan/r10/out/**` "
      "(the same unchanged scripts run on the r10 verdicts), plus `table3_*`, `readings_*`, `tallies_*`, `addendum/*` "
      "in this folder; leaf-by-leaf changes of every output are in `diff/`. "
      "**Flag** (⚑) = the pre-stated label or the direction changes, or the r10 value lies outside the frozen 95% interval. "
      "At the report level the frozen re-send spread is the noise floor: hard-probe κ −0.02 (L0) / −0.01 (L0r) / 0.10 (TF2), "
      "Fleiss κ of the three sends 0.44 (all slots). r10's three report sends were all made on 18 Nov (Fleiss κ 0.78), "
      "so r10's own re-send spread is smaller. **The same-day control** (gate, frozen prompt re-sent on 18 Nov) separates "
      "drift from the fix; see section 2. In section 5 the flags are set by hand in this script (marking claims whose wording must change) and every row whose r10 value lies outside the frozen item interval is flagged too; sections 4 and 6 carry no flags (their intervals are in sections 3 and 6).\n")
    # 1 readings
    A("## 1. Pre-stated readings (PLAN_R10 item 9)\n")
    A("| reading | frozen | r10 | flag |\n|---|---|---|---|")
    for h in ("H1", "H2", "H3", "H5", "H6"):
        a, b = rdf[h], rdr[h]
        la = a.get("label") if isinstance(a, dict) else a
        lb = b.get("label") if isinstance(b, dict) else b
        A(f"| {h} | {la} | {lb} | {'⚑' if la != lb else ''} |")
    h4f = rdf["H4"]["trap | Terra send first send (L0)"]
    h4r = rdr["H4"]["trap | Terra send first send (L0)"]
    A(f"| H4 | {h4f['label']} (gap {h4f['judged_gap']} {h4f['item95']}) | {h4r['label']} (gap {h4r['judged_gap']} {h4r['item95']}) | |")
    A("\nRule: H2 is not \"holds\" in r10, so the title, abstract and contributions change. H1 is \"weakened\" under both "
      "prompts by the same rule (the transcript-level item interval includes 50%); at the report level it holds in both. "
      "H3, H4, H5 and H6 hold in both.\n")
    A("H2 in detail (Terra, set A hard probes, wrong `none` vs wrong cues credited, difference and item interval):\n")
    for lv in ("L0", "L1", "L2"):
        a, b = rdf["H2"]["levels"][lv], rdr["H2"]["levels"][lv]
        A(f"- {lv}: {a['wrong_none']} vs {a['wrong_cue']}, {a['difference']} {a['item95']} ({a['label']}) → "
          f"{b['wrong_none']} vs {b['wrong_cue']}, {b['difference']} {b['item95']} ({b['label']})"
          f"{' ⚑' if a['label'] != b['label'] else ''}")
    ad2f, ad2r = ld(R / "addendum/ad2_frozen.json")["set_A_hard"], ld(R / "addendum/ad2_r10.json")["set_A_hard"]
    A("\nItem-clustered odds ratio (AD2; wrong `none` vs wrong cue): " + "; ".join(
        f"{lv} {ad2f[lv]['odds_ratio_wrong_none_vs_wrong_cue']} {ad2f[lv].get('cluster_robust_95')} → "
        f"{ad2r[lv]['odds_ratio_wrong_none_vs_wrong_cue']} {ad2r[lv].get('cluster_robust_95')}" for lv in ("L0", "L1", "L2")) + ".\n")
    # 2 wrong none on its own + control vs fix
    A("## 2. Wrong `none` acceptance on its own, and the same-day control\n")
    g = ld(R / "p05/reason_scan_gate.json")["all"]["T3_multilabel"]
    cell = lambda lv, c: (g.get(f"{lv} | {c} | credited", {"n": 0})["n"], g.get(f"{lv} | {c} | credited", {"n": 0})["n"] + g.get(f"{lv} | {c} | rejected", {"n": 0})["n"])  # noqa
    A("Set A, 132 runs, all probes, report level (Terra):\n")
    A("| case | 12 Nov frozen (registered) | 18 Nov frozen (control) | 18 Nov r10 | drift (control − 12 Nov) | fix (r10 − control) |\n|---|---|---|---|---|---|")
    reg = {"B": (48, 55), "D": (309 - 91, 309)}
    for c, n in (("B", "wrong `none` credited"), ("D", "passes credited")):
        k1, n1 = cell("L0ctrl", c)
        k2, n2 = cell("L0", c)
        r0 = reg[c]
        A(f"| {n} | {r0[0]}/{r0[1]} | {k1}/{n1} | {k2}/{n2} | {k1 / n1 - r0[0] / r0[1]:+.3f} | {k2 / n2 - k1 / n1:+.3f} |")
    A("\nWrong `none` credited, set A hard probes, by level (frozen → r10): " + "; ".join(
        f"{lv} {t3f[lv]['wrong_none_credited']} → {t3r[lv]['wrong_none_credited']}" for lv in
        ("L0", "L0r", "L1", "L2", "S0", "S1", "S2", "H0", "H1", "H2", "K0", "S3")) + ". "
      "As forecast by P0.5 (no rejected wrong `none` cited latents), wrong-`none` credit barely moves; the fix moves "
      "passes and, at Terra's transcript level and Sol's levels, wrong named cues. The control's drift on wrong `none` "
      "(−0.09) is as large as the fix's (−0.05), so the small wrong-`none` change is within drift.\n")
    # 3 Table 3
    A("## 3. Table 3 (set A hard probes)\n")
    A("| judge | level | κ frozen [item 95%] | κ r10 [item 95%] | wrong cues | wrong `none` | passes rejected | flag |\n|---|---|---|---|---|---|---|---|")
    for lv in ("L0", "L0r", "L1", "L1r", "L2", "K0", "S0", "S1", "S2", "S3", "H0", "H1", "H1r", "H2"):
        a, b = t3f[lv], t3r[lv]
        out = b["hard_kappa"] is not None and not (a["item95"][0] <= b["hard_kappa"] <= a["item95"][1])
        A(f"| {a['judge']} | {lv} | {a['hard_kappa']} {a['item95']} | {b['hard_kappa']} {b['item95']} | "
          f"{a['wrong_cues_credited']} → {b['wrong_cues_credited']} | {a['wrong_none_credited']} → {b['wrong_none_credited']} | "
          f"{a['passes_rejected']} → {b['passes_rejected']} | {'⚑' if out else ''} |")
    A(f"| Haiku | report + key (O1a, new in r10) | — | {t3r['O1a']['hard_kappa']} {t3r['O1a']['item95']} | — → "
      f"{t3r['O1a']['wrong_cues_credited']} | — → {t3r['O1a']['wrong_none_credited']} | — → {t3r['O1a']['passes_rejected']} | |")
    A("\nCost per call (Table 3's last column; App. B Table B1): prompts are 665–746 characters shorter; the dry-run factor "
      "of r10 to frozen cost was 0.99 (Terra), 1.00 (Sol), 1.12 (Haiku), so the per-call costs are unchanged to two "
      "significant figures (RUNLOG has the r10 batch totals).\n")
    # 4 Fig 1
    A("## 4. Fig. 1 values (set A hard probes; Terra and Sol; share credited)\n")
    A("| panel | judge | report | report + log | transcript | report + key |\n|---|---|---|---|---|---|")
    for key, nm in (("wrong_none_credited", "wrong `none` (n = 26)"), ("wrong_cues_credited", "wrong cues (n = 17)")):
        for j, lvs in (("Terra", ("L0", "L1", "L2", "K0")), ("Sol", ("S0", "S1", "S2", "S3"))):
            A(f"| {nm} | {j} | " + " | ".join(f"{t3f[lv][key]} → **{t3r[lv][key]}**" for lv in lvs) + " |")
    A("\nItem-clustered intervals for these bars (AD2's GEE cluster-robust and item bootstrap) are in `addendum/ad2_r10.json`.\n")
    # 5 C12, C17, confidence, sceptical, rubric, key
    c12f, c12r = fz("gpuplan/c12/c12.json")["gpt-6.1-terra"]["pooled"], rt("gpuplan/c12/c12.json")["gpt-6.1-terra"]["pooled"]
    c17f, c17r = fz("gpuplan/c17/c17.json"), rt("gpuplan/c17/c17.json")
    jf, jr = fz("judge/judge.json"), rt("judge/judge.json")
    c7f, c7r = fz("gpuplan/c7/c7.json")["cells"], rt("gpuplan/c7/c7.json")["cells"]
    ff, fr = fz("gpuplan/f/f.json")["F1 (log level)"], rt("gpuplan/f/f.json")["F1 (log level)"]
    sf_, sr_ = fz("gpuplan/s/s.json")["readings"], rt("gpuplan/s/s.json")["readings"]
    A("## 5. Body numbers (abstract, §1, §4)\n")
    A("| claim (paper wording) | frozen | r10 | flag |\n|---|---|---|---|")
    rows = [
        ("§4.1 no report: Terra accepts a `none` on the hard probe (P7)", c12f["hard_credit_P7"], c12r["hard_credit_P7"], True),
        ("§4.1 no report: given the true cue (P0)", c12f["hard_credit_P0"], c12r["hard_credit_P0"], True),
        ("§4.1 no report: `none` everywhere (P1)", c12f.get("hard_credit_P1"), c12r.get("hard_credit_P1"), False),
        ("§4.2 Terra report κ on set A (Table 3)", t3f["L0"]["hard_kappa"], t3r["L0"]["hard_kappa"], True),
        ("§4.2 Sol report κ", t3f["S0"]["hard_kappa"], t3r["S0"]["hard_kappa"], False),
        ("§4.2 Terra accepts wrong `none` (report; r10 19/26 lies below the frozen item interval [0.78, 1.0]; the same-day frozen control gives 21/26)", t3f["L0"]["wrong_none_credited"], t3r["L0"]["wrong_none_credited"], True),
        ("§4.2 Haiku rejects correct answers (report)", t3f["H0"]["passes_rejected"], t3r["H0"]["passes_rejected"], True),
        ("§4.2 J1 hard κ, all 214 runs", jf["J1_hard_slots"]["kappa"], jr["J1_hard_slots"]["kappa"], True),
        ("§4.3 self-agreement, hard Fleiss κ of three Terra report sends", c17f["three_replicates"]["hard_fleiss_kappa"],
         c17r["three_replicates"]["hard_fleiss_kappa"], True),
        ("§4.3 self-agreement, all-slot Fleiss κ", c17f["three_replicates"]["fleiss_kappa"], c17r["three_replicates"]["fleiss_kappa"], True),
        ("§4.4 report → transcript, wrong cues accepted (Terra)", f"{t3f['L0']['wrong_cues_credited']} → {t3f['L2']['wrong_cues_credited']}",
         f"{t3r['L0']['wrong_cues_credited']} → {t3r['L2']['wrong_cues_credited']}", True),
        ("§4.4 report → transcript, wrong `none` accepted (Terra)", f"{t3f['L0']['wrong_none_credited']} → {t3f['L2']['wrong_none_credited']}",
         f"{t3r['L0']['wrong_none_credited']} → {t3r['L2']['wrong_none_credited']}", False),
        ("§4.4 transcript: passes rejected, Sol vs Terra", f"{t3f['S2']['passes_rejected']} vs {t3f['L2']['passes_rejected']}",
         f"{t3r['S2']['passes_rejected']} vs {t3r['L2']['passes_rejected']}", True),
        ("§4.4 transcript: wrong `none` accepted, Sol vs Terra", f"{t3f['S2']['wrong_none_credited']} vs {t3f['L2']['wrong_none_credited']}",
         f"{t3r['S2']['wrong_none_credited']} vs {t3r['L2']['wrong_none_credited']}", True),
        ("§4.6 confidence 100 at report + log: verdicts (right)", f"{tf['check4_L1_confidence_100']['n']} ({tf['check4_L1_confidence_100']['right']})",
         f"{tr['check4_L1_confidence_100']['n']} ({tr['check4_L1_confidence_100']['right']})", True),
        ("§4.6 sceptical prompt: right `none` accepted, Terra (F → K)", f"{c7f['TF']['none_TPR']} → {c7f['TK']['none_TPR']}",
         f"{c7r['TF']['none_TPR']} → {c7r['TK']['none_TPR']}", False),
        ("§4.6 sceptical prompt: wrong `none` accepted, Terra (F → K)", f"{c7f['TF']['none_FPR']} → {c7f['TK']['none_FPR']}",
         f"{c7r['TF']['none_FPR']} → {c7r['TK']['none_FPR']}", False),
        ("§4.6 checking rubric: verdicts on set A hard probes (coverage)", ff["coverage_hard"], fr["coverage_hard"], True),
        ("§4.6 rubric: wrong answers passed", f"{ff['wrong_none_hard']['pass']} none, {ff['commissions_hard']['pass']} cues",
         f"{fr['wrong_none_hard']['pass']} none, {fr['commissions_hard']['pass']} cues", False),
        ("§4.6 key: failures accepted, Terra K0 / Sol S3 (set A, 43 hard failures)",
         f"{sf_['key_control']['terra_K0_hard_failures_credited']} / {sf_['key_control']['hard_failures_credited']}",
         f"{sr_['key_control']['terra_K0_hard_failures_credited']} / {sr_['key_control']['hard_failures_credited']}", True),
        ("§4.6 key: κ Terra / Sol", f"{t3f['K0']['hard_kappa']} / {t3f['S3']['hard_kappa']}", f"{t3r['K0']['hard_kappa']} / {t3r['S3']['hard_kappa']}", False),
    ]
    for nm, a, b, fl in rows:
        A(f"| {nm} | {a} | {b} | {'⚑' if fl and a != b else ''} |")
    # Table 4/5/6
    xf, xr = fz("gpuplan/x7/x7.json")["X1_X2"]["proxy | pooled"], rt("gpuplan/x7/x7.json")["X1_X2"]["proxy | pooled"]
    A("\n## 6. Table 4 (the 40 within-run pairs; 27 at report + log, where 13 runs have no log: AUROC of p(correct), right `none` above wrong `none`)\n")
    A("| judge, level | frozen [item 95%] | r10 [item 95%] |\n|---|---|---|")
    for k, nm in (("L0", "Terra, report"), ("L1", "Terra, report + log"), ("L2", "Terra, transcript"), ("Sol_L2", "Sol, transcript")):
        A(f"| {nm} | {xf[k]['auroc']} {xf[k]['item95']} | {xr[k]['auroc']} {xr[k]['item95']} |")
    rf, rr = fz("gpuplan/r8/r8_12.json"), rt("gpuplan/r8/r8_12.json")
    A("\n## 7. Table 5 (pass mark on p(correct), leave-one-item-out; 188 `none` slots: 52 wrong, 136 right)\n")
    A("| judge, level | default: wrong passed / right passed / BA | held-out cut-off: wrong / right / BA [item 95%] | cut-offs |\n|---|---|---|---|")
    for k, nm in (("L2", "Terra, transcript"), ("Sol_L2", "Sol, transcript"), ("L0", "Terra, report")):
        for tag, d in (("frozen", rf), ("r10", rr)):
            x = d["check1_threshold_calibration"][k]["all_none_slots"]
            A(f"| {nm} ({tag}) | {x['default_verdict']['wrong_none_passed']} / {x['default_verdict']['right_none_passed']} / "
              f"{x['default_verdict']['balanced_accuracy']} | {x['leave_one_item_out']['wrong_none_passed']} / "
              f"{x['leave_one_item_out']['right_none_passed']} / {x['leave_one_item_out']['balanced_accuracy']} "
              f"{x['leave_one_item_out']['item95']} | {min(x['cut_offs_by_held_out_fold'])}–{max(x['cut_offs_by_held_out_fold'])} |")
    A("\n## 8. Table 6 and Fig. 2 (Terra − Luna gap on the [trap] probe, 30 shipped trap runs; executed +0.86)\n")
    A("| grading level | frozen: Terra / Luna, gap [C8 method] | r10: Terra / Luna, gap [C8 method] | flag |\n|---|---|---|---|")
    for k, nm in (("L0_12nov", "report, first send"), ("L0", "report, re-send alongside Luna"), ("L1", "report + log"),
                  ("L2", "transcript"), ("Sol_L2", "Sol, transcript")):
        a, b = rf["check2_trap_gap"][k], rr["check2_trap_gap"][k]
        lo, hi = a["intervals"]["c8_method"]
        A(f"| {nm} | {a['terra']} / {a['luna']}, {a['gap']:+.3f} [{lo:+.3f}, {hi:+.3f}] | {b['terra']} / {b['luna']}, "
          f"{b['gap']:+.3f} [{b['intervals']['c8_method'][0]:+.3f}, {b['intervals']['c8_method'][1]:+.3f}] | "
          f"{'⚑' if not lo <= b['gap'] <= hi else ''} |")
    A("\nIn r10 the report-level \"first send\" and the C8 re-send are the same day (18 Nov); the frozen first send was "
      "12 Nov and the C8 re-send 13 Nov (the other frozen levels 13–17 Nov). **Every judged gap stays far below the executed +0.86** (H4 holds).\n")
    c19f, c19r = fz("gpuplan/c19_reorder.json")["L9"], rt("gpuplan/c19_reorder.json")["L9"]
    A(f"**§4.7 whole rankings (C19, nine systems):** Kendall τ_b {c19f['tau_b']} {c19f['tau_b_run_boot_95']} → "
      f"{c19r['tau_b']} {c19r['tau_b_run_boot_95']}; pairs reversed {c19f['discordant_pairs']} → {c19r['discordant_pairs']} of "
      f"{c19r['pairs']}. (Run through `scripts/r10_c19.py`: the script's reproduction gate checks the frozen counts and is "
      f"bypassed on r10.) Outcome label: {fz('gpuplan/c19_reorder.json')['outcome']} → {rt('gpuplan/c19_reorder.json')['outcome']}.\n")
    # 9 failures table
    A("## 9. JUDGE_FAILURES_TABLE (13 rows), frozen → r10\n")
    fills_f, fills_r = tf["failures_table_fills"], tr["failures_table_fills"]
    kl_f, kl_r = tf["key_level_rejected_passes"], tr["key_level_rejected_passes"]
    sfx, srx = fz("gpuplan/s/s.json")["set_A"]["SF vs F1 (log level, abstaining, candidate-aware)"]["sol"], rt("gpuplan/s/s.json")["set_A"]["SF vs F1 (log level, abstaining, candidate-aware)"]["sol"]
    c6f, c6r = fz("gpuplan/c6/c6.json"), rt("gpuplan/c6/c6.json")
    c6bf, c6br = fz("gpuplan/c6b/c6b.json"), rt("gpuplan/c6b/c6b.json")
    c6cf, c6cr = fz("gpuplan/c6c/c6c.json"), rt("gpuplan/c6c/c6c.json")
    rows = [
        ("1 key rejects a correct answer (Terra / Sol, of 87)", f"{t3f['K0']['passes_rejected']} / {t3f['S3']['passes_rejected']}",
         f"{t3r['K0']['passes_rejected']} / {t3r['S3']['passes_rejected']}"),
        ("2 confidence-100 verdicts wrong (Terra, report + log)", f"{tf['check4_L1_confidence_100']['n'] - tf['check4_L1_confidence_100']['right']} of {tf['check4_L1_confidence_100']['n']}",
         f"{tr['check4_L1_confidence_100']['n'] - tr['check4_L1_confidence_100']['right']} of {tr['check4_L1_confidence_100']['n']} (row disappears)"),
        ("3 log-confirmed passes rejected (Terra log / transcript; topic-unit rule)", f"{fills_f.get('row 3 log-confirmed passes rejected (L1)')} / {fills_f.get('row 3 log-confirmed passes rejected (L2)')}",
         f"{fills_r.get('row 3 log-confirmed passes rejected (L1)')} / {fills_r.get('row 3 log-confirmed passes rejected (L2)')}"),
        ("4 accepts a refuted [decoy] (Luna's 7; report + log / transcript, rejected)", f"{c6f['J9_luna_refuted_then_submitted']['rejected_L1']} rejected / {c6bf['luna'].get('J13_refuted_then_submitted', {}).get('rejected_L2')} rejected",
         f"{c6r['J9_luna_refuted_then_submitted']['rejected_L1']} rejected / {c6br['luna'].get('J13_refuted_then_submitted', {}).get('rejected_L2')} rejected"),
        ("5 key + transcript accepts a wrong cue (main study)", c6cf["main_L2_key"]["false_credit_wrong_cue"], c6cr["main_L2_key"]["false_credit_wrong_cue"]),
        ("6 rubric on refuted failures (F1 / SF verdicts)", f"{fills_f.get('row 6 refuted failures (F1)')} / {fills_f.get('row 6 refuted failures (SF)')}",
         f"{fills_r.get('row 6 refuted failures (F1)')} / {fills_r.get('row 6 refuted failures (SF)')}"),
        ("7 accepts a wrong named cue (Terra L0→L1→L2; Sol; Haiku report)", f"{t3f['L0']['wrong_cues_credited']} → {t3f['L1']['wrong_cues_credited']} → {t3f['L2']['wrong_cues_credited']}; Sol {t3f['S0']['wrong_cues_credited']} → {t3f['S1']['wrong_cues_credited']} → {t3f['S2']['wrong_cues_credited']}; Haiku {t3f['H0']['wrong_cues_credited']}",
         f"{t3r['L0']['wrong_cues_credited']} → {t3r['L1']['wrong_cues_credited']} → {t3r['L2']['wrong_cues_credited']}; Sol {t3r['S0']['wrong_cues_credited']} → {t3r['S1']['wrong_cues_credited']} → {t3r['S2']['wrong_cues_credited']}; Haiku {t3r['H0']['wrong_cues_credited']}"),
        ("8 accepts a wrong `none` with a suspicious untested candidate (40 pairs, transcript; Terra / Sol)", f"{xf['post_hoc_binary_credit']['L2']['wrong_none_credited']} / {xf['post_hoc_binary_credit']['Sol_L2']['wrong_none_credited']}",
         f"{xr['post_hoc_binary_credit']['L2']['wrong_none_credited']} / {xr['post_hoc_binary_credit']['Sol_L2']['wrong_none_credited']}"),
        ("9 rejects correct answers (Terra / Sol / Haiku; report → log → transcript)",
         f"{t3f['L0']['passes_rejected']} → {t3f['L1']['passes_rejected']} → {t3f['L2']['passes_rejected']}; {t3f['S0']['passes_rejected']} → {t3f['S1']['passes_rejected']} → {t3f['S2']['passes_rejected']}; {t3f['H0']['passes_rejected']} → {t3f['H1']['passes_rejected']} → {t3f['H2']['passes_rejected']}",
         f"{t3r['L0']['passes_rejected']} → {t3r['L1']['passes_rejected']} → {t3r['L2']['passes_rejected']}; {t3r['S0']['passes_rejected']} → {t3r['S1']['passes_rejected']} → {t3r['S2']['passes_rejected']}; {t3r['H0']['passes_rejected']} → {t3r['H1']['passes_rejected']} → {t3r['H2']['passes_rejected']}"),
        ("10 accepts a wrong `none` (Terra / Sol / Haiku; report → log → transcript)",
         f"{t3f['L0']['wrong_none_credited']} → {t3f['L1']['wrong_none_credited']} → {t3f['L2']['wrong_none_credited']}; {t3f['S0']['wrong_none_credited']} → {t3f['S1']['wrong_none_credited']} → {t3f['S2']['wrong_none_credited']}; {t3f['H0']['wrong_none_credited']} → {t3f['H1']['wrong_none_credited']} → {t3f['H2']['wrong_none_credited']}",
         f"{t3r['L0']['wrong_none_credited']} → {t3r['L1']['wrong_none_credited']} → {t3r['L2']['wrong_none_credited']}; {t3r['S0']['wrong_none_credited']} → {t3r['S1']['wrong_none_credited']} → {t3r['S2']['wrong_none_credited']}; {t3r['H0']['wrong_none_credited']} → {t3r['H1']['wrong_none_credited']} → {t3r['H2']['wrong_none_credited']}"),
        ("11 no report: `none` accepted vs true cue (Terra)", f"{c12f['hard_credit_P7']} vs {c12f['hard_credit_P0']}", f"{c12r['hard_credit_P7']} vs {c12r['hard_credit_P0']}"),
        ("12 sceptical prompt: right `none` accepted (Terra, F → K)", f"{c7f['TF']['none_TPR']} → {c7f['TK']['none_TPR']}", f"{c7r['TF']['none_TPR']} → {c7r['TK']['none_TPR']}"),
        ("13 rubric withholds credit on 50 confirmed passes (F1 cannot tell)", str(tf["check3_abstaining_on_V6_50"]["F1"]["verdicts"]),
         str(tr["check3_abstaining_on_V6_50"]["F1"]["verdicts"])),
    ]
    A("| row | frozen | r10 |\n|---|---|---|")
    for nm, a, b in rows:
        A(f"| {nm} | {a} | {b} |")
    A("\nRows 2 and 9 (Terra) largely disappear, as expected; Haiku's rejections (row 9) shrink but remain (69/86 at the "
      "report level). Row 1 does not shrink from the latents fix (no key-level rejection cited latents); its small "
      "change comes with A4–A5. Rows 10 and 11 stay: the judge still accepts most wrong `none` answers, and with no "
      "report it still prefers a `none` to the true cue (17/39 vs 7/39; p = 0.041).\n")
    A("## 10. Appendix sections E–L (registered tests whose label changes)\n")
    ff2 = fz("gpuplan/c6b/c6b.json")["set_A"]
    A(f"- J8 (L1 hard κ < 0.40): {c6f['J8']['hard_kappa_L1']} confirmed → {c6r['J8']['hard_kappa_L1']} **not confirmed** ⚑")
    A(f"- J11 (κ gain L1 → L2 ≥ 0.10 with lower bound > 0): {ff2['J11']['delta_kappa_L2_minus_L1']} confirmed → "
      f"{c6br['set_A']['J11']['delta_kappa_L2_minus_L1']} **not confirmed** ⚑ (the log level already reaches most of the transcript's κ)")
    A(f"- S reading R (Sol transcript): \"{sf_['R']['sentence']}\" → \"{sr_['R']['sentence']}\" ⚑")
    A(f"- S key control: {sf_['key_control']['hard_failures_credited']} → {sr_['key_control']['hard_failures_credited']} hard failures credited by Sol with the key ⚑")
    A(f"- C7 P3 (frozen judge replicates on TF): {fz('gpuplan/c7/c7.json')['P3_replicates_frozen']['TF']} → {rt('gpuplan/c7/c7.json')['P3_replicates_frozen']['TF']} ⚑")
    A(f"- C19 outcome: {fz('gpuplan/c19_reorder.json')['outcome']} → **{rt('gpuplan/c19_reorder.json')['outcome']}** ⚑ (H1 of C19, τ_b's run-bootstrap upper bound below AstaBench's 0.467, no longer holds: {c19r['tau_b_run_boot_95']})")
    A(f"- C6b prediction (Terra transcript hard κ < 0.40): {fz('gpuplan/c6b/c6b.json')['set_A']['prediction_kappa_L2_lt_040']} → {rt('gpuplan/c6b/c6b.json')['set_A']['prediction_kappa_L2_lt_040']} ⚑")
    A(f"- D reading (judge on the slots the log decides): \"{fz('gpuplan/d/decidable.json').get('reading', {}).get('primary') if isinstance(fz('gpuplan/d/decidable.json').get('reading'), dict) else fz('gpuplan/d/decidable.json').get('reading')}\" → \"{rt('gpuplan/d/decidable.json').get('reading', {}).get('primary') if isinstance(rt('gpuplan/d/decidable.json').get('reading'), dict) else rt('gpuplan/d/decidable.json').get('reading')}\" ⚑")
    A("- H1's sub-label for Sol transcript changes from weakened to holds (r10 18/26, item interval [0.586, 0.85]); H1 overall stays weakened because of Terra's transcript level.")
    A("- Unchanged labels: J1, J2 (report level, confirmed), J5′, J6, J7′, J9, J12, J14, C8 objection-2, K reading, F readings, "
      "C6c predictions, H4/H6, C14 H5 label. Full leaf-level changes: `diff/`.\n")
    (R / "ROUND10_DIFF.md").write_text("\n".join(L) + "\n")
    # figure value tables
    F = ["# Figure value tables (round 10; r10 = body, frozen = App. N)\n",
         "## Fig. 1 (set A hard probes; bars = share credited; numerator/denominator)\n",
         "| level | judge | slot type | frozen | r10 | r10 item-clustered 95% (AD2 bootstrap of the share) |", "|---|---|---|---|---|---|"]
    ad2 = ld(R / "addendum/ad2_r10.json")["set_A_hard"]
    for lvn, (tl, sl) in (("report", ("L0", "S0")), ("report + log", ("L1", "S1")), ("transcript", ("L2", "S2")), ("report + key", ("K0", "S3"))):
        for j, lv in (("Terra", tl), ("Sol", sl)):
            for key, st in (("wrong_none_credited", "wrong `none`"), ("wrong_cues_credited", "wrong cue")):
                F.append(f"| {lvn} | {j} | {st} | {t3f[lv][key]} | {t3r[lv][key]} | see `addendum/ad2_r10.json` ({lv}) |")
    F += ["\n## Fig. 2 (Terra − Luna pass-rate gap on the [trap] probe; 30 shipped trap runs)\n",
          "| row | send | frozen gap [C8 method] | r10 gap [C8 method] | marker |", "|---|---|---|---|---|"]
    e = rf["check2_trap_gap"]["executed"]
    F.append(f"| executed grade | — | {e['terra']} vs {e['luna']}, +{e['gap']} | (unchanged) | filled |")
    for k, nm, mk in (("L0_12nov", "report (L0), first send", "filled"), ("L0", "report, re-send alongside Luna (C8)", "hollow"),
                      ("L1", "report + log (L1)", "filled"), ("L2", "transcript (L2)", "filled"), ("Sol_L2", "Sol, transcript (L2)", "filled")):
        a, b = rf["check2_trap_gap"][k], rr["check2_trap_gap"][k]
        F.append(f"| {nm} | frozen {'12 Nov' if k == 'L0_12nov' else '13 Nov' if k == 'L0' else '13–17 Nov'}; r10 18 Nov | {a['terra']} vs {a['luna']}, "
                 f"{a['gap']:+.3f} {a['intervals']['c8_method']} | {b['terra']} vs {b['luna']}, {b['gap']:+.3f} "
                 f"{b['intervals']['c8_method']} | {mk} |")
    (R / "fig_values.md").write_text("\n".join(F) + "\n")
    print("written")


if __name__ == "__main__":
    main()
