from math import sqrt
O='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/d4/fig/'
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return max(0,c-h),min(1,c+h)
F='font-family="Helvetica,Arial,sans-serif"'
def svg(w,h,body): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {F} font-size="11"><rect width="{w}" height="{h}" fill="white"/>{body}</svg>'
# Fig 1
W,H=340,230; x0,y0,x1,y1=50,20,320,190
xs={8:x0+20,16:x0+110,64:x0+230}
Y=lambda v: y1-(y1-y0)*v
b=''
for v in (0,0.25,0.5,0.75,1.0):
    b+=f'<line x1="{x0}" x2="{x1}" y1="{Y(v)}" y2="{Y(v)}" stroke="#ddd"/><text x="{x0-6}" y="{Y(v)+4}" text-anchor="end">{v:.2f}</text>'
for n,x in xs.items(): b+=f'<text x="{x}" y="{y1+16}" text-anchor="middle">{n}</text>'
b+=f'<text x="{(x0+x1)/2}" y="{H-6}" text-anchor="middle">exact queries (log scale)</text>'
b+=f'<text transform="translate(12,{(y0+y1)/2}) rotate(-90)" text-anchor="middle">NAME rate (GPT 6.1 Terra)</text>'
bb=[(8,6,24),(16,16,24),(64,24,24)]
pts=' '.join(f'{xs[n]},{Y(k/m)}' for n,k,m in bb)
b+=f'<polyline points="{pts}" fill="none" stroke="#1f5fa8" stroke-width="2"/>'
for n,k,m in bb:
    lo,hi=wilson(k,m); b+=f'<line x1="{xs[n]}" x2="{xs[n]}" y1="{Y(lo)}" y2="{Y(hi)}" stroke="#1f5fa8"/><circle cx="{xs[n]}" cy="{Y(k/m)}" r="4" fill="#1f5fa8"/>'
ce=[(8,.40),(16,.80),(64,.93)]
b+='<polyline points="'+' '.join(f'{xs[n]},{Y(v)}' for n,v in ce)+'" fill="none" stroke="#777" stroke-dasharray="5,4" stroke-width="1.5"/>'
lo,hi=wilson(23,24); xo=xs[8]
b+=f'<line x1="{xo}" x2="{xo}" y1="{Y(lo)}" y2="{Y(hi)}" stroke="#c0392b"/><text x="{xo}" y="{Y(23/24)+5}" text-anchor="middle" font-size="16" fill="#c0392b">&#9733;</text>'
b+=f'<text x="{xo+12}" y="{Y(23/24)+4}" fill="#c0392b">Open-8 (proxy): 23/24</text>'
b+=f'<text x="{xs[16]+8}" y="{Y(.67)+14}" fill="#1f5fa8">no proxy</text>'
b+=f'<text x="{xs[16]-4}" y="{Y(.80)-6}" fill="#555" text-anchor="end">blind ceiling [SC]</text>'
open(O+'fig1_budget.svg','w').write(svg(W,H,b))
# Fig 2
W,H=340,230; x0,y0,x1,y1=50,20,320,185
Y=lambda v: y1-(y1-y0)*v
b=''
for v in (0,0.25,0.5,0.75,1.0):
    b+=f'<line x1="{x0}" x2="{x1}" y1="{Y(v)}" y2="{Y(v)}" stroke="#ddd"/><text x="{x0-6}" y="{Y(v)+4}" text-anchor="end">{v:.2f}</text>'
ranks=['1','2','3','4+']; op=[63/72,21/72,9/72,2/360]; bk=[29/72,7/72,5/72,52/360]
lab_o=['63/72','21/72','9/72','2/360']; lab_b=['29/72','7/72','5/72','52/360']
gw=(x1-x0)/4
for i,r in enumerate(ranks):
    gx=x0+i*gw+12
    for j,(v,c,l) in enumerate([(op[i],'#1f5fa8',lab_o[i]),(bk[i],'#e08e2b',lab_b[i])]):
        bx=gx+j*26
        b+=f'<rect x="{bx}" y="{Y(v)}" width="24" height="{y1-Y(v)}" fill="{c}"/><text x="{bx+12}" y="{Y(v)-3}" text-anchor="middle" font-size="8">{l}</text>'
    b+=f'<text x="{gx+25}" y="{y1+14}" text-anchor="middle">rank {r}</text>'
b+=f'<text x="{(x0+x1)/2}" y="{H-8}" text-anchor="middle">candidate\'s proxy rank (SAE-view effect)</text>'
b+=f'<text transform="translate(12,{(y0+y1)/2}) rotate(-90)" text-anchor="middle">P(isolated on exact logits)</text>'
b+=f'<rect x="{x1-118}" y="{y0}" width="10" height="10" fill="#1f5fa8"/><text x="{x1-104}" y="{y0+9}">Open-8 (proxy)</text>'
b+=f'<rect x="{x1-118}" y="{y0+15}" width="10" height="10" fill="#e08e2b"/><text x="{x1-104}" y="{y0+24}">BB-8 (no proxy)</text>'
open(O+'fig2_allocation.svg','w').write(svg(W,H,b))
# Fig 3 schematic
W,H=880,240
b='<text x="10" y="18" font-weight="bold">(a) Error-term trap</text>'
b+='<text x="10" y="38">proxy (SAE view):</text>'
b+='<rect x="130" y="28" width="180" height="12" fill="#e08e2b"/><text x="316" y="38">[decoy]  rank 1 (reads ~1.8x [main])</text>'
b+='<rect x="130" y="46" width="100" height="12" fill="#1f5fa8"/><text x="236" y="56">[main]  rank 2</text>'
b+='<text x="10" y="80">exact logits:</text>'
b+='<rect x="130" y="70" width="6" height="12" fill="#e08e2b"/><text x="142" y="80">[decoy] ~0</text>'
b+='<rect x="130" y="88" width="200" height="12" fill="#1f5fa8"/><text x="336" y="98">[main] carries the effect (via the SAE error term)</text>'
b+='<text x="10" y="128" font-weight="bold">(b) Two routes with 8 exact texts (schematic of Table 5 routes, not individual runs)</text>'
def row(y,label,cells,note):
    s=f'<text x="10" y="{y+13}">{label}</text>'
    for i,(t,c) in enumerate(cells):
        x=150+i*44; s+=f'<rect x="{x}" y="{y}" width="40" height="18" fill="{c}" stroke="#333" stroke-width="0.5"/><text x="{x+20}" y="{y+13}" text-anchor="middle" font-size="9">{t}</text>'
    s+=f'<text x="{150+8*44+6}" y="{y+13}" font-size="10">{note}</text>'; return s
D='#f5d0a6';M='#a9c4ea';N='#e6e6e6'
b+=row(140,'Wide first batch',[('decoy',D),('main',M),('trap',N),('trap',N),('other',N),('other',N),('other',N),('other',N)],'one burst; [decoy] refuted, [main] confirmed: pass (25/26)')
b+=row(170,'[decoy]-only batch',[('decoy',D),('trap',N),('other',N),('other',N),('other',N),('other',N),('other',N),('other',N)],'one burst; [decoy] refuted with 0 texts left: answers none')
b+='<text x="150" y="212" font-size="9">Each cell is one exact text; "decoy"/"main" = text isolating that candidate on the trap probe (often a sample-base flip); "trap" = other texts on the trap probe;</text>'
b+='<text x="150" y="224" font-size="9">"other" = texts on non-hard probes. All texts are sent before any result returns. Counts: 47 timed development runs with the proxy.</text>'
open(O+'fig3_trap_routes.svg','w').write(svg(W,H,b))
print('ok')
