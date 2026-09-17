"""Health check routes."""

from fastapi import APIRouter
from fastMCP.constants import PHI, FILLED

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "phi": PHI,
        "filled": FILLED,
        "bind": "127.0.0.1:8024"
    }

@router.get("/phi")
async def phi_status():
    return {"phi": PHI, "phi_inv": 1/PHI, "phi2": PHI*PHI}
