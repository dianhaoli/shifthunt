"""scripts/s3_coder.py: the S3 coder ("true cue varied cleanly", plan §5, decision D19).

Synthetic logs only: every run directory here is written by the test into tmp_path, with notes rendered by the
tracked generators (shifthunt.textgen, shifthunt.freetext and its tracked paragraph bank). No raw run data, no
torch, no network.
"""
import csv
import hashlib
import itertools
import json
import os
import random
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import s3_coder as S3  # noqa: E402
from shifthunt import detectors, freetext as FT, textgen as TG  # noqa: E402

TMPL, FTX = "templated", "freetext"
CUES = TG.make_cues(random.Random(0))
ALL_NAMES = set(TG.FEATURES) | set(FT.FEATURES)
COLS = ["m", "p", "x", "y", "z"]  # synthetic columns: main, parent (when nested), three others


def tmpl_note(seed=1, topic="chess", **levels):
    return TG.render(topic, levels, CUES, seed)[0]


def ft_note(seed=1, topic="chess", **levels):
    return FT.render(topic, levels, None, seed)[0]


def s3(rows, main="m", parent=None, cols=COLS):
    return S3.s3_from_flags(rows, cols, main, parent)


# ---------------------------------------------------------------------------------------------------------
# clause (a): the pair

def test_pair_single_property():
    r = s3([[0, 1, 0, 1, 0], [1, 1, 0, 1, 0]])
    assert (r["s3a"], r["s3"], r["pair"], r["pair_other"], r["main_varies"]) == (1, 1, [0, 1], None, 1)
    r = s3([[0, 1, 0, 1, 0], [1, 1, 0, 1, 0]], parent="p")  # nested, parent on in both
    assert (r["s3a"], r["pair"], r["n_parent_on"]) == (1, [0, 1], 2)


def test_pair_main_plus_one_other():
    r = s3([[0, 1, 0, 1, 0], [1, 1, 1, 1, 0]])
    assert (r["s3a"], r["pair"], r["pair_other"]) == (1, [0, 1], "x")
    assert r["s3b"] == 0 and r["s3"] == 1  # on these two texts the main equals x: only the pair clause holds
    r = s3([[0, 1, 0, 1, 0], [1, 1, 1, 1, 0]], parent="p")
    assert (r["s3a"], r["pair_other"]) == (1, "x")


def test_pair_main_plus_two_others():
    r = s3([[0, 1, 0, 1, 0], [1, 1, 1, 0, 0]])
    assert (r["s3a"], r["pair"], r["s3b"], r["s3"]) == (0, None, 0, 0)


def test_pair_main_plus_parent():
    rows = [[0, 0, 0, 1, 0], [1, 1, 0, 1, 0]]  # differ in the main and in its parent only
    r = s3(rows, parent="p")
    assert (r["s3a"], r["s3b"], r["s3"], r["n_parent_on"]) == (0, 0, 0, 1)
    assert s3(rows)["s3a"] == 1  # the same flags without a parent relation: p is just one other property


def test_pair_nested_parent_off_in_one_or_both_texts():
    # parent off in BOTH texts (not something the generator can render, but the rule is explicit)
    r = s3([[0, 0, 0, 1, 0], [1, 0, 0, 1, 0]], parent="p")
    assert (r["s3a"], r["s3b"], r["s3"], r["n_parent_on"]) == (0, 0, 0, 0)
    # parent off in one text, with a third text that has the parent on but the same main level: no pair
    r = s3([[0, 0, 0, 1, 0], [1, 1, 0, 1, 0], [1, 1, 1, 1, 0]], parent="p")
    assert (r["s3a"], r["s3b"], r["s3"]) == (0, 0, 0)


def test_pair_identical_texts_and_too_few():
    assert s3([[1, 1, 0, 1, 0]] * 4)["s3"] == 0
    assert s3([[1, 1, 0, 1, 0]] * 4)["main_varies"] == 0
    one = s3([[1, 1, 0, 1, 0]])
    assert (one["n"], one["s3a"], one["s3b"], one["s3"]) == (1, 0, 0, 0)
    none = s3([])
    assert (none["n"], none["s3"], none["main_varies"], none["pair"]) == (0, 0, 0, None)


def test_pair_witness_prefers_main_only_pair():
    rows = [[0, 1, 0, 0, 0], [1, 1, 1, 0, 0], [1, 1, 0, 0, 0]]
    r = s3(rows)
    assert (r["pair"], r["pair_other"]) == ([0, 2], None)  # (0, 1) differs in x too


def _naive_pair(rows, m, p):
    for a, b in itertools.combinations(rows, 2):
        diff = {k for k in range(len(a)) if a[k] != b[k]}
        if m in diff and len(diff - {m}) <= 1 and p not in diff and (p is None or (a[p] == 1 and b[p] == 1)):
            return 1
    return 0


def test_pair_clause_against_naive_rule():
    rng = random.Random(3)
    seen = set()
    for _ in range(3000):
        n = rng.randrange(0, 10)
        rows = [[rng.randrange(2) for _ in COLS] for _ in range(n)]
        nested = rng.random() < 0.5
        if nested:
            for r in rows:
                r[0] &= r[1]  # a child needs its parent
        got = s3(rows, parent="p" if nested else None)
        assert got["s3a"] == (_naive_pair(rows, 0, 1 if nested else None) if n >= 2 else 0)
        seen.add((nested, got["s3a"], got["s3b"]))
    assert {(n, a, b) for n in (False, True) for a in (0, 1) for b in (0, 1)} <= seen  # every combination occurs


# ---------------------------------------------------------------------------------------------------------
# clause (b): identifiability

def test_identifiable_base_plus_single_flips():
    base = [0, 1, 0, 1, 0]
    rows = [base] + [[v ^ (k == j) for k, v in enumerate(base)] for j in (0, 2, 3, 4)]
    r = s3(rows)
    assert (r["s3b"], r["s3"], r["rank_with"], r["rank_without"]) == (1, 1, 5, 4)
    assert s3(rows, parent="p")["s3b"] == 1


def test_identifiable_without_any_clean_pair():
    cols = ["m", "w", "x", "y", "z"]
    rows = [[0, 0, 0, 0, 0], [0, 1, 1, 1, 1], [1, 1, 1, 0, 0], [1, 0, 0, 1, 1]]
    r = s3(rows, cols=cols)  # every pair that differs in the main differs in two others
    assert (r["s3a"], r["s3b"], r["s3"]) == (0, 1, 1)


def test_main_always_flipped_with_one_other_property():
    rows = [[0, 1, 0, 0, 0], [1, 1, 1, 1, 0], [0, 1, 0, 1, 1], [1, 1, 1, 0, 1]]  # main == x in every text
    r = s3(rows)
    assert (r["s3b"], r["rank_with"], r["rank_without"]) == (0, 4, 4)
    assert (r["s3a"], r["s3"]) == (0, 0)  # and no pair: the texts that differ in the main differ in x and y or z
    inv = [[1 - r_[0]] + r_[1:] for r_ in rows]  # main == 1 - x: still in the span (constant minus x)
    assert s3(inv)["s3b"] == 0
    # the pair clause is separate: main and x flipped together, nothing else, counts under (a) only
    r = s3([[0, 1, 0, 0, 0], [1, 1, 1, 0, 0]])
    assert (r["s3a"], r["s3b"], r["s3"]) == (1, 0, 1)


