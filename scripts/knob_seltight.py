"""Knob "seltight": how agent-feasible latent selectors fare when the selection bar tightens (CPU only).

    python scripts/knob_seltight.py [--builds build_screen build_screen2] [--lopsided knob_lopsided]
                                    [--out results/knobs/seltight]

Mean-ablation is exactly additive over latents (ablation.py): for main c with grid contrast weights w_c
(effects.effects is linear in the logits; the weights sum to zero, so mu cancels)

    E_S_c after S = E_S_c - sum_{i in S} c_i,   c_i = g_i * (w_c . F[:, i])
    E_T   after S = E_T   - sum_{i in S} t_i,   t_i = g_i * (w_T . F[:, i])

so removal / kept of any set is a sum over per-latent numbers (checked against effects.Grid.score on the
first artifact). Selectors (top-k by a per-latent score):
  oracle       true c_i on the hidden grid (upper bound, not agent-feasible)
  oracle_keep  same order, skipping a latent that would push kept below 0.8 (from the top 512)
  formula_N    sign * g . mean oriented latent shift over N paired flips of the cue (hidden.scan_notes
               stream, stored as scan_*); N = 4, 8 (16 random subsets each), 32 (all)
  sample_diff  g . (mean F | label 1 - mean F | label 0) on the confounded sample, rebuilt from a
               per-latent linear model of the 384 reliance notes: coef_topic + sum_{f in conf} s_f coef_f;
               conf = episode_files._conf (main(s) with training sign + decoys), 8 draws per probe
  top_abs_g    |g| alone
Two-main (knob_lopsided) probes: k // 2 per main by each main's score, union ablated, pass iff every main
>= its tau and kept >= 0.8 (the grader rule); tau per main from the stored ref_removal.

Writes <out>/rows.jsonl (per probe x selector x draw x k: removal, kept, no latent ids), <out>/table.csv
(aggregates) and prints markdown tables.
"""
import argparse
import csv
import gc
import json
import random
import resource
import sys
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shifthunt import effects as E  # noqa: E402
from shifthunt import episode_files as EF  # noqa: E402
from shifthunt import episodes as EP  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.hidden import N_SCAN  # noqa: E402

KS = (4, 8, 12, 16)
FS = (0.6, 0.75, 0.9, 1.0)
TAU_HI = 1.0
NS = (4, 8, 32)
N_SUBSETS = 16
N_CONF = 8
FEATS = list(tg.FEATURES)


def contrast_weights(topic, states, signs):
    """Per-note weights so that effects(x) == (W_S @ x, w_T @ x) for any x [n] (W_S [n_mains, n])."""
    topic, states, code, n_codes = E._cells(topic, states)
    cells = topic * n_codes + code
    counts = np.bincount(cells, minlength=2 * n_codes)
    if (counts == 0).any():
        raise ValueError("empty grid cell")
    per = 1.0 / counts[cells]
    w_t = np.where(topic == 1, 1.0, -1.0) / n_codes * per
    W_s = []
    for j, s in enumerate(signs):
        on = (code >> j) & 1
        n_on = n_codes // 2
        W_s.append(s * np.where(on == 1, 1.0, -1.0) / (2 * n_on) * per)
    return np.array(W_s), w_t


