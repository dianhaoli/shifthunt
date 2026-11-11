"""Open-8 feasibility (D35), final-message viewer: the first N characters of each run's last long agent message,
with whether the prompt had a hints section and the episode answer summary. Inspection only: it prints transcript
text and answers to stdout and writes nothing; run it only into a private place.

    python scripts/feasibility/open8_final_msg.py --raw R N BATCH/RUN [BATCH/RUN ...]
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default=os.environ.get("SHIFTHUNT_RAW", str(BC.HARNESS / "results" / "rollouts")))
    ap.add_argument("n", type=int)
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args(argv)
    for run in a.runs:
        d = f"{a.raw}/{run}"
        last, hints = "", None
        for f in glob.glob(f"{d}/transcript_*.jsonl"):
            for line in open(f):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                m = r.get("message") or {}
                if r.get("type") == "assistant":
                    for c in m.get("content", []):
                        if c.get("type") == "text" and len(c["text"]) > 200:
                            last = c["text"]
                elif r.get("type") == "user" and hints is None and isinstance(m.get("content"), str):
                    hints = "Hints for this episode" in m["content"]
        for f in glob.glob(f"{d}/codex_events.jsonl"):
            for line in open(f):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                it = r.get("item") or {}
                if (r.get("type") == "item.completed" and it.get("type") == "agent_message"
                        and len(it.get("text") or "") > 200):
                    last = it["text"]
        ans = json.load(open(f"{d}/answer.json"))
        print("=" * 30, run, open(f"{d}/episode_id").read().strip(), "hints", hints,
              [(p["kind"][:1], p.get("cue")) for p in ans["probes"]])
        print(last[:a.n])


if __name__ == "__main__":
    main()
