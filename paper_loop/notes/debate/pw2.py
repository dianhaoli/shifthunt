import random, math
from math import comb
def fisher_greater(a,n1,b,n2):
    # P(X>=a) hypergeometric, total successes a+b
    K=a+b; N=n1+n2
    tot=comb(N,K)
    return sum(comb(n1,x)*comb(n2,K-x) for x in range(a,min(n1,K)+1))/tot
random.seed(1)
def binom(n,p): return sum(random.random()<p for _ in range(n))
def power(n,p0,p1,sims=3000):
    k=0
    for _ in range(sims):
        a=binom(n,p1); b=binom(n,p0)
        k+= fisher_greater(a,n,b,n)<0.05
    return round(k/sims,2)
for n in (6,8,10,12,16):
    print(n,[(p0,p1,power(n,p0,p1)) for p0,p1 in [(0.05,0.8),(0.15,0.7),(0.25,0.7),(0.2,0.5)]])
def wilson(x,n,z):
    p=x/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (c-h)/d,(c+h)/d
def newc_hi(a,n1,b,n2,z=1.645):
    p1=a/n1;p2=b/n2;l1,u1=wilson(a,n1,z);l2,u2=wilson(b,n2,z)
    return p1-p2+math.sqrt((u1-p1)**2+(p2-l2)**2)
for n in (12,16):
    print(n,[(a,b,round(newc_hi(a,n,b,n),2)) for a,b in [(0,0),(1,1),(2,2),(3,3),(3,1)]])
