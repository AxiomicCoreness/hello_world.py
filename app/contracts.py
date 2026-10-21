"""Option A — two surfaces, two contracts.

MCP:     surface=[/healthz], legacy=[/health,/pulse]
FastAPI: surface=[/health,/status,/pulse,/vision,/systems], POST /gate separate
"""
from __future__ import annotations

from typing import Dict, List, Any

MCP_CONTRACT: Dict[str, Any] = {
    "name": "mcp",
    "surface": {
        "/healthz": ["GET"],
    },
    "legacy_out_of_surface": {
        "/health": ["GET"],
        "/pulse": ["POST"],
    },
}

FASTAPI_CONTRACT: Dict[str, Any] = {
    "name": "fastapi",
    "surface": {
        "/health": ["GET"],
        "/status": ["GET"],
        "/pulse": ["GET"],
        "/vision": ["GET"],
        "/systems": ["GET"],
    },
    "extra_routes": {
        "/gate": ["POST"],
    },
    "legacy_out_of_surface": {},
}


def assert_fastapi_contract(app_routes: List[Any]) -> None:
    """
    Validates that the FastAPI app's registered routes match the declared contract.
    Raises RuntimeError if there is a mismatch, preventing the app from starting.
    """
    # Extract paths and methods from the FastAPI routes
    # (FastAPI routes have `.path` and `.methods` attributes)
    registered = {}
    for route in app_routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            # Skip the automatic docs routes (/docs, /openapi.json, etc.)
            if route.path.startswith("/docs") or route.path.startswith("/openapi"):
                continue
            
            # Clean up methods (FastAPI uses sets)
            methods = [m.upper() for m in route.methods if m != "HEAD"]
            registered[route.path] = methods

    # 1. Verify all declared surface routes exist with correct methods
    expected = {**FASTAPI_CONTRACT["surface"], **FASTAPI_CONTRACT.get("extra_routes", {})}
    
    for path, methods in expected.items():
        if path not in registered:
            raise RuntimeError(f"Contract violation: Expected route {path} is missing.")
        
        registered_methods = set(registered[path])
        expected_methods = set(methods)
        
        if not expected_methods.issubset(registered_methods):
            raise RuntimeError(
                f"Contract violation on {path}: "
                f"Expected {expected_methods}, got {registered_methods}"
            )

    # 2. Verify no undeclared routes are exposed
    for path in registered:
        # Ignore FastAPI's automatically generated paths
        if path in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"):
            continue
        
        if path not in expected:
            raise RuntimeError(f"Contract violation: Undeclared route {path} is exposed.")


def assert_mcp_contract(registered_tools: List[str]) -> None:
    """
    Validates that the MCP server's registered tools match the declared contract.
    """
    expected = set(MCP_CONTRACT["surface"].keys())
    actual = set(registered_tools)
    
    missing = expected - actual
    if missing:
        raise RuntimeError(f"MCP Contract violation: Missing tools {missing}")
        
    # (Optional) Check that legacy tools are explicitly registered under legacy
    # if your MCP server distinguishes them.
