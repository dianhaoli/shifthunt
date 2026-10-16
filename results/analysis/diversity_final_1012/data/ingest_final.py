"""ingest_final.py: condense the listed final_1012 rollouts into roll/, write inventory.json (same format as pipeline/ingest.py)."""
import glob, hashlib, json, os, subprocess, sys
W = os.path.dirname(os.path.abspath(__file__))
R = "results/rollouts"
BATCHES = {"final_1012_h1": "f1", "final_1012_h2": "f2"}
LIST = json.loads(sys.argv[1])
os.makedirs(f"{W}/pipeline/roll", exist_ok=True)
inv = json.load(open(f"{W}/inventory.json")) if os.path.exists(f"{W}/inventory.json") else {}
out = []
for item in LIST:
    bdir, cid = item.split("/"); b = BATCHES[bdir]; rd = f"{R}/{bdir}/{cid}"; key = f"{b}__{cid}"
    g = f"{rd}/grade.json"
    assert os.path.exists(g) and glob.glob(f"{rd}/transcript*.jsonl"), rd
    subprocess.run([sys.executable, f"{W}/pipeline/condense.py", rd, key], check=True, capture_output=True)
    os.replace(f"{W}/pipeline/roll/{key}.condensed.md", f"{W}/roll/{key}.condensed.md")
    gr = json.load(open(g)); ep = open(f"{rd}/episode_id").read().strip()
    anon = "s" + hashlib.sha1(("shuffle7:" + key).encode()).hexdigest()[:8]
    inv[key] = dict(key=key, anon=anon, batch=b, cid=cid, problem=ep, episode=ep.split("-")[0],
                    access=ep.split("-", 1)[1], model="opus48", score=gr.get("score"),
                    probes=[dict(kind=p.get("kind"), pass_=p.get("pass"), bucket=p.get("bucket"))
                            for p in gr["details"]["probes"]])
    out.append(dict(key=key, anon=anon, episode=inv[key]["episode"], score=inv[key]["score"],
                    condensed_path=f"{W}/roll/{key}.condensed.md"))
json.dump(inv, open(f"{W}/inventory.json", "w"), indent=1)
print(json.dumps(out))
