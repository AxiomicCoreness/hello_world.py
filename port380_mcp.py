#!/usr/bin/env python3
"""
Port 380 MCP Gateway — local-first sovereign pulse (no Render).

export GARDEN_SECRET="your_secret_here"
export MCP_CONNECTOR_URL="http://localhost:380"
export MCP_URL="http://localhost:380"
uvicorn port380_mcp:app --port 380

Seal: ∀∞φ² · PORT380_MCP_CONNECTOR · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import hmac
import os
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from quantum.mcp_connector import MCPConnector, health_check, introspect_token
from quantum.provider_httpx import chat as provider_chat
from quantum.provider_httpx import provider_status

GARDEN_SECRET = os.getenv("GARDEN_SECRET", "")
MCP_URL = os.getenv("MCP_URL", "http://localhost:380")
MCP_CONNECTOR_URL = os.getenv("MCP_CONNECTOR_URL", "http://localhost:380")

connector = MCPConnector(base_url=MCP_CONNECTOR_URL)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


app = FastAPI(title="Port 380 MCP Gateway", version="1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:380,http://127.0.0.1:380").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Garden-Secret"],
)
app.add_middleware(SecurityHeadersMiddleware)


def verify_garden_secret(x_garden_secret: str = Header(..., alias="X-Garden-Secret")) -> bool:
    if not GARDEN_SECRET:
        raise HTTPException(status_code=500, detail="GARDEN_SECRET not configured")
    if not hmac.compare_digest(
        x_garden_secret.encode("utf-8"), GARDEN_SECRET.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid Garden Secret")
    return True


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "connector": health_check(),
        "mcp_url": MCP_URL,
        "mcp_connector_url": MCP_CONNECTOR_URL,
        "providers": provider_status(),
        "seal": "∀∞φ² · PORT380_HEALTH · SEALED",
    }


@app.post("/pulse")
async def pulse(
    payload: Optional[Dict[str, Any]] = None,
    _: bool = Depends(verify_garden_secret),
) -> Dict[str, Any]:
    body = payload or {}
    return {
        "status": "pulse_received",
        "message": "Pulse received",
        "source": body.get("source", "unknown"),
        "entry": body.get("entry", 0),
        "note": body.get("note", "scheduled-pulse"),
        "seal": "∀∞φ² · PULSE_ACCEPTED",
    }


@app.post("/llm/chat")
async def llm_chat(
    body: Dict[str, Any],
    _: bool = Depends(verify_garden_secret),
) -> Dict[str, Any]:
    provider = str(body.get("provider", "deepseek"))
    messages = body.get("messages") or [{"role": "user", "content": str(body.get("prompt", ""))}]
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages must be a list")
    return provider_chat(provider, messages, body.get("model"))


@app.post("/oauth/token")
async def oauth_token(body: Dict[str, Any]) -> Dict[str, Any]:
    client_id = str(body.get("client_id", ""))
    client_secret = str(body.get("client_secret", ""))
    scope = str(body.get("scope", ""))
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="client_id and client_secret required")
    ok = connector.authenticate(client_id, client_secret, scope)
    if not ok:
        raise HTTPException(status_code=401, detail="connector authentication failed")
    return {"authenticated": True, "token_present": bool(connector.token)}


@app.post("/oauth/introspect")
async def oauth_introspect(
    body: Dict[str, Any],
    _: bool = Depends(verify_garden_secret),
) -> Dict[str, Any]:
    token = str(body.get("token") or connector.token or "")
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    return introspect_token(token)


@app.post("/oauth/sign")
async def oauth_sign(
    payload: Dict[str, Any],
    _: bool = Depends(verify_garden_secret),
) -> Dict[str, Any]:
    signed = connector.sign(payload)
    if signed is None:
        raise HTTPException(status_code=401, detail="connector not authenticated")
    return signed


@app.get("/qiskit/health")
async def qiskit_health() -> Dict[str, Any]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "port380_mcp:app",
        host=os.getenv("PORT380_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT380_PORT", "380")),
        reload=False,
    )
