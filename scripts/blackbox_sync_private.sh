#!/usr/bin/env bash
# Bring the private harness tree (tasks/shifthunt, branch research-1112) in line with a public commit and with
# the image rl-task-shifthunt-r1112, for the black-box study's launches (DECISIONS D1, D15).
#
#   scripts/blackbox_sync_private.sh <public-commit>            copy what differs, print what changed
#   scripts/blackbox_sync_private.sh --check <public-commit>    change nothing; exit 1 if anything differs
#   ... --worktree scripts/collect_rollouts.py ...              take that host-side file from the working tree
#                                                               (before it is committed; reported loudly)
#
# It writes ONLY these files of the private tree, and never commits there:
#   - the image files the thin layer replaced (the image's shifthunt.replaced label, e.g. shifthunt/reward.py,
#     shifthunt/toolserver.py, grader/grader.py, task.py), so the private tree matches the image;
#   - scripts/collect_rollouts.py (the launcher calls the private copy) and scripts/r1112_env.sh (from
#     docker_research_bb/r1112_env.sh);
#   - problems.txt: the 18 new PROBLEM lines are APPENDED if missing (the file is never overwritten: it has
#     lines the public one lacks). scripts/launch_rollouts.py of the private tree is used as it is.
# Checks: the image exists, is not dirty, and already holds <public-commit>'s image code (planning the layer for
# that commit against the image itself leaves nothing to copy; otherwise rebuild first); afterwards every image source file of the private tree has the sha256 of the file
# inside the image, and every PROBLEM of the committed run orders is a line of the private problems.txt.
# The private repository must be on branch research-1112; from research-1103 the branch is created first.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
PRIV_REPO=${PRIV_REPO:-/home/ec2-user/onsite/sub}
PRIV=$PRIV_REPO/tasks/shifthunt
IMAGE=rl-task-shifthunt-r1112
BRANCH=research-1112
PARENT_BRANCH=research-1103
PY=${PY:-python3}
ITEMS="ep411 ep413 ep415 ep472 ep474 ep476"
NEW_ARMS="blackbox blackbox64 open64"
# host-side files: "<path in the public commit>:<path under tasks/shifthunt>"
HOST_FILES="scripts/collect_rollouts.py:scripts/collect_rollouts.py docker_research_bb/r1112_env.sh:scripts/r1112_env.sh"

check=0; commit=; worktree=" "
while [ $# -gt 0 ]; do
    case "$1" in
        --check) check=1 ;;
        --worktree) shift; worktree="$worktree$1 " ;;
        -*) echo "blackbox_sync_private.sh: unknown option $1" >&2; exit 2 ;;
        *) [ -z "$commit" ] || { echo "blackbox_sync_private.sh: one commit only" >&2; exit 2; }; commit=$1 ;;
    esac
    shift
done
[ -n "$commit" ] || { sed -n '2,8p' "$0" >&2; exit 2; }
SHA=$(git -C "$REPO" rev-parse --verify --quiet "$commit^{commit}") || { echo "not a commit: $commit" >&2; exit 2; }
die() { echo "blackbox_sync_private.sh: $*" >&2; exit 1; }
sha_of() { sha256sum "$1" | cut -d' ' -f1; }

