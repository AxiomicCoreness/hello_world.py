# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Pin check for the sparse DeepInfer vendor under ``deepinfer/`` (no network, no GPU).

* Every vendored file's git blob sha (``sha1(b"blob <len>\\0" + bytes)``, what
  ``git hash-object`` prints) must equal the blob sha recorded from
  ``gh api repos/deepseek-ai/DeepInfer/git/trees/<pin>?recursive=1`` in
  ``deepinfer/VENDOR_MANIFEST.json``.
* ``deepinfer/__init__.py`` and ``deepinfer/model_executor/models/__init__.py`` are a
  repo header plus the upstream file byte-for-byte; the part after each marker line
  must hash to the upstream blob.
* The kept repo stub (``deepinfer/model_executor/__init__.py``; upstream is empty) carries no code.
* The in-package import closure of ``v4_modules`` resolves entirely inside the
  vendored tree (only ``deepinfer._C`` is allowed to be missing), and equals the
  manifest's file list exactly.
* Importing each ``v4_modules`` submodule either succeeds or fails ONLY with a
  ``ModuleNotFoundError`` for an external dependency (torch, deep_gemm,
  tile_kernels, ...) or the compiled ``deepinfer._C``, never for an in-package module.

The last two need Python >= 3.12 because upstream does (pyproject requires-python
">=3.12"; ``environ.py`` uses 3.12-only syntax), so they are version-gated; the
3.12 CI leg and the box run them.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "deepinfer"
MANIFEST = json.loads((PKG / "VENDOR_MANIFEST.json").read_text(encoding="utf-8"))
PIN = "9bd9cf243fc53ef9afbf8f04d391d989117d6ab9"
FILES = MANIFEST["files"]
NEEDS_312 = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="upstream DeepInfer pin requires Python >= 3.12 (environ.py uses 3.12-only syntax)",
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def test_manifest_pin_and_shape() -> None:
    assert MANIFEST["commit"] == PIN
    assert MANIFEST["upstream"] == "https://github.com/deepseek-ai/DeepInfer"
    assert MANIFEST["license"] == "Apache-2.0"
    paths = [f["path"] for f in FILES]
    assert len(paths) == len(set(paths))
    for f in FILES:
        assert len(f["blob_sha"]) == 40 and int(f["blob_sha"], 16) >= 0
        assert f["mode"] in ("byte_identical", "repo_header_plus_upstream", "repo_stub_kept")
    v4 = [f for f in FILES if f["role"] == "v4_modules"]
    assert len(v4) == 24
    assert all(f["mode"] == "byte_identical" for f in v4)


