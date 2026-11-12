import sys; sys.path.insert(0,'../stat')
from power import pval, outcomes
# P 10/10, Pr 10/10, C 4/4 ; isolation; base .11
nsP=(10,10); nsC=(4,4)
def sim(pc,ppr,p0=(0.11,0.11)):
    oP=list(outcomes(nsP,p0)); oR=list(outcomes(nsP,ppr)); oC=list(outcomes(nsC,pc))
    # need pval with unequal n: pval(x1s,x0s,n1s,n0s)
    fs=holm=0; cfail=0
    for xp,pp in oP:
        for xc,pcc in oC:
            pC=pval(xc,xp,nsC,nsP)
            for xr,pr in oR:
                w=pp*pcc*pr
                if w<1e-10: continue
                pR=pval(xr,xp,nsP,nsP)
                if pC<=0.05 and pR<=0.05: fs+=w
                lo,hi=sorted([pC,pR])
                if lo<=0.025 and hi<=0.05: holm+=w
                elif lo<=0.025 and pR==lo: holm+=w
                if pC>0.05: cfail+=w
    return fs,holm,cfail
for pc in [(0.95,0.95),(0.85,0.85)]:
    for d in [0.0,0.3,0.45]:
        fs,h,cf=sim(pc,(0.11+d,)*2)
        print(f"Ceil {pc[0]} Proc +{d}: P(Proc rejected) fixed-seq {fs:.3f} Holm {h:.3f}; P(gate fails) {cf:.3f}")
