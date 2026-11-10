#!/usr/bin/env bash
# Build the black-box study image rl-task-shifthunt-r1112 = rl-task-shifthunt-r1103 + the files a public commit
# changed (plan rev 2.2 section 8; DECISIONS D1, D15).
#
#   docker_research_bb/build.sh [--allow-dirty] <public-commit>      build, verify, tag
#   docker_research_bb/build.sh --plan <public-commit>               print the plan, build nothing
#   docker_research_bb/build.sh --write-dockerfile <public-commit>   rewrite ./Dockerfile for that commit
#
# The build context is a `git archive` of the commit, never the working tree. Files to copy = candidates of
# plan_layer.py whose sha256 differs from the file inside the base image. The image is built untagged, then
# checked, and only tagged if every check passes:
#   1. the base image's layers are a prefix of the new image's, and its config (env, entrypoint, user) is equal;
#   2. inside the image every copied file has the commit's sha256 and every other candidate path has the base
#      image's; owners, modes and the set of paths under the code directories are those of the base image;
#   3. the agent user cannot read any path it could not read in the base image;
#   4. the copied files compile and the modules import, as user toolsrv with the daemon venv and as root with
#      the grader's python, and no copied file uses a name the image's other modules lack (verify_in_image.py).
# "Dirty" means: a tracked file under the image's source paths (or this directory) differs in the working tree
# from the commit. The build then stops, because what is on disk is not what would be built; --allow-dirty
# builds the commit anyway and labels the image shifthunt.dirty=true and shifthunt.commit=<sha>-dirty.
# Nothing is ever deleted: a build that fails a check leaves an untagged image behind (its id is printed).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
BASE=rl-task-shifthunt-r1103
TAG=rl-task-shifthunt-r1112
PY=${PY:-python3}
# code directories whose paths, owners and modes must not change (besides the copied files' content)
WATCH="/opt/toolsrv /grader /opt/toolsrv-admin /task.py /usr/local/bin /entrypoint.sh /run-agent-tmux.sh"

mode=build; allow_dirty=0; commit=
for arg in "$@"; do
    case "$arg" in
        --allow-dirty) allow_dirty=1 ;;
        --plan) mode=plan ;;
        --write-dockerfile) mode=write ;;
        -*) echo "build.sh: unknown option $arg" >&2; exit 2 ;;
        *) [ -z "$commit" ] || { echo "build.sh: one commit only" >&2; exit 2; }; commit=$arg ;;
    esac
done
[ -n "$commit" ] || { sed -n '2,8p' "$0" >&2; exit 2; }
SHA=$(git -C "$REPO" rev-parse --verify --quiet "$commit^{commit}") || { echo "build.sh: not a commit: $commit" >&2; exit 2; }
docker image inspect "$BASE" >/dev/null 2>&1 || { echo "build.sh: base image $BASE not found" >&2; exit 1; }
BASE_ID=$(docker image inspect -f '{{.Id}}' "$BASE")

SOURCES=$("$PY" -c "import sys; sys.path.insert(0, '$HERE'); import plan_layer; print(' '.join(plan_layer.SOURCES))")
dirty=false
# shellcheck disable=SC2086
if ! git -C "$REPO" diff --quiet "$SHA" -- $SOURCES docker_research_bb; then
    dirty=true
    if [ "$mode" = build ] && [ "$allow_dirty" != 1 ]; then
        echo "build.sh: tracked image sources differ in the working tree from $SHA:" >&2
        # shellcheck disable=SC2086
        git -C "$REPO" diff --stat "$SHA" -- $SOURCES docker_research_bb >&2
        echo "build.sh: commit them and build that commit, or pass --allow-dirty to build $SHA as it is" >&2
        exit 1
    fi
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/ctx"
# shellcheck disable=SC2086
FILES=$(git -C "$REPO" ls-tree -r --name-only "$SHA" -- $SOURCES)
# shellcheck disable=SC2086
git -C "$REPO" archive "$SHA" $FILES | tar -x -C "$TMP/ctx"

