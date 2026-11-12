import random
# hard slots: certified pass 146 (judge fail 32), certified fail 68 (judge pass 53)
cells=[(1,1)]*114+[(1,0)]*32+[(0,1)]*53+[(0,0)]*15
def kap(c):
    n=len(c); po=sum(a==b for a,b in c)/n
    pa=sum(a for a,_ in c)/n; pb=sum(b for _,b in c)/n
    pe=pa*pb+(1-pa)*(1-pb)
    return (po-pe)/(1-pe) if pe<1 else 0
random.seed(0)
print('kappa',round(kap(cells),4))
bs=sorted(kap(random.choices(cells,k=len(cells))) for _ in range(20000))
print('95% CI', round(bs[500],3), round(bs[19500],3))
