"""docker_research_bb: which files the thin image layer replaces (plan_layer.py) and the in-image name check
(verify_in_image.py), on synthetic trees. No docker."""
import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BB = ROOT / "docker_research_bb"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", BB / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pl = _load("plan_layer")
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731

BASE_FILES = {
    "shifthunt/__init__.py": b"",
    "shifthunt/contract.py": b"MAX = 4\n",
    "shifthunt/reward.py": b"def reward():\n    return 0\n",
    "shifthunt/toolbackend.py": b"D_MODEL = 2304\nD_SAE = 16384\n",
    "shifthunt/toolserver.py": b"from .toolbackend import D_SAE\n",
    "grader/grader.py": b"from shifthunt import reward as R\n",
    "task.py": b"print('task')\n",
    "prompt.md": b"# prompt $tools_md\n",
    "docker_toolsrv/start_toolsrv.py": b"start = 1\n",
    "docker_toolsrv/stop_toolsrv.py": b"stop = 1\n",
    "toolclient/tool": b"#!/usr/bin/env python3\n",
}


def tree(tmp_path, changes=None, name="src"):
    files = {**BASE_FILES, "shifthunt/toolbackend.py": b"D_RESID = 2304\nD_SAE = 16384\n", **(changes or {})}
    for rel, data in files.items():
        if data is None:
            continue
        p = tmp_path / name / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return tmp_path / name


def base_listing(src, files=BASE_FILES):
    """The base image's listing for the candidate paths of `src`: every base file at each of its image paths."""
    by_source = {}
    for source, dest, _, _ in pl.candidates(src):
        by_source.setdefault(source, []).append(dest)
    lines = []
    for source, dests in by_source.items():
        for dest in dests:
            lines.append(f"{sha(files[source])}  {dest}" if source in files else f"-  {dest}")
    return pl.parse_listing("\n".join(lines) + "\n")


def statuses(rows):
    return {(r["source"], r["dest"]): r["status"] for r in rows}


def test_candidates_map_every_source_to_its_image_paths(tmp_path):
    src = tree(tmp_path)
    got = {(s, d): (o, m) for s, d, o, m in pl.candidates(src)}
    assert got[("shifthunt/toolserver.py", "/opt/toolsrv/shifthunt/toolserver.py")] == ("root:toolsrv", "750")
    assert got[("shifthunt/toolserver.py", "/grader/shifthunt/toolserver.py")] == ("root:root", "700")
    assert got[("grader/grader.py", "/grader/grader.py")] == ("root:root", "700")
    assert got[("task.py", "/task.py")] == ("root:root", "700")
    assert got[("prompt.md", "/opt/toolsrv-admin/prompt.md")] == ("root:root", "700")
    assert got[("toolclient/tool", "/usr/local/bin/tool")] == ("root:root", "755")
    assert len(got) == 2 * 5 + 6 and set(pl.SOURCES) >= {"shifthunt", "grader", "task.py", "prompt.md"}


def test_unchanged_tree_copies_nothing_and_the_rename_is_not_a_change(tmp_path):
    src = tree(tmp_path)
    rows = pl.plan(src, base_listing(src))
    st = statuses(rows)
    assert st[("shifthunt/toolbackend.py", "/opt/toolsrv/shifthunt/toolbackend.py")] == "rename-only"
    assert st[("shifthunt/toolbackend.py", "/grader/shifthunt/toolbackend.py")] == "rename-only"
    assert sorted(set(st.values())) == ["rename-only", "same"] and pl.copy_lines(rows) == []


def test_changed_files_are_copied_to_both_package_paths_with_owner_and_mode(tmp_path):
    src = tree(tmp_path, {"shifthunt/reward.py": b"def reward():\n    return 1\n", "task.py": b"print('new')\n"})
    rows = pl.plan(src, base_listing(src))
    assert pl.copy_lines(rows) == [
        "COPY --chown=root:toolsrv --chmod=750 shifthunt/reward.py /opt/toolsrv/shifthunt/reward.py",
        "COPY --chmod=700 shifthunt/reward.py /grader/shifthunt/reward.py",
        "COPY --chmod=700 task.py /task.py"]
    text = pl.dockerfile(rows)
    assert pl.instructions(text) == ["FROM rl-task-shifthunt-r1103"] + pl.copy_lines(rows)
    assert text.startswith("#") and "prompt.md" not in "\n".join(pl.instructions(text))


def test_a_copied_file_must_not_use_a_public_only_name(tmp_path):
    src = tree(tmp_path, {"shifthunt/toolserver.py": b"from .toolbackend import D_RESID\n"})
    with pytest.raises(ValueError, match="D_RESID"):
        pl.plan(src, base_listing(src))
    # a real change to a renamed module copies it (with its D_RESID): that is caught the same way
    src = tree(tmp_path, {"shifthunt/toolbackend.py": b"D_RESID = 2304\nD_SAE = 1\n"}, name="b")
    with pytest.raises(ValueError, match="D_RESID"):
        pl.plan(src, base_listing(src))


