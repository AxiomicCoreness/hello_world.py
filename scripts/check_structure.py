#!/usr/bin/env python3
"""scripts/check_structure.py — structural invariants for the repo.

Signitorial: Clarke Yoursa Tee
Seal:        ∀∞φ² · AST_STRUCTURE · WOOD_DRAGON_0.91 · SEALED
Instrument:  AST (Python) + yaml.safe_load (workflows)
Needle:      "Clarke Yoursa Tee" in masked header body (above SEAL:BEGIN)

Checks:
  A1. .github/workflows/*.y{a,}ml parses as YAML, has top-level 'on' and 'jobs'.
  A2. No workflow file begins with a Python shebang.
  A3. Numeric soak constants in declared files are in range.
  A4. No live bind to 0.0.0.0 / :: in dual-ASGI entrypoints (a literal host,
      or the literal default of a BIND_HOST-style env lookup).
  A5. Signitorial needle present in header files (masked body);
      CITATION.cff may instead carry it as structured CFF authors.

Exits 0 on pass, 1 on any violation.
No ledger rewrite. MCP unfilled. Dual ASGI 127.0.0.1:8024 only.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

SIGNITORIAL_NEEDLE = "Clarke Yoursa Tee"
SIGNITORIAL_AUTHOR = "Clarke Yoursa Tee"
SEAL_BEGIN = "<!-- SEAL:BEGIN -->"

SIGNITORIAL_FILES = [
    Path("README.md"),
    Path("notice.md"),
    Path("NOTICE"),
    Path("PROVENANCE.md"),
    Path("CITATION.cff"),
    Path("LICENSE"),
]

WORKFLOWS = Path(".github/workflows")
SOAK_FILES = [
    Path("pythonIDE/jitter_soak.py"),
    Path("scripts/merge_engine_phi.py"),
]
SOAK_CONSTANT_NAMES = {"T_MAX_SOAK_DEFAULT", "T_MAX_SOAK", "GAMMA_JITTER"}
# (lo, hi] — strictly positive. Zero is not a legitimate config for these.
# T_MAX_SOAK_DEFAULT = 0.0 (no soak) and GAMMA_JITTER = 0.0 (no jitter) fail.
SOAK_RANGES: dict[str, tuple[float, float]] = {
    "T_MAX_SOAK_DEFAULT": (0.0, 60.0),
    "T_MAX_SOAK": (0.0, 60.0),
    "GAMMA_JITTER": (0.0, 1.0),
}
BIND_ENTRYPOINTS = [
    Path("port380_mcp.py"),
    Path("mcp/port380_mcp.py"),
    Path("app_main.py"),
    Path("app/main.py"),
]
FORBIDDEN_HOSTS = {"0.0.0.0", "::"}
# A4 accepts a host read from one of these env vars, e.g.
# host=os.environ.get("BIND_HOST", "127.0.0.1"), so a container or pod can
# widen the bind (BIND_HOST=0.0.0.0) explicitly. The literal default itself
# must not be a forbidden host.
BIND_HOST_ENV_VARS = {"BIND_HOST", "MCP_BIND_HOST", "PORT380_HOST"}
SHEBANG_RE = re.compile(rb"^#![\s\S]*?python", re.IGNORECASE)

CHECKS = ("A1", "A2", "A3", "A4", "A5")


def check_workflows() -> list[str]:
    errs: list[str] = []
    if not WORKFLOWS.is_dir():
        return errs
    for p in sorted(WORKFLOWS.iterdir()):
        if p.suffix not in (".yml", ".yaml"):
            continue
        raw = p.read_bytes()
        if SHEBANG_RE.match(raw):
            errs.append(f"{p}: first line is a Python shebang")
            continue
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            errs.append(f"{p}: not valid YAML: {exc}")
            continue
        if not isinstance(doc, dict):
            errs.append(f"{p}: top-level is {type(doc).__name__}, not mapping")
            continue
        if "on" not in doc and True not in doc:
            errs.append(f"{p}: no top-level 'on' key")
        if "jobs" not in doc:
            errs.append(f"{p}: no top-level 'jobs' key")
    return errs


def _numeric_assignments(tree: ast.Module) -> dict[str, float]:
    """Collect module-level numeric constants assigned to bare names.

    Handles four literal shapes:
        NAME = 5            Assign,   Constant
        NAME = -5           Assign,   UnaryOp(USub, Constant)
        NAME: float = 5     AnnAssign, Constant
        NAME: float = -5    AnnAssign, UnaryOp(USub, Constant)
    Bools are excluded even though isinstance(True, int) is True.
    Tuple targets (A = B = 5.0) are excluded; only a single Name target counts.
    """
    out: dict[str, float] = {}

    def literal_value(node: ast.AST) -> float | None:
        if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
            if isinstance(node.value, (int, float)):
                return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            inner = literal_value(node.operand)
            if inner is not None:
                return -inner if isinstance(node.op, ast.USub) else inner
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            v = literal_value(node.value)
            if v is not None:
                out[node.targets[0].id] = v
        elif isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name) or node.value is None:
                continue
            v = literal_value(node.value)
            if v is not None:
                out[node.target.id] = v
    return out


def check_soak_constants() -> list[str]:
    errs: list[str] = []
    for p in SOAK_FILES:
        if not p.is_file():
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as exc:
            errs.append(f"{p}: parse error: {exc}")
            continue
        values = _numeric_assignments(tree)
        for name, (lo, hi) in SOAK_RANGES.items():
            if name not in values:
                continue
            v = values[name]
            if not (lo < v <= hi):
                errs.append(f"{p}: {name} = {v} not in ({lo}, {hi}]")
    return errs


def _env_host_lookup(node: ast.AST) -> tuple[str, object] | None:
    """(env var, literal default) for os.environ.get(VAR, d) / os.getenv(VAR, d)
    / environ.get(VAR, d) with VAR in BIND_HOST_ENV_VARS; else None."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
        return None
    fn = node.func
    is_getenv = fn.attr == "getenv"
    is_environ_get = fn.attr == "get" and (
        (isinstance(fn.value, ast.Attribute) and fn.value.attr == "environ")
        or (isinstance(fn.value, ast.Name) and fn.value.id == "environ")
    )
    if not (is_getenv or is_environ_get) or not node.args:
        return None
    var = node.args[0]
    if not (isinstance(var, ast.Constant) and var.value in BIND_HOST_ENV_VARS):
        return None
    default = node.args[1] if len(node.args) > 1 else None
    return var.value, (default.value if isinstance(default, ast.Constant) else None)


