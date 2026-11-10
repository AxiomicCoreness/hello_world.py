# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Sovereign package entry. Dependency-light.

``PlanckEngine`` is imported immediately. ``kernel``, ``octonion_table``,
``phi_mod_mean``, and ``paper_mcp`` load on first access. ``engine`` and
``aklt_e2e`` load numpy when first requested. ``paper_mcp`` imports the
``paper_mcp`` package only when an attribute is used.
"""
from __future__ import annotations

import importlib

from .planck_engine_v2 import PlanckEngine

__all__ = [
    "PlanckEngine",
    "kernel",
    "octonion_table",
    "phi_mod_mean",
    "engine",
    "aklt_e2e",
    "paper_mcp",
]

_LAZY = (
    "kernel",
    "octonion_table",
    "phi_mod_mean",
    "engine",
    "aklt_e2e",
    "paper_mcp",
)


def __getattr__(name: str):
    if name in _LAZY:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