def test_new_module_is_copied_only_if_a_copied_file_imports_it(tmp_path):
    new = {"shifthunt/freetext_listing.py": b"X = 1\n", "shifthunt/helper.py": b"from . import deep\n",
           "shifthunt/deep.py": b"Y = 2\n"}
    src = tree(tmp_path, new)
    st = statuses(pl.plan(src, base_listing(src)))
    assert {v for (s, _), v in st.items() if s in new} == {"new-unused"}
    # imported by a changed file, and a second new module through the first: both needed, the third still not
    src = tree(tmp_path, {**new, "shifthunt/toolserver.py": b"from .toolbackend import D_SAE\nfrom .helper import a\n"},
               name="b")
    rows = pl.plan(src, base_listing(src))
    st = statuses(rows)
    for mod in ("helper", "deep", "toolserver"):
        assert st[(f"shifthunt/{mod}.py", f"/opt/toolsrv/shifthunt/{mod}.py")] == "copy"
        assert st[(f"shifthunt/{mod}.py", f"/grader/shifthunt/{mod}.py")] == "copy"
    assert st[("shifthunt/freetext_listing.py", "/grader/shifthunt/freetext_listing.py")] == "new-unused"
    # a mention outside an import line does not count
    assert not pl.imports(b"# see helper\nx = 'helper'\n", "helper")
    assert pl.imports(b"    from shifthunt import helper as h\n", "helper") and pl.imports(b"import shifthunt.helper\n", "helper")


def test_plan_against_the_built_image_tells_whether_it_is_current(tmp_path):
    """blackbox_sync_private.sh plans a commit against the image itself: nothing to copy = the image holds it."""
    changed = {"shifthunt/reward.py": b"def reward():\n    return 1\n"}
    src = tree(tmp_path, changed)
    built = {**BASE_FILES, **changed}                       # what the image has after the layer
    assert pl.copy_lines(pl.plan(src, base_listing(src, built))) == []
    later = tree(tmp_path, {**changed, "task.py": b"print('later')\n"}, name="later")
    assert pl.copy_lines(pl.plan(later, base_listing(later, built))) == ["COPY --chmod=700 task.py /task.py"]


def test_listing_must_cover_every_candidate(tmp_path):
    src = tree(tmp_path)
    listing = base_listing(src)
    del listing["/task.py"]
    with pytest.raises(ValueError, match="/task.py"):
        pl.plan(src, listing)


def test_check_dockerfile_cli(tmp_path, capsys):
    src = tree(tmp_path, {"task.py": b"print('new')\n"})
    listing = tmp_path / "base.sha"
    listing.write_text("".join(f"{d or '-'}  {p}\n" for p, d in base_listing(src).items()))
    good = tmp_path / "Dockerfile"
    assert pl.main(["--src", str(src), "--base-listing", str(listing), "--dockerfile"]) == 0
    good.write_text(capsys.readouterr().out)
    assert pl.main(["--src", str(src), "--base-listing", str(listing), "--check-dockerfile", str(good)]) == 0
    bad = tmp_path / "Dockerfile.bad"
    bad.write_text(good.read_text() + "COPY --chmod=700 prompt.md /opt/toolsrv-admin/prompt.md\n")
    assert pl.main(["--src", str(src), "--base-listing", str(listing), "--check-dockerfile", str(bad)]) == 1
    assert "does not match" in capsys.readouterr().err
    assert pl.main(["--src", str(src), "--paths"]) == 0
    assert "/opt/toolsrv/shifthunt/toolserver.py" in capsys.readouterr().out.splitlines()


def test_tracked_dockerfile_is_a_plan_layer_dockerfile():
    """The tracked Dockerfile has the generated header and base, and only single-file COPY lines to the image
    paths plan_layer knows, each with the row's owner and mode (build.sh checks the exact list per commit)."""
    text = (BB / "Dockerfile").read_text()
    assert text.startswith(pl.HEADER)
    ins = pl.instructions(text)
    assert ins[0] == f"FROM {pl.BASE_IMAGE}" and len(ins) > 1
    allowed = {}
    for source, dest, chown, chmod in pl.ROWS:
        allowed[(source, dest)] = (chown, chmod)
    for line in ins[1:]:
        parts = line.split()
        assert parts[0] == "COPY" and len(parts) in (4, 5), line
        source, dest = parts[-2], parts[-1]
        row = [(s, d) for (s, d) in allowed
               if (s.endswith("/") and source.startswith(s) and dest == d + source[len(s):]) or (s, d) == (source, dest)]
        assert len(row) == 1, line
        chown, chmod = allowed[row[0]]
        assert f"--chmod={chmod}" in parts and (("--chown=" + chown) in parts) == (chown != "root:root"), line


def test_env_file_has_the_study_settings_and_no_secret():
    text = (BB / "r1112_env.sh").read_text()
    for needle in ("source /home/ec2-user/onsite/.env", "export RL_TASK_IMAGE_SUFFIX=-r1112", "CODEX_EFFORT=max",
                   'OPENAI_API_KEY="$OPENAI_KEY"', "OPENAI_API_IP=172.66.0.243", "OPENAI_PRICES=1.0,0.05,1.25,5.0",
                   "export LAUNCH_PAUSE_FILE=results/rollouts/r1112_pause"):
        assert needle in text
    assert "sk-" not in text and "ANTHROPIC_API_KEY=" not in text


