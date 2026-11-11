"""scripts/failure_flags.py (DECISIONS D36) on synthetic logs only: no real run is read here."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import failure_flags as FF  # noqa: E402
import s3_coder as S3  # noqa: E402
from shifthunt import textgen as TG  # noqa: E402

COLS = list(S3.FEATURES["templated"])


def fake_match(table):
    """match_fn from {regex: predicate(text)}."""
    def m(regex, scope, texts):
        f = table.get(regex)
        return ([bool(f(t)) for t in texts] if f else [False] * len(texts)), None
    return m


# ------------------------------------------------------------------------------------------- topic rule

def test_topic_templated_phrases():
    pair = ["gardening", "astronomy"]
    assert FF.topic_of("He spends most weekends growing tomatoes at the greenhouse.", pair, "templated") == 0
    assert FF.topic_of("She owns two telescopes.", pair, "templated") == 1
    assert FF.topic_of("He owns two telescopes and seed trays.", pair, "templated") is None
    assert FF.topic_of("Nothing about hobbies here.", pair, "templated") is None


def test_topic_templated_on_generated_notes():
    import random
    rng = random.Random(1)
    cues = TG.make_cues(rng)
    pair = ["cooking", "sailing"]
    for i in range(40):
        lv = {f: rng.randrange(2) for f in TG.FEATURES}
        t, _ = TG.render(pair[i % 2], lv, cues, rng.getrandbits(32))
        assert FF.topic_of(t, pair, "templated") == i % 2


def test_topic_freetext_vocab():
    vocab = {"chess": {"rook": 3, "bishop": 2, "gambit": 1, "coffee": 5},
             "fishing": {"trout": 4, "reel": 2, "coffee": 3}}
    pair = ["chess", "fishing"]
    assert FF.topic_scores("The rook and the bishop, then coffee.", pair, "freetext", vocab) == (2, 0)
    assert FF.topic_of("The rook moved.", pair, "freetext", vocab) == 0
    assert FF.topic_of("A trout on the reel.", pair, "freetext", vocab) == 1
    assert FF.topic_of("rook and trout", pair, "freetext", vocab) is None
    assert FF.topic_of("a gambit with coffee", pair, "freetext", vocab) is None  # gambit: one paragraph only
    # generator edit words never count (a weekday name, a pronoun)
    vocab2 = {"chess": {"monday": 9, "she": 9}, "fishing": {}}
    assert FF.topic_of("She plays on Monday.", pair, "freetext", vocab2) is None


# ------------------------------------------------------------------------------------- pairs and effects

def test_clean_pairs_and_effects():
    rows = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 0, 0), (1, 0, 1)]
    topics = [0, 0, 0, 1, None]
    pairs = FF.clean_pairs(rows, topics)
    assert pairs == [(0, 1, 0), (1, 2, 1)]  # 0-3 differ in topic; 4 has no topic; 0-2 differ in two
    eff = FF.effects(rows, [1.0, 3.0, 2.0, 0.0, 0.0], pairs, unit=4.0)
    assert eff == {0: 0.5, 1: -0.25}


def test_duplicates_are_no_pair_and_count_twice():
    rows = [(0, 1), (0, 1), (1, 1)]
    pairs = FF.clean_pairs(rows, [0, 0, 0])
    assert pairs == [(0, 2, 0), (1, 2, 0)]
    assert FF.effects(rows, [0.0, 2.0, 3.0], pairs, 1.0) == {0: 2.0}


def test_balanced_accuracy_and_coverage():
    texts = ["a!", "b", "c!", "d"]
    rows = [(1, 0), (0, 1), (1, 1), (0, 0)]
    m = fake_match({"!": lambda t: "!" in t, "none": lambda t: False, "inv": lambda t: "!" not in t})
    assert FF.covered_columns([{"regex": "!", "scope": "any"}], texts, rows, m) == {0}
    assert FF.covered_columns([{"regex": "inv", "scope": "any"}], texts, rows, m) == {0}  # absence counts
    assert FF.covered_columns([{"regex": "none", "scope": "any"}], texts, rows, m) == set()
    assert FF.balanced_accuracy([1, 1], [1, 1]) is None


def test_aligned_columns():
    rows = [(1, 0, 1), (0, 1, 1), (1, 0, 0), (0, 1, 0)]
    assert FF.aligned_columns(rows, [1, 0, 1, 0]) == [0, 1]


def test_or3():
    assert FF.or3([1, None]) == 1
    assert FF.or3([0, 0]) == 0
    assert FF.or3([0, None]) is None
    assert FF.or3([]) is None


# --------------------------------------------------------------------------------------------- the flags

ROWS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 1, 1)]
TEXTS = ["t0", "t1 X", "t2 Y", "t3 Y Z"]
TOPICS = [0, 0, 0, 0]
MATCH = fake_match({"X": lambda t: "X" in t, "Z": lambda t: "Z" in t, "Q": lambda t: "Q" in t})


def flags(entry, logits=(0.0, 2.0, 0.1, 0.1), covered=(), aligned=(0, 2), texts_ok=True, logits_ok=True,
          unit=4.0, texts=TEXTS, rows=ROWS, topics=TOPICS):
    return FF.slot_flags(entry, list(texts), list(logits), list(topics), list(rows), unit, set(covered),
                         list(aligned), texts_ok, logits_ok, MATCH)


def test_F1_uncovered_effect():
    # pairs: (0,1) col0 +0.5; (0,2) col1 +0.025; (2,3) col2 0.0
    f = flags({"none": True, "cues": []})
    assert f["effects"] == {0: 0.5, 1: 0.025, 2: 0.0}
    assert f["F1"] == 1
    assert flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, covered={0})["F1"] == 0
    assert flags({"none": True, "cues": []}, logits=(0.0, 0.5, 0.0, 0.0))["F1"] == 0  # 0.125 < 0.15
    assert flags({"none": True, "cues": []}, logits=(0.0, -0.6, 0.0, 0.0))["F1"] == 1  # |effect|
    assert flags({"none": True, "cues": []}, logits=(0.0, 0.6, 0.0, 0.0))["F1"] == 1  # exactly 0.15


def test_F1_missing_without_logits_or_texts():
    assert flags({"none": True, "cues": []}, logits_ok=False)["F1"] is None
    assert flags({"none": True, "cues": []}, texts_ok=False)["F1"] is None
    assert flags({"none": True, "cues": []}, unit=None)["F1"] is None


def test_F2_claim_tested_or_not():
    tested = flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, covered={0})
    assert tested["F2"] == 0 and tested["F2n"] is None
    untested = flags({"none": False, "cues": [{"regex": "Q", "scope": "any"}]}, covered={0})
    assert untested["F2"] == 1
    # one tested and one untested cue: flagged; the Z cue differs within pair (2,3)
    two = flags({"none": False, "cues": [{"regex": "Z", "scope": "any"}, {"regex": "Q", "scope": "any"}]})
    assert two["untested_cues"] == 1 and two["F2"] == 1
    # no texts on the probe at all (known): untested
    empty = flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, texts=[], rows=[], topics=[],
                  logits=())
    assert empty["F2"] == 1 and empty["F1"] == 0 and empty["n_pairs"] == 0
    assert flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, texts_ok=False)["F2"] is None


def test_F2n_aligned_untested():
    assert flags({"none": True, "cues": []}, aligned=(0, 2))["F2n"] == 0  # both varied in clean pairs
    f = flags({"none": True, "cues": []}, aligned=(0, 2, 1), rows=ROWS[:2], texts=TEXTS[:2], topics=[0, 0],
              logits=(0.0, 2.0))
    assert f["aligned_untested"] == 2 and f["F2n"] == 1
    assert flags({"none": True, "cues": []}, texts_ok=False)["F2n"] is None
    # an unknown topic breaks the pair
    f = flags({"none": True, "cues": []}, aligned=(0,), topics=[0, None, 0, 0])
    assert f["F2n"] == 1


def test_combined_and_count():
    f = flags({"none": True, "cues": []})  # F1 1, F2n 0
    assert (f["combined"], f["count"]) == (1, 1)
    f = flags({"none": False, "cues": [{"regex": "Q", "scope": "any"}]})  # F1 1 (col0 uncovered), F2 1
    assert (f["combined"], f["count"]) == (1, 2)
    f = flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, covered={0})
    assert (f["combined"], f["count"]) == (0, 0)
    f = flags({"none": False, "cues": [{"regex": "Q", "scope": "any"}]}, logits_ok=False)  # F1 missing, F2 1
    assert (f["combined"], f["count"]) == (1, None)
    f = flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, covered={0}, logits_ok=False)
    assert (f["combined"], f["count"]) == (None, None)


# ---------------------------------------------------------------------------------------------- statistics

def test_fisher_and_auroc_and_verdict():
    assert FF.fisher_p(3, 0, 0, 3) == pytest.approx(0.1, abs=1e-9)
    assert FF.fisher_p(1, 1, 1, 1) == pytest.approx(1.0)
    assert FF.fisher_p(8, 2, 1, 5) == pytest.approx(0.03496503, rel=1e-5)
    assert FF.auroc([2, 1], [0, 1]) == pytest.approx(0.875)
    assert FF.auroc([], [1]) is None
    t = dict(diff=0.35, fisher_p=0.01)
    assert FF.verdict(t) == "supported"
    assert FF.verdict(dict(diff=0.35, fisher_p=0.2)) == "weak"
    assert FF.verdict(dict(diff=0.09, fisher_p=0.9)) == "dead"
    assert FF.verdict(dict(diff=-0.2, fisher_p=0.9)) == "dead"
    assert FF.verdict(dict(diff=0.2, fisher_p=0.01)) == "weak"
    assert FF.verdict(dict(diff=None, fisher_p=None)) == "undetermined"


def test_table_and_summary():
    def s(flag, failed, count=None):
        return dict(failed=failed, flags=dict(F1=flag, F2=None, F2n=None, combined=flag, count=count),
                    F3=dict(queries_unused=1 if failed else 0, calls_left=None, forward_left=10, minutes_left=5.0))
    slots = [s(1, 1, 2), s(1, 1, 1), s(0, 1, 0), s(0, 0, 0), s(1, 0, 1), s(None, 1)]
    t = FF.table2x2(slots, "combined")
    assert (t["flag_failed"], t["flag_passed"], t["noflag_failed"], t["noflag_passed"]) == (2, 1, 1, 1)
    assert t["rate_failed"] == pytest.approx(2 / 3) and t["rate_passed"] == 0.5 and t["missing"] == 1
    assert t["missing_failed"] == 1
    sm = FF.summarise(slots)
    assert sm["auroc_n"] == 5 and sm["auroc_count"] == pytest.approx((1 + 1 + 0.5 + 1 + 0.5 + 0) / 6)
    assert sm["F3"]["queries_unused"]["median_failed"] == 1 and sm["F3"]["calls_left"]["median_failed"] is None


# --------------------------------------------------------------------------------------- recovery: matching

def call(seq, probe, texts):
    return dict(seq=seq, probe=probe, n=len(texts), chars=sum(map(len, texts)))


def rcall(seq, probe, texts, j0=0, action=0):
    return dict(seq=seq, probe=probe, texts=texts, js=list(range(j0, j0 + len(texts))), action=action)


def test_match_exact_sequence():
    logged = [call(5, 0, ["ab", "c"]), call(9, 1, ["xyz"])]
    rec = [rcall(5, 0, ["ab", "c"]), rcall(9, 1, ["xyz"], 2)]
    st, pairs = FF.match_calls(logged, rec)
    assert st == {0: "ok", 1: "ok"} and pairs == [(0, 0), (1, 1)]


def test_match_per_probe_mismatch():
    logged = [call(5, 0, ["ab", "c"]), call(9, 1, ["xyz"]), call(11, 0, ["q"])]
    rec = [rcall(5, 0, ["ab", "c"]), rcall(9, 1, ["xy"]), rcall(11, 0, ["q"])]  # probe 1: chars differ
    st, pairs = FF.match_calls(logged, rec)
    assert st == {0: "ok", 1: "mismatch"} and pairs == [(0, 0), (2, 2)]
    # an extra recovered call on probe 2 (never logged) makes probe 2 missing
    st, _ = FF.match_calls(logged[:1], rec[:1] + [rcall(20, 2, ["zz"])])
    assert st == {0: "ok", 2: "mismatch"}
    # a logged call the replay never made makes its probe missing
    st, _ = FF.match_calls(logged, rec[:1])
    assert st[1] == "mismatch" and st[0] == "mismatch"


# --------------------------------------------------------------------------------------- recovery: logits

def test_sentinel_logits_full_precision_and_rounded():
    s0, s1 = FF.sentinel(0), FF.sentinel(1)
    rep = f'probe 0 {{\n  "logits": [{s0!r}, {s1!r}]\n}}\nmean {(s0 + s1) / 2:.4f}\n'
    real = 'probe 0 {\n  "logits": [4.384818293985096, -2.768413454711618]\n}\nmean 0.8082\n'
    got = FF.sentinel_logits(rep, real, [0, 1])
    assert got[0][0] == pytest.approx(4.384818293985096) and got[1][0] == pytest.approx(-2.768413454711618)
    rep2 = f"p0 a: {s0:.3f}\np0 b: {s1:.3f}\n"
    real2 = "p0 a: 4.385\np0 b: -2.768\n"
    got = FF.sentinel_logits(rep2, real2, [0, 1])
    assert got == {0: (4.385, 3), 1: (-2.768, 3)}


def test_sentinel_logits_needs_alignment_and_precision():
    s0 = FF.sentinel(0)
    assert FF.sentinel_logits(f"x {s0:.2f}\n", "x 4.38\n", [0]) == {}  # 2 decimals: not trusted
    assert FF.sentinel_logits(f"x {s0:.4f}\n", "y 4.3848\n", [0]) == {}  # skeleton differs
    assert FF.sentinel_logits(f"x {s0:.4f}\n", "x 4.38512\n", [0]) == {}  # real more precise: another format
    # real fewer decimals: round(x, 4) printed by repr drops trailing zeros; the precision is the sentinel's
    assert FF.sentinel_logits(f"x {s0:.4f}\n", "x 4.38\n", [0]) == {0: (4.38, 4)}
    # one sentinel printed twice with two different real values: left out
    assert FF.sentinel_logits(f"a {s0:.4f} b {s0:.4f}\n", "a 4.3848 b 1.0000\n", [0]) == {}


def test_reply_logits():
    out = ('{"ids": [1, 2], "labels": [0, 1], "logits": [0.5, 0.25]}\n'
           '{\n  "logits": [1.25, -3.5]\n}\n{"logits": [7.125]}\n')
    got = FF.reply_logits(out, [1, 2])
    assert got[0] == ([7.125], 3) and got[1] is None  # greedy in order: the 2-list comes before the 1-list
    got = FF.reply_logits(out, [2, 1])
    assert got == [([1.25, -3.5], 1), ([7.125], 3)]  # decimals: the fewest printed


class FakeEp:
    def __init__(self, n=2, sample=None):
        self.n = n
        self._s = sample or {}

    def sample_logit_of(self, j):
        return self._s.get(j, {})


def test_recover_from_replay_and_sample_check():
    s = FF.sentinel
    acts = [dict(i=0, kind="exec", output='{\n  "logits": [1.5, -0.25]\n}\n'),
            dict(i=1, kind="exec", output="a 0.123\nb 9.877\n")]
    res = dict(actions=acts, results=[dict(i=0, seq=[2, 2], out=f'{{\n  "logits": [{s(0)!r}, {s(1)!r}]\n}}\n'),
                                      dict(i=1, seq=[3, 4], out=f"a {s(2):.3f}\nb {s(3):.3f}\n")],
               fulltext=[dict(seq=2, tool="probe_query", status="ok", probe=0, texts=["aa", "b"]),
                         dict(seq=3, tool="probe_query", status="ok", probe=1, texts=["note"]),
                         dict(seq=4, tool="probe_query", status="ok", probe=1, texts=["nope"])])
    logged = [call(2, 0, ["aa", "b"]), call(3, 1, ["note"]), call(4, 1, ["nope"])]
    per = FF.recover_from_replay(res, logged, FakeEp())
    assert per[0]["texts"] == ["aa", "b"] and per[0]["logits"] == [1.5, -0.25] and per[0]["logits_ok"]
    assert per[1]["logits"] == [0.123, 9.877] and per[1]["logit_src"] == {"sentinel": 2}
    ep = FakeEp(sample={1: {"note": 0.13}})
    assert FF.check_sample_logits(per, ep) == (1, 0)
    ep = FakeEp(sample={1: {"note": 5.0}})
    assert FF.check_sample_logits(per, ep) == (1, 1)
    assert per[1]["texts_ok"] is False and per[1]["reason"] == "sample_logit_mismatch"


def test_recover_logits_missing_and_conflict():
    s = FF.sentinel
    acts = [dict(i=0, kind="exec", output='{"logits": [2.5]}\nv 1.000\n')]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 2], out=f'{{"logits": [{s(0)!r}]}}\nv {s(0):.3f}\n')],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["x"]),
                         dict(seq=2, tool="probe_query", status="ok", probe=1, texts=["y"])])
    per = FF.recover_from_replay(res, [call(1, 0, ["x"]), call(2, 1, ["y"])], FakeEp())
    # probe 0: the full-precision sentinel maps to 2.5, the 3-decimal one to 1.000: two values, so no logit
    assert per[0]["logits"] == [None] and per[0]["logit_src"] == {"none": 1}
    assert per[1]["texts_ok"] and per[1]["logits"] == [None] and per[1]["logits_ok"] is False


# ------------------------------------------------------------------------------------- recovery: actions

def test_apply_unified_diff():
    old = "a\nb\nc\nd\n"
    new = FF.apply_unified_diff(old, "@@ -2,2 +2,3 @@\n b\n-c\n+C\n+C2\n")
    assert new == "a\nb\nC\nC2\nd\n"
    with pytest.raises(ValueError):
        FF.apply_unified_diff(old, "@@ -2,1 +2,1 @@\n-zzz\n+y\n")


def test_actions_claude_and_codex(tmp_path):
    run = tmp_path / "b" / "r1"
    run.mkdir(parents=True)
    lines = [dict(type="assistant", cwd="/workdir/x", message=dict(content=[
        dict(type="tool_use", id="u1", name="Bash", input=dict(command="echo hi")),
        dict(type="tool_use", id="u2", name="Write", input=dict(file_path="/workdir/f", content="c"))])),
        dict(type="user", message=dict(content=[dict(type="tool_result", tool_use_id="u1",
                                                     content=[dict(type="text", text="hi\n")])]))]
    (run / "transcript_a.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    acts = FF.actions_of(run)
    assert [a["kind"] for a in acts] == ["exec", "write"]
    assert acts[0]["argv"] == ["bash", "-c", "echo hi"] and acts[0]["cwd"] == "/workdir/x"
    assert acts[0]["output"] == "hi\n" and acts[1]["i"] == 1
    run2 = tmp_path / "b" / "r2"
    run2.mkdir()
    items = [dict(type="CommandExecution", command=["/bin/bash", "-lc", "ls"], cwd="file:///workdir",
                  aggregated_output="x\n"),
             dict(type="FileChange", changes={"/workdir/a.py": dict(type="add", content="print(1)\n")})]
    (run2 / "codex_session_rollout-x.jsonl").write_text("".join(
        json.dumps(dict(type="event_msg", payload=dict(type="item_completed", item=it))) + "\n" for it in items))
    acts = FF.actions_of(run2)
    assert acts[0]["argv"] == ["/bin/bash", "-lc", "ls"] and acts[0]["cwd"] == "/workdir"
    assert acts[1]["kind"] == "change" and acts[1]["path"] == "/workdir/a.py"


# ------------------------------------------------------------------------------- recovery: fresh full text

def test_recover_from_fulltext(tmp_path):
    run = tmp_path / "b" / "r"
    run.mkdir(parents=True)
    texts = ["Hi Sam,\nabc", "def\n"]
    ft = [dict(seq=3, t=0, tool="probe_query", status="ok", probe=1, ids=None, latents=None, texts=texts,
               sha256=[S3.sha256_text(t) for t in texts], logits=[0.5, -1.0])]
    (run / "fulltext.jsonl").write_text("".join(json.dumps(x) + "\n" for x in ft))
    log = [dict(seq=3, tool="probe_query", charges={"probe_query": 2}, status="ok",
                args=dict(probe=1, texts=dict(n=2, chars=sum(map(len, texts)))))]
    (run / "log.jsonl").write_text("".join(json.dumps(x) + "\n" for x in log))
    logged, problem = FF.log_calls(run)
    assert problem is None and logged == [dict(seq=3, probe=1, n=2, chars=15)]
    per = FF.recover_from_fulltext(run, logged, FakeEp())
    assert per[1]["texts"] == texts and per[1]["logits"] == [0.5, -1.0] and per[0]["texts"] == []
    (run / "fulltext.jsonl").write_text("{torn\n")
    per = FF.recover_from_fulltext(run, logged, FakeEp())
    assert per[1]["texts_ok"] is False and per[0]["texts_ok"] is False
    (run / "log.jsonl").write_text(json.dumps({"event": "log capped"}) + "\n")
    assert FF.log_calls(run) == ([], "log_capped")


# --------------------------------------------------------------------- episode, slots, end-to-end replay

def synthetic_bank(tmp_path, name="ep901"):
    import test_toolserver as TS
    root = tmp_path / "bank" / name
    TS.make_episode(root)
    return tmp_path / "bank"


def test_episode_unit_and_aligned(tmp_path):
    bank = synthetic_bank(tmp_path)
    ep = FF.Episode(bank, "ep901")
    assert ep.substrate == "templated" and ep.n == 2
    lg = ep.sample_logits(0)
    with np.load(bank / "ep901" / "private" / "probe0.npz") as z:
        w, b = z["w"], float(z["b"])
    with np.load(bank / "ep901" / "private" / "probe0_sample_enc.npz") as z:
        ref = np.asarray(z["resid"], np.float64) @ w + b
    assert np.allclose(lg, ref)
    lab = np.array([t["label"] for t in ep.samples[0]])
    assert ep.unit(0) == pytest.approx(ref[lab == 1].mean() - ref[lab == 0].mean())
    assert isinstance(ep.aligned(0), list) and len(ep.corpus_rows()) == len(ep.corpus)


def write_run(run, grade, submission, budget=None):
    run.mkdir(parents=True, exist_ok=True)
    (run / "grade.json").write_text(json.dumps(grade))
    (run / "submission.json").write_text(json.dumps(submission))
    if budget:
        (run / "budget.json").write_text(json.dumps(budget))


def test_slots_of_run_outcome_and_f3(tmp_path):
    bank = synthetic_bank(tmp_path)
    ep = FF.Episode(bank, "ep901")
    run = tmp_path / "raw" / "bt" / "r1"
    grade = dict(hard_slots=[0], details=dict(probes=[
        dict(kind="planted", **{"pass": False}, checks=dict(identified=False, no_extra=True)),
        dict(kind="null", **{"pass": True})]),
        budget=dict(probe_query=dict(remaining=3), tool_calls=dict(remaining=10), forward=dict(remaining=7),
                    wall_clock_s=dict(remaining=600.0)))
    sub = dict(probes=[dict(probe=0, none=False, cues=[dict(regex="!", scope="any", latents=[])]),
                       dict(probe=1, none=True, cues=[])])
    write_run(run, grade, sub)
    per = {0: dict(texts_ok=True, logits_ok=True, texts=[], logits=[], reason=None),
           1: dict(texts_ok=False, logits_ok=False, texts=[], logits=[], reason="call_mismatch")}
    row = dict(run="r1", batch="bt", agent="gpt", arm="open8", episode="ep901")
    slots = FF.slots_of_run(row, run, ep, per)
    assert [s["failed"] for s in slots] == [1, 0] and [s["hard"] for s in slots] == [1, 0]
    assert slots[0]["flags"]["F2"] == 1 and slots[0]["flags"]["F1"] == 0  # no texts: nothing measured
    assert slots[1]["flags"]["F2n"] is None and slots[1]["flags"]["combined"] is None
    assert slots[0]["F3"] == dict(queries_unused=3, calls_left=10, forward_left=7, minutes_left=10.0)
    (run / "submission.json").unlink()
    assert FF.slots_of_run(row, run, ep, per) == []  # nothing answered


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bubblewrap not installed")
def test_replay_end_to_end(tmp_path):
    bank = synthetic_bank(tmp_path)
    ep = FF.Episode(bank, "ep901")
    run = tmp_path / "raw" / "bt" / "r1"
    run.mkdir(parents=True)
    shutil.copyfile(bank / "ep901" / "private" / "perm.npy", run / "perm.npy")
    t_a = ["Hello there.", "A second note!"]
    t_b = [ep.samples[1][0]["text"].lower()]
    py = ("import json, subprocess\n"
          "s = json.load(open('/workdir/public/probe1_sample.json'))['texts']\n"
          "t = [s[0]['text'].lower()]\n"
          "r = json.loads(subprocess.run(['tool', 'probe_query', json.dumps({'probe': 1, 'texts': t})],"
          " capture_output=True, text=True).stdout)\n"
          "print('logit %.3f' % r['logits'][0])\n")
    entries = [
        dict(type="assistant", cwd="/workdir", message=dict(content=[dict(
            type="tool_use", id="u1", name="Write",
            input=dict(file_path="/workdir/q.json", content=json.dumps({"probe": 0, "texts": t_a})))])),
        dict(type="assistant", cwd="/workdir", message=dict(content=[dict(
            type="tool_use", id="u2", name="Bash", input=dict(command='tool probe_query "$(cat q.json)"'))])),
        dict(type="user", message=dict(content=[dict(type="tool_result", tool_use_id="u2",
                                                     content='{\n  "logits": [1.2345678901234, -0.5]\n}')])),
        dict(type="assistant", cwd="/workdir/sub", message=dict(content=[dict(
            type="tool_use", id="u3", name="Bash", input=dict(command="python3 - <<'EOF'\n" + py + "EOF"))])),
        dict(type="user", message=dict(content=[dict(type="tool_result", tool_use_id="u3",
                                                     content="logit 0.123\n")])),
        dict(type="assistant", cwd="/workdir", message=dict(content=[dict(
            type="tool_use", id="u4", name="Bash", input=dict(command="ls /bankep"))]))]
    (run / "transcript_x.jsonl").write_text("".join(json.dumps(x) + "\n" for x in entries))
    log = [dict(seq=1, tool="budget", peer_uid=0, charges={}, status="ok", args={}),
           dict(seq=2, tool="probe_query", peer_uid=1000, status="ok",
                args=dict(probe=0, texts=dict(n=2, chars=sum(map(len, t_a))))),
           dict(seq=3, tool="probe_query", peer_uid=1000, status="ok",
                args=dict(probe=1, texts=dict(n=1, chars=len(t_b[0]))))]
    (run / "log.jsonl").write_text("".join(json.dumps(x) + "\n" for x in log))
    res = FF.replay_run(run, ep, "ep901-open", tmp_path / "work", action_timeout_s=60, run_timeout_s=120)
    assert not res.get("error"), res.get("stderr")
    logged, _ = FF.log_calls(run)
    per = FF.recover_from_replay(res, logged, ep)
    assert per[0]["texts"] == t_a and per[0]["logits"] == [pytest.approx(1.2345678901234), -0.5]
    assert per[1]["texts"] == t_b and per[1]["logits"] == [0.123]
    assert [r["seq"] for r in res["log"] if "seq" in r][:3] == [1, 2, 3]
    # only the stored probes and sample encodings of the bank are visible, never its answer or grids
    assert res["results"][-1]["out"].split() == ["probe0.npz", "probe0_sample_enc.npz", "probe1.npz",
                                                  "probe1_sample_enc.npz"]
    # the sandbox has no network and does not see the host's home directory
    assert not (tmp_path / "work" / "workdir" / "home").exists()


def test_printed_texts_map_replay_to_real():
    acts = [dict(i=0, kind="exec", output="CHOSEN\n0 'p0 off' 'Hi Sam,\\nreal one'\n0 'p0 on' 'real two!'\n"),
            dict(i=1, kind="exec", output='{"logits": [1.5, 2.5]}\n')]
    res = dict(actions=acts, results=[
        dict(i=0, seq=[1, 0], out="CHOSEN\n0 'p0 off' 'Hi Al,\\nfake one'\n0 'p0 on' 'fake 2!'\n"),
        dict(i=1, seq=[1, 1], out="{}")],
        fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["Hi Al,\nfake one", "fake 2!"])])
    rec = FF.apply_printed_texts(FF.replay_calls(res), res)
    assert rec[0]["texts"] == ["Hi Sam,\nreal one", "real two!"] and rec[0]["text_src"] == "printed"
    # a text printed nowhere: the call keeps its replay texts
    res["results"][0]["out"] = "CHOSEN\n0 'p0 off' 'Hi Al,\\nfake one'\n"
    rec = FF.apply_printed_texts(FF.replay_calls(res), res)
    assert rec[0]["texts"] == ["Hi Al,\nfake one", "fake 2!"] and rec[0]["text_src"] == "replay"


def test_printed_texts_conflict_and_skeleton():
    acts = [dict(i=0, kind="exec", output="a 'X1'\nb 'X2'\n")]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 1], out="a 'T'\nb 'T'\n")],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["T"])])
    assert FF.printed_texts(res, 0, ["T"], {}) == {}  # one replay text, two real values
    res["results"][0]["out"] = "zz 'T'\n"
    assert FF.printed_texts(res, 0, ["T"], {}) == {}  # no line with the same skeleton
    res["results"][0]["out"] = 'a "T"\n'
    res["actions"][0]["output"] = 'a "R\\u00e9"\n'
    assert FF.printed_texts(res, 0, ["T"], {}) == {"T": "Ré"}  # JSON quoting


def test_reply_alone_gives_no_logit():
    acts = [dict(i=0, kind="exec", output='{"logits": [2.5]}\n')]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 1], out="done\n")],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["x"])])
    per = FF.recover_from_replay(res, [call(1, 0, ["x"])], FakeEp())
    assert per[0]["texts_ok"] and per[0]["logits"] == [None] and per[0]["logits_ok"] is False


def test_sample_logit_tolerance():
    per = {0: dict(texts_ok=True, logits_ok=True, texts=["n"], logits=[1.10], reason=None)}
    assert FF.check_sample_logits(per, FakeEp(n=1, sample={0: {"n": 1.0}})) == (1, 0)  # batching noise
    assert FF.check_sample_logits(per, FakeEp(n=1, sample={0: {"n": 1.3}})) == (1, 1)


def test_sentinel_and_reply_must_agree():
    s = FF.sentinel
    acts = [dict(i=0, kind="exec", output='v 1.000\n{"logits": [2.5]}\n')]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 1], out=f'v {s(0):.3f}\ndone\n')],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["x"])])
    per = FF.recover_from_replay(res, [call(1, 0, ["x"])], FakeEp())
    assert per[0]["logits"] == [None] and per[0]["logit_src"] == {"conflict": 1}
    acts[0]["output"] = 'v 2.500\n{"logits": [2.5]}\n'
    per = FF.recover_from_replay(res, [call(1, 0, ["x"])], FakeEp())
    assert per[0]["logits"] == [2.5] and per[0]["logit_src"] == {"sentinel": 1}


def test_table_applicability():
    def s(answered, f2, f2n, failed):
        return dict(failed=failed, flags=dict(answered=answered, F1=0, F2=f2, F2n=f2n, combined=0, count=0),
                    F3={})
    slots = [s("named", 1, None, 1), s("named", None, None, 0), s("none", None, 1, 1), s("none", None, 0, 0)]
    t = FF.table2x2(slots, "F2")
    assert t["n_applicable"] == 2 and t["missing"] == 1 and t["flag_failed"] == 1
    t = FF.table2x2(slots, "F2n")
    assert t["n_applicable"] == 2 and t["missing"] == 0 and (t["flag_failed"], t["noflag_passed"]) == (1, 1)
    assert FF.table2x2(slots, "F1")["n_applicable"] == 4


# ------------------------------------------------------------------- after review (FREEZE change 4)

def test_sentinel_trailing_zero_and_plus_sign():
    s = FF.sentinel
    rep = f"vals {[round(s(0), 3), round(s(1), 3)]}\n"
    assert FF.sentinel_logits(rep, "vals [1.975, 2.49]\n", [0, 1]) == {0: (1.975, 3), 1: (2.49, 3)}
    rep = f"old=+{s(0):.3f} new={s(1):+.3f}\n"
    assert FF.sentinel_logits(rep, "old=+1.250 new=-2.739\n", [0, 1]) == {0: (1.25, 3), 1: (-2.739, 3)}


SAMPLE_A = "Hi all,\nThe sample note about a garden plot.\nBest,\nSam"
SAMPLE_B = "Morning,\nAnother sample note about the harbour.\nCheers,\nAl"


def test_raw_printed_pairs_between_anchors():
    rep_t = ["Hi all,\nA replay text that the fake encoder chose.\nBest,\nSam",
             "Hey,\nA second replay text, chosen the same way.\nAl"]
    real_t = ["Hi all,\nThe agent's real text, which differs.\nBest,\nSam",
              "Hey,\nIts real second text, longer than the replay's one.\nAl"]
    rep = (f"stats 1.25 n 64\n\nQUERY 0 id 12 pred 1.105\nOLD: {SAMPLE_A}\nNEW: {rep_t[0]}\n\n"
           f"QUERY 1 id 65 pred 4.499\nOLD: {SAMPLE_A}\nNEW: {rep_t[1]}\n")
    real = (f"stats 0.75 n 64\n\nQUERY 0 id 19 pred 0.246\nOLD: {SAMPLE_B}\nNEW: {real_t[0]}\n\n"
            f"QUERY 1 id 126 pred 2.973\nOLD: {SAMPLE_B}\nNEW: {real_t[1]}\n")
    holes = set(rep_t) | {SAMPLE_A, SAMPLE_B}
    assert FF.raw_printed_pairs(rep, real, set(rep_t), holes) == list(zip(rep_t, real_t))
    # the sample notes are not holes: the glue holds a differing note, nothing maps
    assert FF.raw_printed_pairs(rep, real, set(rep_t), set(rep_t)) == []
    # the real output has one block fewer: the ordinals cannot be matched, nothing maps
    real2 = real.split("\n\nQUERY 1")[0] + "\n"
    assert FF.raw_printed_pairs(rep, real2, set(rep_t), holes) == []
    # glue without anchoring characters (texts printed back to back): nothing maps
    assert FF.raw_printed_pairs("\n".join(rep_t) + "\n", "\n".join(real_t) + "\n", set(rep_t), set(rep_t)) == []
    # a text inside quotes is left to the literal mapping
    assert FF.raw_printed_pairs(f"text: '{rep_t[0]}' done\n", f"text: '{real_t[0]}' done\n",
                                {rep_t[0]}, {rep_t[0]}) == []


def test_raw_printed_texts_recover_a_call():
    rep_t, real_t = "Replay text number one, long enough.", "The real text, also long enough!"
    acts = [dict(i=0, kind="exec", output=f"=== probe 0 id 3\n{real_t}\n--- end\n"),
            dict(i=1, kind="exec", output='{"logits": [1.5]}\n')]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 0], out=f"=== probe 0 id 7\n{rep_t}\n--- end\n"),
                                      dict(i=1, seq=[1, 1], out="{}")],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=[rep_t])])
    rec = FF.apply_printed_texts(FF.replay_calls(res), res)
    assert rec[0]["texts"] == [real_t] and rec[0]["text_src"] == "printed"


def test_recover_from_replay_call_mismatch_makes_probe_missing():
    s = FF.sentinel
    acts = [dict(i=0, kind="exec", output="a 0.500\nb 0.250\n")]
    res = dict(actions=acts, results=[dict(i=0, seq=[1, 2], out=f"a {s(0):.3f}\nb {s(1):.3f}\n")],
               fulltext=[dict(seq=1, tool="probe_query", status="ok", probe=0, texts=["aa"]),
                         dict(seq=2, tool="probe_query", status="ok", probe=1, texts=["bbb"])])
    per = FF.recover_from_replay(res, [call(1, 0, ["aa"]), call(2, 1, ["bbbb"])], FakeEp())
    assert per[0]["texts_ok"] and per[0]["logits"] == [0.5]
    assert per[1]["texts_ok"] is False and per[1]["reason"] == "call_mismatch" and per[1]["texts"] == []
    f = flags({"none": True, "cues": []}, texts_ok=per[1]["texts_ok"], logits_ok=per[1]["logits_ok"])
    assert (f["F1"], f["F2n"], f["combined"]) == (None, None, None)


def test_verdict_boundaries():
    assert FF.verdict(dict(diff=0.30, fisher_p=0.049)) == "supported"
    assert FF.verdict(dict(diff=0.30, fisher_p=0.05)) == "weak"
    assert FF.verdict(dict(diff=0.2999, fisher_p=0.001)) == "weak"
    assert FF.verdict(dict(diff=0.10, fisher_p=0.9)) == "weak"
    assert FF.verdict(dict(diff=0.0999, fisher_p=0.001)) == "dead"


def test_topic_needs_zero_on_the_other_topic():
    vocab = {"chess": {"rook": 3, "bishop": 2}, "fishing": {"trout": 4}}
    pair = ["chess", "fishing"]
    assert FF.topic_scores("rook, bishop and a trout", pair, "freetext", vocab) == (2, 1)
    assert FF.topic_of("rook, bishop and a trout", pair, "freetext", vocab) is None


def test_unknown_topics_never_pair():
    assert FF.clean_pairs([(0, 0), (1, 0)], [None, None]) == []
    assert FF.clean_pairs([(0, 0), (1, 0)], [0, 0]) == [(0, 1, 0)]


def test_F2_uses_the_cue_scope():
    def m(regex, scope, texts):
        return [("X" in t) if scope == "any" else False for t in texts], None
    rows, texts = [(0,), (1,)], ["a", "a X"]
    any_ = FF.slot_flags({"none": False, "cues": [{"regex": "X", "scope": "any"}]}, texts, [0, 1], [0, 0], rows,
                         1.0, {0}, [], True, True, m)
    first = FF.slot_flags({"none": False, "cues": [{"regex": "X", "scope": "first"}]}, texts, [0, 1], [0, 0], rows,
                          1.0, {0}, [], True, True, m)
    assert any_["F2"] == 0 and first["F2"] == 1


def test_coverage_at_the_bar():
    truth = [1] * 5 + [0] * 5
    texts = [str(i) for i in range(10)]
    rows = [(t,) for t in truth]
    exact = fake_match({"r": lambda t: t in "0123" or t == "9"})  # BA (4/5 + 4/5) / 2 = 0.8
    assert FF.covered_columns([{"regex": "r", "scope": "any"}], texts, rows, exact) == {0}
    absent = fake_match({"r": lambda t: t in "4" or t in "5678"})  # BA 0.2: absence detected at 0.8
    assert FF.covered_columns([{"regex": "r", "scope": "any"}], texts, rows, absent) == {0}
    texts20 = [str(i) for i in range(20)]
    rows20 = [(1,)] * 10 + [(0,)] * 10
    below = fake_match({"r": lambda t: int(t) < 8 or int(t) in (18, 19)})  # (0.8 + 0.8) / 2 = 0.8
    assert FF.covered_columns([{"regex": "r", "scope": "any"}], texts20, rows20, below) == {0}
    below = fake_match({"r": lambda t: int(t) < 8 or int(t) in (17, 18, 19)})  # (0.8 + 0.7) / 2 = 0.75
    assert FF.covered_columns([{"regex": "r", "scope": "any"}], texts20, rows20, below) == set()


def test_missing_bounds_and_forced_f2n():
    def s(flag, failed):
        return dict(failed=failed, flags=dict(F1=None, F2=None, F2n=None, combined=flag, count=None))
    slots = [s(1, 1), s(1, 0), s(0, 0), s(None, 1), s(None, 0)]
    b = FF.missing_bounds(slots)
    assert (b["all_flagged"]["flag_failed"], b["all_flagged"]["flag_passed"]) == (2, 2)
    assert (b["none_flagged"]["noflag_failed"], b["none_flagged"]["noflag_passed"]) == (1, 2)
    assert b["largest_difference"]["diff"] == pytest.approx(1 - 1 / 3)
    assert b["smallest_difference"]["diff"] == pytest.approx(0.5 - 2 / 3)

    def n(n_texts, aligned, f2n, failed=1):
        return dict(failed=failed, flags=dict(answered="none", n_texts=n_texts, F2n=f2n),
                    private=dict(aligned=["c"] * aligned))
    fz = FF.f2n_forced([n(8, 8, 1), n(9, 8, 0, 0), n(0, 2, 1), n(None, 8, None)])
    assert (fz["none_slots_known"], fz["forced_by_count"], fz["F2n_1"]) == (3, 2, 2)
    assert (fz["none_slots"], fz["none_slots_failed"]) == (4, 3)


def test_slots_of_run_normalises_texts(tmp_path):
    bank = synthetic_bank(tmp_path)
    ep = FF.Episode(bank, "ep901")
    run = tmp_path / "raw" / "bt" / "r1"
    grade = dict(hard_slots=[0], details=dict(probes=[dict(kind="null", **{"pass": True})] * 2))
    sub = dict(probes=[dict(probe=0, none=True, cues=[]), dict(probe=1, none=True, cues=[])])
    write_run(run, grade, sub)
    per = {0: dict(texts_ok=True, logits_ok=True, texts=["A note.\r\n\n", "A note!"], logits=[0.0, 1.0],
                   reason=None), 1: dict(texts_ok=True, logits_ok=True, texts=[], logits=[], reason=None)}
    row = dict(run="r1", batch="bt", agent="gpt", arm="open8", episode="ep901")
    s0 = FF.slots_of_run(row, run, ep, per)[0]
    assert s0["private"]["text_sha256"] == [FF.sha256_text("A note."), FF.sha256_text("A note!")]


def test_raw_printed_pairs_output_without_trailing_newline():
    rep_t = ["A replay text for the off side, long enough.", "A replay text for the on side, long enough!"]
    real_t = ["The real off text, of another length.", "The real on text, of another length too!"]
    rep = f"=== probe 1 base 45\n{rep_t[0]}\n--- on:\n{rep_t[1]}\n"
    real = f"=== probe 1 base 67\n{real_t[0]}\n--- on:\n{real_t[1]}"  # the transcript dropped the newline
    assert FF.raw_printed_pairs(rep, real, set(rep_t), set(rep_t)) == list(zip(rep_t, real_t))


def test_raw_printed_pairs_ignore_the_cwd_note():
    t = "A text printed last in the output, long enough."
    rep = f"=== probe 2 base 3\n{t}\n"
    real = f"=== probe 2 base 3\n{t}\nShell cwd was reset to /workdir"
    assert FF.raw_printed_pairs(rep, real, {t}, {t}) == [(t, t)]
