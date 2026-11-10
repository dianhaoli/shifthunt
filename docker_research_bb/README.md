# `rl-task-shifthunt-r1112`: the black-box study image

A thin layer on the main-study image `rl-task-shifthunt-r1103` that replaces only the files this study changed
(plan rev 2.2 §8; DECISIONS D1, D15). Bank, weights, daemon venv, both agent CLIs, `/entrypoint.sh` and every
other module are inherited byte-identical.

| File | What it is |
|---|---|
| `Dockerfile` | `FROM rl-task-shifthunt-r1103` plus one `COPY` per replaced file and image path. Generated; `build.sh` refuses to build if it is not exactly the list the commit needs. |
| `build.sh` | `build.sh <public-commit>`: exports the commit with `git archive`, plans the layer, builds untagged, checks the image, then tags it. `--plan` prints the plan only; `--write-dockerfile` regenerates the Dockerfile. |
| `plan_layer.py` | Which files differ from the base image (sha256 of the commit's file against the file inside the image). Pure; tested in `tests/test_blackbox_layer.py`. |
| `verify_in_image.py` | Piped into the built image by `build.sh`: the replaced files compile, the modules import (daemon venv as user `toolsrv`, grader python as root), and no replaced file uses a name the image's other modules lack. |
| `r1112_env.sh` | The launch environment (no secret in it). `scripts/blackbox_sync_private.sh` installs it as `tasks/shifthunt/scripts/r1112_env.sh` in the private harness tree. |

## Commands (GPU box, from the public repo root)

```bash
export PY=/home/ec2-user/onsite/grader-wt/.venv/bin/python
scripts/blackbox_net_isolation.sh                  # once per boot: firewall rules of the main study; --check to verify
docker_research_bb/build.sh <public-commit>        # builds and tags rl-task-shifthunt-r1112 (label shifthunt.commit)
scripts/blackbox_sync_private.sh <public-commit>   # private tree: replaced image files, collector, env file, problems.txt
$PY scripts/blackbox_image_check.py --quick        # zero-API checks, 2 items (about 10 min of GPU)
$PY scripts/blackbox_image_check.py                # all 24 PROBLEMs and the oracle runs (about 30 min of GPU)
```

`blackbox_image_check.py` takes `/tmp/shifthunt-gpu.lock` itself; do not wrap it in `flock`.

## Rules the tooling enforces

- The build context is a commit, never the working tree. A tracked image source that differs in the working
  tree from the commit stops the build (`--allow-dirty` builds the commit anyway and labels the image dirty).
- A file is replaced only if its sha256 differs from the file inside the base image. Three modules differ
  from the public tree only by a rename (`D_RESID` here, `D_MODEL` in the image); they are left alone, and a
  replaced file that mentions `D_RESID` is an error. A new `shifthunt/*.py` module that no replaced file
  imports (a host-side analysis module) is not copied.
- The image is tagged only after: base layers are a prefix of the new image's and the config is equal; every
  replaced file has the commit's sha256 and every other code file the base image's; owners, modes and the set
  of paths under the code directories are those of the base image; the agent user can read none of the
  replaced files; the import and name checks pass.
- Nothing is deleted: a build that fails a check leaves an untagged image, and a rebuild leaves the previous
  `r1112` image untagged.
