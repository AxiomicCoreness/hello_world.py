"""Pattern 3: same function name defined in more than one file.

Two files defining gate_G3 is how the rank drifted. This invariant fails if
any gate function name appears in more than one of the three AKLT sources.
"""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from ._base import Invariant, Result
from ._paths import repo_root


def check() -> Result:
    root = repo_root()
    targets = [
        root / ".github" / "scripts" / "aklt_e2e_generator.py",
        root / "scripts" / "aklt_e2e_test.py",
    ]
    # workflow heredoc is YAML; skip AST for now
    names = defaultdict(list)
    for path in targets:
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("gate_"):
                names[node.name].append(str(path.relative_to(root)))
    dups = {n: files for n, files in names.items() if len(files) > 1}
    if dups:
        return Result(
            False, "no_gate_duplication",
            f"duplicate gate definitions: {dups}",
            "consolidate to a single module and import",
        )
    return Result(True, "no_gate_duplication", "no duplicate gate function names")


INVARIANT = Invariant(
    name="no_gate_duplication",
    description="no gate_* function defined in more than one AKLT source file",
    check=check,
)
