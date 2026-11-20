import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import followup_failure_modes as F  # noqa: E402


def test_proxy_ranks_by_abs_mean():
    r, m = F.proxy_ranks([{"a": 0.1, "b": -0.5, "c": 0.0}, {"a": 0.3, "b": -0.3, "c": 0.0}], ["a", "b", "c"])
    assert r == {"b": 1, "a": 2, "c": 3} and abs(m["a"] - 0.2) < 1e-12


def test_trap_routes():
    assert F.trap_route(dict(hedge=1, main_isolated=1, decoy_isolated=1)) == "both in the first batch"
    assert F.trap_route(dict(hedge=0, main_isolated=1, decoy_isolated=1, main_after_decoy=1)) == "decoy first, true cue later"
    assert F.trap_route(dict(hedge=0, main_isolated=1, decoy_isolated=0)) == "true cue only"
    assert F.trap_route(dict(hedge=0, main_isolated=0, decoy_isolated=1, left_after_decoy=0)) == "decoy only, no exact texts left"
    assert F.trap_route(dict(hedge=0, main_isolated=0, decoy_isolated=1, left_after_decoy=3)) == "decoy only, exact texts left"
    assert F.trap_route(dict(hedge=0, main_isolated=0, decoy_isolated=0)) == "neither"


def test_answer_type():
    assert F.answer_type(dict(named=0, covered=[]), [3]) == "none"
    assert F.answer_type(dict(named=1, covered=[3, 5]), [3]) == "true cue"
    assert F.answer_type(dict(named=1, covered=[5]), [3]) == "other"


def test_mech_helpers():
    import followup_failure_modes_mech as M
    # agent row differs from a sample row in exactly column 1 (same topic) -> column 1 proxy-tested
    assert M.hamming1_columns([[1, 0, 0]], [1], [[1, 1, 0], [0, 1, 1]], [1, 1]) == {1}
    assert M.hamming1_columns([[1, 0, 0]], [None], [[1, 1, 0]], [1]) == set()
    assert M.hamming1_columns([[1, 0, 0]], [0], [[1, 1, 0]], [1]) == set()      # other topic
    assert M.is_rank_prefix([1, 2]) == 1 and M.is_rank_prefix([2]) == 0 and M.is_rank_prefix([]) == 0
    assert M.P3_RE.search("the SAE has an error term") and not M.P3_RE.search("all good")
    assert M.P4_RE.search("this is my best guess") and M._yes("Yes, listed") == 1 and M._yes("no") == 0