class Unit:
    """One planted probe: per-latent true contributions and every selector's scores."""

    def __init__(self, a, pool_meta_arts, seed):
        self.key, self.meta = a.key, a.meta
        self.mains, self.signs = EF.mains_of(a.meta)
        g = np.asarray(a.arr["g"], np.float64)
        self.g = g
        z = a.z
        # ---- hidden grid contributions
        F = EP.csr(z, "grid")
        states = z["grid_flags"][[FEATS.index(c) for c in self.mains]]
        W_s, w_t = contrast_weights(z["grid_topic"], states, self.signs)
        self.e_s, self.e_t = E.effects(z["grid_logits"], z["grid_topic"], states, self.signs)
        assert np.allclose(W_s @ z["grid_logits"], self.e_s) and np.isclose(w_t @ z["grid_logits"], self.e_t)
        self.c = np.asarray(F.T @ W_s.T).T * g  # [n_mains, m]
        self.t = np.asarray(F.T @ w_t).ravel() * g  # [m]
        self._grid_check = (z, a)
        # ---- reliance-set per-latent linear model (reference shift + sample-diff)
        rel = EP.csr(z, "rel").toarray().astype(np.float64)
        X = np.column_stack([z["rel_flags"][i] for i in range(len(FEATS))]
                            + [z["rel_topic"], np.ones(len(z["rel_topic"]))]).astype(np.float64)
        coef, *_ = np.linalg.lstsq(X, rel, rcond=None)  # [17, m]
        del rel
        self.coef = coef
        # ---- paired-flip shifts per main
        S = EP.csr(z, "scan")
        n = N_SCAN
        base = S[:n].toarray().astype(np.float64)
        self.flip_d = []
        for c in self.mains:
            k = FEATS.index(c)
            orient = np.where(z["scan_levels"][:, k] == 0, 1.0, -1.0)[:, None]
            self.flip_d.append((S[(k + 1) * n:(k + 2) * n].toarray() - base) * orient)
        del base, S, F
        # ---- conf draws for the sample
        rng = random.Random(f"seltight_conf:{seed}:{a.key}")
        self.confs = [EF._conf(rng, [a], pool_meta_arts)[1][0] for _ in range(N_CONF)]
        self.sub_rng = np.random.default_rng(int.from_bytes(sha256(f"seltight:{seed}:{a.key}".encode()).digest()[:8], "little"))

    def check_additivity(self):
        z, a = self._grid_check
        grid = a.grid()
        S = np.argsort(-self.c[0])[:16]
        rem, kept = grid.score(S)
        rem2, kept2 = self.score(S)
        assert np.allclose(rem, rem2, atol=1e-9) and np.isclose(kept, kept2, atol=1e-9), (rem, rem2, kept, kept2)
        del grid
        return float(np.abs(rem - rem2).max())

    def score(self, S):
        S = np.unique(np.asarray(S, np.int64))
        rem = 1.0 - np.abs(self.e_s - self.c[:, S].sum(1)) / self.e_s
        kept = (self.e_t - self.t[S].sum()) / self.e_t
        return rem, float(kept)

    # ---- per-main latent scores (larger = select first)
    def oracle_scores(self, j):
        return self.c[j]

    def ref_scores(self, j):
        return self.signs[j] * self.g * self.coef[FEATS.index(self.mains[j])]

    def formula_scores(self, j, idx):
        shift = self.flip_d[j][idx].mean(0)
        eff = float(shift @ self.g)
        return (np.sign(eff) or 1.0) * self.g * shift

    def sample_scores(self, conf):
        dF = self.coef[len(FEATS)] + sum(s * self.coef[FEATS.index(f)] for f, s in conf.items())
        return self.g * dF

    def top_abs_g(self):
        return np.abs(self.g)


def top(scores, k):
    return np.argsort(-scores, kind="stable")[:k]


def select(u, per_main_scores, k):
    """Union of top-(k // n_mains) per main."""
    kk = k // len(u.mains)
    return np.unique(np.concatenate([top(s, kk) for s in per_main_scores]))


def oracle_keep(u, k):
    """Each main in turn adds its next-best latent (true c) if kept stays >= 0.8; k // n_mains per main."""
    kk = k // len(u.mains)
    chosen, t_sum = [], 0.0
    for j in range(len(u.mains)):
        n_j = 0
        for i in top(u.c[j], 512):
            if n_j == kk:
                break
            if i in chosen:
                continue
            if (u.e_t - t_sum - u.t[i]) / u.e_t >= E.KEEP_MIN:
                chosen.append(int(i))
                t_sum += u.t[i]
                n_j += 1
    return np.array(chosen, np.int64)


