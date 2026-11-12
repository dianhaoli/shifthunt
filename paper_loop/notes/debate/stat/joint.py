from power import outcomes, pval, newcombe_ub
def joint(ns,pC,pK,p0,thr=0.30):
    oP=list(outcomes(ns,p0)); oC=list(outcomes(ns,pC)); oK=list(outcomes(ns,pK)); N=sum(ns)
    gate=0; both=0; krej=0; notdet=0
    for xP,a in oP:
        if a<1e-12: continue
        g=sum(c for xC,c in oC if c>1e-12 and pval(xC,xP,ns,ns)<=0.05)
        ub=sum(k for xK,k in oK if newcombe_ub(sum(xK),N,sum(xP),N)<thr)
        kr=sum(k for xK,k in oK if k>1e-12 and pval(xK,xP,ns,ns)<=0.05)
        gate+=a*g; both+=a*g*ub; krej+=a*g*kr
    return gate,both,krej
ns=(4,6,6)
for pn,p0 in {'zero':(0,0,0),'pooled':(0.4,0,0.2),'main':(2/3,0,1/3)}.items():
    for d in (0,0.1,0.3):
        pK=tuple(min(1,p+d) for p in p0)
        g,b,k=joint(ns,(0.475,0.76,0.76),pK,p0)
        print(f"named p0={pn:6s} Kdelta={d}: P(gate)={g:.2f} P(gate & 'no large rescue')={b:.2f} P(gate & K rescue)={k:.2f} P(gate & 'not detected')={g-b-k:.2f}")
