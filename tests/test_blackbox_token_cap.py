"""scripts/blackbox_token_cap.py: token measures, the cap rule, and that the uncapped table reproduces the
study's confirmatory contrasts from the tracked rows and public summaries."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import blackbox_token_cap as TC  # noqa: E402


def test_token_measures_codex():
    t = {"input_tokens": 1000, "cached_input_tokens": 900, "cache_write_input_tokens": 50, "output_tokens": 30,
         "reasoning_output_tokens": 20}
    assert TC.token_measures(t) == {"out": 30, "fresh": 130, "all_in": 1000}


def test_token_measures_claude():
    t = {"input": 5, "output": 40, "cache_write_5m": 100, "cache_write_1h": 10, "cache_read": 2000}
    assert TC.token_measures(t) == {"out": 40, "fresh": 155, "all_in": 2115}


def test_token_measures_missing():
    with pytest.raises(ValueError):
        TC.token_measures({})


def test_cap_only_removes_passes():
    rows = [{"name": 1, "out": 10}, {"name": 1, "out": 20}, {"name": 0, "out": 5}, {"name": 0, "out": 30}]
    c = TC.capped(rows, "out", 15)
    assert [r["name"] for r in c] == [1, 0, 0, 0]
    assert [r["over"] for r in c] == [0, 1, 0, 1]
    assert [r["name"] for r in TC.capped(rows, "out", None)] == [1, 1, 0, 0]


@pytest.mark.skipif(not TC.ROWS.exists(), reason="study rows not in this checkout")
def test_uncapped_matches_study():
    res = TC.analyse(TC.load(), n=2000)
    t = next(x for x in res["tables"] if x["agent"] == "gpt" and x["measure"] == "out" and x["cap"] is None)
    assert {a: (v["k"], v["n"]) for a, v in t["arms"].items()} == {"open8": (23, 24), "bb8": (6, 24),
                                                                   "bb64": (24, 24)}
    assert t["contrasts"]["C1"]["T"] == pytest.approx(17 / 24)
    assert t["contrasts"]["C4"]["T"] == pytest.approx(1 / 24)
    assert t["r3"] == "eliminated"
