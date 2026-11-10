"""Analysis of the no-SAE study (plan §5): confirmatory tests on GPT, descriptive tables, dry run and power.

    python scripts/blackbox_analysis.py rows.csv [--s3 s3.csv] [--ledger ledger.jsonl]
                                        [--study-tag r1112 | --any-batch] [--exclude-batch NAME ...]
                                        [--out-md report.md] [--out-json report.json]
    python scripts/blackbox_analysis.py --simulate [--simulate-open64]      # the whole pipeline on simulated rows
    python scripts/blackbox_analysis.py --power                             # power of a C1-type contrast

Input: the per-run rows written by scripts/score_naming.py (--study r1112 --csv). Only counted runs of the
study are used: a batch named `<tag>_<agent>_<arm>` (tag r1112 unless --study-tag says otherwise; pilots, the
main study, its hv side batch and smoke runs are left out by name), agent gpt or haiku, arm open8 / bb8 / bb64 /
open64, one of the six items. Infrastructure failures are already uncounted in the rows. --any-batch turns the
batch-name rule off (rows that do not come from the study's run directories, such as simulated rows).
The exit status is 2, and the report says so at its top, when an (agent, arm, item) cell has more counted runs
than planned (4 for GPT, 2 for Haiku): runs from outside the study, or a re-run of a counted run, are pooled in.
A row with status `needs_regrade` (the scorer never writes one) is an error.

Confirmatory tests (GPT only; outcome NAME; arms A vs B; runs nested in items):
  statistic   T = mean over items of (mean NAME in A within the item - mean NAME in B within the item). With a
              balanced design T equals the difference of the pooled rates.
  missing     nothing is imputed: T uses the runs present. An item with no counted run in one of the two arms
              of a contrast is dropped from that contrast and named in the output; the A and B columns of a
              contrast pool the items it uses. The rates table, the Open-64 trigger and the predictions check
              use pooled rates, k/n over the counted runs of an arm.
  p           Monte Carlo within-item permutation test: within each item the arm labels of that item's runs in
              A and B are permuted, keeping the item's arm counts, independently across items; 10^4 resamples,
              seed 20261112; two-sided p = (1 + #{|T*| >= |T| - 1e-12}) / (1 + 10^4).
  CI          item-clustered bootstrap, percentile 95%, labelled approximate (6 clusters): items are resampled
              with replacement, and within each drawn item the runs of each arm are resampled with
              replacement; 10^4 resamples, same seed.
  contrasts   C1 = open8 - bb8 and C2 = bb64 - bb8 form the Holm family. C4 = bb64 - open8 and, if open64 was
              run, C3 = open64 - bb64 are read from CI and p outside the family.
  significant only the Holm family is labelled: C1 or C2 is significant iff its Holm-adjusted two-sided p is
              below 0.05. C4, C3, the by-kind contrasts and Haiku are never labelled significant or not.
  R3 rule     four exclusive branches on the CI [L, U] of C4 (plan §1a, DECISIONS D13 and D24.4):
              L > -0.20 and U >= 0: "eliminated"; L <= -0.20 and U < 0: "not eliminated"; L > -0.20 and U < 0:
              "eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)"; otherwise
              "inconclusive". A bound within 1e-9 of a threshold is not past it (L must exceed -0.20 by more
              than 1e-9, U must be below -1e-9).
  capacity    the "testing capacity" statement (the SAE acts as testing capacity, consistent with R4) holds iff
              C1 is significant and the R3 verdict is the first branch or the third (both-true) branch; under
              the third it is stated together with the residual deficit.
  trigger     Open-64 is run iff rate(GPT bb64) <= rate(GPT open8) - 0.20 on pooled point estimates
              (tolerance 1e-9, so a gap of exactly 0.20 triggers).
Everything else is descriptive: the same contrasts by kind (C1, C2, C4; GPT with an unadjusted permutation p,
Haiku without), the predictions check, the decomposition, S3 x NAME, refused submits, Haiku's rates, the drift
check against the main study (pooled and with equal item weights; no test), and S4.
Haiku has no tests (plan §4 and §5: descriptive only): its rates have Wilson and approximate clustered
intervals, its differences have T and the approximate interval, and no p-value is computed or printed for it.

--s3 <csv>: the CSV written by scripts/s3_coder.py (--out-csv) is joined to the rows on (batch, run). A run of
the rows that is absent from the CSV, or whose s3 is blank there, has S3 missing: it is left out of the S3
tables and counted in "runs without S3" per agent and arm. A CSV row that matches no row of the study's
batches, appears twice, disagrees with its row on episode or arm, or has an s3 other than 0, 1 or blank is an
error (exit 1). Without --s3 an `s3` column of the rows themselves is used if there is one (simulated rows).

--ledger <ledger.jsonl>: the scheduler's ledger (scripts/blackbox_schedule.py). Jobs are (block, order) of
blocks block1 and block2 (pilots have block `pilots` and are not read). Each counted run is tied to its job and
attempt by the container id of the job's `finished` event (its first 12 characters are the run directory's
name) in the batch the event names. First-attempt sensitivity analysis (DECISIONS D24.2): every job's outcome
is its FIRST attempt's; a job whose first attempt was excluded as an infrastructure failure (an `infra` event)
counts as a fail (NAME = 0) in place of its re-run, also when it has no counted re-run. C1, C2, C4 (C3 if
run), the R3 verdict and Haiku's differences are reported under this definition next to the primary ones,
with a table of excluded runs per agent, arm and reason (the `reason` of the `infra` events). An attempt is
opened by its `launching` or `launched` event (the scheduler writes `launching` before the launcher exists).
The ledger's status of a run must agree with its row: `ok` and `needs_regrade` need a counted row with an
accepted submission (`submitted` 1), `fail:*` a counted row without one. A `needs_regrade` event stays in the
append-only ledger after the stored submission was graded offline (DECISIONS D24.3); once the scorer's rows
count that run it is tied to its job like any other, and the report says how many such runs there are.
Errors (exit 1): a counted run that the ledger does not have; a run the ledger records as finished (ok,
needs_regrade or fail:*) without a counted row; a ledger status that disagrees with the row on whether a
submission was accepted; a counted run the ledger records as an infrastructure failure; an attempt with
status unknown:*, or with no recorded outcome; attempts that are not 1..k with every attempt before the last
an infrastructure failure; a job whose agent, arm or item differs from its run's row; dry-run events.

Zero-width intervals: when no (item, arm) cell in play has run-to-run variation (an arm at 0/n or n/n, or two
such arms), every bootstrap resample gives the same value and the percentile interval has zero width. It then
carries no sampling uncertainty; it is flagged `zero width` wherever it is printed, and the R3 line says so
when the interval of C4 is one. The clustered interval of a single arm's rate also under-covers when the rate
is near 0 or 1 (with a true rate of 0.95 and 24 runs it misses the truth about 3 times in 10); the Wilson
interval is the one to read there.

Each test and each interval starts its own generator from the seed and uses the outcomes of each (item, arm)
cell in sorted order, so every number is reproducible and does not depend on row order or on which other
tests were run. The report has no timestamps. "Reproducible" means: with the same numpy random stream. The
resamples come from numpy.random.default_rng(seed) (PCG64) through Generator.permuted and Generator.integers,
whose streams numpy does not promise to keep across versions; the numpy version and the bit generator are
written to the JSON (`meta`) and the report header. Bounds lie on a grid (steps of 1/24 with 24 runs per arm),
so another stream can move a bound by one step.

Generating model of --simulate and --power: item i has a difficulty u_i ~ Normal(0, sd^2) on the logit scale,
shared by every arm; a run of arm a on item i succeeds with probability expit(c_a + u_i), independently; c_a is
chosen so that the rate averaged over the item distribution equals the arm's nominal rate (so the nominal gap
is the expected gap). --simulate draws one such data set (4 GPT and 2 Haiku runs per item and arm) with
sd = 1; --power repeats it for two arms with 4 runs per item and 6 items (n = 24 per arm) at sd = 0 and 1.
Inside the power loop the permutation test uses 2,000 resamples, not 10^4, to keep the run short.
--simulate also draws, from random streams of their own (so the simulated outcomes do not depend on them), the
refused-submit columns, an S3 table in the coder's shape with a few runs absent or blank, and a ledger in the
scheduler's shape in which about 6% of the jobs have an excluded first attempt; they go through --s3's join
and --ledger's checks, so the dry run shows every section of the report.
"""
import argparse
import csv
import json
import math
import sys
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_naming as SN  # noqa: E402

SEED = 20261112
N_RESAMPLES = 10_000
AGENTS = SN.STUDY_AGENTS  # gpt, haiku
STUDY_TAG = "r1112"  # counted batches are named <tag>_<agent>_<arm> (SN.study_batch)
ARMS = SN.ARMS  # open8, bb8, bb64, open64
ITEMS = SN.ITEMS
KINDS = ("trap", "twopart")
KIND = {ep: SN.KIND_BY_EPISODE[ep] for ep in ITEMS}
RUNS_PER_ITEM = SN.STUDY_RUNS_PER_ITEM  # gpt 4, haiku 2
CONTRASTS = OrderedDict([("C1", ("open8", "bb8")), ("C2", ("bb64", "bb8")), ("C4", ("bb64", "open8")),
                         ("C3", ("open64", "bb64"))])
HOLM_FAMILY = ("C1", "C2")
KIND_CONTRASTS = ("C1", "C2", "C4")
ARM_LABEL = {"open8": "Open-8", "bb8": "BB-8", "bb64": "BB-64", "open64": "Open-64"}
R3_MARGIN = -0.20
R3_BOTH = "eliminated at the -0.20 margin, with a residual deficit (CI excludes 0)"  # DECISIONS D13
R3_BRANCH = {"eliminated": 1, "not eliminated": 2, R3_BOTH: 3, "inconclusive": 4}
ALPHA = 0.05  # a Holm-family contrast is significant iff its Holm-adjusted two-sided p < ALPHA
TRIGGER_GAP = 0.20
TOL = 1e-9
COUNTED_BLOCKS = ("block1", "block2")  # ledger blocks of counted runs (runorder_block1.csv, runorder_block2.csv)
S3_COLUMNS = ("run", "batch", "episode", "arm", "s3", "log")  # the columns of scripts/s3_coder.py's CSV read here
UNTESTED_AGENTS = ("haiku",)  # descriptive only (plan §4, §5): no permutation p is computed
# Plan §5 predictions: (agent, arm, kind or "all") -> (low, high), inclusive.
PREDICTED_RANGES = OrderedDict([
    (("gpt", "open8", "all"), (0.75, 0.90)), (("gpt", "bb8", "all"), (0.20, 0.50)),
    (("gpt", "bb64", "trap"), (0.70, 1.00)), (("gpt", "bb64", "twopart"), (0.40, 0.70)),
    (("haiku", "open8", "all"), (0.35, 0.65)), (("haiku", "bb8", "all"), (0.15, 0.45)),
    (("haiku", "bb64", "all"), (0.30, 0.60)),
])
# Drift check: main-study Open-8 NAME per item, (passes, runs). Source: results/cross_model_1103/rollouts.csv, rows
# with batch b1 or b2 (the hv side batch and the smoke runs left out), column hard_pass, which equals NAME on
# every main-study run (tests/test_score_naming.py). tests/test_blackbox_analysis.py recomputes these from the file.
MAIN_STUDY_NAME_BY_ITEM = {
    "gpt": OrderedDict(ep411=(3, 3), ep413=(1, 2), ep415=(3, 3), ep472=(3, 3), ep474=(1, 2), ep476=(3, 3)),
    "haiku": OrderedDict(ep411=(2, 3), ep413=(0, 2), ep415=(1, 3), ep472=(2, 3), ep474=(1, 2), ep476=(2, 3)),
}
MAIN_STUDY_NAME = {a: (sum(k for k, _ in v.values()), sum(n for _, n in v.values()))  # pooled: 14/16 and 8/16
                   for a, v in MAIN_STUDY_NAME_BY_ITEM.items()}
