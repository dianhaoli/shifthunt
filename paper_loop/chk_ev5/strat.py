from math import comb
def hyp(a,b,c,d):
    # table [[a,b],[c,d]] rows: both-first (pass,fail), other(pass,fail); distribution of a given margins
    r1=a+b; c1=a+c; n=a+b+c+d
    lo=max(0,r1-(n-c1)); hi=min(r1,c1)
    return {k: comb(c1,k)*comb(n-c1,r1-k)/comb(n,r1) for k in range(lo,hi+1)}, a
def strat(tabs):
    dist={0:1.0}; obs=0
    for t in tabs:
        h,a=hyp(*t); obs+=a
        nd={}
        for s,p in dist.items():
            for k,q in h.items(): nd[s+k]=nd.get(s+k,0)+p*q
        dist=nd
    exp=sum(s*p for s,p in dist.items())
    return obs, exp, sum(p for s,p in dist.items() if s>=obs)
all4=[(16,1,0,1),(3,0,2,2),(4,0,2,2),(2,0,1,11)]
print('all', strat(all4)); print('claude', strat(all4[1:]))
def fisher_two(a,b,c,d):
    h,_=hyp(a,b,c,d); p0=h[a]; return sum(p for p in h.values() if p<=p0*(1+1e-9))
print('26/26 vs 13/23', fisher_two(26,0,13,10))
print('Open8 vs BB16', fisher_two(23,1,16,8))
print('passes trap', fisher_two(25,1,5,16))
print('latent either claude', fisher_two(10,6,21,11), 'latent_examples only claude', fisher_two(5,4,26,13))
