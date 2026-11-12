# Read-only: bootstrap interval for the GPT Open-8 vs BB-64 break-even gold price (exploratory).
import csv, numpy as np
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results/blackbox_1112'
rows=[r for r in csv.DictReader(open(G+'/rows_r1112.csv')) if r['counted']=='1' and r['agent']=='gpt']
item_key=[k for k in rows[0].keys() if k in ('item','episode','ep','item_id')]
print('cols', list(rows[0].keys())[:40])
def arm(a): return [r for r in rows if r['arm']==a]
def be(o,b):
    a1=sum(float(r['usd']) for r in o)/max(1e-9,sum(float(r['name']) for r in o))
    b1=sum(float(r['pq_used']) for r in o)/max(1e-9,sum(float(r['name']) for r in o))
    a2=sum(float(r['usd']) for r in b)/max(1e-9,sum(float(r['name']) for r in b))
    b2=sum(float(r['pq_used']) for r in b)/max(1e-9,sum(float(r['name']) for r in b))
    return (a1-a2)/(b2-b1)
O,B=arm('open8'),arm('bb64')
print('point', round(be(O,B),5))
rng=np.random.default_rng(1112)
ik=item_key[0] if item_key else None
print('item key', ik)
res=[];resi=[]
for _ in range(10000):
    o=[O[i] for i in rng.integers(0,len(O),len(O))]; b=[B[i] for i in rng.integers(0,len(B),len(B))]
    res.append(be(o,b))
    if ik:
        items=sorted(set(r[ik] for r in O)); pick=rng.choice(items,len(items))
        o=[r for it in pick for r in O if r[ik]==it]; b=[r for it in pick for r in B if r[ik]==it]
        resi.append(be(o,b))
print('run bootstrap 95%%: %.4f %.4f'%tuple(np.percentile(res,[2.5,97.5])))
if resi: print('item bootstrap 95%%: %.4f %.4f'%tuple(np.percentile(resi,[2.5,97.5])))
