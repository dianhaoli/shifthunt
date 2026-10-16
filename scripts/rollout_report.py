"""Tables from collect_rollouts summaries: pass rates, failure buckets and tool use per (model, access).

    python scripts/rollout_report.py results/rollouts/<run>/summary.jsonl [...] [--by access|model|episode]
"""
import argparse
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path


def rows(paths):
    seen = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            r = json.loads(line)
            seen[r["cid"]] = r  # a re-collect of the same container replaces the old row
    return list(seen.values())


def med(xs):
    return round(st.median(xs), 1) if xs else None


def report(rs, by):
    groups = defaultdict(list)
    for r in rs:
        groups[(r.get("model"), r[by])].append(r)
    for (model, key), g in sorted(groups.items(), key=lambda kv: str(kv[0])):
        graded = [r for r in g if r.get("pass") is not None]
        probes = [p for r in graded for p in r["probes"] if "bucket" in p]
        pl = [p for p in probes if p["kind"] == "planted"]
        nu = [p for p in probes if p["kind"] == "null"]
        buckets = Counter(p["bucket"] for p in probes if p["bucket"])
        tools = Counter()
        for r in g:
            tools.update(r["tool_calls"])
        print(f"\n## {model} / {by}={key}: n={len(g)} graded={len(graded)}")
        print(f"episode pass {sum(r['pass'] == 1.0 for r in graded)}/{len(graded)}; "
              f"planted {sum(p['pass'] for p in pl)}/{len(pl)}; null {sum(p['pass'] for p in nu)}/{len(nu)}")
        print(f"buckets: {dict(buckets)}; no submission: {sum(1 for r in g if r.get('feedback') == 'no accepted submission')}; "
              f"timeouts: {sum(1 for r in g if r.get('timeout'))}")
        print(f"median calls {med([r['n_calls'] for r in g])}; own-text SAE calls {med([r['own_text_sae_calls'] for r in g])}; "
              f"forward used {med([(r['budget'].get('forward') or {}).get('used', 0) for r in g])}; "
              f"probe_query used {med([(r['budget'].get('probe_query') or {}).get('used', 0) for r in g])}")
        print(f"tool mix (total): {dict(tools.most_common())}")
        print(f"cost: total ${sum(r['usd'] for r in g):.2f}, median ${med([r['usd'] for r in g])}")
        for r in g:
            fails = [(p.get("cue") or "null", p["bucket"]) for p in r["probes"] if p.get("bucket")]
            print(f"  {r['cid']} {r['episode']}-{r['access']}: pass={r.get('pass')} fails={fails} "
                  f"calls={r['n_calls']} ${r['usd']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("summaries", nargs="+")
    ap.add_argument("--by", default="access")
    a = ap.parse_args()
    report(rows(a.summaries), a.by)


if __name__ == "__main__":
    main()
