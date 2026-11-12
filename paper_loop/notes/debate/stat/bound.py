from power import *
ns=(4,6,6)
print("P(Newcombe one-sided 95% UB of Knowledge-Placebo < 0.30), 16/arm, pooled over items")
for pn,p0 in {'zero':(0,0,0),'mild .2/.05/.1':(0.2,0.05,0.1),'pooled Haiku .4/0/.2':(0.4,0,0.2),'main .67/0/.33':(2/3,0,1/3)}.items():
    for dn,d in {'K=P (no effect)':0.0,'K=P+0.1':0.1,'K=P+0.3':0.3}.items():
        pk=tuple(min(1,p+d) for p in p0)
        print(f"  p0 {pn:22s} {dn:16s} P(UB<0.30)={p_bound(ns,pk,p0):.3f}")
# what diff observed allows UB<0.30
print("UB table, n=16 vs 16:")
for x0 in range(0,6):
    print('  placebo',x0,'/16:', ' '.join(f"K={x1}:{newcombe_ub(x1,16,x0,16):.2f}" for x1 in range(0,7)))
print("n=48 vs 48 (if Knowledge vs Placebo had 48/arm):")
for x0 in (0,5,10):
    print('  placebo',x0,'/48:', ' '.join(f"K={x1}:{newcombe_ub(x1,48,x0,48):.2f}" for x1 in range(x0,x0+12,2)))
