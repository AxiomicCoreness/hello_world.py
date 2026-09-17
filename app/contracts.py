"""Option A — two surfaces, two contracts.

MCP:     surface=[/healthz], legacy=[/health,/pulse]
FastAPI: surface=[/health,/status,/pulse,/vision,/systems], POST /gate separate
"""
from __future__ import annotations

MCP_CONTRACT = {
    "name": "mcp",
    "surface": ["/healthz"],
    "legacy_out_of_surface": ["/health", "/pulse"],
}

FASTAPI_CONTRACT = {
    "name": "fastapi",
    "surface": ["/health", "/status", "/pulse", "/vision", "/systems"],
    "methods": {"/gate": ["POST"]},
    "legacy_out_of_surface": [],
}
