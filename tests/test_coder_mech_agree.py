"""Synthetic tests for coder vs mechanical agreement (no real runs)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import coder_mech_agree as M  # noqa: E402


def test_kappa():
    assert M.kappa([(1, 1), (0, 0)]) == 1.0
    assert M.kappa([(1, 1), (1, 1)]) is None
    assert abs(M.kappa([(1, 1), (0, 0), (1, 0), (0, 1)]) - 0.0) < 1e-12
    assert M.kappa([]) is None


def _fixture():
    scope = [
        {"id": "b__r1", "batch": "b", "run": "r1", "scope": "trap", "population": "main", "agent": "x",
         "episode": "e", "failed": 0},
        {"id": "b__r2", "batch": "b", "run": "r2", "scope": "twopart_sample", "population": "bb8", "agent": "x",
         "episode": "e", "failed": 1},
    ]
    s1 = [
        {"batch": "b", "run": "r1", "hard": 1, "F1a_computable": False, "F1a": None, "named": 1, "F2": 1},
        {"batch": "b", "run": "r1", "hard": 0, "F1a_computable": True, "F1a": 1, "named": 1, "F2": 0},
        {"batch": "b", "run": "r2", "hard": 1, "F1a_computable": True, "F1a": 1, "named": 0, "F2": None},
    ]
    traps = [{"batch": "b", "run": "r1", "T_D": 0}]
    f4 = [{"batch": "b", "run": "r1", "hard": 1, "missing": False, "primary": {"F4": None},
           "proxy_unit": {"F4": 0}}]
    return scope, s1, traps, f4


def test_mech_values():
    scope, s1, traps, f4 = _fixture()
    m = M.mech_values(scope, s1, traps, f4)
    assert m["b__r1"] == {"F1": "not computable", "F2": 1, "T-D": 0, "F4": "n/a", "F4_sens": 0}
    assert m["b__r2"] == {"F1": 1, "F2": "n/a", "T-D": "n/a", "F4": "no SAE", "F4_sens": "no SAE"}


def test_disagreement_rules():
    assert M.is_disagreement("F1", 1, "not computable")
    assert not M.is_disagreement("F1", 0, "not computable")
    assert not M.is_disagreement("F1", 1, "missing")
    assert M.is_disagreement("F2", "n/a", 1)
    assert not M.is_disagreement("F2", "cannot tell", 1)
    assert M.is_disagreement("F4", 0, "n/a")
    assert M.is_disagreement("F4", 1, "no SAE")
    assert not M.is_disagreement("F4", "n/a", "no SAE")
    assert M.is_disagreement("F4", 1, 0)


def test_compare_and_adjudication():
    scope, s1, traps, f4 = _fixture()
    mech = M.mech_values(scope, s1, traps, f4)
    rows = [
        {"id": "b__r1", "coder": "A", "codes": {"F1": {"value": 1}, "F2": {"value": 1}, "T-D": {"value": 1},
                                                "F4": {"value": "n/a"}}},
        {"id": "b__r1", "coder": "B", "codes": {"F1": {"value": 0}, "F2": {"value": 1}, "T-D": {"value": 0},
                                                "F4": {"value": 0}}},
        {"id": "b__r2", "coder": "A", "codes": {"F1": {"value": 1}, "F2": {"value": "n/a"},
                                                "T-D": {"value": "n/a"}, "F4": {"value": "n/a"}}},
        {"id": "b__r2", "coder": "B", "codes": {"F1": {"value": "cannot tell"}, "F2": {"value": "n/a"},
                                                "T-D": {"value": "n/a"}, "F4": {"value": "n/a"}}},
    ]
    cv = M.coder_values(rows)
    res = M.compare(scope, cv, mech)
    assert res["cannot_tell"]["B"]["F1"] == 1
    assert res["coder_vs_mech"]["A"]["F1"]["all"]["primary_computable"]["n"] == 1
    assert res["coder_vs_mech"]["A"]["F1"]["all"]["as_scored_nc0"]["n"] == 2
    dis = M.disagreements(scope, cv, mech)
    keys = {(d["id"], d["flag"]): d["coders_disagreeing"] for d in dis}
    assert keys == {("b__r1", "F1"): ["A"], ("b__r1", "T-D"): ["A"], ("b__r1", "F4"): ["B"]}
    adj = [{"id": "b__r1", "flag": "T-D", "truth_letter": 0, "truth_substance": 1, "reason": "mech_miss_multi"},
           {"id": "b__r1", "flag": "F1", "truth_letter": 0, "truth_substance": 0, "reason": "coder_error"}]
    s = M.summarise_adjudication(dis, adj)
    assert s["n_adjudicated"] == 2 and s["unadjudicated"] == 1
    td = s["by_flag"]["T-D"]
    assert td["right_letter"] == {"coder_A_right": 0, "mechanical": 1}
    assert td["right_substance"] == {"coder_A_right": 1, "not_mechanical": 1}
    assert s["by_flag"]["F1"]["right_letter"]["mechanical"] == 1
    assert s["by_flag"]["T-D"]["substance_values"] == {"1": 1}


def test_adjudication_no_sae_and_ambiguous():
    dis = [{"id": "x", "flag": "F4", "scope": "trap", "coders_disagreeing": ["A"], "A": 0, "B": "n/a",
            "mech": "no SAE"},
           {"id": "y", "flag": "F4", "scope": "trap", "coders_disagreeing": ["B"], "A": "n/a", "B": 1,
            "mech": "n/a"}]
    adj = [{"id": "x", "flag": "F4", "truth_letter": "no SAE", "truth_substance": 0, "reason": "definition_scope"},
           {"id": "y", "flag": "F4", "truth_letter": "n/a", "truth_substance": "ambiguous", "reason": "definition_unit"}]
    f4 = M.summarise_adjudication(dis, adj)["by_flag"]["F4"]
    assert f4["right_letter"] == {"coder_A_right": 0, "coder_B_right": 0, "mechanical": 2}
    assert f4["right_substance"] == {"ambiguous": 1, "coder_A_right": 1, "mech_undefined_no_sae": 1}
    assert f4["by_reason"] == {"definition_scope": 1, "definition_unit": 1}
