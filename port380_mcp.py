#!/usr/bin/env python3
"""
port380_mcp.py – A/B/C Protocol Gateway + DeepSeek-assisted dispatch
MCP surface for the Sovereign Engine (OIDC optional; local contracts + LLM).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

PHI = (1 + math.sqrt(5)) / 2
GARDEN_SECRET = os.environ.get("X_GARDEN_SECRET", os.environ.get("GARDEN_SECRET", "wood_dragon_0.91"))
CONTRACT_DIR = os.environ.get("CONTRACT_DIR", "./contracts")
THRESHOLD_ERROR = 0.5
PHASE_TARGET = 202.6
PHASE_TOLERANCE = 2.0

try:
    from deepseek.api import get_client

    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

    def get_client():  # type: ignore
        raise RuntimeError("deepseek unavailable")

app = FastAPI(title="Port-380 MCP Surface", version="1.2.0")


class PulseRequest(BaseModel):
    phase_override: float | None = None
    source: str | None = None
    force_branch: str | None = Field(None, description="A|B|C override")
    use_deepseek: bool = True


class CompleteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    max_tokens: int = Field(256, ge=1, le=4096)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": type(exc).__name__, "detail": str(exc), "path": str(request.url.path)},
    )


def _auth(secret: str | None) -> None:
    if secret != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid X-Garden-Secret")


def _read_coherence_phase() -> tuple[float, float]:
    try:
        with open(f"{CONTRACT_DIR}/symplectic_status.agent.jsonl", "r") as f:
            lines = f.readlines()
            latest = json.loads(lines[-1]) if lines else {}
            return float(latest.get("coherence", 0.9999)), float(
                latest.get("phi_phase", time.time() % 78624.0)
            )
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0.9999, time.time() % 78624.0


def _select_branch(e: float, phi_phase: float, force: str | None) -> str:
    if force in ("A", "B", "C"):
        return force
    if e > THRESHOLD_ERROR:
        return "A"
    if abs(phi_phase - PHASE_TARGET) > PHASE_TOLERANCE:
        return "C"
    return "B"


async def _branch_prompt(branch: str, coherence: float, phi_phase: float, e: float) -> Optional[Dict[str, Any]]:
    if not DEEPSEEK_AVAILABLE:
        return None
    templates = {
        "A": (
            f"Strike X immediate flush. coherence={coherence:.6f} error={e:.6f}. "
            f"Generate a 6-entry WASP-107b flush plan (bullet list)."
        ),
        "B": (
            f"Natural cron hold. coherence={coherence:.6f} phase={phi_phase:.3f}. "
            f"Suggest Merkle temper factor for next 6h window."
        ),
        "C": (
            f"E9→Choir Trappist reroute. phase={phi_phase:.3f} target={PHASE_TARGET}. "
            f"Propose frequency map correction anchored at phi^-2."
        ),
    }
    try:
        return await get_client().complete(templates[branch], max_tokens=200)
    except Exception as ex:
        return {"mode": "error", "text": str(ex)}


@app.get("/health")
async def health_check():
    online = False
    if DEEPSEEK_AVAILABLE:
        try:
            online = get_client().online
        except Exception:
            online = False
    return {
        "status": "alive",
        "coherence": 1.0 - 1e-18,
        "branch": "HEALTHY",
        "deepseek": DEEPSEEK_AVAILABLE,
        "deepseek_online": online,
    }


@app.get("/status")
async def get_status():
    return {
        "service": "port-380-gate",
        "phase_lock": PHASE_TARGET,
        "state": "ETERNAL_NOW",
        "deepseek": DEEPSEEK_AVAILABLE,
    }


@app.get("/380")
async def identity_380():
    return {
        "layer": 314,
        "port_identity": 380,
        "phase_deg": PHASE_TARGET,
        "phi": PHI,
        "seal": "LAYER314_GATE",
        "deepseek_routes": ["/deepseek/complete", "/deepseek/stream", "/pulse", "/gate"],
    }


@app.post("/pulse")
async def gate_pulse(
    request: PulseRequest = PulseRequest(),
    x_garden_secret: str | None = Header(None),
):
    _auth(x_garden_secret)
    coherence, phi_phase = _read_coherence_phase()
    if request.phase_override is not None:
        phi_phase = request.phase_override
    e = 1.0 - coherence
    branch = _select_branch(e, phi_phase, request.force_branch)

    seal_input = f"{branch}|{coherence}|{phi_phase}|{int(time.time())}"
    sub_seal = hashlib.sha256(seal_input.encode()).hexdigest()[:16]

    llm: Optional[Dict[str, Any]] = None
    if request.use_deepseek and branch in ("A", "C"):
        llm = await _branch_prompt(branch, coherence, phi_phase, e)

    return {
        "branch": branch,
        "coherence": coherence,
        "phi_phase": phi_phase,
        "error": e,
        "sub_seal": sub_seal,
        "recommended_action": {
            "A": "force_immediate_flush",
            "B": "wait_for_cron_cycle",
            "C": "reroute_to_trappist_harmony",
        }[branch],
        "deepseek": llm,
        "status": "DECOUPLED_WORKAROUND_ACTIVE",
    }


@app.post("/gate")
async def gate_proxy(
    payload: dict | None = None,
    x_garden_secret: str | None = Header(None),
):
    force = None
    use_ds = True
    if isinstance(payload, dict):
        force = payload.get("force_branch") or payload.get("branch")
        if "use_deepseek" in payload:
            use_ds = bool(payload["use_deepseek"])
    return await gate_pulse(
        PulseRequest(force_branch=force, use_deepseek=use_ds, source="gate"),
        x_garden_secret,
    )


# ---- DeepSeek exposed on MCP surface (same process) ----
@app.post("/deepseek/complete")
async def mcp_deepseek_complete(
    body: CompleteRequest,
    x_garden_secret: str | None = Header(None),
):
    _auth(x_garden_secret)
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")
    result = await get_client().complete(body.prompt, max_tokens=body.max_tokens)
    if result.get("mode") == "error":
        raise HTTPException(status_code=502, detail=result.get("text", "upstream error"))
    return result


@app.post("/deepseek/stream")
async def mcp_deepseek_stream(
    body: CompleteRequest,
    x_garden_secret: str | None = Header(None),
):
    _auth(x_garden_secret)
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")

    async def event_gen():
        try:
            async for chunk in get_client().stream(body.prompt, max_tokens=body.max_tokens):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [error:{type(e).__name__}] {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
