"""Pattern 1: same literal asserted in N places.

gate_G3 rank must agree across generator, workflow heredoc, and test file.
"""
from __future__ import annotations

import re
from pathlib import Path

from ._base import Invariant, Result
from ._paths import repo_root


def check() -> Result:
    root = repo_root()
    targets = [
        root / ".github" / "scripts" / "aklt_e2e_generator.py",
        root / ".github" / "workflows" / "aklt-e2e.yml",
        root / "scripts" / "aklt_e2e_test.py",
    ]
    ranks = {}
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # crude: look for rank == N near gate_G3
        m = re.search(r"rank\s*==\s*(\d+)", text)
        if m:
            ranks[str(path.relative_to(root))] = int(m.group(1))
    if not ranks:
        return Result(True, "rank_unison", "no rank assertions found")
    values = set(ranks.values())
    if len(values) > 1:
        return Result(
            False, "rank_unison",
            f"rank assertions differ: {ranks}",
            "make all three copies assert the same rank",
        )
    return Result(True, "rank_unison", f"all copies assert rank={list(values)[0]}")


INVARIANT = Invariant(
    name="rank_unison",
    description="gate_G3 rank assertion must agree across all copies",
    check=check,
)
