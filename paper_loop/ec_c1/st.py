from math import comb
def fisher(a,b,c,d):
    n1=a+b;n2=c+d;k=a+c;N=n1+n2
    p=lambda x: comb(n1,x)*comb(n2,k-x)/comb(N,k)
    p0=p(a); lo=max(0,k-n2); hi=min(k,n1)
    two=sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
    gr=sum(p(x) for x in range(a,hi+1)); ls=sum(p(x) for x in range(lo,a+1))
    return two,gr,ls
