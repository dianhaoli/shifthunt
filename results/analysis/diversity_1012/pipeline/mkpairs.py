"""mkpairs.py -> new judge batches for every same-cell (episode x access) pair whose two records exist and
that has not been judged yet. Same formats as the prior audit's mkjudge.py:
  judge/S<tag>.txt : "- P<pid>: A = <abs>/out/<a>.py   B = <abs>/out/<b>.py"      (whole-rollout scripts)
  judge/Q<tag>.txt : "### Q<pid>\nA: <procedure>\nB: <procedure>"                  (subtask slot only)
Pair kinds and identities stay in judge/pairs_key.json (never shown to judges). A/B sides are shuffled with a
seeded RNG per pair. Prints the batch files written (one per line) as JSON.
"""
import hashlib, itertools, json, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
inv = json.load(open(f"{D}/inventory.json"))
SUBTASK = json.load(open(f"{D}/subtask_slots.json"))   # episode -> {"slot": i, "subtask": name}
kp = f"{D}/judge/pairs_key.json"
key = json.load(open(kp)) if os.path.exists(kp) else {}
done = {(v["level"], tuple(sorted([v["a_key"], v["b_key"]]))) for v in key.values()}
tag = sys.argv[1]
ok = lambda k: os.path.exists(f"{D}/out/{inv[k]['anon']}.py") and os.path.exists(f"{D}/out/{inv[k]['anon']}.json")
cells = {}
for k, v in inv.items():
    if ok(k):
        cells.setdefault(v["problem"], []).append(k)
S, Q = [], []
for prob, ks in sorted(cells.items()):
    for a, b in itertools.combinations(sorted(ks), 2):
        for level in ("script", "probe"):
            if (level, tuple(sorted([a, b]))) in done:
                continue
            rng = random.Random(f"ab:{level}:{a}:{b}")
            x, y = (a, b) if rng.random() < 0.5 else (b, a)
            pid = ("P" if level == "script" else "Q") + hashlib.sha1(f"{level}:{x}:{y}".encode()).hexdigest()[:6]
            ep = inv[a]["episode"]
            rec = {"pid": pid, "level": level, "a_key": x, "b_key": y, "problem": prob, "episode": ep,
                   "access": inv[a]["access"], "batch": inv[a]["batch"]}
            if level == "script":
                S.append(f"- {pid}: A = {D}/out/{inv[x]['anon']}.py   B = {D}/out/{inv[y]['anon']}.py")
            else:
                st = SUBTASK.get(ep)
                if st is None:
                    continue
                def proc(k):
                    r = json.load(open(f"{D}/out/{inv[k]['anon']}.json"))
                    pp = [p for p in r.get("per_probe", []) if int(p.get("probe", -1)) == st["slot"]]
                    return pp[0]["procedure"] if pp else "MISSING"
                rec["subtask"] = st["subtask"]; rec["slot"] = st["slot"]
                Q.append(f"### {pid}\nA: {proc(x)}\nB: {proc(y)}")
            key[pid] = rec
out = []
if S:
    open(f"{D}/judge/S{tag}.txt", "w").write("\n".join(S) + "\n"); out.append(f"S{tag}")
if Q:
    open(f"{D}/judge/Q{tag}.txt", "w").write("\n\n".join(Q) + "\n"); out.append(f"Q{tag}")
json.dump(key, open(kp, "w"), indent=1)
print(json.dumps({"batches": out, "n_script": len(S), "n_probe": len(Q)}))
