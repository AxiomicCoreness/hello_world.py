#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/api.py

Sovereign FastAPI surface for DiffuseKLCache + Orchestrator health.
Entry 620 – Local smoke-test validated, now materialised on main.

Endpoints:
  GET  /test
  GET  /health
  GET  /diffuse_kl
  GET  /diffuse
  POST /add
  POST /objective
"""

from typing import Dict, Any, Optional, List
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from core.diffuse_kl_cache import DiffuseKLCache
except ImportError:
    from .diffuse_kl_cache import DiffuseKLCache

# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------
app = FastAPI(
    title="Sovereign DiffuseKL API",
    version="1.0.0",
    description="FastAPI surface for DiffuseKLCache (Entry 620)"
)

# Global cache instance
cache = DiffuseKLCache(M=1024, T=1.0, beta=0.1)


class AddEntryRequest(BaseModel):
    entry: str
    embedding: List[float]
    entry_id: Optional[int] = None


class ObjectiveRequest(BaseModel):
    trajectory_log_prob: float = 0.0


@app.get("/test")
def test() -> Dict[str, Any]:
    """Simple connectivity / smoke test endpoint."""
    return {
        "status": "ok",
        "message": "Sovereign FastAPI surface is live",
        "endpoints": ["/test", "/diffuse_kl", "/diffuse", "/health", "/add", "/objective"],
        "coherence": 1.0,
        "phase_lock": 202.6
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check that includes cache status."""
    report = cache.health_report()
    return {
        "status": "healthy",
        "service": "sovereign-diffuse-kl",
        "cache": report,
        "coherence": 1.0,
        "entropy_floor": "phi^-1418"
    }


@app.get("/diffuse_kl")
def diffuse_kl() -> Dict[str, Any]:
    """Return the current diffuse KL value and summary."""
    try:
        value = cache.diffuse_kl()
        summary = cache.summary()
        return {
            "diffuse_kl": value,
            "summary": summary,
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diffuse")
def diffuse() -> Dict[str, Any]:
    """Higher-level view based on /diffuse_kl."""
    kl = cache.diffuse_kl()
    summary = cache.summary()
    return {
        "status": "ok",
        "diffuse_kl": kl,
        "cache_size": summary["entries"],
        "top_bin": summary["top_bin"],
        "top_bin_mass": summary["top_bin_mass"],
        "M": summary["M"],
        "message": "Diffuse view derived from DiffuseKLCache"
    }


@app.post("/add")
def add_entry(req: AddEntryRequest) -> Dict[str, Any]:
    """Add an entry + embedding to the cache."""
    try:
        emb = np.array(req.embedding, dtype=np.float64)
        cache.add_entry(req.entry, emb, req.entry_id)
        return {
            "status": "added",
            "entry": req.entry,
            "bin": cache.hash_entry(req.entry),
            "current_entries": len(cache.ledger)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/objective")
def objective(req: ObjectiveRequest) -> Dict[str, Any]:
    """Compute the agent improvement objective."""
    try:
        value = cache.objective(req.trajectory_log_prob)
        return {
            "objective": value,
            "trajectory_log_prob": req.trajectory_log_prob,
            "diffuse_kl": cache.diffuse_kl(),
            "beta": cache.beta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\u29c1\u2200 Starting Sovereign DiffuseKL FastAPI on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
