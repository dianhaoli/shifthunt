"""R10: frozen vs r10 values of every judge-based analysis output (ROUND10_DIFF inputs).

    python scripts/r10_diff.py FILE...     # FILE relative to results/blackbox_1112 (e.g. gpuplan/c6/c6.json)
        -> results/blackbox_1112/gpuplan/r10/diff/<file path with / -> __>.json  (every leaf: frozen, r10, change)

Frozen = the main tree's tracked file (registered); r10 = the same file in the r10 worktree after the r10 analyse
steps. "k/n" strings are compared as fractions. The r10 copies of the analysis outputs are also written under
gpuplan/r10/out/<same path> in the main tree.
"""
import json
import shutil
import sys
from collections import OrderedDict
from pathlib import Path

MAIN = Path("/home/ec2-user/shifthunt-public/results/blackbox_1112")
WT = Path("/home/ec2-user/shifthunt_r10/results/blackbox_1112")
OUT = MAIN / "gpuplan" / "r10" / "diff"
COPY = MAIN / "gpuplan" / "r10" / "out"


def flat(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flat(v, f"{pre}/{k}" if pre else str(k))
    elif isinstance(x, list) and x and all(isinstance(v, (int, float)) for v in x) and len(x) <= 4:
        yield pre, x
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, x


def num(v):
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and "/" in v:
        a, _, b = v.partition("/")
        try:
            return float(a) / float(b) if float(b) else None
        except ValueError:
            return None
    return None


def main(files):
    OUT.mkdir(parents=True, exist_ok=True)
    for f in files:
        a, b = MAIN / f, WT / f
        if not b.is_file():
            print(f, "no r10 output")
            continue
        (COPY / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(b, COPY / f)
        A = dict(flat(json.loads(a.read_text()))) if a.is_file() else {}
        B = dict(flat(json.loads(b.read_text())))
        rows = OrderedDict()
        for k in list(A) + [k for k in B if k not in A]:
            va, vb = A.get(k), B.get(k)
            if va == vb:
                continue
            na, nb = num(va), num(vb)
            rows[k] = OrderedDict(frozen=va, r10=vb, change=None if na is None or nb is None else round(nb - na, 4))
        (OUT / (f.replace("/", "__"))).write_text(json.dumps(OrderedDict(file=f, changed=len(rows), rows=rows), indent=1,
                                                             default=str) + "\n")
        print(f, "changed leaves:", len(rows))


if __name__ == "__main__":
    main(sys.argv[1:])
