"""agg_final.py: aggregate the final_1012 diversity audit (judge/, code/, inventory.json) into markdown tables."""
import json, os, sys, glob
from collections import defaultdict, Counter
W = os.path.dirname(os.path.abspath(__file__))
inv = json.load(open(f"{W}/inventory.json"))
anon = {k: v["anon"] for k, v in inv.items()}
by_anon = {v["anon"]: v for v in inv.values()}
SLOT = {"ep411": 2, "ep412": 2, "ep413": 0, "ep414": 2, "ep415": 2, "ep416": 3, "ep421": 1, "ep422": 1, "ep423": 0}
ARM = {**{e: "trap" for e in ("ep411", "ep413", "ep415")}, **{e: "two-part" for e in ("ep412", "ep414", "ep416")},
       **{e: "focused two-part" for e in ("ep421", "ep422", "ep423")}}
pairs = json.load(open(f"{W}/pairs_unblinded.json"))
code = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(f"{W}/code/*.json")}

# judge files: first entry script, second entry hard slot
J = {}
for f in sorted(glob.glob(f"{W}/judge/P*.json")):
    j = json.load(open(f)); pid = int(os.path.basename(f)[1:3])
    J[pid] = dict(script=j[0], hard=j[1])
for p in pairs:
    js, jh = J[p["pair"]]["script"], J[p["pair"]]["hard"]
    assert js["score"] == p["script_score"] and jh["score"] == p["hard_slot_score"], p["pair"]
    assert {js["A"], js["B"]} == {anon[p["a"]], anon[p["b"]]}, p["pair"]
    p["hard_one_config"] = bool(jh.get("one_config_script"))
    p["stages_script"] = js.get("differing_stages", []); p["stages_hard"] = jh.get("differing_stages", [])

def slot_pass(key):
    v = inv[key]; return bool(v["probes"][SLOT[v["episode"]]]["pass_"])
for p in pairs:  # slot outcome equals episode outcome here; assert it
    so = sorted([slot_pass(p["a"]), slot_pass(p["b"])], reverse=True)
    p["slot_outcome"] = {(True, True): "pass-pass", (False, False): "fail-fail"}.get(tuple(so), "pass-fail")
    assert p["slot_outcome"] == p["outcome"], p

KINDS = [("same_cell", "same cell (same episode)"), ("cross_episode_trap_passes", "cross-episode, trap passes"),
         ("cross_episode_focused_twopart", "cross-episode, focused two-part")]
OUTS = ["pass-pass", "fail-fail", "pass-fail"]

def stat(rows, s, oc):
    if not rows: return "n=0"
    xs = [r[s] for r in rows]
    return f"n={len(xs)} mean={sum(xs)/len(xs):.2f} >=4: {sum(x >= 4 for x in xs)}/{len(xs)} one-config: {sum(bool(r[oc]) for r in rows)}/{len(xs)}"

def judge_table(s, oc):
    out = ["| group | all | pass-pass | fail-fail | pass-fail |", "|---|---|---|---|---|"]
    groups = [("ALL pairs", pairs)] + [(lab, [p for p in pairs if p["kind"] == k]) for k, lab in KINDS]
    same = [p for p in pairs if p["kind"] == "same_cell"]
    groups += [("same cell, trap arm (ep411/413/415)", [p for p in same if ARM[p["cell"]] == "trap"]),
               ("same cell, two-part arm (ep412/414)", [p for p in same if ARM[p["cell"]] == "two-part"])]
    for lab, rows in groups:
        out.append(f"| {lab} | {stat(rows, s, oc)} | " + " | ".join(stat([r for r in rows if r['outcome'] == o], s, oc) for o in OUTS) + " |")
    return "\n".join(out)

def stage_counts(key):
    c = Counter(st for p in pairs for st in p[key]); return ", ".join(f"{k} {v}" for k, v in c.most_common())

print("## Script judge\n"); print(judge_table("script_score", "one_config")); print()
print(f"Differing stages named (script, n pairs={len(pairs)}): {stage_counts('stages_script')}\n")
print("## Hard-slot judge\n"); print(judge_table("hard_slot_score", "hard_one_config")); print()
print(f"Differing stages named (hard slot, n pairs={len(pairs)}): {stage_counts('stages_hard')}\n")

