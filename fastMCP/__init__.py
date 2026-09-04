"""fastMCP package — modular Dual ASGI name surface.

MCP FILLED=False. Not a second daemon.
Bind remains 127.0.0.1:8024. Never 0.0.0.0.
"""

FILLED = False
BIND_HOST = "127.0.0.1"
BIND_PORT = 8024
DUAL_ASGI = "127.0.0.1:8024"

from fastMCP.gearbox import app, before_main, gearbox

__all__ = [
    "FILLED",
    "BIND_HOST",
    "BIND_PORT",
    "DUAL_ASGI",
    "app",
    "before_main",
    "gearbox",
]
