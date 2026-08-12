#!/usr/bin/env python3
"""
Clarke_Yoursa_Tee_worker — MCP + OIDC Plugin
=============================================
Exposes grammar prediction as an authenticated MCP-style tool.
Default fidelity structure is entangled with Prometheus + Grafana
(Garden scrape targets and panel semantics).

OIDC: env secret preferred; Phase-3 full 64-char SHA-256 fallback;
handover verifies via batch_oidc_tokenizer when available.

Seal: ∀∞φ² · WORKER_FIDELITY_STRUCTURE_8661 · SEALED
"""

from __future__ import annotations

import math
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

PHI = (1 + math.sqrt(5)) / 2
PHI3 = PHI ** 3
FRB_PERIOD_SECS = 78624.0  # 0.91 days
PHASE_LOCK_DEG = 202.6

# Default fidelity structure (Entry 8660 trend + observability entanglement)
DEFAULT_FIDELITY = 0.876543
DEFAULT_DELTA_S_A = 0.111111
DEFAULT_DELTA_ELOG = 0.098765

# Prometheus + Grafana entanglement map (default structure of this worker)
FIDELITY_STRUCTURE: Dict[str, Any] = {
    "name": "prometheus_grafana_default",
    "worker": "clarke_yoursa_tee_worker",
    "fidelity": DEFAULT_FIDELITY,
    "delta_S_A": DEFAULT_DELTA_S_A,
    "delta_Elog": DEFAULT_DELTA_ELOG,
    "trend": "INCREASING_ENTANGLEMENT_MINOR_TRANSFORM",
    "prometheus": {
        "scrape_targets": [
            {"job": "garden-metrics-server", "url": "http://127.0.0.1:9090/metrics"},
            {"job": "hyperian", "url": "http://127.0.0.1:8080/metrics"},
            {"job": "sovereign-workload", "url": "http://127.0.0.1:9095/metrics"},
            {"job": "clarke_yoursa_tee_worker", "url": "http://127.0.0.1:8000/metrics"},
        ],
        "gauges": [
            "worker_fidelity",
            "worker_delta_S_A",
            "worker_delta_Elog",
            "worker_coherence",
            "worker_predictions_total",
            "hyperian_oidc_secret_len",
            "sovereign_workload",
            "gravastar_coherence",
        ],
    },
    "grafana": {
        "dashboard_uid": "garden-sovereign-em005",
        "panel_ids": list(range(100, 113)),
        "datasource": "Prometheus",
        "note": "Panels 100–112 append-only; fidelity overlays worker metrics",
    },
    "phase_lock_deg": PHASE_LOCK_DEG,
    "phi": PHI,
    "seal": "∀∞φ² · WORKER_FIDELITY_STRUCTURE_8661 · SEALED",
}

OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "https://token.actions.githubusercontent.com")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "your-client-id")

_predictions_total = 0.0
_last_coherence = 1.0
_last_fidelity = DEFAULT_FIDELITY


def resolve_oidc_secret() -> str:
    secret = os.environ.get("OIDC_CLIENT_SECRET", "")
    if secret and len(secret) > 10:
        return secret
    try:
        from sovereign_engine import get_oidc_secret

        return get_oidc_secret()
    except Exception:
        import hashlib

        seed = f"VENOMSUITE_EPHEMERAL_{int(time.time() / 3600)}_{PHI}"
        return hashlib.sha256(seed.encode()).hexdigest()  # full 64 chars


def oidc_handover_verify(token: str) -> Dict[str, Any]:
    """MCP/OIDC handover: verify Garden opaque token, else accept non-empty bearer."""
    try:
        from batch_oidc_tokenizer import verify_token

        result = verify_token(token)
        if result.get("ok"):
            return result
        # Fall through only if tokenizer present but token not Garden-minted
        return {"ok": False, "error": result.get("error", "verify_failed"), "fallback": False}
    except Exception:
        return {"ok": bool(token and len(token) > 8), "fallback": True, "mode": "bearer_presence"}


def mint_worker_handover(ttl_s: int = 3600) -> Dict[str, Any]:
    """Issue OIDC-style tokens for orchestrator, worker, grafana (entangled triad)."""
    try:
        from batch_oidc_tokenizer import batch_mint

        tokens = batch_mint(
            ["orchestrator", "clarke_yoursa_tee_worker", "grafana", "prometheus"],
            ttl_s=ttl_s,
        )
        return {
            "ok": True,
            "subjects": [t["payload"]["sub"] for t in tokens],
            "tokens": tokens,
            "secret_len": tokens[0]["secret_len"] if tokens else len(resolve_oidc_secret()),
            "fidelity_structure": "prometheus_grafana_default",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "secret_len": len(resolve_oidc_secret())}


