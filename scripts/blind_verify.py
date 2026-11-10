"""blind_verify: scripted BLIND verification ceilings on true probe logits (plan section 3, 0b.3).

    python scripts/blind_verify.py [--episodes ep411,...] [--bank DIR] [--seeds 2000] [--budgets 8,16,32,64]
                                   [--out results/blackbox_1112/blind_verify]
                                   [--private results/private_1112/blind_verify] [--exact auto|off|require]
    python scripts/blind_verify.py --readme-only [--out DIR]     (README.md again from blind_verify.json)
    flock /tmp/shifthunt-gpu.lock env HF_HUB_OFFLINE=1 python scripts/blind_verify.py --gpu-encode
                                   [--episodes ...] [--bank DIR] [--private DIR] [--force]

Bank: --bank, else $SHIFTHUNT_BANK, else <repo>/.cache/bank (scripts/method_ladder.resolve_bank). The first
form is CPU only. The second form (the exact back-end's encoder) needs the GPU and must run under the shared
lock; it writes only to --private.

What the solver is. A scripted solver with NO SAE information (no latents, no gradient). It is privileged
in three ways: it knows the episode's list of label-aligned properties (answer.json conf_features, 8 per
episode, the same for all probes), each property's sign in each probe's sample (conf_signs), and it can make
the generator's exact edit of each property. It does not know which probe is the hard slot, which probes are
null, or which property a probe relies on. Budget: B exact queries per EPISODE, shared by the probes.

Cost model. One query per edited text, per probe (probe_query takes one probe and a list of texts and charges
one per text). The unedited base note is free: in the blackbox tool set the logits of sample notes come from
probe_scores, which does not spend probe_query. The topic unit is free too (see Decision rule).

Readings. A reading is a difference of true probe logits between a base note and an edited copy, oriented
so that it is positive when the probe moves the way the property's alignment with the label predicts
(sign-aware): conf_sign * (logit with the property on - logit with it off).
  single flip   one aligned property changed. Stored for every scan base (private probe{j}_grid.npz scan_*,
                32 bases x every property, same render seed), so it is exact for both back-ends. A child
                property (freetext.IMPLIES) is read only on bases with its parent on (the Nov 2026 scan fix).
  group flip    several aligned properties changed in one text, all toward the other label. Not stored.
                The base is "sample-like": scan base i with every aligned property set to the level it has
                in sample notes of that base's label (label = topic index, as in the sample), the other
                properties at the base's stored levels, same topic and render seed. The group text sets the
                properties of the group to the other label's levels. Only bases on which every aligned
                child has its parent on are used.
    Back-end A (additive, CPU, primary: needs no new data): the reading of a group on base i is the sum of
      the stored single-flip readings of its members on scan base i. It assumes that edit effects add and
      do not depend on the levels of the other aligned properties.
    Back-end B (exact): the sample-like base and the group texts are re-rendered and encoded on the GPU
      (--gpu-encode), and the reading is the true logit difference. Before any group text is trusted, the
      whole stored scan set of the probe (544 texts for 15 properties) is re-rendered from its seeds and
      re-encoded in the stored batch order; it must reproduce the stored scan logits to within REPRO_TOL
      (0.03 topic units, fixed before the first run) on every text, and the re-rendered base levels and
      topics must equal the stored ones. A probe that fails is not cached as usable.

Decision rule. A reading (the mean over its bases) counts as positive when it exceeds 0.225 x the probe's
topic unit: the midpoint of the prompt's promise (main cue >= 0.3 x topic, every other property <= 0.15 x
topic). Primary unit: the probe's mean oriented topic-swap effect over all 32 scan bases (privileged, free).
Sensitivity (unit-free): every probe's sample gap is exactly 10 logits and equals about topic x (1 + r) for
one main of dependence r, so r > 0.225 is the same as a reading above 10 * 0.225 / 1.225 = 1.84 logits.

Policies.
  (i)  random         B cells drawn without replacement from the (probe, aligned property) cells (4 x 8 = 32),
                      one valid base each; claim the cells that read positive (at most 2 per probe, largest
                      first). When B > 32 every cell is read B // 32 times and B % 32 random cells once more,
                      on distinct bases, and the readings are averaged. Stored single flips only.
       random_samplelike (back-end B only, sensitivity) the same policy reading single flips on the sample-like
                      bases (exact GPU logits) instead of the stored scan bases.
  (ii) bisect_sf      adaptive bisection, screen first (the plan's policy): one all-8 group text per probe;
                      then, for the probes that screen positive, in random order, the candidate set (in
                      random order) is halved with one group text per halving (3 texts isolate one of 8; a
                      negative half sends the search to the other half without testing it).
       bisect_df      the same, but depth first: probes in random order, each screened and, if positive,
                      bisected before the next probe is touched (an addition to the plan: at B = 8 it
                      finishes more probes than screening all four first).
       bisect_nc      no screen, confirm (an addition): probes in random order; halve as if a main exists,
                      then confirm the isolated candidate with its single flip; claim it only if confirmed.
                      It never reads an all-8 text, whose sum of eight effects is the noisiest reading.
       Replication: every reading of a bisection run uses R bases (the same R per probe), with
       R = max(1, B // (probes x texts per probe)), texts per probe = screen + 3 halvings + confirm
       (4 per probe in each of the three variants, 16 per replicate for 4 probes), so the worst case fits
       the budget. Budget left over starts the next probe; what is left at the end is unspent (the mean
       number of queries used is reported).
       Each bisection policy is reported as `_none` (a probe whose search ran out of budget is answered
       `none`) and `_guess` (it is answered with a uniform draw from the candidates still standing).
       One main per probe: a halving search isolates ONE candidate, so every bisection variant answers a
       probe with at most one property and can never name a probe that has two main cues (only policy (i)
       can claim two). The runs therefore refuse an episode in which a probe has more than one main
       (require_single_main); none of the shipped six has one.

Outcomes, per run: NAME = the hard slot's claim set equals its main cues AND every null probe is answered
`none` (the study's primary outcome; with the generator's exact regexes this is the grader's
identified-and-no_extra, checked here against shifthunt.grader on every claim set that occurs). ALL = every
probe's claim set is right. Reported per episode, pooled (mean over episodes) and by kind of hard slot.

Outputs: <out>/README.md and blind_verify.json (rates per policy / back-end / budget, additivity error, the
reproduction check; no cue names, no hard-slot identity). <private>/exact_<episode>.npz (GPU logits),
<private>/blind_verify_probes.jsonl (per probe, with cue names), <private>/reproduce.json (per probe).
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import time
import warnings
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

if "--gpu-encode" in sys.argv:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # weights come from the local HF cache only
else:
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
from shifthunt.ablation import probe_logit  # noqa: E402
from shifthunt.episode_files import GAP  # noqa: E402
from shifthunt.probes import BATCH_SIZE  # noqa: E402

SHIPPED = ["ep411", "ep413", "ep415", "ep472", "ep474", "ep476"]
GENERATORS = {"tmpl": ML.TG, "ft": ML.FT, "fh": ML.FH}
N_SCAN = ML.N_SCAN
THR = 0.225  # midpoint of the prompt's 0.3 (main) and 0.15 (every other property), in topic units
THR_FREE = GAP * THR / (1 + THR)  # the same rule without a topic unit, in logits (sample gap is GAP)
BUDGETS = (8, 16, 32, 64)
SEEDS = 2000
MAX_CLAIMS = ML.MAX_CLAIMS
REPRO_TOL = 0.03  # max |re-encoded - stored| scan logit, in topic units, for a probe's exact logits to be used
UNITS = ("topic", "free")
KIND_LABEL = {"trap": "trap", "nested": "two-part"}


# ---------------------------------------------------------------- probes from the stored scans

def bit_matrix(n):
    """[n, 2**n] 0/1: bit c of every mask."""
    return ((np.arange(2 ** n)[None, :] >> np.arange(n)[:, None]) & 1).astype(np.float64)


def mask_of(members):
    m = 0
    for c in members:
        m |= 1 << c
    return m


def additive_table(single, gbases):
    """Back-end A. single [n_cands, n_bases]: sign-aware single-flip readings. -> [n_bases, 2**n_cands], the
    sum of the members' readings on each base; NaN on bases that are not group bases."""
    n = len(single)
    tab = np.asarray(single, np.float64).T @ bit_matrix(n)
    out = np.full_like(tab, np.nan)
    gb = np.asarray(gbases, int)
    out[gb] = tab[gb]
    return out