def test_main_constant():
    rng = random.Random(5)
    for level in (0, 1):
        rows = [[level] + [rng.randrange(2) for _ in range(4)] for _ in range(12)]
        r = s3(rows)
        assert (r["main_varies"], r["s3a"], r["s3b"], r["s3"]) == (0, 0, 0, 0)


def test_nested_main_varies_only_with_parent():
    rng = random.Random(6)
    rows = []
    for _ in range(16):
        on = rng.randrange(2)
        rows.append([on, on] + [rng.randrange(2) for _ in range(3)])  # main == parent in every text
    r = s3(rows, parent="p")
    assert (r["main_varies"], r["s3a"], r["s3b"], r["s3"]) == (1, 0, 0, 0)
    assert s3(rows)["s3b"] == 0  # also without the relation: the main equals another column


def test_nested_main_uses_parent_on_texts_only():
    # over all texts the child is not in the span of the others, but among parent-on texts it equals x
    rows = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0], [0, 1, 0, 1, 1], [1, 1, 1, 1, 1], [0, 1, 0, 0, 1]]
    assert s3(rows, parent="p")["s3b"] == 0
    assert s3(rows)["s3b"] == 1
    rows.append([1, 1, 0, 0, 0])  # one parent-on text where the child is on without x
    assert s3(rows, parent="p")["s3b"] == 1


def test_random_64_text_design():
    rng = random.Random(64)
    cols = list(FT.FEATURES)
    rows = [[rng.randrange(2) for _ in cols] for _ in range(64)]
    m, p = cols.index("ps_question"), cols.index("postscript")
    for r in rows:
        r[m] &= r[p]
    got = S3.s3_from_flags(rows, cols, "ps_question", "postscript")
    assert (got["s3b"], got["s3"]) == (1, 1) and got["n_parent_on"] == sum(r[p] for r in rows)
    plain = S3.s3_from_flags(rows, cols, "weekday", None)
    assert (plain["s3b"], plain["s3"]) == (1, 1) and plain["rank_with"] == 16 and plain["rank_without"] == 15


