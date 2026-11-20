"""Every number the paper prints that is checkable from tracked files matches them (scripts/paper_numbers.py)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mod():
    spec = importlib.util.spec_from_file_location("paper_numbers", ROOT / "scripts" / "paper_numbers.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_paper_numbers_match_the_result_files(capsys):
    m = _mod()
    assert m.main([]) == 0
    out = capsys.readouterr().out
    assert " 0 differ" in out
    checked = [c for c in m.CHECKS if c[2] is not None]
    assert len(checked) >= 120
