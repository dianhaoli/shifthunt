"""S3 coder (plan §5 S3; decisions D8 and D19): "true cue varied cleanly", from the full-text tool log.

    python scripts/s3_coder.py --raw <batch dir> [--raw ...] --out-csv results/blackbox_1112/s3.csv
                               [--private-out results/private_1112/s3/]
    python scripts/s3_coder.py --raw <batch dir> [--raw ...] --validate-sample N --seed S --out <private dir>
                               [--force]

`--raw` is a run directory, a batch directory (one `<cid>/` per rollout) or a parent of batch directories. The
raw directories are private; run and batch names are the last two components of the run directory's absolute
path (so `--raw .` from inside a batch directory works). Per run this script reads fulltext.jsonl (shifthunt/toolserver.py: one JSON line
per charged call of probe_query / latent_means / latent_tokens, with the agent's texts, their SHA-256 and, for
an "ok" probe_query, the logits), answer.json (hard slot, its main cue, the generator), grade.json (hard_slots
cross-check, access and budget for the arm), episode_id and log.jsonl (cross-check of the full-text log).

Definition (pre-registered wording, D19):
  scored texts  the agent-written texts of probe_query calls with status "ok" on the hard probe, in call
                order, duplicates kept. Sample notes scored with probe_scores are not counted.
  normalisation "\\r" is removed and trailing "\\n" are stripped before detection; nothing else.
  flags         the detectors of the episode's generator on each text, one 0/1 column per generator property
                (all 15 of the substrate): shifthunt.detectors.detect_all for the templated generator,
                shifthunt.freetext.detect for the free-text one (dispatch on answer.json "features").
  m, p          m = the hard slot's main cue (for a two-part item the child), p = its parent if nested
                (freetext.IMPLIES), else none.
  (a) pair      two scored texts differ in m and in at most one other property; that other property is never
                p; for a nested main p is on in both texts.
  (b) identif.  over the scored texts (nested main: the texts with p on), the column of m is not in the linear
                span of the constant column and the other properties' columns (p left out: it is constant
                there). Exact integer rank comparison: rank([1, O, m]) > rank([1, O]).
  S3            1 iff (a) or (b); fewer than 2 scored texts -> 0. With several mains on a hard slot, or several
                hard slots (neither occurs in the shipped six), S3, S3a and S3b are each computed per main and
                all must hold.

Outputs. The tracked CSV has one row per run: run, batch, episode, arm, n_scored_hard, n_distinct (distinct
raw texts among the scored ones), main_varies, s3a, s3b, s3, then the other descriptors (probe_query texts on
other probes, own-text SAE calls and texts, the hard probe's logit minimum and maximum over the scored texts)
and `log`. It names no property and holds no text; this is checked before the file is written. The private
JSONL (one file per batch, one line per run) has the flags matrix with property names, the witnessing pair of
(a) and the text hashes. Rows join to the rows of scripts/score_naming.py on (batch, run).

`log` says what the full-text log allowed:
  ok                  coded from fulltext.jsonl.
  no_calls            no fulltext.jsonl, and log.jsonl shows no charged call of the three tools: S3 = 0.
  missing             no fulltext.jsonl although such calls were charged (an image without the full-text log,
                      for example the main study), or no log.jsonl either: S3 is blank.
  torn, capped, malformed, hash_mismatch, log_mismatch
                      the full-text log is not a complete, intact record of the charged calls (an unparsable
                      line, the size cap, a record of an unexpected shape, a text whose SHA-256 differs from
                      the logged one, a charged call of log.jsonl without its record): S3 is blank; the counts
                      describe what was read.
  no_answer, unsupported_substrate, no_hard_slot, hard_slot_mismatch
                      answer.json is missing, is of a generator other than the two above, has no hard slot,
                      or disagrees with grade.json's hard_slots: S3 is blank.

Detector validation (plan §5: about 50 hand-checked logged texts): --validate-sample draws N distinct "ok"
probe_query texts (any probe) from the given runs, split evenly over the substrates present, and writes
s3_validate_flags.jsonl (text, where it came from, detector flags), s3_validate_blind.jsonl (id, substrate,
text and an empty label per property, for an independent labeller) and s3_validate_meta.json. The labeller
fills s3_validate_blind.jsonl in place, so a directory that already holds any of the three files is refused
unless --force is given.

Imports only shifthunt.detectors, shifthunt.freetext, shifthunt.textgen, shifthunt.reward and
scripts/score_naming.py (episode id and arm, as the scorer reads them): no torch. Do not run under
scripts/freetext_run.py (it swaps shifthunt.textgen).
"""
import argparse
import csv
import hashlib
import io
import json
import os
import random
import subprocess
import sys
from collections import Counter, OrderedDict
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import score_naming as SN  # noqa: E402
from shifthunt import detectors, freetext as FT, textgen as TG  # noqa: E402
from shifthunt.reward import hard_slots  # noqa: E402

