import sys, itertools, math
sys.path.insert(0, '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/pylib')
import numpy as np, pandas as pd
from scipy import stats
from scipy.special import expit
rng = np.random.default_rng(11)
d = pd.read_csv('/home/user/shifthunt/results/cross_model_1103/rollouts.csv')
B = d[d.batch.isin(['b1', 'b2'])].copy().reset_index(drop=True)
AG = ['gpt', 'opus', 'sonnet', 'haiku']; EPS = sorted(B.episode.unique())
fp = lambda a, n1, c, n2: stats.fisher_exact([[a, n1-a], [c, n2-c]])[1]

# ---- power
from functools import lru_cache
@lru_cache(None)
def fpc(x, n1, y, n2): return fp(x, n1, y, n2)
def power(p1, p2, n, alpha=0.05):
    b1 = stats.binom.pmf(range(n+1), n, p1); b2 = stats.binom.pmf(range(n+1), n, p2)
    return sum(b1[x]*b2[y] for x in range(n+1) for y in range(n+1) if fpc(x, n, y, n) <= alpha)
print('power 0.875 v 0.6875 n16', round(power(0.875, 0.6875, 16), 3), ' 0.88 v 0.69', round(power(0.88, 0.69, 16), 3))
for n in [60, 70, 76, 80, 84, 88, 92, 100]:
    print(' n', n, round(power(0.875, 0.6875, n), 3), round(power(0.88, 0.69, n), 3))
print('0.78 v 0.90 n80', round(power(0.90, 0.78, 80), 3))
# power under item clustering: simulate with item random effects (sd on logit) , 6 fixed items reused
def sim_power(pa, pb, n_per_item, items=6, sd=1.0, R=3000):
    hits = 0
    for _ in range(R):
        b = rng.normal(0, sd, items)
        la, lb = np.log(pa/(1-pa)), np.log(pb/(1-pb))
        xa = rng.binomial(n_per_item, expit(la+b)).sum(); xb = rng.binomial(n_per_item, expit(lb+b)).sum()
        N = n_per_item*items
        hits += fpc(int(xa), N, int(xb), N) <= 0.05
    return hits/R

# ---- item heterogeneity permutation (larger agents)
L = B[B.agent != 'haiku']
def chi(df):
    t = df.groupby('episode').hard_pass.agg(['sum', 'count']); p = t['sum'].sum()/t['count'].sum()
    e = t['count']*p; return (((t['sum']-e)**2)/(e*(1-p))).sum()
obs = chi(L); y = L.hard_pass.values.copy(); cnt = 0; R = 20000
for _ in range(R):
    rng.shuffle(y); cnt += chi(L.assign(hard_pass=y)) >= obs - 1e-12
print('item heterogeneity larger perm p', cnt/R)
cnt = 0; y = B.hard_pass.values.copy(); obsA = chi(B)
for _ in range(R):
    rng.shuffle(y); cnt += chi(B.assign(hard_pass=y)) >= obsA - 1e-12
print('item heterogeneity all agents perm p', cnt/R)

# ---- ep472 cell multiplicity: within-episode permutation of agent labels; stat = min over 24 cells of fisher(cell vs rest of episode)
def minp(df):
    m = 1
    for e, g in df.groupby('episode'):
        tot, n = g.hard_pass.sum(), len(g)
        for a, ga in g.groupby('agent'):
            k, na = ga.hard_pass.sum(), len(ga)
            m = min(m, fpc(int(k), na, int(tot-k), n-na))
    return m
obsm = minp(B); print('observed min cell-vs-rest p', obsm, 'opus472 vs other 9:', fp(0, 3, 8, 9))
grp = [B.index[B.episode == e].values for e in EPS]; ag = B.agent.values.copy(); hits = 0; R2 = 4000
for _ in range(R2):
    a2 = ag.copy()
    for idx in grp: a2[idx] = rng.permutation(ag[idx])
    hits += minp(B.assign(agent=a2)) <= obsm + 1e-12
print('P(min cell p <= obs) under within-episode exchangeability', hits/R2)

# ---- item-level sign/permutation tests (6 items as units)
rate = B.groupby(['episode', 'agent']).hard_pass.mean().unstack()
print(rate.round(2))
for a, b in itertools.combinations(AG, 2):
    dv = (rate[a]-rate[b]).values
    # exact sign-flip permutation on mean diff
    vals = [abs(np.mean(dv*np.array(s))) >= abs(dv.mean())-1e-12 for s in itertools.product([1, -1], repeat=6)]
    print(f'item-level {a}-{b}: diffs {np.round(dv,2)} mean {dv.mean():+.3f} sign-flip p={np.mean(vals):.3f}')

