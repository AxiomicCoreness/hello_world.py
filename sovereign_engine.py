#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Compatibility shim. The engine body lives in ``scripts/ml_sovereign_core.py``.

Existing imports (``from sovereign_engine import PHI``, ``systems_go``,
``get_oidc_secret``, ``main_full``) resolve here and execute that module.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "scripts" / "ml_sovereign_core.py"
_spec = importlib.util.spec_from_file_location("_ml_sovereign_core", _IMPL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"sovereign engine implementation missing: {_IMPL}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_ml_sovereign_core"] = _mod
_spec.loader.exec_module(_mod)

__all__ = [name for name in vars(_mod) if not name.startswith("_")]
for _name in __all__:
    globals()[_name] = getattr(_mod, _name)


def __getattr__(name: str):
    return getattr(_mod, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_mod)))


if __name__ == "__main__":
    raise SystemExit(_mod.main_full())
