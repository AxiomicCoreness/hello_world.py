"""MCP routes — unfilled stub."""

from fastapi import APIRouter
from fastMCP.constants import FILLED

router = APIRouter(prefix="/mcp", tags=["mcp"])

@router.get("/")
async def mcp_status():
    return {
        "filled": FILLED,
        "status": "unfilled",
        "message": "MCP remains FILLED=False"
    }
