"""Pre-registered no-SAE study (Block 1, Nov 10-11) + BB-16: outcomes, cost, tokens,
omission/commission at matched 8-query budget, S3 by arm. Read-only on repo files."""
import csv, json, statistics as st, sys
from collections import Counter
sys.path.insert(0, '.')
from stats_lib import *
G = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu'
RES = f'{G}/results/blackbox_1112'
rows = list(csv.DictReader(open(f'{RES}/rows_r1112.csv')))
s3 = {r['run']: r for r in csv.DictReader(open(f'{RES}/s3_r1112.csv'))}
out = []; P = out.append
EP = ['ep411', 'ep413', 'ep415', 'ep472', 'ep474', 'ep476']
arms = [('gpt', 'open8'), ('gpt', 'bb8'), ('gpt', 'bb64'), ('haiku', 'open8'), ('haiku', 'bb8'), ('haiku', 'bb64')]
P('## A. NAME per arm (recomputed from rows_r1112.csv)')
for a, arm in arms:
    rr = [r for r in rows if r['agent'] == a and r['arm'] == arm and r['counted'] == '1']
    k = sum(int(r['name']) for r in rr)
    tr = [r for r in rr if r['kind'] == 'trap']; tp = [r for r in rr if r['kind'] == 'twopart']
    per = ' '.join(f"{sum(int(r['name']) for r in rr if r['episode']==e)}/{sum(1 for r in rr if r['episode']==e)}" for e in EP)
    usd = [float(r['usd']) for r in rr]; ti = [int(r['tokens_in']) for r in rr]; to = [int(r['tokens_out']) for r in rr]
    P(f"{a} {arm}: NAME {fmt(k, len(rr))}; traps {sum(int(r['name']) for r in tr)}/{len(tr)}, two-part {sum(int(r['name']) for r in tp)}/{len(tp)}; per item {per}")
    P(f"    USD mean {st.mean(usd):.3f} median {st.median(usd):.3f} total {sum(usd):.2f}; per NAME pass {sum(usd)/k if k else float('nan'):.2f}; tokens_in median {st.median(ti):,.0f}; tokens_out median {st.median(to):,.0f}; wall median {st.median(float(r['wall_min']) for r in rr):.1f} min; pq_hard mean {st.mean(int(r['pq_hard']) for r in rr):.2f}; pq_used mean {st.mean(int(r['pq_used']) for r in rr):.2f}; usd_src {set(r['usd_src'] for r in rr)}")
    P(f"    hard naming buckets {dict(Counter(r['naming_bucket'] for r in rr if r['name']=='0'))}; null false claims {sum(int(r['n_null_false']) for r in rr)}/{sum(int(r['n_null']) for r in rr)}; plain slots named {sum(int(r['s1_named']) for r in rr)}/{sum(int(r['s1_n']) for r in rr)}")
    sv = [s3[r['run']] for r in rr]
    P(f"    S3 (true cue varied cleanly on agent's hard-probe texts) {sum(int(x['s3']) for x in sv)}/{len(sv)}; main_varies at all {sum(int(x['main_varies']) for x in sv)}/{len(sv)}; NAME|S3=1 {sum(1 for r in rr if s3[r['run']]['s3']=='1' and r['name']=='1')}/{sum(1 for r in rr if s3[r['run']]['s3']=='1')}; NAME|S3=0 {sum(1 for r in rr if s3[r['run']]['s3']!='1' and r['name']=='1')}/{sum(1 for r in rr if s3[r['run']]['s3']!='1')}")
P('\n## B. Matched-budget contrasts at 8 exact queries (Fisher, descriptive) and Haiku vs GPT')
def nm(a, arm, kind=None):
    rr = [r for r in rows if r['agent'] == a and r['arm'] == arm and (kind is None or r['kind'] == kind)]; return sum(int(r['name']) for r in rr), len(rr)
for kind in (None, 'trap', 'twopart'):
    for a in ('gpt', 'haiku'):
        k1, n1 = nm(a, 'open8', kind); k2, n2 = nm(a, 'bb8', kind)
        P(f"{a} {kind or 'all'} Open-8 {k1}/{n1} vs BB-8 {k2}/{n2}: diff {k1/n1-k2/n2:+.3f}, Fisher p {fisher2(k1,n1-k1,k2,n2-k2):.3f}")
    for arm in ('open8', 'bb8', 'bb64'):
        k1, n1 = nm('gpt', arm, kind); k2, n2 = nm('haiku', arm, kind)
        P(f"   GPT vs Haiku {arm} {kind or 'all'}: {k1}/{n1} vs {k2}/{n2}, Fisher p {fisher2(k1,n1-k1,k2,n2-k2):.4f}")
# Haiku traps with SAE (main + Open-8) vs without
P('\n## C. Omission / commission on PLANTED probes, from results/rollouts/<batch>/probes_public.jsonl (grader buckets)')
def tally(batches):
    c = Counter(); 
    for b in batches:
        for l in open(f'{G}/results/rollouts/{b}/probes_public.jsonl'):
            d = json.loads(l); c[(d['kind'], d['bucket'])] += 1
    pl = sum(v for (k, b), v in c.items() if k == 'planted'); wrong = sum(v for (k, b), v in c.items() if k == 'planted' and b)
    none = c[('planted', 'planted_none')]; named = pl - none; nw = wrong - none
    nul = sum(v for (k, b), v in c.items() if k == 'null'); nf = c[('null', 'null_false_claim')]
    return pl, wrong, none, named, nw, nul, nf, {b: v for (k, b), v in c.items() if k == 'planted' and b}
