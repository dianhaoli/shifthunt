#!/usr/bin/env bash
# quote-check every record, then build judge batches for any new same-cell pairs (tag = next free number)
cd "$(dirname "$0")"
exec 9>judge/.post.lock; flock 9
python3 - <<'PY'
import json, subprocess, os
inv = json.load(open("inventory.json"))
bad = []
for k, v in inv.items():
    a = v["anon"]
    if os.path.exists(f"out/{a}.json"):
        r = subprocess.run(["python3", "check_quotes.py", f"roll/{k}.condensed.md", f"out/{a}.json", f"out/{a}.py"], capture_output=True, text=True)
        if not r.stdout.strip().endswith("OK"): bad.append(a)
print("quote check fails:", bad)
PY
n=$(ls judge/S*.txt judge/Q*.txt 2>/dev/null | sed -E 's/.*[SQ]([0-9]+)\.txt/\1/' | sort -n | tail -1); n=$(printf "%02d" $((10#${n:-0}+1)))
python3 mkpairs.py $n
