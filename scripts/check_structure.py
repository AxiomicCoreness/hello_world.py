#!/usr/bin/env python3
"""scripts/check_structure.py — structural invariants for the repo.
Checks A1–A4: workflows YAML, no shebang workflows, soak ranges, no 0.0.0.0 binds.
"""
from __future__ import annotations
import ast, re, sys
from pathlib import Path
import yaml
WORKFLOWS = Path(".github/workflows")
SOAK_FILES = [Path("pythonIDE/jitter_soak.py"), Path("scripts/merge_engine_phi.py")]
SOAK_RANGES = {"T_MAX_SOAK_DEFAULT": (0.0, 60.0), "T_MAX_SOAK": (0.0, 60.0), "GAMMA_JITTER": (0.0, 1.0)}
BIND_ENTRYPOINTS = [Path("port380_mcp.py"), Path("mcp/port380_mcp.py"), Path("app_main.py"), Path("app/main.py")]
FORBIDDEN_HOSTS = {"0.0.0.0", "::"}
SHEBANG_RE = re.compile(rb"^#![\s\S]*?python", re.IGNORECASE)
def check_workflows():
    errs = []
    if not WORKFLOWS.is_dir(): return errs
    for p in sorted(WORKFLOWS.iterdir()):
        if p.suffix not in (".yml", ".yaml"): continue
        raw = p.read_bytes()
        if SHEBANG_RE.match(raw):
            errs.append(f"{p}: first line is a Python shebang"); continue
        try: doc = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            errs.append(f"{p}: not valid YAML: {exc}"); continue
        if not isinstance(doc, dict):
            errs.append(f"{p}: top-level is {type(doc).__name__}, not mapping"); continue
        if "on" not in doc and True not in doc: errs.append(f"{p}: no top-level 'on' key")
        if "jobs" not in doc: errs.append(f"{p}: no top-level 'jobs' key")
    return errs
def check_soak_constants():
    errs = []
    for p in SOAK_FILES:
        if not p.is_file(): continue
        try: tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as exc:
            errs.append(f"{p}: parse error: {exc}"); continue
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name): values[tgt.id] = float(node.value.value)
        for name, (lo, hi) in SOAK_RANGES.items():
            if name in values and not (lo < values[name] <= hi):
                errs.append(f"{p}: {name} = {values[name]} not in ({lo}, {hi}]")
    return errs
def check_binds():
    errs = []
    for p in BIND_ENTRYPOINTS:
        if not p.is_file(): continue
        try: tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as exc:
            errs.append(f"{p}: parse error: {exc}"); continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call): continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else None
            if name not in {"run", "serve_forever", "TCPServer", "HTTPServer"}: continue
            for kw in node.keywords:
                if kw.arg == "host" and isinstance(kw.value, ast.Constant) and kw.value.value in FORBIDDEN_HOSTS:
                    errs.append(f"{p}:{node.lineno}: host={kw.value.value!r} in {name}()")
            for arg in node.args:
                if isinstance(arg, ast.Tuple):
                    for elt in arg.elts:
                        if isinstance(elt, ast.Constant) and elt.value in FORBIDDEN_HOSTS:
                            errs.append(f"{p}:{node.lineno}: tuple host {elt.value!r} in {name}()")
    return errs
def main():
    errors = check_workflows() + check_soak_constants() + check_binds()
    for e in errors: print(f"::error::{e}")
    if errors:
        print(f"\n❌ {len(errors)} structural violation(s)"); return 1
    print("✅ structure check: workflows valid, soak constants in range, no forbidden binds"); return 0
if __name__ == "__main__":
    sys.exit(main())