# ---- conditional logit stratified by episode (agent dummies, ref haiku)
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
X = pd.get_dummies(B.agent)[['gpt', 'opus', 'sonnet']].astype(float)
cl = ConditionalLogit(B.hard_pass.values, X.values, groups=B.episode.values).fit(disp=0)
print('cond logit vs haiku (log OR, se, p):', np.round(cl.params, 2), np.round(cl.bse, 2), np.round(cl.pvalues, 4))
# plain logit with episode fixed effects and cluster-robust SE by episode
Xf = pd.concat([X, pd.get_dummies(B.episode, drop_first=True).astype(float)], axis=1); Xf = sm.add_constant(Xf)
m = sm.Logit(B.hard_pass.values, Xf.values).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(B.episode)[0]})
print('FE logit cluster-robust (6 clusters) gpt/opus/sonnet vs haiku p:', np.round(m.pvalues[1:4], 4))
m0 = sm.Logit(B.hard_pass.values, sm.add_constant(X.values)).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(B.episode)[0]})
print('logit agent only, cluster-robust by episode p:', np.round(m0.pvalues[1:4], 4))

# ---- Bayesian hierarchical logistic: logit p = mu_a + b_e + u_ae ; b~N(0,sb), u~N(0,su); half-normal(1) priors on sd; mu~N(0,2)
cells = B.groupby(['agent', 'episode']).hard_pass.agg(['sum', 'count']).reset_index()
ai = cells.agent.map({a: i for i, a in enumerate(AG)}).values; ei = cells.episode.map({e: i for i, e in enumerate(EPS)}).values
K = cells['sum'].values; N = cells['count'].values
def logpost(th):
    mu = th[0:4]; zb = th[4:10]; zu = th[10:34]; lsb, lsu = th[34], th[35]
    sb, su = np.exp(lsb), np.exp(lsu)
    eta = mu[ai] + sb*zb[ei] + su*zu
    ll = np.sum(K*eta - N*np.logaddexp(0, eta))
    lp = -0.5*np.sum(mu**2)/4 - 0.5*np.sum(zb**2) - 0.5*np.sum(zu**2)
    lp += (-0.5*sb**2 + lsb) + (-0.5*su**2 + lsu)  # half-normal(1) with log-jacobian
    return ll + lp
def run_chain(seed, iters=300000):
    r = np.random.default_rng(seed); th = np.zeros(36); th[34:] = -1; lp = logpost(th)
    step = np.full(36, 0.3); acc = np.zeros(36); out = []
    for t in range(iters):
        j = t % 36
        prop = th.copy(); prop[j] += step[j]*r.normal()
        lq = logpost(prop)
        if np.log(r.random()) < lq - lp: th, lp = prop, lq; acc[j] += 1
        if t < iters//3 and t % 3600 == 3599:
            rate_ = acc/100; step *= np.exp(rate_-0.44); acc[:] = 0
        if t >= iters//3 and t % 36 == 0: out.append(th.copy())
    return np.array(out)
S = np.vstack([run_chain(s) for s in (1, 2, 3)])
mu = S[:, :4]; sb = np.exp(S[:, 34]); su = np.exp(S[:, 35])
print('posterior sd_item median', np.median(sb).round(2), 'sd_item:agent', np.median(su).round(2))
for a, b in itertools.combinations(range(4), 2):
    dlt = mu[:, a]-mu[:, b]
    print(f'GLMM {AG[a]}-{AG[b]}: logOR median {np.median(dlt):+.2f} 95% [{np.percentile(dlt,2.5):+.2f},{np.percentile(dlt,97.5):+.2f}] P(>0)={np.mean(dlt>0):.3f}')
# marginal (new item) pass prob per agent
newb = np.random.default_rng(5).normal(size=len(S))*sb; newu = np.random.default_rng(6).normal(size=len(S))*su
for i, a in enumerate(AG):
    p = expit(mu[:, i]+newb+newu)
    print(f'  {a} pass prob on a new item: median {np.median(p):.2f} [{np.percentile(p,2.5):.2f},{np.percentile(p,97.5):.2f}]')
np.save('/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/glmm.npy', S)
