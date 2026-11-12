from math import comb
def hyper(a,b,c,d):
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    lo=max(0,c1-r2); hi=min(r1,c1)
    return {x: comb(r1,x)*comb(r2,c1-x)/comb(n,c1) for x in range(lo,hi+1)}
def fisher(a,b,c,d):
    h=hyper(a,b,c,d); p0=h[a]; return sum(p for p in h.values() if p<=p0*(1+1e-9))
def pmf(k,n,p): return comb(n,k)*p**k*(1-p)**(n-k)
n=16
sig={(x,y): fisher(x,n-x,y,n-y)<0.05 for x in range(n+1) for y in range(n+1)}
def power(p1,p2):
    return sum(pmf(x,n,p1)*pmf(y,n,p2) for x in range(n+1) for y in range(n+1) if sig[(x,y)])
for p1 in [0.875]:
    for p2 in [i/100 for i in range(20,85,5)]:
        print(p1,p2,round(power(p1,p2),3))
