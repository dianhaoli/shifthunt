import random
def kappa(a,b,c,d):  # a=certP&jP, b=certP&jF, c=certF&jP, d=certF&jF
    n=a+b+c+d; po=(a+d)/n; pe=((a+b)*(a+c)+(c+d)*(b+d))/n/n
    return (po-pe)/(1-pe) if pe<1 else float('nan')
print('hard',kappa(114,32,53,15))
print('claude',kappa(41,11,35,7), 'gpt', kappa(94-21,21,18,8))
random.seed(1); cells=[0]*114+[1]*32+[2]*53+[3]*15; ks=[]
for _ in range(20000):
    s=[0,0,0,0]
    for x in random.choices(cells,k=214): s[x]+=1
    ks.append(kappa(*s))
ks.sort(); print(ks[int(.025*len(ks))], ks[int(.975*len(ks))])
