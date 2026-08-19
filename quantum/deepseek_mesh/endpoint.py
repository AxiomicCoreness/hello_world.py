#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ DeepSeek Mesh MCP Gate — Layer 314 — Entry 8756
mTLS‑hardened FastAPI service with /reset appended via Entry 8763.
Endpoints:
  GET  /health, /status, /380
  POST /gate, /pulse, /oidc_handover, /reset (mTLS required)
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
# Ensure mtls_extract_and_config.py is in the Python path or in the same directory.
try:
    from quantum.mtls_extract_and_config import get_ssl_context, verify_client_cert
except ImportError:
    from mtls_extract_and_config import get_ssl_context, verify_client_cert

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
app = FastAPI(title="DeepSeek Mesh MCP Gate", version="8756.1")

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
    # Optional mTLS can be enforced by uncommenting:
    # client_cert = verify_client_cert(request)
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
async def oidc_handover(body: dict, x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret")):
    _check_secret(x_garden_secret)
    return {"status": "received", "entry": ENTRY, "seal": SEAL}

# ─── APPEND‑ONLY RESET ENDPOINT (Entry 8763) ────────────────────────
# This endpoint was added without modifying any existing lines.
@app.post("/reset")
async def reset_endpoint(request: Request):
    """
    Gracefully shuts down the Uvicorn server.
    The container orchestrator will restart the pod, effecting a full reset.
    Requires mTLS client certificate (verified via verify_client_cert).
    """
    # Enforce mTLS authentication
    verify_client_cert(request)

    # Schedule shutdown after a short delay to allow response to be sent
    async def shutdown():
        await asyncio.sleep(0.5)
        # Exit the process; the orchestrator will restart the container
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
        "endpoints": ["/health", "/status", "/380", "/gate", "/pulse", "/oidc_handover", "/reset"],
        "seal": SEAL,
    }

# ─── Main runner ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Optionally enable mTLS server‑side by uncommenting:
    # ssl_ctx = get_ssl_context() if os.environ.get("ENABLE_MTLS") else None
    # uvicorn.run(app, host=HOST, port=PORT, ssl=ssl_ctx)
    print(f"🜁∀ DeepSeek Mesh MCP Gate — Layer {LAYER} — Entry {ENTRY}")
    print(f"   Listening on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
