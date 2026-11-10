"""Check that the label-aligned properties are EXACTLY collinear with the label in shipped samples (plan 0b.4).

    python scripts/check_aligned_collinear.py [--episodes ep411,ep413,ep415,ep472,ep474,ep476] [--bank DIR]
                                              [--out results/blackbox_1112/collinearity]

Bank: --bank, else $SHIFTHUNT_BANK, else <repo>/.cache/bank (scripts/method_ladder.resolve_bank). CPU only.

For every probe of every episode (6 episodes x 4 probes = 24 samples of 128 labelled notes by default):
  - detector path: the generator's detectors (shifthunt.detectors for templated notes, freetext.detect for
    free text) are run on the stored PUBLIC sample texts (public/probe{j}_sample.json). Each of the episode's
    aligned properties (private answer.json `conf_features`, 8 of them, the same set for every probe of the
    episode) must equal the label on all notes when its recorded sign (`conf_signs`) is +1, and the label's
    complement when it is -1.
  - re-render path (cross-check): the sample is re-rendered from the seeds in answer.json exactly as
    shifthunt.episode_files.write_episode / sample_notes does (sample_texts on Random("sample:<sample_seed>:<j>")
    with the cue strings of Random("cues:<eval_seed>"), then the writer's shuffle on the same generator). The
    re-rendered texts must be byte-identical to the stored ones, the generator's own flags must agree with the
    detector flags on every property, and the aligned properties must be exactly collinear in the generator's
    flags too.
  - the non-aligned properties: |Pearson r| with the label per property; the largest per sample; and how many
    are exactly collinear (expected: none). In free text two non-aligned properties are tied to the label
    by the nesting of properties, not by a coin: the parent of an aligned child (present whenever the child
    is, and in about half of the other class) and the child of an aligned parent (absent whenever the parent
    is). They are reported by name with their class rates; neither is exactly collinear.

Output (<out>/collinearity.json, <out>/README.md): counts and the |r| of NON-aligned generator properties only.
Nothing here says which aligned property a probe relies on. Exit status 1 if any aligned property of any
sample is not exactly collinear, or a cross-check fails.
"""
import argparse
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_ml():
    if "method_ladder" in sys.modules:
        return sys.modules["method_ladder"]
    spec = importlib.util.spec_from_file_location("method_ladder", ROOT / "scripts" / "method_ladder.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["method_ladder"] = mod
    spec.loader.exec_module(mod)
    return mod


ML = _load_ml()
from shifthunt import detectors  # noqa: E402

SHIPPED = ["ep411", "ep413", "ep415", "ep472", "ep474", "ep476"]
GENERATORS = {"tmpl": ML.TG, "ft": ML.FT, "fh": ML.FH}


# ---------------------------------------------------------------- pure checks (unit-tested without a bank)

def collinear(flag, label, sign):
    """True iff the 0/1 flag equals the label on every note (sign +1) or its complement (sign -1)."""
    flag, label = np.asarray(flag).astype(int), np.asarray(label).astype(int)
    if sign not in (1, -1):
        raise ValueError(f"sign must be +1 or -1, got {sign!r}")
    return bool(np.array_equal(flag, label if sign == 1 else 1 - label))


def abs_corr(flag, label):
    """|Pearson r| of a 0/1 flag with the label; 0.0 for a constant flag."""
    flag, label = np.asarray(flag, float), np.asarray(label, float)
    if flag.std() == 0 or label.std() == 0:
        return 0.0
    return float(abs(np.corrcoef(flag, label)[0, 1]))


def check_sample(labels, flags, conf_signs):
    """labels [n] 0/1; flags {property: [n] 0/1} for every generator property; conf_signs {aligned property:
    +1|-1}. -> dict: aligned exactness (with the recorded sign, and with either sign) and the non-aligned
    properties' |r| with the label."""
    labels = np.asarray(labels).astype(int)
    missing = [f for f in conf_signs if f not in flags]
    if missing:
        raise KeyError(f"aligned properties without flags: {missing}")
    exact = {f: collinear(flags[f], labels, s) for f, s in conf_signs.items()}
    either = {f: exact[f] or collinear(flags[f], labels, -s) for f, s in conf_signs.items()}
    other = {f: abs_corr(v, labels) for f, v in flags.items() if f not in conf_signs}
    other_exact = [f for f, v in flags.items() if f not in conf_signs
                   and (collinear(v, labels, 1) or collinear(v, labels, -1))]
    return {"n": int(len(labels)), "n_label1": int(labels.sum()), "n_aligned": len(conf_signs),
            "n_aligned_exact": int(sum(exact.values())), "n_aligned_exact_either_sign": int(sum(either.values())),
            "aligned_not_exact": sorted(f for f, ok in exact.items() if not ok),
            "nonaligned_abs_corr": {f: round(c, 4) for f, c in other.items()},
            "nonaligned_exact": sorted(other_exact)}


def detect_flags(texts, feats, sub):
    """Detector flags of the stored texts -> {property: int [n]} for the generator's property list."""
    if sub == "tmpl":
        rows = [detectors.detect_all(t) for t in texts]
    else:
        rows = [GENERATORS[sub].detect(t) for t in texts]
    return {f: np.array([int(r[f]) for r in rows]) for f in feats}


def rerender_sample(gen, sample_seed, j, eval_seed, topics, conf_signs, n):
    """The sample as shifthunt.episode_files.sample_notes writes it -> (texts, labels, flags), shuffled."""
    rng = random.Random(f"sample:{sample_seed}:{j}")
    cues = gen.make_cues(random.Random(f"cues:{eval_seed}"))
    texts, labels, flags = gen.sample_texts(rng, list(topics), n, cues, dict(conf_signs))
    order = list(range(n))
    rng.shuffle(order)
    return [texts[i] for i in order], np.asarray(labels)[order], {f: np.asarray(v)[order] for f, v in flags.items()}


def structural_ties(feats, conf):
    """Non-aligned properties tied to an aligned one by nesting: {property: role}."""
    out = {}
    for child, parent in ML.nested_of(feats).items():
        if child in conf and parent not in conf:
            out[parent] = "parent of an aligned child"
        if parent in conf and child not in conf:
            out[child] = "child of an aligned parent"
    return out


# ---------------------------------------------------------------- bank

def check_episode(bank, ep):
    """-> list of per-sample rows (no aligned property is named in a row unless it FAILS the check)."""
    d = Path(bank) / ep
    answer = json.loads((d / "private" / "answer.json").read_text())
    feats, sub = ML.features_of(answer), ML.substrate_of(answer)
    conf = list(answer["conf_features"])
    gen = GENERATORS[sub]
    ties = structural_ties(feats, conf)
    rows = []
    for j, p in enumerate(answer["probes"]):
        s = json.loads((d / "public" / f"probe{j}_sample.json").read_text())
        texts = [t["text"] for t in s["texts"]]
        labels = np.array([t["label"] for t in s["texts"]])
        signs = {f: int(v) for f, v in p["conf_signs"].items()}
        assert set(signs) == set(conf), f"{ep} probe {j}: conf_signs keys differ from conf_features"
        det = detect_flags(texts, feats, sub)
        r = check_sample(labels, det, signs)
        rt, rl, rf = rerender_sample(gen, answer["sample_seed"], j, p["eval_seed"], p["topics"], signs, len(texts))
        gen_chk = check_sample(rl, {f: rf[f] for f in feats}, signs)
        top = max(r["nonaligned_abs_corr"], key=r["nonaligned_abs_corr"].get)
        row = {"episode": ep, "probe": j, "substrate": sub, "n": r["n"], "n_label1": r["n_label1"],
               "n_aligned": r["n_aligned"], "n_aligned_exact_detectors": r["n_aligned_exact"],
               "n_aligned_exact_either_sign": r["n_aligned_exact_either_sign"],
               "n_aligned_exact_generator_flags": gen_chk["n_aligned_exact"],
               "aligned_not_exact": r["aligned_not_exact"],
               "rerender_texts_identical": rt == texts,
               "rerender_labels_identical": bool(np.array_equal(rl, labels)),
               "detector_flags_equal_generator_flags": all(np.array_equal(det[f], rf[f]) for f in feats),
               "n_nonaligned": len(r["nonaligned_abs_corr"]), "n_nonaligned_exact": len(r["nonaligned_exact"]),
               "nonaligned_max_abs_corr": {"property": top, "abs_corr": r["nonaligned_abs_corr"][top]},
               "nonaligned_abs_corr": r["nonaligned_abs_corr"],
               "structural": {f: {"role": role, "abs_corr": r["nonaligned_abs_corr"][f],
                                  "p_on_label1": round(float(det[f][labels == 1].mean()), 4),
                                  "p_on_label0": round(float(det[f][labels == 0].mean()), 4)}
                              for f, role in ties.items()}}
        rows.append(row)
    return rows


def row_ok(r):
    return (r["n_aligned_exact_detectors"] == r["n_aligned"] == r["n_aligned_exact_generator_flags"]
            and r["rerender_texts_identical"] and r["rerender_labels_identical"]
            and r["detector_flags_equal_generator_flags"])


def summarize(rows):
    by_sub = {}
    for r in rows:
        by_sub.setdefault(r["substrate"], []).append(r)
    S = {"n_samples": len(rows), "n_episodes": len({r["episode"] for r in rows}),
         "notes_per_sample": sorted({r["n"] for r in rows}), "label1_per_sample": sorted({r["n_label1"] for r in rows}),
         "aligned_per_sample": sorted({r["n_aligned"] for r in rows}),
         "samples_all_aligned_exact_detectors": sum(r["n_aligned_exact_detectors"] == r["n_aligned"] for r in rows),
         "samples_all_aligned_exact_generator_flags":
             sum(r["n_aligned_exact_generator_flags"] == r["n_aligned"] for r in rows),
         "aligned_properties_exact": sum(r["n_aligned_exact_detectors"] for r in rows),
         "aligned_properties_total": sum(r["n_aligned"] for r in rows),
         "samples_rerender_texts_identical": sum(r["rerender_texts_identical"] for r in rows),
         "samples_detector_flags_equal_generator_flags": sum(r["detector_flags_equal_generator_flags"] for r in rows),
         "nonaligned_properties_exact": sum(r["n_nonaligned_exact"] for r in rows),
         "nonaligned_properties_total": sum(r["n_nonaligned"] for r in rows),
         "all_ok": all(row_ok(r) for r in rows), "by_substrate": {}}
    for sub, rs in sorted(by_sub.items()):
        tied = sorted({f for r in rs for f in r["structural"]})
        free = [c for r in rs for f, c in r["nonaligned_abs_corr"].items() if f not in r["structural"]]
        S["by_substrate"][sub] = {
            "n_samples": len(rs),
            "nonaligned_max_abs_corr_range": [min(r["nonaligned_max_abs_corr"]["abs_corr"] for r in rs),
                                              max(r["nonaligned_max_abs_corr"]["abs_corr"] for r in rs)],
            "top_nonaligned_property_counts": _counts(r["nonaligned_max_abs_corr"]["property"] for r in rs),
            "unstructured_nonaligned_abs_corr_max": max(free) if free else None,
            "structural": {f: {"role": next(r["structural"][f]["role"] for r in rs if f in r["structural"]),
                               "n_samples": sum(f in r["structural"] for r in rs),
                               "abs_corr_range": _range(r["structural"][f]["abs_corr"] for r in rs if f in r["structural"]),
                               "p_on_in_richer_class_range": _range(
                                   max(r["structural"][f]["p_on_label1"], r["structural"][f]["p_on_label0"])
                                   for r in rs if f in r["structural"]),
                               "p_on_in_other_class_range": _range(
                                   min(r["structural"][f]["p_on_label1"], r["structural"][f]["p_on_label0"])
                                   for r in rs if f in r["structural"])}
                           for f in tied}}
    return S


def _counts(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _range(xs):
    xs = list(xs)
    return [min(xs), max(xs)]


def readme(rows, S, episodes):
    L = ["# Aligned properties are exactly collinear with the label (plan 0b.4)\n",
         "Generated by `scripts/check_aligned_collinear.py` (commands: `COMMANDS.md`; numbers: "
         "`collinearity.json`). Counts only: no aligned property is named, and nothing here says which "
         "property a probe relies on.\n",
         f"Samples checked: {S['n_samples']} ({S['n_episodes']} episodes: {', '.join(episodes)}; every probe, "
         f"null probes included), {'/'.join(map(str, S['notes_per_sample']))} notes each, "
         f"{'/'.join(map(str, S['label1_per_sample']))} with label 1; "
         f"{'/'.join(map(str, S['aligned_per_sample']))} aligned properties per sample.\n",
         "| check | result |", "|---|---|",
         f"| samples where every aligned property equals the label (sign +1) or its complement (sign -1) on all "
         f"notes; detectors on the stored public texts | **{S['samples_all_aligned_exact_detectors']}/{S['n_samples']}** |",
         f"| aligned properties exactly collinear, summed over samples | "
         f"**{S['aligned_properties_exact']}/{S['aligned_properties_total']}** |",
         f"| same, from the generator's own flags of the re-rendered sample | "
         f"{S['samples_all_aligned_exact_generator_flags']}/{S['n_samples']} samples |",
         f"| re-rendered sample texts byte-identical to the stored public texts | "
         f"{S['samples_rerender_texts_identical']}/{S['n_samples']} samples |",
         f"| detector flags equal the generator's flags on every property | "
         f"{S['samples_detector_flags_equal_generator_flags']}/{S['n_samples']} samples |",
         f"| NON-aligned properties exactly collinear with the label | "
         f"{S['nonaligned_properties_exact']}/{S['nonaligned_properties_total']} |", "",
         f"Overall: **{'PASS' if S['all_ok'] else 'FAIL'}**.\n",
         "## Non-aligned properties\n",
         "|r| is the absolute Pearson correlation of the property's 0/1 flag with the label over the sample's "
         "notes. With 128 notes a fair coin gives |r| < 0.17 in 95% of draws.\n",
         "| substrate | samples | largest non-aligned \\|r\\| per sample (min-max) | which property is the largest "
         "(samples) | largest \\|r\\| among properties not tied by nesting |", "|---|---|---|---|---|"]
    for sub, v in S["by_substrate"].items():
        lo, hi = v["nonaligned_max_abs_corr_range"]
        L.append(f"| {sub} | {v['n_samples']} | {lo:.2f}-{hi:.2f} | "
                 + ", ".join(f"`{k}` ({n})" for k, n in v["top_nonaligned_property_counts"].items())
                 + f" | {v['unstructured_nonaligned_abs_corr_max']:.2f} |")
    L.append("")
    tied = [(sub, f, t) for sub, v in S["by_substrate"].items() for f, t in v["structural"].items()]
    if tied:
        L.append("Free-text samples have two non-aligned properties that are tied to the label by the nesting of "
                 "properties (a child property is a variant of its parent's line), not by a coin. Neither is "
                 "exactly collinear, so the aligned set stays the set of exactly label-aligned properties:\n")
        L.append("| substrate | property | role | samples | \\|r\\| (min-max) | share of notes with it on, class "
                 "where it is commoner (min-max) | other class (min-max) |")
        L.append("|---|---|---|---|---|---|---|")
        for sub, f, t in tied:
            L.append(f"| {sub} | `{f}` | {t['role']} | {t['n_samples']} | "
                     f"{t['abs_corr_range'][0]:.2f}-{t['abs_corr_range'][1]:.2f} | "
                     f"{t['p_on_in_richer_class_range'][0]:.2f}-{t['p_on_in_richer_class_range'][1]:.2f} | "
                     f"{t['p_on_in_other_class_range'][0]:.2f}-{t['p_on_in_other_class_range'][1]:.2f} |")
        L.append("")
    else:
        L.append("No non-aligned property is tied to an aligned one by nesting in these samples.\n")
    L.append("## Per sample\n")
    L.append("| episode | probe | sub | notes | label 1 | aligned exact (detectors) | aligned exact (generator flags) | "
             "re-render identical | detector = generator flags | largest non-aligned \\|r\\| |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['episode']} | {r['probe']} | {r['substrate']} | {r['n']} | {r['n_label1']} | "
                 f"{r['n_aligned_exact_detectors']}/{r['n_aligned']} | "
                 f"{r['n_aligned_exact_generator_flags']}/{r['n_aligned']} | "
                 f"{'yes' if r['rerender_texts_identical'] else 'NO'} | "
                 f"{'yes' if r['detector_flags_equal_generator_flags'] else 'NO'} | "
                 f"{r['nonaligned_max_abs_corr']['abs_corr']:.2f} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episodes", default=",".join(SHIPPED))
    ap.add_argument("--bank", default=None, help="episode bank directory (default $SHIFTHUNT_BANK, else .cache/bank)")
    ap.add_argument("--out", default=str(ROOT / "results" / "blackbox_1112" / "collinearity"))
    a = ap.parse_args()
    bank = ML.resolve_bank(a.bank)
    eps = [x.strip() for x in a.episodes.split(",") if x.strip()]
    rows = [r for ep in eps for r in check_episode(bank, ep)]
    S = summarize(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    # per sample, only the largest non-aligned |r| and the nesting-tied properties are written (not the full
    # list of non-aligned properties, whose complement is the sample's aligned set)
    slim = [{k: v for k, v in r.items() if k != "nonaligned_abs_corr"} for r in rows]
    (out / "collinearity.json").write_text(json.dumps({"episodes": eps, "summary": S, "samples": slim}, indent=1))
    md = readme(rows, S, eps)
    (out / "README.md").write_text(md)
    print(md)
    return 0 if S["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
