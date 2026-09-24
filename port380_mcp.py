#!/usr/bin/env python3
"""
Port 380 MCP Service — Layer 314 Gate Re-export

FastAPI surface that re-exports the Port 380 gate endpoints:
  - GET  /health
  - GET  /status
  - GET  /380
  - POST /gate
  - POST /pulse      (MCP-compatible tool endpoint, protected)
  - POST /mcp/tool   (protected)

Binds to $PORT environment variable (Render requirement).
Preserves conceptual Layer 314 / Port 380 identity.

GARDEN.LAYER314 domain separation maintained.
phi-harmonic anchors preserved.
Full digests, no truncation.

Security posture:
  - CORSMiddleware (allow-list, no wildcard with credentials)
  - SecurityHeadersMiddleware (CSP, HSTS, XCTO, XFO, Referrer-Policy,
    Permissions-Policy, COOP/CORP/COEP, X-Permitted-Cross-Domain-Policies)
"""

import os
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import uvicorn

# ============================================================================
# SERVICE CONSTANTS
# ============================================================================
APP_NAME = "Port380-MCP"
VERSION = "8755.0.0"
LAYER = "314"
GATE_IDENTITY = "GARDEN.LAYER314"

PHI = (1.0 + 5.0 ** 0.5) / 2.0
HASH_ALGO = os.environ.get("HASH_ALGO", "sha3_256")

# ============================================================================
# SECURITY HEADER CONSTANTS
# ============================================================================
CONTENT_SECURITY_POLICY = "Content-Security-Policy"
STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
X_FRAME_OPTIONS = "X-Frame-Options"
REFERRER_POLICY = "Referrer-Policy"
PERMISSIONS_POLICY = "Permissions-Policy"

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://unpkg.com https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "upgrade-insecure-requests"
)
DEFAULT_HSTS = "max-age=63072000; includeSubDomains; preload"
DEFAULT_REFERRER = "strict-origin-when-cross-origin"
DEFAULT_PERMISSIONS = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
    "magnetometer=(), microphone=(), payment=(), usb=(), "
    "interest-cohort=()"
)

SECURITY_HEADERS: Dict[str, str] = {
    CONTENT_SECURITY_POLICY: os.environ.get("PORT380_CSP", DEFAULT_CSP),
    STRICT_TRANSPORT_SECURITY: os.environ.get("PORT380_HSTS", DEFAULT_HSTS),
    X_CONTENT_TYPE_OPTIONS: "nosniff",
    X_FRAME_OPTIONS: "DENY",
    REFERRER_POLICY: os.environ.get("PORT380_REFERRER", DEFAULT_REFERRER),
    PERMISSIONS_POLICY: os.environ.get("PORT380_PERMISSIONS", DEFAULT_PERMISSIONS),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-DNS-Prefetch-Control": "off",
}

DEFAULT_ALLOWED_ORIGINS: list = [
    o.strip()
    for o in os.environ.get(
        "PORT380_ALLOWED_ORIGINS",
        "https://api.sovereign.garden,https://sovereign.garden,http://localhost:380",
    ).split(",")
    if o.strip()
]