listing() {  # listing <image> <paths file> : "<sha256>  <path>" or "-  <path>" per line, read as root, no network
    docker run --rm -i --network none --entrypoint bash "$1" -c \
        'while IFS= read -r f; do if [ -f "$f" ]; then sha256sum "$f"; else echo "-  $f"; fi; done' < "$2"
}
meta() {  # meta <image> : owner, mode, type and path of everything under the code directories
    # shellcheck disable=SC2086
    docker run --rm --network none --entrypoint bash "$1" -c \
        "find $WATCH -xdev \\( -type f -o -type d -o -type l \\) -printf '%u:%g %m %y %p\\n' | LC_ALL=C sort"
}
readable() {  # readable <image> <paths file> : the paths the agent user (model) can read
    docker run --rm -i --network none --user model --entrypoint bash "$1" -c \
        'while IFS= read -r f; do if [ -r "$f" ]; then echo "$f"; fi; done' < "$2"
}

"$PY" "$HERE/plan_layer.py" --src "$TMP/ctx" --paths > "$TMP/paths"
listing "$BASE" "$TMP/paths" > "$TMP/base.sha"
"$PY" "$HERE/plan_layer.py" --src "$TMP/ctx" --base-listing "$TMP/base.sha" > "$TMP/plan"
echo "== plan for commit $SHA against $BASE ($BASE_ID)"
awk -F'\t' '{printf "  %-12s %-34s -> %s\n", $1, $2, $3}' "$TMP/plan"

if [ "$mode" = write ]; then
    "$PY" "$HERE/plan_layer.py" --src "$TMP/ctx" --base-listing "$TMP/base.sha" --dockerfile > "$HERE/Dockerfile"
    echo "wrote $HERE/Dockerfile"; exit 0
fi
"$PY" "$HERE/plan_layer.py" --src "$TMP/ctx" --base-listing "$TMP/base.sha" --check-dockerfile "$HERE/Dockerfile"
[ "$mode" = plan ] && exit 0

awk -F'\t' '$1 == "copy" {print $3}' "$TMP/plan" > "$TMP/copied"
REPLACED=$(awk -F'\t' '$1 == "copy" {print $2}' "$TMP/plan" | sort -u | paste -sd, -)
[ -s "$TMP/copied" ] || { echo "build.sh: nothing differs from $BASE; no image to build" >&2; exit 1; }
label_sha=$SHA; [ "$dirty" = true ] && label_sha="$SHA-dirty"

docker build --iidfile "$TMP/iid" -f "$HERE/Dockerfile" \
    --label "shifthunt.commit=$label_sha" --label "shifthunt.dirty=$dirty" \
    --label "shifthunt.base=$BASE" --label "shifthunt.base_id=$BASE_ID" \
    --label "shifthunt.replaced=$REPLACED" "$TMP/ctx"
IID=$(cat "$TMP/iid")
echo "== built $IID (untagged until the checks pass)"
fail() { echo "build.sh: CHECK FAILED: $*" >&2; echo "build.sh: image $IID was NOT tagged $TAG" >&2; exit 1; }

# 1. layers and config
"$PY" - "$BASE" "$IID" <<'EOF' || fail "layers or config differ from the base image"
import hashlib, json, subprocess, sys
def insp(image):
    return json.loads(subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True,
                                     check=True).stdout)[0]
base, new = insp(sys.argv[1]), insp(sys.argv[2])
bl, nl = base["RootFS"]["Layers"], new["RootFS"]["Layers"]
ok = nl[:len(bl)] == bl and len(nl) > len(bl)
print(f"  layers: base {len(bl)}, new {len(nl)} (+{len(nl) - len(bl)}), base is a prefix: {nl[:len(bl)] == bl}")
for k in ("Env", "Entrypoint", "Cmd", "User", "WorkingDir", "Volumes", "ExposedPorts"):
    same = base["Config"].get(k) == new["Config"].get(k)  # values are not printed
    h = hashlib.sha256(json.dumps(new["Config"].get(k), sort_keys=True).encode()).hexdigest()[:12]
    print(f"  config {k}: {'same' if same else 'DIFFERENT'} (sha256 {h})")
    ok = ok and same
