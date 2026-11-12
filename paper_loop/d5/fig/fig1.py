# Figure 1 from committed counts (Table 2 / Table 4). Writes fig1.svg next to this script.
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig1.svg")
W, H = 760, 300
C_OK, C_COM, C_OMI = "#c9ced6", "#d1495b", "#2e86ab"
rows = [  # (arm, verdict type, total, wrong, error colour)
    ("Open-8 (proxy)", "named", 98, 1, C_COM),
    ("Open-8 (proxy)", "none", 46, 10, C_OMI),
    ("BB-8 (no proxy)", "named", 78, 27, C_COM),
    ("BB-8 (no proxy)", "none", 66, 33, C_OMI),
]
s = []
a = s.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif" font-size="12">')
a(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
a('<text x="20" y="22" font-size="13" font-weight="bold" fill="#222">A. Verdicts at matched 8 exact queries (GPT + Haiku, 144 per arm)</text>')
x0, scale, y = 190, 2.6, 50   # 1 verdict = 2.6 px
for i, (arm, vt, n, wrong, col) in enumerate(rows):
    if i % 2 == 0:
        a(f'<text x="20" y="{y+14}" fill="#222" font-weight="bold">{arm}</text>')
    a(f'<text x="{x0-8}" y="{y+14}" text-anchor="end" fill="#444">{"named" if vt=="named" else "none"}</text>')
    wpx = wrong*scale; okpx = (n-wrong)*scale
    a(f'<rect x="{x0}" y="{y}" width="{wpx:.1f}" height="20" fill="{col}"/>')
    a(f'<rect x="{x0+wpx:.1f}" y="{y}" width="{okpx:.1f}" height="20" fill="{C_OK}"/>')
    a(f'<text x="{x0+wpx+okpx+6:.1f}" y="{y+14}" fill="#222">{wrong}/{n} wrong</text>')
    y += 28 if i % 2 == 0 else 44
ly = y + 2
for j, (lab, col) in enumerate([("commission (named, wrong)", C_COM), ("omission (none, wrong)", C_OMI), ("correct", C_OK)]):
    lx = 20 + j*170
    a(f'<rect x="{lx}" y="{ly}" width="12" height="12" fill="{col}"/><text x="{lx+17}" y="{ly+10}" fill="#333">{lab}</text>')
# Panel B: recheck curve
px, py, pw, ph = 560, 50, 170, 170
a(f'<text x="{px-20}" y="22" font-size="13" font-weight="bold" fill="#222">B. Recheck `none` first</text>')
a(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="none" stroke="#888"/>')
a(f'<line x1="{px}" y1="{py+ph}" x2="{px+pw}" y2="{py}" stroke="#aaa" stroke-dasharray="4 3"/>')
def pt(xf, yf): return f"{px+xf*pw:.1f},{py+ph-yf*ph:.1f}"
for lab, xf, yf, col in [("Open-8", 0.32, 0.91, C_OMI), ("BB-8", 0.46, 0.55, "#7a7a7a")]:
    a(f'<polyline points="{pt(0,0)} {pt(xf,yf)} {pt(1,1)}" fill="none" stroke="{col}" stroke-width="2.2"/>')
    a(f'<circle cx="{px+xf*pw:.1f}" cy="{py+ph-yf*ph:.1f}" r="3.5" fill="{col}"/>')
    a(f'<text x="{px+xf*pw+6:.1f}" y="{py+ph-yf*ph+ (4 if lab=="Open-8" else 14):.1f}" fill="{col}">{lab}: {int(xf*100)}% → {int(yf*100)}%</text>')
a(f'<text x="{px+pw/2}" y="{py+ph+18}" text-anchor="middle" fill="#444">share of verdicts rechecked</text>')
a(f'<text x="{px-10}" y="{py+ph/2}" text-anchor="middle" fill="#444" transform="rotate(-90 {px-10} {py+ph/2})">share of errors caught</text>')
a(f'<text x="{px+0.80*pw:.1f}" y="{py+ph-0.68*ph:.1f}" fill="#999" font-size="10">random</text>')
a('</svg>')
open(out, "w").write("\n".join(s))
print(out)
