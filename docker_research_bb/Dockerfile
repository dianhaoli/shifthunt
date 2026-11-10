# Black-box study image rl-task-shifthunt-r1112 (plan rev 2.2 section 8; DECISIONS D1, D15): the main-study image
# with ONLY the files this study changed, copied to their image paths with the owners and modes of the
# main-study Dockerfile. Bank, weights, daemon venv, both agent CLIs, /entrypoint.sh and every other module are
# inherited byte-identical.
#
# Do not build this file directly: ./build.sh <public-commit> exports that commit with `git archive`, works
# out the changed files against the base image (plan_layer.py), refuses to build unless the COPY lines below
# are exactly that list, labels the image with the commit and checks hashes, owners, modes and imports inside
# the built image before tagging it. Regenerate the COPY lines with ./build.sh --write-dockerfile <commit>.
FROM rl-task-shifthunt-r1103
COPY --chown=root:toolsrv --chmod=750 shifthunt/reward.py /opt/toolsrv/shifthunt/reward.py
COPY --chown=root:toolsrv --chmod=750 shifthunt/toolserver.py /opt/toolsrv/shifthunt/toolserver.py
COPY --chmod=700 shifthunt/reward.py /grader/shifthunt/reward.py
COPY --chmod=700 shifthunt/toolserver.py /grader/shifthunt/toolserver.py
COPY --chmod=700 grader/grader.py /grader/grader.py
COPY --chmod=700 task.py /task.py
