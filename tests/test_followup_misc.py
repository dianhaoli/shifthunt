"""Synthetic tests for the follow-up 'misc' scripts (latent_regrade, scripted_cheaters, exp_f_ci)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import exp_f_ci as EF  # noqa: E402
import latent_regrade as LR  # noqa: E402
import scripted_cheaters as SC  # noqa: E402
from shifthunt.effects import Grid  # noqa: E402


def _claims(*lists):
    return [SimpleNamespace(latents=list(x)) for x in lists]


def test_latent_list_order_dedup_and_cut():
    cues = _claims([5, 3, 5], [3, 9, 1])
    assert LR.latent_list(cues) == [5, 3, 9, 1]
    assert LR.latent_list(cues, 2) == [5, 3]
    assert LR.latent_list(cues, 50) == [5, 3, 9, 1]
    assert LR.latent_list(_claims([], [])) == []


def test_removal_pass_per_main_and_scalar():
    assert LR.removal_pass([0.5, 0.31], 0.9, 0.30)
    assert not LR.removal_pass([0.5, 0.29], 0.9, 0.30)
    assert not LR.removal_pass([0.5], 0.79, 0.15)
    assert LR.removal_pass([0.2, 0.4], 0.8, [0.2, 0.4])
    assert not LR.removal_pass([0.2, 0.4], 0.8, [0.21, 0.4])


def test_cut_list_on_synthetic_grid_is_monotone_in_k():
    rng = np.random.default_rng(0)
    n, m = 64, 40
    topic = np.repeat([0, 1], n // 2)
    state = np.tile([0, 1], n // 2)
    F = rng.random((n, m)) * 0.1
    F[:, :6] += state[:, None] * np.linspace(1.0, 0.2, 6)  # the cue lives in latents 0..5, strongest first
    g = np.ones(m)
    logits = F @ g + 3.0 * topic
    grid = Grid(logits, F, topic, state[None, :], [1], g, F.mean(0))
    cues = _claims([0, 1, 2], [3, 4, 5])
    rems = [grid.score(np.unique(LR.latent_list(cues, k)))[0][0] for k in (1, 3, 5, None)]
    assert rems == sorted(rems)
    assert rems[-1] > 0.9


def test_union_regex():
    rx, sc, merged = SC.union_regex([("a", "any"), ("b|c", "any")])
    assert (rx, sc, merged) == ("(?:a)|(?:b|c)", "any", False)
    rx, sc, merged = SC.union_regex([("a", "first_line"), ("b", "any")])
    assert sc == "any" and merged
    rx, sc, merged = SC.union_regex([("a", "last_line"), ("b", "last_line")])
    assert sc == "last_line" and not merged


def test_sample_attribution_ranks_the_label_latent_first():
    labels = np.array([0, 0, 1, 1])
    F = np.array([[0, 1, 0], [0, 1, 0], [2, 1, 0], [2, 1, 0.5]], float)
    g = np.array([0.5, 3.0, 1.0])
    a = SC.sample_attribution(g, F, labels)
    assert np.allclose(a, [1.0, 0.0, 0.25])
    assert SC.top_ids(a, 2) == [0, 2]


def test_with_latents_puts_all_on_first_cue():
    cs = SC.with_latents([SC.cue("a", "any", []), SC.cue("b", "any", [])], [1, 2])
    assert cs[0]["latents"] == [1, 2] and cs[1]["latents"] == []


def test_exp_f_runner_modes():
    seen = []

    def base(jobs, texts):
        seen.append(list(jobs))
        return [([False] * len(texts), None) for _ in jobs]
    EF.make_runner("ci", base)([("abc", "any"), ("(?m)^x", "last_line")], ["t"])
    assert seen[-1] == [("(?i)abc", "any"), ("(?i)(?m)^x", "last_line")]
    assert EF.make_runner("cs", base) is base


def test_exp_f_ci_regex_is_case_insensitive_in_the_sandbox():
    run = EF.make_runner("ci")
    (m1, e1), (m2, e2) = run([("Hello", "any"), ("(?m)^P\\.S\\.", "any")], ["hello there", "x\np.s. hi"])
    assert e1 is None and e2 is None
    assert m1 == [True, False] and m2 == [False, True]
