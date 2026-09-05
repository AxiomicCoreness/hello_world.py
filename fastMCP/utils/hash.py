"""Hashing utilities."""

import hashlib

def event_hash(event: str, salt: str = "") -> str:
    """Generate event hash using SHA3-256."""
    data = f"{event}{salt}"
    return hashlib.sha3_256(data.encode()).hexdigest()