def _fraction_rank(rows):
    M = [[Fraction(int(x)) for x in r] for r in rows]
    rank = 0
    for c in range(len(M[0]) if M else 0):
        piv = next((i for i in range(rank, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        M[rank] = [x / M[rank][c] for x in M[rank]]
        for i in range(len(M)):
            if i != rank and M[i][c] != 0:
                M[i] = [x - M[i][c] * y for x, y in zip(M[i], M[rank])]
        rank += 1
    return rank


def test_rank_agrees_with_exact_arithmetic_and_numpy():
    rng = np.random.default_rng(20261112)
    n_deficient = 0
    for trial in range(300):
        n, k = int(rng.integers(1, 65)), int(rng.integers(1, 21))
        A = rng.integers(0, 2, size=(n, k))
        if trial % 3 == 1 and k >= 3:  # planted dependencies: a copy, a complement-like sum, a zero column
            A[:, -1] = A[:, 0]
            A[:, -2] = (A[:, 0] + A[:, 1]) % 2 if trial % 2 else 0
        if trial % 3 == 2:  # few distinct rows
            A = A[rng.integers(0, min(n, 4), size=n)]
        rows = A.tolist()
        got = S3.exact_rank(rows)
        assert got == _fraction_rank(rows) == int(np.linalg.matrix_rank(A))
        n_deficient += got < min(n, k)
    assert n_deficient > 50
    assert S3.exact_rank([]) == 0 and S3.exact_rank([[0, 0], [0, 0]]) == 0
    assert S3.exact_rank([[1, 64, 64 ** 2], [1, 63, 63 ** 2], [2, 127, 64 ** 2 + 63 ** 2]]) == 2  # large entries
    with pytest.raises(ValueError):
        S3.exact_rank([[1, 0], [1]])


def test_identifiability_clause_against_fraction_rank():
    rng = random.Random(9)
    for _ in range(200):
        n = rng.randrange(2, 20)
        distinct = [[rng.randrange(2) for _ in COLS] for _ in range(rng.randrange(1, 6))]
        rows = [list(rng.choice(distinct)) for _ in range(n)]
        nested = rng.random() < 0.5
        if nested:
            for r in rows:
                r[0] &= r[1]
        sub = [r for r in rows if r[1]] if nested else rows
        base = [[1] + r[2:] if nested else [1] + r[1:] for r in sub]
        want = int(len(sub) >= 2 and _fraction_rank([b + [r[0]] for b, r in zip(base, sub)]) > _fraction_rank(base))
        assert s3(rows, parent="p" if nested else None)["s3b"] == want


def test_s3_from_flags_rejects_bad_input():
    with pytest.raises(ValueError):
        s3([[0, 1, 0, 1, 0]], main="nope")
    with pytest.raises(ValueError):
        s3([[0, 1, 0, 1, 0]], parent="nope")
    with pytest.raises(ValueError):
        s3([[0, 1, 0, 1, 0]], parent="m")
    with pytest.raises(ValueError):
        s3([[0, 1, 0, 1]])
    with pytest.raises(ValueError):
        s3([[0, 2, 0, 1, 0]])
    with pytest.raises(ValueError):
        S3.s3_from_flags([[0, 1]], ["m", "m"], "m")
    # values are checked as given, not after truncation to int: 0.9 is not 0 and 1.7 is not 1
    for bad in ([[0.9, 0], [0.2, 0], [1.7, 1]], [[0, 0], [1.5, 1]], [[0, 0], ["1", 1]], [[0, 0], [None, 1]],
                [[0, 0], [-1, 1]]):
        with pytest.raises(ValueError):
            S3.s3_from_flags(bad, ["m", "x"], "m")
    # exact 0/1 of another numeric type are flags
    want = S3.s3_from_flags([[0, 0], [1, 0]], ["m", "x"], "m")
    assert want["s3"] == 1
    for same in ([[False, False], [True, False]], [[0.0, 0.0], [1.0, 0.0]], np.array([[0, 0], [1, 0]])):
        assert S3.s3_from_flags(same, ["m", "x"], "m") == want


# ---------------------------------------------------------------------------------------------------------
# normalisation and detector dispatch

def test_trailing_newline_does_not_change_flags():
    note = ft_note(seed=3, greeting=1, signoff=1, postscript=1, ps_question=1)
    want = S3.flags_for(note, FTX)
    assert want["postscript"] == want["ps_question"] == want["greeting"] == want["signoff"] == 1
    assert FT.detect(note + "\n")["ps_question"] == 0  # why the normalisation exists
    for tail in ("\n", "\n\n", "\r\n", "\n\r\n\r"):
        assert S3.flags_for(note + tail, FTX) == want
    t = tmpl_note(seed=3, greeting=1, signoff=1, postscript=1, hashtag=1)
    want = S3.flags_for(t, TMPL)
    assert want["postscript"] == want["greeting"] == want["signoff"] == want["hashtag"] == 1
    assert detectors.detect_all(t + "\n")["postscript"] == 0
    for tail in ("\n", "\n\n", "\r\n"):
        assert S3.flags_for(t + tail, TMPL) == want


def test_crlf_line_ends():
    note = ft_note(seed=4, greeting=1, signoff=1, signoff_excl=1, postscript=1)
    crlf = note.replace("\n", "\r\n")
    assert FT.detect(crlf) != FT.detect(note)
    assert S3.flags_for(crlf, FTX) == S3.flags_for(note, FTX)
    assert S3.flags_for(crlf + "\r\n", FTX) == S3.flags_for(note, FTX)
    t = tmpl_note(seed=4, greeting=1, signoff=1, postscript=1, bullet_list=1)
    assert S3.flags_for(t.replace("\n", "\r\n"), TMPL) == S3.flags_for(t, TMPL)


def test_normalise_changes_nothing_else():
    assert S3.normalise("a\r\nb\n\n") == "a\nb"
    assert S3.normalise("\n  a  b \n c \n") == "\n  a  b \n c "  # leading newline, inner and trailing spaces kept
    assert S3.normalise("x\n\r\n\r") == "x"
    assert S3.normalise("") == "" and S3.normalise("\n") == ""
    assert S3.flags_for("", FTX)["postscript"] == 0  # the detectors accept an empty text
    assert set(S3.flags_for("", TMPL)) == set(TG.FEATURES)


@pytest.mark.parametrize("substrate", [TMPL, FTX])
def test_flags_reproduce_generator_levels(substrate):
    feats = S3.FEATURES[substrate]
    assert list(feats) == list(TG.FEATURES if substrate == TMPL else FT.FEATURES)
    rng = random.Random(f"s3:{substrate}")
    on = dict.fromkeys(feats, 0)
    for k in range(400):
        levels = {f: rng.randrange(2) for f in feats}
        topic = rng.choice(list(TG.TOPICS))
        if substrate == TMPL:
            text, flags = TG.render(topic, levels, CUES, k)
        else:
            text, flags = FT.render(topic, levels, None, k)
        got = S3.flags_for(text, substrate)
        assert list(got) == list(feats)
        assert dict(got) == {f: int(flags[f]) for f in feats}, (substrate, k)
        for f in feats:
            on[f] += got[f]
    assert all(0 < v < 400 for v in on.values())  # every property was seen on and off


def test_dispatch_is_per_substrate():
    assert set(S3.FEATURES[TMPL]) != set(S3.FEATURES[FTX])
    assert S3.PARENTS == {TMPL: {}, FTX: {"signoff_excl": "signoff", "ps_question": "postscript"}}
    note = ft_note(seed=8, postscript=1, ps_question=1)
    assert "ps_question" in S3.flags_for(note, FTX) and "ps_question" not in S3.flags_for(note, TMPL)
    with pytest.raises(ValueError):
        S3.flags_for(note, "other")
    assert S3.substrate_of({"features": list(TG.FEATURES)}) == TMPL
    assert S3.substrate_of({}) == TMPL
    assert S3.substrate_of({"features": list(FT.FEATURES)}) == FTX
    with pytest.raises(ValueError):
        S3.substrate_of({"features": list(FT.FEATURES) + ["hedge"]})


def test_no_torch_import():
    code = ("import sys; sys.path.insert(0, 'scripts'); import s3_coder; "
            "print(sorted(m for m in ('torch', 'transformers') if m in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"


# ---------------------------------------------------------------------------------------------------------
# synthetic run directories

def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def make_answer(substrate, main, hard=2, mains=None):
    """A 4-probe answer.json: three planted probes and a null one; `hard` is the hard slot."""
    feats = list(S3.FEATURES[substrate])
    plain = [f for f in feats if f != main and f not in (mains or ()) and f not in FT.IMPLIES
             and f not in FT.IMPLIES.values()]
    probes, k = [], 0
    for j in range(4):
        if j == hard:
            src = "ft_tp2_r90a/planted_001" if main == "ps_question" else "knob_trap_s3/planted_000"
            p = {"probe": j, "kind": "planted", "cue": main, "source": src}
            if mains:
                p["mains"] = list(mains)
        elif j == (3 if hard != 3 else 0):
            p = {"probe": j, "kind": "null", "cue": None, "source": "screen/null_003"}
        else:
            p = {"probe": j, "kind": "planted", "cue": plain[k], "source": f"screen/planted_{k:03d}"}
            k += 1
        probes.append(p)
    return {"canary": "c", "features": feats, "conf_features": feats[:8], "probes": probes}


def rec(seq, probe=None, texts=None, tool="probe_query", status="ok", logits=None, ids=None, latents=None):
    if tool == "probe_query" and status == "ok" and logits is None:
        logits = [round(0.5 * k - 1.0, 3) for k in range(len(texts))]
    return {"seq": seq, "t": 1000.0 + seq, "tool": tool, "status": status, "probe": probe, "ids": ids,
            "latents": latents, "texts": texts, "sha256": None if texts is None else [sha(t) for t in texts],
            "logits": logits}


def log_rec(r):
    args = {k: r[k] for k in ("probe", "ids", "latents") if r[k] is not None}
    if r["texts"] is not None:
        args["texts"] = {"n": len(r["texts"]), "chars": sum(map(len, r["texts"]))}
    out = {"seq": r["seq"], "t": r["t"], "tool": r["tool"], "peer_uid": 1000, "charges": {"tool_calls": 1},
           "args": args, "status": r["status"], "ms": 1.0}
    if r["texts"] is not None:
        out["texts_sha256"] = r["sha256"]
    return out


FREE_CALLS = [{"seq": 1, "t": 1.0, "tool": "help", "peer_uid": 1000, "charges": {}, "args": {}, "status": "ok"},
              {"seq": 2, "t": 2.0, "tool": "sample_texts", "peer_uid": 1000, "charges": {"tool_calls": 1},
               "args": {"probe": 0}, "status": "ok"}]


def make_run(root, answer, records, batch="r1112_gpt_bb8", cid="aaaaaaaaaaaa", episode_id="ep411-blackbox",
             access="blackbox", limit=8, hard=None, fulltext=True, log=True, grade=True):
    d = Path(root) / batch / cid
    d.mkdir(parents=True)
    if answer is not None:
        (d / "answer.json").write_text(json.dumps(answer))
    (d / "episode_id").write_text(episode_id + "\n")
    if grade:
        if hard is None:
            hard = [j for j, p in enumerate((answer or {}).get("probes", []))
                    if p["source"].startswith(("knob_trap", "ft_tp2"))]
        (d / "grade.json").write_text(json.dumps({
            "hard_slots": hard, "episode": episode_id, "access": access,
            "budget": {"probe_query": {"used": 0, "limit": limit, "remaining": limit}},
            "details": {"probes": []}}))
    if fulltext:
        (d / "fulltext.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    if log:
        (d / "log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in FREE_CALLS + [log_rec(r) for r in records]))
    return d


def public(res):
    return {k: res[k] for k in S3.CSV_COLUMNS}


def test_code_run_templated_single_flip(tmp_path):
    base = dict(greeting=1, hashtag=1)
    off, on = tmpl_note(seed=5, **base), tmpl_note(seed=5, **base, weekday=1)
    d = make_run(tmp_path, make_answer(TMPL, "weekday"), [rec(3, 2, [off, on], logits=[-1.25, 2.5])])
    res = S3.code_run(d)
    assert public(res) == dict(run="aaaaaaaaaaaa", batch="r1112_gpt_bb8", episode="ep411", arm="bb8",
                               n_scored_hard=2, n_distinct=2, main_varies=1, s3a=1, s3b=1, s3=1, n_other_texts=0,
                               n_own_text_sae_calls=0, n_own_text_sae_texts=0, logit_min=-1.25, logit_max=2.5,
                               log="ok")
    priv = res["private"]
    assert priv["substrate"] == TMPL and priv["hard_slots"] == [2] and priv["log"] == "ok"
    slot = priv["slots"][0]
    assert slot["cols"] == list(TG.FEATURES) and slot["probe"] == 2
    assert [t["sha256"] for t in slot["texts"]] == [sha(off), sha(on)]
    w = slot["cols"].index("weekday")
    assert [t["flags"][w] for t in slot["texts"]] == [0, 1]
    assert [sum(a != b for a, b in zip(slot["texts"][0]["flags"], slot["texts"][1]["flags"]))] == [1]
    main = slot["mains"][0]
    assert (main["main"], main["parent"], main["pair"], main["pair_other"]) == ("weekday", None, [0, 1], None)
    assert main["pair_texts"] == [{"seq": 3, "index": 0, "sha256": sha(off)}, {"seq": 3, "index": 1, "sha256": sha(on)}]
    json.dumps(res)  # serialisable as is


def test_code_run_texts_across_calls_in_call_order(tmp_path):
    notes = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1, quote=1, hashtag=1), tmpl_note(seed=5, weekday=1)]
    recs = [rec(3, 2, [notes[0]]), rec(4, 2, [notes[1]]), rec(9, 2, [notes[2]])]
    res = S3.code_run(make_run(tmp_path, make_answer(TMPL, "weekday"), recs))
    assert (res["n_scored_hard"], res["s3a"], res["s3"]) == (3, 1, 1)
    main = res["private"]["slots"][0]["mains"][0]
    assert main["pair"] == [0, 2] and [t["seq"] for t in main["pair_texts"]] == [3, 9]
    assert [t["seq"] for t in res["private"]["slots"][0]["texts"]] == [3, 4, 9]


def test_code_run_main_plus_two_others_is_not_clean(tmp_path):
    notes = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1, quote=1, hashtag=1)]
    res = S3.code_run(make_run(tmp_path, make_answer(TMPL, "weekday"), [rec(3, 2, notes)]))
    assert (res["n_scored_hard"], res["main_varies"], res["s3a"], res["s3b"], res["s3"]) == (2, 1, 0, 0, 0)


def test_status_filtering_and_duplicates(tmp_path):
    off, on = tmpl_note(seed=7, signoff=1), tmpl_note(seed=7, signoff=1, weekday=1)
    other = tmpl_note(seed=8, quote=1)
    recs = [
        rec(3, 2, [off, off + "\n"], logits=[0.25, 0.25]),             # scored: a text and its newline twin
        rec(4, 2, [off], logits=[0.25]),                                # scored: an exact duplicate
        rec(5, 2, [on], status="timeout"),                              # charged, no logits: not scored
        rec(6, 2, [on], status="internal"),
        rec(7, 2, [on], status="leak"),
        rec(8, 1, [off, on, other], logits=[0.0, 4.0, 1.0]),            # another probe
        rec(9, 0, [on]),
        rec(10, None, [on, off], tool="latent_means"),                  # own-text SAE call
        rec(11, None, [on], tool="latent_tokens", latents=[5, 6]),
        rec(12, None, [on], tool="latent_means", status="timeout"),
        rec(13, 2, None, tool="latent_means", ids=[0, 1, 2]),           # sample notes: no agent text
        rec(14, 2, None, tool="latent_tokens", ids=[0], latents=[5]),
    ]
    d = make_run(tmp_path, make_answer(TMPL, "weekday"), recs, episode_id="ep411-open", access="open",
                 batch="r1112_gpt_open8")
    res = S3.code_run(d)
    assert public(res) == dict(run="aaaaaaaaaaaa", batch="r1112_gpt_open8", episode="ep411", arm="open8",
                               n_scored_hard=3, n_distinct=2, main_varies=0, s3a=0, s3b=0, s3=0, n_other_texts=4,
                               n_own_text_sae_calls=2, n_own_text_sae_texts=3, logit_min=0.25, logit_max=0.25,
                               log="ok")
    flags = [t["flags"] for t in res["private"]["slots"][0]["texts"]]
    assert flags[0] == flags[1] == flags[2]  # the newline twin has the same flags
    # the same log with the hard-probe flip accepted: now it counts
    recs[2] = rec(5, 2, [on], logits=[3.0])
    res = S3.code_run(make_run(tmp_path / "b", make_answer(TMPL, "weekday"), recs, episode_id="ep411-open",
                               access="open"))
    assert (res["n_scored_hard"], res["n_distinct"], res["s3a"], res["s3"], res["logit_max"]) == (4, 3, 1, 1, 3.0)


def test_scored_texts_keeps_duplicates_in_order():
    recs = [rec(4, 1, ["b", "a"], logits=[1.0, 2.0]), rec(5, 0, ["x"]), rec(6, 1, ["a"], logits=[2.0]),
            rec(7, 1, ["c"], status="timeout", logits=[9.0])]
    T = S3.scored_texts(recs, 1)
    assert [(t["seq"], t["index"], t["text"], t["logit"]) for t in T] == [(4, 0, "b", 1.0), (4, 1, "a", 2.0),
                                                                         (6, 0, "a", 2.0)]
    assert S3.scored_texts(recs, 3) == []


def test_code_run_freetext_nested(tmp_path):
    base = dict(greeting=1, postscript=1)
    stmt, quest = ft_note(seed=11, **base), ft_note(seed=11, **base, ps_question=1)
    no_ps = ft_note(seed=11, greeting=1)
    ans = make_answer(FTX, "ps_question")
    # child flipped with the parent on in both texts
    res = S3.code_run(make_run(tmp_path / "a", ans, [rec(3, 2, [stmt, quest])], episode_id="ep472-open",
                               access="open"))
    assert (res["arm"], res["episode"], res["s3a"], res["s3b"], res["s3"]) == ("open8", "ep472", 1, 1, 1)
    main = res["private"]["slots"][0]["mains"][0]
    assert (main["main"], main["parent"], main["n_parent_on"]) == ("ps_question", "postscript", 2)
    assert res["private"]["slots"][0]["cols"] == list(FT.FEATURES)
    # the P.S. question against no P.S. at all: the main varies, but only together with its parent
    res = S3.code_run(make_run(tmp_path / "b", ans, [rec(3, 2, [no_ps, quest])], episode_id="ep472-open",
                               access="open"))
    assert (res["main_varies"], res["s3a"], res["s3b"], res["s3"]) == (1, 0, 0, 0)
    assert res["private"]["slots"][0]["mains"][0]["n_parent_on"] == 1
    # adding a statement P.S. gives the clean pair
    res = S3.code_run(make_run(tmp_path / "c", ans, [rec(3, 2, [no_ps, quest]), rec(4, 2, [stmt + "\n"])],
                               episode_id="ep472-open", access="open"))
    assert (res["s3a"], res["s3b"], res["s3"]) == (1, 1, 1)
    assert res["private"]["slots"][0]["mains"][0]["pair"] == [1, 2]
    # a trailing newline on the question text must not hide the main (it would without normalisation)
    res = S3.code_run(make_run(tmp_path / "d", ans, [rec(3, 2, [stmt + "\r\n", quest + "\n"])],
                               episode_id="ep472-open", access="open"))
    assert (res["main_varies"], res["s3"]) == (1, 1)


def test_code_run_hard_slot_position_and_null_first(tmp_path):
    off, on = ft_note(seed=2, postscript=1), ft_note(seed=2, postscript=1, ps_question=1)
    ans = make_answer(FTX, "ps_question", hard=3)
    assert ans["probes"][0]["kind"] == "null"
    res = S3.code_run(make_run(tmp_path, ans, [rec(3, 2, [off, on]), rec(4, 3, [off, on])], episode_id="ep476-blackbox64",
                               limit=64))
    assert (res["arm"], res["n_scored_hard"], res["n_other_texts"], res["s3"]) == ("bb64", 2, 2, 1)
    assert res["private"]["hard_slots"] == [3]


def test_two_mains_must_both_hold(tmp_path):
    ans = make_answer(TMPL, "weekday", mains=["weekday", "quote"])
    base, a, b = tmpl_note(seed=9), tmpl_note(seed=9, weekday=1), tmpl_note(seed=9, quote=1)
    res = S3.code_run(make_run(tmp_path / "a", ans, [rec(3, 2, [base, a])]))
    mains = res["private"]["slots"][0]["mains"]
    assert [(m["main"], m["s3"]) for m in mains] == [("weekday", 1), ("quote", 0)]
    assert (res["main_varies"], res["s3a"], res["s3b"], res["s3"]) == (0, 0, 0, 0)
    res = S3.code_run(make_run(tmp_path / "b", ans, [rec(3, 2, [base, a, b])]))
    assert (res["main_varies"], res["s3a"], res["s3b"], res["s3"]) == (1, 1, 1, 1)


# ---------------------------------------------------------------------------------------------------------
# what the log allows

def test_no_fulltext_log(tmp_path):
    ans = make_answer(TMPL, "weekday")
    notes = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1)]
    # an image without the full-text log: calls were charged, nothing to code
    res = S3.code_run(make_run(tmp_path / "a", ans, [rec(3, 2, notes)], fulltext=False))
    assert res["log"] == "missing"
    assert all(res[k] is None for k in S3.CSV_COLUMNS[4:-1])
    # no tool log either
    res = S3.code_run(make_run(tmp_path / "b", ans, [], fulltext=False, log=False))
    assert (res["log"], res["s3"]) == ("missing", None)
    # the agent never called the three tools: zero scored texts, S3 = 0
    res = S3.code_run(make_run(tmp_path / "c", ans, [], fulltext=False))
    assert (res["log"], res["n_scored_hard"], res["n_distinct"], res["main_varies"]) == ("no_calls", 0, 0, 0)
    assert (res["s3a"], res["s3b"], res["s3"], res["logit_min"], res["n_other_texts"]) == (0, 0, 0, None, 0)
    # an empty full-text file reads the same way
    res = S3.code_run(make_run(tmp_path / "d", ans, []))
    assert (res["log"], res["n_scored_hard"], res["s3"]) == ("ok", 0, 0)


