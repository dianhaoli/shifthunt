from math import comb
def fisher(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    p=lambda x: comb(n1,x)*comb(n2,k-x)/comb(N,k)
    p0=p(a); return sum(p(x) for x in range(max(0,k-n2),min(k,n1)+1) if p(x)<=p0*(1+1e-9))
print('NOV heldout routes excl Opus5.5: wide 6/0 vs other 0/7', fisher(6,0,0,7))
print('worst case Opus5.5 both other-route passes: 6/0 vs 2/7', fisher(6,0,2,7))
print('best case: 8/0 vs 0/7', fisher(8,0,0,7))
print('Opus+Sonnet other routes 4/8 vs wide 7/7', fisher(7,0,4,4))
print('Haiku 3/14 vs O+S 12/16', fisher(3,11,12,4))
