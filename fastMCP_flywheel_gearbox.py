"""Root name-seal for the misspelled dispatch line.

uvicorn fastMCP_flywheel_gearbox:app --host 127.0.0.1 --port 8024

Same object as fastapi_flywheel_gearbox:app. MCP FILLED=False.
"""

from fastMCP.gearbox import FILLED, app, before_main, gearbox

__all__ = ["FILLED", "app", "before_main", "gearbox"]
