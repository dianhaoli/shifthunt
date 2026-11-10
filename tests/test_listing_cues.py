"""shifthunt/listing_cues.py: the Exp F generator (profiles, nesting, edits, detectors, masks, aligned-set draw).

CPU only, no API call, no regex subprocess except where a test says so."""
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import episode_files as E  # noqa: E402
from shifthunt import freetext as ft  # noqa: E402
from shifthunt import freetext_listing as fl  # noqa: E402
from shifthunt import listing_cues as lc  # noqa: E402

TOPICS = ["sailing", "chess"]
ADMITTED = ["base", "gq", "px", "fi", "pn", "pqx", "pf"]


def ba(pred, truth):
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    return 0.5 * (pred[truth].mean() + (~pred[~truth]).mean())


def test_base_profile_is_exactly_freetext_listing():
    a = lc.sample_grid(random.Random("t"), TOPICS, 64, "base")
    b = fl.sample_grid(random.Random("t"), TOPICS, 64, None)
    assert a[0] == b[0]
    assert all(np.array_equal(a[2][f], b[2][f]) for f in fl.FEATURES)
    lv = {f: 1 for f in fl.FEATURES}
    assert lc.render("cycling", lv, "base", 9) == fl.render("cycling", lv, None, 9)


@pytest.mark.parametrize("profile", sorted(lc.PROFILES))
def test_detectors_agree_with_the_flags(profile):
    prof = lc.profile_of(profile)
    texts, _, flags = lc.sample_grid(random.Random(f"det:{profile}"), TOPICS, 400, prof)
    for i, t in enumerate(texts):
        d = lc.detect(t, prof)
        assert {f: d[f] for f in prof.scored} == {f: int(flags[f][i]) for f in prof.scored}, t
    for f in prof.flags + prof.derived:   # every new property occurs and is absent
        assert 0 < flags[f].sum() < len(texts)


@pytest.mark.parametrize("profile", ADMITTED[1:])
def test_each_new_edit_changes_the_text_and_only_its_property(profile):
    prof = lc.profile_of(profile)
    rng = random.Random(f"edit:{profile}")
    for f in prof.flags:
        n = 0
        while n < 60:
            lv = {g: int(rng.random() < 0.5) for g in prof.features}
            seed = rng.getrandbits(32)
            lv[f] = 1
            try:
                lc.imply(lv, prof, protect={f})
            except ValueError:
                continue
            on, on_lv = lc.render("pottery", lv, prof, seed)
            off, _ = lc.render("pottery", {**on_lv, f: 0}, prof, seed)
            assert on != off
            d_on, d_off = lc.detect(on, prof), lc.detect(off, prof)
            diff = {g for g in prof.scored if d_on[g] != d_off[g]}
            assert f in diff and diff <= {f} | {d for d, comps in lc.DERIVED.items() if f in comps}
            n += 1