def _host_problem(node: ast.AST) -> str | None:
    """Why a host expression is a live 0.0.0.0/:: bind, or None if it is not."""
    if isinstance(node, ast.Constant) and node.value in FORBIDDEN_HOSTS:
        return f"host={node.value!r}"
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        # os.environ.get("BIND_HOST") or os.environ.get("MCP_BIND_HOST", "127.0.0.1")
        for operand in node.values:
            why = _host_problem(operand)
            if why:
                return why
        return None
    env = _env_host_lookup(node)
    if env and env[1] in FORBIDDEN_HOSTS:
        return f"host default {env[1]!r} via ${env[0]}"
    return None


def check_binds() -> list[str]:
    errs: list[str] = []
    for p in BIND_ENTRYPOINTS:
        if not p.is_file():
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as exc:
            errs.append(f"{p}: parse error: {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = (
                fn.attr if isinstance(fn, ast.Attribute)
                else fn.id if isinstance(fn, ast.Name)
                else None
            )
            if name not in {"run", "serve_forever", "TCPServer", "HTTPServer"}:
                continue
            for kw in node.keywords:
                if kw.arg == "host":
                    why = _host_problem(kw.value)
                    if why:
                        errs.append(f"{p}:{node.lineno}: {why} in {name}()")
            for arg in node.args:
                if isinstance(arg, ast.Tuple):
                    for elt in arg.elts:
                        why = _host_problem(elt)
                        if why:
                            errs.append(
                                f"{p}:{node.lineno}: tuple {why} in {name}()"
                            )
    return errs


def _masked_head(text: str) -> str:
    """Body above SEAL:BEGIN — the region self_seal.py hashes."""
    if SEAL_BEGIN in text:
        return text.split(SEAL_BEGIN, 1)[0]
    return text


def _cff_has_author(text: str) -> bool:
    """True if CITATION.cff lists the author, either as one literal string
    (name / given+family joined) or as given-names Clarke, family-names Yoursa Tee."""
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError:
        return False
    authors = doc.get("authors") if isinstance(doc, dict) else None
    for a in authors if isinstance(authors, list) else []:
        if not isinstance(a, dict):
            continue
        given = str(a.get("given-names", "")).strip()
        family = str(a.get("family-names", "")).strip()
        if (given, family) == ("Clarke", "Yoursa Tee"):
            return True
        if SIGNITORIAL_AUTHOR in (str(a.get("name", "")).strip(), f"{given} {family}"):
            return True
    return False


def check_signitorial() -> list[str]:
    """A5 — needle 'Clarke Yoursa Tee' in masked header body.

    Same region as scripts/self_seal.py check(). Definition-rank
    presence, not a theorem. Missing file is skip, not fail, so a
    branch that only carries a subset of the header set still passes
    if every present file carries the name.
    """
    errs: list[str] = []
    seen = 0
    for p in SIGNITORIAL_FILES:
        if not p.is_file():
            continue
        seen += 1
        text = p.read_text(encoding="utf-8")
        head = _masked_head(text)
        if p.name == "CITATION.cff" and _cff_has_author(text):
            continue
        if SIGNITORIAL_NEEDLE not in head:
            errs.append(
                f"{p}: signitorial needle {SIGNITORIAL_NEEDLE!r} "
                f"missing from masked header"
            )
    here = Path(__file__).resolve()
    src = here.read_text(encoding="utf-8")
    if SIGNITORIAL_NEEDLE not in src:
        errs.append(f"{here.name}: signitorial needle missing from AST source")
    if seen == 0:
        errs.append("A5: no signitorial header files present on disk")
    return errs


def main() -> int:
    results = {
        "A1": check_workflows(),
        "A2": [],  # shebang is checked inside check_workflows
        "A3": check_soak_constants(),
        "A4": check_binds(),
        "A5": check_signitorial(),
    }
    # A2 is a subset of A1's shebang detection; report it separately
    # by scanning A1 errors for shebang lines.
    a1_errs = results["A1"]
    a2_errs = [e for e in a1_errs if "shebang" in e]
    results["A2"] = a2_errs
    results["A1"] = [e for e in a1_errs if "shebang" not in e]

    all_errors: list[str] = []
    passed = 0
    for name in CHECKS:
        errs = results[name]
        if errs:
            all_errors.extend(errs)
            print(f"{name}: FAIL ({len(errs)})")
        else:
            passed += 1
            print(f"{name}: PASS")

    score = (passed / len(CHECKS)) * 100.0
    print(f"\nstructure integrity: {passed}/{len(CHECKS)} = {score:.1f}%")

    for e in all_errors:
        print(f"::error::{e}")

    if all_errors:
        print(f"\n\u274c {len(all_errors)} structural violation(s)")
        return 1
    print(
        "\u2705 structure check: workflows valid, soak constants in range, "
        "no forbidden binds, signitorial Clarke Yoursa Tee present"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