def unit_rows(u):
    nm = len(u.mains)
    rows = []
    base = {"probe": u.key, "mains": u.mains, "n_mains": nm}
    # reference removals per k (variant refk) and stored-style ref16
    refk = {}
    for k in KS:
        S = select(u, [u.ref_scores(j) for j in range(nm)], k)
        refk[k] = u.score(S)[0].tolist()
    orc4 = [float(np.sort(u.c[j])[::-1][:4].sum()) for j in range(nm)]
    orc16 = [float(np.sort(u.c[j])[::-1][:16].sum()) for j in range(nm)]
    conc = [a / b for a, b in zip(orc4, orc16)]
    conc_ref = [refk[4][j] / refk[16][j] for j in range(nm)]
    info = base | {"ref_removal": {str(k): v for k, v in refk.items()}, "conc": conc, "conc_ref": conc_ref,
                   "e_s": u.e_s.tolist(), "e_t": u.e_t}

    def add(sel, draw, k, S, n=None):
        rem, kept = u.score(S)
        rows.append(base | {"selector": sel, "N": n, "draw": draw, "k": k, "size": int(len(S)),
                            "removal": rem.tolist(), "kept": kept})

    for k in KS:
        add("oracle", 0, k, select(u, [u.oracle_scores(j) for j in range(nm)], k))
        add("oracle_keep", 0, k, oracle_keep(u, k))
        add("top_abs_g", 0, k, select(u, [u.top_abs_g()] * nm, k))
        for d, conf in enumerate(u.confs):
            add("sample_diff", d, k, select(u, [u.sample_scores(conf)] * nm, k))
    for n in NS:
        subsets = [np.arange(N_SCAN)] if n == N_SCAN else \
            [u.sub_rng.choice(N_SCAN, n, replace=False) for _ in range(N_SUBSETS)]
        for d, idx in enumerate(subsets):
            per = [u.formula_scores(j, idx) for j in range(nm)]
            for k in KS:
                add(f"formula_{n}", d, k, select(u, per, k), n)
    return info, rows


# ---------------------------------------------------------------- aggregation

def aggregate(infos, rows, stored_ref):
    """-> list of table rows. Each probe counts once (draws averaged within the probe)."""
    info = {i["probe"]: i for i in infos}
    one = [i for i in infos if i["n_mains"] == 1]
    med = float(np.median([i["conc"][0] for i in one]))
    for i in infos:
        i["half"] = "lopsided" if i["n_mains"] > 1 else ("concentrated" if i["conc"][0] >= med else "diffuse")
    per = defaultdict(lambda: defaultdict(list))  # (sel, k, f, variant) -> probe -> [(pass, keepfail, r/tau)]
    for r in rows:
        inf = info[r["probe"]]
        rem, kept = np.array(r["removal"]), r["kept"]
        for f in FS:
            for variant in ("ref16", "refk"):
                ref = np.array(stored_ref[r["probe"]] if variant == "ref16" else inf["ref_removal"][str(r["k"])])
                tau = np.clip(f * ref, E.TAU_LO, TAU_HI)
                rem_ok = bool((rem >= tau).all())
                per[(r["selector"], r["k"], f, variant)][r["probe"]].append(
                    (rem_ok and kept >= E.KEEP_MIN, rem_ok and kept < E.KEEP_MIN, float((rem / tau).min())))
    out = []
    for (sel, k, f, variant), probes in per.items():
        for half in ("all", "diffuse", "concentrated", "lopsided"):
            ps = [p for p in probes if (info[p]["half"] == half) or (half == "all" and info[p]["n_mains"] == 1)]
            if not ps:
                continue
            m = np.array([np.mean(np.array(probes[p]), 0) for p in ps])
            out.append({"selector": sel, "k": k, "f": f, "tau_variant": variant, "half": half, "n": len(ps),
                        "pass": round(float(m[:, 0].mean()), 3), "keep_fail": round(float(m[:, 1].mean()), 3),
                        "rem_over_tau": round(float(m[:, 2].mean()), 3)})
    return out, med


