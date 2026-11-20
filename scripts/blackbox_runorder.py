"""Seeded, interleaved run order of one block of the no-SAE study (plan §4).

    python scripts/blackbox_runorder.py --block 1 --seed 20261112 --out results/blackbox_1112/runorder_block1.csv
    python scripts/blackbox_runorder.py --block 2 --seed 20261112 --out results/blackbox_1112/runorder_block2.csv
    python scripts/blackbox_runorder.py --pilots --out results/blackbox_1112/runorder_pilots.csv

Block 1: GPT Open-8, BB-8, BB-64 on the six items, 4 runs each (72), and Haiku Open-8, BB-8, BB-64 on the six
items, 2 runs each (36): 108 rows. Block 2: GPT Open-64 on the six items, 4 runs each: 24 rows.
The rows of a block are listed in a fixed order (agent, arm, item, rep) and then put in one random
permutation drawn with numpy.random.default_rng(seed), so arms, agents and items are interleaved.
--pilots: the four excluded pilot runs in a fixed order (GPT Open-8, BB-8, BB-64 on the first item; Haiku BB-8
on the first two-part item); no seed is used.

Columns: order (1-based position in the queue), agent, model, engine, arm, item, problem (the runner's
PROBLEM string: open8 `<item>-open`, bb8 `<item>-blackbox`, bb64 `<item>-blackbox64`, open64 `<item>-open64`),
rep (the replicate number, 1-based, within agent x arm x item). These are the column names the scheduler reads
(scripts/blackbox_schedule.py). The file is a pure function of (block, seed).
Without --out the CSV goes to stdout.
"""
import argparse
import csv
import io
import sys
from pathlib import Path

import numpy as np

SEED = 20261112
ITEMS = ("ep411", "ep413", "ep415", "ep472", "ep474", "ep476")
AGENTS = {"gpt": ("gpt-6.1-terra", "codex"), "haiku": ("claude-haiku-5-5", "claude")}  # agent -> (model, engine)
PROBLEM_SUFFIX = {"open8": "-open", "bb8": "-blackbox", "bb64": "-blackbox64", "open64": "-open64"}
BLOCKS = {  # block -> [(agent, arms, runs per item)]
    1: [("gpt", ("open8", "bb8", "bb64"), 4), ("haiku", ("open8", "bb8", "bb64"), 2)],
    2: [("gpt", ("open64",), 4)],
}
PILOTS = [("gpt", "open8", "ep411"), ("gpt", "bb8", "ep411"), ("gpt", "bb64", "ep411"), ("haiku", "bb8", "ep472")]
COLUMNS = ["order", "agent", "model", "engine", "arm", "item", "problem", "rep"]


def problem(item, arm):
    return item + PROBLEM_SUFFIX[arm]


def _row(agent, arm, item, rep):
    model, engine = AGENTS[agent]
    return {"agent": agent, "model": model, "engine": engine, "arm": arm, "item": item,
            "problem": problem(item, arm), "rep": rep}


def block_rows(block):
    """The rows of a block in their fixed listing order (before the permutation)."""
    return [_row(agent, arm, item, rep) for agent, arms, n in BLOCKS[block] for arm in arms for item in ITEMS
            for rep in range(1, n + 1)]


def run_order(block, seed=SEED):
    """The block's rows in the seeded random order, with `order` 1..n."""
    rows = block_rows(block)
    perm = np.random.default_rng(seed).permutation(len(rows))
    return [dict(rows[int(j)], order=i + 1) for i, j in enumerate(perm)]


def pilot_order():
    """The four pilot runs, fixed order."""
    return [dict(_row(agent, arm, item, 1), order=i + 1) for i, (agent, arm, item) in enumerate(PILOTS)]


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--block", type=int, choices=sorted(BLOCKS))
    g.add_argument("--pilots", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    text = to_csv(pilot_order() if a.pilots else run_order(a.block, a.seed))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text)
        print(f"{text.count(chr(10)) - 1} rows -> {a.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
