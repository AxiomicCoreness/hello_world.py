#!/usr/bin/env python3
"""
Clarke_Yoursa_Tee_worker — MCP + OIDC Plugin
=============================================
Exposes grammar prediction as an authenticated MCP-style tool.
Default fidelity structure is entangled with Prometheus + Grafana
(Garden scrape targets and panel semantics).

OIDC: env secret preferred; Phase-3 full 64-char SHA-256 fallback;
handover verifies via batch_oidc_tokenizer when available.

APPEND (8665): Pauli φ-Hamiltonian wiring + capabilities surface.
  Policy: do not truncate digests; do not subtract existing wiring code.

Seal: ∀∞φ² · MCP_OIDC_PAULI_CAPABILITIES_8665 · SEALED
"""

from __future__ import annotations

import math
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

PHI = (1 + math.sqrt(5)) / 2
PHI2 = PHI * PHI
PHI3 = PHI ** 3
PHI_NEG2 = PHI ** (-2)
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
            # APPEND 8665 — Pauli (no removal of prior gauges)
            "worker_pauli_trace",
            "worker_pauli_verified",
            "worker_systems_go",
        ],
    },
    "grafana": {
        "dashboard_uid": "garden-sovereign-em005",
        "panel_ids": list(range(100, 113)),
        "datasource": "Prometheus",
        "note": "Panels 100–112 append-only; fidelity overlays worker metrics",
        "append_panel_hint": {
            "id": 113,
            "title": "Pauli φ-Hamiltonian Trace",
            "targets": ["worker_pauli_trace", "worker_pauli_verified", "worker_systems_go"],
        },
    },
    "phase_lock_deg": PHASE_LOCK_DEG,
    "phi": PHI,
    "seal": "∀∞φ² · MCP_OIDC_PAULI_CAPABILITIES_8665 · SEALED",
}

# Available capabilities (Prom + Grafana + MCP + OIDC + Pauli) — append catalog
AVAILABLE_CAPABILITIES: Dict[str, Any] = {
    "mcp": [
        "predict_grammar_score_tool",
        "get_fidelity_structure",
        "get_pauli_status",
        "get_systems_go",
        "list_capabilities",
    ],
    "http": [
        "GET /health",
        "GET /fidelity",
        "GET /capabilities",
        "GET /pauli",
        "GET /systems_go",
        "GET /metrics",
        "POST /oidc/handover",
        "POST /mcp/tools/predict_grammar_score",
    ],
    "prometheus": FIDELITY_STRUCTURE["prometheus"],
    "grafana": FIDELITY_STRUCTURE["grafana"],
    "oidc": {
        "handover": "POST /oidc/handover",
        "subjects": ["orchestrator", "clarke_yoursa_tee_worker", "grafana", "prometheus"],
        "secret_policy": "full_64_char_sha256_no_truncation",
    },
    "pauli": {
        "module": "quantum.pauli_phi_hamiltonian",
        "trace_target": "phi^{-2}",
        "trace_value": PHI_NEG2,
        "disclaimer": "coherence invariant only — not encryption-breaking",
    },
    "engine": {
        "module": "sovereign_engine",
        "systems_go": "sovereign_engine.systems_go",
    },
}

OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "https://token.actions.githubusercontent.com")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "your-client-id")

_predictions_total = 0.0
_last_coherence = 1.0
_last_fidelity = DEFAULT_FIDELITY
_last_pauli_trace = PHI_NEG2
_last_pauli_verified = 1.0
_last_systems_go = 1.0


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
        # FULL 64-char hex — never truncate
        return hashlib.sha256(seed.encode()).hexdigest()


def oidc_handover_verify(token: str) -> Dict[str, Any]:
    """MCP/OIDC handover: verify Garden opaque token, else accept non-empty bearer."""
    try:
        from batch_oidc_tokenizer import verify_token

        result = verify_token(token)
        if result.get("ok"):
            return result
        return {"ok": False, "error": result.get("error", "verify_failed"), "fallback": False}
    except Exception:
        return {"ok": bool(token and len(token) > 8), "fallback": True, "mode": "bearer_presence"}


def mint_worker_handover(ttl_s: int = 3600) -> Dict[str, Any]:
    """Issue OIDC-style tokens for orchestrator, worker, grafana, prometheus (+ Pauli claim)."""
    try:
        from batch_oidc_tokenizer import batch_mint, mint_token

        tokens = batch_mint(
            ["orchestrator", "clarke_yoursa_tee_worker", "grafana", "prometheus"],
            ttl_s=ttl_s,
        )
        # APPEND: extra claim token for Pauli wire (full secret_len, no truncation)
        pauli_claim = mint_token(
            "pauli_phi_hamiltonian",
            claims={
                "trace_target": "phi^{-2}",
                "trace": PHI_NEG2,
                "fidelity_structure": "prometheus_grafana_default",
                "capabilities": list(AVAILABLE_CAPABILITIES["mcp"]),
            },
            ttl_s=ttl_s,
        )
        tokens.append(pauli_claim)
        secret_len = tokens[0]["secret_len"] if tokens else len(resolve_oidc_secret())
        # Assert full digest policy
        assert secret_len >= 32, "OIDC secret too short — refuse truncation"
        for t in tokens:
            assert len(t.get("sig", "")) == 64, "HMAC sig must be full 64-hex"
        return {
            "ok": True,
            "subjects": [t["payload"]["sub"] for t in tokens],
            "tokens": tokens,
            "secret_len": secret_len,
            "sig_lens": [len(t["sig"]) for t in tokens],
            "fidelity_structure": "prometheus_grafana_default",
            "pauli_wired": True,
            "capabilities": AVAILABLE_CAPABILITIES,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "secret_len": len(resolve_oidc_secret()),
            "pauli_wired": False,
        }