def test_broken_fulltext_log_gives_blank_s3(tmp_path):
    ans = make_answer(TMPL, "weekday")
    notes = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1)]
    good = rec(3, 2, notes)

    def run(name, mutate, **kw):
        d = make_run(tmp_path / name, ans, [good], **kw)
        mutate(d)
        return S3.code_run(d)

    def append(text):
        return lambda d: (d / "fulltext.jsonl").open("a").write(text)

    res = run("torn", append('{"seq": 4, "t": 1.0, "tool": "probe_query", "status": "ok", "probe": 2, "texts": ["ab'))
    assert (res["log"], res["s3"], res["s3a"], res["s3b"], res["n_scored_hard"]) == ("torn", None, None, None, 2)
    res = run("capped", append(json.dumps({"event": "fulltext capped", "t": 1.0, "seq": 4, "bytes": 9}) + "\n"))
    assert (res["log"], res["s3"]) == ("capped", None)
    bad_hash = dict(good, sha256=[good["sha256"][0], sha("something else")])
    res = run("hash", lambda d: (d / "fulltext.jsonl").write_text(json.dumps(bad_hash) + "\n"), log=False)
    assert (res["log"], res["s3"], res["n_scored_hard"]) == ("hash_mismatch", None, 0)
    short = dict(good, logits=[1.0])
    res = run("shape", lambda d: (d / "fulltext.jsonl").write_text(json.dumps(short) + "\n"), log=False)
    assert (res["log"], res["s3"]) == ("malformed", None)
    res = run("alien", append(json.dumps({"seq": 4, "tool": "probe_scores", "status": "ok"}) + "\n"))
    assert (res["log"], res["s3"]) == ("malformed", None)
    # log.jsonl has a charged probe_query that the full-text log lacks
    extra = log_rec(rec(4, 2, [notes[1]]))
    res = run("lost", lambda d: (d / "log.jsonl").open("a").write(json.dumps(extra) + "\n"))
    assert (res["log"], res["s3"], res["n_scored_hard"]) == ("log_mismatch", None, 2)
    # ... while an uncharged (refused) call in log.jsonl is not expected in the full-text log
    refused = dict(extra, charges={}, status="bad_request")
    res = run("refused", lambda d: (d / "log.jsonl").open("a").write(json.dumps(refused) + "\n"))
    assert (res["log"], res["s3"]) == ("ok", 1)
    # ... and neither is a torn last line of log.jsonl
    res = run("logtorn", lambda d: (d / "log.jsonl").open("a").write('{"seq": 4, "tool": "probe_qu'))
    assert (res["log"], res["s3"]) == ("ok", 1)
    # a status that differs between the two logs
    res = run("status", lambda d: (d / "log.jsonl").write_text(json.dumps(dict(log_rec(good), status="timeout")) + "\n"))
    assert (res["log"], res["s3"]) == ("log_mismatch", None)
    # without log.jsonl there is no cross-check
    res = run("nolog", lambda d: None, log=False)
    assert (res["log"], res["s3"]) == ("ok", 1)


