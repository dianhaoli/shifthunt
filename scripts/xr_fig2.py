#!/usr/bin/env python3
"""X5 (GPU plan): Figure 2, "One proxy, many exchange rates", with MEASURED series.

    <python with matplotlib> scripts/xr_fig2.py      -> results/blackbox_1112/gpuplan/fig2_measured.{png,pdf}

Based on paper_loop/exchange_rate/calc/fig2/make_fig2.py (branch claude/nifty-wozniak-vunb6z). Solid lines are
measured in the real environment (X1, gpuplan/xr_curves.json: scripted policies on the stored episodes, exact
logits for the six shipped items) [expl X1]; thin dashed lines are the abstract-model references [priv]
(gpuplan/fig2_inputs/c2_results.json, c3_bstar.json, copied unchanged). Agent points: Block 1 and Luna
[pre-reg]; X3 Open-4 (gpuplan/open4/open4.json) and C14 fresh traps (gpuplan/c14/c14.json) when present.
Cues are never named; no item id appears in the figure.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "results", "blackbox_1112", "gpuplan")
XR = json.load(open(os.path.join(G, "xr_curves.json")))
C2 = json.load(open(os.path.join(G, "fig2_inputs", "c2_results.json")))
C3 = json.load(open(os.path.join(G, "fig2_inputs", "c3_bstar.json")))


def opt(path):
    p = os.path.join(G, path)
    return json.load(open(p)) if os.path.exists(p) else None


OPEN4, C14, C14B = opt("open4/open4.json"), opt("c14/c14.json"), opt("c14b/c14b.json")

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET = "#e87ba4", "#008300", "#6250d6"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 7.2,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
    "figure.facecolor": "white", "axes.facecolor": "white"})


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, p - (mid - half), (mid + half) - p


def kn(s):
    return tuple(int(x) for x in s.split("/"))


def measured(group, pol):
    c = XR["curves"][group][pol]
    xs = sorted(int(b) for b in c)
    return np.array(xs), np.array([c[str(b)]["name"] for b in xs])


POL = [("bayes_bank", "calibrated adaptive Bayes (bank prior)", ORANGE, "o", "-"),
       ("top2", "test the SAE's top two", YELLOW, "s", "-"),
       ("hedge", "hedge: screen what the SAE does not flag", GREEN, "P", "-"),
       ("top1", "test the SAE's top one", MAGENTA, "v", "-"),
       ("best_blind", "best blind policy (no SAE)", BLUE, "D", "-")]

fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.6, 6.6), gridspec_kw={"width_ratios": [1.3, 1]})

# ---- (a) shipped six, P(NAME) against B
for key, lab, c, m, ls in POL:
    x, y = measured("shipped_six", key)
    ax.plot(x, y, color=c, marker=m, ms=4.5, ls=ls, label=f"{lab} [expl X1]", zorder=4)
NC = C2["noiseless_curves"]
pr = NC["proxy Bayes | shipped (trap at r2) | known counts | group"]
xs = sorted(int(b) for b in pr if int(b) <= 12)
ax.plot(xs, [pr[str(b)] for b in xs], color=ORANGE, lw=1.0, ls=(0, (3, 2)), label="calibrated Bayes, abstract model, noiseless [priv]")
bs = NC["blind ideal | known counts | single"]
xs = sorted(int(b) for b in bs if int(b) <= 64)
ax.plot(xs, [bs[str(b)] for b in xs], color=BLUE, lw=1.0, ls=(0, (3, 2)), label="ideal blind single isolations, abstract model [priv]")
TARGET = 23 / 24
ax.axhline(TARGET, color=MUTED, lw=0.8, ls=(0, (1, 2)), zorder=1)
for B, k, n in [(8, 6, 24), (16, 16, 24), (64, 24, 24)]:
    p, lo, hi = wilson(k, n)
    ax.errorbar(B * 1.05, p, yerr=[[lo], [hi]], fmt="o", color=INK, mfc="white", mew=1.5, ms=6.5, capsize=2.5, lw=1.1, zorder=8)
p, lo, hi = wilson(23, 24)
ax.errorbar(8 / 1.05, p, yerr=[[lo], [hi]], fmt="o", color=INK, ms=6.5, capsize=2.5, lw=1.1, zorder=9)
agent_h = [Line2D([], [], marker="o", color=INK, mfc="white", mew=1.5, ls="none", ms=6),
           Line2D([], [], marker="o", color=INK, ls="none", ms=6)]
agent_l = ["Terra without SAE, B = 8/16/64 [pre-reg]", "Terra with SAE, B = 8 [pre-reg]"]
if OPEN4 and "terra_open4" in OPEN4:
    k, n = kn(OPEN4["terra_open4"]["name_all"])
    p, lo, hi = wilson(k, n)
    ax.errorbar(4, p, yerr=[[lo], [hi]], fmt="*", color=INK, ms=10, capsize=2.5, lw=1.1, zorder=9)
    ax.annotate(f"{k}/{n}", (4, p), xytext=(4.4, p - 0.09), fontsize=7, color=INK2)
    agent_h.append(Line2D([], [], marker="*", color=INK, ls="none", ms=9))
    agent_l.append("Terra with SAE, B = 4 [pre-reg X3]")
if OPEN4 and "luna_open4" in OPEN4:
    k, n = kn(OPEN4["luna_open4"]["name_all"])
    p, lo, hi = wilson(k, n)
    ax.errorbar(4 / 1.07, p, yerr=[[lo], [hi]], fmt="*", color=MUTED, ms=9, capsize=2.5, lw=1.1, zorder=9)
    agent_h.append(Line2D([], [], marker="*", color=MUTED, ls="none", ms=8))
    agent_l.append("Luna with SAE, B = 4 [desc X3b]")
k, n = 5, 36
p, lo, hi = wilson(k, n)
ax.errorbar(8 * 1.12, p, yerr=[[lo], [hi]], fmt="D", color=MUTED, ms=5.5, capsize=2.5, lw=1.1, zorder=8)
agent_h.append(Line2D([], [], marker="D", color=MUTED, ls="none", ms=5.5))
agent_l.append("Luna with SAE, B = 8, all six [pre-reg]")
ax.set_xscale("log", base=2)
ax.set_xlim(1.8, 72)
ax.set_xticks([2, 3, 4, 5, 6, 8, 12, 16, 32, 64])
ax.set_xticklabels(["2", "3", "4", "5", "6", "8", "12", "16", "32", "64"])
ax.set_ylim(-0.03, 1.06)
ax.grid(axis="y", color=GRID, lw=0.6)
ax.set_xlabel("exact texts per episode, B (log scale)")
ax.set_ylabel("P(NAME), the six shipped items")
ax.set_title("(a) Success against exact budget", loc="left")
ha, la = ax.get_legend_handles_labels()

# ---- (b) depth response on the shipped traps, B = 8
D = XR["depth"]["shipped_traps"]
ranks = sorted(int(r) for r in D)
for key, lab, c, m, ls in POL[:4] + [("bayes_law", "calibrated Bayes that knows the trap rank", VIOLET, "^", "-")]:
    ys = [D[str(r)][key]["8"]["name"] if key in D[str(r)] else np.nan for r in ranks]
    bx.plot(ranks, ys, color=c, marker=m, ms=5, ls=ls, label=f"{lab} [expl X1]", zorder=4)
bb = XR["curves"]["shipped_traps"]["best_blind"]["8"]["name"]
bx.axhline(bb, color=BLUE, lw=1.4, ls="-", label=f"best blind policy, rank-free ({bb:.2f}) [expl X1]")
pts = [("Terra, Open-8, shipped traps [pre-reg]", 11, 12, INK, "o", 2), ("Luna, Open-8, shipped traps [pre-reg]", 1, 18, MUTED, "D", 2)]
if C14 and "terra" in C14 and "fresh" in C14["terra"]:
    k, n = kn(C14["terra"]["fresh"]["NAME_trap"])
    lab = "Terra, fresh held-out traps [pre-reg C14]"
    if C14B:  # third fresh item: C14b's pre-registered pooled count over the three items
        k, n = kn(C14B["H1_pooled_three"]["terra_NAME_trap"])
        lab = "Terra, 3 fresh held-out traps [pre-reg C14, C14b]"
    pts.append((lab, k, n, INK, "*", 2))
if C14 and "luna" in C14 and "fresh" in C14["luna"]:
    k, n = kn(C14["luna"]["fresh"]["NAME_trap"])
    lab = "Luna, fresh held-out traps [pre-reg C14]"
    if C14B:  # the original counted runs: C14's 10 + C14b's 7 on F2-c (C14L's extra 4 are a secondary table)
        k2, n2 = kn(C14B["F2c"]["luna"]["NAME_trap"])
        k, n, lab = k + k2, n + n2, "Luna, 3 fresh held-out traps [pre-reg C14, C14b]"
    pts.append((lab, k, n, MUTED, "*", 2))
for i, (lab, k, n, c, m, r) in enumerate(pts):
    p, lo, hi = wilson(k, n)
    x = r - 0.18 - 0.16 * i
    bx.errorbar(x, p, yerr=[[lo], [hi]], fmt=m, color=c, ms=7 if m == "*" else 6, capsize=2.5, lw=1.1, zorder=8,
                label=lab)
bx.set_xticks(ranks)
bx.set_xlim(0.2, max(ranks) + 0.5)
bx.set_ylim(-0.03, 1.06)
bx.grid(axis="y", color=GRID, lw=0.6)
bx.set_xlabel("SAE rank of the trap's [main]\n(shipped traps; order changed, true logits unchanged)")
bx.set_ylabel("P(NAME), trap episodes, B = 8")
bx.set_title("(b) Depth response at B = 8", loc="left")
hb, lb = bx.get_legend_handles_labels()
H, L = [], []
for h_, l_ in zip(ha + hb + agent_h, la + lb + agent_l):
    if l_ not in L:
        H.append(h_)
        L.append(l_)
fig.legend(H, L, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=False, handlelength=2.4,
           columnspacing=1.2)

fig.suptitle("One proxy, many exchange rates (measured)", x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(rect=(0, 0.17, 1, 0.97))
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(G, f"fig2_measured.{ext}"), dpi=200, bbox_inches="tight")
print("wrote", os.path.join(G, "fig2_measured.png"))
