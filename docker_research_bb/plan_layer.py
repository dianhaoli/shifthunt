#!/usr/bin/env python3
"""Which files of a public commit the thin image layer must replace (used by build.sh; pure, stdlib only).

    plan_layer.py --src <exported commit dir> --base-listing <file> [--dockerfile | --copied]

`--base-listing` is the output of LISTING_CMD run in the base image (rl-task-shifthunt-r1103): one line per
image path, `<sha256>  <path>` or `-  <path>` for a path that does not exist there.

Every file of the commit that the main-study Dockerfile copies into the image is a candidate (candidates()):
shifthunt/*.py goes to BOTH /opt/toolsrv/shifthunt (root:toolsrv 750, the daemon's copy) and /grader/shifthunt
(root 700, the grader's copy); grader/* to /grader; task.py; prompt.md and the two daemon admin scripts to
/opt/toolsrv-admin; the tool client. A candidate is

  same         its sha256 equals the file in the base image: not copied;
  rename-only  it equals the base file after undoing the public tree's renames (RENAMES: the public tree says
               D_RESID where the image says D_MODEL, in three modules this study did not touch): not copied, so
               the image keeps the main study's bytes;
  new-unused   a shifthunt/*.py file that the base image does not have and that no copied file imports
               (directly or through another new file), e.g. a host-side analysis module added to the package
               later: not copied, the image does not need it;
  copy         anything else (changed, or new and imported): copied with the owner and mode of its row.

A copied file must not mention a public-only name (the left side of RENAMES): it would fail at run time against
the uncopied modules. That is an error here; the build also imports the modules inside the image.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

BASE_IMAGE = "rl-task-shifthunt-r1103"
RENAMES = (("D_RESID", "D_MODEL"),)  # (public tree, image)
# (source dir or file in the commit, image dir or file, chown, chmod): the COPY lines of the main-study
# Dockerfile (tasks/shifthunt/Dockerfile lines 29-47). A source ending in "/" means every file directly in it.
ROWS = (
    ("shifthunt/", "/opt/toolsrv/shifthunt/", "root:toolsrv", "750"),
    ("shifthunt/", "/grader/shifthunt/", "root:root", "700"),
    ("grader/", "/grader/", "root:root", "700"),
    ("task.py", "/task.py", "root:root", "700"),
    ("prompt.md", "/opt/toolsrv-admin/prompt.md", "root:root", "700"),
    ("docker_toolsrv/start_toolsrv.py", "/opt/toolsrv-admin/start_toolsrv.py", "root:root", "700"),
    ("docker_toolsrv/stop_toolsrv.py", "/opt/toolsrv-admin/stop_toolsrv.py", "root:root", "700"),
    ("toolclient/tool", "/usr/local/bin/tool", "root:root", "755"),
)
SOURCES = tuple(dict.fromkeys(r[0].rstrip("/") for r in ROWS))  # what build.sh exports from the commit
HEADER = """\
# Black-box study image rl-task-shifthunt-r1112 (plan rev 2.2 section 8; DECISIONS D1, D15): the main-study image
# with ONLY the files this study changed, copied to their image paths with the owners and modes of the
# main-study Dockerfile. Bank, weights, daemon venv, both agent CLIs, /entrypoint.sh and every other module are
# inherited byte-identical.
#
# Do not build this file directly: ./build.sh <public-commit> exports that commit with `git archive`, works
# out the changed files against the base image (plan_layer.py), refuses to build unless the COPY lines below
# are exactly that list, labels the image with the commit and checks hashes, owners, modes and imports inside
# the built image before tagging it. Regenerate the COPY lines with ./build.sh --write-dockerfile <commit>.
"""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def candidates(src):
    """[(source path relative to src, image path, chown, chmod)] for every candidate file present in `src`."""
    src, out = Path(src), []
    for source, dest, chown, chmod in ROWS:
        if source.endswith("/"):
            files = sorted(p for p in (src / source).glob("*") if p.is_file()) if (src / source).is_dir() else []
            out += [(f"{source}{p.name}", f"{dest}{p.name}", chown, chmod) for p in files]
        elif (src / source).is_file():
            out.append((source, dest, chown, chmod))
    return out


def parse_listing(text):
    """LISTING_CMD output -> {image path: sha256 or None}."""
    base = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        base[path.strip()] = None if digest == "-" else digest
    return base


def undo_renames(data):
    for public, image in RENAMES:
        data = data.replace(public.encode(), image.encode())
    return data


def classify(data, base_sha):
    """same | rename-only | copy for a candidate with bytes `data` whose base-image file has sha `base_sha`."""
    if base_sha is not None and sha256(data) == base_sha:
        return "same"
    if base_sha is not None and sha256(undo_renames(data)) == base_sha:
        return "rename-only"
    return "copy"


def imports(data, stem):
    """True iff the Python source `data` has an import line that names the shifthunt module `stem`."""
    pat = re.compile(rb"^[ \t]*(?:from|import)\b[^\n#]*\b" + re.escape(stem.encode()) + rb"\b", re.M)
    return bool(pat.search(data))


def unused_new(sources):
    """Of the new shifthunt/*.py files, those that nothing copied imports. `sources` = {source path: (bytes,
    is_new, is_copied)}; a new file outside shifthunt/ always counts as needed."""
    new = {s for s, (_, is_new, _) in sources.items() if is_new and s.startswith("shifthunt/") and s.endswith(".py")}
    needed = {s for s, (_, is_new, copied) in sources.items() if copied and s not in new}
    grew = True
    while grew:
        grew = False
        for s in sorted(new - needed):
            stem = s[len("shifthunt/"):-3]
            if any(imports(sources[n][0], stem) for n in needed if n != s):
                needed.add(s)
                grew = True
    return new - needed


def plan(src, base):
    """-> [{"status", "source", "dest", "chown", "chmod", "sha256", "base_sha256"}], in ROWS order. Raises
    ValueError if the listing lacks a candidate's path or a copied file mentions a public-only name."""
    out, problems, sources = [], [], {}
    for source, dest, chown, chmod in candidates(src):
        if dest not in base:
            raise ValueError(f"base listing has no line for {dest}")
        data = (Path(src) / source).read_bytes()
        status = classify(data, base[dest])
        was = sources.get(source, (data, True, False))
        sources[source] = (data, was[1] and base[dest] is None, was[2] or status == "copy")
        out.append({"status": status, "source": source, "dest": dest, "chown": chown, "chmod": chmod,
                    "sha256": sha256(data), "base_sha256": base[dest]})
    unused = unused_new(sources)
    for r in out:
        if r["source"] in unused and r["base_sha256"] is None:
            r["status"] = "new-unused"
        if r["status"] == "copy":
            data = sources[r["source"]][0]
            problems += [f"{r['source']} mentions {public}, which only the public tree's uncopied modules define "
                         f"(the image says {image})" for public, image in RENAMES if public.encode() in data]
    if problems:
        raise ValueError("; ".join(sorted(set(problems))))
    return out


def copy_lines(rows):
    """The Dockerfile COPY lines for the plan's `copy` rows: one file to one explicit file path each, so no
    directory of the base image is touched."""
    lines = []
    for r in rows:
        if r["status"] != "copy":
            continue
        owner = "" if r["chown"] == "root:root" else f"--chown={r['chown']} "
        lines.append(f"COPY {owner}--chmod={r['chmod']} {r['source']} {r['dest']}")
    return lines


def dockerfile(rows):
    return HEADER + f"FROM {BASE_IMAGE}\n" + "".join(l + "\n" for l in copy_lines(rows))


def instructions(text):
    """A Dockerfile's instruction lines (comments and blank lines dropped), for comparing two Dockerfiles."""
    return [l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]


def listing_paths(src):
    """Every image path the base listing must cover for this commit."""
    return [c[1] for c in candidates(src)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True)
    ap.add_argument("--base-listing")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--paths", action="store_true", help="print the image paths the base listing must cover")
    g.add_argument("--dockerfile", action="store_true", help="print the Dockerfile for this plan")
    g.add_argument("--check-dockerfile", metavar="FILE", help="exit 1 unless FILE has exactly this plan's lines")
    a = ap.parse_args(argv)
    if a.paths:
        print("\n".join(listing_paths(a.src)))
        return 0
    try:
        rows = plan(a.src, parse_listing(Path(a.base_listing).read_text()))
    except ValueError as e:
        print(f"plan_layer: {e}", file=sys.stderr)
        return 1
    if a.dockerfile:
        sys.stdout.write(dockerfile(rows))
    elif a.check_dockerfile:
        have, want = instructions(Path(a.check_dockerfile).read_text()), instructions(dockerfile(rows))
        if have != want:
            print(f"plan_layer: {a.check_dockerfile} does not match the files that differ from {BASE_IMAGE}.\n"
                  "  Dockerfile has:\n" + "".join(f"    {l}\n" for l in have)
                  + "  this commit needs:\n" + "".join(f"    {l}\n" for l in want), file=sys.stderr, end="")
            return 1
    else:  # the plan, tab separated: status source dest chown chmod sha256 base_sha256
        for r in rows:
            print("\t".join([r["status"], r["source"], r["dest"], r["chown"], r["chmod"], r["sha256"],
                             r["base_sha256"] or "-"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
