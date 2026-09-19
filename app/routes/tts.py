"""FastAPI TTS stub — FILLED=False."""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
router = APIRouter(tags=["tts"])
FILLED = False
class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    voice: str = Field(default="stub", max_length=64)
"""FastAPI TTS stub — no audio synthesis; FILLED=False surface."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["tts"])

FILLED = False
BIND_POLICY = "127.0.0.1 only for local probes; pod may use cluster DNS"


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    voice: str = Field(default="stub", max_length=64)


class TTSResponse(BaseModel):
    ok: bool
    filled: bool
    message: str
    text_len: int
    voice: str
    audio_url: str | None = None
@router.get("/tts")
def tts_status() -> dict:
    return {"ok": True, "filled": FILLED, "status": "stub", "message": "TTS unfilled"}
@router.post("/tts", response_model=TTSResponse)
def tts_synthesize(body: TTSRequest) -> TTSResponse:
    return TTSResponse(ok=True, filled=FILLED, message="stub only", text_len=len(body.text), voice=body.voice, audio_url=None)


@router.get("/tts")
def tts_status() -> dict:
    return {
        "ok": True,
        "filled": FILLED,
        "status": "stub",
        "message": "TTS not synthesized; MCP/TTS remain unfilled",
        "bind_policy": BIND_POLICY,
    }


@router.post("/tts", response_model=TTSResponse)
def tts_synthesize(body: TTSRequest) -> TTSResponse:
    return TTSResponse(
        ok=True,
        filled=FILLED,
        message="stub only — no audio bytes generated",
        text_len=len(body.text),
        voice=body.voice,
        audio_url=None,
    )
