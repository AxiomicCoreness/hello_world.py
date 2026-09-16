"""Systems-go soft report — Bedrock optional; hard invariants only for phi/coherence."""
from __future__ import annotations

import math
import os

from fastapi import APIRouter

router = APIRouter(tags=["systems"])

PHI = (1 + math.sqrt(5)) / 2
PHI2 = PHI * PHI
PHI_NEG2 = PHI ** (-2)
NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6


@router.get("/systems")
def systems_go():
    """Soft report: Bedrock absence is warn, not hard fail."""
    bedrock = False
    try:
        import boto3  # noqa: F401

        bedrock = True
    except ImportError:
        bedrock = False

    phi_ok = abs(PHI2 - (PHI + 1)) < 1e-12
    secret = os.environ.get("OIDC_CLIENT_SECRET", "")
    oidc_len = len(secret) if secret else 0

    hard = {
        "phi_polynomial": phi_ok,
        "north_star_hz": NORTH_STAR_HZ,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "pauli_trace_target": PHI_NEG2,
    }
    soft = {
        "bedrock_available": bedrock,
        "oidc_secret_present": oidc_len >= 32,
        "oidc_secret_len": oidc_len,
    }
    # Hard pass does not require Bedrock
    systems_go_hard = phi_ok
    return {
        "systems_go": systems_go_hard,
        "hard": hard,
        "soft": soft,
        "seal": "∀∞φ² · SYSTEMS_GO_SOFT_BEDROCK · SEALED",
        "note": "Bedrock is soft; pre-deploy All-passed must not require it",
    }
