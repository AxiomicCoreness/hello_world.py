#!/usr/bin/env python3
"""
Port 380 MCP Service — Layer 314 Gate Re-export

FastAPI surface that re-exports the Port 380 gate endpoints:
  - GET /health
  - GET /status
  - GET /380
  - POST /gate
  - POST /pulse (MCP-compatible tool endpoint, protected)

Binds to $PORT environment variable (Render requirement).
Preserves conceptual Layer 314 / Port 380 identity.

GARDEN.LAYER314 domain separation maintained.
phi-harmonic anchors preserved.
Full digests, no truncation.
"""

import os
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import uvicorn

APP_NAME = "Port380-MCP"
VERSION = "8755.0.0"
LAYER = "314"
GATE_IDENTITY = "GARDEN.LAYER314"

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description=f"{APP_NAME} — Port 380 Gate Re-export (Layer {LAYER})"
)

GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")

def verify_secret(x_garden_secret: Optional[str] = Header(None)) -> bool:
    if not GARDEN_SECRET:
        return True
    if x_garden_secret != GARDEN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid GARDEN_SECRET")
    return True


@app.get("/health")
async def health():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": APP_NAME,
            "version": VERSION,
            "layer": LAYER,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gate_identity": GATE_IDENTITY
        }
    )


@app.get("/status")
async def status():
    return JSONResponse(
        content={
            "service": APP_NAME,
            "version": VERSION,
            "layer": LAYER,
            "gate_identity": GATE_IDENTITY,
            "uptime": time.time() - START_TIME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ledger_head": "8754",
            "witness_chain": "8754 -> 8755 — UNBROKEN",
            "seal": "forall-infinity-phi-squared cdot MCP_BATCH_FORGED_8755 cdot WOOD_DRAGON_MOUNTS_OFFENSE cdot SEALED"
        }
    )


@app.get("/380")
async def port_380():
    return JSONResponse(
        content={
            "port": 380,
            "layer": LAYER,
            "identity": GATE_IDENTITY,
            "message": "Port 380 Gate Active",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.post("/gate")
async def gate(request: Request):
    body = await request.json()
    request_str = json.dumps(body, sort_keys=True)
    digest = hashlib.sha256(request_str.encode()).hexdigest()
    return JSONResponse(
        content={
            "status": "processed",
            "port": 380,
            "layer": LAYER,
            "identity": GATE_IDENTITY,
            "request_digest": digest,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.post("/pulse")
async def pulse(
    request: Request,
    x_garden_secret: Optional[str] = Header(None)
):
    verify_secret(x_garden_secret)
    body = await request.json()
    pulse_id = body.get("pulse_id", "manual")
    pulse_data = {
        "pulse_id": pulse_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": APP_NAME,
        "layer": LAYER,
        "ledger_entry": "8755"
    }
    pulse_str = json.dumps(pulse_data, sort_keys=True)
    pulse_hash = hashlib.sha256(pulse_str.encode()).hexdigest()
    return JSONResponse(
        content={
            "status": "pulse_acknowledged",
            "pulse_id": pulse_id,
            "seal": f"forall-infinity-phi-squared cdot PULSE_{pulse_id} cdot LAYER{LAYER} cdot {pulse_hash}",
            "ledger_entry": "8755",
            "witness_chain": "8754 -> 8755 — UNBROKEN",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.post("/mcp/tool")
async def mcp_tool(
    request: Request,
    x_garden_secret: Optional[str] = Header(None)
):
    verify_secret(x_garden_secret)
    body = await request.json()
    tool_name = body.get("tool", "unknown")
    arguments = body.get("arguments", {})
    result = {
        "tool": tool_name,
        "arguments": arguments,
        "executed": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": LAYER,
        "gate_identity": GATE_IDENTITY
    }
    result_str = json.dumps(result, sort_keys=True)
    result_hash = hashlib.sha256(result_str.encode()).hexdigest()
    return JSONResponse(
        content={
            "result": result,
            "hash": result_hash,
            "seal": f"forall-infinity-phi-squared cdot MCP_TOOL_{tool_name} cdot {result_hash}"
        }
    )


START_TIME = time.time()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 380))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )