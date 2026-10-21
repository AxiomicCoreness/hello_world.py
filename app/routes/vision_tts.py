"""Vision + TTS soft-gate stub — pairs vision catalog with TTS status."""
from __future__ import annotations

from fastapi import APIRouter
import logging

router = APIRouter(tags=["vision-tts"])
logger = logging.getLogger(__name__)


@router.get("/vision/tts")
def vision_tts_status() -> dict:
    vision_ok = False
    vision_filled = False
    vision_error = None

    # 1. Probe Vision Catalog
    try:
        from garden_surgery.vision_code_frequency_fleck_paste import FILLED as V_FILLED
        vision_ok = True
        vision_filled = bool(V_FILLED)
    except ImportError as e:
        vision_error = f"Vision module missing: {e}"
        logger.warning(vision_error)
    except Exception as e:
        # Only catch standard Exceptions, avoiding KeyboardInterrupt/SystemExit
        vision_error = f"Vision probe failed: {e}"
        logger.error(vision_error, exc_info=True)

    # 2. Probe TTS Route
    tts_ok = False
    tts_filled = False
    tts_error = None
    try:
        from app.routes.tts import FILLED as T_FILLED
        tts_ok = True
        tts_filled = bool(T_FILLED)
    except ImportError as e:
        tts_error = f"TTS module missing: {e}"
        logger.warning(tts_error)
    except Exception as e:
        tts_error = f"TTS probe failed: {e}"
        logger.error(tts_error, exc_info=True)

    # 3. Compose response (explicit keys to prevent dict override attacks)
    response = {
        "ok": True,
        "filled": False,
        "vision_reachable": vision_ok,
        "vision_filled": vision_filled,
        "tts_reachable": tts_ok,
        "tts_filled": tts_filled,
        "message": "vision/tts soft-gate; no synthesis",
    }

    # 4. Conditionally attach error details under safe, namespaced keys
    if vision_error:
        response["vision_error"] = vision_error
    if tts_error:
        response["tts_error"] = tts_error

    return response