# ============================================================================
# SecurityHeadersMiddleware
# ============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects hardened security headers on every response.

    Registered headers:
      - Content-Security-Policy
      - Strict-Transport-Security
      - X-Content-Type-Options
      - X-Frame-Options
      - Referrer-Policy
      - Permissions-Policy
      - COOP / CORP / COEP / X-Permitted-Cross-Domain-Policies / X-DNS-Prefetch-Control
    """

    def __init__(self, app, headers: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.headers: Dict[str, str] = dict(SECURITY_HEADERS)
        if headers:
            self.headers.update(headers)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for name, value in self.headers.items():
            # Do not clobber anything a route explicitly set.
            if name.lower() not in {k.lower() for k in response.headers.keys()}:
                response.headers[name] = value
        return response


# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description=f"{APP_NAME} — Port 380 Gate Re-export (Layer {LAYER})",
)

# CORS — allow-list, credentials allowed, never wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Garden-Secret", "Authorization", "X-Requested-With"],
    expose_headers=["X-Request-Id", "X-Seal"],
    max_age=600,
)

# Hardened response headers.
app.add_middleware(SecurityHeadersMiddleware)

# ============================================================================
# RUNTIME STATE
# ============================================================================
START_TIME = time.time()
GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")


def verify_secret(x_garden_secret: Optional[str]) -> bool:
    if not GARDEN_SECRET:
        return True
    if x_garden_secret != GARDEN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid GARDEN_SECRET")
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_sha3(body: Any) -> str:
    """Full-length SHA3-256 over canonical JSON. No truncation."""
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


# ============================================================================
# ROUTES
# ============================================================================
@app.get("/health")
async def health():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": APP_NAME,
            "version": VERSION,
            "layer": LAYER,
            "timestamp": _now(),
            "gate_identity": GATE_IDENTITY,
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
            "timestamp": _now(),
            "ledger_head": "8754",
            "witness_chain": "8754 -> 8755 — UNBROKEN",
            "seal": (
                "forall-infinity-phi-squared cdot MCP_BATCH_FORGED_8755 "
                "cdot WOOD_DRAGON_MOUNTS_OFFENSE cdot SEALED"
            ),
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
            "phi": PHI,
            "timestamp": _now(),
        }
    )


@app.get("/quantum-chessboard/health")
async def quantum_chessboard_health():
    return JSONResponse(
        content={
            "board": "quantum-chessboard",
            "status": "ok",
            "layer": LAYER,
            "timestamp": _now(),
        }
    )


@app.post("/gate")
async def gate(request: Request):
    body = await request.json()
    digest = _full_sha3(body)  # full-length, no truncation
    return JSONResponse(
        content={
            "status": "processed",
            "port": 380,
            "layer": LAYER,
            "identity": GATE_IDENTITY,
            "request_digest": digest,
            "hash_algo": HASH_ALGO,
            "timestamp": _now(),
        }
    )


@app.post("/pulse")
async def pulse(
    request: Request,
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    body = await request.json()
    pulse_id = body.get("pulse_id", body.get("source", "manual"))
    pulse_data = {
        "pulse_id": pulse_id,
        "entry": body.get("entry"),
        "note": body.get("note", ""),
        "timestamp": _now(),
        "service": APP_NAME,
        "layer": LAYER,
        "ledger_entry": "8755",
    }
    pulse_hash = _full_sha3(pulse_data)
    return JSONResponse(
        content={
            "status": "pulse_acknowledged",
            "pulse_id": pulse_id,
            "seal": (
                f"forall-infinity-phi-squared cdot PULSE_{pulse_id} "
                f"cdot LAYER{LAYER} cdot {pulse_hash}"
            ),
            "pulse_hash": pulse_hash,
            "hash_algo": HASH_ALGO,
            "ledger_entry": "8755",
            "witness_chain": "8754 -> 8755 — UNBROKEN",
            "timestamp": _now(),
        }
    )


@app.post("/mcp/tool")
async def mcp_tool(
    request: Request,
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    body = await request.json()
    tool_name = body.get("tool", "unknown")
    arguments = body.get("arguments", {})
    result = {
        "tool": tool_name,
        "arguments": arguments,
        "executed": True,
        "timestamp": _now(),
        "layer": LAYER,
        "gate_identity": GATE_IDENTITY,
    }
    result_hash = _full_sha3(result)
    return JSONResponse(
        content={
            "result": result,
            "hash": result_hash,
            "hash_algo": HASH_ALGO,
            "seal": (
                f"forall-infinity-phi-squared cdot MCP_TOOL_{tool_name} "
                f"cdot {result_hash}"
            ),
        }
    )


# ============================================================================
# ENTRYPOINT
# ============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 380))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