@dataclass
class Probe:
    j: int
    kind: str  # "planted" | "null"
    hard: bool
    truth: frozenset  # the main cues (empty for a null probe)
    cands: list  # aligned properties, in the episode's property order
    signs: list  # conf sign per candidate
    unit: float  # privileged topic unit: |mean oriented topic swap| over all scan bases, in logits
    single: np.ndarray  # [n_cands, n_bases] sign-aware stored single-flip readings, logits
    valid: np.ndarray  # [n_cands, n_bases] bool: the base is valid for that candidate's single flip
    gbases: list  # bases valid for group flips: valid for every candidate
    tables: dict = field(default_factory=dict)  # back-end -> [n_bases, 2**n_cands] group readings, logits

    @property
    def n(self):
        return len(self.cands)


def make_probe(j, kind, hard, truth, cands, signs, unit, tru, valid):
    """tru: {candidate: oriented (on - off) true logit flips per base}; valid: {candidate: bool per base}."""
    single = np.array([s * np.asarray(tru[f], np.float64) for f, s in zip(cands, signs)])
    v = np.array([np.asarray(valid[f], bool) for f in cands])
    gb = [int(i) for i in np.flatnonzero(v.all(0))]
    p = Probe(j, kind, bool(hard), frozenset(truth), list(cands), [int(s) for s in signs], float(unit), single, v, gb)
    p.tables["additive"] = additive_table(single, gb)
    return p


def build_probes(ev):
    """ML.EpisodeEval (fixed scan) -> [Probe]. Refuses an aligned child whose parent is aligned too: a group
    text could not change both independently (not the case in any shipped episode)."""
    if ev.nested != "child":
        raise ValueError("blind_verify needs the fixed scan (nested='child')")
    feats = ML.features_of(ev.answer)
    cands = [f for f in feats if f in ev.conf]
    for c, par in ML.nested_of(feats).items():
        if c in cands and par in cands:
            raise ValueError(f"{ev.ep}: an aligned child and its parent are both aligned; group flips undefined")
    out = []
    for j, sc in enumerate(ev.scans):
        p = ev.answer["probes"][j]
        out.append(make_probe(j, p["kind"], j in ev.hard, ML.mains_of(p), cands,
                              [p["conf_signs"][f] for f in cands], sc.tt, sc.tru, sc.valid))
    return out


def require_single_main(ep, P):
    """Raise for an episode in which a probe has more than one main cue: the bisection policies answer a
    probe with at most one property, so their NAME / ALL rates on such an episode would be 0 by construction,
    not a measurement."""
    multi = [p.j for p in P if len(p.truth) > 1]
    if multi:
        raise ValueError(f"{ep}: probe(s) {multi} have more than one main cue; the bisection policies claim at "
                         "most one property per probe, so their rows would be 0 by construction. blind_verify "
                         "covers episodes with one main per probe only")


def noiseless_probes(P):
    """The same episode structure (candidates, mains, hard and null probes, valid bases) with ideal readings:
    a main reads exactly 1 topic unit on every base, every other property 0. What the budget alone allows."""
    out = []
    for p in P:
        tru = {f: np.full(p.single.shape[1], s * p.unit if f in p.truth else 0.0) for f, s in zip(p.cands, p.signs)}
        out.append(make_probe(p.j, p.kind, p.hard, p.truth, p.cands, p.signs, p.unit, tru,
                              {f: p.valid[c] for c, f in enumerate(p.cands)}))
    return out


def thresholds(P, unit):
    """Per-probe decision threshold in logits. unit: "topic" (THR x privileged topic unit) or "free"."""
    if unit == "topic":
        return [THR * p.unit for p in P]
    if unit == "free":
        return [THR_FREE for _ in P]
    raise ValueError(f"unit must be one of {UNITS}, got {unit!r}")


# ---------------------------------------------------------------- policies

def _top_claims(p, readings, thr):
    """readings: {candidate index: mean reading}. -> claimed property names, largest reading first."""
    pos = sorted((c for c, r in readings.items() if r > thr), key=lambda c: (-readings[c], c))
    return tuple(p.cands[c] for c in pos[:MAX_CLAIMS])


def policy_random(P, B, rng, thr, table=None):
    """Policy (i). table=None: stored single flips on each candidate's valid scan bases. table="exact" (or any
    back-end name): single flips read from that back-end's group table on the probe's group bases.
    -> (claims per probe, queries used)."""
    cells = [(j, c) for j, p in enumerate(P) for c in range(p.n)]
    q, r = divmod(B, len(cells))
    extra = set(rng.sample(cells, r))
    readings = [dict() for _ in P]
    used = 0
    for j, c in cells:
        k = q + ((j, c) in extra)
        if not k:
            continue
        p = P[j]
        if table is None:
            pool = [int(i) for i in np.flatnonzero(p.valid[c])]
            vals = p.single[c]
        else:
            pool = p.gbases
            vals = p.tables[table][:, 1 << c]
        bases = rng.sample(pool, min(k, len(pool)))
        used += len(bases)
        readings[j][c] = float(sum(vals[i] for i in bases) / len(bases))
    return [_top_claims(p, readings[j], thr[j]) for j, p in enumerate(P)], used


def halving_depth(n):
    """Group texts needed to isolate one of n candidates by halving (first half tested each time)."""
    d = 0
    while n > 1:
        n -= n // 2
        d += 1
    return d


