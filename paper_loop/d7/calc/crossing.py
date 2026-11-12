import numpy as np, math
open8=[4,3,4,4,4,4]; bb8=[0,1,1,3,0,1]; bb16=[4,3,2,3,2,2]; bb64=[4,4,4,4,4,4]
def fit(it):
    x=np.array([3.,4.,6.]); y=np.array([sum(arr[i] for i in it) for arr in (bb8,bb16,bb64)],float); n=np.full(3,4.*len(it))
    t=np.array([-5.,1.5])
    for _ in range(200):  # Newton with ridge for separation
        p=1/(1+np.exp(-(t[0]+t[1]*x))); W=n*p*(1-p)
        X=np.stack([np.ones(3),x],1); g=X.T@(y-n*p)-1e-3*t; H=X.T@(X*W[:,None])+1e-3*np.eye(2)
        t=t+np.linalg.solve(H,g)
    return t
def cross(it):
    a,b=fit(it); tg=min(sum(open8[i] for i in it)/(4*len(it)),0.995)
    return 2**((math.log(tg/(1-tg))-a)/b) if b>0 else np.inf
a,b=fit(range(6)); print('fit a=%.3f b=%.3f equiv=%.1f'%(a,b,cross(range(6))))
for B in [8,16,24,32,48,64]: print(B, round(1/(1+math.exp(-(a+b*math.log2(B)))),3))
rng=np.random.default_rng(1); bs=np.array([cross(list(rng.integers(0,6,6))) for _ in range(4000)])
print('item bootstrap pct 2.5/50/97.5', np.percentile(bs,[2.5,50,97.5]).round(1))
def fisher2(a,b,c,d):
    from math import comb
    n=a+b+c+d; r1=a+b; c1=a+c
    def pr(x): return comb(r1,x)*comb(n-r1,c1-x)/comb(n,c1)
    p0=pr(a); return sum(pr(x) for x in range(max(0,c1-(n-r1)),min(r1,c1)+1) if pr(x)<=p0*(1+1e-9))
print('Open8 vs BB16 fisher', round(fisher2(23,1,16,8),4))
