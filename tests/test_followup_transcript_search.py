import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import followup_transcript_search as T  # noqa: E402


def _write(p, rows):
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_claude_blocks_skip_prompt_and_tool_results(tmp_path):
    f = tmp_path / "transcript_x.jsonl"
    _write(f, [
        {"type": "user", "message": {"content": "main cue at least 0.3 times the topic"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "the band rules out this"},
                                                      {"type": "tool_use", "input": {"command": "echo 0.15"}},
                                                      {"type": "thinking", "thinking": "error term matters"}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "contract gap 0.3"}]}},
    ])
    b = T.claude_blocks(f)
    assert [k for k, _ in b] == ["visible", "visible", "thinking"]
    counts, hits = T.search(b)
    assert counts["visible"]["band_any"] == 1 and counts["visible"].get("gap_any") == 0
    assert counts["all"]["gap_any"] == 1
    assert counts["visible"][r"band"] == 1 and counts["visible"][r"rules? out"] == 1
    assert counts["visible"][r"0\.15"] == 1
    assert r"contract" not in counts["visible"]  # only in a tool result


def test_codex_blocks(tmp_path):
    f = tmp_path / "codex_session_rollout-1.jsonl"
    _write(f, [
        {"type": "response_item", "payload": {"type": "message", "role": "user",
                                              "content": [{"type": "input_text", "text": "contract 0.15"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                                              "content": [{"type": "output_text", "text": "Proxy is off by scale"}]}},
        {"type": "response_item", "payload": {"type": "custom_tool_call", "input": "x = 0.30"}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "output": "band"}},
        {"type": "response_item", "payload": {"type": "reasoning", "summary": [], "encrypted_content": "zz"}},
    ])
    b = T.codex_blocks(f)
    assert [k for k, _ in b] == ["visible", "visible"]
    counts, _ = T.search(b)
    assert counts["visible"]["gap_any"] == 1 and counts["visible"]["band_any"] == 1
    assert counts["visible"][r"0\.3"] == 1 and r"band" not in counts["visible"]


def test_proxy_pattern_does_not_cross_lines():
    counts, _ = T.search([("visible", "the proxy\nis off")])
    assert counts["visible"].get("gap_any") == 0


def test_blocks_of_needs_one_engine(tmp_path):
    (tmp_path / "transcript_a.jsonl").write_text("")
    (tmp_path / "codex_session_rollout-a.jsonl").write_text("")
    assert T.blocks_of(tmp_path) == (None, [])
