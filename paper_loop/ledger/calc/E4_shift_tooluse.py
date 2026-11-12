"""E4: latent-meaning tool use vs pass, from tracked public summaries (read-only).
Sources: results/rollouts/*/summary_public.jsonl (tool_calls counts, own_text_sae_calls, pass, access, model)
         results/cross_model_1103/rollouts.csv (counted 86 r1103 runs; binary latent_examples/latent_tokens/ablate_check; hard_pass)
         results/blackbox_1112/rows_r1112.csv (counted r1112 runs; counted flag; name/score)
"""
import json, glob, csv, statistics, collections, os, sys
G = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results'
AG = {"gpt-6.1-terra": "gpt", "claude-opus-5-5": "opus", "claude-sonnet-5-5": "sonnet", "claude-haiku-5-5": "haiku"}
S = {}
for f in sorted(glob.glob(G + '/rollouts/*/summary_public.jsonl')):
    run = f.split('/')[-2]
    for l in open(f):
        r = json.loads(l); r['run'] = run
        S[(run, r['cid'][:12])] = r
def med(x): return statistics.median(x) if x else None
def tc(r, t): return (r.get('tool_calls') or {}).get(t, 0)
out = []
P = lambda *a: out.append(' '.join(str(x) for x in a))

# ---- Part 1: r1103 cross-model (86 counted runs) ----
R = list(csv.DictReader(open(G + '/cross_model_1103/rollouts.csv')))
P('## Part 1: r1103 cross-model study, 86 counted runs (rollouts.csv joined to summary_public tool counts)')
P('| agent | batch set | runs | hard pass | latent_examples runs | latent_tokens runs | either | median calls (users, either tool) | calls list | pass w/ either | pass w/o | ablate_check runs | pass w/ ablate | pass w/o ablate | own-text SAE calls, runs>0 | median own-text SAE calls | probe_query used up |')
P('|' + '---|' * 17)
for sel, lab in [(lambda r: r['batch'] in ('b1', 'b2'), 'b1+b2 (64)'), (lambda r: True, 'all 86 (b1,b2,hv,smoke)'), (lambda r: r['batch'] == 'hv', 'hv only')]:
    for a in ['gpt', 'opus', 'sonnet', 'haiku', 'ALL']:
        rs = [r for r in R if sel(r) and (a == 'ALL' or r['agent'] == a)]
        if not rs: continue
        ss = [S[(r['run'], r['cid'])] for r in rs]
        le = [int(r['latent_examples']) for r in rs]; lt = [int(r['latent_tokens']) for r in rs]
        ei = [max(x, y) for x, y in zip(le, lt)]
        ncalls = [tc(s, 'latent_examples') + tc(s, 'latent_tokens') for s in ss]
        users = [n for n, e in zip(ncalls, ei) if e]
        hp = [int(r['hard_pass']) for r in rs]
        ab = [int(r['ablate_check']) for r in rs]
        own = [s.get('own_text_sae_calls', 0) for s in ss]
        pq = [ (s.get('budget') or {}).get('probe_query', {}) for s in ss]
        pqu = sum(1 for p in pq if p and p.get('remaining') == 0)
        f = lambda m: f"{sum(h for h, e in zip(hp, m) if e)}/{sum(m)}"
        g = lambda m: f"{sum(h for h, e in zip(hp, m) if not e)}/{len(m)-sum(m)}"
        P(f"| {a} | {lab} | {len(rs)} | {sum(hp)}/{len(rs)} | {sum(le)}/{len(rs)} | {sum(lt)}/{len(rs)} | {sum(ei)}/{len(rs)} | {med(users)} | {sorted(users)} | {f(ei)} | {g(ei)} | {sum(ab)}/{len(rs)} | {f(ab)} | {g(ab)} | {sum(1 for o in own if o>0)}/{len(rs)} | {med(own)} | {pqu}/{len(rs)} |")
# consistency check summary counts vs csv binary
bad = [(r['cid'], r['latent_examples'], tc(S[(r['run'], r['cid'])], 'latent_examples')) for r in R
       if int(r['latent_examples']) != int(tc(S[(r['run'], r['cid'])], 'latent_examples') > 0)]
P('\ncsv latent_examples binary vs summary count>0 mismatches (summary counts include error-status calls):', bad)
bad2 = [(r['cid'], r['latent_tokens'], tc(S[(r['run'], r['cid'])], 'latent_tokens')) for r in R
        if int(r['latent_tokens']) != int(tc(S[(r['run'], r['cid'])], 'latent_tokens') > 0)]
P('latent_tokens mismatches:', bad2)