sys.exit(0 if ok else 1)
EOF

# 2. file content, owners, modes, path set
listing "$IID" "$TMP/paths" > "$TMP/new.sha"
echo "== sha256 of every candidate path: commit / new image / base image"
"$PY" - "$TMP/plan" "$TMP/new.sha" <<'EOF' || fail "file content inside the image is not what the plan says"
import sys
new = {}
for line in open(sys.argv[2]):
    digest, path = line.split(None, 1)
    new[path.strip()] = digest
bad = 0
for line in open(sys.argv[1]):
    status, source, dest, chown, chmod, sha, base = line.rstrip("\n").split("\t")
    want = sha if status == "copy" else base
    ok = new.get(dest) == want
    bad += not ok
    if status == "copy" or not ok:
        print(f"  {'ok ' if ok else 'BAD'} {status:11s} {dest}\n      commit {sha}\n      image  {new.get(dest)}\n      base   {base}")
print(f"  {sum(1 for l in open(sys.argv[1]))} candidate paths, {bad} mismatch(es); uncopied paths equal the base image")
sys.exit(1 if bad else 0)
EOF
meta "$BASE" > "$TMP/base.meta"
meta "$IID" > "$TMP/new.meta"
if ! diff "$TMP/base.meta" "$TMP/new.meta" > "$TMP/meta.diff"; then
    cat "$TMP/meta.diff" >&2; fail "owners, modes or the set of paths under [$WATCH] differ from the base image"
fi
echo "== owners/modes: $(wc -l < "$TMP/new.meta") paths under [$WATCH] identical to the base image; copied files:"
while IFS= read -r f; do
    awk -v f="$f" '$4 == f {found = 1; printf "  %-14s %s %s\n", $1, $2, $4} END {exit !found}' "$TMP/new.meta" \
        || fail "copied file $f is not under the checked directories"
done < "$TMP/copied"

# 3. what the agent user can read
readable "$BASE" "$TMP/paths" > "$TMP/base.readable"
readable "$IID" "$TMP/paths" > "$TMP/new.readable"
diff "$TMP/base.readable" "$TMP/new.readable" >&2 || fail "the agent user can read different paths than in the base image"
if grep -F -x -f "$TMP/copied" "$TMP/new.readable"; then fail "the agent user can read a copied file"; fi
echo "== agent user (model) can read $(wc -l < "$TMP/new.readable") of $(wc -l < "$TMP/paths") candidate paths, as in the base image; none of the copied files"

# 4. compile, import, names
# shellcheck disable=SC2046
docker run --rm -i --network none --user toolsrv --entrypoint /opt/toolsrv-venv/bin/python "$IID" -B -I - daemon \
    $(cat "$TMP/copied") < "$HERE/verify_in_image.py" || fail "daemon-side import check"
# shellcheck disable=SC2046
docker run --rm -i --network none --entrypoint python3 "$IID" -B - grader \
    $(cat "$TMP/copied") < "$HERE/verify_in_image.py" || fail "grader-side import check"
meta "$IID" | diff - "$TMP/new.meta" >/dev/null || fail "internal: image listing not reproducible"

OLD=$(docker image inspect -f '{{.Id}}' "$TAG" 2>/dev/null || true)
docker tag "$IID" "$TAG"
[ -n "$OLD" ] && [ "$OLD" != "$IID" ] && echo "== note: $TAG previously pointed to $OLD (still present, untagged)"
echo "== tagged $TAG"
echo "image id: $IID"
echo "labels:   shifthunt.commit=$label_sha shifthunt.dirty=$dirty shifthunt.base_id=$BASE_ID"
echo "replaced: $REPLACED"
