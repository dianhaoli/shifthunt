import itertools, math
from functools import lru_cache
from math import comb
class binom:
    @staticmethod
    def pmf(x,n,p): return comb(n,x)*p**x*(1-p)**(n-x)
class hypergeom:
    @staticmethod
    def pmf(x,N,K,n): return comb(K,x)*comb(N-K,n-x)/comb(N,n)


def cond_dist(strata):
    # strata: list of (n1, n0, m) m = total successes; distribution of sum of X1 (treatment successes)
    dist = {0:1.0}
    for n1,n0,m in strata:
        lo=max(0,m-n0); hi=min(n1,m)
        new={}
        for s,p in dist.items():
            for x in range(lo,hi+1):
                q=hypergeom.pmf(x,n1+n0,m,n1)
                new[s+x]=new.get(s+x,0)+p*q
        dist=new
    return dist

def pval(x1s, x0s, n1s, n0s, mid=False):
    strata=[(n1,n0,a+b) for a,b,n1,n0 in zip(x1s,x0s,n1s,n0s)]
    d=cond_dist(strata); t=sum(x1s)
    p=sum(v for k,v in d.items() if k>t)
    p+= d.get(t,0)*(0.5 if mid else 1)
    return p

def outcomes(ns, ps):
    ranges=[range(n+1) for n in ns]
    for xs in itertools.product(*ranges):
        pr=1.0
        for x,n,p in zip(xs,ns,ps): pr*=binom.pmf(x,n,p)
        yield xs,pr

def power(ns, p1, p0, alpha=0.05, mid=False):
    pw=0
    o0=list(outcomes(ns,p0)); o1=list(outcomes(ns,p1))
    for x1,pr1 in o1:
        for x0,pr0 in o0:
            if pr1*pr0<1e-12: continue
            if pval(x1,x0,ns,ns,mid)<=alpha: pw+=pr1*pr0
    return pw

def wilson(x,n,z):
    p=x/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return c-h,c+h

def newcombe_ub(x1,n1,x0,n0,z=1.6449):
    p1=x1/n1;p0=x0/n0
    l1,u1=wilson(x1,n1,z); l0,u0=wilson(x0,n0,z)
    return p1-p0+math.sqrt((u1-p1)**2+(p0-l0)**2)

def p_bound(ns, pk, p0, thr=0.30):
    # P(UB of pooled diff < thr), pooled counts (equal allocation so pooled = weighted)
    N=sum(ns); tot=0
    o0=list(outcomes(ns,p0)); o1=list(outcomes(ns,pk))
    for x1,pr1 in o1:
        for x0,pr0 in o0:
            if newcombe_ub(sum(x1),N,sum(x0),N)<thr: tot+=pr1*pr0
    return tot

if __name__=='__main__':
    designs={'48 (4/6/6)':(4,6,6),'30 (2/4/4)':(2,4,4),'12 (0/3/3)':(0,3,3)}
    scen_p0={'zero':(0,0,0),'pooled Haiku SAE 2/5,0/4,1/5':(0.4,0.0,0.2),'main-study 2/3,0/2,1/3':(2/3,0,1/3),'mild 0.2,0.05,0.1':(0.2,0.05,0.1)}
    scen_p1={'full .4/.8/.8':(0.4,0.8,0.8),'moderate .2/.4/.4':(0.2,0.4,0.4),'moderate2 .3/.6/.6':(0.3,0.6,0.6),'read-limited .6/.6/.6':(0.6,0.6,0.6),'Haiku pass|iso 0.6, ep411 .5':(0.5,0.6,0.6)}
    for dn,ns in designs.items():
        nn=tuple(n for n in ns if n>0)
        for pn,p0 in scen_p0.items():
            p0n=tuple(p for p,n in zip(p0,ns) if n>0)
            for qn,p1 in scen_p1.items():
                p1n=tuple(p for p,n in zip(p1,ns) if n>0)
                print(f"{dn:12s} | p0 {pn:32s} | p1 {qn:28s} | power {power(nn,p1n,p0n):.3f}  midp {power(nn,p1n,p0n,mid=True):.3f}")