# --simulate
SIM_RATES = {"gpt": {"open8": 0.85, "bb8": 0.40, "bb64": 0.70, "open64": 0.88},
             "haiku": {"open8": 0.50, "bb8": 0.30, "bb64": 0.45}}
SIM_ITEM_SD = 1.0
# --power
POWER_SCENARIOS = ((0.35, ((0.85, 0.50), (0.80, 0.45), (0.75, 0.40))),
                   (0.45, ((0.90, 0.45), (0.85, 0.40), (0.80, 0.35))),
                   (0.00, ((0.60, 0.60),)))
POWER_ITEM_SDS = (0.0, 1.0)
POWER_SIMS = 2000
POWER_RESAMPLES = 2000


# ---------------------------------------------------------------------------------------------------------
# statistics

wilson = SN.wilson


def holm(pvals, m=None):
    """Holm step-down adjusted p-values. pvals: {name: p}; m: family size (default: the number given)."""
    order = sorted(pvals.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(order) if m is None else m
    out, run = {}, 0.0
    for i, (name, p) in enumerate(order):
        run = max(run, min(1.0, (m - i) * p))
        out[name] = run
    return out


def r3_decision(lo, hi, margin=R3_MARGIN):
    """Plan §1a rule on the 95% CI [L, U] = [lo, hi] of C4 = BB-64 - Open-8, as four exclusive branches.
    "L > margin" means L exceeds it by more than TOL, "U < 0" means U is below -TOL."""
    if lo is None or hi is None:
        return "not evaluable (no data)"
    above_margin, below_zero = lo > margin + TOL, hi < -TOL
    if above_margin and not below_zero:      # 1: L > -0.20 and U >= 0
        return "eliminated"
    if not above_margin and below_zero:      # 2: L <= -0.20 and U < 0
        return "not eliminated"
    if above_margin and below_zero:          # 3: L > -0.20 and U < 0 (both conditions hold, D13)
        return R3_BOTH
    return "inconclusive"                    # 4: L <= -0.20 and U >= 0


def open64_trigger(rate_bb64, rate_open8, gap=TRIGGER_GAP):
    """Plan §4: Open-64 runs iff GPT BB-64 is at least `gap` below GPT Open-8 on point estimates."""
    if rate_bb64 is None or rate_open8 is None:
        return None
    return bool(rate_bb64 <= rate_open8 - gap + TOL)


def cell_values(rows, arm, items=ITEMS, outcome="name"):
    """{item: outcomes of the arm's runs on that item, sorted descending}; items without a run are absent."""
    out = OrderedDict()
    for it in items:
        y = sorted((float(r[outcome]) for r in rows if r["arm"] == arm and r["episode"] == it), reverse=True)
        if y:
            out[it] = np.array(y)
    return out


def contrast_cells(rows, arm_a, arm_b, items=ITEMS, outcome="name"):
    """-> (cells, dropped): cells {item: (outcomes in A, outcomes in B)} for the items with runs in both arms;
    dropped = the other items."""
    a, b = cell_values(rows, arm_a, items, outcome), cell_values(rows, arm_b, items, outcome)
    cells = OrderedDict((it, (a[it], b[it])) for it in items if it in a and it in b)
    return cells, [it for it in items if it not in cells]


def statistic(cells):
    """T = mean over items of (mean of A - mean of B); None without items."""
    if not cells:
        return None
    return float(np.mean([ya.mean() - yb.mean() for ya, yb in cells.values()]))


def permuted_labels(n_a, n_b, n, rng):
    """[n, n_a + n_b] boolean arm labels (True = arm A), each row a uniform permutation with n_a True."""
    base = np.zeros(n_a + n_b, dtype=bool)
    base[:n_a] = True
    return rng.permuted(np.tile(base, (n, 1)), axis=1)


def permutation_test(cells, n=N_RESAMPLES, seed=SEED):
    """Monte Carlo within-item permutation test of T. -> {"T", "p", "n_extreme", "n_resamples", "seed"}."""
    T = statistic(cells)
    if T is None:
        return {"T": None, "p": None, "n_extreme": None, "n_resamples": n, "seed": seed}
    rng = np.random.default_rng(seed)
    total = np.zeros(n)
    for ya, yb in cells.values():
        y = np.concatenate([ya, yb])
        lab = permuted_labels(len(ya), len(yb), n, rng)
        sum_a = (lab * y).sum(1)
        total += sum_a / len(ya) - (y.sum() - sum_a) / len(yb)
    t_star = total / len(cells)
    extreme = int((np.abs(t_star) >= abs(T) - 1e-12).sum())
    return {"T": T, "p": (1 + extreme) / (1 + n), "n_extreme": extreme, "n_resamples": n, "seed": seed}


def _cluster_bootstrap(groups, n, seed):
    """Item-clustered bootstrap draws of mean over items of (mean of the first array - mean of the second, or
    the mean of the only array). groups: one tuple of 1 or 2 outcome arrays per item."""
    rng = np.random.default_rng(seed)
    k = len(groups)
    draw = rng.integers(0, k, size=(n, k))
    total = np.zeros(n)
    for i, arrays in enumerate(groups):
        val = np.zeros((n, k))
        for sign, y in zip((1.0, -1.0), arrays):
            val += sign * y[rng.integers(0, len(y), size=(n, k, len(y)))].mean(-1)
        total += ((draw == i) * val).sum(1)
    return total / k


def bootstrap_ci(cells, n=N_RESAMPLES, seed=SEED, level=0.95):
    """Approximate item-clustered percentile interval of T. cells: {item: (A, B)} or {item: outcomes} (a rate).
    -> (lo, hi), or (None, None) without items."""
    if not cells:
        return None, None
    groups = [v if isinstance(v, tuple) else (v,) for v in cells.values()]
    lo, hi = np.quantile(_cluster_bootstrap(groups, n, seed), [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def zero_width(lo, hi):
    """True when a bootstrap interval has no width: every resample gave the same value."""
    return lo is not None and hi is not None and hi - lo <= 1e-12


def rng_meta():
    """What produced the random streams (the same seed gives the same numbers only with the same stream)."""
    return {"numpy": np.__version__,
            "bit_generator": type(np.random.default_rng(0).bit_generator).__name__ + " (numpy.random.default_rng)"}


def _rate(rows, outcome="name"):
    k, n = sum(int(r[outcome] or 0) for r in rows), len(rows)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "wilson95": [lo, hi] if n else None}


def contrast(rows, arm_a, arm_b, items=ITEMS, n=N_RESAMPLES, seed=SEED, outcome="name", test=True):
    """One contrast A - B on one agent's rows: T, permutation p, approximate CI, pooled rates, dropped items.
    test=False (a descriptive difference): no permutation test is run and p is None."""
    cells, dropped = contrast_cells(rows, arm_a, arm_b, items, outcome)
    tested = bool(test)
    test = permutation_test(cells, n, seed) if tested else {"T": statistic(cells), "p": None, "n_extreme": None}
    lo, hi = bootstrap_ci(cells, n, seed)
    used = [r for r in rows if r["episode"] in cells]
    ra, rb = _rate([r for r in used if r["arm"] == arm_a], outcome), _rate([r for r in used if r["arm"] == arm_b], outcome)
    sizes = {(len(ya), len(yb)) for ya, yb in cells.values()}
    return {"a": arm_a, "b": arm_b, "T": test["T"], "p": test["p"], "n_extreme": test["n_extreme"],
            "tested": tested, "ci95": [lo, hi] if lo is not None else None,
            "ci_label": f"approximate ({len(cells)} clusters)", "ci_zero_width": zero_width(lo, hi),
            "n_resamples": n, "seed": seed, "rate_a": ra, "rate_b": rb,
            "pooled_diff": (ra["rate"] - rb["rate"]) if cells else None,
            "items_used": list(cells), "items_dropped": dropped,
            "balanced": len(sizes) == 1}  # same arm counts in every item: T is the pooled difference


# ---------------------------------------------------------------------------------------------------------
# the study

def study_rows(rows, exclude_batches=(), study_tag=None):
    """-> (rows used, {reason: rows left out}). Used: counted, agent gpt/haiku, a study arm, a study item and,
    with study_tag, a batch named `<tag>_<agent>_<arm>` (pilots, the main study, hv and smoke batches are left
    out by name). A counted row whose agent or arm is not the one its batch names is an error, and so is a row
    with status needs_regrade (the scorer keeps such a run out of its rows until it is regraded)."""
    used, out = [], Counter()
    for r in rows:
        named = SN.study_batch(r.get("batch"), study_tag) if study_tag else None
        if r.get("batch") in exclude_batches:
            out["excluded batch"] += 1
        elif study_tag and named is None:
            out[f"batch outside the study (not {study_tag}_<agent>_<arm>)"] += 1
        elif r.get("status") == SN.NEEDS_REGRADE:
            raise ValueError(f"run {r.get('run')} in batch {r.get('batch')} has status {SN.NEEDS_REGRADE}: an accepted "
                             "submission without a grade.json; regrade it and score again before the analysis")
        elif not int(r.get("counted") or 0):
            out["not counted (infrastructure failure)"] += 1
        elif study_tag and (r.get("agent"), r.get("arm")) != named:
            raise ValueError(f"run {r.get('run')} in batch {r.get('batch')} has agent {r.get('agent')}, arm "
                             f"{r.get('arm')}: not what the batch name says")
        elif r.get("agent") not in AGENTS:
            out["other agent"] += 1
        elif r.get("arm") not in ARMS:
            out["other arm"] += 1
        elif r.get("episode") not in ITEMS:
            out["other episode"] += 1
        else:
            used.append(r)
    return used, dict(sorted(out.items()))


def _sel(rows, agent=None, arm=None, kind=None, item=None):
    return [r for r in rows if (agent is None or r["agent"] == agent) and (arm is None or r["arm"] == arm)
            and (kind is None or KIND[r["episode"]] == kind) and (item is None or r["episode"] == item)]


def _arm_rate(rows, agent, arm, kind=None, n=N_RESAMPLES, seed=SEED):
    rs = _sel(rows, agent, arm, kind)
    items = [it for it in ITEMS if kind is None or KIND[it] == kind]
    out = _rate(rs)
    cells = cell_values(rs, arm, items)
    lo, hi = bootstrap_ci(cells, n, seed)
    out["cluster95"] = [lo, hi] if lo is not None else None
    out["cluster_label"] = f"approximate ({len(cells)} clusters)"
    out["cluster_zero_width"] = zero_width(lo, hi)
    out["by_item"] = {it: {"k": int(cells[it].sum()), "n": len(cells[it])} if it in cells else {"k": 0, "n": 0}
                      for it in items}
    return out


def _mean(vals):
    vals = [float(v) for v in vals if v is not None]
    return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)


def confirmatory(gpt_rows, n=N_RESAMPLES, seed=SEED):
    """The GPT contrasts on one set of GPT rows: C1 and C2 (Holm family), C4 and, if Open-64 has runs, C3.
    `significant` is set for the Holm family only (Holm-adjusted p < ALPHA) and is None for C4 and C3."""
    tests = OrderedDict()
    for name, (a, b) in CONTRASTS.items():
        if _sel(gpt_rows, arm=a) and _sel(gpt_rows, arm=b):
            tests[name] = contrast(gpt_rows, a, b, ITEMS, n, seed)
    fam = {k: tests[k]["p"] for k in HOLM_FAMILY if k in tests and tests[k]["p"] is not None}
    adj = holm(fam, m=len(HOLM_FAMILY))
    for k, t in tests.items():
        t["family"] = "holm" if k in HOLM_FAMILY else "outside the family"
        t["p_holm"] = adj.get(k)
        t["significant"] = bool(adj[k] < ALPHA) if k in adj else None
    return tests


def r3_verdict(tests, gpt_rows):
    """The R3 rule on the CI of C4 from confirmatory(); gpt_rows: the rows the contrasts were computed on."""
    c4 = tests.get("C4")
    lo, hi = (c4["ci95"] if c4 and c4["ci95"] else (None, None))
    decision = r3_decision(lo, hi)
    out = {"contrast": "C4 = bb64 - open8 (gpt)", "margin": R3_MARGIN, "ci95": [lo, hi] if lo is not None else None,
           "p": c4["p"] if c4 else None, "decision": decision, "branch": R3_BRANCH.get(decision),
           "ci_zero_width": zero_width(lo, hi), "caveat": None}
    if out["ci_zero_width"]:  # the rule is applied as written; the reader is told what the interval is
        def w(arm):
            r = _rate(_sel(gpt_rows, arm=arm))
            return f"{ARM_LABEL[arm]} {_kn(r)} {_iv(r['wilson95'])}"
        out["caveat"] = ("zero-width interval: no (item, arm) cell of the two arms has run-to-run variation, "
                         "so every bootstrap resample gives the same difference and the interval carries no "
                         "sampling uncertainty; the rule is applied as written, and the reading rests on the "
                         f"Wilson 95% intervals of the two arms: {w('bb64')}, {w('open8')}")
    return out


def testing_capacity(tests, r3):
    """The "testing capacity" statement (plan §1a, DECISIONS D24.4): it holds iff C1 is significant and the R3
    verdict is the first branch ("eliminated") or the third (both-true) branch; under the third it is stated
    together with the residual deficit. -> {"c1_significant", "r3_branch", "holds", "statement"}."""
    sig = (tests.get("C1") or {}).get("significant")
    branch = r3["branch"]
    if sig is None or branch is None:
        return {"c1_significant": sig, "r3_branch": branch, "holds": None, "statement": "not evaluable (no data)"}
    holds = bool(sig and branch in (1, 3))
    if holds and branch == 1:
        text = ('holds: C1 is significant and the R3 verdict is "eliminated" (first branch); the SAE acts as testing '
                "capacity (consistent with R4)")
    elif holds:
        text = (f'holds, with a residual deficit: C1 is significant and the R3 verdict is the both-true branch ("{R3_BOTH}"); '
                "the SAE acts as testing capacity at the -0.20 margin (consistent with R4), and a residual deficit "
                "remains: BB-64 is below Open-8 (the CI of C4 excludes 0)")
    else:
        why = ([] if sig else ["C1 is not significant"]) + ([] if branch in (1, 3) else [f'the R3 verdict is "{r3["decision"]}"'])
        text = "does not hold: " + " and ".join(why)
    return {"c1_significant": bool(sig), "r3_branch": branch, "holds": holds, "statement": text}


# ---------------------------------------------------------------------------------------------------------
# S3: the CSV of scripts/s3_coder.py, joined on (batch, run)

def read_s3_csv(path):
    """Rows of the CSV written by scripts/s3_coder.py --out-csv (cells as text). ValueError if a column this
    script reads is not there."""
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in S3_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: not a CSV of scripts/s3_coder.py (column(s) {', '.join(missing)} missing)")
        return list(reader)


def join_s3(rows, s3_rows, study_tag=None):
    """Join S3 to the scorer's rows on (batch, run). -> copies of the rows with `s3` (0, 1, or None when S3 is
    missing) and `s3_log` (the coder's `log`, or "not in the S3 CSV"). ValueError on an S3 row that matches no
    row of the study's batches (every row when study_tag is None), appears twice, disagrees with its row on
    episode or arm, or has an s3 other than 0, 1 or blank."""
    in_study = lambda r: not study_tag or SN.study_batch(r.get("batch"), study_tag) is not None
    key = lambda r: (str(r.get("batch")), str(r.get("run")))
    have = {key(r): r for r in rows if in_study(r)}
    by_key, bad = {}, []
    for s in s3_rows:
        k = key(s)
        where = "/".join(k)
        if k in by_key:
            bad.append(f"{where}: twice in the S3 CSV")
            continue
        by_key[k] = s
        r = have.get(k)
        if r is None:
            bad.append(f"{where}: no row of the study has this batch and run")
            continue
        for col in ("episode", "arm"):
            if (s.get(col) or "") != (r.get(col) or ""):
                bad.append(f"{where}: {col} {s.get(col)!r} in the S3 CSV, {r.get(col)!r} in the rows")
        if (s.get("s3") or "").strip() not in ("", "0", "1"):
            bad.append(f"{where}: s3 is {s.get('s3')!r}, not 0, 1 or blank")
    if bad:
        raise ValueError("S3 CSV: " + "; ".join(bad))
    out = []
    for r in rows:
        s = by_key.get(key(r)) if in_study(r) else None
        v = (s.get("s3") or "").strip() if s else ""
        out.append(dict(r, s3=int(v) if v else None,
                        s3_log="not in the S3 CSV" if s is None else (s.get("log") or "").strip() or "blank"))
    return out


def s3_table(rows, arms_present):
    """S3 x NAME per agent and arm over the counted runs with an S3 value; `no_s3` = the runs without one."""
    tab = OrderedDict()
    for a in AGENTS:
        for arm in arms_present:
            every = _sel(rows, a, arm)
            if not every:
                continue
            rs = [r for r in every if r.get("s3") not in (None, "")]
            c = Counter((int(float(r["s3"])), int(r["name"])) for r in rs)
            n1, n0 = c[(1, 1)] + c[(1, 0)], c[(0, 1)] + c[(0, 0)]
            why = Counter(str(r.get("s3_log") or "blank") for r in every if r.get("s3") in (None, ""))
            tab[f"{a}|{arm}"] = {"s3_1_name_1": c[(1, 1)], "s3_1_name_0": c[(1, 0)], "s3_0_name_1": c[(0, 1)],
                                 "s3_0_name_0": c[(0, 0)], "n": len(rs), "no_s3": len(every) - len(rs),
                                 "no_s3_why": dict(sorted(why.items())),
                                 "name_given_s3_1": {"k": c[(1, 1)], "n": n1, "rate": c[(1, 1)] / n1 if n1 else None,
                                                     "wilson95": list(wilson(c[(1, 1)], n1)) if n1 else None},
                                 "name_given_s3_0": {"k": c[(0, 1)], "n": n0}}
    return tab


# ---------------------------------------------------------------------------------------------------------
# the scheduler's ledger: jobs, attempts, the first-attempt sensitivity analysis

def read_ledger(path):
    """-> (events, number of non-empty lines that are not JSON objects). The scheduler skips such lines too (a
    line torn by a crash); what they would have said is caught by the checks of first_attempt()."""
    events, unreadable = [], 0
    for line in Path(path).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            obj = None
        if isinstance(obj, dict):
            events.append(obj)
        else:
            unreadable += 1
    return events, unreadable


def ledger_jobs(events, blocks=COUNTED_BLOCKS):
    """Jobs of the counted blocks from ledger events (scripts/blackbox_schedule.py: `launching`, `launched`,
    `finished`, `infra` and `gave_up` events carry block, order, agent, arm, item; the first four also attempt
    and run, the batch directory; `finished` and `infra` carry cid). A `launching` event opens an attempt just
    as `launched` does: it is written before the launcher exists, so an attempt can have it alone.
    -> ({(block, order): job}, problems). A job is
    {"block", "order", "agent", "arm", "item", "batch", "gave_up", "attempts": {k: {"infra": event or None,
    "finished": the event with a status other than unknown:*, "unknown": an unknown:* event}}}."""
    jobs, problems, dry = OrderedDict(), [], 0
    for e in events:
        if e.get("block") not in blocks or e.get("event") not in ("launching", "launched", "finished", "infra", "gave_up"):
            continue
        if e.get("dry_run"):
            dry += 1
            continue
        if type(e.get("order")) is not int:
            problems.append(f"{e.get('block')}: a {e['event']} event without an order")
            continue
        where = f"{e['block']} order {e['order']}"
        j = jobs.setdefault((e["block"], e["order"]), dict(
            block=e["block"], order=e["order"], agent=e.get("agent"), arm=e.get("arm"), item=e.get("item"),
            batch=None, gave_up=False, attempts=OrderedDict()))
        if (e.get("agent"), e.get("arm"), e.get("item")) != (j["agent"], j["arm"], j["item"]):
            problems.append(f"{where}: its events disagree on agent, arm or item")
        if e["event"] == "gave_up":
            j["gave_up"] = True
            continue
        if type(e.get("attempt")) is not int:
            problems.append(f"{where}: a {e['event']} event without an attempt number")
            continue
        if e.get("run"):
            if j["batch"] not in (None, e["run"]):
                problems.append(f"{where}: its events name two run directories ({j['batch']}, {e['run']})")
            j["batch"] = e["run"]
        a = j["attempts"].setdefault(e["attempt"], {"infra": None, "finished": None, "unknown": None})
        kind = "unknown" if e["event"] == "finished" and str(e.get("status", "")).startswith("unknown:") else e["event"]
        if kind in ("infra", "finished"):
            if a[kind] is not None:
                problems.append(f"{where} attempt {e['attempt']}: two {kind} events")
            a[kind] = e
        elif kind == "unknown":
            a["unknown"] = e
    if dry:
        problems.append(f"{dry} dry-run event(s) in blocks {', '.join(blocks)}: this is not the ledger of real runs")
    return jobs, problems


def first_attempt(rows, events, exclude_batches=(), study_tag=None, uncounted=()):
    """Tie the counted rows to the ledger's jobs and build the rows of the first-attempt sensitivity analysis.

    rows: the counted study rows (study_rows). uncounted: the uncounted rows of the same batches (for a note).
    -> {"rows": one row per job with a recorded first attempt (the job's counted row, or a NAME = 0 row when
    the first attempt was an infrastructure failure), "runs": {"batch/run": {block, order, attempt}},
    "excluded": the infra events, "first_infra": the jobs whose first attempt is one, "jobs": number of jobs
    with a recorded first attempt, "regraded": the counted runs the ledger records as needs_regrade,
    "uncounted_not_in_ledger"}. ValueError with every problem found (see the module docstring)."""
    jobs, problems = ledger_jobs(events)
    cid = lambda x: str(x)[:SN.CID_LEN]
    counted = {(str(r["batch"]), cid(r["run"])): r for r in rows}
    runs, sens, excluded, first_infra, infra_keys, recorded, regraded = OrderedDict(), [], [], [], set(), set(), []
    for (block, order), j in jobs.items():
        where = f"{block} order {order}"
        if j["batch"] in exclude_batches:
            continue
        if j["agent"] not in AGENTS or j["arm"] not in ARMS or j["item"] not in ITEMS:
            problems.append(f"{where}: agent {j['agent']}, arm {j['arm']}, item {j['item']} is not a job of the study")
            continue
        if study_tag and j["batch"] is not None and SN.study_batch(j["batch"], study_tag) != (j["agent"], j["arm"]):
            problems.append(f"{where}: its run directory {j['batch']} is not {study_tag}_{j['agent']}_{j['arm']}")
            continue
        ks = sorted(j["attempts"])
        if ks != list(range(1, len(ks) + 1)):
            problems.append(f"{where}: its attempts are {ks}, not 1..{len(ks)}")
            continue
        outcome, reason_of = {}, {}  # attempt -> "infra" or the counted row; attempt -> reason of its infra event
        for k in ks:
            a, at = j["attempts"][k], f"{where} attempt {k}"
            if a["infra"] is not None and a["finished"] is not None:
                problems.append(f"{at}: both an infra and a finished event")
            elif a["infra"] is not None:
                e = a["infra"]
                reason_of[k] = str(e.get("reason") or "no reason recorded")
                excluded.append(dict(block=block, order=order, attempt=k, agent=j["agent"], arm=j["arm"],
                                     item=j["item"], reason=reason_of[k], cid=cid(e["cid"]) if e.get("cid") else None))
                if e.get("cid"):
                    infra_keys.add((str(j["batch"]), cid(e["cid"])))
                    if (str(j["batch"]), cid(e["cid"])) in counted:
                        problems.append(f"{at}: the ledger records run {j['batch']}/{cid(e['cid'])} as an infrastructure "
                                        f"failure ({reason_of[k]}) but the rows count it")
                outcome[k] = "infra"
            elif a["finished"] is not None:
                e = a["finished"]
                status, key = str(e.get("status")), (str(j["batch"]), cid(e.get("cid")))
                recorded.add(key)
                accepted = status in ("ok", SN.NEEDS_REGRADE)  # the ledger says a submission was accepted
                if k != ks[-1]:
                    problems.append(f"{at}: recorded as {status}, yet attempt {k + 1} exists")
                elif not accepted and not status.startswith("fail:"):
                    problems.append(f"{at}: status {status} is not one this analysis knows (ok, {SN.NEEDS_REGRADE}, fail:*)")
                elif key not in counted:
                    problems.append(f"{at}: the ledger records run {'/'.join(key)} as {status} but the rows have no "
                                    "counted run of that batch and name"
                                    + (" (grade the stored submission offline, then score again)"
                                       if status == SN.NEEDS_REGRADE else ""))
                elif accepted != bool(int(counted[key].get("submitted") or 0)):
                    problems.append(f"{at}: the ledger records run {'/'.join(key)} as {status}, but its row has "
                                    + ("no accepted submission" if accepted else "an accepted submission")
                                    + f" (status {counted[key].get('status')})")
                elif key in runs:
                    problems.append(f"{at}: run {'/'.join(key)} is recorded for two jobs")
                elif (counted[key]["agent"], counted[key]["arm"], counted[key]["episode"]) != (j["agent"], j["arm"], j["item"]):
                    r = counted[key]
                    problems.append(f"{at}: job {j['agent']} {j['arm']} {j['item']}, but run {'/'.join(key)} is "
                                    f"{r['agent']} {r['arm']} {r['episode']} in the rows")
                else:
                    runs[key] = dict(block=block, order=order, attempt=k)
                    outcome[k] = counted[key]
                    if status == SN.NEEDS_REGRADE:  # graded offline since: the rows count it
                        regraded.append("/".join(key))
            elif a["unknown"] is not None:
                problems.append(f"{at}: status {a['unknown'].get('status')} is not resolved")
            else:
                problems.append(f"{at}: started, with no finished or infra event (still running, or the scheduler "
                                "has to be started again to record it)")
        if outcome.get(1) == "infra":  # an excluded first attempt: the job is a fail under this definition
            first_infra.append(dict(block=block, order=order, agent=j["agent"], arm=j["arm"], item=j["item"],
                                    reason=reason_of[1], counted_rerun=isinstance(outcome.get(ks[-1]), dict)))
            sens.append(OrderedDict(run=f"{block}-o{order:03d}-a1", batch=j["batch"], agent=j["agent"], arm=j["arm"],
                                    episode=j["item"], kind=KIND[j["item"]], counted=1, name=0,
                                    status="first attempt excluded (infrastructure failure)"))
        elif 1 in outcome:
            sens.append(outcome[1])
    for key, r in counted.items():
        if key not in recorded and key not in infra_keys:  # a run the ledger has is reported with its job
            problems.append(f"counted run {'/'.join(key)} ({r['agent']} {r['arm']} {r['episode']}): the ledger has no "
                            f"finished event for it in blocks {', '.join(COUNTED_BLOCKS)}")
    if problems:
        raise ValueError("ledger: " + "; ".join(problems))
    return {"rows": sens, "runs": OrderedDict(("/".join(k), v) for k, v in runs.items()), "excluded": excluded,
            "first_infra": first_infra, "jobs": len(sens), "regraded": regraded,
            "uncounted_not_in_ledger": sorted("/".join(k) for k in {(str(r.get("batch")), cid(r.get("run"))) for r in uncounted}
                                              - infra_keys)}


def sensitivity(rows, events, n=N_RESAMPLES, seed=SEED, exclude_batches=(), study_tag=None, uncounted=()):
    """The first-attempt sensitivity analysis (module docstring) on the counted study rows and the ledger's
    events: the GPT contrasts with the Holm family, the R3 verdict, the testing-capacity statement and Haiku's
    differences under the first-attempt definition, the counted runs' jobs, and the excluded runs."""
    fa = first_attempt(rows, events, exclude_batches, study_tag, uncounted)
    sens = fa["rows"]
    gpt = _sel(sens, "gpt")
    tests = confirmatory(gpt, n, seed)
    r3 = r3_verdict(tests, gpt)
    by_reason = Counter((x["agent"], x["arm"], x["reason"]) for x in fa["excluded"])
    firsts = Counter((x["agent"], x["arm"], x["reason"]) for x in fa["excluded"] if x["attempt"] == 1)
    return {
        "definition": "every job's outcome is its first attempt's; a job whose first attempt was excluded as an "
                      "infrastructure failure counts as a fail (NAME = 0) in place of its re-run",
        "blocks": list(COUNTED_BLOCKS), "jobs": fa["jobs"], "runs": fa["runs"],
        "counted_runs_by_attempt": {str(k): v for k, v in sorted(Counter(v["attempt"] for v in fa["runs"].values()).items())},
        "first_attempt_infra": fa["first_infra"], "equals_primary": not fa["first_infra"],
        "rates": {a: {arm: _rate(_sel(sens, a, arm)) for arm in ARMS if _sel(sens, a, arm)} for a in AGENTS},
        "contrasts": tests, "r3": r3, "testing_capacity": testing_capacity(tests, r3),
        "haiku_contrasts": {c: contrast(_sel(sens, "haiku"), *CONTRASTS[c], items=ITEMS, n=n, seed=seed, test=False)
                            for c in KIND_CONTRASTS
                            if _sel(sens, "haiku", CONTRASTS[c][0]) and _sel(sens, "haiku", CONTRASTS[c][1])},
        "excluded": [{"agent": a, "arm": arm, "reason": why, "runs": k, "first_attempts": firsts[(a, arm, why)]}
                     for (a, arm, why), k in sorted(by_reason.items(), key=lambda kv: (AGENTS.index(kv[0][0]),
                                                                                     ARMS.index(kv[0][1]), kv[0][2]))],
        "excluded_runs": fa["excluded"], "regraded_offline": fa["regraded"],
        "uncounted_not_in_ledger": fa["uncounted_not_in_ledger"]}


def refusal_table(rows, arms_present):
    """Refused submits per agent and arm from the scorer's columns `submit_refused` and `submit_keys_refused`
    (scripts/score_naming.py); None when no row has the first column."""
    if not any("submit_refused" in r for r in rows):
        return None
    tab = OrderedDict()
    no_sub = lambda rs: sum(not int(r.get("submitted") or 0) for r in rs)
    for a in AGENTS:
        for arm in arms_present:
            rs = _sel(rows, a, arm)
            if not rs:
                continue
            known = [r for r in rs if r.get("submit_refused") is not None]
            ref = [r for r in known if int(r["submit_refused"]) >= 1]
            keys = [r for r in ref if r.get("submit_keys_refused") is not None and int(r["submit_keys_refused"]) == 1]
            tab[f"{a}|{arm}"] = {"n": len(rs), "no_log": len(rs) - len(known), "refused_runs": len(ref),
                                 "refused_no_submission": no_sub(ref), "keys_runs": len(keys),
                                 "keys_no_submission": no_sub(keys),
                                 "keys_unknown": sum(r.get("submit_keys_refused") is None for r in ref)}
    return tab


def drift_check(rates):
    """Fresh Open-8 against the main study, per agent: pooled rates, and the mean over items of the per-item
    rate (equal item weights) in both. Descriptive: no test. An item without a fresh run is left out of both
    means and named."""
    out = {}
    for a, (k0, n0) in MAIN_STUDY_NAME.items():
        r = rates[a].get("open8")
        if not r or not r["n"]:
            continue
        main = MAIN_STUDY_NAME_BY_ITEM[a]
        items = [it for it in ITEMS if r["by_item"][it]["n"]]
        fresh_mean = sum(r["by_item"][it]["k"] / r["by_item"][it]["n"] for it in items) / len(items)
        main_mean = sum(main[it][0] / main[it][1] for it in items) / len(items)
        out[a] = {"fresh": {"k": r["k"], "n": r["n"], "rate": r["rate"], "wilson95": r["wilson95"]},
                  "main_study": {"k": k0, "n": n0, "rate": k0 / n0, "wilson95": list(wilson(k0, n0))},
                  "difference": r["rate"] - k0 / n0,
                  "equal_item_weight": {
                      "fresh": fresh_mean, "main_study": main_mean, "difference": fresh_mean - main_mean,
                      "items": items, "items_without_fresh_run": [it for it in ITEMS if it not in items],
                      "main_study_all_items": sum(k / n for k, n in main.values()) / len(main),
                      "fresh_by_item": {it: dict(r["by_item"][it]) for it in ITEMS},
                      "main_study_by_item": {it: {"k": main[it][0], "n": main[it][1]} for it in ITEMS}}}
    return out


def analyse(rows, n=N_RESAMPLES, seed=SEED, exclude_batches=(), study_tag=None, s3=None, ledger=None):
    """The whole analysis on score_naming rows. -> a JSON-serialisable dict with every number.
    study_tag: keep only the rows of that study's batches (see study_rows); None keeps every batch.
    s3: the rows of the S3 coder's CSV (read_s3_csv), joined on (batch, run); None uses an `s3` column of the
    rows if there is one. ledger: the scheduler's events (read_ledger) for the first-attempt sensitivity
    analysis; None leaves it out. ValueError on anything join_s3, first_attempt or study_rows refuses."""
    all_rows = list(rows)
    if s3 is not None:
        all_rows = join_s3(all_rows, s3, study_tag)
    rows, left_out = study_rows(all_rows, exclude_batches, study_tag)
    arms_present = [a for a in ARMS if _sel(rows, arm=a)]
    res = OrderedDict()
    res["meta"] = dict({"seed": seed, "n_resamples": n, "outcome": "name", "items": list(ITEMS), "kind": KIND,
                        "naming_source": SN.NAMING_SOURCE, "alpha": ALPHA, "tolerance": TOL}, **rng_meta())
    res["input"] = {"rows_given": len(all_rows), "rows_used": len(rows), "left_out": left_out,
                    "study_tag": study_tag, "batches": sorted({str(r.get("batch")) for r in rows}),
                    "overfull_cells": SN.overfull_cells(rows),
                    "design": {a: {arm: {it: len(_sel(rows, a, arm, item=it)) for it in ITEMS}
                                   for arm in arms_present} for a in AGENTS},
                    "design_deviations": [
                        f"{a} {arm} {it}: {len(_sel(rows, a, arm, item=it))} runs (planned {RUNS_PER_ITEM[a]})"
                        for a in AGENTS for arm in arms_present for it in ITEMS
                        if _sel(rows, a, arm) and len(_sel(rows, a, arm, item=it)) != RUNS_PER_ITEM[a]]}
    res["rates"] = {a: {arm: dict(_arm_rate(rows, a, arm, None, n, seed),
                                  by_kind={k: _arm_rate(rows, a, arm, k, n, seed) for k in KINDS})
                        for arm in arms_present if _sel(rows, a, arm)} for a in AGENTS}

    gpt = _sel(rows, "gpt")
    tests = confirmatory(gpt, n, seed)
    res["confirmatory"] = {"agent": "gpt", "contrasts": tests, "holm_family": list(HOLM_FAMILY),
                           "holm_m": len(HOLM_FAMILY), "alpha": ALPHA}
    res["r3"] = r3_verdict(tests, gpt)
    res["testing_capacity"] = testing_capacity(tests, res["r3"])
    rate = lambda arm: (res["rates"]["gpt"].get(arm) or {}).get("rate")
    trig = open64_trigger(rate("bb64"), rate("open8"))
    res["open64_trigger"] = {"rate_gpt_bb64": rate("bb64"), "rate_gpt_open8": rate("open8"), "gap": TRIGGER_GAP,
                             "threshold": None if rate("open8") is None else rate("open8") - TRIGGER_GAP,
                             "triggered": trig}

    res["first_attempt"] = None
    if ledger is not None:
        uncounted = [r for r in all_rows if not int(r.get("counted") or 0) and r.get("batch") not in exclude_batches
                     and (not study_tag or SN.study_batch(r.get("batch"), study_tag) is not None)]
        res["first_attempt"] = sensitivity(rows, ledger, n, seed, exclude_batches, study_tag, uncounted)

    res["by_kind"] = {}
    for a in AGENTS:  # GPT: pre-registered secondaries; Haiku: descriptive differences, no test
        rs = _sel(rows, a)
        res["by_kind"][a] = {k: {c: contrast(rs, *CONTRASTS[c], items=[it for it in ITEMS if KIND[it] == k], n=n, seed=seed,
                                             test=a not in UNTESTED_AGENTS)
                                 for c in KIND_CONTRASTS if _sel(rs, arm=CONTRASTS[c][0]) and _sel(rs, arm=CONTRASTS[c][1])}
                             for k in KINDS}
    res["haiku_contrasts"] = {c: contrast(_sel(rows, "haiku"), *CONTRASTS[c], items=ITEMS, n=n, seed=seed, test=False)
                              for c in KIND_CONTRASTS
                              if _sel(rows, "haiku", CONTRASTS[c][0]) and _sel(rows, "haiku", CONTRASTS[c][1])}

    def obs(agent, arm, kind):
        r = (res["rates"][agent].get(arm) or {})
        r = r if kind == "all" else (r.get("by_kind") or {}).get(kind) or {}
        return r.get("rate"), r.get("k"), r.get("n")
    ranges = []
    for (agent, arm, kind), (lo_, hi_) in PREDICTED_RANGES.items():
        rate_, k_, n_ = obs(agent, arm, kind)
        ranges.append({"agent": agent, "arm": arm, "kind": kind, "predicted": [lo_, hi_], "k": k_, "n": n_,
                       "observed": rate_, "holds": None if rate_ is None else bool(lo_ - TOL <= rate_ <= hi_ + TOL)})
    orders = []
    t_, tw_ = obs("gpt", "bb8", "trap")[0], obs("gpt", "bb8", "twopart")[0]
    orders.append({"prediction": "gpt bb8: trap rate above two-part rate", "left": t_, "right": tw_,
                   "holds": None if t_ is None or tw_ is None else bool(t_ > tw_ + TOL)})
    for agent in AGENTS:
        base = obs(agent, "open8", "trap")[0]
        for arm in ("bb8", "bb64"):
            v = obs(agent, arm, "trap")[0]
            orders.append({"prediction": f"{agent} {arm}: trap rate >= open8 trap rate", "left": v, "right": base,
                           "holds": None if v is None or base is None else bool(v >= base - TOL)})
    res["predictions"] = {"ranges": ranges, "orders": orders}

    agg, agg_kind = SN.aggregate(rows, ("agent", "arm")), SN.aggregate(rows, ("agent", "arm", "kind"))
    res["decomposition"] = OrderedDict((f"{a}|{arm}", agg[(a, arm)]) for a in AGENTS for arm in ARMS if (a, arm) in agg)
    res["decomposition_by_kind"] = OrderedDict((f"{a}|{arm}|{k}", agg_kind[(a, arm, k)]) for a in AGENTS for arm in ARMS
                                               for k in KINDS if (a, arm, k) in agg_kind)

    has_s3 = s3 is not None or any(r.get("s3") not in (None, "") for r in rows)
    res["s3"] = s3_table(rows, arms_present) if has_s3 else None
    res["s3_source"] = "S3 CSV joined on (batch, run)" if s3 is not None else "the rows' own s3 column" if has_s3 else None
    res["submit_refusals"] = refusal_table(rows, arms_present)
    res["drift"] = drift_check(res["rates"])

    res["s4"] = {}
    for a in AGENTS:
        for arm in arms_present:
            rs = _sel(rows, a, arm)
            if not rs:
                continue
            cell = {"n": len(rs)}
            for key in ("pq_hard", "pq_used", "usd", "tokens_in", "tokens_out", "wall_min"):
                m, k = _mean(r.get(key) for r in rs)
                cell[key] = {"mean": m, "n": k}
            cell["usd_total"] = sum(float(r["usd"]) for r in rs if r.get("usd") is not None)
            res["s4"][f"{a}|{arm}"] = cell
    return res


# ---------------------------------------------------------------------------------------------------------
# report

def _f(x, d=3, signed=False):
    if x is None:
        return "n/a"
    return f"{x:+.{d}f}" if signed else f"{x:.{d}f}"


def _kn(r):
    return "n/a" if not r or not r.get("n") else f"{r['k']}/{r['n']} = {r['rate']:.2f}"


def _iv(pair, signed=False, d=2):
    return "n/a" if not pair else f"[{_f(pair[0], d, signed)}, {_f(pair[1], d, signed)}]"


ZERO_WIDTH = " (zero width)"
ZERO_WIDTH_NOTE = ("An interval marked `zero width` comes from cells with no run-to-run variation: every bootstrap "
                   "resample gives the same value, so the interval carries no sampling uncertainty.")
MISSING_NOTE = ("Missing runs: nothing is imputed. T is the mean over items of the within-item rate differences on the "
                "runs present. An item with no counted run in one of the two arms of a contrast is dropped from that "
                "contrast and named under its table, and the A and B columns of a contrast pool the items it uses. The "
                "rates table, the Open-64 trigger and the predictions check use pooled rates (k/n over the counted "
                "runs of an arm).")
RULES_NOTE = (f"Significance: only the Holm family (C1, C2) is labelled; a contrast in it is significant iff its "
              f"Holm-adjusted two-sided permutation p is below {ALPHA:.2f}. C4, C3, the by-kind contrasts and Haiku are "
              "never labelled significant or not. R3 rule on the interval [L, U] of C4: L > -0.20 and U >= 0: "
              f'"eliminated"; L <= -0.20 and U < 0: "not eliminated"; L > -0.20 and U < 0: "{R3_BOTH}"; otherwise '
              '"inconclusive". Tolerance 1e-9: a bound within 1e-9 of a threshold is not past it (L must exceed '
              "-0.20 by more than 1e-9, U must be below -1e-9); the Open-64 trigger and the prediction ranges "
              "count a value within 1e-9 of their bound as meeting it.")
assert TOL == 1e-9  # the text above states it
CONTRAST_HEAD = ("| Contrast | A − B | A | B | T | approx. 95% CI (item-clustered bootstrap) | permutation p | Holm p | "
                 "significant (Holm p < 0.05) | items |\n|---|---|---|---|---|---|---|---|---|---|")
KIND_HEAD = ("| Kind, contrast | A − B | A | B | T | approx. 95% CI (item-clustered bootstrap) | "
             "permutation p (unadjusted) | items |\n|---|---|---|---|---|---|---|---|")
PLAIN_HEAD = ("| Contrast | A − B | A | B | T | approx. 95% CI (item-clustered bootstrap) | items |\n"
              "|---|---|---|---|---|---|---|")


def _lead(label, t):
    return [label, f"{ARM_LABEL[t['a']]} − {ARM_LABEL[t['b']]}", _kn(t["rate_a"]), _kn(t["rate_b"]), _f(t["T"], 3, True),
            f"{_iv(t['ci95'], True)}{ZERO_WIDTH if t.get('ci_zero_width') else ''}"]


def _items(t):
    return f"{len(t['items_used'])}{' (dropped: ' + ', '.join(t['items_dropped']) + ')' if t['items_dropped'] else ''}"


def _line(cells):
    return "| " + " | ".join(cells) + " |"


def _contrast_row(label, t):
    """A GPT contrast with its permutation p, Holm p and, in the Holm family only, the significance label."""
    sig = t.get("significant")
    return _line(_lead(label, t) + [_f(t["p"], 4), _f(t.get("p_holm"), 4) if t.get("p_holm") is not None else "—",
                                    "—" if sig is None else "yes" if sig else "no", _items(t)])


def _kind_row(label, t):
    """A GPT by-kind contrast: unadjusted permutation p, no Holm p, no significance label."""
    return _line(_lead(label, t) + [_f(t["p"], 4), _items(t)])


def _plain_row(label, t):
    """A descriptive difference (Haiku): no p-value column at all."""
    return _line(_lead(label, t) + [_items(t)])


def _dropped(named):
    """The line that names the items dropped from contrasts; named: (label, contrast) pairs."""
    d = [f"{label}: {', '.join(t['items_dropped'])}" for label, t in named if t["items_dropped"]]
    return ["", "Items dropped from a contrast (no counted run in one of its two arms): " + "; ".join(d) + "."] if d else []


def _r3_line(r3, what=""):
    return (f"**R3 rule (C4, margin {R3_MARGIN:+.2f}){what}:** CI {_iv(r3['ci95'], True, 3)}, p {_f(r3['p'], 4)} → "
            f"**{r3['decision']}**." + (f" Caveat ({r3['caveat']})." if r3.get("caveat") else ""))


def _capacity_line(tc, tests, what=""):
    c1 = tests.get("C1")
    sig = ("not evaluable" if tc["c1_significant"] is None else
           f"{'yes' if tc['c1_significant'] else 'no'} (Holm p {_f(c1['p_holm'], 4)})")
    branch = {1: 'first branch ("eliminated")', 2: 'second branch ("not eliminated")',
              3: "third branch (both-true: eliminated at the -0.20 margin, with a residual deficit)",
              4: 'fourth branch ("inconclusive")'}.get(tc["r3_branch"], "not evaluable")
    return (f'**Testing capacity{what}** (the statement needs C1 significant and the R3 verdict "eliminated" or the '
            f"both-true branch): C1 significant: {sig}; R3 verdict: {branch} → **{tc['statement']}**.")


def render_md(res, title="No-SAE study: analysis"):
    m = res["meta"]
    L = [f"# {title}", "",
         f"Outcome NAME. Monte Carlo within-item permutation tests and item-clustered bootstrap intervals, "
         f"{m['n_resamples']} resamples each, seed {m['seed']}, numpy {m.get('numpy', 'n/a')}, bit generator "
         f"{m.get('bit_generator', 'n/a')} (the same seed gives the same numbers only with the same numpy random "
         "stream). Bootstrap intervals are approximate (few clusters). The clustered interval of a single arm's "
         "rate under-covers when the rate is near 0 or 1, and has zero width when every run of the arm has the "
         "same outcome: read the Wilson interval there. Haiku is descriptive only: no test is run for it.", ""]
    over = res["input"].get("overfull_cells") or []
    if over:
        L += [f"**ERROR: {len(over)} cell(s) have more counted runs than planned: " + "; ".join(over) + ". Runs from "
              "outside the study, or a re-run of a counted run, are pooled in. The numbers below are not the study's "
              "results.**", ""]
    L += [MISSING_NOTE, "", RULES_NOTE, ""]
    tag = res["input"].get("study_tag")
    L += ["## Input", "",
          f"{res['input']['rows_used']} counted study runs of {res['input']['rows_given']} rows"
          + ("; left out: " + ", ".join(f"{v} {k}" for k, v in res["input"]["left_out"].items()) if res["input"]["left_out"] else "")
          + ".", "",
          "Batches used: " + (", ".join(res["input"]["batches"]) or "none")
          + (f" (rule: named {tag}_<agent>_<arm>)." if tag else " (no batch-name rule applied)."), ""]
    if res["input"]["design_deviations"]:
        L += ["Cells that differ from the planned runs per item: " + "; ".join(res["input"]["design_deviations"]) + ".", ""]
    else:
        L += ["Every arm that was run has the planned number of runs in every item.", ""]

    L += ["## Rates by agent and arm", "",
          "| Agent | Arm | NAME | Wilson 95% | approx. clustered 95% | traps | two-part | per item (" + ", ".join(ITEMS) + ") |",
          "|---|---|---|---|---|---|---|---|"]
    for a in AGENTS:
        for arm, r in res["rates"][a].items():
            L.append(f"| {a} | {ARM_LABEL[arm]} | {_kn(r)} | {_iv(r['wilson95'])} | {_iv(r['cluster95'])}"
                     f"{' (zero width; read the Wilson interval)' if r.get('cluster_zero_width') else ''} | "
                     f"{_kn(r['by_kind']['trap'])} | {_kn(r['by_kind']['twopart'])} | "
                     + " ".join(f"{v['k']}/{v['n']}" for v in r["by_item"].values()) + " |")

    c = res["confirmatory"]["contrasts"]
    family = lambda k: "Holm family" if k in HOLM_FAMILY else "outside the family"
    L += ["", "## Confirmatory tests (GPT)", "", CONTRAST_HEAD]
    for k, t in c.items():
        L.append(_contrast_row(f"{k} ({family(k)})", t))
    if "C3" not in c:
        L.append("| C3 (outside the family) | Open-64 − BB-64 | not run | | | | | | | |")
    L += _dropped(c.items())
    if any(t.get("ci_zero_width") for t in c.values()):
        L += ["", ZERO_WIDTH_NOTE]
    unbalanced = [k for k, t in c.items() if not t["balanced"]]
    if unbalanced:
        L += ["", "Unbalanced cells in " + ", ".join(unbalanced) + ": T is the mean of within-item differences and "
              "differs from the difference of pooled rates."]
    tr = res["open64_trigger"]
    L += ["", _r3_line(res["r3"]), "", _capacity_line(res["testing_capacity"], c), "",
          f"**Open-64 trigger:** GPT BB-64 rate {_f(tr['rate_gpt_bb64'], 4)}, GPT Open-8 rate {_f(tr['rate_gpt_open8'], 4)}, "
          f"threshold {_f(tr['threshold'], 4)} → "
          + ("not evaluable" if tr["triggered"] is None else "**triggered**" if tr["triggered"] else "**not triggered**") + "."]

    fa = res.get("first_attempt")
    L += ["", "## First-attempt sensitivity analysis (infrastructure re-runs)", ""]
    if fa is None:
        L += ["Not computed: no ledger was given (--ledger)."]
    else:
        L += [f"Definition: {fa['definition']}. A job with an excluded first attempt and no counted re-run also counts "
              f"as a fail, so its cell then has one run more than in the primary analysis. Jobs are the (block, order) "
              f"entries of blocks {', '.join(fa['blocks'])} in the scheduler's ledger; pilots are not read.", "",
              f"{len(fa['runs'])} counted runs are tied to their job by container id; {fa['jobs']} jobs have a recorded "
              "first attempt. Counted runs by attempt number: "
              + (", ".join(f"attempt {k}: {v}" for k, v in fa["counted_runs_by_attempt"].items()) or "none") + "."
              + (" Counted runs that the ledger records as needs_regrade (an accepted submission that the container "
                 f"did not grade; graded offline since): {len(fa['regraded_offline'])} ("
                 + ", ".join(fa["regraded_offline"]) + ")." if fa.get("regraded_offline") else "")
              + (f" {res['input']['ledger_unreadable_lines']} line(s) of the ledger are not JSON and were skipped, as "
                 "the scheduler does." if res["input"].get("ledger_unreadable_lines") else ""), ""]
        if fa["equals_primary"]:
            L += ["No job had an infrastructure failure: every job's first attempt is its counted run, and the "
                  "sensitivity analysis equals the primary analysis.", ""]
        else:
            per = Counter((x["agent"], x["arm"]) for x in fa["first_attempt_infra"])
            L += [f"{len(fa['first_attempt_infra'])} job(s) have an excluded first attempt and count as fails here: "
                  + ", ".join(f"{a} {ARM_LABEL[arm]} {per[(a, arm)]}" for a in AGENTS for arm in ARMS if per[(a, arm)])
                  + f"; {sum(not x['counted_rerun'] for x in fa['first_attempt_infra'])} of them have no counted re-run.", ""]
        L += [CONTRAST_HEAD.replace("| Contrast |", "| Contrast, definition |")]
        for k, t in fa["contrasts"].items():
            if k in c:
                L.append(_contrast_row(f"{k} ({family(k)}), primary", c[k]))
            L.append(_contrast_row(f"{k} ({family(k)}), first attempt", t))
        L += _dropped([(f"{k}, first attempt", t) for k, t in fa["contrasts"].items()])
        L += ["", _r3_line(res["r3"], ", primary"), "", _r3_line(fa["r3"], ", first attempt"), "",
              _capacity_line(fa["testing_capacity"], fa["contrasts"], ", first attempt")]
        if fa["haiku_contrasts"]:
            L += ["", "Haiku differences under the two definitions (descriptive; no test, no p-value):", "",
                  PLAIN_HEAD.replace("| Contrast |", "| Contrast, definition |")]
            for k, t in fa["haiku_contrasts"].items():
                if k in res["haiku_contrasts"]:
                    L.append(_plain_row(f"{k}, primary", res["haiku_contrasts"][k]))
                L.append(_plain_row(f"{k}, first attempt", t))
        L += ["", "## Excluded runs (infrastructure failures) by agent, arm and reason", ""]
        if fa["excluded"]:
            L += ["From the ledger's `infra` events. A job can be excluded more than once (at most 2 re-runs).", "",
                  "| Agent | Arm | reason | excluded runs | of them first attempts |", "|---|---|---|---|---|"]
            L += [f"| {x['agent']} | {ARM_LABEL[x['arm']]} | {x['reason']} | {x['runs']} | {x['first_attempts']} |"
                  for x in fa["excluded"]]
        else:
            L += [f"The ledger records no infrastructure failure in blocks {', '.join(fa['blocks'])}."]
        if fa["uncounted_not_in_ledger"]:
            L += ["", f"{len(fa['uncounted_not_in_ledger'])} uncounted run director(ies) of the rows have no `infra` event "
                  "in the ledger and are not in the table: " + ", ".join(fa["uncounted_not_in_ledger"]) + "."]

    L += ["", "## By kind, GPT (pre-registered secondaries; unadjusted permutation p; 3 items each)", "", KIND_HEAD]
    L += [_kind_row(f"{k}, {cn}", t) for k in KINDS for cn, t in res["by_kind"]["gpt"][k].items()]
    L += _dropped([(f"{k}, {cn}", t) for k in KINDS for cn, t in res["by_kind"]["gpt"][k].items()])
    hk_kind = [(f"{k}, {cn}", t) for k in KINDS for cn, t in res["by_kind"]["haiku"][k].items()]
    if hk_kind:
        L += ["", "## By kind, Haiku (descriptive differences; no test, no p-value; 3 items each)", "",
              PLAIN_HEAD.replace("| Contrast |", "| Kind, contrast |")]
        L += [_plain_row(label, t) for label, t in hk_kind] + _dropped(hk_kind)
    if any(t.get("ci_zero_width") for a in AGENTS for k in KINDS for t in res["by_kind"][a][k].values()):
        L += ["", ZERO_WIDTH_NOTE]

    L += ["", "## Predictions (plan §5)", "", "| Prediction | Observed | Holds |", "|---|---|---|"]
    yn = lambda h: "no data" if h is None else "yes" if h else "no"
    for p in res["predictions"]["ranges"]:
        kind = "" if p["kind"] == "all" else f" {p['kind']}"
        L.append(f"| {p['agent']} {ARM_LABEL[p['arm']]}{kind} in [{p['predicted'][0]:.2f}, {p['predicted'][1]:.2f}] | "
                 f"{'n/a' if p['observed'] is None else str(p['k']) + '/' + str(p['n']) + ' = ' + _f(p['observed'], 3)} | {yn(p['holds'])} |")
    for p in res["predictions"]["orders"]:
        L.append(f"| {p['prediction']} | {_f(p['left'], 3)} vs {_f(p['right'], 3)} | {yn(p['holds'])} |")

    L += ["", "## Decomposition", "",
          "| Agent | Arm | runs | NAME | identified | no_extra | null false claims (S2) | plain slots named (S1) | full pass (S5) | "
          "episode pass | not submitted | naming failure buckets | hard-slot grader buckets |", "|" + "---|" * 13]
    b = lambda d: ", ".join(f"{k} {v}" for k, v in d.items()) or "—"
    for key, g in res["decomposition"].items():
        a, arm = key.split("|")
        L.append(f"| {a} | {ARM_LABEL.get(arm, arm)} | {g['n']} | {g['name']}/{g['n']} | {g['identified']}/{g['n']} | "
                 f"{g['no_extra']}/{g['n']} | {g['n_null_false']}/{g['n_null']} | {g['s1_named']}/{g['s1_n']} | "
                 f"{g['s5_full']}/{g['n']} | {g['episode_pass']}/{g['n']} | {g['n'] - g['submitted']} | "
                 f"{b(g['naming_buckets'])} | {b(g['hard_buckets'])} |")
    L += ["", "S1 and S2 count slots of submitted runs. S5 and the grader buckets use the full contract "
          "(naming, removal, kept) and are meaningful in the open arms only."]

    if res["s3"]:
        L += ["", "## S3 × NAME (descriptive)", "",
              f"S3 from {res.get('s3_source') or 'the rows'}. A counted run without an S3 value (not in the S3 CSV, or "
              "coded blank there) is left out of the four cells and counted in the last column.", "",
              "| Agent | Arm | S3=1, NAME=1 | S3=1, NAME=0 | S3=0, NAME=1 | S3=0, NAME=0 | NAME given S3=1 (Wilson 95%) | runs without S3 |",
              "|---|---|---|---|---|---|---|---|"]
        for key, t in res["s3"].items():
            a, arm = key.split("|")
            g = t["name_given_s3_1"]
            why = ", ".join(f"{k} {v}" for k, v in (t.get("no_s3_why") or {}).items())
            L.append(f"| {a} | {ARM_LABEL[arm]} | {t['s3_1_name_1']} | {t['s3_1_name_0']} | {t['s3_0_name_1']} | {t['s3_0_name_0']} | "
                     f"{(_kn(g) + ' ' + _iv(g['wilson95'])) if g['n'] else 'n/a'} | {t['no_s3']}{' (' + why + ')' if why else ''} |")
        L += ["", "Off-diagonal cells are S3=1, NAME=0 and S3=0, NAME=1."]
    else:
        L += ["", "## S3 × NAME", "", "The input has no `s3` column."]

    L += ["", '## Refused submits (the "latents" key, DECISIONS D21)', ""]
    if res.get("submit_refusals"):
        L += ["From the scorer's columns. A refused submit is a `submit` call that reached the contract check and was "
              "not accepted (log.jsonl; any contract reason: the tool log holds neither the verdict nor the message). "
              f'The keys message is "{SN.CUE_KEYS_MESSAGE}", looked for in the transcript of a run with a refused '
              "submit (white space ignored); it says that the message is somewhere in that transcript, not which "
              "call it answered. A run without a tool log, or with one that reached the tool server's size cap "
              "(later calls are then not logged), has no count and is in the last column only.", "",
              "| Agent | Arm | runs | runs with at least one refused submit | of them: no accepted submission | "
              "runs with a refused submit and the keys message | of them: no accepted submission | "
              "refused, no transcript to look in | runs without a complete tool log |", "|---|---|---|---|---|---|---|---|---|"]
        for key, t in res["submit_refusals"].items():
            a, arm = key.split("|")
            L.append(f"| {a} | {ARM_LABEL[arm]} | {t['n']} | {t['refused_runs']} | {t['refused_no_submission']} | "
                     f"{t['keys_runs']} | {t['keys_no_submission']} | {t['keys_unknown']} | {t['no_log']} |")
    else:
        L += ["The rows have no `submit_refused` column."]

    if res["haiku_contrasts"]:
        L += ["", "## Haiku (descriptive only; no family, not pooled with GPT)", "",
              "Rates with Wilson and approximate clustered intervals are in the first table. Differences with their "
              "approximate intervals, for reading only; no test is run and no p-value is computed for Haiku (plan §4, §5):", "",
              PLAIN_HEAD]
        L += [_plain_row(cn, t) for cn, t in res["haiku_contrasts"].items()] + _dropped(res["haiku_contrasts"].items())

    L += ["", "## Drift check: fresh Open-8 against the main study (descriptive; no test)", "",
          "Pooled rates, and the mean over items of the per-item rate (equal item weights: the main study ran 2 or 3 "
          "runs per item). Main-study per-item counts are constants of this script, from "
          "results/cross_model_1103/rollouts.csv (batches b1 and b2).", "",
          "| Agent | Fresh Open-8, pooled (Wilson 95%) | Main study, pooled (Wilson 95%) | Difference | "
          "Fresh Open-8, mean of item rates | Main study, mean of item rates | Difference | "
          "fresh per item | main study per item |", "|---|---|---|---|---|---|---|---|---|"]
    for a, d in res["drift"].items():
        e = d["equal_item_weight"]
        per = lambda by: " ".join(f"{by[it]['k']}/{by[it]['n']}" for it in ITEMS)
        L.append(f"| {a} | {_kn(d['fresh'])} {_iv(d['fresh']['wilson95'])} | {_kn(d['main_study'])} {_iv(d['main_study']['wilson95'])} | "
                 f"{_f(d['difference'], 3, True)} | {_f(e['fresh'], 4)} | {_f(e['main_study'], 4)} | {_f(e['difference'], 3, True)} | "
                 f"{per(e['fresh_by_item'])} | {per(e['main_study_by_item'])} |")
    gone = [f"{a}: {', '.join(d['equal_item_weight']['items_without_fresh_run'])}" for a, d in res["drift"].items()
            if d["equal_item_weight"]["items_without_fresh_run"]]
    if gone:
        L += ["", "Items without a fresh Open-8 run, left out of both means of item rates: " + "; ".join(gone) + "."]
    L += ["", "Per item in the order " + ", ".join(ITEMS) + "."]

    L += ["", "## S4: queries and cost (means over runs with a value)", "",
          "| Agent | Arm | runs | probe_query on the hard probe | probe_query in all | USD | USD total | input tokens | output tokens | wall minutes |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for key, s in res["s4"].items():
        a, arm = key.split("|")
        L.append(f"| {a} | {ARM_LABEL[arm]} | {s['n']} | {_f(s['pq_hard']['mean'], 2)} | {_f(s['pq_used']['mean'], 2)} | "
                 f"{_f(s['usd']['mean'], 3)} | {_f(s['usd_total'], 2)} | {_f(s['tokens_in']['mean'], 0)} | "
                 f"{_f(s['tokens_out']['mean'], 0)} | {_f(s['wall_min']['mean'], 1)} |")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------------------
# simulation and power

def expit(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def calibrated_intercept(rate, sd):
    """c with E[expit(c + u)] = rate for u ~ Normal(0, sd^2) (Gauss-Hermite quadrature, bisection)."""
    if sd <= 0:
        return float(math.log(rate / (1 - rate)))
    x, w = np.polynomial.hermite_e.hermegauss(80)
    w = w / w.sum()
    lo, hi = -30.0, 30.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if float((expit(mid + sd * x) * w).sum()) < rate:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def simulate_rows(seed=SEED, rates=None, item_sd=SIM_ITEM_SD, open64=False, runs_per_item=None, s3=True):
    """Simulated score_naming rows under the generating model in the module docstring (one draw)."""
    rates = rates or SIM_RATES
    runs_per_item = runs_per_item or RUNS_PER_ITEM
    rng = np.random.default_rng(seed)
    rows = []
    for agent in AGENTS:
        u = rng.normal(0.0, item_sd, len(ITEMS)) if item_sd > 0 else np.zeros(len(ITEMS))
        for arm in ARMS:
            if arm not in rates[agent] or (arm == "open64" and not open64):
                continue
            c = calibrated_intercept(rates[agent][arm], item_sd)
            for i, item in enumerate(ITEMS):
                for rep in range(runs_per_item[agent]):
                    name = int(rng.random() < expit(c + u[i]))
                    fail = None if name else str(rng.choice(["planted_none", "cue_not_identified", "extra_cue",
                                                             "null_false_claim", "no_submission"],
                                                            p=[0.55, 0.15, 0.15, 0.05, 0.10]))
                    sub = int(fail != "no_submission")
                    ident = int(name or fail in ("extra_cue", "null_false_claim"))
                    noex = int(name or fail == "null_false_claim")
                    is_open = arm.startswith("open")
                    limit = SN.ARM_SPEC[arm][1]
                    used = int(min(limit, rng.integers(limit // 2, limit + 1)))
                    grader_bucket = (fail if fail in ("planted_none", "cue_not_identified", "extra_cue")
                                     else None if not sub or is_open else "removal_short")
                    rows.append(OrderedDict(
                        run=f"sim{len(rows):04d}", batch="simulated", agent=agent,
                        model={"gpt": "gpt-6.1-terra", "haiku": "claude-haiku-5-5"}[agent], episode=item,
                        episode_id=f"{item}-{SN.ARM_SPEC[arm][0]}{'' if limit == SN.DEFAULT_PROBE_QUERY else limit}",
                        access=SN.ARM_SPEC[arm][0], pq_limit=limit, arm=arm, kind=KIND[item], hard_slot=None,
                        status="submitted" if sub else "no_submission", counted=1, submitted=sub, timeout=0,
                        name=name, identified=ident * sub, no_extra=noex * sub,
                        nulls_ok=int(sub and fail != "null_false_claim"), n_null=sub,
                        n_null_false=int(fail == "null_false_claim"), s1_named=2 * sub, s1_n=2 * sub,
                        plain_pass=2 * sub * is_open, s5_full=name * is_open, episode_pass=name * is_open,
                        score=float(name * is_open), hard_bucket=grader_bucket,
                        naming_bucket=fail, n_latent_fail=0 if is_open else 3 * sub - (0 if name else sub),
                        min_kept=None, pq_used=used, pq_hard=int(rng.integers(0, used + 1)),
                        usd=round(float(rng.gamma(20, {"gpt": 0.033, "haiku": 0.051}[agent]) * (1.5 if limit == 64 else 1)), 3),
                        usd_src="simulated", tokens_in=int(rng.integers(2_000_000, 6_000_000)),
                        tokens_out=int(rng.integers(40_000, 250_000)),
                        wall_min=round(float(rng.gamma(16, {"gpt": 0.97, "haiku": 1.34}[agent])), 2),
                        harness_status="ok",
                        **({"s3": int(rng.random() < (0.95 if name else 0.20))} if s3 else {})))
    extra = np.random.default_rng([seed, 1])  # its own stream: the draws above do not depend on these columns
    for r in rows:
        bb = r["access"] == "blackbox"
        r["submit_refused"] = int(extra.random() < (0.12 if bb else 0.03))
        r["submit_keys_refused"] = int(bool(r["submit_refused"]) and bb and extra.random() < 0.8)
    return rows


def simulate_s3(rows, seed=SEED, absent=0.02, blank=0.04):
    """The S3 coder's CSV rows for simulated rows that have an `s3` column: a few runs are absent and a few are
    coded blank (log `missing`), so the dry run shows the join and the "runs without S3" count."""
    rng = np.random.default_rng([seed, 3])
    out = []
    for r in rows:
        u = rng.random()
        if u < absent:
            continue
        ok = u >= absent + blank
        out.append({"run": r["run"], "batch": r["batch"], "episode": r["episode"], "arm": r["arm"],
                    "s3": str(r["s3"]) if ok else "", "log": "ok" if ok else "missing"})
    return out


def simulate_ledger(rows, seed=SEED, infra_share=0.06):
    """Ledger events in the scheduler's shape for simulated rows: one job per row in row order (block1; the
    Open-64 rows block2). With probability infra_share a job's first attempt is an infrastructure failure and
    the row is its second attempt, so the dry run shows a sensitivity analysis that differs from the primary."""
    rng = np.random.default_rng([seed, 2])
    events, order = [], Counter()
    for r in rows:
        block = "block2" if r["arm"] == "open64" else "block1"
        order[block] += 1
        job = dict(block=block, order=order[block], agent=r["agent"], arm=r["arm"], item=r["episode"])
        attempt = 1
        if rng.random() < infra_share:
            reason = str(rng.choice(["api_error", "no_grade", "no_container"]))
            events += [dict(job, event="launching", attempt=1, run=r["batch"]),
                       dict(job, event="launched", attempt=1, run=r["batch"]),
                       dict(job, event="infra", attempt=1, run=r["batch"], reason=reason,
                            cid=None if reason == "no_container" else f"x{r['run']}"),
                       dict(job, event="requeued")]
            attempt = 2
        events += [dict(job, event="launching", attempt=attempt, run=r["batch"]),
                   dict(job, event="launched", attempt=attempt, run=r["batch"]),
                   dict(job, event="finished", attempt=attempt, run=r["batch"], cid=r["run"],
                        status="ok" if int(r.get("submitted") or 0) else "fail:no_submission")]
    return events


def simulate_power(p_a, p_b, item_sd, n_items=len(ITEMS), per_item=RUNS_PER_ITEM["gpt"], n_sims=POWER_SIMS,
                   n_perm=POWER_RESAMPLES, seed=SEED):
    """Rejection rates of the within-item permutation test for arms with nominal rates p_a and p_b.
    -> {"power_05", "power_025", "mean_T", "n_sims", "n_perm", "se_max"}."""
    rng = np.random.default_rng(seed)
    ca, cb = calibrated_intercept(p_a, item_sd), calibrated_intercept(p_b, item_sd)
    ps, ts = np.empty(n_sims), np.empty(n_sims)
    for s in range(n_sims):
        u = rng.normal(0.0, item_sd, n_items) if item_sd > 0 else np.zeros(n_items)
        ya = (rng.random((n_items, per_item)) < expit(ca + u)[:, None]).astype(float)
        yb = (rng.random((n_items, per_item)) < expit(cb + u)[:, None]).astype(float)
        t = permutation_test(OrderedDict((i, (ya[i], yb[i])) for i in range(n_items)), n_perm,
                             int(rng.integers(0, 2**31 - 1)))
        ps[s], ts[s] = t["p"], t["T"]
    return {"p_a": p_a, "p_b": p_b, "gap": round(p_a - p_b, 10), "item_sd": item_sd, "n_per_arm": n_items * per_item,
            "power_05": float((ps <= 0.05).mean()), "power_025": float((ps <= 0.025).mean()),
            "mean_T": float(ts.mean()), "n_sims": n_sims, "n_perm": n_perm, "se_max": 0.5 / math.sqrt(n_sims)}


def power_table(n_sims=POWER_SIMS, n_perm=POWER_RESAMPLES, seed=SEED):
    """Power over POWER_SCENARIOS x POWER_ITEM_SDS. -> list of simulate_power results."""
    out = []
    for gap, pairs in POWER_SCENARIOS:
        for sd in POWER_ITEM_SDS:
            for j, (pa, pb) in enumerate(pairs):
                out.append(simulate_power(pa, pb, sd, n_sims=n_sims, n_perm=n_perm, seed=seed + 1000 * len(out) + j))
    return out


def render_power(table):
    L = ["# Power of a C1-type contrast (within-item permutation test, two-sided)", "",
         f"Design: 6 items x 4 runs per item and arm (n = 24 per arm). {table[0]['n_sims']} simulated data sets per row; "
         f"{table[0]['n_perm']} permutation resamples per test inside the loop (the analysis itself uses {N_RESAMPLES}); "
         f"Monte Carlo standard error of each power at most {table[0]['se_max']:.3f}.",
         "Generating model: item difficulty u_i ~ Normal(0, sd^2) on the logit scale, shared by both arms; a run "
         "succeeds with probability expit(c_arm + u_i); c_arm is set so that the arm's rate averaged over items is the "
         "nominal rate. sd = 0 is no between-item heterogeneity.",
         "alpha = 0.05 is the level of a single test (and of the larger p in the Holm family); alpha = 0.025 is the level "
         "the smaller p of the two-test Holm family must meet, so the Holm-adjusted power of C1 lies between the two columns.",
         "", "| gap | rate A | rate B | item sd (logit) | power at alpha 0.05 | power at alpha 0.025 | mean T |", "|---|---|---|---|---|---|---|"]
    for r in table:
        L.append(f"| {r['gap']:.2f} | {r['p_a']:.2f} | {r['p_b']:.2f} | {r['item_sd']:.1f} | {r['power_05']:.3f} | "
                 f"{r['power_025']:.3f} | {r['mean_T']:+.3f} |")
    L += ["", "| gap | mean power at alpha 0.05 | mean power at alpha 0.025 | plan §5 |", "|---|---|---|---|"]
    plan = {0.35: "about 0.6", 0.45: "about 0.8", 0.0: "size (should be at most alpha)"}
    for gap in sorted({r["gap"] for r in table}, reverse=True):
        rs = [r for r in table if r["gap"] == gap]
        L.append(f"| {gap:.2f} | {np.mean([r['power_05'] for r in rs]):.3f} | {np.mean([r['power_025'] for r in rs]):.3f} | "
                 f"{plan.get(gap, '')} |")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------------------

def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def dumps(obj):
    return json.dumps(obj, indent=1, sort_keys=True, default=_json_default) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rows", nargs="?", type=Path, help="per-run rows from scripts/score_naming.py --csv")
    ap.add_argument("--study-tag", default=STUDY_TAG,
                    help=f"use only rows of batches named <tag>_<agent>_<arm> (default {STUDY_TAG}); pilots, the main "
                         "study, hv and smoke batches are left out by name")
    ap.add_argument("--any-batch", action="store_true",
                    help="do not select rows by batch name (rows that are not from the study's run directories)")
    ap.add_argument("--exclude-batch", action="append", default=[], help="a further batch directory name to leave out")
    ap.add_argument("--s3", type=Path, metavar="CSV",
                    help="the CSV of scripts/s3_coder.py --out-csv, joined to the rows on (batch, run)")
    ap.add_argument("--ledger", type=Path, metavar="JSONL",
                    help="the scheduler's ledger.jsonl: ties each counted run to its job and attempt, and adds the "
                         "first-attempt sensitivity analysis and the table of excluded runs")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--resamples", type=int, default=N_RESAMPLES)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--simulate", action="store_true", help="dry run of the whole pipeline on simulated rows")
    ap.add_argument("--simulate-open64", action="store_true", help="with --simulate: also simulate the Open-64 arm")
    ap.add_argument("--sim-seed", type=int, default=SEED, help="seed of the simulated rows")
    ap.add_argument("--power", action="store_true", help="power simulation for a C1-type contrast")
    ap.add_argument("--power-sims", type=int, default=POWER_SIMS)
    a = ap.parse_args(argv)
    if a.power:
        table = power_table(n_sims=a.power_sims, seed=a.seed)
        meta = dict({"seed": a.seed}, **rng_meta())
        md = render_power(table) + f"\nSeed {meta['seed']}, numpy {meta['numpy']}, bit generator {meta['bit_generator']}.\n"
        payload = {"meta": meta, "power": table}
    else:
        s3 = ledger = unreadable = None
        if a.simulate:
            if a.rows or a.s3 or a.ledger:
                ap.error("--simulate takes no rows, --s3 or --ledger: it simulates all three")
            rows = simulate_rows(seed=a.sim_seed, open64=a.simulate_open64)
            s3, ledger = simulate_s3(rows, a.sim_seed), simulate_ledger(rows, a.sim_seed)
            title = (f"DRY RUN ON SIMULATED DATA (not results): nominal rates {json.dumps(SIM_RATES, sort_keys=True)}, "
                     f"item sd {SIM_ITEM_SD} on the logit scale, simulation seed {a.sim_seed}")
        elif a.rows:
            rows, title = SN.read_csv(a.rows), "No-SAE study: analysis"
        else:
            ap.error("give the rows CSV, or --simulate, or --power")
        tag = None if a.simulate or a.any_batch else a.study_tag
        try:
            if a.s3:
                s3 = read_s3_csv(a.s3)
            if a.ledger:
                ledger, unreadable = read_ledger(a.ledger)
            payload = analyse(rows, n=a.resamples, seed=a.seed, exclude_batches=tuple(a.exclude_batch), study_tag=tag,
                              s3=s3, ledger=ledger)
        except (OSError, ValueError) as e:  # a row that contradicts its batch name, the S3 CSV or the ledger
            raise SystemExit(f"error: {e}")
        payload["input"]["s3_csv"] = a.s3.name if a.s3 else None
        payload["input"]["ledger"] = a.ledger.name if a.ledger else None
        payload["input"]["ledger_unreadable_lines"] = unreadable
        if not payload["input"]["rows_used"]:
            raise SystemExit(f"error: none of the {len(rows)} rows is a counted run of the study"
                             + (f" (batches named {tag}_<agent>_<arm>; --any-batch turns the name rule off)" if tag else "")
                             + f"; left out: {payload['input']['left_out']}")
        if a.simulate:
            payload["simulated"] = {"rates": SIM_RATES, "item_sd": SIM_ITEM_SD, "seed": a.sim_seed,
                                    "open64": a.simulate_open64, "s3_csv": "simulated", "ledger": "simulated"}
        md = render_md(payload, title)
    if a.out_md:
        a.out_md.parent.mkdir(parents=True, exist_ok=True)
        a.out_md.write_text(md)
    else:
        sys.stdout.write(md)
    if a.out_json:
        a.out_json.parent.mkdir(parents=True, exist_ok=True)
        a.out_json.write_text(dumps(payload))
    over = [] if a.power else payload["input"]["overfull_cells"]
    if over:
        print(f"ERROR: {len(over)} cell(s) have more counted runs than planned (runs from outside the study, or a "
              "re-run of a counted run, are pooled in): " + "; ".join(over), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
