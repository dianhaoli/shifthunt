"""scripts/exp_f_rescore_ci.py on the fake bank of tests/test_exp_f_listing.py and synthetic stored responses.

No network and no paid call: responses go through the local stub server of test_exp_f_listing (made-up keys,
127.0.0.1), everything is written under tmp_path.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import exp_f_listing as exp  # noqa: E402
import exp_f_rescore_ci as X  # noqa: E402
import test_exp_f_listing as T  # noqa: E402  (fake bank, stub server, answer helper)
from shifthunt.regex_sandbox import run_many  # noqa: E402

PS_CASED = r"^P\.S\..*\b(maybe|perhaps|probably|I think|I guess)\b"   # misses "p.s. i think ..." notes


def _env(mp):
    for k, v in (("ANTHROPIC_API_KEY", "sk-ant-test-x"), ("OPENAI_API_KEY", "sk-oai-test-x"),
                 ("NO_PROXY", "127.0.0.1,localhost"), ("no_proxy", "127.0.0.1,localhost")):
        mp.setenv(k, v)
    mp.delenv("OPENAI_KEY", raising=False)
    mp.setattr(T.tc, "BACKOFF_BASE_S", 0.001)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    bank = T.make_fake_bank(tmp_path_factory.mktemp("bank"))
    out = tmp_path_factory.mktemp("priv")
    m = exp.build(out, bank=bank, cues=["ps_tentative", "curly_apostrophe"], episodes=list(T.FAKE), reps=2,
                  **T.SMALL)
    return out, m


def answer(row):
    """ps_tentative prompts: the case-sensitive P.S. regex; every other prompt: the frozen reference answer."""
    if row.get("cue") == "ps_tentative":
        return json.dumps([{"property": "hedged P.S.", "regex": PS_CASED, "scope": "last_line"}])
    return T.answer_for(row)


@pytest.fixture(scope="module")
def stored(built, tmp_path_factory):
    out, m = built
    tmp = tmp_path_factory.mktemp("run")
    runlog = tmp / "RUNLOG.md"
    runlog.write_bytes(exp.RUNLOG.read_bytes())
    by_sha = {r["prompt_sha256"]: answer(r) for r in m["prompts"]}
    stub = T.Stub(T.reply_with(by_sha))
    try:
        with pytest.MonkeyPatch.context() as mp:      # made-up keys; the stub on 127.0.0.1 answers every call
            _env(mp)
            rows = exp.run(out, tmp / "pub", T.BIG, base_urls=stub.base_urls, require_committed=False,
                           runlog=runlog)
    finally:
        stub.close()
    assert all(r["status"] == "ok" for r in rows)
    exp.score(out)        # the frozen scores.jsonl, as the study's `score` writes it
    return out, m


def test_ci_runner_matches_lowercase_ps():
    texts = ["Hi\nBody.\np.s. i think so", "Hi\nBody.\nP.S. I think so", "Hi\nBody.\nBye"]
    plain = run_many([(PS_CASED, "last_line")], texts)[0][0]
    ci = X.ci_runner([(PS_CASED, "last_line")], texts)[0][0]
    assert plain == [False, True, False] and ci == [True, True, False]


def test_ps_candidate_flips_from_miss_to_hit(stored):
    out, m = stored
    frozen, ci = X.rescore(out)
    gen = [(a, b) for a, b in zip(frozen, ci) if a["cue"] == "ps_tentative" and a["outcome"] == "scored"]
    assert len(gen) == 2 * len(exp.MODELS)
    for a, b in gen:
        assert not a["targets"][0]["primary"]["listed"], a["targets"][0]["primary"]
        assert b["targets"][0]["primary"]["listed"] and b["targets"][0]["primary"]["rank"] == 1
    s = X.compare(frozen, ci, X.reproduction(frozen, out / "scores.jsonl"))
    assert s["reproduction"] == {"stored": True, "compared": s["reproduction"]["compared"], "mismatches": 0}
    lv = s["by_level"]["L4"]
    assert lv["frozen"]["primary"]["k"] == 0 and lv["ci"]["primary"]["k"] == lv["ci"]["primary"]["n"] == 8
    assert lv["changes"]["primary_miss_to_hit"] == 8 and lv["changes"]["primary_hit_to_miss"] == 0
    assert lv["changes"]["answers_with_a_primary_change"] == 8
    assert lv["ci"]["primary"]["median_rank"] == 1 and lv["frozen"]["primary"]["median_rank"] is None
    # the reference answers do not change: L2 and the calibration groups are listed under both rules
    assert s["by_level"]["L2"]["changes"]["primary_miss_to_hit"] == 0
    assert s["by_level"]["L2"]["frozen"]["primary"]["k"] == s["by_level"]["L2"]["ci"]["primary"]["k"] == 8
    for g in exp.GROUPS:
        c = s["calibration"][g]
        assert c["frozen"]["primary"]["k"] == c["ci"]["primary"]["k"] == c["frozen"]["primary"]["n"] > 0


def test_frozen_rescore_equals_the_scripts_own_score(stored):
    out, _ = stored
    frozen, _ = X.rescore(out)
    mine = {r["call_id"]: r for r in frozen}
    for r in map(json.loads, (out / "scores.jsonl").read_text().splitlines()):
        assert mine[r["call_id"]]["targets"] == r["targets"]


def test_main_writes_pooled_tracked_outputs_and_keeps_scores(stored, tmp_path):
    out, _ = stored
    before = (out / "scores.jsonl").read_bytes()
    pub = tmp_path / "pub"
    assert X.main(["--out", str(out), "--pub", str(pub)]) == 0
    assert (out / "scores.jsonl").read_bytes() == before            # the frozen scores are never rewritten
    assert (out / "scores_ci.jsonl").exists() and (out / "rescore_ci_diff.jsonl").exists()
    cal = json.loads((out / "calibration.json").read_text())
    sources = {mm["source"]: mm["cue"] for e in cal.values() for mm in e["mains"]}
    for name in ("CASE_INSENSITIVE.md", "case_insensitive.json"):
        text = (pub / name).read_text()
        assert exp.find_pairings(text, cal, sources) == [], name
        assert "epf0" not in text and "fake_screen" not in text and "knob_trap" not in text
    s = json.loads((pub / "case_insensitive.json").read_text())
    assert set(s["calibration"]) == set(exp.GROUPS) and "by_episode" not in json.dumps(s)
    assert "| L4 |" in (pub / "CASE_INSENSITIVE.md").read_text()


def test_privacy_check_refuses_a_pairing(tmp_path):
    cal = {"ep999": {"mains": [{"cue": "weekday", "source": "x_screen/planted_1"}]}}
    with pytest.raises(ValueError):
        X.write_tracked(tmp_path, {"a.md": "ep999 weekday 3/5"}, cal)
    with pytest.raises(ValueError):
        X.write_tracked(tmp_path, {"a.md": "knob_trap3/planted_9 2/5"}, cal)
    X.write_tracked(tmp_path, {"a.md": "L4 3/5"}, cal)
    assert (tmp_path / "a.md").read_text() == "L4 3/5"
