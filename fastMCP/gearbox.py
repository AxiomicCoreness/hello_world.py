#!/usr/bin/env python3
"""Modular flywheel gearbox under fastMCP/.

Same ASGI object as fastapi_flywheel_gearbox:app.
No second daemon. MCP FILLED=False.

Dispatch:
  uvicorn fastMCP.gearbox:app --host 127.0.0.1 --port 8024
"""

from __future__ import annotations

FILLED = False

from fastapi_flywheel_gearbox import app, before_main, Gearbox
from fastMCP.bind import resolve

app.title = "fastMCP flywheel gearbox (unfilled)"
gearbox = Gearbox()


def main() -> None:
    import uvicorn

    host, port = resolve()
    print("FILLED=", FILLED)
    print("before_main():", before_main())
    print(f"Starting uvicorn on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
