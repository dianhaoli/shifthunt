#!/usr/bin/env python3
"""Fig. 1 (V10): share of wrong hard-slot answers that the judge credits, set A.

Set A, 130 hard slots (87 passes, 17 wrong named cues, 26 wrong `none`).
Two judges (Terra, Sol) x four evidence levels (report, report + log,
transcript, report + key). Each value is k credited / n wrong answers.

Numbers (facts/FACTS_ONLY.md; every value checked against the entry named):
  Terra report      : wrong none 23/26, wrong cue 9/17   S0-A (Terra L0 row); B3 (L0)
  Terra report+log  : wrong none 21/26, wrong cue 7/17   S1-A (Terra L1 row); B3 (L1)
  Terra transcript  : wrong none 17/26, wrong cue 3/17   S2-A (Terra L2 row); B3 (L2)
  Terra report+key  : wrong none  0/26, wrong cue 0/17   S3-A (Terra K0 row)
  Sol   report      : wrong none 18/26, wrong cue 6/17   S0-A (Sol S0 row)
  Sol   report+log  : wrong none 16/26, wrong cue 8/17   S1-A (Sol S1 row)
  Sol   transcript  : wrong none 15/26, wrong cue 8/17   S2-A (Sol S2 row)
  Sol   report+key  : wrong none  0/26, wrong cue 0/17   S3-A (Sol S3 row)
Terra report level is the 12 Nov send (L0), the one Sol's S0 is compared with
in S0-A. (The re-send L0r gives 20/26 and 7/17; B3 notes both are valid sends.)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "hatch.linewidth": 0.6,
})

LEVELS = ["report", "report + log", "transcript", "report + key"]
# (credited k) per level; n fixed per panel
DATA = {
    "none": {"n": 26, "Terra": [23, 21, 17, 0], "Sol": [18, 16, 15, 0]},
    "cue":  {"n": 17, "Terra": [9, 7, 3, 0],    "Sol": [6, 8, 8, 0]},
}
PANELS = [("none", "Wrong ‘none’ answers credited (n = 26)"),
          ("cue", "Wrong named cues credited (n = 17)")]

STYLE = {
    "Terra": dict(facecolor="0.25", edgecolor="0.0", hatch=None),
    "Sol":   dict(facecolor="0.80", edgecolor="0.0", hatch="////"),
}

fig, axes = plt.subplots(2, 1, figsize=(3.3, 3.05), sharex=True)
bh = 0.36
y = np.arange(len(LEVELS))[::-1].astype(float)  # report on top

for ax, (key, xlabel) in zip(axes, PANELS):
    n = DATA[key]["n"]
    for j, judge in enumerate(["Terra", "Sol"]):
        ks = DATA[key][judge]
        off = bh / 2 + 0.02 if j == 0 else -(bh / 2 + 0.02)
        shares = [k / n for k in ks]
        ax.barh(y + off, shares, height=bh, linewidth=0.5,
                label=judge, **STYLE[judge])
        for yy, s, k in zip(y + off, shares, ks):
            ax.text(s + 0.015, yy, f"{k}/{n}", va="center", ha="left",
                    fontsize=7, color="0.0")
    ax.set_yticks(y)
    ax.set_yticklabels(LEVELS)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(y.min() - 0.6, y.max() + 0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=3)
    ax.xaxis.grid(True, color="0.88", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title(xlabel, fontsize=8, loc="left", pad=3)

axes[1].set_xticks([0, 0.25, 0.5, 0.75, 1.0])
axes[1].set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
axes[1].set_xlabel("share credited by the judge")
axes[1].tick_params(axis="x", labelbottom=True)
axes[0].legend(loc="lower right", frameon=False, handlelength=1.4,
               handleheight=0.9, borderaxespad=0.1)

fig.tight_layout(h_pad=0.8)
out = "/home/user/shifthunt/paper_loop/final/fig/fig1_v10"
fig.savefig(out + ".png", dpi=300)
fig.savefig(out + ".pdf")
print("wrote", out + ".png/.pdf")
