import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import followup_failure_modes_heldout as FH  # noqa: E402


def _row(tested_ranks, n=8):
    return dict(cands=[dict(rank=k, tested=int(k in tested_ranks), is_main=0) for k in range(1, n + 1)])


def test_curve_and_prefix():
    rs = [_row({1}), _row({1, 2}), _row({3}), _row(set())]
    c = FH.curve(rs)
    assert c["rank 1"]["tested"] == 2 and c["rank 1"]["n"] == 4 and c["rank 4+"]["tested"] == 0 and c["rank 4+"]["n"] == 20
    p = FH.prefix(rs)
    assert p["slots"] == 3 and p["observed"] == 2
    assert abs(p["expected"] - round(1 / 8 + 1 / 28 + 1 / 8, 2)) < 1e-9
