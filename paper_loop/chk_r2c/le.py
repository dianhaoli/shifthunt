import json, csv, sys
sys.path.insert(0,'/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/ledger/calc')
from stats_lib import fisher2
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results'
hard={r['cid']: r['hard_pass']=='1' for r in csv.DictReader(open(f'{G}/cross_model_1103/rollouts.csv'))}
def load(d): return [json.loads(l) for l in open(f'{G}/rollouts/{d}/summary_public.jsonl')]
tot={}
for a in ['opus','sonnet','haiku','gpt']:
    L=[x for d in [f'r1103_{a}_b1',f'r1103_{a}_b2'] for x in load(d) if x['cid'] in hard]
    ex=[x for x in L if x['tool_calls'].get('latent_examples',0)>0]; ne=[x for x in L if x not in ex]
    pe=sum(hard[x['cid']] for x in ex); pn=sum(hard[x['cid']] for x in ne)
    print(a,len(L),'ex',pe,len(ex),'not',pn,len(ne))
    tot[a]=(pe,len(ex),pn,len(ne))
c=[tot[a] for a in ['opus','sonnet','haiku']]
a=sum(x[0] for x in c); n1=sum(x[1] for x in c); b=sum(x[2] for x in c); n2=sum(x[3] for x in c)
print('claude',a,n1,b,n2,fisher2(a,n1-a,b,n2-b))
# probe_gradient and own text
for ag in ['gpt','opus','sonnet','haiku']:
    for bb in ['b1','b2']:
        L=load(f'r1103_{ag}_{bb}')
        print(ag,bb,len(L),'pg',sum(1 for x in L if x['tool_calls'].get('probe_gradient',0)>0),'inhard',sum(1 for x in L if x['cid'] in hard))
