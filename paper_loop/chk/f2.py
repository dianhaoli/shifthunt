from math import comb
def fisher(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    def p(x): return comb(n1,x)*comb(n2,k-x)/comb(N,k)
    p0=p(a); lo=max(0,k-n2); hi=min(k,n1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-7))
for t in [(3,13,15,6),(3,11,12,4),(5,11,12,8),(23,1,17,19),(3,5,12,4)]:
    print(t, fisher(*t))
