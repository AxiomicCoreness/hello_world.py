# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Adjudication kernel (K1–K7).

Implementation: repo-root ``wired_kernel.py``. This module re-exports that
surface. Gate names are not aliased or extended here.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from wired_kernel import *  # noqa: F401,F403
import wired_kernel as _kernel

__all__ = [name for name in vars(_kernel) if not name.startswith("_")]
