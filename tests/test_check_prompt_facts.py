"""The held-out reliance estimator in scripts/check_prompt_facts.py on synthetic data."""
import importlib.util
import os
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_prompt_facts", ROOT / "scripts" / "check_prompt_facts.py")
cpf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpf)


def _synthetic(n=4096, seed=0):
    rng = np.random.default_rng(seed)
    feats = ["a", "parent", "child", "d"]
    fl = rng.integers(0, 2, (4, n))
    fl[2] = fl[2] * fl[1]  # child implies parent, flags as rendered
    tp = np.arange(n) % 2
    coef = np.array([1.5, 0.6, -0.9, 0.0])  # topic coef 3.0 -> ratios 0.5, 0.2, -0.3, 0
    y = fl.T @ coef - 3.0 * (tp == 0) + 3.0 * (tp == 1) * 0 + 0.7 + rng.normal(0, 0.05, n)
    return feats, fl, tp, y


def test_ols_ratio_recovers_coefficients():
    feats, fl, tp, y = _synthetic()
    r = cpf.ols_ratio(cpf.design(fl, tp), y)
    assert np.allclose(r, [0.5, 0.2, -0.3, 0.0], atol=0.01)


def test_alt_coding_child_is_parent_plus_child():
    feats, fl, tp, y = _synthetic()
    alt = cpf.alt_coding(fl, feats, {"child": "parent"})
    r = cpf.ols_ratio(cpf.design(alt, tp), y)
    assert np.allclose(r, [0.5, 0.2, -0.1, 0.0], atol=0.01)  # child from none = 0.2 - 0.3


def test_bootstrap_se_and_classify():
    feats, fl, tp, y = _synthetic(n=1024)
    pt, se = cpf.ratio_boot(cpf.design(fl, tp), y, 200, np.random.default_rng(1))
    assert (se > 0).all() and (se < 0.01).all()
    assert cpf.classify(0.5, 0.01, True) == "ok"
    assert cpf.classify(0.29, 0.01, True) == "TIGHT"
    assert cpf.classify(0.25, 0.01, True) == "FAIL"
    assert cpf.classify(0.31, 0.01, True) == "MARGINAL"
    assert cpf.classify(-0.2, 0.01, False) == "FAIL"
    assert cpf.classify(0.155, 0.01, False) == "TIGHT"
    assert cpf.classify(0.14, 0.01, False) == "MARGINAL"


def test_source_rng_independent_of_order():
    a = cpf.source_rng("pool_x/planted_001").integers(0, 1 << 30, 5)
    _ = cpf.source_rng("pool_y/null_002").integers(0, 1 << 30, 5)
    b = cpf.source_rng("pool_x/planted_001").integers(0, 1 << 30, 5)
    assert (a == b).all()
    assert not (a == cpf.source_rng("pool_x/planted_002").integers(0, 1 << 30, 5)).all()


def test_load_heldout_checks_stream_and_n(tmp_path):
    f = tmp_path / "s.npz"
    n = 32
    kw = dict(logits=np.zeros(n), flags=np.zeros((3, n), np.int8), features=np.array(["a", "b", "c"]),
              topic=np.zeros(n, np.int8))
    np.savez(f, stream=f"{cpf.HELDOUT_STREAM}:7", n=n, **kw)
    assert cpf.load_heldout(f, 7, n)[0] is not None
    assert cpf.load_heldout(f, 8, n)[0] is None  # other eval_seed
    assert cpf.load_heldout(f, 7, 64)[0] is None  # other N
    np.savez(f, stream="other:7", n=n, **kw)
    assert cpf.load_heldout(f, 7, n)[0] is None
    assert cpf.load_heldout(tmp_path / "missing.npz", 7, n) == (None, "missing")


def test_small_pools_merged_into_family_row():
    rows = {f"{pl}/s{i}": {"pool": pl} for pl, k in [("ft_a", 4), ("ft_b", 1), ("knob_c", 3)] for i in range(k)}
    key = cpf.row_keys(rows)
    assert key == {"ft_a": "ft_* (merged)", "ft_b": "ft_* (merged)", "knob_c": "knob_c"}


# ---- prompt variants of the black-box study (check_variants: no bank arrays, no torch)

import json  # noqa: E402

import pytest  # noqa: E402

from shifthunt import toolserver as ts  # noqa: E402

HINT = "Some properties occur only together with another property; cost $5 is not a ${var}."


def _task(substrate="templated", **extra):
    task = {"n_probes": 4, "k": 16, "probes": [{"probe": j, "topics": ["a", "b"]} for j in range(4)],
            "budgets": dict(ts.DEFAULT_BUDGETS),
            "contract": {"max_cues": 4, "max_latents": 16, "max_regex": 200,
                         "scopes": ["any", "first_line", "last_line"]}, **extra}
    if substrate != "templated":
        task["substrate"] = substrate
    return task


