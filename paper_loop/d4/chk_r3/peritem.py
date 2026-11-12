import csv, collections
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results'
rows=list(csv.DictReader(open(f'{G}/cross_model_1103/rollouts.csv')))
rows=[r for r in rows if r['batch'] in ('b1','b2')]
print('main-study rows', len(rows))
items=sorted({r['episode'] for r in rows if r['hard_kind']=='trap'})
lab={e:'T'+'ABC'[i] for i,e in enumerate(items)}
c=collections.defaultdict(lambda:[0,0,0])
for r in rows:
    if r['hard_kind']!='trap': continue
    k=(r['agent'],lab[r['episode']]); c[k][0]+=1; c[k][1]+=int(r['hard_pass']); c[k][2]+= (r['true_main_tested']=='1')
for k in sorted(c): print(k, 'n=%d pass=%d main_tested=%d'%tuple(c[k]))
# per item pooled
p=collections.defaultdict(lambda:[0,0,0])
for (a,i),v in c.items():
    for j in range(3): p[i][j]+=v[j]
print('pooled per item', dict(p))
# Open-8 per item
b=list(csv.DictReader(open(f'{G}/blackbox_1112/rows_r1112.csv')))
q=collections.defaultdict(lambda:[0,0])
for r in b:
    if r['counted']!='1' or r['kind']!='trap': continue
    k=(r['agent'],r['arm'],lab.get(r['episode'],r['episode'])); q[k][0]+=1; q[k][1]+=int(r['name'] or 0)
for k in sorted(q): print(k, q[k])
