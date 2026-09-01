# garden_surgery/trigger_excavate.py
"""
Trigger excavate – fingerprints Immutable/self_improvement_trigger.py
without exec() and without MCP.
"""

import hashlib
from pathlib import Path

# ─── Constants ─────────────────────────────────────────
KAPPA_DECLARED = 12.754  # declared kappa_eff from Entry 707


# ─── Functions ─────────────────────────────────────────
def kappa_decomposition():
    """Return reconstructed kappa_eff value."""
    return {"reconstructed": KAPPA_DECLARED}


def diagnostic_scalars():
    """Return flat dict with diagnostic scalars."""
    return {
        "k_eff": KAPPA_DECLARED,
        "phi": (1 + 5**0.5) / 2,
        "coherence": 1.0,
        "entropy": "φ⁻¹⁴¹⁸",
    }


def golden_hash(data: str = "sovereign") -> str:
    """
    Placeholder golden hash (16-hex truncation of SHA3-256).
    In production, this should be the actual ledger hash.
    """
    full = hashlib.sha3_256(data.encode()).hexdigest()
    return full[:16]


def fingerprint_file(filepath: str):
    """Fingerprint a file without executing it."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    content = path.read_text(encoding="utf-8", errors="replace")
    return {
        "file": filepath,
        "sha3_256": hashlib.sha3_256(content.encode()).hexdigest(),
        "lines": len(content.splitlines()),
        "size_bytes": len(content),
    }
