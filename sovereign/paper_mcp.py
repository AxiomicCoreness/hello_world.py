# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Lazy re-export of the ``paper_mcp`` package.

That package is not part of this commit. Attribute access imports it.
``ImportError`` means the checkout does not have ``paper_mcp`` yet.
"""
from __future__ import annotations

import importlib
from typing import Any

_PKG = None


def __getattr__(name: str) -> Any:
    global _PKG
    if _PKG is None:
        try:
            _PKG = importlib.import_module("paper_mcp")
        except ImportError as exc:
            raise ImportError(
                "paper_mcp is not importable on this checkout"
            ) from exc
    return getattr(_PKG, name)
