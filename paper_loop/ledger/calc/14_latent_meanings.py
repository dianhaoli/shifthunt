"""E3: did agents read latent meanings (latent_examples / latent_tokens tool calls) and does it go with passing?
Inputs: G/results/rollouts/r1103_{agent}_{b1,b2}/summary_public.jsonl and r1112_{gpt,haiku}_open8/summary_public.jsonl
(tool-call counts from the tool server logs; pass = hard-slot NAME for Open-8 'name', main 'pass' via rollouts.csv)."""
import json, csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from stats_lib import fmt, fisher2
G = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results'
hard = {r['cid']: r['hard_pass'] == '1' for r in csv.DictReader(open(f'{G}/cross_model_1103/rollouts.csv'))}
out = []
def load(d):
    return [json.loads(l) for l in open(f'{G}/rollouts/{d}/summary_public.jsonl')]
groups = {f'main {a}': [f'r1103_{a}_b1', f'r1103_{a}_b2'] for a in ['gpt', 'opus', 'sonnet', 'haiku']}
groups.update({'open8 gpt': ['r1112_gpt_open8'], 'open8 haiku': ['r1112_haiku_open8']})
for g, ds in groups.items():
    L = [x for d in ds for x in load(d)]
    if g.startswith('main'): L = [x for x in L if x['cid'] in hard]
    ps = lambda x: hard[x['cid']] if g.startswith('main') else x.get('name') == 1.0
    ex = [x for x in L if x['tool_calls'].get('latent_examples', 0) > 0]; tk = [x for x in L if x['tool_calls'].get('latent_tokens', 0) > 0]
    either = [x for x in L if x in ex or x in tk]; nei = [x for x in L if x not in either]
    pe = sum(ps(x) for x in either); pn = sum(ps(x) for x in nei)
    med = sorted(x['tool_calls'].get('latent_examples', 0) for x in L)[len(L)//2]
    out.append(f"- {g}: runs {len(L)}; latent_examples used {len(ex)}; latent_tokens used {len(tk)}; either {len(either)}; median latent_examples calls {med}; "
               f"pass | either {pe}/{len(either)}, pass | neither {pn}/{len(nei)}")
open(os.path.join(os.path.dirname(__file__), '14_latent_meanings.out.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
# counterfactual-edit pipeline: SAE calls on the agent's own (edited) texts
out2 = ['## SAE tool calls on the agent\'s own texts (own_text_sae_calls; counterfactual edits encoded through the SAE)']
for g, ds in groups.items():
    L = [x for d in ds for x in load(d)]
    if g.startswith('main'): L = [x for x in L if x['cid'] in hard]
    v = sorted(x.get('own_text_sae_calls', 0) or 0 for x in L)
    out2.append(f"- {g}: runs with >=1 own-text SAE call {sum(1 for a in v if a>0)}/{len(v)}; median {v[len(v)//2]}; min {v[0]}; max {v[-1]}")
open(os.path.join(os.path.dirname(__file__), '14_latent_meanings.out.md'), 'a').write('\n'.join(out2) + '\n'); print('\n'.join(out2))
