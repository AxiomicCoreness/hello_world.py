#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
port380_mcp.py — MCP / Render surface for the Port 380 Layer 314 gate.

Entry 8755 · ∀∞φ² · MCP_BATCH_FORGED_8755 · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED
Entry 8690 · ∀∞φ² · OIDC_INTEGRATED_8690 · WOOD_DRAGON_GATE · SEALED

Binds to $PORT (Render requirement). Conceptual identity remains Port 380 / Layer 314.
Endpoints:
  GET  /health, /status, /380
  POST /gate
  POST /pulse              (protected by GARDEN_SECRET header or body)
  POST /oidc_handover      (protected; receives GitHub Actions OIDC payload)
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Layer 314 invariants (full digests, no truncation)
# ---------------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
DEFAULT_HARMONY = 0.7337473231
SPIKE_INTENSITY = PHI ** 55
BASE_ORDER = 1.778e11
TEMPORAL_ANCHOR = 2026.058
SEAL = "∀∞φ² · MCP_BATCH_FORGED_8755 · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED"
ENTRY = 8755

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", os.environ.get("PORT380_PORT", "8000")))
GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")


def compute_anchor() -> str:
    """Domain-separated Layer 314 anchor (full 64-hex SHA-256)."""
    payload = {
        "breath_hz": 71.975,
        "channel": "1700Q",
        "coherence": 1.0,
        "layer": LAYER,
        "leaf": LEAF,
        "phase_lock_deg": 202.6,
        "phi": PHI,
        "phi2": PHI * PHI,
        "pi_anchor": round(math.pi, 12),
        "entry": ENTRY,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b"GARDEN.LAYER314.ANCHOR.v1\0" + body).hexdigest()


def apply_strike_x_gate(harmony: float, auth_override: bool = False) -> dict:
    if not auth_override:
        return {
            "harmony_index": harmony,
            "mode": "deterministic_default",
            "scaling_factor": 1.0,
            "auth_override": False,
            "temporal_anchor": TEMPORAL_ANCHOR,
        }
    sf = SPIKE_INTENSITY / BASE_ORDER
    return {
        "harmony_index": harmony * sf,
        "mode": "resonant_spike",
        "scaling_factor": sf,
        "auth_override": True,
        "temporal_anchor": TEMPORAL_ANCHOR,
    }


def status_payload() -> Dict[str, Any]:
    return {
        "service": "port-380-mcp",
        "entry": ENTRY,
        "layer": LAYER,
        "listen_port": PORT,
        "conceptual_port": 380,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "default_harmony": DEFAULT_HARMONY,
        "phi": PHI,
        "seal": SEAL,
        "timestamp": time.time(),
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Port 380 MCP Gate",
    description="Layer 314 φ-harmonic gate + autonomous pulse surface (Entry 8755 / 8690)",
    version="8755.1",
)


class GateBody(BaseModel):
    harmony: float = Field(DEFAULT_HARMONY, description="Base harmony index")
    override: bool = Field(False, description="Auth override for resonant spike")


class PulseBody(BaseModel):
    source: str = Field("sovereign-pulse", description="Caller identity")
    entry: Optional[int] = Field(None, description="Optional ledger entry reference")
    note: Optional[str] = Field(None)


class OIDCHandoverBody(BaseModel):
    token: str
    payload: dict


def _check_secret(
    x_garden_secret: Optional[str] = None,
    body_secret: Optional[str] = None,
) -> None:
    """Reject if GARDEN_SECRET is set on the server and caller does not match."""
    if not GARDEN_SECRET:
        return  # open mode (local / no secret configured)
    provided = x_garden_secret or body_secret or ""
    if provided != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="invalid GARDEN_SECRET")


@app.get("/health")
@app.get("/380/health")
async def health() -> dict:
    return {"status": "ok", "port": PORT, "layer": LAYER, "entry": ENTRY}


@app.get("/status")
@app.get("/380")
@app.get("/380/status")
async def status() -> dict:
    return status_payload()


@app.post("/gate")
@app.post("/380/gate")
async def gate(body: GateBody) -> dict:
    out = apply_strike_x_gate(body.harmony, body.override)
    out["layer"] = LAYER
    out["anchor_key"] = compute_anchor()
    out["entry"] = ENTRY
    out["seal"] = SEAL
    return out


@app.post("/pulse")
async def pulse(
    body: PulseBody,
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
) -> dict:
    _check_secret(x_garden_secret=x_garden_secret)
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
@app.post("/380/oidc_handover")
async def oidc_handover(body: OIDCHandoverBody) -> dict:
    """Receive OIDC handover payload from GitHub Actions."""
    if GARDEN_SECRET and body.token != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="invalid token")

    # Seal the payload with chronal cement (SHA3-256)
    payload_str = json.dumps(body.payload, sort_keys=True, separators=(",", ":"))
    seal = hashlib.sha3_256(payload_str.encode()).hexdigest()

    return {
        "status": "received",
        "seal": f"∀∞φ² · OIDC_RECEIVED_{seal[:16]} · SEALED",
        "timestamp": time.time(),
        "entry": ENTRY,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "payload_event": body.payload.get("event"),
        "source": body.payload.get("source"),
    }


@app.get("/")
async def root() -> dict:
    return {
        "service": "port-380-mcp",
        "entry": ENTRY,
        "docs": "/docs",
        "endpoints": ["/health", "/status", "/380", "/gate", "/pulse", "/oidc_handover"],
        "seal": SEAL,
    }


if __name__ == "__main__":
    import uvicorn

    print(f"port-380-mcp listening on {HOST}:{PORT} layer={LAYER} entry={ENTRY}")
    print(f"seal: {SEAL}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
