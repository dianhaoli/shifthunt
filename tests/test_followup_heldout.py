import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import followup_heldout as H  # noqa: E402


def _items(fail_flag, fail_n, pass_flag, pass_n):
    return ([dict(failed=1, F=1)] * fail_flag + [dict(failed=1, F=0)] * (fail_n - fail_flag)
            + [dict(failed=0, F=1)] * pass_flag + [dict(failed=0, F=0)] * (pass_n - pass_flag))


def test_rule_supported_dead_weak_underpowered():
    r = H.rule(_items(5, 5, 1, 10), "F", lambda x: x["failed"], "a", "b")
    assert r["verdict"] == "supported" and r["diff"] == 0.9
    r = H.rule(_items(1, 5, 2, 10), "F", lambda x: x["failed"], "a", "b")
    assert r["verdict"] == "dead"
    r = H.rule(_items(2, 5, 1, 10), "F", lambda x: x["failed"], "a", "b")
    assert r["verdict"] == "weak"
    r = H.rule(_items(2, 2, 1, 10), "F", lambda x: x["failed"], "a", "b")
    assert r["verdict"] == "underpowered"


def test_missing_flags_left_out():
    it = _items(4, 4, 0, 4) + [dict(failed=1, F=None)]
    r = H.rule(it, "F", lambda x: x["failed"], "a", "b")
    assert r["n"] == 8


def test_one_sided_direction():
    assert H.one_sided(5, 0, 0, 5) < 0.01
    assert H.one_sided(0, 5, 5, 0) > 0.99
