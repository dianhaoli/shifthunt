# Figure 1 for d7 draft_r2: NAME vs exact-query budget (GPT 6.1 Terra). Pure-python SVG (no matplotlib here).
import math, sys
def wilson(k,n,z=1.959964):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
W,H=560,340; L,R,T,B=62,150,22,52
x0,x1=math.log2(6),math.log2(80)
X=lambda b: L+(math.log2(b)-x0)/(x1-x0)*(W-L-R)
Y=lambda p: T+(1-p)*(H-T-B)
BLUE,ORANGE,INK,INK2,GRID,SURF='#2a78d6','#eb6834','#0b0b0b','#52514e','#e4e3df','#fcfcfb'
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif" font-size="11">',
   f'<rect width="{W}" height="{H}" fill="{SURF}"/>']
for p in [0,.25,.5,.75,1]:
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" stroke="{GRID}" stroke-width="1"/>')
    s.append(f'<text x="{L-6}" y="{Y(p)+4:.1f}" text-anchor="end" fill="{INK2}">{p:.2f}</text>')
for b in [8,16,32,64]:
    s.append(f'<text x="{X(b):.1f}" y="{H-B+16}" text-anchor="middle" fill="{INK2}">{b}</text>')
s.append(f'<text x="{(L+W-R)/2:.1f}" y="{H-12}" text-anchor="middle" fill="{INK}">exact queries (log scale)</text>')
s.append(f'<text transform="translate(16,{(T+H-B)/2:.1f}) rotate(-90)" text-anchor="middle" fill="{INK}">NAME (hard cue named, nulls clean)</text>')
# Open-8 band (Wilson) and line
lo,hi=wilson(23,24)
s.append(f'<rect x="{L}" y="{Y(hi):.1f}" width="{W-R-L}" height="{Y(lo)-Y(hi):.1f}" fill="{ORANGE}" fill-opacity="0.12"/>')
s.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(23/24):.1f}" y2="{Y(23/24):.1f}" stroke="{ORANGE}" stroke-width="2"/>')
s.append(f'<circle cx="{X(8):.1f}" cy="{Y(23/24):.1f}" r="4.5" fill="{ORANGE}" stroke="{SURF}" stroke-width="2"/>')
# logistic interpolation
a,b=-7.142,1.986
pts=[(bb, 1/(1+math.exp(-(a+b*math.log2(bb))))) for bb in [8*2**(i/40) for i in range(121)]]
s.append('<polyline fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="5 4" points="%s"/>'%(BLUE,' '.join(f'{X(q):.1f},{Y(p):.1f}' for q,p in pts)))
xc=36.1; s.append(f'<line x1="{X(xc):.1f}" x2="{X(xc):.1f}" y1="{Y(23/24):.1f}" y2="{Y(0):.1f}" stroke="{INK2}" stroke-width="1" stroke-dasharray="2 3"/>')
s.append(f'<text x="{X(xc)+4:.1f}" y="{Y(0.08):.1f}" fill="{INK2}">≈36 (interpolated)</text>')
# reference policies (privileged, exact back-end)
for q,p in [(8,.40),(16,.80),(64,.93)]:
    cx,cy=X(q),Y(p); s.append(f'<path d="M{cx-5:.1f},{cy:.1f} L{cx:.1f},{cy-5:.1f} L{cx+5:.1f},{cy:.1f} L{cx:.1f},{cy+5:.1f} Z" fill="none" stroke="{INK2}" stroke-width="1.5"/>')
cx,cy=X(8),Y(.703); s.append(f'<path d="M{cx-5:.1f},{cy:.1f} L{cx:.1f},{cy-5:.1f} L{cx+5:.1f},{cy:.1f} L{cx:.1f},{cy+5:.1f} Z" fill="{SURF}" stroke="{INK2}" stroke-width="1" stroke-dasharray="2 2"/>')
s.append(f'<text x="{cx+8:.1f}" y="{cy+4:.1f}" fill="{INK2}" font-size="10">noiseless optimum 0.70 (untracked sim.)</text>')
# black-box points with Wilson bars
bb=[(8,6),(16,16),(64,24)]
s.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>'%(BLUE,' '.join(f'{X(q):.1f},{Y(k/24):.1f}' for q,k in bb)))
for q,k in bb:
    lo,hi=wilson(k,24); s.append(f'<line x1="{X(q):.1f}" x2="{X(q):.1f}" y1="{Y(lo):.1f}" y2="{Y(hi):.1f}" stroke="{BLUE}" stroke-width="2"/>')
    s.append(f'<circle cx="{X(q):.1f}" cy="{Y(k/24):.1f}" r="4.5" fill="{BLUE}" stroke="{SURF}" stroke-width="2"/>')
    ty=Y(k/24)-10 if k==24 else Y(k/24)+14; tx=X(q)-34 if k==24 else X(q)+8
    s.append(f'<text x="{tx:.1f}" y="{ty:.1f}" fill="{INK}">{k}/24</text>')
# legend (right)
lx=W-R+12; ly=T+10
items=[('line',ORANGE,'Open-8 (proxy), 23/24'),('line',BLUE,'no proxy (BB-8/16/64)'),('dash',BLUE,'logistic interpolation'),('diam',INK2,'privileged reference')]
for i,(kind,c,lab) in enumerate(items):
    y=ly+i*18
    if kind=='line': s.append(f'<line x1="{lx}" x2="{lx+18}" y1="{y}" y2="{y}" stroke="{c}" stroke-width="2"/><circle cx="{lx+9}" cy="{y}" r="3.5" fill="{c}"/>')
    elif kind=='dash': s.append(f'<line x1="{lx}" x2="{lx+18}" y1="{y}" y2="{y}" stroke="{c}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    else: s.append(f'<path d="M{lx+4},{y} L{lx+9},{y-5} L{lx+14},{y} L{lx+9},{y+5} Z" fill="none" stroke="{c}" stroke-width="1.5"/>')
    s.append(f'<text x="{lx+24}" y="{y+4}" fill="{INK}" font-size="10">{lab}</text>')
s.append('</svg>')
open(sys.argv[1],'w').write('\n'.join(s))
