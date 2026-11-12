"""Fast exact Bayes-optimal search for the abstract ShiftHunt episode, by exchangeable candidate classes.
(Equivalent to the hypothesis-set DP in sim_core.HypDP; cross-checked in check_models.py.)

Roles: 'N' null, 'T' trap (hard), 'P' nested two-part (hard), 'O' ordinary. Each planted role has a law over
proxy ranks 1..8 (blind = uniform). Candidate ranks with the same probability under every role form one class;
ranks with probability 0 under every role form an inert class (never the truth under the model).
Per-probe state: (consistent count per class..., null still possible). Role assignments are enumerated with
their prior weight; the prior is symmetric over probes, so joint states are sorted.

counts='known': exactly one null, one hard, two ordinary (the paper's 0.703 model).
counts='unknown': each probe null with prob p_null independently (all-null excluded), hard uniform among the
planted probes, the rest ordinary. NAME = hard answered with its truth and every null answered `none`.
"""
import itertools
from functools import lru_cache

K = 8


class Model:
    def __init__(self, piT, piN=None, piO=None, p_trap=0.5, counts="known", p_null=0.25, blind=False, mode="group"):
        if blind:
            u = {r: 1.0 / K for r in range(1, K + 1)}
            piT = piN = piO = u
        piN = piN or {1: 1.0}
        piO = piO or {1: 1.0}
        self.law = {"T": {r: float(piT.get(r, 0)) for r in range(1, K + 1)},
                    "P": {r: float(piN.get(r, 0)) for r in range(1, K + 1)},
                    "O": {r: float(piO.get(r, 0)) for r in range(1, K + 1)}}
        for ro in self.law:
            s = sum(self.law[ro].values())
            self.law[ro] = {r: v / s for r, v in self.law[ro].items()}
        sigs = {}
        for r in range(1, K + 1):
            sig = tuple(round(self.law[ro][r], 12) for ro in "TPO")
            sigs.setdefault(sig, []).append(r)
        # classes ordered by smallest rank; inert class last
        cl = sorted(sigs.items(), key=lambda kv: (all(x == 0 for x in kv[0]), kv[1][0]))
        self.classes = [members for sig, members in cl]
        self.inert = [all(x == 0 for x in sig) for sig, members in cl]
        self.cl_of = {r: c for c, mem in enumerate(self.classes) for r in mem}
        self.C = len(self.classes)
        # per-member law of each class for each role
        self.mlaw = {ro: [self.law[ro][mem[0]] for mem in self.classes] for ro in "TPO"}
        # role assignments
        A = []
        if counts == "known":
            for kind, pk in (("T", p_trap), ("P", 1 - p_trap)):
                if pk == 0:
                    continue
                for h in range(4):
                    for n in range(4):
                        if n != h:
                            ro = ["O"] * 4
                            ro[h], ro[n] = kind, "N"
                            A.append((tuple(ro), h, pk / 12))
        else:
            for mask in range(15):
                nulls = [i for i in range(4) if (mask >> i) & 1]
                planted = [i for i in range(4) if not (mask >> i) & 1]
                w = p_null ** len(nulls) * (1 - p_null) ** len(planted)
                for kind, pk in (("T", p_trap), ("P", 1 - p_trap)):
                    if pk == 0:
                        continue
                    for h in planted:
                        ro = ["O"] * 4
                        for i in nulls:
                            ro[i] = "N"
                        ro[h] = kind
                        A.append((tuple(ro), h, w * pk / len(planted)))
        tot = sum(a[2] for a in A)
        self.assign = [(ro, h, w / tot) for ro, h, w in A]
        self.mode = mode
        self.s0 = tuple([tuple(len(m) for m in self.classes) + (True,)] * 4)
        self._V, self._A = {}, {}

    # ---- likelihoods ------------------------------------------------------------------------------------
    def L(self, ro, s):
        if ro == "N":
            return 1.0 if s[-1] else 0.0
        return sum(s[c] * self.mlaw[ro][c] for c in range(self.C))

    def posterior(self, state):
        """list of (assign index, posterior); empty if the state has prior probability 0."""
        out = []
        for a, (ro, h, w) in enumerate(self.assign):
            p = w
            for i in range(4):
                p *= self.L(ro[i], state[i])
                if p == 0:
                    break
            if p > 0:
                out.append((a, p))
        s = sum(p for _, p in out)
        return [(a, p / s) for a, p in out], s

    def terminal(self, state, post=None):
        post = post if post is not None else self.posterior(state)[0]
        opts = [[None] + [c for c in range(self.C) if state[i][c] > 0 and not self.inert[c]] for i in range(4)]
        best, ba = 0.0, (None,) * 4
        for ans in itertools.product(*opts):
            v = 0.0
            for a, p in post:
                ro, h, _ = self.assign[a]
                if any(ro[i] == "N" and ans[i] is not None for i in range(4)):
                    continue
                c = ans[h]
                if c is None:
                    continue
                v += p * self.mlaw[ro[h]][c] / self.L(ro[h], state[h])
            if v > best + 1e-15:
                best, ba = v, ans
        return best, ba

    def actions(self, state, i):
        s = state[i]
        live = [c for c in range(self.C) if s[c] > 0 and not self.inert[c]]
        if self.mode == "single":
            for c in live:
                k = [0] * self.C
                k[c] = 1
                yield tuple(k)
            return
        for ks in itertools.product(*[range(s[c] + 1) if c in live else (0,) for c in range(self.C)]):
            if any(ks):
                yield ks

    def outcome(self, state, i, ks, post):
        s = state[i]
        pp = 0.0
        for a, p in post:
            ro = self.assign[a][0][i]
            if ro == "N":
                continue
            pp += p * sum(ks[c] * self.mlaw[ro][c] for c in range(self.C)) / self.L(ro, s)
        sp = tuple(ks) + (False,)
        sn = tuple(s[c] - ks[c] for c in range(self.C)) + (s[-1],)
        return pp, sp, sn

    def V(self, state, b):
        key = (state, b)
        if key in self._V:
            return self._V[key]
        post, _ = self.posterior(state)
        best, _ = self.terminal(state, post)
        bact = None
        if b > 0 and best < 1 - 1e-12:
            done = set()
            for i in range(4):
                if state[i] in done:
                    continue  # identical probe states are interchangeable
                done.add(state[i])
                for ks in self.actions(state, i):
                    pp, sp, sn = self.outcome(state, i, ks, post)
                    if pp < 1e-13 or pp > 1 - 1e-13:
                        continue
                    stp = list(state); stp[i] = sp
                    stn = list(state); stn[i] = sn
                    v = pp * self.V(tuple(sorted(stp)), b - 1) + (1 - pp) * self.V(tuple(sorted(stn)), b - 1)
                    if v > best + 1e-12:
                        best, bact = v, (state[i], ks)
        self._V[key] = best
        self._A[key] = bact
        return best

    def value(self, b):
        return self.V(self.s0, b)

    # ---- replay on a true world ------------------------------------------------------------------------
    def replay(self, world, b, reader=None, episodes=None):
        """Play this model's Bayes-optimal policy in `world` (another Model; its prior is the truth).
        reader=None: noiseless; enumerate the world's hypotheses exactly.
        reader(ep_index, probe, ranks_tuple) -> bool and episodes = list of (roles, h, truth ranks) for Monte Carlo.
        Surprise (assumed posterior 0): claim every rank seen positive in a single isolation, else `none`.
        Returns dict(success, tests_hard, tests_total, surprise_rate)."""
        if episodes is None:
            hyps = []
            for ro, h, w in world.assign:
                lists = []
                for i in range(4):
                    if ro[i] == "N":
                        lists.append([(0, 1.0)])
                    else:
                        lists.append([(r, p) for r, p in world.law[ro[i]].items() if p > 0])
                for combo in itertools.product(*lists):
                    p = w
                    for _, q in combo:
                        p *= q
                    hyps.append((ro, h, tuple(r for r, _ in combo), p))
        else:
            hyps = [(ro, h, t, 1.0 / len(episodes)) for (ro, h, t) in episodes]
        S = TH = TT = SU = 0.0
        for e, (ro, h, t, w) in enumerate(hyps):
            cons = [{c: list(m) for c, m in enumerate(self.classes)} for _ in range(4)]
            nullok = [True] * 4
            state = list(self.s0)
            seen = {}
            bb, nh, nt, surprised = b, 0, 0, False
            while True:
                key = tuple(sorted(state))
                _, mass = self.posterior(key)
                if mass == 0:
                    surprised = True
                    ans = [seen.get(i) for i in range(4)]
                    break
                self.V(key, bb)
                act = self._A.get((key, bb))
                if act is None or bb == 0:
                    _, cans = self.terminal(key)
                    # map class answers back to probes: sorted-state answers are per state value
                    order = sorted(range(4), key=lambda i: state[i])
                    ans = [None] * 4
                    for pos, i in enumerate(order):
                        c = cans[pos]
                        ans[i] = None if c is None else cons[i][c][0]
                    break
                pstate, ks = act
                i = next(j for j in range(4) if state[j] == pstate)
                Sset = []
                for c in range(self.C):
                    Sset += cons[i][c][:ks[c]]
                if reader is None:
                    r = t[i] in Sset
                else:
                    r = reader(e, i, tuple(Sset))
                nt += 1
                nh += (i == h)
                if r:
                    if len(Sset) == 1:
                        seen[i] = Sset[0]
                    for c in range(self.C):
                        cons[i][c] = cons[i][c][:ks[c]]
                    nullok[i] = False
                else:
                    for c in range(self.C):
                        cons[i][c] = cons[i][c][ks[c]:]
                state[i] = tuple(len(cons[i][c]) for c in range(self.C)) + (nullok[i],)
                bb -= 1
            ok = (ans[h] == t[h]) and all(ans[i] is None for i in range(4) if ro[i] == "N")
            S += w * ok
            TH += w * nh
            TT += w * nt
            SU += w * surprised
        Wt = sum(x[3] for x in hyps)
        return dict(success=S / Wt, tests_hard=TH / Wt, tests_total=TT / Wt, surprise=SU / Wt)
