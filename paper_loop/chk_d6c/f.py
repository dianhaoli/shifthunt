from math import comb
def fisher(a,b,c,d):
    n1=a+b; n2=c+d; k=a+c; N=n1+n2
    def p(x): return comb(n1,x)*comb(n2,k-x)/comb(N,k)
    p0=p(a); lo=max(0,k-n2); hi=min(k,n1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
for name,t in [("gpt trap vs ord",(23,1,5,83)),("r2 open8 vs bb8",(21,51,7,65)),("r4",(2,358,52,308)),
 ("haiku listed",(14,2,42,6)),("haiku hyp fail",(2,14,6,42)),("haiku tested",(7,9,35,13)),("haiku acq fail",(6,10,5,43)),
 ("haiku trap vs O+S",(3,13,15,6)),("gpt vs claude r2",(23,1,17,19))]:
    print(name, fisher(*t))
print('--- within harness Haiku vs Opus+Sonnet (32)')
for name,t in [("listed",(14,2,27,5)),("hyp fail",(2,14,5,27)),("tested",(7,9,20,12)),("acq fail",(6,10,4,28)),
  ("main-only trap pass 3/8 vs 12/16",(3,5,12,4)),("trap r2 5/16 vs 12/20",(5,11,12,8)),("GPT14 vs Opus11",(14,2,11,5)),("haiku acq fail vs all others 13 runs?",(6,10,5,43))]:
    print(name, fisher(*t))