# ---- the image and its commit
docker image inspect "$IMAGE" >/dev/null 2>&1 || die "image $IMAGE not found: run docker_research_bb/build.sh $SHA first"
IMG_SHA=$(docker image inspect -f '{{index .Config.Labels "shifthunt.commit"}}' "$IMAGE")
REPLACED=$(docker image inspect -f '{{index .Config.Labels "shifthunt.replaced"}}' "$IMAGE" | tr ',' ' ')
[[ "$IMG_SHA" =~ ^[0-9a-f]{40}$ ]] || die "image $IMAGE has no clean shifthunt.commit label ('$IMG_SHA'): rebuild it"
[ -n "$REPLACED" ] || die "image $IMAGE has no shifthunt.replaced label: rebuild it with docker_research_bb/build.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# Is the image current for <public-commit>? Plan the layer for that commit against the IMAGE ITSELF
# (docker_research_bb/plan_layer.py): any file it would still copy means the image is stale.
PLAN="$PY $REPO/docker_research_bb/plan_layer.py"
SOURCES=$("$PY" -c "import sys; sys.path.insert(0, '$REPO/docker_research_bb'); import plan_layer; print(' '.join(plan_layer.SOURCES))")
mkdir "$TMP/ctx"
# shellcheck disable=SC2086
git -C "$REPO" archive "$SHA" $(git -C "$REPO" ls-tree -r --name-only "$SHA" -- $SOURCES) | tar -x -C "$TMP/ctx"
$PLAN --src "$TMP/ctx" --paths > "$TMP/paths"
docker run --rm -i --network none --entrypoint bash "$IMAGE" -c \
    'while IFS= read -r f; do if [ -f "$f" ]; then sha256sum "$f"; else echo "-  $f"; fi; done' < "$TMP/paths" > "$TMP/image.sha"
$PLAN --src "$TMP/ctx" --base-listing "$TMP/image.sha" > "$TMP/plan"
stale=$(awk -F'\t' '$1 == "copy" {print $2}' "$TMP/plan" | sort -u | paste -sd' ' -)
[ -z "$stale" ] || die "image $IMAGE (built from $IMG_SHA) does not hold these files of $SHA: $stale. Rebuild: docker_research_bb/build.sh $SHA"
echo "public commit $SHA; image $IMAGE $(docker image inspect -f '{{.Id}}' "$IMAGE") built from $IMG_SHA"
echo "image is current for $SHA: $(awk -F'\t' '$1 == "same"' "$TMP/plan" | wc -l) image paths identical, $(awk -F'\t' '$1 == "rename-only"' "$TMP/plan" | wc -l) differ only by the public tree's rename, $(awk -F'\t' '$1 == "new-unused"' "$TMP/plan" | wc -l) are new modules the image does not need"

# ---- the private branch
cur=$(git -C "$PRIV_REPO" branch --show-current)
if [ "$cur" != "$BRANCH" ]; then
    [ "$cur" = "$PARENT_BRANCH" ] || die "private repo is on branch '$cur'; expected $BRANCH (or $PARENT_BRANCH to create it from)"
    git -C "$PRIV_REPO" show-ref --verify --quiet "refs/heads/$BRANCH" && die "branch $BRANCH exists but $PARENT_BRANCH is checked out: switch to it by hand"
    if [ "$check" = 1 ]; then echo "DIFFERS: private repo is on $PARENT_BRANCH, branch $BRANCH not created yet"; fail=1
    else git -C "$PRIV_REPO" checkout -q -b "$BRANCH"; echo "created branch $BRANCH from $PARENT_BRANCH ($(git -C "$PRIV_REPO" rev-parse --short HEAD)) in $PRIV_REPO"; fi
fi
fail=${fail:-0}; changed=0

sync_file() {  # sync_file <public path> <private path relative to tasks/shifthunt>
    local src=$1 dst=$PRIV/$2 from="commit ${SHA:0:12}" old was
    case "$worktree" in
        *" $src "*) cp "$REPO/$src" "$TMP/new"; from="WORKING TREE (uncommitted)"
            if git -C "$REPO" show "$SHA:$src" > "$TMP/committed" 2>/dev/null && cmp -s "$TMP/new" "$TMP/committed"; then
                from="commit ${SHA:0:12} (working tree identical)"; fi ;;
        *) git -C "$REPO" show "$SHA:$src" > "$TMP/new" 2>/dev/null || die "$src is not in commit $SHA (not committed yet? use --worktree $src)" ;;
    esac
    if [ -f "$dst" ] && cmp -s "$TMP/new" "$dst"; then
        echo "  unchanged  $2  $(sha_of "$dst")  [= $from]"; return
    fi
    if [ "$check" = 1 ]; then echo "  DIFFERS    $2  private $([ -f "$dst" ] && sha_of "$dst" || echo absent)  wanted $(sha_of "$TMP/new")  [$from]"; fail=1; return; fi
    if [ ! -f "$dst" ]; then old=absent; was="new file"
    else
        old=$(sha_of "$dst")
        if git -C "$PRIV_REPO" show "HEAD:tasks/shifthunt/$2" 2>/dev/null | cmp -s - "$dst"; then was="was the committed $(git -C "$PRIV_REPO" rev-parse --short HEAD) version"
        else was="was already modified in the working tree"; fi
    fi
    cat "$TMP/new" > "$dst"
    changed=$((changed + 1))
    echo "  UPDATED    $2  $old -> $(sha_of "$dst")  [$from; $was]"
}

