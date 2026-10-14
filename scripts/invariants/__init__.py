"""Auto-discovery registry for structure invariants."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from ._base import Invariant, Result

CHECKS: list[Invariant] = []

for mod in pkgutil.iter_modules([str(Path(__file__).parent)]):
    if mod.name.startswith("_"):
        continue
    m = importlib.import_module(f".{mod.name}", __package__)
    entry = getattr(m, "INVARIANT", None)
    if entry is not None:
        CHECKS.append(entry)