def test_git_blob_sha_matches_git_hash_object_definition() -> None:
    # Empty blob sha is a well-known git constant.
    assert git_blob_sha(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


@pytest.mark.parametrize("entry", [f for f in FILES if f["mode"] == "byte_identical"], ids=lambda f: f["path"])
def test_byte_identical_blob_sha(entry: dict) -> None:
    data = (ROOT / entry["path"]).read_bytes()
    assert len(data) == entry["size"], entry["path"]
    assert git_blob_sha(data) == entry["blob_sha"], f"{entry['path']} drifted from DeepInfer@{PIN}"


@pytest.mark.parametrize(
    "entry", [f for f in FILES if f["mode"] == "repo_header_plus_upstream"], ids=lambda f: f["path"]
)
def test_repo_header_plus_upstream_bytes(entry: dict) -> None:
    data = (ROOT / entry["path"]).read_bytes()
    marker = entry["marker"].encode() + b"\n"
    assert data.count(marker) == 1
    header, upstream = data.split(marker)
    assert len(upstream) == entry["size"]
    assert git_blob_sha(upstream) == entry["blob_sha"], f"{entry['path']} upstream part drifted"
    code = [ln for ln in header.decode().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if entry["path"] == "deepinfer/__init__.py":
        # Only the Python >= 3.12 guard (upstream requires-python) is allowed as header code.
        assert code[0] == "import sys as _sys"
        assert any("raise ImportError(" in ln for ln in code)
        assert code[-1] == "del _sys"
    else:
        assert code == [], f"{entry['path']} header must be comments only"


def test_header_files_are_exactly_the_two_documented() -> None:
    assert sorted(f["path"] for f in FILES if f["mode"] == "repo_header_plus_upstream") == [
        "deepinfer/__init__.py",
        "deepinfer/model_executor/models/__init__.py",
    ]


@pytest.mark.parametrize("entry", [f for f in FILES if f["mode"] == "repo_stub_kept"], ids=lambda f: f["path"])
def test_kept_repo_stub_has_no_code(entry: dict) -> None:
    src = (ROOT / entry["path"]).read_text(encoding="utf-8")
    assert ast.parse(src).body == [], f"{entry['path']} must stay a comment-only package marker"


def test_no_unmanifested_or_compiled_files() -> None:
    listed = {f["path"] for f in FILES} | set(MANIFEST["repo_only_files"])
    actual = set()
    for p in PKG.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            actual.add(p.relative_to(ROOT).as_posix())
    assert actual - {"deepinfer/VENDOR_MANIFEST.json"} <= listed, sorted(actual - listed)
    assert listed <= actual, sorted(listed - actual)
    bad = [a for a in actual if a.endswith((".so", ".cu", ".cuh", ".cpp", ".cc", ".h", ".pyd")) or "/_C" in a]
    assert bad == []


# ------------------------------------------------------------- import closure

def _mod_file(mod: str) -> Path | None:
    base = ROOT.joinpath(*mod.split("."))
    if base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def _module_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    stack: list[ast.stmt] = list(tree.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                names |= {x.id for x in ast.walk(t) if isinstance(x, ast.Name)}
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            names |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, (ast.If, ast.Try, ast.With)):
            for field in ("body", "orelse", "finalbody", "handlers"):
                for c in getattr(n, field, []) or []:
                    stack.extend(c.body if isinstance(c, ast.ExceptHandler) else [c])
    return names


def _is_excluded(mod: str) -> bool:
    return mod == "deepinfer._C" or mod.startswith("deepinfer._C.")


def _closure() -> tuple[set[str], list[str]]:
    roots = [f["path"] for f in FILES if f["role"] == "v4_modules"]
    todo = [p[:-3].replace("/", ".").removesuffix(".__init__") for p in roots]
    seen: dict[str, Path] = {}
    problems: list[str] = []
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        path = _mod_file(mod)
        if path is None:
            problems.append(f"in-package module not vendored: {mod}")
            continue
        seen[mod] = path
        parts = mod.split(".")
        todo.extend(".".join(parts[:i]) for i in range(1, len(parts)))
        pkg = mod if path.name == "__init__.py" else mod.rpartition(".")[0]
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] == "deepinfer" and not _is_excluded(a.name):
                        todo.append(a.name)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    up = pkg.split(".")[: len(pkg.split(".")) - (node.level - 1)]
                    base = ".".join(up + ([node.module] if node.module else []))
                if base.split(".")[0] != "deepinfer" or _is_excluded(base):
                    continue
                todo.append(base)
                for a in node.names:
                    sub = f"{base}.{a.name}"
                    if _mod_file(sub) is not None:
                        todo.append(sub)
                    else:
                        target = _mod_file(base)
                        if target is not None and a.name != "*":
                            defined = _module_level_names(ast.parse(target.read_text(encoding="utf-8")))
                            if a.name not in defined:
                                problems.append(f"{mod}: 'from {base} import {a.name}' not defined in vendored {base}")
    files = {p.relative_to(ROOT).as_posix() for p in seen.values()}
    return files, problems


@NEEDS_312
def test_in_package_closure_is_complete_and_exact() -> None:
    files, problems = _closure()
    assert problems == []
    manifested = {f["path"] for f in FILES if f["role"] != "license"}
    assert files == manifested, {"unvendored": sorted(files - manifested), "extra": sorted(manifested - files)}


_PROBE = r"""
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
out = {}
for name in sys.argv[2:]:
    try:
        importlib.import_module(name)
        out[name] = ["ok", None, None]
    except BaseException as exc:  # report everything; the test decides
        out[name] = [type(exc).__name__, getattr(exc, "name", None), str(exc)[:300]]
print(json.dumps(out))
"""


@NEEDS_312
def test_v4_modules_import_fails_only_on_external_deps() -> None:
    mods = sorted(
        f["path"][:-3].replace("/", ".").removesuffix(".__init__") for f in FILES if f["role"] == "v4_modules"
    )
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _PROBE, str(ROOT), *mods],
        capture_output=True, text=True, timeout=600, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert set(result) == set(mods)
    external = set(MANIFEST["external_modules"])
    bad = {}
    for mod, (kind, missing, msg) in result.items():
        if kind == "ok":
            continue
        if kind != "ModuleNotFoundError" or not missing:
            bad[mod] = (kind, missing, msg)
            continue
        top = missing.split(".")[0]
        if top == "deepinfer":
            if not _is_excluded(missing):
                bad[mod] = (kind, missing, msg)  # an in-package module is missing: vendoring bug
        elif top not in external:
            bad[mod] = (kind, missing, f"not a declared external dependency: {msg}")
    assert bad == {}
