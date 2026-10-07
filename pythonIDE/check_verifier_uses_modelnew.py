#!/usr/bin/env python3
"""AST gate for ModelNew usage. No regex on text. No seal."""

from __future__ import annotations

import ast
from pathlib import Path

MODELNEW_CLASS_NAME = "ModelNew"
MODELNEW_MODULE_SUBSTRING = "model_new_ascendc"
MODELNEW_VERIFIER_FILENAME = "pass_a_runner.py"


def check_verifier_uses_modelnew(workspace, vj=None):
    ws = Path(workspace)
    verifier_path = ws / MODELNEW_VERIFIER_FILENAME
    if not verifier_path.is_file():
        return None
    try:
        text = verifier_path.read_text(errors="ignore")
    except OSError:
        return f"check_verifier_uses_modelnew: cannot read {MODELNEW_VERIFIER_FILENAME}"
    try:
        tree = ast.parse(text, filename=str(verifier_path))
    except SyntaxError as exc:
        return (
            f"check_verifier_uses_modelnew: {MODELNEW_VERIFIER_FILENAME} "
            f"does not parse as Python: {exc}"
        )
    has_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and MODELNEW_MODULE_SUBSTRING in node.module:
            has_import = True
            break
        if isinstance(node, ast.Import) and any(MODELNEW_MODULE_SUBSTRING in a.name for a in node.names):
            has_import = True
            break
    if not has_import:
        return "no model_new_ascendc import in code"
    instance_names = set()
    inline_seen = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Call):
            inner = node.func.func
            if isinstance(inner, ast.Name) and inner.id == MODELNEW_CLASS_NAME:
                inline_seen = True
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == MODELNEW_CLASS_NAME:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        instance_names.add(target.id)
    if inline_seen:
        return None
    if not instance_names:
        return "never instantiates ModelNew"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in instance_names:
            return None
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in instance_names:
            return None
    return "instantiates ModelNew but never invokes it"


def main() -> int:
    cases = {
        "docstring": '"""ModelNew()"""\nimport model_new_ascendc\n',
        "fstring": 'import model_new_ascendc\nx = f"ModelNew()"\n',
        "named": "import model_new_ascendc\nx = ModelNew()\nx(1)\n",
        "inline": "import model_new_ascendc\nModelNew()(1)\n",
        "uncalled": "import model_new_ascendc\nx = ModelNew()\n",
        "syntax": "import model_new_ascendc\n(\n",
    }
    root = Path("/tmp/mn")
    for name, body in cases.items():
        d = root / name
        d.mkdir(exist_ok=True)
        (d / "pass_a_runner.py").write_text(body)
        print(name, check_verifier_uses_modelnew(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
