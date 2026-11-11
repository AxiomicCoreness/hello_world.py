# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""φ-mod mean. Implementation: ``scripts/phi_mod_mean.py``.

``PHI`` there is ``(1 + sqrt(5)) / 2``, the positive root of
``x² − x − 1 = 0``. This module re-exports that script. It does not
recompute the mean. The script's assert is the mod-mean against its target,
and it exits 1 when ``scripts/clarke_engine.py`` is absent.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "scripts" / "phi_mod_mean.py"
_spec = importlib.util.spec_from_file_location("_scripts_phi_mod_mean", _PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"phi_mod_mean implementation missing: {_PATH}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_scripts_phi_mod_mean"] = _mod
_spec.loader.exec_module(_mod)

__all__ = [name for name in vars(_mod) if not name.startswith("_")]
for _name in __all__:
    globals()[_name] = getattr(_mod, _name)


def __getattr__(name: str):
    return getattr(_mod, name)
