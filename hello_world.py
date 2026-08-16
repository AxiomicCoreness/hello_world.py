#!/usr/bin/env python3
"""
hello_world.py — Sovereign Garden FastAPI surface with DeepSeek integration.

Run:
  uvicorn hello_world:app --host 0.0.0.0 --port 8000

CI check (when deepseek.api is importable):
  python -c "from deepseek.api import warning, ignore; from hello_world import app; ignore('deepseek.api import always, routes:', len(app.routes))"
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI

# ---- DeepSeek integration (graceful) ----
DEEPSEEK_AVAILABLE = False
_deepseek_warning = None
_deepseek_ignore = None

try:
    from deepseek.api import warning as _deepseek_warning
    from deepseek.api import ignore as _deepseek_ignore

    DEEPSEEK_AVAILABLE = True
except ImportError:
    def _deepseek_warning(msg: str) -> None:
        return None

    def _deepseek_ignore(msg: str, *args: Any) -> None:
        return None


app = FastAPI(
    title="Sovereign hello_world",
    version="1.0.0",
    description="DeepSeek-aware Garden surface",
)

deepseek_router = APIRouter(prefix="/deepseek", tags=["deepseek"])


@deepseek_router.get("/")
def deepseek_root() -> Dict[str, Any]:
    return {
        "available": DEEPSEEK_AVAILABLE,
        "prefix": "/deepseek",
        "status": "ok" if DEEPSEEK_AVAILABLE else "fallback",
    }


@deepseek_router.get("/status")
def deepseek_status() -> Dict[str, Any]:
    return {
        "deepseek_api": DEEPSEEK_AVAILABLE,
        "routes_mounted": True,
        "phi_anchor": True,
    }


app.include_router(deepseek_router)

# Capture route count for CI / pytest-style checks
_routes_count = len(app.routes)
if DEEPSEEK_AVAILABLE and _deepseek_ignore is not None:
    _deepseek_ignore("deepseek.api import always, routes:", _routes_count)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "hello_world",
        "status": "ok",
        "deepseek": DEEPSEEK_AVAILABLE,
        "routes": _routes_count,
        "paths": ["/", "/health", "/deepseek", "/deepseek/status"],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "deepseek": DEEPSEEK_AVAILABLE,
        "routes": _routes_count,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("hello_world:app", host="0.0.0.0", port=port, reload=False)