print("## Per pair\n")
print("| pair | kind | cell | A (score) | B (score) | outcome | script | hard slot | hard-slot probe A/B |")
print("|---|---|---|---|---|---|---|---|---|")
for p in pairs:
    ea, eb = inv[p["a"]]["episode"], inv[p["b"]]["episode"]
    print(f"| P{p['pair']:02d} | {p['kind']} | {p['cell'] if p['kind']=='same_cell' else ea+' x '+eb} | {anon[p['a']]} ({p['a_score']}) | {anon[p['b']]} ({p['b_score']}) | {p['outcome']} | {p['script_score']} | {p['hard_slot_score']} | {SLOT[ea]}/{SLOT[eb]} |")
print()

print("## Codebook agreement\n")
DIMS = ["D1_hypotheses", "D2_counterfactuals", "D3_effect_estimate", "D4_probe_query_allocation", "D5_null_rule",
        "D6_confound_disentangling", "D7_regex", "D8_latent_selection", "D9_verification"]
def agree(rows):
    r = []
    for d in DIMS:
        n = sum(code[anon[p["a"]]]["codes"][d]["primary"] == code[anon[p["b"]]]["codes"][d]["primary"] for p in rows)
        r.append(f"{n}/{len(rows)}")
    return r
print("| group | n pairs | " + " | ".join(d.split("_")[0] for d in DIMS) + " |"); print("|---|---|" + "---|" * len(DIMS))
groups = [("ALL pairs", pairs)] + [(lab, [p for p in pairs if p["kind"] == k]) for k, lab in KINDS] + \
         [(o, [p for p in pairs if p["outcome"] == o]) for o in OUTS]
for lab, rows in groups:
    print(f"| {lab} | {len(rows)} | " + " | ".join(agree(rows)) + " |")
print()
print("Primary codes per rollout:\n")
print("| anon | episode | ep pass | " + " | ".join(d.split("_")[0] for d in DIMS) + " |"); print("|---|---|---|" + "---|" * len(DIMS))
for a in sorted(code, key=lambda a: (by_anon[a]["episode"], a)):
    v = by_anon[a]
    print(f"| {a} | {v['episode']} | {int(v['score'])} | " + " | ".join(code[a]["codes"][d]["primary"] or "-" for d in DIMS) + " |")
print()

print("## probe_query texts per arm\n")
print("| arm | rollouts | single | bundle | topic | null | other | total | on hard slot |"); print("|---|---|---|---|---|---|---|---|---|")
agg = defaultdict(lambda: Counter()); nr = Counter()
for a, c in code.items():
    ep = by_anon[a]["episode"]; arm = ARM[ep]; nr[arm] += 1
    for k in ("single", "bundle", "topic", "null", "other"): agg[arm][k] += c["pq"].get(k, 0)
    agg[arm]["total"] += sum(c["pq"].get(k, 0) for k in ("single", "bundle", "topic", "null", "other"))
    agg[arm]["slot"] += sum(1 for t in c["pq_texts"] if t.get("probe") == SLOT[ep])
for arm in ("trap", "two-part", "focused two-part"):
    g = agg[arm]
    print(f"| {arm} | {nr[arm]} | {g['single']} | {g['bundle']} | {g['topic']} | {g['null']} | {g['other']} | {g['total']} | {g['slot']} |")
print()

print("## Hard slot: decisive reading per rollout\n")
print("| arm | cell | anon | slot pass | conclusion | evidence | n_notes | replicated | pq texts on slot | pq total |")
print("|---|---|---|---|---|---|---|---|---|---|")
for a in sorted(code, key=lambda a: (ARM[by_anon[a]["episode"]], by_anon[a]["episode"], a)):
    v = by_anon[a]; ep = v["episode"]; c = code[a]
    rd = [r for r in c.get("decisive_readings", []) if r.get("probe") == SLOT[ep]]
    main = next((r for r in rd if not str(r.get("conclusion", "")).lower().startswith("reject")), rd[0] if rd else {})
    nslot = sum(1 for t in c["pq_texts"] if t.get("probe") == SLOT[ep]); ntot = len(c["pq_texts"])
    concl = str(main.get("conclusion", "-")).replace("|", "/")[:48]
    print(f"| {ARM[ep]} | {ep} | {a} | {int(v['probes'][SLOT[ep]]['pass_'])} | {concl} | {main.get('evidence','-')} | {main.get('n_notes','-')} | {int(bool(main.get('replicated')))} | {nslot} | {ntot} |")
