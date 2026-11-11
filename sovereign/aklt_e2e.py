# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""AKLT invariant surface. Re-export of repo-root ``aklt_invariants.py``.

That module's checks are ``check_ground_state_energy``,
``check_entanglement_degeneracy``, ``check_string_order``, and
``check_singlet``. It does not define gates G1–G10. Those gates already
live in ``scripts/aklt_e2e_test.py`` and are not copied or renamed here.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from aklt_invariants import *  # noqa: F401,F403
import aklt_invariants as _aklt

__all__ = [name for name in vars(_aklt) if not name.startswith("_")]
