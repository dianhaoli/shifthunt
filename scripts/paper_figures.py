#!/usr/bin/env python3
"""Figures for the AAAI-27 paper (paper/figures_aaai/), from committed public files only.

fig_control.pdf  (a) hard-slot NAME by arm, GPT and Haiku (Block 1, Wilson 95%); (b) the same split by item kind;
                 (c) Exp F listing rate by conditionality level (pooled over cues and models, Wilson 95%).
Palette: categorical slots 1-2 of the dataviz reference palette (blue, orange; validated pair), plus marker shape
so identity never rests on colour alone.
"""
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/figures_aaai"
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
STY = {"gpt": (BLUE, "o", "GPT 6.1 Terra"), "haiku": (ORANGE, "s", "Haiku 5.5")}
ARMS = [("open8", "Open-8"), ("bb8", "BB-8"), ("bb64", "BB-64")]
# Exp F per-level pooled counts (results/blackbox_1112/SUMMARY.md, Exp F; exp_f/exp_f.json)
EXPF = [("L2\ntypogr.", 44, 60), ("L3\nposition", 22, 40), ("L4\nprop. of\nprop.", 9, 40),
        ("L5\ntwo\ntogether", 0, 20), ("L6\ndoubly\ncond.", 1, 20)]


def wilson(k, n, z=1.96):
    if n == 0:
        return (math.nan,) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def counts():
    c = {}
    with open(ROOT / "results/blackbox_1112/rows_r1112.csv") as f:
        for r in csv.DictReader(f):
            if r["counted"] != "1":
                continue
            for key in ((r["agent"], r["arm"], "all"), (r["agent"], r["arm"], r["kind"])):
                k, n = c.get(key, (0, 0))
                c[key] = (k + int(r["name"]), n + 1)
    return c


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.6)
    ax.tick_params(colors=MUTED, labelcolor=INK, labelsize=7, width=0.6, length=2)
    ax.set_ylim(-0.03, 1.05)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def main():
    plt.rcParams.update({"font.family": "serif", "font.size": 7, "pdf.fonttype": 42})
    c = counts()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.05), gridspec_kw={"width_ratios": [1, 1.5, 1.35]})
    ax = axes[0]
    for j, ag in enumerate(("gpt", "haiku")):
        col, mk, lab = STY[ag]
        xs = [i + (j - 0.5) * 0.22 for i in range(3)]
        for x, (arm, _) in zip(xs, ARMS):
            k, n = c[(ag, arm, "all")]
            p, lo, hi = wilson(k, n)
            ax.plot([x, x], [lo, hi], color=col, lw=1.2, solid_capstyle="round")
            ax.plot(x, p, mk, color=col, ms=4.5, mec="white", mew=0.6, label=lab if arm == "open8" else None)
            ax.annotate(f"{k}/{n}", (x, hi), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=5.5, color=MUTED)
    ax.set_xticks(range(3), [a for _, a in ARMS])
    ax.set_ylabel("hard slot named (NAME)", fontsize=7, color=INK)
    ax.set_title("(a) Control: SAE removed", fontsize=7.5, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=6, loc="lower center", handletextpad=0.2, borderaxespad=0.1)
    style(ax)

    ax = axes[1]
    groups = [(arm, kind) for kind in ("trap", "twopart") for arm, _ in ARMS]
    for j, ag in enumerate(("gpt", "haiku")):
        col, mk, lab = STY[ag]
        for i, (arm, kind) in enumerate(groups):
            x = i + (i >= 3) * 0.5 + (j - 0.5) * 0.24
            k, n = c[(ag, arm, kind)]
            p, lo, hi = wilson(k, n)
            ax.plot([x, x], [lo, hi], color=col, lw=1.2)
            ax.plot(x, p, mk, color=col, ms=4.5, mec="white", mew=0.6)
            ax.annotate(f"{k}/{n}", (x, hi), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=5, color=MUTED)
    ax.set_xticks([i + (i >= 3) * 0.5 for i in range(6)], [a for _, a in ARMS] * 2)
    ax.text(1, -0.33, "trap items", ha="center", fontsize=6.5, color=INK, transform=ax.get_xaxis_transform())
    ax.text(4.5, -0.33, "two-part items", ha="center", fontsize=6.5, color=INK, transform=ax.get_xaxis_transform())
    ax.set_title("(b) By item kind", fontsize=7.5, color=INK, loc="left")
    style(ax)

    ax = axes[2]
    for i, (lab, k, n) in enumerate(EXPF):
        p, lo, hi = wilson(k, n)
        ax.plot([i, i], [lo, hi], color=MUTED, lw=1.2)
        ax.plot(i, p, "D", color=INK, ms=3.8, mec="white", mew=0.6)
        ax.annotate(f"{k}/{n}", (i, hi), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=5.5, color=MUTED)
    ax.set_xticks(range(len(EXPF)), [e[0] for e in EXPF], fontsize=5.8)
    ax.set_ylabel("cue listed from sample", fontsize=7, color=INK)
    ax.set_title("(c) Listing ladder (no tools)", fontsize=7.5, color=INK, loc="left")
    style(ax)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig_control.pdf")
    fig.savefig(OUT / "fig_control.png", dpi=200)


if __name__ == "__main__":
    main()
