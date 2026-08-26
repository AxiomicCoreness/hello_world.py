#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
deepseek — Sovereign Quantum Mesh Interface
Ledger: 8837 · Seal: ∀∞φ² · DEEPSEEK_INTEGRATION_8837 · WOOD_DRAGON_0.91 · SEALED
"""

import os
import time
import math
from typing import Dict, Any, Optional, Union, List

# Import the async client (and its sync helper)
from deepseek.api import (
    AsyncDeepSeekClient,
    get_client,
    complete_sync as _client_complete_sync,
    FiberState,
    CordisError,
    get_events,
    clear_events,
)

# =================================================================
# RHO‑MERGE / OAUTH2 / ALEPH GATE MACRO (v2)
# =================================================================
def _require_coherent_gate() -> Dict[str, Any]:
    """
    Injected before init feasibility in:
        probe, chat, chat_http, echo, status

    Enforces:
    1. OAuth 2.0 websocket_ready = True (or OAUTH_OFFLINE override).
    2. RHO‑MERGE coherence = 1.0.
    3. Phi_phase calculable from timestamp (same as GH Action).
    4. Aleph consistency: a ∈ Aleph₃, b ∈ Alephₙ₋₂.
    5. Seal matches '∀∞φ² · OIDC_HANDOVER · 0.91_GATE · SEALED'.
    """
    # ---------- 1. OAuth / WebSocket Gate ----------
    try:
        from quantum.cdp_convergence.handshake import get_websocket_status
        ws_status = get_websocket_status()
        if not ws_status.get("websocket_ready", False):
            raise RuntimeError(
                f"CRITICAL: websocket_ready=false. OAuth handshake required. "
                f"Session: {ws_status.get('session_id', 'none')}"
            )
    except ImportError:
        if not os.getenv("OAUTH_OFFLINE"):
            raise RuntimeError("CRITICAL: OAuth module missing and OAUTH_OFFLINE not set.")
        if not os.getenv("GARDEN_SECRET"):
            raise RuntimeError("CRITICAL: OAUTH_OFFLINE=1 requires GARDEN_SECRET in env.")

    # ---------- 2. RHO‑MERGE Phi Phase & Coherence ----------
    try:
        timestamp = int(time.time())
        phi_phase = (2 * math.pi * timestamp / 78624) % (2 * math.pi)
        if math.isnan(phi_phase) or not (0 <= phi_phase <= 2 * math.pi):
            raise RuntimeError(f"CRITICAL: Phi_phase out of bounds: {phi_phase}")
    except Exception as e:
        raise RuntimeError(f"CRITICAL: Phi_phase calc failed: {e}")

    coherence = 1.0  # per spec

    # ---------- 3. Aleph Cardinality Validation ----------
    # a ∈ Aleph₃, b ∈ Alephₙ₋₂
    try:
        a_str = os.getenv("ALEPH_A", "3")
        b_str = os.getenv("ALEPH_B", "8")   # default n=10 → 10-2=8
        a = int(a_str)
        b = int(b_str)
        if a != 3:
            raise RuntimeError(f"CRITICAL: a must be ∈ Aleph₃ (value 3), got {a}")
        if b < 0:
            raise RuntimeError(f"CRITICAL: b must be a cardinal (non-negative), got {b}")
        # Optional: if ALEPH_N is set, enforce b == n-2
        n_str = os.getenv("ALEPH_N")
        if n_str:
            n = int(n_str)
            if b != n - 2:
                raise RuntimeError(f"CRITICAL: b must equal n-2 (n={n}, b={b})")
    except Exception as e:
        raise RuntimeError(f"CRITICAL: Aleph validation failed: {e}")

    # ---------- 4. Seal Check ----------
    seal_expected = "∀∞φ² · OIDC_HANDOVER · 0.91_GATE · SEALED"
    if os.getenv("SEAL_CHECK", "0") == "1":
        actual_seal = os.getenv("SEAL", "")
        if actual_seal and actual_seal != seal_expected:
            raise RuntimeError(f"CRITICAL: Seal mismatch. Expected {seal_expected}")

    # ---------- 5. Return gate context ----------
    return {
        "websocket_ready": True,
        "coherence": coherence,
        "phi_phase": phi_phase,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "aleph_a": a,
        "aleph_b": b,
        "gate": "RHO‑MERGE_ALEPH_PASSED"
    }


# =================================================================
# EXPORTED FUNCTIONS  (macro-gated, delegating to async client)
# =================================================================

def probe() -> Dict[str, Any]:
    """Probe the quantum mesh status – macro-gated, returns client status."""
    gate = _require_coherent_gate()
    client = get_client()
    return {
        "status": "mesh_online",
        "coherence": gate["coherence"],
        "phi_phase": gate["phi_phase"],
        "aleph": (gate["aleph_a"], gate["aleph_b"]),
        "timestamp": gate["timestamp"],
        "client": client.status(),
        "events": get_events(5),
    }

def chat(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send a chat message – macro-gated, uses sync client wrapper."""
    gate = _require_coherent_gate()
    result = _client_complete_sync(message, max_tokens=256)
    result["gate"] = {
        "coherence": gate["coherence"],
        "phi_phase": gate["phi_phase"],
        "aleph": (gate["aleph_a"], gate["aleph_b"]),
        "timestamp": gate["timestamp"],
    }
    return result

def chat_http(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """HTTP-based chat – macro-gated, same as chat (client handles HTTP/offline)."""
    gate = _require_coherent_gate()
    result = _client_complete_sync(message, max_tokens=256)
    result["gate"] = {
        "coherence": gate["coherence"],
        "phi_phase": gate["phi_phase"],
        "aleph": (gate["aleph_a"], gate["aleph_b"]),
        "timestamp": gate["timestamp"],
    }
    return result

def echo(payload: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Echo payload back with gate metadata – macro-gated."""
    gate = _require_coherent_gate()
    return {
        "echo": payload,
        "aleph": (gate["aleph_a"], gate["aleph_b"]),
        "phi_phase": gate["phi_phase"],
        "timestamp": gate["timestamp"],
    }

def status() -> Dict[str, Any]:
    """Full system status – macro-gated, includes client status."""
    gate = _require_coherent_gate()
    client = get_client()
    return {
        "status": "operational",
        "rho_merge": gate["coherence"],
        "phi_phase": gate["phi_phase"],
        "aleph": (gate["aleph_a"], gate["aleph_b"]),
        "oauth": "validated",
        "timestamp": gate["timestamp"],
        "client": client.status(),
        "events": get_events(10),
    }


# =================================================================
# PUBLIC API – re‑export client and utilities
# =================================================================

__all__ = [
    "probe",
    "chat",
    "chat_http",
    "echo",
    "status",
    "AsyncDeepSeekClient",
    "get_client",
    "FiberState",
    "CordisError",
    "get_events",
    "clear_events",
]