echo "image files (the layer's list: $REPLACED):"
for f in $REPLACED; do
    case "$worktree" in *" $f "*) die "--worktree is for host-side files only; $f is in the image" ;; esac
    sync_file "$f" "$f"
done
echo "host-side files:"
for pair in $HOST_FILES; do sync_file "${pair%%:*}" "${pair##*:}"; done

# ---- problems.txt: append the missing new PROBLEM lines
P=$PRIV/problems.txt
echo "problems.txt ($(wc -l < "$P") lines before):"
missing=
for ep in $ITEMS; do for arm in $NEW_ARMS; do
    grep -qxF "$ep-$arm" "$P" || missing="$missing $ep-$arm"
done; done
if [ -z "$missing" ]; then echo "  unchanged  all 18 new PROBLEM lines present"
elif [ "$check" = 1 ]; then echo "  DIFFERS    missing lines:$missing"; fail=1
else
    [ -z "$(tail -c1 "$P")" ] || echo >> "$P"   # make sure the last line is terminated before appending
    for p in $missing; do echo "$p" >> "$P"; done
    changed=$((changed + 1))
    echo "  APPENDED   $(echo $missing | wc -w) lines:$missing"
fi
for csv in pilots block1 block2; do
    git -C "$REPO" show "$SHA:results/blackbox_1112/runorder_$csv.csv" 2>/dev/null | awk -F, 'NR > 1 {print $7}' | sort -u > "$TMP/problems" || true
    n=0; bad=
    while IFS= read -r p; do n=$((n + 1)); grep -qxF "$p" "$P" || bad="$bad $p"; done < "$TMP/problems"
    if [ -n "$bad" ]; then echo "  DIFFERS    runorder_$csv.csv PROBLEMs not in the private problems.txt:$bad"; fail=1
    else echo "  ok         runorder_$csv.csv: all $n distinct PROBLEMs are lines of the private problems.txt"; fi
done

# ---- the private tree must now equal the image, file by file (every image path, copied by the layer or not)
n=0; bad=0
while IFS=$'\t' read -r status source dest _ _ sha base; do
    [ "$status" = new-unused ] && continue      # not in the image; the private tree does not need it either
    n=$((n + 1))
    have=$([ -f "$PRIV/$source" ] && sha_of "$PRIV/$source" || echo absent)
    if [ "$base" != "$have" ]; then bad=$((bad + 1)); echo "  DIFFERS    $source: private $have, image $dest $base"; fi
done < "$TMP/plan"
if [ "$bad" = 0 ]; then echo "private tree == image $IMAGE for all $n image paths ($(awk -F'\t' '$1 != "new-unused" {print $2}' "$TMP/plan" | sort -u | wc -l) source files)"
else fail=1; echo "private tree differs from the image in $bad of $n image paths"; fi

if [ "$fail" != 0 ]; then echo "RESULT: NOT in sync"; exit 1; fi
if [ "$check" = 1 ]; then echo "RESULT: in sync (nothing checked needs a change)"
else echo "RESULT: in sync; $changed file(s) written in $PRIV (nothing committed there)"; fi
