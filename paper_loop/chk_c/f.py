from math import comb
def p2(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    def pr(x): return comb(n1,x)*comb(n2,k-x)/comb(N,k)
    po=pr(a); lo=max(0,k-n2); hi=min(k,n1)
    return sum(pr(x) for x in range(lo,hi+1) if pr(x)<=po*(1+1e-9))
print('claude S1 vs other', p2(9,0,5,15))
print('all', p2(25,1,5,16))
