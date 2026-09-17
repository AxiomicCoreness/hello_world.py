"""Merkle policy seal — SHA3‑256 sealed control policy."""

import hashlib
from datetime import datetime

PHI8 = PHI ** 8
TEMPORAL_ANCHOR = "2026.02.24"

def seal_policy(prev_hash: str, policy_data: str) -> str:
    timestamp = datetime(2026, 2, 24).timestamp()
    phi_factor = PHI8 * timestamp
    data = f"{prev_hash}{policy_data}{phi_factor}"
    return hashlib.sha3_256(data.encode()).hexdigest()

def verify_policy_seal(seal: str, prev_hash: str, policy_data: str) -> bool:
    return seal == seal_policy(prev_hash, policy_data)
