from math import comb, sqrt
def wilson(k,n,z=1.959964):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
def w(k,n): lo,hi=wilson(k,n); return f"{k}/{n}={k/n:.3f} [{lo:.2f},{hi:.2f}]"
def fisher(a,b,c,d):
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    def p(x): return comb(r1,x)*comb(r2,c1-x)/comb(n,c1)
    p0=p(a); lo=max(0,c1-r2); hi=min(r1,c1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-7))
for k,n in [(203,207),(156,163),(176,176),(192,192),(30,31),(39,39),(25,26),(5,21),(3,16),(13,23),(26,26),(8,19),(11,19),(24,32),(32,32),(35,48),(7,16),(9,12),(31,47),(24,49)]:
    print(w(k,n))
print("tested main larger vs haiku", fisher(35,13,7,9))
print("listed larger vs haiku", fisher(42,6,14,2))
print("formed 45/56 vs 0/8", fisher(45,11,0,8))
print("read proxy vs BB", fisher(203,4,156,7))
print("trap tested 27/31 vs 3/16", fisher(27,4,3,13))
print("two-part 26/26 vs 13/23", fisher(26,0,13,10))
print("route 25/1 vs 5/16", fisher(25,1,5,16))
print("main got test 40/42 vs 5/22", fisher(40,2,5,17))
print("haiku A-stage fails 6/16 vs larger 5/48", fisher(6,10,5,43))
print("H-stage fails haiku 2/16 vs larger 6/48", fisher(2,14,6,42))
