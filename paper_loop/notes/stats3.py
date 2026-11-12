import sys, itertools, math
sys.path.insert(0, '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/pylib')
import numpy as np, pandas as pd
from scipy import stats
d = pd.read_csv('/home/user/shifthunt/results/cross_model_1103/rollouts.csv')
B = d[d.batch.isin(['b1', 'b2'])].copy().reset_index(drop=True)
AG = ['gpt', 'opus', 'sonnet', 'haiku']; EPS = sorted(B.episode.unique())
fp = lambda a, n1, c, n2: stats.fisher_exact([[a, n1-a], [c, n2-c]])[1]
rng = np.random.default_rng(3)

# Table 7 stratified: Opus 4.8 one run per episode, one pass on unknown episode
def strat(xs):  # xs: list of (x1,n1,x2,n2)
    dist = {0: 1.0}; obs = 0
    for x1, n1, x2, n2 in xs:
        k = x1+x2; hg = stats.hypergeom(n1+n2, k, n1); nd = {}
        for s, p in dist.items():
            for x in range(max(0, k-n2), min(k, n1)+1): nd[s+x] = nd.get(s+x, 0)+p*hg.pmf(x)
        dist = nd; obs += x1
    p0 = dist[obs]; return sum(p for p in dist.values() if p <= p0*(1+1e-7))
for a in AG:
    res = []
    for pe in EPS:
        xs = []
        for e in EPS:
            g = B[(B.agent == a) & (B.episode == e)]
            xs.append((int(g.hard_pass.sum()), len(g), int(e == pe), 1))
        res.append(round(strat(xs), 4))
    # equal-weight per-episode rate
    ew = B[B.agent == a].groupby('episode').hard_pass.mean().mean()
    print('T7 strat', a, dict(zip(EPS, res)), 'equal-wt rate', round(ew, 3))
# Opus 4.8 1/6 vs batch-1 only (one run per ep closer to design)
for a in AG:
    g = B[(B.agent == a) & (B.batch == 'b1')]; print('b1 vs 4.8', a, g.hard_pass.sum(), fp(int(g.hard_pass.sum()), 8, 1, 6))

# margins
P = B[B.hard_pass == 1].copy(); P['ratio'] = P.hard_removal/P.hard_tau; P['marg'] = P.hard_removal-P.hard_tau
print('pass removal/tau ratio min/med/max', P.ratio.min().round(3), P.ratio.median().round(3), P.ratio.max().round(3), 'abs margin min', P.marg.min().round(3))
print(P.groupby('episode').agg(rem_min=('hard_removal', 'min'), rem_max=('hard_removal', 'max'), tau=('hard_tau', 'first'), sd=('hard_removal', 'std')).round(4))
print('min_kept dist', B.min_kept.describe().round(4).to_dict(), 'n<0.9', (B.min_kept < 0.9).sum())
print('min_kept by agent', B.groupby('agent').min_kept.min().round(3).to_dict())
F = B[B.hard_pass == 0]; print('failed rows with removal', F[['agent', 'episode', 'failure_mode', 'hard_bucket', 'hard_removal', 'hard_tau']].dropna().values.tolist())
print('hv margins', d[(d.batch == 'hv') & (d.hard_pass == 1)].eval('hard_removal/hard_tau').round(2).tolist())

# correlates of failure, stratified by agent (permutation of outcome within agent)
for col in ['usd', 'submit_min', 'forward', 'tool_calls', 'pq_hard', 'pq_first_min', 'pq_span_min', 'fwd_latent_means', 'latent_examples', 'ablate_check']:
    sub = B.dropna(subset=[col])
    def stat(df):  # mean within-agent standardized difference fail - pass
        s = 0
        for a, g in df.groupby('agent'):
            if g.hard_pass.nunique() < 2: continue
            z = (g[col]-g[col].mean())/(g[col].std()+1e-9)
            s += z[g.hard_pass == 0].mean()-z[g.hard_pass == 1].mean()
        return s
    obs = stat(sub); cnt = 0; R = 5000; y = sub.hard_pass.values
    groups = [sub.index[sub.agent == a] for a in AG]
    for _ in range(R):
        yy = sub.hard_pass.copy()
        for gi in groups: yy.loc[gi] = rng.permutation(yy.loc[gi].values)
        cnt += abs(stat(sub.assign(hard_pass=yy))) >= abs(obs)-1e-12
    med = sub.groupby('hard_pass')[col].median().to_dict()
    print(f'{col}: within-agent fail-pass z {obs:+.2f}, perm p={cnt/R:.3f}; medians fail/pass {med.get(0)}/{med.get(1)}')

# batch / order effects
B['pos'] = B.groupby(['agent', 'batch']).cumcount()+1
print('pass by batch', B.groupby('batch').hard_pass.agg(['sum', 'count']).to_dict())
print('pass by position', B.groupby('pos').hard_pass.agg(['sum', 'count']).T.to_dict())
# b1 vs b2 within agent on shared episodes
sh = B[B.episode.isin(['ep411', 'ep415', 'ep472', 'ep476'])]
print('shared eps b1 vs b2', sh.groupby(['agent', 'batch']).hard_pass.agg(['sum', 'count']).unstack().to_string())
s1 = sh[sh.batch == 'b1'].hard_pass; s2 = sh[sh.batch == 'b2'].hard_pass
print('shared eps all agents b1', s1.sum(), len(s1), 'b2', s2.sum(), len(s2), 'fisher', round(fp(int(s1.sum()), len(s1), int(s2.sum()), len(s2)), 3))
# day effect: 3 Nov (gpt b1/b2, opus b1/b2, sonnet b1) vs 4 Nov (haiku, sonnet b2) among Claude
# last query -> submit gap
B['lastq'] = B.pq_first_min+B.pq_span_min; B['gap'] = B.submit_min-B.lastq
print('median gap last query->submit', B.groupby('agent').gap.median().round(2).to_dict())
print('tool_calls claude batch sum', B[B.agent != 'gpt'].tool_calls.sum(), 'hv claude', d[(d.batch == 'hv') & (d.agent != 'gpt')].tool_calls.sum())
print('submit_min max gpt', B[B.agent == 'gpt'].submit_min.max(), 'agent_min max overall', d.agent_min.max())
# GPT forward exhausted
print('gpt forward >= 2947', (B[B.agent == 'gpt'].forward >= 2947).sum(), B[B.agent == 'gpt'].forward.min())
# texts on hard probe vs pass within agent
print('pq_hard by pass', B.groupby(['agent', 'hard_pass']).pq_hard.mean().round(2).unstack().to_string())
# hard_tests vs pq_hard
print('hard_tests==pq_hard', (B.hard_tests == B.pq_hard).mean())
# usd vs pass correlation within Opus/Sonnet
for a in AG:
    g = B[B.agent == a]
    if g.hard_pass.nunique() > 1:
        print(a, 'usd fail/pass', g.groupby('hard_pass').usd.mean().round(2).to_dict(), 'submit', g.groupby('hard_pass').submit_min.mean().round(1).to_dict(), 'fwd', g.groupby('hard_pass').forward.mean().round(0).to_dict())
