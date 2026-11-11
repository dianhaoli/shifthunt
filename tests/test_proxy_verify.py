"""Synthetic tests of scripts/proxy_verify.py (no bank, no GPU)."""
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import blind_verify as BV  # noqa: E402
import proxy_verify as PV  # noqa: E402

N, NB = 8, 16
CANDS = [f"f{i}" for i in range(N)]


def probe(j, main=None, hard=False, kind="planted", unit=4.0):
    tru = {f: np.full(NB, unit if f == main else 0.0) for f in CANDS}
    return BV.make_probe(j, kind, hard, {main} if main else set(), CANDS, [1] * N, unit, tru,
                         {f: np.ones(NB, bool) for f in CANDS})


def episode(trap_main="f5"):
    """Probe 0: a trap (the proxy's top candidate f0 is not used; the main is trap_main). 1, 2: ordinary. 3: null."""
    P = [probe(0, trap_main, hard=True), probe(1, "f1"), probe(2, "f2"), probe(3, None, kind="null")]
    prox = [np.full(N, 0.01) for _ in P]
    prox[0][0] = 0.6
    prox[1][1] = 0.6
    prox[2][2] = 0.6
    return P, prox


def run(P, prox, order, B=8, seed=0):
    thr = BV.thresholds(P, "topic")
    return PV.run_all(P, prox, order, B, lambda name: random.Random(f"{name}:{seed}"), thr, "additive")


def test_order_and_place():
    assert PV.order_of([np.array([0.1, 0.5, 0.5, 0.2])]) == [[1, 2, 3, 0]]
    assert PV.place_main([3, 1, 2, 0], 0, 2) == [3, 0, 1, 2]
    assert PV.place_main([3, 1, 2, 0], 1, 4) == [3, 2, 0, 1]


def test_budget_never_exceeded():
    P, prox = episode()
    for B in (4, 8, 11, 16):
        for row, (claims, used) in run(P, prox, PV.order_of(prox), B).items():
            assert used <= B, (row, B, used)
            assert len(claims) == len(P)


def test_complement_names_the_cue_at_every_rank_and_prefix2_only_at_rank_2():
    P, prox = episode("f5")
    base = PV.order_of(prox)
    for r in range(2, N + 1):
        order = [list(o) for o in base]
        order[0] = PV.place_main(base[0], 5, r)
        res = run(P, prox, order)
        assert BV.name_ok(P, res["complement_none"][0]), r
        assert BV.all_ok(P, res["complement_none"][0]), r
        assert BV.name_ok(P, res["complement_rand_none"][0]), r
        assert BV.name_ok(P, res["prefix2"][0]) == (r == 2), r
        assert not BV.name_ok(P, res["prefix1"][0])
        assert not BV.name_ok(P, res["proxy_only"][0])  # it claims the decoy


def test_complement_spends_exactly_eight_on_a_trap():
    P, prox = episode("f5")
    cl, used, info = PV.policy_complement(P, prox, PV.order_of(prox), 8, random.Random(0), BV.thresholds(P, "topic"),
                                          "additive")
    assert used == 8 and info == {"screen_pos": 1, "searched": 1, "verified": 1}
    assert cl["none"][0] == ("f5",) and cl["none"][3] == ()


def test_no_trap_everything_trusts_the_proxy():
    P = [probe(0, "f0", hard=True), probe(1, "f1"), probe(2, "f2"), probe(3, None, kind="null")]
    prox = [np.full(N, 0.01) for _ in P]
    for j in range(3):
        prox[j][j] = 0.6
    res = run(P, prox, PV.order_of(prox))
    for row in PV.ROWS:
        assert BV.all_ok(P, res[row][0]), row


def test_missing_group_size_raises():
    P, prox = episode()
    for p in P:
        tab = np.full_like(p.tables["additive"], np.nan)
        for m in BV.family_masks(N):
            tab[:, m] = p.tables["additive"][:, m]
        p.tables["exact"] = tab
    thr = BV.thresholds(P, "topic")
    try:
        PV.policy_complement(P, prox, PV.order_of(prox), 8, random.Random(0), thr, "exact")
    except KeyError:
        pass
    else:
        raise AssertionError("a size-7 group read from a table without it")
    assert len(PV.extra_masks(N)) == 8 + 56
