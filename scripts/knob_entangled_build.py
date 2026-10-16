"""Knob "entangled" (GPU): build topic-entangled hashtag probes, their grader arrays and corpus evidence.

    flock /tmp/shifthunt-gpu.lock python scripts/knob_entangled_build.py [--tag knob_entangled] [--jobs 8]
        [--start 0] [--word topic]

Per job: topic pair, hashtag topic index a, eval_seed; hashtag word = topics[a] (registered in
shifthunt/knob_entangled.py); sign = +1 if a == 1 else -1 (ALIGNED: cue on for the label whose topic it
names). Probe: probes.search_planted (cue "hashtag", seed screen 64, planted_max 1.0, rho ladder extended
down to 0.6). Accepted probes: artifacts/probes/<tag>/planted_<j>.{npz,json}; grader arrays with
scripts/grader_build.build_one (pool salt, build name <tag>); then per probe the top-10 notes by max
token activation on an episode-style corpus for the top-64 agent-side IE latents (scan set), written to
artifacts/grader/<tag>/<name>_interp.json (true ids; gitignored).
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from shifthunt import effects as E  # noqa: E402
from shifthunt import episodes as EP  # noqa: E402
from shifthunt import hidden as H  # noqa: E402
from shifthunt import knob_entangled as K  # noqa: E402
from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.episode_files import corpus_notes  # noqa: E402

RESULTS = ROOT / "results" / "knobs" / "entangled"
ARTIFACTS = ROOT / "artifacts" / "probes"
GRADER = ROOT / "artifacts" / "grader"
CACHE = ROOT / ".cache" / "encodings"
LADDER = P.RHO_LADDER + (0.85, 0.8, 0.75, 0.7, 0.6)
N_CAND = 64
TOP_N = 10


def jobs(tag, n):
    rng = random.Random(f"knob_entangled:{tag}")
    out = []
    for j in range(n):
        topics = tuple(rng.sample(tg.TOPIC_NAMES, 2))
        a = rng.randrange(2)
        eval_seed = rng.getrandbits(31)
        out.append(dict(j=j, topics=topics, a=a, eval_seed=eval_seed, sign=1 if a == 1 else -1,
                        draw_rng=random.Random(rng.getrandbits(64))))
    return out


def scan_ie(a):
    """Agent-side IE from the paired-flip scan set (as grader_baselines.scan): -> (effect, shift)."""
    F = EP.csr(a.z, "scan")
    n = H.N_SCAN
    k = tg.FEATURES.index(a.meta["cue"])
    on = a.z["scan_levels"][:, k]
    orient = np.where(on == 0, 1.0, -1.0)[:, None]
    d = (F[(k + 1) * n:(k + 2) * n].toarray() - F[:n].toarray()) * orient
    return float((d @ a.arr["g"]).mean()), d.mean(0)


def other_eval_seeds(n=3):
    man = json.loads((ARTIFACTS / "build_screen2" / "manifest.json").read_text())
    return [m["eval_seed"] for m in man if m["kind"] == "planted"][:n]


def cue_line(cue, word, eval_seed):
    return f"#{word}" if cue == "hashtag" else P.cue_strings(eval_seed).closing.lower() + ","


def interp_evidence(subject, a, word):
    eff, shift = scan_ie(a)
    cand = E.ranked(a.arr["g"], shift, np.sign(eff) or 1, N_CAND)
    metas = [{"eval_seed": a.meta["eval_seed"]}] + [{"eval_seed": s} for s in other_eval_seeds()]
    texts, topics = corpus_notes(metas, f"knob_entangled_corpus:{a.meta['eval_seed']}")
    acts = subject.token_latents(texts, cand)
    mx = np.stack([t.acts.max(0) if len(t.acts) else np.zeros(len(cand)) for t in acts])  # [n, L]
    tag_line = cue_line(a.meta["cue"], word, a.meta["eval_seed"])
    has_tag = np.array([tag_line in t.lower().split("\n") for t in texts])
    out = []
    for c, lid in enumerate(cand):
        top = np.argsort(-mx[:, c], kind="stable")[:TOP_N]
        top = [int(i) for i in top if mx[i, c] > 0]
        # where the max token sits: inside the entangled hashtag line or not
        in_tag = []
        for i in top:
            toks = acts[i].tokens
            pos = int(np.argmax(acts[i].acts[:, c]))
            prefix = "".join(toks[:pos + 1])
            line = prefix.split("\n")[-1] + "".join(toks[pos + 1:]).split("\n")[0]
            in_tag.append(line.strip().lower() == tag_line)
        out.append({"id": int(lid), "rank": c, "top_topics": [topics[i] for i in top],
                    "top_has_tag": [bool(has_tag[i]) for i in top], "top_max_in_tag": in_tag,
                    "top_max": [float(mx[i, c]) for i in top]})
    return {"scan_effect": eff, "candidates": [int(x) for x in cand], "latents": out,
            "corpus_n": len(texts)}


def _mem_watch(period=10):
    import threading

    def run():
        while True:
            with open("/proc/self/status") as fh:
                d = dict(l.split(":", 1) for l in fh)
            print(f"[mem] anon {d['RssAnon'].strip()} file {d['RssFile'].strip()}", flush=True)
            time.sleep(period)
    threading.Thread(target=run, daemon=True).start()


def main():
    _mem_watch()
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="knob_entangled")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--screen", type=int, default=64)
    ap.add_argument("--cue", choices=["hashtag", "signoff"], default="hashtag")
    ap.add_argument("--closings", choices=["base", "strong"], default="base")
    args = ap.parse_args()
    import grader_build as GB
    from shifthunt.substrate import Subject
    K.install()
    K.use_lean_loader()  # same weights bitwise (verified), ~1 GB anon RSS instead of a CPU checkpoint copy
    salt = H.load_salt(GRADER)
    subject = Subject()
    lab = P.Lab(P.CachedEncoder(subject, CACHE))
    out = ARTIFACTS / args.tag
    out.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    man_path = out / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else []
    fits = open(RESULTS / f"{args.tag}_fits.jsonl", "a")
    t0 = time.time()
    for job in jobs(args.tag, args.jobs)[args.start:]:
        t = time.time()
        word = job["topics"][job["a"]]
        if args.cue == "hashtag":
            K.register(job["eval_seed"], word)
            assert P.cue_strings(job["eval_seed"]).hashtag == word
        else:
            closing = K.CLOSING_SETS[args.closings][word]
            K.register(job["eval_seed"], closing, field="closing")
            assert P.cue_strings(job["eval_seed"]).closing == closing
        K.save_registry()
        p, attempts = P.search_planted(lab, job["topics"], args.cue, job["sign"], job["eval_seed"],
                                       job["draw_rng"], max_draws=4, planted_max=1.0, ladder=LADDER,
                                       n_screen=args.screen)
        for k, row in enumerate(attempts):
            fits.write(json.dumps(row | {"job": job["j"], "attempt": k, "word": word,
                                         "accepted": p is not None and k == len(attempts) - 1}) + "\n")
        fits.flush()
        last = attempts[-1]
        print(f"job {job['j']} {job['topics']} {args.cue}:{word} sign {job['sign']}: "
              f"{'ACCEPTED' if p else 'failed'} after {len(attempts)} fits; last rho={last['rho']} "
              f"eps={last['eps']} rel={last['reliance'][args.cue]:.3f} "
              f"maxother={max(abs(v) for f, v in last['reliance'].items() if f != args.cue):.3f} "
              f"{last['failures']} {time.time() - t:.0f}s", flush=True)
        if p is None:
            continue
        name = f"planted_{job['j']:03d}"
        meta = P.save_probe(p, out, name) | {"attempts": len(attempts), "entangled_word": word}
        (out / f"{name}.json").write_text(json.dumps(meta, indent=1))
        manifest = [m for m in manifest if m["name"] != name] + [meta]
        man_path.write_text(json.dumps(manifest, indent=1))
        meta, arr = P.load_probe(out, name)
        drift = GB.build_one(subject, args.tag, meta, arr, salt)
        a = EP.load(args.tag, name)
        ev = interp_evidence(subject, a, word)
        (GRADER / args.tag / f"{name}_interp.json").write_text(json.dumps(ev))
        print(f"  grader arrays + interp done, reliance drift {drift:.1e}, scan effect {ev['scan_effect']:.3f} "
              f"{time.time() - t:.0f}s", flush=True)
    print(f"done in {time.time() - t0:.0f}s; encoded {lab.enc.n_encoded}, cache hits {lab.enc.n_cached}")


if __name__ == "__main__":
    main()
