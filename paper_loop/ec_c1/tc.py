import csv,sys
from st import fisher
R=list(csv.DictReader(open(sys.argv[1])))
g=[r for r in R if r['agent']=='gpt' and r['counted']=='1']
def arm(a): return [r for r in g if r['arm']==a]
o,b,b64=arm('open8'),arm('bb8'),arm('bb64')
print(set(r['arm'] for r in g))
for a in (o,b,b64): print(len(a), sum(int(r['name']) for r in a), max(int(r['tokens_out']) for r in a), sorted(int(r['tokens_out']) for r in a)[-3:])
caps=sorted(set(int(r['tokens_out']) for r in o+b+b64))
def rate(a,c): return sum(int(r['name']) and int(r['tokens_out'])<=c for r in a)/len(a)
mx=max(int(r['tokens_out']) for r in o)
for c in [mx-1,mx]+[x for x in caps if x>=mx]:
  print(c, round(rate(o,c)-rate(b,c),3), round(rate(b64,c)-rate(o,c),3))
print(fisher(23,1,16,8))
print(2*0.5**6, 0.5**6)
