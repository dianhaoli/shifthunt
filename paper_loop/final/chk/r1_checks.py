# Polish round 1: cheap read-only checks on numbers already in the paper.
from math import comb
def fisher2(a,b,c,d):
    # two-sided Fisher exact for [[a,b],[c,d]]
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): return comb(c1,x)*comb(n-c1,r1-x)/comb(n,r1)
    p0=p(a); lo=max(0,r1-(n-c1)); hi=min(r1,c1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
print('C1 traps only, GPT Open-8 11/12 vs BB-8 2/12: p =', fisher2(11,1,2,10))
print('C1 two-part only 12/12 vs 4/12: p =', fisher2(12,0,4,8))
print('C10 GPT 17/18 vs Claude 9/29 (both in first batch): p =', fisher2(17,1,9,20))
print('C10 literal runner-up first, Claude up to 11/29: p =', fisher2(17,1,11,18))
# item-level trap C1 (Appendix E): trap items Open-8 vs BB-8 = 4/4 v 0/4, 3/4 v 1/4, 4/4 v 1/4 -> 3/3 positive
print('item-level sign test, 3/3 positive: two-sided p =', 2*0.5**3)
# judge errors on hard slot: false credit 53 + false blame 32 = 85; omissions 41
print('omissions share of judge hard-slot errors: 41/85 =', round(41/85,3))
# Block 1 judge-implied (pooled GPT+Haiku), from judge.json hard_by_access
cert={'bb8':11,'open8':28,'bb64':32}; fb={'bb8':7,'open8':5,'bb64':12}; fc={'bb8':16,'open8':7,'bb64':4}
J={k:cert[k]-fb[k]+fc[k] for k in cert}; print('judge-implied of 36:',J)
print('certified budget effect', round((32-11)/36,3), 'judge', round((J['bb64']-J['bb8'])/36,3))
