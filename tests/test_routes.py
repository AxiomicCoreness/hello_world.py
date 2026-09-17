"""Route stub tests — MCP remains unfilled."""

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
