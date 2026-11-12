from math import comb
def fisher(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    p0=comb(n1,a)*comb(n2,c)/comb(N,k)
    s=0
    for x in range(max(0,k-n2),min(k,n1)+1):
        p=comb(n1,x)*comb(n2,k-x)/comb(N,k)
        if p<=p0*(1+1e-9): s+=p
    return s
import sys
for t in [(203,4,156,7),(25,1,5,16),(9,0,5,15),(23,1,5,83),(5,4,26,13),(16,24-16,23,1)]:
    print(t, fisher(*t))
