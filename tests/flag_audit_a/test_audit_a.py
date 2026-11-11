"""Flag audit A (docs/FLAG_AUDIT_A.md): the frozen scripts/failure_flags.py run on synthetic fixtures with
hand-derived expectations (expected.json, written before any flag code ran on the fixtures).

  test_d36_flag            failure_flags' F1, F2, F2n, combined, count, F3 and the outcome vs expected.json;
                           xfail(strict) where the frozen code disagrees with the written definition (a finding).
  test_d36_proposed        the audit's proposed resolutions of definition problems vs the frozen code;
                           xfail(strict) by construction (the code implements the definition as written).
  test_followup_oracle     the audit's reference reading (audit_a_oracle.py) reproduces expected.json for F1a, F1a-loose,
                           the T-flags and F4: a consistency check of the JSON, not of any implementation.
  test_followup_impl       an implementation of DEFINITIONS §1-§3 vs expected.json, when one is named by the
                           environment variable FLAG_AUDIT_A_IMPL="module:function" (README.md); skipped otherwise.
  test_replay_sample_note  the replay path's sample-note check on the fixture episode.

The fixtures are committed; tests/flag_audit_a/audit_a_build.py rebuilds them (test_fixtures_reproducible).
"""
import importlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(ROOT / "scripts"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import failure_flags as FF  # noqa: E402
import s3_coder as S3  # noqa: E402

EXPECTED = json.loads((HERE / "expected.json").read_text())
FIX = {f["id"]: f for f in EXPECTED["fixtures"]}
D36 = ("F1", "F2", "F2n", "combined", "count", "F3")
FOLLOWUP = ("F1a", "F1a-loose", "T-F2", "T-D", "T-RULE", "T-F2L", "T-DL", "T-RULEL", "F4")

# (fixture, flag) -> reason: the frozen code disagrees with the written definition
FINDINGS = {
    ("f11a_threshold_exactly_0_15", "F1"): "F1 compares |effect| >= 0.15 with no tolerance (failure_flags.py:299): "
                                           "logits 0.51 / 2.01 give 1.4999999999999998 / 10 < 0.15",
    ("f11a_threshold_exactly_0_15", "combined"): "follows from the F1 threshold finding",
    ("f11a_threshold_exactly_0_15", "count"): "follows from the F1 threshold finding",
    ("f14_f3_budget_after_submit", "F3"): "F3 minutes_left is read from the last budget.json write "
                                          "(failure_flags.py:1283-1290), which a free call after the submit "
                                          "rewrites with a later wall clock; D36 asks for minutes left at submission",
}

_CACHE = {}


def code_slot(fid):
    """failure_flags' slot record for a fixture, through the fresh-run path run() uses (log_calls ->
    recover_from_fulltext -> slots_of_run)."""
    if fid not in _CACHE:
        fx = FIX[fid]
        ep = FF.Episode(HERE / fx["bank"], fx["episode"])
        run = HERE / fx["run_dir"]
        logged, problem = FF.log_calls(run)
        if problem:
            per = {j: dict(texts_ok=False, logits_ok=False, texts=[], logits=[], reason=problem) for j in range(ep.n)}
        else:
            per = FF.recover_from_fulltext(run, logged, ep)
        row = dict(run=fid, batch="audit_a", agent="synthetic", arm="open8", episode=fx["episode"])
        slots = FF.slots_of_run(row, run, ep, per)
        _CACHE[fid] = slots[fx["probe"]]
    return _CACHE[fid]


def code_value(slot, flag):
    if flag == "F3":
        return dict(slot["F3"])
    return slot["flags"][flag]


def want_value(exp):
    """The code's encoding of an expectation: a value, or None for missing / not applicable / not computable."""
    return exp["value"] if exp["status"] == "value" else None


def _params(flags, with_findings=True):
    out = []
    for fid, fx in FIX.items():
        for flag in flags:
            if flag not in fx["expected"]:
                continue
            marks = []
            if with_findings and (fid, flag) in FINDINGS:
                marks = [pytest.mark.xfail(strict=True, reason=FINDINGS[(fid, flag)])]
            out.append(pytest.param(fid, flag, marks=marks, id=f"{fid}-{flag}"))
    return out


@pytest.mark.parametrize("fid,flag", _params(D36))
def test_d36_flag(fid, flag):
    exp = FIX[fid]["expected"][flag]
    got = code_value(code_slot(fid), flag)
    want = want_value(exp)
    if isinstance(want, dict):
        assert got == pytest.approx(want), exp["reason"]
    else:
        assert got == want, exp["reason"]


@pytest.mark.parametrize("fid", list(FIX))
def test_outcome_and_hard(fid):
    s = code_slot(fid)
    assert (s["failed"], s["hard"]) == (FIX[fid]["failed"], FIX[fid]["hard"])


def _proposed():
    out = []
    for fid, fx in FIX.items():
        for flag in D36:
            alt = (fx["expected"].get(flag) or {}).get("alt")
            if alt and alt.get("kind") == "proposed":
                out.append(pytest.param(fid, flag, alt, id=f"{fid}-{flag}", marks=[pytest.mark.xfail(
                    strict=True, reason="definition problem: the frozen code implements the written rule; "
                                        "alt = the audit's proposed resolution (" + alt["under"] + ")")]))
    return out


@pytest.mark.parametrize("fid,flag,alt", _proposed())
def test_d36_proposed(fid, flag, alt):
    assert code_value(code_slot(fid), flag) == (alt["value"] if alt["status"] == "value" else None)


_ORACLE = {}


@pytest.mark.parametrize("fid,flag", _params(FOLLOWUP, with_findings=False))
def test_followup_oracle(fid, flag):
    import audit_a_oracle as oracle
    if fid not in _ORACLE:
        _ORACLE[fid] = oracle.slot(FIX[fid])
    exp = FIX[fid]["expected"][flag]
    got = _ORACLE[fid][flag]
    assert (got["status"], got["value"]) == (exp["status"], exp["value"]), exp["reason"]


def _impl():
    spec = os.environ.get("FLAG_AUDIT_A_IMPL")
    if not spec:
        return None
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn)


