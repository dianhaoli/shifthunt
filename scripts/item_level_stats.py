#!/usr/bin/env python3
"""Item-level statistics on committed public data (task 3 of the 11-11 plan).

Inputs (both committed, public):
  results/blackbox_1112/rows_r1112.csv     fresh no-SAE study (108 counted runs; NAME column `name`)
  results/cross_model_1103/rollouts.csv    main study (batches b1+b2: 64 runs; column `hard_pass`)

Outputs: results/blackbox_1112/stats_items/{stats_items.md, stats_items.json}

What is computed
  1. Item-level sign-flip (randomisation) tests. The unit is the item (episode). For each item i the
     statistic is d_i = rate_A(i) - rate_B(i); the test statistic is mean_i d_i and the null
     distribution flips the sign of every d_i independently (exact enumeration, 2^n assignments).
     Items with d_i = 0 contribute nothing. The smallest attainable two-sided p with n non-zero
     items is 2 / 2^n (n=6: 0.031; n=3: 0.25); it is reported next to every p.
     Inference is to the population of items the six were drawn from, and is honest about n = 6.
  2. Run-level Fisher exact tests for the same contrasts. These treat runs as independent and
     therefore CONDITION ON THE ITEMS: they speak about these six items only.
  3. A logistic mixed model, logit P(pass) = beta_agent + u_item + v_item:agent with
     u ~ N(0, s_u^2), v ~ N(0, s_v^2), fitted by maximum likelihood with nested Gauss-Hermite
     quadrature (exact up to quadrature error; no Laplace step). From it we report the predicted
     distribution of an agent's pass rate on a NEW item: expit(beta_a + z), z ~ N(0, s_u^2 + s_v^2).
     With six items the variance components are weakly identified; a parametric bootstrap gives
     their spread. Agents at ceiling make beta_a run to large values; the fit caps |beta| at 8.

Run:  python3 scripts/item_level_stats.py           (writes the outputs)
      python3 scripts/item_level_stats.py --check   (recompute and diff against committed json)
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import optimize, stats
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / "results/blackbox_1112/rows_r1112.csv"
MAIN = ROOT / "results/cross_model_1103/rollouts.csv"
OUT = ROOT / "results/blackbox_1112/stats_items"
ITEMS = ["ep411", "ep413", "ep415", "ep472", "ep474", "ep476"]
TRAPS = ["ep411", "ep413", "ep415"]
TWOPART = ["ep472", "ep474", "ep476"]


# ----------------------------------------------------------------------------- data

def load_fresh(path=FRESH):
    """-> list of dicts {agent, arm, item, y} for counted runs."""
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["counted"] != "1":
                continue
            rows.append({"agent": r["agent"], "arm": r["arm"], "item": r["episode"], "y": int(r["name"])})
    return rows


def load_main(path=MAIN):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["batch"] not in ("b1", "b2"):
                continue
            rows.append({"agent": r["agent"], "arm": "main_open8", "item": r["episode"], "y": int(r["hard_pass"])})
    return rows


def cell_counts(rows, agent, arm, items):
    """-> {item: (passes, n)}"""
    c = {i: [0, 0] for i in items}
    for r in rows:
        if r["agent"] == agent and r["arm"] == arm and r["item"] in c:
            c[r["item"]][0] += r["y"]
            c[r["item"]][1] += 1
    return {i: tuple(v) for i, v in c.items()}


# ----------------------------------------------------------------------------- tests

def sign_flip(d):
    """Exact sign-flip test on per-item differences d. Returns dict."""
    d = np.asarray(d, float)
    nz = d[np.abs(d) > 1e-12]
    n = len(nz)
    obs = float(d.mean()) if len(d) else 0.0
    if n == 0:
        return {"mean_diff": obs, "n_items": len(d), "n_nonzero": 0, "p_two": 1.0, "p_one_greater": 1.0,
                "p_one_less": 1.0, "min_p_two": 1.0, "min_p_one": 1.0}
    sums = []
    for signs in itertools.product((1.0, -1.0), repeat=n):
        sums.append(float(np.dot(signs, nz)))
    sums = np.array(sums)
    s_obs = float(nz.sum())
    eps = 1e-9
    p_two = float(np.mean(np.abs(sums) >= abs(s_obs) - eps))
    p_g = float(np.mean(sums >= s_obs - eps))
    p_l = float(np.mean(sums <= s_obs + eps))
    return {"mean_diff": obs, "n_items": len(d), "n_nonzero": n, "p_two": p_two, "p_one_greater": p_g,
            "p_one_less": p_l, "min_p_two": min(1.0, 2.0 / 2 ** n), "min_p_one": 1.0 / 2 ** n}


def fisher_runs(ca, cb):
    """Run-level Fisher on pooled counts. ca, cb: {item: (k, n)}."""
    ka, na = sum(k for k, _ in ca.values()), sum(n for _, n in ca.values())
    kb, nb = sum(k for k, _ in cb.values()), sum(n for _, n in cb.values())
    table = [[ka, na - ka], [kb, nb - kb]]
    p_two = stats.fisher_exact(table, alternative="two-sided")[1]
    p_g = stats.fisher_exact(table, alternative="greater")[1]
    return {"a": f"{ka}/{na}", "b": f"{kb}/{nb}", "p_two": float(p_two), "p_one_greater": float(p_g)}


def contrast(name, rows_a, agent_a, arm_a, rows_b, agent_b, arm_b, items, note=""):
    ca = cell_counts(rows_a, agent_a, arm_a, items)
    cb = cell_counts(rows_b, agent_b, arm_b, items)
    use = [i for i in items if ca[i][1] > 0 and cb[i][1] > 0]
    d = [ca[i][0] / ca[i][1] - cb[i][0] / cb[i][1] for i in use]
    out = {"name": name, "note": note, "items": use,
           "per_item": {i: {"a": f"{ca[i][0]}/{ca[i][1]}", "b": f"{cb[i][0]}/{cb[i][1]}",
                            "d": round(ca[i][0] / ca[i][1] - cb[i][0] / cb[i][1], 4)} for i in use},
           "sign_flip": sign_flip(d),
           "fisher_runs": fisher_runs({i: ca[i] for i in use}, {i: cb[i] for i in use})}
    return out


# ----------------------------------------------------------------------------- mixed model

GH_X, GH_W = np.polynomial.hermite.hermgauss(20)  # for exp(-x^2)
Z = GH_X * math.sqrt(2.0)
W = GH_W / math.sqrt(math.pi)  # standard-normal weights


def _item_loglik(beta, su, sv, cells):
    """cells: list of (agent_index, k, n) for one item. Marginal log-lik of the item."""
    # inner: for each agent cell, integrate over v; outer: integrate over u
    tot = np.zeros(len(Z))  # log of product over agent cells, per outer node
    for a, k, n in cells:
        eta = beta[a] + su * Z[:, None] + sv * Z[None, :]  # outer x inner
        p = np.clip(expit(eta), 1e-300, 1 - 1e-16)
        ll = k * np.log(p) + (n - k) * np.log1p(-p)
        m = ll.max(axis=1, keepdims=True)
        inner = m[:, 0] + np.log(np.exp(ll - m) @ W)
        tot += inner
    m = tot.max()
    return m + math.log(float(np.exp(tot - m) @ W))


def fit_glmm(rows, agents, items, arm_of=None):
    """rows: dicts with agent, item, y (one arm). Returns params."""
    cells = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["agent"] in agents and r["item"] in items:
            c = cells[(r["item"], r["agent"])]
            c[0] += r["y"]
            c[1] += 1
    by_item = defaultdict(list)
    for (i, a), (k, n) in cells.items():
        by_item[i].append((agents.index(a), k, n))

    def nll(theta):
        beta = theta[: len(agents)]
        su, sv = math.exp(theta[-2]), math.exp(theta[-1])
        return -sum(_item_loglik(beta, su, sv, c) for c in by_item.values())

    best = None
    for s0 in (-2.0, 0.0):
        x0 = np.concatenate([np.zeros(len(agents)), [s0, s0]])
        bounds = [(-8, 8)] * len(agents) + [(-7, 2.5), (-7, 2.5)]
        res = optimize.minimize(nll, x0, method="L-BFGS-B", bounds=bounds)
        if best is None or res.fun < best.fun:
            best = res
    beta = best.x[: len(agents)]
    su, sv = math.exp(best.x[-2]), math.exp(best.x[-1])
    return {"agents": agents, "beta": [float(b) for b in beta], "s_item": su, "s_item_agent": sv,
            "loglik": float(-best.fun), "cells": {f"{i}|{a}": v for (i, a), v in cells.items()}}


def new_item_prediction(beta_a, su, sv, q=(0.025, 0.1, 0.5, 0.9, 0.975)):
    s = math.sqrt(su ** 2 + sv ** 2)
    quant = {f"q{int(qq * 1000) / 10:g}": float(expit(beta_a + s * stats.norm.ppf(qq))) for qq in q}
    mean = float(expit(beta_a + s * Z) @ W)
    return {"mean": mean, **quant}


def glmm_report(rows, agents, items, label, n_boot=200, seed=0):
    fit = fit_glmm(rows, agents, items)
    preds = {a: new_item_prediction(fit["beta"][j], fit["s_item"], fit["s_item_agent"])
             for j, a in enumerate(agents)}
    # parametric bootstrap of the variance components and the 95% predictive bounds
    rng = np.random.default_rng(seed)
    n_per = defaultdict(int)
    for r in rows:
        if r["agent"] in agents and r["item"] in items:
            n_per[(r["item"], r["agent"])] += 1
    boot = []
    for _ in range(n_boot):
        u = {i: rng.normal(0, fit["s_item"]) for i in items}
        fake = []
        for (i, a), n in n_per.items():
            p = expit(fit["beta"][agents.index(a)] + u[i] + rng.normal(0, fit["s_item_agent"]))
            fake += [{"agent": a, "item": i, "y": int(y)} for y in rng.random(n) < p]
        f = fit_glmm(fake, agents, items)
        boot.append((f["s_item"], f["s_item_agent"],
                     [new_item_prediction(f["beta"][j], f["s_item"], f["s_item_agent"]) for j in range(len(agents))]))
    s_tot = [math.hypot(b[0], b[1]) for b in boot]
    out = {"label": label, "fit": fit, "new_item": preds,
           "bootstrap": {"n": n_boot, "s_total_q05_q50_q95": [float(np.quantile(s_tot, q)) for q in (0.05, 0.5, 0.95)],
                         "share_s_total_below_0.1": float(np.mean(np.array(s_tot) < 0.1))}}
    for j, a in enumerate(agents):
        lo = [b[2][j]["q2.5"] for b in boot]
        hi = [b[2][j]["q97.5"] for b in boot]
        out["bootstrap"][a] = {"q2.5_bound_q05_q95": [float(np.quantile(lo, 0.05)), float(np.quantile(lo, 0.95))],
                               "q97.5_bound_q05_q95": [float(np.quantile(hi, 0.05)), float(np.quantile(hi, 0.95))]}
    return out


# ----------------------------------------------------------------------------- main

def compute(n_boot=200):
    fresh, main = load_fresh(), load_main()
    res = {"contrasts": [], "glmm": []}
    C = res["contrasts"]
    C.append(contrast("C1 GPT: Open-8 vs BB-8 (NAME)", fresh, "gpt", "open8", fresh, "gpt", "bb8", ITEMS,
                      "pre-registered contrast C1, re-tested with the item as the unit"))
    C.append(contrast("C2 GPT: BB-64 vs BB-8 (NAME)", fresh, "gpt", "bb64", fresh, "gpt", "bb8", ITEMS))
    C.append(contrast("GPT vs Haiku, fresh Open-8 (NAME)", fresh, "gpt", "open8", fresh, "haiku", "open8", ITEMS))
    C.append(contrast("GPT vs Haiku, fresh BB-64 (NAME)", fresh, "gpt", "bb64", fresh, "haiku", "bb64", ITEMS))
    C.append(contrast("GPT vs Haiku, main study (hard pass)", main, "gpt", "main_open8", main, "haiku", "main_open8", ITEMS))
    C.append(contrast("Haiku traps: BB-64 (no SAE) vs Open-8 (SAE)", fresh, "haiku", "bb64", fresh, "haiku", "open8", TRAPS,
                      "3 items: smallest attainable two-sided sign-flip p is 0.25"))
    C.append(contrast("Haiku traps: BB-8 (no SAE) vs Open-8 (SAE)", fresh, "haiku", "bb8", fresh, "haiku", "open8", TRAPS,
                      "3 items: smallest attainable two-sided sign-flip p is 0.25; budget differs from BB-64"))
    C.append(contrast("Haiku traps, main study vs fresh Open-8 (drift check)", main, "haiku", "main_open8", fresh, "haiku", "open8", TRAPS))
    C.append(contrast("Haiku two-part: BB-64 vs Open-8", fresh, "haiku", "bb64", fresh, "haiku", "open8", TWOPART))
    main_agents = ["gpt", "opus", "sonnet", "haiku"]
    res["glmm"].append(glmm_report(main, main_agents, ITEMS, "main study (b1+b2, 64 runs, Open-8, hard pass)", n_boot))
    fresh_o8 = [r for r in fresh if r["arm"] == "open8"]
    res["glmm"].append(glmm_report(fresh_o8, ["gpt", "haiku"], ITEMS, "fresh Open-8 (36 runs, NAME)", n_boot))
    fresh_bb64 = [r for r in fresh if r["arm"] == "bb64"]
    res["glmm"].append(glmm_report(fresh_bb64, ["gpt", "haiku"], ITEMS, "fresh BB-64 (36 runs, NAME)", n_boot))
    return res


def _f(p):
    return f"{p:.3f}" if p >= 0.001 else f"{p:.1e}"


def render(res):
    L = ["# Item-level statistics (task 3, 11-11)", "",
         "Generated by `scripts/item_level_stats.py` from committed public files only "
         "(`results/blackbox_1112/rows_r1112.csv`, `results/cross_model_1103/rollouts.csv`). Exploratory: none of "
         "these tests was pre-registered. The pre-registered C1 test (run-level, Holm) stands as reported in "
         "`analysis.md`; the sign-flip version below re-asks the question with the item as the unit.", "",
         "**How to read the two kinds of p.** The *sign-flip* p treats the six (or three) items as a sample of items "
         "and is the honest test for a claim about the task family; it cannot go below 2/2^n. The *run-level Fisher* p "
         "treats runs as independent and so **conditions on these items**: it supports a claim about these six "
         "episodes only.", "",
         "## Contrasts", "",
         "| Contrast | Per item (A vs B) | Mean item diff | Sign-flip p two-sided (min attainable) | one-sided A>B | Run-level Fisher A vs B, p two-sided / one-sided (conditions on items) |",
         "|---|---|---|---|---|---|"]
    for c in res["contrasts"]:
        pi = "; ".join(f"{i} {v['a']} vs {v['b']}" for i, v in c["per_item"].items())
        s, fr = c["sign_flip"], c["fisher_runs"]
        L.append(f"| {c['name']} | {pi} | {s['mean_diff']:+.3f} | {_f(s['p_two'])} ({_f(s['min_p_two'])}) | "
                 f"{_f(s['p_one_greater'])} | {fr['a']} vs {fr['b']}: {_f(fr['p_two'])} / {_f(fr['p_one_greater'])} |")
    L += ["", "Notes: " + " ".join(f"*{c['name']}*: {c['note']}." for c in res["contrasts"] if c["note"]), "",
          "## Mixed model: predicted pass rate on a new item", "",
          "logit P(pass) = beta_agent + u_item + v_item×agent, u ~ N(0, s_item²), v ~ N(0, s_item×agent²); ML fit by "
          "nested 20-point Gauss–Hermite quadrature. The predicted rate on a new item for agent a is "
          "expit(beta_a + z), z ~ N(0, s_item² + s_item×agent²). Six items identify the variance components poorly: "
          "the bootstrap columns show how far the predictive bounds move under a parametric bootstrap. |beta| is "
          "capped at 8, which binds for agents at ceiling.", ""]
    for g in res["glmm"]:
        f = g["fit"]
        b = g["bootstrap"]
        L += [f"### {g['label']}", "",
              f"s_item = {f['s_item']:.2f}, s_item×agent = {f['s_item_agent']:.2f} (total {math.hypot(f['s_item'], f['s_item_agent']):.2f}); "
              f"bootstrap total s 5/50/95%: {', '.join(f'{x:.2f}' for x in b['s_total_q05_q50_q95'])}; "
              f"share of bootstrap fits with total s < 0.1: {b['share_s_total_below_0.1']:.2f}.", "",
              "| Agent | beta | Mean rate on new item | 95% predictive range (2.5%–97.5%) | 80% range | Bootstrap 5–95% of lower / upper bound |",
              "|---|---|---|---|---|---|"]
        for j, a in enumerate(f["agents"]):
            p = g["new_item"][a]
            bb = b[a]
            L.append(f"| {a} | {f['beta'][j]:+.2f} | {p['mean']:.2f} | {p['q2.5']:.2f}–{p['q97.5']:.2f} | "
                     f"{p['q10']:.2f}–{p['q90']:.2f} | {bb['q2.5_bound_q05_q95'][0]:.2f}–{bb['q2.5_bound_q05_q95'][1]:.2f} / "
                     f"{bb['q97.5_bound_q05_q95'][0]:.2f}–{bb['q97.5_bound_q05_q95'][1]:.2f} |")
        L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--n-boot", type=int, default=200)
    a = ap.parse_args()
    res = compute(a.n_boot)
    js = json.dumps(res, indent=1, sort_keys=True, default=float)
    if a.check:
        old = (OUT / "stats_items.json").read_text()
        ok = old == js + "\n"
        print("match" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stats_items.json").write_text(js + "\n")
    (OUT / "stats_items.md").write_text(render(res))
    print(render(res))


if __name__ == "__main__":
    main()