if list(TG.FEATURES) == list(FT.FEATURES):  # shifthunt.textgen was swapped by scripts/freetext_run.py
    raise ImportError("s3_coder needs the plain interpreter, not scripts/freetext_run.py")
if set(detectors.DETECTORS) != set(TG.FEATURES):
    raise ImportError("shifthunt.detectors does not cover shifthunt.textgen.FEATURES")

SUBSTRATES = ("templated", "freetext")
FEATURES = {"templated": tuple(TG.FEATURES), "freetext": tuple(FT.FEATURES)}
PARENTS = {"templated": {}, "freetext": dict(FT.IMPLIES)}  # child -> parent
PROPERTY_NAMES = frozenset(FEATURES["templated"]) | frozenset(FEATURES["freetext"])
FULLTEXT_TOOLS = ("probe_query", "latent_means", "latent_tokens")  # shifthunt.toolserver.FULLTEXT_TOOLS
SAE_TEXT_TOOLS = ("latent_means", "latent_tokens")
CSV_COLUMNS = ["run", "batch", "episode", "arm", "n_scored_hard", "n_distinct", "main_varies", "s3a", "s3b", "s3",
               "n_other_texts", "n_own_text_sae_calls", "n_own_text_sae_texts", "logit_min", "logit_max", "log"]
RUN_FILES = tuple(SN.RUN_FILES) + ("fulltext.jsonl", "answer.json")
VALIDATE_FILES = ("s3_validate_flags.jsonl", "s3_validate_blind.jsonl", "s3_validate_meta.json")


# ---------------------------------------------------------------------------------------------------------
# text -> flags

def normalise(text):
    """D19: remove "\\r", strip trailing "\\n"; nothing else."""
    return text.replace("\r", "").rstrip("\n")


def flags_for(text, substrate):
    """{property: 0/1} of one agent-written text, in the generator's property order, from the generator's own
    detectors on the normalised text."""
    t = normalise(text)
    if substrate == "templated":
        d = detectors.detect_all(t)
    elif substrate == "freetext":
        d = FT.detect(t)
    else:
        raise ValueError(f"unknown substrate {substrate!r} (one of {SUBSTRATES})")
    return OrderedDict((f, int(bool(d[f]))) for f in FEATURES[substrate])


def substrate_of(answer):
    """Generator of an episode from answer.json "features" (absent in the oldest templated episodes)."""
    f = answer.get("features")
    if f is None or list(f) == list(FEATURES["templated"]):
        return "templated"
    if list(f) == list(FEATURES["freetext"]):
        return "freetext"
    raise ValueError("answer.json features match neither the templated nor the free-text generator")


def mains_of(probe):
    """Main cues of one answer.json probe entry ([] for a null probe)."""
    if probe.get("mains"):
        return list(probe["mains"])
    return [probe["cue"]] if probe.get("kind") == "planted" and probe.get("cue") else []


# ---------------------------------------------------------------------------------------------------------
# S3 from a flags matrix

