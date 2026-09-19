#!/usr/bin/env python3
"""Verify Section V artifacts parse. Exit 0 iff all succeed."""
from __future__ import annotations
import py_compile
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml required", file=sys.stderr)
    sys.exit(2)

CHECKS = [
    ("yaml", "ledger/9195.yaml"),
    ("yaml", "k8s/section-iv/10-configmap-payload-schema.yaml"),
    ("yaml", "k8s/section-iv/30-deployment-sink.yaml"),
    ("py", "pythonIDE/argo_sink.py"),
]


def check_yaml(path: str) -> bool:
    p = Path(path)
    if not p.is_file():
        print(f" MISSING: {path}")
        return False
    try:
        with p.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        print(f" PARSE ERROR: {e}")
        return False
    print(f" parsed; top-level type = {type(data).__name__}")
    return True


def check_py(path: str) -> bool:
    p = Path(path)
    if not p.is_file():
        print(f" MISSING: {path}")
        return False
    try:
        py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        print(f" COMPILE ERROR: {e}")
        return False
    print(" compiled")
    return True


def main() -> int:
    failures = 0
    for kind, path in CHECKS:
        print(path)
        ok = check_yaml(path) if kind == "yaml" else check_py(path)
        if not ok:
            failures += 1
    if failures:
        print(f"FAIL: {failures} of {len(CHECKS)} checks did not pass")
        return 1
    print(f"PASS: all {len(CHECKS)} checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
