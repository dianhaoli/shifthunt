"""BB-8 feasibility (D35), a blind free-channel ranker: within each label class, regress the free sample logits
(probe_scores) on the share of each aligned property's realisation in the note (characters of the property's span
over note length), optionally controlling for 1/length. The t-statistic, oriented to the label direction, ranks the
aligned properties. It uses only public sample texts and their logits (and which properties are aligned, which a
blind agent finds by regex on the sample).

    python scripts/feasibility/bb8_ranker.py --out AGG.json --private-dir DIR [--bank B]

Tracked: for each control setting, the sorted ranks of the main among the 8 aligned properties on every planted
probe, top-1 and top-2 counts, and the ranks on hard probes. Per-probe lines go to <private-dir>/bb8_ranker.txt.
The span rules below are hand-written for every property of the two generators alike; they encode no episode.
"""
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb8_common as BC  # noqa: E402

WD = r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"


def spans(sub, text):
    """Share of the note taken by each property's realisation (0 if absent)."""
    t = text
    L = t.split("\n")
    n = len(t)
    out = {}
    if sub == "freetext":
        body = max(L, key=len)
        out["greeting"] = len(L[0]) if (len(L) > 1 and L[0] != body and re.match(r"(?i)(hi|hello|hey|dear|morning)\b", L[0])) else 0
        m = re.search(r"(?im)^(cheers|best|take care|talk soon|all the best|thanks|warmly|speak soon)[,!]\n\w+", t)
        out["signoff"] = len(m.group(0)) if m else 0
        m = re.search(r"#\w+", t)
        out["hashtag"] = len(m.group(0)) if m else 0
        out["ps_question"] = len(L[-1]) if (L[-1].lower().startswith("p.s.") and L[-1].endswith("?")) else 0
        out["postscript"] = len(L[-1]) if L[-1].lower().startswith("p.s.") else 0
        m = re.search(r"(?i)[^.!?]*\b" + WD + r"\b[^.!?]*[.!?]", body)
        out["weekday"] = len(m.group(0)) if m else 0
        m = re.search(r"\([^)]*\)", t)
        out["parenthetical"] = len(m.group(0)) if m else 0
        m = re.search(r'[^.!?]*"[^"]*"\.?', body)
        out["quote"] = len(m.group(0)) if m else 0
        qs = re.findall(r"[^.!?]*\?", body)
        out["question"] = sum(len(q) for q in qs)
        out["she_pronoun"] = 5 * len(re.findall(r"(?i)\b(she|her|herself)\b", body))
        out["lowercase"] = float(t == t.lower()) * len(re.findall(r"[.!?]\s", t)) * 5
        out["exclamation"] = 5 * body.count("!")
        out["ellipsis"] = 5 * body.count("...")
        out["emoticon"] = 3 * len(re.findall(r"(?i)(:\)|:-\)|:D|;\)|:P|\^_\^)", body))
    else:
        out["greeting"] = len(L[0]) if re.match(r"(?i)^hi \w+,$", L[0]) else 0
        m = re.search(r"(?im)^[a-z ]+,\n[a-z]+$", t)
        out["signoff"] = len(m.group(0)) if m else 0
        m = re.search(r"(?m)^#\w+$", t)
        out["hashtag"] = len(m.group(0)) if m else 0
        out["postscript"] = len(L[-1]) if L[-1].lower().startswith("p.s.") else 0
        m = re.search(r"\([^)]*\)", t)
        out["parenthetical"] = len(m.group(0)) if m else 0
        out["bullet_list"] = 3 * len(re.findall(r"(?m)^- ", t))
        out["exclamation"] = 3 * t.count("!")
        out["question_ending"] = len(re.findall(r"(?i)would you try it with \w+\?", t)) * 25
        out["british_spelling"] = 6 * len(re.findall(
            r"(?i)\b(neighbour|favourite|colour|centre|grey|organis\w*|practis\w*|theatre)\b", t))
        out["past_tense"] = 5 * len(re.findall(
            r"(?i)\b(spent|owned|kept|loved|hated|said|was|thought|found|went|organised|organized|practised|practiced|met)\b", t))
        out["she_pronoun"] = 4 * len(re.findall(r"(?i)\b(she|her)\b", t))
        out["lowercase"] = float(t == t.lower()) * 5 * (1 + len(re.findall(r"[.!?]\s", t)) + t.count("\n"))
        m = re.search(r"(?i)[^.!?\n]*\b" + WD + r"\b[^.!?\n]*[.!?]", t)
        out["weekday"] = len(m.group(0)) if m else 0
        m = re.search(r'[^.!?\n]*"[^"]*"', t)
        out["quote"] = len(m.group(0)) if m else 0
    return {k: v / n for k, v in out.items()}