# ---- Part 2: r1112 Block 1 open8 arm (counted rows) ----
B = list(csv.DictReader(open(G + '/blackbox_1112/rows_r1112.csv')))
P('\n## Part 2: r1112 Block 1 (rows_r1112.csv, counted==1), joined to summary_public')
P('| arm | agent | counted runs | episode score>0 (pass) | hard NAME | latent_examples runs | latent_tokens runs | either | median calls among users | pass w/ either | pass w/o | NAME w/ either | NAME w/o | own-text SAE runs>0 | median own-text SAE | probe_gradient runs | probe_scores calls median |')
P('|' + '---|' * 17)
for arm in ['open8', 'bb8', 'bb64']:
    for a in ['gpt', 'haiku']:
        rs = [r for r in B if r['arm'] == arm and r['agent'] == a and r['counted'] == '1']
        ss = [S.get((r['batch'], r['run'][:12])) for r in rs]
        miss = sum(1 for s in ss if s is None)
        ok = [(r, s) for r, s in zip(rs, ss) if s]
        ps = [float(r['score']) > 0 for r, s in ok]
        nm = [r['name'] == '1' for r, s in ok]
        le = [tc(s, 'latent_examples') > 0 for r, s in ok]; lt = [tc(s, 'latent_tokens') > 0 for r, s in ok]
        ei = [x or y for x, y in zip(le, lt)]
        users = [tc(s, 'latent_examples') + tc(s, 'latent_tokens') for (r, s), e in zip(ok, ei) if e]
        own = [s.get('own_text_sae_calls', 0) for r, s in ok]
        pg = [tc(s, 'probe_gradient') > 0 for r, s in ok]
        f = lambda v, m: f"{sum(x for x, e in zip(v, m) if e)}/{sum(m)}"
        g = lambda v, m: f"{sum(x for x, e in zip(v, m) if not e)}/{len(m)-sum(m)}"
        P(f"| {arm} | {a} | {len(ok)}{' (missing summ '+str(miss)+')' if miss else ''} | {sum(ps)}/{len(ok)} | {sum(nm)}/{len(ok)} | {sum(le)} | {sum(lt)} | {sum(ei)} | {med(users)} | {f(ps, ei)} | {g(ps, ei)} | {f(nm, ei)} | {g(nm, ei)} | {sum(1 for o in own if o>0)} | {med(own)} | {sum(pg)} | {med([tc(s,'probe_scores') for r,s in ok])} |")

# ---- Part 3: all other summary rows by run (October + sample_only), access, model ----
P('\n## Part 3: every summary_public row, grouped by run dir / access / model (all rows incl. infra failures; pass = episode pass as logged)')
P('| run | access | model | rows | pass(>0) | latent_examples runs | latent_tokens runs | either | median meaning calls (users) | pass w/ either | pass w/o | own-text SAE runs>0 |')
P('|' + '---|' * 12)
grp = collections.defaultdict(list)
for (run, cid), r in S.items():
    grp[(run, r.get('access', 'open') or 'open', r.get('model'))].append(r)
for k in sorted(grp, key=lambda k: (k[0], k[1], str(k[2]))):
    rs = grp[k]
    ps = [(r.get('pass') or 0) > 0 for r in rs]
    le = [tc(r, 'latent_examples') > 0 for r in rs]; lt = [tc(r, 'latent_tokens') > 0 for r in rs]
    ei = [x or y for x, y in zip(le, lt)]
    users = [tc(r, 'latent_examples') + tc(r, 'latent_tokens') for r, e in zip(rs, ei) if e]
    f = lambda v, m: f"{sum(x for x, e in zip(v, m) if e)}/{sum(m)}"
    g = lambda v, m: f"{sum(x for x, e in zip(v, m) if not e)}/{len(m)-sum(m)}"
    P(f"| {k[0]} | {k[1]} | {k[2]} | {len(rs)} | {sum(ps)}/{len(rs)} | {sum(le)} | {sum(lt)} | {sum(ei)} | {med(users)} | {f(ps, ei)} | {g(ps, ei)} | {sum(1 for r in rs if r.get('own_text_sae_calls',0)>0)} |")

# ---- Part 4: pooled by access (all rows) ----
P('\n## Part 4: pooled by access mode over all summary rows (excluding blackbox), by engine family')
for acc in ['open', 'sample_only']:
    for fam in ['claude', 'gpt', 'ALL']:
        rs = [r for r in S.values() if (r.get('access') or 'open') == acc and (fam == 'ALL' or (fam == 'gpt') == ('gpt' in str(r.get('model'))))]
        if not rs: continue
        le = sum(1 for r in rs if tc(r, 'latent_examples') > 0); lt = sum(1 for r in rs if tc(r, 'latent_tokens') > 0)
        ei = sum(1 for r in rs if tc(r, 'latent_examples') + tc(r, 'latent_tokens') > 0)
        mc = [tc(r, 'latent_examples') + tc(r, 'latent_tokens') for r in rs]
        P(f"{acc} {fam}: rows {len(rs)}; latent_examples {le}; latent_tokens {lt}; either {ei} ({ei/len(rs):.2f}); mean meaning calls/run {sum(mc)/len(rs):.2f}; median among users {med([m for m in mc if m])}")
txt = '\n'.join(out)
print(txt)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'E4_shift_tooluse.out.md'), 'w').write(txt + '\n')
