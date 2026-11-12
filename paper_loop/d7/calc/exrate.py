import csv, sys, json, math, random
import numpy as np
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results/blackbox_1112'
rows=[r for r in csv.DictReader(open(G+'/rows_r1112.csv')) if r['counted']=='1']
from collections import defaultdict
agg=defaultdict(lambda: defaultdict(list))
for r in rows:
    k=(r['agent'],r['arm'])
    for c in ['name','pq_used','pq_hard','usd','tokens_out']:
        agg[k][c].append(float(r[c]) if r[c] else float('nan'))
for k,v in sorted(agg.items()):
    n=len(v['name'])
    print(k,n,'NAME',sum(v['name']),'pq_used mean %.2f'%np.mean(v['pq_used']),'min',min(v['pq_used']),'max',max(v['pq_used']),'usd/run %.3f'%np.nanmean(v['usd']))
# break-even price per gold text, GPT: cost per pass incl. gold
def cpp(arm,p):
    v=agg[('gpt',arm)]
    return (sum(v['usd'])+p*sum(v['pq_used']))/sum(v['name'])
for p in [0,0.01,0.05,0.1,0.5,1,5]:
    print('p=%g'%p, {a:round(cpp(a,p),3) for a in ['open8','bb8','bb64']})
# solve open8 == bb64
vo=agg[('gpt','open8')]; vb=agg[('gpt','bb64')]
a1=sum(vo['usd'])/sum(vo['name']); b1=sum(vo['pq_used'])/sum(vo['name'])
a2=sum(vb['usd'])/sum(vb['name']); b2=sum(vb['pq_used'])/sum(vb['name'])
print('gold per pass open8 %.2f bb64 %.2f; usd per pass %.3f %.3f; breakeven p=%.4f'%(b1,b2,a1,a2,(a1-a2)/(b2-b1)))
