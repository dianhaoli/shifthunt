"""Render a collected Claude Code transcript (*.jsonl) as readable text, in order.

    python scripts/render_transcript.py results/rollouts/<run>/<cid>/ [--max-result 1500] [--out FILE]

Prints each assistant text block, thinking block (if any text), tool call (Bash commands in full, other
tools as JSON) and tool result (truncated to --max-result characters, head and tail kept), numbered by
turn, with subagent transcripts after the main one. Reads only the collected copy, never the container.
"""
import argparse
import json
from pathlib import Path


def short(s, n):
    s = s if isinstance(s, str) else json.dumps(s)
    return s if len(s) <= n else s[: n * 2 // 3] + f"\n  [... {len(s) - n} chars cut ...]\n" + s[-n // 3:]


def result_text(c):
    if isinstance(c, list):
        return "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return str(c)


def render(path, n):
    out, turn, seen = [], 0, set()
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        msg = r.get("message")
        if not isinstance(msg, dict):
            continue
        role, content = msg.get("role"), msg.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for b in content or []:
            key = (msg.get("id"), json.dumps(b, sort_keys=True)[:200])
            if role == "assistant" and key in seen:
                continue
            seen.add(key)
            t = b.get("type")
            if role == "assistant" and t == "text" and b["text"].strip():
                turn += 1
                out.append(f"\n### [{turn}] ASSISTANT\n{b['text'].strip()}")
            elif role == "assistant" and t == "thinking" and b.get("thinking", "").strip():
                out.append(f"\n### THINKING\n{b['thinking'].strip()}")
            elif role == "assistant" and t == "tool_use":
                turn += 1
                inp = b.get("input", {})
                body = inp.get("command") if b.get("name") == "Bash" and "command" in inp else json.dumps(inp)
                out.append(f"\n### [{turn}] TOOL {b.get('name')}\n{body}")
            elif role == "user" and t == "tool_result":
                out.append(f"--- result{' (error)' if b.get('is_error') else ''}:\n{short(result_text(b.get('content')), n)}")
            elif role == "user" and t == "text" and turn == 0:
                out.append(f"### USER (prompt)\n{short(b['text'], 400)}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rollout_dir", type=Path)
    ap.add_argument("--max-result", type=int, default=1500)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    files = sorted(a.rollout_dir.glob("transcript_*.jsonl"), key=lambda p: p.stat().st_size, reverse=True)
    text = "\n\n".join(f"======== {f.name} ========\n{render(f, a.max_result)}" for f in files)
    if a.out:
        a.out.write_text(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