def test_answer_problems(tmp_path):
    notes = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1)]
    recs = [rec(3, 2, notes)]
    ans = make_answer(TMPL, "weekday")
    res = S3.code_run(make_run(tmp_path / "a", None, recs, hard=[2]))
    assert (res["log"], res["s3"], res["n_scored_hard"], res["arm"]) == ("no_answer", None, None, "bb8")
    assert S3.code_run(tmp_path / "a" / "r1112_gpt_bb8" / "aaaaaaaaaaaa", answer=ans)["s3"] == 1  # answer override
    res = S3.code_run(make_run(tmp_path / "b", dict(ans, features=["a", "b"]), recs))
    assert (res["log"], res["s3"]) == ("unsupported_substrate", None)
    plain = make_answer(TMPL, "weekday")
    plain["probes"][2]["source"] = "screen/planted_009"
    res = S3.code_run(make_run(tmp_path / "c", plain, recs, hard=[]))
    assert (res["log"], res["s3"], res["n_scored_hard"]) == ("no_hard_slot", None, 0)
    res = S3.code_run(make_run(tmp_path / "d", ans, recs, hard=[1]))  # grade.json names another slot
    assert (res["log"], res["s3"], res["n_scored_hard"]) == ("hard_slot_mismatch", None, 2)
    res = S3.code_run(make_run(tmp_path / "e", ans, recs, grade=False))  # no grade.json: nothing to cross-check
    assert (res["log"], res["s3"], res["arm"]) == ("ok", 1, "bb8")
    # an unsubmitted run's grade.json has no hard_slots key
    d = make_run(tmp_path / "f", ans, recs)
    g = json.loads((d / "grade.json").read_text())
    del g["hard_slots"]
    (d / "grade.json").write_text(json.dumps(g))
    assert (S3.code_run(d)["log"], S3.code_run(d)["s3"]) == ("ok", 1)