sets = [('GPT main study (b1+b2), SAE, 8q', ['r1103_gpt_b1', 'r1103_gpt_b2']),
        ('Opus main study, SAE, 8q', ['r1103_opus_b1', 'r1103_opus_b2']),
        ('Sonnet main study, SAE, 8q', ['r1103_sonnet_b1', 'r1103_sonnet_b2']),
        ('Haiku main study, SAE, 8q', ['r1103_haiku_b1', 'r1103_haiku_b2']),
        ('GPT Open-8', ['r1112_gpt_open8']), ('GPT BB-8', ['r1112_gpt_bb8']), ('GPT BB-64', ['r1112_gpt_bb64']),
        ('Haiku Open-8', ['r1112_haiku_open8']), ('Haiku BB-8', ['r1112_haiku_bb8']), ('Haiku BB-64', ['r1112_haiku_bb64']),
        ('ALL with SAE (main + Open-8)', ['r1103_%s_b%d' % (a, i) for a in ('gpt','opus','sonnet','haiku') for i in (1,2)] + ['r1112_gpt_open8', 'r1112_haiku_open8']),
        ('ALL BB-8 (GPT+Haiku)', ['r1112_gpt_bb8', 'r1112_haiku_bb8']),
        ('Open-8 (GPT+Haiku) only', ['r1112_gpt_open8', 'r1112_haiku_open8'])]
P('| set | planted wrong | of which none (omission) | named answers wrong (commission) | null false claims | buckets |')
P('|---|---|---|---|---|---|')
for lab, bs in sets:
    pl, wrong, none, named, nw, nul, nf, bk = tally(bs)
    P(f"| {lab} | {wrong}/{pl} | {none}/{wrong} ({none/wrong if wrong else 0:.0%}) | {nw}/{named} ({nw/named if named else 0:.1%}) | {nf}/{nul} | {bk} |")
# Fisher on commission: Open-8 vs BB-8 per agent
for a in ('gpt', 'haiku'):
    _, _, _, n1, w1, nu1, f1, _ = tally([f'r1112_{a}_open8']); _, _, _, n2, w2, nu2, f2, _ = tally([f'r1112_{a}_bb8'])
    P(f"{a}: commission Open-8 {w1}/{n1} vs BB-8 {w2}/{n2}, Fisher p {fisher2(w1,n1-w1,w2,n2-w2):.4f}; null false Open-8 {f1}/{nu1} vs BB-8 {f2}/{nu2}, Fisher p {fisher2(f1,nu1-f1,f2,nu2-f2):.3f}")
_, _, _, n1, w1, nu1, f1, _ = tally(['r1112_gpt_open8', 'r1112_haiku_open8']); _, _, _, n2, w2, nu2, f2, _ = tally(['r1112_gpt_bb8', 'r1112_haiku_bb8'])
P(f"pooled GPT+Haiku: commission Open-8 {w1}/{n1} vs BB-8 {w2}/{n2}, Fisher p {fisher2(w1,n1-w1,w2,n2-w2):.2e}; null false {f1}/{nu1} vs {f2}/{nu2}, p {fisher2(f1,nu1-f1,f2,nu2-f2):.3f}")
P('\n### C2. Hard slot only (rows_r1112.csv naming_bucket), wrong answers by type')
for a, arm in arms:
    rr = [r for r in rows if r['agent'] == a and r['arm'] == arm]
    c = Counter(r['naming_bucket'] for r in rr if r['name'] == '0')
    P(f"{a} {arm}: hard-slot failures {sum(c.values())}/{len(rr)}: {dict(c)}")
P('\n## D. Haiku traps with vs without SAE (cross-population; descriptive)')
mc = [r for r in csv.DictReader(open(f'{G}/results/cross_model_1103/rollouts.csv')) if r['batch'] in ('b1','b2') and r['agent']=='haiku' and r['hard_kind']=='trap']
km = sum(int(r['hard_pass']) for r in mc); k8, n8 = nm('haiku','open8','trap'); kb, nb = nm('haiku','bb8','trap'); k64, n64 = nm('haiku','bb64','trap')
P(f"with SAE: main {km}/{len(mc)} + Open-8 {k8}/{n8} = {km+k8}/{len(mc)+n8}; without: BB-8 {kb}/{nb}, BB-64 {k64}/{n64}")
P(f"matched budget (8q, same Block 1): Open-8 {k8}/{n8} vs BB-8 {kb}/{nb}, Fisher p {fisher2(k8,n8-k8,kb,nb-kb):.3f}")
P(f"pooled SAE {km+k8}/{len(mc)+n8} vs BB-8+BB-64 {kb+k64}/{nb+n64}: Fisher p {fisher2(km+k8,len(mc)+n8-km-k8,kb+k64,nb+n64-kb-k64):.3f} (mixes 8q and 64q; not budget-matched)")
open('02_blackbox.out.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
