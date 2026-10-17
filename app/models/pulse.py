from fastapi import APIRouter

from app.config import settings
from app.models.mcp import PulseResponse

router = APIRouter()


@router.get("/pulse", response_model=PulseResponse)
def pulse() -> PulseResponse:
    return PulseResponse(
        mcp="port380",
        filled=settings.MCP_FILLED,
        port=settings.MCP_PORT,
        phase_lock=settings.PHASE_LOCK,
        tick="6.49Hz",
    )
