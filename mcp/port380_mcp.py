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
import sys
import hashlib
import hmac
import ipaddress
from contextlib import asynccontextmanager
import json
import time
from datetime import datetime, timezone
from pathlib import Path
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
STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
X_FRAME_OPTIONS = "X-Frame-Options"
CONTENT_SECURITY_POLICY = "Content-Security-Policy"
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
# GARDEN_SECRET FAIL-FAST
# ============================================================================
def garden_secret_missing() -> bool:
    """True when GARDEN_SECRET is unset, empty or whitespace only."""
    return not os.environ.get("GARDEN_SECRET", "").strip()


def require_garden_secret() -> None:
    """Refuse to serve without GARDEN_SECRET: print FATAL to stderr and exit 1."""
    if garden_secret_missing():
        print(
            "FATAL: GARDEN_SECRET is unset or empty; refusing to start "
            "(/pulse and /mcp/tool would be unauthenticated).",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)


@asynccontextmanager
async def _lifespan(_app):
    # Also covers `uvicorn port380_mcp:app`, which skips __main__.
    if garden_secret_missing():
        print("FATAL: GARDEN_SECRET is unset or empty; refusing to start.", file=sys.stderr, flush=True)
        raise RuntimeError("GARDEN_SECRET is unset or empty")
    yield


# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description=f"{APP_NAME} — Port 380 Gate Re-export (Layer {LAYER})",
    lifespan=_lifespan,
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

# Appended channel constants. Do not replace the service block above.
AUTOMATON_REL = "garden_surgery/sovereign_automaton_10.06.py"
AUTOMATON_CALLABLE = "sovereign_automaton_10_06"
MCP_TOOL_PATH = "/mcp/tool"
CHAT_TOOL = "chat"
# Live entrypoint uses PORT (default 380); host defaults to 127.0.0.1,
# and containers override it with BIND_HOST=0.0.0.0.
# The slot's 127.0.0.1:8024 is a proposed bind, not this file's bind.
SLOT_BIND_PROPOSED = "127.0.0.1:8024"


def verify_secret(x_garden_secret: Optional[str]) -> bool:
    if not GARDEN_SECRET.strip():
        raise HTTPException(status_code=503, detail="GARDEN_SECRET not configured")
    # Constant-time comparison on bytes.
    if not hmac.compare_digest((x_garden_secret or "").encode("utf-8"), GARDEN_SECRET.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid GARDEN_SECRET")
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_sha3(body: Any) -> str:
    """Full-length SHA3-256 over canonical JSON. No truncation."""
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


async def _read_json(request: Request, require_object: bool = False) -> Any:
    """Parse the request body as JSON; malformed input is a 400, not a 500."""
    try:
        body = await request.json()
    except ValueError:  # json.JSONDecodeError and UnicodeDecodeError are ValueErrors
        raise HTTPException(status_code=400, detail="request body must be valid JSON")
    if require_object and not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    return body


# ============================================================================
# ROUTES
# ============================================================================
@app.get("/health")
@app.get("/healthz")
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
    body = await _read_json(request)
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
    body = await _read_json(request, require_object=True)
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



def run_automaton(text: str) -> str:
    """Call the named surface. It takes no text. Input is not consumed."""
    import importlib.util
    path = Path(AUTOMATON_REL)
    if not path.is_file():
        raise FileNotFoundError(AUTOMATON_REL)
    spec = importlib.util.spec_from_file_location("sovereign_automaton_10_06", path)
    if spec is None or spec.loader is None:
        raise ImportError(AUTOMATON_REL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, AUTOMATON_CALLABLE)
    payload = fn()
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("status") or payload)
    return str(payload)


@app.post("/mcp/tool")
async def mcp_tool(
    request: Request,
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    body = await _read_json(request, require_object=True)
    tool_name = body.get("tool", "unknown")
    arguments = body.get("arguments", {})
    reply = None
    dispatch_error = None
    if tool_name == CHAT_TOOL:
        raw_text = body.get("text", "")
        if not isinstance(raw_text, str) or not raw_text:
            dispatch_error = "missing text"
        else:
            try:
                reply = run_automaton(raw_text)
            except Exception as exc:
                dispatch_error = f"{type(exc).__name__}: {exc}"
    result = {
        "tool": tool_name,
        "arguments": arguments,
        "executed": dispatch_error is None,
        "timestamp": _now(),
        "layer": LAYER,
        "gate_identity": GATE_IDENTITY,
        "text": reply,
        "ok": dispatch_error is None,
        "error": dispatch_error,
        "callable": AUTOMATON_CALLABLE,
        "text_consumed": False,
    }
    result_hash = _full_sha3(result)
    return JSONResponse(
        content={
            "ok": dispatch_error is None,
            "text": reply,
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
HEALTHZ_PATH = "/healthz"


def check_config() -> Dict[str, Any]:
    """Validate the runtime env without starting the server. Never includes the secret."""
    errors = []
    host = (os.environ.get("BIND_HOST") or os.environ.get("MCP_BIND_HOST", "127.0.0.1")).strip()
    if host != "localhost":
        try:
            ipaddress.ip_address(host)
        except ValueError:
            errors.append(f"bind host {host!r} is not an IP address or 'localhost'")
    raw_port = os.environ.get("PORT") or os.environ.get("MCP_PORT") or "380"
    port: Optional[int]
    try:
        port = int(raw_port)
        if not 1 <= port <= 65535:
            errors.append(f"port {port} is outside 1-65535")
    except ValueError:
        port = None
        errors.append(f"PORT/MCP_PORT {raw_port!r} is not an integer")
    if garden_secret_missing():
        errors.append("GARDEN_SECRET is unset or empty")
    url_host = f"[{host}]" if ":" in host else host
    return {
        "ok": not errors,
        "host": host,
        "bind_host": host,
        "bind": f"{url_host}:{port}",
        "port": port,
        "url": f"http://{url_host}:{port}{HEALTHZ_PATH}",
        "surface": [HEALTHZ_PATH],
        "legacy_out_of_surface": ["/health", "/pulse"],
        "namespace": os.environ.get("MCP_NAMESPACE", "default"),
        "legacy_404_hard": os.environ.get("MCP_LEGACY_404_HARD", "0") == "1",
        "garden_secret": "missing" if garden_secret_missing() else "set",
        "errors": errors,
    }


if __name__ == "__main__":
    if "--check-config" in sys.argv[1:]:
        plan = check_config()
        print(json.dumps(plan, sort_keys=True))
        for err in plan["errors"]:
            print(f"check-config: {err}", file=sys.stderr)
        raise SystemExit(0 if plan["ok"] else 1)
    require_garden_secret()
    plan = check_config()
    if not plan["ok"]:
        print("FATAL: " + "; ".join(plan["errors"]), file=sys.stderr, flush=True)
        raise SystemExit(1)
    uvicorn.run(
        app,
        host=plan["host"],
        port=plan["port"],
        log_level="info",
    )
