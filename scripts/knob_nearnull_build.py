"""Knob "nearnull": near-threshold null and planted probes (GPU; run under the shared flock).

    python scripts/knob_nearnull_build.py [--tag knob_nearnull] [--weak 6] [--plain 4] [--planted 6]

Three recipes, all through probes.py (fit, reliance, validity, seed screen); only the search differs.
  weak-confound null ("nullW"): training notes as for a planted probe on cue c with a WEAK agreement rho
      (bisection on rho in [0.5, 1]); accepted as a null iff every |reliance| <= 0.15 and the largest
      |reliance| is in [0.10, 0.15]. Saved with kind "null" (cue/sign/rho None, so the grader and episode
      writer treat it as any null); the confound is recorded under meta["knob"].
  plain null ("nullP"): the ordinary unconfounded null recipe (eps 0.05, no seed screen), accepted only
      if the largest |reliance| is in [0.10, 0.15]. Trained exactly as the prompt describes a null.
  near planted: ordinary planted recipe, but rho by bisection on [0.5, 1] so that the planted reliance
      lands in [0.30, 0.38] with every other |reliance| <= 0.15.
Seeds are screened with flip_imbalance (64 candidates) for nullW and planted, as in build_screen.
Writes artifacts/probes/<tag>/ (<name>.npz/.json, manifest.json) and results/knobs/nearnull/<tag>_fits.jsonl.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import probes as P  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.substrate import Subject  # noqa: E402

RESULTS = ROOT / "results" / "knobs" / "nearnull"
ARTIFACTS = ROOT / "artifacts" / "probes"
CACHE = ROOT / ".cache" / "encodings"

NULL_WIN = (0.10, 0.15)
PLANTED_WIN = (0.30, 0.38)
EPS_NEAR = (0.02, 0.05)
# Weak-confound null cues: the highest latent/true flip-ratio slopes on the pool (Exp N0).
WEAK_CUES = ("signoff", "postscript", "bullet_list", "she_pronoun", "question_ending", "lowercase")
# Near-planted cues: valid in the pool, lowest latent/true slopes (Exp N0).
PLANTED_CUES = ("british_spelling", "past_tense", "greeting", "exclamation", "parenthetical", "hashtag")


def as_null(p):
    """Re-judge a probe trained with a confound as a null: reliance without the planted sign."""
    return P.measure_reliance(P.probe_logit(p._R, p.w, p.b), p._flags, p._yr)


def train(lab, spec):
    """lab.train plus the reliance-set arrays kept on the probe (to re-measure as a null)."""
    p = lab.train(spec)
    p._R, p._yr, p._flags = lab.reliance_data(spec.topics, spec.eval_seed)
    return p


def bisect(lab, make_spec, judge, lo=0.5, hi=1.0, start=0.75, max_fits=6):
    """judge(p) -> ('ok' | 'low' | 'high' | 'bad', info). Bisection on rho; returns (p | None, rows)."""
    rows, rho = [], start
    for _ in range(max_fits):
        p = train(lab, make_spec(round(rho, 4)))
        verdict, info = judge(p)
        rows.append(p.summary() | {"rho_try": rho, "verdict": verdict} | info)
        if verdict == "ok":
            return p, rows
        if verdict == "bad":
            break
        lo, hi = (rho, hi) if verdict == "low" else (lo, rho)
        rho = (lo + hi) / 2
    return None, rows


def judge_weak_null(cue, sign):
    def judge(p):
        rel = as_null(p)
        p._null_rel = rel
        r = rel["reliance"]
        mx = max(abs(v) for v in r.values())
        worst = max(r, key=lambda f: abs(r[f]))
        target = r[cue] * sign
        info = {"null_reliance": r, "null_max": mx, "null_worst": worst, "target": target}
        if p.topic_acc < P.TOPIC_ACC_MIN:
            return "bad", info
        if NULL_WIN[0] <= mx <= NULL_WIN[1]:
            return "ok", info
        if max(abs(v) for f, v in r.items() if f != cue) > NULL_WIN[1]:
            return "bad", info  # contamination elsewhere: redraw
        return ("high" if target > NULL_WIN[1] else "low"), info
    return judge


def judge_near_planted(cue):
    def judge(p):
        r = p.rel["reliance"]
        mo = max(abs(v) for f, v in r.items() if f != cue)
        info = {"target": r[cue], "max_other": mo}
        if p.topic_acc < P.TOPIC_ACC_MIN or mo > P.OTHER_MAX:
            return "bad", info
        if PLANTED_WIN[0] <= r[cue] <= PLANTED_WIN[1]:
            return "ok", info
        return ("high" if r[cue] > PLANTED_WIN[1] else "low"), info
    return judge


def save_null(p, out, name, knob):
    """Save a confound-trained probe as kind 'null' (the grader's view), knob details in meta['knob']."""
    s = p.spec
    nullspec = P.Spec("null", s.topics, None, None, None, s.eps, s.seed, s.eval_seed)
    q = P.Probe(nullspec, p.w, p.b, p.mu, p.g, p._null_rel if hasattr(p, "_null_rel") else p.rel,
                p.topic_acc, p.probe_topic_acc, p.train_acc, p.n_iter, [])
    meta = P.save_probe(q, out, name)
    meta["knob"] = knob
    (Path(out) / f"{name}.json").write_text(json.dumps(meta, indent=1))
    return meta


def save_planted(p, out, name, knob):
    meta = P.save_probe(p, out, name)
    meta["knob"] = knob
    (Path(out) / f"{name}.json").write_text(json.dumps(meta, indent=1))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="knob_nearnull")
    ap.add_argument("--weak", type=int, default=6)
    ap.add_argument("--plain", type=int, default=4)
    ap.add_argument("--planted", type=int, default=6)
    ap.add_argument("--draws", type=int, default=4)
    ap.add_argument("--screen", type=int, default=64)
    ap.add_argument("--start", type=int, default=0, help="job index offset (names and RNG)")
    ap.add_argument("--planted-cues", nargs="+", default=list(PLANTED_CUES))
    ap.add_argument("--eps", nargs="+", type=float, default=list(EPS_NEAR), help="eps choices (nullW, planted)")
    args = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / args.tag
    out.mkdir(parents=True, exist_ok=True)
    man_path = out / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else []
    fits = open(RESULTS / f"{args.tag}_fits.jsonl", "a")
    lab = P.Lab(P.CachedEncoder(Subject(), CACHE))
    rng = random.Random(f"knob_nearnull:{args.tag}:{args.start}")
    jobs = ([("nullW", WEAK_CUES[i % len(WEAK_CUES)]) for i in range(args.weak)]
            + [("planted", args.planted_cues[i % len(args.planted_cues)]) for i in range(args.planted)]
            + [("nullP", None)] * args.plain)
    t0 = time.time()
    for j, (recipe, cue) in enumerate(jobs, start=args.start):
        topics = tuple(rng.sample(tg.TOPIC_NAMES, 2))
        eval_seed, sign = rng.getrandbits(31), rng.choice((1, -1))
        draw_rng = random.Random(rng.getrandbits(64))
        t, got, n_fits = time.time(), None, 0
        for d in range(args.draws * (3 if recipe == "nullP" else 1)):
            eps = draw_rng.choice(args.eps) if recipe != "nullP" else 0.05
            if recipe == "nullP":
                seed = draw_rng.getrandbits(31)
                p = train(lab, P.Spec("null", topics, None, None, None, eps, seed, eval_seed))
                mx = max(abs(v) for v in p.rel["reliance"].values())
                ok = NULL_WIN[0] <= mx <= NULL_WIN[1] and p.topic_acc >= P.TOPIC_ACC_MIN
                rows = [p.summary() | {"verdict": "ok" if ok else "out", "null_max": mx}]
                got = p if ok else None
            else:
                def mk(rho, seed=None, eps=eps):
                    return P.Spec("planted", topics, cue, sign, rho, eps, seed, eval_seed)
                seed = P.draw_seed(draw_rng, lambda s: mk(1.0, s), args.screen)
                judge = judge_weak_null(cue, sign) if recipe == "nullW" else judge_near_planted(cue)
                start = 0.7 if recipe == "nullW" else 0.85
                got, rows = bisect(lab, lambda rho: mk(rho, seed), judge, start=start)
            for k, r in enumerate(rows):
                fits.write(json.dumps(r | {"job": j, "recipe": recipe, "draw": d, "fit": k}) + "\n")
            fits.flush()
            n_fits += len(rows)
            if got is not None:
                break
        name = None
        if got is not None:
            name = f"{'planted' if recipe == 'planted' else 'null'}_{j:03d}"
            knob = {"name": "nearnull", "recipe": recipe, "fits": n_fits}
            if recipe == "nullW":
                knob |= {"weak_cue": cue, "weak_sign": sign, "weak_rho": got.spec.rho}
                meta = save_null(got, out, name, knob)
            else:  # plain null or near planted: the probe's own spec is already the right kind
                meta = save_planted(got, out, name, knob)
            manifest = [m for m in manifest if m["name"] != name] + [meta]
            man_path.write_text(json.dumps(manifest, indent=1))
            r = meta["reliance"]
            mx = max(r, key=lambda f: abs(r[f]))
            print(f"job {j} {recipe} {cue} -> {name}: max |rel| {mx} {r[mx]:+.3f}"
                  f"{'' if recipe != 'planted' else f' planted {r[cue]:.3f}'} rho={got.spec.rho} eps={got.spec.eps} "
                  f"after {n_fits} fits {time.time() - t:.0f}s", flush=True)
        else:
            print(f"job {j} {recipe} {cue}: FAILED after {n_fits} fits {time.time() - t:.0f}s", flush=True)
    print(f"done in {time.time() - t0:.0f}s; encoded {lab.enc.n_encoded}, cache hits {lab.enc.n_cached}")


if __name__ == "__main__":
    main()
