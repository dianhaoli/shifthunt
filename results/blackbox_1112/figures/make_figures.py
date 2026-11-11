"""Hand-built SVG figures for results/blackbox_1112/SUMMARY.md (standard library only).
Reads only committed aggregate files; writes results/blackbox_1112/figures/*.svg."""
import json, math, os, sys
from xml.sax.saxutils import escape

RES = sys.argv[1] if len(sys.argv) > 1 else "results/blackbox_1112"
OUT = os.path.join(RES, "figures")
os.makedirs(OUT, exist_ok=True)
A = json.load(open(os.path.join(RES, "analysis.json")))
BV = json.load(open(os.path.join(RES, "blind_verify", "blind_verify.json")))
EF = json.load(open(os.path.join(RES, "exp_f", "exp_f.json")))
ED = json.load(open(os.path.join(RES, "exp_d", "exp_d.json")))

INK, INK2, MUTED, GRID, BG = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#ffffff"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"   # categorical slots 1-4 (reference palette, light)
FONT = "font-family='-apple-system,Segoe UI,Helvetica,Arial,sans-serif'"


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


class SVG:
    def __init__(self, w, h, title, desc):
        self.w, self.h = w, h
        self.p = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' {FONT} role='img'>",
                  f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>",
                  f"<rect x='0' y='0' width='{w}' height='{h}' fill='{BG}'/>"]

    def text(self, x, y, s, size=12, fill=INK, anchor="start", weight="normal", rot=None):
        tr = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        self.p.append(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' fill='{fill}' text-anchor='{anchor}' font-weight='{weight}'{tr}>{escape(s)}</text>")

    def line(self, x1, y1, x2, y2, stroke=GRID, w=1, dash=None):
        da = f" stroke-dasharray='{dash}'" if dash else ""
        self.p.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{w}'{da}/>")

    def poly(self, pts, stroke, w=2, dash=None):
        da = f" stroke-dasharray='{dash}'" if dash else ""
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.p.append(f"<polyline points='{s}' fill='none' stroke='{stroke}' stroke-width='{w}' stroke-linejoin='round'{da}/>")

    def dot(self, x, y, fill, r=5, hollow=False, tip=None, shape="circle"):
        f = BG if hollow else fill
        t = f"<title>{escape(tip)}</title>" if tip else ""
        if shape == "square":
            self.p.append(f"<rect x='{x-r:.1f}' y='{y-r:.1f}' width='{2*r}' height='{2*r}' fill='{f}' stroke='{fill}' stroke-width='2'>{t}</rect>")
        elif shape == "diamond":
            self.p.append(f"<polygon points='{x:.1f},{y-r-1:.1f} {x+r+1:.1f},{y:.1f} {x:.1f},{y+r+1:.1f} {x-r-1:.1f},{y:.1f}' fill='{f}' stroke='{fill}' stroke-width='2'>{t}</polygon>")
        else:
            self.p.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{f}' stroke='{fill}' stroke-width='2'>{t}</circle>")

    def ci(self, x, y0, y1, stroke):
        self.line(x, y0, x, y1, stroke, 2)
        self.line(x - 4, y0, x + 4, y0, stroke, 2)
        self.line(x - 4, y1, x + 4, y1, stroke, 2)

    def save(self, name):
        self.p.append("</svg>")
        with open(os.path.join(OUT, name), "w") as f:
            f.write("\n".join(self.p) + "\n")


def yaxis(s, x0, x1, top, bot, label):
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        y = bot - v * (bot - top)
        s.line(x0, y, x1, y, GRID if v else INK2, 1)
        s.text(x0 - 8, y + 4, f"{v:.2f}", 11, INK2, "end")
    s.text(x0 - 44, (top + bot) / 2, label, 12, INK2, "middle", rot=-90)


def legend(s, x, y, items):
    for i, (lab, col, hollow, shape) in enumerate(items):
        s.dot(x + 6, y + i * 18, col, 5, hollow, shape=shape)
        s.text(x + 18, y + i * 18 + 4, lab, 12, INK)


ARMS = [("open8", "Open-8"), ("bb8", "BB-8"), ("bb64", "BB-64")]
AG = [("gpt", "GPT 6.1 Terra (n = 24 per arm)", C1, "circle"), ("haiku", "Haiku 5.5 (n = 12 per arm)", C2, "square")]


# (a) NAME by arm
def fig_a():
    s = SVG(640, 400, "NAME rate by arm and agent", "Pooled NAME rate (k/n) with Wilson 95% intervals, Block 1.")
    x0, x1, top, bot = 80, 620, 40, 320
    s.text(x0, 22, "NAME rate by arm (Block 1, Wilson 95% intervals)", 14, INK, weight="bold")
    yaxis(s, x0, x1, top, bot, "NAME rate")
    gw = (x1 - x0) / 3
    for i, (arm, lab) in enumerate(ARMS):
        cx = x0 + gw * (i + 0.5)
        s.text(cx, bot + 22, lab, 13, INK, "middle")
        for j, (ag, alab, col, shp) in enumerate(AG):
            r = A["rates"][ag][arm]; k, n = r["k"], r["n"]; lo, hi = wilson(k, n)
            x = cx + (j - 0.5) * 44
            Y = lambda v: bot - v * (bot - top)
            s.ci(x, Y(lo), Y(hi), col)
            s.dot(x, Y(k / n), col, 5, shape=shp, tip=f"{alab.split(' (')[0]} {lab}: {k}/{n} = {k/n:.2f} [{lo:.2f}, {hi:.2f}]")
            s.text(x, Y(hi) - 8, f"{k}/{n}", 11, INK2, "middle")
    legend(s, x0 + 10, bot + 42, [(a[1], a[2], False, a[3]) for a in AG])
    s.save("fig_a_name_by_arm.svg")


# (b) by kind
def fig_b():
    W, H = 800, 400
    s = SVG(W, H, "NAME rate by arm, agent and item kind", "Pooled NAME rate per kind (3 items each) with Wilson 95% intervals.")
    s.text(70, 22, "NAME rate by arm and item kind (3 items per kind; Wilson 95% intervals)", 14, INK, weight="bold")
    panels = [("trap", "Trap items (ep411, ep413, ep415)"), ("twopart", "Two-part items (ep472, ep474, ep476)")]
    pw = 320
    for p, (kind, title) in enumerate(panels):
        x0 = 70 + p * (pw + 50); x1 = x0 + pw; top, bot = 76, 320
        s.text((x0 + x1) / 2, 48, title, 12, INK, "middle", "bold")
        if p == 0:
            yaxis(s, x0, x1, top, bot, "NAME rate")
        else:
            for v in (0, 0.25, 0.5, 0.75, 1.0):
                y = bot - v * (bot - top); s.line(x0, y, x1, y, GRID if v else INK2, 1)
                s.text(x0 - 6, y + 4, f"{v:.2f}", 10, INK2, "end")
        gw = pw / 3
        for i, (arm, lab) in enumerate(ARMS):
            cx = x0 + gw * (i + 0.5)
            s.text(cx, bot + 20, lab, 12, INK, "middle")
            for j, (ag, alab, col, shp) in enumerate(AG):
                r = A["rates"][ag][arm]["by_kind"][kind]; k, n = r["k"], r["n"]; lo, hi = wilson(k, n)
                x = cx + (j - 0.5) * 34
                Y = lambda v: bot - v * (bot - top)
                s.ci(x, Y(lo), Y(hi), col)
                s.dot(x, Y(k / n), col, 5, shape=shp, tip=f"{alab.split(' (')[0]} {lab} {kind}: {k}/{n} [{lo:.2f}, {hi:.2f}]")
                s.text(x, Y(hi) - 7, f"{k}/{n}", 10, INK2, "middle")
    legend(s, 80, 356, [("GPT 6.1 Terra (n = 12 per arm and kind)", C1, False, "circle"), ("Haiku 5.5 (n = 6 per arm and kind)", C2, False, "square")])
    s.save("fig_b_name_by_kind.svg")


# (c) GPT NAME vs exact-query budget, next to scripted blind ceilings
def fig_c():
    W, H = 820, 470
    s = SVG(W, H, "GPT NAME against the exact-query budget, with scripted blind ceilings",
            "GPT agent points (Wilson 95%) at 8 and 64 probe_query texts; privileged scripted blind ceilings from blind_verify (additive back-end, pooled over the six items).")
    x0, x1, top, bot = 80, 520, 50, 360
    s.text(x0, 22, "GPT NAME vs probe_query budget, next to privileged scripted blind ceilings", 14, INK, weight="bold")
    yaxis(s, x0, x1, top, bot, "NAME rate")
    Bs = [8, 16, 32, 64]
    X = lambda b: x0 + 30 + (math.log2(b) - 3) / 3 * (x1 - x0 - 60)
    Y = lambda v: bot - v * (bot - top)
    for b in Bs:
        s.text(X(b), bot + 20, str(b), 12, INK, "middle")
    s.text((x0 + x1) / 2, bot + 40, "probe_query texts per episode (log scale)", 12, INK2, "middle")
    add = BV["results"]["topic"]["additive"]; nl = BV["noiseless"]
    pol = list(add.keys())
    best = [max(add[p][str(b)]["pooled"]["name"] for p in pol) for b in Bs]
    rnd = [add["random"][str(b)]["pooled"]["name"] for b in Bs]
    bestnl = [max(nl[p][str(b)]["pooled"]["name"] for p in pol) for b in Bs]
    series = [("best scripted blind policy, noiseless readings", bestnl, MUTED, "2 4"),
              ("best scripted blind policy, stored readings", best, INK2, None),
              ("random single flips, stored readings", rnd, INK2, "6 3")]
    for lab, vals, col, dash in series:
        s.poly([(X(b), Y(v)) for b, v in zip(Bs, vals)], col, 2, dash)
        for b, v in zip(Bs, vals):
            s.dot(X(b), Y(v), col, 3, tip=f"{lab}, B = {b}: {v:.2f}")
    # agent points
    pts = [("open8", 8, -12, "Open-8", "diamond"), ("bb8", 8, 12, "BB-8", "circle"), ("bb64", 64, 0, "BB-64", "circle")]
    for arm, b, dx, lab, shp in pts:
        r = A["rates"]["gpt"][arm]; k, n = r["k"], r["n"]; lo, hi = wilson(k, n)
        x = X(b) + dx
        s.ci(x, Y(lo), Y(hi), C1)
        s.dot(x, Y(k / n), C1, 6, hollow=(arm == "open8"), shape=shp, tip=f"GPT {lab}: {k}/{n} [{lo:.2f}, {hi:.2f}]")
        if arm == "open8":
            s.text(x + 30, Y(k / n) + 4, f"GPT {lab} {k}/{n}", 11, INK)
        elif arm == "bb8":
            s.text(x + 10, Y(lo) + 16, f"GPT {lab} {k}/{n}", 11, INK)
        else:
            s.text(x - 10, Y(lo) + 16, f"GPT {lab} {k}/{n}", 11, INK, "end")
    # legend
    lx = x1 + 60; ly = 70
    s.text(lx, ly - 16, "GPT agent (Block 1, Wilson 95%)", 12, INK, weight="bold")
    s.dot(lx + 6, ly, C1, 5, hollow=True, shape="diamond"); s.text(lx + 18, ly + 4, "Open-8 (SAE tools)", 12)
    s.dot(lx + 6, ly + 18, C1, 5); s.text(lx + 18, ly + 22, "BB-8, BB-64 (no SAE)", 12)
    s.text(lx, ly + 54, "Scripted ceilings (privileged,", 12, INK, weight="bold")
    s.text(lx, ly + 70, "blind_verify, pooled)", 12, INK, weight="bold")
    for i, (lab, vals, col, dash) in enumerate(series):
        yy = ly + 92 + i * 34
        s.line(lx, yy, lx + 26, yy, col, 2, dash)
        words = lab.split(", ")
        s.text(lx + 32, yy + 4, words[0], 11)
        s.text(lx + 32, yy + 18, words[1], 11, INK2)
    s.text(x0, H - 30, "Ceilings: solver given the 8 aligned properties, signs and exact edits; base notes and topic unit free.", 10, INK2)
    s.text(x0, H - 16, "Not agent results. Best policy per budget: B = 8 (ii-b) guess, B = 16 and 32 (ii-c), B = 64 (i).", 10, INK2)
    s.save("fig_c_gpt_budget_ceilings.svg")


# (d) Exp F listing rate by level per model
MODELS = [("gpt-6.1-terra", "GPT 6.1 Terra", C1, "circle"), ("claude-opus-5-5", "Opus 5.5", C2, "square"),
          ("claude-sonnet-5-5", "Sonnet 5.5", C3, "diamond"), ("claude-haiku-5-5", "Haiku 5.5", C4, "circle")]


def fig_d():
    W, H = 760, 420
    s = SVG(W, H, "Exp F listing rate by cue level and model", "Listing rate (primary rule) per level; per-model lines, pooled with Wilson 95% intervals.")
    x0, x1, top, bot = 80, 560, 50, 340
    s.text(x0, 22, "Exp F (exploratory): listing rate by cue level, 8 aligned properties per sample", 14, INK, weight="bold")
    yaxis(s, x0, x1, top, bot, "listing rate (primary rule)")
    levels = [("S-L1", "L1 controls"), ("L2", "L2 typography"), ("L3", "L3 positional"), ("L4", "L4 prop. of prop."), ("L5", "L5 two together"), ("L6", "L6 doubly cond.")]
    gw = (x1 - x0) / len(levels)
    X = lambda i: x0 + gw * (i + 0.5)
    Y = lambda v: bot - v * (bot - top)
    for i, (lv, lab) in enumerate(levels):
        a, b = lab.split(" ", 1)
        s.text(X(i), bot + 18, a, 12, INK, "middle"); s.text(X(i), bot + 32, b, 10, INK2, "middle")
        n = EF["by_level"][lv]["pooled"]["primary"]["n"]
        s.text(X(i), bot + 46, f"n = {n}", 10, INK2, "middle")
    for mi, (m, lab, col, shp) in enumerate(MODELS):
        pts = []
        for i, (lv, _) in enumerate(levels):
            o = EF["by_level"][lv]["by_model"][m]["primary"]; pts.append((X(i) + (mi - 1.5) * 5, Y(o["k"] / o["n"]), o["k"], o["n"], lv))
        s.poly([(x, y) for x, y, *_ in pts], col, 2)
        for x, y, k, n, lv in pts:
            s.dot(x, y, col, 4, shape=shp, tip=f"{lab} {lv}: {k}/{n}")
    for i, (lv, _) in enumerate(levels):
        o = EF["by_level"][lv]["pooled"]["primary"]; k, n = o["k"], o["n"]; lo, hi = wilson(k, n)
        x = X(i) + 16
        s.ci(x, Y(lo), Y(hi), INK)
        s.dot(x, Y(k / n), INK, 4, tip=f"pooled {lv}: {k}/{n} [{lo:.2f}, {hi:.2f}]")
    lx = x1 + 24
    s.text(lx, 64, "per model (n = 5 per cue)", 12, INK, weight="bold")
    for i, (m, lab, col, shp) in enumerate(MODELS):
        s.line(lx, 82 + i * 18, lx + 20, 82 + i * 18, col, 2); s.dot(lx + 10, 82 + i * 18, col, 4, shape=shp)
        s.text(lx + 28, 86 + i * 18, lab, 12)
    s.dot(lx + 10, 172, INK, 4); s.text(lx + 28, 176, "pooled, Wilson 95%", 12)
    t = EF["trend"]
    s.text(lx, 210, f"Spearman rho = {t['rho']:.2f}", 12, INK2)
    s.text(lx, 226, f"over {t['n_cues']} generated cues,", 12, INK2)
    s.text(lx, 242, f"permutation p = {t['p']:.4f}", 12, INK2)
    s.text(lx, 258, "(exploratory)", 12, INK2)
    s.text(x0, H - 14, "L1 controls = the two stress-test plain cues; stress bridge and multi cues are reported apart in SUMMARY.md.", 10, INK2)
    s.save("fig_d_expf_levels.svg")


# (e) distractor effect: Exp D (1 aligned) vs Exp F (8 aligned), shared cues
def fig_e():
    cues = list(EF["distractor"].keys())
    rows = []
    for c in cues:
        d = EF["distractor"][c]; rows.append((c, d["exp_d_1_aligned"]["k"], d["exp_d_1_aligned"]["n"], d["exp_f_8_aligned"]["k"], d["exp_f_8_aligned"]["n"]))
    rows.sort(key=lambda r: r[3] / r[4] - r[1] / r[2])
    W = 800; rh = 30; top = 60; H = top + rh * len(rows) + 90
    s = SVG(W, H, "Distractor effect per shared cue, Exp D vs Exp F", "Pooled listing rate over four models, k/20, Wilson 95% intervals; Exp D one aligned property, Exp F eight.")
    x0, x1 = 200, 620
    X = lambda v: x0 + v * (x1 - x0)
    s.text(20, 22, "Listing rate with 1 aligned property (Exp D) vs 8 (Exp F), pooled over 4 models", 14, INK, weight="bold")
    bot = top + rh * len(rows)
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        s.line(X(v), top - 10, X(v), bot, GRID if v else INK2, 1)
        s.text(X(v), bot + 16, f"{v:.2f}", 11, INK2, "middle")
    s.text((x0 + x1) / 2, bot + 34, "listing rate (primary rule), k/20 per experiment", 12, INK2, "middle")
    for i, (c, kd, nd, kf, nf) in enumerate(rows):
        y = top + rh * i + rh / 2
        s.text(x0 - 12, y + 4, c, 12, INK, "end")
        s.line(X(kf / nf), y, X(kd / nd), y, MUTED, 2)
        lo, hi = wilson(kd, nd); s.line(X(lo), y - 6, X(hi), y - 6, C1, 1)
        lo2, hi2 = wilson(kf, nf); s.line(X(lo2), y + 6, X(hi2), y + 6, C2, 1)
        s.dot(X(kd / nd), y, C1, 5, tip=f"{c} Exp D: {kd}/{nd}")
        s.dot(X(kf / nf), y, C2, 5, shape="square", tip=f"{c} Exp F: {kf}/{nf}")
        s.text(x1 + 14, y + 4, f"{kd}/{nd} -> {kf}/{nf} ({kf/nf - kd/nd:+.2f})", 11, INK2)
    ly = bot + 54
    s.dot(x0 + 6, ly, C1, 5); s.text(x0 + 18, ly + 4, "Exp D: 1 aligned property", 12)
    s.dot(x0 + 206, ly, C2, 5, shape="square"); s.text(x0 + 218, ly + 4, "Exp F: 8 aligned properties", 12)
    s.text(20, ly + 24, "Thin lines above/below each row: Wilson 95% intervals. Same cue definitions; Exp F samples also differ in framing.", 10, INK2)
    s.save("fig_e_distractor_effect.svg")


for f in (fig_a, fig_b, fig_c, fig_d, fig_e):
    f()
print("wrote", sorted(os.listdir(OUT)))
