#!/usr/bin/env python3
"""
Clarke_Yoursa_Tee_worker — MCP + OIDC Plugin
=============================================
Exposes the worker's grammar prediction as an authenticated MCP-style tool.
Orchestrator (bigger model) and worker both authenticate via OIDC tokens.

OIDC secrets: prefer env; Phase-3 fallback uses full 64-char SHA-256
(from sovereign_engine.get_oidc_secret) — never truncated.

Seal: ∀∞φ² · WORKER_8623 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# ---- φ-Harmonic Constants ----
PHI = (1 + math.sqrt(5)) / 2
FRB_PERIOD_SECS = 78624.0  # 0.91 days

# ---- OIDC Configuration (secrets via env / full-hash fallback) ----
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "https://token.actions.githubusercontent.com")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "your-client-id")


def resolve_oidc_secret() -> str:
    """Env primary; else full SHA-256 ephemeral from sovereign_engine (no truncation)."""
    secret = os.environ.get("OIDC_CLIENT_SECRET", "")
    if secret and len(secret) > 10:
        return secret
    try:
        from sovereign_engine import get_oidc_secret

        return get_oidc_secret()
    except Exception:
        import hashlib
        import time

        seed = f"VENOMSUITE_EPHEMERAL_{int(time.time() / 3600)}_{PHI}"
        return hashlib.sha256(seed.encode()).hexdigest()  # full 64 chars


def phi_corrected_score(actual: float, phase: float) -> float:
    """Narrow φ-corrected prediction (Wood Dragon fast path)."""
    coherence = (math.cos(phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
    slope = 0.35 + (0.65 * coherence)
    intercept = 9.0 * (1 - coherence)
    return intercept + slope * actual


class GrammarRequest(BaseModel):
    actual_score: float
    phi_phase: float = 0.0
    grammar_text: str = ""


class GrammarResponse(BaseModel):
    actual_score: float
    predicted_score: float
    prediction_error: float
    coherence: float
    worker_name: str = "clarke_yoursa_tee_worker"
    oidc_secret_len: int = Field(
        description="Length of resolved secret (must be 64 when Phase-3 hash)"
    )


app = FastAPI(title="Clarke_Yoursa_Tee_worker", version="1.0.0")


def require_oidc(
    x_oidc_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    token = x_oidc_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing OIDC token")
    return token


@app.get("/health")
def health() -> Dict[str, Any]:
    secret = resolve_oidc_secret()
    return {
        "status": "ok",
        "worker": "clarke_yoursa_tee_worker",
        "oidc_secret_len": len(secret),
        "frb_period_secs": FRB_PERIOD_SECS,
        "phi": PHI,
    }


@app.post("/mcp/tools/predict_grammar_score", response_model=GrammarResponse)
def predict_grammar_score(
    request: GrammarRequest,
    x_oidc_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> GrammarResponse:
    """
    Narrow grammar score prediction (worker). Requires OIDC token in header.
    Compatible with orchestrator MCP-style POST.
    """
    require_oidc(x_oidc_token, authorization)
    predicted = phi_corrected_score(request.actual_score, request.phi_phase)
    coherence = (math.cos(request.phi_phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
    secret = resolve_oidc_secret()
    return GrammarResponse(
        actual_score=request.actual_score,
        predicted_score=round(predicted, 4),
        prediction_error=round(predicted - request.actual_score, 4),
        coherence=coherence,
        oidc_secret_len=len(secret),
    )


# Optional FastMCP mount when library is installed
try:
    from fastmcp import FastMCP

    mcp = FastMCP("Clarke Yoursa Tee Grammar Worker")

    @mcp.tool()
    def predict_grammar_score_tool(
        actual_score: float, phi_phase: float = 0.0, grammar_text: str = ""
    ) -> dict:
        predicted = phi_corrected_score(actual_score, phi_phase)
        coherence = (math.cos(phi_phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
        return {
            "actual_score": actual_score,
            "predicted_score": round(predicted, 4),
            "prediction_error": round(predicted - actual_score, 4),
            "coherence": coherence,
            "worker_name": "clarke_yoursa_tee_worker",
        }

    app.mount("/mcp", mcp.http_app())
except ImportError:
    pass  # FastAPI routes remain available without fastmcp


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
