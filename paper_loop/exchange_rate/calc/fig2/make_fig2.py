#!/usr/bin/env python3
"""Figure 2: "One proxy, many exchange rates."

Built exactly from existing outputs (no new simulation, no API calls):
  ../compute/c2_results.json     (noiseless_curves, misspecification, noisy_scripted, terra_logistic)
  ../compute/c3_bstar.json       (envelopes, B_star)
  ../referee/ref_minimax_dp.json (trap_only_u2..8_single_adaptive)
  ../../../final/PAPER_V4_user.md Table 2 (agent counts, hedge, repo scripted blind)
Numbers that are in none of the json files are taken from 00_ANSWER.md section 4 and are
marked "from 00_ANSWER.md" (or from the paper) in comments next to them.

Labels: [priv] privileged reference (scripted policy or exact DP / MC on the abstract episode
model); [pre-reg] confirmatory agent result; [expl] exploratory; [desc] descriptive.
Cues are never named; nothing here pairs an item id with a property.

Run:  python3 make_fig2.py   ->  fig2.png, fig2.pdf in this folder.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CALC = os.path.dirname(HERE)
C2 = json.load(open(os.path.join(CALC, "compute", "c2_results.json")))
C3 = json.load(open(os.path.join(CALC, "compute", "c3_bstar.json")))
REF = json.load(open(os.path.join(CALC, "referee", "ref_minimax_dp.json")))

# ---------------------------------------------------------------- palette (dataviz reference)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET, RED = "#e87ba4", "#008300", "#6250d6", "#e34948"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 7.3,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, p - (mid - half), (mid + half) - p  # point, lower err, upper err


def curve(d, bmin=2, bmax=64):
    xs = sorted(int(k) for k in d)
    xs = [b for b in xs if bmin <= b <= bmax]
    return np.array(xs), np.array([d[str(b)] for b in xs])


NC = C2["noiseless_curves"]
TRAP = "shipped (trap at r2)"

# ============================================================== panel (a) data
# Blind references [priv]
b_single = curve(NC["blind ideal | known counts | single"])          # .36/.71/.96/1.0 at 8/16/24/32
b_group = curve(NC["blind ideal | known counts | group"])            # .70 at 8, 1.0 at 12
b_robust = curve(C3["envelopes"]["noisy robust blind, best of both"], 4)  # .47/.77/.89/.92/.95/.99
# Best scripted blind, repo exact back-end: NOT in any json (the json has only the noisy-sim
# re-run, c2 noisy_scripted 'blind scripted (ii-c) | any mix'). Values from paper Table 2
# (PAPER_V4_user.md line 98) = 00_ANSWER.md section 4: .40 / .80 / .93 at 8 / 16 / 64.
b_script = (np.array([8, 16, 64]), np.array([0.40, 0.80, 0.93]))
# Proxy references [priv]
p_noiseless = curve(NC["proxy Bayes | " + TRAP + " | known counts | group"], 2, 12)  # .54/.75/.92/1.0
p_noisy = curve(C3["envelopes"]["noisy robust proxy Bayes shipped (best of both)"], 4)  # .87/.97/.995
p_top1 = curve(C2["noisy_scripted"]["top1 prefix | " + TRAP], 4)  # ~0.50 flat (noisy sim)
# corroboration (noiseless believer, B = 5/8/12): misspecification[...]['shipped']['success'] = 0.5
for B in (5, 8, 12):
    assert C2["misspecification"][f"believes proxy always right (r1) | single | B={B}"][TRAP]["success"] == 0.5

# Terra blind logistic [expl]: logit P = a + c * log2(B)
LG = C2["terra_logistic"]
bb = np.geomspace(4, 64, 200)
terra_log = 1 / (1 + np.exp(-(LG["a"] + LG["c_per_doubling"] * np.log2(bb))))

# Agent points, Table 2 of PAPER_V4_user.md (lines 99-100) [pre-reg]
terra_bb = [(8, 6, 24), (16, 16, 24), (64, 24, 24)]
terra_open = (8, 23, 24)
TARGET = 23 / 24  # 0.958

# Crossing ticks: c3_bstar.json B_star['shipped: Terra Open-8 23/24']
XS = C3["B_star"]["shipped: Terra Open-8 23/24"]
assert abs(XS["target"] - TARGET) < 1e-3
cross = [
    (XS["ideal group, known counts"], "11", VIOLET),
    (XS["ideal single, known counts"], "24", BLUE),
    (XS["Terra logistic"], "≈36", INK),
    (XS["noisy robust ideal (best of both)"], "≈50", AQUA),
]

# ============================================================== panel (b) data
# Trap-only success at B = 8. The c2 mixes are 50% trap + 50% two-part (nested at rank 1)
# (c2_episode.py line 56), and every policy below scores 1.0 on two-part episodes noiselessly,
# so trap-only = 2 * mix - 1 exactly.
def trap_only(mix):
    return round(2 * mix - 1, 4)


RANK_KEYS = [TRAP, "adv: fixed r3", "adv: fixed r6", "adv: uniform r2..r8"]
XPOS = np.array([0, 1, 2, 3.25])  # 2, 3, 6, then "anywhere 2-8" set apart
XLAB = ["2\n(shipped)", "3", "6\n(bank has 3)", "anywhere\nin 2-8"]

top1 = [trap_only(C2["misspecification"]["believes proxy always right (r1) | single | B=8"][k]["success"])
        for k in RANK_KEYS]                                           # 0, 0, 0, 0
top2 = [trap_only(NC[f"top-2 prefix (B=8) | {k} | noiseless"]) for k in RANK_KEYS]  # 1, 0, 0, .14
bayes = [trap_only(NC[f"proxy Bayes | {k} | known counts | single"]["8"]) for k in RANK_KEYS[:3]]  # 1,1,1
bayes_any = REF["trap_only_u2..8_single_adaptive"]["8"]            # 0.5119 (referee DP, trap-only)
blind_single8 = NC["blind ideal | known counts | single"]["8"]       # 0.36 (rank-invariant, pooled)
blind_group8 = NC["blind ideal | known counts | group"]["8"]         # 0.70 (rank-invariant, pooled)
# Hedge: not in any json (compute.md line 385: not re-simulated). Paper Table 2 line 97 (0.54 on
# the shipped trap) and App. D line 482 (0.46-0.56 with the [main] at rank 3-8); from 00_ANSWER.md.
hedge_r2 = 0.54
hedge_lo, hedge_hi = 0.46, 0.56
# Best one-batch agent vs a designer free over ranks 2-8: 8/28 = 0.29; not in any json
# (referee.md line 87; from 00_ANSWER.md).
onebatch_any = 8 / 28

# Agent points at rank 2: Table 2 trap column (PAPER_V4_user.md lines 99, 101, 102)
agents_b = [("Terra, Open-8 [pre-reg]", 11, 12, INK, "o"),
            ("Luna, Open-8 [pre-reg]", 1, 18, INK2, "D"),
            ("Haiku, Open-8 [desc]", 0, 6, MUTED, "^")]

# ============================================================== draw
fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.2, 5.4), gridspec_kw={"width_ratios": [1.35, 1]})
NOTRUN_Y = -0.085  # "not run" strip below 0 in both panels

# ---- (a)
ax.axhline(TARGET, color=MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)
ax.text(2.0, 1.045, "dashed line: Terra with proxy, B = 8: 23/24 = 0.958; ticks = where each blind curve crosses it",
        color=INK2, fontsize=7, va="center")
for x, lab, c in cross:
    ax.plot([x, x], [TARGET - 0.035, TARGET + 0.0], color=c, lw=2.0, zorder=5, solid_capstyle="butt")
    ax.text(x, TARGET - 0.045, lab, color=INK, fontsize=7, ha="center", va="top", zorder=6,
            bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"))

ax.plot(*b_single, color=BLUE, label="blind: ideal single isolations [priv]")
ax.plot(*b_group, color=VIOLET, label="blind: ideal group tests [priv]")
ax.plot(*b_robust, color=AQUA, marker="o", ms=3.5, label="blind: noise-robust ideal, sim [priv]")
ax.plot(*b_script, color=INK2, marker="s", ms=4.5, ls=(0, (1, 1.5)), lw=1.4,
        label="blind: best scripted, repo [priv]")
ax.plot(bb, terra_log, color=INK, ls=(0, (5, 2)), lw=1.2, label="Terra blind: logistic fit [expl]")
ax.plot(*p_noiseless, color=ORANGE, lw=2.4, label="proxy: calibrated Bayes, noiseless [priv]")
ax.plot(*p_noisy, color=ORANGE, ls=(0, (4, 2)), marker="o", ms=3.5, mfc="white",
        label="proxy: calibrated Bayes, fitted noise [priv]")
ax.plot(*p_top1, color=MAGENTA, ls=(0, (1, 1.2)), lw=2.2, label="proxy: top-one believer [priv]")

for B, k, n in terra_bb:
    p, lo, hi = wilson(k, n)
    ax.errorbar(B, p, yerr=[[lo], [hi]], fmt="o", color=INK, mfc="white", mew=1.6, ms=6.5,
                capsize=2.5, lw=1.1, zorder=8)
p, lo, hi = wilson(terra_open[1], terra_open[2])
ax.errorbar(terra_open[0] * 1.06, p, yerr=[[lo], [hi]], fmt="o", color=INK, ms=6.5, capsize=2.5,
            lw=1.1, zorder=9)
ax.annotate("6/24", (8, 0.25), xytext=(8.9, 0.13), fontsize=7, color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
ax.annotate("16/24", (16, 0.667), xytext=(17.5, 0.55), fontsize=7, color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))

# Open-4 agent arm: not run -> open marker in the "not run" strip
ax.axhspan(-0.13, -0.04, color="#f3f2ee", zorder=0, lw=0)
ax.plot(4, NOTRUN_Y, marker="o", ms=7, mfc="none", mec=ORANGE, mew=1.4, ls="none", zorder=7)
ax.text(4.35, NOTRUN_Y, "Open-4 agent arm: not run", fontsize=7, color=INK2, va="center")

ax.set_xscale("log", base=2)
ax.set_xlim(1.85, 70)
ax.set_xticks([2, 4, 8, 16, 32, 64])
ax.set_xticklabels(["2", "4", "8", "16", "32", "64"])
ax.set_ylim(-0.13, 1.08)
ax.set_yticks(np.arange(0, 1.01, 0.2))
ax.grid(axis="y", color=GRID, lw=0.6)
ax.set_xlabel("exact texts per episode, B (log scale)")
ax.set_ylabel("P(NAME), shipped mix")
ax.set_title("(a) Success against exact budget", loc="left")

h, l = ax.get_legend_handles_labels()
h += [Line2D([], [], marker="o", color=INK, mfc="white", mew=1.6, ls="none", ms=6),
      Line2D([], [], marker="o", color=INK, ls="none", ms=6),
      Line2D([], [], marker="o", color=ORANGE, mfc="none", ls="none", ms=6)]
l += ["Terra without proxy, 8/16/64 [pre-reg]", "Terra with proxy, 8 [pre-reg]", "not run"]
ax.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2, frameon=False,
          handlelength=2.6, columnspacing=1.2)

# ---- (b)
bx.axvline(2.625, color=GRID, lw=1.0)
bx.axhline(blind_group8, color=VIOLET, lw=1.5, label=f"blind: ideal group tests ({blind_group8:.2f}) [priv]")
bx.axhline(blind_single8, color=BLUE, lw=1.5, label=f"blind: ideal single isolations ({blind_single8:.2f}) [priv]")

bx.plot(XPOS[:3], bayes, color=ORANGE, lw=2.4, marker="o", ms=8, zorder=3, label="calibrated Bayes, adaptive [priv]")
bx.plot(XPOS[3], bayes_any, color=ORANGE, marker="o", ms=6, ls="none")
bx.plot(XPOS[:3], top2[:3], color=YELLOW, lw=1.8, marker="s", ms=4.5, zorder=4, label="top-two [priv]")
bx.plot(XPOS[3], top2[3], color=YELLOW, marker="s", ms=5.5, ls="none")
bx.plot(XPOS[:3], top1[:3], color=MAGENTA, lw=1.8, ls=(0, (1, 1.2)), marker="v", ms=5.5, label="top-one [priv]")
bx.plot(XPOS[3], top1[3], color=MAGENTA, marker="v", ms=5.5, ls="none")
# hedge: point at rank 2, range bars 0.46-0.56 at ranks 3, 6 and "anywhere"
bx.plot(XPOS[0], hedge_r2, color=GREEN, marker="P", ms=6.5, ls="none", label="hedge, repo [priv]")
for x in XPOS[1:]:
    x = x - 0.17
    bx.plot([x, x], [hedge_lo, hedge_hi], color=GREEN, lw=4.0, solid_capstyle="round", alpha=0.85)
bx.plot(XPOS[3] + 0.18, onebatch_any, color=RED, marker="X", ms=7, ls="none",
        label="best one-batch vs free designer, 8/28 [priv]")

# value labels on the "anywhere" column
bx.text(XPOS[3] + 0.12, bayes_any, "0.51", ha="left", va="center", fontsize=7, color=INK2)
bx.text(XPOS[3] + 0.12, top2[3], "0.14", ha="left", va="center", fontsize=7, color=INK2)
bx.text(XPOS[3] + 0.32, onebatch_any, "0.29", ha="left", va="center", fontsize=7, color=INK2)

# agent points at rank 2 only (jittered right of the policy markers)
for i, (lab, k, n, c, m) in enumerate(agents_b):
    p, lo, hi = wilson(k, n)
    x = XPOS[0] - 0.16 - 0.15 * i
    bx.errorbar(x, p, yerr=[[lo], [hi]], fmt=m, color=c, ms=6, capsize=2.5, lw=1.1, zorder=8, label=lab)
    bx.text(x - 0.05, p, f"{k}/{n}", fontsize=6.5, color=INK2, ha="right", va="center", zorder=9,
            bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))

# rank-6 agents: not run (bank has three rank-6 traps); open markers in the "not run" strip
bx.axhspan(-0.13, -0.04, color="#f3f2ee", zorder=0, lw=0)
for i, (lab, k, n, c, m) in enumerate(agents_b):
    bx.plot(XPOS[2] - 0.14 + 0.14 * i, NOTRUN_Y, marker=m, ms=6.5, mfc="none", mec=c, mew=1.3, ls="none")
bx.text(XPOS[2] + 0.28, NOTRUN_Y, "agents: not run", fontsize=7, color=INK2, va="center")
bx.text(XPOS[0] - 0.75, NOTRUN_Y, "not run", fontsize=7, color=MUTED, va="center")

bx.set_xticks(XPOS)
bx.set_xticklabels(XLAB)
bx.set_xlim(-0.85, 3.85)
bx.set_ylim(-0.13, 1.08)
bx.set_yticks(np.arange(0, 1.01, 0.2))
bx.grid(axis="y", color=GRID, lw=0.6)
bx.set_xlabel("proxy rank of the trap's [main]")
bx.set_ylabel("P(NAME), trap episodes, B = 8")
bx.set_title("(b) Depth response at B = 8, trap episodes", loc="left")
h, l = bx.get_legend_handles_labels()
h += [Line2D([], [], color=GREEN, lw=4, alpha=0.85)]
l += ["hedge range 0.46-0.56, ranks 3-8 [priv]"]
bx.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2, frameon=False,
          handlelength=2.2, columnspacing=1.0)

fig.suptitle("One proxy, many exchange rates", x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.97))
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(HERE, f"fig2.{ext}"), dpi=200, bbox_inches="tight")
print("wrote", os.path.join(HERE, "fig2.png"), "and fig2.pdf")
print("panel (b) values: top1", top1, "top2", top2, "bayes", bayes, bayes_any)
