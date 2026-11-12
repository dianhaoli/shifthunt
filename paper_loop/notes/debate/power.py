import numpy as np
from math import comb
from itertools import product
def hyper_pmf(n1,n0,m):
    # successes in arm1 given total m
    lo=max(0,m-n0); hi=min(n1,m)
    return {k: comb(n1,k)*comb(n0,m-k)/comb(n1+n0,m) for k in range(lo,hi+1)}
def strat_p(x1s,ms,ns):
    dist={0:1.0}
    for n,m in zip(ns,ms):
        h=hyper_pmf(n,n,m); nd={}
        for a,pa in dist.items():
            for b,pb in h.items(): nd[a+b]=nd.get(a+b,0)+pa*pb
        dist=nd
    t=sum(x1s); return sum(p for k,p in dist.items() if k>=t)
class binom:
    @staticmethod
    def pmf(ks,n,p): return np.array([comb(n,int(k))*p**k*(1-p)**(n-k) for k in ks])
def power(ns,p0,p1,alpha=0.05):
    # exact enumeration
    pw=0.0
    ranges=[range(n+1) for n in ns]
    probs1=[binom.pmf(np.arange(n+1),n,p) for n,p in zip(ns,p1)]
    probs0=[binom.pmf(np.arange(n+1),n,p) for n,p in zip(ns,p0)]
    # enumerate per stratum pairs
    import itertools
    cells=[[(x1,x0,probs1[i][x1]*probs0[i][x0]) for x1 in range(n+1) for x0 in range(n+1)] for i,n in enumerate(ns)]
    for combo in itertools.product(*cells):
        pr=np.prod([c[2] for c in combo])
        if pr<1e-12: continue
        x1s=[c[0] for c in combo]; ms=[c[0]+c[1] for c in combo]
        if strat_p(x1s,ms,ns)<=alpha: pw+=pr
    return pw
for ns,lab in [((4,6,6),'16/arm'),((2,4,4),'10/arm'),((0,6,6),'no-raise ep413/415 x3? use (3,3)')]:
    pass
designs={'16/arm 4/6/6':(4,6,6),'10/arm 2/4/4':(2,4,4),'no raise 3/3 on ep413,ep415':(3,3)}
for lab,ns in designs.items():
    k=len(ns)
    full=(0.4,0.8,0.8)[-k:]; mod=(0.2,0.5,0.5)[-k:]
    for p0name,p0 in [('placebo 0',(0,0,0)[-k:]),('placebo 0.1',(0.1,0.1,0.1)[-k:]),('placebo 0.2',(0.2,0.2,0.2)[-k:])]:
        print(lab,p0name,'full',round(power(ns,p0,full),3),'moderate(.2/.5/.5)',round(power(ns,p0,mod),3))
