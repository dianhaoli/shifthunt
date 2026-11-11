import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import followup_tflags_samplebase as SB  # noqa: E402


def test_sample_pair_clears_main():
    rows = [[1, 0, 0]]                 # one agent text: main (col 0) on
    topics = [1]
    srows = [[0, 0, 0], [1, 1, 0]]     # sample note 0 differs only in the main; note 1 differs in col 1
    stopics = [1, 1]
    f = SB.flags_samplebase(rows, topics, srows, stopics, 0, 1, True, True, [[True]], [[False, True]])
    assert f["T_F2s"] == 0 and f["T_Ds"] == 0 and f["F2s"] == 0 and f["T_RULEs"] == 0
    assert f["n_sample_pairs"] == 2


def test_other_topic_and_sample_sample_pairs_ignored():
    rows = [[1, 0, 0]]
    topics = [0]
    srows = [[0, 0, 0], [1, 0, 0]]
    stopics = [1, 1]                   # wrong topic for the agent text; the two notes pair only with each other
    f = SB.flags_samplebase(rows, topics, srows, stopics, 0, 1, True, False, [], [])
    assert f["T_F2s"] == 1 and f["T_RULEs"] == 1 and f["n_sample_pairs"] == 0


def test_untested_cue_still_flags():
    rows = [[1, 0, 0], [0, 0, 0]]
    topics = [1, 1]
    f = SB.flags_samplebase(rows, topics, [], [], 0, 0, True, True, [[True, True]], [[]])
    assert f["T_F2s"] == 0 and f["F2s"] == 1 and f["T_RULEs"] == 1


def test_missing_texts():
    f = SB.flags_samplebase([], [], [], [], 0, 1, False, True, [], [])
    assert f["T_RULEs"] is None


def test_edit_variant_pairs_only_with_source_note():
    rows = [[1, 0, 0]]
    topics = [1]
    srows = [[0, 0, 0], [0, 0, 0]]
    stopics = [1, 1]
    f = SB.flags_samplebase(rows, topics, srows, stopics, 0, 1, True, False, [], [], allowed=[{1}])
    assert f["T_F2s"] == 0 and f["n_sample_pairs"] == 1
    f = SB.flags_samplebase(rows, topics, srows, stopics, 0, 1, True, False, [], [], allowed=[set()])
    assert f["T_F2s"] == 1 and f["n_sample_pairs"] == 0


def test_edit_sources():
    notes = ["the cat sat on the mat today.", "a completely different sentence about knitting yarn."]
    src = SB.edit_sources(["the cat sat on the mat today!", "zzzz"], notes)
    assert src == [{0}, set()]