HINT_STAT = "arms: a hint has SAE or ablation text (informational; 1 = yes: not a blackbox item)"


def _failed(C):
    return {name: where for name, where in C.fail.items() if where}


@pytest.mark.parametrize("task,pinned", [
    (_task(), 1), (_task("freetext"), 1), (_task("freetext", hints=[HINT]), 1), (_task(hints=[HINT, "second"]), 1),
    ({**_task(), "budgets": {**ts.DEFAULT_BUDGETS, "probe_query": 16}}, 0),  # a budget variant: not the pinned shape
    ({**_task(), "n_probes": 2, "probes": _task()["probes"][:2]}, 0)])
def test_check_variants_passes_on_every_arm(tmp_path, task, pinned):
    C = cpf.Claims()
    before = json.dumps(task)
    prompts = cpf.check_variants(task, 384, C, "epX")
    assert _failed(C) == {} and len(C.fail) == 12 and all(name.startswith("arms: ") for name in C.fail)
    assert C.stats.get(HINT_STAT, []) == ([0.0] if task.get("hints") else [])
    assert set(prompts) == set(cpf.ARMS) == {("open", None), ("open", 64), ("blackbox", None), ("blackbox", 64)}
    assert json.dumps(task) == before
    assert C.stats["arms: open prompt compared with the main study's (1 = yes; 0 = another shape)"] == [pinned]
    mod = cpf.task_py()
    for (access, pq), prompt in prompts.items():
        t = mod.apply_problem(task, access, pq)
        assert prompt == mod.render(t, access, ts.help_text(access), cpf.HARD_STOP_S, 384)
        assert mod.split_hints(prompt)[1] == list(task.get("hints") or [])
    for word in cpf.BLACKBOX_ABSENT:
        assert word not in prompts["blackbox", 64].replace(ts.ACCESS_HELP["blackbox"], "")
        assert word in prompts["open", 64]
    for prompt in prompts.values():  # the latent-id limit is stated in every arm, blackbox included
        assert prompt.count(cpf.LIMIT_MD.format(k=task["k"])) == 1
    assert "(with a scope). A probe may list at most 16 distinct latent ids" in prompts["blackbox", None]
    assert "(with a scope) plus SAE latents to ablate. A probe may list at most 16" in prompts["open", None]
    (tmp_path / "public").mkdir()  # render_prompt (the per-episode claims) reads only the corpus size from disk
    (tmp_path / "public" / "corpus.json").write_text(json.dumps({"texts": [{}] * 384}))
    assert cpf.render_prompt({**task, "access": "blackbox"}, tmp_path) == prompts["blackbox", None]
    assert cpf.render_prompt(task, tmp_path) == prompts["open", None]


def test_check_variants_reports_a_hint_with_sae_text():
    """Hints are rendered in every arm; one that talks about the SAE makes the episode unusable as a blackbox
    item. The contract part still passes, so this is reported, not failed (as "hint names a property" is)."""
    C = cpf.Claims()
    prompts = cpf.check_variants(_task(hints=["Rank the SAE latents by the probe gradient first."]), 384, C)
    assert _failed(C) == {} and C.stats[HINT_STAT] == [1.0] and "SAE latents" in prompts["blackbox", None]


def test_check_variants_other_corpus_size_is_not_compared_with_the_pin():
    C = cpf.Claims()
    cpf.check_variants(_task(), 96, C)
    assert _failed(C) == {} and list(C.stats.values()) == [[0.0]]


def test_check_variants_catches_a_changed_open_prompt(monkeypatch):
    mod = cpf.task_py()
    monkeypatch.setitem(mod.ACCESS_MD, "open", "You can compute SAE activations for any text.")
    C = cpf.Claims()
    cpf.check_variants(_task(), 384, C, "epX")
    assert _failed(C) == {"arms: open prompt (hints excluded) is byte-identical to the main study's": ["epX-open"]}


@pytest.mark.parametrize("drop,claim", [
    (0, "arms: blackbox prompt (hints excluded) has no SAE or ablation text outside its access line"),
    (1, "arms: blackbox prompt (hints excluded) has no SAE or ablation text outside its access line"),
    (2, "arms: blackbox prompt (hints excluded) has no SAE or ablation text outside its access line"),
    (3, "arms: blackbox submit example has empty latents")])
