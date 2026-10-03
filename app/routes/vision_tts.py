"""Vision + TTS soft-gate stub — pairs vision catalog with TTS status."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["vision-tts"])


@router.get("/vision/tts")
def vision_tts_status() -> dict:
    vision_ok = False
    vision_detail: dict = {}
    try:
        from garden_surgery.vision_code_frequency_fleck_paste import FILLED as V_FILLED

        vision_ok = True
        vision_detail = {"vision_filled": bool(V_FILLED)}
    except Exception as e:
        vision_detail = {"vision_error": str(e)}

    return {
        "ok": True,
        "filled": False,
        "vision_reachable": vision_ok,
        "tts_filled": False,
        "message": "vision/tts soft-gate; no synthesis",
        **vision_detail,
    }
