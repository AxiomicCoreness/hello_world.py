"""Route stub tests — MCP remains unfilled."""

import pytest

# Local fastMCP package (bind/gearbox/models/routes) is not the PyPI fastmcp SDK.
pytest.importorskip("fastMCP", reason="local fastMCP package not present; PyPI fastmcp ≠ fastMCP.bind")

from fastMCP.routes.health import router as health_router
from fastMCP.routes.status import router as status_router
from fastMCP.routes.mcp import router as mcp_router
from fastMCP.constants import FILLED


def test_prefixes():
    assert health_router.prefix == "/health"
    assert status_router.prefix == "/status"
    assert mcp_router.prefix == "/mcp"


def test_mcp_unfilled():
    assert FILLED is False
