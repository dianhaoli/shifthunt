from math import comb
def hyper(a,b,c,d):
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    lo=max(0,c1-r2); hi=min(r1,c1)
    return {x: comb(r1,x)*comb(r2,c1-x)/comb(n,c1) for x in range(lo,hi+1)}
def fisher(a,b,c,d):
    h=hyper(a,b,c,d); p0=h[a]; return sum(p for p in h.values() if p<=p0*(1+1e-9))
print('haiku 3/16 vs OS 15/21', fisher(3,13,15,6))
print('haiku main+heldout 3/10 vs OS 15/21', fisher(3,7,15,6))
print('haiku rank2 5/16 vs 12/20', fisher(5,11,12,8))
print('C9 unconditional 1/108 vs 24/108', fisher(1,107,24,84))
print('C9 GPT 0/71 vs 15/51', fisher(0,71,15,36))
print('C9 Haiku 1/27 vs 9/24', fisher(1,26,9,15))
print('C9 1/98 vs 24/75', fisher(1,97,24,51))
print('C3 trap tested 27/31 vs not 3/16', fisher(27,4,3,13))
print('C3 BB trap 23/24 vs 8/24', fisher(23,1,8,16))
# stratified exact for C9 by agent
def strat(S):
    tot={0:1.0}
    for v in S:
        d=hyper(*v); new={}
        for t,p in tot.items():
            for x,q in d.items(): new[t+x]=new.get(t+x,0)+p*q
        tot=new
    obs=sum(v[0] for v in S)
    return obs, sum(p for t,p in tot.items() if t<=obs), sum(p for t,p in tot.items() if p<=tot[obs]*(1+1e-9))
print('C9 agent-strat (Open8 wrong, ok, BB8 wrong, ok)', strat([(0,71,15,36),(1,26,9,15)]))
