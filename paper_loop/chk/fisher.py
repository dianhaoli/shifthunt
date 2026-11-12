from math import comb
def fisher(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    def p(x): return comb(n1,x)*comb(n2,k-x)/comb(N,k)
    p0=p(a); lo=max(0,k-n2); hi=min(k,n1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
for name,t in [("trap tested vs not",(27,4,3,13)),("2part",(26,0,13,10)),("routes",(25,1,5,16)),
 ("haiku traps",(3,13,15,6)),("haiku r2",(5,11,12,8)),("gpt vs claude r2",(23,1,17,19)),("gpt trap vs ord",(23,1,5,83)),("GPT14 vs Haiku8",(14,2,8,8)),("GPT14 v Opus11",(14,2,11,5))]:
    print(name, fisher(*t))
print("---balanced")
for name,t in [("main+ho pass H3/10 vs OS15/21",(3,7,15,6)),("main only pass 3/8 vs 12/16",(3,5,12,4)),
 ("main+ho r2 3/10 vs 12/20",(3,7,12,8)),("main r2 3/8 vs 9/15",(3,5,9,6)),("haiku SAE traps vs O+S main+open?",(3,11,12,4))]:
    print(name, fisher(*t))
print("---claude-only routes", fisher(9,0,5,15))
import math
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return ((c-r)/d,(c+r)/d)
print(wilson(203,207), wilson(9,9), wilson(5,20))
