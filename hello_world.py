#!/usr/bin/env python3
"""
hello_world.py — Sovereign Garden FastAPI surface with DeepSeek integration.

Run:
  uvicorn hello_world:app --host 0.0.0.0 --port 8000

CI:
  python -c "from deepseek.api import warning, ignore; from hello_world import app; ignore('deepseek.api import always, routes:', len(app.routes))"
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---- DeepSeek (functional module; always importable via local package) ----
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
    version="1.1.0",
    description="DeepSeek-aware Garden surface (functional client + event log)",
)

deepseek_router = APIRouter(prefix="/deepseek", tags=["deepseek"])


class CompleteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    max_tokens: int = Field(256, ge=1, le=4096)


@deepseek_router.get("/")
def deepseek_root() -> Dict[str, Any]:
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
def deepseek_status() -> Dict[str, Any]:
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
def deepseek_events(limit: int = 50) -> Dict[str, Any]:
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")
    return {"events": get_events(limit=limit)}


@deepseek_router.post("/complete")
def deepseek_complete(body: CompleteRequest) -> Dict[str, Any]:
    if not DEEPSEEK_AVAILABLE:
        raise HTTPException(status_code=503, detail="deepseek.api unavailable")
    client = get_client()
    return client.complete(body.prompt, max_tokens=body.max_tokens)


app.include_router(deepseek_router)

_routes_count = len(app.routes)
if DEEPSEEK_AVAILABLE:
    _deepseek_ignore("deepseek.api import always, routes:", _routes_count)


@app.get("/")
def root() -> Dict[str, Any]:
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
        ],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
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