def test_arm_mismatch_raises_like_the_scorer(tmp_path):
    d = make_run(tmp_path, make_answer(TMPL, "weekday"), [], episode_id="ep411-blackbox64", limit=8)
    with pytest.raises(S3.SN.ArmMismatchError):
        S3.code_run(d)


def test_reads_what_the_tool_server_writes(tmp_path):
    """The record shapes above are hand-written; this one is the daemon's own (fake backend, no GPU)."""
    try:
        import test_toolserver as tst
        from shifthunt import toolserver as ts
        from shifthunt.toolbackend import FakeBackend
    except Exception as e:  # the tool server is being changed in another work package
        pytest.skip(f"tool server test helpers not importable: {type(e).__name__}: {e}")
    if not hasattr(ts, "FULLTEXT_TOOLS"):
        pytest.skip("this tool server has no full-text log")
    assert tuple(ts.FULLTEXT_TOOLS) == S3.FULLTEXT_TOOLS
    env = ts.ToolEnv(tst.make_episode(tmp_path / "ep"), FakeBackend(), tmp_path / "out", tmp_path / "state")
    off, on = tmpl_note(seed=5, postscript=1) + "\n", tmpl_note(seed=5, postscript=1, weekday=1)
    other = "caf\u00e9  \u2019quoted\u2019\r\nsecond line"
    r = env.call("probe_query", {"probe": 0, "texts": [off, on]})
    assert "logits" in r
    env.call("probe_query", {"probe": 1, "texts": [other]})
    env.call("probe_query", {"probe": 0, "texts": []})             # invalid: not charged, not logged
    env.call("probe_query", {"probe": 0, "texts": ["x"] * 99})     # over budget: refused
    env.call("latent_means", {"texts": [on, other]})
    env.call("latent_means", {"probe": 0, "ids": [0, 1]})
    env.call("latent_tokens", {"latents": [3], "texts": [on]})
    env.call("sample_texts", {"probe": 0})
    records, problems = S3.read_fulltext(env.state_dir / "fulltext.jsonl")
    assert problems == [] and [r_["tool"] for r_ in records] == ["probe_query", "probe_query", "latent_means",
                                                                "latent_means", "latent_tokens"]
    assert [t["text"] for t in S3.scored_texts(records, 0)] == [off, on]
    assert [t["logit"] for t in S3.scored_texts(records, 0)] == r["logits"]
    assert [t["text"] for t in S3.scored_texts(records, 1)] == [other]
    d = make_run(tmp_path / "raw", make_answer(TMPL, "weekday", hard=0), [], fulltext=False, log=False,
                 episode_id="ep411-open", access="open")
    for name in ("fulltext.jsonl", "log.jsonl"):
        shutil.copy(env.state_dir / name, d / name)
    res = S3.code_run(d)
    assert (res["log"], res["n_scored_hard"], res["n_distinct"], res["s3a"], res["s3b"], res["s3"]) == ("ok", 2, 2, 1, 1, 1)
    assert (res["n_other_texts"], res["n_own_text_sae_calls"], res["n_own_text_sae_texts"]) == (1, 2, 3)
    assert (res["logit_min"], res["logit_max"]) == (min(r["logits"]), max(r["logits"]))
    # dropping the last full-text record is caught by the cross-check with log.jsonl
    lines = (d / "fulltext.jsonl").read_text().splitlines(keepends=True)
    (d / "fulltext.jsonl").write_text("".join(lines[:-1]))
    assert (S3.code_run(d)["log"], S3.code_run(d)["s3"]) == ("log_mismatch", None)


# ---------------------------------------------------------------------------------------------------------
# output files

def study(tmp_path):
    raw = tmp_path / "raw"
    t = [tmpl_note(seed=5), tmpl_note(seed=5, weekday=1), tmpl_note(seed=6, quote=1, hashtag=1)]
    f = [ft_note(seed=5, postscript=1), ft_note(seed=5, postscript=1, ps_question=1), ft_note(seed=6, question=1)]
    make_run(raw, make_answer(TMPL, "weekday"), [rec(3, 2, t[:2]), rec(4, 1, t)], cid="aaaaaaaaaaaa")
    make_run(raw, make_answer(TMPL, "weekday"), [rec(3, 2, [t[0], t[2]]), rec(4, 0, [t[0] + "\n"])],
             cid="bbbbbbbbbbbb", episode_id="ep413-blackbox")
    make_run(raw, make_answer(FTX, "ps_question"), [rec(3, 2, f[:2]), rec(4, 0, f), rec(5, None, f[:1], tool="latent_means")],
             batch="r1112_gpt_open8", cid="cccccccccccc", episode_id="ep472-open", access="open")
    make_run(raw, make_answer(FTX, "ps_question"), [rec(3, 2, [f[0]])], batch="r1112_gpt_open8",
             cid="dddddddddddd", episode_id="ep474-open", access="open", fulltext=False)
    return raw