def test_edits_read_as_specified():
    d = {"greet": 0, "gname": "Sam", "ps": 1, "psq": 0}
    x = {"gq": 0, "follow": 0}
    gq = lc.PROFILES["gq"]     # the same words; only the mark differs
    assert lc.greeting_line(gq, {"greet_question": 1}, d, x) == "Hi Sam, hope you are well? All good here."
    assert lc.greeting_line(gq, {"greet_question": 0}, d, x) == "Hi Sam, hope you are well. All good here."
    assert lc.greeting_line(lc.PROFILES["gq_v1"], {"greet_question": 1}, d, x) == "Hi Sam, how are you?"
    v2 = lc.PROFILES["gq_v2"]
    assert lc.greeting_line(v2, {"greet_question": 1}, d, x) == "Hi Sam, how are you? Hope all is well."
    assert lc.greeting_line(v2, {"greet_question": 0}, d, x) == "Hi Sam, hope all is well."
    fi = lc.PROFILES["fi"]
    assert lc.greeting_line(fi, {"greet_informal": 1}, d, x) == "Hey Sam,"
    assert lc.greeting_line(fi, {"greet_informal": 0}, d, x) == "Hello Sam,"
    base = {"ps_question": 0, "ps_tentative": 0}
    assert lc.ps_line(lc.PROFILES["px"], {**base, "ps_exclaim": 1}, d) == "P.S. Oh! I owe you lunch."
    assert lc.ps_line(lc.PROFILES["px"], {**base, "ps_exclaim": 0}, d) == "P.S. Oh, I owe you lunch."
    q = {"ps_question": 1, "ps_tentative": 0}
    assert lc.ps_line(lc.PROFILES["pn"], {**q, "ps_named": 1}, d) == "P.S. Sam, are you free next week?"
    pqx = lc.PROFILES["pqx"]   # ps_q_excl = ps_question AND ps_exclaim: the "Oh!" also on statement P.S. lines
    assert lc.ps_line(pqx, {**q, "ps_exclaim": 1}, d) == "P.S. Oh! Are you free next week?"
    assert lc.ps_line(pqx, {**q, "ps_exclaim": 0}, d) == "P.S. Oh, are you free next week?"
    assert lc.ps_line(pqx, {**base, "ps_exclaim": 1}, d) == "P.S. Oh! I owe you lunch."
    assert lc.ps_line(lc.PROFILES["pqx_v2"], {**q, "ps_qx_child": 1}, d) == "P.S. Oh! Are you free next week?"
    assert lc.ps_line(lc.PROFILES["pqx_v1"], {**q, "ps_qx_child": 1}, d) == "P.S. Are you free next week?!"
    text, _ = lc.render("cycling", {"postscript": 1, "signoff": 1, "ps_first": 1}, "pf", 3)
    lines = text.split("\n")
    assert lines[-3].startswith("P.S. ") and lines[-2].rstrip(",!") in ft.CLOSINGS


def test_imply_nesting_chains_and_exclusions():
    v2 = lc.PROFILES["pqx_v2"]
    lv = lc.imply(lc.check_levels({"ps_qx_child": 1}, v2), v2, protect={"ps_qx_child"})
    assert lv["ps_question"] == lv["postscript"] == 1               # a chain: every ancestor switched on
    lv = lc.imply(lc.check_levels({"ps_qx_child": 1, "ps_question": 1}, v2), v2)
    assert lv["ps_qx_child"] == lv["ps_question"] == 0              # unprotected: dropped to a fixed point
    pf = lc.PROFILES["pf"]
    lv = lc.imply(lc.check_levels({"ps_first": 1}, pf), pf, protect={"ps_first"})
    assert lv["postscript"] == lv["signoff"] == 1
    with pytest.raises(ValueError):
        lc.imply(lc.check_levels({"ps_first": 1}, pf), pf, protect={"ps_first", "signoff"})
    base = lc.PROFILES["base"]
    lv = lc.imply(lc.check_levels({"postscript": 1, "ps_question": 1, "ps_tentative": 1}, base), base)
    assert lv["ps_question"] == 1 and lv["ps_tentative"] == 0        # ps_question wins by default
    lv = lc.imply(lc.check_levels({"postscript": 1, "ps_question": 1, "ps_tentative": 1}, base), base,
                  protect={"ps_tentative"})
    assert lv["ps_question"] == 0 and lv["ps_tentative"] == 1
    v1 = lc.PROFILES["px_v1"]
    lv = lc.imply(lc.check_levels({"postscript": 1, "ps_question": 1, "ps_exclaim": 1}, v1), v1)
    assert lv["ps_exclaim"] == 0
    px = lc.PROFILES["px"]   # the admitted "Oh!" version needs no exclusion
    lv = lc.imply(lc.check_levels({"postscript": 1, "ps_question": 1, "ps_exclaim": 1}, px), px)
    assert lv["ps_exclaim"] == 1 and lv["ps_question"] == 1


