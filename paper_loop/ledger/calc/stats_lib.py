"""Pure-python stats helpers (no scipy available)."""
import math
from functools import lru_cache

def wilson(k, n, z=1.959964):
    if n == 0: return (float('nan'), float('nan'))
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), min(1.0, c+h))

def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k/n:.2f} [{lo:.2f}, {hi:.2f}]" if n else f"{k}/{n}"

def _lchoose(n, k):
    return math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)

def fisher2(a, b, c, d):
    """Two-sided Fisher exact p for [[a,b],[c,d]] (sum of probs <= observed)."""
    r1, r2, c1 = a+b, c+d, a+c; n = r1+r2
    lo, hi = max(0, c1-r2), min(r1, c1)
    def p(x): return math.exp(_lchoose(r1, x)+_lchoose(r2, c1-x)-_lchoose(n, c1))
    po = p(a); return min(1.0, sum(p(x) for x in range(lo, hi+1) if p(x) <= po*(1+1e-7)))

def fisher_one(a, b, c, d):
    """One-sided P(X >= a) (group1 successes high)."""
    r1, r2, c1 = a+b, c+d, a+c; n = r1+r2
    hi = min(r1, c1)
    return sum(math.exp(_lchoose(r1, x)+_lchoose(r2, c1-x)-_lchoose(n, c1)) for x in range(a, hi+1))

def holm(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i]); m = len(ps); out = [0]*m; run = 0
    for r, i in enumerate(idx):
        run = max(run, min(1.0, (m-r)*ps[i])); out[i] = run
    return out

def newcombe(k1, n1, k2, n2):
    l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2); p1, p2 = k1/n1, k2/n2; d = p1-p2
    return (d - math.sqrt((p1-l1)**2 + (u2-p2)**2), d + math.sqrt((u1-p1)**2 + (p2-l2)**2))

def binom_pmf(n, p):
    return [math.exp(_lchoose(n, k) + (k*math.log(p) if k else 0) + ((n-k)*math.log(1-p) if n-k else 0)) if 0<p<1 else (1.0 if (p==0 and k==0) or (p==1 and k==n) else 0.0) for k in range(n+1)]

def fisher_power(n1, p1, n2, p2, alpha=0.05):
    """Exact power of two-sided Fisher test, independent binomial arms."""
    f1, f2 = binom_pmf(n1, p1), binom_pmf(n2, p2); pw = 0.0
    for a in range(n1+1):
        for c in range(n2+1):
            pr = f1[a]*f2[c]
            if pr < 1e-12: continue
            if fisher2(a, n1-a, c, n2-c) <= alpha: pw += pr
    return pw

def mh_or(strata):
    """strata: list of (a,b,c,d). Mantel-Haenszel OR."""
    num = sum(a*d/(a+b+c+d) for a,b,c,d in strata if a+b+c+d); den = sum(b*c/(a+b+c+d) for a,b,c,d in strata if a+b+c+d)
    return num/den if den else float('inf')

def exact_cmh(strata):
    """Exact conditional test of common OR=1: distribution of sum a over strata (product of hypergeometrics). Two-sided by prob <= observed."""
    dist = {0: 1.0}
    obs = 0
    for a,b,c,d in strata:
        r1, r2, c1 = a+b, c+d, a+c; n = r1+r2; obs += a
        lo, hi = max(0, c1-r2), min(r1, c1)
        pm = {x: math.exp(_lchoose(r1, x)+_lchoose(r2, c1-x)-_lchoose(n, c1)) for x in range(lo, hi+1)}
        nd = {}
        for s, ps in dist.items():
            for x, px in pm.items(): nd[s+x] = nd.get(s+x, 0)+ps*px
        dist = nd
    po = dist[obs]
    two = sum(v for v in dist.values() if v <= po*(1+1e-7))
    lower = sum(v for s, v in dist.items() if s <= obs); upper = sum(v for s, v in dist.items() if s >= obs)
    return obs, two, lower, upper
