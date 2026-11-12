import numpy as np
from scipy.stats import fisher_exact
rng=np.random.default_rng(1)
def power(n,p0,p1,sims=4000):
    k=0
    for _ in range(sims):
        a=rng.binomial(n,p1); b=rng.binomial(n,p0)
        p=fisher_exact([[a,n-a],[b,n-b]],alternative='greater')[1]
        k+=p<0.05
    return k/sims
for n in (6,8,10,12,16):
    print(n,[ (p0,p1,round(power(n,p0,p1),2)) for p0,p1 in [(0.05,0.8),(0.15,0.7),(0.25,0.7),(0.2,0.55)]])
# upper bound of diff (Newcombe hybrid score, one-sided 95%)
from statsmodels.stats.proportion import confint_proportions_2indep
for n in (12,16):
  for a,b in [(1,1),(2,2),(3,1),(3,3),(4,2)]:
    lo,hi=confint_proportions_2indep(a,n,b,n,method='newcomb',alpha=0.10)
    print(n,a,b,round(hi,3))
