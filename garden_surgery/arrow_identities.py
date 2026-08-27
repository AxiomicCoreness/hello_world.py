"""Standby vector: evaluable Sagittarius-arrow identities only."""
from __future__ import annotations
import json, hashlib
from garden_surgery.theorems import PHI, PHI2
PHI4 = PHI2 * PHI2
PHI_NEG2 = PHI ** -2
VECTOR = "standby"

def canonical_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha3_256(blob.encode("utf-8")).hexdigest()

def arrow_identities():
    momentum = PHI4 + PHI2
    velocity = PHI_NEG2
    product = momentum * velocity
    return {
        "vector": VECTOR,
        "momentum": momentum,
        "velocity": velocity,
        "product": product,
        "target_phi2_plus_1": PHI2 + 1.0,
        "product_equals_phi2_plus_1": abs(product - (PHI2 + 1.0)) < 1e-12,
        "shell_identity_equals_phi": abs((PHI ** 13) ** (1.0 / 13.0) - PHI) < 1e-12,
        "duplicate_of_sovereign_long_road": True,
        "monolith_appended": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
    }

def payload():
    ids = arrow_identities()
    return {"event": "/surgery/standby_arrow_identities", "entry": 9037, "identities": ids}
