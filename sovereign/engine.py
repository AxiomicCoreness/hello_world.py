# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""THE ENGINE.

Body: ``scripts/ml_sovereign_core.py`` (moved from repo-root ``sovereign_engine.py``).
``sovereign_engine.py`` remains the compatibility import path.

Importing this module loads that body (numpy, and mpmath/sympy when present).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sovereign_engine import *  # noqa: F401,F403
import sovereign_engine as _engine

__all__ = list(_engine.__all__)