@pytest.mark.parametrize("fid,flag", _params(FOLLOWUP, with_findings=False))
def test_followup_impl(fid, flag):
    impl = _impl()
    if impl is None:
        pytest.skip("no implementation named (FLAG_AUDIT_A_IMPL=module:function)")
    fx = FIX[fid]
    got = impl(HERE / fx["run_dir"], HERE / fx["bank"], fx["episode"], fx["probe"])[flag]
    exp = fx["expected"][flag]
    assert (got["status"], got["value"]) == (exp["status"], exp["value"]), exp["reason"]


# ------------------------------------------------------------------------- replay path: sample notes

def _sample_note():
    facts = json.loads((HERE / "fixtures" / "facts.json").read_text())
    ep = FF.Episode(HERE / "fixtures" / "bank", "epA")
    sid = facts["sample_note_used_as_base"]["id"]
    return ep, ep.samples[0][sid]["text"]


def test_replay_sample_note_counts_with_its_recovered_logit():
    ep, s = _sample_note()
    per = {0: dict(texts_ok=True, logits_ok=True, texts=[s], logits=[5.04], reason=None)}
    assert FF.check_sample_logits(per, ep) == (1, 0)          # 0.04 from the stored 5.00: within 0.15
    assert per[0]["logits"] == [5.04] and per[0]["texts_ok"]   # the recovered (returned) logit is kept
    per = {0: dict(texts_ok=True, logits_ok=True, texts=[s], logits=[5.2], reason=None)}
    assert FF.check_sample_logits(per, ep) == (1, 1) and per[0]["reason"] == "sample_logit_mismatch"


@pytest.mark.xfail(strict=True, reason="low: the sample-note check keys on the raw recovered text "
                                       "(failure_flags.py:1243), while the flags use the D19-normalised text; a "
                                       "sample note sent with a trailing newline is coded as that note but its "
                                       "logit escapes the check")
def test_replay_sample_note_check_after_normalisation():
    ep, s = _sample_note()
    per = {0: dict(texts_ok=True, logits_ok=True, texts=[s + "\n"], logits=[-5.0], reason=None)}  # wrong class
    assert FF.check_sample_logits(per, ep) == (1, 1)


def test_fixtures_reproducible(tmp_path, monkeypatch):
    """The committed fixtures are what build_fixtures.py writes (text files compared byte for byte)."""
    import audit_a_build as BF
    monkeypatch.setattr(BF, "OUT", tmp_path / "fixtures")
    BF.main()
    for p in sorted((HERE / "fixtures").rglob("*")):
        if p.is_file() and p.suffix in (".json", ".jsonl"):
            q = tmp_path / "fixtures" / p.relative_to(HERE / "fixtures")
            assert q.read_text() == p.read_text(), p
