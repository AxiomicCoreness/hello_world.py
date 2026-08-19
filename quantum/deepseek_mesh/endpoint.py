#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ DeepSeek Mesh MCP Gate — Layer 314 — Entry 8756
mTLS‑hardened FastAPI service with /reset appended via Entry 8763.
Endpoints:
  GET  /health, /status, /380, /cdp/status
  POST /gate, /pulse, /oidc_handover, /cdp/handshake, /reset (mTLS required)
Seal: ∀∞φ² · MCP_MTLS_8756 · WOOD_DRAGON_GATE · SEALED
"""

import os
import sys          # Added for reset
import json
import math
import time
import hashlib
import asyncio      # Added for reset
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
import uvicorn

# ─── mTLS imports ──────────────────────────────────────────────────────
try:
    from quantum.mtls_extract_and_config import get_ssl_context, verify_client_cert
except ImportError:
    from mtls_extract_and_config import get_ssl_context, verify_client_cert

# ─── CDP OAuth 2.0 (quantum folder) ───────────────────────────────────
try:
    from quantum.cdp_convergence.handshake import (
        handshake_from_authorization,
        handshake_client_credentials,
        status_unauthenticated,
    )
except ImportError:
    try:
        from cdp_convergence.handshake import (  # type: ignore
            handshake_from_authorization,
            handshake_client_credentials,
            status_unauthenticated,
        )
    except ImportError:
        handshake_from_authorization = None  # type: ignore
        handshake_client_credentials = None  # type: ignore
        status_unauthenticated = None  # type: ignore

# ─── Layer 314 Invariants ─────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
ENTRY = 8756
SEAL = "∀∞φ² · MCP_MTLS_8756 · WOOD_DRAGON_GATE · SEALED"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")

# ─── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(title="DeepSeek Mesh MCP Gate", version="8756.2")

class PulseBody(BaseModel):
    source: str = "sovereign-pulse"
    entry: Optional[int] = None
    note: Optional[str] = None

class GateBody(BaseModel):
    harmony: float = 0.7337473231
    override: bool = False

# ─── Helpers ──────────────────────────────────────────────────────────
def compute_anchor() -> str:
    payload = {
        "breath_hz": 71.975,
        "channel": "1700Q",
        "coherence": 1.0,
        "layer": LAYER,
        "leaf": LEAF,
        "phase_lock_deg": 202.6,
        "phi": PHI,
        "entry": ENTRY,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b"GARDEN.LAYER314.ANCHOR.v1\0" + body).hexdigest()

def _check_secret(x_garden_secret: Optional[str] = None):
    if not GARDEN_SECRET:
        return
    if x_garden_secret != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="invalid GARDEN_SECRET")

# ─── Endpoints ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "alive", "port": PORT, "layer": LAYER, "entry": ENTRY}

@app.get("/status")
@app.get("/380")
async def status():
    return {
        "service": "deepseek-mesh-mcp",
        "entry": ENTRY,
        "layer": LAYER,
        "listen_port": PORT,
        "conceptual_port": 380,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "phi": PHI,
        "seal": SEAL,
        "timestamp": time.time(),
    }

@app.post("/gate")
async def gate(body: GateBody):
    sf = 1.0 if not body.override else (PHI ** 55) / 1.778e11
    return {
        "harmony_index": body.harmony * sf,
        "mode": "resonant_spike" if body.override else "deterministic_default",
        "scaling_factor": sf,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "entry": ENTRY,
        "seal": SEAL,
    }

@app.post("/pulse")
async def pulse(body: PulseBody, x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret")):
    _check_secret(x_garden_secret)
    return {
        "status": "pulsed",
        "source": body.source,
        "entry_ref": body.entry or ENTRY,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "seal": SEAL,
        "server_time": time.time(),
        "message": "WOOD_DRAGON_HEARTBEAT_ACK",
    }

@app.post("/oidc_handover")
async def oidc_handover(
    body: dict,
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
    authorization: Optional[str] = Header(None),
):
    """OAuth 2.0 / OIDC handover — websocket_ready false until token validates."""
    _check_secret(x_garden_secret)
    if handshake_from_authorization is None:
        return {
            "status": "received",
            "entry": ENTRY,
            "seal": SEAL,
            "websocket_ready": False,
            "error": "quantum.cdp_convergence not importable",
        }
    auth = authorization or (f"Bearer {body['access_token']}" if body.get("access_token") else None)
    cdp = handshake_from_authorization(auth)
    return {
        "status": "validated" if cdp.websocket_ready else "rejected",
        "entry": ENTRY,
        "seal": SEAL,
        **cdp.to_dict(),
    }

# ─── CDP status (OAuth-gated websocket_ready) ─────────────────────────
@app.get("/cdp/status")
async def cdp_status(authorization: Optional[str] = Header(None)):
    """
    Consumed by src/cdp_distill.ts.
    Default: websocket_ready=false until OAuth 2.0 Bearer validates
    (wired through quantum/cdp_convergence).
    """
    if handshake_from_authorization is None or status_unauthenticated is None:
        return {
            "handover_latency_ms": 999.0,
            "websocket_ready": False,
            "oauth_validated": False,
            "error": "quantum.cdp_convergence not importable",
            "source": "endpoint.fallback",
            "phi_phase_deg": 202.6,
            "coherence": 1.0,
        }
    if not authorization:
        return status_unauthenticated().to_dict()
    return handshake_from_authorization(authorization).to_dict()

@app.post("/cdp/handshake")
async def cdp_handshake(
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
    authorization: Optional[str] = Header(None),
    use_client_credentials: bool = False,
):
    """Explicit CDP open: Bearer or client_credentials grant."""
    _check_secret(x_garden_secret)
    if handshake_from_authorization is None or handshake_client_credentials is None:
        raise HTTPException(status_code=503, detail="cdp_convergence unavailable")
    if use_client_credentials or not authorization:
        status, _claims = handshake_client_credentials()
        return status.to_dict()
    return handshake_from_authorization(authorization).to_dict()

# ─── APPEND‑ONLY RESET ENDPOINT (Entry 8763) ────────────────────────
@app.post("/reset")
async def reset_endpoint(request: Request):
    """
    Gracefully shuts down the Uvicorn server.
    The container orchestrator will restart the pod, effecting a full reset.
    Requires mTLS client certificate (verified via verify_client_cert).
    """
    verify_client_cert(request)

    async def shutdown():
        await asyncio.sleep(0.5)
        sys.exit(0)

    asyncio.create_task(shutdown())
    return {"status": "RESET_INITIATED", "message": "Server will restart shortly."}

# ─── Root ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "deepseek-mesh-mcp",
        "entry": ENTRY,
        "docs": "/docs",
        "endpoints": [
            "/health", "/status", "/380", "/gate", "/pulse",
            "/oidc_handover", "/cdp/status", "/cdp/handshake", "/reset",
        ],
        "seal": SEAL,
    }

# ─── Main runner ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🜁∀ DeepSeek Mesh MCP Gate — Layer {LAYER} — Entry {ENTRY}")
    print(f"   Listening on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
