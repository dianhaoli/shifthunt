from math import comb, sqrt
def fisher(a,b,c,d):
    # rows: [a,b],[c,d]; two-sided sum of probs <= observed
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    def p(x): return comb(r1,x)*comb(r2,c1-x)/comb(n,c1)
    lo=max(0,c1-r2); hi=min(r1,c1); po=p(a)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=po*(1+1e-7))
def wilson(k,n,z=1.959963984540054):
    ph=k/n; den=1+z*z/n; c=(ph+z*z/(2*n))/den; h=z*sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return round(c-h,2),round(c+h,2)
