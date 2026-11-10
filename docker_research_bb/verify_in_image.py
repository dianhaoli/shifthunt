"""Run INSIDE the built image by build.sh (piped to an interpreter with -B, so nothing is written):

    <python> -B [-I] - daemon|grader <copied image path>...

daemon: as user toolsrv with the daemon venv (/opt/toolsrv-venv/bin/python -I), package root /opt/toolsrv.
grader: as root with the system python3 (the entrypoint's and the grader's interpreter), package root /grader.

Fails (exit 1, one line per problem) if a copied file does not compile, if a module the image really imports
does not import, or if a copied file refers to a name that the image's version of another shifthunt module does
not have. The last check is static (ast): `from .x import name` anywhere in the file, including inside
functions, and `alias.name` for every alias bound to a shifthunt module, so a lazy import or an attribute used
only at call time is caught too. That is what goes wrong when a changed file is copied next to an unchanged
module that the public tree has since edited.
"""
import ast
import importlib
import importlib.util
import os
import sys

PKG = "shifthunt"
ROOT = {"daemon": "/opt/toolsrv", "grader": "/grader"}
IMPORTS = {"daemon": ["shifthunt.toolserver", "shifthunt.grader", "shifthunt.reward", "shifthunt.contract",
                      "shifthunt.toolbackend", "shifthunt.episode_files"],
           "grader": ["shifthunt.grader", "shifthunt.reward", "shifthunt.contract", "shifthunt.episode_files"]}


def module_name(path, root):
    """Dotted module name of a file under the package root, None for a file outside it (task.py, grader.py)."""
    rel = os.path.relpath(path, root)
    if rel.startswith("..") or not rel.startswith(PKG + os.sep) or not rel.endswith(".py"):
        return None
    return rel[:-3].replace(os.sep, ".")


def refs(path, this):
    """(problems, modules) for one file: names it takes from shifthunt modules that those modules lack."""
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    aliases, problems = {}, []

    def load(name, lineno):
        try:
            return importlib.import_module(name)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{path}:{lineno}: cannot import {name} ({type(e).__name__}: {e})")
            return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                if this is None:
                    continue
                base = this.rsplit(".", node.level)[0]
                mod = base + ("." + node.module if node.module else "")
            else:
                mod = node.module or ""
            if mod != PKG and not mod.startswith(PKG + "."):
                continue
            m = load(mod, node.lineno)
            if m is None:
                continue
            for a in node.names:
                if hasattr(m, a.name):
                    v = getattr(m, a.name)
                elif hasattr(m, "__path__") and importlib.util.find_spec(f"{mod}.{a.name}") is not None:
                    v = load(f"{mod}.{a.name}", node.lineno)  # `from package import submodule`
                else:
                    problems.append(f"{path}:{node.lineno}: {mod} has no {a.name!r} in this image")
                    continue
                if v is not None and type(v).__name__ == "module":
                    aliases[a.asname or a.name] = v.__name__
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith(PKG + ".") and a.asname:
                    aliases[a.asname] = a.name
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases \
                and isinstance(node.ctx, ast.Load):
            m = load(aliases[node.value.id], node.lineno)
            if m is not None and not hasattr(m, node.attr):
                problems.append(f"{path}:{node.lineno}: {aliases[node.value.id]} has no {node.attr!r} in this image")
    return problems


def main(argv):
    mode, files = argv[0], argv[1:]
    root = os.environ.get("SHIFTHUNT_VERIFY_ROOT") or ROOT[mode]  # the override is for tests/test_blackbox_layer.py
    sys.path.insert(0, root)
    sys.path.insert(1, "/opt/toolsrv-admin")  # grader.py imports stop_toolsrv from there
    problems = []
    mine = [f for f in files if f.startswith(root + "/") or (mode == "grader" and f == "/task.py")]
    for f in mine:
        try:
            compile(open(f, encoding="utf-8").read(), f, "exec")
        except (OSError, SyntaxError) as e:
            problems.append(f"{f}: does not compile ({type(e).__name__}: {e})")
    for name in IMPORTS[mode]:
        try:
            importlib.import_module(name)
        except Exception as e:  # noqa: BLE001
            problems.append(f"import {name} failed ({type(e).__name__}: {e})")
    if mode == "grader":  # the two entry files, loaded as the entrypoint and run_grader.py load them
        for name, path in (("container_grader", "/grader/grader.py"), ("task_py", "/task.py")):
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception as e:  # noqa: BLE001
                problems.append(f"loading {path} failed ({type(e).__name__}: {e})")
    checked = []
    if not problems:
        loaded = {getattr(m, "__file__", None) for m in list(sys.modules.values())}
        for f in mine:
            # grader mode: /grader/shifthunt/toolserver.py is never imported by the system python (it has no
            # scipy), so only files this interpreter really loads are checked; the daemon run covers the twin
            if f.endswith(".py") or f == "/task.py":
                if mode == "grader" and f not in loaded and f not in ("/grader/grader.py", "/task.py"):
                    continue
                problems += refs(f, module_name(f, root))
                checked.append(f)
    for p in problems:
        print("PROBLEM " + p)
    print(f"verify_in_image {mode}: python {sys.version.split()[0]} uid {os.getuid()}, {len(mine)} file(s) compiled, "
          f"{len(IMPORTS[mode])} module(s) imported, names checked in {checked}: "
          + ("FAILED" if problems else "ok"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
