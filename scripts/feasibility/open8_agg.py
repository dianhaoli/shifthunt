"""Open-8 feasibility (D35), NAME by population: for the main study (r1103 batches 1-2), Block 1 Open-8, BB-64 and
BB-8, the NAME count per episode type and agent, the reasons NAME failed (hard-slot bucket, null claim), the
probe_query texts spent on the hard probe by named and unnamed runs, and the distribution of claimed-cue BAs.

    python scripts/feasibility/open8_agg.py --out AGG.json [--raw R]

Every run with a grade.json that has per-probe records is read (as the scratch analysis did; the counted-run
filter of score_naming is not applied). Tracked numbers are pooled by episode type (no per-episode cue mapping).
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

GROUPS = {"r1103": ["r1103_%s_%s" % (m, b) for m in ("gpt", "opus", "sonnet", "haiku") for b in ("b1", "b2")],
          "r1112_open8": ["r1112_gpt_open8", "r1112_haiku_open8"],
          "r1112_bb64": ["r1112_gpt_bb64", "r1112_haiku_bb64"], "r1112_bb8": ["r1112_gpt_bb8", "r1112_haiku_bb8"]}


def ba_bin(b):
    return "1.0" if b == 1 else ">=0.95" if b >= .95 else "0.8-0.95" if b >= .8 else "0.7-0.8" if b >= .7 else "<0.7"


def main(argv=None):
    from shifthunt import reward as R
    a = BC.parser(__doc__, private=False, raw=True).parse_args(argv)
    bas, out = Counter(), {}
    for gname, sets in GROUPS.items():
        tab = defaultdict(lambda: [0, 0])
        hb = defaultdict(Counter)
        hq = defaultdict(lambda: {"named": [], "not_named": []})
        for s in sets:
            for d in BC.run_dirs(a.raw, [s]):
                d += "/"
                if not os.path.exists(d + "grade.json"):
                    continue
                gr = json.load(open(d + "grade.json"))
                recs = gr.get("details", {}).get("probes", [])
                if not recs:
                    continue
                ans = json.load(open(d + "answer.json"))
                ep = open(d + "episode_id").read().strip().split("-")[0]
                et = BC.EP_TYPE[ep]
                hard = R.hard_slots(ans)
                name = R.name_outcome(recs, hard)
                model = s.split("_")[1]
                for key in (et, f"{et}|{model}", "all"):
                    tab[key][0] += int(name)
                    tab[key][1] += 1
                h = recs[hard[0]]
                nulls_bad = any(not r["pass"] for r in recs if r["kind"] == "null")
                if not name:
                    hb[et][f"{h.get('bucket')}{'|null_bad' if nulls_bad else ''}"] += 1
                pq = 0
                for line in open(d + "log.jsonl"):
                    r = json.loads(line)
                    if (r.get("tool") == "probe_query" and r.get("status") == "ok"
                            and r["args"].get("probe") == hard[0]):
                        pq += r["charges"].get("probe_query", 0)
                hq[et]["named" if name else "not_named"].append(pq)
                for r in recs:
                    for c in r.get("cues", []):
                        bas[ba_bin(c["ba"])] += 1
        out[gname] = {"NAME": {k: f"{v[0]}/{v[1]}" for k, v in sorted(tab.items())},
                      "fail_buckets": {k: dict(v) for k, v in hb.items()},
                      "hard_probe_queries": {et: {k: BC.stats(v) for k, v in d.items()} for et, d in hq.items()}}
    BC.write_out(a.out, {"script": "open8_agg", "by_population": out, "claimed_cue_ba_bins": dict(bas)})


if __name__ == "__main__":
    main()
