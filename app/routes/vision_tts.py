"""Vision + TTS soft-gate stub."""
from __future__ import annotations
from fastapi import APIRouter
router = APIRouter(tags=["vision-tts"])
@router.get("/vision/tts")
def vision_tts_status() -> dict:
    return {"ok": True, "filled": False, "tts_filled": False, "message": "vision/tts soft-gate; no synthesis"}
