import json,csv,sys
sys.path.insert(0,'/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/ledger/calc')
import stats_lib as s
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results'
rows=list(csv.DictReader(open(f'{G}/cross_model_1103/rollouts.csv')))
print(len(rows), rows[0].keys())
cids={r['cid'] for r in rows}
n=0;pg=0;own=0
for ag in ['gpt','opus','sonnet','haiku']:
  for bb in ['b1','b2','hv']:
    try: L=[json.loads(l) for l in open(f'{G}/rollouts/r1103_{ag}_{bb}/summary_public.jsonl')]
    except Exception as e: print(e); continue
    L=[x for x in L if x['cid'] in cids]
    n+=len(L); pg+=sum(1 for x in L if x['tool_calls'].get('probe_gradient',0)>0); own+=sum(1 for x in L if (x.get('own_text_sae_calls') or 0)>0)
print('coded runs',n,'pg',pg,'own',own)
print(s.exact_cmh.__doc__)
import inspect; print(inspect.signature(s.exact_cmh))
print(s.exact_cmh([(0,0,11,5),(4,2,8,2),(1,2,7,6)]))
