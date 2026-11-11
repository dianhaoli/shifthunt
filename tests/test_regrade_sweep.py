"""Synthetic tests for scripts/regrade_sweep.py (no bank, no runs)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import regrade_sweep as RS  # noqa: E402
from shifthunt.effects import Grid  # noqa: E402


def entry(*lists):
    return SimpleNamespace(none=False, cues=[SimpleNamespace(latents=list(x)) for x in lists])


def test_latent_list_order_and_dedup():
    assert RS.latent_list(entry([5, 3, 5], [3, 9, 1])) == [5, 3, 9, 1]
    assert RS.cut([5, 3, 9, 1], 2) == [5, 3]
    assert RS.cut([5, 3], None) == [5, 3]
    assert RS.cut([5, 3], 50) == [5, 3]


def test_slot_pass_rule():
    assert RS.slot_pass(True, [0.3], 0.9, [0.3])
    assert not RS.slot_pass(True, [0.29], 0.9, [0.3])
    assert not RS.slot_pass(True, [0.5], 0.79, [0.3])
    assert not RS.slot_pass(False, [0.5], 0.9, [0.3])
    assert not RS.slot_pass(True, [0.5, 0.1], 0.9, [0.3, 0.3])


def test_tau_of_cells():
    own, ref = [0.2, 0.25], [0.4, 0.5]
    assert np.allclose(RS.tau_of(("d6", "own", None), own, ref), own)
    assert np.allclose(RS.tau_of(("d6", 0.4, 5), own, ref), [0.4, 0.4])
    assert np.allclose(RS.tau_of(("a1", 0.9, 4), own, ref), [0.36, 0.45])   # no clip, no floor
    assert np.allclose(RS.tau_of(("a1", 0.8, None), own, [0.1, 0.9]), [0.08, 0.72])


def test_cells_cover_both_grids():
    keys = {RS.cell_key(c) for c in RS.cells()}
    assert "d6|tau=own|k=all" in keys and "d6|tau=0.6|k=50" in keys
    assert "a1|tau=0.8|k=4" in keys and "a1|tau=1.0|k=all" in keys
    assert len(keys) == 1 + 4 + 6 * 5 + 5 * 3


def test_cell_outcome_with_closed_form_grid():
    rng = np.random.default_rng(0)
    n, m = 64, 6
    topic = np.repeat([0, 1], n // 2)
    state = np.tile([0, 1], n // 2)
    F = rng.random((n, m)) * 0.01
    F[:, 0] += 2.0 * state   # latent 0 carries the cue
    F[:, 1] += 3.0 * topic   # latent 1 carries the topic
    g = np.array([1.0, 1.0, 0, 0, 0, 0])
    mu = F.mean(0)
    logits = F @ g
    grid = Grid(logits, F, topic, state, [1], g, mu)
    rem, kept = grid.score([0])
    s = {"valid": True, "kind": "planted", "none": False, "named": True, "own_tau": [0.3], "ref_removal": [1.0],
         "by_k": {"all": {"removal": list(rem), "kept": kept}, "4": {"removal": list(rem), "kept": kept}}}
    assert rem[0] > 0.99 and kept > 0.99
    assert RS.cell_outcome(s, ("d6", "own", None)) == (True, True)
    assert RS.cell_outcome(s, ("a1", 1.0, 4)) == (True, rem[0] >= 1.0)
    rem1, kept1 = grid.score([1])   # ablating the topic latent: kept fails
    s["by_k"]["all"] = {"removal": list(rem1), "kept": kept1}
    assert RS.cell_outcome(s, ("d6", 0.15, None)) == (True, False)
    assert RS.cell_outcome({"valid": True, "kind": "null", "none": True}, ("d6", 0.6, 5)) == (True, True)
    assert RS.cell_outcome({"valid": False, "kind": "null"}, ("d6", 0.6, 5)) == (False, False)


def test_compare_records_exact():
    a = {"kind": "planted", "pass": True, "removal": [0.2], "kept": 0.9}
    assert RS.compare_records(a, dict(a)) == []
    assert RS.compare_records(a, {**a, "kept": 0.900001})