def test_relations():
    assert lc.ancestors("ps_qx_child") == {"ps_question", "postscript"}
    assert lc.ancestors("ps_q_excl") == {"postscript"} and lc.components("ps_q_excl") == {"ps_question", "ps_exclaim"}
    assert lc.ancestors("ps_first") == {"postscript", "signoff"}
    assert lc.ancestors("informal_lower") == {"greeting"}
    assert lc.ancestors("ps_q_named") == {"postscript"}
    assert lc.related("informal_lower", "fi") == {"informal_lower", "greet_informal", "lowercase", "greeting"}
    assert "ps_tentative" in lc.exclusive_with("ps_question")
    assert lc.exclusive_with("ps_exclaim", "px") == set() and lc.exclusive_with("ps_exclaim", "px_v1") == {"ps_question"}
    assert lc.shares_mark("ps_question") >= {"question", "greet_question", "ps_q_named", "ps_q_excl"}
    assert lc.shares_mark("signoff_excl") >= {"exclamation", "ps_exclaim"} and "question" not in lc.shares_mark("signoff_excl")
    assert lc.shares_mark("weekday") == set()


def test_masks_balance_the_parent_and_each_component_away():
    for profile, cue, comps in (("fi", "informal_lower", ("greet_informal", "lowercase")),
                                ("pn", "ps_q_named", ("ps_question", "ps_named")),
                                ("pqx", "ps_q_excl", ("ps_question", "ps_exclaim"))):
        _, _, flags = lc.sample_grid(random.Random(profile), TOPICS, 8192, profile)
        flags = {f: np.asarray(v, bool) for f, v in flags.items()}
        m = lc.mask(cue, flags, profile)
        truth = flags[cue][m]
        assert ba(truth, truth) == 1.0
        for c in comps:          # each component alone: BA 0.75 by design
            assert abs(ba(flags[c][m], truth) - 0.75) < 0.02
        parent = next(iter(lc.ancestors(cue)))
        assert flags[parent][m].all()     # parent constant within the mask
    _, _, flags = lc.sample_grid(random.Random("m"), TOPICS, 4096, "gq")
    flags = {f: np.asarray(v, bool) for f, v in flags.items()}
    m = lc.mask("greet_question", flags, "gq")
    assert np.array_equal(m, flags["greeting"])
    assert np.array_equal(lc.mask("ps_tentative", flags, "gq"), flags["postscript"] & ~flags["ps_question"])
    assert lc.mask("curly_apostrophe", flags, "gq").all()


@pytest.mark.parametrize("cue,profile", [("curly_apostrophe", "base"), ("greet_question", "gq"),
                                         ("ps_exclaim", "px"), ("ps_tentative", "base"),
                                         ("informal_lower", "fi"), ("ps_q_named", "pn"), ("ps_q_excl", "pqx"),
                                         ("ps_first", "pf"), ("ps_question", "base"), ("quote", "base")])
def test_aligned_set_mirrors_the_bank_rule(cue, profile):
    seen = Counter()
    for rep in range(30):
        rng = random.Random(f"al:{cue}:{rep}")
        signs = lc.draw_aligned(rng, cue, profile)
        assert len(signs) == lc.N_ALIGNED and next(iter(signs)) == cue
        others = [f for f in signs if f != cue]
        rel = lc.related(cue, profile)
        excl = set().union(*(lc.exclusive_with(c, profile) for c in {cue} | lc.components(cue)))
        assert not set(others) & (rel | excl)
        assert set(others) <= set(lc.POOL_WEIGHTS)        # never planted -> never a decoy
        assert not any(b in lc.ancestors(a) for a in signs for b in signs)   # no parent-child pair (as shipped)
        assert set(signs.values()) <= {1, -1}
        for child in signs:
            for p in lc.PARENTS.get(child, ()):
                if p in signs:
                    assert signs[p] == signs[child]       # episode_files.py:200-213
        seen.update(others)
    assert lc.draw_aligned(random.Random("same"), cue, profile) == lc.draw_aligned(random.Random("same"), cue, profile)
    if "ps_question" not in lc.related(cue, profile) and "ps_question" not in lc.exclusive_with(cue, profile):
        assert seen["ps_question"] == 30                  # weight 9 of the pool: always drawn (PPS "sure")