def exact_rank(rows):
    """Rank of an integer matrix (list of equal-length rows) over the rationals, by integer elimination:
    exact, no floating point."""
    M = [[int(x) for x in r] for r in rows]
    if not M:
        return 0
    n_cols = len(M[0])
    if any(len(r) != n_cols for r in M):
        raise ValueError("rows of different lengths")
    rank = 0
    for c in range(n_cols):
        piv = next((i for i in range(rank, len(M)) if M[i][c]), None)
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        p = M[rank]
        for i in range(rank + 1, len(M)):
            a = M[i][c]
            if a:
                row = [p[c] * x - a * y for x, y in zip(M[i], p)]
                g = gcd(*row)
                M[i] = [x // g for x in row] if g > 1 else row
        rank += 1
        if rank == len(M):
            break
    return rank


def _is_01(x):
    """A flag value: exactly 0 or 1 (checked on the value as given: 0.9 or "1" is not one)."""
    try:
        return not isinstance(x, (str, bytes)) and bool(x == 0 or x == 1)
    except (TypeError, ValueError):
        return False


def s3_from_flags(F, cols, main, parent=None):
    """S3 of one main cue from the flags of the scored texts.

    F: one row of 0/1 per scored text, in call order; cols: the property name of each column; main: the main
    cue's column name; parent: the column name of its parent for a nested main, else None.
    -> dict: n, n_parent_on (None without a parent), main_varies, s3a, s3b, s3 (0/1), pair ([i, j], row indices
    of the witnessing pair of clause (a), a pair that differs in the main only if there is one, else the first
    pair in row order; None without one), pair_other (the one other property the pair differs in, or None),
    rank_without, rank_with (the two ranks of clause (b))."""
    cols = list(cols)
    if len(set(cols)) != len(cols):
        raise ValueError("duplicate column names")
    if main not in cols or (parent is not None and (parent not in cols or parent == main)):
        raise ValueError("main (and parent) must be distinct column names")
    rows = [list(r) for r in F]
    if any(len(r) != len(cols) or any(not _is_01(x) for x in r) for r in rows):
        raise ValueError("F must be rows of 0/1, one value per column")
    rows = [[int(x) for x in r] for r in rows]
    m = cols.index(main)
    p = cols.index(parent) if parent is not None else None
    n = len(rows)
    # (a) pair clause
    best = None  # (number of other differing properties, i, j, that property's column)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = rows[i], rows[j]
            if a[m] == b[m]:
                continue
            if p is not None and not (a[p] and b[p]):
                continue
            others = [k for k in range(len(cols)) if k != m and a[k] != b[k]]
            if len(others) > 1 or p in others:
                continue
            cand = (len(others), i, j, others[0] if others else None)
            if best is None or cand[:3] < best[:3]:
                best = cand
    # (b) identifiability clause
    sub = rows if p is None else [r for r in rows if r[p]]
    keep = [k for k in range(len(cols)) if k not in (m, p)]
    base = [[1] + [r[k] for k in keep] for r in sub]
    rank_without = exact_rank(base)
    rank_with = exact_rank([b + [r[m]] for b, r in zip(base, sub)])
    s3a = int(n >= 2 and best is not None)
    s3b = int(n >= 2 and rank_with > rank_without)
    return dict(n=n, n_parent_on=None if p is None else len(sub),
                main_varies=int(len({r[m] for r in rows}) > 1), s3a=s3a, s3b=s3b, s3=int(bool(s3a or s3b)),
                pair=[best[1], best[2]] if best else None,
                pair_other=cols[best[3]] if best and best[3] is not None else None,
                rank_without=rank_without, rank_with=rank_with)


# ---------------------------------------------------------------------------------------------------------
# the logs of one run

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_file(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _record_ok(rec):
    """A full-text record of the expected shape, with matching hashes? -> None, "malformed" or
    "hash_mismatch"."""
    texts, sha, logits = rec.get("texts"), rec.get("sha256"), rec.get("logits")
    if type(rec.get("seq")) is not int or not isinstance(rec.get("status"), str):
        return "malformed"
    if texts is None:
        return None if sha is None and rec["tool"] != "probe_query" else "malformed"
    if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
        return "malformed"
    if not isinstance(sha, list) or len(sha) != len(texts):
        return "malformed"
    if rec["tool"] == "probe_query":
        if type(rec.get("probe")) is not int:
            return "malformed"
        if rec["status"] == "ok" and not (isinstance(logits, list) and len(logits) == len(texts)
                                         and all(_is_num(x) for x in logits)):
            return "malformed"
    try:
        if [sha256_text(t) for t in texts] != sha:
            return "hash_mismatch"
    except UnicodeEncodeError:
        return "malformed"
    return None


def read_fulltext(path):
    """(records in file order, problems) of a fulltext.jsonl. problems is a list of distinct tags: "torn" (a
    line that is not JSON), "capped" (the size-cap marker), "malformed", "hash_mismatch". Records with a
    problem are left out."""
    records, problems = [], []
    for line in Path(path).read_bytes().split(b"\n"):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            problems.append("torn")
            continue
        if isinstance(rec, dict) and rec.get("event") == "fulltext capped":
            problems.append("capped")
            continue
        if not isinstance(rec, dict) or rec.get("tool") not in FULLTEXT_TOOLS:
            problems.append("malformed")
            continue
        bad = _record_ok(rec)
        if bad:
            problems.append(bad)
            continue
        records.append(rec)
    return records, list(OrderedDict.fromkeys(problems))


def _charged_log_calls(run_dir):
    """Charged calls of the three tools in log.jsonl, {seq: record}; None without the file."""
    path = Path(run_dir) / "log.jsonl"
    if not path.exists():
        return None
    out = {}
    for line in path.read_bytes().split(b"\n"):
        try:
            r = json.loads(line) if line.strip() else None
        except ValueError:
            continue  # a torn last line of the tool log
        if isinstance(r, dict) and isinstance(r.get("tool"), str) and r["tool"] in FULLTEXT_TOOLS \
                and r.get("charges") and type(r.get("seq")) is int:
            out[r["seq"]] = r
    return out


def _log_agrees(charged, records):
    """Every charged call of log.jsonl has its full-text record, with the same tool, status and number of
    texts. (log.jsonl may itself be capped, so a full-text record without a log record is not an error.)"""
    have = {r["seq"]: r for r in records}
    for seq, lr in charged.items():
        fr = have.get(seq)
        if fr is None or fr["tool"] != lr["tool"] or fr["status"] != lr.get("status"):
            return False
        n = ((lr.get("args") or {}).get("texts") or {}).get("n") if isinstance(lr.get("args"), dict) else None
        if isinstance(n, int) and n != len(fr["texts"] or []):
            return False
    return True


def scored_texts(records, probe):
    """The scored texts of one probe: [{seq, index, text, sha256, logit}] in call order, duplicates kept."""
    out = []
    for r in records:
        if r["tool"] == "probe_query" and r["status"] == "ok" and r["probe"] == probe:
            out += [dict(seq=r["seq"], index=k, text=t, sha256=h, logit=float(x))
                    for k, (t, h, x) in enumerate(zip(r["texts"], r["sha256"], r["logits"]))]
    return out


def _abs(path):
    """Absolute path without following symbolic links: `.` and `..` are resolved, so that the run and batch
    names can be read off the last two components."""
    return Path(os.path.abspath(path))


def _all3(values):
    """None if empty, else 1 iff every value is 1."""
    return int(all(values)) if values else None


def code_run(run_dir, answer=None):
    """S3 and its descriptors for one run directory. -> OrderedDict with the CSV_COLUMNS (values that could not
    be computed are None) and "private": the per-slot detail with property names (flags matrix, witnessing
    pair, hashes). `answer` overrides <run_dir>/answer.json. Raises score_naming.ArmMismatchError like the
    scorer when a study item's episode id disagrees with grade.json, ValueError for a run directory without a
    batch directory above it (the batch name would be empty)."""
    run_dir = _abs(run_dir)
    if not run_dir.name or not run_dir.parent.name:
        raise ValueError(f"{run_dir}: a run directory must be <batch>/<run>; there is no batch name here")
    grade = _json_file(run_dir / "grade.json")
    grade = grade if isinstance(grade, dict) else {}
    eid_path = run_dir / "episode_id"
    episode_id = (eid_path.read_text().strip() if eid_path.exists() else "") or grade.get("episode") or ""
    pq = (grade.get("budget") or {}).get("probe_query") or {}
    out = OrderedDict((k, None) for k in CSV_COLUMNS)
    out.update(run=run_dir.name, batch=run_dir.parent.name, episode=SN.split_episode_id(episode_id)[0],
               arm=SN.arm_of(episode_id, grade.get("access"), pq.get("limit")) if episode_id else "other")
    private = OrderedDict(run=out["run"], batch=out["batch"], episode=out["episode"], episode_id=episode_id,
                          arm=out["arm"], substrate=None, hard_slots=None, log=None, problems=[], slots=[])
    out["private"] = private

    def done(log):
        out["log"] = private["log"] = log
        private.update((k, out[k]) for k in CSV_COLUMNS if k not in private)
        return out

    if answer is None:
        answer = _json_file(run_dir / "answer.json")
    if not isinstance(answer, dict) or not isinstance(answer.get("probes"), list):
        return done("no_answer")
    try:
        substrate = private["substrate"] = substrate_of(answer)
    except ValueError:
        return done("unsupported_substrate")
    cols = list(FEATURES[substrate])
    hard = private["hard_slots"] = [int(j) for j in hard_slots(answer)]
    slot_mains = {j: mains_of(answer["probes"][j]) for j in hard}
    if any(m not in cols for ms in slot_mains.values() for m in ms):
        return done("unsupported_substrate")
    hard = private["hard_slots"] = [j for j in hard if slot_mains[j]]
    status = None
    if not hard:
        status = "no_hard_slot"
    elif grade.get("hard_slots") is not None and sorted(int(j) for j in grade["hard_slots"]) != sorted(hard):
        status = "hard_slot_mismatch"

    charged = _charged_log_calls(run_dir)
    ft_path = run_dir / "fulltext.jsonl"
    if ft_path.exists():
        records, problems = read_fulltext(ft_path)
        if charged is not None and not _log_agrees(charged, records):
            problems.append("log_mismatch")
    elif charged is not None and not charged:
        records, problems = [], []
        status = status or "no_calls"
    else:
        return done(status or "missing")
    private["problems"] = problems
    status = status or (problems[0] if problems else "ok")

    # descriptors of what was read
    per_main = []
    for j in hard:
        T = scored_texts(records, j)
        F = [list(flags_for(t["text"], substrate).values()) for t in T]
        slot = OrderedDict(probe=j, cols=cols, n_scored=len(T), n_distinct=len({t["sha256"] for t in T}),
                           texts=[dict(seq=t["seq"], index=t["index"], sha256=t["sha256"], logit=t["logit"],
                                       flags=f) for t, f in zip(T, F)], mains=[])
        for main in slot_mains[j]:
            parent = PARENTS[substrate].get(main)
            res = s3_from_flags(F, cols, main, parent)
            res.update(main=main, parent=parent,
                       pair_texts=[dict(seq=T[i]["seq"], index=T[i]["index"], sha256=T[i]["sha256"])
                                   for i in res["pair"]] if res["pair"] else None)
            slot["mains"].append(res)
            per_main.append(res)
        private["slots"].append(slot)
    ok_pq = [r for r in records if r["tool"] == "probe_query" and r["status"] == "ok"]
    own = [r for r in records if r["tool"] in SAE_TEXT_TOOLS and r["status"] == "ok" and r["texts"] is not None]
    logits = [t["logit"] for s in private["slots"] for t in s["texts"]]
    out.update(n_scored_hard=sum(s["n_scored"] for s in private["slots"]),
               n_distinct=sum(s["n_distinct"] for s in private["slots"]),
               main_varies=_all3([r["main_varies"] for r in per_main]),
               n_other_texts=sum(len(r["texts"]) for r in ok_pq if r["probe"] not in hard),
               n_own_text_sae_calls=len(own), n_own_text_sae_texts=sum(len(r["texts"]) for r in own),
               logit_min=min(logits) if logits else None, logit_max=max(logits) if logits else None)
    if status in ("ok", "no_calls"):
        out.update(s3a=_all3([r["s3a"] for r in per_main]), s3b=_all3([r["s3b"] for r in per_main]),
                   s3=_all3([r["s3"] for r in per_main]))
    return done(status)


# ---------------------------------------------------------------------------------------------------------
# directories and output files

def run_dirs(raws):
    """Run directories under the --raw arguments (a run directory, a batch directory or a parent of batch
    directories), each once, as absolute paths, sorted by (batch, run)."""
    found = {}
    for raw in raws:
        raw = _abs(raw)
        if not raw.is_dir():
            raise FileNotFoundError(f"not a directory: {raw}")
        if any((raw / f).is_file() for f in RUN_FILES):
            cands = [raw]
        else:
            cands = [d for b in ([raw] + sorted(c for c in raw.iterdir() if c.is_dir()))
                     for d in sorted(b.iterdir()) if d.is_dir() and any((d / f).is_file() for f in RUN_FILES)]
        for d in cands:
            found.setdefault(d.resolve(), d)
    return sorted(found.values(), key=lambda d: (d.parent.name, d.name))


def public_row(res):
    """The tracked CSV row of a code_run result: no property name, no text."""
    def cell(k):
        v = res.get(k)
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:.4f}"
        return int(v) if isinstance(v, bool) else v
    return OrderedDict((k, cell(k)) for k in CSV_COLUMNS)


def property_names_in(text):
    """Generator property names that occur in a text (case-insensitive substrings), sorted."""
    low = text.lower()
    return sorted(f for f in PROPERTY_NAMES if f.lower() in low)


def csv_text(results):
    """The tracked CSV as a string; raises ValueError if any generator property name occurs in it."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for res in results:
        w.writerow(public_row(res))
    text = buf.getvalue()
    if property_names_in(text):
        raise ValueError("the tracked CSV would contain a generator property name (in a run, batch or episode "
                         "name); nothing was written")
    return text


def require_untracked(path):
    """Refuse a private output directory that git would track: inside this repository it must be ignored
    (`git check-ignore`; without git, a path component must start with "private")."""
    p = Path(path).resolve()
    if ROOT != p and ROOT not in p.parents:
        return
    try:
        rc = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", str(p / "x")],
                            capture_output=True, timeout=30).returncode
    except (OSError, subprocess.SubprocessError):
        rc = None
    if rc not in (0, 1):
        rc = 0 if any(part.startswith("private") for part in p.relative_to(ROOT).parts) else 1
    if rc != 0:
        raise SystemExit(f"{path}: private output must go to a git-ignored directory (for example "
                         "results/private_1112/s3/)")


def write_private(results, out_dir):
    """One JSONL per batch in out_dir, one line per run (flags matrix with property names, pair, hashes)."""
    out_dir = Path(out_dir)
    require_untracked(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_batch = OrderedDict()
    for res in results:
        by_batch.setdefault(res["batch"], []).append(res["private"])
    paths = []
    for batch, recs in by_batch.items():
        path = out_dir / f"{batch}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in recs))
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------------------------------------
# detector validation sample

def allocate(n, sizes):
    """Split n draws evenly over strata {name: available}, moving what a small stratum cannot take to the
    others. -> {name: draws}, summing to min(n, total available)."""
    take = {s: 0 for s in sizes}
    left = min(max(int(n), 0), sum(sizes.values()))
    while left:
        open_ = [s for s in sorted(sizes) if take[s] < sizes[s]]
        share, extra = divmod(left, len(open_))
        for k, s in enumerate(open_):
            add = min(share + (k < extra), sizes[s] - take[s])
            take[s] += add
            left -= add
    return take


def validation_pool(dirs):
    """Distinct "ok" probe_query texts of the runs (any probe), per substrate, first occurrence in
    (batch, run, call) order. Runs without a readable answer.json or fulltext.jsonl are skipped."""
    pool, seen = {}, set()
    for d in dirs:
        d = _abs(d)
        answer = _json_file(d / "answer.json")
        if not isinstance(answer, dict) or not (d / "fulltext.jsonl").exists():
            continue
        try:
            substrate = substrate_of(answer)
            hard = hard_slots(answer)
        except (ValueError, KeyError, TypeError):
            continue
        records, _ = read_fulltext(d / "fulltext.jsonl")
        for r in records:
            if r["tool"] != "probe_query" or r["status"] != "ok":
                continue
            for k, (t, h) in enumerate(zip(r["texts"], r["sha256"])):
                if (substrate, h) in seen:
                    continue
                seen.add((substrate, h))
                pool.setdefault(substrate, []).append(dict(
                    substrate=substrate, batch=d.parent.name, run=d.name, seq=r["seq"], index=k,
                    probe=r["probe"], hard_probe=int(r["probe"] in hard), sha256=h, text=t))
    return pool


def validation_sample(dirs, n, seed):
    """N texts for hand checking, split evenly over substrates, seeded. -> (items with flags, meta). Item ids
    are assigned after a seeded shuffle, so id order carries no information."""
    pool = validation_pool(dirs)
    take = allocate(n, {s: len(v) for s, v in pool.items()})
    items = []
    for s in sorted(pool):
        items += random.Random(f"s3-validate:{seed}:{s}").sample(pool[s], take[s])
    random.Random(f"s3-validate:{seed}:order").shuffle(items)
    out = []
    for k, it in enumerate(items):
        out.append(OrderedDict(id=f"v{k:03d}", **it, normalised_differs=int(normalise(it["text"]) != it["text"]),
                               flags=flags_for(it["text"], it["substrate"])))
    meta = OrderedDict(requested=int(n), seed=seed, drawn=len(out), per_substrate=take,
                       pool={s: len(v) for s, v in sorted(pool.items())}, runs=len(list(dirs)),
                       normalisation='remove "\\r", strip trailing "\\n"')
    return out, meta


def existing_validation_files(out_dir):
    """The validation files already in out_dir (the blind one may hold hand labels)."""
    return [Path(out_dir) / f for f in VALIDATE_FILES if (Path(out_dir) / f).exists()]


def write_validation(items, meta, out_dir, force=False):
    """Write the three validation files. Raises FileExistsError, before writing anything, if one of them is
    already there and `force` is not set: the labeller fills the blind file in place."""
    out_dir = Path(out_dir)
    require_untracked(out_dir)
    have = existing_validation_files(out_dir)
    if have and not force:
        raise FileExistsError(f"{', '.join(str(p) for p in have)} already there (hand labels would be lost); "
                              "give another --out, or --force to overwrite")
    out_dir.mkdir(parents=True, exist_ok=True)
    flags, blind, meta_path = (out_dir / f for f in VALIDATE_FILES)
    flags.write_text("".join(json.dumps(it) + "\n" for it in items))
    blind.write_text("".join(json.dumps(OrderedDict(
        id=it["id"], substrate=it["substrate"], text=it["text"],
        labels=OrderedDict((f, None) for f in FEATURES[it["substrate"]]))) + "\n" for it in items))
    meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    return flags, blind, meta_path


# ---------------------------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", action="append", required=True, help="run, batch or parent directory (repeatable)")
    ap.add_argument("--out-csv", help="tracked CSV, one row per run (no property names, no texts)")
    ap.add_argument("--private-out", help="private directory for the per-run detail (one JSONL per batch)")
    ap.add_argument("--validate-sample", type=int, metavar="N", help="draw N logged texts for hand checking")
    ap.add_argument("--seed", default="0", help="seed of --validate-sample")
    ap.add_argument("--out", help="private directory for the --validate-sample files")
    ap.add_argument("--force", action="store_true",
                    help="--validate-sample: overwrite validation files already in --out (hand labels are lost)")
    args = ap.parse_args(argv)
    dirs = run_dirs(args.raw)
    if args.validate_sample is not None:
        if not args.out:
            ap.error("--validate-sample needs --out <private dir>")
        if existing_validation_files(args.out) and not args.force:
            ap.error(f"{args.out} already holds validation files (hand labels would be lost); give another "
                     "--out, or --force to overwrite")
        items, meta = validation_sample(dirs, args.validate_sample, args.seed)
        paths = write_validation(items, meta, args.out, force=args.force)
        print(f"{meta['drawn']} of {meta['requested']} texts drawn from {meta['runs']} runs "
              f"(per substrate {meta['per_substrate']}; pool {meta['pool']})")
        for p in paths:
            print(f"wrote {p}")
        return 0
    if not args.out_csv:
        ap.error("give --out-csv (or --validate-sample N --out <private dir>)")
    if args.private_out:
        require_untracked(args.private_out)
    results = [code_run(d) for d in dirs]
    text = csv_text(results)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_csv.write_text(text)
    print(f"wrote {out_csv} ({len(results)} runs)")
    if args.private_out:
        for p in write_private(results, args.private_out):
            print(f"wrote {p}")
    logs = Counter(r["log"] for r in results)
    print("log: " + ", ".join(f"{k} {v}" for k, v in sorted(logs.items())))
    by_arm = OrderedDict()
    for r in results:
        if r["s3"] is not None:
            by_arm.setdefault((r["batch"], r["arm"]), []).append(r)
    for (batch, arm), rs in by_arm.items():
        print(f"{batch} {arm}: S3 {sum(r['s3'] for r in rs)}/{len(rs)} "
              f"(a {sum(r['s3a'] for r in rs)}, b {sum(r['s3b'] for r in rs)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
