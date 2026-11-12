from math import comb
def hyp(N,K,n,x): return comb(K,x)*comb(N-K,n-x)/comb(N,n)
def fisher(a,b,c,d):
    N=a+b+c+d; n1=a+b; K=a+c
    lo=max(0,n1-(N-K)); hi=min(n1,K)
    ps={x:hyp(N,K,n1,x) for x in range(lo,hi+1)}
    return sum(p for p in ps.values() if p<=ps[a]*(1+1e-9))
print('decoy-first 14/17 vs 2/30', fisher(14,3,2,28))
print('11/17 vs 2/30', fisher(11,6,2,28))
print('S1 25/26 vs 5/21', fisher(25,1,5,16))
strata={'gpt':(16,1,0,1),'haiku':(2,0,1,11),'opus':(3,0,2,2),'sonnet':(4,0,2,2)}
tot={0:1.0};obs=0
for k,(a,b,c,d) in strata.items():
    N=a+b+c+d;n1=a+b;K=a+c
    lo=max(0,n1-(N-K));hi=min(n1,K)
    dd={x:hyp(N,K,n1,x) for x in range(lo,hi+1)}
    new={}
    for s,p in tot.items():
        for x,q in dd.items(): new[s+x]=new.get(s+x,0)+p*q
    tot=new;obs+=a
pobs=tot[obs]
print('agent-stratified exact two-sided',sum(p for p in tot.values() if p<=pobs*(1+1e-9)),'one-sided',sum(p for s,p in tot.items() if s>=obs))
# Claude only
tot={0:1.0};obs=0
for k in ['haiku','opus','sonnet']:
    a,b,c,d=strata[k];N=a+b+c+d;n1=a+b;K=a+c
    lo=max(0,n1-(N-K));hi=min(n1,K)
    dd={x:hyp(N,K,n1,x) for x in range(lo,hi+1)}
    new={}
    for s,p in tot.items():
        for x,q in dd.items(): new[s+x]=new.get(s+x,0)+p*q
    tot=new;obs+=a
pobs=tot[obs]
print('Claude-only stratified two-sided',sum(p for p in tot.values() if p<=pobs*(1+1e-9)))
print('Claude pooled S1 9/9 vs 5/20', fisher(9,0,5,15))