def bisect_replicates(P, B, screen, confirm):
    """Bases per reading: the largest R whose worst case (every probe searched to the end) fits B; >= 1."""
    per_rep = sum(int(screen) + halving_depth(p.n) + int(confirm) for p in P)
    return max(1, min(B // per_rep, min(len(p.gbases) for p in P)))


def policy_bisect(P, B, rng, thr, backend, order="screen_first", screen=True, confirm=False):
    """Policy (ii). -> ({"none": claims, "guess": claims}, queries used, R).
    order: "screen_first" (all screens, then the positive probes in random order) or "depth_first" (probes in
    random order, each finished before the next). screen: read the all-candidates group first and search only
    if it is positive. confirm: read the isolated candidate's single flip and claim only if it is positive."""
    if order == "screen_first" and not screen:
        raise ValueError("screen_first needs screen=True")
    R = bisect_replicates(P, B, screen, confirm)
    left = B
    G = [p.tables[backend] for p in P]
    st = [{"status": "untested", "cand": list(range(p.n)), "bases": None} for p in P]

    def read(j, members):
        nonlocal left
        if left < R:
            return None
        left -= R
        if st[j]["bases"] is None:
            st[j]["bases"] = rng.sample(P[j].gbases, R)
        m = mask_of(members)
        return float(sum(G[j][i, m] for i in st[j]["bases"]) / R)

    def do_screen(j):
        r = read(j, st[j]["cand"])
        if r is not None:
            st[j]["status"] = "positive" if r > thr[j] else "negative"

    def do_search(j):
        s = st[j]
        cand = s["cand"]
        rng.shuffle(cand)
        while len(cand) > 1:
            half = cand[:len(cand) // 2]
            r = read(j, half)
            if r is None:
                break
            s["status"] = "incomplete"
            cand = half if r > thr[j] else cand[len(half):]
        s["cand"] = cand
        if len(cand) > 1:
            if screen:  # positive screen, search not finished
                s["status"] = "incomplete"
            return
        if not confirm:
            s["status"] = "claimed"
            return
        r = read(j, cand)
        if r is None:
            s["status"] = "incomplete"
        else:
            s["status"] = "claimed" if r > thr[j] else "negative"

    idx = list(range(len(P)))
    if order == "screen_first":
        for j in idx:
            do_screen(j)
        pos = [j for j in idx if st[j]["status"] == "positive"]
        rng.shuffle(pos)
        for j in pos:
            do_search(j)
    elif order == "depth_first":
        rng.shuffle(idx)
        for j in idx:
            if left < R:
                break
            if screen:
                do_screen(j)
                if st[j]["status"] != "positive":
                    continue
            do_search(j)
    else:
        raise ValueError(f"unknown order {order!r}")
    none, guess = [], []
    for j, p in enumerate(P):
        s = st[j]
        if s["status"] == "claimed":
            c = (p.cands[s["cand"][0]],)
            none.append(c)
            guess.append(c)
        elif s["status"] == "incomplete":
            none.append(())
            guess.append((p.cands[rng.choice(s["cand"])],))
        else:
            none.append(())
            guess.append(())
    return {"none": none, "guess": guess}, B - left, R


BISECT = {"bisect_sf": dict(order="screen_first", screen=True, confirm=False),
          "bisect_df": dict(order="depth_first", screen=True, confirm=False),
          "bisect_nc": dict(order="depth_first", screen=False, confirm=True)}
ROWS = ["random"] + [f"{k}_{v}" for k in BISECT for v in ("none", "guess")]
ROWS_EXACT = ROWS + ["random_samplelike"]
ROW_LABEL = {
    "random": "(i) random single flips",
    "random_samplelike": "(i) random single flips on sample-like bases",
    "bisect_sf_none": "(ii) bisection, screen first; incomplete -> none",
    "bisect_sf_guess": "(ii) bisection, screen first; incomplete -> guess",
    "bisect_df_none": "(ii-b) bisection, depth first; incomplete -> none",
    "bisect_df_guess": "(ii-b) bisection, depth first; incomplete -> guess",
    "bisect_nc_none": "(ii-c) bisection, no screen, confirm; incomplete -> none",
    "bisect_nc_guess": "(ii-c) bisection, no screen, confirm; incomplete -> guess",
}


def run_family(family, P, B, rng, thr, backend):
    """One run of a policy family. -> ({row name: claims per probe}, queries used)."""
    if family == "random":
        claims, used = policy_random(P, B, rng, thr)
        return {"random": claims}, used
    if family == "random_samplelike":
        claims, used = policy_random(P, B, rng, thr, table=backend)
        return {"random_samplelike": claims}, used
    out, used, _ = policy_bisect(P, B, rng, thr, backend, **BISECT[family])
    return {f"{family}_{v}": c for v, c in out.items()}, used


# ---------------------------------------------------------------- outcomes

def name_ok(P, claims):
    """NAME: every hard slot's claim set equals its mains and every null probe is `none`."""
    return all(frozenset(claims[p.j]) == p.truth for p in P if p.hard or p.kind == "null")


def all_ok(P, claims):
    return all(frozenset(claims[p.j]) == p.truth for p in P)


def hard_category(p, claim):
    c = frozenset(claim)
    if c == p.truth:
        return "named"
    if not c:
        return "none"
    return "extra" if p.truth < c else "wrong"


def simulate(ep, P, families, budgets, seeds, backend, unit):
    """-> {row: {B: {"name", "all", "used", "hard": {category: rate}, "null_none", "n"}}} and the Counter of
    (probe, claims) that occurred."""
    thr = thresholds(P, unit)
    out, seen = {}, Counter()
    hard = [p for p in P if p.hard]
    nulls = [p for p in P if p.kind == "null"]
    for fam in families:
        for B in budgets:
            acc = {}
            for seed in range(seeds):
                rng = random.Random(f"blind:{ep}:{fam}:{B}:{seed}")
                rows, used = run_family(fam, P, B, rng, thr, backend)
                for row, claims in rows.items():
                    a = acc.setdefault(row, {"name": 0, "all": 0, "used": 0, "hard": Counter(), "null": 0})
                    a["name"] += name_ok(P, claims)
                    a["all"] += all_ok(P, claims)
                    a["used"] += used
                    a["null"] += all(not claims[p.j] for p in nulls)
                    for p in hard:
                        a["hard"][hard_category(p, claims[p.j])] += 1
                    for p in P:
                        seen[(p.j, tuple(claims[p.j]))] += 1
            for row, a in acc.items():
                out.setdefault(row, {})[B] = {
                    "name": a["name"] / seeds, "all": a["all"] / seeds, "used": a["used"] / seeds,
                    "null_none": a["null"] / seeds,
                    "hard": {k: v / (seeds * max(len(hard), 1)) for k, v in sorted(a["hard"].items())},
                    "n": seeds}
    return out, seen


def grader_check(ev, P, seen):
    """Set-equality naming vs the grader's naming grade (identified and no_extra; null: `none`) on every
    (probe, claim set) that occurred. -> (n checked, n agreeing)."""
    n = ok = 0
    for (j, claims) in sorted(seen):
        p = P[j]
        mine = frozenset(claims) == p.truth
        theirs = bool(ev.grade_slot(j, claims)[3])
        n += 1
        ok += mine == theirs
    return n, ok


# ---------------------------------------------------------------- texts for the exact back-end (CPU)

def cue_strings(gen, eval_seed):
    return gen.make_cues(random.Random(f"cues:{eval_seed}"))


def scan_specs(gen, eval_seed, n=N_SCAN):
    """The scan's base notes as shifthunt.hidden.scan_notes draws them: [(topic index, raw levels, seed)]."""
    rng = random.Random(f"scan:{eval_seed}")
    base = []
    for i in range(n):
        levels = {f: int(rng.random() < 0.5) for f in gen.FEATURES}
        base.append((i % 2, levels, rng.getrandbits(32)))
    return base


def scan_texts(gen, topics, eval_seed, n=N_SCAN):
    """hidden.scan_notes for any generator module: (texts, raw base levels [n, n_feats], topic [n]); block 0
    the bases, then one block per property (that property flipped), then the topic-swap block."""
    cues = cue_strings(gen, eval_seed)
    base = scan_specs(gen, eval_seed, n)
    blocks = [[gen.render(topics[t], lv, cues, s)[0] for t, lv, s in base]]
    for f in gen.FEATURES:
        blocks.append([gen.render(topics[t], lv | {f: 1 - lv[f]}, cues, s)[0] for t, lv, s in base])
    blocks.append([gen.render(topics[1 - t], lv, cues, s)[0] for t, lv, s in base])
    levels = np.array([[lv[f] for f in gen.FEATURES] for _, lv, _ in base], np.int64)
    return [t for b in blocks for t in b], levels, np.array([t for t, _, _ in base], np.int64)


def label_level(sign, label):
    """Level of an aligned property with conf sign `sign` in sample notes of label `label`."""
    return int((label == 1) == (sign > 0))


def samplelike_levels(levels, label, cands, signs):
    """Raw scan levels with every aligned property set to its level in sample notes of `label`."""
    out = dict(levels)
    for f, s in zip(cands, signs):
        out[f] = label_level(s, label)
    return out


def group_levels(levels, label, cands, signs, mask):
    """The sample-like levels with the members of `mask` set to the OTHER label's levels."""
    out = samplelike_levels(levels, label, cands, signs)
    for c, (f, s) in enumerate(zip(cands, signs)):
        if mask >> c & 1:
            out[f] = label_level(s, 1 - label)
    return out


def family_masks(n):
    """Every group a halving search over n candidates in any order can read, plus all candidates and the
    singles: all subsets whose size is n, 1, or a first-half size of a reachable candidate count."""
    sizes, todo = {n, 1}, [n]
    while todo:
        k = todo.pop()
        if k > 1:
            sizes.add(k // 2)
            todo += [k // 2, k - k // 2]
    return [mask_of(c) for k in sorted(sizes, reverse=True) for c in combinations(range(n), k)]


def group_texts(gen, topics, eval_seed, bases, cands, signs, masks):
    """-> texts in the order [base' of bases[0], its group texts in `masks` order, base' of bases[1], ...]."""
    cues = cue_strings(gen, eval_seed)
    specs = scan_specs(gen, eval_seed)
    out = []
    for i in bases:
        t, lv, s = specs[i]
        out.append(gen.render(topics[t], samplelike_levels(lv, t, cands, signs), cues, s)[0])
        for m in masks:
            out.append(gen.render(topics[t], group_levels(lv, t, cands, signs, m), cues, s)[0])
    return out


# ---------------------------------------------------------------- exact back-end: encode, cache, load

def encode_logits(encoder, texts, w, b):
    """True logits of texts through `encoder` (list of BATCH_SIZE-multiple texts -> resid [n, d]); the list is
    padded to a multiple of BATCH_SIZE with copies of its last text."""
    texts = list(texts)
    pad = (-len(texts)) % BATCH_SIZE
    resid = encoder(texts + [texts[-1]] * pad)
    return probe_logit(resid[:len(texts)], w, b)


def reproduction_stats(stored, fresh, unit):
    d = np.abs(np.asarray(fresh, np.float64) - np.asarray(stored, np.float64))
    return {"n": int(d.size), "n_equal": int((d == 0).sum()), "n_within_1e-9": int((d <= 1e-9).sum()),
            "max_abs_logit": float(d.max()),
            "rms_logit": float(np.sqrt((d ** 2).mean())), "max_abs_units": float(d.max() / unit),
            "rms_units": float(np.sqrt((d ** 2).mean()) / unit)}


def exact_probe(encoder, gen, meta, w, b, z, p):
    """Reproduce the stored scan of one probe, then (only if it reproduces) encode its sample-like bases and
    group texts. meta: answer probe dict (topics, eval_seed); z: its grid arrays; p: Probe.
    -> dict of arrays for the cache (always with the reproduction numbers; group logits only if usable)."""
    topics = list(meta["topics"])
    texts, levels, topic = scan_texts(gen, topics, meta["eval_seed"])
    levels_ok = bool(np.array_equal(levels, np.asarray(z["scan_levels"]))
                     and np.array_equal(topic, np.asarray(z["scan_topic"])))
    stored = np.asarray(z["scan_logits"], np.float64)
    out = {"levels_ok": np.array(levels_ok), "bases": np.array(p.gbases, np.int64),
           "scan_sha": np.array(_sha(texts))}
    if len(texts) != len(stored):
        out["scan_relogits"] = np.zeros(0)
        out["usable"] = np.array(False)
        return out
    fresh = encode_logits(encoder, texts, w, b)
    rep = reproduction_stats(stored, fresh, p.unit)
    usable = levels_ok and rep["max_abs_units"] <= REPRO_TOL
    out["scan_relogits"] = fresh
    out["usable"] = np.array(bool(usable))
    if not usable:
        return out
    masks = family_masks(p.n)
    gt = group_texts(gen, topics, meta["eval_seed"], p.gbases, p.cands, p.signs, masks)
    lg = encode_logits(encoder, gt, w, b).reshape(len(p.gbases), 1 + len(masks))
    out |= {"masks": np.array(masks, np.int64), "base_logit": lg[:, 0], "group_logit": lg[:, 1:],
            "group_sha": np.array(_sha(gt))}
    return out


def _sha(texts):
    h = hashlib.sha256()
    for t in texts:
        h.update(b"\x00" + t.encode())
    return h.hexdigest()


def exact_table(p, bases, masks, base_logit, group_logit, topic_of_base):
    """Cached logits -> [n_bases, 2**n] sign-aware group readings (NaN where not measured):
    (2 * label - 1) * (logit of the sample-like base - logit of the group text), label = the base's topic
    index. Positive when the probe follows the group's properties the way the sample's alignment predicts."""
    tab = np.full((p.single.shape[1], 2 ** p.n), np.nan)
    for r, i in enumerate(bases):
        s = 2 * int(topic_of_base[i]) - 1
        tab[i, np.asarray(masks, int)] = s * (base_logit[r] - np.asarray(group_logit[r], np.float64))
    return tab


def cands_tag(p):
    return hashlib.sha256(json.dumps([p.cands, p.signs, p.gbases]).encode()).hexdigest()[:16]


def exact_path(private, ep):
    return Path(private) / f"exact_{ep}.npz"


def load_exact(private, ep, ev, P):
    """Attach the exact tables from the cache. -> per-probe reproduction rows (recomputed here from the cached
    re-encoded scan logits and the bank's stored ones), or None if there is no cache for the episode.
    A probe is attached only if its reproduction check passes and its candidate list matches the cache."""
    path = exact_path(private, ep)
    if not path.exists():
        return None
    rows = []
    with np.load(path, allow_pickle=False) as z:
        for p in P:
            k = f"p{p.j}_"
            g = ev.e.grid(p.j)
            stored = np.asarray(g["scan_logits"], np.float64)
            fresh = z[k + "scan_relogits"]
            row = {"episode": ep, "probe": p.j, "levels_ok": bool(z[k + "levels_ok"]),
                   "tag_ok": str(z[k + "tag"]) == cands_tag(p)}
            if len(fresh) == len(stored):
                row |= reproduction_stats(stored, fresh, p.unit)
                n = N_SCAN
                pair = np.abs((fresh[n:] - np.tile(fresh[:n], len(fresh) // n - 1))
                              - (stored[n:] - np.tile(stored[:n], len(stored) // n - 1)))
                row["max_abs_pair_units"] = float(pair.max() / p.unit)
            row["usable"] = bool(row["levels_ok"] and row["tag_ok"] and "max_abs_units" in row
                                 and row["max_abs_units"] <= REPRO_TOL and (k + "group_logit") in z.files)
            if row["usable"]:
                p.tables["exact"] = exact_table(p, z[k + "bases"], z[k + "masks"], z[k + "base_logit"],
                                                z[k + "group_logit"], np.asarray(g["scan_topic"]))
                row["n_bases"] = int(len(z[k + "bases"]))
                row["n_group_texts"] = int(z[k + "group_logit"].size + len(z[k + "bases"]))
            rows.append(row)
    return rows


def subject_encoder(subject):
    """Residuals as hidden.encode_sparse computes them (Subject.encode in consecutive BATCH_SIZE batches, no
    OOM fallback), without keeping the latents."""
    def enc(texts):
        if not texts or len(texts) % BATCH_SIZE:
            raise ValueError(f"need a non-empty multiple of {BATCH_SIZE} texts, got {len(texts)}")
        out = []
        for i in range(0, len(texts), BATCH_SIZE):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                e = subject.encode(texts[i:i + BATCH_SIZE], batch_size=BATCH_SIZE)
            if any("OOM" in str(c.message) for c in caught):
                raise RuntimeError("encode fell back to a smaller batch; results would not match")
            out.append(e.resid)
        return np.concatenate(out)
    return enc


def encode_episode(encoder, ev, P, gen, log=None):
    """exact_probe for every probe of an episode. ev needs .ep, .answer["probes"], .e.grid(j), .e.probes[j].
    -> (cache arrays keyed p{j}_<name>, texts encoded, probes failing the reproduction check)."""
    arrays, n_texts, bad = {}, 0, 0
    for p in P:
        z = ev.e.grid(p.j)
        pr = ev.e.probes[p.j]
        res = exact_probe(encoder, gen, ev.answer["probes"][p.j], pr["w"], pr["b"], z, p)
        res["tag"] = np.array(cands_tag(p))
        usable = bool(res["usable"])
        n_texts += len(res["scan_relogits"]) + (res["group_logit"].size + len(p.gbases) if usable else 0)
        bad += not usable
        if log:
            rep = (reproduction_stats(z["scan_logits"], res["scan_relogits"], p.unit)
                   if len(res["scan_relogits"]) else {})
            log(f"  {ev.ep} probe {p.j}: levels_ok={bool(res['levels_ok'])} usable={usable} "
                + " ".join(f"{k}={v:.3g}" for k, v in rep.items()), flush=True)
        arrays |= {f"p{p.j}_{k}": v for k, v in res.items()}
    return arrays, int(n_texts), int(bad)


def save_exact(private, ep, arrays, meta):
    """Write <private>/exact_<ep>.npz atomically (arrays from encode_episode plus a JSON `meta` string)."""
    private = Path(private)
    private.mkdir(parents=True, exist_ok=True)
    meta = {"episode": ep, "repro_tol_units": REPRO_TOL, "batch_size": BATCH_SIZE} | dict(meta)
    tmp = private / f"exact_{ep}.{os.getpid()}.tmp.npz"
    np.savez_compressed(tmp, **arrays, meta=np.array(json.dumps(meta)))
    os.replace(tmp, exact_path(private, ep))


def gpu_main(args):
    import torch
    if not torch.cuda.is_available():
        raise SystemExit("--gpu-encode needs CUDA (run under flock /tmp/shifthunt-gpu.lock, without "
                         "CUDA_VISIBLE_DEVICES=\"\")")
    import transformers
    from shifthunt.substrate import Subject
    priv = Path(args.private)
    priv.mkdir(parents=True, exist_ok=True)
    eps = [x.strip() for x in args.episodes.split(",") if x.strip()]
    todo = [ep for ep in eps if args.force or not exact_path(priv, ep).exists()]
    if not todo:
        print("every episode is cached; use --force to re-encode")
        return 0
    t0 = time.time()
    enc = subject_encoder(Subject("cuda"))
    print(f"model loaded {time.time() - t0:.0f}s", flush=True)
    bad = 0
    versions = {"torch": torch.__version__, "transformers": transformers.__version__,
                "device": torch.cuda.get_device_name(0)}
    for ep in todo:
        t = time.time()
        ev = ML.EpisodeEval(ep)
        P = build_probes(ev)
        require_single_main(ep, P)
        arrays, n_texts, n_bad = encode_episode(enc, ev, P, GENERATORS[ev.sub], log=print)
        bad += n_bad
        save_exact(priv, ep, arrays, versions | {"n_texts": n_texts, "seconds": round(time.time() - t, 1)})
        print(f"{ep} [{ev.sub}] {n_texts} texts {time.time() - t:.0f}s", flush=True)
        del ev
    print(f"total {time.time() - t0:.0f}s; probes failing the reproduction check: {bad}")
    return 1 if bad else 0


# ---------------------------------------------------------------- additivity of group readings

def additivity_rows(P, kind):
    """Per (probe, base, group) with exact logits: exact reading, the additive back-end's reading (sum of
    stored single flips on the raw scan base), and the sum of exact single flips on the sample-like base.
    All in topic units."""
    rows = []
    for p in P:
        if "exact" not in p.tables:
            continue
        ex, ad = p.tables["exact"] / p.unit, p.tables["additive"] / p.unit
        bits = bit_matrix(p.n)
        main_bits = sum(1 << p.cands.index(m) for m in p.truth if m in p.cands)
        slot = "hard" if p.hard else p.kind if p.kind == "null" else "ordinary"
        for i in p.gbases:
            singles = np.array([ex[i, 1 << c] for c in range(p.n)])
            for m in np.flatnonzero(~np.isnan(ex[i])):
                rows.append((kind, slot, int(bits[:, m].sum()), bool(m & main_bits), float(ex[i, m]),
                             float(ad[i, m]), float(singles @ bits[:, m])))
    return rows


def additivity_summary(rows):
    """-> {comparison: {group key: stats}}. Comparisons: "stored" = exact group reading minus the additive
    back-end's (sum of stored single flips on the raw scan base); "samplelike" = exact group reading minus the
    sum of exact single flips on the same sample-like base (pure additivity; sizes > 1)."""
    def stats(err, a, b):
        err = np.asarray(err)
        return {"n": int(err.size), "bias": float(err.mean()), "rms": float(np.sqrt((err ** 2).mean())),
                "p95_abs": float(np.quantile(np.abs(err), 0.95)), "max_abs": float(np.abs(err).max()),
                "decision_flip": float(np.mean((np.asarray(a) > THR) != (np.asarray(b) > THR)))}
    out = {"stored": {}, "samplelike": {}}
    groups = {}
    for kind, slot, size, has_main, ex, ad, ss in rows:
        for key in (f"{kind}|size {size}", f"{kind}|all sizes", f"all|size {size}", "all|all sizes",
                    f"all|{slot}|size {size}", f"{kind}|size {size}|{'with' if has_main else 'without'} a main"):
            groups.setdefault(key, []).append((size, ex, ad, ss))
    for key, v in sorted(groups.items()):
        a = np.array(v)
        out["stored"][key] = stats(a[:, 1] - a[:, 2], a[:, 1], a[:, 2])
        multi = a[a[:, 0] > 1]
        if len(multi):
            out["samplelike"][key] = stats(multi[:, 1] - multi[:, 3], multi[:, 1], multi[:, 3])
    return out


# ---------------------------------------------------------------- report

def episode_kind(ev):
    types = set().union(*[ML.slot_types(ev.answer["probes"][j]) for j in ev.hard]) if ev.hard else set()
    for k, label in KIND_LABEL.items():
        if k in types:
            return label
    return "other"


def aggregate(per_ep, kinds):
    """per_ep: {ep: {row: {B: cell}}} -> {row: {B: {"per_episode", "pooled", "by_kind"}}} for name/all/used."""
    out = {}
    eps = list(per_ep)
    rows = [r for r in per_ep[eps[0]]]
    for row in rows:
        for B in per_ep[eps[0]][row]:
            cells = {ep: per_ep[ep][row][B] for ep in eps}

            def mean(key, sel):
                return float(np.mean([cells[ep][key] for ep in sel]))
            by_kind = {}
            for k in sorted(set(kinds.values())):
                sel = [ep for ep in eps if kinds[ep] == k]
                by_kind[k] = {key: mean(key, sel) for key in ("name", "all", "used", "null_none")} | {"episodes": len(sel)}
                by_kind[k]["hard"] = {c: float(np.mean([cells[ep]["hard"].get(c, 0.0) for ep in sel]))
                                      for c in ("named", "none", "wrong", "extra")}
            out.setdefault(row, {})[str(B)] = {
                "per_episode": cells,
                "pooled": {key: mean(key, eps) for key in ("name", "all", "used", "null_none")}
                | {"episodes": len(eps),
                   "hard": {c: float(np.mean([cells[ep]["hard"].get(c, 0.0) for ep in eps]))
                            for c in ("named", "none", "wrong", "extra")}},
                "by_kind": by_kind}
    return out


def _f(x):
    return f"{x:.2f}"


def _table(res, rows, budgets, pick, head="policy"):
    L = [f"| {head} | " + " | ".join(f"B = {b}" for b in budgets) + " |", "|---|" + "---|" * len(budgets)]
    for row in rows:
        if row in res:
            L.append(f"| {ROW_LABEL[row]} | " + " | ".join(_f(pick(res[row][str(b)])) for b in budgets) + " |")
    return L


def best(res, rows, B, key="name"):
    """Best pooled rate at budget B over the rows. -> (rate, row)."""
    return max(((res[r][str(B)]["pooled"][key], r) for r in rows if r in res), key=lambda t: (t[0], t[1]))


def readme(J):
    budgets = J["budgets"]
    eps = J["episodes"]
    kinds = sorted(set(J["kinds"].values()))
    have_exact = "exact" in J["results"]["topic"]
    A = J["results"]["topic"]["additive"]
    L = ["# blind_verify: what a scripted blind solver can name with B exact queries (plan 0b.3)\n",
         "Generated by `scripts/blind_verify.py` (commands: `COMMANDS.md`; all numbers: `blind_verify.json`). "
         "No cue is named and nothing here says which probe is an episode's hard slot.\n",
         "**PRIVILEGED scripted ceilings, not agent results.** The solver has no SAE information, but it is "
         "handed the episode's list of 8 label-aligned properties, their signs, and the generator's exact edit "
         "of each. It does not know which probe is hard or null. These are the best of the scripted policies "
         "written here, not a proven optimum.\n",
         f"Episodes: {', '.join(eps)} ({', '.join(f'{k}: ' + str(sum(v == k for v in J['kinds'].values())) for k in kinds)}). "
         f"{J['seeds']} seeded runs per episode, policy and budget (Monte Carlo standard error of one episode's "
         f"rate at most {0.5 / math.sqrt(J['seeds']):.3f}; of a pooled rate over {len(eps)} episodes at most "
         f"{0.5 / math.sqrt(J['seeds'] * len(eps)):.3f}). B is the number of exact queries per episode, shared "
         "by the 4 probes.\n",
         "## Cost model and decision rule\n",
         "- **One query per edited text; the unedited base note is free.** In the blackbox tool set the logits "
         "of sample notes come from `probe_scores`, which does not spend `probe_query`; the stored scan bases "
         "stand in for sample notes here. A blind agent that edits notes it wrote itself would also pay for "
         "the base, roughly halving its readings per budget.",
         f"- A reading is the sign-aware true logit difference between a base note and its edited copy. It "
         f"counts as positive above **{THR} x the probe's topic unit** (midpoint of the prompt's 0.3 and 0.15). "
         "Primary unit: the privileged mean topic-swap effect over all 32 stored bases, taken as free. "
         f"Sensitivity, unit-free: positive above {THR_FREE:.2f} logits (10 x 0.225 / 1.225, from the sample gap "
         "of exactly 10).",
         "- NAME = the hard slot's claim set equals its main cue(s) and every null probe is answered `none`. "
         "ALL = every probe's claim set is right. Rates are per episode; pooled and by-kind rates are means "
         "over episodes.",
         "- Back-end A (additive, primary, stored data only): a group text's reading is the sum of the stored "
         "single-flip readings of its members on the same scan base. Back-end B (exact): the group texts are "
         "re-rendered and their true logits computed on the GPU. Single flips are stored, so policy (i) is "
         "exact under both.\n",
         "## Policies\n",
         "- **(i) random single flips.** B of the 32 (probe, aligned property) cells, drawn without replacement, "
         "one single-flip text each on a random valid base (a child property only on bases with its parent on). "
         "A cell that reads positive is claimed (at most 2 per probe). Above 32, cells are read again on new "
         "bases and averaged.",
         "- **(ii) bisection, screen first (the plan's policy).** One text per probe with all 8 aligned "
         "properties moved to the other label's levels. For the probes that read positive, in random order, "
         "the 8 candidates (random order) are halved with one group text per step: 3 texts isolate one. "
         "`none` / `guess`: a probe whose search ran out of budget is answered `none`, or with a uniform draw "
         "from the candidates still standing.",
         "- **(ii-b) bisection, depth first (added).** The same texts, but each probe is screened and "
         "searched to the end before the next one is touched.",
         "- **(ii-c) bisection, no screen, confirm (added).** No all-8 text: halve as if a main exists "
         "(3 texts), then read the isolated candidate's single flip and claim it only if that is positive.",
         "- **One main per probe.** A halving search isolates one candidate, so every bisection variant answers "
         "a probe with at most one property; on a probe with two main cues it could never be right (only "
         "policy (i) can claim two). The script refuses an episode that has such a probe. None of these "
         "episodes has one, so no rate here is affected.",
         "- Group texts start from a sample-like base: a stored scan base with every aligned property at the "
         "level it has in sample notes of that base's label, so a group text moves its members toward the "
         "other label, as an agent editing a sample note would. Every bisection reading uses R bases, R = "
         "max(1, B // 16); leftover budget starts the next probe, and what remains at the end is unspent.",
         "- Bases: a single flip of a child property (a variant of its parent's line) is read only on bases "
         "with the parent on; group texts only on bases where that holds for every aligned child ("
         + "; ".join(f"{k} episodes: {v[0]}-{v[1]} of 32 bases per probe" if v[0] != v[1] else
                     f"{k} episodes: {v[0]} of 32 bases per probe" for k, v in sorted(J["group_bases"].items()))
         + ").\n",
         "## Bases per reading\n",
         "Single-base readings are noisy; the table says how many base notes each reading averages.\n",
         "| policy | " + " | ".join(f"B = {b}" for b in budgets) + " |", "|---|" + "---|" * len(budgets),
         "| (i) random single flips: cells read (of 32), bases per cell | "
         + " | ".join(J["bases_per_reading"]["random"][str(b)] for b in budgets) + " |"]
    for fam in BISECT:
        L.append(f"| {ROW_LABEL[fam + '_none'].split(';')[0]}: bases per reading (R) | "
                 + " | ".join(str(J["bases_per_reading"][fam][str(b)]) for b in budgets) + " |")
    L += ["", "Mean queries actually used (back-end A, pooled):\n"]
    L += _table(A, ROWS, budgets, lambda c: c["pooled"]["used"])
    L += ["", "## NAME, back-end A (additive), privileged topic unit: primary\n", "Pooled over the episodes:\n"]
    L += _table(A, ROWS, budgets, lambda c: c["pooled"]["name"])
    for k in kinds:
        n = sum(v == k for v in J["kinds"].values())
        L += ["", f"{k} episodes (n = {n}):\n"]
        L += _table(A, ROWS, budgets, lambda c, k=k: c["by_kind"][k]["name"])
    if have_exact:
        X = J["results"]["topic"]["exact"]
        L += ["", "## NAME, back-end B (exact group-flip logits from the GPU), privileged topic unit\n",
              "Policy (i) reads stored single flips, so its row is the same as above. The last row is policy "
              "(i) reading its single flips on the sample-like bases instead (also exact GPU logits).\n",
              "Pooled over the episodes:\n"]
        L += _table(X, ROWS_EXACT, budgets, lambda c: c["pooled"]["name"])
        for k in kinds:
            n = sum(v == k for v in J["kinds"].values())
            L += ["", f"{k} episodes (n = {n}):\n"]
            L += _table(X, ROWS_EXACT, budgets, lambda c, k=k: c["by_kind"][k]["name"])
    else:
        L += ["", "## Back-end B (exact)\n", "Not available: " + J["exact_status"] + "\n"]
    if have_exact and "backend_gap" in J:
        g, e = J["backend_gap"]["pooled"], J["backend_gap"]["per_episode"]
        L += ["", f"Back-ends A and B compared (same seeds): the largest pooled difference in NAME is "
              f"{g['abs_diff']:.2f} ({ROW_LABEL[g['row']]}, B = {g['B']}: {_f(g['additive'])} additive, "
              f"{_f(g['exact'])} exact); the largest for one episode is {e['abs_diff']:.2f} ({e['episode']}, "
              f"{ROW_LABEL[e['row']]}, B = {e['B']}: {_f(e['additive'])} additive, {_f(e['exact'])} exact)."]
    if "noiseless" in J:
        L += ["", "## Noiseless reference: what the budget alone allows\n",
              "The same policies and seeds when every reading is exactly right (a main reads 1 topic unit, "
              "every other property 0). What is lost here is lost to the budget, not to noisy readings. NAME, "
              "pooled:\n"]
        L += _table(J["noiseless"], ROWS, budgets, lambda c: c["pooled"]["name"])
    L += ["", "## NAME per episode\n"]
    for backend, rows in (("additive", ROWS), ("exact", ROWS_EXACT)):
        if backend not in J["results"]["topic"]:
            continue
        res = J["results"]["topic"][backend]
        L += [f"Back-end {'A (additive)' if backend == 'additive' else 'B (exact)'}, privileged topic unit:\n",
              "| policy | B | " + " | ".join(f"{ep} ({J['kinds'][ep]})" for ep in eps) + " | pooled |",
              "|---|---|" + "---|" * (len(eps) + 1)]
        for row in rows:
            for b in budgets:
                c = res[row][str(b)]
                L.append(f"| {ROW_LABEL[row]} | {b} | " + " | ".join(_f(c["per_episode"][ep]["name"]) for ep in eps)
                         + f" | {_f(c['pooled']['name'])} |")
        L.append("")
    L += ["## Where NAME is lost (back-end A, privileged unit, pooled)\n",
          "Share of runs by the hard slot's answer, and the share of runs with every null probe answered "
          "`none`. NAME needs both.\n",
          "| policy | B | hard slot named | answered `none` | wrong property | right plus an extra | nulls all `none` |",
          "|---|---|---|---|---|---|---|"]
    for row in ROWS:
        for b in budgets:
            c = A[row][str(b)]["pooled"]
            L.append(f"| {ROW_LABEL[row]} | {b} | " + " | ".join(_f(c["hard"][k]) for k in ("named", "none", "wrong", "extra"))
                     + f" | {_f(c['null_none'])} |")
    L += ["", "## ALL-slots naming (every probe right), pooled, privileged unit\n"]
    L += ["Back-end A:\n"] + _table(A, ROWS, budgets, lambda c: c["pooled"]["all"])
    if have_exact:
        L += ["", "Back-end B:\n"] + _table(J["results"]["topic"]["exact"], ROWS_EXACT, budgets,
                                           lambda c: c["pooled"]["all"])
    L += ["", f"## Sensitivity: unit-free threshold ({THR_FREE:.2f} logits), NAME pooled\n"]
    L += ["Back-end A:\n"] + _table(J["results"]["free"]["additive"], ROWS, budgets, lambda c: c["pooled"]["name"])
    for k in kinds:
        L += ["", f"Back-end A, {k} episodes:\n"]
        L += _table(J["results"]["free"]["additive"], ROWS, budgets, lambda c, k=k: c["by_kind"][k]["name"])
    if "exact" in J["results"]["free"]:
        L += ["", "Back-end B:\n"] + _table(J["results"]["free"]["exact"], ROWS_EXACT, budgets,
                                           lambda c: c["pooled"]["name"])
    if have_exact:
        R = J["reproduction"]
        L += ["", "## Reproduction check before the exact back-end is trusted\n",
              f"Each probe's stored scan set was re-rendered from its seeds and re-encoded in the stored batch "
              f"order ({R['n_probes']} probes, {R['n_texts']} texts). Gate, fixed before the run: re-rendered "
              f"base levels and topics equal the stored ones, and every re-encoded logit within {REPRO_TOL} "
              "topic units of the stored one.\n",
              "| check | result |", "|---|---|",
              f"| probes with re-rendered levels and topics equal to the stored ones | {R['levels_ok']}/{R['n_probes']} |",
              f"| scan logits within 1e-9 logits of the stored ones | {R['n_within_1e-9']}/{R['n_texts']} |",
              f"| largest \\|re-encoded - stored\\| logit | {R['max_abs_logit']:.3g} logits = {R['max_abs_units']:.3g} topic units |",
              f"| largest difference of a flip pair (edited - base), topic units | {R['max_abs_pair_units']:.3g} |",
              f"| probes passing the gate | **{R['usable']}/{R['n_probes']}** |",
              f"| sample-like bases and group texts then encoded | {R['n_group_texts']} texts on {R['n_bases']} bases |",
              ""]
        Ad = J["additivity"]
        L += ["## Additivity error (exact group reading minus additive reading), topic units\n",
              "Per sample-like base and group. `vs stored singles` is the error of back-end A itself: exact "
              "group reading minus the sum of the stored single flips on the raw scan base (other aligned "
              "properties at random levels there). `vs exact singles` isolates non-additivity: exact group "
              "reading minus the sum of the exact single flips on the same sample-like base. `flips` is the "
              f"share of readings on opposite sides of the {THR} threshold.\n",
              "| kind | group size | n | vs stored singles: bias | rms | 95th pct \\|err\\| | max | flips | "
              "vs exact singles: bias | rms | max | flips |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for k in kinds + ["all"]:
            for size in J["group_sizes"]:
                key = f"{k}|size {size}"
                if key not in Ad["stored"]:
                    continue
                s, e = Ad["stored"][key], Ad["samplelike"].get(key)
                L.append(f"| {k} | {size} | {s['n']} | {s['bias']:+.3f} | {s['rms']:.3f} | {s['p95_abs']:.3f} | "
                         f"{s['max_abs']:.3f} | {s['decision_flip']:.3f} | "
                         + (f"{e['bias']:+.3f} | {e['rms']:.3f} | {e['max_abs']:.3f} | {e['decision_flip']:.3f} |"
                            if e else "- | - | - | - |"))
        L.append("")
    g = J["grader_check"]
    L += ["## Check against the grader\n",
          f"Set-equality naming (used above) agrees with the grader's naming grade (`identified` and `no_extra` "
          f"for a planted probe, `none` for a null probe; the generator's exact regexes) on {g['agree']}/{g['checked']} "
          "distinct (probe, claim set) pairs that occurred in the runs.\n"]
    L += ["## Answer: is a low BB-8 an agent shortfall, or low by budget design?\n", J["answer"], ""]
    return "\n".join(L) + "\n"


def answer_paragraph(J):
    """One paragraph from the numbers: best scripted blind NAME at the smallest and largest budget."""
    budgets = J["budgets"]
    lo, hi = budgets[0], budgets[-1]
    A = J["results"]["topic"]["additive"]
    X = J["results"]["topic"].get("exact")
    kinds = sorted(set(J["kinds"].values()))

    def desc(res, rows, B):
        v, r = best(res, rows, B)
        per = ", ".join(f"{k} {_f(res[r][str(B)]['by_kind'][k]['name'])}" for k in kinds)
        return v, f"{_f(v)} ({ROW_LABEL[r]}; {per})"
    a_lo, s_lo = desc(A, ROWS, lo)
    a_hi, s_hi = desc(A, ROWS, hi)
    spec_lo = max(A[r][str(lo)]["pooled"]["name"] for r in ("random", "bisect_sf_none", "bisect_sf_guess"))
    T = [f"At B = {lo} the best scripted blind policy gets NAME (hard slot named, null probe left alone) in "
         f"{s_lo} of runs with the additive back-end; the plan's two policies alone (random single flips, "
         f"screen-first bisection) reach at most {_f(spec_lo)}. At B = {hi} the best is {s_hi}."]
    if X:
        x_lo, sx_lo = desc(X, ROWS_EXACT, lo)
        x_hi, sx_hi = desc(X, ROWS_EXACT, hi)
        T.append(f"With exact group-flip logits from the GPU the best rates are {sx_lo} at B = {lo} and {sx_hi} at "
                 f"B = {hi}.")
        b_lo, b_hi = max(a_lo, x_lo), max(a_hi, x_hi)
    else:
        T.append("The exact back-end was not available, so the bisection rows rest on the additivity assumption.")
        b_lo, b_hi = a_lo, a_hi
    if "noiseless" in J:
        n_lo, n_hi = best(J["noiseless"], ROWS, lo)[0], best(J["noiseless"], ROWS, hi)[0]
        T.append(f"With every reading exactly right the same policies reach at most {_f(n_lo)} at B = {lo} and "
                 f"{_f(n_hi)} at B = {hi}: there are 32 (probe, aligned property) cells and the hard slot is not "
                 f"marked, so {lo} single flips cover a quarter of the cells, and a bisection needs 4 texts per "
                 f"probe, so {lo} texts finish two of the four probes.")
    if b_lo < 0.7 <= b_hi:
        T.append(f"So a low BB-{lo} NAME rate is mostly **low by budget design**, not an agent shortfall: a solver "
                 f"that is handed the candidate list, the signs and the exact edits, and gets base notes and the "
                 f"topic unit free, tops out near {_f(b_lo)} at {lo} queries and reaches {_f(b_hi)} at {hi}. A "
                 f"BB-{lo} agent rate up to about {_f(b_lo)} is what the budget allows. The budget does not put "
                 f"BB-{lo} at the floor, though: a rate near zero would be below this ceiling, and a BB-{hi} rate "
                 f"well below {_f(b_hi)} would be an agent shortfall. A BB-{lo} rate clearly above {_f(b_lo)} would "
                 f"mean the agent used something this solver lacks, such as a prior about which properties are "
                 f"plausible cues (the two-part hint is not such a thing: it says how to measure a nested "
                 f"property, which this solver already does).")
    elif b_lo >= 0.7:
        T.append(f"So a low BB-{lo} NAME rate would be **an agent shortfall**: the scripted blind ceiling at "
                 f"{lo} queries is already {_f(b_lo)}.")
    else:
        T.append(f"The scripted ceiling is low at both budgets ({_f(b_lo)} at {lo}, {_f(b_hi)} at {hi}), so "
                 f"these policies do not separate an agent shortfall from the budget.")
    F = J["results"]["free"]
    f_lo = max(best(F[b], ROWS, lo)[0] for b in F)
    f_hi = max(best(F[b], ROWS, hi)[0] for b in F)
    T.append(f"Caveats: these are the best of the policies written here, not a proven optimum; a reading uses one "
             f"base note at B <= 16 (and at B = 32 for single flips), two to four above, so part of every loss is "
             f"single-base noise; without the privileged topic unit (unit-free rule) the best rates are "
             f"{_f(f_lo)} at B = {lo} and {_f(f_hi)} at B = {hi}; and an agent that had to pay for its base notes "
             f"would get about half as many readings per budget.")
    return " ".join(T)


def backend_gap(res_a, res_b, rows, budgets, eps):
    """Largest |NAME(back-end A) - NAME(back-end B)|, pooled and per episode, over the rows and budgets."""
    pooled = max((abs(res_a[r][str(b)]["pooled"]["name"] - res_b[r][str(b)]["pooled"]["name"]), r, b)
                 for r in rows for b in budgets)
    per_ep = max((abs(res_a[r][str(b)]["per_episode"][ep]["name"] - res_b[r][str(b)]["per_episode"][ep]["name"]),
                  r, b, ep) for r in rows for b in budgets for ep in eps)
    cell = lambda res, r, b, ep=None: (res[r][str(b)]["per_episode"][ep] if ep else res[r][str(b)]["pooled"])["name"]
    return {"pooled": {"abs_diff": pooled[0], "row": pooled[1], "B": pooled[2],
                       "additive": cell(res_a, pooled[1], pooled[2]), "exact": cell(res_b, pooled[1], pooled[2])},
            "per_episode": {"abs_diff": per_ep[0], "row": per_ep[1], "B": per_ep[2], "episode": per_ep[3],
                            "additive": cell(res_a, *per_ep[1:]), "exact": cell(res_b, *per_ep[1:])}}


def bases_per_reading(P_by_ep, budgets):
    out = {"random": {}}
    n_cells = max(sum(p.n for p in P) for P in P_by_ep.values())
    for b in budgets:
        q, r = divmod(b, n_cells)
        out["random"][str(b)] = (f"{b} cells, 1 base" if q == 0 else
                                 f"{n_cells} cells, {q} base{'s' if q > 1 else ''}" + (f" ({r} cells {q + 1})" if r else ""))
    for fam, kw in BISECT.items():
        out[fam] = {}
        for b in budgets:
            rs = sorted({bisect_replicates(P, b, kw["screen"], kw["confirm"]) for P in P_by_ep.values()})
            out[fam][str(b)] = rs[0] if len(rs) == 1 else f"{rs[0]}-{rs[-1]}"
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episodes", default=",".join(SHIPPED))
    ap.add_argument("--bank", default=None, help="episode bank directory (default $SHIFTHUNT_BANK, else .cache/bank)")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--budgets", default=",".join(map(str, BUDGETS)))
    ap.add_argument("--out", default=str(ROOT / "results" / "blackbox_1112" / "blind_verify"))
    ap.add_argument("--private", default=str(ROOT / "results" / "private_1112" / "blind_verify"))
    ap.add_argument("--exact", choices=("auto", "off", "require"), default="auto",
                    help="use the cached exact group-flip logits in --private (auto: if present for every episode)")
    ap.add_argument("--gpu-encode", action="store_true",
                    help="compute the exact back-end's logits on the GPU into --private and exit")
    ap.add_argument("--force", action="store_true", help="with --gpu-encode: re-encode cached episodes")
    ap.add_argument("--no-grader-check", action="store_true")
    ap.add_argument("--readme-only", action="store_true",
                    help="no run: rewrite <out>/README.md (and the answer paragraph) from <out>/blind_verify.json")
    args = ap.parse_args()
    if args.readme_only:
        path = Path(args.out) / "blind_verify.json"
        J = json.loads(path.read_text())
        J["answer"] = answer_paragraph(J)
        path.write_text(json.dumps(J, indent=1))
        (Path(args.out) / "README.md").write_text(readme(J))
        print(readme(J))
        return 0
    ML.BANK = ML.resolve_bank(args.bank)
    if args.gpu_encode:
        return gpu_main(args)
    if args.seeds < 1000:
        print(f"note: {args.seeds} seeds (the plan asks for at least 1000)", file=sys.stderr)
    eps = [x.strip() for x in args.episodes.split(",") if x.strip()]
    budgets = [int(x) for x in args.budgets.split(",")]
    out, priv = Path(args.out), Path(args.private)
    t0 = time.time()

    evs, Ps, kinds, repro = {}, {}, {}, []
    exact_missing = []
    for ep in eps:
        evs[ep] = ML.EpisodeEval(ep)
        Ps[ep] = build_probes(evs[ep])
        try:
            require_single_main(ep, Ps[ep])
        except ValueError as e:
            raise SystemExit(str(e))
        kinds[ep] = episode_kind(evs[ep])
        if args.exact != "off":
            rows = load_exact(priv, ep, evs[ep], Ps[ep])
            if rows is None:
                exact_missing.append(f"{ep}: no cache")
            else:
                repro += rows
                if not all(r["usable"] for r in rows):
                    exact_missing.append(f"{ep}: {sum(not r['usable'] for r in rows)} probe(s) fail the reproduction check")
    use_exact = args.exact != "off" and not exact_missing
    if args.exact == "require" and not use_exact:
        raise SystemExit("exact back-end required but unavailable: " + "; ".join(exact_missing))
    exact_status = ("used" if use_exact else "switched off (--exact off)" if args.exact == "off"
                    else "; ".join(exact_missing))

    results = {u: {} for u in UNITS}
    grader = {"checked": 0, "agree": 0}
    private_rows = []
    seen_all = {ep: Counter() for ep in eps}
    for unit in UNITS:
        for backend in (["additive", "exact"] if use_exact else ["additive"]):
            fams = ["random"] + list(BISECT) + (["random_samplelike"] if backend == "exact" else [])
            per_ep = {}
            for ep in eps:
                per_ep[ep], seen = simulate(ep, Ps[ep], fams, budgets, args.seeds, backend, unit)
                seen_all[ep] |= seen
            results[unit][backend] = aggregate(per_ep, kinds)
            print(f"[{time.time() - t0:.0f}s] unit={unit} backend={backend}: "
                  + " ".join(f"{r}@{budgets[0]}={results[unit][backend][r][str(budgets[0])]['pooled']['name']:.2f}"
                             f"/@{budgets[-1]}={results[unit][backend][r][str(budgets[-1])]['pooled']['name']:.2f}"
                             for r in results[unit][backend]), flush=True)
    fams = ["random"] + list(BISECT)
    noiseless = aggregate({ep: simulate(ep, noiseless_probes(Ps[ep]), fams, budgets, args.seeds, "additive", "topic")[0]
                           for ep in eps}, kinds)
    if not args.no_grader_check:
        for ep in eps:
            n, ok = grader_check(evs[ep], Ps[ep], seen_all[ep])
            grader["checked"] += n
            grader["agree"] += ok

    J = {"episodes": eps, "kinds": kinds, "seeds": args.seeds, "budgets": budgets, "threshold_topic_units": THR,
         "threshold_unit_free_logits": THR_FREE, "max_claims": MAX_CLAIMS,
         "cost_model": "one probe_query per edited text per probe; the unedited base note is free (sample-note "
                       "logits come from probe_scores); the privileged topic unit is free",
         "privileged": "aligned property list, per-probe signs, exact edits; no SAE information; hard slot and "
                       "null probes unknown to the solver",
         "bases_per_reading": bases_per_reading(Ps, budgets), "exact_status": exact_status,
         "group_bases": {k: [min(len(p.gbases) for ep in eps if kinds[ep] == k for p in Ps[ep]),
                             max(len(p.gbases) for ep in eps if kinds[ep] == k for p in Ps[ep])]
                         for k in sorted(set(kinds.values()))},
         "results": results, "noiseless": noiseless, "grader_check": grader, "row_labels": ROW_LABEL}
    if use_exact:
        J["reproduction"] = {
            "tolerance_units": REPRO_TOL, "n_probes": len(repro), "n_texts": sum(r["n"] for r in repro),
            "levels_ok": sum(r["levels_ok"] for r in repro), "n_equal": sum(r["n_equal"] for r in repro),
            "n_within_1e-9": sum(r["n_within_1e-9"] for r in repro),
            "max_abs_logit": max(r["max_abs_logit"] for r in repro),
            "max_abs_units": max(r["max_abs_units"] for r in repro),
            "rms_units_max": max(r["rms_units"] for r in repro),
            "max_abs_pair_units": max(r["max_abs_pair_units"] for r in repro),
            "usable": sum(r["usable"] for r in repro), "n_bases": sum(r["n_bases"] for r in repro),
            "n_group_texts": sum(r["n_group_texts"] for r in repro),
            "per_episode": {ep: {"max_abs_logit": max(r["max_abs_logit"] for r in repro if r["episode"] == ep),
                                 "max_abs_units": max(r["max_abs_units"] for r in repro if r["episode"] == ep),
                                 "n_within_1e-9": sum(r["n_within_1e-9"] for r in repro if r["episode"] == ep),
                                 "n": sum(r["n"] for r in repro if r["episode"] == ep)} for ep in eps}}
        rows = [r for ep in eps for r in additivity_rows(Ps[ep], kinds[ep])]
        J["additivity"] = additivity_summary(rows)
        J["group_sizes"] = sorted({r[2] for r in rows})
        J["backend_gap"] = backend_gap(results["topic"]["additive"], results["topic"]["exact"], ROWS, budgets, eps)
    J["answer"] = answer_paragraph(J)

    for ep in eps:
        for p in Ps[ep]:
            u = p.unit
            gb = p.gbases
            row = {"episode": ep, "probe": p.j, "kind": p.kind, "hard": p.hard, "mains": sorted(p.truth),
                   "cands": p.cands, "signs": p.signs, "unit": u, "n_group_bases": len(gb),
                   "single_mean_units": [float(np.mean(p.single[c][p.valid[c]]) / u) for c in range(p.n)],
                   "single_sd_units": [float(np.std(p.single[c][p.valid[c]]) / u) for c in range(p.n)],
                   "all_group": {b: {"mean": float(np.mean(t[gb, -1]) / u), "sd": float(np.std(t[gb, -1]) / u),
                                     "p_positive": float(np.mean(t[gb, -1] > THR * u))}
                                 for b, t in p.tables.items()},
                   "claims_seen": {",".join(c) or "none": n for (j, c), n in sorted(seen_all[ep].items()) if j == p.j}}
            if "exact" in p.tables:
                row["exact_single_mean_units"] = [float(np.mean(p.tables["exact"][gb, 1 << c]) / u) for c in range(p.n)]
            private_rows.append(row)

    out.mkdir(parents=True, exist_ok=True)
    priv.mkdir(parents=True, exist_ok=True)
    (out / "blind_verify.json").write_text(json.dumps(J, indent=1))
    md = readme(J)
    (out / "README.md").write_text(md)
    (priv / "blind_verify_probes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in private_rows))
    (priv / "reproduce.json").write_text(json.dumps(repro, indent=1))
    print(md)
    print(f"wrote {out}/README.md, blind_verify.json; private rows in {priv} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
