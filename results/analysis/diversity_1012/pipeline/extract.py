"""Condense each rollout transcript into steps.jsonl + condensed.md (notes, commands, code, truncated outputs)."""
import json, os, ast
inv = json.load(open("inventory.json"))
os.makedirs("roll", exist_ok=True)
OUT_CHARS = 1200

def cc_steps(path):
    steps, pending = [], {}
    for line in open(path):
        d = json.loads(line)
        m = d.get("message") or {}
        if d.get("type") == "assistant":
            for c in m.get("content", []) if isinstance(m.get("content"), list) else []:
                if c.get("type") == "text" and c["text"].strip():
                    steps.append(dict(kind="note", text=c["text"]))
                elif c.get("type") == "tool_use":
                    inp = c.get("input", {})
                    if c["name"] == "Bash":
                        s = dict(kind="cmd", text=inp.get("command", ""))
                    elif c["name"] in ("Write",):
                        s = dict(kind="write", path=inp.get("file_path"), text=inp.get("content", ""))
                    elif c["name"] == "Edit":
                        s = dict(kind="edit", path=inp.get("file_path"), text=f"--- old\n{inp.get('old_string','')}\n+++ new\n{inp.get('new_string','')}")
                    else:
                        s = dict(kind="other", text=f"{c['name']} {json.dumps(inp)[:500]}")
                    steps.append(s); pending[c["id"]] = s
        elif d.get("type") == "user" and isinstance(m.get("content"), list):
            for c in m["content"]:
                if c.get("type") == "tool_result" and c.get("tool_use_id") in pending:
                    out = c.get("content")
                    if isinstance(out, list):
                        out = "\n".join(x.get("text", "") for x in out if isinstance(x, dict))
                    pending[c["tool_use_id"]]["out"] = str(out)
    return steps

def sol_steps(path):
    steps, pending = [], {}
    for line in open(path):
        d = json.loads(line)
        if d.get("type") == "assistant":
            if (d.get("text") or "").strip():
                steps.append(dict(kind="note", text=d["text"]))
            tc = d.get("tool_calls") or []
            if isinstance(tc, str):
                try: tc = ast.literal_eval(tc)
                except Exception: tc = []
            for c in tc:
                try: cmd = json.loads(c["arguments"]).get("command", "")
                except Exception: cmd = str(c.get("arguments"))
                s = dict(kind="cmd", text=cmd); steps.append(s); pending[c["call_id"]] = s
        elif d.get("type") == "tool_output" and d.get("call_id") in pending:
            pending[d["call_id"]]["out"] = str(d.get("output", ""))
    return steps

for r in inv:
    if r["run"] == "r0_smoke_haiku" or not r["transcript"]:
        continue
    key = f"{r['run']}__{r['rid']}"
    sol = r["transcript"].endswith("/transcript.jsonl")
    steps = sol_steps(r["transcript"]) if sol else cc_steps(r["transcript"])
    with open(f"roll/{key}.steps.jsonl", "w") as f:
        for s in steps: f.write(json.dumps(s) + "\n")
    with open(f"roll/{key}.condensed.md", "w") as f:
        for i, s in enumerate(steps):
            hdr = {"note": "NOTE", "cmd": "CMD", "write": f"WRITE {s.get('path')}", "edit": f"EDIT {s.get('path')}", "other": "OTHER"}[s["kind"]]
            f.write(f"\n### [{i}] {hdr}\n{s['text']}\n")
            if "out" in s:
                o = s["out"]; o = o if len(o) <= OUT_CHARS else o[:OUT_CHARS] + f"\n...[{len(o)-OUT_CHARS} chars truncated]"
                f.write(f"--- output:\n{o}\n")
    r["key"] = key; r["n_steps"] = len(steps)
json.dump(inv, open("inventory.json", "w"), indent=1)
import subprocess
print(subprocess.run("wc -c roll/*.condensed.md | sort -n | head -3; wc -c roll/*.condensed.md | sort -n | tail -4", shell=True, capture_output=True, text=True).stdout)