def test_cli_writes_csv_without_property_names_and_private_detail(tmp_path, capsys):
    raw = study(tmp_path)
    out_csv, priv = tmp_path / "pub" / "s3.csv", tmp_path / "private"
    assert S3.main(["--raw", str(raw), "--out-csv", str(out_csv), "--private-out", str(priv)]) == 0
    text = out_csv.read_text()
    low = text.lower()
    assert not [f for f in ALL_NAMES if f.lower() in low]
    assert S3.property_names_in(text) == []
    rows = list(csv.DictReader(out_csv.open()))
    assert list(rows[0])[:10] == ["run", "batch", "episode", "arm", "n_scored_hard", "n_distinct", "main_varies",
                                  "s3a", "s3b", "s3"]
    assert [(r["batch"], r["run"], r["episode"], r["arm"], r["s3"], r["log"]) for r in rows] == [
        ("r1112_gpt_bb8", "aaaaaaaaaaaa", "ep411", "bb8", "1", "ok"),
        ("r1112_gpt_bb8", "bbbbbbbbbbbb", "ep413", "bb8", "0", "ok"),
        ("r1112_gpt_open8", "cccccccccccc", "ep472", "open8", "1", "ok"),
        ("r1112_gpt_open8", "dddddddddddd", "ep474", "open8", "", "missing")]
    assert (rows[2]["n_own_text_sae_calls"], rows[2]["n_other_texts"], rows[2]["logit_min"]) == ("1", "3", "-1.0000")
    assert rows[3]["n_scored_hard"] == "" and rows[3]["s3a"] == ""
    for cell in (c for r in rows for c in r.values()):
        assert "\n" not in cell and len(cell) < 40  # no text in any cell
    # private detail: one file per batch, one line per run, with names, pair and hashes
    assert sorted(p.name for p in priv.iterdir()) == ["r1112_gpt_bb8.jsonl", "r1112_gpt_open8.jsonl"]
    recs = [json.loads(line) for line in (priv / "r1112_gpt_open8.jsonl").read_text().splitlines()]
    assert [r["run"] for r in recs] == ["cccccccccccc", "dddddddddddd"]
    slot = recs[0]["slots"][0]
    assert slot["cols"] == list(FT.FEATURES) and len(slot["texts"]) == 2
    assert all(len(t["flags"]) == 15 and len(t["sha256"]) == 64 for t in slot["texts"])
    assert slot["mains"][0]["main"] == "ps_question" and slot["mains"][0]["pair"] == [0, 1]
    assert recs[0]["s3"] == 1 and recs[1]["log"] == "missing" and recs[1]["slots"] == []
    assert "postscript" not in out_csv.read_text() and "ft_note" not in (priv / "r1112_gpt_open8.jsonl").read_text()
    # no text in the private detail either: hashes only
    blob = "".join(p.read_text() for p in priv.iterdir())
    assert "P.S." not in blob and "p.s." not in blob
    out = capsys.readouterr().out
    assert "r1112_gpt_bb8 bb8: S3 1/2" in out and not S3.property_names_in(out)
    # a single batch directory and a single run directory are accepted too; a run is coded once
    assert [d.name for d in S3.run_dirs([raw / "r1112_gpt_bb8"])] == ["aaaaaaaaaaaa", "bbbbbbbbbbbb"]
    assert [d.name for d in S3.run_dirs([raw / "r1112_gpt_bb8" / "bbbbbbbbbbbb", raw / "r1112_gpt_bb8"])] == [
        "aaaaaaaaaaaa", "bbbbbbbbbbbb"]
    assert len(S3.run_dirs([raw, raw / "r1112_gpt_open8"])) == 4
    with pytest.raises(FileNotFoundError):
        S3.run_dirs([raw / "nope"])


def test_relative_raw_keeps_run_and_batch_names(tmp_path, monkeypatch):
    raw = study(tmp_path)
    want = [S3.public_row(S3.code_run(d)) for d in S3.run_dirs([raw / "r1112_gpt_bb8"])]
    assert [r["batch"] for r in want] == ["r1112_gpt_bb8"] * 2
    # from inside the batch directory
    monkeypatch.chdir(raw / "r1112_gpt_bb8")
    dirs = S3.run_dirs(["."])
    assert all(d.is_absolute() for d in dirs)
    assert [(d.parent.name, d.name) for d in dirs] == [("r1112_gpt_bb8", "aaaaaaaaaaaa"), ("r1112_gpt_bb8", "bbbbbbbbbbbb")]
    assert [S3.public_row(S3.code_run(d)) for d in dirs] == want
    assert S3.public_row(S3.code_run("aaaaaaaaaaaa")) == want[0]  # a relative run directory given directly
    assert S3.main(["--raw", ".", "--out-csv", str(tmp_path / "rel.csv"), "--private-out", str(tmp_path / "relpriv")]) == 0
    rows = list(csv.DictReader((tmp_path / "rel.csv").open()))
    assert [(r["batch"], r["run"], r["s3"]) for r in rows] == [("r1112_gpt_bb8", "aaaaaaaaaaaa", "1"),
                                                             ("r1112_gpt_bb8", "bbbbbbbbbbbb", "0")]
    assert [p.name for p in (tmp_path / "relpriv").iterdir()] == ["r1112_gpt_bb8.jsonl"]
    assert [it["batch"] for v in S3.validation_pool(dirs).values() for it in v] == ["r1112_gpt_bb8"] * 4
    # from inside a run directory, and from the parent of the batches, by relative paths
    monkeypatch.chdir(raw / "r1112_gpt_bb8" / "bbbbbbbbbbbb")
    assert S3.public_row(S3.code_run(".")) == want[1]
    assert [(d.parent.name, d.name) for d in S3.run_dirs([".", ".."])] == [
        ("r1112_gpt_bb8", "aaaaaaaaaaaa"), ("r1112_gpt_bb8", "bbbbbbbbbbbb")]
    assert len(S3.run_dirs(["../.."])) == 4
    # no batch directory above the run: refused rather than coded with an empty batch name
    with pytest.raises(ValueError):
        S3.code_run("/aaaaaaaaaaaa")
    with pytest.raises(ValueError):
        S3.code_run("/")


def test_csv_refuses_a_property_name(tmp_path):
    d = make_run(tmp_path, make_answer(TMPL, "weekday"), [], batch="pilot_weekday")
    res = S3.code_run(d)
    with pytest.raises(ValueError):
        S3.csv_text([res])
    out_csv = tmp_path / "s3.csv"
    with pytest.raises(ValueError):
        S3.main(["--raw", str(tmp_path / "pilot_weekday"), "--out-csv", str(out_csv)])
    assert not out_csv.exists()
    assert S3.property_names_in("run,batch\nx,PS_Question_pilot\n") == ["ps_question", "question"]
    assert set(S3.PROPERTY_NAMES) == ALL_NAMES
    assert not S3.property_names_in(",".join(S3.CSV_COLUMNS))


def test_public_row_formats():
    res = dict.fromkeys(S3.CSV_COLUMNS)
    res.update(run="r", batch="b", s3=1, main_varies=True, logit_min=-0.123456, logit_max=2)
    row = S3.public_row(res)
    assert list(row) == S3.CSV_COLUMNS
    assert (row["s3"], row["main_varies"], row["logit_min"], row["logit_max"], row["s3a"]) == (1, 1, "-0.1235", 2, "")