def test_derived_sample_cells_and_collinearity():
    for profile, cue in (("fi", "informal_lower"), ("pn", "ps_q_named"), ("pqx", "ps_q_excl")):
        rng = random.Random(f"s:{cue}")
        signs = lc.draw_aligned(rng, cue, profile)
        texts, labels, flags = lc.sample_aligned(rng, TOPICS, 128, profile, signs, target=cue)
        tclass = 1 if signs[cue] > 0 else 0
        a, b = lc.DERIVED[cue]
        other = labels != tclass
        cells = Counter(zip(flags[a][other], flags[b][other]))
        assert cells == {(1, 0): 28, (0, 1): 28, (0, 0): 8}
        assert (flags[a][~other] == 1).all() and (flags[b][~other] == 1).all()
        for f, s in signs.items():
            want = labels if s > 0 else 1 - labels
            assert np.array_equal(flags[f], want)
        for c in (a, b):
            assert not np.array_equal(flags[c], labels) and not np.array_equal(flags[c], 1 - labels)
        for i, t in enumerate(texts):
            d = lc.detect(t, profile)
            assert all(d[f] == flags[f][i] for f in lc.profile_of(profile).scored)


def test_sample_with_a_child_target_keeps_the_exclusive_sibling_off():
    rng = random.Random("tent")
    signs = lc.draw_aligned(rng, "ps_tentative", "base")
    _, labels, flags = lc.sample_aligned(rng, TOPICS, 128, "base", signs)
    on = flags["ps_tentative"] == 1
    assert (flags["postscript"][on] == 1).all() and (flags["ps_question"][on] == 0).all()


def test_grids_hold_and_balance():
    _, _, g = lc.sample_grid(random.Random("g"), TOPICS, 256, "fi", mains=["informal_lower"])
    assert g["informal_lower"].sum() == 128 and (g["greeting"] == 1).all()
    off = g["informal_lower"] == 0
    assert Counter(zip(g["greet_informal"][off], g["lowercase"][off])) == {(1, 0): 64, (0, 1): 64}
    _, _, g = lc.sample_grid(random.Random("g"), TOPICS, 256, "pqx", mains=["ps_q_excl"])
    assert g["ps_q_excl"].sum() == 128 and (g["postscript"] == 1).all()
    off = g["ps_q_excl"] == 0
    assert Counter(zip(g["ps_question"][off], g["ps_exclaim"][off])) == {(1, 0): 64, (0, 1): 64}
    with pytest.raises(ValueError):
        lc.sample_grid(random.Random("g"), TOPICS, 12, "fi", mains=["informal_lower"])


def test_negative_candidates_exclude_related_and_exclusive():
    aligned = ["ps_tentative", "signoff", "lowercase", "question", "hashtag", "weekday", "parenthetical", "quote"]
    cands = lc.negative_candidates(aligned, "base")
    assert not set(cands) & set(aligned)
    for bad in ("postscript", "signoff_excl", "signoff_initial", "ps_question"):
        assert bad not in cands
    assert "curly_apostrophe" in cands and "greeting" in cands
    cands = lc.negative_candidates(["informal_lower", "quote"], "fi")
    assert not {"greeting", "greet_informal", "lowercase", "informal_lower"} & set(cands)
    # a shared mark: no body question / exclamation as the control while a "?" / "!" property is aligned
    cands = lc.negative_candidates(["greet_question", "weekday"], "gq")
    assert "question" not in cands and "ps_question" not in cands and "exclamation" in cands
    cands = lc.negative_candidates(["ps_q_excl", "weekday"], "pqx")
    assert not {"question", "exclamation", "signoff_excl", "ps_tentative"} & set(cands)
    cands = lc.negative_candidates(["signoff_excl", "weekday"], "base")
    assert "exclamation" not in cands and "question" in cands


