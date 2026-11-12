import numpy as np
from math import comb
# hard slots: cert pass 146 (judge pass 114, judge fail 32); cert fail 68 (judge pass 53, judge fail 15)
a,b,c,d=114,32,53,15  # (cp,jp),(cp,jf),(cf,jp),(cf,jf)
n=a+b+c+d
def kap(a,b,c,d):
    n=a+b+c+d; po=(a+d)/n; pe=((a+b)/n)*((a+c)/n)+((c+d)/n)*((b+d)/n); return (po-pe)/(1-pe),po,pe
print(kap(a,b,c,d))
rng=np.random.default_rng(0); p=np.array([a,b,c,d])/n
ks=[kap(*rng.multinomial(n,p))[0] for _ in range(20000)]
print('boot95',np.percentile(ks,[2.5,97.5]))
po,pe=kap(a,b,c,d)[1:]
se=np.sqrt(po*(1-po)/(n*(1-pe)**2)); print('asym se',se, 'ci',kap(a,b,c,d)[0]-1.96*se,kap(a,b,c,d)[0]+1.96*se)
print('always pass agreement',146/214)
# GPT width run-clustered sign-test bound: >=18 favor vs <=1 against
def sign2(k,nn): return min(1,2*sum(comb(nn,i) for i in range(0,k+1))/2**nn)
print('sign bound',sign2(1,19), sign2(0,18))
# fisher 23/24 vs 5/88
from scipy.stats import fisher_exact
print(fisher_exact([[23,1],[5,83]]))
print('SAE vs BB false credit',fisher_exact([[28,5],[25,10]]))
