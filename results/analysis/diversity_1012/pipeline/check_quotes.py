import json, re, sys, ast
log, js, py = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(log).read()
parts = re.split(r'\n### \[(\d+)\] ', '\n' + text)
steps = {}
for i in range(1, len(parts), 2):
    steps[int(parts[i])] = parts[i + 1]
d = json.load(open(js))
items = [("pp", x) for x in d["per_probe"]] + [("dp", x) for x in d["decision_points"]]
ok = True
for k, x in items:
    q, s = x["quote"], x["step"]
    if len(q) > 300:
        print("TOO LONG", k, len(q)); ok = False
    if q not in steps.get(s, ""):
        where = [i for i, b in steps.items() if q in b]
        print("BAD", k, s, where, q[:80]); ok = False
nlines = len(open(py).read().splitlines())
ast.parse(open(py).read())
print("script_lines actual", nlines, "json", d["script_lines"])
print("summary words", len(d["summary"].split()), "phases", len(d["phases"]))
for x in d["per_probe"]:
    print("proc words", x["probe"], len(x["procedure"].split()))
print("OK" if ok else "FAIL")
