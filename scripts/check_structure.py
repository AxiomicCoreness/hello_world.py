#!/usr/bin/env python3
"""scripts/check_structure.py — structural invariants for the repo.

Checks:
  A1. .github/workflows/*.y{a,}ml parses as YAML, has top-level 'on' and 'jobs'.
  A2. No workflow file begins with a Python shebang.
  A3. Numeric soak constants in declared files are in range.
  A4. No live bind to 0.0.0.0 / :: in dual-ASGI entrypoints.

Exits 0 on pass, 1 on any violation.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

WORKFLOWS = Path(".github/workflows")
SOAK_FILES = [
    Path("pythonIDE/jitter_soak.py"),
    Path("scripts/merge_engine_phi.py"),
]
SOAK_CONSTANT_NAMES = {"T_MAX_SOAK_DEFAULT", "T_MAX_SOAK", "GAMMA_JITTER"}
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
SHEBANG_RE = re.compile(rb"^#![\s\S]*?python", re.IGNORECASE)


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
    out: dict[str, float] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, (int, float)):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        out[tgt.id] = float(node.value.value)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in SOAK_CONSTANT_NAMES:
                    try:
                        out[tgt.id] = float(eval(compile(ast.Expression(node.value), "<ast>", "eval"), {"PHI": (1 + 5 ** 0.5) / 2}))  # noqa: S307
                    except Exception:
                        pass
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
                if kw.arg == "host" and isinstance(kw.value, ast.Constant):
                    if kw.value.value in FORBIDDEN_HOSTS:
                        errs.append(
                            f"{p}:{node.lineno}: host={kw.value.value!r} in {name}()"
                        )
            for arg in node.args:
                if isinstance(arg, ast.Tuple):
                    for elt in arg.elts:
                        if (
                            isinstance(elt, ast.Constant)
                            and elt.value in FORBIDDEN_HOSTS
                        ):
                            errs.append(
                                f"{p}:{node.lineno}: tuple host "
                                f"{elt.value!r} in {name}()"
                            )
    return errs


def main() -> int:
    errors: list[str] = []
    errors.extend(check_workflows())
    errors.extend(check_soak_constants())
    errors.extend(check_binds())
    for e in errors:
        print(f"::error::{e}")
    if errors:
        print(f"\n❌ {len(errors)} structural violation(s)")
        return 1
    print(
        "✅ structure check: workflows valid, soak constants in range, "
        "no forbidden binds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