def rank_probe(bank, ep, j, a, sub, ctrl=True):
    conf = a["conf_features"]
    p = a["probes"][j]
    cs = p["conf_signs"]
    s = json.loads((Path(bank) / ep / "public" / f"probe{j}_sample.json").read_text())["texts"]
    lg = BC.sample_logits(bank, ep, j)
    lab = np.array([t["label"] for t in s])
    SP = [spans(sub, t["text"]) for t in s]
    score = {}
    for c in (0, 1):
        idx = np.flatnonzero(lab == c)
        props = [f for f in conf if (cs[f] == 1) == (c == 1)]  # present in class c
        if not props:
            continue
        X = np.array([[SP[i][f] for f in props] for i in idx])
        y = lg[idx]
        keep = [k for k in range(len(props)) if X[:, k].std() > 1e-9]
        cols = [np.ones(len(idx))] + [X[:, k] for k in keep]
        if ctrl:
            cols.append(np.array([1.0 / len(s[i]["text"]) for i in idx]) * 100)
        A = np.column_stack(cols)
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        r = y - A @ beta
        dof = max(1, len(y) - A.shape[1])
        s2 = r @ r / dof
        cov = s2 * np.linalg.pinv(A.T @ A)
        se = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
        t = beta / se
        d = 1 if c == 1 else -1
        for q, k in enumerate(keep):
            score[props[k]] = float(t[1 + q] * d)
        for k in range(len(props)):
            if k not in keep:
                score[props[k]] = 0.0
    return score


def main(argv=None):
    a = BC.parser(__doc__).parse_args(argv)
    priv = BC.require_ignored(a.private_dir)
    lines, res = [], {}
    for ctrl in (False, True):
        lines.append(f"control 1/len: {ctrl}")
        ranks, hr = [], []
        for ep in BC.EPS:
            ans, sub = BC.answer(a.bank, ep), BC.substrate(a.bank, ep)
            for j, p in enumerate(ans["probes"]):
                sc = rank_probe(a.bank, ep, j, ans, sub, ctrl)
                order = sorted(sc, key=lambda f: -sc[f])
                if p["kind"] == "planted":
                    rk = order.index(p["cue"]) + 1
                    ranks.append(rk)
                    hard = BC.is_hard_source(p["source"])
                    if hard:
                        hr.append(rk)
                    lines.append(f"  {ep} p{j} {'HARD' if hard else 'plain'} rank of main {rk}/8 "
                                 f"t_main={sc[p['cue']]:+.1f} top t={sc[order[0]]:+.1f} 2nd={sc[order[1]]:+.1f}")
                else:
                    lines.append(f"  {ep} p{j} null top t={sc[order[0]]:+.1f} 2nd={sc[order[1]]:+.1f}")
        res["control_1_over_length" if ctrl else "no_control"] = {
            "planted_main_ranks_sorted": sorted(ranks), "top1": sum(r == 1 for r in ranks),
            "top2": sum(r <= 2 for r in ranks), "planted": len(ranks), "hard_main_ranks_sorted": sorted(hr)}
    (priv / "bb8_ranker.txt").write_text("\n".join(lines) + "\n")
    BC.write_out(a.out, {"script": "bb8_ranker", "results": res})


if __name__ == "__main__":
    main()
