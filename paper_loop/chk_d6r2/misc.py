# d6 critic r2 existing-data checks (read-only over committed files; November only)
import csv, statistics as s
from collections import Counter
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu'
R=list(csv.DictReader(open(f'{G}/results/cross_model_1103/rollouts.csv')))
P=lambda r: r['hard_pass'] in ('1','True','true')
stage={'N1':'hyp','N2':'hyp','N3':'acq','T1':'acq','T2':'acq','T3':'acq','T4':'acq','T5':'acq'}
for b in ('b1','b2'):
    f=[r for r in R if r['batch']==b and not P(r)]
    print('Table5', b, len(f), Counter(stage.get(r['failure_mode'][:2],'?') for r in f), Counter(r['failure_mode'][:2] for r in f))
for k in ('trap','twopart'):
    v=[r for r in R if r['batch'] in ('b1','b2') and r['hard_kind']==k and P(r)]
    rem=[float(r['hard_removal']) for r in v]
    print('abs removal main passes',k,len(v),round(min(rem),3),round(s.median(rem),3),round(max(rem),3))
B=list(csv.DictReader(open(f'{G}/results/blackbox_1112/rows_r1112.csv')))
B=[r for r in B if r['counted'] in ('1','True','true') and r['agent']=='gpt']
def arm(a):
    v=[r for r in B if r['arm']==a]; return s.mean(float(r['usd']) for r in v), s.mean(float(r['pq_used']) for r in v), sum(r['name'] in ('1','True','true') for r in v)/len(v)
o=arm('open8'); b=arm('bb64')
# per pass cost incl. c per exact query: (usd + pq*c)/rate ; solve equality
c=(b[0]/b[2]-o[0]/o[2])/(o[1]/o[2]-b[1]/b[2])
print('break-even USD per exact query (per NAME pass), GPT Open-8 vs BB-64:', round(c,4), o, b)
