#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-facing helpers for the Garden.

get_symplectic_status() — return latest symplectic_status.json (or live collect).
get_wood_dragon_report() — 0.91d / 16.35d rhythm + status snapshot.

These are plain functions so they can be registered with an MCP server:

    @mcp.tool()
    def get_symplectic_status() -> dict:
        from mcp_tools import get_symplectic_status as _g
        return _g()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

STATUS_PATH = Path("symplectic_status.json")


def get_symplectic_status(path: Path = STATUS_PATH) -> Dict[str, Any]:
    """Return the current symplectic status of the Garden."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    # Fallback: collect live if artifacts not yet written
    try:
        from symplectic_status import build_status

        return build_status()
    except Exception as exc:
        return {
            "name": "Symplectic_Status",
            "error": str(exc),
            "hint": "Run: python symplectic_status.py",
        }


def get_wood_dragon_report() -> Dict[str, Any]:
    """Return wood-dragon cadence + status presence."""
    from wood_dragon_technique import run_wood_dragon_technique

    return run_wood_dragon_technique()


def main() -> None:
    print(json.dumps(get_symplectic_status(), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
