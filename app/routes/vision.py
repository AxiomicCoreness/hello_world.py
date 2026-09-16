"""Vision / fleck paste surface — ledger 9130 catalog (stub, FILLED=False)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["vision"])


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

        return {
            "ok": True,
            "filled": FILLED,
            "ledger_entry": LEDGER_ENTRY,
            "seal": SEAL,
            "frequency": dict(FREQUENCY),
            "holds": dict(HOLDS),
            "vision": list(VISION),
            "notes": dict(NOTES),
            "stub": vision_code_frequency_fleck_paste(),
        }
    except Exception as e:
        return {
            "ok": False,
            "filled": False,
            "error": str(e),
            "message": "vision catalog unavailable",
        }
