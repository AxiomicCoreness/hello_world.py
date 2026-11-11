# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Fano-plane octonion multiplication table.

Implementation: repo-root ``octonion_table.py``. This module re-exports that
table (``FANO_LINES``, ``octonion_product``, ``build_octonion_table``).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from octonion_table import *  # noqa: F401,F403
import octonion_table as _table

__all__ = [name for name in vars(_table) if not name.startswith("_")]
