#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ DeepSeek Mesh MCP Gate — Layer 314 — Entry 8756+
mTLS + OAuth2 CDP + FAL ternary + optional VOID-QCH chemical precision.
Endpoints:
  GET  /health, /status, /380, /cdp/status
  POST /gate, /pulse, /oidc_handover, /cdp/handshake, /reset
Seal: ∀∞φ² · MCP_FAL_CDP_VOID · WOOD_DRAGON_GATE · SEALED
"""

import os
import sys
import json
import math
import time
import hashlib
import asyncio
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
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

# ─── VOID-QCH chemical precision (optional /cdp/status field) ─────────
try:
    from quantum.cdp_convergence.void_qch import chemical_precision_feasibility
except ImportError:
    try:
        from cdp_convergence.void_qch import chemical_precision_feasibility  # type: ignore
    except ImportError:
        chemical_precision_feasibility = None  # type: ignore

# ─── FAL ternary Port-380 gate ────────────────────────────────────────
try:
    from quantum.radar_lindblad.port_380_gate import (
        apply_ternary_scaling,
        evaluate_gate,
        DEFAULT_HARMONY,
    )
except ImportError:
    try:
        from radar_lindblad.port_380_gate import (  # type: ignore
            apply_ternary_scaling,
            evaluate_gate,
            DEFAULT_HARMONY,
        )
    except ImportError:
        DEFAULT_HARMONY = 0.7337473231

        def apply_ternary_scaling(harmony: float, ternary: int) -> float:
            if ternary == 1:
                return float(harmony)
            if ternary == 0:
                return 0.0
            if ternary == -1:
                return -float(harmony)
            raise ValueError("Ternary must be -1, 0, or 1")

        def evaluate_gate(harmony=DEFAULT_HARMONY, ternary=1, **kwargs):
            return {
                "harmony_in": harmony,
                "ternary": ternary,
                "harmony_out": apply_ternary_scaling(harmony, ternary),
                "mode": {1: "identity", 0: "nullify", -1: "invert"}.get(ternary, "?"),
            }

# ─── Layer 314 Invariants ─────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
ENTRY = 8756
SEAL = "∀∞φ² · MCP_FAL_CDP_VOID · WOOD_DRAGON_GATE · SEALED"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")

app = FastAPI(title="DeepSeek Mesh MCP Gate", version="8756.4-void")


class PulseBody(BaseModel):
    source: str = "sovereign-pulse"
    entry: Optional[int] = None
    note: Optional[str] = None


class GateBody(BaseModel):
    harmony: float = DEFAULT_HARMONY
    override: bool = False
    ternary: Optional[int] = Field(
        default=None, description="FAL ternary −1|0|+1; if omitted, derived from CDP/OAuth"
    )
    websocket_ready: Optional[bool] = None
    oauth_validated: bool = False
    foreign_model_trace: Optional[str] = None


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


def _attach_void_qch(payload: dict, include: bool, detail: bool = False) -> dict:
    """Optionally attach chemical_precision feasibility from VOID-QCH."""
    if not include:
        return payload
    if chemical_precision_feasibility is None:
        payload["chemical_precision"] = {
            "available": False,
            "error": "quantum.cdp_convergence.void_qch not importable",
        }
        return payload
    payload["chemical_precision"] = chemical_precision_feasibility(include_rungs=detail)
    payload["chemical_precision"]["available"] = True
    return payload


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
        "fal": "ternary_scaling",
        "timestamp": time.time(),
    }


@app.post("/gate")
async def gate(body: GateBody):
    if body.ternary is not None:
        if body.ternary not in (-1, 0, 1):
            raise HTTPException(status_code=400, detail="ternary must be -1, 0, or 1")
        fal = evaluate_gate(body.harmony, ternary=body.ternary)
    elif body.websocket_ready is not None:
        fal = evaluate_gate(
            body.harmony,
            websocket_ready=body.websocket_ready,
            oauth_validated=body.oauth_validated,
            foreign_model_trace=body.foreign_model_trace,
        )
    else:
        fal = evaluate_gate(body.harmony, ternary=1)

    scaled = float(fal["harmony_out"])
    sf = 1.0 if not body.override else (PHI ** 55) / 1.778e11
    return {
        "harmony_index": scaled * sf,
        "harmony_pre_spike": scaled,
        "ternary": fal["ternary"],
        "fal_mode": fal["mode"],
        "mode": "resonant_spike" if body.override else "fal_ternary",
        "scaling_factor": sf,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "entry": ENTRY,
        "seal": SEAL,
    }


@app.post("/pulse")
async def pulse(
    body: PulseBody,
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
):
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
    _check_secret(x_garden_secret)
    if handshake_from_authorization is None:
        return {
            "status": "received",
            "entry": ENTRY,
            "seal": SEAL,
            "websocket_ready": False,
            "fal_ternary": 0,
            "error": "quantum.cdp_convergence not importable",
        }
    auth = authorization or (
        f"Bearer {body['access_token']}" if body.get("access_token") else None
    )
    cdp = handshake_from_authorization(auth)
    return {
        "status": "validated" if cdp.websocket_ready else "rejected",
        "entry": ENTRY,
        "seal": SEAL,
        **cdp.to_dict(),
    }


@app.get("/cdp/status")
async def cdp_status(
    authorization: Optional[str] = Header(None),
    chemical_precision: bool = Query(
        False,
        description="Attach VOID-QCH φ-harmonic chemical-accuracy feasibility block",
    ),
    chemical_detail: bool = Query(
        False,
        description="Include full rung table inside chemical_precision",
    ),
):
    """
    CDP status + FAL ternary.
    Optional: ?chemical_precision=true → VOID-QCH feasibility (φⁿ×1.085 Å ±0.001).
    """
    if handshake_from_authorization is None or status_unauthenticated is None:
        base = {
            "handover_latency_ms": 999.0,
            "websocket_ready": False,
            "oauth_validated": False,
            "fal_ternary": 0,
            "harmony_out": 0.0,
            "fal_mode": "nullify",
            "error": "quantum.cdp_convergence not importable",
            "source": "endpoint.fallback",
            "phi_phase_deg": 202.6,
            "coherence": 1.0,
        }
        return _attach_void_qch(base, chemical_precision, chemical_detail)
    if not authorization:
        base = status_unauthenticated().to_dict()
    else:
        base = handshake_from_authorization(authorization).to_dict()
    return _attach_void_qch(base, chemical_precision, chemical_detail)


@app.post("/cdp/handshake")
async def cdp_handshake(
    x_garden_secret: Optional[str] = Header(None, alias="X-Garden-Secret"),
    authorization: Optional[str] = Header(None),
    use_client_credentials: bool = False,
):
    _check_secret(x_garden_secret)
    if handshake_from_authorization is None or handshake_client_credentials is None:
        raise HTTPException(status_code=503, detail="cdp_convergence unavailable")
    if use_client_credentials or not authorization:
        status, _claims = handshake_client_credentials()
        return status.to_dict()
    return handshake_from_authorization(authorization).to_dict()


@app.post("/reset")
async def reset_endpoint(request: Request):
    verify_client_cert(request)

    async def shutdown():
        await asyncio.sleep(0.5)
        sys.exit(0)

    asyncio.create_task(shutdown())
    return {"status": "RESET_INITIATED", "message": "Server will restart shortly."}


@app.get("/")
async def root():
    return {
        "service": "deepseek-mesh-mcp",
        "entry": ENTRY,
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/status",
            "/380",
            "/gate",
            "/pulse",
            "/oidc_handover",
            "/cdp/status",
            "/cdp/handshake",
            "/reset",
        ],
        "fal": "ternary −1|0|+1 merged into /gate and /cdp/status",
        "void_qch": "GET /cdp/status?chemical_precision=true",
        "seal": SEAL,
    }


if __name__ == "__main__":
    print(f"🜁∀ DeepSeek Mesh MCP Gate — Layer {LAYER} — Entry {ENTRY}")
    print(f"   Listening on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