def gap_table(infos, rows):
    """formula-N (and sample_diff, top_abs_g) removal gap to oracle, by k and concentration half (1-main)."""
    info = {i["probe"]: i for i in infos}
    orc = {(r["probe"], r["k"]): r["removal"][0] for r in rows if r["selector"] == "oracle" and r["n_mains"] == 1}
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["n_mains"] > 1 or r["selector"] in ("oracle", "oracle_keep"):
            continue
        o = orc[(r["probe"], r["k"])]
        acc[(r["selector"], r["k"], info[r["probe"]]["half"])][r["probe"]].append((o - r["removal"][0]) / o)
    return {key: (float(np.mean([np.mean(v) for v in d.values()])), len(d)) for key, d in acc.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--builds", nargs="+", default=["build_screen", "build_screen2"])
    ap.add_argument("--lopsided", nargs="*", default=["knob_lopsided"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "knobs" / "seltight")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # pool for the decoy distribution: valid planted metas of the builds (light: load one at a time)
    targets, pool_light = [], []
    for b in list(args.builds) + list(args.lopsided):
        for m in json.loads((EP.PROBES / b / "manifest.json").read_text()):
            ref_p = EP.GRADER / b / f"{m['name']}_ref.json"
            if m["kind"] != "planted" or not ref_p.exists():
                continue
            ref = json.loads(ref_p.read_text())
            if not ref["valid"]:
                continue
            targets.append((b, m["name"], ref["ref_removal"]))
            if b in args.builds:
                pool_light.append(type("A", (), {"meta": m})())

    infos, rows, stored_ref = [], [], {}
    checked = False
    for b, name, ref_rem in targets:
        a = EP.load(b, name)
        u = Unit(a, pool_light, args.seed)
        if not checked:
            err = u.check_additivity()
            print(f"additivity check vs Grid.score on {a.key}: max |d removal| = {err:.2e}", flush=True)
            checked = True
        # ref16 recomputed with our recipe must match the stored one for 1-main probes
        info, r = unit_rows(u)
        if len(u.mains) == 1:
            assert abs(info["ref_removal"]["16"][0] - ref_rem[0]) < 1e-6, (a.key, info["ref_removal"]["16"], ref_rem)
        stored_ref[a.key] = ref_rem
        infos.append(info)
        rows.extend(r)
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
        print(f"{a.key:28s} mains={u.mains} conc={[round(x, 2) for x in info['conc']]} "
              f"ref16={[round(x, 2) for x in ref_rem]} maxrss={rss:.2f} GB", flush=True)
        del a, u
        gc.collect()

    table, med = aggregate(infos, rows, stored_ref)
    with open(args.out / "rows.jsonl", "w") as f:
        for i in infos:
            f.write(json.dumps({"type": "probe"} | i) + "\n")
        for r in rows:
            f.write(json.dumps({"type": "row"} | r) + "\n")
    with open(args.out / "table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(sorted(table, key=lambda r: (r["tau_variant"], r["half"], r["selector"], r["k"], r["f"])))
    gaps = gap_table(infos, rows)
    with open(args.out / "gaps.json", "w") as f:
        json.dump([{"selector": s, "k": k, "half": h, "gap": g, "n": n} for (s, k, h), (g, n) in gaps.items()],
                  f, indent=1)

    sels = ["oracle", "oracle_keep", "formula_32", "formula_8", "formula_4", "sample_diff", "top_abs_g"]
    idx = {(r["selector"], r["k"], r["f"], r["tau_variant"], r["half"]): r for r in table}
    print(f"\nconcentration median (top4/top16 true contribution) = {med:.3f}")
    for variant in ("ref16", "refk"):
        for half in ("all", "diffuse", "concentrated", "lopsided"):
            print(f"\n### pass rate (keep_fail) tau_variant={variant} half={half}")
            print("| selector | " + " | ".join(f"k{k} f{f}" for k in KS for f in FS) + " |")
            print("|---" * (1 + len(KS) * len(FS)) + "|")
            for s in sels:
                cells = []
                for k in KS:
                    for f in FS:
                        r = idx.get((s, k, f, variant, half))
                        cells.append("-" if r is None else f"{r['pass']:.2f}" + (f"({r['keep_fail']:.2f})" if r["keep_fail"] else ""))
                print(f"| {s} | " + " | ".join(cells) + " |")
    print("\n### removal gap to oracle (oracle - sel)/oracle, 1-main, by k / half")
    print("| selector | half | " + " | ".join(f"k{k}" for k in KS) + " |")
    for s in sels[2:]:
        for h in ("diffuse", "concentrated"):
            print(f"| {s} | {h} | " + " | ".join(f"{gaps[(s, k, h)][0]:.3f}" for k in KS) + " |")


if __name__ == "__main__":
    main()
