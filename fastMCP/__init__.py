#!/usr/bin/env python3
"""fastMCP — Modular Flywheel Gearbox

FILLED = False invariant. Dual ASGI loopback-only bind policy.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["FILLED", "app", "gearbox", "bind"]

FILLED = False

from fastMCP.bind import bind, resolve, uvicorn_argv
from fastMCP.gearbox import Gearbox, gearbox
from fastapi_flywheel_gearbox import app
