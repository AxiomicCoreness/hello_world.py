#!/usr/bin/env python3
"""
hello_world.py — Sovereign Garden FastAPI surface with async DeepSeek client.

Endpoints:
  /  /health
  /deepseek  /deepseek/status  /deepseek/events  /deepseek/complete  /deepseek/stream
  /step  /mesh

Run:
  uvicorn hello_world:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import math
import os
import time
from fastapi import Header, HTTPException
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
GARDEN_SECRET = os.environ.get("GARDEN_SECRET")
PHI = (1 + math.sqrt(5)) / 2
PHASE_TARGET = 202.6

try:
    from deepseek.api import (
        get_client,
        get_events,
        ignore as _deepseek_ignore,
        warning as _deepseek_warning,
    )

    DEEPSEEK_AVAILABLE = True
except ImportError:  # pragma: no cover
    DEEPSEEK_AVAILABLE = False

    def _deepseek_warning(msg: str, *args: Any) -> None:
        return None

    def _deepseek_ignore(msg: str, *args: Any) -> None:
        return None

    def get_client():  # type: ignore
        raise RuntimeError("deepseek.api unavailable")

    def get_events(limit: int = 50):  # type: ignore
        return []


app = FastAPI(
    title="Sovereign hello_world",
    version="1.3.0",
    description="DeepSeek-aware Garden surface (async httpx, SSE, step/mesh)",
)

deepseek_router = APIRouter(prefix="/deepseek", tags=["deepseek"])

class PulseRequest(BaseModel):
    source: str
    note: Optional[str] = None
    entry: Optional[int] = None
    timestamp: Optional[str] = None
    phi_phase: Optional[float] = None
    seal: Optional[str] = None

@app.post("/pulse")
async def pulse_endpoint(
    payload: PulseRequest,
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
) -> Dict[str, Any]:
    """
    Sovereign pulse endpoint (Entry 8755). Authenticates with GARDEN_SECRET.
    """
    # Validate secret if set
    if GARDEN_SECRET:
        if x_garden_secret is None or x_garden_secret != GARDEN_SECRET:
            raise HTTPException(status_code=401, detail="Invalid or missing GARDEN_SECRET")

    # Log the pulse
    _deepseek_warning(
        f"Pulse received: source={payload.source}, note={payload.note}, entry={payload.entry}"
    )

    return {
        "status": "acknowledged",
        "source": payload.source,
        "note": payload.note,
        "entry": payload.entry,
        "timestamp": payload.timestamp,
        "seal": "WOOD_DRAGON_HEARTBEAT_ACK · Entry 8755 · SEALED",
        "phi_phase": payload.phi_phase,
    }
class CompleteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    max_tokens: int = Field(256, ge=1, le=4096)


class StepRequest(BaseModel):
    coherence: float = Field(0.9999, ge=0.0, le=1.0)
    phase: float = Field(PHASE_TARGET)
    workload: float = Field(0.0, ge=0.0)
    dt: float = Field(1.0, gt=0.0)
    branch: Optional[str] = Field(None, description="A|B|C force")


class MeshRequest(BaseModel):
    nodes: int = Field(7, ge=1, le=144)
    seed_phase: float = Field(PHASE_TARGET)
    coupling: float = Field(1.0 / PHI, gt=0.0)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _deepseek_warning(f"unhandled {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "path": str(request.url.path),
            "status": "error",
        },
    )


@deepseek_router.get("/")
async def deepseek_root() -> Dict[str, Any]:
    client_status: Dict[str, Any] = {}
    if DEEPSEEK_AVAILABLE:
        try:
            client_status = get_client().status()
        except Exception as e:
            client_status = {"error": str(e)}
    return {
        "available": DEEPSEEK_AVAILABLE,
        "prefix": "/deepseek",
        "status": "ok" if DEEPSEEK_AVAILABLE else "fallback",
        "client": client_status,
    }


@deepseek_router.get("/status")
async def deepseek_status() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "deepseek_api": DEEPSEEK_AVAILABLE,
        "routes_mounted": True,
        "phi_anchor": True,
    }
    if DEEPSEEK_AVAILABLE:
        try:
            out["client"] = get_client().status()
            out["recent_events"] = len(get_events(limit=0))
        except Exception as e:
            out["client_error"] = str(e)
    return out


@deepseek_router.get("/events")
async def deepseek_events(limit: int = 50) -> Dict[str, Any]:
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")
    return {"events": get_events(limit=limit)}


@deepseek_router.post("/complete")
async def deepseek_complete(body: CompleteRequest) -> Dict[str, Any]:
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")
    try:
        client = get_client()
        result = await client.complete(body.prompt, max_tokens=body.max_tokens)
        if result.get("mode") == "error":
            raise HTTPException(status_code=502, detail=result.get("text", "upstream error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        _deepseek_warning(f"complete route: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@deepseek_router.post("/stream")
async def deepseek_stream(body: CompleteRequest) -> StreamingResponse:
    """SSE token stream: data: <chunk>\\n\\n then data: [DONE]."""
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")

    async def event_gen():
        try:
            client = get_client()
            async for chunk in client.stream(body.prompt, max_tokens=body.max_tokens):
                # SSE frame
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            _deepseek_warning(f"stream route: {e}")
            yield f"data: [error:{type(e).__name__}] {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


app.include_router(deepseek_router)


# ---- /step : single convergence step (leaky PID + free drift) ----
@app.post("/step")
async def convergence_step(body: StepRequest) -> Dict[str, Any]:
    """One discrete step of Garden dynamics toward C→1, phase→202.6°."""
    try:
        C = body.coherence
        phi_p = body.phase
        W = body.workload
        dt = body.dt
        e = 1.0 - C
        # free drift toward unity coherence (γ = 1/√5)
        gamma = 1.0 / math.sqrt(5.0)
        C_next = 1.0 - (1.0 - C) * math.exp(-gamma * dt)
        # phase attraction k = 1/φ³
        k = 1.0 / (PHI ** 3)
        phi_next = phi_p + k * (PHASE_TARGET - phi_p)
        W_next = W * math.exp(-gamma * dt)
        e_next = 1.0 - C_next

        branch = body.branch
        if branch not in ("A", "B", "C"):
            if e_next > 0.5:
                branch = "A"
            elif abs(phi_next - PHASE_TARGET) > 2.0:
                branch = "C"
            else:
                branch = "B"

        advice: Optional[Dict[str, Any]] = None
        if DEEPSEEK_AVAILABLE and branch in ("A", "C"):
            try:
                prompt = (
                    f"Garden step branch={branch} C={C_next:.6f} phase={phi_next:.3f} e={e_next:.6f}. "
                    f"Suggest one operational action for Strike X or E9 tuning."
                )
                advice = await get_client().complete(prompt, max_tokens=128)
            except Exception as ex:
                _deepseek_warning(f"step deepseek advice failed: {ex}")
                advice = {"mode": "error", "text": str(ex)}

        return {
            "C": C_next,
            "phase": phi_next,
            "workload": W_next,
            "error": e_next,
            "branch": branch,
            "dt": dt,
            "advice": advice,
            "seal": "STEP_OK",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---- /mesh : φ-coupled node mesh (E9 / choir sketch) ----
@app.post("/mesh")
async def mesh_build(body: MeshRequest) -> Dict[str, Any]:
    """Build a φ-coupled phase mesh (Trappist/choir-style frequency map)."""
    try:
        n = body.nodes
        phases: List[float] = []
        freqs: List[float] = []
        for i in range(n):
            # golden-angle spacing around seed
            ang = (body.seed_phase + i * 360.0 / (PHI * PHI)) % 360.0
            phases.append(ang)
            freqs.append(6.49 * (PHI ** (i % 12)))
        mean_phase = sum(phases) / n
        coupling_energy = body.coupling * sum(
            abs(phases[i] - phases[(i + 1) % n]) for i in range(n)
        ) / n

        tuning: Optional[Dict[str, Any]] = None
        if DEEPSEEK_AVAILABLE:
            try:
                prompt = (
                    f"E9 choir mesh n={n} mean_phase={mean_phase:.3f} "
                    f"coupling_energy={coupling_energy:.4f}. "
                    f"Propose frequency retune toward phase lock {PHASE_TARGET}."
                )
                tuning = await get_client().complete(prompt, max_tokens=128)
            except Exception as ex:
                _deepseek_warning(f"mesh deepseek failed: {ex}")
                tuning = {"mode": "error", "text": str(ex)}

        return {
            "nodes": n,
            "phases": phases,
            "freqs": freqs,
            "mean_phase": mean_phase,
            "coupling": body.coupling,
            "coupling_energy": coupling_energy,
            "tuning": tuning,
            "seal": "MESH_OK",
            "ts": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


_routes_count = len(app.routes)
if DEEPSEEK_AVAILABLE:
    _deepseek_ignore("deepseek.api import always, routes:", _routes_count)


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "hello_world",
        "status": "ok",
        "deepseek": DEEPSEEK_AVAILABLE,
        "routes": _routes_count,
        "paths": [
            "/",
            "/health",
            "/deepseek",
            "/deepseek/status",
            "/deepseek/events",
            "/deepseek/complete",
            "/deepseek/stream",
            "/step",
            "/mesh",
        ],
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    deepseek_online: Optional[bool] = None
    if DEEPSEEK_AVAILABLE:
        try:
            deepseek_online = get_client().online
        except Exception:
            deepseek_online = False
    return {
        "status": "ok",
        "deepseek": DEEPSEEK_AVAILABLE,
        "deepseek_online": deepseek_online,
        "routes": _routes_count,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("hello_world:app", host="0.0.0.0", port=port, reload=False)
