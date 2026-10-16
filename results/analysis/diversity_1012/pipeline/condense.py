"""condense.py <rollout_dir> <key>  -> roll/<key>.condensed.md (same format as the prior audit's extract.py/p2_extract.py)."""
import glob, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
src = open(f"{D}/extract.py").read().split("for r in inv:")[0]
ns = {}; exec(src.replace('inv = json.load(open("inventory.json"))', "inv = []"), ns)
rd, key = sys.argv[1], sys.argv[2]
tr = sorted(glob.glob(f"{rd}/transcript*.jsonl"))[0]
steps = ns["cc_steps"](tr)
with open(f"{D}/roll/{key}.condensed.md", "w") as f:
    for i, s in enumerate(steps):
        hdr = {"note": "NOTE", "cmd": "CMD", "write": f"WRITE {s.get('path')}", "edit": f"EDIT {s.get('path')}", "other": "OTHER"}[s["kind"]]
        f.write(f"\n### [{i}] {hdr}\n{s['text']}\n")
        if "out" in s:
            o = s["out"]; o = o if len(o) <= 1200 else o[:1200] + f"\n...[{len(o)-1200} chars truncated]"
            f.write(f"--- output:\n{o}\n")
print(json.dumps(dict(key=key, n_steps=len(steps), transcript=tr)))
