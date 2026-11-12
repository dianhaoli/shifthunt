import sys; sys.path.insert(0,'../stat')
from power import power, pval, outcomes, newcombe_ub, binom
from math import comb
def bt(n,p,k,ge=True):
    return sum(binom.pmf(x,n,p) for x in (range(k,n+1) if ge else range(0,k+1)))
print("== Budget dose B=16, 12 runs ep413+415, isolation bands (<=4 thesis, >=9 scarcity)")
for p in [0.11,0.2,0.36,0.5,0.67,0.73,0.9,0.95]:
    print(f" iso true {p:.2f}: P(<=4)={bt(12,p,4,False):.3f} P(>=9)={bt(12,p,9):.3f}")
print("== skeptic NAME scarcity band >=9/12 if scarcity is the whole story: NAME = iso*read")
for iso in [0.95,1.0]:
    for rd in [0.6,0.76,0.9]:
        print(f" iso {iso} read {rd}: P(NAME>=9)={bt(12,iso*rd,9):.3f}")
# Historical control comparison for budget dose: exact one-sided Fisher vs 1/9 iso on ep413+415
def fisher1(x1,n1,x0,n0): return pval((x1,),(x0,),(n1,),(n0,))
for x in range(2,8): print(f" dose iso {x}/12 vs hist 1/9: p={fisher1(x,12,1,9):.3f}")
print("== Procedure vs Placebo, isolation primary, ep413+415 only, base 0.11")
for ns in [(8,8),(10,10),(9,9)]:
    for d in [0.2,0.3,0.45]:
        print(f" ns {ns} +{d}: power {power(ns,(0.11+d,)*2,(0.11,)*2):.3f}")
print("== with ep411 2/7/7, base iso .8/.0/.2")
for d in [0.3,0.45]:
    p1=(min(1,.8+d*0.25),0+d,.2+d)
    print(f" 2/7/7 +{d}: power {power((2,7,7),p1,(.8,0,.2)):.3f}")
print("== Ceiling iso 0.95 vs 0.11, ep413+415")
for ns in [(3,3),(4,4),(6,6)]:
    print(f" ns {ns}: power {power(ns,(0.95,0.95),(0.11,0.11)):.3f}  (realistic .85: {power(ns,(0.85,0.85),(0.11,0.11)):.3f})")