def test_private_output_must_be_untracked(tmp_path):
    S3.require_untracked(tmp_path / "anything")  # outside the repository
    S3.require_untracked(ROOT / "results" / "private_1112" / "s3")
    for bad in (ROOT / "results" / "blackbox_1112" / "s3_detail", ROOT / "scripts", ROOT):
        with pytest.raises(SystemExit):
            S3.require_untracked(bad)
    with pytest.raises(SystemExit):
        S3.main(["--raw", str(tmp_path), "--out-csv", str(tmp_path / "s3.csv"), "--private-out",
                 str(ROOT / "results" / "blackbox_1112" / "s3_detail")])
    assert not (tmp_path / "s3.csv").exists()


# ---------------------------------------------------------------------------------------------------------
# detector validation sample

def test_allocate():
    assert S3.allocate(50, {"a": 10, "b": 100}) == {"a": 10, "b": 40}
    assert S3.allocate(5, {"a": 9, "b": 9}) == {"a": 3, "b": 2}
    assert S3.allocate(50, {"a": 3, "b": 4}) == {"a": 3, "b": 4}
    assert S3.allocate(7, {"a": 1, "b": 2, "c": 50}) == {"a": 1, "b": 2, "c": 4}
    assert S3.allocate(0, {"a": 3}) == {"a": 0} and S3.allocate(4, {}) == {}


def validation_runs(tmp_path):
    raw = tmp_path / "raw"
    t = [tmpl_note(seed=k, weekday=k % 2, postscript=(k // 2) % 2) + ("\n" if k == 3 else "") for k in range(12)]
    f = [ft_note(seed=k, postscript=k % 2, ps_question=(k // 2) % 2) for k in range(5)]
    make_run(raw, make_answer(TMPL, "weekday"), [rec(3, 2, t[:6]), rec(4, 1, t[6:] + t[:2]),
                                                 rec(5, 2, ["never scored"], status="timeout"),
                                                 rec(6, None, ["sae only"], tool="latent_means")])
    make_run(raw, make_answer(FTX, "ps_question"), [rec(3, 2, f[:3]), rec(4, 0, f[3:])], batch="r1112_gpt_open8",
             cid="cccccccccccc", episode_id="ep472-open", access="open")
    make_run(raw, make_answer(FTX, "ps_question"), [rec(3, 2, f[:1])], batch="r1112_gpt_open8", cid="dddddddddddd",
             episode_id="ep474-open", access="open", fulltext=False)
    return raw, t, f


def test_validation_sample_is_stratified_and_seeded(tmp_path):
    raw, t, f = validation_runs(tmp_path)
    dirs = S3.run_dirs([raw])
    pool = S3.validation_pool(dirs)
    assert {s: len(v) for s, v in pool.items()} == {TMPL: 12, FTX: 5}  # distinct ok probe_query texts only
    assert {it["text"] for it in pool[TMPL]} == set(t)
    items, meta = S3.validation_sample(dirs, 8, "7")
    assert meta["per_substrate"] == {FTX: 4, TMPL: 4} and meta["drawn"] == 8 and meta["pool"] == {FTX: 5, TMPL: 12}
    assert [it["id"] for it in items] == [f"v{k:03d}" for k in range(8)]
    assert len({it["sha256"] for it in items}) == 8
    for it in items:
        assert it["flags"] == S3.flags_for(it["text"], it["substrate"]) and it["sha256"] == sha(it["text"])
        assert it["hard_probe"] == int(it["probe"] == 2)
    again, _ = S3.validation_sample(dirs, 8, "7")
    assert again == items
    other, _ = S3.validation_sample(dirs, 8, "8")
    assert [it["sha256"] for it in other] != [it["sha256"] for it in items]
    items, meta = S3.validation_sample(dirs, 50, "7")  # more than there is: everything, the small stratum whole
    assert meta["per_substrate"] == {FTX: 5, TMPL: 12} and len(items) == 17
    assert sum(it["normalised_differs"] for it in items) == 1


def test_validation_cli_writes_blind_companion(tmp_path, capsys):
    raw, _, _ = validation_runs(tmp_path)
    out = tmp_path / "private" / "validate"
    assert S3.main(["--raw", str(raw), "--validate-sample", "6", "--seed", "3", "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == sorted(S3.VALIDATE_FILES)
    flags = [json.loads(line) for line in (out / "s3_validate_flags.jsonl").read_text().splitlines()]
    blind = [json.loads(line) for line in (out / "s3_validate_blind.jsonl").read_text().splitlines()]
    assert len(flags) == len(blind) == 6
    assert [b["id"] for b in blind] == [x["id"] for x in flags]
    for b, x in zip(blind, flags):
        assert set(b) == {"id", "substrate", "text", "labels"}  # no flags, no run, no probe
        assert b["text"] == x["text"] and b["substrate"] == x["substrate"]
        assert list(b["labels"]) == list(S3.FEATURES[b["substrate"]]) and set(b["labels"].values()) == {None}
        assert x["flags"] == dict(S3.flags_for(x["text"], x["substrate"]))
    meta = json.loads((out / "s3_validate_meta.json").read_text())
    assert meta["requested"] == 6 and meta["seed"] == "3" and meta["per_substrate"] == {FTX: 3, TMPL: 3}
    assert "6 of 6 texts drawn" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        S3.main(["--raw", str(raw), "--validate-sample", "6"])  # needs --out
    # a second run into the same directory must not wipe hand labels
    blind_path = out / "s3_validate_blind.jsonl"
    blind[0]["labels"][next(iter(blind[0]["labels"]))] = 1
    blind_path.write_text("".join(json.dumps(b) + "\n" for b in blind))
    before = {f: (out / f).read_bytes() for f in S3.VALIDATE_FILES}
    args = ["--raw", str(raw), "--validate-sample", "6", "--seed", "3", "--out", str(out)]
    with pytest.raises(SystemExit):
        S3.main(args)
    assert "already holds validation files" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        S3.main(args[:-5] + ["4", "--seed", "9", "--out", str(out)])  # nor with another sample
    items, meta = S3.validation_sample(S3.run_dirs([raw]), 6, "3")
    with pytest.raises(FileExistsError):
        S3.write_validation(items, meta, out)
    assert {f: (out / f).read_bytes() for f in S3.VALIDATE_FILES} == before
    # one leftover file is enough to refuse, and nothing else is written then
    part = tmp_path / "private" / "partial"
    part.mkdir()
    (part / "s3_validate_blind.jsonl").write_text("labelled\n")
    with pytest.raises(SystemExit):
        S3.main(args[:-1] + [str(part)])
    assert [p.name for p in part.iterdir()] == ["s3_validate_blind.jsonl"]
    assert (part / "s3_validate_blind.jsonl").read_text() == "labelled\n"
    # --force overwrites, and says so by being asked for
    assert S3.main(args + ["--force"]) == 0
    again = [json.loads(line) for line in blind_path.read_text().splitlines()]
    assert all(set(b["labels"].values()) == {None} for b in again)
    assert (out / "s3_validate_flags.jsonl").read_bytes() == before["s3_validate_flags.jsonl"]
    with pytest.raises(SystemExit):
        S3.main(["--raw", str(raw)])  # needs --out-csv
