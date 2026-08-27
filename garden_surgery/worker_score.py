"""Narrow φ-corrected grammar score. No live OIDC. No secret echo."""
from __future__ import annotations
import math
from typing import Any, Dict
from garden_surgery.theorems import PHI
FRB_PERIOD_SECS = 0.91 * 86400.0
PHI4_SQRT7 = (PHI ** 4) * math.sqrt(7.0)

def coherence(phase: float, period: float = FRB_PERIOD_SECS) -> float:
    return (math.cos(phase * 2.0 * math.pi / period) + 1.0) / 2.0

def phi_corrected_score(actual: float, phase: float = 0.0) -> float:
    c = coherence(phase)
    slope = 0.35 + (0.65 * c)
    intercept = 9.0 * (1.0 - c)
    return intercept + slope * actual

def score_payload(actual: float, phase: float = 0.0) -> Dict[str, Any]:
    predicted = phi_corrected_score(actual, phase)
    return {
        "actual_score": actual,
        "predicted_score": round(predicted, 4),
        "prediction_error": round(predicted - actual, 4),
        "coherence": coherence(phase),
        "worker_name": "clarke_yoursa_tee_worker",
        "mcp_live": False,
        "oidc_client_credentials_used": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "kappa_phi4_sqrt7": PHI4_SQRT7,
    }
