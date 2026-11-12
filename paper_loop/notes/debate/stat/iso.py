from power import *
from math import comb
ns=(4,6,6)
print("--- Ceiling vs Placebo, NAMED, realistic p1 = 0.95*read(.5,.8,.8)")
p1=(0.475,0.76,0.76)
for pn,p0 in {'zero':(0,0,0),'pooled .4/0/.2':(0.4,0,0.2),'main .67/0/.33':(2/3,0,1/3)}.items():
    print(f"  p0 {pn:16s} power {power(ns,p1,p0):.3f}")
print("--- RANK-2 ISOLATED as outcome")
for pn,p0 in {'open8 1/0/0':(0.99,0.0,0.0),'pooled .8/0/.2':(0.8,0,0.2),'main .67?':(0.67,0,0.33)}.items():
    print(f"  Ceiling p1=.95 all, p0 {pn}: power {power(ns,(0.95,0.95,0.95),p0):.3f}")
    for d in (0.2,0.3,0.4):
        pk=tuple(min(1,p+d) for p in p0)
        print(f"     Knowledge +{d}: power {power(ns,pk,p0):.3f}")
    for dn,d in {'K=P':0.0,'K=P+.1':0.1,'K=P+.3':0.3}.items():
        pk=tuple(min(1,p+d) for p in p0)
        print(f"     P(UB<.30) {dn}: {p_bound(ns,pk,p0):.3f}")
print("--- NAMED Knowledge power (rescue test, ungated)")
for pn,p0 in {'zero':(0,0,0),'pooled .4/0/.2':(0.4,0,0.2)}.items():
    for d in (0.2,0.3,0.4):
        pk=tuple(min(1,p+d) for p in p0)
        print(f"  p0 {pn}: K +{d}: power {power(ns,pk,p0):.3f}")
# dilution: an isolation effect of +0.3 translates to named effect +0.3*read
print("--- dilution: isolation +0.3, read|iso .6 -> named +0.18; P(UB<.30) on named")
for pn,p0 in {'zero':(0,0,0),'pooled .4/0/.2':(0.4,0,0.2)}.items():
    pk=tuple(min(1,p+0.18) for p in p0)
    print(f"  p0 {pn}: P(UB<.30 on named)={p_bound(ns,pk,p0):.3f}")
# heterogeneity test 0/6 vs 3/8
def fisher2(a,n1,c,n2):
    m=a+c;N=n1+n2
    pmf=lambda x: comb(m,x)*comb(N-m,n1-x)/comb(N,n1)
    p0=pmf(a); return sum(pmf(x) for x in range(max(0,m-n2),min(n1,m)+1) if pmf(x)<=p0+1e-12)
print("Fisher 0/6 vs 3/8 two-sided:",round(fisher2(0,6,3,8),3))
# placebo vs historical
