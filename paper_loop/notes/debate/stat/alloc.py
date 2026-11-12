import itertools
from power import outcomes, pval, newcombe_ub, binom
def power2(n1s,n0s,p1,p0,alpha=0.05):
    o1=list(outcomes(n1s,p1)); o0=list(outcomes(n0s,p0)); pw=0
    for x1,a in o1:
        for x0,b in o0:
            if a*b<1e-12: continue
            if pval(x1,x0,n1s,n0s)<=alpha: pw+=a*b
    return pw
def pbound2(ns,pk,p0,thr=0.30):
    N=sum(ns); o1=list(outcomes(ns,pk)); o0=list(outcomes(ns,p0)); t=0
    for x1,a in o1:
        for x0,b in o0:
            if newcombe_ub(sum(x1),N,sum(x0),N)<thr: t+=a*b
    return t
def sub(ns,ps): return tuple(n for n in ns if n), tuple(p for n,p in zip(ns,ps) if n)
P0={'zero':(0,0,0),'pooled':(0.4,0,0.2)}
ISO0={'pooled iso':(0.8,0,0.2)}
C1=(0.475,0.76,0.76)
designs={
 'A plan 16/16/16 (4/6/6)':((4,6,6),(4,6,6),(4,6,6)),
 'B P18 K18 C12 (2/8/8,2/8/8,2/5/5)':((2,8,8),(2,8,8),(2,5,5)),
 'C drop ep411: P18 K18 C12 (0/9/9,0/9/9,0/6/6)':((0,9,9),(0,9,9),(0,6,6)),
 'D drop ep411, equal 16 (0/8/8)':((0,8,8),(0,8,8),(0,8,8)),
 'E $35: P12 K12 C6 (0/6/6,0/6/6,0/3/3)':((0,6,6),(0,6,6),(0,3,3)),
 'F $15: P6 K6 (0/3/3) no ceiling':((0,3,3),(0,3,3),None),
}
for name,(nP,nK,nC) in designs.items():
    out=[name]
    for pn,p0 in P0.items():
        if nC:
            a,b=sub(nC,C1); c,d=sub(nP,p0)
            out.append(f"Cpow[{pn}]={power2(a,c,b,d):.2f}")
        k,pk=sub(nK,tuple(min(1,x+0.3) for x in p0)); c,d=sub(nP,p0)
        out.append(f"K+.3pow[{pn}]={power2(k,c,pk,d):.2f}")
        ns,pp=sub(nP,p0); out.append(f"PUB<.3|K=P[{pn}]={pbound2(ns,pp,pp):.2f}")
    for pn,p0 in ISO0.items():
        k,pk=sub(nK,tuple(min(1,x+0.3) for x in p0)); c,d=sub(nP,p0)
        out.append(f"ISO K+.3pow={power2(k,c,pk,d):.2f}")
        ns,pp=sub(nP,p0); out.append(f"ISO PUB<.3|K=P={pbound2(ns,pp,pp):.2f}")
    print(' | '.join(out))
