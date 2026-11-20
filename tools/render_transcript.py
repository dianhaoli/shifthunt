#!/usr/bin/env python3
"""Render a Claude Code transcript .jsonl as a color-coded, self-contained HTML page.

Usage: render_transcript.py OUT_DIR TRANSCRIPT.jsonl [TRANSCRIPT.jsonl ...]
Every block carries an anchor matching its JSONL line number (open page.html#L289).
"""
import html, json, re, sys
from pathlib import Path

CSS = """
:root{--bg:#fafafa;--fg:#1c1c1e;--mut:#6b7280;--card:#fff;--bd:#e5e7eb;
--user:#2563eb;--asst:#16a34a;--think:#9ca3af;--tool:#d97706;--res:#7c3aed;--err:#dc2626;--code:#f3f4f6}
@media(prefers-color-scheme:dark){:root{--bg:#111214;--fg:#e5e7eb;--mut:#9ca3af;--card:#1a1b1e;--bd:#2d2f34;
--user:#60a5fa;--asst:#4ade80;--think:#6b7280;--tool:#fbbf24;--res:#a78bfa;--err:#f87171;--code:#0d0e10}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:960px;margin:0 auto;padding:16px}
h1{font-size:18px}.meta{color:var(--mut);font-size:13px;margin-bottom:16px}
.b{background:var(--card);border:1px solid var(--bd);border-left:5px solid var(--c);border-radius:8px;
margin:10px 0;padding:8px 12px;position:relative}
.b .h{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--c);margin-bottom:4px}
.b .h a{color:var(--mut);font-weight:400;text-decoration:none;margin-left:8px}
.b:target{outline:3px solid var(--c)}
.user{--c:var(--user)}.asst{--c:var(--asst);border-left-width:8px}
.think{--c:var(--think);font-style:italic;color:var(--mut);padding:2px 12px}
.tool{--c:var(--tool)}.res{--c:var(--res);margin-left:24px}.err{--c:var(--err)}
.asst .t{font-size:16px}
pre{background:var(--code);border-radius:6px;padding:8px;overflow-x:auto;margin:4px 0;
font:12.5px/1.45 ui-monospace,Menlo,monospace;white-space:pre-wrap;word-break:break-word}
details>summary{cursor:pointer;color:var(--mut);font-size:13px}
.k{color:var(--tool);font-weight:600}
"""

def esc(s): return html.escape(s)

def block(line_no, kind, label, body, extra=""):
    return (f'<div class="b {kind}" id="L{line_no}"><div class="h">{label}'
            f'<a href="#L{line_no}">L{line_no}</a></div>{body}{extra}</div>')

def fold(text, limit=1500, summary=None):
    pre = f"<pre>{esc(text)}</pre>"
    if len(text) <= limit:
        return pre
    n = text.count("\n") + 1
    return f"<details><summary>{summary or 'show'} ({n} lines, {len(text):,} chars)</summary>{pre}</details>"

def render_tool_use(c):
    name, inp = c.get("name", "?"), c.get("input", {})
    if name == "Bash" and "command" in inp:
        desc = inp.get("description")
        body = (f'<div class="k">{esc(desc)}</div>' if desc else "") + fold(inp["command"], 1200, "full command")
    else:
        body = fold(json.dumps(inp, indent=1), 1200, "input")
    return name, body

def render(src: Path, out: Path):
    parts, counts = [], {}
    for n, raw in enumerate(src.read_text().splitlines(), 1):
        try: d = json.loads(raw)
        except Exception: continue
        t = d.get("type")
        if t not in ("user", "assistant"): continue
        content = d.get("message", {}).get("content")
        items = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
        for c in items:
            ct = c.get("type")
            if ct == "text" and t == "user":
                kind, label, body = "user", "User / prompt", fold(c["text"], 2500, "full prompt")
            elif ct == "text":
                kind, label, body = "asst", "Assistant", f'<div class="t">{esc(c["text"]).replace(chr(10), "<br>")}</div>'
            elif ct == "thinking":
                ms = d.get("thinkingDurationMs")
                txt = c.get("thinking") or ""
                kind, label = "think", "thinking"
                body = fold(txt, 800) if txt else f"(content redacted{f', thought for {ms/1000:.0f}s' if ms else ''})"
            elif ct == "tool_use":
                name, b = render_tool_use(c)
                kind, label, body = "tool", f"Tool call · {esc(name)}", b
            elif ct == "tool_result":
                r = c.get("content")
                if isinstance(r, list): r = "\n".join(x.get("text", "") for x in r if isinstance(x, dict))
                kind = "err" if c.get("is_error") else "res"
                label, body = "Result", fold(str(r), 1200, "output")
            else:
                continue
            counts[kind] = counts.get(kind, 0) + 1
            parts.append(block(n, kind, label, body))
    summ = " · ".join(f"{v} {k}" for k, v in counts.items())
    out.write_text(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                   f"<title>{esc(src.parent.name)}</title><style>{CSS}</style><main>"
                   f'<h1>{esc(src.parent.parent.name)}/{esc(src.parent.name)}</h1>'
                   f'<div class="meta">{esc(src.name)} — {summ}. Block anchors = JSONL line numbers.</div>'
                   + "".join(parts) + "</main>")

if __name__ == "__main__":
    outdir = Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
    for s in map(Path, sys.argv[2:]):
        o = outdir / f"{s.parent.parent.name}__{s.parent.name}.html"
        render(s, o); print(o)
