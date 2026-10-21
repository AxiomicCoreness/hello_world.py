"""Vision / fleck paste surface — ledger 9130 catalog (stub, FILLED=False)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
import logging

router = APIRouter(tags=["vision"])
logger = logging.getLogger(__name__)

# Fallback definitions in case the garden_surgery module is missing
FALLBACK_STATE = {
    "FILLED": False,
    "FREQUENCY": {"hz": 0.0},
    "HOLDS": {},
    "LEDGER_ENTRY": "missing",
    "NOTES": {"error": "garden_surgery module not found"},
    "SEAL": "unsynced",
    "VISION": [],
    "STUB": {"ok": False, "message": "stub unavailable"}
}

@router.get("/vision")
def vision_status():
    try:
        from garden_surgery.vision_code_frequency_fleck_paste import (
            FILLED,
            FREQUENCY,
            HOLDS,
            LEDGER_ENTRY,
            NOTES,
            SEAL,
            VISION,
            vision_code_frequency_fleck_paste,
        )
        
        stub_result = vision_code_frequency_fleck_paste()
        
    except ImportError as e:
        logger.error(f"Vision module import failed: {e}")
        return {
            "ok": True,  # API works, but backend catalog is absent
            "filled": FALLBACK_STATE["FILLED"],
            "ledger_entry": FALLBACK_STATE["LEDGER_ENTRY"],
            "seal": FALLBACK_STATE["SEAL"],
            "error_detail": "Module garden_surgery.vision_code_frequency_fleck_paste not found",
            "stub": FALLBACK_STATE["STUB"]
        }
    except Exception as e:
        logger.exception("Unexpected error in vision catalog")
        raise HTTPException(status_code=500, detail=f"Vision catalog failed: {str(e)}")

    return {
        "ok": True,
        "filled": FILLED,
        "ledger_entry": LEDGER_ENTRY,
        "seal": SEAL,
        "frequency": dict(FREQUENCY),
        "holds": dict(HOLDS),
        "vision": list(VISION),
        "notes": dict(NOTES),
        "stub": stub_result,
    }
