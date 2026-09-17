"""Status routes."""

from fastapi import APIRouter
from fastMCP.constants import BIND_HOST, BIND_PORT, FILLED

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/")
async def status():
    return {
        "host": BIND_HOST,
        "port": BIND_PORT,
        "filled": FILLED,
        "state": "loopback_only"
    }