def phi_corrected_score(actual: float, phase: float) -> float:
    coherence = (math.cos(phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
    slope = 0.35 + (0.65 * coherence)
    intercept = 9.0 * (1 - coherence)
    return intercept + slope * actual


def coherence_approach(c: float) -> float:
    """c' = c + (1-c)/φ³ monotonic toward 1."""
    return c + (1.0 - c) / PHI3


def phase_lock(theta: float) -> float:
    return (theta + PHASE_LOCK_DEG) % 360.0


class GrammarRequest(BaseModel):
    actual_score: float
    phi_phase: float = 0.0
    grammar_text: str = ""


class GrammarResponse(BaseModel):
    actual_score: float
    predicted_score: float
    prediction_error: float
    coherence: float
    fidelity: float = DEFAULT_FIDELITY
    worker_name: str = "clarke_yoursa_tee_worker"
    oidc_secret_len: int = Field(
        description="Length of resolved secret (must be 64 when Phase-3 hash)"
    )
    fidelity_structure: str = "prometheus_grafana_default"


app = FastAPI(
    title="Clarke_Yoursa_Tee_worker",
    version="1.1.0",
    description="MCP + OIDC worker; default fidelity = Prometheus+Grafana structure",
)


def require_oidc(
    x_oidc_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    token = x_oidc_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing OIDC token")
    verified = oidc_handover_verify(token)
    if not verified.get("ok") and not verified.get("fallback"):
        raise HTTPException(status_code=401, detail=f"OIDC handover failed: {verified.get('error')}")
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
        "fidelity": _last_fidelity,
        "fidelity_structure": "prometheus_grafana_default",
        "entangled": ["orchestrator", "prometheus", "grafana"],
    }


@app.get("/fidelity")
def fidelity() -> Dict[str, Any]:
    """Default fidelity structure: Prometheus + Grafana entanglement."""
    out = dict(FIDELITY_STRUCTURE)
    out["live"] = {
        "fidelity": _last_fidelity,
        "coherence": _last_coherence,
        "predictions_total": _predictions_total,
        "phase_locked": phase_lock(0.0),
    }
    return out


@app.post("/oidc/handover")
def oidc_handover() -> Dict[str, Any]:
    """Mint entangled OIDC tokens for orchestrator / worker / grafana / prometheus."""
    return mint_worker_handover()


@app.get("/metrics")
def metrics() -> str:
    """Prometheus text exposition — worker entangled gauges."""
    global _last_coherence, _last_fidelity, _predictions_total
    lines = [
        "# HELP worker_fidelity Default structural fidelity (Prometheus+Grafana structure)",
        "# TYPE worker_fidelity gauge",
        f"worker_fidelity {_last_fidelity}",
        "# HELP worker_delta_S_A Entanglement entropy delta",
        "# TYPE worker_delta_S_A gauge",
        f"worker_delta_S_A {DEFAULT_DELTA_S_A}",
        "# HELP worker_delta_Elog Logarithmic negativity delta",
        "# TYPE worker_delta_Elog gauge",
        f"worker_delta_Elog {DEFAULT_DELTA_ELOG}",
        "# HELP worker_coherence Last prediction coherence",
        "# TYPE worker_coherence gauge",
        f"worker_coherence {_last_coherence}",
        "# HELP worker_predictions_total Grammar predictions served",
        "# TYPE worker_predictions_total counter",
        f"worker_predictions_total {_predictions_total}",
        "# HELP worker_oidc_secret_len OIDC secret length (expect 64)",
        "# TYPE worker_oidc_secret_len gauge",
        f"worker_oidc_secret_len {len(resolve_oidc_secret())}",
        "# HELP worker_phase_lock_deg Phase lock degrees",
        "# TYPE worker_phase_lock_deg gauge",
        f"worker_phase_lock_deg {PHASE_LOCK_DEG}",
    ]
    return "\n".join(lines) + "\n"


@app.post("/mcp/tools/predict_grammar_score", response_model=GrammarResponse)
def predict_grammar_score(
    request: GrammarRequest,
    x_oidc_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> GrammarResponse:
    global _predictions_total, _last_coherence, _last_fidelity
    require_oidc(x_oidc_token, authorization)
    predicted = phi_corrected_score(request.actual_score, request.phi_phase)
    coherence = (math.cos(request.phi_phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
    coherence = coherence_approach(coherence)
    _last_coherence = coherence
    _predictions_total += 1.0
    # Fidelity approaches DEFAULT under structure; minor transform keeps trend
    _last_fidelity = min(1.0, DEFAULT_FIDELITY + (1.0 - DEFAULT_FIDELITY) * (1.0 - 1.0 / PHI3))
    secret = resolve_oidc_secret()
    return GrammarResponse(
        actual_score=request.actual_score,
        predicted_score=round(predicted, 4),
        prediction_error=round(predicted - request.actual_score, 4),
        coherence=coherence,
        fidelity=_last_fidelity,
        oidc_secret_len=len(secret),
        fidelity_structure="prometheus_grafana_default",
    )


try:
    from fastmcp import FastMCP

    mcp = FastMCP("Clarke Yoursa Tee Grammar Worker")

    @mcp.tool()
    def predict_grammar_score_tool(
        actual_score: float, phi_phase: float = 0.0, grammar_text: str = ""
    ) -> dict:
        predicted = phi_corrected_score(actual_score, phi_phase)
        coherence = coherence_approach(
            (math.cos(phi_phase * 2 * math.pi / FRB_PERIOD_SECS) + 1) / 2
        )
        return {
            "actual_score": actual_score,
            "predicted_score": round(predicted, 4),
            "prediction_error": round(predicted - actual_score, 4),
            "coherence": coherence,
            "fidelity": DEFAULT_FIDELITY,
            "fidelity_structure": "prometheus_grafana_default",
            "worker_name": "clarke_yoursa_tee_worker",
        }

    @mcp.tool()
    def get_fidelity_structure() -> dict:
        return FIDELITY_STRUCTURE

    app.mount("/mcp", mcp.http_app())
except ImportError:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