# ---------------------------------------------------------------- verify_in_image.py (in a subprocess)

def run_verify(tmp_path, files, mode="daemon"):
    root = tmp_path / "root"
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    paths = [str(root / rel) for rel in files if rel.endswith("toolserver.py") or rel.endswith("reward.py")]
    env = {**os.environ, "SHIFTHUNT_VERIFY_ROOT": str(root)}
    r = subprocess.run([sys.executable, "-B", "-I", "-", mode, *paths], input=(BB / "verify_in_image.py").read_text(),
                       capture_output=True, text=True, env=env, cwd=tmp_path)
    return r.returncode, r.stdout + r.stderr


PKG = {"shifthunt/__init__.py": "", "shifthunt/grader.py": "", "shifthunt/contract.py": "",
       "shifthunt/episode_files.py": "", "shifthunt/reward.py": "def reward():\n    return 1\n",
       "shifthunt/toolbackend.py": "D_MODEL = 1\nD_SAE = 2\nclass RealBackend: pass\n",
       "shifthunt/toolserver.py": ("from .toolbackend import D_SAE\nfrom . import reward as R\n\n"
                                   "def f():\n    from .toolbackend import RealBackend\n    return R.reward()\n")}


def test_verify_passes_on_a_consistent_package(tmp_path):
    code, out = run_verify(tmp_path, PKG)
    assert code == 0 and out.strip().endswith("ok") and "PROBLEM" not in out, out


@pytest.mark.parametrize("server, needle", [
    ("from .toolbackend import D_SAE\n\ndef f():\n    from .toolbackend import D_RESID\n", "has no 'D_RESID'"),
    ("from . import toolbackend as tb\n\ndef f():\n    return tb.D_RESID\n", "has no 'D_RESID'"),
    ("from shifthunt import reward as R\n\ndef f():\n    return R.naming_slot_pass([])\n", "has no 'naming_slot_pass'"),
    ("from .missing_module import x\n", "missing_module"),
    ("def f(:\n", "does not compile"),
])
def test_verify_catches_names_the_image_modules_lack(tmp_path, server, needle):
    """Each of these imports fine at module level or fails only when the code path runs; the static check
    reports them all."""
    code, out = run_verify(tmp_path, {**PKG, "shifthunt/toolserver.py": server})
    assert code == 1 and needle in out and "FAILED" in out, out


# ---------------------------------------------------------------- the shell tooling (static checks only)

SCRIPTS = (BB / "build.sh", ROOT / "scripts" / "blackbox_sync_private.sh", ROOT / "scripts" / "blackbox_net_isolation.sh")


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_shell_scripts_parse_and_are_executable(script):
    assert os.access(script, os.X_OK)
    r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_build_script_only_ever_tags_r1112_and_never_removes_images():
    text = (BB / "build.sh").read_text()
    assert "TAG=rl-task-shifthunt-r1112" in text and "BASE=rl-task-shifthunt-r1103" in text
    assert text.count("docker tag ") == 1 and 'docker tag "$IID" "$TAG"' in text
    for banned in ("docker rmi", "docker image rm", "docker rm ", "prune", "docker push"):
        assert banned not in text
    assert 'git -C "$REPO" archive "$SHA"' in text          # the context is a commit, never the working tree


def test_sync_script_writes_only_the_listed_private_files():
    text = (ROOT / "scripts" / "blackbox_sync_private.sh").read_text()
    assert "scripts/collect_rollouts.py:scripts/collect_rollouts.py" in text
    assert "docker_research_bb/r1112_env.sh:scripts/r1112_env.sh" in text
    assert 'NEW_ARMS="blackbox blackbox64 open64"' in text and 'ITEMS="ep411 ep413 ep415 ep472 ep474 ep476"' in text
    writes = [l.strip() for l in text.splitlines() if ">>" in l or 'cat "$TMP/new" >' in l]
    assert writes and all('"$P"' in l or '> "$dst"' in l for l in writes), writes   # problems.txt appends, sync_file
    for banned in ("git commit", "git -C \"$PRIV_REPO\" add", "rm -rf \"$PRIV", "> \"$P\"\n"):
        assert banned not in text
    lines = (ROOT / "problems.txt").read_text().splitlines()
    for ep in "ep411 ep413 ep415 ep472 ep474 ep476".split():
        for arm in "blackbox blackbox64 open64".split():
            assert f"{ep}-{arm}" in lines


def test_net_isolation_script_has_the_main_study_rules():
    text = (ROOT / "scripts" / "blackbox_net_isolation.sh").read_text()
    for needle in ("NET=anthropic_only", "ANTHROPIC_RANGE=160.79.104.0/23", "172.66.0.243", "162.159.140.245",
                   "--dport 443 -j ACCEPT", '-i "$BR" -j REJECT', "--check"):
        assert needle in text
    assert "-F DOCKER-USER" not in text and "iptables -D" not in text and " -X " not in text   # never removes rules