def test_check_variants_catches_a_missing_blackbox_edit(monkeypatch, drop, claim):
    mod = cpf.task_py()
    edits = [e for i, e in enumerate(mod.BLACKBOX_EDITS) if i != drop]
    monkeypatch.setattr(mod, "BLACKBOX_EDITS", edits)
    C = cpf.Claims()
    cpf.check_variants(_task(), 384, C, "epX")
    assert _failed(C) == {claim: ["epX-blackbox", "epX-blackbox64"]}


LIMIT_CLAIM = "arms: the prompt states the latent-id limit once, with task.json's k = contract.max_latents"


def test_check_variants_catches_a_blackbox_prompt_without_the_latent_limit_sentence(monkeypatch):
    """Plan §8 removes only "latents to ablate" from the cue sentence. An edit that also deletes the sentence
    after it (the first implementation did) is a wording change beyond the plan: the blackbox arms fail."""
    mod = cpf.task_py()
    edits = list(mod.BLACKBOX_EDITS)
    assert edits[1] == (" plus SAE latents to ablate", "")
    edits[1] = (" plus SAE latents to ablate. A probe may list at most $k distinct latent ids over all its cues,\n"
                "and no cue's list may have more than $k entries.", ".")
    monkeypatch.setattr(mod, "BLACKBOX_EDITS", edits)
    C = cpf.Claims()
    prompts = cpf.check_variants(_task(), 384, C, "epX")
    assert _failed(C) == {LIMIT_CLAIM: ["epX-blackbox", "epX-blackbox64"]}
    assert "(with a scope).\n\n## How it is checked" in prompts["blackbox", None]


@pytest.mark.parametrize("old,new,counts", [
    # the first line of the sentence stays, the second is cut: the whole sentence is no longer there
    (",\nand no cue's list may have more than $k entries.", ".", (0, 1)),
    # the sentence stays, and the limit is stated a second time in other words
    ("## How it is checked", "No answer may hold more than $k distinct latent ids.\n\n## How it is checked", (1, 2)),
    # the first line is reworded, the second stays
    ("at most $k distinct latent ids", "up to $k latent ids", (0, 0)),
])
def test_check_variants_checks_both_halves_of_the_latent_limit_claim(monkeypatch, old, new, counts):
    """The limit claim has two counts: the whole sentence once, and the words "distinct latent ids" once. Each
    of these edits breaks one of them (or both) and nothing else the checker looks at."""
    mod = cpf.task_py()
    monkeypatch.setattr(mod, "BLACKBOX_EDITS", list(mod.BLACKBOX_EDITS) + [(old, new)])
    C = cpf.Claims()
    prompts = cpf.check_variants(_task(), 384, C, "epX")
    assert _failed(C) == {LIMIT_CLAIM: ["epX-blackbox", "epX-blackbox64"]}
    part = mod.split_hints(prompts["blackbox", None])[0]
    assert (part.count(cpf.LIMIT_MD.format(k=16)), part.count("distinct latent ids")) == counts
    assert prompts["open", None].count(cpf.LIMIT_MD.format(k=16)) == 1  # the open arms are untouched


def test_check_variants_catches_a_latent_limit_that_is_not_the_contracts():
    C = cpf.Claims()
    task = _task()
    task["contract"]["max_latents"] = 8  # the prompt would say 16, the contract enforces 8
    cpf.check_variants(task, 384, C, "epX")
    assert _failed(C) == {LIMIT_CLAIM: ["epX-open", "epX-open64", "epX-blackbox", "epX-blackbox64"]}


def test_check_variants_catches_help_and_budget_drift(monkeypatch):
    mod = cpf.task_py()
    C = cpf.Claims()
    monkeypatch.setitem(ts._HELP_BLACKBOX_TOOLS, "probe_scores", ts._HELP_TOOLS["probe_scores"])  # ablate is back
    cpf.check_variants(_task(), 384, C, "a")
    assert _failed(C) == {"arms: blackbox prompt (hints excluded) has no SAE or ablation text outside its access line":
                          ["a-blackbox", "a-blackbox64"]}
    monkeypatch.undo()
    C = cpf.Claims()
    monkeypatch.setattr(ts, "BLACKBOX_REFUSED", frozenset({"probe_gradient", "latent_means", "latent_tokens"}))
    cpf.check_variants(_task(), 384, C, "a")
    assert "arms: blackbox help lists exactly the blackbox tools" in _failed(C)
    monkeypatch.undo()
    C = cpf.Claims()
    monkeypatch.setattr(mod, "apply_problem", lambda task, access, pq=None: {**task, "access": access})  # no override
    cpf.check_variants(_task(), 384, C, "a")
    assert set(_failed(C)) == {"arms: task.json = the stored one with the problem's access and probe_query budget",
                               "arms: prompt, task.json and the tool server limit give the same probe_query budget"}
    assert all(where == ["a-open64", "a-blackbox64"] for where in _failed(C).values())