def test_lower_twins_differ_only_in_the_capitals_after_the_greeting():
    notes, twins = lc.lower_twins(random.Random("tw"), TOPICS, 40, "fi")
    for note, twin in zip(notes, twins):
        assert note.split("\n", 1)[0] == twin.split("\n", 1)[0]
        assert lc.detect(note, "fi")["informal_lower"] == 1 and lc.detect(twin, "fi")["informal_lower"] == 0
        assert lc.detect(twin, "fi")["greet_informal"] == 1 and twin.lower() == note
        assert any(c.isupper() for c in twin)


def test_new_strings_hold_no_mark_another_property_tests():
    strings = (lc.FORMAL + lc.INFORMAL + lc.GREET_QUESTIONS + lc.GREET_FOLLOW + lc.GREET_WISHES + lc.GREET_REPLIES)
    for s in strings:
        assert "'" not in s and "’" not in s and not any(ch.isdigit() for ch in s)
        assert not any(w.lower() in s.lower() for w in ft.WEEKDAYS)
        assert not any(e.lower() in s.lower() for e in ft.EMOTICONS)
        assert "(" not in s and '"' not in s and "#" not in s and "  " not in s
    assert not set(lc.FORMAL) & set(lc.INFORMAL)


PRIVATE_TREE = Path("/home/ec2-user/onsite/sub/tasks/shifthunt")
# The shipped free-text episodes' build seeds are private build provenance: they live in a gitignored file.
BUILD_SEEDS = ROOT / "results" / "private_1112" / "exp_f" / "bank_build_seeds.json"


@pytest.mark.skipif(not (PRIVATE_TREE / "artifacts" / "grader").exists() or not BUILD_SEEDS.exists(),
                    reason="private artifact tree or private build seeds absent")
def test_pool_weights_reproduce_the_shipped_free_text_aligned_sets():
    """POOL_WEIGHTS / P_NEG are the valid planted artifacts of ft_screen + ft_tp2_r90a, and with that pool
    episode_files._conf reproduces the stored aligned sets and signs (read-only; nothing printed)."""
    probes, grader = ROOT / "artifacts" / "probes", PRIVATE_TREE / "artifacts" / "grader"
    bank = PRIVATE_TREE / ".cache" / "bank"

    class Art:
        def __init__(self, build, name):
            self.meta = json.loads((probes / build / f"{name}.json").read_text())
            ref = grader / build / f"{name}_ref.json"
            self.ref = json.loads(ref.read_text()) if ref.exists() else None
            self.ok = (grader / build / f"{name}.npz").exists()

    pool = [a for b in ("ft_screen", "ft_tp2_r90a") for m in json.loads((probes / b / "manifest.json").read_text())
            for a in [Art(b, m["name"])] if a.ok and (a.meta["kind"] == "null" or (a.ref and a.ref["valid"]))]
    planted = [a.meta for a in pool if a.meta["kind"] == "planted"]
    assert dict(Counter(m["cue"] for m in planted)) == lc.POOL_WEIGHTS
    assert sum(m["sign"] < 0 for m in planted) / len(planted) == lc.P_NEG
    keep = E.tg
    E.tg = ft
    try:
        for ep, seed in json.loads(BUILD_SEEDS.read_text()).items():
            ans = json.loads((bank / ep / "private" / "answer.json").read_text())
            arts = [Art(*p["source"].split("/")) for p in ans["probes"]]
            rng = random.Random(f"episode:{seed}")
            rng.getrandbits(63)
            assert rng.getrandbits(63) == ans["sample_seed"]
            rng.getrandbits(64)
            feats, signs = E._conf(rng, arts, pool)
            assert feats == ans["conf_features"]
            assert signs == [p["conf_signs"] for p in ans["probes"]]
    finally:
        E.tg = keep
