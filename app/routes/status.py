from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/status")
def status():
    return {
        "phase_lock": settings.PHASE_LOCK,
        "mcp_filled": settings.MCP_FILLED,
        "coherence": 0.999947,
        "layer": 210,
        "phi_inv3_atlas": settings.PHI_INV3,
    }
