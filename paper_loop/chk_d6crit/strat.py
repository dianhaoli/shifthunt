# Agent-stratified exact test of route (S1 = decoy+main in first batch) vs pass, development trap runs (CALC/10)
# strata: (S1 pass, S1 fail, other pass, other fail)
from math import comb
from itertools import product
S={'gpt':(16,1,0,1),'haiku':(2,0,1,11),'opus':(3,0,2,2),'sonnet':(4,0,2,2)}
# exact conditional test: statistic = total S1 passes; conditional on all margins per stratum (hypergeometric each)
def hyper(a,b,c,d):
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    lo=max(0,c1-r2); hi=min(r1,c1)
    return {x: comb(r1,x)*comb(r2,c1-x)/comb(n,c1) for x in range(lo,hi+1)}
dists=[hyper(*v) for v in S.values()]
tot={0:1.0}
for d in dists:
    new={}
    for t,p in tot.items():
        for x,q in d.items(): new[t+x]=new.get(t+x,0)+p*q
    tot=new
obs=sum(v[0] for v in S.values())
mean=sum(t*p for t,p in tot.items())
p_one=sum(p for t,p in tot.items() if t>=obs)
p_two=sum(p for t,p in tot.items() if p<=tot[obs]*(1+1e-9))
print('observed S1 passes',obs,'expected',round(mean,2),'one-sided',p_one,'two-sided',p_two)
# MH odds ratio
num=sum(a*d/(a+b+c+d) for a,b,c,d in S.values()); den=sum(b*c/(a+b+c+d) for a,b,c,d in S.values())
print('MH OR', num/den if den else 'inf', num, den)
# excluding GPT
S2={k:v for k,v in S.items() if k!='gpt'}
dists=[hyper(*v) for v in S2.values()]
tot={0:1.0}
for d in dists:
    new={}
    for t,p in tot.items():
        for x,q in d.items(): new[t+x]=new.get(t+x,0)+p*q
    tot=new
obs=sum(v[0] for v in S2.values())
print('Claude only stratified: obs',obs,'one-sided',sum(p for t,p in tot.items() if t>=obs),'two-sided',sum(p for t,p in tot.items() if p<=tot[obs]*(1+1e-9)))
# Claude pooled
a=sum(v[0] for v in S2.values()); b=sum(v[1] for v in S2.values()); c=sum(v[2] for v in S2.values()); d=sum(v[3] for v in S2.values())
print('Claude pooled', a,b,c,d)
def fisher(a,b,c,d):
    h=hyper(a,b,c,d); p0=h[a]; return sum(p for p in h.values() if p<=p0*(1+1e-9))
print('Claude pooled fisher', fisher(a,b,c,d))
for k,v in S.items(): print(k, v, fisher(*v))
# Item-level sign test, GPT Block 1 per item (SUMMARY.md §3): Open-8 vs BB-8, BB-64 vs BB-8
o8=[4,3,4,4,4,4]; b8=[0,1,1,3,0,1]; b64=[4]*6
for name,a in [('Open8>BB8',o8),('BB64>BB8',b64)]:
    k=sum(x>y for x,y in zip(a,b8)); print(name,'items higher',k,'/6; two-sided sign p',min(1,2*sum(comb(6,j) for j in range(k,7))/64))
