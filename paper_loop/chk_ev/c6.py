from scipy.stats import fisher_exact
import numpy as np
print('decoy-first 14/17 vs 2/30', fisher_exact([[14,3],[2,28]]))
print('decoy-only first batch 11/17 vs 2/30', fisher_exact([[11,6],[2,28]]))
# strata by agent: (S1 pass, S1 fail, other pass, other fail)
strata={'gpt':(16,1,0,1),'haiku':(2,0,1,11),'opus':(3,0,2,2),'sonnet':(4,0,2,2)}
# exact conditional test: sum over strata of S1-pass count given margins; use permutation
from scipy.stats import hypergeom
import itertools
dists=[]
obs=0
for k,(a,b,c,d) in strata.items():
    n1=a+b; npass=a+c; N=a+b+c+d
    rv=hypergeom(N,npass,n1)
    lo=max(0,n1-(N-npass)); hi=min(n1,npass)
    dists.append({x:rv.pmf(x) for x in range(lo,hi+1)})
    obs+=a
# convolve
tot={0:1.0}
for dd in dists:
    new={}
    for s,p in tot.items():
        for x,q in dd.items(): new[s+x]=new.get(s+x,0)+p*q
    tot=new
pobs=tot[obs]
p2=sum(p for s,p in tot.items() if p<=pobs*(1+1e-9))
pone=sum(p for s,p in tot.items() if s>=obs)
print('stratified exact (agent) obs',obs,'two-sided',p2,'one-sided',pone)
