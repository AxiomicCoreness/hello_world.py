#!/usr/bin/env python3
"""Modular flywheel gearbox under fastMCP/.

Same ASGI object as fastapi_flywheel_gearbox:app.
No second daemon. MCP FILLED=False.

Dispatch:
  uvicorn fastMCP.gearbox:app --host 127.0.0.1 --port 8024
  python -m fastMCP.gearbox
"""

from __future__ import annotations

import sys
from typing import Any

FILLED = False

from fastMCP.bind import resolve
from fastapi_flywheel_gearbox import app, before_main, Gearbox

app.title = "fastMCP flywheel gearbox (unfilled)"
gearbox = Gearbox()


def main() -> None:
    import uvicorn

    host, port = resolve()
    print(f"FILLED={FILLED}")
    print(f"before_main(): {before_main()}")
    print(f"Starting uvicorn on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