def load_pauli_status() -> Dict[str, Any]:
    """Wire Pauli module — full status, no truncated fields."""
    global _last_pauli_trace, _last_pauli_verified
    try:
        from quantum.pauli_phi_hamiltonian import PauliPhiHamiltonian

        st = PauliPhiHamiltonian().status()
        _last_pauli_trace = float(st["trace"])
        _last_pauli_verified = 1.0 if st.get("verified") else 0.0
        return st
    except Exception as e:
        _last_pauli_trace = PHI_NEG2
        _last_pauli_verified = 0.0
        return {
            "model": "pauli_phi_hamiltonian",
            "trace": PHI_NEG2,
            "verified": False,
            "error": str(e),
            "disclaimer": "coherence invariant only — not encryption-breaking",
        }


def load_systems_go() -> Dict[str, Any]:
    global _last_systems_go
    try:
        from sovereign_engine import systems_go

        report = systems_go()
        _last_systems_go = 1.0 if report.get("systems_go") else 0.0
        return report
    except Exception as e:
        _last_systems_go = 0.0
        return {"systems_go": False, "error": str(e)}


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
    pauli_trace: float = PHI_NEG2


app = FastAPI(
    title="Clarke_Yoursa_Tee_worker",
    version="1.2.0",
    description="MCP + OIDC worker; Prometheus+Grafana fidelity; Pauli wire; full digests",
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
    pauli = load_pauli_status()
    return {
        "status": "ok",
        "worker": "clarke_yoursa_tee_worker",
        "version": "1.2.0",
        "oidc_secret_len": len(secret),
        "frb_period_secs": FRB_PERIOD_SECS,
        "phi": PHI,
        "fidelity": _last_fidelity,
        "fidelity_structure": "prometheus_grafana_default",
        "entangled": ["orchestrator", "prometheus", "grafana", "pauli_phi_hamiltonian"],
        "pauli_trace": pauli.get("trace", PHI_NEG2),
        "pauli_verified": bool(pauli.get("verified")),
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
        "pauli_trace": _last_pauli_trace,
        "systems_go": _last_systems_go,
    }
    return out


@app.get("/capabilities")
def capabilities() -> Dict[str, Any]:
    """Available MCP + OIDC + Prometheus + Grafana + Pauli capabilities."""
    return {
        "worker": "clarke_yoursa_tee_worker",
        "capabilities": AVAILABLE_CAPABILITIES,
        "policy": {
            "truncate": False,
            "subtract_wiring": False,
            "oidc_digest": "full_64_char",
            "hmac_sig": "full_64_hex",
        },
        "seal": "∀∞φ² · MCP_OIDC_PAULI_CAPABILITIES_8665 · SEALED",
    }


@app.get("/pauli")
def pauli_route() -> Dict[str, Any]:
    return load_pauli_status()


@app.get("/systems_go")
def systems_go_route() -> Dict[str, Any]:
    return load_systems_go()


@app.post("/oidc/handover")
def oidc_handover() -> Dict[str, Any]:
    """Mint entangled OIDC tokens for orchestrator / worker / grafana / prometheus / Pauli."""
    return mint_worker_handover()


@app.get("/metrics")
def metrics() -> str:
    """Prometheus text exposition — worker entangled gauges (append Pauli; no subtract)."""
    global _last_coherence, _last_fidelity, _predictions_total
    load_pauli_status()
    load_systems_go()
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
        # APPEND 8665 — Pauli + systems_go (do not remove lines above)
        "# HELP worker_pauli_trace Pauli φ-Hamiltonian trace (target φ^{-2})",
        "# TYPE worker_pauli_trace gauge",
        f"worker_pauli_trace {_last_pauli_trace}",
        "# HELP worker_pauli_verified 1 if trace identity verified",
        "# TYPE worker_pauli_verified gauge",
        f"worker_pauli_verified {_last_pauli_verified}",
        "# HELP worker_systems_go 1 if sovereign_engine.systems_go",
        "# TYPE worker_systems_go gauge",
        f"worker_systems_go {_last_systems_go}",
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
    _last_fidelity = min(1.0, DEFAULT_FIDELITY + (1.0 - DEFAULT_FIDELITY) * (1.0 - 1.0 / PHI3))
    secret = resolve_oidc_secret()
    pauli = load_pauli_status()
    return GrammarResponse(
        actual_score=request.actual_score,
        predicted_score=round(predicted, 4),
        prediction_error=round(predicted - request.actual_score, 4),
        coherence=coherence,
        fidelity=_last_fidelity,
        oidc_secret_len=len(secret),
        fidelity_structure="prometheus_grafana_default",
        pauli_trace=float(pauli.get("trace", PHI_NEG2)),
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
        pauli = load_pauli_status()
        return {
            "actual_score": actual_score,
            "predicted_score": round(predicted, 4),
            "prediction_error": round(predicted - actual_score, 4),
            "coherence": coherence,
            "fidelity": DEFAULT_FIDELITY,
            "fidelity_structure": "prometheus_grafana_default",
            "pauli_trace": pauli.get("trace", PHI_NEG2),
            "worker_name": "clarke_yoursa_tee_worker",
        }

    @mcp.tool()
    def get_fidelity_structure() -> dict:
        return FIDELITY_STRUCTURE

    @mcp.tool()
    def get_pauli_status() -> dict:
        return load_pauli_status()

    @mcp.tool()
    def get_systems_go() -> dict:
        return load_systems_go()

    @mcp.tool()
    def list_capabilities() -> dict:
        return AVAILABLE_CAPABILITIES

    app.mount("/mcp", mcp.http_app())
except ImportError:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
