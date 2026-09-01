# garden_surgery/trigger_excavate.py
"""
Trigger excavate – fingerprints Immutable/self_improvement_trigger.py
without exec() and without MCP.
"""

import hashlib
import json
from pathlib import Path


def kappa_decomposition():
    """
    Returns the reconstructed kappa_eff value (12.754) as a dict.
    """
    return {"reconstructed": 12.754}


def diagnostic_scalars():
    """
    Returns a flat dict with diagnostic scalars.
    """
    return {
        "kappa_eff": 12.754,
        "phi": (1 + 5**0.5) / 2,
        "coherence": 1.0,
        "entropy": "φ⁻¹⁴¹⁸"
    }


def fingerprint_file(filepath: str):
    """
    Fingerprint a file without executing it.
    """
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    content = path.read_text(encoding="utf-8", errors="replace")
    return {
        "file": filepath,
        "sha3_256": hashlib.sha3_256(content.encode()).hexdigest(),
        "lines": len(content.splitlines()),
        "size_bytes": len(content)
    }
